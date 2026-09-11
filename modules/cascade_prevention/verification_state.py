"""Verification provenance -- the input two Hard Rules were starving for.

HR-CASCADE-001 refuses a deploy when the relevant tests have not passed.
HR-CASCADE-003 pauses a commit that has no prior verification. Both are
sealed, both are CRITICAL/HIGH, and both are implemented: `_detect_deploy`
and `_detect_commit` read `ctx["verified"]`.

Nothing in this estate ever wrote it. A grep for a tests-passed signal
across modules/, tools/ and vault/ returns zero producers, so `verified`
defaulted to True at every call site and neither rule could ever fire. A
consumer with no producer is dead by starvation, and a policy that cannot
fire is not enforcement no matter how it reads.

THREE-VALUED ON PURPOSE. was_verified() returns True, False, or None, and
None means NOT MEASURED. Unknown must never behave as false: a blocking
rule that treats "I have no record" as "the tests failed" would refuse
work on the strength of its own ignorance, which is how a guard gets
disabled by the people it obstructs.

AND THE WRITER MUST HAVE THE READER'S VOCABULARY. Measured 2026-09-11: the
reader above was three-valued from the day it was written, and the writer
took a bool. A sweep that ended INCONCLUSIVE therefore recorded
``passed=False`` and summary() reported "last run failed" -- a run that
judged nothing, described as a judgement against the code, by the one store
built to keep those apart. A run REFUSED by the host preflight recorded
nothing at all, so a stale green kept vouching for a tree the host could no
longer even measure.

So the record carries an OUTCOME, not a verdict-shaped bool, and only PASS
and FAIL are verdicts. INCONCLUSIVE and BLOCKED read back as None, because
they are exactly what None already meant: no evidence either way. That is
deliberately NOT a new blocking policy -- an unmeasured run must not be able
to claim green, and it must not be able to accuse the code either. The one
thing it may do is say so out loud, which is what summary() now does.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = _PP_ROOT / "vault" / "state" / "verification.json"

# A gate that drives this store through a REAL subprocess cannot reach into the
# child to redirect a module global, so without this seam the only way to prove
# the producer works is to let it overwrite the estate's live provenance with
# fixture values -- a test that damages the thing it measures. The override is
# read at call time, never cached, so a child process inherits it by env alone.
_STATE_ENV = "CLAUDE_PP_VERIFICATION_STATE"


def _state_path() -> Path:
    override = os.environ.get(_STATE_ENV)
    return Path(override) if override else STATE_PATH

# How long a green run vouches for the tree. Long enough to cover a normal
# edit-commit cycle, short enough that yesterday's pass cannot authorise
# today's deploy.
DEFAULT_MAX_AGE_S = 3600

# The estate's own words, reused rather than reinvented: verify_spp already
# prints STRICT PASS / STRICT FAIL / INCONCLUSIVE / REFUSED, and SQI-03
# already owns BLOCKED. A third vocabulary for one distinction is worse than
# the second one.
OUTCOME_PASS = "PASS"
OUTCOME_FAIL = "FAIL"
OUTCOME_INCONCLUSIVE = "INCONCLUSIVE"
OUTCOME_BLOCKED = "BLOCKED"
# WRITE-AHEAD, and the only outcome a DEAD run can leave. A process killed
# mid-flight reports nothing, because the thing that would write the epitaph is
# the thing that died. MEASURED 2026-09-11: an 87-row sweep was taken by the OS
# at roughly row 50 and this store learned nothing at all, so "a sweep died"
# and "no sweep ever ran" were the same reading -- which is the founding
# incident of the whole verdict ladder, recurring one layer further in.
# Stamped before dispatch and overwritten by the real outcome at the end; a
# STARTED still standing afterwards IS the evidence of a death.
OUTCOME_STARTED = "STARTED"

# Only these two are verdicts about a subject. Everything else is a statement
# about the run, and must not be readable as either answer.
VERDICT_OUTCOMES = frozenset({OUTCOME_PASS, OUTCOME_FAIL})


def record_verification(suite: str, passed: bool,
                        detail: str = "",
                        outcome: str | None = None) -> dict | None:
    """Record that `suite` ran and WHAT KIND of result it produced. Fail-open.

    `outcome` is the authoritative field. `passed` is kept because callers
    predate it and because a record written before this change has only that;
    when `outcome` is omitted it is derived, so every existing call site keeps
    its exact meaning.
    """
    if outcome is None:
        outcome = OUTCOME_PASS if passed else OUTCOME_FAIL
    entry = {
        "suite": suite,
        "outcome": outcome,
        # Derived, never independent: a reader that trusts this field on an
        # INCONCLUSIVE record must not be told the run failed.
        "passed": outcome == OUTCOME_PASS,
        "detail": detail[:200],
        "ts": time.time(),
        "pid": os.getpid(),
    }
    path = _state_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = _load()
        data["last"] = entry
        history = data.setdefault("history", [])
        history.append(entry)
        del history[:-20]
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8",
                       newline="\n")
        tmp.replace(path)
        return entry
    except OSError:
        return None


def _load() -> dict:
    try:
        return json.loads(_state_path().read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}


def _outcome_of(entry: dict) -> str:
    """The record's outcome, tolerating records written before the field.

    An older record carries only `passed`, and it was only ever written on a
    real verdict, so deriving one back is faithful rather than a guess.
    """
    outcome = entry.get("outcome")
    if isinstance(outcome, str) and outcome:
        return outcome
    return OUTCOME_PASS if entry.get("passed") else OUTCOME_FAIL


def last_outcome(max_age_s: int = DEFAULT_MAX_AGE_S) -> str | None:
    """The typed outcome of the last run, or None when there is nothing live.

    This is the lossless read. was_verified() is a deliberate projection of
    it onto the bool the two Hard Rules consume, and a projection is only
    honest while the thing it projects from is still reachable.
    """
    last = _load().get("last")
    if not isinstance(last, dict):
        return None
    ts = last.get("ts")
    if not isinstance(ts, (int, float)):
        return None
    if (time.time() - ts) > max_age_s:
        return None
    return _outcome_of(last)


def was_verified(max_age_s: int = DEFAULT_MAX_AGE_S) -> bool | None:
    """True / False / None, where None means NO RECORD -- not a failure.

    An expired record is also None: a pass that has aged out has stopped
    vouching for anything, and reporting it as False would be inventing a
    failure that was never observed.

    A run that reached no verdict -- INCONCLUSIVE, BLOCKED -- is None for the
    same reason. It observed nothing about the subject, so it may neither
    vouch for it nor accuse it. The record still says which of the two it was;
    read last_outcome() when that distinction matters, because this projection
    cannot carry it.
    """
    outcome = last_outcome(max_age_s)
    if outcome not in VERDICT_OUTCOMES:
        return None
    return outcome == OUTCOME_PASS


_REASONS = {
    OUTCOME_PASS: "last run passed",
    OUTCOME_FAIL: "last run failed",
    OUTCOME_INCONCLUSIVE: "last run could not judge -- INCONCLUSIVE, "
                          "which is not a failure of the code",
    OUTCOME_BLOCKED: "last run was REFUSED before it started -- BLOCKED, "
                     "so nothing about the code was measured",
    OUTCOME_STARTED: "last run STARTED and never reported -- it was killed "
                     "or is still running; nothing was measured either way",
}


def summary() -> dict:
    """Human-facing state, for a report that has to say WHY it is silent."""
    last = _load().get("last") or {}
    verdict = was_verified()
    outcome = last_outcome()
    return {
        "verified": verdict,
        "outcome": outcome,
        "reason": ("no verification recorded" if outcome is None and not last
                   else "record expired" if outcome is None
                   else _REASONS.get(outcome, f"last run: {outcome}")),
        "suite": last.get("suite", ""),
        "age_s": (round(time.time() - last["ts"])
                  if isinstance(last.get("ts"), (int, float)) else None),
        "path": str(_state_path()),
    }
