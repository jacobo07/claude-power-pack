"""WU-S2: programme authority gates. Run: python tools/test_programme_spend.py (prints PROGRAMME_SPEND_PASS=n/m).

Hermetic: own state dir, own projects dir; a launch can never reach a real claude (CPP_CLAUDE_EXE is a stub)."""
import json
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="programme-spend-")
os.environ["GSD_LONG_RUN_STATE_DIR"] = TMP
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(Path(TMP) / "sessions")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP
os.environ["CPP_CLAUDE_JOBS_DIR"] = str(Path(TMP) / "jobs")
os.environ["CPP_CLAUDE_EXE"] = str(Path(TMP) / "no-such-claude.exe")
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gsd_mission as gm  # noqa: E402
import mission_spend as ms  # noqa: E402

gm.progress_fingerprint = lambda work_dir: None
PASS = FAIL = 0


def check(name, ok, detail=""):
    global PASS, FAIL
    PASS, FAIL = PASS + bool(ok), FAIL + (not ok)
    print(("PASS " if ok else "FAIL ") + name + (" " + str(detail) if detail else ""))


ROOT = tempfile.mkdtemp(prefix="ps-root-")
PROJ = Path(TMP) / "projects"
PROJ.mkdir()
GOAL = "autonomy-t"
d = ms.goal_declare(GOAL, 10_000_000, "test", [ROOT])
check("goal declared", d.get("ok"), d)


def transcript(sid, cwd, tokens, human):
    p = PROJ / ms.encode_cwd(cwd)
    p.mkdir(exist_ok=True)
    rows = []
    if human:
        rows.append({"type": "user", "cwd": cwd, "message": {"role": "user", "content": "hello"}})
    rows.append({"type": "assistant", "cwd": cwd, "uuid": sid + "a",
                 "message": {"id": sid + "m", "model": "x", "usage": {"input_tokens": tokens}}})
    (p / f"{sid}.jsonl").write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")


# (1) plain arm binds by root; a NEW mission id under the same root binds the same goal
m1 = gm.arm(ROOT, "echo a", launch=False)["mission"]
m2 = gm.arm(ROOT, "echo b", launch=False)["mission"]
check("arm binds ledger_goal (m1)", m1.get("ledger_goal") == GOAL, m1.get("ledger_goal"))
check("new mission id binds same goal (m2)", m2.get("ledger_goal") == GOAL and m2["mission_id"] != m1["mission_id"])
other = tempfile.mkdtemp(prefix="ps-other-")
m3 = gm.arm(other, "echo c", launch=False)["mission"]
check("cwd outside any root stays unbound", not m3.get("ledger_goal"))

# (2)(3) one view, roles
W, C, I, X = "w" * 8 + "-0000", "c" * 8 + "-0000", "i" * 8 + "-0000", "x" * 8 + "-0000"
transcript(W, ROOT, 500_000, True)
transcript(C, ROOT, 300_000, True)
transcript(I, ROOT, 200_000, True)
led = ms._goal_ledger(GOAL)
ms.goal_settle(GOAL, W, 500_000)
ms.goal_settle(GOAL, C, 300_000)
v = ms.programme_spend(GOAL, projects=PROJ, mission_sids={W})
role = {r["sid"]: r["role"] for r in v["sessions"]}
check("roles worker/control/interactive", (role[W], role[C], role[I]) == ("worker", "control", "interactive"), role)
check("settled counts ledger only; interactive not productive", v["settled"] == 800_000 and v["interactive_processed"] == 200_000
      and v["productive"] == {"worker": 500_000, "control": 300_000}, v)
check("available = cap - settled - reserved - unknown", v["available"] == 10_000_000 - 800_000 - v["reserved"] and v["available_certain"], v)

# (new mission id must not reset spend)
v2 = ms.programme_spend(GOAL, projects=PROJ, mission_sids={W, "n" * 8 + "-0001"})
check("new mission id under same root does not reset spend", v2["settled"] == v["settled"] and v2["available"] == v["available"])

# (4) unattributed material spend = telemetry failure; UNKNOWN is not zero
transcript(X, ROOT, 400_000, False)
v3 = ms.programme_spend(GOAL, projects=PROJ, mission_sids={W})
check("unattributed material spend flagged", not v3["telemetry_ok"] and v3["telemetry_failures"][0]["kind"] == "unattributed_material_spend", v3["telemetry_failures"])
check("unknown reduces available, not certain", v3["unknown"] == 400_000 and not v3["available_certain"]
      and v3["available"] == v["available"] - 400_000)
ms.goal_settle(GOAL, "g" * 8 + "-0000", 123_000)      # ledger charge, no transcript
v4 = ms.programme_spend(GOAL, projects=PROJ, mission_sids={W})
check("ledger charge without transcript is UNKNOWN", v4["unknown"] == 523_000, v4["unknown"])
check("undeclared goal is UNKNOWN, not empty", ms.programme_spend("nope-g", projects=PROJ)["ok"] is False)

# WU-S7b: an interactive pane's charge path -- role=interactive in the LEDGER, apart from productive spend
IA = "a" * 8 + "-0000"
transcript(IA, ROOT, 150_000, True)
ms.write_binding(IA, GOAL, "test", role="interactive")
rn = ms.goal_renew(GOAL, IA, 150_000, 1000, "h")
v5 = ms.programme_spend(GOAL, projects=PROJ, mission_sids={W})
r5 = {r["sid"]: r for r in v5["sessions"]}
check("S7b interactive renew charged role=interactive in ledger", rn.get("ok", True) and
      ms._goal_ledger(GOAL)._gfold(ms._goal_ledger(GOAL)._read())["roles"].get(IA) == "interactive", rn)
check("S7b interactive apart from productive", r5[IA]["role"] == "interactive" and v5["interactive_settled"] == 150_000
      and v5["productive"] == {"worker": 500_000, "control": 300_000 + 123_000}, (v5["productive"], v5.get("interactive_settled")))
check("S7b interactive still counts toward the cap", v5["settled"] == v4["settled"] + 150_000, v5["settled"])
ms.write_binding(("b" * 8) + "-0000", GOAL, "test")
rp = ms.goal_renew(GOAL, ("b" * 8) + "-0000", 1000, 1000, "h")
check("S7b RED: unmarked pane stays productive", ms._goal_ledger(GOAL)._gfold(ms._goal_ledger(GOAL)._read())["roles"].get(("b" * 8) + "-0000") != "interactive", rp)

# mutation drill: root binding disabled -> the binding gate must go red
real = ms.goal_for_cwd
ms.goal_for_cwd = lambda cwd: None
mut = gm.arm(ROOT, "echo d", launch=False)["mission"]
ms.goal_for_cwd = real
check("MUTATION: unbinding goal_for_cwd is caught (binding absent)", mut.get("ledger_goal") != GOAL)

print(f"PROGRAMME_SPEND_PASS={PASS}/{PASS + FAIL}")
sys.exit(1 if FAIL else 0)
