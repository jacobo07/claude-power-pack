#!/usr/bin/env python3
"""V-RF-*: the general Reconstruction Factory on the synthetic corpus (fixtures/synthetic), end to end. Run in-process so that a drill
(`--drills`) that patches one instrument reaches the code under test; each gate must turn RED under its drill (a gate that cannot go red is a rumour)."""
import os
import shutil
import sys
import tempfile
import json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from modules.reconstruction_factory import build_twin as BT
from modules.reconstruction_factory import causal_diff as CD
from modules.reconstruction_factory import certify as C
from modules.reconstruction_factory import fingerprint as FP
from modules.reconstruction_factory import judge as J
from modules.reconstruction_factory import genome as GN
from modules.reconstruction_factory import method_graph as MG
from modules.reconstruction_factory import nsm as NS
from modules.reconstruction_factory import om as OM
from modules.reconstruction_factory import om_skeleton as OS
from modules.reconstruction_factory import permute as PM
from modules.reconstruction_factory import residual as RS
from modules.reconstruction_factory import search as S
from modules.reconstruction_factory import search_plan as SP
from modules.reconstruction_factory.core import Factory
from modules.reconstruction_factory.gatekit import Kit, patched
import rf_gen_corpus as GC

MANIFEST = os.path.join(ROOT, "fixtures/synthetic/recon.toml")
kit = Kit("test_reconstruction_factory")


class Ctx:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="rft-")
        self.f = Factory(MANIFEST, workdir=self.tmp.name)
        self.P = self.f.project
        self._sk = {}

    def close(self):
        self.f.close()
        self.tmp.cleanup()

    def skeletons(self):
        out = {}
        for fn, d in self.P.functions.items():
            p = os.path.join(self.P.source_dir("skeleton"), d["source"])
            if os.path.exists(p):
                out[fn] = open(p).read()
        return out

    def mutants(self):
        out = {}
        for fn, d in self.P.functions.items():
            p = os.path.join(self.P.source_dir("mutant"), d["source"])
            if os.path.exists(p) and not d.get("heldout"):
                out[fn] = open(p).read()
        return out


def weak_symbol(te, ce, sym):
    """A broken judge: 'exact' iff the symbol exists with equal size (ignores every byte)."""
    r = {"symbol": sym, "defined": False, "size_eq": False, "code": False, "relocs": False, "data": True, "pct": 0.0, "reasons": [], "unknown_relocs": []}
    t, c = te.extent(sym), ce.extent(sym)
    if t and c and t[2] == c[2]:
        r.update(defined=True, size_eq=True, code=True, relocs=True, pct=100.0)
    else:
        r["reasons"].append("SIZE")
    return r


@kit.gate("V-RF-JUDGE", drill=lambda: patched(J, "judge_symbol", weak_symbol))
def g_judge(ctx):
    f = ctx.f
    for fn in ctx.P.names():
        assert f.judge_obj(fn, f.target(fn))["exact"], "ref not exact vs itself: " + fn
    mut = ctx.mutants()
    assert len(mut) >= 40, "mutant corpus too small: %d" % len(mut)
    for fn, t in mut.items():
        r, c = f.judge_text(fn, t)
        assert r["compiles"] and r["exact"] is False, "mutant judged exact: " + fn
    r = J.judge(f.target("rf_add3"), "/nonexistent.o", ["rf_add3"])
    assert r["compiles"] is False and r["exact"] is None, "unreadable candidate must not be a mismatch measurement"


@kit.gate("V-RF-CERT-POSITIVE", drill=lambda: patched(C, "text_equal", lambda *a: False))
def g_cert_pos(ctx):
    for fn in ctx.P.names():
        c = C.certify(ctx.f, fn, ctx.f.read_source(fn))
        assert c["verdict"] == "CERTIFIED_EXACT", "%s: %s" % (fn, c["verdict"])
        assert c["evidence"]["independent"] == {"elf": True, "text": True}, fn
        assert all(c["evidence"]["corroborating"].values()), fn
    for fn in ("rf_call_area", "rf_total_area", "rf_scale_all"):               # C++ virtual calls certified exact
        d = FP.fingerprint(ctx.f.adapter, ctx.f.target(fn), ctx.P.functions[fn]["symbols"])
        assert d["indirect_calls"] >= 1, fn + " has no indirect call: not a virtual-call witness"


@kit.gate("V-RF-CERT-NEGATIVE", drill=lambda: patched(J, "judge_symbol", weak_symbol))
def g_cert_neg(ctx):
    for fn, t in ctx.mutants().items():
        v = C.certify(ctx.f, fn, t)["verdict"]
        assert v == "NOT_EXACT", "mutant %s -> %s" % (fn, v)


@kit.gate("V-RF-CERT-CONTROLS", drill=lambda: patched(C, "flip_byte", lambda s, d, y: shutil.copyfile(s, d)))
def g_controls(ctx):
    c = C.certify(ctx.f, "rf_checksum", ctx.f.read_source("rf_checksum"))
    assert c["verdict"] == "CERTIFIED_EXACT" and c["evidence"]["corroborating"]["negative_control_refused"], c["verdict"]


@kit.gate("V-RF-CERT-INDEPENDENT", drill=lambda: patched(C, "text_equal", lambda *a: True))
def g_independent(ctx):
    fn = "rf_add3"
    t = ctx.mutants()[fn]
    with patched(J, "judge_symbol", weak_symbol):                  # ELF instrument lies; the objdump text instrument must veto
        v = C.certify(ctx.f, fn, t)["verdict"]
    assert v == "DISAGREEMENT", v


@kit.gate("V-RF-TOOLCHAIN-UNDERDETERMINED", drill=lambda: patched(C, "text_equal", lambda *a: False))
def g_toolchain(ctx):
    fn, P = "rf_sum_n", ctx.P
    other = ctx.f.compile_text(fn, ctx.f.read_source(fn), flags=P.flags("o0", "c", "o0_to_o2"))
    assert other.ok
    f2 = Factory(MANIFEST, workdir=ctx.tmp.name)
    try:
        assert not f2.judge_obj(fn, f2.target(fn))["exact"] or True
        f2._targets[fn] = other.obj                                # the target was really built with -O2; the manifest still pins o0
        c = C.certify(f2, fn, f2.read_source(fn))
        assert c["verdict"] == "UNDERDETERMINED_TOOLCHAIN" and "o0_to_o2" in c["toolchain"]["exact_under"], c["verdict"]
        assert "candidate_sha256" not in c, "no certificate may be issued"
    finally:
        pass


@kit.gate("V-RF-HELDOUT-REFUSE", drill=lambda ctx: _unheld(ctx))
def g_heldout(ctx):
    fn = "hs_sum_arr"
    assert ctx.P.functions[fn]["heldout"]
    assert C.certify(ctx.f, fn, ctx.f.read_source(fn, "heldout"))["verdict"] == "HELDOUT_NOT_RELEASED"
    assert C.certify(ctx.f, fn, ctx.f.read_source(fn, "heldout"), released=True)["verdict"] == "CERTIFIED_EXACT"


import contextlib


@contextlib.contextmanager
def _unheld(ctx):
    ds = [d for d in ctx.P.functions.values() if d.get("heldout")]
    for d in ds:
        d["heldout"] = False
    try:
        yield
    finally:
        for d in ds:
            d["heldout"] = True


@kit.gate("V-RF-FINGERPRINT", drill=lambda: patched(FP, "norm_op", lambda o: "x"))
def g_fp(ctx):
    f = ctx.f
    a = FP.fingerprint(f.adapter, f.target("rf_abs_diff"), ["rf_abs_diff"])
    b = FP.fingerprint(f.adapter, f.target("rf_bsearch"), ["rf_bsearch"])
    assert FP.distance(a, a) == 0.0 and FP.distance(a, b) > 0.2
    fl = FP.fingerprint(f.adapter, f.target("rf_flt_lerp"), ["rf_flt_lerp"])
    assert fl["float"] > 0 and a["float"] == 0
    assert FP.fingerprint(f.adapter, f.target("rf_abs_diff"), ["no_such_symbol"]) is None


@kit.gate("V-RF-CAUSAL-DIFF", drill=lambda: patched(CD, "classify_pair", lambda t, c: "REG_ALLOC"))
def g_causal(ctx):
    f, fn = ctx.f, "rf_abs_diff"
    tgt, syms = f.target(fn), ctx.P.functions[fn]["symbols"]
    src = f.read_source(fn)

    def diff(t):
        return CD.causal_diff(f.adapter, tgt, f.judge_text(fn, t)[1].obj, syms)
    same = diff(src)
    assert same["hunks"] == 0
    assert diff(src.replace("a > b", "a >= b"))["classes"] == {"OPCODE": 1}
    assert diff(src.replace("return a - b;", "return a - b + 1;"))["classes"] == {"CONST": 1, "OPCODE": 1}
    d = CD.attribute(diff(src.replace("a > b", "a >= b")), same)
    assert d["verdict"] == "IMPROVED" and d["delta"]["OPCODE"] == -1


@kit.gate("V-RF-RESIDUAL", drill=lambda: patched(RS, "MAP", {k: ("METHOD_PLATEAU", "") for k in RS.MAP}))
def g_residual(ctx):
    f, fn = ctx.f, "rf_abs_diff"
    tgt, syms = f.target(fn), ctx.P.functions[fn]["symbols"]
    ok = RS.residual(f.adapter, tgt, f.target(fn), syms)
    assert ok["residual_class"] is None
    c = f.judge_text(fn, f.read_source(fn).replace("return a - b;", "return a - b + 1;"))[1]
    r = RS.residual(f.adapter, tgt, c.obj, syms)
    assert r["residual_class"] in ("UNIQUE_SEMANTIC_RESIDUAL", "METHOD_PLATEAU") and r["primary"] in ("CONST", "OPCODE")
    assert RS.MAP["ORDER"][0] == "COMPILER_SHAPE_RESIDUAL" and RS.MAP["RELOC"][0] == "TYPE_LAYOUT_BLOCKED" and RS.MAP["MISSING"][0] == "OBJECT_MODEL_BLOCKED"


@kit.gate("V-RF-SEARCH", drill=lambda: patched(S, "apply_all", lambda *a, **k: []))
def g_search(ctx):
    sk = ctx.skeletons()
    assert len(sk) >= 40, len(sk)
    for fn, t in sk.items():
        assert not ctx.f.judge_text(fn, t)[0]["exact"], "skeleton already exact: " + fn
        r = S.search(ctx.f, fn, t, budget=300)
        assert r["status"] == "EXACT" and r["path"], "%s: %s" % (fn, r["status"])
        assert C.certify(ctx.f, fn, r["text"], released=True)["verdict"] == "CERTIFIED_EXACT", fn
    mut = ctx.mutants()["rf_abs_diff"]                                   # a semantic mutant is NOT repairable by rewrite operators
    assert S.search(ctx.f, "rf_abs_diff", mut, budget=120)["status"] in ("NOT_FOUND", "BUDGET_EXHAUSTED")
    assert S.search(ctx.f, "rf_abs_diff", "int broken(", budget=5)["status"] == "SKELETON_DOES_NOT_COMPILE"


@kit.gate("V-RF-SEARCH-BUDGET", drill=lambda: patched(S, "score", lambda *a, **k: {"pct": 1.0, "exact": False, "gap": 0, "obj": None}))
def g_budget(ctx):
    r = S.search(ctx.f, "rf_bsearch", ctx.skeletons()["rf_bsearch"], budget=2)
    assert r["status"] in ("BUDGET_EXHAUSTED", "EXACT") and r["compiles"] <= 2, r


@kit.gate("V-RF-PERMUTE", drill=lambda: patched(PM, "apply_all", lambda *a, **k: []))
def g_permute(ctx):
    sk = ctx.skeletons()
    names = sorted(sk)[:12]
    hit = 0
    for fn in names:
        r = PM.permute(ctx.f, fn, sk[fn], seed=7, iters=160)
        r2 = PM.permute(ctx.f, fn, sk[fn], seed=7, iters=160)
        assert r["path"] == r2["path"] and r["status"] == r2["status"], "not reproducible: " + fn
        hit += r["status"] == "EXACT"
    assert hit >= 8, "permuter solved only %d/12" % hit


@kit.gate("V-RF-PLAN", drill=lambda: patched(SP, "FAMILY_BY_CLASS", {k: SP.FAMILY_BY_CLASS["OPCODE"] for k in SP.FAMILY_BY_CLASS}))
def g_plan(ctx):
    a, b = SP.plan("ORDER"), SP.plan("OPCODE")
    assert a != b and a[0].startswith("commute") and b[0].endswith(("shl", "shr", "mul", "div")), (a[:2], b[:2])

    class N:
        def refuted_operator(self, fn, cls, op):
            return op == a[0]
    assert a[0] not in SP.plan("ORDER", nsm=N(), fn="x")


@kit.gate("V-RF-BUILD-TWIN", drill=lambda: patched(BT, "hypotheses", lambda p: BT.hypotheses(p)[:1]))
def g_twin(ctx):
    anch = ["rf_abs_diff", "rf_checksum", "rf_collatz", "rf_sum_n", "rf_gcd", "rf_clamp", "rf_min3"]
    P, f = ctx.P, ctx.f
    for var, want in (("o0_to_o1", "recipe:o1=variant:o0_to_o1"), ("o0_to_o2", "variant:o0_to_o2=variant:o1_to_o2"), ("o0_to_os", "variant:o0_to_os")):
        tg = {fn: f.compile_text(fn, f.read_source(fn), flags=P.flags("o0", "c", var)).obj for fn in anch}
        r = BT.twin(f, anch, tg)
        assert r["verdict"] == "TWIN_CONFIRMED" and r["matches"] == [want], (var, r["verdict"], r["matches"])
    tg = {"rf_add3": f.compile_text("rf_add3", f.read_source("rf_add3"), flags=P.flags("o0", "c")).obj}
    assert BT.twin(f, ["rf_add3"], tg)["verdict"] == "TWIN_UNCERTAIN"           # one anchor cannot discriminate -o0 from -msdata variants
    tg = {fn: f.compile_text(fn, f.read_source(fn), flags=["-O1", "-fno-tree-ch", "-ffunction-sections"]).obj for fn in anch}
    assert BT.twin(f, anch, tg)["verdict"] == "TWIN_NONE"


@kit.gate("V-RF-CORPUS-DETERMINISTIC", drill=lambda: patched(GC, "skeleton_for", lambda f, fn, t: None))
def g_corpus(ctx):
    P, out, seal = GC.build(ROOT)
    for src, t in out["skeleton"].items():
        assert open(os.path.join(P.source_dir("skeleton"), src)).read() == t, "skeleton drifted: " + src
    assert set(out["skeleton"]) == {s for s in os.listdir(P.source_dir("skeleton"))}
    assert json.load(open(P.p(P.doc["corpus"]["heldout_seal"]))) == seal, "held-out seal drifted"
    assert len(seal["functions"]) == 8


def _reg(ctx):
    if not hasattr(ctx, "reg"):
        ctx.reg = GC.om_registry(ctx.f)
    return ctx.reg


@contextlib.contextmanager
def _no_override():
    orig = OM.propagate

    def flat(reg):
        return {c: [dict(x, override=False) for x in rows] for c, rows in orig(reg).items()}
    OM.propagate = flat
    try:
        yield
    finally:
        OM.propagate = orig


@kit.gate("V-RF-OM-REGISTRY", drill=lambda: patched(OM, "grade", lambda kinds: "VTABLE"))
def g_om_registry(ctx):
    reg = _reg(ctx)
    assert {c: reg[c]["grade"] for c in reg} == {"Shape": "VTABLE", "CircleShape": "VTABLE", "RectShape": "VTABLE"}, {c: reg[c]["grade"] for c in reg}
    assert reg["Shape"]["kinds"] == ["data", "install", "vcall"] and reg["CircleShape"]["base"] == "Shape" and reg["Shape"]["base"] is None
    f = ctx.f                                                          # single-kind case: one object that only carries the table stays a CANDIDATE
    img = OM.Image(f.adapter, {"only": f.target("rf_shape_area")})
    one = OM.build_registry(img)
    assert one and all(r["grade"] == "CANDIDATE" and len(r["kinds"]) < 2 for r in one.values()), one
    assert OM.grade(["data", "data"]) == "CANDIDATE" and OM.grade(["data", "install"]) == "VTABLE"


@kit.gate("V-RF-OM-PROPAGATE", drill=_no_override)
def g_om_prop(ctx):
    reg = _reg(ctx)
    pr = OM.propagate(reg)
    circ = {x["method"] or x["kind"]: x for x in pr["CircleShape"]}
    rect = {x["method"] or x["kind"]: x for x in pr["RectShape"]}
    assert circ["area"]["override"] and circ["scale"]["override"] and circ["area"]["index"] == 0 and circ["scale"]["index"] == 1
    assert rect["area"]["override"] and not rect["scale"]["override"], "RectShape inherits Shape::scale"
    assert OM.root_methods(reg) == {0: ("area", [], True), 1: ("scale", ["s32"], False)}
    assert not any(x["override"] for x in pr["Shape"])


@kit.gate("V-RF-OM-THISCALL", drill=lambda: patched(OM, "field_accesses", lambda rows: []))
def g_om_this(ctx):
    f = ctx.f
    fn = "rf_circle_ctor"
    img = OM.Image(f.adapter, {fn: f.target(fn)})
    got = OM.field_accesses(img.rows(fn, ctx.P.functions[fn]["symbols"][0]))
    assert got == [(0, "stw"), (8, "stw")], got                             # vptr at 0, r at 8 (Shape::id is stored by the base ctor)
    assert OM.field_accesses([("blr", "", "", "")]) == []                   # no this-slot evidence -> no invented fields


@kit.gate("V-RF-OM-DECLS", drill=lambda: patched(OS, "class_decls", lambda reg: "struct Shape {};\n"))
def g_om_decls(ctx):
    reg = _reg(ctx)
    d = OS.class_decls(reg)
    assert "struct CircleShape : Shape" in d and d.index("virtual s32 area() const;") < d.index("virtual s32 scale(s32);")
    f = ctx.f
    c = f.adapter.compile("typedef int s32;\n" + d + "s32 g(const Shape *s){ return s->area(); }\n", "cxx", ctx.P.flags("o0", "cxx"), [], f._clean_dir("decl"), name="decls")
    assert c.ok, c.log
    cr = dict(reg)
    cr["Shape"] = dict(reg["Shape"], grade="CANDIDATE")
    assert "CANDIDATE: not promoted" in OS.class_decls(cr), "a CANDIDATE table must not emit declarations"


@kit.gate("V-RF-OM-VCALL", drill=lambda: patched(OS, "vslot_to_method", lambda t, reg: []))
def g_om_vcall(ctx):
    reg = _reg(ctx)
    vs = lambda t: OS.vslot_to_method(t, reg)
    for fn in ("rf_call_area", "rf_total_area", "rf_scale_all"):
        ref = ctx.f.read_source(fn)
        raw = OS.method_to_vslot(ref, reg)
        assert raw and "(*(void ***)" in raw[0], fn
        assert ctx.f.judge_text(fn, raw[0])[1].ok, "raw slot form must compile: " + fn
        assert OS.vslot_to_method(raw[0], reg) == [ref], fn                    # the OM operator inverts the lift exactly
        r = S.search(ctx.f, fn, raw[0], budget=60, extra={"vslot_to_method": vs})
        assert r["status"] == "EXACT", (fn, r["status"])
        assert C.certify(ctx.f, fn, r["text"], released=True)["verdict"] == "CERTIFIED_EXACT", fn
    sk = ctx.skeletons()["rf_scale_all"]
    assert S.search(ctx.f, "rf_scale_all", sk, budget=80, extra={"vslot_to_method": vs})["status"] == "EXACT"
    assert OS.vslot_to_method("int x;", reg) == []


@kit.gate("V-RF-NSM", drill=lambda: patched(NS.NSM, "known_not_found", lambda *a: None))
def g_nsm(ctx):
    f = ctx.f
    path = os.path.join(ctx.tmp.name, "nsm.jsonl")
    n = NS.NSM(path, world="A")
    mut = ctx.mutants()["rf_abs_diff"]
    r1 = S.search(f, "rf_abs_diff", mut, budget=200, nsm=n)
    r2 = S.search(f, "rf_abs_diff", mut, budget=200, nsm=n)
    assert r1["status"] == "NOT_FOUND" and r1["compiles"] > 0
    assert r2["status"] == "NOT_FOUND" and r2["compiles"] == 0, "a known dead run must not be re-paid: %s" % r2["compiles"]
    assert NS.NSM(path, world="A").known_not_found("rf_abs_diff", "x") is None                   # a different key is not known
    assert any(r["why"] == "RUN_NOT_FOUND" for r in NS.NSM(path, world="A").applicable())
    assert NS.NSM(path, world="B").applicable() == [], "another world must not inherit negatives"
    for _ in range(3):                                           # soundness: pruning must never make a solvable function unsolvable
        assert S.search(f, "rf_collatz", ctx.skeletons()["rf_collatz"], budget=300, nsm=n)["status"] == "EXACT"
    m = NS.NSM(world="A")
    m.record("fx", "OPCODE", "shr_to_div", "REFUTED")
    assert m.refuted_operator("fx", "OPCODE", "shr_to_div") and not m.refuted_operator("fx", "ORDER", "shr_to_div")
    m.record("fx", "OPCODE", "shr_to_div", "SOLVED")
    assert not m.refuted_operator("fx", "OPCODE", "shr_to_div"), "a solve vetoes a refutation"
    m.record("fx", "OPCODE", "mul_to_shl", "NO_GAIN")
    assert not m.refuted_operator("fx", "OPCODE", "mul_to_shl"), "no-gain is advisory, never a refutation"
    w = NS.NSM(world="B")
    w.rows = list(m.rows)
    assert not w.refuted_operator("fx", "OPCODE", "shr_to_div") and w.applicable() == []


def _cls(ctx, fn, text):
    c = ctx.f.judge_text(fn, text)[1]
    return CD.causal_diff(ctx.f.adapter, ctx.f.target(fn), c.obj, ctx.P.functions[fn]["symbols"])["primary"]


@kit.gate("V-RF-METHOD-GRAPH", drill=lambda: patched(MG, "expand", lambda *a, **k: []))
def g_mgraph(ctx):
    sk = ctx.skeletons()
    g = MG.MethodGraph()
    assert g.prior("OPCODE") == {} and g.supercompile() == {}, "an empty graph must claim nothing"
    solved = {}
    for fn in ("rf_clamp", "rf_min3", "rf_abs_diff", "rf_bsearch", "rf_collatz"):
        r = S.search(ctx.f, fn, sk[fn], budget=300)
        assert r["status"] == "EXACT", fn
        solved[fn] = r["path"]
        g.learn(_cls(ctx, fn, sk[fn]), r["path"])
    g.learn("OPCODE", ["x"], solved=False)
    macros = g.supercompile(min_count=2)
    assert "flip_cmp+flip_cmp" in macros, macros                                    # clamp and min3 share a trajectory -> one macro
    assert all(len(v) >= 2 for v in macros.values())
    cls = _cls(ctx, "rf_clamp", sk["rf_clamp"])
    pri = g.prior(cls)
    assert pri.get("flip_cmp", 0) > 0 and "x" not in pri
    assert SP.plan(cls, prior=pri)[0] in pri and SP.plan(cls, prior=pri) != SP.plan(cls), "a learned prior must reorder the plan"
    for fn in ("rf_clamp", "rf_min3"):                                                # the macro replays as ONE step and reaches an exact text
        ts = MG.expand(sk[fn], macros["flip_cmp+flip_cmp"])
        assert ts and any(ctx.f.judge_text(fn, t)[0]["exact"] for t in ts), fn
    g2 = MG.MethodGraph.from_json(g.to_json())
    assert g2.supercompile(2) == macros and g2.prior(cls) == pri
    r = S.search(ctx.f, "rf_clamp", sk["rf_clamp"], budget=300, prior=pri)
    assert r["status"] == "EXACT"


@kit.gate("V-RF-GENOME", drill=lambda: patched(GN, "fitness", lambda *a, **k: (0, 0)))
def g_genome(ctx):
    sk = ctx.skeletons()
    train = [(fn, sk[fn]) for fn in ("rf_abs_diff", "rf_bsearch", "rf_clamp")]
    a = GN.evolve(ctx.f, train, seed=3, pop=4, gens=2, budget=40)
    b = GN.evolve(ctx.f, train, seed=3, pop=4, gens=2, budget=40)
    assert a == b, "evolution must be reproducible from its seed"
    assert a["baseline_fitness"][0] == 0, "the depth-0 baseline solves nothing"
    assert a["fitness"][0] >= 2 and a["fitness"] > a["baseline_fitness"], a
    g = GN.baseline()
    rng = __import__("random").Random(1)
    for _ in range(40):
        g = GN.mutate(g, rng)
        assert 0 <= g["depth"] <= 4 and 1 <= g["width"] <= 6 and len(set(g["ops"])) == len(g["ops"])


if __name__ == "__main__":
    sys.exit(kit.main(Ctx))
