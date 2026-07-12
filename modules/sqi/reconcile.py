"""SQI-02 — the Reconciliation Engine. Existence does not imply connection.

A test runner reports on what it collected. Its report is a complete and truthful
description of its own activity, and it contains no field -- and can contain no field --
describing the tests it never saw. A report generated from inside the collection boundary
cannot describe the boundary. This is not a deficiency to be fixed by a better runner; it
is a property of any instrument that measures only what it touches (SQI-02 1.3).

So reach is measured by a second instrument, standing outside the runner, holding an
independent census. This module is that instrument. It performs one subtraction between
two censuses that MUST NOT SHARE A PRODUCER:

    census A   the filesystem topology map, built by a process that has never read the
               project configuration. Asking the runner what it knows about yields a
               reach of one hundred percent in every repository forever (3.2).
    census B   the executed manifest, harvested as NODE IDENTITIES from the runner's own
               structured output. Counts cannot be reconciled -- two matching counts may
               describe disjoint sets (5.7).

Everything else here is bookkeeping. The discipline is knowing which two censuses to
subtract, and knowing that neither may be produced by the party being audited.

Naming note: this module is deliberately NOT called test_reconciliation_engine.py. Under
that name it matched the very `test_*.py` discovery pattern it applies, and entered its
own authored census as a test file -- the Part III 3.4 false positive, committed by the
instrument against itself on its first run. The engine caught it. The name is the fix.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

from modules.sqi.repo_reality_scanner import scan_repo, RepoRealityProfile

UNKNOWN = "UNKNOWN"

# The five green verdicts of SQI-02 Part XVI. Green is the only signal that a correct
# system and an unexamined system produce identically, and the information required to
# separate them is not in the artifact.
TRUE_GREEN = "TRUE_GREEN"                              # -> PROVEN
PARTIAL_GREEN = "PARTIAL_GREEN"                        # -> PARTIALLY-VERIFIED
MISLEADING_GREEN = "MISLEADING_GREEN"                  # -> UNVERIFIED (not partially!)
UNVERIFIED_GREEN = "UNVERIFIED_GREEN"                  # -> UNVERIFIED
ENVIRONMENT_DEPENDENT_GREEN = "ENVIRONMENT_DEPENDENT_GREEN"  # -> CONDITIONALLY-PROVEN

VERDICT_TO_ONTOLOGY = {
    TRUE_GREEN: "PROVEN",
    PARTIAL_GREEN: "PARTIALLY-VERIFIED",
    MISLEADING_GREEN: "UNVERIFIED",
    UNVERIFIED_GREEN: "UNVERIFIED",
    ENVIRONMENT_DEPENDENT_GREEN: "CONDITIONALLY-PROVEN",
}

OK, BROKEN, BLOCKED = "OK", "BROKEN", "BLOCKED"

_NODE = re.compile(r"^(?P<file>[^\s:]+\.py)::")
_SUMMARY = re.compile(r"(\d+)\s+tests?\s+collected")
_ERRORS = re.compile(r"(\d+)\s+error")
_DESELECTED = re.compile(r"(\d+)\s+deselected")

SELF_SYMBOL = "modules.sqi"


@dataclass
class Invocation:
    """A reach figure quoted without its invocation and its environment is not a weak
    measurement -- it is not a measurement, in the same way a temperature quoted without
    a scale is not a temperature (SQI-02 2.8)."""

    command: str
    oracle: str            # "ci" | "documentation" | "zero_arg_default"
    authoritative: bool
    status: str = UNKNOWN  # OK | BROKEN | BLOCKED
    exit_code: int | None = None
    executed_files: list[str] = field(default_factory=list)
    executed_cases: int | None = None
    collection_errors: int = 0
    deselected: int = 0
    blocker: str | None = None     # verbatim; never paraphrased
    verdict: str = UNKNOWN
    # Files that live inside this invocation's root and yield no collected case. They are
    # inside the reach boundary and protect nothing -- a class the audit that founded this
    # corpus missed entirely, because it counted files in the directory rather than files
    # in the manifest.
    inert_in_root: list[str] = field(default_factory=list)


@dataclass
class ReconciliationReport:
    repo: str
    commit: str

    authored_files: list[str]
    authored_count: int

    invocations: list[Invocation]
    authoritative_command: str | None

    reached_files: list[str]
    orphaned_files: list[str]
    surprise_files: list[str]          # executed-but-not-authored: the instrument's self-audit

    # Reach metrics (Part VII). None means UNKNOWN. Never estimated. Never zero-by-default.
    test_file_reach: float | None
    test_case_reach: float | None
    suite_activation_ratio: float | None

    # Loss metrics (Part VIII). The orphan count is an ABSOLUTE, because a ratio can be
    # improved by growing the denominator and an absolute cannot.
    orphaned_count: int
    orphaned_ratio: float | None
    silent_collection_loss: int
    executed_protection_ratio: float | None
    unprotected_surface: list[str]

    signal_integrity_verdict: str
    ontology_verdict: str
    authoritative_reach_state: str     # "MEASURED" | "UNKNOWN"

    self_reach: dict                   # mandatory (5.10). An auditor exempt from its own
                                       # audit is not an auditor.
    join_sanity: dict
    per_rule_hits: dict
    uncertainty_count: int
    hermetic_runs: int
    hermetic_stable: bool | None
    findings: list[str]
    error: str | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["invocations"] = [asdict(i) for i in self.invocations]
        return d


def _norm(p: str) -> str:
    """The join key. A join that fails on normalization reports every test as an orphan --
    a catastrophic false positive that destroys the engine's credibility on first contact
    (5.4). Repo-relative, forward-separated, case-folded."""
    p = p.replace("\\", "/").strip()
    while p.startswith("./"):
        p = p[2:]
    return p.casefold()


def _collect(root: Path, argv: list[str], timeout: int = 180) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            [sys.executable] + argv, cwd=str(root), capture_output=True,
            text=True, timeout=timeout, errors="replace",
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, f"collection timed out after {timeout}s"
    except OSError as exc:
        return 126, str(exc)


def _parse_manifest(out: str) -> tuple[list[str], int | None, int, int]:
    """Harvest node IDENTITIES from the runner's own structured output, never a summary.
    A runner that reports forty-three passing has told you a count; a runner that reports
    the identity of each has told you a set, and a set can be subtracted (5.2)."""
    files: list[str] = []
    seen: set[str] = set()
    cases = 0
    for line in out.splitlines():
        m = _NODE.match(line.strip())
        if m:
            cases += 1
            f = _norm(m.group("file"))
            if f not in seen:
                seen.add(f)
                files.append(f)
    summary = _SUMMARY.search(out)
    total = int(summary.group(1)) if summary else (cases or None)
    errors = int(_ERRORS.search(out).group(1)) if _ERRORS.search(out) else 0
    desel = int(_DESELECTED.search(out).group(1)) if _DESELECTED.search(out) else 0
    return files, total, errors, desel


def discover_invocations(root: Path) -> list[Invocation]:
    """SQI-02 Part IX. Three oracles, each answering a different question: the job answers
    what RUNS, the documentation answers what somebody INTENDED to run, and the
    zero-argument default answers what will run when a party with no context arrives.

    Precedence (9.4): the job is authoritative where one exists, because it is the only
    oracle backed by an observation rather than an intention. Where none exists, the
    zero-argument default is authoritative, because it is what will be run by whoever
    arrives next. Documentation is NEVER authoritative.

    An engine that lets the measured party nominate its own invocation has handed over the
    denominator and has ceased to measure anything (9.1).
    """
    invs: list[Invocation] = []

    # Oracle 1: the job. What actually runs.
    ci_dir = root / ".github" / "workflows"
    ci_cmds: list[str] = []
    if ci_dir.is_dir():
        for wf in sorted(ci_dir.glob("*.y*ml")):
            try:
                text = wf.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                continue
            for line in text.splitlines():
                s = line.strip().lstrip("- ").strip()
                if "pytest" in s and not s.startswith("#"):
                    ci_cmds.append(s)
    for c in ci_cmds:
        invs.append(Invocation(command=c, oracle="ci", authoritative=True))

    # Oracle 2: documentation. Evidence of intent, frequently a description of a command
    # that stopped working two years ago. Never authoritative.
    doc_cmds: set[str] = set()
    docs = [root / n for n in ("README.md", "CLAUDE.md", "CONTRIBUTING.md")]
    docs += sorted((root / "rules").rglob("*.md")) if (root / "rules").is_dir() else []
    for p in docs:
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        for m in re.finditer(r"`(pytest [^`\n]{0,60})`", text):
            doc_cmds.add(m.group(1).strip())
    for c in sorted(doc_cmds):
        invs.append(Invocation(command=c, oracle="documentation", authoritative=False))

    # Oracle 3: the zero-argument default. The de facto canon (9.3) -- an agent, a new
    # engineer, a hook and a done-gate will all type the stack's default command, because
    # it is the only one that generalizes across a heterogeneous estate.
    invs.append(
        Invocation(command="pytest", oracle="zero_arg_default", authoritative=not ci_cmds)
    )
    return invs


def _argv_for(cmd: str) -> list[str]:
    """Turn a discovered command into a collection-only argv. Collection, not execution:
    the reach question is answered entirely at collection, which costs seconds and has no
    side effects, and that is what makes the engine cheap enough to run on every commit
    (5.3)."""
    parts = cmd.split()
    if parts and parts[0] == "pytest":
        parts = parts[1:]
    parts = [p for p in parts if not p.startswith("-")]
    return ["-m", "pytest", *parts, "--collect-only", "-q", "-p", "no:cacheprovider"]


def _roots_of(cmd: str) -> list[str]:
    parts = [p for p in cmd.split()[1:] if not p.startswith("-")]
    return [_norm(p).rstrip("/") for p in parts]


def _protection_surface(root: Path, profile: RepoRealityProfile) -> list[str]:
    """SQI-02 Part XIII. Every metric so far has counted guards; not one has counted the
    things being guarded. A repository can achieve perfect reach over its authored tests
    while leaving its most abusable surface entirely unprotected -- and the founding audit
    observed exactly that.

    The surface elements are the units at which a failure has a consequence somebody can
    name. For this estate that is the module packages.
    """
    mods = root / "modules"
    if not mods.is_dir():
        return []
    return sorted(
        d.name for d in mods.iterdir()
        if d.is_dir() and not d.name.startswith((".", "_")) and any(d.iterdir())
    )


def _read_all(root: Path, rels: list[str]) -> str:
    blobs: list[str] = []
    for rel in rels:
        try:
            blobs.append((root / rel).read_text(encoding="utf-8-sig", errors="replace"))
        except OSError:
            continue
    return "\n".join(blobs)


def _executed_protection_ratio(
    surface: list[str], executed_text: str
) -> tuple[float | None, list[str]]:
    """The cheap implementation of 13.4: symbol reference. Shallow, fast enough to run on
    every commit, and it produces exactly zero false negatives of the kind that matter --
    a surface element with no reference anywhere in any EXECUTED test is unambiguously
    unprotected, which is precisely what the economy-service finding was."""
    if not surface:
        return None, []
    if not executed_text:
        return 0.0, list(surface)
    unprotected = [s for s in surface if s not in executed_text]
    return (len(surface) - len(unprotected)) / len(surface), unprotected


def _classify(
    inv: Invocation, reconciled: bool, orphans: int, surface_clean: bool,
    env_qualified: bool, hermetic_stable: bool | None,
) -> str:
    """The four ordered probes of 16.7. The third fires in every repository that has never
    run this engine, and it is why the default verdict is MISLEADING GREEN and not TRUE
    GREEN: an unreconciled green carries exactly zero information about the fraction of
    authored protection it describes, and a system that defaults such a green to healthy
    has adopted the presumption that produced every finding in this corpus (16.8)."""
    # Probe 1: did the run examine a non-zero count of things?
    if not inv.executed_cases:
        return UNVERIFIED_GREEN
    # Probe 2: is the environment qualified and the result stable across hermetic runs?
    if not env_qualified or hermetic_stable is False:
        return ENVIRONMENT_DEPENDENT_GREEN
    # Probe 3: has a reconciliation been performed against an independent census?
    if not reconciled:
        return MISLEADING_GREEN
    # Probe 4: is the orphan set empty (or fully declared) and the surface sentinel clean?
    if orphans > 0 or not surface_clean or hermetic_stable is not True:
        return PARTIAL_GREEN
    return TRUE_GREEN


def reconcile(
    cwd: str | Path, hermetic_runs: int = 1, env_qualified: bool = True
) -> ReconciliationReport:
    """Subtract the executed manifest from the authored census. Never raises."""
    root = Path(cwd).resolve()
    profile = scan_repo(root)
    findings: list[str] = []

    authored = [a["path"] for a in profile.test_artifacts if a["stack"] == "python"]
    authored_n = {_norm(p) for p in authored}

    invocations = discover_invocations(root)

    stable: bool | None = None
    for inv in invocations:
        argv = _argv_for(inv.command)
        runs = []
        for _ in range(max(1, hermetic_runs)):
            rc, out = _collect(root, argv)
            runs.append((rc, out, *_parse_manifest(out)))
        rc, out, files, cases, errors, desel = runs[0]
        if hermetic_runs > 1:
            same = all(sorted(r[2]) == sorted(files) and r[3] == cases for r in runs)
            stable = same if stable is None else (stable and same)

        inv.exit_code = rc
        inv.executed_files = files
        inv.executed_cases = cases
        inv.collection_errors = errors
        inv.deselected = desel

        if rc == 0 or files:
            inv.status = OK
            # Inside the invocation's own root, which authored files yielded no case?
            roots = _roots_of(inv.command)
            if roots:
                in_root = {
                    p for p in authored_n
                    if any(p.startswith(r + "/") or p == r for r in roots)
                }
                inv.inert_in_root = sorted(in_root - set(files))
        else:
            # The runner could not be invoked, or crashed before producing a manifest. An
            # engine that computes reach as executed-over-authored would report zero, which
            # is arithmetically defensible and epistemically WRONG: zero is a measurement
            # and this is the absence of one (5.8). Reporting zero would attribute to the
            # repository a defect that belongs to the invocation.
            inv.status = BROKEN
            tail = [l for l in out.splitlines() if l.strip()]
            inv.blocker = "\n".join(tail[-8:]) if tail else f"exit {rc}, no manifest produced"

    authoritative = next((i for i in invocations if i.authoritative), None)

    # Reach is computed over the UNION of the canonical invocation set (9.6): a test
    # reached by the interface suite is not an orphan merely because the primary suite
    # does not collect it. Per-invocation reach is reported too, because a set whose union
    # covers everything while one member covers nothing has a DEAD INVOCATION that will be
    # discovered on the day somebody relies on it.
    executed_union: set[str] = set()
    for inv in invocations:
        if inv.status == OK:
            executed_union |= set(inv.executed_files)

    reached = sorted(authored_n & executed_union)
    orphaned = sorted(authored_n - executed_union)
    surprise = sorted(executed_union - authored_n)

    # The join sanity assertion (5.4). An intersection of zero is NOT a finding of total
    # orphanhood -- it is a normalization bug, and the engine says so and refuses a verdict.
    join_sanity = {
        "intersection": len(reached),
        "sane": bool(reached) or not executed_union,
        "note": "",
    }
    if executed_union and not reached:
        join_sanity["note"] = (
            "NORMALIZATION BUG: the runner executed files and none joined against the "
            "authored census. This is an instrument defect, not a finding of total "
            "orphanhood. No verdict is emitted."
        )
        findings.append(join_sanity["note"])

    # The surprise set is the instrument's SELF-AUDIT and is an error, not a curiosity
    # (5.6). Non-empty means the authored census is incomplete, which means the reach
    # denominator is too small, which inflates reach in the flattering direction. The
    # engine's own most likely failure mode is silently reporting a better reach than real.
    if surprise:
        findings.append(
            f"SURPRISE SET NON-EMPTY ({len(surprise)}): the runner executed files the "
            f"authored census never found. The discovery rule has a recall gap or the "
            f"exclusion list is over-broad. Every reach figure below is flatteringly "
            f"wrong until this is repaired. First: {surprise[:3]}"
        )

    authored_count = len(authored_n)
    measurable = bool(executed_union) and join_sanity["sane"]

    tfr = (len(reached) / authored_count) if (authored_count and measurable) else None
    orphan_ratio = (len(orphaned) / authored_count) if (authored_count and measurable) else None

    # Test Case Reach is UNKNOWN unless the authored case count has been established --
    # and establishing it requires parsing every orphaned file, which nothing in this
    # pipeline has ever done. The correct report is UNKNOWN, and the unknown IS the
    # finding: a repository that cannot state how many cases it has authored cannot
    # compute the metric that would tell it how many are protecting anything. An engine
    # that filled the gap with an estimate would manufacture the exact false confidence it
    # exists to destroy (7.6).
    tcr: float | None = None

    all_roots = {str(Path(p).parent) for p in authored_n}
    entered = {str(Path(p).parent) for p in reached}
    sar = (len(entered) / len(all_roots)) if (all_roots and measurable) else None

    silent_loss = sum(i.collection_errors + i.deselected for i in invocations if i.status == OK)
    inert = sorted({p for i in invocations for p in i.inert_in_root})
    if inert:
        findings.append(
            f"INERT-IN-ROOT ({len(inert)}): authored test files that live INSIDE a "
            f"canonical invocation's root and yield zero collected cases. They are inside "
            f"the reach boundary and protect nothing. The founding audit counted these as "
            f"reached, because it counted files in the directory rather than identities in "
            f"the manifest: {inert}"
        )

    executed_text = _read_all(root, reached)
    surface = _protection_surface(root, profile)
    epr, unprotected = _executed_protection_ratio(surface, executed_text)

    # Self-reach (5.10): the engine is a program, it lives in a file, and that file is
    # subject to the exact law it enforces -- it can be authored and never executed. A
    # report that does not contain a positive self-reach assertion is inadmissible.
    self_reached = SELF_SYMBOL in executed_text
    self_reach = {
        "engine": "modules/sqi",
        "symbol": SELF_SYMBOL,
        "reached_by": sorted(
            p for p in reached
            if SELF_SYMBOL in _read_all(root, [p])
        ),
        "reached": self_reached,
        "admissible": self_reached,
    }
    if not self_reached:
        findings.append(
            "SELF-REACH ZERO: no test reached by a canonical invocation exercises this "
            "engine. An auditor exempt from its own audit is not an auditor (SQI-02 5.10). "
            "This report is INADMISSIBLE until the engine is reached."
        )

    if authoritative and authoritative.status == BROKEN:
        findings.append(
            f"AUTHORITATIVE INVOCATION BROKEN: `{authoritative.command}` "
            f"(oracle={authoritative.oracle}) exits {authoritative.exit_code} and produces "
            f"no manifest. Reach under the estate's de facto canonical command is UNKNOWN, "
            f"not zero. Blocker (verbatim):\n{authoritative.blocker}"
        )

    surface_clean = not unprotected
    for inv in invocations:
        if inv.status == OK:
            inv.verdict = _classify(
                inv, reconciled=True, orphans=len(orphaned),
                surface_clean=surface_clean, env_qualified=env_qualified,
                hermetic_stable=stable,
            )

    ok_invs = [i for i in invocations if i.status == OK]
    if authoritative and authoritative.status == OK:
        repo_verdict = authoritative.verdict
        reach_state = "MEASURED"
    elif ok_invs:
        # The authoritative command does not run. A non-authoritative one does. Reach under
        # the canon is UNKNOWN; what the metrics below describe is a command the estate
        # does not actually run.
        repo_verdict = ok_invs[0].verdict
        reach_state = "UNKNOWN"
    else:
        repo_verdict = UNVERIFIED_GREEN
        reach_state = "UNKNOWN"

    return ReconciliationReport(
        repo=profile.repo,
        commit=profile.commit,
        authored_files=sorted(authored_n),
        authored_count=authored_count,
        invocations=invocations,
        authoritative_command=authoritative.command if authoritative else None,
        reached_files=reached,
        orphaned_files=orphaned,
        surprise_files=surprise,
        test_file_reach=tfr,
        test_case_reach=tcr,
        suite_activation_ratio=sar,
        orphaned_count=len(orphaned),
        orphaned_ratio=orphan_ratio,
        silent_collection_loss=silent_loss,
        executed_protection_ratio=epr,
        unprotected_surface=unprotected,
        signal_integrity_verdict=repo_verdict,
        ontology_verdict=VERDICT_TO_ONTOLOGY.get(repo_verdict, "UNVERIFIED"),
        authoritative_reach_state=reach_state,
        self_reach=self_reach,
        join_sanity=join_sanity,
        per_rule_hits=profile.per_rule_hits,
        uncertainty_count=profile.uncertainty_count,
        hermetic_runs=hermetic_runs,
        hermetic_stable=stable,
        findings=findings,
    )


if __name__ == "__main__":  # pragma: no cover - manual probe
    rep = reconcile(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(json.dumps(rep.to_dict(), indent=2)[:6000])
