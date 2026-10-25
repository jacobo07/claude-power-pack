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


def env(tmp, spend, cfg_extra=None, hosts=("gex44",), calib=CALIB, reset=NOW - 3 * 86400):
    sd = tempfile.mkdtemp(dir=tmp)
    cfg = {"reset_at": reset}
    if calib is not None:
        cfg["calibration_api_eq_per_100pct"] = calib
    cfg.update(cfg_extra or {})
    jdump(os.path.join(sd, "account-governor.json"), cfg)
    for h in hosts:
        jdump(os.path.join(sd, "account-governor-hosts", h + ".json"), {"api_eq_usd": spend, "reset_at": reset, "host": h})
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
    gate("V-CCN-GOV-COVERAGE-PARTIAL", st["coverage"] == "PARTIAL" and st["missing_hosts"] == ["laptop"] and "LOWER BOUND ONLY" in st["confidence"],
         "coverage=%s missing=%s confidence=%s" % (st["coverage"], st["missing_hosts"], st["confidence"]))
    sd = env(tmp, 40 * CALIB / 100.0, {"reported_pct": 95, "reported_at": NOW - 5 * 86400})
    st = g.status(sd, NOW, [])
    gate("V-CCN-GOV-REPORT-STALE", st["pct_estimate"] == 40.0, "a reading from before the reset is ignored: estimate=%s" % st["pct_estimate"])

    sd = env(tmp, 50 * CALIB / 100.0, hosts=("gex44", "laptop"))
    st = g.status(sd, NOW, [])
    gate("V-CCN-GOV-COVERAGE-FULL", st["coverage"] == "FULL" and st["pct_lower_bound"] == 100.0 and run(sd)[0] == 3,
         "two hosts at 50%% each: FULL, 100%%, refused (merge sums hosts): %s" % st["per_host_api_eq_usd"])
    sd = env(tmp, 10.0, hosts=())
    st = g.status(sd, NOW, [])
    gate("V-CCN-GOV-COVERAGE-NONE", st["coverage"] == "NONE" and st["pct_lower_bound"] is None and run(sd) == (0, "ALLOW+UNKNOWN"),
         "no host reported -> NONE, UNKNOWN, allowed: coverage=%s" % st["coverage"])

    # a reset observed two weeks ago rolls forward to this week's: last week's measurement is stale, not summed
    old_reset = NOW - 15 * 86400
    sd = env(tmp, 99 * CALIB / 100.0, reset=old_reset)
    st = g.status(sd, NOW, [])
    gate("V-CCN-GOV-WEEKLY-ROLL", st["reset_at"] == old_reset + 14 * 86400 and st["stale_hosts"] == ["gex44"] and run(sd)[0] == 0,
         "reset %+.0f d rolled to %+.0f d; host measured on the old window excluded, not refused" % ((old_reset - NOW) / 86400, (st["reset_at"] - NOW) / 86400))

    # window mismatch: a host measured against another reset is not summed
    sd = env(tmp, 99 * CALIB / 100.0)
    jdump(os.path.join(sd, "account-governor-hosts", "laptop.json"), {"api_eq_usd": 900.0, "reset_at": NOW - 9 * 86400})
    st = g.status(sd, NOW, [])
    gate("V-CCN-GOV-STALE-HOST", st["stale_hosts"] == ["laptop"] and st["lower_bound_usd"] == 990.0, "laptop measured on another window is excluded: %s" % st["stale_hosts"])

    # unknown telemetry
    sd = env(tmp, 99 * CALIB / 100.0, calib=None)
    gate("V-CCN-GOV-UNKNOWN-NOCALIB", run(sd) == (0, "ALLOW+UNKNOWN"), "no calibration -> ALLOW+UNKNOWN, not a refusal")
    sd = tempfile.mkdtemp(dir=tmp)
    open(os.path.join(sd, "account-governor.json"), "w").write("{not json")
    gate("V-CCN-GOV-UNKNOWN-CORRUPT", run(sd) == (0, "ALLOW+UNKNOWN"), "corrupt config -> ALLOW+UNKNOWN")
    rows = [json.loads(x) for x in open(os.path.join(sd, "account-governor-ledger.jsonl"))]
    gate("V-CCN-GOV-LEDGER", rows and rows[-1]["verdict"] == "ALLOW+UNKNOWN" and rows[-1]["action"] == "arm", "every decision appends a ledger row: %s" % rows[-1])

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
