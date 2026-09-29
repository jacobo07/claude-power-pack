"""V-KRA-* gates: after a rollover `/clear`, `/kresume` is typed into the successor.

Measured 2026-09-29 (fe1c49ea -> e9d6887e): /kclear and /clear were both typed by the
daemon, the SessionStart card reached the successor, and still nobody claimed the
capsule. A SessionStart card is context for a turn that has not started; nothing
types into the fresh prompt, so "the successor runs /kresume unprompted" could not
happen by construction.

The fix has two halves, each pinned here:
  hub    -- on a `clear` start with an unretired capsule for this cwd, drop a daemon
            flag for the NEW session carrying fresh_line=/kresume.
  daemon -- a fresh_line flag is typed only while the session's transcript has no
            assistant turn; once one exists the request is refused or withdrawn.
            Only /kresume is representable as a fresh_line.

The daemon runs in DRY-RUN with the terminal inbox and session registry isolated
(helpers from test_autocompact_per_session). No keystroke reaches a live pane.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
# The canonical daemon is the one edited and committed; the live copy under ~/.claude/hooks
# is deployed from it. A mutation drill points this elsewhere.
os.environ.setdefault("AC_TEST_DAEMON", str(HERE.parent / "hooks" / "auto-compact-sendkeys-daemon.ps1"))
import test_autocompact_per_session as acps  # noqa: E402

HUB = Path(os.environ.get("KRA_TEST_HUB") or HERE.parent / "hooks" / "session_start_hub.js")
AUTOTYPE_HOOK = HUB.parent / "rollover_autotype.js"

passes = fails = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


def fresh() -> Path:
    return Path(tempfile.mkdtemp(prefix="kra_"))


# ------------------------------------------------------------------ hub half
def run_hub(home: Path, source: str, sid: str, cwd: str, transcript: str, extra_env=None):
    """Drive the hub's rollover functions in isolation (require, not the hook main)."""
    js = (
        "const h=require(process.argv[1]);"
        "const line=h.hookRolloverResume(process.argv[3],process.argv[2]);"
        "const focus=h.rolloverFocus(process.argv[3],process.argv[2]);"
        "const armed=line?h.armKresumeAutotype(process.argv[4],process.argv[3],process.argv[5],focus):null;"
        "process.stdout.write(JSON.stringify({line:!!line,armed:armed,focus:focus}));"
    )
    env = dict(os.environ)
    env.update({"USERPROFILE": str(home), "HOME": str(home),
                "AC_DAEMON_DIR": str(home / ".claude" / "hooks")})
    env.update(extra_env or {})
    for k in [k for k, v in env.items() if v is None]:
        del env[k]
    r = subprocess.run(["node", "-e", js, str(HUB), source, cwd, sid, transcript],
                       env=env, capture_output=True, text=True, timeout=60)
    try:
        return json.loads(r.stdout or "{}"), r
    except ValueError:
        return {}, r


def seed_capsule(home: Path, cwd: str, certified=False, obligations=None) -> Path:
    d = home / ".claude" / "state" / "rollover" / "capsules"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "pred-1111.json"
    rec = {"session_id": "pred-1111", "cwd": cwd}
    if obligations is not None:
        rec["obligations"] = obligations
    p.write_text(json.dumps(rec), encoding="utf-8")
    if certified:
        p.with_suffix(".certified").write_text("x", encoding="utf-8")
    return p


def hub_gates():
    cwd = r"C:\p\ProjA"
    flag_name = "auto-compact-trigger-succ-2222.flag"

    home = fresh()
    seed_capsule(home, cwd)
    out, r = run_hub(home, "clear", "succ-2222", cwd, r"C:\t\succ.jsonl")
    if not out:
        print(f"HARNESS-FAILED: hub did not answer rc={r.returncode} err={r.stderr[-300:]!r}")
        sys.exit(2)
    flag = home / ".claude" / "hooks" / flag_name
    body = json.loads(flag.read_text(encoding="utf-8")) if flag.exists() else {}
    check("V-KRA-HUB-ARMS-ON-CLEAR",
          out.get("line") and body.get("fresh_line") == "/kresume"
          and body.get("session_id") == "succ-2222" and body.get("transcript") == r"C:\t\succ.jsonl"
          and body.get("cwd") == cwd,
          f"out={out} flag={body}")

    # Controls: every case in which the card is NOT shown must also not arm.
    home = fresh()
    seed_capsule(home, cwd)
    out, _ = run_hub(home, "startup", "succ-2222", cwd, "t")
    check("V-KRA-HUB-NOT-ON-STARTUP",
          not out.get("line") and not (home / ".claude" / "hooks" / flag_name).exists(), f"out={out}")

    home = fresh()
    seed_capsule(home, cwd, certified=True)
    out, _ = run_hub(home, "clear", "succ-2222", cwd, "t")
    check("V-KRA-HUB-NOT-WHEN-RETIRED",
          not out.get("line") and not (home / ".claude" / "hooks" / flag_name).exists(), f"out={out}")

    home = fresh()
    seed_capsule(home, r"C:\p\OtherRepo")
    out, _ = run_hub(home, "clear", "succ-2222", cwd, "t")
    check("V-KRA-HUB-NOT-OTHER-REPO",
          not out.get("line") and not (home / ".claude" / "hooks" / flag_name).exists(), f"out={out}")

    # Kill switch: the card still shows (a human can still type it), nothing is typed.
    home = fresh()
    seed_capsule(home, cwd)
    out, _ = run_hub(home, "clear", "succ-2222", cwd, "t", extra_env={"CPP_KRESUME_AUTOTYPE": "off"})
    check("V-KRA-HUB-KILL-SWITCH",
          out.get("line") and not out.get("armed")
          and not (home / ".claude" / "hooks" / flag_name).exists(), f"out={out}")

    # 2026-09-29 (cf02a0a5 -> 7e953f9d): the hub was reaped by the SessionStart chain's 4 s
    # deadline before it logged a line, so the arm moved to rollover_autotype.js, a
    # top-level hook. Driven END TO END here as the harness runs it: payload on stdin.
    def run_autotype_hook(payload, extra_env=None):
        home = fresh()
        seed_capsule(home, cwd, obligations=["Re-point rows 28/29"])
        hooks = home / ".claude" / "hooks"
        hooks.mkdir(parents=True, exist_ok=True)
        (hooks / "auto-compact-sendkeys-daemon.ps1").write_text("exit 0\r\n", encoding="ascii")
        env = dict(os.environ)
        env.update({"USERPROFILE": str(home), "HOME": str(home), "AC_DAEMON_DIR": str(hooks)})
        env.update(extra_env or {})
        r = subprocess.run(["node", str(AUTOTYPE_HOOK)], input=json.dumps(payload), env=env,
                           capture_output=True, text=True, timeout=60)
        f = hooks / flag_name
        return (json.loads(f.read_text(encoding="utf-8")) if f.exists() else None), r

    body, r = run_autotype_hook({"source": "clear", "session_id": "succ-2222", "cwd": cwd,
                                 "transcript_path": r"C:\t\succ.jsonl"})
    check("V-KRA-HOOK-ARMS-END-TO-END",
          r.returncode == 0 and body is not None
          and body.get("fresh_line") == "/kresume focus on Re-point rows 28/29"
          and body.get("transcript") == r"C:\t\succ.jsonl",
          f"rc={r.returncode} body={body} err={r.stderr[-200:]!r}")
    body, r = run_autotype_hook({"source": "startup", "session_id": "succ-2222", "cwd": cwd})
    check("V-KRA-HOOK-SILENT-ON-STARTUP", r.returncode == 0 and body is None, f"body={body}")
    body, r = run_autotype_hook({"source": "clear", "session_id": "succ-2222", "cwd": cwd},
                                {"CPP_KRESUME_AUTOTYPE": "off"})
    check("V-KRA-HOOK-KILL-SWITCH", r.returncode == 0 and body is None, f"body={body}")

    # STATIC: the hub must NOT also arm (a second daemon launch for the same flag).
    src = HUB.read_text(encoding="utf-8")
    main_src = src[src.find("async function main()"):]
    check("V-KRA-HUB-DOES-NOT-ARM (static)",
          "armKresumeAutotype(" not in main_src, "armKresumeAutotype called inside hub main()")

    # LIVE CONFIG, labelled so: the hook must be a top-level SessionStart entry, not a
    # SessionStart-chain member, or it inherits the 4 s deadline that caused the incident.
    settings = Path(os.environ.get("KRA_SETTINGS") or Path.home() / ".claude" / "settings.json")
    try:
        entries = json.loads(settings.read_text(encoding="utf-8")).get("hooks", {}).get("SessionStart", [])
    except (OSError, ValueError):
        entries = []
    cmds = [" ".join([h.get("command", "")] + list(h.get("args", [])))
            for e in entries for h in e.get("hooks", [])]
    check("V-KRA-HOOK-REGISTERED-TOP-LEVEL (live config)",
          any("rollover_autotype.js" in c and "hook-dispatcher" not in c for c in cmds),
          f"{len(cmds)} SessionStart commands in {settings}")

    # A session id that could escape the hooks dir is sanitised, never followed.
    home = fresh()
    seed_capsule(home, cwd)
    out, _ = run_hub(home, "clear", "..\\..\\evil", cwd, "t")
    names = sorted(p.name for p in (home / ".claude" / "hooks").glob("*.flag"))
    check("V-KRA-HUB-SID-SANITISED", names == ["auto-compact-trigger-evil.flag"], f"names={names}")

    # --- focus (2026-09-29, Owner): `/kresume focus on <first obligation>`, like /compact.
    def armed_line(obligations):
        home = fresh()
        seed_capsule(home, cwd, obligations=obligations)
        run_hub(home, "clear", "succ-2222", cwd, "t")
        f = home / ".claude" / "hooks" / flag_name
        return json.loads(f.read_text(encoding="utf-8")).get("fresh_line") if f.exists() else None

    got = armed_line(["Decide event delivery for X", "second"])
    check("V-KRA-HUB-FOCUS-FIRST-OBLIGATION",
          got == "/kresume focus on Decide event delivery for X", f"fresh_line={got!r}")

    got = armed_line([{"title": "Fix the relay", "detail": "long detail"}])
    check("V-KRA-HUB-FOCUS-DICT-TITLE", got == "/kresume focus on Fix the relay", f"fresh_line={got!r}")

    # A newline typed into a terminal submits early; the rest would land as a second prompt.
    got = armed_line(["line one\r\nline two\tthree\x07"])
    check("V-KRA-HUB-FOCUS-ONE-LINE",
          got == "/kresume focus on line one line two three", f"fresh_line={got!r}")

    got = armed_line(["x" * 500])
    check("V-KRA-HUB-FOCUS-CAPPED",
          got is not None and got.startswith("/kresume focus on x") and len(got) <= len("/kresume focus on ") + 200,
          f"len={len(got or '')}")

    # No obligation, or one that sanitises to nothing -> bare /kresume, never "focus on ".
    got = armed_line([])
    check("V-KRA-HUB-FOCUS-NONE-BARE", got == "/kresume", f"fresh_line={got!r}")
    got = armed_line(["\r\n\t "])
    check("V-KRA-HUB-FOCUS-EMPTY-BARE", got == "/kresume", f"fresh_line={got!r}")

    # --- launch timing (2026-09-29, 435014d6). The daemon launch used to be QUEUED for
    # flushSpawns() at the end of main(); a starved host abandoned the hub after arming and
    # before the flush, so the flag sat unserved until the Owner had already typed.
    # child_process.spawn is recorded (never executed) before the hub is required, and
    # flushSpawns is never called: a spawn seen here happened at arm time. Recording,
    # not launching, because a detached powershell started from inside the agent's tool
    # sandbox never runs its script (measured: 1.2 s synchronously, nothing in 40 s
    # detached) -- a marker-file gate would measure the sandbox, not the hub.
    def spawns_at_arm(extra_env=None):
        home = fresh()
        seed_capsule(home, cwd)
        hooks = home / ".claude" / "hooks"
        hooks.mkdir(parents=True, exist_ok=True)
        (hooks / "auto-compact-sendkeys-daemon.ps1").write_text("exit 0\r\n", encoding="ascii")
        js = (
            "const cp=require('child_process');const calls=[];"
            "cp.spawn=(c,a)=>{calls.push([c].concat(a||[]).join(' '));return {pid:1,unref(){}};};"
            "const h=require(process.argv[1]);"
            "const line=h.hookRolloverResume(process.argv[3],process.argv[2]);"
            "const armed=line?h.armKresumeAutotype('succ-2222',process.argv[3],'t',''):null;"
            "process.stdout.write(JSON.stringify({armed:armed,calls:calls}));"
        )
        env = dict(os.environ)
        env.update({"USERPROFILE": str(home), "HOME": str(home),
                    "AC_DAEMON_DIR": str(hooks)})
        env.update(extra_env or {})
        r = subprocess.run(["node", "-e", js, str(HUB), "clear", cwd],
                           env=env, capture_output=True, text=True, timeout=60)
        try:
            return json.loads(r.stdout or "{}")
        except ValueError:
            return {"err": r.stderr[-300:]}

    got = spawns_at_arm()
    daemon_calls = [c for c in got.get("calls", []) if "auto-compact-sendkeys-daemon.ps1" in c]
    check("V-KRA-HUB-LAUNCHES-WITHOUT-FLUSH",
          got.get("armed") and len(daemon_calls) == 1 and daemon_calls[0].startswith("powershell.exe"),
          f"got={got}")

    got = spawns_at_arm({"CPP_KRESUME_AUTOTYPE": "off"})
    check("V-KRA-HUB-KILL-SWITCH-NO-LAUNCH",
          "calls" in got and not got.get("armed") and got["calls"] == [], f"got={got}")



# --------------------------------------------------------------- daemon half
def transcript(d: Path, rows) -> Path:
    t = d / "t.jsonl"
    t.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return t


FRESH_ROWS = [{"type": "custom-title", "customTitle": "x"},
              {"type": "user", "message": {"role": "user", "content": "<command-name>/clear</command-name>"}}]
USED_ROWS = FRESH_ROWS + [{"type": "assistant", "message": {"role": "assistant",
                                                             "content": [{"type": "text", "text": "hi"}]}}]


def kresume_case(ft, me, rows=FRESH_ROWS, line="/kresume", missing_transcript=False):
    d = fresh()
    (d / "sessions").mkdir()
    (d / "sessions" / f"{me}.json").write_text(json.dumps(
        {"pid": me, "sessionId": "sx", "procStart": ft, "status": "idle"}), encoding="utf-8")
    tr = d / "never-written.jsonl" if missing_transcript else transcript(d, rows)
    (d / "auto-compact-trigger-sx.flag").write_text(json.dumps(
        {"session_id": "sx", "cwd": r"C:\p\ProjA", "transcript": str(tr), "fresh_line": line}) + "\n",
        encoding="utf-8")
    return d, tr


def daemon_gates():
    me = os.getpid()
    ft = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command",
         f"(Get-CimInstance Win32_Process -Filter 'ProcessId={me}').CreationDate.ToFileTimeUtc()"],
        capture_output=True, text=True, timeout=60).stdout.strip()
    default = {"CPP_LEGACY_FOREGROUND_SENDKEYS": None}      # production mode: exact or nothing
    not_cursor = (acps.fg(name="brave", title="x"), ["ProjA - Cursor"])

    d, _ = kresume_case(ft, me)
    run, seen = _fake(d, "sent")
    sent, text, started, rc = acps.run_daemon(d, *not_cursor, ttl=6, script=run, extra_env=default)
    if not started:
        print(f"HARNESS-FAILED: daemon did not start rc={rc} log={text!r}")
        sys.exit(2)
    req = seen.get("req") or {}
    check("V-KRA-D-FRESH-TYPES-KRESUME",
          req.get("text") == "/kresume" and "SENT via=extension" in text and acps.remaining(d) == [],
          f"req={req} left={acps.remaining(d)} log={text[-240:]!r}")

    d, _ = kresume_case(ft, me, missing_transcript=True)
    run, seen = _fake(d, "sent")
    sent, text, _, _ = acps.run_daemon(d, *not_cursor, ttl=6, script=run, extra_env=default)
    check("V-KRA-D-UNWRITTEN-TRANSCRIPT-IS-FRESH",
          (seen.get("req") or {}).get("text") == "/kresume" and "SENT via=extension" in text,
          f"req={seen.get('req')} log={text[-200:]!r}")

    # Negative pole: the session already had a turn -> never typed, refused and ledgered.
    d, _ = kresume_case(ft, me, rows=USED_ROWS)
    run, seen = _fake(d, "sent")
    sent, text, _, _ = acps.run_daemon(d, *not_cursor, ttl=5, script=run, extra_env=default)
    led = d / "gsd-autorun-ledger.jsonl"
    check("V-KRA-D-USED-SESSION-REFUSED",
          "REQUESTED" not in text and not seen.get("req")
          and acps.remaining(d) == ["auto-compact-refused-sx.flag"]
          and led.exists() and "already had a turn" in led.read_text(encoding="utf-8"),
          f"left={acps.remaining(d)} log={text[-240:]!r}")

    # Only /kresume is representable: a fresh_line of /clear is refused, never requested.
    d, _ = kresume_case(ft, me, line="/clear")
    run, seen = _fake(d, "sent")
    sent, text, _, _ = acps.run_daemon(d, *not_cursor, ttl=5, script=run, extra_env=default)
    check("V-KRA-D-ALLOWLIST",
          "REQUESTED" not in text and not seen.get("req")
          and acps.remaining(d) == ["auto-compact-refused-sx.flag"],
          f"left={acps.remaining(d)} log={text[-240:]!r}")

    # Focus form: typed verbatim when it is one clean line.
    focus = "/kresume focus on Fix the relay (obligation 1)"
    d, _ = kresume_case(ft, me, line=focus)
    run, seen = _fake(d, "sent")
    sent, text, _, _ = acps.run_daemon(d, *not_cursor, ttl=6, script=run, extra_env=default)
    check("V-KRA-D-FOCUS-TYPED",
          (seen.get("req") or {}).get("text") == focus and "SENT via=extension" in text,
          f"req={seen.get('req')} log={text[-200:]!r}")

    # The daemon is the authority, not the hub: it re-checks the shape and refuses
    # anything a hub bug (or a hand-written flag) could smuggle into a terminal.
    for gate, bad in (("V-KRA-D-FOCUS-NEWLINE-REFUSED", "/kresume focus on a\nb"),
                      ("V-KRA-D-FOCUS-SUFFIX-REFUSED", "/kresume; /clear"),
                      ("V-KRA-D-FOCUS-EMPTY-REFUSED", "/kresume focus on "),
                      ("V-KRA-D-FOCUS-TOO-LONG-REFUSED", "/kresume focus on " + "y" * 201)):
        d, _ = kresume_case(ft, me, line=bad)
        run, seen = _fake(d, "sent")
        sent, text, _, _ = acps.run_daemon(d, *not_cursor, ttl=5, script=run, extra_env=default)
        check(gate,
              "REQUESTED" not in text and not seen.get("req")
              and acps.remaining(d) == ["auto-compact-refused-sx.flag"],
              f"left={acps.remaining(d)} log={text[-200:]!r}")

    # The owner defers (session busy); the user starts a turn meanwhile -> withdrawn.
    d, tr = kresume_case(ft, me)

    def defer_then_user_turn():
        req_p, ack_p = d / "inbox" / "sx.req.json", d / "inbox" / "sx.ack.json"
        for _ in range(150):
            if req_p.exists():
                try:
                    req = json.loads(req_p.read_text(encoding="utf-8"))
                    break
                except ValueError:
                    pass
            time.sleep(0.1)
        else:
            return
        ack_p.write_text(json.dumps({"id": req["id"], "session_id": "sx", "status": "deferred",
                                     "reason": "status-busy"}), encoding="utf-8")
        time.sleep(2.0)
        transcript(d, USED_ROWS)

    sent, text, _, _ = acps.run_daemon(d, *not_cursor, ttl=10, script=defer_then_user_turn,
                                       extra_env=dict(default, AC_INBOX_TTL="60000"))
    check("V-KRA-D-WITHDRAWN-WHEN-USER-STARTS",
          "WITHDRAWN" in text and "SENT via=extension" not in text
          and not (d / "inbox" / "sx.req.json").exists(),
          f"log={text[-240:]!r}")

    # Control for the gate above: same deferral, transcript untouched -> still pending.
    d, _ = kresume_case(ft, me)

    def defer_only():
        req_p, ack_p = d / "inbox" / "sx.req.json", d / "inbox" / "sx.ack.json"
        for _ in range(150):
            if req_p.exists():
                try:
                    req = json.loads(req_p.read_text(encoding="utf-8"))
                    break
                except ValueError:
                    pass
            time.sleep(0.1)
        else:
            return
        ack_p.write_text(json.dumps({"id": req["id"], "session_id": "sx", "status": "deferred",
                                     "reason": "status-busy"}), encoding="utf-8")

    sent, text, _, _ = acps.run_daemon(d, *not_cursor, ttl=8, script=defer_only,
                                       extra_env=dict(default, AC_INBOX_TTL="60000"))
    check("V-KRA-D-NO-WITHDRAW-WHILE-FRESH",
          "WITHDRAWN" not in text and "deferred by extension" in text
          and acps.remaining(d) == ["auto-compact-trigger-sx.flag"],
          f"left={acps.remaining(d)} log={text[-240:]!r}")


def _fake(d: Path, status: str, reason: str = ""):
    seen = {}

    def run():
        req_p, ack_p = d / "inbox" / "sx.req.json", d / "inbox" / "sx.ack.json"
        for _ in range(150):
            if req_p.exists():
                try:
                    req = json.loads(req_p.read_text(encoding="utf-8"))
                except ValueError:
                    time.sleep(0.1)
                    continue
                seen["req"] = req
                ack_p.write_text(json.dumps({"id": req["id"], "session_id": "sx", "status": status,
                                             "reason": reason, "terminal": "t1"}), encoding="utf-8")
                return
            time.sleep(0.1)
    return run, seen


def main() -> int:
    hub_gates()
    daemon_gates()
    total = passes + fails
    print(f"KRA_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
