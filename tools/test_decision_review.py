"""test_decision_review.py -- DRK done-gate (V-DRK-* gates + FASE-5 scenarios).

Hermetic: writes only to a temp Registry, reads no global state, deterministic
(no wall-clock in the kernel). Re-runnable with identical output.

Run: python tools/test_decision_review.py
Exit 0 iff every gate passes.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PP_ROOT = Path(__file__).resolve().parents[1]
if str(PP_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_ROOT))

from modules.decision_review.decision_record import (  # noqa: E402
    DecisionObject, DecisionRecord, Evidence, EvidenceType, Reversibility,
    ReviewTier, Verdict, Registry,
)
from modules.decision_review.decision_kernel import (  # noqa: E402
    review_decision, classify_reversibility, compute_dcs,
)
from modules.decision_review.accountability import (  # noqa: E402
    score_predictions, attribute, calibrate,
)

_passes = 0
_fails = 0


def _ok(gate: str, evidence: str) -> None:
    global _passes
    _passes += 1
    print(f"  [PASS] {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    global _fails
    _fails += 1
    print(f"  [FAIL] {gate}: {diag}")


def _tmp_registry() -> Registry:
    d = tempfile.mkdtemp(prefix="drk_test_")
    return Registry(Path(d) / "records.jsonl")


def _obj(**kw) -> DecisionObject:
    base = dict(id="DEC-TEST", statement="", problem="p", options=["a", "b"],
                chosen="a", rationale="r")
    base.update(kw)
    return DecisionObject(**base)


def _fact(level: int = 4) -> Evidence:
    return Evidence(type=EvidenceType.FACT, claim="measured", source="run",
                    acis_level=level)


# ----------------------------------------------------------------------------
# V-DRK-REVERSIBILITY -- Tipo A/B/C assigned from markers
# ----------------------------------------------------------------------------
def test_reversibility():
    a = classify_reversibility(_obj(statement="polish the wording of a note"))
    b = classify_reversibility(_obj(statement="refactor the config dependency"))
    c = classify_reversibility(_obj(statement="run a database schema migration"))
    if a == Reversibility.A and b == Reversibility.B and c == Reversibility.C:
        _ok("V-DRK-REVERSIBILITY", f"A/B/C = {a.value}/{b.value}/{c.value}")
    else:
        _fail("V-DRK-REVERSIBILITY", f"got {a}/{b}/{c}")


# ----------------------------------------------------------------------------
# V-DRK-SCOPE -- out-of-scope decision -> L0, no verdict, no record
# ----------------------------------------------------------------------------
def test_scope_l0():
    reg = _tmp_registry()
    rec = review_decision(
        _obj(statement="polish the wording of an internal note",
             evidence=[_fact()]), registry=reg, ts="t")
    if rec.tier == ReviewTier.L0 and rec.verdict is None and reg.count() == 0:
        _ok("V-DRK-SCOPE", "trivial choice -> L0, no record written")
    else:
        _fail("V-DRK-SCOPE", f"tier={rec.tier} verdict={rec.verdict} n={reg.count()}")


# ----------------------------------------------------------------------------
# V-DRK-RECORD-CANONICAL -- an in-scope review writes a schema-valid record
# ----------------------------------------------------------------------------
def test_record_canonical():
    reg = _tmp_registry()
    rec = review_decision(
        _obj(statement="add a helper to the user greeting code",
             evidence=[_fact()]), registry=reg, ts="t1")
    d = rec.to_dict()
    keys = {"id", "ts", "tier", "verdict", "blocked", "decision"}
    loaded = reg.load()
    if keys <= set(d) and reg.count() == 1 and loaded and loaded[0]["id"] == "DEC-TEST":
        _ok("V-DRK-RECORD-CANONICAL", f"record persisted, verdict={rec.verdict.value}")
    else:
        _fail("V-DRK-RECORD-CANONICAL", f"keys/count mismatch n={reg.count()}")


# ----------------------------------------------------------------------------
# V-DRK-VERDICT-ONTOLOGY -- each of the ten verdicts is reachable
# ----------------------------------------------------------------------------
def test_verdict_ontology():
    reg = _tmp_registry()
    reached = {}

    # APPROVE: reversible, in-scope, no objection
    reached["APPROVE"] = review_decision(
        _obj(statement="add a helper to the user greeting code",
             evidence=[_fact()]), registry=reg, ts="t").verdict

    # APPROVE-WITH-CONDITIONS: Tipo B adequately evidenced
    reached["AWC"] = review_decision(
        _obj(statement="refactor the loader module dependency",
             evidence=[_fact()], accepted_risks=["r"]),
        registry=reg, ts="t").verdict

    # REQUEST-EVIDENCE: Tipo B, no strong evidence
    reached["REQ"] = review_decision(
        _obj(statement="change the module dependency",
             evidence=[Evidence(EvidenceType.ASSUMPTION, "guess")]),
        registry=reg, ts="t").verdict

    # REJECT: precedent collision on a veto
    reached["REJECT"] = review_decision(
        _obj(statement="use the code module", evidence=[_fact()]),
        precedent={"verdict": "COLLISION", "on_veto": True},
        registry=reg, ts="t").verdict

    # REFRAME: L3, no discarded alternatives
    reached["REFRAME"] = review_decision(
        _obj(statement="refactor the module dependency",
             evidence=[_fact(), Evidence(EvidenceType.UNKNOWN, "?")],
             discarded_alternatives=[]),
        registry=reg, ts="t").verdict

    # RUN-EXPERIMENT: L3, alternatives present, no accepted risks
    reached["RUNEXP"] = review_decision(
        _obj(statement="refactor the module dependency",
             evidence=[_fact(), Evidence(EvidenceType.UNKNOWN, "?")],
             discarded_alternatives=["keep as-is"], accepted_risks=[]),
        registry=reg, ts="t").verdict

    # CONSOLIDATE / KEEP-LOCAL / REMOVE: build decisions with placement
    reached["CONS"] = review_decision(
        _obj(statement="build a new module", is_build_decision=True,
             evidence=[_fact()]),
        placement={"operation": "CONSOLIDATE", "coverage": 0.95},
        registry=reg, ts="t").verdict
    reached["KEEP"] = review_decision(
        _obj(statement="build a new module", is_build_decision=True,
             evidence=[_fact()]),
        placement={"operation": "KEEP_LOCAL"}, registry=reg, ts="t").verdict
    reached["REMOVE"] = review_decision(
        _obj(statement="build a new module", is_build_decision=True,
             evidence=[_fact()]),
        placement={"operation": "DO_NOT_BUILD"}, registry=reg, ts="t").verdict

    # DEFER: fail-open on pathological input
    reached["DEFER"] = review_decision(None, registry=reg, ts="t").verdict

    expected = {
        "APPROVE": Verdict.APPROVE,
        "AWC": Verdict.APPROVE_WITH_CONDITIONS,
        "REQ": Verdict.REQUEST_EVIDENCE,
        "REJECT": Verdict.REJECT,
        "REFRAME": Verdict.REFRAME,
        "RUNEXP": Verdict.RUN_EXPERIMENT,
        "CONS": Verdict.CONSOLIDATE,
        "KEEP": Verdict.KEEP_LOCAL,
        "REMOVE": Verdict.REMOVE,
        "DEFER": Verdict.DEFER,
    }
    bad = {k: (reached[k], expected[k]) for k in expected if reached[k] != expected[k]}
    distinct = {v for v in reached.values() if v is not None}
    if not bad and len(distinct) == 10:
        _ok("V-DRK-VERDICT-ONTOLOGY", "all 10 verdicts reachable + correct")
    else:
        _fail("V-DRK-VERDICT-ONTOLOGY", f"mismatches={bad} distinct={len(distinct)}")


# ----------------------------------------------------------------------------
# V-DRK-BLOCK-GATE -- blocks iff Tipo-C AND evidence < E3; never otherwise
# ----------------------------------------------------------------------------
def test_block_gate():
    reg = _tmp_registry()
    # Tipo C, evidence below E3 -> blocked
    blocked = review_decision(
        _obj(statement="run an irreversible production database schema migration that deletes data",
             evidence=[Evidence(EvidenceType.INFERENCE, "guess", acis_level=1)]),
        registry=reg, ts="t")
    # Tipo C, evidence at E3+ -> not blocked
    okc = review_decision(
        _obj(statement="run an irreversible production database schema migration that deletes data",
             evidence=[_fact(level=4)], accepted_risks=["data loss priced"]),
        registry=reg, ts="t")
    # Reversible -> never blocked
    rev = review_decision(
        _obj(statement="add a helper to the user greeting code", evidence=[_fact()]),
        registry=reg, ts="t")
    if blocked.blocked and blocked.tier == ReviewTier.L4 \
            and not okc.blocked and not rev.blocked:
        _ok("V-DRK-BLOCK-GATE",
            f"C&<E3 blocked; C&>=E3 not; reversible not (verdicts "
            f"{blocked.verdict.value}/{okc.verdict.value}/{rev.verdict.value})")
    else:
        _fail("V-DRK-BLOCK-GATE",
              f"blocked={blocked.blocked}/{blocked.tier} okc={okc.blocked} rev={rev.blocked}")


# ----------------------------------------------------------------------------
# V-DRK-FAILOPEN -- pathological input -> DEFER, never raise
# ----------------------------------------------------------------------------
def test_failopen():
    reg = _tmp_registry()
    try:
        rec = review_decision(None, registry=reg, ts="t")
        if rec.verdict == Verdict.DEFER and any("fail-open" in g for g in rec.guards_fired):
            _ok("V-DRK-FAILOPEN", "None input -> DEFER, no raise")
        else:
            _fail("V-DRK-FAILOPEN", f"verdict={rec.verdict} guards={rec.guards_fired}")
    except Exception as exc:  # noqa: BLE001
        _fail("V-DRK-FAILOPEN", f"raised {type(exc).__name__}")


# ----------------------------------------------------------------------------
# V-DRK-ACCOUNTABILITY -- prediction scored vs outcome (Parte VI)
# ----------------------------------------------------------------------------
def test_accountability():
    obj = _obj(statement="ship feature x",
               predicted_consequences=[
                   {"claim": "adoption rises", "observable": "adoption", "expected": True},
                   {"claim": "latency flat", "observable": "latency", "expected": True},
                   {"claim": "vibes improve"},  # no observable -> unobservable
               ])
    rec = DecisionRecord(obj=obj, verdict=Verdict.APPROVE)
    summary = score_predictions(rec, {"adoption": True, "latency": False})
    if summary["hits"] == 1 and summary["misses"] == 1 and summary["unobservable"] == 1 \
            and abs(summary["error"] - 0.5) < 1e-9:
        _ok("V-DRK-ACCOUNTABILITY",
            f"hits/misses/unobs = {summary['hits']}/{summary['misses']}/{summary['unobservable']}")
    else:
        _fail("V-DRK-ACCOUNTABILITY", str(summary))


# ----------------------------------------------------------------------------
# V-DRK-ATTRIBUTION -- reasoning/execution/luck/context separated
# ----------------------------------------------------------------------------
def test_attribution():
    obj = _obj(statement="ship feature x", accepted_risks=["provider outage"])
    rec = DecisionRecord(obj=obj, verdict=Verdict.APPROVE)
    rec.prediction_error = {"error": 1.0}  # bad outcome
    # execution failed -> outcome partly execution, not reasoning
    a = attribute(rec, execution_ok=False, failed_risk_was_accepted=None)
    # priced risk landed badly -> luck, reasoning residual preserved
    b = attribute(rec, execution_ok=True, failed_risk_was_accepted=True)
    if a["sources"]["execution"] == 0.5 and a["sources"]["reasoning"] == 0.5 \
            and b["sources"]["luck"] > 0 and b["dominant"] in ("reasoning", "luck"):
        _ok("V-DRK-ATTRIBUTION",
            f"exec-fail reasoning={a['sources']['reasoning']}; luck-case luck={b['sources']['luck']}")
    else:
        _fail("V-DRK-ATTRIBUTION", f"a={a['sources']} b={b['sources']}")


# ----------------------------------------------------------------------------
# V-DRK-3-BIAS -- never-reject / always-reject / always-platform detected
# ----------------------------------------------------------------------------
def _rec_with(verdict: Verdict, blocked: bool = False, conf: int = 70) -> DecisionRecord:
    o = _obj(); o.confidence = conf
    return DecisionRecord(obj=o, verdict=verdict, blocked=blocked)


def test_three_bias():
    never = calibrate([_rec_with(Verdict.APPROVE) for _ in range(10)])
    always_rej = calibrate([_rec_with(Verdict.REJECT) for _ in range(6)]
                           + [_rec_with(Verdict.APPROVE) for _ in range(4)])
    always_plat = calibrate([_rec_with(Verdict.CONSOLIDATE) for _ in range(6)]
                            + [_rec_with(Verdict.APPROVE) for _ in range(4)])
    insufficient = calibrate([_rec_with(Verdict.APPROVE) for _ in range(3)])
    ok = ("never-reject" in never["biases_detected"]
          and "always-reject" in always_rej["biases_detected"]
          and "always-platform" in always_plat["biases_detected"]
          and insufficient["status"] == "insufficient_data")
    if ok:
        _ok("V-DRK-3-BIAS", "all three biases detected; <8 -> insufficient_data")
    else:
        _fail("V-DRK-3-BIAS",
              f"never={never['biases_detected']} rej={always_rej['biases_detected']} "
              f"plat={always_plat['biases_detected']} insuf={insufficient['status']}")


# ----------------------------------------------------------------------------
# FASE-5 scenario matrix -- the mandatory decision scenarios map to verdicts
# ----------------------------------------------------------------------------
def test_fase5_scenarios():
    reg = _tmp_registry()
    scenarios = [
        # (name, kwargs, precedent, placement, expected verdict)
        ("build-nothing", dict(statement="build a new module", is_build_decision=True,
                               evidence=[_fact()]), None,
         {"operation": "DO_NOT_BUILD"}, Verdict.REMOVE),
        ("platform-correct", dict(statement="build a new module", is_build_decision=True,
                                  evidence=[_fact()]), None,
         {"operation": "CONSOLIDATE", "coverage": 0.9}, Verdict.CONSOLIDATE),
        ("platform-incorrect", dict(statement="build a new module", is_build_decision=True,
                                    evidence=[_fact()]), None,
         {"operation": "KEEP_LOCAL"}, Verdict.KEEP_LOCAL),
        ("temp-duplication-ok", dict(statement="build a new module", is_build_decision=True,
                                     evidence=[_fact()]), None,
         {"operation": "KEEP_LOCAL"}, Verdict.KEEP_LOCAL),
        ("request-evidence", dict(statement="change the module dependency",
                                  evidence=[Evidence(EvidenceType.ASSUMPTION, "big tech does this")]),
         None, None, Verdict.REQUEST_EVIDENCE),
        ("big-tech-bad-ref", dict(statement="change the module dependency",
                                  evidence=[Evidence(EvidenceType.PREFERENCE, "big tech does this")]),
         None, None, Verdict.REQUEST_EVIDENCE),
        # decider DID weigh alternatives + name risks; abstains because the
        # evidence burden for a Tipo-C decision is unmet (not because unconsidered)
        ("short-term-destroys-optionality",
         dict(statement="run an irreversible schema migration that deletes data",
              evidence=[Evidence(EvidenceType.INFERENCE, "guess", acis_level=1)],
              discarded_alternatives=["defer the migration"],
              accepted_risks=["irreversible data loss"]),
         None, None, Verdict.REQUEST_EVIDENCE),
        ("adversarial-abstain",
         dict(statement="run an irreversible production schema migration deleting data",
              evidence=[Evidence(EvidenceType.HYPOTHESIS, "maybe", acis_level=1)],
              discarded_alternatives=["keep the current schema"],
              accepted_risks=["irreversible data loss"]),
         None, None, Verdict.REQUEST_EVIDENCE),
        ("ambiguous-incomplete", dict(statement="refactor the module dependency",
                                      evidence=[Evidence(EvidenceType.UNKNOWN, "?")],
                                      discarded_alternatives=["x"]),
         None, None, Verdict.REQUEST_EVIDENCE),
    ]
    bad = []
    for name, kw, prec, plac, expect in scenarios:
        rec = review_decision(_obj(**kw), precedent=prec, placement=plac,
                              registry=reg, ts="t")
        if rec.verdict != expect:
            bad.append((name, rec.verdict.value if rec.verdict else None, expect.value))
    # precedent-reversal: a WARNING is cited on the record, decision still proceeds
    rev = review_decision(_obj(statement="use the code module", evidence=[_fact()]),
                          precedent={"verdict": "WARNING", "on_veto": False},
                          registry=reg, ts="t")
    reversal_ok = any(c.get("provider") == "arch-decision" for c in rev.cited_sources)
    if not bad and reversal_ok:
        _ok("V-DRK-FASE5", f"{len(scenarios)} scenarios + precedent-reversal citation")
    else:
        _fail("V-DRK-FASE5", f"mismatches={bad} reversal_cited={reversal_ok}")


# ----------------------------------------------------------------------------
# V-DRK-DCS -- confidence is derived and bounded; one-option caps low
# ----------------------------------------------------------------------------
def test_dcs():
    strong = compute_dcs(_obj(evidence=[_fact(), _fact()], options=["a", "b", "c"]))
    one_opt = compute_dcs(_obj(evidence=[_fact()], options=["a"]))
    if 0 <= strong <= 100 and 0 <= one_opt <= 35 and strong > one_opt:
        _ok("V-DRK-DCS", f"strong={strong} one-option-capped={one_opt}")
    else:
        _fail("V-DRK-DCS", f"strong={strong} one_opt={one_opt}")


def main() -> int:
    print("== DRK done-gate: tools/test_decision_review.py ==")
    for t in (test_reversibility, test_scope_l0, test_record_canonical,
              test_verdict_ontology, test_block_gate, test_failopen,
              test_accountability, test_attribution, test_three_bias,
              test_fase5_scenarios, test_dcs):
        t()
    total = _passes + _fails
    print(f"\nDRK_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
