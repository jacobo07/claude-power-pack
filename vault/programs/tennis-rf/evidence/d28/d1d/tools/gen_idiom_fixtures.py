"""D1d idiom fixtures: pick REAL Tennis windows (positive = detector hit +-2 ctx; negative = trigger-bearing window with no hit), write idioms_test.txt.
    python3 -I gen_idiom_fixtures.py <d1d_dir>"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import asmlib as A, idioms as I
M = "/home/kobii/missions/tennis-w11"
ASM = M + "/wst_tennis/step0/split_sports/out/asm"
TRIG = {  # trigger predicate for near-miss negatives
 "switch_jump_table": lambda i: i.m == "bctr",
 "bool_from_compare": lambda i: i.m.rstrip(".") in ("cntlzw", "srwi"),
 "float_to_int": lambda i: i.m.rstrip(".") in ("fctiwz", "fctiw"),
 "struct_copy": lambda i: i.m == "stw",
 "vtable_call": lambda i: i.m == "bctrl",
 "ptmf_call": lambda i: i.m in ("bl", "bctrl") ,
 "stack_guard_prolog": lambda i: i.m in ("stwu", "mflr"),
}
def main(d):
    P = A.parse_program(ASM)
    out, meta = [], {}
    for name in I.NAMES:
        det = I.DETECT[name]; pos = neg = None
        for fn in sorted(P.fns):
            ins = P.fns[fn]
            sp = det(ins)
            if sp and pos is None:
                lo, hi = max(0, min(sp[0]) - 2), min(len(ins), max(sp[0]) + 3)
                if name == "stack_guard_prolog": lo, hi = 0, min(len(ins), 6)
                if len(det(ins[lo:hi])) >= 1: pos = (fn, ins[lo:hi])
            if neg is None and (name != "stack_guard_prolog" or len(ins) >= 3):
                if name == "stack_guard_prolog":
                    if not sp and any(TRIG[name](x) for x in ins): 
                        k = next(j for j, x in enumerate(ins) if TRIG[name](x)); w = ins[max(0,k-1):k+5]
                        if not det(w): neg = (fn, w)
                    continue
                for k, x in enumerate(ins):
                    if TRIG[name](x):
                        w = ins[max(0, k - 5):k + 3]
                        if len(w) >= 4 and not det(w) and not any(set(s) & set(range(max(0,k-5), k+3)) for s in sp):
                            neg = (fn, w); break
            if pos and neg: break
        meta[name] = dict(pos=pos[0] if pos else None, neg=neg[0] if neg else None)
        for lab, v in (("POS", pos), ("NEG", neg)):
            if v:
                out.append("### idiom=%s label=%s fn=%s addr=%08X" % (name, lab, v[0], v[1][0].addr))
                out += ["%08X %s" % (x.addr, x.text) for x in v[1]]
    open(os.path.join(d, "idioms_test.txt"), "w").write("\n".join(out) + "\n")
    print(json.dumps(meta, indent=1))
main(sys.argv[1])
