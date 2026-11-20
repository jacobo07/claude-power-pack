"""BI-18 raster->trace lane validators (pure, no tracer invoked here).

A traced SVG is NOT a production vector: it is measured, then a human-or-gate
decision (inspect / repair / reject) is required before it may be used.
"""
import re

DECISIONS = ("inspect", "repair", "reject")
_PATH = re.compile(r"<path\b[^>]*\bd=\"([^\"]*)\"", re.S)
_CMD = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]")
_NUM = re.compile(r"-?\d+\.\d+")


def measure_trace(svg: bytes) -> dict:
    """Path count, command count, max coordinate precision, byte size."""
    text = svg.decode("utf-8", "replace")
    ds = _PATH.findall(text)
    digits = [len(n.split(".")[1]) for d in ds for n in _NUM.findall(d)]
    return {"paths": len(ds), "commands": sum(len(_CMD.findall(d)) for d in ds),
            "max_decimals": max(digits) if digits else 0, "bytes": len(svg)}


def check_trace(svg: bytes, decision, limits=None) -> list:
    """Problems that stop a traced SVG being accepted. Empty list = acceptable."""
    lim = {"max_paths": 40, "max_commands": 400, "max_decimals": 3}
    lim.update(limits or {})
    out = []
    if decision not in DECISIONS:
        out.append("no inspect/repair/reject decision recorded")
    elif decision == "reject":
        out.append("decision is reject")
    m = measure_trace(svg)
    if m["paths"] == 0:
        out.append("no paths: nothing traced")
    if m["paths"] > lim["max_paths"]:
        out.append(f"path count {m['paths']} exceeds {lim['max_paths']}")
    if m["commands"] > lim["max_commands"]:
        out.append(f"command count {m['commands']} exceeds {lim['max_commands']}")
    if m["max_decimals"] > lim["max_decimals"]:
        out.append(f"coordinate precision {m['max_decimals']} decimals exceeds {lim['max_decimals']} (unrepaired trace)")
    return out
