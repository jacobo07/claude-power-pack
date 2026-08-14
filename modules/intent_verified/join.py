"""Join declared criteria to the evidence the repo can actually produce.

Two tiers, deliberately separate:

  resolve  static, milliseconds -- does any executable file emit this id, and
           is that file reachable from the standing gate?
  observe  bounded subprocess -- run the owner and read its output for this
           id's result.

`resolve` alone proves an owner EXISTS. That is the weaker statement the audit
found everywhere else in the repo, so it is never reported as satisfaction.
Only `observe` produces evidence.
"""
from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .criteria import VID, Criterion

SKIP_DIRS = ("__pycache__", "_knowledge_graph", "node_modules", ".git")
OBSERVE_TIMEOUT_S = 180


class Reach(str, Enum):
    REACHABLE = "REACHABLE"        # emitted by a file the standing gate runs
    UNJOINED = "UNJOINED"          # emitted, but no standing gate reaches it
    UNVERIFIABLE = "UNVERIFIABLE"  # emitted by nothing executable


class Observed(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ABSENT = "ABSENT"        # the owner ran and never emitted the id
    NOT_RUN = "NOT_RUN"      # the observe tier was not applied here
    ERROR = "ERROR"          # the owner could not be run to completion


@dataclass
class CriterionResult:
    criterion: Criterion
    reach: Reach
    owners: tuple[str, ...] = ()
    observed: Observed = Observed.NOT_RUN
    evidence: str = ""

    @property
    def satisfied(self) -> bool:
        return self.observed is Observed.PASS

    def as_dict(self) -> dict:
        return {**self.criterion.as_dict(), "reach": self.reach.value,
                "owners": list(self.owners), "observed": self.observed.value,
                "evidence": self.evidence}


def _skip(p: Path) -> bool:
    return any(part in SKIP_DIRS for part in p.parts)


def emitters(root: Path) -> dict[str, tuple[str, ...]]:
    """Map every V-id the repo emits to the executable files emitting it."""
    index: dict[str, list[str]] = {}
    for pattern in ("*.py", "*.js"):
        for p in root.rglob(pattern):
            if _skip(p):
                continue
            try:
                text = p.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                continue
            for vid in set(VID.findall(text)):
                index.setdefault(vid, []).append(str(p.relative_to(root)))
    return {k: tuple(sorted(v)) for k, v in index.items()}


def standing_gate_targets(root: Path) -> set[str]:
    """The files `verify_spp` runs, parsed from its own row table.

    Read from the source rather than declared here, so a row added tomorrow
    counts tomorrow without editing this module.
    """
    src = root / "tools" / "verify_spp.py"
    try:
        text = src.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return set()
    head, sep, rest = text.partition("rows_spec = [")
    if not sep:
        return set()
    body = rest.split("\n    ]", 1)[0]
    return set(re.findall(r'"([\w.\-]+\.(?:py|js))"', body))


def resolve(criteria: list[Criterion], root: Path,
            index: dict[str, tuple[str, ...]] | None = None,
            reached: set[str] | None = None) -> list[CriterionResult]:
    """Static tier. No subprocess, no evidence -- only reachability."""
    index = emitters(root) if index is None else index
    reached = standing_gate_targets(root) if reached is None else reached
    out: list[CriterionResult] = []
    for c in criteria:
        owners = index.get(c.id, ())
        if not owners:
            out.append(CriterionResult(c, Reach.UNVERIFIABLE))
            continue
        hit = any(Path(o).name in reached for o in owners)
        out.append(CriterionResult(
            c, Reach.REACHABLE if hit else Reach.UNJOINED, owners))
    return out


# Two layouts, both in live use in this repo. Measured 2026-08-14: a
# verdict-first-only parser reported 9 ABSENT against
# modules/code-review/test_v_block.py, which emits a table with the id first
# and the verdict in the last column. The parser's vocabulary was deciding the
# answer, and an unrecognised layout read as "never emitted".
_VERDICT_FIRST = re.compile(
    r"^\s*\[?\s*(PASS|OK|FAIL|ERROR)\s*\]?[\s:]+(V-[A-Z0-9][A-Z0-9_\-]*)",
    re.I)
_ID_FIRST = re.compile(
    r"^\s*\|?\s*`?(V-[A-Z0-9][A-Z0-9_\-]*)`?\b.*?\b(PASS|OK|FAIL|ERROR)\s*\|?\s*$",
    re.I)


def _line_result(line: str) -> tuple[str, str] | None:
    m = _VERDICT_FIRST.match(line)
    if m:
        return m.group(2), m.group(1).upper()
    m = _ID_FIRST.match(line)
    if m:
        return m.group(1), m.group(2).upper()
    return None


def parse_results(stdout: str) -> dict[str, tuple[str, str]]:
    """Map every V-id in a run's output to (verdict, the line that said so).

    A FAIL anywhere for an id wins over a PASS: a gate that reports both did
    not pass, and taking the last line would make order decide correctness.
    """
    found: dict[str, tuple[str, str]] = {}
    for line in (stdout or "").splitlines():
        hit = _line_result(line)
        if hit is None:
            continue
        vid, raw = hit
        verdict = "PASS" if raw in ("PASS", "OK") else "FAIL"
        prior = found.get(vid)
        if prior is None or (prior[0] == "PASS" and verdict == "FAIL"):
            found[vid] = (verdict, line.strip())
    return found


# Only a verifier is ever executed. An emitter is any file mentioning the id,
# and some of those mutate the repo (`tools/normalize_paths.py` names a V-id
# and rewrites paths when run without --check). A gate that runs arbitrary
# repo files to collect evidence is a worse defect than the one it measures.
RUNNABLE = re.compile(r"(?:^|[\\/])(?:test_|verify_)[^\\/]*\.(?:py|js)$")


def is_runnable(owner: str) -> bool:
    return bool(RUNNABLE.search(owner))


def run_owner(owner: str, root: Path,
              timeout: int = OBSERVE_TIMEOUT_S) -> tuple[str, str]:
    """Run one owner file. Returns (stdout+stderr, error) -- error is empty
    when the process ran to completion, whatever its exit code."""
    path = root / owner
    if not path.is_file():
        return "", f"owner missing on disk: {owner}"
    argv = ([sys.executable, str(path)] if path.suffix == ".py"
            else ["node", str(path)])
    try:
        cp = subprocess.run(argv, cwd=str(root), capture_output=True,
                            text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return "", f"owner exceeded {timeout}s: {owner}"
    except OSError as exc:
        return "", f"owner could not start ({type(exc).__name__}): {exc}"
    return (cp.stdout or "") + (cp.stderr or ""), ""


def observe(results: list[CriterionResult], root: Path,
            timeout: int = OBSERVE_TIMEOUT_S) -> list[CriterionResult]:
    """Dynamic tier. Each owner runs at most once; its output is reused.

    A criterion may have several emitters -- `V-TIMING` has seven. Fixing on
    one and reporting ABSENT when it stays quiet measures the choice, not the
    criterion, so every runnable owner is consulted until one produces a
    verdict. Only then is the criterion genuinely unobserved.

    Mutates and returns the results given. Criteria with no owner keep
    NOT_RUN -- there is nothing to run, which `resolve` already recorded.
    """
    cache: dict[str, tuple[dict[str, tuple[str, str]], str]] = {}

    def _output(owner: str) -> tuple[dict[str, tuple[str, str]], str]:
        if owner not in cache:
            out, err = run_owner(owner, root, timeout)
            cache[owner] = ({} if err else parse_results(out), err)
        return cache[owner]

    for r in results:
        runnable = [o for o in r.owners if is_runnable(o)]
        if not runnable:
            if r.owners:
                r.observed = Observed.ABSENT
                r.evidence = (f"no verifier emits {r.criterion.id}; named "
                              f"only by {r.owners[0]}, which is not run")
            continue
        errors: list[str] = []
        for owner in runnable:
            parsed, err = _output(owner)
            if err:
                errors.append(err)
                continue
            hit = parsed.get(r.criterion.id)
            if hit is None:
                continue
            r.observed = (Observed.PASS if hit[0] == "PASS"
                          else Observed.FAIL)
            r.evidence = f"{owner}: {hit[1]}"
            break
        else:
            if errors and len(errors) == len(runnable):
                r.observed, r.evidence = Observed.ERROR, errors[0]
            else:
                r.observed = Observed.ABSENT
                r.evidence = (f"{len(runnable)} verifier(s) ran and none "
                              f"emitted {r.criterion.id}: "
                              f"{', '.join(runnable)}")
    return results


__all__ = ["Reach", "Observed", "CriterionResult", "emitters",
           "standing_gate_targets", "resolve", "parse_results", "run_owner",
           "observe", "OBSERVE_TIMEOUT_S"]
