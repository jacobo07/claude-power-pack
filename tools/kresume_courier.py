#!/usr/bin/env python3
"""Arm `/kresume` for the successor of a rollover, from the PREDECESSOR's side.

Spec: vault/specs/kresume-courier.md. Spawned detached by context-watchdog.py at the moment it
dispatches `/clear`. The successor's own SessionStart hook used to be the only thing that armed
/kresume, and on a starved host its stdin never arrived: nothing was armed and nothing was
logged (2026-10-01, 5b46e055 -> d3e92cda, claimed by hand 77 minutes later).

`/clear` does not restart claude.exe. The host registry ~/.claude/sessions/<pid>.json keeps the
pid and rewrites `sessionId` in place, so this watches ONE file -- the predecessor's own process
-- until the id changes, and arms the new id through the one writer
(`node hooks/rollover_autotype.js --arm`). Exactly one ledger row per crossing, never silent.

    python tools/kresume_courier.py --predecessor SID --cwd DIR [--transcript PATH]

Never raises; always exits 0 (it runs detached and nobody reads its exit code -- the ledger
row is the result).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTOTYPE = ROOT / "hooks" / "rollover_autotype.js"
EVENT = "kresume_courier"
DEADLINE_S = 600        # spec contract; CPP_KRESUME_COURIER_DEADLINE_S overrides
POLL_S = 1.0
ARM_TIMEOUT_S = 120     # node + hub on a starved host; the hook path's own budget is 45 s
STDERR_TAIL = 160
ARM_ATTEMPTS = 3
ARM_RETRY_S = 2.0

sys.path.insert(0, str(ROOT / "tools"))


def _ledger(predecessor: str, outcome: str, **fields) -> None:
    try:
        import gsd_long_run  # one ledger writer for every rollover event
        gsd_long_run.ledger_append(predecessor, EVENT, outcome=outcome, **fields)
    except Exception as exc:  # noqa: BLE001 -- the row is the result; say why it is missing
        print(f"{EVENT}: ledger unavailable ({exc.__class__.__name__}); outcome={outcome}",
              file=sys.stderr)


def _registry_dir() -> Path:
    override = os.environ.get("CPP_CLAUDE_SESSIONS_DIR")
    return Path(override) if override else Path.home() / ".claude" / "sessions"


def _read(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:  # noqa: BLE001 -- vanished, or caught mid-rewrite; caller decides
        return None


def ancestor_pids(pid: int) -> set[int]:
    """pid and every ancestor, from ONE process-table snapshot. Empty set when unreadable.

    Own copy, not two_pane_drill._ancestors: a live hook must not depend on a drill file, and
    GEX44 rolls over on Linux, where that helper (Toolhelp32) does not exist."""
    parents: dict[int, int] = {}
    try:
        if os.name == "nt":
            import ctypes
            import ctypes.wintypes as wt

            class _PE32(ctypes.Structure):
                _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
                            ("th32ProcessID", wt.DWORD),
                            ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                            ("th32ModuleID", wt.DWORD), ("cntThreads", wt.DWORD),
                            ("th32ParentProcessID", wt.DWORD), ("pcPriClassBase", ctypes.c_long),
                            ("dwFlags", wt.DWORD), ("szExeFile", ctypes.c_char * 260)]

            k32 = ctypes.windll.kernel32
            k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
            snap = k32.CreateToolhelp32Snapshot(0x00000002, 0)
            if not snap or snap == wt.HANDLE(-1).value:
                return set()
            entry = _PE32()
            entry.dwSize = ctypes.sizeof(_PE32)
            try:
                ok = k32.Process32First(snap, ctypes.byref(entry))
                while ok:
                    parents[int(entry.th32ProcessID)] = int(entry.th32ParentProcessID)
                    ok = k32.Process32Next(snap, ctypes.byref(entry))
            finally:
                k32.CloseHandle(snap)
        else:
            for d in Path("/proc").iterdir():
                if d.name.isdigit():
                    try:
                        # field 4 of /proc/<pid>/stat, read after the ")" that ends comm
                        parents[int(d.name)] = int((d / "stat").read_text().rsplit(")", 1)[1].split()[1])
                    except (OSError, IndexError, ValueError):
                        continue
    except Exception:  # noqa: BLE001 -- no table means no ancestry, never a guess
        return set()
    chain, cur = set(), int(pid)
    while cur and cur not in chain:
        chain.add(cur)
        cur = parents.get(cur, 0)
    return chain


def resolve(predecessor: str, ancestors: set[int] | None = None) -> dict:
    """The ONE registry entry to watch for the predecessor, or why there is none.

    Two live claude.exe processes CAN hold the same sessionId (measured 2026-10-01: pids
    21620 and 41256 both on c4f1031c, two `/resume` of one session). Taking the first match
    watches the wrong process: a false CLEAR_NEVER_LANDED, or worse, /kresume armed into the
    other pane after ITS /clear. So: keep only entries whose pid is an ancestor of the caller
    (the watchdog runs under its own claude.exe), and refuse rather than guess between two.

    Returns {"file": Path, "identity": str} | {"error": NO_REGISTRY_ENTRY | AMBIGUOUS_REGISTRY}."""
    try:
        files = list(_registry_dir().glob("*.json"))
    except OSError:
        files = []
    matches = []
    for f in files:
        rec = _read(f)
        if rec and rec.get("sessionId") == predecessor:
            matches.append((f, rec))
    if ancestors:
        mine = [(f, r) for f, r in matches if _as_int(r.get("pid"), f) in ancestors]
        matches = mine or matches
    if not matches:
        return {"error": "NO_REGISTRY_ENTRY", "count": 0}
    if len(matches) > 1:
        return {"error": "AMBIGUOUS_REGISTRY", "count": len(matches),
                "files": sorted(f.name for f, _ in matches)}
    f, rec = matches[0]
    return {"file": f, "identity": str(rec.get("procStart") or rec.get("startedAt") or "")}


def _as_int(value, path: Path) -> int:
    """The record's pid, else the file's stem (the registry names files <pid>.json)."""
    for v in (value, path.stem):
        try:
            return int(v)
        except (TypeError, ValueError):
            continue
    return 0


def find_process(predecessor: str, ancestors: set[int] | None = None) -> tuple[Path, str] | None:
    """(file, identity) when resolve() names exactly one entry, else None."""
    r = resolve(predecessor, ancestors)
    return (r["file"], r["identity"]) if "file" in r else None


def _node() -> str | None:
    # CPP_KRESUME_COURIER_NODE exists so the suite can drive ARM_FAILED with a node that is
    # absent; it never bypasses a check -- the arm it would run is the same one-writer CLI.
    override = os.environ.get("CPP_KRESUME_COURIER_NODE")
    if override:
        return override if Path(override).is_file() else None
    found = shutil.which("node")
    if found:
        return found
    for cand in (r"C:\Program Files\nodejs\node.exe", "/usr/bin/node", "/usr/local/bin/node"):
        if Path(cand).is_file():
            return cand
    return None


def _stderr_digest(text: str) -> str:
    """Head AND tail: node prints `FATAL ERROR: ...` first and a native stack after it, so a
    tail alone recorded an unreadable V8 frame instead of the reason (measured 2026-10-01)."""
    s = (text or "").strip()
    if len(s) <= 2 * STDERR_TAIL:
        return s
    return s[:STDERR_TAIL] + " ... " + s[-STDERR_TAIL:]


def arm_once(successor: str, cwd: str, transcript: str) -> tuple[str, str]:
    """(outcome, why) from the one writer. ARMED / NOT_ARMED / ARM_FAILED."""
    node = _node()
    if not node or not AUTOTYPE.is_file():
        return "ARM_FAILED", f"node={node} autotype_present={AUTOTYPE.is_file()}"
    try:
        r = subprocess.run([node, str(AUTOTYPE), "--arm", successor, cwd, transcript],
                           stdin=subprocess.DEVNULL, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=ARM_TIMEOUT_S,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception as exc:  # noqa: BLE001
        return "ARM_FAILED", f"arm did not run: {exc.__class__.__name__}"
    lines = [ln for ln in (r.stdout or "").splitlines() if ln.strip().startswith("{")]
    try:
        out = json.loads(lines[-1])
    except (IndexError, ValueError):
        return "ARM_FAILED", f"no answer from arm (rc={r.returncode}) {_stderr_digest(r.stderr)}"
    return ("ARMED" if out.get("armed") else "NOT_ARMED"), str(out.get("why") or "")


def arm(successor: str, cwd: str, transcript: str) -> tuple[str, str, int]:
    """Retry only ARM_FAILED, a bounded number of times. Measured 2026-10-01: node aborted
    (rc 134) once on a host at ~500 MB free and armed fine on the next six runs. A starved
    host is the case this courier exists for, so one crashed node must not cost the rollover.
    NOT_ARMED is an answer, never retried."""
    outcome, why = "ARM_FAILED", "not attempted"
    for attempt in range(1, ARM_ATTEMPTS + 1):
        outcome, why = arm_once(successor, cwd, transcript)
        if outcome != "ARM_FAILED":
            return outcome, why, attempt
        if attempt < ARM_ATTEMPTS:
            time.sleep(ARM_RETRY_S)
    return outcome, why, ARM_ATTEMPTS


def successor_transcript(predecessor_transcript: str, successor: str) -> str:
    """Same project directory, new id: that is where the host writes the successor's rows."""
    if not predecessor_transcript:
        return ""
    return str(Path(predecessor_transcript).with_name(f"{successor}.jsonl"))


def run(predecessor: str, cwd: str, transcript: str, registry_file: str = "",
        identity: str = "") -> str:
    sw = (os.environ.get("CPP_KRESUME_AUTOTYPE") or "").strip().lower()
    if sw in ("0", "off", "false"):
        _ledger(predecessor, "NOT_ARMED", why="kill switch CPP_KRESUME_AUTOTYPE")
        return "NOT_ARMED"
    if registry_file and identity:
        # Resolved by the watchdog inside the predecessor's own Stop, when the registry still
        # held the predecessor for certain. Measured in V-KRC: a courier that looked the
        # process up itself started AFTER the swap on a loaded host and found nothing.
        path = Path(registry_file)
    else:
        # A detached courier has no useful ancestry (its parent was the watchdog's python, now
        # gone), so it cannot tell two holders of one session id apart: it refuses, by name.
        r = resolve(predecessor)
        if "error" in r:
            _ledger(predecessor, r["error"], registry=str(_registry_dir()),
                    candidates=r.get("files", []))
            return r["error"]
        path, identity = r["file"], r["identity"]
    deadline_s = float(os.environ.get("CPP_KRESUME_COURIER_DEADLINE_S") or DEADLINE_S)
    poll_s = float(os.environ.get("CPP_KRESUME_COURIER_POLL_S") or POLL_S)
    t0 = time.monotonic()
    while time.monotonic() - t0 < deadline_s:
        rec = _read(path)
        if rec is None:
            if not path.exists():
                _ledger(predecessor, "PROCESS_GONE", registry_file=path.name)
                return "PROCESS_GONE"
            # caught mid-rewrite: read again next tick
        elif str(rec.get("procStart") or rec.get("startedAt") or "") != identity:
            # Same pid, different process: arming it would type into a stranger's session.
            _ledger(predecessor, "PROCESS_GONE", registry_file=path.name, why="pid reused")
            return "PROCESS_GONE"
        elif (rec.get("sessionId") or predecessor) != predecessor:
            successor = rec["sessionId"]
            outcome, why, attempts = arm(successor, cwd, successor_transcript(transcript, successor))
            _ledger(predecessor, outcome, successor=successor, why=why, attempts=attempts,
                    waited_s=round(time.monotonic() - t0, 1))
            return outcome
        time.sleep(poll_s)
    _ledger(predecessor, "CLEAR_NEVER_LANDED", registry_file=path.name, deadline_s=deadline_s)
    return "CLEAR_NEVER_LANDED"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--predecessor", required=True)
    ap.add_argument("--cwd", required=True)
    ap.add_argument("--transcript", default="")
    ap.add_argument("--registry-file", default="", help="resolved by the watchdog at dispatch")
    ap.add_argument("--identity", default="", help="procStart of that process at dispatch")
    a = ap.parse_args(argv)
    try:
        print(run(a.predecessor, a.cwd, a.transcript, a.registry_file, a.identity))
    except Exception as exc:  # noqa: BLE001 -- detached: the ledger is the only reader
        _ledger(a.predecessor, "ARM_FAILED", why=f"courier crashed: {exc.__class__.__name__}: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
