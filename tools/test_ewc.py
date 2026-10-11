"""V-EWC gate: Stop hooks vs closure fixtures (target behaviour; RED until E2+)."""
import json, os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "tools" / "fixtures" / "ewc"
HOOKS = ["hooks/closer-guard.js", "hooks/gsd_stop_continuation.js"]


def run_stop(case):
    """Run both real Stop hooks in a temp HOME; return (blocked, receipts)."""
    with tempfile.TemporaryDirectory() as home:
        env = dict(os.environ, HOME=home, USERPROFILE=home)
        for k in ("CPP_GSD_CONT_FORCE", "CPP_GSD_STOP_CONTINUATION"):
            env.pop(k, None)
        (Path(home) / ".claude" / "state").mkdir(parents=True)
        (Path(home) / ".claude" / "logs").mkdir(parents=True)
        payload = {"session_id": "ewc-" + case, "hook_event_name": "Stop",
                   "transcript_path": str(FIX / (case + ".jsonl")), "cwd": str(ROOT)}
        blocked = False
        for h in HOOKS:
            r = subprocess.run(["node", str(ROOT / h)], input=json.dumps(payload),
                               capture_output=True, text=True, env=env, cwd=str(ROOT), timeout=30)
            try:
                out = json.loads(r.stdout or "{}")
            except ValueError:
                out = {}
            if out.get("decision") == "block":
                blocked = True
        rp = Path(home) / ".claude" / "state" / "autonomy-decisions.jsonl"
        rec = rp.read_text(encoding="utf8") if rp.exists() else ""
        return blocked, rec


results = []


def check(name, ok):
    results.append(ok)
    print(("[PASS] " if ok else "[FAIL] ") + name)


b, rec = run_stop("incident")
check("V-EWC-1 incident: blocked or CONTINUE_* receipt", b or "CONTINUE_" in rec)
b, rec = run_stop("complete")
check("V-EWC-2a complete: not blocked", not b)
check("V-EWC-2b complete: STOP_COMPLETE receipt", "STOP_COMPLETE" in rec)
b, rec = run_stop("human_only")
check("V-EWC-3a human-only: not blocked", not b)
check("V-EWC-3b human-only: STOP_HUMAN_GATE receipt", "STOP_HUMAN_GATE" in rec)
print("EWC_PASS=%d/%d" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
