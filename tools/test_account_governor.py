#!/usr/bin/env python3
"""V-CCN-GOV gates for tools/account_governor.py."""
import json
import os
import subprocess
import sys
import tempfile
import time
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import account_governor as g  # noqa: E402

passes = fails = 0
NOW = 1_800_000_000.0
CALIB = 1000.0


def gate(name, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print("PASS %s: %s" % (name, ev))
    else:
        fails += 1
        print("FAIL %s: %s" % (name, ev))


def jdump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f)


def env(tmp, spend, cfg_extra=None, hosts=None, calib=CALIB, reset=NOW - 3 * 86400):
    """Default: both configured hosts report (FULL coverage), all spend on gex44, 0 on laptop.
    Explicit `hosts`: each listed host reports `spend`."""
    sd = tempfile.mkdtemp(dir=tmp)
    cfg = {"reset_at": reset}
    if calib is not None:
        cfg["calibration_api_eq_per_100pct"] = calib
    cfg.update(cfg_extra or {})
    jdump(os.path.join(sd, "account-governor.json"), cfg)
    rows = [("gex44", spend), ("laptop", 0.0)] if hosts is None else [(h, spend) for h in hosts]
    for h, v in rows:
        jdump(os.path.join(sd, "account-governor-hosts", h + ".json"), {"api_eq_usd": v, "reset_at": reset, "host": h, "measured_at": NOW - 60})
    return sd


def run(sd, action="arm"):
    code, verdict, why, st = g.check(sd, action, now=NOW, roots=[])
    return code, verdict


def mutant_module():
    src = open(os.path.join(HERE, "account_governor.py"), encoding="utf-8").read()
    old = "    if lo >= REFUSE_PCT:"
    assert src.count(old) == 1
    src = src.replace(old, "    if (est if est is not None else lo) >= REFUSE_PCT:")
    mod = types.ModuleType("gov_mutant")
    mod.__file__ = os.path.join(HERE, "account_governor.py")
    exec(compile(src, "<mutant>", "exec"), mod.__dict__)
    return mod


with tempfile.TemporaryDirectory() as tmp:
    for pct, want in ((84, 0), (85, 3), (86, 3)):
        sd = env(tmp, pct * CALIB / 100.0)
        code, verdict = run(sd)
        gate("V-CCN-GOV-THRESHOLD-%d" % pct, code == want, "lower bound %d%% -> exit %d %s (expected %d)" % (pct, code, verdict, want))

    sd = env(tmp, 90 * CALIB / 100.0)
    jdump(os.path.join(sd, "account-governor-override.json"), {"until": NOW + 3600, "reason": "Owner: finish release"})
    code, verdict = run(sd, "topup")
    gate("V-CCN-GOV-OVERRIDE-VALID", code == 0 and verdict == "ALLOW+OVERRIDE", "valid override at 90%% -> %s" % verdict)
    jdump(os.path.join(sd, "account-governor-override.json"), {"until": NOW - 1, "reason": "old"})
    gate("V-CCN-GOV-OVERRIDE-EXPIRED", run(sd)[0] == 3, "expired override does not override")
    jdump(os.path.join(sd, "account-governor-override.json"), {"until": NOW + 25 * 3600, "reason": "too long"})
    gate("V-CCN-GOV-OVERRIDE-TOOLONG", run(sd)[0] == 3, "until > 24 h away is rejected")
    jdump(os.path.join(sd, "account-governor-override.json"), {"until": NOW + 60, "reason": "  "})
    gate("V-CCN-GOV-OVERRIDE-NOREASON", run(sd)[0] == 3, "override without a reason is rejected")
    os.remove(os.path.join(sd, "account-governor-override.json"))
    gate("V-CCN-GOV-OVERRIDE-ABSENT", run(sd)[0] == 3, "absent override file = no override")

    # GEX44-only report: lower bound only, laptop missing; a reported pct can lift the estimate to a WARN, never a REFUSE
    sd = env(tmp, 70 * CALIB / 100.0, {"reported_pct": 92, "reported_at": NOW - 600})
    st = g.status(sd, NOW, [])
    code, verdict = run(sd)
    gate("V-CCN-GOV-ESTIMATE-WARN", code == 0 and verdict == "ALLOW+WARN" and st["pct_estimate"] == 92.0 and st["pct_lower_bound"] == 70.0,
         "lower 70%%, reported 92%% -> %s (estimate never refuses)" % verdict)
    sd = env(tmp, 70 * CALIB / 100.0, hosts=("gex44",))
    st = g.status(sd, NOW, [])
    gate("V-CCN-GOV-COVERAGE-PARTIAL", st["coverage"] == "PARTIAL" and st["missing_hosts"] == ["laptop"] and "LOWER BOUND ONLY" in st["confidence"]
         and run(sd) == (3, "REFUSE+UNKNOWN"),
         "laptop missing: coverage=%s, missing spend is unknown not zero -> refused (BAMR)" % st["coverage"])
    sd = env(tmp, 40 * CALIB / 100.0, {"reported_pct": 95, "reported_at": NOW - 5 * 86400})
    st = g.status(sd, NOW, [])
    gate("V-CCN-GOV-REPORT-STALE", st["pct_estimate"] == 40.0, "a reading from before the reset is ignored: estimate=%s" % st["pct_estimate"])

    sd = env(tmp, 50 * CALIB / 100.0, hosts=("gex44", "laptop"))
    st = g.status(sd, NOW, [])
    gate("V-CCN-GOV-COVERAGE-FULL", st["coverage"] == "FULL" and st["pct_lower_bound"] == 100.0 and run(sd)[0] == 3,
         "two hosts at 50%% each: FULL, 100%%, refused (merge sums hosts): %s" % st["per_host_api_eq_usd"])
    sd = env(tmp, 10.0, hosts=())
    st = g.status(sd, NOW, [])
    gate("V-CCN-GOV-COVERAGE-NONE", st["coverage"] == "NONE" and st["pct_lower_bound"] is None and run(sd) == (3, "REFUSE+UNKNOWN"),
         "no host reported -> NONE, UNKNOWN, refused (BAMR): coverage=%s" % st["coverage"])

    # a reset observed two weeks ago rolls forward to this week's: last week's measurement is stale, not summed
    old_reset = NOW - 15 * 86400
    sd = env(tmp, 99 * CALIB / 100.0, reset=old_reset, hosts=("gex44",))
    st = g.status(sd, NOW, [])
    gate("V-CCN-GOV-WEEKLY-ROLL", st["reset_at"] == old_reset + 14 * 86400 and st["stale_hosts"] == ["gex44"] and run(sd) == (3, "REFUSE+UNKNOWN"),
         "reset %+.0f d rolled to %+.0f d; old-window host excluded -> nothing known this window -> REFUSE+UNKNOWN (BAMR)" % ((old_reset - NOW) / 86400, (st["reset_at"] - NOW) / 86400))

    # window mismatch: a host measured against another reset is not summed
    sd = env(tmp, 99 * CALIB / 100.0)
    jdump(os.path.join(sd, "account-governor-hosts", "laptop.json"), {"api_eq_usd": 900.0, "reset_at": NOW - 9 * 86400})
    st = g.status(sd, NOW, [])
    gate("V-CCN-GOV-STALE-HOST", st["stale_hosts"] == ["laptop"] and st["lower_bound_usd"] == 990.0, "laptop measured on another window is excluded: %s" % st["stale_hosts"])

    # unknown telemetry (BAMR, Owner decision 2026-11-20: unknown or stale blocks autonomous model spend)
    sd = env(tmp, 99 * CALIB / 100.0, calib=None)
    gate("V-CCN-GOV-UNKNOWN-NOCALIB", run(sd) == (3, "REFUSE+UNKNOWN"), "no calibration, no official reading -> REFUSE+UNKNOWN")
    gate("V-BAMR-DETERMINISTIC", run(sd, "deterministic") == (0, "ALLOW+DETERMINISTIC"), "unknown quota never blocks work that spends no model quota")
    sd = tempfile.mkdtemp(dir=tmp)
    open(os.path.join(sd, "account-governor.json"), "w").write("{not json")
    gate("V-CCN-GOV-UNKNOWN-CORRUPT", run(sd) == (3, "REFUSE+UNKNOWN"), "corrupt config -> REFUSE+UNKNOWN")
    rows = [json.loads(x) for x in open(os.path.join(sd, "account-governor-ledger.jsonl"))]
    gate("V-CCN-GOV-LEDGER", rows and rows[-1]["verdict"] == "REFUSE+UNKNOWN" and rows[-1]["action"] == "arm", "every decision appends a ledger row: %s" % rows[-1])
    jdump(os.path.join(sd, "account-governor-override.json"), {"until": NOW + 3600, "reason": "Owner: run blind"})
    gate("V-BAMR-UNKNOWN-OVERRIDE", run(sd) == (0, "ALLOW+OVERRIDE"), "a valid Owner override still lifts an UNKNOWN refusal")

    # BAMR P1: a stray host file (a name not in the configured hosts) is never summed
    sd = env(tmp, 40 * CALIB / 100.0, hosts=("gex44", "laptop", "DESKTOP-X"))
    st = g.status(sd, NOW, [])
    gate("V-BAMR-UNEXPECTED-HOST", st["pct_lower_bound"] == 80.0 and st["unexpected_hosts"] == ["DESKTOP-X"],
         "laptop measured twice under two names is counted once: %s%% extra=%s" % (st["pct_lower_bound"], st["unexpected_hosts"]))
    p = subprocess.run([sys.executable, os.path.join(HERE, "account_governor.py"), "--state-dir", sd, "measure", "--host", "NOT-CONFIGURED", "--root", tmp],
                       capture_output=True, text=True)
    gate("V-BAMR-MEASURE-HOST", p.returncode == 2 and not os.path.exists(os.path.join(sd, "account-governor-hosts", "NOT-CONFIGURED.json")),
         "measure refuses a host name outside the configured set: exit %d" % p.returncode)
    # a host measurement older than host_fresh_s makes coverage PARTIAL -> unknown -> refused
    sd = env(tmp, 30 * CALIB / 100.0, hosts=("gex44", "laptop"))
    jdump(os.path.join(sd, "account-governor-hosts", "gex44.json"), {"api_eq_usd": 300.0, "reset_at": NOW - 3 * 86400, "measured_at": NOW - 4 * 3600})
    st = g.status(sd, NOW, [])
    gate("V-BAMR-HOST-OLD", st["coverage"] == "PARTIAL" and st["old_hosts"] == ["gex44"] and run(sd) == (3, "REFUSE+UNKNOWN"),
         "gex44 last measured 4 h ago (GEX44 down): %s old=%s" % (st["coverage"], st["old_hosts"]))

    # BAMR P1: the harness's official reading (statusline rate_limits) outranks the API-eq estimate
    def official(sd, captured, seven=None, five=None, source="harness_statusline"):
        rl = {}
        if seven is not None:
            rl["seven_day"] = {"used_percentage": seven, "resets_at": NOW + 2 * 86400}
        if five is not None:
            rl["five_hour"] = {"used_percentage": five, "resets_at": NOW + 3600}
        jdump(os.path.join(sd, "quota-reading.json"), {"captured_at": captured, "source": source, "rate_limits": rl or None})
    sd = env(tmp, 90 * CALIB / 100.0, hosts=("gex44", "laptop"))       # estimate says 180%
    official(sd, NOW - 60, seven=18)
    gate("V-BAMR-OFFICIAL-WINS", run(sd) == (0, "ALLOW+OFFICIAL"), "fresh official 18%% beats a miscalibrated 180%% estimate")
    official(sd, NOW - 60, seven=85)
    gate("V-BAMR-OFFICIAL-WEEKLY", run(sd)[0] == 3, "official 7d 85%% -> refused (15%% Owner reserve)")
    official(sd, NOW - 60, seven=10, five=80)
    gate("V-BAMR-5H-RESERVE", run(sd)[0] == 3, "official 5h 80%% -> refused (20%% Owner reserve, decision 3)")
    official(sd, NOW - 60, seven=10, five=79)
    gate("V-BAMR-5H-UNDER", run(sd) == (0, "ALLOW+OFFICIAL"), "official 5h 79%% -> allowed")
    sd2 = env(tmp, 10.0, hosts=("gex44", "laptop"), calib=None)        # no estimate possible
    official(sd2, NOW - 3600, seven=5)
    gate("V-BAMR-OFFICIAL-STALE", run(sd2) == (3, "REFUSE+UNKNOWN"), "an hour-old official reading is stale, not current")
    official(sd2, NOW - 60, five=5)
    gate("V-BAMR-OFFICIAL-NO7D", run(sd2) == (3, "REFUSE+UNKNOWN"), "a reading without the weekly window is not a quota picture")
    official(sd2, NOW - 60, source="absent")
    gate("V-BAMR-OFFICIAL-ABSENT", run(sd2) == (3, "REFUSE+UNKNOWN"), "harness sent no rate_limits -> unknown")
    jdump(os.path.join(sd2, "quota-reading.json"), {"captured_at": NOW - 60, "source": "harness_statusline",
                                                     "rate_limits": {"seven_day": {"used_percentage": 5, "resets_at": NOW - 10}}})
    gate("V-BAMR-OFFICIAL-ROLLED", run(sd2) == (3, "REFUSE+UNKNOWN"), "a reading whose window has since reset says nothing about the new one")
    st = g.status(sd, NOW, [])
    gate("V-BAMR-IMPLIED-CALIB", st["official"]["state"] == "FRESH" and st.get("implied_calibration_api_eq_per_100pct") == round(1800.0 / 0.10, 2),
         "status reports the calibration the official reading implies: %s" % st.get("implied_calibration_api_eq_per_100pct"))

    # reset inference from transcripts: a 3 h gap, spend only after it
    proj = os.path.join(tmp, "proj", "-p")
    os.makedirs(proj)
    def iso(t):
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))
    now = time.time()
    with open(os.path.join(proj, "s1.jsonl"), "w") as f:
        for i, (t, mid) in enumerate([(now - 6 * 3600, "a"), (now - 5.9 * 3600, "b"), (now - 2 * 3600, "c"), (now - 1.9 * 3600, "d")]):
            f.write(json.dumps({"timestamp": iso(t), "message": {"role": "assistant", "id": mid,
                    "usage": {"input_tokens": 1000000}}}) + "\n")
    root = os.path.join(tmp, "proj")
    rs = g.infer_reset([root], now)
    gate("V-CCN-GOV-INFER-RESET", rs is not None and abs(rs - (now - 2 * 3600)) < 2, "reset = first call after the 3.9 h gap: %.0f s ago" % (now - (rs or 0)))
    sp = g.measure_spend([root], rs, now)
    gate("V-CCN-GOV-MEASURE", sp["calls"] == 2 and abs(sp["api_eq_usd"] - 6.0) < 1e-6, "only the 2 calls after the reset are priced at $3/M: %s" % sp)
    proj2 = os.path.join(tmp, "proj2", "-q")
    os.makedirs(proj2)
    with open(os.path.join(proj2, "s2.jsonl"), "w") as f:
        for k in range(5):
            f.write(json.dumps({"timestamp": iso(now - 3600 * (5 - k)), "message": {"role": "assistant", "id": "x%d" % k, "usage": {"input_tokens": 1}}}) + "\n")
    gate("V-CCN-GOV-INFER-NOGAP", g.infer_reset([os.path.join(tmp, "proj2")], now) is None, "hourly calls leave no >= 2 h gap: reset is None, not guessed")

    # CLI exit code through the real entry point (process boundary)
    sd = env(tmp, 90 * CALIB / 100.0)
    p = subprocess.run([sys.executable, os.path.join(HERE, "account_governor.py"), "--state-dir", sd, "check", "--action", "arm"],
                       capture_output=True, text=True)
    gate("V-CCN-GOV-CLI-EXIT3", p.returncode == 3 and p.stdout.startswith("REFUSE"), "process exit=%d out=%s" % (p.returncode, p.stdout.strip()[:70]))

    # mutant: deciding on the estimate instead of the lower bound must flip the WARN case to a refusal
    mm = mutant_module()
    sd = env(tmp, 70 * CALIB / 100.0, {"reported_pct": 92, "reported_at": NOW - 600})
    st = mm.status(sd, NOW, [])
    mc, mv, _ = mm.decide(st, (False, "none"), "arm")
    gate("V-CCN-GOV-MUTANT", mc == 3 and run(sd)[0] == 0, "estimate-based mutant refuses (exit %d), real code allows" % mc)

print("CCN_GOV_PASS=%d/%d" % (passes, passes + fails))
sys.exit(0 if fails == 0 else 1)
