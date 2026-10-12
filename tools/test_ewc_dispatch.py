"""V-EWC-HB gates: incident fixture -> node dispatcher Stop-chain -> merged JSON `decision`.

Sibling of tools/test_hook_boundary.py (that file is CDIO-specific). Drives the REAL
hooks/hook-dispatcher.js (--event=Stop-chain) with every chain member as shipped, in a temp
HOME. The chain resolves the EWC member at ../skills/claude-power-pack/hooks/, which only
exists in the installed layout, so the test builds that layout: a copy of hooks/ plus a
directory junction skills/claude-power-pack -> this worktree. Nothing outside tmp is written.
"""
import json, os, subprocess, sys, tempfile, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "tools" / "fixtures" / "ewc"
REPO = "abcdef0123456"
sys.path.insert(0, str(ROOT))
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("[PASS] " if ok else "[FAIL] ") + name + (("  :: " + detail) if detail and not ok else ""))


base = Path(tempfile.mkdtemp(prefix="ewc-hb-"))
layout = base / "layout"
shutil.copytree(ROOT / "hooks", layout / "hooks", ignore=shutil.ignore_patterns("tests", "node_modules"))
(layout / "skills").mkdir()
jn = subprocess.run(["cmd", "/c", "mklink", "/J", str(layout / "skills" / "claude-power-pack"), str(ROOT)],
                    capture_output=True, text=True) if os.name == "nt" else None
if os.name != "nt":
    os.symlink(ROOT, layout / "skills" / "claude-power-pack")
DISP = layout / "hooks" / "hook-dispatcher.js"
check("V-EWC-HB0 installed layout built: EWC member resolvable from dispatcher dir",
      (layout / "skills" / "claude-power-pack" / "hooks" / "gsd_stop_continuation.js").exists(),
      (jn.stdout + jn.stderr) if jn else "")

_hr = base / "highram.js"
_hr.write_text("require('os').freemem = () => 64 * 1024 * 1048576;\n", encoding="utf8")


def dispatch(mode, with_ledger, case="complete", sid="hb1"):
    home = Path(tempfile.mkdtemp(dir=base))
    (home / ".claude" / "state").mkdir(parents=True)
    (home / ".claude" / "logs").mkdir(parents=True)
    goals = home / "goals"
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), GSDX_GOALS_ROOT=str(goals),
               NODE_OPTIONS="--require " + str(_hr).replace("\\", "/"))
    for k in ("CPP_GSD_CONT_FORCE", "CPP_GSD_STOP_CONTINUATION", "CPP_EWC_GATE", "CLAUDE_STATE_DIR"):
        env.pop(k, None)
    if mode:
        env["CPP_EWC_GATE"] = mode
    if with_ledger:
        from modules.gsd_x.goal import session_scope as ss
        os.environ["GSDX_GOALS_ROOT"] = str(goals)
        ss.add(REPO, sid, text="Re-run the gate for module X", source="test", severity="RED",
               actionability="NOW", owner_class="AGENT", next_action="Do the work: re-run the gate")
    payload = {"session_id": sid, "hook_event_name": "Stop", "cwd": str(home),
               "transcript_path": str(FIX / (case + ".jsonl"))}
    r = subprocess.run(["node", str(DISP), "--event=Stop-chain"], input=json.dumps(payload),
                       capture_output=True, text=True, env=env, cwd=str(home), timeout=400)
    try:
        out = json.loads(r.stdout or "{}")
    except ValueError:
        out = {"_unparseable": r.stdout[:200]}
    rp = home / ".claude" / "state" / "autonomy-decisions.jsonl"
    rec = [json.loads(l) for l in rp.read_text(encoding="utf8").splitlines() if l.strip()] if rp.exists() else []
    return out, rec


out, rec = dispatch("enforce", True)
check("V-EWC-HB1 enforce: dispatcher Stop-chain merged JSON keeps decision=block (ledger obligation, clean transcript)",
      out.get("decision") == "block" and "UNRESOLVED AGENT-OWNED" in out.get("reason", ""), json.dumps(out)[:300])
check("V-EWC-HB2 enforce: receipt is CONTINUE_*, mode=enforce, would_block",
      bool(rec) and rec[-1].get("category", "").startswith("CONTINUE_") and rec[-1].get("mode") == "enforce"
      and rec[-1].get("would_block") is True, str(rec)[-300:])
out, rec = dispatch("shadow", True)
check("V-EWC-HB3 shadow: dispatcher never emits a block, receipt says would_block",
      out.get("decision") != "block" and bool(rec) and rec[-1].get("would_block") is True
      and rec[-1].get("mode") == "shadow", json.dumps(out)[:300] + str(rec)[-200:])
out, rec = dispatch(None, True)
check("V-EWC-HB4 default interactive (no marker, no env) is shadow: no block through the dispatcher",
      out.get("decision") != "block" and bool(rec) and rec[-1].get("mode") == "shadow", json.dumps(out)[:300])
out, rec = dispatch("enforce", False)
check("V-EWC-HB5 enforce control, nothing open: not blocked, STOP_COMPLETE",
      out.get("decision") != "block" and bool(rec) and rec[-1].get("category") == "STOP_COMPLETE",
      json.dumps(out)[:300] + str(rec)[-200:])
out, rec = dispatch("off", True)
check("V-EWC-HB6 off: no block, no gate receipt", out.get("decision") != "block" and not rec, json.dumps(out)[:300])

try:
    os.rmdir(layout / "skills" / "claude-power-pack")     # drop the junction/symlink BEFORE rmtree touches the worktree
except OSError:
    pass
if not (layout / "skills" / "claude-power-pack").exists():
    shutil.rmtree(base, ignore_errors=True)
print("EWC_HB_PASS=%d/%d" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
