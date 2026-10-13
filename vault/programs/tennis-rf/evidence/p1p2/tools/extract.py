"""WU-P1P2 Pass 1: per-function facts for the 1,797 Tennis functions, from the whole-program asm.

    python3 -I extract.py <asm_dir> <tennis_fns.json> <out_dir>   -> <out_dir>/facts.jsonl (m2c_with_ctx NOT_RUN),
                                                                    <out_dir>/extract_summary.json
Linear register tracking (control-flow-insensitive): field_accesses and helper_sig are structural observations.
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asmlib as A  # noqa: E402
import idioms  # noqa: E402

ARGS = ["r%d" % k for k in range(3, 11)]
FARGS = ["f%d" % k for k in range(1, 9)]
ROLE_RULES = {
    "TAILCALL_THUNK": "size_insns <= 2 AND last insn is `b <symbol>` to a non-local target",
    "LEAF_ACCESSOR": "size_insns <= 4 AND last insn blr AND no other branch/call AND exactly one D-form load/store "
                     "AND its base register is r3",
    "UNREACHABLE": "no bl/b from any of the 18,820 program functions AND 0 `.4byte` words naming it in any data/rodata/"
                   "sdata/sdata2/init object AND 0 @ha/@l/@sda21 code operands naming it AND 0 jump-table words "
                   "naming it from another function's table",
}
NOT_EMITTED = {"CTOR_SHAPE": "no rule proven: the corpus has 0 __ct__ symbols to validate a shape rule against (A1)",
               "DTOR_SHAPE": "no rule proven: the corpus has 0 __dt__ symbols to validate a shape rule against (A1)"}


def depth(o):
    return 1 if o.startswith("*(") else 0


def track(ins):
    """field accesses [origin, off, width, rw, op, use], helper_sig {callee: [[gpr, fpr, ret_r3, ret_f1], ...]},
    access sites [(insn index, origin, off)]."""
    orig = {r: r for r in ARGS}
    acc, pending = [], {}
    sites = collections.defaultdict(set)
    setg, setf = set(), set()
    last_call = None  # (callee, gpr, fpr) waiting for ret-use evidence
    ret = {}
    for k, i in enumerate(ins):
        mo = A.mem_op(i)
        rd = A.reads(i)
        # use evidence for pending loaded values
        for r in list(pending):
            if i.m in A.CALLS and r in ARGS + FARGS:
                acc[pending.pop(r)][5] = "arg"
            elif i.m == "blr" and r in ("r3", "f1"):
                acc[pending.pop(r)][5] = "ret"
            elif mo and mo[3] == r:
                acc[pending.pop(r)][5] = "ptr"
            elif r in rd:
                acc[pending.pop(r)][5] = "val"
        if last_call is not None:
            for r in ("r3", "f1"):
                if r not in ret:
                    if r in rd:
                        ret[r] = 1
            w = A.writes(i)
            for r in ("r3", "f1"):
                if r not in ret and r in w:
                    ret[r] = 0
            if i.m in A.CALLS or A.is_branch(i) or len(ret) == 2:
                c, g, f = last_call
                sites[c].add((g, f, ret.get("r3", 0), ret.get("f1", 0)))
                last_call, ret = None, {}
        w = A.writes(i)
        if i.m == "bl":
            g = max([int(r[1:]) - 2 for r in setg] or [0])
            f = max([int(r[1:]) for r in setf] or [0])
            last_call = (A.target(i), g, f)
            setg, setf = set(), set()
        elif i.m in A.CALLS:
            setg, setf = set(), set()
        else:
            setg |= w & set(ARGS)
            setf |= w & set(FARGS)
        new = None
        if mo:
            kind, wd, off, base, sym = mo
            if sym is not None:
                if kind == "l" and i.m == "lwz":
                    new = "*" + sym
                elif orig.get(base) == "ha:" + sym and kind:
                    acc.append(["&" + sym, 0, wd, "r" if kind == "l" else "w", i.m, None, k])
                    if kind == "l" and i.m == "lwz":
                        new = "*" + sym
            elif base != "r1" and base in orig and off is not None and not orig[base].startswith("ha:"):
                acc.append([orig[base], off, wd, "r" if kind == "l" else "w", i.m, None, k])
                if kind == "l" and i.m in ("lwz", "lwzu") and depth(orig[base]) == 0:
                    new = "*(%s+0x%X)" % (orig[base], off)
                    pending[i.ops[0]] = len(acc) - 1
        elif i.m == "mr" and len(i.ops) == 2:
            new = orig.get(i.ops[1])
        elif i.m == "lis" and len(i.ops) == 2 and i.ops[1].endswith("@ha"):
            new = "ha:" + i.ops[1][:-3].strip('"')
        elif i.m == "addi" and len(i.ops) == 3 and i.ops[2].endswith("@l") and orig.get(i.ops[1]) == "ha:" + i.ops[2][:-2].strip('"'):
            new = "&" + i.ops[2][:-2].strip('"')
        for r in w:
            orig.pop(r, None)
            if r in pending and not (mo and mo[0] == "l" and r == i.ops[0] and pending.get(r) == len(acc) - 1):
                pending.pop(r)
        if new is not None and i.ops:
            orig[i.ops[0]] = new
    if last_call is not None:
        c, g, f = last_call
        sites[c].add((g, f, ret.get("r3", 0), ret.get("f1", 0)))
    at = [(a[6], a[0], a[1]) for a in acc]
    acc = sorted({tuple(a[:5]) + (a[5] or "none",) for a in acc}, key=lambda t: (t[0], t[1], t[3], t[4], t[5]))
    return [list(a) for a in acc], {c: sorted(map(list, v)) for c, v in sorted(sites.items())}, at


def constants(ins, floats):
    ints, fl = set(), set()
    for i in ins:
        if A.is_branch(i) or i.m in A.CALLS:
            continue
        mo = A.mem_op(i)
        if mo:
            if mo[4] in floats and i.m.startswith(("lfs", "lfd", "psq_l")):
                fl.add(floats[mo[4]])
            continue
        for o in i.ops[1:]:
            if A.NUM.match(o):
                v = A.parse_num(o)
                if abs(v) >= 0x100:
                    ints.add(v)
    return sorted(ints), sorted(fl)


def main(argv):
    asm_dir, inv_path, out = argv[1], argv[2], argv[3]
    P = A.parse_program(asm_dir)
    inv = json.load(open(inv_path))
    tennis = [r["fn"] for r in inv]
    callers = collections.defaultdict(set)
    table_owner = collections.defaultdict(set)
    for fn in P.order:
        for i in P.fns[fn]:
            if i.m in ("bl", "b"):
                t = A.target(i)
                if t and t not in P.labels[fn]:
                    callers[t].add(fn)
            for t in A.re.findall(r'\b(jumptable_[0-9A-Fa-f_]+)', i.text):
                table_owner[t].add(fn)
    table_refs = collections.Counter()
    for t, words in P.tables.items():
        for sym, off in words:
            if table_owner[t] - {sym} or not table_owner[t]:
                table_refs[sym] += 1
    rows, size_mismatch = [], []
    for r in inv:
        fn = r["fn"]
        ins = P.fns[fn]
        if len(ins) != r["insns"]:
            size_mismatch.append((fn, len(ins), r["insns"]))
        labels = P.labels[fn]
        callees = sorted({A.target(i) for i in ins if i.m == "bl"})
        tails = sorted({A.target(i) for i in ins if i.m == "b" and A.target(i) not in labels})
        blocks, edges, back = A.cfg(fn, ins, labels, P.tables)
        sizes = [e - s for s, e in blocks]
        acc, hs, _ = track(ins)
        ci, cf = constants(ins, P.floats)
        mems = [A.mem_op(i) for i in ins]
        roles = []
        if len(ins) <= 2 and ins[-1].m == "b" and A.target(ins[-1]) not in labels:
            roles.append("TAILCALL_THUNK")
        nm = [m for m in mems if m]
        if (len(ins) <= 4 and ins[-1].m == "blr" and not any(A.is_branch(i) or i.m in A.CALLS for i in ins[:-1])
                and len(nm) == 1 and nm[0][3] == "r3" and nm[0][2] is not None):
            roles.append("LEAF_ACCESSOR")
        if not callers.get(fn) and P.data_refs[fn] == 0 and P.code_refs[fn] == 0 and table_refs[fn] == 0:
            roles.append("UNREACHABLE")
        rows.append(dict(
            fn=fn, addr="%08X" % ins[0].addr, size_insns=len(ins),
            role=roles[0] if roles else "UNKNOWN", role_all=roles, role_proof={k: ROLE_RULES[k] for k in roles},
            callees=callees, tailcalls=tails, callers=sorted(callers.get(fn, ())),
            ref_counts=dict(data_words=P.data_refs[fn], code_operands=P.code_refs[fn], foreign_jumptable_words=table_refs[fn]),
            cfg_fingerprint=dict(blocks=len(blocks), edges=len(edges), loops=back, block_sizes_sha=A.sha(",".join(map(str, sizes)))),
            field_accesses=acc, globals=sorted(set(A.re.findall(r'\b(lbl_[0-9A-Fa-f_]+)', " ".join(i.text for i in ins)))),
            constants=dict(int=ci, float=cf), helper_sig=hs, idiom_hits=idioms.hits(ins),
            m2c_with_ctx=dict(status="NOT_RUN")))
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "facts.jsonl"), "w") as w:
        for row in rows:
            w.write(json.dumps(row, sort_keys=True) + "\n")
    summ = dict(n_rows=len(rows), program_functions=len(P.fns), size_mismatch=size_mismatch,
                roles=dict(collections.Counter(r["role"] for r in rows)),
                role_all=dict(collections.Counter(x for r in rows for x in r["role_all"])),
                roles_not_emitted=NOT_EMITTED, role_rules=ROLE_RULES,
                idiom_functions={k: sum(1 for r in rows if k in r["idiom_hits"]) for k in idioms.NAMES},
                idiom_hits_total={k: sum(r["idiom_hits"].get(k, 0) for r in rows) for k in idioms.NAMES},
                idiom_program_functions={k: sum(1 for f in P.order if idioms.DETECT[k](P.fns[f])) for k in idioms.NAMES})
    json.dump(summ, open(os.path.join(out, "extract_summary.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in summ.items() if k not in ("role_rules", "roles_not_emitted")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
