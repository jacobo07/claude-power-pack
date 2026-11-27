#!/usr/bin/env python3
"""V-GOV-CSWAP-*: the account governor reads the cswap auto cron's last poll (Owner 2026-11-27, pane 31498a3e:
"haz autoswitch cuando sea necesario" / "cuando lleguen al 100%"). Arms refuse only when every managed account's
7-day window is full; an absent or stale reading leaves the old decision untouched. Run: python tools/test_account_governor_cswap.py"""
import json
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import account_governor as ag  # noqa: E402

results = []


def check(name, cond):
    results.append((name, bool(cond)))


def iso(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def write_log(path, now, wins, age=30, tail_noise=True):
    rows = [{"schemaVersion": 1, "event": "poll", "ts": iso(now - 900), "active": {"number": 1},
             "windowsPct": {"1": {"7d": 99.95}, "2": {"7d": 99.95}}},
            {"schemaVersion": 1, "event": "poll", "ts": iso(now - age), "active": {"number": 4}, "windowsPct": wins}]
    if tail_noise:
        rows.append({"schemaVersion": 1, "event": "no-switch", "ts": iso(now - age), "reason": "below-threshold"})
    with open(path, "w", encoding="utf-8") as f:
        f.write("not json\n" + "\n".join(json.dumps(r) for r in rows) + "\n")


def main():
    now = time.time()
    tmp = tempfile.mkdtemp(prefix="gov-cswap-")
    log = os.path.join(tmp, "cswap-auto.log")
    state = os.path.join(tmp, "state")
    roots = [os.path.join(tmp, "no-transcripts")]
    os.makedirs(state)
    os.makedirs(roots[0])
    keep_log = ag.CSWAP_LOG
    ag.CSWAP_LOG = log
    try:
        room = {"1": {"7d": 0.0}, "2": {"5h": 0.0, "7d": 98.0}, "3": {"7d": 0.0}, "4": {"7d": 42.0}}
        write_log(log, now, room)
        cap = ag.cswap_capacity(now)
        check("V-GOV-CSWAP-READS-NEWEST-POLL", cap is not None and cap["active"] == 4 and cap["min_7d"] == 0.0
              and cap["seven_day"]["2"] == 98.0)
        code, verdict, why, _ = ag.check(state, "arm", now, roots)
        check("V-GOV-CSWAP-ALLOWS-WITH-ROOM", code == 0 and verdict == "ALLOW+CSWAP" and "account 1" in why)
        full = {k: {"7d": 99.95} for k in ("1", "2", "3", "4")}
        write_log(log, now, full)
        code, verdict, why, _ = ag.check(state, "arm", now, roots)
        check("V-GOV-CSWAP-REFUSES-ALL-FULL", code == 3 and verdict == "REFUSE" and "every managed account" in why)
        with open(os.path.join(state, "account-governor-override.json"), "w") as f:
            json.dump({"until": iso(now + 3600), "reason": "test override"}, f)
        code, verdict, _, _ = ag.check(state, "arm", now, roots)
        check("V-GOV-CSWAP-OVERRIDE-LIFTS", code == 0 and verdict == "ALLOW+OVERRIDE")
        os.remove(os.path.join(state, "account-governor-override.json"))
        write_log(log, now, room, age=ag.CSWAP_FRESH_S + 60)
        check("V-GOV-CSWAP-STALE-IGNORED", ag.cswap_capacity(now) is None)
        code, verdict, _, _ = ag.check(state, "arm", now, roots)
        check("V-GOV-CSWAP-STALE-KEEPS-OLD-DECISION", verdict != "ALLOW+CSWAP")
        write_log(log, now, room)
        check("V-GOV-CSWAP-DETERMINISTIC-UNTOUCHED", ag.cswap_decide(ag.cswap_capacity(now), (False, "none"),
                                                                        "deterministic") is None)
        os.environ["CPP_GOVERNOR_CSWAP"] = "off"
        try:
            check("V-GOV-CSWAP-KILL-SWITCH", ag.cswap_decide(ag.cswap_capacity(now), (False, "none"), "arm") is None)
        finally:
            os.environ.pop("CPP_GOVERNOR_CSWAP", None)
        os.remove(log)
        check("V-GOV-CSWAP-ABSENT-LOG", ag.cswap_capacity(now) is None)
        write_log(log, now, {"1": {"5h": 10.0}})
        check("V-GOV-CSWAP-NO-WEEKLY-IGNORED", ag.cswap_capacity(now) is None)
    finally:
        ag.CSWAP_LOG = keep_log
    for n, ok in results:
        print(("PASS " if ok else "FAIL ") + n)
    bad = [n for n, ok in results if not ok]
    print("GOV_CSWAP_PASS" if not bad else "GOV_CSWAP_FAIL %s" % bad)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
