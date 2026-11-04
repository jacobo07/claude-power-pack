"""Structural fingerprint of a compiled function: coarse, toolchain-independent features read from the disassembly. Used to cluster, retrieve
similar solved functions (CBR) and route a regime. Never a verdict."""
import hashlib
import re
from collections import Counter

from .certify import text_rows

_REG = re.compile(r"\b(r|f|cr)(\d+)\b")
_MEM = ("lwz", "lbz", "lhz", "lha", "stw", "stb", "sth", "lfs", "lfd", "stfs", "stfd", "lwzx", "stwx", "lmw", "stmw")


def norm_op(op):
    return op.rstrip(".+-")


def fingerprint(adapter, obj, symbols):
    rows = []
    for s in symbols:
        r = text_rows(adapter, obj, [s])[s]
        if r is None:
            return None
        rows += r
    ops = [norm_op(r[0]) for r in rows]
    c = Counter(ops)
    shape = "".join(sorted(set(o[0] for o in ops)))
    return {
        "n_ins": len(rows),
        "opcodes": dict(sorted(c.items())),
        "seq_sha": hashlib.sha256(" ".join(ops).encode()).hexdigest()[:16],
        "bag_sha": hashlib.sha256(" ".join(sorted(ops)).encode()).hexdigest()[:16],
        "branches": sum(1 for o in ops if o.startswith("b") and o not in ("blr", "bctr")),
        "calls": sum(1 for o in ops if o in ("bl", "bctrl", "blrl")),
        "indirect_calls": sum(1 for o in ops if o in ("bctrl", "mtctr")),
        "mem": sum(c[o] for o in _MEM if o in c),
        "float": sum(1 for o in ops if o.startswith("f")),
        "relocs": sorted({x[3] for x in rows if x[3]}),
        "frame": next((int(m.group(1)) for r in rows if r[0] == "stwu" for m in [re.search(r"r1,(-?\d+)\(r1\)", r[1])] if m), 0),
        "klass": shape,
    }


def distance(a, b):
    """0.0 identical sequence .. 1.0 disjoint. Opcode-bag L1 distance normalised by total size."""
    if a is None or b is None:
        return 1.0
    keys = set(a["opcodes"]) | set(b["opcodes"])
    num = sum(abs(a["opcodes"].get(k, 0) - b["opcodes"].get(k, 0)) for k in keys)
    den = sum(a["opcodes"].values()) + sum(b["opcodes"].values())
    return round(num / den, 4) if den else 1.0
