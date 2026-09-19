"""Live two-pane exactness drill (spec exact-target-continuation.md, Phase 1 Task 1).

Drives the REAL path once, end to end, against one subject pane:

    flag -> real daemon -> real request file -> real extension decide()
         -> real term.sendText -> real transcript row

Nothing here simulates a layer. The one thing it cannot do is create the
subject: a subject must be a live Claude session whose terminal THIS Cursor
window's PP Sessions extension owns, so `arm` prints a command and waits for a
human to run it. That is the phase's design, not a gap in this tool.

Containment (the drill owns its subjects and can address nothing else):

  AC_DAEMON_DIR=<run>/hooks         the daemon scans only its own flag dir, takes
                                    its own lock, writes its own log (daemon:52-54)
  AC_SESSIONS_DIR=<run>/sessions     Resolve-Session iterates only this dir
                                    (daemon:292), so the daemon can resolve no
                                    session but one the drill copied in
  GSD_LONG_RUN_STATE_DIR=<run>/state the drill's ledger rows never touch
                                    ~/.claude/state/gsd-autorun-ledger.jsonl,
                                    which is the file `report` reads for this
                                    milestone's PROVEN/UNPROVEN verdict

  AC_INBOX_DIR is deliberately NOT set: INBOX_DIR is hardcoded in the extension,
  so an overridden daemon-side inbox is a directory no extension watches, which
  would silently convert the whole drill into the no-provider timeout path.
  AC_DAEMON_DRYRUN is deliberately NOT set: it is what neuters the V-ACPS suite,
  and default-off exact-or-refused is the posture under test.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOME = Path.home()
PYTHON = Path(r"C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe")
DAEMON = HOME / ".claude" / "hooks" / "auto-compact-sendkeys-daemon.ps1"
REAL_SESSIONS = HOME / ".claude" / "sessions"
REAL_INBOX = HOME / ".claude" / "state" / "terminal-inbox"
CURSOR_EXTENSIONS = HOME / ".cursor" / "extensions"
MIN_EXTENSION = (0, 4, 0)
RUNS = Path(os.environ.get("TEMP", "/tmp")) / "pp-two-pane-drill"


def _load_gsd_long_run():
    spec = importlib.util.spec_from_file_location("gsd_long_run", REPO / "tools" / "gsd_long_run.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gsd_long_run"] = mod
    spec.loader.exec_module(mod)
    return mod


lr = _load_gsd_long_run()


# --------------------------------------------------------------------- run state
def run_dir(runid: str) -> Path:
    return RUNS / runid


def manifest_path(runid: str) -> Path:
    return run_dir(runid) / "manifest.json"


def read_manifest(runid: str) -> dict:
    p = manifest_path(runid)
    if not p.is_file():
        return {"runid": runid, "panes": {}}
    return json.loads(p.read_text(encoding="utf-8"))


def write_manifest(runid: str, data: dict) -> None:
    p = manifest_path(runid)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def drill_env(runid: str) -> dict:
    """The containment env, built by ADDING to a copy -- never by filtering.

    A filtered env is how an off-switch gets dropped (see the estate's
    allowlist lesson). The two switches that must stay off are asserted
    explicitly below rather than left to whatever the parent happened to carry.
    """
    run = run_dir(runid)
    env = dict(os.environ)
    env["AC_DAEMON_DIR"] = str(run / "hooks")
    env["AC_SESSIONS_DIR"] = str(run / "sessions")
    env["GSD_LONG_RUN_STATE_DIR"] = str(run / "state")
    env.pop("AC_INBOX_DIR", None)      # must reach the inbox the extension watches
    env.pop("AC_DAEMON_DRYRUN", None)  # a dry run measures nothing
    env["CPP_LEGACY_FOREGROUND_SENDKEYS"] = "0"
    return env


# --------------------------------------------------------------------- probe
def _extension_version() -> tuple[str, tuple | None, str]:
    """(evidence, version tuple or None, outcome). `unreadable` is not `absent`."""
    if not CURSOR_EXTENSIONS.is_dir():
        return (f"{CURSOR_EXTENSIONS} is not a directory", None, "unreadable")
    try:
        found = sorted(CURSOR_EXTENSIONS.glob("kobii.pp-sessions-*"))
    except OSError as exc:
        return (f"{exc.__class__.__name__} listing {CURSOR_EXTENSIONS}", None, "unreadable")
    if not found:
        return ("no kobii.pp-sessions-* directory", None, "absent")
    best, best_v = None, None
    for d in found:
        raw = d.name.rsplit("-", 1)[-1]
        try:
            v = tuple(int(x) for x in raw.split("."))
        except ValueError:
            continue
        if best_v is None or v > best_v:
            best, best_v = d, v
    if best_v is None:
        return (f"no parseable version in {[d.name for d in found]}", None, "unreadable")
    return (best.name, best_v, "ok")


def probe() -> int:
    """Assert every precondition INDIVIDUALLY and name each that fails.

    A precondition that could not be READ is a distinct outcome from one that is
    absent: only the second is a fact about the environment under test.
    """
    checks: list[tuple[str, str, str]] = []

    def record(name: str, outcome: str, evidence: str) -> None:
        checks.append((name, outcome, evidence))

    record("python", "ok" if PYTHON.is_file() else "absent", str(PYTHON))
    record("daemon", "ok" if DAEMON.is_file() else "absent", str(DAEMON))
    for rel in ("extension/src/terminal_inbox.js", "extension/src/extension.js"):
        p = REPO / rel
        record(rel, "ok" if p.is_file() else "absent", str(p))

    ev, ver, outcome = _extension_version()
    if outcome == "ok" and ver < MIN_EXTENSION:
        outcome = "too-old"
        ev = f"{ev} < {'.'.join(str(x) for x in MIN_EXTENSION)}"
    record("pp-sessions>=0.4.0", outcome, ev)

    try:
        REAL_INBOX.mkdir(parents=True, exist_ok=True)
        probe_file = REAL_INBOX / ".drill-write-probe"
        probe_file.write_text("probe\n", encoding="utf-8")
        probe_file.unlink()
        record("inbox-writable", "ok", str(REAL_INBOX))
    except OSError as exc:
        record("inbox-writable", "unreadable", f"{exc.__class__.__name__}: {exc}")

    record("sessions-dir", "ok" if REAL_SESSIONS.is_dir() else "absent", str(REAL_SESSIONS))

    bad = [c for c in checks if c[1] != "ok"]
    for name, outcome, ev in checks:
        print(f"{'PASS' if outcome == 'ok' else 'FAIL'} probe/{name}: {outcome} -- {ev}")
    print(f"PROBE={len(checks) - len(bad)}/{len(checks)}")
    return 0 if not bad else 1


# --------------------------------------------------------------------- arm
def _session_paths() -> set:
    """The SET of session files -- a count cannot see one leaving as another arrives."""
    try:
        return {p.resolve() for p in REAL_SESSIONS.glob("*.json")}
    except OSError:
        return set()


def arm(runid: str, pane: str, timeout: float) -> int:
    run = run_dir(runid)
    cwd = run / "panes" / pane
    cwd.mkdir(parents=True, exist_ok=True)
    nonce = f"DRILL-{pane}-{runid}"
    before = _session_paths()

    print(f"### arm pane {pane}")
    print("OPERATOR, in THIS Cursor window: Terminal -> New Terminal, then run:\n")
    print(f'    cd "{cwd}"; claude\n')
    print("Then, when Claude's prompt appears, paste exactly this prompt:\n")
    print(f"    Reply with a single line beginning {nonce} and nothing else.\n")
    print("Then LEAVE THE PANE ALONE -- a busy pane is not a failure (decide() returns")
    print("`defer` with status-busy and the extension re-polls), but idle is what the")
    print(f"drill waits for. Waiting up to {timeout:.0f}s for exactly one new session...")

    deadline = time.time() + timeout
    subject = None
    while time.time() < deadline:
        new = _session_paths() - before
        if len(new) == 1:
            subject = next(iter(new))
            break
        if len(new) > 1:
            print(f"FAIL arm/{pane}: {len(new)} new sessions appeared; identity is ambiguous")
            return 1
        time.sleep(1.0)
    if subject is None:
        print(f"FAIL arm/{pane}: no new session within {timeout:.0f}s")
        return 1

    try:
        ident = json.loads(subject.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"FAIL arm/{pane}: could not read {subject}: {exc.__class__.__name__}")
        return 1

    sid = ident.get("sessionId")
    own = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if sid and own and sid == own:
        print(f"FAIL arm/{pane}: that is THIS session; the drill never targets a real working pane")
        return 1

    transcript = lr.find_transcript(sid) if sid else None
    if transcript is None:
        print(f"FAIL arm/{pane}: no transcript resolved for session {sid}")
        return 1

    # Copy the identity verbatim. Resolve-Session reads only sessionId/pid/
    # procStart and never `status`; the extension reads `status` from the LIVE
    # file, so this copy going stale cannot weaken the extension's authority.
    sess_dir = run / "sessions"
    sess_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(subject, sess_dir / subject.name)

    data = read_manifest(runid)
    data["panes"][pane] = {"session_id": sid, "pid": ident.get("pid"),
                           "procStart": ident.get("procStart"), "cwd": str(cwd),
                           "transcript": str(transcript), "nonce": nonce,
                           "identity_file": subject.name}
    write_manifest(runid, data)
    print(f"PASS arm/{pane}: session={sid} pid={ident.get('pid')} transcript={transcript}")
    return 0


# --------------------------------------------------------------------- fire
def fire(runid: str, pane: str, timeout: float) -> int:
    data = read_manifest(runid)
    info = data.get("panes", {}).get(pane)
    if not info:
        print(f"FAIL fire/{pane}: pane not armed")
        return 1
    transcript = Path(info["transcript"])
    if not transcript.is_file():
        print(f"FAIL fire/{pane}: transcript missing at {transcript}")
        return 1

    # t0 BEFORE anything is written, so the observation window cannot start late.
    t0 = time.time()

    # The daemon types the line back: Get-ExpectState returns `line = $last` and
    # the loop requests only when state is ok AND a line exists. So the drill
    # must ADAPT to what the subject actually said, never dictate it. Same rule,
    # imported rather than reimplemented.
    expect = lr.last_line(lr.last_assistant_text(transcript))
    if not expect:
        print(f"FAIL fire/{pane}: subject has no last assistant line yet -- let it answer first")
        return 1

    run = run_dir(runid)
    (run / "hooks").mkdir(parents=True, exist_ok=True)
    (run / "state").mkdir(parents=True, exist_ok=True)
    flag = run / "hooks" / f"auto-compact-trigger-{info['session_id']}.flag"
    payload = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(t0)),
               "session_id": info["session_id"], "cwd": info["cwd"], "used_pct": None,
               "transcript": str(transcript), "expect_line": expect}
    # UTF-8 with NO BOM: three invisible bytes defeat a JSON parser, and this
    # estate has already paid for that once.
    flag.write_bytes((json.dumps(payload) + "\n").encode("utf-8"))

    info["t0"] = t0
    info["expect_line"] = expect
    write_manifest(runid, data)
    print(f"fire/{pane}: expect_line={expect!r}")

    proc = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
         "-File", str(DAEMON)],
        env=drill_env(runid), capture_output=True, text=True, timeout=timeout, check=False)
    log = run / "hooks" / "auto-compact-sendkeys.log"
    tail = ""
    if log.is_file():
        tail = "\n".join(log.read_text(encoding="utf-8", errors="replace").splitlines()[-15:])
    print(f"fire/{pane}: daemon exit={proc.returncode}")
    if tail:
        print(tail)
    return 0


# --------------------------------------------------------------------- observe
def observe(runid: str, pane: str) -> int:
    data = read_manifest(runid)
    info = data.get("panes", {}).get(pane)
    if not info or "t0" not in info:
        print(f"FAIL observe/{pane}: pane not fired")
        return 1
    got = lr.user_issued_command_since(Path(info["transcript"]), info["nonce"], info["t0"])
    print(f"observe/{pane}: user_issued_command_since={got}")
    return 0 if got else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Live two-pane exactness drill")
    ap.add_argument("action", choices=["probe", "arm", "fire", "observe"])
    ap.add_argument("--runid", default=time.strftime("%Y%m%d-%H%M%S"))
    ap.add_argument("--pane", default="A")
    ap.add_argument("--timeout", type=float, default=300.0)
    args = ap.parse_args(argv)

    if os.environ.get("CPP_LEGACY_FOREGROUND_SENDKEYS") == "1":
        print("FAIL: CPP_LEGACY_FOREGROUND_SENDKEYS=1 -- that is the foreground fallback, "
              "not the exact-or-refused posture under test")
        return 1

    if args.action == "probe":
        return probe()
    print(f"runid={args.runid}  run={run_dir(args.runid)}")
    if args.action == "arm":
        return arm(args.runid, args.pane, args.timeout)
    if args.action == "fire":
        return fire(args.runid, args.pane, args.timeout)
    return observe(args.runid, args.pane)


if __name__ == "__main__":
    sys.exit(main())
