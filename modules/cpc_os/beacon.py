"""Write a liveness beacon for a session that ``kclaude.ps1`` cannot cover.

``kclaude.ps1`` writes ``%TEMP%/kclaude-pane-<pid>.sid`` only when the session id
is known AT LAUNCH -- i.e. only for ``--resume``. A session created FRESH has no
id until Claude Code mints one, so it never gets a beacon at all
(``T-BEACON-NEW-SESSION-GAP-001``). Those are precisely the panes worth keeping:
a new chat the Owner worked in all day, left open, and expects back after a
Cursor quit. Without a beacon such a pane is only visible to the content-age
tiers, so once it idles past ACTIVE it is dropped from ``tasks.json`` and does
not come back.

The SessionStart hub knows the id (``PP_PANE_SID``) but not a durable pid: the
hub's node process and its detached python child both exit within seconds, and
keying a beacon to a dead pid makes it invisible to ``live_beacon_sids()``. The
pid that lives exactly as long as the pane is the ancestor ``claude.exe``, so
this module walks up the process tree to find it.

The beacon format is byte-identical to ``kclaude.ps1``'s so
``live_beacon_sids()`` and ``build_pane_map.ps1`` read both without change.

Fail-open ABSOLUTE: every failure path returns ``None`` and writes nothing. A
missing beacon degrades to the previous behaviour (content-age tiers), never to
a crash in SessionStart.
"""

from __future__ import annotations

import ctypes
import json
import os
import tempfile
from ctypes import wintypes
from datetime import datetime, timezone
from pathlib import Path

TH32CS_SNAPPROCESS = 0x00000002
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
MAX_WALK = 12
TARGET = "claude.exe"


class _PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", ctypes.c_char * 260),
    ]


def _process_table() -> dict[int, tuple[int, str]]:
    """pid -> (ppid, exe_name). One snapshot call; empty dict on any failure."""
    k32 = ctypes.windll.kernel32
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == INVALID_HANDLE_VALUE or not snap:
        return {}
    table: dict[int, tuple[int, str]] = {}
    try:
        entry = _PROCESSENTRY32()
        entry.dwSize = ctypes.sizeof(_PROCESSENTRY32)
        ok = k32.Process32First(snap, ctypes.byref(entry))
        while ok:
            name = entry.szExeFile.decode("latin-1", "replace").lower()
            table[int(entry.th32ProcessID)] = (int(entry.th32ParentProcessID), name)
            ok = k32.Process32Next(snap, ctypes.byref(entry))
    finally:
        k32.CloseHandle(snap)
    return table


def _creation_time(pid: int) -> int | None:
    """Process creation time as a raw FILETIME, or None if unreadable."""
    k32 = ctypes.windll.kernel32
    handle = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return None
    try:
        created = wintypes.FILETIME()
        exited = wintypes.FILETIME()
        kernel = wintypes.FILETIME()
        user = wintypes.FILETIME()
        if not k32.GetProcessTimes(handle, ctypes.byref(created),
                                   ctypes.byref(exited), ctypes.byref(kernel),
                                   ctypes.byref(user)):
            return None
        return (created.dwHighDateTime << 32) | created.dwLowDateTime
    finally:
        k32.CloseHandle(handle)


def owning_pane_pid(start_pid: int | None = None) -> int | None:
    """The ancestor ``claude.exe`` whose lifetime equals this pane's.

    A pid is only meaningful together with a creation time: Windows reuses pids,
    so a stale ppid can point at an unrelated live process. Each step therefore
    requires the parent to have been created no later than the child; a chain
    that violates that is a reused pid, not an ancestor, and the walk stops.

    Returns None when no ``claude.exe`` ancestor is found -- the caller must
    treat that as "cannot measure" and write nothing.
    """
    if os.name != "nt":
        return None
    try:
        table = _process_table()
    except Exception:
        return None
    if not table:
        return None

    pid = int(start_pid if start_pid is not None else os.getpid())
    child_ctime = _creation_time(pid)
    for _ in range(MAX_WALK):
        row = table.get(pid)
        if not row:
            return None
        ppid, _name = row
        if ppid <= 0 or ppid == pid:
            return None
        parent = table.get(ppid)
        if not parent:
            return None
        parent_ctime = _creation_time(ppid)
        if (child_ctime is not None and parent_ctime is not None
                and parent_ctime > child_ctime):
            return None  # pid reuse: "parent" is younger than its child
        if parent[1] == TARGET:
            return ppid
        pid, child_ctime = ppid, parent_ctime
    return None


def write_session_beacon(sid: str, cwd: str | None = None,
                         start_pid: int | None = None) -> str | None:
    """Write this session's beacon if one does not already exist.

    Idempotent: ``kclaude.ps1`` already wrote a beacon for a resumed session, and
    a re-entrant SessionStart must not duplicate or clobber it. Returns the
    beacon path on write, None on skip or any failure.
    """
    if not sid:
        return None
    try:
        pid = owning_pane_pid(start_pid)
        if not pid:
            return None
        path = Path(tempfile.gettempdir()) / f"kclaude-pane-{pid}.sid"
        if path.exists():
            try:
                if json.loads(path.read_text(encoding="utf-8-sig")).get("sid") == sid:
                    return None
            except Exception:
                pass  # unreadable/foreign beacon for our pid -> overwrite
        payload = {
            "sid": sid,
            "cwd": cwd or os.getcwd(),
            "pid": pid,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        path.write_text(json.dumps(payload, separators=(",", ":")),
                        encoding="utf-8")
        return str(path)
    except Exception:
        return None
