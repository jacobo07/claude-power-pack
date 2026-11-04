"""Incremental invalidation: a header delta -> the set of functions whose emitted code CAN change. Static, over-approximating (sound): identifiers in
the lines that differ (multiset line diff) are the changed facts; a changed type declaration widens to every declaration that mentions it (fixpoint);
a function is dirty if its source mentions a changed identifier, plus its callers when a signature-bearing fact changed. Ground truth is the
compiler: V-RF-INVALIDATION recompiles with the edited header and requires changed-objects ⊆ closure."""
import difflib
import re

KW = set("""void s8 s16 s32 s64 u8 u16 u32 u64 f32 f64 char short int long float double signed unsigned struct typedef const static extern enum union
if else return sizeof virtual class public private for while do switch case break continue default new delete this""".split())
ID = re.compile(r"[A-Za-z_]\w*")
COMMENT = re.compile(r"/\*.*?\*/|//[^\n]*|^[ \t]*#[ \t]*include[^\n]*", re.S | re.M)


def strip(t):
    return COMMENT.sub("", t)


def blocks(h):
    """-> [(first line, last line, text)] top-level declarations (brace-balanced, ending in ; or })."""
    out, b, depth, start = [], [], 0, 0
    for i, l in enumerate(h.split("\n")):
        if not b:
            start = i
        b.append(l)
        depth += l.count("{") - l.count("}")
        if depth <= 0 and l.rstrip().endswith((";", "}")):
            out.append((start, i, "\n".join(b)))
            b, depth = [], 0
    if b:
        out.append((start, start + len(b) - 1, "\n".join(b)))
    return out


def declared(t):
    t = strip(t)
    d = set(re.findall(r"\b(?:struct|class|enum|union)\s+(\w+)", t)) | set(re.findall(r"}\s*(\w+)\s*;", t))
    d |= set(re.findall(r"typedef\s+[\w\s\*]+?\b(\w+)\s*;", t))
    return d - KW


def delta_ids(old, new):
    """SEQUENCE diff (a pure reorder of lines is a change; a multiset diff cannot see it). -> (ids, typedelta, changed lines).
    The names declared by every block that contains a changed line are included (editing a member changes the type that owns it).
    Identifiers on INTERIOR lines of a brace block that are not type names are MEMBERS: returned as '.name' and matched only as `.name` / `->name`."""
    a, b = old.split("\n"), new.split("\n")
    sides = ((old, a), (new, b))
    types = set()
    for src, _ in sides:
        for (_s0, _s1, txt) in blocks(src):
            types |= declared(txt)
    ids, typedelta, ch = set(), False, []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        for (src, lines), lo, hi in ((sides[0], i1, i2), (sides[1], j1, j2)):
            bl = blocks(src)
            for ln in range(lo, hi):
                text = strip(lines[ln])
                ch.append(lines[ln])
                owner = next((x for x in bl if x[0] <= ln <= x[1]), None)
                interior = owner is not None and "{" in owner[2] and owner[0] < ln < owner[1]
                if owner:
                    ids |= declared(owner[2])
                for t in ID.findall(text):
                    if t not in KW:
                        ids.add(t if (t in types or not interior) else "." + t)
                typedelta |= bool(re.search(r"\b(struct|typedef|union|enum|class)\b", text))
            if hi == lo:                                              # pure deletion on this side: the neighbouring block is the owner
                for x in bl:
                    if x[0] < lo <= x[1]:
                        ids |= declared(x[2])
    return sorted(ids), typedelta or bool(ids), ch


def widen(header, ids):
    cur, bl = {i for i in ids if not i.startswith(".")}, blocks(header)
    mem = {i for i in ids if i.startswith(".")}
    changed = True
    while changed:
        changed = False
        for (_a, _b, blk) in bl:
            if {x for x in ID.findall(strip(blk)) if x not in KW} & cur:
                decl = declared(blk)
                if not decl <= cur:
                    cur |= decl
                    changed = True
    return sorted(cur | mem)


def closure(sources, old, new, callers=None):
    """sources: {fn: text}; callers: {fn: [callers]} (optional). -> (sorted dirty fns, info)"""
    ids, typedelta, ch = delta_ids(old, new)
    ids2 = widen(new, ids) if typedelta else ids
    pats = [re.compile((r"(?:\.|->)\s*%s(?![\w])" % re.escape(i[1:])) if i.startswith(".") else (r"(?<![\w])%s(?![\w])" % re.escape(i))) for i in ids2]
    dirty = {fn for fn, t in sources.items() if any(p.search(strip(t)) for p in pats)}
    if callers:
        for fn in list(dirty):
            dirty |= set(callers.get(fn, []))
    return sorted(dirty), {"ids": ids2, "typedelta": typedelta, "changed_lines": len(ch)}
