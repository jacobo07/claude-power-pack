#!/usr/bin/env python
"""V-AL-* gates: an Owner authority raise also carries its headroom to the lineage ceiling.

Measured 2026-11-22 (avatar lineage m-6fa310e1b676 -> m-d91ce6590a09 -> m-c4569262384c): the Owner typed
"autorizo 90M"; `authority` set the mission ceiling to 122.4M (31.9M spent), but `lineage_authority_tokens` stayed at
200M with 199.56M processed across the lineage, so renewal/autoresume would refuse the mission at its cycle cap.
Gates: the raise lifts the lineage ceiling and budget by the same headroom; it never lowers them; a mission outside a
lineage is untouched; unmeasured mission or lineage spend leaves the lineage unchanged and says why. Hermetic.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="mission-authority-lineage-test-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_MISSION_RECOVERY"] = "off"
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gsd_mission as gm  # noqa: E402
import mission_spend as ms  # noqa: E402

NOW = 1_800_000_000.0
M = 1_000_000
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def mission(mid: str, **extra) -> dict:
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    owner = {"session_id": f"{mid}-w", "pid": None, "proc_start": None, "heartbeat_at": NOW, "epoch": 1,
             "kind": "background"}
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, state=gm.RUNNING,
                         epoch=1, max_hours=100.0, owner=owner, **extra)


def lineage_at(processed, unmeasured=()):
    return lambda mid, extra=None: {"processed": processed, "unmeasured": list(unmeasured), "members": [mid]}


def main() -> int:
    meter = lambda r: 31_933_530  # noqa: E731  (the avatar mission's measured spend)
    lin = lineage_at(199_564_756)

    # 1. the incident: 32.4M -> 122.4M on a lineage at 199.56M of 200M.
    mission("m-al0000000001", authority_tokens=32_368_774, lineage_authority_tokens=200 * M,
            lineage_token_budget=199 * M)
    out = gm.set_authority("m-al0000000001", 122_368_774, spent_fn=meter, lineage_fn=lin, reason="typed 90M")
    want = 199_564_756 + (122_368_774 - 31_933_530)
    check("V-AL-LINEAGE-CEILING-CARRIES-HEADROOM", out["lineage_authority_tokens"] == want,
          f"{out.get('lineage_authority_tokens')} want {want}")
    check("V-AL-LINEAGE-BUDGET-RAISED", out["lineage_token_budget"] == want - 1 * M, str(out.get("lineage_token_budget")))
    rem = {"budget": out["lineage_token_budget"], "remaining": out["lineage_token_budget"] - 199_564_756}
    r = out["authority_receipts"][-1]["lineage"]
    check("V-AL-RECEIPT-NAMES-LINEAGE", r["prev"] == 200 * M and r["new"] == want and r["spent"] == 199_564_756, str(r))
    check("V-AL-HEADROOM-EQUALS-MISSION-HEADROOM", out["lineage_authority_tokens"] - 199_564_756
          == out["authority_tokens"] - 31_933_530)
    check("V-AL-MISSION-CEILING-UNCHANGED-SEMANTICS", out["authority_tokens"] == 122_368_774)
    check("V-AL-REMAINING-POSITIVE-AFTER-RAISE", rem["remaining"] == 122_368_774 - 31_933_530 - 1 * M, str(rem))

    # 2. never lowered: a smaller raise on a lineage with plenty of room leaves it alone.
    mission("m-al0000000002", authority_tokens=10 * M, lineage_authority_tokens=500 * M, lineage_token_budget=499 * M)
    o2 = gm.set_authority("m-al0000000002", 20 * M, spent_fn=lambda r: 5 * M, lineage_fn=lineage_at(100 * M))
    check("V-AL-NEVER-LOWERED", o2["lineage_authority_tokens"] == 500 * M and o2["lineage_token_budget"] == 499 * M
          and "never lowered" in o2["authority_receipts"][-1]["lineage"]["unchanged"])

    # 3. control: a mission outside any lineage gets no lineage fields.
    mission("m-al0000000003", authority_tokens=10 * M)
    o3 = gm.set_authority("m-al0000000003", 50 * M, spent_fn=lambda r: 5 * M, lineage_fn=lin)
    check("V-AL-CONTROL-NO-LINEAGE-UNTOUCHED", "lineage_authority_tokens" not in o3
          and o3["authority_receipts"][-1]["lineage"] is None and o3["authority_tokens"] == 50 * M)

    # 4. unmeasured lineage member: unchanged and named (absent is not zero).
    mission("m-al0000000004", authority_tokens=32 * M, lineage_authority_tokens=200 * M, lineage_token_budget=199 * M)
    o4 = gm.set_authority("m-al0000000004", 122 * M, spent_fn=meter, lineage_fn=lineage_at(150 * M, ["m-x"]))
    check("V-AL-UNMEASURED-LINEAGE-UNCHANGED", o4["lineage_authority_tokens"] == 200 * M and o4["authority_tokens"] == 122 * M
          and "unmeasured" in o4["authority_receipts"][-1]["lineage"]["unchanged"])

    # 5. lineage meter raising: unchanged, named, and the mission raise still lands.
    def boom(mid, extra=None):
        raise OSError("meter down")
    mission("m-al0000000005", authority_tokens=32 * M, lineage_authority_tokens=200 * M)
    o5 = gm.set_authority("m-al0000000005", 122 * M, spent_fn=meter, lineage_fn=boom)
    check("V-AL-LINEAGE-METER-DOWN-NAMED", o5["lineage_authority_tokens"] == 200 * M and o5["authority_tokens"] == 122 * M
          and "OSError" in o5["authority_receipts"][-1]["lineage"]["unchanged"])

    # 6. unmeasured mission spend: the headroom cannot be computed, so the lineage is unchanged.
    def mboom(r):
        raise OSError("mission meter down")
    mission("m-al0000000006", authority_tokens=32 * M, lineage_authority_tokens=200 * M)
    o6 = gm.set_authority("m-al0000000006", 122 * M, spent_fn=mboom, lineage_fn=lin)
    check("V-AL-MISSION-UNMEASURED-UNCHANGED", o6["lineage_authority_tokens"] == 200 * M
          and o6["authority_receipts"][-1]["lineage"]["unchanged"] == "mission spend unmeasured")

    # 7. a lineage without a separate budget field: only the ceiling moves.
    mission("m-al0000000007", authority_tokens=32 * M, lineage_authority_tokens=200 * M)
    o7 = gm.set_authority("m-al0000000007", 122 * M, spent_fn=lambda r: 32 * M, lineage_fn=lineage_at(199 * M))
    check("V-AL-NO-BUDGET-FIELD-CEILING-ONLY", o7["lineage_authority_tokens"] == 289 * M and "lineage_token_budget" not in o7)

    print(f"AUTHORITY_LINEAGE_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    shutil.rmtree(TMP, ignore_errors=True)
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
