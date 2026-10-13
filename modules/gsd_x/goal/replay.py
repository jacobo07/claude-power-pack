"""Bounded parallel REPLAY for the independent judge (spec S9, D16).

The judge re-runs each satisfied obligation's pinned gate. Independent re-runs may overlap, under a bound
that only ever goes DOWN:

    bound = min( frontier.bound(state)            posture ECONOMY 1 / BALANCED 2 / WALL_CLOCK 4,
                                                  lowered by the goal budget's `max_parallel`
               , memory_bound(free RAM)           >= 3072 MB: 4, >= 1536 MB: 2, below or unreadable: 1
               , GSDX_REPLAY_MAX )                a positive int, when set

and 1 when the frontier is switched off (`GSDX_FRONTIER` / `FRONTIER.off`). A goal that never declared a
posture is ECONOMY, so it replays serially exactly as before. The probe is read at every call and never
cached: the pressure that matters is the pressure now.

Two replays overlap only when `proof.independent` holds for their `frontier.gate_unit`s -- the one
definition of independence. An undeclared unit is not independent of anything, and two `integration`
gates share `integration-env`, so both stay serial. Every started gate is joined before this module
returns, whatever the others did: the judge may not report while a gate it started is still running.
"""
from __future__ import annotations

import ctypes
import os
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path
from types import SimpleNamespace

from . import frontier as fr
from . import proof as pf

MAX_ENV = "GSDX_REPLAY_MAX"
MB_FOR_FOUR = 3072
MB_FOR_TWO = 1536
_PROBE = object()          # "read the host now"; an explicit None means "unreadable"


def free_ram_mb():
    """Available physical memory in MB, or None when the host will not say (unknown escalates safe)."""
    try:
        if os.name == "nt":
            class MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            ms = MS()
            ms.dwLength = ctypes.sizeof(MS)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms)):
                return ms.ullAvailPhys // (1024 * 1024)
            return None
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) // 1024
    except (OSError, ValueError, AttributeError):
        return None
    return None


def memory_bound(free_mb) -> int:
    """How many replays this much free memory allows. Unreadable is the smallest answer, never the largest."""
    if not isinstance(free_mb, (int, float)) or isinstance(free_mb, bool):
        return 1
    if free_mb >= MB_FOR_FOUR:
        return 4
    if free_mb >= MB_FOR_TWO:
        return 2
    return 1


def replay_bound(state, free_mb=_PROBE, env=None) -> int:
    """The number of gates the judge may run at once for this goal, right now."""
    if not fr.frontier_enabled():
        return 1
    n = fr.bound(SimpleNamespace(state=state))
    n = min(n, memory_bound(free_ram_mb() if free_mb is _PROBE else free_mb))
    raw = (os.environ if env is None else env).get(MAX_ENV)
    try:
        cap = int(str(raw).strip()) if raw is not None else None
    except ValueError:
        cap = None
    if cap is not None and cap >= 1:
        n = min(n, cap)
    return max(1, n)


def run_bounded(items: list, run_one, bound: int, units: list) -> list:
    """`run_one(item)` for every item, at most `bound` at a time, results in the order of `items`.

    `units[i]` is item i's declared unit (reads / writes / resources). A bound of 1 is the plain serial
    loop. The executor's context joins every started call before this returns, so a failure in one never
    leaves another running; the first exception is re-raised only after all have finished.
    """
    n = len(items)
    results: list = [None] * n
    if bound <= 1 or n <= 1:
        for i, item in enumerate(items):
            results[i] = run_one(item)
        return results
    pending = list(range(n))
    running: dict = {}
    first_exc = None
    with ThreadPoolExecutor(max_workers=bound) as ex:
        while pending or running:
            admitted = True
            while admitted and len(running) < bound:
                admitted = False
                for i in pending:
                    if all(pf.independent(units[i], units[j]) for j in running.values()):
                        pending.remove(i)
                        running[ex.submit(run_one, items[i])] = i
                        admitted = True
                        break
            done, _ = wait(list(running), return_when=FIRST_COMPLETED)
            for fut in done:
                i = running.pop(fut)
                try:
                    results[i] = fut.result()
                except BaseException as exc:  # noqa: BLE001 -- re-raised below, after every call is joined
                    if first_exc is None:
                        first_exc = exc
    if first_exc is not None:
        raise first_exc
    return results
