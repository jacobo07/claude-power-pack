"""Did a rule change actually improve anything?

`compile_rules` decides whether a rule is ADMISSIBLE. Nothing decided whether
adopting one made any measured difference, so a rule's value rested on the
argument that produced it (`vault/plans/igef-2026-07-29.md`, M1b -- the single
CREATE_MISSING verdict in that audit; the other three proposed mechanisms were
already owned).

An effect claim binds a rule to something runnable. Not a description of an
improvement -- a probe whose output contains the number, and a baseline the
number is compared against. A claim nobody can run is UNMEASURED, which is a
verdict, not a gap in the report.

    python -m modules.rule_compiler.effect_harness            # measure all
    python -m modules.rule_compiler.effect_harness --coverage # who has none

Verdicts: IMPROVED / NO_CHANGE / REGRESSED / UNMEASURED. Exit 1 only on
REGRESSED -- a rule whose own probe says it made things worse is the one
result that should stop a session.

The registry is version-controlled and probes are argv lists executed without
a shell; this is a repo-local measurement tool, not an arbitrary runner.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[2]
EFFECTS_PATH = PP_ROOT / "vault" / "rule_effects" / "effects.json"
PROBE_TIMEOUT = 120

IMPROVED = "IMPROVED"
NO_CHANGE = "NO_CHANGE"
REGRESSED = "REGRESSED"
UNMEASURED = "UNMEASURED"

DOWN = "down"
UP = "up"


@dataclass(frozen=True)
class EffectClaim:
    rule_id: str
    claim: str
    probe: list
    pattern: str
    metric: str
    baseline: float
    direction: str = DOWN
    note: str = ""


@dataclass(frozen=True)
class Measurement:
    claim: EffectClaim
    verdict: str
    observed: float | None = None
    reason: str = ""

    def render(self) -> str:
        seen = "-" if self.observed is None else f"{self.observed:g}"
        line = (f"  [{self.verdict:<10}] {self.claim.rule_id}: "
                f"{self.claim.metric} {self.claim.baseline:g} -> {seen}")
        return line + (f"  ({self.reason})" if self.reason else "")


def _registry_path(path: Path | None) -> Path:
    """Resolved per call, never bound as a default: a module constant captured
    in a signature is fixed at import and cannot be pointed elsewhere."""
    return Path(path) if path is not None else EFFECTS_PATH


def load_claims(path: Path | None = None) -> list:
    try:
        raw = json.loads(_registry_path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return []
    rows = raw.get("effects", []) if isinstance(raw, dict) else raw
    claims = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            claims.append(EffectClaim(
                rule_id=str(row["rule_id"]),
                claim=str(row.get("claim", "")),
                probe=list(row["probe"]),
                pattern=str(row["pattern"]),
                metric=str(row.get("metric", "value")),
                baseline=float(row["baseline"]),
                direction=str(row.get("direction", DOWN)),
                note=str(row.get("note", "")),
            ))
        except (KeyError, TypeError, ValueError):
            continue  # a malformed claim is reported as absent, never as a pass
    return claims


def run_probe(claim: EffectClaim, cwd: Path) -> tuple:
    """(stdout+stderr, reason|None). A probe that cannot run is not a failure
    of the rule -- it is an absence of evidence, and says so."""
    argv = [sys.executable if a == "python" else a for a in claim.probe]
    try:
        proc = subprocess.run(argv, cwd=str(cwd), capture_output=True,
                              text=True, timeout=PROBE_TIMEOUT, shell=False)
    except (OSError, subprocess.SubprocessError) as e:
        return "", f"probe did not run: {e}"
    return (proc.stdout or "") + (proc.stderr or ""), None


def extract(pattern: str, text: str):
    try:
        m = re.search(pattern, text)
    except re.error as e:
        return None, f"bad pattern: {e}"
    if not m or not m.groups():
        return None, "metric not present in probe output"
    try:
        return float(m.group(1)), None
    except ValueError:
        return None, f"metric is not numeric: {m.group(1)!r}"


def judge(baseline: float, observed: float, direction: str) -> str:
    if observed == baseline:
        return NO_CHANGE
    better = observed < baseline if direction == DOWN else observed > baseline
    return IMPROVED if better else REGRESSED


def measure(claim: EffectClaim, cwd: Path = PP_ROOT) -> Measurement:
    out, reason = run_probe(claim, cwd)
    if reason:
        return Measurement(claim, UNMEASURED, None, reason)
    observed, reason = extract(claim.pattern, out)
    if observed is None:
        return Measurement(claim, UNMEASURED, None, reason)
    return Measurement(claim, judge(claim.baseline, observed, claim.direction),
                       observed, claim.note)


def measure_all(path: Path | None = None, cwd: Path = PP_ROOT) -> list:
    return [measure(c, cwd) for c in load_claims(path)]


def coverage(path: Path | None = None) -> dict:
    """Which rules carry an effect claim and which carry none.

    The corpus count is best-effort: if the compiler cannot run, the claimed
    count still stands on its own and `corpus` reports None rather than 0,
    because 0 would read as "no rules exist"."""
    claimed = {c.rule_id for c in load_claims(path)}
    corpus = None
    try:
        from .compiler import compile_rules
        corpus = {r.rule_id for r in compile_rules().valid}
    except Exception:
        corpus = None
    return {
        "claimed": sorted(claimed),
        "corpus_size": None if corpus is None else len(corpus),
        "unmeasured": None if corpus is None else sorted(corpus - claimed),
        # A claim naming a rule the corpus does not contain must be visible.
        # Without this the report shows "1 claimed" beside "147 unmeasured of
        # 147" and the two cannot both be true -- a ledger that quietly
        # overstates its own coverage.
        "unknown_rule_ids": None if corpus is None else sorted(claimed - corpus),
    }


def main(argv: list | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--coverage" in args:
        cov = coverage()
        size = cov["corpus_size"]
        print(f"rules with a measured effect claim: {len(cov['claimed'])}")
        for rid in cov["claimed"]:
            print(f"  [CLAIMED] {rid}")
        if size is None:
            print("corpus size: UNKNOWN (compiler unavailable) -- the claimed "
                  "set above is still exact")
            return 0
        for rid in cov["unknown_rule_ids"]:
            print(f"  [NOT-IN-CORPUS] {rid}: measured, but no compiled rule "
                  f"carries this id -- the effect is real, the rule is not sealed")
        print(f"corpus: {size} valid rule(s); "
              f"{len(cov['unmeasured'])} carry no effect claim; "
              f"{size - len(cov['unmeasured'])} carry one")
        return 0

    results = measure_all()
    if not results:
        print("no effect claims registered "
              f"({EFFECTS_PATH.relative_to(PP_ROOT)})")
        return 0
    print(f"measuring {len(results)} effect claim(s)")
    for m in results:
        print(m.render())
    counts = {v: sum(1 for m in results if m.verdict == v)
              for v in (IMPROVED, NO_CHANGE, REGRESSED, UNMEASURED)}
    print("RULE_EFFECTS " + "  ".join(f"{k}={v}" for k, v in counts.items()))
    return 1 if counts[REGRESSED] else 0


if __name__ == "__main__":
    raise SystemExit(main())
