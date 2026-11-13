"""Patch autopilot.py + test_autopilot.py: a checkpoint hold's path is `evidence` or `residual`; an empty path parks
without a judge call (Owner 2026-11-13 'y', pane c26eafbf). Usage: holdfix.py <dir>. Prints the sha256 of both files."""
import hashlib, sys

D = sys.argv[1]


def patch(p, pairs):
    s = open(p, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    s = s.replace("\r\n", "\n")
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:70], s.count(old))
        s = s.replace(old, new)
    open(p, "w", encoding="utf-8", newline="").write(s.replace("\n", nl))
    return hashlib.sha256(s.encode()).hexdigest()[:16]


a = patch(D + "/autopilot.py", [
    ("# ---------------------------------------------------------------- the per-lane transition\n"
     "def lane_tick(",
     "def hold_checkpoint(hold: dict) -> str:\n"
     "    \"\"\"The path a checkpoint hold names: `evidence`, or `residual` for a pivot hold (gsd_mission leaves evidence null\n"
     "    there). Owner 2026-11-13 (pane c26eafbf): S36K's METHOD_PIVOT_REQUIRED hold was judged with an empty path.\"\"\"\n"
     "    return hold.get(\"evidence\") or hold.get(\"residual\") or \"\"\n\n\n"
     "# ---------------------------------------------------------------- the per-lane transition\n"
     "def lane_tick("),
    ("        checkpoint = hold.get(\"evidence\") or \"\"\n"
     "        if ls.get(\"judged_for\") == f\"{mid}:{hold.get('set_at')}\":\n"
     "            return\n",
     "        checkpoint = hold_checkpoint(hold)\n"
     "        if ls.get(\"judged_for\") == f\"{mid}:{hold.get('set_at')}\":\n"
     "            return\n"
     "        if not checkpoint:  # a judge with no path can only say INCONCLUSIVE: park instead of paying for it\n"
     "            ls[\"judged_for\"] = f\"{mid}:{hold.get('set_at')}\"\n"
     "            return _park(st, ls, lane[\"name\"], f\"checkpoint hold of {mid} names no evidence or residual path; \"\n"
     "                                               \"not judged\")\n"),
])
t = patch(D + "/test_autopilot.py", [
    ("    check(\"V-EVO-OTHER-PARK-HOLDS\", st[\"lanes\"][\"L\"][\"status\"] == \"PARKED\")\n",
     "    check(\"V-EVO-OTHER-PARK-HOLDS\", st[\"lanes\"][\"L\"][\"status\"] == \"PARKED\")\n"
     "    # Owner 2026-11-13 (pane c26eafbf): a pivot hold names its path in `residual` (evidence null): judge that path,\n"
     "    # and never call the judge with an empty one\n"
     "    check(\"V-AP-HOLD-PATH-ORDER\", ap.hold_checkpoint({\"evidence\": \"/e\", \"residual\": \"/r\"}) == \"/e\"\n"
     "          and ap.hold_checkpoint({\"evidence\": None, \"residual\": \"/r\"}) == \"/r\" and ap.hold_checkpoint({}) == \"\")\n"
     "    judged = []\n"
     "    st = evo_fresh([LA], {\"lever\": \"lev_a\"})  # evo_fresh resets ap.judge: install the recorder after it\n"
     "    ap.judge = lambda lane, ck, prod: judged.append(ck) or dict(full, _tokens=1)\n"
     "    rec[\"owner_hold\"].update(set_at=7903, evidence=None, residual=str(tmp / \"ck.md\")); recp.write_text(json.dumps(rec))\n"
     "    ap.lane_tick(st, lanes[0], False)\n"
     "    check(\"V-AP-PIVOT-HOLD-JUDGES-RESIDUAL\", judged == [str(tmp / \"ck.md\")])\n"
     "    st = evo_fresh([LA], {\"lever\": \"lev_a\"})\n"
     "    ap.judge = lambda lane, ck, prod: judged.append(ck) or dict(full, _tokens=1)\n"
     "    judged.clear()\n"
     "    rec[\"owner_hold\"].update(set_at=7904, evidence=None, residual=None); recp.write_text(json.dumps(rec))\n"
     "    ap.lane_tick(st, lanes[0], False)\n"
     "    check(\"V-AP-EMPTY-HOLD-PARKS-UNJUDGED\", not judged and st[\"lanes\"][\"L\"][\"status\"] == \"PARKED\")\n"
     "    rec[\"owner_hold\"].update(evidence=str(tmp / \"ck.md\")); rec[\"owner_hold\"].pop(\"residual\", None)\n"
     "    recp.write_text(json.dumps(rec))\n"),
    ("         \"trigger_negation_off\": lambda m: setattr(m, \"TRIGGER_NEGATED\", __import__(\"re\").compile(r\"(?!x)x\")),\n",
     "         \"trigger_negation_off\": lambda m: setattr(m, \"TRIGGER_NEGATED\", __import__(\"re\").compile(r\"(?!x)x\")),\n"
     "         \"hold_residual_ignored\": lambda m: setattr(m, \"hold_checkpoint\", lambda h: h.get(\"evidence\") or \"\"),\n"),
])
print("autopilot.py", a, "test_autopilot.py", t)
