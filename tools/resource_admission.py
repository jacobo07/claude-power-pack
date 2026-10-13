"""Resource admission: refuse a worker launch when free RAM is below the profile floor.

Verdicts: ADMIT | REFUSE_LOW_MEMORY | UNKNOWN_REFUSE (an unreadable reading refuses; it never admits).
Floors: vault/config/resource-floors.json (MB per worker profile, "default" for any other).
Kill switch: CPP_RESOURCE_ADMISSION=off (also 0/false). Pure apart from read_available_mb.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

FLOORS_PATH = Path(__file__).resolve().parent.parent / "vault" / "config" / "resource-floors.json"
ADMIT, REFUSE_LOW_MEMORY, UNKNOWN_REFUSE = "ADMIT", "REFUSE_LOW_MEMORY", "UNKNOWN_REFUSE"
FALLBACK_FLOOR_MB = 3000


def switch_off() -> bool:
    return str(os.environ.get("CPP_RESOURCE_ADMISSION") or "").strip().lower() in ("0", "off", "false")


def read_available_mb() -> dict:
    """{"available_mb": float | None, "source": str}. None = unreadable, never 0."""
    try:
        if sys.platform.startswith("linux"):
            for line in Path("/proc/meminfo").read_text().splitlines():
                if line.startswith("MemAvailable:"):
                    return {"available_mb": int(line.split()[1]) / 1024.0, "source": "/proc/meminfo"}
        elif sys.platform == "win32":
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            ms = MS()
            ms.dwLength = ctypes.sizeof(MS)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms)):
                return {"available_mb": ms.ullAvailPhys / 1048576.0, "source": "GlobalMemoryStatusEx"}
        elif sys.platform == "darwin":
            out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=5).stdout
            page = 4096
            pages = 0
            for line in out.splitlines():
                if "page size of" in line:
                    page = int(line.split("page size of")[1].split()[0])
                elif line.startswith(("Pages free", "Pages inactive", "Pages speculative")):
                    pages += int(line.split(":")[1].strip().rstrip("."))
            if pages:
                return {"available_mb": pages * page / 1048576.0, "source": "vm_stat"}
    except Exception:
        pass
    return {"available_mb": None, "source": "unreadable"}


def floor_mb(profile: str | None, floors_path: Path | str | None = None) -> int:
    try:
        data = json.loads(Path(floors_path or FLOORS_PATH).read_text(encoding="utf-8-sig"))
        prof = data.get("profiles") or {}
        v = prof.get(profile) if profile in prof else data.get("default", FALLBACK_FLOOR_MB)
        return int(v)
    except Exception:
        return FALLBACK_FLOOR_MB


def verdict(reading: dict | None, profile: str | None, floors_path=None) -> dict:
    floor = floor_mb(profile, floors_path)
    mb = (reading or {}).get("available_mb")
    if isinstance(mb, bool) or not isinstance(mb, (int, float)) or mb != mb or mb < 0:
        v = UNKNOWN_REFUSE
    elif mb >= floor:
        v = ADMIT
    else:
        v = REFUSE_LOW_MEMORY
    return {"verdict": v, "available_mb": mb if v != UNKNOWN_REFUSE else None, "floor_mb": floor,
            "profile": profile or "default"}


def refusal(profile: str | None, reader=None, floors_path=None) -> dict | None:
    """None = admit (or switched off); else the verdict dict to ledger."""
    if switch_off():
        return None
    try:
        reading = (reader or read_available_mb)()
    except Exception:
        reading = None
    res = verdict(reading, profile, floors_path)
    return None if res["verdict"] == ADMIT else res
