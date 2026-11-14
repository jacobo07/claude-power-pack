"""RETRY keeps the judgment (Owner 2026-11-14 'y', pane c26eafbf; hand-off item 3 from pane 4246d04c).
Usage: retryfix.py <dir> [--revert-control]. Prints the sha256 prefixes of both files."""
import hashlib, sys

D = sys.argv[1]
CONTROL = "--revert-control" in sys.argv


def patch(p, pairs):
    s = open(p, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    s = s.replace("\r\n", "\n")
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:70], s.count(old))
        s = s.replace(old, new)
    open(p, "w", encoding="utf-8", newline="").write(s.replace("\n", nl))
    return hashlib.sha256(s.encode()).hexdigest()[:16]


code = [("    elif res == \"RETRY\":\n"
         "        ls[\"arm_fails\"] = ls.get(\"arm_fails\", 0) + 1\n"
         "        ls[\"judged_for\"] = None\n",
         "    elif res == \"RETRY\":\n"
         "        ls[\"arm_fails\"] = ls.get(\"arm_fails\", 0) + 1\n"
         "        ls[\"judged_for\"] = None\n"
         "        # 2026-11-14 (Owner 'y', pane c26eafbf): nothing irreversible happened, but the judgment and EVO already\n"
         "        # counted this checkpoint; the next tick re-plans from it (resumable_plan) instead of re-judging it\n"
         "        ls[\"pending_plan\"] = pend\n")]
test = [("    check(\"V-AP-DIRTY-NO-MISSION-ACT\", not calls and st[\"lanes\"][\"L\"][\"status\"] != \"PARKED\"\n"
         "          and st[\"lanes\"][\"L\"][\"arm_fails\"] == 1)\n",
         "    check(\"V-AP-DIRTY-NO-MISSION-ACT\", not calls and st[\"lanes\"][\"L\"][\"status\"] != \"PARKED\"\n"
         "          and st[\"lanes\"][\"L\"][\"arm_fails\"] == 1)\n"
         "    # 2026-11-14 (Owner 'y', pane c26eafbf): a RETRY keeps the judgment; the next tick re-plans from it and does\n"
         "    # not call the judge again, so the checkpoint's class and graph credit are counted once\n"
         "    check(\"V-AP-RETRY-KEEPS-JUDGMENT\", (st[\"lanes\"][\"L\"].get(\"pending_plan\") or {}).get(\"for\", \"\").endswith(\":100\"))\n"
         "    _jr, _kj = {\"n\": 0}, ap.judge\n"
         "    ap.judge = lambda *a: (_jr.__setitem__(\"n\", _jr[\"n\"] + 1), _kj(*a))[1]\n"
         "    sh_out[\"dirty\"] = \"\"\n"
         "    calls.clear()\n"
         "    ap.lane_tick(st, lanes[0], False)\n"
         "    check(\"V-AP-RETRY-REARMS-WITHOUT-REJUDGE\", _jr[\"n\"] == 0 and any(c[0] == \"arm\" for c in calls)\n"
         "          and len([r for r in ledger() if r[\"kind\"] == \"judge\"]) == 1\n"
         "          and len([r for r in ledger() if r[\"kind\"] == \"replan_resume\"]) == 1)\n"
         "    ap.judge = _kj\n")]
a = patch(D + "/autopilot.py", code) if not CONTROL else "control-no-code-change"
t = patch(D + "/test_autopilot.py", test)
print("autopilot.py", a, "test_autopilot.py", t)
