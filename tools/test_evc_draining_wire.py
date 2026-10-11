#!/usr/bin/env python
"""V-EVC-DRAIN-* gates: the supervisor's cost breaker drives the predictive DRAINING edge and records it.

Hermetic: state goes to a temp dir BEFORE import; measure/fingerprint/forecast are injected.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="evc-drain-wire-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ.pop("CPP_MISSION_RENEW", None)
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import mission_spend as ms  # noqa: E402
import gsd_mission as gm  # noqa: E402
import gsd_long_run as lr  # noqa: E402

passes = fails = 0
NOW = 1_800_000_000.0
M = 1_000_000
K = 1_000
FP = lambda w: "f"  # noqa: E731


def check(gate, cond, ev=""):
    global passes, fails
    passes += bool(cond)
    fails += not cond
    print(f"{'PASS' if cond else 'FAIL'} {gate} {ev}")


def _mission(mid, **fields):
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                         state=gm.RUNNING, epoch=1, token_estimate=1 * M, token_trip_ratio=1.0, max_hours=1000.0, **fields)


def _rows(mid, event):
    p = lr.ledger_path()
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("session_id") == mid and r.get("event") == event:
            out.append(r)
    return out


def main() -> int:
    fc = lambda r: 500 * K  # noqa: E731

    _mission("m-d")
    out = gm._cost_breaker(gm.load("m-d"), NOW, measure=lambda r: 600 * K, fingerprint=FP, forecast=fc)
    check("V-EVC-DRAIN-WIRE", out.get("lease_state") == "DRAINING" and out["state"] == gm.RUNNING
          and not out.get("owner_hold"), str({k: out.get(k) for k in ("lease_state", "state", "owner_hold")}))
    _mission("m-c")
    ctl = gm._cost_breaker(gm.load("m-c"), NOW, measure=lambda r: 100 * K, fingerprint=FP, forecast=fc)
    check("V-EVC-DRAIN-WIRE-CONTROL", "lease_state" not in ctl and not ctl.get("owner_hold"))

    rows = _rows("m-d", "lease_draining")
    check("V-EVC-DRAIN-LEDGER", len(rows) == 1 and rows[0].get("spent") == 600 * K
          and rows[0].get("p95_remaining") == 500 * K and rows[0].get("authority"), str(rows))
    again = gm._cost_breaker(gm.load("m-d"), NOW + 1, measure=lambda r: 600 * K, fingerprint=FP, forecast=fc)
    check("V-EVC-DRAIN-IDEMPOTENT", len(_rows("m-d", "lease_draining")) == 1
          and again.get("lease_state") == "DRAINING")

    _mission("m-h")
    held = gm._cost_breaker(gm.load("m-h"), NOW, measure=lambda r: 3 * M, fingerprint=FP, forecast=fc)
    check("V-EVC-DRAIN-HARD-WINS", bool(held.get("owner_hold")) and "cost breaker" in held["owner_hold"]["reason"],
          str(held.get("owner_hold")))

    _mission("m-n")
    none = gm._cost_breaker(gm.load("m-n"), NOW, measure=lambda r: 600 * K, fingerprint=FP, forecast=lambda r: None)
    check("V-EVC-DRAIN-NOFORECAST", "lease_state" not in none and not none.get("owner_hold")
          and not _rows("m-n", "lease_draining"))

    _mission("m-r")

    def boom(r):
        raise OSError("forecast")
    err = gm._cost_breaker(gm.load("m-r"), NOW, measure=lambda r: 600 * K, fingerprint=FP, forecast=boom)
    check("V-EVC-DRAIN-FORECAST-RAISE-RECORDED", "lease_state" not in err and not err.get("owner_hold")
          and len(_rows("m-r", "cost_breaker_unmeasured")) == 1)

    check("V-EVC-DRAIN-STATES-UNCHANGED", "DRAINING" not in gm.STATES)
    print(f"{passes} pass, {fails} fail")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
