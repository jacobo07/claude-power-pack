"""Would the rule actually have stopped the incident that produced it?

`effect_harness` answers "did adopting this rule move a metric?" -- a forward,
aggregate question. It cannot answer the backward, specific one the estate keeps
asking in prose and never measures: given incident I, and rule R written because
of I, would R have fired on I?

That question has been answered from memory every time a Hard Rule was sealed.
`vault/plans/igef-2026-07-29.md` struck three of four proposed mechanisms, and the
one it kept was effect measurement -- the counterfactual half was never built, so
"this rule would have prevented that" has remained an assertion by the party who
wrote the rule.

A claim binds three things: a rule id, a RECORDED incident, and a detector that
can be RUN against that incident's preserved input.

    WOULD_BLOCK      the detector fired on the incident input
    WOULD_NOT_BLOCK  it did not -- the rule does not cover its own origin
    UNMEASURABLE     no detector, or it could not run. A verdict, never a pass.

WOULD_NOT_BLOCK is the finding worth having: a rule that does not fire on the
incident that produced it is governance prose, and Ley VI ("no governance without
enforcement") is unmet for that rule regardless of how well it reads.

    python -m modules.rule_compiler.counterfactual
    python -m modules.rule_compiler.counterfactual --coverage

Exit 1 only on WOULD_NOT_BLOCK: a rule whose own origin escapes it is the one
result that should stop a session. UNMEASURABLE never fails the build -- absence
of evidence is not evidence of failure.

Probes are argv lists executed without a shell, from a version-controlled
registry; this is a repo-local measurement tool, not an arbitrary runner.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]
CLAIMS_PATH = PP_ROOT / "vault" / "rule_effects" / "counterfactuals.json"
PROBE_TIMEOUT = 120

WOULD_BLOCK = "WOULD_BLOCK"
WOULD_NOT_BLOCK = "WOULD_NOT_BLOCK"
UNMEASURABLE = "UNMEASURABLE"

FAILING = {WOULD_NOT_BLOCK}


@dataclass(frozen=True)
class CounterfactualClaim:
    rule_id: str
    incident_id: str          # the sealed incident this rule was written for
    incident_input: str       # the preserved trigger, replayed verbatim
    probe: list               # argv; receives incident_input on stdin
    fires_pattern: str = ""   # if set, the detector "fired" when this matches stdout
    fires_on_exit: int | None = None   # else: it fired when exit code == this
    note: str = ""


@dataclass(frozen=True)
class Counterfactual:
    claim: CounterfactualClaim
    verdict: str
    evidence: str = ""
    reason: str = ""

    def render(self) -> str:
        line = (f"  [{self.verdict:<15}] {self.claim.rule_id} vs "
                f"{self.claim.incident_id}")
        return line + (f"  ({self.reason})" if self.reason else "")


def _claims_path(path: Path | None) -> Path:
    """Resolved per call, never bound as a default: a constant captured in a
    signature is fixed at import and cannot be pointed elsewhere."""
    return Path(path) if path is not None else CLAIMS_PATH


def load_claims(path: Path | None = None) -> list:
    try:
        raw = json.loads(_claims_path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return []
    rows = raw.get("counterfactuals", []) if isinstance(raw, dict) else raw
    out = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            fires_exit = row.get("fires_on_exit")
            out.append(CounterfactualClaim(
                rule_id=str(row["rule_id"]),
                incident_id=str(row["incident_id"]),
                incident_input=str(row["incident_input"]),
                probe=list(row["probe"]),
                fires_pattern=str(row.get("fires_pattern", "")),
                fires_on_exit=None if fires_exit is None else int(fires_exit),
                note=str(row.get("note", "")),
            ))
        except (KeyError, TypeError, ValueError):
            continue  # a malformed claim is reported absent, never as a pass
    return out


def run_probe(claim: CounterfactualClaim, cwd: Path) -> tuple:
    """(stdout+stderr, exit_code, reason|None)."""
    argv = [sys.executable if a == "python" else a for a in claim.probe]
    try:
        proc = subprocess.run(
            argv, cwd=str(cwd), input=claim.incident_input,
            capture_output=True, text=True, timeout=PROBE_TIMEOUT, shell=False,
        )
    except (OSError, subprocess.SubprocessError) as e:
        return "", None, f"detector did not run: {e}"
    return (proc.stdout or "") + (proc.stderr or ""), proc.returncode, None


def judge(claim: CounterfactualClaim, out: str, code: int | None) -> tuple:
    """(verdict, evidence, reason). A claim declaring neither a pattern nor an
    exit code cannot be judged -- and saying so is the honest output, because a
    default of 'fired' would let every unspecified claim read as a success."""
    if claim.fires_pattern:
        try:
            m = re.search(claim.fires_pattern, out)
        except re.error as e:
            return UNMEASURABLE, "", f"bad pattern: {e}"
        if m:
            return WOULD_BLOCK, m.group(0)[:200], claim.note
        return WOULD_NOT_BLOCK, "", (
            "the detector ran and did not fire on the incident that produced "
            "this rule"
        )
    if claim.fires_on_exit is not None:
        if code is None:
            return UNMEASURABLE, "", "no exit code captured"
        if code == claim.fires_on_exit:
            return WOULD_BLOCK, f"exit={code}", claim.note
        return WOULD_NOT_BLOCK, f"exit={code}", (
            f"detector exited {code}, expected {claim.fires_on_exit} to signal a block"
        )
    return UNMEASURABLE, "", (
        "claim declares neither fires_pattern nor fires_on_exit; nothing to judge"
    )


def measure(claim: CounterfactualClaim, cwd: Path = PP_ROOT) -> Counterfactual:
    out, code, reason = run_probe(claim, cwd)
    if reason:
        return Counterfactual(claim, UNMEASURABLE, "", reason)
    verdict, evidence, note = judge(claim, out, code)
    return Counterfactual(claim, verdict, evidence, note)


def measure_all(path: Path | None = None, cwd: Path = PP_ROOT) -> list:
    return [measure(c, cwd) for c in load_claims(path)]


def coverage(path: Path | None = None) -> dict:
    """Which rules carry a counterfactual and which carry none.

    `corpus` is None rather than 0 when the compiler cannot run, because 0 would
    read as 'no rules exist' -- the same honesty the effect harness applies."""
    claimed = {c.rule_id for c in load_claims(path)}
    try:
        from .compiler import compile_rules
        corpus = {r.rule_id for r in compile_rules().valid}
    except Exception:
        corpus = None
    return {
        "claimed": sorted(claimed),
        "corpus_size": None if corpus is None else len(corpus),
        "uncovered": None if corpus is None else sorted(corpus - claimed),
        "unknown_rule_ids": None if corpus is None else sorted(claimed - corpus),
    }


def main(argv: list | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--coverage" in args:
        cov = coverage()
        size = cov["corpus_size"]
        print(f"rules with a counterfactual claim: {len(cov['claimed'])}")
        for rid in cov["claimed"]:
            print(f"  [CLAIMED] {rid}")
        if size is None:
            print("corpus size: UNKNOWN (compiler unavailable) -- the claimed "
                  "set above is still exact")
            return 0
        for rid in cov["unknown_rule_ids"]:
            print(f"  [NOT-IN-CORPUS] {rid}: claimed, but no compiled rule "
                  f"carries this id")
        print(f"corpus: {size} valid rule(s); {len(cov['uncovered'])} have never "
              f"been replayed against their own incident")
        return 0

    results = measure_all()
    if not results:
        print(f"no counterfactual claims registered "
              f"({CLAIMS_PATH.relative_to(PP_ROOT)})")
        return 0
    print(f"replaying {len(results)} incident(s) against their rule")
    for r in results:
        print(r.render())
    counts = {v: sum(1 for r in results if r.verdict == v)
              for v in (WOULD_BLOCK, WOULD_NOT_BLOCK, UNMEASURABLE)}
    print("RULE_COUNTERFACTUALS " + "  ".join(f"{k}={v}" for k, v in counts.items()))
    return 1 if counts[WOULD_NOT_BLOCK] else 0


if __name__ == "__main__":
    raise SystemExit(main())
