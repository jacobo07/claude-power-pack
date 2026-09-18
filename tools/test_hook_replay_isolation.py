"""An isolated hook replay must prove that EVERY mutating participant honours the isolation.

Incident 2026-09-16/18 follow-up. A replay that exported CLAUDE_STATE_DIR believed itself
isolated, yet wrote into the real dead-closer-recovery and correction-guard state: no hook
except the dispatcher reads CLAUDE_STATE_DIR. Worse, synthetic drivers writing into the
PRODUCTION context-watchdog log produced ~150 rows during the 42 h the real Stop chain was
dark, so the log looked alive while every real session was unhooked.

The contract that the hooks actually implement is the home directory: they resolve state via
os.homedir() / Path.home() (USERPROFILE on Windows) or HOME. This gate replays all six
dispatcher chains with HOME and USERPROFILE pointed at a temp root and a unique session id,
then searches every production state/ and logs/ file touched during the run for that id.
Search by id, not by mtime: concurrent panes write those directories constantly.

Exit 0 = isolated. 1 = a production file carries the drill id (named). 2 = harness failure.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

NODE = r"C:\Program Files\nodejs\node.exe" if os.name == "nt" else "node"
REAL_HOME = Path.home()
DISPATCHER = REAL_HOME / ".claude" / "hooks" / "hook-dispatcher.js"
PROD_DIRS = [REAL_HOME / ".claude" / "state", REAL_HOME / ".claude" / "logs"]
CHAINS = {
    "PreToolUse-Bash-chain": {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "echo isolation-drill"}},
    "PreToolUse-Edit-chain": {"hook_event_name": "PreToolUse", "tool_name": "Write", "tool_input": {"file_path": "", "content": "drill"}},
    "PreToolUse-Read-chain": {"hook_event_name": "PreToolUse", "tool_name": "Read", "tool_input": {"file_path": ""}},
    "PostToolUse-default": {"hook_event_name": "PostToolUse", "tool_name": "Read", "tool_input": {"file_path": ""}, "tool_response": {}},
    "Stop-chain": {"hook_event_name": "Stop", "stop_hook_active": False},
    "UserPromptSubmit-chain": {"hook_event_name": "UserPromptSubmit", "prompt": "isolation drill: no action"},
}


def scan_for(marker: str, since: float) -> list[str]:
    """Production files modified since `since` whose bytes contain `marker`."""
    hits = []
    for d in PROD_DIRS:
        for f in d.rglob("*") if d.exists() else []:
            try:
                if f.is_file() and f.stat().st_mtime >= since - 1 and f.stat().st_size < 50_000_000:
                    if marker.encode() in f.read_bytes():
                        hits.append(str(f))
            except OSError:
                continue
    return hits


def main() -> int:
    if not DISPATCHER.exists():
        print(f"HARNESS-FAILED: no dispatcher at {DISPATCHER}")
        return 2
    drill_id = f"isolation-drill-{uuid.uuid4().hex[:12]}"
    t0 = time.time()
    with tempfile.TemporaryDirectory() as root:
        fake_home = Path(root)
        (fake_home / ".claude").mkdir()
        env = dict(os.environ, HOME=str(fake_home), USERPROFILE=str(fake_home), CLAUDE_STATE_DIR=str(fake_home / ".claude" / "state"))
        ran = 0
        for chain, payload in CHAINS.items():
            if "file_path" in payload.get("tool_input", {}):
                payload["tool_input"]["file_path"] = str(fake_home / "drill.txt")
            body = dict(payload, session_id=drill_id, cwd=str(fake_home), transcript_path="")
            p = subprocess.run([NODE, str(DISPATCHER), f"--event={chain}"], input=json.dumps(body).encode(),
                               capture_output=True, env=env, timeout=300)
            ran += 1 if p.returncode in (0, 1, 2) else 0
            print(f"ran {chain}: rc={p.returncode}")
        written = [q for q in fake_home.rglob("*") if q.is_file()]
        # Precondition: the drill must have exercised hooks that DO write, or isolation is vacuous.
        if ran != len(CHAINS) or not written:
            print(f"HARNESS-FAILED: chains_ran={ran}/{len(CHAINS)} files_in_fake_home={len(written)}")
            return 2
        print(f"files written inside the isolated home: {len(written)} (e.g. {sorted(str(w.relative_to(fake_home)) for w in written)[:4]})")
    # Positive control: a scanner that stopped finding things reports the same "no leak".
    # Plant our OWN marker in production state/, require the scan to see it, then remove it.
    probe = PROD_DIRS[0] / f"_isolation_probe_{drill_id}.tmp"
    probe.parent.mkdir(parents=True, exist_ok=True)
    probe.write_text(drill_id, encoding="utf-8")
    try:
        found = scan_for(drill_id, t0)
    finally:
        probe.unlink(missing_ok=True)
    if str(probe) not in found:
        print("HARNESS-FAILED: the leak scanner did not find its own planted marker")
        return 2
    leaks = [f for f in found if f != str(probe)]
    print(f"scanner positive control: planted marker found (scanned since t0)")
    if leaks:
        for lk in leaks:
            print(f"FAIL V-ISOLATION-LEAK: drill id found in production file {lk}")
        print(f"ISOLATION_PASS=0/1 leaks={len(leaks)}")
        return 1
    print("PASS V-ISOLATION-HOME: no production state/logs file carries the drill id")
    print("ISOLATION_PASS=1/1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
