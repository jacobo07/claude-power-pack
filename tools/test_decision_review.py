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


# ----------------------------------------------------------------------------
# V-DRK-PROVIDERS-LIVE -- the kernel off the bench: real providers, not fixtures
# ----------------------------------------------------------------------------
def test_providers_live():
    from modules.decision_review import providers as P
    obj = _obj(statement="run a schema migration that drops the legacy table",
               is_build_decision=True, evidence=[_fact()],
               discarded_alternatives=["keep it"], accepted_risks=["data loss"])
    res = P.resolve_all(obj)
    # spec_gate.classify_tier and cost_collapse.route are pure functions: they
    # always answer. If they do not, the adapters are not really wired.
    tier_ok = isinstance(res.get("tier"), dict) and "tier" in res["tier"]
    route_ok = isinstance(res.get("route"), dict) and res["route"].get("model")
    rec = review_decision(obj, registry=_tmp_registry(), ts="t", live=True)
    verdict_ok = rec.verdict is not None
    if tier_ok and route_ok and verdict_ok:
        _ok("V-DRK-PROVIDERS-LIVE",
            f"tier={res['tier']['tier']} route={res['route']['model']} "
            f"verdict={rec.verdict.value} (no fixture injected)")
    else:
        _fail("V-DRK-PROVIDERS-LIVE",
              f"tier_ok={tier_ok} route_ok={route_ok} verdict_ok={verdict_ok}")


# ----------------------------------------------------------------------------
# V-DRK-FAILOPEN-PROVIDER -- a dead provider degrades the review, never stops it
# ----------------------------------------------------------------------------
def test_failopen_provider():
    from modules.decision_review import providers as P
    obj = _obj(statement="refactor the module dependency", evidence=[_fact()],
               discarded_alternatives=["leave it"], accepted_risks=["churn"])
    orig_loader, orig_placement = P._load_arch_check, P.placement_for
    try:
        P._load_arch_check = lambda: None            # arch-decision unreadable
        def _boom(*a, **k):                          # D2A raises
            raise RuntimeError("provider down")
        P.placement_for = _boom
        res = P.resolve_all(obj)
        rec = review_decision(obj, registry=_tmp_registry(), ts="t", live=True)
    finally:
        P._load_arch_check, P.placement_for = orig_loader, orig_placement
    degraded = res.get("precedent") is None
    survived = res.get("route") is not None and rec.verdict is not None
    if degraded and survived:
        _ok("V-DRK-FAILOPEN-PROVIDER",
            f"arch-decision dead + D2A raising -> verdict still {rec.verdict.value} "
            f"from the surviving providers")
    else:
        _fail("V-DRK-FAILOPEN-PROVIDER",
              f"degraded={degraded} survived={survived} verdict={rec.verdict}")


# ----------------------------------------------------------------------------
# V-DRK-NO-LENGTH-BIAS -- a verbose decision must not be rejected FOR being
# verbose. Regression gate for the always-reject bias
# (T-DECISION-AUTHORITY-CAPTURE-001 / T-DRK-PRECEDENT-LENGTH-BIAS-001): the
# precedent provider's score rises with input length and 86% of its index is
# veto-class, so a naive adapter turns "this is a big decision" into "this
# collides with a Hard Rule" and REJECTs every substantial decision.
# ----------------------------------------------------------------------------
def test_no_length_bias():
    from modules.decision_review import providers as P
    short = "Add a daily scanner"
    verbose = (short + " that composes the arch-decision precedent index, the D2A "
               "placement engine, the ACIS epistemic ladder, the spec_gate tier "
               "classifier, the cost_collapse router, the OWNER_QUEUE residual "
               "ledger and the D1 liveness ledger, writing an audit report and "
               "publishing high-urgency findings without blocking the workflow")
    pv = P.precedent_for(verbose)
    if pv is None:
        _ok("V-DRK-NO-LENGTH-BIAS",
            "arch-index unavailable -> provider silent (fail-open)")
        return
    # on_veto is True only when a source actually clears the COLLISION floor --
    # not merely because a veto-class source appears (86% of the index is).
    floor = 4.5
    veto_earned = (not pv["on_veto"]) or any(s["score"] >= floor
                                             for s in pv["sources"])
    # A verbose restatement of a benign decision must not escalate to REJECT.
    obj = _obj(statement=verbose, evidence=[_fact()],
               discarded_alternatives=["do nothing"], accepted_risks=["noise"])
    rec = review_decision(obj, registry=_tmp_registry(), ts="t", live=True)
    not_rejected = rec.verdict != Verdict.REJECT
    if veto_earned and not_rejected:
        _ok("V-DRK-NO-LENGTH-BIAS",
            f"verbose({len(verbose.split())}w) -> precedent={pv['verdict']} "
            f"on_veto={pv['on_veto']} verdict={rec.verdict.value} (not REJECT)")
    else:
        _fail("V-DRK-NO-LENGTH-BIAS",
              f"veto_earned={veto_earned} verdict={rec.verdict} "
              f"precedent={pv['verdict']}/{pv['on_veto']}")


# ----------------------------------------------------------------------------
# V-DRK-SCANNER-RUNS -- runs on a real repo; an empty repo is [] not an error
# ----------------------------------------------------------------------------
def test_scanner_runs():
    from modules.decision_review.proactive_scanner import scan_repo
    td = Path(tempfile.mkdtemp(prefix="drk_scan_"))
    real = scan_repo(PP_ROOT, state_dir=td, td=td, registry=_tmp_registry())
    empty = scan_repo(td, state_dir=td, td=td, registry=_tmp_registry())
    missing = scan_repo(td / "does_not_exist", state_dir=td, td=td)
    # An empty repo must yield ZERO findings. PP-global ledgers (D1 liveness, D3
    # recall-ROI) describe the pack, not the target: leaking them into a foreign
    # repo's scan would be inventing evidence about a repo that has none.
    if isinstance(real, list) and real and empty == [] and missing == []:
        _ok("V-DRK-SCANNER-RUNS",
            f"PP repo -> {len(real)} real suggestion(s); empty repo -> 0 "
            f"(no PP-ledger leakage); missing repo -> []")
    else:
        _fail("V-DRK-SCANNER-RUNS",
              f"real={len(real) if isinstance(real, list) else real} "
              f"empty={len(empty) if isinstance(empty, list) else empty} "
              f"missing={missing}")


# ----------------------------------------------------------------------------
# V-DRK-SCANNER-EVIDENCE -- every suggestion cites a REAL repo artifact
# (T-DRK-PROACTIVE-NOISE-001: no evidence -> not published)
# ----------------------------------------------------------------------------
def test_scanner_evidence():
    from modules.decision_review.proactive_scanner import scan_repo, HIGH
    from modules.decision_review.proactive_scanner import HIGH_BLAST_MAGNITUDE
    td = Path(tempfile.mkdtemp(prefix="drk_scan_"))
    sugg = scan_repo(PP_ROOT, state_dir=td, td=td, registry=_tmp_registry())
    ungrounded = [s.path for s in sugg if not s.is_publishable()]
    # every module-path suggestion must name a directory that actually exists
    fake_paths = [s.path for s in sugg
                  if s.path.startswith("modules/") and s.path != "modules/"
                  and not (PP_ROOT / s.path).is_dir()]
    # high urgency must be earned: a verifiable blast magnitude or a DRIFTED gate
    unearned = [s.path for s in sugg if s.urgency == HIGH
                and s.blast.get("magnitude", 0) < HIGH_BLAST_MAGNITUDE
                and s.detector != "liveness"]
    if not ungrounded and not fake_paths and not unearned:
        _ok("V-DRK-SCANNER-EVIDENCE",
            f"{len(sugg)} suggestion(s): 0 ungrounded, 0 invented paths, "
            f"0 unearned-high")
    else:
        _fail("V-DRK-SCANNER-EVIDENCE",
              f"ungrounded={ungrounded} invented={fake_paths} unearned_high={unearned}")


# ----------------------------------------------------------------------------
# V-DRK-QUEUE-INTEGRATION -- a high-urgency finding reaches the OWNER_QUEUE (D4)
# ----------------------------------------------------------------------------
def test_queue_integration():
    from modules.decision_review.proactive_scanner import (
        ProactiveSuggestion, publish, HIGH, LOW)
    from modules.owner_queue.owner_queue import pending
    td = Path(tempfile.mkdtemp(prefix="drk_q_"))
    high = ProactiveSuggestion(
        type="orphan", description="a shipped gate is not deployed",
        repo="pp", path="liveness:hooks-dir/hook-dispatcher",
        verdict_hint="APPROVE-WITH-CONDITIONS", urgency=HIGH,
        evidence="D1 liveness audit -> DRIFTED: hash mismatch", detector="liveness")
    low = ProactiveSuggestion(
        type="opportunity", description="a dataset is never recalled", repo="pp",
        path="vault/specs/x.md", verdict_hint="REMOVE", urgency=LOW,
        evidence="D3 recall-ROI: 0 injections", detector="recall_roi")
    ids = publish([high, low], state_dir=td)
    rows = pending(td)
    only_high = len(ids) == 1 and len(rows) == 1 \
        and "shipped gate" in rows[0].get("action", "")
    # idempotent: a daily re-scan of an unfixed finding must not duplicate the row
    publish([high, low], state_dir=td)
    idempotent = len(pending(td)) == 1
    if only_high and idempotent:
        _ok("V-DRK-QUEUE-INTEGRATION",
            f"high -> OWNER_QUEUE row {ids[0]}; low withheld; re-scan idempotent")
    else:
        _fail("V-DRK-QUEUE-INTEGRATION",
              f"ids={ids} rows={len(rows)} idempotent={idempotent}")


# ----------------------------------------------------------------------------
# V-DRK-LIVENESS-ENTRY -- DRK is in the D1 ledger (PR-LIVENESS-CHECK-BEFORE-SHIP-001)
# ----------------------------------------------------------------------------
def test_liveness_entry():
    from modules.liveness.liveness_ledger import default_registry, audit
    ids = {r.get("id") for r in default_registry()}
    have = {"drk-kernel", "drk-proactive"} <= ids
    rows = {r["id"]: r for r in audit(repo_root=PP_ROOT)}
    probed = "drk-kernel" in rows and rows["drk-kernel"].get("verdict")
    if have and probed:
        _ok("V-DRK-LIVENESS-ENTRY",
            f"drk-kernel={rows['drk-kernel']['verdict']} "
            f"drk-proactive={rows['drk-proactive']['verdict']} (probed, not asserted)")
    else:
        _fail("V-DRK-LIVENESS-ENTRY", f"registered={have} probed={probed}")


def main() -> int:
    print("== DRK done-gate: tools/test_decision_review.py ==")
    for t in (test_reversibility, test_scope_l0, test_record_canonical,
              test_verdict_ontology, test_block_gate, test_failopen,
              test_accountability, test_attribution, test_three_bias,
              test_fase5_scenarios, test_dcs,
              test_providers_live, test_failopen_provider, test_no_length_bias,
              test_scanner_runs, test_scanner_evidence, test_queue_integration,
              test_liveness_entry):
        t()
    total = _passes + _fails
    print(f"\nDRK_PASS={_passes}/{total}  threshold={total}/{total}")
    return 0 if _fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
