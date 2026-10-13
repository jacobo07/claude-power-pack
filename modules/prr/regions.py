"""Read-only per-process memory region attribution (Windows).

Splits a process's address space the way VMMap does: by region type (image / mapped / private) and state
(committed / reserved), and adds the resident view (working set, private working set) from
GetProcessMemoryInfo. Exists because "private bytes" (commit charge) on Windows and anonymous RSS on Linux are
different quantities; comparing them is the first suspect for the Windows~Linux floor gap (goal prr, priority 3).

Nothing here writes to, suspends, trims or signals the target. Off Windows, `scan()` raises.

CLI: python -m modules.prr.regions [--name claude.exe] [--json]
"""
from __future__ import annotations

import argparse
import ctypes
import json
import subprocess
import sys
from ctypes import wintypes

MEM_COMMIT, MEM_RESERVE = 0x1000, 0x2000
MEM_IMAGE, MEM_MAPPED, MEM_PRIVATE = 0x1000000, 0x40000, 0x20000
PROCESS_QUERY_INFORMATION, PROCESS_VM_READ = 0x0400, 0x0010
MB = 1024 * 1024


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
                ("AllocationProtect", wintypes.DWORD), ("PartitionId", wintypes.WORD),
                ("RegionSize", ctypes.c_size_t), ("State", wintypes.DWORD),
                ("Protect", wintypes.DWORD), ("Type", wintypes.DWORD)]


class PROCESS_MEMORY_COUNTERS_EX2(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                ("PrivateUsage", ctypes.c_size_t), ("PrivateWorkingSetSize", ctypes.c_size_t),
                ("SharedCommitUsage", ctypes.c_ulonglong)]


def _api():
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    k32.OpenProcess.restype = wintypes.HANDLE
    k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k32.VirtualQueryEx.restype = ctypes.c_size_t
    k32.VirtualQueryEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.POINTER(MEMORY_BASIC_INFORMATION),
                                   ctypes.c_size_t]
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
    return k32, psapi


def scan(pid: int) -> dict:
    """Region split for one pid. Raises OSError when the process cannot be opened."""
    if sys.platform != "win32":
        raise OSError("regions.scan is Windows-only; use /proc/<pid>/smaps_rollup on Linux")
    k32, psapi = _api()
    h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h:
        raise OSError(ctypes.get_last_error(), f"OpenProcess({pid}) failed")
    try:
        pmc = PROCESS_MEMORY_COUNTERS_EX2()
        pmc.cb = ctypes.sizeof(pmc)
        if not psapi.GetProcessMemoryInfo(h, ctypes.byref(pmc), pmc.cb):
            raise OSError(ctypes.get_last_error(), f"GetProcessMemoryInfo({pid}) failed")
        split = {f"{t}_{s}": 0 for t in ("image", "mapped", "private") for s in ("commit", "reserve")}
        largest_private_commit, n = 0, 0
        mbi, addr = MEMORY_BASIC_INFORMATION(), 0
        while k32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
            size = mbi.RegionSize
            kind = {MEM_IMAGE: "image", MEM_MAPPED: "mapped", MEM_PRIVATE: "private"}.get(mbi.Type)
            state = {MEM_COMMIT: "commit", MEM_RESERVE: "reserve"}.get(mbi.State)
            if kind and state:
                split[f"{kind}_{state}"] += size
                if kind == "private" and state == "commit":
                    largest_private_commit = max(largest_private_commit, size)
            n += 1
            addr = (mbi.BaseAddress or 0) + size
            if addr >= 1 << 47:
                break
        out = {k: round(v / MB, 1) for k, v in split.items()}
        out.update(pid=pid, regions=n, largest_private_commit_mb=round(largest_private_commit / MB, 1),
                   private_usage_mb=round(pmc.PrivateUsage / MB, 1),
                   working_set_mb=round(pmc.WorkingSetSize / MB, 1),
                   private_working_set_mb=round(pmc.PrivateWorkingSetSize / MB, 1),
                   peak_working_set_mb=round(pmc.PeakWorkingSetSize / MB, 1))
        # Committed private that is not resident: paged out or never touched. Not RAM, but commit charge.
        out["private_nonresident_mb"] = round(out["private_usage_mb"] - out["private_working_set_mb"], 1)
        return out
    finally:
        k32.CloseHandle(h)


def pids(name: str) -> list[int]:
    r = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {name}", "/FO", "CSV", "/NH"],
                       capture_output=True, text=True, errors="replace")
    out = []
    for line in r.stdout.splitlines():
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) > 1 and parts[1].isdigit():
            out.append(int(parts[1]))
    return out


def summarize(rows: list[dict]) -> dict:
    keys = ["private_usage_mb", "private_working_set_mb", "private_nonresident_mb", "working_set_mb",
            "private_commit", "private_reserve", "image_commit", "mapped_commit"]
    ok = [r for r in rows if "error" not in r]
    if not ok:
        return {"n": 0}
    med = lambda k: sorted(r[k] for r in ok)[len(ok) // 2]
    return {"n": len(ok), "errors": len(rows) - len(ok),
            "sum": {k: round(sum(r[k] for r in ok), 1) for k in keys},
            "median": {k: med(k) for k in keys}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="PRR read-only region attribution (Windows)")
    ap.add_argument("--name", default="claude.exe")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rows = []
    for pid in pids(a.name):
        try:
            rows.append(scan(pid))
        except OSError as e:
            rows.append({"pid": pid, "error": str(e)})
    rep = {"name": a.name, "summary": summarize(rows), "rows": rows}
    print(json.dumps(rep if a.json else rep["summary"], indent=1))
    return 0 if rep["summary"]["n"] else 1


if __name__ == "__main__":
    sys.exit(main())
