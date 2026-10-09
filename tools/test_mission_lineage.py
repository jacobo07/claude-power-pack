#!/usr/bin/env python
"""V-LINEAGE-* gates: a renewal inherits the REMAINING token budget of its lineage (UCDA A2).

Measured: renewals carried a fresh token_estimate, so a lineage could spend N x its envelope.
Every gate has a paired control; the mutation drill replaces the remaining-budget rule with the old
fresh-budget rule and requires the gate to go RED. Hermetic: state in a temp dir before import."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="mission-lineage-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import mission_spend as ms  # noqa: E402
import gsd_mission as gm  # noqa: E402

passes = fails = 0
NOW = 1_800_000_000.0
M = 1_000_000
SPEND: dict = {}


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def _root(mid, estimate):
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                         state=gm.RUNNING, epoch=1, token_estimate=estimate, work_dir=TMP)


def _measure(rec, *_a, **_k):
    return SPEND.get(rec["mission_id"])


def renewal_budget_ok(rec, spent_by_id, expect):
    """Pure gate: renew `rec` with the given per-mission spend; True when the successor's estimate is `expect`."""
    SPEND.clear()
    SPEND.update(spent_by_id)
    new = gm.renew_mission(rec, now=NOW + 1)
    return new.get("token_estimate") == expect, new


def main() -> int:
    real = ms.processed_tokens
    ms.processed_tokens = _measure
    try:
        a = _root("m-la", 10 * M)
        ok, b = renewal_budget_ok(a, {"m-la": 7 * M}, 3 * M)
        check("V-LINEAGE-REMAINING", ok, f"successor estimate {b.get('token_estimate')}")
        check("V-LINEAGE-BUDGET-CARRIED", b.get("lineage_token_budget") == 10 * M)
        check("V-LINEAGE-HEAD", ms.lineage_head("m-la") == b["mission_id"] and
              ms.lineage_head(b["mission_id"]) == b["mission_id"])
        check("V-LINEAGE-HEAD-UNKNOWN-CONTROL", ms.lineage_head("m-nope") == "m-nope")
        SPEND.update({b["mission_id"]: 2 * M})
        meter = ms.lineage_spend("m-la")
        check("V-LINEAGE-METER", meter["processed"] == 9 * M and not meter["unmeasured"], str(meter))
        # replay canary: third link inherits what is left of the ROOT budget, not of the 3M successor
        ok, c = renewal_budget_ok(gm.load(b["mission_id"]), {"m-la": 7 * M, b["mission_id"]: 2 * M}, 1 * M)
        check("V-LINEAGE-REPLAY-CANARY", ok, f"third estimate {c.get('token_estimate')}")
        # mutation drill: the old fresh-budget rule must go red
        real_rem = ms.lineage_remaining
        ms.lineage_remaining = lambda rec, **k: {"remaining": rec.get("token_estimate"), "unmeasured": []}
        try:
            d0 = _root("m-ld", 10 * M)
            mut_ok, _ = renewal_budget_ok(d0, {"m-ld": 7 * M}, 3 * M)
        finally:
            ms.lineage_remaining = real_rem
        check("V-LINEAGE-MUTATION-RED", not mut_ok, "fresh-budget mutant fails the remaining gate")
        # exhausted lineage is refused, with a non-exhausted control
        e = _root("m-le", 10 * M)
        SPEND.clear()
        SPEND["m-le"] = 11 * M
        why = gm._renewal_why_not(e, "budget: cycles", {"outcome": "OK"}, TMP)
        check("V-LINEAGE-EXHAUSTED-REFUSED", why and "lineage" in why, str(why))
        SPEND["m-le"] = 4 * M
        why2 = gm._renewal_why_not(e, "budget: cycles", {"outcome": "OK"}, TMP)
        check("V-LINEAGE-NOT-EXHAUSTED-CONTROL", not (why2 and "lineage" in why2), str(why2))
        # unknown spend is not zero: estimate carried unchanged and flagged
        f = _root("m-lf", 10 * M)
        SPEND.clear()
        nf = gm.renew_mission(f, now=NOW + 2)
        check("V-LINEAGE-UNKNOWN-FLAGGED", nf.get("lineage_spend_unknown") is True and
              nf.get("token_estimate") == 10 * M)
        SPEND["m-lf"] = 0
        why3 = gm._renewal_why_not(f, "budget: cycles", {"outcome": "OK"}, TMP)
        check("V-LINEAGE-ZERO-MEASURED-CONTROL", not (why3 and "lineage" in why3), str(why3))
    finally:
        ms.processed_tokens = real
    print(f"LINEAGE_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
