"""D1d fixture: a function outside every partition must not KeyError. Runs the gid block of factor.py.orig (must FAIL = RED)
and factor.py (must PASS = GREEN) on a 3-function synthetic corpus where fn 'c' is an outsider.
    python3 -I test_factor_partition.py [--expect-red-only]   exit 0 iff orig raises KeyError and patched passes"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))

def block(path):
    L = open(path).read().split("\n")
    s = next(i for i, l in enumerate(L) if l.startswith("    def gid("))
    e = next(i for i, l in enumerate(L) if l.startswith("    sg, dg, dag, ig = gid("))
    e += 1
    while e < len(L) and (L[e].startswith("        ") or L[e].startswith("    for fn in names")):
        e += 1
    return "\n".join(l[4:] for l in L[s:e])

def run(path):
    names = ["a", "b", "c"]
    struct_groups = [["a", "b"], ["c"]]
    data_groups = [["a", "b"]]          # c has < DATA_MIN accesses: outside every partition
    data_groups_anch = [["a", "b"]]
    idiom_groups = [["a", "b"]]         # c: zero idiom hits
    ns = dict(names=names, struct_groups=struct_groups, data_groups=data_groups, data_groups_anch=data_groups_anch, idiom_groups=idiom_groups)
    exec(block(path), ns)
    return [m[fn] for fn in names for m in (ns["sg"], ns["dg"], ns["dag"], ns["ig"])]

def attempt(path):
    try:
        v = run(path)
        return "PASS", v
    except KeyError as e:
        return "KEYERROR", repr(e)

if __name__ == "__main__":
    ro, ev_o = attempt(os.path.join(HERE, "factor.py.orig"))
    gr, ev_p = attempt(os.path.join(HERE, "factor.py"))
    print("RED   factor.py.orig:", ro, ev_o)
    print("GREEN factor.py     :", gr, ev_p)
    sys.exit(0 if ro == "KEYERROR" and gr == "PASS" and ev_p[8:12] == [None] * 4 else 1)
