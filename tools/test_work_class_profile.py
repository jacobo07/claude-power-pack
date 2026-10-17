#!/usr/bin/env python
"""V-PROF-* gates: a settled work unit updates its work-class profile before the next forecast.

Measured 2026-10-16: a DWS phase forecast 8.3M (a default ceiling / 2) and cost 17.0M; nothing recorded the actual
anywhere a later forecast could use. These gates drive the real settle_unit / forecast / calibration path on a temp
store; the CLI seed is driven through a subprocess. Each refusal has a paired control that is admitted.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="work-class-profile-test-")
os.environ["CPP_WORK_CLASS_PROFILE_DIR"] = TMP
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import work_class_profile as wcp  # noqa: E402

passes = fails = 0


def _ok(gate, ev):
    global passes
    passes += 1
    print(f"PASS {gate}: {ev}")


def _fail(gate, why):
    global fails
    fails += 1
    print(f"FAIL {gate}: {why}")


def check(gate, cond, ev, why=""):
    (_ok if cond else _fail)(gate, ev if cond else why or ev)


def act(processed, calls=100, avg=169784, mx=216013, att=8, failed=7):
    return {"processed": processed, "calls": calls, "avg_ctx": avg, "max_ctx": mx, "attempts": att,
            "attempts_failed": failed}


# V-PROF-UNKNOWN-CLASS: absent is not zero
u = wcp.forecast("NEVER_SEEN")
check("V-PROF-UNKNOWN-CLASS", u["confidence"] == "NONE" and u["n"] == 0 and u["p50"] is None and u["p80"] is None
      and u["p95"] is None, "no samples -> confidence NONE, no numbers", f"got {u}")
u2 = wcp.forecast("NEVER_SEEN", calls=50)
check("V-PROF-UNKNOWN-CLASS-STRUCTURAL", u2["p50"] is None and u2["structural"] is not None
      and u2["structural"] >= 50 * 110835, "structural lower bound present, quantiles absent", f"got {u2}")

# V-PROF-SETTLE-IDEMPOTENT
r1 = wcp.settle_unit("C1", "u1", act(17_032_240), forecast=8_332_455, cause="floor x calls")
r1b = wcp.settle_unit("C1", "u1", act(1), forecast=1, cause="replay")
check("V-PROF-SETTLE-IDEMPOTENT", wcp.forecast("C1")["n"] == 1 and r1b["idempotent"] is True
      and r1b["actual"] == 17_032_240 and r1["idempotent"] is False,
      "replayed unit_id keeps one sample and returns the first receipt", f"n={wcp.forecast('C1')['n']} r1b={r1b}")

# receipt fields
check("V-PROF-RECEIPT", abs(r1["variance_ratio"] - 17_032_240 / 8_332_455) < 1e-9
      and abs(r1["abs_pct_error"] - abs(17_032_240 - 8_332_455) / 8_332_455) < 1e-9
      and r1["cause"] == "floor x calls" and r1["forecast"] == 8_332_455,
      "receipt carries forecast, actual, variance ratio, abs pct error, cause", f"got {r1}")
rn = wcp.settle_unit("C_NOFC", "x", act(1_000_000), forecast=None, cause="no forecast existed")
check("V-PROF-RECEIPT-NO-FORECAST", rn["variance_ratio"] is None and rn["abs_pct_error"] is None,
      "no forecast -> no ratio (absent is not zero)", f"got {rn}")

# V-PROF-NO-FABRICATED-QUANTILES
f1 = wcp.forecast("C1", calls=100)
check("V-PROF-NO-FABRICATED-QUANTILES", f1["n"] == 1 and f1["p50"] == 17_032_240 and f1["p80"] is None
      and f1["p95"] is None and f1["confidence"] == "LOW" and "fewer than 3" in f1["basis"]
      and f1["structural"] is not None,
      "n=1: p50 = the sample, p80/p95 None, basis says so, structural present", f"got {f1}")

# V-PROF-FORECAST-MOVES-BEFORE-ADMISSION
before = wcp.forecast("C1")
wcp.settle_unit("C1", "u2", act(4_000_000, calls=40), forecast=before["p50"], cause="smaller unit")
after = wcp.forecast("C1")
check("V-PROF-FORECAST-MOVES-BEFORE-ADMISSION", after["p50"] != before["p50"] and after["n"] == 2
      and after["p50"] == (17_032_240 + 4_000_000) / 2, "settle moved the next forecast",
      f"before={before['p50']} after={after['p50']}")

# confidence tiers + quantiles appear only with enough samples
for i in range(3, 12):
    wcp.settle_unit("C1", f"u{i}", act(5_000_000 + i * 100_000), forecast=None, cause="fill")
    n = wcp.forecast("C1")["n"]
    if n == 3:
        f3 = wcp.forecast("C1")
    if n == 9:
        f9 = wcp.forecast("C1")
    if n == 10:
        f10 = wcp.forecast("C1")
check("V-PROF-CONFIDENCE-TIERS", f3["confidence"] == "MEDIUM" and f3["p80"] is not None
      and f9["confidence"] == "MEDIUM" and f10["confidence"] == "HIGH" and f10["p95"] is not None
      and f10["p50"] <= f10["p80"] <= f10["p95"], "3-9 MEDIUM (p80 present), >=10 HIGH (p95 present)",
      f"f3={f3['confidence']} f9={f9['confidence']} f10={f10['confidence']} p95={f10['p95']}")

# V-PROF-CALIBRATION: two units with known forecast/p80
os.environ["CPP_WORK_CLASS_PROFILE_DIR"] = tempfile.mkdtemp(prefix="wcp-cal-")
for i, v in enumerate([10, 10, 10]):
    wcp.settle_unit("K", f"s{i}", act(v * 1_000_000), forecast=None, cause="seed")
p80 = wcp.forecast("K")["p80"]
wcp.settle_unit("K", "hit", act(int(p80 * 2)), forecast=10_000_000, cause="over p80")      # error 100%+, surprise
wcp.settle_unit("K", "miss", act(10_000_000), forecast=20_000_000, cause="under p80")      # error 50%, no surprise
cal = wcp.calibration("K")
exp_mae = (abs(int(p80 * 2) - 10_000_000) / 10_000_000 + 0.5) / 2
check("V-PROF-CALIBRATION", cal["units_with_forecast"] == 2 and abs(cal["mean_abs_pct_error"] - exp_mae) < 1e-9
      and cal["units_with_p80"] == 2 and cal["surprise_rate"] == 0.5,
      "MAE over forecast units, surprise rate over units that had a p80", f"got {cal} exp_mae={exp_mae}")
check("V-PROF-CALIBRATION-EMPTY", wcp.calibration("NOPE")["mean_abs_pct_error"] is None
      and wcp.calibration("NOPE")["surprise_rate"] is None, "no receipts -> None, not 0")

# validation refusals and a paired control
for gate, kw in (("negative", act(-5)), ("zero", act(0)), ("bool", act(True))):
    try:
        wcp.settle_unit("V", "bad-" + gate, kw, forecast=None, cause="x")
        _fail("V-PROF-REFUSES-BAD-ACTUAL", f"{gate} admitted")
    except wcp.ProfileError:
        _ok("V-PROF-REFUSES-BAD-ACTUAL", f"{gate} refused")
try:
    wcp.settle_unit("V", "../evil", act(5), forecast=None, cause="x")
    _fail("V-PROF-REFUSES-BAD-ID", "path-ish unit id admitted")
except wcp.ProfileError:
    _ok("V-PROF-REFUSES-BAD-ID", "refused")
try:
    wcp.settle_unit("../x", "ok", act(5), forecast=None, cause="x")
    _fail("V-PROF-REFUSES-BAD-CLASS", "path-ish class admitted")
except wcp.ProfileError:
    _ok("V-PROF-REFUSES-BAD-CLASS", "refused")
check("V-PROF-REFUSES-CONTROL", wcp.forecast("V")["n"] == 0, "no refused unit left a sample")

# lease feed: make_lease accepts what lease_forecast returns
import phase_lease as pls  # noqa: E402
lf = wcp.lease_forecast("K", calls=100)
lease = pls.make_lease(phase="2", forecast=lf["forecast"], base=0, state_file="STATE.md", set_at=1.0)
check("V-PROF-FEEDS-LEASE", isinstance(lf["forecast"], int) and lf["forecast"] > 0 and lease["forecast"] == lf["forecast"]
      and lf["basis"], f"lease forecast {lf['forecast']} ({lf['basis']})", f"got {lf}")
try:
    wcp.lease_forecast("NO_SUCH_CLASS")
    _fail("V-PROF-LEASE-NO-FORECAST", "unknown class produced a lease forecast")
except wcp.ProfileError:
    _ok("V-PROF-LEASE-NO-FORECAST", "unknown class refuses instead of inventing a number")

# CLI seed shape
env = dict(os.environ, CPP_WORK_CLASS_PROFILE_DIR=tempfile.mkdtemp(prefix="wcp-cli-"))
py = sys.executable
tool = str(HERE / "work_class_profile.py")
s = subprocess.run([py, tool, "settle", "--class", "DWS_LIVE_LEG", "--unit", "orca-dws-phase2", "--processed", "17032240",
                    "--calls", "100", "--avg-ctx", "169784", "--max-ctx", "216013", "--attempts", "8",
                    "--attempts-failed", "7", "--forecast", "8332455", "--cause", "seed"],
                   capture_output=True, text=True, env=env)
fc = subprocess.run([py, tool, "forecast", "--class", "DWS_LIVE_LEG", "--calls", "100"], capture_output=True,
                    text=True, env=env)
try:
    j = json.loads(fc.stdout)
    check("V-PROF-CLI", s.returncode == 0 and j["n"] == 1 and j["p50"] == 17032240 and j["p80"] is None,
          "CLI settle then forecast round-trips", f"{s.stdout}{s.stderr}{fc.stdout}{fc.stderr}")
except Exception as exc:  # noqa: BLE001
    _fail("V-PROF-CLI", f"{exc}: {s.stderr} {fc.stdout} {fc.stderr}")

print(f"WCP_PASS={passes}/{passes + fails}")
sys.exit(0 if fails == 0 else 1)
