"""Typed resource requirements for a mission (stage M2).

A requirement is {id, kind, arg, obligation}. The sweep evaluates them with no model call:
MET, UNMET, or UNKNOWN (the probe raised or the arg is unusable). UNKNOWN is never MET.
Requirements are grouped by the obligation they gate; the mission is admissible when ANY obligation has every
requirement MET (sibling independence).

Probes are the only I/O. ``PROBES`` is the seam: tests replace entries, or pass ``probes=`` to ``evaluate``.
"""
from __future__ import annotations

import os
import subprocess
from typing import Any, Callable

KINDS = ("ram_free_gb", "path_exists", "no_process")
MET, UNMET, UNKNOWN = "MET", "UNMET", "UNKNOWN"
NO_OBLIGATION = "(mission)"


def probe_ram_free_gb(arg: Any) -> float:
    """Free physical memory in GB. psutil when importable, else Win32_OperatingSystem.FreePhysicalMemory."""
    try:
        import psutil  # type: ignore
        return psutil.virtual_memory().available / float(1 << 30)
    except ImportError:
        pass
    out = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command",
         "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory"],
        capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError(f"FreePhysicalMemory query failed: {(out.stderr or out.stdout).strip()[:200]}")
    return int(out.stdout.strip()) / float(1 << 20)   # the counter is KB


def probe_path_exists(arg: Any) -> bool:
    """True/False only when the OS answered; a permission or I/O error raises (UNKNOWN), never False."""
    try:
        os.stat(str(arg))
        return True
    except (FileNotFoundError, NotADirectoryError):
        return False


def probe_no_process(arg: Any) -> int:
    """How many processes carry this image name (0 = none running)."""
    name = str(arg).strip().lower()
    stem = name[:-4] if name.endswith(".exe") else name
    try:
        import psutil  # type: ignore
        n = 0
        for p in psutil.process_iter(["name"]):
            pn = str(p.info.get("name") or "").lower()
            if pn == name or (pn[:-4] if pn.endswith(".exe") else pn) == stem:
                n += 1
        return n
    except ImportError:
        pass
    out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {stem}.exe", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError(f"tasklist failed: {(out.stderr or out.stdout).strip()[:200]}")
    return sum(1 for ln in out.stdout.splitlines() if ln.startswith('"'))


PROBES: dict[str, Callable[[Any], Any]] = {
    "ram_free_gb": probe_ram_free_gb,
    "path_exists": probe_path_exists,
    "no_process": probe_no_process,
}


def _judge(kind: str, arg: Any, measured: Any) -> tuple[str, str]:
    if kind == "ram_free_gb":
        need = float(arg)
        got = float(measured)
        return (MET if got >= need else UNMET), f"{got:.1f} GB free < {need:g} GB needed" if got < need else f"{got:.1f} GB free"
    if kind == "path_exists":
        return (MET, "present") if measured else (UNMET, "absent")
    if kind == "no_process":
        return (MET, "not running") if int(measured) == 0 else (UNMET, f"{int(measured)} running")
    raise ValueError(f"unknown requirement kind {kind!r}")


def check_one(req: dict, probes: dict | None = None) -> dict:
    """Evaluate one requirement. Any failure to measure is UNKNOWN with the error named."""
    kind, arg = req.get("kind"), req.get("arg")
    row = {"id": req.get("id"), "kind": kind, "arg": arg, "obligation": req.get("obligation") or NO_OBLIGATION}
    try:
        probe = (probes or PROBES).get(kind)
        if probe is None:
            raise ValueError(f"unknown requirement kind {kind!r}")
        measured = probe(arg)
        status, detail = _judge(kind, arg, measured)
        row.update({"status": status, "measured": measured if isinstance(measured, (int, float, bool)) else str(measured),
                    "detail": detail})
    except Exception as exc:  # noqa: BLE001 -- unmeasurable is UNKNOWN, with the reason on the row
        row.update({"status": UNKNOWN, "measured": None, "detail": "unmeasured",
                    "error": f"{type(exc).__name__}: {exc}"[:200]})
    return row


def evaluate(requires: list[dict], probes: dict | None = None) -> dict:
    """{admissible, actionable:[oid], waiting:[oid], obligations:{oid:{status, requirements:[...]}}}.
    An obligation is MET only when every requirement is MET; UNMET beats UNKNOWN when both occur."""
    groups: dict[str, list[dict]] = {}
    for req in requires or []:
        row = check_one(req, probes)
        groups.setdefault(row["obligation"], []).append(row)
    obligations = {}
    for oid, rows in groups.items():
        sts = {r["status"] for r in rows}
        status = UNMET if UNMET in sts else UNKNOWN if UNKNOWN in sts else MET
        obligations[oid] = {"status": status, "requirements": rows}
    actionable = sorted(o for o, v in obligations.items() if v["status"] == MET)
    waiting = sorted(o for o, v in obligations.items() if v["status"] != MET)
    return {"admissible": bool(actionable), "actionable": actionable, "waiting": waiting, "obligations": obligations}


def key(ev: dict) -> str:
    """Identity of an evaluation WITHOUT the measured numbers, so a drifting RAM reading is not a change."""
    return "|".join(f"{o}:{v['status']}:" + ",".join(f"{r['id']}={r['status']}" for r in v["requirements"])
                    for o, v in sorted(ev["obligations"].items()))


def _unmet_text(r: dict) -> str:
    base = f"{r['kind']} {r['arg']}"
    return f"{base} {r['status']} ({r.get('error') or r.get('detail')})"


def reason(ev: dict) -> str:
    parts = []
    for oid in ev["waiting"]:
        bad = [r for r in ev["obligations"][oid]["requirements"] if r["status"] != MET]
        parts.append(f"{oid} needs " + "; ".join(_unmet_text(r) for r in bad))
    return "WAIT_RESOURCE: " + " | ".join(parts)


def snapshot(ev: dict, now: float) -> dict:
    """What the record keeps (and the card reads): per-obligation status and the requirements still unmet."""
    return {"at": now, "actionable": ev["actionable"], "waiting": ev["waiting"],
            "unmet": {oid: [_unmet_text(r) for r in ev["obligations"][oid]["requirements"] if r["status"] != MET]
                      for oid in ev["waiting"]}}


def card_lines(rec: dict) -> list[str]:
    """Empty for a mission with no `requires`, so its card is byte-for-byte what it was."""
    snap = rec.get("resource_eval")
    if not rec.get("requires") or not snap:
        return []
    lines = ["RESOURCES (checked by the supervisor, not by you; do not spend calls rediscovering them):"]
    if snap.get("actionable"):
        lines.append("  ACTIONABLE now: " + ", ".join(snap["actionable"]) + " (every requirement met)")
    for oid in snap.get("waiting") or []:
        lines.append(f"  WAITING: {oid} -- " + "; ".join((snap.get("unmet") or {}).get(oid) or ["unmet"]))
    if snap.get("actionable") and snap.get("waiting"):
        lines.append("  Work only on the actionable obligation(s); a waiting one is woken by the sweep.")
    return lines
