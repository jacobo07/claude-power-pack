"""Language provenance for the C++ lane. Provenance is NOT certification: it is independent, graded evidence (from the object, not from the source) that a function
came from C++. Rules are fixed before use:
  E2  a constructor chain (a vptr install plus a call to a base constructor) or a deleting destructor (a D0 symbol next to a vptr-installing destructor)  -- C cannot write these
  E3  exactly one vptr install (also writable in C as a table-pointer store)
  E0  C++-mangled symbol(s), no vptr evidence
  NONE no C++ evidence (unmangled symbols only)
Data-layout evidence (the vtable itself) is graded by the Object Model, not here."""
import re

from . import certify as C
from . import om as OM

_CTOR = re.compile(r"^_ZN\d+\w+?C[12]E")
_D0 = re.compile(r"D0Ev$")


def grade(adapter, obj, symbols):
    syms = list(symbols)
    img = OM.Image(adapter, {"o": obj})
    installs, edges = OM.scan_installs(img)
    inst = {s for s, _ in installs}
    ev, mangled = [], [s for s in syms if s.startswith("_Z")]
    g = "NONE"
    if mangled:
        g = "E0"
    mine = [s for s in syms if s in inst]
    if mine:
        g = "E3"
        ev.append("%d symbol(s) install a vptr" % len(mine))
    chain = [s for s in mine if _CTOR.match(s) and _calls_base_ctor(adapter, obj, s)]
    deleting = [s for s in syms if _D0.search(s)] if mine else []
    if chain:
        g = "E2"
        ev.append("constructor chain: " + chain[0])
    if deleting:
        g = "E2"
        ev.append("deleting destructor: " + deleting[0])
    return {"grade": g, "evidence": ev, "e1": "NOT_GRADED_HERE", "vptr_symbols": sorted(mine)}


def _calls_base_ctor(adapter, obj, sym):
    rows = C.text_rows(adapter, obj, [sym])[sym] or []
    for r in rows:
        if r[2] == "R_PPC_REL24" and r[3]:
            d = OM.demangle(r[3])
            if d and d["kind"] == "ctor" and r[3] != sym:
                return True
    return False
