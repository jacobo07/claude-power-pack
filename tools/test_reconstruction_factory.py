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
from modules.reconstruction_factory import atoms as AT
from modules.reconstruction_factory import claims as CL
from modules.reconstruction_factory import invalidation as INV
from modules.reconstruction_factory import judge as J
from modules.reconstruction_factory import genome as GN
from modules.reconstruction_factory import heldout as HO
from modules.reconstruction_factory import frontier as FR
from modules.reconstruction_factory import maturity as MT
from modules.reconstruction_factory import cbr as CB
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
            if os.path.exists(p) and not d.get("heldout"):
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


def _raises(exc, fn, *a):
    try:
        fn(*a)
    except exc:
        return True
    return False


@kit.gate("V-RF-ATOMS", drill=lambda: patched(AT, "_check", lambda *a: None))
def g_atoms(ctx):
    good = {"fn": "rf_add3", "verdict": "CERTIFIED_EXACT", "candidate_sha256": "ab"}
    assert AT.validate("certificate", good) is good
    for bad in ({"fn": "x", "verdict": "MAYBE", "candidate_sha256": None}, {"fn": 1, "verdict": "NOT_EXACT", "candidate_sha256": None},
                {"fn": "x", "verdict": "NOT_EXACT"}, {"fn": "x", "verdict": "NOT_EXACT", "candidate_sha256": None, "extra": 1}):
        assert _raises(AT.Malformed, AT.validate, "certificate", bad), bad
    assert _raises(AT.Malformed, AT.validate, "no_such_predicate", {})
    assert _raises(AT.Malformed, AT.validate, "vcall_site", {"fn": "x", "slot": -1}) and not _raises(AT.Malformed, AT.validate, "vcall_site", {"fn": "x", "slot": 0})
    w1, w2 = AT.world(compiler_profile="o0"), AT.world(compiler_profile="o2")
    k = AT.semantic_key("f", "vcall_site", {"fn": "f", "slot": 1}, w1)
    assert k == AT.semantic_key("f", "vcall_site", {"slot": 1, "fn": "f"}, w1) and k != AT.semantic_key("f", "vcall_site", {"fn": "f", "slot": 1}, w2)
    assert AT.world_compatible(w1, {}) and not AT.world_compatible(w1, w2) and AT.world_compatible(w1, AT.world(tool_versions="1"))
    assert _raises(AT.Malformed, lambda: AT.world(bogus=1))
    n = len(AT.PREDICATES)
    assert _raises(AT.Refused, AT.register, "vtable", {"consumers": ["x"]}) and _raises(AT.Refused, AT.register, "fresh_pred", {"fields": {}, "consumers": []})
    try:
        AT.register("fresh_pred", {"fields": {"a": "int"}, "consumers": ["tools/x.py::y"]})
        assert AT.validate("fresh_pred", {"a": 1}) == {"a": 1}
    finally:
        AT.PREDICATES.pop("fresh_pred", None)
    assert len(AT.PREDICATES) == n


@kit.gate("V-RF-CLAIMS", drill=lambda: patched(CL.ClaimStore, "invalidate", lambda self, reason, w: {"reason": reason, "claims": []}))
def g_claims(ctx):
    st = CL.ClaimStore()
    w = AT.world(compiler_profile="o0", tool_versions="gcc-a")
    c1 = C.certify(ctx.f, "rf_add3", ctx.f.read_source("rf_add3"))
    a = st.from_certificate("rf_add3", c1, w)
    b = st.from_certificate("rf_add3", c1, w)
    assert a is b and len(st.claims) == 1 and len(a["evidence"]) == 2 and a["grade"] == "PROVEN", "the same proposition is one claim"
    neg = C.certify(ctx.f, "rf_add3", ctx.mutants()["rf_add3"])
    n = st.from_certificate("rf_add3", neg, w)
    assert n["grade"] == "SHADOW" and n["payload"]["candidate_sha256"] is None and len(st.claims) == 2
    st.from_judge("rf_add3", ctx.f.judge_text("rf_add3", ctx.f.read_source("rf_add3"))[0], w)
    assert st.require("rf_add3", "certificate", w)["grade"] == "PROVEN"
    assert _raises(CL.Refused, st.require, "rf_never", "certificate", w), "UNKNOWN is a refusal, not a pass"
    assert _raises(AT.Malformed, st.assert_claim, "x", "certificate", {"fn": "x", "verdict": "BOGUS", "candidate_sha256": None}, w)
    assert _raises(AT.Malformed, st.assert_claim, "x", "vtable", {"cls": "X", "grade": "VTABLE", "kinds": [], "slots": 0}, w, "INVALIDATED")
    ev = st.invalidate("tool_version_changed", AT.world(tool_versions="gcc-b"))
    assert len(ev["claims"]) == 3 and all(c["grade"] == "INVALIDATED" for c in st.claims.values()), ev
    assert _raises(CL.Refused, st.require, "rf_add3", "certificate", AT.world(compiler_profile="o0", tool_versions="gcc-a")), "an invalidated claim is not handed over"
    assert st.invalidate("scope_changed", AT.world(tool_versions="gcc-b"))["claims"] == [], "nothing live left to withdraw"
    assert _raises(AT.Malformed, st.invalidate, "because", {})


@kit.gate("V-RF-INVALIDATION", drill=lambda: patched(INV, "delta_ids", lambda o, n: ([], False, [])))
def g_invalidation(ctx):
    f, P = ctx.f, ctx.P
    hdr = os.path.join(ROOT, "fixtures/synthetic/ctx/ctx.h")
    old = open(hdr).read()
    src = {fn: f.read_source(fn) for fn in P.names()}
    edits = {"reorder RfRect": old.replace("    s32 w;\n    s32 h;\n} RfRect;", "    s32 h;\n    s32 w;\n} RfRect;"),
             "widen RfVec2.x": old.replace("typedef struct RfVec2 {\n    s32 x;", "typedef struct RfVec2 {\n    s16 x;"),
             "comment only": old + "\n/* nothing changes */\n"}
    seen_changed = {}
    for label, new in edits.items():
        assert new != old, label
        d = os.path.join(ctx.tmp.name, "inc-" + label.replace(" ", "_"))
        shutil.copytree(os.path.dirname(hdr), d)
        open(os.path.join(d, "ctx.h"), "w").write(new)
        truth = set()
        for fn in P.names():
            a = f.adapter.compile(src[fn], P.functions[fn]["lang"], f.flags_for(fn), [d], f._clean_dir("inv"), name=fn)
            if not a.ok or open(a.obj, "rb").read() != open(f.target(fn), "rb").read():
                truth.add(fn)
        dirty, info = INV.closure(src, old, new)
        assert truth <= set(dirty), "UNSOUND %s: compiler changed %s, closure missed %s" % (label, sorted(truth), sorted(truth - set(dirty)))
        seen_changed[label] = (len(truth), len(dirty))
    assert seen_changed["reorder RfRect"][0] >= 3 and seen_changed["reorder RfRect"][1] < len(src) // 2, seen_changed      # sound AND selective
    assert seen_changed["comment only"] == (0, 0), seen_changed


@kit.gate("V-RF-HELDOUT-RELEASE", drill=lambda: patched(HO, "verify_seal", lambda project: []))
def g_heldout(ctx):
    from modules.reconstruction_factory.manifest import Project
    P = ctx.P
    assert HO.verify_seal(P) == [] and HO.leak_scan(P) == [], (HO.verify_seal(P), HO.leak_scan(P))
    held = P.names(heldout=True)
    assert len(held) >= 8
    root = os.path.join(ctx.tmp.name, "ho")
    shutil.copytree(os.path.join(ROOT, "fixtures/synthetic"), root)
    P2 = Project(os.path.join(root, "recon.toml"))
    led = os.path.join(ctx.tmp.name, "ledger.json")
    f2 = Factory(P2, workdir=ctx.tmp.name)
    txt = f2.read_source(held[0], "heldout") if False else open(P2.source_path(held[0])).read()
    assert C.certify(f2, held[0], txt)["verdict"] == "HELDOUT_NOT_RELEASED"
    assert HO.certify_released(f2, held[0], txt, led)["verdict"] == "HELDOUT_NOT_RELEASED", "no ledger entry: still refused"
    sha = "ab" * 32
    assert _raises(HO.HeldoutError, HO.release, P2, led, held[:1], "short", "x") and _raises(HO.HeldoutError, HO.release, P2, led, held[:1], sha, "")
    assert _raises(HO.HeldoutError, HO.release, P2, led, [P2.names()[0]], sha, "dev fn is not held-out")
    HO.release(P2, led, held[:2], sha, "first evaluation")
    assert HO.is_released(led, held[0]) and not HO.is_released(led, held[2])
    assert HO.certify_released(f2, held[0], txt, led)["verdict"] == "CERTIFIED_EXACT"
    assert HO.certify_released(f2, held[2], open(P2.source_path(held[2])).read(), led)["verdict"] == "HELDOUT_NOT_RELEASED"
    assert _raises(HO.HeldoutError, HO.release, P2, led, held[2:3], "cd" * 32, "solver edited after peeking")
    HO.release(P2, led, held[2:3], sha, "same frozen solver")
    # tamper: a changed held-out source breaks the seal; release and certification both stop
    with open(P2.source_path(held[3]), "a") as fh:
        fh.write("\n/* tampered */\n")
    assert HO.verify_seal(P2) == ["SOURCE_CHANGED:" + held[3]], HO.verify_seal(P2)
    assert _raises(HO.HeldoutError, HO.release, P2, led, held[3:4], sha, "after tamper")
    assert HO.certify_released(f2, held[0], txt, led)["verdict"] == "HELDOUT_NOT_RELEASED", "a broken seal revokes the door"
    f2.close()
    # leak: a held-out name in the dev corpus is caught
    with open(os.path.join(root, "ctx", "leak.h"), "w") as fh:
        fh.write("/* %s */\n" % held[0])
    assert any(x.startswith("NAME:" + held[0]) for x in HO.leak_scan(P2)), HO.leak_scan(P2)


@kit.gate("V-RF-PROVENANCE", drill=lambda: patched(OM, "scan_installs", lambda img: ([], {})))
def g_provenance(ctx):
    from modules.reconstruction_factory import provenance as PV
    f = ctx.f
    want = {"rf_circle_ctor": "E2", "rf_rect_ctor": "E2", "rf_rect_dtor": "E2", "rf_shape_ctor": "E3", "rf_counter_inc": "E0", "rf_shape_scale": "E0", "rf_call_area": "E0",
            "rf_add3": "NONE", "rf_clamp": "NONE"}
    for fn, g in want.items():
        if fn not in ctx.P.functions:
            continue
        r = PV.grade(f.adapter, f.target(fn), ctx.P.functions[fn]["symbols"] if ctx.P.functions[fn]["lang"] == "cxx" else [e["name"] for e in OM.read_elf(f.target(fn)).defined_function_symbols()])
        assert r["grade"] == g, (fn, r)
    assert sum(1 for fn in want if fn in ctx.P.functions) >= 7


@kit.gate("V-RF-FRONTIER", drill=lambda: patched(FR, "project", lambda rows, removed: ([f for f, b in [(r["fn"], x) for r in rows for x in r["blockers"] if x in removed]], [])))
def g_frontier(ctx):
    rows = [{"fn": "A", "blockers": ["x", "y"], "callers": ["D"]}, {"fn": "B", "blockers": ["x"], "callers": []}, {"fn": "C", "blockers": ["y"], "callers": []},
            {"fn": "D", "blockers": ["z"], "callers": []}]
    unl, touched = FR.project(rows, ["x", "y"])
    assert unl == ["A", "B", "C"] and touched == ["A", "B", "C"], (unl, touched)
    assert FR.project(rows, ["x"])[0] == ["B"] and FR.project(rows, [])[0] == []
    fr = FR.compute(rows)
    assert fr["x"]["blocked_direct"] == [1, 2] and fr["x"]["sole"] == ["B"]
    assert fr["z"]["blocked"] == [1, 1] and fr["x"]["blocked_transitive_high"] == 1, fr["x"]      # D calls A: A's blocker x also blocks D transitively (high side only)
    pl = FR.plan(rows, 3)
    assert pl[-1][2] == 4 and sum(p[1] for p in pl) == pl[-1][2], pl      # newly-unlocked counts add up to the union: each function once
    res = {}
    for fn, t in ctx.skeletons().items():
        r, c = ctx.f.judge_text(fn, t)
        if c.ok and not r["exact"]:
            res[fn] = RS.residual(ctx.f.adapter, ctx.f.target(fn), c.obj, ctx.P.functions[fn]["symbols"])
    real = FR.rows_from_project(ctx.f, res)
    assert len(real) >= 10 and all(r["blockers"] for r in real)
    top = FR.rank(FR.compute(real))
    assert top and top[0]["blocked"][1] >= 2
    unl2, _ = FR.project(real, [d["blocker"] for d in top])
    assert len(unl2) == len(set(unl2)) == len(real), "removing every blocker unlocks each function exactly once"
    sc = FR.shuffle_control(real, n=5)
    assert set(sc) == {"real", "shuffled_mean", "shuffled_max", "falls"}


@kit.gate("V-RF-MATURITY", drill=lambda: patched(MT, "holds", lambda p, graph=None: True))
def g_maturity(ctx):
    rub = {"D": [(2, ("file", "modules/reconstruction_factory/certify.py"), "a"), (4, ("file", "no/such/file"), "b"), (6, ("file", "modules/reconstruction_factory/search.py"), "c")]}
    assert MT.vector(rub)["dimensions"]["D"] == 2, "a chain: anchor 6 holds but anchor 4 does not, so the grade is 2"
    assert MT.grade([], None) == 0 and MT.grade([(3, ("file", "no/such"), "x")]) == 0
    assert _raises(ValueError, MT.holds, ("nope",))
    v = MT.vector()
    assert v["overall"] == min(v["dimensions"].values()) and v["overall"] < 10, "10 is Owner acceptance; nothing here may self-grade to it"
    assert all(g < 10 for g in v["dimensions"].values())
    g = MT.import_graph()
    assert "judge" in g["search"] and MT.reachable("judge") and not MT.reachable("maturity")
    assert MT.verify_contract(), "the frozen rubric hash must match"
    edited = dict(MT.RUBRIC, D01_certification=[(2, ("file", "modules/reconstruction_factory/certify.py"), "edited")])
    assert not MT.verify_contract(edited), "editing the rubric turns the contract red"
    assert not MT.verify_contract(path=os.path.join(ctx.tmp.name, "absent.json"))


_cbr_decide = CB.decide


@kit.gate("V-RF-CBR", drill=lambda: patched(CB, "decide", lambda p, satisfied=(): _cbr_decide(p, satisfied)[:-1]))
def g_cbr(ctx):
    P = ctx.P
    b = CB.birth(P)
    ins = ["%s:%s" % x for x in CB.discover(P)]
    assert len(b["rows"]) == len(ins) and sorted(r["input"] for r in b["rows"]) == ins, "one row per discovered input"
    assert "module:heldout" in ins and "heldout:sealed" in ins and "adapter:gcc-ppc" in ins and "lang:cxx" in ins
    assert b["counts"]["UNKNOWN"] == 0 and b["counts"]["INHERITED"] > 30, b["counts"]
    assert CB.birth(P)["digest"] == b["digest"], "deterministic"
    prof = CB.profile(P)
    assert CB._decide("module", "om", dict(prof, cxx=False))[0] == "NOT_APPLICABLE"
    assert CB._decide("module", "heldout", dict(prof, sealed=False))[0] == "CONFLICT"
    assert CB._decide("module", "judge", dict(prof, adapter="mwcc"))[0] == "ADAPTED"
    assert CB._decide("module", "never_heard_of_it", prof)[0] == "UNKNOWN" and CB._decide("adapter", "mwcc", prof)[0] == "UNKNOWN"
    assert CB._decide("module", "judge", prof, satisfied=("module:judge",))[0] == "ALREADY_SATISFIED"
    assert {CB._decide("module", m, prof)[0] for m in ("om", "judge")} == {"INHERITED"}
    assert any(r["disposition"] == "ALREADY_SATISFIED" for r in CB.decide(P, satisfied=("module:judge",)))
    rows = b["rows"]
    assert CB.check_rows(rows[:-1], P) and CB.check_rows(rows + rows[:1], P) and CB.check_rows(rows + [{"input": "x:y", "disposition": "INHERITED", "reason": "", "evidence": ["e"]}], P)
    assert CB.check_rows([dict(r, disposition="MAYBE") if i == 0 else r for i, r in enumerate(rows)], P)
    assert CB.check_rows([dict(r, evidence=[]) if r["disposition"] == "INHERITED" and i == 0 else r for i, r in enumerate(rows)], P)
    ret = CB.construction_return([{"kind": "NEW_ORACLE", "subject": "objdump text compare", "evidence": ["V-RF-CERT-POSITIVE"]}], rows)
    assert len(ret["digest"]) == 64
    conflict = [dict(rows[0], input="adapter:mwcc", disposition="UNKNOWN")] + rows
    assert CB.construction_return([{"kind": "FAILED_TRANSFER", "subject": "mwcc", "birth_input": "adapter:mwcc", "evidence": ["x"]}], conflict)
    assert _raises(ValueError, CB.construction_return, [{"kind": "FAILED_TRANSFER", "subject": "judge", "birth_input": rows[0]["input"], "evidence": ["x"]}], rows)
    assert _raises(ValueError, CB.construction_return, [{"kind": "NEW_CAPABILITY", "subject": "s", "evidence": []}], rows)
    assert _raises(ValueError, CB.construction_return, [{"kind": "WISHFUL", "subject": "s", "evidence": ["e"]}], rows)


if __name__ == "__main__":
    sys.exit(kit.main(Ctx))
