"""V-PRE-* gates for gsd_mission.arm_preflight (flow-compression S2). Injected readers; no launch, no host state."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ["GSD_LONG_RUN_STATE_DIR"] = tempfile.mkdtemp(prefix="arm-preflight-")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402


class Reached(Exception):
    """create() reached: the preflight let the arm through."""


def _reached(*a, **k):
    raise Reached()


gm.create = _reached   # no test here may write a mission record

passes = fails = 0


def check(name, cond, detail=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {name} {detail}")
    else:
        fails += 1
        print(f"FAIL {name} {detail}")


def status(outcome, reason="r"):
    return lambda c, w: {"outcome": outcome, "reason": reason}


def mem(mb):
    return lambda: {"available_mb": mb, "source": "test"}


def pre(cmd="/gsd-autonomous --ws x", **kw):
    kw.setdefault("status_reader", status("OK"))
    kw.setdefault("memory_reader", mem(60000))
    return gm.arm_preflight("/tmp/x", cmd, workstream="x", **kw)


def by(res, name):
    return next(c for c in res["checks"] if c["check"] == name)


def main():
    os.environ.pop("CPP_ARM_PREFLIGHT", None)
    os.environ.pop("CPP_RESOURCE_ADMISSION", None)

    r = pre(authority_tokens=1000)
    check("V-PRE-HAPPY", r["ok"] and r["refusal"] is None, str(r["checks"]))
    for oc in ("NO_PHASES", "ALL_COMPLETE"):
        r = pre(status_reader=status(oc))
        check(f"V-PRE-REFUSE-{oc}", not r["ok"] and oc in r["refusal"], r["refusal"])
    r = pre(status_reader=status("UNAVAILABLE"))
    check("V-PRE-UNAVAILABLE-IS-UNMEASURED", r["ok"] and by(r, "gsd_status")["status"] == "unmeasured")
    r = pre(status_reader=lambda c, w: 1 / 0)
    check("V-PRE-RAISING-READER-IS-UNMEASURED", r["ok"] and by(r, "gsd_status")["status"] == "unmeasured")
    r = pre("python tool.py", status_reader=status("NO_PHASES"))
    check("V-PRE-NON-GSD-ROUTE-SKIPS-GSD", r["ok"] and by(r, "gsd_status")["status"] == "n/a")
    r = pre(memory_reader=mem(100))
    check("V-PRE-REFUSE-LOW-MEMORY", not r["ok"] and "resource_admission" in r["refusal"], r["refusal"])
    r = pre(memory_reader=mem(100), launch=False)
    check("V-PRE-NO-LAUNCH-NO-MEMORY-CHECK", r["ok"])
    r = pre(memory_reader=lambda: {"available_mb": None})
    check("V-PRE-UNREADABLE-MEMORY-IS-UNMEASURED", r["ok"] and by(r, "resource_admission")["status"] == "unmeasured")
    r = pre()
    check("V-PRE-NO-AUTHORITY-WARNS-NOT-REFUSES", r["ok"] and by(r, "authority")["status"] == "warn")
    r = pre(autocompact=1_000_000, continue_max_tokens=900_000)
    check("V-PRE-ROTATION-REPAIR-REPORTED", r["ok"] and by(r, "rotation_invariant")["status"] == "warn")
    check("V-PRE-IDEMPOTENT", pre(status_reader=status("NO_PHASES")) == pre(status_reader=status("NO_PHASES")))

    os.environ["CPP_ARM_PREFLIGHT"] = "off"
    r = pre(status_reader=status("NO_PHASES"))
    check("V-PRE-KILL-SWITCH", r["ok"] and r.get("off"))
    os.environ.pop("CPP_ARM_PREFLIGHT")

    # wiring: arm() refuses through the real call path, before any record exists
    os.environ["_TEST_GSD_STATUS"] = '{"outcome": "NO_PHASES", "reason": "forced"}'
    os.environ["CPP_RESOURCE_ADMISSION"] = "off"
    try:
        gm.arm("/tmp/x-nonexistent", "/gsd-autonomous --ws x", launch=True)
        check("V-PRE-ARM-WIRED", False, "arm did not refuse")
    except gm.MissionError as exc:
        check("V-PRE-ARM-WIRED", "preflight" in str(exc) and "NO_PHASES" in str(exc), str(exc)[:120])
    res = gm.arm_chain("/tmp/x-nonexistent", "/gsd-autonomous --ws x", wu_packet="p", token_estimate=1, route="r")
    check("V-PRE-ARM-CHAIN-WIRED", res["ok"] is False and "preflight" in res["why"], res.get("why", "")[:100])
    os.environ.pop("_TEST_GSD_STATUS")

    # mutation drill: an always-pass preflight must turn the refusal gates red
    real = gm.arm_preflight
    gm.arm_preflight = lambda *a, **k: {"ok": True, "checks": [], "refusal": None}
    try:
        os.environ["_TEST_GSD_STATUS"] = '{"outcome": "NO_PHASES", "reason": "forced"}'
        try:
            gm.arm("/tmp/x-nonexistent", "/gsd-autonomous --ws x", launch=True)
            refused = False
        except gm.MissionError as exc:
            refused = "preflight" in str(exc)
        except Reached:
            refused = False
        check("V-PRE-MUTANT-ALWAYS-PASS-GOES-RED", not refused, "mutant did not refuse, so the wired gate detects it")
    finally:
        gm.arm_preflight = real
        os.environ.pop("_TEST_GSD_STATUS", None)

    print(f"PRE_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
