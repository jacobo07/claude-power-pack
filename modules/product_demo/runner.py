"""Bounded child run: a wall-clock ceiling and a whole-tree kill that touches
nothing else.

Why a Job Object: Playwright's Python API does not expose the browser PID, and a
timeout that kills only the direct child leaves node.exe (driver) and chrome.exe
(browser + renderers) orphaned -- the leak every existing launcher in this repo
has. Killing by image name would also kill the Owner's Playwright MCP and
mcp-chrome, which are live. So the child is put in a Job Object with
KILL_ON_JOB_CLOSE before it can spawn anything: every descendant joins the job,
TerminateJobObject ends exactly that set, and closing our handle on any exit path
(including our own crash) ends it too.

POSIX: new session + killpg, the equivalent boundary.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass, field

IS_WINDOWS = sys.platform == "win32"


@dataclass
class RunResult:
    outcome: str                 # "ok" | "failed" | "timeout" | "spawn_error"
    returncode: int | None
    stdout: str
    stderr: str
    elapsed_s: float
    pids_seen: list = field(default_factory=list)   # job members observed before exit (Windows)

    @property
    def ok(self) -> bool:
        return self.outcome == "ok"


if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    _k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _JobObjectExtendedLimitInformation = 9
    _JobObjectBasicProcessIdList = 3
    _KILL_ON_JOB_CLOSE = 0x2000
    _PROCESS_SET_QUOTA = 0x0100
    _PROCESS_TERMINATE = 0x0001

    class _IO_COUNTERS(ctypes.Structure):
        _fields_ = [(n, ctypes.c_ulonglong) for n in (
            "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
            "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

    class _BASIC_LIMIT(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong),
                    ("PerJobUserTimeLimit", ctypes.c_longlong),
                    ("LimitFlags", wintypes.DWORD),
                    ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t),
                    ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t),
                    ("PriorityClass", wintypes.DWORD),
                    ("SchedulingClass", wintypes.DWORD)]

    class _EXTENDED_LIMIT(ctypes.Structure):
        _fields_ = [("BasicLimitInformation", _BASIC_LIMIT),
                    ("IoInfo", _IO_COUNTERS),
                    ("ProcessMemoryLimit", ctypes.c_size_t),
                    ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t),
                    ("PeakJobMemoryUsed", ctypes.c_size_t)]

    _k32.CreateJobObjectW.restype = wintypes.HANDLE
    _k32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    _k32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    _k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    _k32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    _k32.OpenProcess.restype = wintypes.HANDLE
    _k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _k32.CloseHandle.argtypes = [wintypes.HANDLE]
    _k32.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                               wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]

    def _new_job():
        job = _k32.CreateJobObjectW(None, None)
        if not job:
            raise OSError(ctypes.get_last_error(), "CreateJobObjectW failed")
        info = _EXTENDED_LIMIT()
        info.BasicLimitInformation.LimitFlags = _KILL_ON_JOB_CLOSE
        if not _k32.SetInformationJobObject(job, _JobObjectExtendedLimitInformation,
                                            ctypes.byref(info), ctypes.sizeof(info)):
            err = ctypes.get_last_error()
            _k32.CloseHandle(job)
            raise OSError(err, "SetInformationJobObject failed")
        return job

    def _assign(job, pid: int) -> None:
        h = _k32.OpenProcess(_PROCESS_SET_QUOTA | _PROCESS_TERMINATE, False, pid)
        if not h:
            raise OSError(ctypes.get_last_error(), f"OpenProcess({pid}) failed")
        try:
            if not _k32.AssignProcessToJobObject(job, h):
                raise OSError(ctypes.get_last_error(), "AssignProcessToJobObject failed")
        finally:
            _k32.CloseHandle(h)

    def job_pids(job) -> list:
        """PIDs currently in the job (used by the kill drill)."""
        n = 1024
        buf = (ctypes.c_ulonglong * (2 + n))()
        ok = _k32.QueryInformationJobObject(job, _JobObjectBasicProcessIdList,
                                            ctypes.byref(buf), ctypes.sizeof(buf), None)
        if not ok:
            return []
        # JOBOBJECT_BASIC_PROCESS_ID_LIST: DWORD NumberOfAssignedProcesses, DWORD
        # NumberOfProcessIdsInList (together the first 8 bytes), then ULONG_PTR ids.
        listed = int(buf[0] >> 32)
        return [int(buf[1 + i]) for i in range(min(listed, n)) if buf[1 + i]]


def run_bounded(argv: list, *, timeout_s: float, cwd: str | None = None,
                env: dict | None = None, observe_pids=None) -> RunResult:
    """Run argv with a wall-clock ceiling; on timeout the WHOLE descendant tree dies.

    observe_pids: optional callable(list[int]) invoked once the child is running,
    with the job's member PIDs (Windows only). The kill drill uses it to prove the
    exact set it saw is gone afterwards.
    """
    t0 = time.monotonic()
    creation = 0
    job = None
    kwargs = {}
    if IS_WINDOWS:
        # Suspended start would be ideal; CREATE_SUSPENDED is not exposed by
        # subprocess, so the child is a Python interpreter that spawns nothing
        # for its first import phase -- assignment happens well before Chromium.
        creation = subprocess.CREATE_NEW_PROCESS_GROUP
        try:
            job = _new_job()
        except OSError as exc:
            return RunResult("spawn_error", None, "", f"job object: {exc}", 0.0)
    else:
        kwargs["start_new_session"] = True

    try:
        proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, encoding="utf-8",
                                errors="replace", creationflags=creation, **kwargs)
    except OSError as exc:
        if job:
            _k32.CloseHandle(job)
        return RunResult("spawn_error", None, "", str(exc), time.monotonic() - t0)

    pids_seen: list = []
    try:
        if IS_WINDOWS:
            try:
                _assign(job, proc.pid)
            except OSError as exc:
                proc.kill()
                proc.communicate()
                return RunResult("spawn_error", None, "", f"assign to job: {exc}",
                                 time.monotonic() - t0)
        try:
            if observe_pids is not None and IS_WINDOWS:
                # Give the tree a moment to form, then report it.
                # Sample until the tree has formed (>= 3 members) and then held
                # steady for ~1 s, so the drill sees the renderers, not just the root.
                deadline = time.monotonic() + min(timeout_s * 0.8, 20.0)
                steady = 0
                while time.monotonic() < deadline and proc.poll() is None:
                    time.sleep(0.25)
                    members = set(job_pids(job))
                    grew = not members <= set(pids_seen)
                    pids_seen = sorted(set(pids_seen) | members)
                    steady = 0 if grew else steady + 1
                    if len(pids_seen) >= 3 and steady >= 4:
                        break
                observe_pids(list(pids_seen))
            remaining = max(0.1, timeout_s - (time.monotonic() - t0))
            out, err = proc.communicate(timeout=remaining)
        except subprocess.TimeoutExpired:
            if IS_WINDOWS:
                _k32.TerminateJobObject(job, 1)
            else:
                import signal
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            out, err = proc.communicate()
            return RunResult("timeout", proc.returncode, out or "", err or "",
                             time.monotonic() - t0, pids_seen)
        return RunResult("ok" if proc.returncode == 0 else "failed", proc.returncode,
                         out or "", err or "", time.monotonic() - t0, pids_seen)
    finally:
        if IS_WINDOWS and job:
            # KILL_ON_JOB_CLOSE: anything still alive in the tree dies here, on
            # every exit path, including an exception in this function.
            _k32.CloseHandle(job)


def pid_alive(pid: int) -> bool:
    if IS_WINDOWS:
        h = _k32.OpenProcess(0x1000, False, pid)   # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        try:
            code = wintypes.DWORD()
            _k32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
            _k32.GetExitCodeProcess(h, ctypes.byref(code))
            return code.value == 259            # STILL_ACTIVE
        finally:
            _k32.CloseHandle(h)
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False
