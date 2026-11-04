"""The judge: exact comparison of a candidate object against a target object for one function. Pure and deterministic; no model call.

A candidate is EXACT iff, for every symbol the function lists: it is defined in both objects, the extents are equal in size, the bytes are equal after masking only
the bit fields their relocations cover, the relocation lists are equal by (offset, type, target identity, addend), and every local data section a relocation points at is
byte-identical. `pct` is an instruction-aligned similarity for ordering search; it is 100.0 only for an EXACT candidate. `pct` is never a verdict.
"""
import difflib
import struct

from .elf import Elf, ElfError


def words(b):
    return [b[i:i + 4] for i in range(0, len(b) - len(b) % 4, 4)]


def _pct(a, b):
    if a == b:
        return 100.0
    if not a or not b:
        return 0.0
    return round(min(99.99, 100.0 * difflib.SequenceMatcher(None, words(a), words(b), autojunk=False).ratio()), 2)


def read_elf(path):
    with open(path, "rb") as fh:
        return Elf(fh.read())


def judge_symbol(te, ce, sym):
    """-> dict for one symbol: {defined, size_eq, code, relocs, data, pct, reasons[], unknown_relocs}"""
    r = {"symbol": sym, "defined": False, "size_eq": False, "code": False, "relocs": False, "data": False, "pct": 0.0, "reasons": [], "unknown_relocs": []}
    t, c = te.extent(sym), ce.extent(sym)
    if t is None:
        r["reasons"].append("TARGET_SYMBOL_ABSENT")
        return r
    if c is None:
        r["reasons"].append("SYMBOL_UNDEFINED")
        return r
    r["defined"] = True
    (ts, to, tz), (cs, co, cz) = t, c
    tb, tu = te.masked(ts, to, tz)
    cb, cu = ce.masked(cs, co, cz)
    r["unknown_relocs"] = sorted(set(tu) | set(cu))
    r["size_eq"] = tz == cz
    r["pct"] = _pct(tb, cb)
    r["code"] = r["size_eq"] and tb == cb
    tr, cr = te.reloc_rows(ts, to, tz), ce.reloc_rows(cs, co, cz)
    r["relocs"] = tr == cr
    data_ok = True
    for (_o, _t, ident, _a) in cr:
        if ident.startswith("sec:"):                           # a local section of OUR object: its bytes must equal the target's section of that name
            nm = ident[4:]
            a, b = ce.section(nm), te.section(nm)
            if b is None or ce.section_bytes(a) != te.section_bytes(b):
                data_ok = False
    r["data"] = data_ok
    if not r["size_eq"]:
        r["reasons"].append("SIZE")
    if not r["code"] and r["size_eq"]:
        r["reasons"].append("CODE")
    if not r["relocs"]:
        r["reasons"].append("RELOCS")
    if not data_ok:
        r["reasons"].append("DATA")
    if r["unknown_relocs"]:
        r["reasons"].append("UNKNOWN_RELOC_TYPE")
    if r["code"] and r["relocs"] and data_ok and not r["unknown_relocs"]:
        r["pct"] = 100.0
    elif r["pct"] >= 100.0:
        r["pct"] = 99.99
    return r


def judge(target_path, cand_path, symbols):
    """-> {compiles, exact, pct, symbols:[...], reasons}. An unreadable candidate is NOT a mismatch measurement: compiles=False, exact=None."""
    try:
        te = read_elf(target_path)
    except (OSError, ElfError) as e:
        return {"compiles": None, "exact": None, "pct": None, "symbols": [], "reasons": ["TARGET_UNREADABLE"], "error": str(e)}
    try:
        ce = read_elf(cand_path)
    except (OSError, ElfError) as e:
        return {"compiles": False, "exact": None, "pct": None, "symbols": [], "reasons": ["CANDIDATE_UNREADABLE"], "error": str(e)}
    rows = [judge_symbol(te, ce, s) for s in symbols]
    exact = all(not x["reasons"] and x["pct"] == 100.0 for x in rows)
    pct = round(sum(x["pct"] for x in rows) / len(rows), 2) if rows else 0.0
    reasons = sorted({x for r in rows for x in r["reasons"]})
    return {"compiles": True, "exact": exact, "pct": 100.0 if exact else min(pct, 99.99), "symbols": rows, "reasons": reasons}


def size_gap(target_path, cand_path, symbols):
    """Total byte-size difference over the function's symbols (the second Pareto axis). None when a symbol is absent."""
    te, ce = read_elf(target_path), read_elf(cand_path)
    g = 0
    for s in symbols:
        a, b = te.extent(s), ce.extent(s)
        if a is None or b is None:
            return None
        g += abs(a[2] - b[2])
    return g
