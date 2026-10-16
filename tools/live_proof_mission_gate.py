#!/usr/bin/env python
"""S0-DONE-5 live proof: the REAL hook dispatcher denies a PreToolUse PowerShell call of a synthetic held-out worker
whose next call would pass the hard cap, and admits the control. State dir is a temp dir (env override read by
hooks/lib/mission_gate.js); the dispatcher, session_budget_guard.js and mission_gate.js are the installed ones.
Usage: python tools/live_proof_mission_gate.py   -> exit 0 only when deny AND control both behave."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="live-proof-gate-")
for k, v in (("GSD_LONG_RUN_STATE_DIR", TMP), ("GSD_AUTORUN_MARKER_DIR", TMP), ("CPP_MISSION_RECOVERY", "off"),
             ("GSD_LONG_RUN_SESSIONS_DIR", f"{TMP}/sessions"), ("CPP_CLAUDE_JOBS_DIR", f"{TMP}/jobs"),
             ("GSD_LONG_RUN_PROJECTS_DIR", f"{TMP}/projects")):
    os.environ[k] = v
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gsd_mission as gm  # noqa: E402

DISPATCHER = Path.home() / ".claude" / "hooks" / "hook-dispatcher.js"
NOW = 1_800_000_000.0
MID = "m-feed01"
SID = f"{MID}-w"


def setup(authority: int) -> str:
    gm.create(TMP, "/gsd-autonomous", mission_id=MID, now=NOW)
    owner = {"session_id": SID, "pid": None, "proc_start": None, "heartbeat_at": NOW, "epoch": 1, "kind": "background"}
    rec = gm.transition(MID, expect_epoch=0, expect_state=gm.PREPARED, event="t_setup", now=NOW, state=gm.RUNNING,
                        epoch=1, max_hours=100.0, owner=owner)
    gm.write_worker_index(rec, SID)
    gm.transition(MID, expect_epoch=1, expect_state=gm.RUNNING, event="t_auth", authority_tokens=authority)
    tp = Path(TMP) / "proj" / f"{SID}.jsonl"
    tp.parent.mkdir(parents=True, exist_ok=True)
    rows = [{"uuid": f"u{i}", "message": {"id": f"msg-{i}", "model": "claude", "usage": {
        "input_tokens": n, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 0}}}
        for i, n in ((1, 400_000), (2, 500_000))]
    tp.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return str(tp)


def dispatch(tp: str) -> tuple[int, str]:
    payload = {"hook_event_name": "PreToolUse", "session_id": SID, "cwd": TMP, "transcript_path": tp,
               "tool_name": "PowerShell", "tool_input": {"command": "Get-Date"}}
    p = subprocess.run(["node", str(DISPATCHER), "--event=PreToolUse-Bash-default"], input=json.dumps(payload),
                       capture_output=True, text=True, timeout=60, env=os.environ)
    return p.returncode, (p.stdout + p.stderr).strip()


def main() -> int:
    tp = setup(1_000_000)
    rc, out = dispatch(tp)
    print(f"DENY    authority=1,000,000 used=900,000 next~500,000 -> rc={rc} out={out[:400]}")
    deny_ok = "MISSION CAP" in out and ("deny" in out or rc == 2)
    gm.transition(MID, expect_epoch=1, expect_state=gm.RUNNING, event="t_auth2", authority_tokens=5_000_000)
    rc2, out2 = dispatch(tp)
    print(f"CONTROL authority=5,000,000 same transcript -> rc={rc2} out={out2[:400]}")
    ctl_ok = "MISSION CAP" not in out2
    print(f"LIVE_PROOF deny={deny_ok} control={ctl_ok}")
    return 0 if deny_ok and ctl_ok else 1


if __name__ == "__main__":
    sys.exit(main())
