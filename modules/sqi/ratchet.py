"""SQI Baseline Ratchet -- enforcement for Ley XV, "every generation must raise the baseline".

`baseline_guardian` is asymmetric on purpose: an increase requires nothing, a decrease
fails the build. It records that the bar was met and ratchets the RECORDED figure upward
when the repository improves. Nothing decides that a bar has stopped discriminating and
that a harder one is owed. That is the whole of the gap this module closes.

Two objects, and the order between them is the safety property:

    is_saturated(...)  -> SATURATED | NOT_SATURATED | INSUFFICIENT_HISTORY | UNMEASURABLE
    propose(...)       -> escalation candidates, ONLY when the verdict is SATURATED

PROPOSE-ONLY. Nothing here writes a baseline, edits a threshold, or fails a build. A gate
empowered to raise its own bar is a gate grading itself, which is the defect `sqi_scs_c93`
was sealed to prevent. The output is a candidate list for a human; adoption is a separate,
attributed act, exactly as `baseline_guardian.check(accept=True)` already is.

Three traps this module is built around, each a sealed estate lesson:

1. Saturation is NOT staleness. The live baseline has been unchanged since 2026-07-12 at
   `test_file_reach` 2.97 %. A detector keyed on "unchanged for N observations" reports
   saturation there and proposes a harder bar for a benchmark whose current bar is met by
   3 % of the authored surface. Ceiling-reached is a required conjunct, never inferred
   from stability (Pathology 1, benchmark theatre).

2. A ratio cannot carry a gate alone (`feedback_never_gate_on_a_ratio`). `reach` rises when
   the denominator shrinks, so the ceiling test reads the absolute counts beside it.

3. An empty conjunction is vacuously true (`feedback_provider_score_to_hard_verdict`:
   beware `all([])`). Every predicate here requires a non-empty evidence set before it may
   return True, so an absence of measurements resolves to INSUFFICIENT_HISTORY -- a
   verdict -- and never to SATURATED.

Fail-open ABSOLUTE: no function raises. An unreadable ledger yields UNMEASURABLE, which is
not a pass and licenses no proposal.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --- verdicts ---------------------------------------------------------------------------
SATURATED = "RATCHET_SATURATED"
NOT_SATURATED = "RATCHET_NOT_SATURATED"
INSUFFICIENT_HISTORY = "RATCHET_INSUFFICIENT_HISTORY"
UNMEASURABLE = "RATCHET_UNMEASURABLE"

LICENSES_PROPOSAL = {SATURATED}

LEDGER_VERSION = 1

# --- thresholds -------------------------------------------------------------------------
# Independent observations required before stability means anything. Two points are a line;
# three are the smallest set in which a line can be contradicted.
MIN_OBSERVATIONS = 3

# A ceiling is a ceiling only if the population underneath it is non-trivial. 100 % of three
# cases is not a saturated benchmark, it is a small one (Pathology 1).
MIN_EXECUTED_CASES = 50
MIN_AUTHORED_FILES = 20

# Reach at or above this is "the bar is being met". Deliberately short of 1.0: a benchmark
# does not need to be perfect to be saturated, it needs to have stopped discriminating.
REACH_CEILING = 0.95

# Float representation only -- never widen this to quiet a signal (guardian 12.8).
EPSILON = 1e-9


@dataclass
class Observation:
    """One recorded guardian outcome. The ratchet's own producer; the guardian keeps no
    history, and a derivative cannot be taken from a single point."""

    recorded: str
    commit: str | None
    environment_key: str | None
    verdict: str
    executed_total: int
    authored_count: int
    test_file_reach: float | None
    root_count: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Candidate:
    """One escalation proposal. Every field is required; a candidate without an instrument
    is prose, and prose cannot raise a bar."""

    axis: str
    observed: Any
    proposed: Any
    rationale: str
    instrument: str          # the command or module that would MEASURE the new bar
    reversible: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RatchetVerdict:
    verdict: str
    reasons: list[str] = field(default_factory=list)
    unmet: list[str] = field(default_factory=list)
    observations_used: int = 0
    candidates: list[Candidate] = field(default_factory=list)
    summary: str = ""
    error: str | None = None

    @property
    def licenses_proposal(self) -> bool:
        return self.verdict in LICENSES_PROPOSAL

    def to_dict(self) -> dict:
        d = asdict(self)
        d["candidates"] = [c.to_dict() for c in self.candidates]
        d["licenses_proposal"] = self.licenses_proposal
        return d


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_ledger_path(repo: Path) -> Path:
    """Overridable. A gate writing to a global path is not hermetic and fails its own second
    run (`feedback_hermetic_test_global_writes_time_window`)."""
    env = os.environ.get("SQI_RATCHET_LEDGER")
    if env:
        return Path(env)
    return repo / "vault" / "sqi_ratchet" / "observations.jsonl"


# --- ledger -----------------------------------------------------------------------------

def record(
    baseline: dict,
    verdict: str,
    *,
    repo: Path | None = None,
    ledger_path: Path | None = None,
) -> bool:
    """Append one observation. This is the producer the estate lacked: `decision_review`'s
    calibrator is dead by starvation for exactly this reason -- a consumer with no producer
    (`feedback_orphan_field_dead_recovery_path`). Returns False on any failure; never raises.
    """
    try:
        repo = Path(repo) if repo else Path.cwd()
        path = Path(ledger_path) if ledger_path else default_ledger_path(repo)
        roots = baseline.get("roots") or {}
        obs = Observation(
            recorded=_now(),
            commit=baseline.get("commit"),
            environment_key=baseline.get("environment_key"),
            verdict=str(verdict),
            executed_total=sum(
                int(r.get("executed_cases") or 0)
                for r in roots.values()
                if isinstance(r, dict)
            ),
            authored_count=int(baseline.get("authored_count") or 0),
            test_file_reach=baseline.get("test_file_reach"),
            root_count=len(roots),
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"v": LEDGER_VERSION, **obs.to_dict()}) + "\n")
        return True
    except Exception:
        return False


def load_observations(
    *,
    repo: Path | None = None,
    ledger_path: Path | None = None,
    environment_key: str | None = None,
) -> tuple[list[Observation], str | None]:
    """Read the ledger. Observations under a different environment key are DROPPED, not
    compared: two measurements of two different systems are not a series (guardian 12.4)."""
    try:
        repo = Path(repo) if repo else Path.cwd()
        path = Path(ledger_path) if ledger_path else default_ledger_path(repo)
        if not path.is_file():
            return [], None
        out: list[Observation] = []
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except ValueError:
                continue  # one corrupt line must not disarm the instrument
            if not isinstance(d, dict):
                continue
            if environment_key and d.get("environment_key") != environment_key:
                continue
            try:
                out.append(
                    Observation(
                        recorded=str(d.get("recorded") or ""),
                        commit=d.get("commit"),
                        environment_key=d.get("environment_key"),
                        verdict=str(d.get("verdict") or ""),
                        executed_total=int(d.get("executed_total") or 0),
                        authored_count=int(d.get("authored_count") or 0),
                        test_file_reach=d.get("test_file_reach"),
                        root_count=int(d.get("root_count") or 0),
                    )
                )
            except (TypeError, ValueError):
                continue
        return out, None
    except Exception as exc:
        return [], f"ledger unreadable: {exc}"


# --- saturation -------------------------------------------------------------------------

def is_saturated(
    baseline: dict,
    *,
    repo: Path | None = None,
    ledger_path: Path | None = None,
    min_observations: int = MIN_OBSERVATIONS,
) -> RatchetVerdict:
    """Decide whether the current bar has stopped discriminating.

    Five conjuncts, every one of which must be independently satisfied by a non-empty
    measurement. The conjunction is explicit rather than a score: a composite score mapped
    onto a hard verdict is the defect sealed in `feedback_provider_score_to_hard_verdict`.
    """
    try:
        if not isinstance(baseline, dict):
            return RatchetVerdict(
                verdict=UNMEASURABLE,
                error="baseline is not a mapping",
                summary=f"{UNMEASURABLE}: no baseline to judge. Not a pass.",
            )

        env = baseline.get("environment_key")
        obs, err = load_observations(
            repo=repo, ledger_path=ledger_path, environment_key=env
        )
        if err:
            return RatchetVerdict(
                verdict=UNMEASURABLE,
                error=err,
                summary=f"{UNMEASURABLE}: {err}. No claim about saturation is licensed.",
            )

        if len(obs) < min_observations:
            return RatchetVerdict(
                verdict=INSUFFICIENT_HISTORY,
                observations_used=len(obs),
                unmet=[f"observations {len(obs)} < {min_observations}"],
                summary=(
                    f"{INSUFFICIENT_HISTORY}: {len(obs)} observation(s) under env {env!r}, "
                    f"{min_observations} required. A derivative needs a series. Run the "
                    f"guardian again to accumulate history."
                ),
            )

        window = obs[-min_observations:]
        roots = baseline.get("roots") or {}
        executed = sum(
            int(r.get("executed_cases") or 0)
            for r in roots.values()
            if isinstance(r, dict)
        )
        authored = int(baseline.get("authored_count") or 0)
        reach = baseline.get("test_file_reach")

        reasons: list[str] = []
        unmet: list[str] = []

        # 1. Ceiling reached. The RATIO is the headline, so the ABSOLUTES are read beside it:
        #    reach rises when the denominator shrinks (`feedback_never_gate_on_a_ratio`).
        if reach is None:
            unmet.append("test_file_reach unmeasured")
        elif reach + EPSILON < REACH_CEILING:
            unmet.append(
                f"reach {reach * 100:.2f}% < ceiling {REACH_CEILING * 100:.0f}% "
                f"-- the current bar is not met, so it cannot be saturated"
            )
        else:
            reasons.append(f"reach {reach * 100:.2f}% >= {REACH_CEILING * 100:.0f}%")

        # 2. Non-trivial population. 100 % of three cases is a small benchmark, not a
        #    saturated one.
        if executed < MIN_EXECUTED_CASES:
            unmet.append(f"executed {executed} < {MIN_EXECUTED_CASES}")
        else:
            reasons.append(f"executed {executed} >= {MIN_EXECUTED_CASES}")

        if authored < MIN_AUTHORED_FILES:
            unmet.append(f"authored {authored} < {MIN_AUTHORED_FILES}")
        else:
            reasons.append(f"authored {authored} >= {MIN_AUTHORED_FILES}")

        # 3. Stable across the window -- no movement in the absolutes.
        exec_series = [o.executed_total for o in window]
        if len(set(exec_series)) == 1:
            reasons.append(f"executed stable across {len(window)} observations")
        else:
            unmet.append(
                f"executed still moving across the window {exec_series} "
                f"-- a moving benchmark is still discriminating"
            )

        # 4. No regression inside the window. A window containing a failure is a window in
        #    which the bar demonstrably still bites.
        failed = [o.verdict for o in window if "REGRESSION" in o.verdict.upper()]
        if failed:
            unmet.append(f"{len(failed)} regression verdict(s) inside the window")
        else:
            reasons.append("no regression inside the window")

        # 5. Root coverage did not shrink -- an entire root can die while a sibling absorbs
        #    the total (guardian 12.3).
        root_series = [o.root_count for o in window]
        if root_series and min(root_series) >= root_series[0] and len(roots) >= root_series[0]:
            reasons.append(f"root count held at {len(roots)}")
        else:
            unmet.append(f"root count moved {root_series} -> {len(roots)}")

        if unmet:
            return RatchetVerdict(
                verdict=NOT_SATURATED,
                reasons=reasons,
                unmet=unmet,
                observations_used=len(window),
                summary=(
                    f"{NOT_SATURATED}: {len(unmet)} condition(s) unmet -- {unmet[0]}. "
                    f"The bar still discriminates; raising it now would be benchmark "
                    f"inflation, not evolution."
                ),
            )

        return RatchetVerdict(
            verdict=SATURATED,
            reasons=reasons,
            unmet=[],
            observations_used=len(window),
            summary=(
                f"{SATURATED}: all 5 conditions met across {len(window)} observations "
                f"(reach {(reach or 0) * 100:.2f}%, {executed} executed, {authored} "
                f"authored). The bar has stopped discriminating. Ley XV is owed a harder one."
            ),
        )
    except Exception as exc:  # fail-open ABSOLUTE
        return RatchetVerdict(
            verdict=UNMEASURABLE,
            error=str(exc),
            summary=f"{UNMEASURABLE}: {exc}. Not a pass.",
        )


# --- escalation proposal ------------------------------------------------------------------

def propose(baseline: dict, verdict: RatchetVerdict) -> list[Candidate]:
    """Emit escalation candidates. ONLY when the verdict licenses it.

    Each candidate names the axis, the observed value, the proposed bar, the evidence that
    licensed it, and -- the field that keeps this honest -- the INSTRUMENT that would
    measure the new bar. An axis PP cannot measure yields no candidate, because a bar
    nothing can score is not a harder benchmark, it is an aspiration.
    """
    if not verdict.licenses_proposal:
        return []
    try:
        roots = baseline.get("roots") or {}
        executed = sum(
            int(r.get("executed_cases") or 0)
            for r in roots.values()
            if isinstance(r, dict)
        )
        authored = int(baseline.get("authored_count") or 0)
        reach = baseline.get("test_file_reach") or 0.0
        oracles = {
            str(r.get("oracle") or "unknown")
            for r in roots.values()
            if isinstance(r, dict)
        }

        out: list[Candidate] = []

        # Axis: reach. The denominator, never the ratio -- name the files.
        if reach < 1.0:
            out.append(
                Candidate(
                    axis="reach",
                    observed=round(reach, 4),
                    proposed=1.0,
                    rationale=(
                        f"{authored - len(_executed_identities(roots))} authored file(s) are "
                        f"never reached by any invocation. The bar is met without them."
                    ),
                    instrument="python tools/run_sqi.py  (test_file_reach)",
                )
            )

        # Axis: population. A saturated benchmark grows by adding cases, not by relaxing.
        out.append(
            Candidate(
                axis="population",
                observed=executed,
                proposed=int(executed * 1.25),
                rationale="a saturated case set discriminates again once widened by 25%",
                instrument="python tools/run_sqi.py  (executed_cases per root)",
            )
        )

        # Axis: oracle strength. `documentation` is the weakest oracle SQI recognises.
        if oracles and oracles <= {"documentation", "unknown"}:
            out.append(
                Candidate(
                    axis="oracle_strength",
                    observed=sorted(oracles),
                    proposed="assertion",
                    rationale=(
                        "every root is scored by the weakest oracle; a stronger oracle "
                        "re-discriminates without adding a single case"
                    ),
                    instrument="modules/sqi/repo_reality_scanner.py  (oracle classification)",
                )
            )

        # Axis: mutation resistance. The existing engine, pointed at a saturated target.
        out.append(
            Candidate(
                axis="mutation_resistance",
                observed="unmeasured at this bar",
                proposed="surviving-mutant rate reported per root",
                rationale=(
                    "a suite that passes every case but kills no mutant is saturated "
                    "against its cases and empty against its purpose"
                ),
                instrument="modules/sqi/weakening_detectors.py  (mutation_probe)",
            )
        )

        # Axis: adversariality. Existing protocol, unused at this bar.
        out.append(
            Candidate(
                axis="adversariality",
                observed="unmeasured at this bar",
                proposed="one red-team pass recorded against the saturated root",
                rationale="a bar nobody has attacked has not been shown to resist attack",
                instrument="modules/sqi/redteam_protocol.py",
            )
        )

        # Axis: environment diversity. One env key is one system, not a matrix.
        if baseline.get("environment_key"):
            out.append(
                Candidate(
                    axis="environment_diversity",
                    observed=1,
                    proposed=2,
                    rationale=(
                        "the bar is met under exactly one qualified environment; a second "
                        "makes compatibility a measured property rather than an assumption"
                    ),
                    instrument="modules/sqi/environment_qualifier.py",
                )
            )

        return out
    except Exception:
        return []  # fail-open: a broken proposer proposes nothing, it never raises


def _executed_identities(roots: dict) -> set[str]:
    out: set[str] = set()
    for r in roots.values():
        if isinstance(r, dict):
            for f in r.get("executed_files") or []:
                out.add(str(f))
    return out


def evaluate(
    baseline: dict,
    *,
    repo: Path | None = None,
    ledger_path: Path | None = None,
    min_observations: int = MIN_OBSERVATIONS,
) -> RatchetVerdict:
    """Saturation, then proposal, in that order. The order IS the safety property."""
    v = is_saturated(
        baseline, repo=repo, ledger_path=ledger_path, min_observations=min_observations
    )
    v.candidates = propose(baseline, v)
    return v
