from pathlib import Path
p = Path("tools/gsd_mission.py")
s = p.read_bytes().decode("utf-8")
crlf = "\r\n" in s
block = Path("_logs/wuadv/block.py").read_text(encoding="utf-8")
if crlf:
    block = block.replace("\n", "\r\n")
anchor = "def supervise(now: float | None = None"
assert s.count(anchor) == 1
s = s.replace(anchor, block + "def _supervise_core(now: float | None = None", 1)

# step 3: goal-aware admission
old = "    remaining = None\n    if rec.get(\"token_estimate\"):\n        spent = (measure or ms.processed_tokens)(rec)"
if crlf:
    old = old.replace("\n", "\r\n")
assert s.count(old) == 1
new = old.replace("    remaining = None", "    remaining = None\n    goal_rem = goal_headroom((rec.get(\"goal\") or {}).get(\"ce_goal\") or os.environ.get(\"CPP_CE_GOAL\"))", 1) if not crlf else None
if crlf:
    new = old.replace("    remaining = None", "    remaining = None\r\n    goal_rem = goal_headroom((rec.get(\"goal\") or {}).get(\"ce_goal\") or os.environ.get(\"CPP_CE_GOAL\"))", 1)
s = s.replace(old, new, 1)
old2 = "    try:\n        res = ra.admit(route, ra.load_floors(floors_path), remaining=remaining)"
new2 = ("    if goal_rem is not None:\n        remaining = goal_rem if remaining is None else min(remaining, goal_rem)\n" + old2)
if crlf:
    old2 = old2.replace("\n", "\r\n")
    new2 = new2.replace("\n", "\r\n")
assert s.count(old2) == 1
s = s.replace(old2, new2, 1)
old3 = "\"need_with_margin\": res.get(\"need_with_margin\"), \"remaining\": remaining,"
assert s.count(old3) == 1
s = s.replace(old3, old3 + " \"goal_remaining\": goal_rem,", 1)

# arm_chain: ce_goal
old4 = "    kw.pop(\"launch\", None)\n    rec = arm(cwd, resume_command, launch=False, **kw)[\"mission\"]\n    mid = rec[\"mission_id\"]\n"
if crlf:
    old4 = old4.replace("\n", "\r\n")
assert s.count(old4) == 1
new4 = ("    kw.pop(\"launch\", None)\n    ce_goal = kw.pop(\"ce_goal\", None)\n"
        "    rec = arm(cwd, resume_command, launch=False, **kw)[\"mission\"]\n    mid = rec[\"mission_id\"]\n"
        "    if ce_goal:\n        rec = transition(mid, expect_epoch=rec[\"epoch\"], expect_state=rec[\"state\"], event=\"ce_goal_bound\",\n"
        "                         goal={**(rec.get(\"goal\") or {}), \"ce_goal\": ce_goal})\n")
if crlf:
    new4 = new4.replace("\n", "\r\n")
s = s.replace(old4, new4, 1)
p.write_bytes(s.encode("utf-8"))
print("patched, crlf=", crlf)
