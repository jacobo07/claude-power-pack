"""Predictive governance gates G1/G2/G3 -- catch the defects that ship green.

Enforcement in this estate covers what crashes. These three cover what lies.

G1 VACUITY      a suite that never asserts a failing outcome tests only the happy
                path, so the gate it guards is unfalsifiable and certifies itself.
G2 EXECUTED     a suite that ran zero tests is UNVERIFIED, never PASS; a collection
                failure is COLLECTION_FAILURE, never a result.
G3 ORACLE       a mechanism emitting a number needs at least one assertion against
                a literal, because comparing a mechanism to itself measures nothing.

New offenders fail the gate. Pre-existing offenders are carried in a baseline and
reported to the Owner queue, so this lands without blocking the current build --
the same debt-baseline shape `reachability.py` uses. The baseline holds NAMES, not
a count: a threshold is satisfied by deleting a suite, a name is not.

Every constant below states the reason it has its value.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from fnmatch import fnmatch
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE = REPO_ROOT / "vault" / "governance" / "predictive_gates_baseline.json"
REPORT = REPO_ROOT / "vault" / "audits" / "predictive_gates_offenders.md"

# Suites live here. Discovered by glob, never enumerated: a suite nobody wrote
# down would otherwise be absent from the denominator, and absence reads as health.
SUITE_GLOB = "tools/test_*.py"

# G2 uses a WIDER denominator than G1/G3, and the difference is the point.
# G1 and G3 judge AUTHORED SUITES, which live in tools/. G2 judges WHAT THE RUNNER
# IMPORTS, which is pytest's default `python_files` surface anywhere in the repo.
# The incident G2 exists for was nine scratch scripts under `_logs/` matching
# `*_test.py`: collected by bare pytest, exiting at import, aborting the run with
# INTERNALERROR before a single test executed. Globbing only tools/ would leave G2
# unable to catch its own founding incident -- a detector that never runs.
COLLECTION_GLOBS = ("test_*.py", "*_test.py")
PRUNE_DIRS = {".git", "node_modules", ".venv", "__pycache__", ".pytest_cache"}

TRIPLE = re.compile(r'("""|\'\'\')(?:.|\n)*?\1')
LINE_COMMENT = re.compile(r"^\s*#")

# --- G1: what a failing expectation looks like in executable text.
# Deliberately conservative. Each alternative denotes an expectation that
# something went WRONG, not merely a comparison that happens to use a number.
FAILURE_ASSERT = re.compile(
    r"pytest\.raises"
    r"|assert\s+not\s"
    r"|\bis\s+False\b"
    r"|==\s*False\b"
    r"|!=\s*0\b"
    r"|(?:rc|ret|code|status|exit|exitcode|returncode|run\([^)]*\))\s*==\s*[1-9]"
    r"|[\"'](?:FAIL|BLOCK|BLOCKED|REJECT|REJECTED|VACUOUS|UNVERIFIED"
    r"|DENY|DENIED|COLLECTION_FAILURE|ERROR)[\"']",
    re.I,
)

# --- G1, second reading: the same expectation, spelled through a helper.
# Most suites in this estate do not write `assert not x`. They hand the
# condition to a helper whose first argument is the V-gate name --
# `_check("V-X-Y", not bad, ok, diagnostic)`. A text scan cannot see through the
# call, so suites that DO construct a broken input and require the rejection
# were reported as never asserting one. A detector blind to the idiom its own
# estate writes in reports zero, and zero never falls.
#
# The bar is unchanged, only the spelling: exactly the constructs the regex
# already honours in bare-assert form. `is not None` is deliberately excluded --
# all six occurrences in this repo are presence checks on a happy path, so
# counting them would clear suites that assert no failure at all.
GATE_NAME_PREFIX = "V-"
FAILURE_LITERALS = {"FAIL", "BLOCK", "BLOCKED", "REJECT", "REJECTED", "VACUOUS",
                    "UNVERIFIED", "DENY", "DENIED", "COLLECTION_FAILURE", "ERROR"}

# --- G3: a comparison against a numeric literal, excluding exit-code checks.
# An exit code is not the number the mechanism emits, so counting it would let
# every suite pass and make G3 vacuous -- the defect G1 exists to catch.
LITERAL_CMP = re.compile(r"(==|>=|<=|>|<)\s*(-?\d+(?:\.\d+)?)\b")
EXITCODE_CONTEXT = re.compile(
    r"(?:(?:rc|ret|code|status|exit|exitcode|returncode|errno)"
    r"|\w*(?:run|main|exit)\([^)]*\))\s*$", re.I)
# Chars of preceding text inspected to decide whether a comparison is an exit-code
# check. 40 covers `assert result.returncode ` comfortably without spanning lines.
LOOKBACK_CHARS = 40


def executable_text(txt: str) -> str:
    """Strip docstrings and comment lines. A comment naming a rule is not a check."""
    txt = TRIPLE.sub("", txt)
    keep = []
    for line in txt.splitlines():
        if LINE_COMMENT.match(line):
            continue
        i = line.find(" #")
        if i > 0:
            line = line[:i]
        keep.append(line)
    return "\n".join(keep)


def suites(repo: Path) -> list[Path]:
    return sorted(repo.glob(SUITE_GLOB))


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8-sig", errors="ignore")
    except OSError:
        return ""


# ---------------------------------------------------------------- G1 vacuity
def _gate_call_args(node: ast.AST) -> list[ast.AST]:
    """Arguments of a call carrying a `V-...` literal, i.e. a V-gate assertion."""
    if not isinstance(node, ast.Call):
        return []
    args = list(node.args) + [k.value for k in node.keywords]
    named = any(isinstance(a, ast.Constant) and isinstance(a.value, str)
                and a.value.startswith(GATE_NAME_PREFIX) for a in args)
    return args if named else []


def _expects_failure(expr: ast.AST) -> bool:
    for n in ast.walk(expr):
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
            return True
        if not isinstance(n, ast.Compare):
            continue
        if any(isinstance(op, ast.NotIn) for op in n.ops):
            return True
        for op, cmp_to in zip(n.ops, n.comparators):
            if not isinstance(cmp_to, ast.Constant):
                continue
            if cmp_to.value is False:
                return True
            if isinstance(op, ast.NotEq) and cmp_to.value == 0:
                return True
            if isinstance(cmp_to.value, str) and cmp_to.value.upper() in FAILURE_LITERALS:
                return True
    return False


# --- G1, third reading: the guard clause, where the assertion is the NEGATION
# of the branch condition.
#
#     if v.status is not Status.NEVER_OBSERVED_TO_WORK or v.passed:
#         _fail("V-DONE-GATE-REJECTS-PROXY", ...)
#         return
#     _ok(...)
#
# The suite asserts `status is NEVER_OBSERVED_TO_WORK and not v.passed` -- a
# failure expectation, spelled inverted and carried in the control flow. Neither
# the regex nor the helper reading can see it, and this is the idiom the most
# rigorous suites in the estate use: the file above holds five such gates and was
# still reported as never asserting a failure.
#
# The fix is not another vocabulary. It inverts the guard and applies the SAME
# criterion agreed above, so the bar does not move: `if status is not PASS:
# _fail(...)` negates to `status is PASS` and correctly stays an offender,
# because it asserts only the happy path.
_OP_INVERSE = {ast.Is: ast.IsNot, ast.IsNot: ast.Is, ast.In: ast.NotIn,
               ast.NotIn: ast.In, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}


def _negate(expr: ast.AST) -> ast.AST:
    """`not expr`, pushed down one level so the existing criterion applies."""
    if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.Not):
        return expr.operand
    if isinstance(expr, ast.BoolOp):
        flipped = ast.Or() if isinstance(expr.op, ast.And) else ast.And()
        return ast.BoolOp(op=flipped, values=[_negate(v) for v in expr.values])
    if isinstance(expr, ast.Compare) and len(expr.ops) == 1:
        inverse = _OP_INVERSE.get(type(expr.ops[0]))
        if inverse is not None:
            return ast.Compare(left=expr.left, ops=[inverse()],
                               comparators=expr.comparators)
    return ast.UnaryOp(op=ast.Not(), operand=expr)


def _reports_failure(stmts: list[ast.stmt]) -> bool | None:
    """Which reporter a branch body calls: True=_fail, False=_ok, None=neither.

    The polarity is load-bearing and cannot be skipped. Both shapes exist here:

        if COND: _fail(...); return   -> the suite asserts `not COND`
        if COND: _ok(...) else: ...   -> the suite asserts `COND`

    Reading only "the body names a V-gate" negates the SUCCESS condition of the
    second shape, which turns `if status == REACHABLE: _ok(...)` into a claimed
    failure assertion and makes G1 a rubber stamp.
    """
    reporters = set()
    for stmt in stmts:
        for inner in ast.walk(stmt):
            if not _gate_call_args(inner):
                continue
            fn = getattr(inner.func, "attr", None) or getattr(inner.func, "id", "") or ""
            reporters.add("fail" in fn.lower())
    if not reporters:
        return None
    return True in reporters


def asserts_a_failure(src: str) -> bool:
    """True when the suite expects a failing outcome, in ANY of the three idioms."""
    if FAILURE_ASSERT.search(executable_text(src)):
        return True
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if any(_expects_failure(a) for a in _gate_call_args(node)):
            return True
        if not isinstance(node, ast.If):
            continue
        polarity = _reports_failure(node.body)
        if polarity is None:
            continue
        asserted = _negate(node.test) if polarity else node.test
        if _expects_failure(asserted):
            return True
    return False


def g1_vacuity(repo: Path) -> list[str]:
    """Suites containing no assertion that expects a failing outcome."""
    return sorted(s.name for s in suites(repo) if not asserts_a_failure(_read(s)))


# --------------------------------------------------- G2 executed-count, static
def _guarded_by_main(node: ast.If) -> bool:
    """True for `if __name__ == "__main__":`, whose sys.exit is legitimate."""
    test = node.test
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == "__name__"
    )


def _is_exit_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
        return False
    fn = node.value.func
    if isinstance(fn, ast.Attribute) and fn.attr == "exit":
        return True
    return isinstance(fn, ast.Name) and fn.id in {"exit", "quit"}


def conftest_ignores(repo: Path) -> list[str]:
    """The `collect_ignore_glob` patterns the runner actually honours.

    Without this, G2 reports files the runner never imports. Measured on this repo:
    the nine `_logs/*_test.py` scripts from the origin incident are already excluded
    here, so counting them would be nine plausible, wrong findings -- the very defect
    class these gates exist to catch.

    Reading the config also makes the config load-bearing: delete the exclusion and
    those files re-enter the surface, and G2 fires. The guard is now monitored rather
    than merely present.
    """
    conftest = repo / "conftest.py"
    if not conftest.exists():
        return []
    try:
        tree = ast.parse(_read(conftest))
    except SyntaxError:
        return []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if "collect_ignore_glob" not in names:
            continue
        if isinstance(node.value, (ast.List, ast.Tuple)):
            return [e.value for e in node.value.elts
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)]
    return []


def collected_files(repo: Path) -> list[Path]:
    """Every file a bare pytest run would import, pruned of vendored trees."""
    ignores = conftest_ignores(repo)
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(repo):
        dirnames[:] = [d for d in dirnames if d not in PRUNE_DIRS]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            if not (fn.startswith("test_") or fn.endswith("_test.py")):
                continue
            p = Path(dirpath) / fn
            rel = p.relative_to(repo).as_posix()
            if any(fnmatch(rel, pat) for pat in ignores):
                continue
            found.append(p)
    return sorted(found)


def g2_module_scope_exit(repo: Path) -> list[str]:
    """Files that can terminate at import time, silencing every test below.

    This is the shape that left 340 authored tests unexecuted: a module-scope
    conditional exit skips the file while the runner still sees a clean status.
    Scanned over the collection surface, not just tools/, because the origin
    incident lived under `_logs/`.
    """
    out = []
    for s in collected_files(repo):
        try:
            tree = ast.parse(_read(s))
        except SyntaxError:
            continue
        rel = s.relative_to(repo).as_posix()
        for node in tree.body:
            if _is_exit_call(node):
                out.append(rel)
                break
            if isinstance(node, ast.If) and not _guarded_by_main(node):
                if any(_is_exit_call(inner) for inner in node.body):
                    out.append(rel)
                    break
    return sorted(out)


# -------------------------------------------------- G2 executed-count, dynamic
PP_TALLY = re.compile(r"_PASS\s*=\s*(\d+)\s*/\s*(\d+)")
PYTEST_TALLY = re.compile(r"(\d+)\s+passed")

PYTEST_NO_TESTS = 5      # pytest exit code for "no tests collected"
PYTEST_INTERNAL = 3      # pytest exit code for an internal error


def classify_run(returncode: int, stdout: str) -> str:
    """Turn a suite's exit into a verdict that distinguishes silence from success.

    An instrument that collapses "nothing ran" into "everything passed" cannot say
    which it found, so those two get different names here.
    """
    if "INTERNALERROR" in stdout or returncode == PYTEST_INTERNAL:
        return "COLLECTION_FAILURE"
    if returncode == PYTEST_NO_TESTS or "no tests ran" in stdout.lower():
        return "UNVERIFIED"
    m = PP_TALLY.search(stdout)
    if m and int(m.group(2)) == 0:
        return "UNVERIFIED"
    if returncode == 0:
        p = PYTEST_TALLY.search(stdout)
        if p and int(p.group(1)) == 0:
            return "UNVERIFIED"
        if not m and not p:
            return "UNVERIFIED"
        return "PASS"
    return "FAIL"


# ----------------------------------------------------------------- G3 oracle
def _literal_assertions(text: str) -> int:
    n = 0
    for m in LITERAL_CMP.finditer(text):
        before = text[max(0, m.start() - LOOKBACK_CHARS):m.start()]
        if EXITCODE_CONTEXT.search(before):
            continue
        n += 1
    return n


def g3_oracle(repo: Path) -> list[str]:
    """Suites with no assertion against a numeric literal.

    LIMIT, stated because omitting it would make this gate claim more than it
    measures: G3 detects the ABSENCE of a literal-compared assertion. It cannot
    tell whether the literal is right. A suite asserting `count == 5` where the
    true answer is 4 passes G3. The oracle gate is necessary, not sufficient --
    correctness of the oracle needs a case whose answer is known independently of
    the mechanism, which no static check can supply. `V-PGG-G3-LIMIT` asserts this
    blind spot exists rather than pretending it does not.
    """
    out = []
    for s in suites(repo):
        if _literal_assertions(executable_text(_read(s))) == 0:
            out.append(s.name)
    return sorted(out)


# ---------------------------------------------------------------- baseline
def load_baseline() -> dict:
    if BASELINE.exists():
        try:
            return json.loads(BASELINE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
    return {}


def collect(repo: Path) -> dict:
    return {"G1": g1_vacuity(repo), "G2": g2_module_scope_exit(repo), "G3": g3_oracle(repo)}


def new_offenders(current: dict, baseline: dict) -> dict:
    return {g: sorted(set(current.get(g, [])) - set(baseline.get(g, []))) for g in current}


# ------------------------------------------------------------------ reporting
def write_report(current: dict, repo: Path) -> None:
    total = len(suites(repo))
    lines = [
        "# Predictive governance -- existing offenders",
        "",
        "Produced by `tools/predictive_governance_gate.py`. These are PRE-EXISTING and",
        "do not block the current build; they are carried in",
        "`vault/governance/predictive_gates_baseline.json` by NAME so the debt falls for",
        "the right reason. A NEW offender fails the gate.",
        "",
        f"Suites discovered: {total}.",
        "",
        "| gate | offenders | what it means |",
        "|---|---|---|",
        f"| G1 vacuity | {len(current['G1'])} | no assertion expects a failing outcome |",
        f"| G2 module-scope exit | {len(current['G2'])} | can terminate at import, silencing the file |",
        f"| G3 oracle | {len(current['G3'])} | no assertion against a numeric literal |",
        "",
    ]
    for gate, blurb in (
        ("G1", "Suites that never assert a failing outcome"),
        ("G2", "Suites that can exit at module scope"),
        ("G3", "Suites with no literal-compared assertion"),
    ):
        lines.append(f"## {gate} -- {blurb}")
        lines.append("")
        lines.extend(f"- `{n}`" for n in current[gate]) if current[gate] else lines.append("none")
        lines.append("")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="G1/G2/G3 predictive governance gates")
    ap.add_argument("--baseline", action="store_true", help="record current offenders as accepted debt")
    ap.add_argument("--report", action="store_true", help="write the Owner-facing offender report")
    args = ap.parse_args()

    current = collect(REPO_ROOT)
    base = load_baseline()

    if args.baseline:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps(current, indent=1), encoding="utf-8")
        print(f"baseline written: {BASELINE}")
        for g in ("G1", "G2", "G3"):
            print(f"  {g}: {len(current[g])} accepted")
        return 0

    if args.report:
        write_report(current, REPO_ROOT)
        print(f"report written: {REPORT}")

    fresh = new_offenders(current, base)
    failed = False
    for gate, label in (("G1", "vacuity"), ("G2", "module-scope exit"), ("G3", "oracle")):
        n_new = len(fresh[gate])
        carried = len(current[gate]) - n_new
        if n_new:
            failed = True
            print(f"{gate} {label:20s} FAIL  {n_new} new, {carried} carried")
            for name in fresh[gate]:
                print(f"    new offender: {name}")
        else:
            print(f"{gate} {label:20s} PASS  0 new, {carried} carried")

    print(f"PREDICTIVE_GATES={'FAIL' if failed else 'PASS'}  suites={len(suites(REPO_ROOT))}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
