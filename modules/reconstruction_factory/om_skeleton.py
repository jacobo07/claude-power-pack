"""Skeletons generated FROM Object Model facts (not from the reference source).
  class_decls(reg)          C++ declarations of the recovered hierarchy: virtual methods in SLOT order with decoded prototypes, base classes from
                            ctor edges. Members are not invented: layout beyond the vptr is `field_accesses` evidence only.
  method_to_vslot(text,reg) the lift's raw form: a virtual call `p->m(a)` as an explicit slot call through the vptr.
  vslot_to_method(text,reg) the OM-driven operator that turns the raw slot call back into a method call (a search operator with OM context).
Return types are not in the mangling: they are taken as s32 unless the caller supplies one (a stated limitation, see PARITY.md)."""
import re

from . import om as OM

SLOT_RE = re.compile(r"\(\((\w+) \(\*\)\(((?:const )?)(\w+)\*(?:, ([^)]*))?\)\)\(\*\(void \*\*\*\)(\w+(?:\[\w+\])?)\)\[(\d+)\]\)\(\5(?:, ([^)]*))?\)")


def _ptype(p):
    return p


def class_decls(reg):
    out = ["/* generated from Object Model facts */"]
    pr = OM.propagate(reg)
    order = sorted(reg, key=lambda c: (reg[c]["base"] is not None, c))
    for c in order:
        r = reg[c]
        base = " : %s" % r["base"] if r["base"] else ""
        out.append("struct %s%s {" % (c, base))
        if r["grade"] != "VTABLE":
            out.append("    /* CANDIDATE: not promoted, no declarations emitted */")
        else:
            for x in pr[c]:
                if x["kind"] == "method" and (x["owner"] == c):
                    ps = ", ".join(x["params"] or [])
                    out.append("    virtual s32 %s(%s)%s;" % (x["method"], ps, " const" if x["const"] else ""))
                elif x["kind"] == "dtor" and x["owner"] == c and x["method"] == "D1":
                    out.append("    virtual ~%s();" % c)
        out.append("};")
    return "\n".join(out) + "\n"


def method_to_vslot(text, reg):
    rm = OM.root_methods(reg)
    root = next((c for c, r in reg.items() if r["base"] is None and r["slots"]), None)
    names = {m[0]: (k, m) for k, m in rm.items()}
    out = []
    for m in re.finditer(r"(\w+(?:\[\w+\])?)->(\w+)\(([^()]*)\)", text):
        if m.group(2) not in names:
            continue
        slot, (_n, params, const) = names[m.group(2)]
        x, args = m.group(1), m.group(3).strip()
        sig = ", ".join([("const " if const else "") + root + "*"] + list(params or []))
        call = "((s32 (*)(%s))(*(void ***)%s)[%d])(%s%s)" % (sig, x, slot, x, (", " + args) if args else "")
        out.append(text[:m.start()] + call + text[m.end():])
    return out


def vslot_to_method(text, reg):
    rm = OM.root_methods(reg)
    out = []
    for m in SLOT_RE.finditer(text):
        slot = int(m.group(6))
        if slot not in rm:
            continue
        args = m.group(7) or ""
        out.append(text[:m.start()] + "%s->%s(%s)" % (m.group(5), rm[slot][0], args) + text[m.end():])
    return out
