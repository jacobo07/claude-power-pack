"""V-ORCA-* gates: the auto-compact daemon answers the terminal inbox for sessions in Orca panes.

Sessions hosted in an Orca X pane had no provider (the PP Sessions extension lives in Cursor), so
every rollover /clear was refused after 10 s. The daemon now reads ORCA_TERMINAL_HANDLE from the
session's own claude.exe environment block, confirms it with `orca terminal list`, and types with
`orca terminal send`.

What is real here: the daemon, its session resolution (pid + creation FILETIME), and the
environment-block read -- the "session" is a live child process started with the handle in its
environment. What is a fixture: the Orca CLI (AC_ORCA_APP=node + a recording script), so this suite
can never type into a real pane, even when it is launched from one.

AC_TEST_DAEMON overrides the daemon path (defaults to this repo's copy, the one under edit).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DAEMON = Path(os.environ.get("AC_TEST_DAEMON") or ROOT / "hooks" / "auto-compact-sendkeys-daemon.ps1")
NODE = shutil.which("node")
HANDLE, TAB = "term_7e57-orca-a", "tab-7e57-a"

FAKE_CLI = r"""
const fs = require('fs');
const args = process.argv.slice(2);
fs.appendFileSync(process.env.FAKE_ORCA_LOG, JSON.stringify(args) + '\n');
const st = JSON.parse(fs.readFileSync(process.env.FAKE_ORCA_STATE, 'utf8'));
let result;
if (args[0] === 'terminal' && args[1] === 'list') result = { terminals: st.terminals };
else if (args[0] === 'terminal' && args[1] === 'send') result = { send: { accepted: st.accept !== false } };
else { process.stdout.write(JSON.stringify({ ok: false, error: { code: 'unknown' } })); process.exit(1); }
process.stdout.write(JSON.stringify({ id: 'x', ok: true, result }));
"""

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


def spawn_session(handle=HANDLE, tab=TAB):
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("ORCA_")}
    if handle:
        env["ORCA_TERMINAL_HANDLE"] = handle
    if tab:
        env["ORCA_TAB_ID"] = tab
    p = subprocess.Popen([NODE, "-e", "setTimeout(()=>{},600000)"], env=env)
    ft = subprocess.run(["powershell.exe", "-NoProfile", "-Command",
                         f"(Get-CimInstance Win32_Process -Filter 'ProcessId={p.pid}').CreationDate.ToFileTimeUtc()"],
                        capture_output=True, text=True, timeout=60).stdout.strip()
    return p, ft


def case(line, status="idle", terminals=None, accept=True, handle=HANDLE, tab=TAB,
         ttl=8, inject_cli=True, ack_first="10", torn_first=False):
    d = Path(tempfile.mkdtemp(prefix="orcainbox_"))
    (d / "sessions").mkdir()
    proc, ft = spawn_session(handle, tab)
    fixer = None
    try:
        rec = d / "sessions" / f"{proc.pid}.json"
        good = json.dumps({"pid": proc.pid, "sessionId": "sx", "procStart": ft, "status": status})
        rec.write_text(good, encoding="utf-8")
        if torn_first:
            # Resolution finds the session by id in any *.json; the provider reads <pid>.json, torn until healed.
            (d / "sessions" / "resolve-alias.json").write_text(good, encoding="utf-8")
            rec.write_text(good[: len(good) // 2], encoding="utf-8")

            def tear_then_heal():
                req = d / "inbox" / "sx.req.json"
                for _ in range(1200):
                    if req.exists():
                        break
                    time.sleep(0.05)
                time.sleep(1.0)
                rec.write_text(good, encoding="utf-8")
            fixer = threading.Thread(target=tear_then_heal)
            fixer.start()
        tr = d / "t.jsonl"
        tr.write_text("\n".join(json.dumps(r) for r in [
            {"type": "user", "message": {"role": "user", "content": "go"}},
            {"type": "assistant", "message": {"role": "assistant",
                                              "content": [{"type": "text", "text": "Done.\n" + line}]}}]) + "\n",
            encoding="utf-8")
        (d / "auto-compact-trigger-sx.flag").write_text(json.dumps(
            {"session_id": "sx", "cwd": r"C:\p\ProjA", "transcript": str(tr), "expect_line": line}), encoding="utf-8")
        if terminals is None:
            terminals = [{"handle": HANDLE, "tabId": TAB, "connected": True, "writable": True}]
        (d / "orca-state.json").write_text(json.dumps({"terminals": terminals, "accept": accept}), encoding="utf-8")
        (d / "fake-orca.js").write_text(FAKE_CLI, encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith("ORCA_")}
        env.update({"AC_DAEMON_DIR": str(d), "AC_DAEMON_DRYRUN": "1", "AC_DAEMON_TTL": str(ttl),
                    "AC_DAEMON_FAKE_FG": json.dumps({"name": "brave", "title": "x", "hwnd": "1"}),
                    "AC_DAEMON_FAKE_WINDOWS": "[]", "AC_ACK_FIRST": ack_first,
                    "GSD_LONG_RUN_STATE_DIR": str(d), "AC_INBOX_DIR": str(d / "inbox"),
                    "AC_SESSIONS_DIR": str(d / "sessions"),
                    "FAKE_ORCA_LOG": str(d / "orca-calls.jsonl"), "FAKE_ORCA_STATE": str(d / "orca-state.json")})
        for k in ("CPP_LEGACY_FOREGROUND_SENDKEYS", "AC_ORCA_PROVIDER", "AC_ORCA_APP", "AC_ORCA_CLI_JS"):
            env.pop(k, None)
        if inject_cli:
            env.update({"AC_ORCA_APP": NODE, "AC_ORCA_CLI_JS": str(d / "fake-orca.js")})
        subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(DAEMON)],
                       env=env, capture_output=True, text=True, timeout=ttl + 90)
    finally:
        proc.kill()
        if fixer:
            fixer.join(timeout=5)
    log = d / "auto-compact-daemon.log"
    calls_p = d / "orca-calls.jsonl"
    led = d / "gsd-autorun-ledger.jsonl"
    return {
        "log": log.read_text(encoding="utf-8-sig") if log.exists() else "",
        "calls": [json.loads(l) for l in calls_p.read_text(encoding="utf-8").splitlines()] if calls_p.exists() else [],
        "ledger": [json.loads(l) for l in led.read_text(encoding="utf-8").splitlines() if l.strip()] if led.exists() else [],
        "flags": sorted(p.name for p in d.glob("auto-compact-*.flag")),
    }


def sends(r):
    return [c[2:] for c in r["calls"] if c[:2] == ["terminal", "send"]]


def refused_with(r, reason):
    return (f"terminal inbox refused: {reason}" in [x.get("detail") for x in r["ledger"]]
            and r["flags"] == ["auto-compact-refused-sx.flag"])


def main() -> int:
    if not DAEMON.is_file() or not NODE:
        print(f"HARNESS-FAILED: daemon={DAEMON.is_file()} node={NODE}")
        print("ORCA_PASS=0/0  threshold=all")
        return 2

    line = "/gsd-autonomous --from 10.1"
    r = case(line)
    check("V-ORCA-SENT-INTO-OWN-PANE",
          sends(r) == [["--terminal", HANDLE, "--text", line, "--enter", "--json"],
                       ["--terminal", HANDLE, "--enter", "--json"]]
          and "SENT via=orca" in r["log"] and r["flags"] == []
          and any(x.get("event") == "compact_dispatched" and f"orca:{HANDLE}" in x.get("detail", "")
                  for x in r["ledger"]),
          f"sends={sends(r)} flags={r['flags']} ledger={r['ledger']} log={r['log'][-300:]!r}")

    r = case("/compact focus on v1 phases done")
    check("V-ORCA-COMPACT-ARGUMENT-TAIL",
          [s[3] if len(s) > 3 and s[2] == "--text" else None for s in sends(r)]
          == ["/compact focus on v1 phases done", None, "focus on v1 phases done"]
          and "enters=3" in r["log"],
          f"sends={sends(r)} log={r['log'][-200:]!r}")

    quoted = '/kclear say "two words" and C:\\path\\ end\\'
    r = case(quoted)
    check("V-ORCA-TEXT-BYTE-EXACT", sends(r)[:1] and sends(r)[0][3] == quoted,
          f"sent={sends(r)[:1]} want={quoted!r}")

    # Red branches: the session IS in an Orca pane, but Orca cannot confirm it -> refuse, type nothing.
    r = case(line, terminals=[])
    check("V-ORCA-RED-HANDLE-NOT-LIVE", sends(r) == [] and refused_with(r, "orca-handle-not-live"),
          f"sends={sends(r)} flags={r['flags']} ledger={r['ledger']}")

    r = case(line, terminals=[{"handle": HANDLE, "tabId": "another-tab", "connected": True, "writable": True}])
    check("V-ORCA-RED-TAB-MISMATCH", sends(r) == [] and refused_with(r, "orca-tab-mismatch"),
          f"sends={sends(r)} flags={r['flags']}")

    r = case(line, terminals=[{"handle": HANDLE, "tabId": TAB, "connected": False, "writable": True}])
    check("V-ORCA-RED-DISCONNECTED", sends(r) == [] and refused_with(r, "orca-terminal-not-writable"),
          f"sends={sends(r)} flags={r['flags']}")

    r = case(line, accept=False)
    check("V-ORCA-RED-SEND-NOT-ACCEPTED",
          len(sends(r)) == 1 and refused_with(r, "orca-send-not-accepted") and "SENT" not in r["log"],
          f"sends={sends(r)} flags={r['flags']}")

    # Claude Code rewrites its session record constantly: a torn read is retried, not a refusal.
    r = case(line, torn_first=True)
    check("V-ORCA-TORN-SESSION-RECORD-RETRIED",
          len(sends(r)) == 2 and "SENT via=orca" in r["log"]
          and not any(x.get("event") == "refused" for x in r["ledger"]),
          f"sends={sends(r)} ledger={r['ledger']} log={r['log'][-200:]!r}")

    r = case(line, status="busy", ttl=5, ack_first="1")
    check("V-ORCA-BUSY-DEFERS", sends(r) == [] and "deferred by orca" in r["log"]
          and r["flags"] == ["auto-compact-trigger-sx.flag"],
          f"sends={sends(r)} flags={r['flags']} log={r['log'][-200:]!r}")

    # Not an Orca pane: the provider stays out entirely and the old path is byte-unchanged.
    r = case(line, handle=None, tab=None, ttl=6, ack_first="1")
    check("V-ORCA-NOT-AN-ORCA-PANE", r["calls"] == [] and "no extension answer" in r["log"]
          and "Orca pane" not in r["log"],
          f"calls={r['calls']} log={r['log'][-200:]!r}")

    # A dry-run suite started from an Orca pane, without an injected CLI, must never reach Orca.
    r = case(line, inject_cli=False, ttl=6, ack_first="1")
    check("V-ORCA-DRYRUN-NEVER-REACHES-ORCA", r["calls"] == [] and "Orca pane" not in r["log"]
          and "no extension answer" in r["log"],
          f"calls={r['calls']} log={r['log'][-200:]!r}")

    print(f"\nORCA_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 and passes else 1


if __name__ == "__main__":
    sys.exit(main())
