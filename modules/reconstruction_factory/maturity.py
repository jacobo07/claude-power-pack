"""Maturity contract as code. Dimensions are graded 0..10 by EXECUTABLE predicates only (files, gates present in the suite, import edges between modules, greps of
code, JSON facts) - never from prose. A dimension's grade is the highest anchor whose predicate holds AND every lower anchor holds (a chain: no skipping);
overall = the minimum. The rubric is hashed into vault/programs/reconstruction-factory/maturity.contract.json; verify_contract is red when the rubric changed
after the freeze. The rubric is never edited to pass. Anchor 10 of every dimension is Owner acceptance (a file only the Owner's release writes).
Predicates: ("file",p) ("gate",id) ("imports",a,b) ("reach",mod) ("grep",p,regex) ("json",p,dotted,op,val)"""
import ast
import glob
import hashlib
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PKG = os.path.join(ROOT, "modules", "reconstruction_factory")
SUITE = "tools/test_reconstruction_factory.py"
CONTRACT_PATH = os.path.join(ROOT, "vault", "programs", "reconstruction-factory", "maturity.contract.json")
ACCEPT = "vault/programs/reconstruction-factory/OWNER_ACCEPTANCE.json"
ENTRIES = ("core", "certify", "search", "search_plan", "permute", "build_twin")
M = "modules/reconstruction_factory/"

RUBRIC = {
    "D01_certification": [(2, ("file", M + "certify.py"), "certifier exists"), (4, ("gate", "V-RF-CERT-POSITIVE"), "positive controls certify"),
                          (6, ("gate", "V-RF-CERT-NEGATIVE"), "mutants are refused"), (8, ("gate", "V-RF-HELDOUT"), "held-out law enforced"), (10, ("file", ACCEPT), "Owner acceptance")],
    "D02_search": [(2, ("file", M + "search.py"), "search exists"), (4, ("gate", "V-RF-SEARCH"), "search solves"), (6, ("gate", "V-RF-SEARCH-BUDGET"), "budget honoured"),
                   (8, ("gate", "V-RF-PLAN"), "plan chooses families by class"), (10, ("file", ACCEPT), "Owner acceptance")],
    "D03_object_model": [(2, ("file", M + "om.py"), "object model exists"), (4, ("gate", "V-RF-OM-REGISTRY"), "registry graded"), (6, ("gate", "V-RF-OM-PROPAGATE"), "prototypes propagate"),
                         (8, ("gate", "V-RF-OM-VCALL"), "virtual-call pipeline end to end"), (10, ("file", ACCEPT), "Owner acceptance")],
    "D04_claims": [(2, ("file", M + "claims.py"), "claim store exists"), (4, ("gate", "V-RF-ATOMS"), "typed predicates"), (6, ("gate", "V-RF-CLAIMS"), "claims keyed semantically"),
                   (8, ("gate", "V-RF-INVALIDATION"), "invalidation sound against the compiler"), (10, ("file", ACCEPT), "Owner acceptance")],
    "D05_negative_knowledge": [(2, ("file", M + "nsm.py"), "negative memory exists"), (5, ("gate", "V-RF-NSM"), "sound refutations only"), (7, ("grep", M + "search.py", r"nsm\.known_not_found"), "search consults it"),
                               (10, ("file", ACCEPT), "Owner acceptance")],
    "D06_method_selection": [(2, ("file", M + "method_graph.py"), "method graph exists"), (4, ("gate", "V-RF-METHOD-GRAPH"), "macros expand"), (6, ("gate", "V-RF-GENOME"), "strategy genome mutates within bounds"),
                             (8, ("grep", M + "search_plan.py", r"prior"), "plan weights families by the learned prior"), (10, ("file", ACCEPT), "Owner acceptance")],
    "D07_toolchain_honesty": [(3, ("file", M + "build_twin.py"), "build twin exists"), (5, ("gate", "V-RF-BUILD-TWIN"), "toolchain alternatives discriminated"),
                              (7, ("grep", M + "certify.py", r"UNDERDETERMINED_TOOLCHAIN"), "under-determined toolchain is a verdict, not a pass"), (10, ("file", ACCEPT), "Owner acceptance")],
    "D08_heldout_integrity": [(3, ("file", M + "heldout.py"), "release gate exists"), (6, ("gate", "V-RF-HELDOUT-RELEASE"), "seal, leak scan, one-way release proven"),
                              (8, ("imports", "heldout", "certify"), "the only door to a held-out certificate"), (10, ("file", ACCEPT), "Owner acceptance")],
    "D09_transfer": [(3, ("file", M + "cbr.py"), "birth/return records exist"), (6, ("gate", "V-RF-CBR"), "one disposition per discovered input"), (10, ("file", ACCEPT), "Owner acceptance")],
    "D10_public_safety": [(3, ("file", "tools/recon_public_gate.py"), "public gate exists"), (6, ("file", "tools/test_recon_public_gate.py"), "public gate has a drilled test"),
                          (8, ("gate", "V-RF-MATURITY"), "the maturity contract itself is verified"), (10, ("file", ACCEPT), "Owner acceptance")],
}


def _p(path):
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def import_graph(pkg=PKG):
    g = {}
    for f in glob.glob(os.path.join(pkg, "*.py")):
        deps = set()
        with open(f, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom):
                if n.level >= 1 and not n.module:
                    deps |= {a.name for a in n.names}
                elif n.level >= 1:
                    deps.add(n.module.split(".")[0])
                elif n.module == "modules.reconstruction_factory":
                    deps |= {a.name for a in n.names}
                elif n.module and n.module.startswith("modules.reconstruction_factory."):
                    deps.add(n.module.split(".")[2])
        g[os.path.basename(f)[:-3]] = deps
    return g


def reachable(mod, graph=None, entries=ENTRIES):
    graph = graph or import_graph()
    seen, todo = set(), [e for e in entries if e in graph and e != mod]
    seen.update(todo)
    while todo:
        for d in graph.get(todo.pop(), ()):
            if d in graph and d not in seen:
                seen.add(d)
                todo.append(d)
    return mod in seen or mod in entries


def holds(p, graph=None):
    k = p[0]
    try:
        if k == "file":
            return os.path.isfile(_p(p[1])) and os.path.getsize(_p(p[1])) > 0
        if k == "gate":
            with open(_p(SUITE), encoding="utf-8") as fh:
                return re.search(r'@kit\.gate\("%s"' % re.escape(p[1]), fh.read()) is not None
        if k == "imports":
            return p[2] in (graph or import_graph()).get(p[1], ())
        if k == "reach":
            return reachable(p[1], graph)
        if k == "grep":
            with open(_p(p[1]), encoding="utf-8") as fh:
                return re.search(p[2], fh.read()) is not None
        if k == "json":
            with open(_p(p[1]), encoding="utf-8") as fh:
                d = json.load(fh)
            for part in p[2].split("."):
                d = d[part]
            return (d == p[4]) if p[3] == "==" else (d >= p[4])
    except (OSError, KeyError, TypeError, ValueError):
        return False
    raise ValueError("unknown predicate " + k)


def grade(anchors, graph=None, check=holds):
    g = 0
    for gr, pred, _ in sorted(anchors, key=lambda a: a[0]):
        if not check(pred, graph):
            break
        g = gr
    return g


def vector(rubric=RUBRIC, check=holds):
    graph = import_graph()
    v = {d: grade(a, graph, check) for d, a in rubric.items()}
    low = min(v.values())
    return {"dimensions": v, "overall": low, "bottleneck": sorted(d for d in v if v[d] == low)}


def contract_hash(rubric=RUBRIC):
    return hashlib.sha256(json.dumps({d: [[g, list(p), t] for g, p, t in a] for d, a in sorted(rubric.items())}, sort_keys=True).encode()).hexdigest()


def verify_contract(rubric=RUBRIC, path=CONTRACT_PATH):
    try:
        with open(path) as fh:
            return json.load(fh)["rubric_sha256"] == contract_hash(rubric)
    except (OSError, KeyError, ValueError):
        return False


def write_contract(path=CONTRACT_PATH):
    if os.path.exists(path):
        raise FileExistsError("contract already frozen")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump({"version": "maturity1", "rubric_sha256": contract_hash(), "dimensions": len(RUBRIC), "rule": "the rubric is never edited to pass"}, fh, indent=1, sort_keys=True)


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "vector"
    if cmd == "freeze":
        write_contract()
    print(json.dumps(vector(), indent=1) if cmd != "verify" else "contract %s" % verify_contract())
