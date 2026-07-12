"""SQI-02 Part XV -- weakening detection. The attack the count-based guardian cannot see.

Part XII catches deletion, and deletion is the LOUD failure: it lowers a count, and a lowered
count fails a build. Weakening lowers NOTHING (15.1). The file is present, the case is collected,
the case is executed, the case passes, every metric in the corpus reports no change, and the
protection is gone. It is almost never done with intent, and it is the exact mechanism by which a
suite becomes decorative without a single alarming event ever occurring.

Ten mechanisms. What each one does to the instrument, and what actually detects it:

    15.2  removed assertion      assertions fall, the case still passes     assertion count   FAIL
    15.3  widened handler        the assertion decouples from the behaviour broad-catch scan  REVIEW
    15.4  unreal fixture         the input stops resembling production      -- none --        REVIEW
    15.5  skip / marker          the executed count moves                   Part XII          gated
    15.6  over-mocking           the unit is the only real object left      mock count trend  FAIL
    15.7  lowered threshold      each change defensible, the sum is lethal  threshold ledger  gap
    15.8  tautological assertion passes for every implementation, incl. broken  mutation probe FAIL
    15.9  relocation / rewrite   identity or content changes under a stable count  hash        REVIEW

Two contracts govern this module.

FIRST: the counters are AST-based, never regular expressions over source. A regex counts the word
`assert` inside a comment, a docstring, and a string literal, and an instrument that can be
satisfied by writing the word `assert` in a comment is worse than no instrument, because it will
be satisfied exactly when somebody is trying to satisfy it.

SECOND, and this is 15.4 stated as code: THERE IS NO COUNTING DETECTOR FOR THE UNREAL FIXTURE, and
the Part is explicit that claiming one would be dishonest. A fixture that supplied a realistic
payload and now supplies a minimal one keeps every number in this module constant. What is offered
instead is the content hash -- the change is surfaced for review, and the reviewer is told the
arithmetic did not move, which is precisely the signature of a fixture edit and of a same-name
rewrite (15.9). It is a candidate list, not a verdict.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

from .reconcile import _norm  # the join key MUST be the one the census uses (SQI-02 5.4)

UNKNOWN = "UNKNOWN"

# 15.2 -- what counts as an assertion. `assert` is the statement; the rest are the library forms
# that carry the same meaning, and a test that uses only the library forms is not assertion-free.
#
# THE VOCABULARY IS THE GATE'S EYESIGHT, and its direction of danger is the exact inverse of the
# census `exclusions`. Widening this list makes more verifications visible and the gate STRICTER.
# NARROWING it makes removed assertions invisible -- a file whose entire protective content is
# written in an idiom the list does not name has an assertion count of zero, and ZERO CANNOT FALL.
# Measured on this repository the first time this detector ran: 92 of 101 authored test files
# reported zero assertions, and 60 of them had been verifying things the whole time, in the
# estate's own V-gate idiom, one file 139 times over. So the call forms live in the governed
# artifact beside the census rules, where a narrowing is a reviewable act rather than an edit.
_ASSERT_METHOD = re.compile(r"^assert[A-Za-z_]*$")          # self.assertEqual, assertTrue, ...
_MOCK_ASSERT = re.compile(r"^assert_[a-z_]+$")               # m.assert_called_once_with(...)

_DEFAULT_CALL_NAMES = frozenset({"_ok", "_fail", "_check", "_assert", "expect", "should"})
_DEFAULT_ATTR_TAILS = frozenset({"raises", "warns", "should", "expect"})

_RULES_PATH = Path(__file__).with_name("discovery_rules.json")


def _vocabulary() -> tuple[frozenset, frozenset]:
    """Fail-open: an unreadable or malformed rules file yields the built-in defaults. A detector
    that refused to run because its configuration was missing would be a detector that is off."""
    try:
        voc = json.loads(_RULES_PATH.read_text(encoding="utf-8-sig"))["assertion_vocabulary"]["python"]
        calls = frozenset(voc.get("call_names") or ()) or _DEFAULT_CALL_NAMES
        tails = frozenset(voc.get("attr_tails") or ()) or _DEFAULT_ATTR_TAILS
        return calls, tails
    except (OSError, ValueError, KeyError, TypeError):
        return _DEFAULT_CALL_NAMES, _DEFAULT_ATTR_TAILS


_ASSERT_CALL_NAME, _ASSERT_CALL_TAIL = _vocabulary()

# 15.6 -- what counts as a mocked collaborator. Each entry here is one real interaction removed
# from the exercise. Past a threshold the unit under test is the only real object in the room and
# the test asserts that a function calls the stubs it was told to call.
_MOCK_FACTORIES = {"Mock", "MagicMock", "AsyncMock", "NonCallableMock", "create_autospec", "patch"}
_MONKEYPATCH_METHODS = {"setattr", "setitem", "setenv", "delattr", "delitem", "delenv", "syspath_prepend"}

# The estate's standing static rule (rules/python/testing.md): four or more mocked collaborators
# means the unit under test is doing too much. It is an ADVISORY here, never a build failure --
# it describes a design smell that may predate this commit, and a gate that fails a build for a
# condition the current change did not cause is a gate that gets disabled.
MOCK_SMELL_FLOOR = 4

# The probe runs a real suite twice per target, so its ceiling is a suite's wall time, not a
# command's. The git probe is a metadata read and is bounded far tighter -- if `git status` on one
# path has not answered in this long, the answer is not coming.
PROBE_TIMEOUT_S = 600
GIT_STATUS_TIMEOUT_S = 30

# The mutated expression is echoed into the report so a reader sees WHAT was broken without
# opening the file. It is an excerpt, not the expression: a 400-character return line would push
# the finding off the screen, and the finding is the point.
SNIPPET_CHARS = 80


@dataclass
class FileRecord:
    """One authored test file, as three independent observations.

    `None` is UNKNOWN and is never coerced to zero. A file the parser cannot read has an unknown
    assertion count, and reporting that as zero would manufacture a weakening event out of a
    syntax error -- an instrument that cries wolf is an instrument that gets turned off."""

    path: str
    assertions: int | None = None
    mocks: int | None = None
    sha256: str | None = None
    cases: int | None = None
    broad_catches: int | None = None
    verification: str = "assertions"   # assertions | exit_code_gate | none
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _has_exit_gate(tree: ast.Module) -> bool:
    """A THIRD idiom, found in this repository and in no textbook: the file builds a results table,
    counts its failures, and gates on `sys.exit(main())`. Its protection is a non-zero exit code,
    and it contains not one assertion of any recognized form.

    This matters more than it looks. Such a file has an assertion count of zero, and ZERO CANNOT
    FALL -- so recording it as zero would hand the gate a number that can never raise an alarm
    while reporting, in the same breath, that the file protects nothing. Both halves would be
    wrong. The count is not low here; it is INAPPLICABLE, and the honest output is UNKNOWN. Zero
    is a measurement; this is the absence of one, and rounding the second to the first is the
    attribution error the whole corpus exists to forbid."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
        if name not in {"exit", "_exit"}:
            continue
        if not node.args:
            continue
        arg = node.args[0]
        # `sys.exit(0)` is a success path, not a gate. Anything computed -- a failure count, a
        # main() return, a boolean -- is one.
        if isinstance(arg, ast.Constant) and arg.value in (0, None):
            continue
        return True
    return False


def hash_test_content(path: Path) -> str | None:
    """15.9 -- the content hash defeats the same-name rewrite: a test deleted and reintroduced
    under the same name with a weaker body has kept its identity and kept its count and lost its
    content. It is invisible to any instrument that stores numbers."""
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def _parse(path: Path) -> ast.Module | None:
    try:
        return ast.parse(Path(path).read_text(encoding="utf-8-sig"), filename=str(path))
    except (OSError, SyntaxError, ValueError):
        return None


def _is_assertion(node: ast.AST) -> bool:
    if isinstance(node, ast.Assert):
        return True
    if isinstance(node, ast.Call):
        f = node.func
        if isinstance(f, ast.Attribute):
            if _ASSERT_METHOD.match(f.attr) or _MOCK_ASSERT.match(f.attr):
                return True
            if f.attr in _ASSERT_CALL_TAIL:
                return True
        # The estate's V-gate idiom: `_ok("V-NAME", evidence)` / `_fail("V-NAME", diagnostic)`.
        # These ARE the assertions in 60 of this repository's 101 test files, and a detector that
        # did not name them would grade the majority of the suite as protecting nothing while
        # being unable to notice if it ever stopped.
        if isinstance(f, ast.Name) and f.id in _ASSERT_CALL_NAME:
            return True
    # `with pytest.raises(...)` is an assertion about a failure, and a test that only raises-checks
    # is still asserting something.
    if isinstance(node, (ast.With, ast.AsyncWith)):
        for item in node.items:
            c = item.context_expr
            if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute):
                if c.func.attr in _ASSERT_CALL_TAIL:
                    return True
    return False


def count_assertions(path: Path) -> int | None:
    """15.2. An assertion is the only thing in a test that can fail, so a test that lost its
    assertions passes MORE reliably than before. A test with zero assertions is not a test; it is
    an execution, and every runner reports it as passing."""
    tree = _parse(path)
    if tree is None:
        return None
    n = 0
    for node in ast.walk(tree):
        if _is_assertion(node):
            n += 1
    return n


def _mock_hits(node: ast.AST) -> int:
    n = 0
    if isinstance(node, ast.Call):
        f = node.func
        if isinstance(f, ast.Name) and f.id in _MOCK_FACTORIES:
            n += 1
        elif isinstance(f, ast.Attribute):
            if f.attr in _MOCK_FACTORIES:                       # mock.patch(...), unittest.mock.Mock()
                n += 1
            elif f.attr in _MONKEYPATCH_METHODS and isinstance(f.value, ast.Name) \
                    and f.value.id in {"monkeypatch", "mp"}:
                n += 1
    return n


def count_mocks(path: Path) -> int | None:
    """15.6. Each collaborator replaced by a stub removes a real interaction from the exercise.
    Decorators count: `@patch(...)` above a test IS a mocked collaborator, and it is the form that
    a body-only scan misses."""
    tree = _parse(path)
    if tree is None:
        return None
    n = 0
    for node in ast.walk(tree):
        n += _mock_hits(node)
    return n


def count_cases(path: Path) -> int | None:
    """Authored cases in the file. The denominator that makes an assertion count comparable: a
    file that gained three tests and three assertions did not weaken, and a file that gained three
    tests and no assertions gained three executions."""
    tree = _parse(path)
    if tree is None:
        return None
    return sum(
        1 for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test")
    )


def count_broad_catches(path: Path) -> int | None:
    """15.3 -- the widened handler, which most often ships inside a sincere repair. A test that
    asserted a specific failure now catches a broad class of them, and it passes when the system
    does the wrong thing, because the wrong thing is inside the class the handler tolerates.

    This is a REVIEW signal and never a verdict. The Part is explicit: a broad handler is
    sometimes correct."""
    tree = _parse(path)
    if tree is None:
        return None
    n = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            t = node.type
            if t is None:                                              # bare `except:`
                n += 1
            elif isinstance(t, ast.Name) and t.id in {"Exception", "BaseException"}:
                n += 1
    return n


def scan_file(repo: Path, path: Path) -> FileRecord:
    """Never raises. A file that cannot be read is UNKNOWN in every field, and UNKNOWN is not a
    finding -- it is the absence of one."""
    rel = _norm(str(Path(path).resolve().relative_to(Path(repo).resolve())))
    sha = hash_test_content(path)
    tree = _parse(path)
    if tree is None:
        return FileRecord(
            path=rel, sha256=sha,
            error="unparseable (syntax error, encoding, or unreadable) -- counts are UNKNOWN, "
                  "not zero",
        )
    a = m = c = b = 0
    for node in ast.walk(tree):
        if _is_assertion(node):
            a += 1
        m += _mock_hits(node)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
            c += 1
        if isinstance(node, ast.ExceptHandler):
            t = node.type
            if t is None or (isinstance(t, ast.Name) and t.id in {"Exception", "BaseException"}):
                b += 1

    if a == 0 and _has_exit_gate(tree):
        return FileRecord(
            path=rel, assertions=None, mocks=m, sha256=sha, cases=c, broad_catches=b,
            verification="exit_code_gate",
            error="protection is an exit-code gate, not an assertion. The assertion count is "
                  "INAPPLICABLE here, not zero -- a zero could never fall, and a gate holding one "
                  "would be permanently blind to this file. Tracked by content hash only.",
        )
    return FileRecord(
        path=rel, assertions=a, mocks=m, sha256=sha, cases=c, broad_catches=b,
        verification="assertions" if a else "none",
    )


def scan(repo: Path, files) -> dict[str, dict]:
    """Build the per-file record set for an authored census.

    `files` are repo-relative identities as the reconciliation engine normalizes them -- the join
    key is imported rather than re-derived, because two censuses that normalize their keys
    independently will disagree at exactly the moment a rename happens (SQI-02 5.4)."""
    repo = Path(repo)
    out: dict[str, dict] = {}
    for rel in files:
        p = repo / rel
        if not p.is_file():
            # A case-folded identity may not resolve on a case-sensitive host. Report the miss;
            # do not silently drop the file from the census, which would shrink the denominator.
            out[rel] = FileRecord(
                path=rel, error="authored identity does not resolve to a file on this host"
            ).to_dict()
            continue
        out[rel] = scan_file(repo, p).to_dict()
    return out


# --------------------------------------------------------------------------------------------
# 15.8 -- THE MUTATION PROBE. The tautological assertion is the endpoint of every other
# weakening, and it is the one that no count reveals: `assertIsNotNone` replacing an assertion
# that a result equals an expected value passes for every implementation, including a broken one.
# It raises no count, lowers no count, and appears in a coverage report as a covered line.
#
# The Part offers a cheap approximation and says it is worth more than its cost: take the units
# the instrument claims are protected, break one return value, run the tests that reference it,
# and record which ones remain green. EVERY GREEN ONE IS ASSERTING NOTHING ABOUT THE VALUE IT
# CLAIMS TO PROTECT.
#
# This EXECUTES tests and MUTATES source, so it is opt-in and never part of the default pipeline:
# a measurement that alters the thing it measures as a side effect of measuring it is not one.
# Three safety properties, in order of how badly their absence would end:
#   1. it refuses to touch a file with uncommitted changes -- a failed restore must never be able
#      to destroy work that exists nowhere else;
#   2. the original bytes are restored in a `finally`, and the restore is VERIFIED by hash;
#   3. a verification failure is raised loudly, never swallowed. Fail-open is the rule everywhere
#      in SQI except here: a probe that quietly leaves a mutant in the tree has done the one thing
#      no instrument may ever do.
# --------------------------------------------------------------------------------------------

_NODE_RESULT = re.compile(r"^(?P<node>\S+::\S+)\s+(?P<outcome>PASSED|FAILED|ERROR|XFAIL|XPASS|SKIPPED)")
_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


@dataclass
class Mutant:
    target: str
    line: int
    original: str
    mutated_to: str = "None"
    killed_by: list[str] = field(default_factory=list)
    survived_by: list[str] = field(default_factory=list)
    referencing_tests: list[str] = field(default_factory=list)
    status: str = UNKNOWN          # KILLED | SURVIVED | NOT_REFERENCED | UNKNOWN
    note: str = ""


@dataclass
class MutationReport:
    invocation: str
    mutants: list[Mutant] = field(default_factory=list)
    survivors: int = 0
    killed: int = 0
    skipped: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["mutants"] = [asdict(m) for m in self.mutants]
        return d


def _run_suite(repo: Path, invocation: str, timeout: int) -> dict[str, str]:
    """Return {node_id: outcome}. Per-node, because the Part asks which tests remain green, and a
    suite-level pass/fail cannot answer that: one strong test failing masks a hundred tautologies
    passing beside it."""
    parts = [p for p in invocation.split()[1:] if not p.startswith("-")]
    argv = [sys.executable, "-m", "pytest", *parts, "-v", "--tb=no", "-p", "no:cacheprovider"]
    try:
        proc = subprocess.run(
            argv, cwd=str(repo), capture_output=True, text=True, timeout=timeout,
            errors="replace",
        )
    except (OSError, subprocess.TimeoutExpired):
        return {}
    out: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        # pytest colours its own output, so the outcome arrives as `PASSED` wrapped in escape
        # codes and a naive line match sees nothing at all -- the probe would then report zero
        # per-node results and conclude, wrongly, that the suite never ran. Colour is transport
        # noise; stripping it is not paraphrasing.
        m = _NODE_RESULT.match(_ANSI.sub("", line).strip())
        if m:
            out[_norm(m.group("node"))] = m.group("outcome")
    return out


def _mutation_site(path: Path) -> tuple[int, int, int, int, str] | None:
    """The first `return <non-trivial value>` in the file. Breaking it is the cheapest possible
    perturbation of the unit's observable output, which is exactly what 15.8 asks for."""
    try:
        src = Path(path).read_text(encoding="utf-8-sig")
    except OSError:
        return None
    try:
        tree = ast.parse(src)
    except (SyntaxError, ValueError):
        return None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Return) or node.value is None:
            continue
        v = node.value
        if isinstance(v, ast.Constant) and v.value is None:
            continue                                   # `return None` -- nothing to break
        if v.end_lineno is None or v.end_col_offset is None:
            continue
        seg = ast.get_source_segment(src, v)
        if not seg:
            continue
        return v.lineno, v.col_offset, v.end_lineno, v.end_col_offset, seg
    return None


def _apply(src: str, lineno: int, col: int, end_lineno: int, end_col: int, repl: str) -> str:
    lines = src.splitlines(keepends=True)
    if lineno == end_lineno:
        ln = lines[lineno - 1]
        lines[lineno - 1] = ln[:col] + repl + ln[end_col:]
    else:
        head = lines[lineno - 1][:col] + repl
        tail = lines[end_lineno - 1][end_col:]
        lines[lineno - 1:end_lineno] = [head + tail]
    return "".join(lines)


def _is_dirty(repo: Path, rel: str) -> bool | None:
    """None == cannot tell. The probe treats that as dirty: the cost of being wrong is a
    destroyed uncommitted file, and no measurement is worth that."""
    git = r"C:\Program Files\Git\cmd\git.exe"
    exe = git if Path(git).is_file() else "git"
    try:
        proc = subprocess.run(
            [exe, "-C", str(repo), "status", "--porcelain", "--", rel],
            capture_output=True, text=True, timeout=GIT_STATUS_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return bool(proc.stdout.strip())


def _references(test_src: str, target_rel: str) -> bool:
    dotted = target_rel.replace(".py", "").replace("/", ".")
    stem = Path(target_rel).stem
    low = test_src.casefold()
    return dotted.casefold() in low or f"import {stem}".casefold() in low or f" {stem}.".casefold() in low


def mutation_probe(
    repo,
    *,
    invocation: str,
    targets,
    test_files,
    timeout: int = PROBE_TIMEOUT_S,
    allow_dirty: bool = False,
) -> MutationReport:
    """Break one return value per target; record which referencing tests stay green."""
    repo = Path(repo)
    rep = MutationReport(invocation=invocation)

    green_before = _run_suite(repo, invocation, timeout)
    if not green_before:
        rep.error = (
            "the baseline suite produced no per-node results; the probe cannot distinguish a "
            "surviving mutant from a suite that never ran. UNKNOWN, not zero survivors."
        )
        return rep

    sources: dict[str, str] = {}
    for t in test_files:
        try:
            sources[t] = (repo / t).read_text(encoding="utf-8-sig")
        except OSError:
            continue

    for rel in targets:
        path = repo / rel
        if not path.is_file():
            rep.skipped.append(f"{rel}: not a file")
            continue
        if not allow_dirty and _is_dirty(repo, rel) is not False:
            rep.skipped.append(
                f"{rel}: the working tree copy is modified or its state is unknown. The probe "
                f"will not mutate a file whose only copy of a change is on disk."
            )
            continue
        site = _mutation_site(path)
        if site is None:
            rep.skipped.append(f"{rel}: no mutable return site")
            continue

        refs = [
            _norm(t) for t, src in sources.items()
            if _references(src, rel)
        ]
        lineno, col, end_lineno, end_col, seg = site
        mut = Mutant(
            target=rel, line=lineno, original=seg[:SNIPPET_CHARS],
            referencing_tests=sorted(refs),
        )
        if not refs:
            mut.status = "NOT_REFERENCED"
            mut.note = (
                "no test the canonical invocation reaches even mentions this unit. There is "
                "nothing to survive the mutation, and nothing protecting the unit."
            )
            rep.mutants.append(mut)
            continue

        original = path.read_bytes()
        before_hash = hashlib.sha256(original).hexdigest()
        try:
            src = original.decode("utf-8-sig", errors="strict")
            path.write_text(
                _apply(src, lineno, col, end_lineno, end_col, "None"), encoding="utf-8"
            )
            after = _run_suite(repo, invocation, timeout)
        except (OSError, UnicodeDecodeError) as exc:
            rep.skipped.append(f"{rel}: {exc}")
            continue
        finally:
            # Property 2 and 3. The restore is verified, and a failed verification is LOUD.
            try:
                path.write_bytes(original)
            except OSError as exc:  # pragma: no cover -- unreachable without a disk fault
                raise RuntimeError(
                    f"SQI mutation probe FAILED TO RESTORE {rel}. A mutant is on disk. "
                    f"Restore it from git immediately: {exc}"
                ) from exc
            if hashlib.sha256(path.read_bytes()).hexdigest() != before_hash:  # pragma: no cover
                raise RuntimeError(
                    f"SQI mutation probe restored {rel} but the content hash does not match the "
                    f"original. A mutant may be on disk. Restore it from git immediately."
                )

        for node, outcome in after.items():
            test_file = _norm(node.split("::", 1)[0])
            if test_file not in refs:
                continue
            was_green = green_before.get(node) == "PASSED"
            if not was_green:
                continue
            if outcome == "PASSED":
                mut.survived_by.append(node)
            else:
                mut.killed_by.append(node)

        mut.survived_by.sort()
        mut.killed_by.sort()
        if mut.killed_by:
            mut.status = "KILLED"
            rep.killed += 1
            if mut.survived_by:
                mut.note = (
                    f"{len(mut.survived_by)} referencing test(s) stayed green through a broken "
                    f"return value. Each is asserting nothing about the value it claims to "
                    f"protect (15.8)."
                )
        elif mut.survived_by:
            mut.status = "SURVIVED"
            rep.survivors += 1
            mut.note = (
                "every referencing test stayed green while the unit returned a broken value. "
                "The tests execute the unit and assert nothing about its output -- the "
                "tautological assertion (15.8), which no count in this corpus can reveal."
            )
        else:
            mut.status = UNKNOWN
            mut.note = "no referencing test was green before the mutation; nothing to conclude."
        rep.mutants.append(mut)

    return rep
