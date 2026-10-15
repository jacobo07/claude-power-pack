#!/usr/bin/env python3
"""D7 dirty closure. fact id -> dependent functions; header delta -> direct closure (static) ; transitive by D4-style
rule is applied at run time in d7.py (a dependent whose emitted signature changes dirties its callers).
Inputs only: d1d/facts.jsonl, d1d/m2c/ctx_run1 (records+c), d3/residuals.jsonl, d1d/blockers.json, asm text. Deterministic."""
import json, os, re, sys, collections
M = "/home/kobii/missions/tennis-w11"
D28 = M + "/out/d28"
KW = set("""void s8 s16 s32 s64 u8 u16 u32 u64 f32 f64 char short int long float double signed unsigned struct typedef
const static extern enum union if else return sizeof""".split())
ID = re.compile(r'[A-Za-z_]\w*')
TYPEDEF_LINE = re.compile(r'\b(struct|typedef|union|enum)\b|^\s*[\w\s\*]+;\s*(/\*.*)?$')


def load():
    C = {}
    C["facts"] = {}
    for l in open(D28 + "/d1d/facts.jsonl"):
        r = json.loads(l); C["facts"][r["fn"]] = r
    C["res"] = {}
    for l in open(D28 + "/d3/residuals.jsonl"):
        r = json.loads(l); C["res"][r["fn"]] = r
    C["base"] = {}
    for l in open(D28 + "/d1d/m2c/ctx_run1/records.jsonl"):
        r = json.loads(l); C["base"][r["fn"]] = r
    C["basec"] = {}
    for fn in C["base"]:
        p = D28 + "/d1d/m2c/ctx_run1/c/%s.c" % fn
        C["basec"][fn] = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
    C["keyfns"] = {b["key"]: set(b["functions"]) for b in json.load(open(D28 + "/d1d/blockers.json"))["blockers"]}
    C["hctx"] = open(D28 + "/d1d/ctx/tennis_context.h", encoding="utf-8").read()
    return C


def delta_ids(old, new):
    """identifiers in header lines that differ (multiset diff of lines), minus keywords/primitive types."""
    a, b = collections.Counter(old.split("\n")), collections.Counter(new.split("\n"))
    ch = [l for l in list((a - b).elements()) + list((b - a).elements())]
    ids = set()
    typedelta = False
    for l in ch:
        l2 = re.sub(r'/\*.*?\*/', '', l)
        ids |= {t for t in ID.findall(l2) if t not in KW and not re.fullmatch(r'arg\d+|a\d+|var_\w+', t)}
        if re.search(r'\b(struct|typedef|union|enum)\b', l2):
            typedelta = True
    return sorted(ids), typedelta, ch


def header_decl_ids(hctx, ids):
    """Header-level closure: any header line mentioning a changed id contributes the ids of its enclosing top-level decl
    names (struct/typedef tags, function names) -> those become changed too (fixpoint). Over-approximation, sound."""
    lines = hctx.split("\n")
    cur = set(ids)
    # group lines into top-level blocks by blank-line/typedef boundaries
    blocks, b = [], []
    depth = 0
    for l in lines:
        b.append(l)
        depth += l.count("{") - l.count("}")
        if depth <= 0 and l.rstrip().endswith(";"):
            blocks.append(b); b = []; depth = 0
    if b: blocks.append(b)
    changed = True
    while changed:
        changed = False
        for blk in blocks:
            txt = re.sub(r'/\*.*?\*/', '', "\n".join(blk), flags=re.S)
            t = {x for x in ID.findall(txt) if x not in KW}
            if t & cur:
                # declared names of this block: struct/typedef tags + trailing name + first name before '('
                decl = set(re.findall(r'struct\s+(\w+)', txt)) | set(re.findall(r'}\s*(\w+)\s*;', txt)) | set(re.findall(r'(\w+)\s*\(', txt.split("{")[0]))
                decl = {x for x in decl if x not in KW}
                if not decl <= cur:
                    cur |= decl; changed = True
    return sorted(cur)


def rev_index(C):
    rev = collections.defaultdict(set)
    for fn, f in C["facts"].items():
        for g in f["callees"] + f["tailcalls"]:
            rev[g].add(fn)
        for g in f["callers"]:
            rev[fn].add(g)   # fn's callers depend on fn's prototype
    return rev


def dependents(C, ids, typedelta, asm_text, rev=None):
    """fact id -> set(functions). asm_text: {fn: block}."""
    rev = rev or rev_index(C)
    out = {}
    for i in ids:
        pat = re.compile(r'(?<![\w])%s(?![\w])' % re.escape(i))
        s = set()
        if i in C["facts"]:
            s.add(i)
        s |= rev.get(i, set())
        s |= {fn for fn, f in C["facts"].items() if i in f["globals"]}
        s |= C["keyfns"].get("HELPER:" + i, set())
        for k, v in C["keyfns"].items():
            if k.endswith(":" + i):
                s |= v
        s |= {fn for fn, r in C["res"].items() if any(pat.search(str(u["id"])) for u in r["unresolved_vars"])}
        s |= {fn for fn, t in asm_text.items() if pat.search(t)}
        s |= {fn for fn, t in C["basec"].items() if pat.search(t)}
        out[i] = s
    if typedelta:   # a type fact can also type fields/types m2c left unknown (UNK_FIELD / UNRESOLVED_TYPE / FIELD_UNTYPED)
        s = {fn for fn, r in C["base"].items() if set(r.get("lint_codes", [])) & {"UNK_FIELD", "UNRESOLVED_TYPE"}}
        s |= {fn for fn, r in C["res"].items() if any(u["type"].startswith(("field", "type")) or "FIELD" in str(u["id"]) for u in r["unresolved_vars"])}
        out["<type-delta:untyped-field-holders>"] = s
    return out


def closure(C, old, new, asm_text):
    ids, typedelta, ch = delta_ids(old, new)
    ids2 = header_decl_ids(new, ids) if typedelta else ids
    deps = dependents(C, ids2, typedelta, asm_text)
    allf = set()
    for v in deps.values():
        allf |= v
    return sorted(allf & set(C["base"])), dict(ids=ids2, typedelta=typedelta, changed_lines=len(ch), per_fact={k: len(v) for k, v in deps.items()})