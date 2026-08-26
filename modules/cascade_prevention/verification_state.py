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
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = _PP_ROOT / "vault" / "state" / "verification.json"

# How long a green run vouches for the tree. Long enough to cover a normal
# edit-commit cycle, short enough that yesterday's pass cannot authorise
# today's deploy.
DEFAULT_MAX_AGE_S = 3600


def record_verification(suite: str, passed: bool,
                        detail: str = "") -> dict | None:
    """Record that `suite` ran and whether it passed. Fail-open."""
    entry = {
        "suite": suite,
        "passed": bool(passed),
        "detail": detail[:200],
        "ts": time.time(),
        "pid": os.getpid(),
    }
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = _load()
        data["last"] = entry
        history = data.setdefault("history", [])
        history.append(entry)
        del history[:-20]
        tmp = STATE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8",
                       newline="\n")
        tmp.replace(STATE_PATH)
        return entry
    except OSError:
        return None


def _load() -> dict:
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}


def was_verified(max_age_s: int = DEFAULT_MAX_AGE_S) -> bool | None:
    """True / False / None, where None means NO RECORD -- not a failure.

    An expired record is also None: a pass that has aged out has stopped
    vouching for anything, and reporting it as False would be inventing a
    failure that was never observed.
    """
    last = _load().get("last")
    if not isinstance(last, dict):
        return None
    ts = last.get("ts")
    if not isinstance(ts, (int, float)):
        return None
    if (time.time() - ts) > max_age_s:
        return None
    return bool(last.get("passed"))


def summary() -> dict:
    """Human-facing state, for a report that has to say WHY it is silent."""
    last = _load().get("last") or {}
    verdict = was_verified()
    return {
        "verified": verdict,
        "reason": ("no verification recorded" if verdict is None and not last
                   else "record expired" if verdict is None
                   else "last run passed" if verdict else "last run failed"),
        "suite": last.get("suite", ""),
        "age_s": (round(time.time() - last["ts"])
                  if isinstance(last.get("ts"), (int, float)) else None),
        "path": str(STATE_PATH),
    }
