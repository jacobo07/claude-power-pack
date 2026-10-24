"""V-S4-* gates: economic lease -- variance is not a stop when semantic progress is verified (flow-compression S4)."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="s4-lease-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["GSD_LONG_RUN_PROJECTS_DIR"] = str(Path(TMP) / "projects")
os.environ["CPP_CLAUDE_EXE"] = "__no_such_claude_in_tests__"
os.environ.pop("CPP_ECON_LEASE", None)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import mission_spend as ms  # noqa: E402
import gsd_mission as gm  # noqa: E402

passes = fails = 0
M = 1_000_000


def check(name, cond, detail=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {name} {detail}")
    else:
        fails += 1
        print(f"FAIL {name} {detail}")


def rec(**kw):
    base = {"token_estimate": 10 * M, "authority_tokens": 140 * M, "cost_mark": {"fp": "A", "tokens": 5 * M}}
    base.update(kw)
    return base


# --- judge, pure
v = ms.judge(rec(), 25 * M, "B")                       # > 2 x 10M, fp moved, authority remains
check("V-S4-PRODUCTIVE-CROSSES-VARIANCE", v["trip"] is None and v.get("recompile", {}).get("lease") is True
      and v["mark"] == {"fp": "B", "tokens": 25 * M}, str(v))
v = ms.judge(rec(), 25 * M, "A")                       # same fp: no semantic delta
check("V-S4-NONPRODUCTIVE-STILL-STOPS", v["trip"] and "cost breaker" in v["trip"] and not v.get("recompile"), str(v)[:120])
v = ms.judge(rec(cost_mark={}), 25 * M, "B")           # no prior mark: delta unverifiable
check("V-S4-UNVERIFIED-DELTA-STOPS", v["trip"] and not v.get("recompile"))
v = ms.judge(rec(), 25 * M, None)                      # fingerprint unmeasured is not progress
check("V-S4-UNMEASURED-FP-STOPS", v["trip"] and not v.get("recompile"))
v = ms.judge(rec(), 139.5 * M, "B")                    # runaway: authority less closeout is the ceiling
check("V-S4-CEILING-AUTHORITATIVE", v["trip"] and v.get("level") == "MISSION_AUTHORITY" and not v.get("recompile"), str(v)[:100])
v = ms.judge(rec(authority_tokens=None), 25 * M, "B")  # no Owner authority: operator estimate keeps its stop
check("V-S4-NO-AUTHORITY-STILL-STOPS", v["trip"] and not v.get("recompile"))
v = ms.judge(rec(lease_renewals=ms.LEASE_MAX_RENEWALS), 25 * M, "B")
check("V-S4-RENEWAL-CAP", v["trip"] and not v.get("recompile"))
os.environ["CPP_ECON_LEASE"] = "off"
v = ms.judge(rec(), 25 * M, "B")
check("V-S4-KILL-SWITCH", v["trip"] and not v.get("recompile"))
del os.environ["CPP_ECON_LEASE"]

# --- integrated: _cost_breaker renews, then the same fingerprint cannot renew twice
NOW = 1_800_000_000.0


def mission(mid, **fields):
    gm.create(TMP, "/gsd-autonomous", mission_id=mid, now=NOW)
    return gm.transition(mid, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW,
                         state=gm.RUNNING, epoch=1, **fields)


mission("m-lease", token_estimate=10 * M, authority_tokens=140 * M, closeout_tokens=M,
        cost_mark={"fp": "A", "tokens": 5 * M})
out = gm._cost_breaker(gm.load("m-lease"), NOW, measure=lambda r: 25 * M, fingerprint=lambda w: "B")
check("V-S4-RENEW-NO-OWNER-HOLD", not out.get("owner_hold") and out.get("lease_renewals") == 1
      and out["token_estimate"] > 10 * M and out["cost_mark"]["fp"] == "B", str({k: out.get(k) for k in ("owner_hold", "token_estimate", "cost_mark")}))
check("V-S4-RENEWED-INSIDE-AUTHORITY", out["token_estimate"] * ms.DEFAULT_TRIP_RATIO <= 139 * M, str(out["token_estimate"]))
again = gm._cost_breaker(gm.load("m-lease"), NOW + 60, measure=lambda r: 25 * M, fingerprint=lambda w: "B")
check("V-S4-IDEMPOTENT-SAME-FP", again.get("lease_renewals") == 1 and not again.get("owner_hold"))
mission("m-stuck", token_estimate=10 * M, authority_tokens=140 * M, closeout_tokens=M,
        cost_mark={"fp": "A", "tokens": 5 * M})
st = gm._cost_breaker(gm.load("m-stuck"), NOW, measure=lambda r: 25 * M, fingerprint=lambda w: "A")
check("V-S4-STUCK-HOLDS", bool(st.get("owner_hold")) and "cost breaker" in st["owner_hold"]["reason"])
mission("m-run", token_estimate=10 * M, authority_tokens=140 * M, closeout_tokens=M,
        cost_mark={"fp": "A", "tokens": 5 * M})
rn = gm._cost_breaker(gm.load("m-run"), NOW, measure=lambda r: 139.5 * M, fingerprint=lambda w: "B")
check("V-S4-RUNAWAY-HOLDS-AT-CEILING", bool(rn.get("owner_hold")) and "mission authority" in rn["owner_hold"]["reason"])

# --- mutant: a judge that never leases must turn the productive gate red
real = ms.lease_on
ms.lease_on = lambda: False
check("V-S4-MUTANT-NO-LEASE-GOES-RED", ms.judge(rec(), 25 * M, "B")["trip"] is not None)
ms.lease_on = real

print(f"S4_PASS={passes}/{passes + fails}  threshold=all")
sys.exit(0 if fails == 0 else 1)
