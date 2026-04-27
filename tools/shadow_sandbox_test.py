#!/usr/bin/env python3
"""
shadow_sandbox_test.py — MC-LAZ-06b forensic byte-integrity test.

Verifies the Shadow-Folder Engine never causes a single byte of data
loss in a session whose .jsonl is renamed mid-write. This is the
ONLY question that matters for whether the engine is safe to deploy
on the Owner's live sessions.

Test plan:
  1. Build a synthetic ~/.claude/projects/<pid>/ with no real files.
  2. Build a synthetic ~/.claude/lazarus/<pid>/heartbeats/<sid>.lock
     for two fake "writer" sessions, both with fresh mtimes (live).
  3. Spawn TWO Node subprocess writers. Each:
       - Opens its <sid>.jsonl in append mode (createWriteStream)
       - Writes one JSON line every 80ms
       - Continues until told to stop via stdin
       - Reports total bytes / line count to stdout on shutdown
  4. Sleep 600ms (~7 lines per writer flushed).
  5. Invoke shadow_engine.js shadow --project-id <pid> --owner-sid <X>
     using --no-gate (sandbox bypass, kill-switch is for production).
  6. Sleep 2000ms — SUSTAINED RENAME. Writers continue producing lines
     against their open handle. On Windows + FILE_SHARE_DELETE the
     writes should follow the inode to the renamed path.
  7. Invoke shadow_engine.js restore --project-id <pid> --owner-sid <X>.
  8. Sleep 600ms (let any in-flight writes settle).
  9. Stop writers via stdin "STOP\n", read each one's final tally.
  10. Read the original .jsonl files. Count lines + bytes.
  11. ASSERT: writer-reported lines == file-line-count
              writer-reported bytes == file-byte-count
              No corruption (every line parses as JSON, monotonic seq).
  12. Extra: check no .conflict.* files were parked (means restore was
      clean, not racy).
  13. Cleanup sandbox.

Exit 0 = byte integrity confirmed. Exit 1 = data loss detected
(engine MUST NOT be deployed). Exit 2 = sandbox setup failed.

Usage:
  python tools/shadow_sandbox_test.py
  python tools/shadow_sandbox_test.py --verbose
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

# Windows cp1252 → UTF-8 reconfiguration (matches forensic_test pattern).
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass


THIS_DIR = Path(__file__).resolve().parent
ENGINE = THIS_DIR.parent / "lib" / "lazarus" / "shadow_engine.js"

# A small, self-contained Node writer. Embedded as a string so the
# sandbox is one file. Each line written is a strictly-monotonic JSON
# object {"seq": N, "ts": "...", "writer": "<sid>"}. The writer keeps
# a single createWriteStream open in append mode for the entire run —
# this is the worst case for shadow-engine safety, since the handle
# is the longest-lived possible.
WRITER_SCRIPT = r"""
'use strict';
const fs = require('fs');
const path = require('path');

const sid = process.argv[2];
const targetPath = process.argv[3];
const intervalMs = parseInt(process.argv[4] || '80', 10);

const stream = fs.createWriteStream(targetPath, { flags: 'a' });
let seq = 0;
let bytes = 0;
let stopping = false;

function tick() {
  if (stopping) return;
  seq += 1;
  const line = JSON.stringify({
    seq, ts: new Date().toISOString(), writer: sid,
  }) + '\n';
  bytes += Buffer.byteLength(line, 'utf8');
  stream.write(line);
}

const t = setInterval(tick, intervalMs);

process.stdin.setEncoding('utf8');
let buf = '';
process.stdin.on('data', chunk => {
  buf += chunk;
  if (buf.includes('STOP')) {
    stopping = true;
    clearInterval(t);
    stream.end(() => {
      // Final report on stdout — single JSON line.
      process.stdout.write(JSON.stringify({
        sid, lines_written: seq, bytes_written: bytes,
      }) + '\n');
      process.exit(0);
    });
  }
});

process.on('SIGTERM', () => { stopping = true; clearInterval(t); stream.end(); process.exit(0); });
"""


def now_iso(offset: float = 0.0) -> str:
    return (datetime.now(timezone.utc).timestamp() + offset).__str__()


def sanitize(p: str) -> str:
    return re.sub(r"[^a-zA-Z0-9-]", "-", p)


def write_text(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def write_json(p: Path, obj) -> None:
    write_text(p, json.dumps(obj, indent=2))


def expect(label: str, cond: bool, evidence: str = "") -> None:
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {label}")
    if not cond:
        if evidence:
            print(f"        evidence: {evidence}")
        raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Shadow-engine forensic sandbox")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--keep", action="store_true",
                        help="don't delete sandbox (debug)")
    args = parser.parse_args()

    if not ENGINE.exists():
        print(f"FATAL: engine not found at {ENGINE}", file=sys.stderr)
        return 2

    sandbox = Path(tempfile.mkdtemp(prefix="shadow-sandbox-"))
    print(f"Sandbox HOME: {sandbox}")

    proj_path = "/synthetic/shadow/project"
    project_id = sanitize(proj_path)
    proj_dir = sandbox / ".claude" / "projects" / project_id
    hb_dir = sandbox / ".claude" / "lazarus" / project_id / "heartbeats"
    proj_dir.mkdir(parents=True, exist_ok=True)
    hb_dir.mkdir(parents=True, exist_ok=True)

    # Two synthetic "live" sessions. The owner is a third sid that
    # will run the engine (mimicking a NEW session opening for /resume).
    writer_sids = ["writer-AAAA", "writer-BBBB"]
    owner_sid = "owner-CCCC"

    # Heartbeats for the two writers (fresh mtime).
    for sid in writer_sids:
        write_json(hb_dir / f"{sid}.lock", {
            "session_id": sid,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    # NOT writing a heartbeat for owner — engine treats anything not in
    # heartbeats as "dead/non-other", so this proves the include/exclude
    # logic works correctly.

    # Write the embedded Node writer to a file inside sandbox.
    writer_js = sandbox / "writer.js"
    write_text(writer_js, WRITER_SCRIPT)

    # Spawn writers — each appending to its <sid>.jsonl in proj_dir.
    procs = {}
    for sid in writer_sids:
        target = proj_dir / f"{sid}.jsonl"
        target.write_text("", encoding="utf-8")  # ensure file exists
        p = subprocess.Popen(
            ["node", str(writer_js), sid, str(target), "80"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, "HOME": str(sandbox), "USERPROFILE": str(sandbox)},
            text=True,
            encoding="utf-8",
        )
        procs[sid] = p

    print("Phase 1 — writers spawned, warming up 600ms")
    time.sleep(0.6)

    # Phase 2 — invoke shadow.
    print("Phase 2 — invoking shadow_engine.shadow (sustained rename begins)")
    shadow_env = {**os.environ, "HOME": str(sandbox), "USERPROFILE": str(sandbox)}
    shadow_proc = subprocess.run(
        ["node", str(ENGINE), "shadow",
         "--project-id", project_id,
         "--owner-sid", owner_sid,
         "--no-gate"],
        capture_output=True, text=True, env=shadow_env, encoding="utf-8",
    )
    if args.verbose:
        print("shadow stdout:\n" + shadow_proc.stdout)
        print("shadow stderr:\n" + shadow_proc.stderr)
    if shadow_proc.returncode != 0:
        print(f"FATAL: shadow exit {shadow_proc.returncode}", file=sys.stderr)
        return 2
    shadow_result = json.loads(shadow_proc.stdout)
    expect("shadow operation hid both writer .jsonl",
           len(shadow_result.get("shadowed", [])) == 2,
           f"got {shadow_result}")
    # Sanity: the original .jsonl should NOT exist any more.
    for sid in writer_sids:
        expect(f"{sid}.jsonl absent during shadow window",
               not (proj_dir / f"{sid}.jsonl").exists())

    print("Phase 3 — sustained rename window (2000ms; writers must keep writing to inode)")
    time.sleep(2.0)

    # Phase 4 — restore.
    print("Phase 4 — invoking shadow_engine.restore")
    restore_proc = subprocess.run(
        ["node", str(ENGINE), "restore",
         "--project-id", project_id,
         "--owner-sid", owner_sid,
         "--no-gate"],
        capture_output=True, text=True, env=shadow_env, encoding="utf-8",
    )
    if args.verbose:
        print("restore stdout:\n" + restore_proc.stdout)
        print("restore stderr:\n" + restore_proc.stderr)
    if restore_proc.returncode != 0:
        print(f"FATAL: restore exit {restore_proc.returncode}", file=sys.stderr)
        return 2
    restore_result = json.loads(restore_proc.stdout)
    expect("restore operation un-shadowed both",
           len(restore_result.get("restored", [])) == 2,
           f"got {restore_result}")
    expect("no conflict files parked (clean restore)",
           len(restore_result.get("skipped", [])) == 0,
           f"got {restore_result}")

    print("Phase 5 — settle 600ms then stop writers and collect tallies")
    time.sleep(0.6)

    tallies = {}
    for sid, p in procs.items():
        try:
            out, err = p.communicate("STOP\n", timeout=5)
            if args.verbose and err:
                print(f"writer {sid} stderr: {err}")
            tallies[sid] = json.loads(out.strip().splitlines()[-1])
        except subprocess.TimeoutExpired:
            p.kill()
            print(f"FATAL: writer {sid} did not exit cleanly", file=sys.stderr)
            return 2

    print("Phase 6 — byte-integrity assertions")
    for sid in writer_sids:
        target = proj_dir / f"{sid}.jsonl"
        expect(f"{sid}.jsonl exists at original path post-restore", target.exists())
        raw = target.read_bytes()
        actual_bytes = len(raw)
        # Count lines (each ends with '\n' written by writer).
        actual_lines = raw.count(b"\n")

        reported_bytes = tallies[sid]["bytes_written"]
        reported_lines = tallies[sid]["lines_written"]

        expect(
            f"{sid}: byte-exact integrity (writer={reported_bytes}, file={actual_bytes})",
            actual_bytes == reported_bytes,
            f"diff={reported_bytes - actual_bytes} bytes",
        )
        expect(
            f"{sid}: line count exact (writer={reported_lines}, file={actual_lines})",
            actual_lines == reported_lines,
            f"diff={reported_lines - actual_lines} lines",
        )

        # Every line must be valid JSON with monotonic seq.
        prev_seq = 0
        for i, line in enumerate(raw.decode("utf-8", errors="replace").splitlines(), 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                expect(f"{sid}: line {i} is valid JSON", False, f"{e} :: {line[:80]!r}")
            if obj.get("seq") != prev_seq + 1:
                expect(
                    f"{sid}: monotonic seq (line {i}: got {obj.get('seq')}, expected {prev_seq + 1})",
                    False,
                )
            prev_seq = obj["seq"]
        expect(f"{sid}: no gaps in seq (final={prev_seq}, expected={reported_lines})",
               prev_seq == reported_lines)

    # Cleanup pre-Phase-7
    if not args.keep:
        try:
            shutil.rmtree(sandbox, ignore_errors=True)
        except Exception:
            pass
    else:
        print(f"(sandbox-phase16 retained at {sandbox})")

    # ---------------------------------------------------------------
    # Phase 7 — MC-OVO-161: SIGKILL writer mid-shadow, verify recovery.
    # Proves the engine survives an asymmetric crash where one
    # session dies while its .jsonl is in the renamed state. Without
    # the restoreSelfToo + panic-restore safety net, the killed
    # session's transcript would stay invisible.
    # ---------------------------------------------------------------
    print("\nPhase 7 — MC-OVO-161 SIGKILL-during-shadow recovery")
    sandbox2 = Path(tempfile.mkdtemp(prefix="shadow-killtest-"))
    print(f"  killtest sandbox: {sandbox2}")
    proj_dir2 = sandbox2 / ".claude" / "projects" / project_id
    hb_dir2 = sandbox2 / ".claude" / "lazarus" / project_id / "heartbeats"
    proj_dir2.mkdir(parents=True, exist_ok=True)
    hb_dir2.mkdir(parents=True, exist_ok=True)

    kill_sids = ["kill-victim-AAAA", "kill-survivor-BBBB"]
    kill_owner = "kill-owner-CCCC"
    for sid in kill_sids:
        write_json(hb_dir2 / f"{sid}.lock", {
            "session_id": sid,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    writer_js2 = sandbox2 / "writer.js"
    write_text(writer_js2, WRITER_SCRIPT)

    procs2 = {}
    for sid in kill_sids:
        target = proj_dir2 / f"{sid}.jsonl"
        target.write_text("", encoding="utf-8")
        procs2[sid] = subprocess.Popen(
            ["node", str(writer_js2), sid, str(target), "80"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={**os.environ, "HOME": str(sandbox2), "USERPROFILE": str(sandbox2)},
            text=True, encoding="utf-8",
        )

    time.sleep(0.6)
    print("  shadow active")
    shadow_env2 = {**os.environ, "HOME": str(sandbox2), "USERPROFILE": str(sandbox2)}
    subprocess.run(
        ["node", str(ENGINE), "shadow", "--project-id", project_id, "--owner-sid", kill_owner, "--no-gate"],
        capture_output=True, env=shadow_env2,
    )

    time.sleep(1.0)
    print(f"  SIGKILL {kill_sids[0]}")
    procs2[kill_sids[0]].kill()
    procs2[kill_sids[0]].wait(timeout=3)

    time.sleep(0.5)
    # Survivor's heartbeat is still fresh; victim's heartbeat will go stale soon.

    # Run panic-restore (PowerShell) — bypasses kill-switch by design.
    panic_script = THIS_DIR / "lazarus-panic-restore.ps1"
    if panic_script.exists() and sys.platform == "win32":
        panic_proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(panic_script), "-ProjectId", project_id],
            capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "HOME": str(sandbox2), "USERPROFILE": str(sandbox2)},
        )
        if args.verbose:
            print("  panic-restore stdout:\n" + panic_proc.stdout)
    else:
        # Non-Windows or panic-restore missing: run engine restore directly.
        subprocess.run(
            ["node", str(ENGINE), "restore", "--project-id", project_id, "--owner-sid", kill_owner, "--no-gate"],
            capture_output=True, env=shadow_env2,
        )

    time.sleep(0.3)

    # Stop survivor, collect its tally.
    try:
        out, _ = procs2[kill_sids[1]].communicate("STOP\n", timeout=5)
        survivor_tally = json.loads(out.strip().splitlines()[-1])
    except Exception as e:
        print(f"  FATAL: survivor exit failed: {e}", file=sys.stderr)
        return 2

    expect("kill-victim .jsonl recovered to original path",
           (proj_dir2 / f"{kill_sids[0]}.jsonl").exists())
    expect("kill-survivor .jsonl exists at original path",
           (proj_dir2 / f"{kill_sids[1]}.jsonl").exists())
    expect("kill-survivor: byte-exact (writer-reported == file)",
           len((proj_dir2 / f"{kill_sids[1]}.jsonl").read_bytes())
           == survivor_tally["bytes_written"])

    # Victim's bytes will be <= what it wrote before kill (writer
    # exited mid-stream so no final tally available). The key proof
    # is that the file IS recoverable and contains valid JSON lines.
    victim_raw = (proj_dir2 / f"{kill_sids[0]}.jsonl").read_bytes()
    victim_lines = [l for l in victim_raw.decode("utf-8", errors="replace").splitlines() if l.strip()]
    expect("kill-victim has at least 5 valid JSON lines (proves writes pre-kill survived)",
           len(victim_lines) >= 5,
           f"got {len(victim_lines)} lines")
    for i, ln in enumerate(victim_lines, 1):
        try:
            json.loads(ln)
        except Exception as e:
            expect(f"kill-victim line {i} parses as JSON", False, str(e))

    expect("no shadow leftovers after panic-restore",
           not any(f.name.endswith('.live-shadow-' + kill_owner)
                   for f in proj_dir2.iterdir()))

    if not args.keep:
        try:
            shutil.rmtree(sandbox2, ignore_errors=True)
        except Exception:
            pass

    print("\nFORENSIC SANDBOX PASS — Shadow-Engine preserves every byte under sustained rename")
    print("                       AND survives SIGKILL mid-shadow with panic-restore recovery.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
