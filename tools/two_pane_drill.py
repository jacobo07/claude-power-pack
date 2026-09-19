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
NONCE_TAIL_BYTES = 2 * 1024 * 1024
NONCE_POLL_S = 3.0


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


def _carries_nonce(transcript: Path, nonce: str) -> bool:
    """True when a TYPED user row carries the nonce anywhere in its text.

    Deliberately weaker than `observe`'s predicate, and they must stay
    different: the operator's own prompt CONTAINS the nonce, so if this test
    were reused for the observation the drill would pass on its own setup.
    `observe` calls lr.user_issued_command_since, which additionally requires
    the row to BEGIN with the nonce and to postdate t0 -- the operator's prompt
    satisfies neither.

    Rows are classified by shape: a tool result is also `type: "user"`, so
    counting by type reads an echo as an event.

    Bounded tail: this runs against EVERY registered session on each poll, and
    reading them whole was ~150 MB per pass on the host where it was written (31
    sessions, one of them 47 MB). The subject's prompt is the newest thing in a
    session the operator just started, so the window is sized to the question.
    """
    try:
        size = transcript.stat().st_size
        with open(transcript, "rb") as fh:
            fh.seek(max(0, size - NONCE_TAIL_BYTES))
            raw = fh.read()
    except OSError:
        return False
    if size > NONCE_TAIL_BYTES:
        raw = raw.split(b"\n", 1)[-1]  # drop the leading fragment
    needle = nonce.encode("utf-8")
    for line in raw.split(b"\n"):
        if needle not in line:
            continue
        try:
            row = json.loads(line.decode("utf-8", errors="replace"))
        except Exception:
            continue
        if not isinstance(row, dict) or row.get("type") != "user" or row.get("toolUseResult"):
            continue
        content = (row.get("message") or {}).get("content")
        if isinstance(content, str):
            if nonce in content:
                return True
        elif isinstance(content, list):
            kinds = {c.get("type") for c in content if isinstance(c, dict)}
            if kinds and kinds <= {"text"}:
                if any(nonce in (c.get("text") or "") for c in content if isinstance(c, dict)):
                    return True
    return False


def _process_parents() -> dict:
    """pid -> (ppid, exe), from ONE snapshot. A walk over a moving table is not a chain."""
    import ctypes
    import ctypes.wintypes as wt

    class _PE32(ctypes.Structure):
        _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD), ("th32ProcessID", wt.DWORD),
                    ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                    ("th32ModuleID", wt.DWORD), ("cntThreads", wt.DWORD),
                    ("th32ParentProcessID", wt.DWORD), ("pcPriClassBase", ctypes.c_long),
                    ("dwFlags", wt.DWORD), ("szExeFile", ctypes.c_char * 260)]

    k32 = ctypes.windll.kernel32
    snap = k32.CreateToolhelp32Snapshot(0x00000002, 0)
    if snap == -1:
        return {}
    out, entry = {}, _PE32()
    entry.dwSize = ctypes.sizeof(_PE32)
    try:
        ok = k32.Process32First(snap, ctypes.byref(entry))
        while ok:
            out[int(entry.th32ProcessID)] = (int(entry.th32ParentProcessID),
                                             entry.szExeFile.decode("mbcs", "replace"))
            ok = k32.Process32Next(snap, ctypes.byref(entry))
    finally:
        k32.CloseHandle(snap)
    return out


def _ancestors(pid, table=None) -> list:
    table = _process_parents() if table is None else table
    chain, seen = [], set()
    cur = int(pid) if isinstance(pid, int) or str(pid).isdigit() else 0
    while cur and cur in table and cur not in seen:
        seen.add(cur)
        chain.append(cur)
        cur = table[cur][0]
    return chain


def _chain_text(pid) -> str:
    table = _process_parents()
    return " -> ".join(f"{p} {table.get(p, (0, '?'))[1]}" for p in _ancestors(pid, table)) or "unknown"


def _owning_window(pid) -> dict | None:
    """The window whose terminal registry names a shell in this pid's ancestry.

    Reads the extension's own published registry rather than restating its rule:
    those rows ARE `vscode.window.terminals[].processId`, which is exactly the
    set decide() matches against.
    """
    chain = set(_ancestors(pid))
    if not chain:
        return None
    root = Path.home() / ".claude" / "state" / "terminals"
    if not root.is_dir():
        return None
    for f in sorted(root.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        rows = data.get("terminals") or data.get("rows") or []
        for row in rows:
            if not isinstance(row, dict):
                continue
            tpid = row.get("processId")
            if isinstance(tpid, int) and tpid in chain:
                return {"registry": f.name, "pid": tpid, "cwd": data.get("cwd")}
    return None


def _nonce_candidates(nonce: str, own: str | None) -> list[tuple[Path, dict, Path]]:
    """Every registered session whose transcript carries the nonce."""
    out = []
    for path in sorted(REAL_SESSIONS.glob("*.json")):
        try:
            ident = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        sid = ident.get("sessionId")
        if not sid or (own and sid == own):
            continue
        transcript = lr.find_transcript(sid)
        if transcript is None:
            continue          # a session registers BEFORE its transcript exists
        if _carries_nonce(transcript, nonce):
            out.append((path, ident, transcript))
    return out


def arm(runid: str, pane: str, timeout: float) -> int:
    run = run_dir(runid)
    cwd = run / "panes" / pane
    cwd.mkdir(parents=True, exist_ok=True)
    nonce = f"DRILL-{pane}-{runid}"
    own = os.environ.get("CLAUDE_CODE_SESSION_ID")
    before = _session_paths()

    print(f"### arm pane {pane}")
    print("OPERATOR, in THIS Cursor window: Terminal -> New Terminal, then run:\n")
    print(f'    cd "{cwd}"; claude\n')
    print("Then, when Claude's prompt appears, paste exactly this prompt:\n")
    print(f"    Reply with a single line beginning {nonce} and nothing else.\n")
    print("Then LEAVE THE PANE ALONE -- a busy pane is not a failure (decide() returns")
    print("`defer` with status-busy and the extension re-polls), but idle is what the")
    print(f"drill waits for. Waiting up to {timeout:.0f}s for the session that carries")
    print(f"the nonce {nonce}...")

    # Identity is the NONCE, not the timing. The first version of this claimed
    # "exactly one new session appeared since I started" -- measured 2026-09-19,
    # that adopted an unrelated working session which happened to start 40 s into
    # the window (a colleague pane running `/ultra plan mode`), and it aborted on
    # `no transcript resolved` only because a session registers BEFORE its
    # transcript exists. A coincidence of timing saved that run; nothing in the
    # rule did. On this host the registry grew 25 -> 31 rows during one drill.
    deadline = time.time() + timeout
    subject = ident = transcript = None
    while time.time() < deadline:
        found = _nonce_candidates(nonce, own)
        if len(found) == 1:
            subject, ident, transcript = found[0]
            break
        if len(found) > 1:
            sids = [i.get("sessionId") for _, i, _ in found]
            print(f"FAIL arm/{pane}: {len(found)} sessions carry the nonce; identity is "
                  f"ambiguous: {sids}")
            return 1
        time.sleep(NONCE_POLL_S)
    if subject is None:
        appeared = len(_session_paths() - before)
        print(f"FAIL arm/{pane}: no session carried the nonce within {timeout:.0f}s "
              f"({appeared} session(s) started meanwhile, none of them the subject)")
        return 1

    sid = ident.get("sessionId")

    # PRECONDITION, not a diagnosis after the fact: is this subject ADDRESSABLE?
    # Ownership is `one of a window's terminals has a shell pid in the subject's
    # ancestor chain` (terminal_inbox.js::decide). A session started in Windows
    # Terminal, a detached console or another app has no such ancestor in any
    # window, so every extension ignores it and the daemon can only time out.
    # Measured 2026-09-19: arm said PASS on exactly that subject
    # (21692 claude.exe -> 32340 powershell.exe -> 54752 WindowsTerminal.exe),
    # fire spent its 10 s discovering it, and the run produced a refusal
    # indistinguishable from the one the drill demonstrates deliberately.
    # An unaddressable subject must fail HERE, where it costs nothing and says why.
    owner = _owning_window(ident.get("pid"))
    if owner is None:
        print(f"FAIL arm/{pane}: session {sid} (pid {ident.get('pid')}) sits in a terminal no "
              f"Cursor window owns.")
        print(f"      ancestor chain: {_chain_text(ident.get('pid'))}")
        print("      Open the pane from Cursor's OWN terminal panel (View -> Terminal),")
        print("      not Windows Terminal, an external console or another app.")
        return 1
    print(f"arm/{pane}: addressable -- {owner['registry']} owns terminal pid {owner['pid']}")

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

    # Record pane B at the same instant. Exactness is a claim about TWO panes --
    # "A received it" alone is delivery, not exactness -- and B must be a real
    # live pane, not a fixture. This process's own session is exactly that: a
    # second Claude session in a terminal this window owns, which is precisely
    # the pane a mis-resolved request would reach. Captured here rather than at
    # verification time so the window B is judged over starts at the same t0.
    own = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if own:
        b_transcript = lr.find_transcript(own)
        if b_transcript is not None:
            data.setdefault("panes", {})["B"] = {
                "session_id": own, "transcript": str(b_transcript), "t0": t0,
                "nonce": info["nonce"], "role": "negative control (the drill's own pane)"}
        else:
            print(f"fire/{pane}: WARNING no transcript for pane B ({own}); "
                  "the negative control cannot be judged")
    else:
        print(f"fire/{pane}: WARNING CLAUDE_CODE_SESSION_ID unset; no pane B recorded")

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
