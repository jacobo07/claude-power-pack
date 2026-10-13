"""Idiom table v0 (WU-P1P2). Each detector: list[Insn] -> list of hits, each the list of insn indices it covers. Structural patterns only.

switch_jump_table  : bctr with an lwzx in the 4 instructions before it
bool_from_compare  : cntlzw rA,.. followed within 2 instructions by srwi rB, rA, 5
float_to_int       : fctiwz fX,..; stfd fX, o(r1); lwz rY, o+4(r1) (window 4)
struct_copy        : inside a run of only lwz/stw, >= 4 stores at consecutive offsets (step 4) on one destination base,
                     each storing a register loaded inside the run from one source base
vtable_call        : lwz rX, 0(rB); lwz rY, N(rX); mtctr rY; bctrl  (in order, window 8)
ptmf_call          : a non-load write of r12 followed by a call (bl/bctrl) within 4 instructions, no mtctr r12 between
                     (MWCC passes the member pointer in r12 to the __ptmf_scall-style helper)
stack_guard_prolog : stwu r1, -N(r1) and mflr r0 among the first 3 instructions
"""
import re

from asmlib import GPR, MEM, mem_op, parse_num, writes

NAMES = ["switch_jump_table", "bool_from_compare", "float_to_int", "struct_copy", "vtable_call", "ptmf_call",
         "stack_guard_prolog"]


def switch_jump_table(ins):
    out = []
    for k, i in enumerate(ins):
        if i.m == "bctr":
            js = [j for j in range(max(0, k - 4), k) if ins[j].m == "lwzx"]
            if js:
                out.append(list(range(js[-1], k + 1)))
    return out


def bool_from_compare(ins):
    n = []
    for k, i in enumerate(ins):
        if i.m.rstrip(".") == "cntlzw" and i.ops:
            for j in ins[k + 1:k + 3]:
                if j.m.rstrip(".") == "srwi" and len(j.ops) == 3 and j.ops[1] == i.ops[0] and parse_num(j.ops[2]) == 5:
                    n.append([k, ins.index(j, k)])
                    break
    return n


def float_to_int(ins):
    n = []
    for k, i in enumerate(ins):
        if i.m.rstrip(".") != "fctiwz" or not i.ops:
            continue
        fx, st = i.ops[0], None
        for jj, j in enumerate(ins[k + 1:k + 5], k + 1):
            if j.m == "stfd" and j.ops[0] == fx:
                mm = MEM.match(j.ops[1])
                if mm and mm.group(2) == "r1":
                    st = parse_num(mm.group(1))
                continue
            if st is not None and j.m == "lwz":
                mm = MEM.match(j.ops[1])
                if mm and mm.group(2) == "r1" and parse_num(mm.group(1)) == st + 4:
                    n.append(list(range(k, jj + 1)))
                    break
    return n


def struct_copy(ins):
    n, k = [], 0
    while k < len(ins):
        if ins[k].m not in ("lwz", "stw"):
            k += 1
            continue
        e = k
        while e < len(ins) and ins[e].m in ("lwz", "stw"):
            e += 1
        loaded, dest, idx = {}, {}, {}
        for q in range(k, e):
            i = ins[q]
            mo = mem_op(i)
            if not mo or mo[2] is None:
                continue
            if i.m == "lwz":
                loaded[i.ops[0]] = (mo[3], q)
            elif i.ops[0] in loaded:
                key = (loaded[i.ops[0]][0], mo[3])
                dest.setdefault(key, set()).add(mo[2])
                idx.setdefault(key, set()).update((q, loaded[i.ops[0]][1]))
        for key, offs in dest.items():
            s = sorted(offs)
            best = run = 1
            for a, b in zip(s, s[1:]):
                run = run + 1 if b - a == 4 else 1
                best = max(best, run)
            if best >= 4:
                n.append(sorted(idx[key]))
        k = e
    return n


def vtable_call(ins):
    n = []
    for k, i in enumerate(ins):
        if i.m != "bctrl":
            continue
        win = ins[max(0, k - 8):k]
        ctr = next((j for j in reversed(win) if j.m == "mtctr"), None)
        if ctr is None:
            continue
        ry = ctr.ops[0]
        ld2 = next((j for j in reversed(win) if j.m == "lwz" and j.ops[0] == ry and MEM.match(j.ops[1])), None)
        if ld2 is None:
            continue
        rx = MEM.match(ld2.ops[1]).group(2)
        ld1 = next((j for j in win if j.m == "lwz" and j.ops[0] == rx and MEM.match(j.ops[1])
                    and parse_num(MEM.match(j.ops[1]).group(1)) == 0 and win.index(j) < win.index(ld2)), None)
        if ld1 is not None:
            n.append(sorted({ins.index(ld1, max(0, k - 8)), ins.index(ld2, max(0, k - 8)), ins.index(ctr, max(0, k - 8)), k}))
    return n


def ptmf_call(ins):
    n = []
    for k, i in enumerate(ins):
        if "r12" not in writes(i) or i.m in ("bl", "bctrl", "blrl") or mem_op(i):
            continue
        for jj, j in enumerate(ins[k + 1:k + 5], k + 1):
            if j.m == "mtctr" and j.ops and j.ops[0] == "r12":
                break
            if j.m in ("bl", "bctrl"):
                n.append(list(range(k, jj + 1)))
                break
    return n


def stack_guard_prolog(ins):
    head = ins[:3]
    a = any(i.m == "stwu" and i.ops[0] == "r1" and re.match(r"^-0x[0-9A-Fa-f]+\(r1\)$", i.ops[1]) for i in head)
    b = any(i.m == "mflr" and i.ops == ["r0"] for i in head)
    return [list(range(len(head)))] if a and b else []


DETECT = {k: globals()[k] for k in NAMES}


def spans(ins):
    """{idiom: [[insn index, ...] per hit]} for idioms with >= 1 hit."""
    out = {}
    for k, f in DETECT.items():
        s = f(ins)
        if s:
            out[k] = s
    return out


def hits(ins):
    return {k: len(v) for k, v in spans(ins).items()}
