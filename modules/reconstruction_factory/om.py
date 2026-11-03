"""Object Model recovery over a set of compiled objects (an IMAGE). Everything here is read from ELF bytes, relocations and disassembly; no source,
no private target. Facts and the rule that promotes them:

  vtable table   a defined `_ZTV<class>` symbol whose section is headed (2 zero words) and whose remaining words are relocations to functions
  vptr install   a function that builds `_ZTV<class>+8` (R_PPC_ADDR16_HA/LO) and stores it at offset 0 of its `this`
  vcall site     lwz vptr,0(this) ; lwz fn,SLOT*4(vptr) ; mtctr ; bctrl  -- in >= 2 DISTINCT functions bound to the table
Support rule: a table is a VTABLE only with >= 2 independent support KINDS among {data, install, vcall}; otherwise it stays a CANDIDATE.
Two installs of one table are ONE kind (same observation channel), and a table plus its own slots is ONE kind.

Prototype propagation: slot prototypes are decoded from Itanium-mangled slot symbols; an override inherits its base slot's slot index; a vcall
site's callee prototype is the base slot's. This-call: r3 is `this`; `field_accesses` reads member offsets from loads/stores through the saved this.
"""
import re

from .certify import text_rows
from .elf import Elf

TYPE = {"i": "s32", "j": "u32", "v": "void", "f": "f32", "c": "s8", "h": "u8", "s": "s16", "t": "u16", "b": "bool"}


def read_elf(p):
    with open(p, "rb") as fh:
        return Elf(fh.read())


def decode_type(s, i):
    """-> (type string, next index). P = pointer, K = const."""
    if s[i] == "P":
        t, j = decode_type(s, i + 1)
        return t + "*", j
    if s[i] == "K":
        t, j = decode_type(s, i + 1)
        return "const " + t, j
    if s[i].isdigit():
        m = re.match(r"(\d+)", s[i:])
        n = int(m.group(1))
        a = i + len(m.group(1))
        return s[a:a + n], a + n
    return TYPE.get(s[i], "?" + s[i]), i + 1


def demangle(sym):
    """Itanium subset -> {kind, cls, name, const, params, sym} or None. kinds: method, ctor, dtor, func."""
    if not sym.startswith("_Z"):
        return {"kind": "func", "cls": None, "name": sym, "const": False, "params": None, "sym": sym}
    s = sym[2:]
    if s[0] == "N":
        i, const = 1, False
        if s[i] == "K":
            const, i = True, i + 1
        parts = []
        while s[i].isdigit():
            m = re.match(r"(\d+)", s[i:])
            n = int(m.group(1))
            a = i + len(m.group(1))
            parts.append(s[a:a + n])
            i = a + n
        kind, name = "method", parts[-1]
        mm = re.match(r"(C[012]|D[012])", s[i:])
        if mm:
            kind, name = ("ctor" if mm.group(1)[0] == "C" else "dtor"), mm.group(1)
            i += 2
        if s[i] != "E":
            return None
        i += 1
        params = []
        while i < len(s):
            t, i = decode_type(s, i)
            params.append(t)
        return {"kind": kind, "cls": parts[-1] if kind != "method" else parts[-2] if len(parts) > 1 else None, "name": name, "const": const,
                "params": [p for p in params if p != "void"], "sym": sym}
    m = re.match(r"(\d+)", s)
    if not m:
        return None
    n = int(m.group(1))
    name = s[len(m.group(1)):len(m.group(1)) + n]
    i = len(m.group(1)) + n
    params = []
    while i < len(s):
        t, i = decode_type(s, i)
        params.append(t)
    return {"kind": "func", "cls": None, "name": name, "const": False, "params": [p for p in params if p != "void"], "sym": sym}


def class_of_table(sym):
    m = re.match(r"_ZTV(\d+)", sym)
    if not m:
        return None
    n = int(m.group(1))
    a = 4 + len(m.group(1))
    return sym[a:a + n]


class Image:
    """A set of objects with one adapter; names objects for provenance only."""

    def __init__(self, adapter, objs):
        self.adapter, self.objs = adapter, dict(objs)          # name -> path
        self.elfs = {k: read_elf(p) for k, p in self.objs.items()}

    def functions(self):
        for k, e in self.elfs.items():
            for s in e.defined_function_symbols():
                yield k, s["name"]

    def rows(self, obj, sym):
        return text_rows(self.adapter, self.objs[obj], [sym])[sym] or []


def scan_tables(img):
    out = {}
    for k, e in img.elfs.items():
        for s in e.symbols:
            c = class_of_table(s["name"])
            if c is None or not (0 < s["shndx"] < len(e.sections)) or s["size"] == 0:
                continue
            sec = e.sections[s["shndx"]]
            data = e.section_bytes(sec)[s["value"]:s["value"] + s["size"]]
            slots, headed = {}, data[:8] == b"\0" * 8
            for (ro, rt, si, ad) in e.relocs.get(sec["i"], []):
                if s["value"] <= ro < s["value"] + s["size"] and rt == 1:
                    slots[(ro - s["value"] - 8) // 4] = e.sym_identity(si)
            out[c] = {"class": c, "table": s["name"], "obj": k, "headed": headed, "slots": [slots[i] for i in sorted(slots)], "n_words": s["size"] // 4}
    return out


def scan_installs(img):
    """-> [(function symbol, class)]: builds _ZTV<c>+8 and stores it at offset 0 of a register. Also returns base-ctor edges {class: base}."""
    inst, edges = [], {}
    for obj, sym in img.functions():
        rows = img.rows(obj, sym)
        cls = None
        for i, r in enumerate(rows):
            if r[2] == "R_PPC_ADDR16_HA" and r[3] and r[3].startswith("_ZTV"):
                c = class_of_table(r[3].split("+")[0])
                reg = r[1].split(",")[0]
                for r2 in rows[i + 1:i + 6]:
                    if r2[0] == "addi" and r2[2] == "R_PPC_ADDR16_LO":
                        reg = r2[1].split(",")[0]
                    if r2[0] == "stw" and re.match(r"%s,0\(r\d+\)$" % reg, r2[1]):
                        cls = c
        if cls:
            inst.append((sym, cls))
            dm = demangle(sym)
            if dm and dm["kind"] == "ctor":
                for r in rows:
                    if r[2] == "R_PPC_REL24" and r[3]:
                        bd = demangle(r[3])
                        if bd and bd["kind"] == "ctor" and bd["cls"] != cls:
                            edges[cls] = bd["cls"]
    return inst, edges


def scan_vcalls(img):
    """-> [(function symbol, slot index)]"""
    out = []
    for obj, sym in img.functions():
        rows = img.rows(obj, sym)
        for i in range(len(rows) - 3):
            a, b, c, d = rows[i:i + 4]
            if a[0] == "lwz" and b[0] == "lwz" and c[0] == "mtctr" and d[0] == "bctrl":
                ma, mb = re.match(r"(r\d+),0\((r\d+)\)$", a[1]), re.match(r"(r\d+),(\d+)\((r\d+)\)$", b[1])
                if ma and mb and mb.group(3) == ma.group(1) and c[1] == mb.group(1):
                    out.append((sym, int(mb.group(2)) // 4))
    return out


def grade(kinds):
    return "VTABLE" if len(set(kinds)) >= 2 else "CANDIDATE"


def build_registry(img):
    tables, (installs, edges), vcalls = scan_tables(img), scan_installs(img), scan_vcalls(img)
    reg = {}
    classes = set(tables) | {c for _, c in installs} | set(edges)
    roots = {c for c in classes if c not in edges}
    for c in sorted(classes):
        t = tables.get(c)
        kinds = []
        if t and t["headed"] and t["slots"]:
            kinds.append("data")
        inst_fns = sorted({f for f, k in installs if k == c})
        if inst_fns:
            kinds.append("install")
        bound = sorted({f for f, slot in vcalls if c in roots and t and slot < len(t["slots"])})
        if len(bound) >= 2:
            kinds.append("vcall")
        reg[c] = {"class": c, "table": t["table"] if t else None, "slots": t["slots"] if t else [], "installs": inst_fns, "vcall_fns": bound,
                  "kinds": kinds, "grade": grade(kinds), "base": edges.get(c)}
    return reg


def propagate(reg):
    """Prototype propagation. Each slot gets {index, symbol, proto, origin class, override:bool}; an override keeps its base slot index."""
    out = {}
    for c, r in reg.items():
        rows = []
        base = reg.get(r["base"]) if r["base"] else None
        for k, sym in enumerate(r["slots"]):
            dm = demangle(sym) or {}
            bsym = base["slots"][k] if base and k < len(base["slots"]) else None
            rows.append({"index": k, "symbol": sym, "method": dm.get("name"), "kind": dm.get("kind"), "owner": dm.get("cls"), "params": dm.get("params"),
                         "const": dm.get("const"), "override": bool(bsym and bsym != sym), "base_symbol": bsym})
        out[c] = rows
    return out


def root_methods(reg):
    """slot index -> (method name, params, const) for the ROOT class: what a vcall through a base pointer calls."""
    pr = propagate(reg)
    for c, r in reg.items():
        if r["base"] is None and r["slots"]:
            return {x["index"]: (x["method"], x["params"], x["const"]) for x in pr[c] if x["kind"] == "method"}
    return {}


def field_accesses(rows):
    """This-call field recovery for frame-based code: the stack slot that receives r3 at entry holds `this`; a register reloaded from it is `this`;
    loads/stores through it give (offset, op). -> sorted [(offset, op)]"""
    this_slot = None
    for r in rows[:10]:
        m = re.match(r"r3,(\d+)\(r31\)$", r[1])
        if r[0] == "stw" and m:
            this_slot = m.group(1)
            break
    if this_slot is None:
        return []
    out, regs = set(), set()
    for r in rows:
        m = re.match(r"(r\d+),%s\(r31\)$" % this_slot, r[1])
        if r[0] == "lwz" and m:
            regs = {m.group(1)}
            continue
        m = re.match(r"(r\d+|f\d+),(\d+)\((r\d+)\)$", r[1])
        if m and m.group(3) in regs and r[0] in ("lwz", "stw", "lfs", "stfs", "lha", "sth", "lbz", "stb"):
            out.add((int(m.group(2)), r[0]))
    return sorted(out)
