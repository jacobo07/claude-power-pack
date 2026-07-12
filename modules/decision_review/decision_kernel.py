"""decision_kernel.py -- the nine-stage review sieve (DRK-01).

review_decision(obj) carries a candidate decision from proposal to recorded
verdict: scope-test -> instantiate -> classify -> route -> evidence/burden ->
precedent -> placement -> adversarial -> verdict/record. It emits exactly one
of the ten verdicts (DRK-00 II.2) and writes an append-only Decision Record.

Composition without unverified signatures (HR-PREMISE-001): the kernel consumes
already-computed *provider verdicts* injected by the caller --
  precedent = {"verdict": "COLLISION"|"WARNING"|"CLEAR", "on_veto": bool}
  placement = {"operation": "CONSOLIDATE"|"KEEP_LOCAL"|"REMOVE"|..., "coverage": float}
so the doctrine's composition (arch-decision precedent, D2A placement, ACIS
evidence levels) is real and testable here; the thin live adapters that call
those modules are wired separately once their signatures are verified.

Block-narrow (DRK-01 III.2, PR-DECISION-AUTHORITY-LIMITS-001): the kernel BLOCKS
only at L4 under Tipo-C AND max-evidence-level < ACIS E3. Everywhere else it
recommends. Fail-open: any internal failure yields a DEFER record, never a raise
and never a silent APPROVE.

Stdlib only. No hardcoded absolute paths (E11).
"""
from __future__ import annotations

import re

from .decision_record import (
    DecisionObject,
    DecisionRecord,
    EvidenceType,
    Reversibility,
    ReviewTier,
    Verdict,
    Registry,
)

# --- ACIS evidence-level threshold that satisfies a high burden ---
ACIS_E3 = 3

# --- marker vocabularies (deterministic classifiers) ---
# Tipo-C: practically irreversible surfaces.
_TIPO_C = re.compile(
    r"\b(schema|migration|public\s+api|public\s+contract|delete[sd]?|drop(?:ped|s)?|"
    r"purge|irreversible|one[-\s]way|production\s+data|data\s+loss|rename[sd]?|"
    r"breaking\s+change|deprecat)\w*", re.IGNORECASE)
# Tipo-B: hard-to-undo-but-possible.
_TIPO_B = re.compile(
    r"\b(refactor|dependency|dependencies|config|contract|interface|protocol|"
    r"format|api|integration|coupl)\w*", re.IGNORECASE)

# Blast-radius surfaces (DRK-02 nine surfaces).
_SURFACES = {
    "code": re.compile(r"\b(code|module|function|class|file)\w*", re.IGNORECASE),
    "users": re.compile(r"\b(user|customer|player|audience)\w*", re.IGNORECASE),
    "cost": re.compile(r"\b(cost|token|budget|spend|price|bill)\w*", re.IGNORECASE),
    "infra": re.compile(r"\b(infra|infrastructure|server|deploy|host|database|db)\w*", re.IGNORECASE),
    "roadmap": re.compile(r"\b(roadmap|milestone|release|sprint)\w*", re.IGNORECASE),
    "operations": re.compile(r"\b(operation|ops|monitor|reliab|uptime)\w*", re.IGNORECASE),
    "agents": re.compile(r"\b(agent|subagent|hook|daemon)\w*", re.IGNORECASE),
    "workflows": re.compile(r"\b(workflow|pipeline|process|flow)\w*", re.IGNORECASE),
    "data": re.compile(r"\b(data|record|schema|table|store)\w*", re.IGNORECASE),
}

# Identity / public-contract markers (an in-scope, tier-raising signal).
_IDENTITY = re.compile(
    r"\b(public\s+(api|contract|interface)|schema|data\s+model|user[-\s]visible|"
    r"name\s+(users|clients)|external\s+depend)\w*", re.IGNORECASE)


def _text_blob(obj: DecisionObject) -> str:
    parts = [obj.statement, obj.problem, obj.rationale,
             " ".join(obj.options), " ".join(obj.dependencies),
             " ".join(obj.accepted_risks)]
    return " \n ".join(p for p in parts if p)


def classify_reversibility(obj: DecisionObject) -> Reversibility:
    """Tipo A/B/C from surface markers (DRK-02 I). Highest match wins
    (max-not-sum; escalation, DRK-02)."""
    blob = _text_blob(obj)
    if _TIPO_C.search(blob):
        return Reversibility.C
    if _TIPO_B.search(blob):
        return Reversibility.B
    return Reversibility.A


def compute_blast_radius(obj: DecisionObject) -> dict:
    """Which of the nine surfaces the decision touches (DRK-02 II)."""
    blob = _text_blob(obj)
    hits = {name: bool(rx.search(blob)) for name, rx in _SURFACES.items()}
    magnitude = sum(1 for v in hits.values() if v)
    return {"surfaces": [k for k, v in hits.items() if v], "magnitude": magnitude}


def _max_evidence_level(obj: DecisionObject) -> int:
    levels = [e.acis_level for e in obj.evidence if e.acis_level is not None]
    return max(levels) if levels else 0


def compute_dcs(obj: DecisionObject) -> int:
    """Decision Confidence Score 0-100, DERIVED (DRK-00 II.4, DRK-03).

    Signals: strong-typed evidence count, alternatives explored (Default
    Suspicion Rule), assumption/unknown proportion, max ACIS level. A proxy
    that routes attention, never a certifier (anti-Goodhart)."""
    ev = obj.evidence
    if not ev:
        base = 10
    else:
        strong = sum(1 for e in ev if e.weight == "strong")
        weak_assume = sum(1 for e in ev
                          if e.type in (EvidenceType.ASSUMPTION, EvidenceType.UNKNOWN))
        strong_ratio = strong / len(ev)
        assume_ratio = weak_assume / len(ev)
        base = int(round(100 * (0.65 * strong_ratio + 0.35 * (1 - assume_ratio))))
    # ACIS level lifts confidence toward its ceiling.
    lvl = _max_evidence_level(obj)
    base = min(100, base + lvl * 3)
    # Alternatives explored: one-option decisions cap low (Default Suspicion Rule).
    # Applied LAST so evidence strength never lifts a one-option decision past
    # the cap -- exploring alternatives is a hard gate on confidence, not a factor.
    if len(obj.options) < 2:
        base = min(base, 35)
    elif len(obj.options) >= 3:
        base = min(100, base + 5)
    return max(0, min(100, base))


def in_scope(obj: DecisionObject, reversibility: Reversibility,
             blast: dict, precedent: dict | None) -> bool:
    """Stage 1 scope test (DRK-00 I.2). Crosses >=1 consequence threshold?"""
    if reversibility in (Reversibility.B, Reversibility.C):
        return True
    if blast.get("magnitude", 0) >= 1:
        return True
    if _IDENTITY.search(_text_blob(obj)):
        return True
    if precedent and precedent.get("verdict") in ("COLLISION", "WARNING"):
        return True
    # Evidence gap: an in-flight decision resting only on assumptions.
    if obj.evidence and all(e.type in (EvidenceType.ASSUMPTION, EvidenceType.UNKNOWN)
                            for e in obj.evidence):
        return True
    return False


def route_tier(obj: DecisionObject, reversibility: Reversibility,
               blast: dict) -> ReviewTier:
    """Map taxonomy maxima to a review tier (DRK-00 II.3)."""
    if reversibility == Reversibility.C or _IDENTITY.search(_text_blob(obj)) \
            or blast.get("magnitude", 0) >= 5:
        return ReviewTier.L4
    high_uncertainty = any(e.type == EvidenceType.UNKNOWN for e in obj.evidence)
    if reversibility == Reversibility.B and (blast.get("magnitude", 0) >= 3
                                             or high_uncertainty):
        return ReviewTier.L3
    if reversibility == Reversibility.B or blast.get("magnitude", 0) >= 1:
        return ReviewTier.L2
    return ReviewTier.L1


def evidence_burden_met(obj: DecisionObject, reversibility: Reversibility) -> bool:
    """DRK-03: burden scales with reversibility. Tipo A tolerates thin evidence;
    Tipo C demands >=1 strong item at ACIS >= E3."""
    strong = [e for e in obj.evidence if e.weight == "strong"]
    if reversibility == Reversibility.A:
        return True  # cheap to undo; low burden
    if reversibility == Reversibility.B:
        return len(strong) >= 1
    # Tipo C: strong evidence at ACIS >= E3.
    return any((e.acis_level or 0) >= ACIS_E3 for e in strong)


def _missing_evidence(obj: DecisionObject, reversibility: Reversibility) -> str:
    if reversibility == Reversibility.B:
        return "at least one strong-typed evidence item (fact/observed_evidence)"
    return ("at least one strong-typed evidence item re-derived to ACIS E3+ "
            "(a probe or a second substrate)")


def adversarial_pass(obj: DecisionObject) -> tuple[bool, str]:
    """DRK-01 III.1: default-refuted; the decision must survive.
    Returns (survives, reason_if_not)."""
    # Q2: ignores an obvious alternative?
    if len(obj.discarded_alternatives) == 0 and len(obj.options) >= 2:
        return False, "no discarded alternatives recorded; alternatives not genuinely weighed"
    # Q1/Q4: no accepted risks named on a consequential decision = under-considered.
    if not obj.accepted_risks:
        return False, "no accepted risks named; failure modes unconsidered"
    # Q3: predictions carry no observable -> cannot be scored (Parte VI).
    for p in obj.predicted_consequences:
        if isinstance(p, dict) and not p.get("observable"):
            return False, "a predicted consequence has no observable; unscorable"
    return True, ""


def _resolve_placement(placement: dict | None) -> Verdict | None:
    if not placement:
        return None
    op = (placement.get("operation") or "").upper()
    mapping = {
        "CONSOLIDATE": Verdict.CONSOLIDATE,
        "KEEP_LOCAL": Verdict.KEEP_LOCAL,
        "KEEP-LOCAL": Verdict.KEEP_LOCAL,
        "REMOVE": Verdict.REMOVE,
        "RETIRE": Verdict.REMOVE,
        "DO_NOT_BUILD": Verdict.REMOVE,
    }
    return mapping.get(op)


# Verdict precedence (DRK-01 I.3), most-restrictive first.
def _resolve_knowledge(knowledge: dict | None) -> Verdict | None:
    """DFP knowledge-sufficiency provider (amendment 2026-07-12).

    Maps the Dataset First Protocol's ProjectClass onto this kernel's ontology. Only
    DATASET_FIRST_MANDATORY produces a distinct verdict -- the other three classes already
    have homes here, and minting synonyms for them would be the parallel-verdict-space
    failure that the amendment exists to avoid.
    """
    if not knowledge:
        return None
    cls = (knowledge.get("project_class") or "").upper()
    mapping = {
        "DATASET_FIRST_MANDATORY": Verdict.BUILD_KNOWLEDGE_FIRST,
        "EXPERIMENT_FIRST": Verdict.RUN_EXPERIMENT,      # already ours
        "HYBRID": Verdict.APPROVE_WITH_CONDITIONS,       # already ours
    }
    return mapping.get(cls)


def _resolve_knowledge_live(obj: DecisionObject) -> dict | None:
    """Ask the real DFP engine whether the governing science exists. Statement-only input
    (T-DRK-PRECEDENT-LENGTH-BIAS-001: never feed an adapter a long blob whose score rises
    with length). Lazy import + fail-open: no DFP is not a failure, it is silence."""
    try:
        from modules.dataset_first.knowledge_sufficiency import evaluate
        rev = getattr(getattr(obj, "reversibility", None), "value", None)
        v = evaluate(str(getattr(obj, "statement", "") or ""),
                     reversibility=rev if rev in ("A", "B", "C") else None)
        return {"project_class": v.verdict, "missing": list(v.missing),
                "score": v.score, "confidence": v.confidence}
    except Exception:  # noqa: BLE001 -- fail-open ABSOLUTE
        return None


# Ordered by severity, FIRST MATCH WINS. BUILD_KNOWLEDGE_FIRST sits AFTER RUN_EXPERIMENT
# on purpose: when both fire, the cheaper remedy wins, because a two-hour probe that would
# settle the question beats demanding a corpus (DFP-00 IV.7 -- a tie resolves to the
# cheaper class, since inflation always disguises itself as thoroughness).
_PRECEDENCE = [
    Verdict.REJECT, Verdict.REFRAME, Verdict.REQUEST_EVIDENCE,
    Verdict.RUN_EXPERIMENT, Verdict.BUILD_KNOWLEDGE_FIRST,
    Verdict.CONSOLIDATE, Verdict.KEEP_LOCAL,
    Verdict.REMOVE, Verdict.DEFER, Verdict.APPROVE_WITH_CONDITIONS,
    Verdict.APPROVE,
]


def _highest_precedence(candidates: list[Verdict]) -> Verdict:
    for v in _PRECEDENCE:
        if v in candidates:
            return v
    return Verdict.DEFER


def _resolve_live(obj: DecisionObject) -> dict:
    """Ask the real providers (arch-decision / D2A / ACIS ladder / spec_gate /
    cost_collapse) for their verdicts. Imported lazily so the kernel keeps working
    -- with injected fixtures -- even if a provider module is absent or broken.
    Fail-open: an unavailable provider layer yields no inputs, never an error."""
    try:
        from . import providers
        return providers.resolve_all(obj)
    except Exception:  # noqa: BLE001 -- fail-open: no providers is not a failure
        return {}


def review_decision(obj: DecisionObject, *, precedent: dict | None = None,
                    placement: dict | None = None,
                    knowledge: dict | None = None,
                    registry: Registry | None = None,
                    ts: str = "", live: bool = False) -> DecisionRecord:
    """The nine-stage sieve. Returns a DecisionRecord; writes it at L1+.

    Provider inputs (`precedent`, `placement`, `knowledge`) may be injected by the
    caller -- which is what the test suite does, keeping every gate hermetic -- or
    resolved from the real sealed modules by passing `live=True`
    (providers.resolve_all). Injection always wins: an explicitly-passed provider is
    never overwritten by a live lookup, so a fixture can pin any branch.

    `knowledge` is the DFP provider (amendment 2026-07-12): a dict carrying
    `project_class` and `missing`. It is what makes BUILD-KNOWLEDGE-FIRST reachable;
    without a producer the eleventh verdict would be dead by starvation.

    Fail-open: any exception yields a DEFER record, and a provider that cannot
    answer contributes nothing rather than a wrong answer.
    """
    reg = registry if registry is not None else Registry()
    try:
        if live:
            resolved = _resolve_live(obj)
            if precedent is None:
                precedent = resolved.get("precedent")
            if placement is None:
                placement = resolved.get("placement")
            if knowledge is None:
                knowledge = _resolve_knowledge_live(obj)

        # Stage 3 (partial): classify (needed for the scope test too).
        reversibility = classify_reversibility(obj)
        blast = compute_blast_radius(obj)

        # Stage 1: scope test.
        if not in_scope(obj, reversibility, blast, precedent):
            rec = DecisionRecord(obj=obj, ts=ts, tier=ReviewTier.L0,
                                 verdict=None)
            return rec  # L0: no verdict, no record written (DRK-00 II.3)

        # Stage 2: instantiate + record derived classification.
        obj.reversibility = reversibility
        obj.blast_radius = blast
        obj.confidence = compute_dcs(obj)
        guards: list[str] = []
        cited: list[dict] = []

        # Stage 4: route.
        tier = route_tier(obj, reversibility, blast)
        obj.review_tier = tier

        candidates: list[Verdict] = []
        conditions: list[str] = []

        # L1: record only.
        if tier == ReviewTier.L1:
            verdict = Verdict.APPROVE
            rec = _finish(obj, reg, ts, tier, verdict, cited, guards,
                          conditions, blocked=False)
            return rec

        # Stage 5: evidence & burden (L2+).
        if not evidence_burden_met(obj, reversibility):
            candidates.append(Verdict.REQUEST_EVIDENCE)
            guards.append("burden-unmet:" + _missing_evidence(obj, reversibility))

        # Stage 6: precedent collision (injected).
        if precedent:
            cited.append({"provider": "arch-decision", **precedent})
            if precedent.get("verdict") == "COLLISION" and precedent.get("on_veto"):
                candidates.append(Verdict.REJECT)
                guards.append("precedent-collision-on-veto")

        # Stage 7: placement (build/capability decisions, injected).
        if obj.is_build_decision:
            pv = _resolve_placement(placement)
            if pv is not None:
                cited.append({"provider": "d2a", **(placement or {})})
                candidates.append(pv)

        # Stage 7b: knowledge sufficiency (DFP provider; amendment 2026-07-12).
        # Does the institutional science that must govern this build exist yet? DFP is an
        # ADVISOR here, never an authority -- it contributes a candidate verdict and this
        # kernel decides, under this kernel's precedence and override protocol.
        if obj.is_build_decision:
            kv = _resolve_knowledge(knowledge)
            if kv is not None:
                cited.append({"provider": "dfp", **(knowledge or {})})
                candidates.append(kv)
                if kv == Verdict.BUILD_KNOWLEDGE_FIRST:
                    missing = ",".join((knowledge or {}).get("missing", []))
                    guards.append("knowledge-absent:" + (missing or "unnamed"))

        # Stage 8: adversarial pass (L3+).
        if tier in (ReviewTier.L3, ReviewTier.L4):
            survives, why = adversarial_pass(obj)
            if not survives:
                guards.append("adversarial-fail:" + why)
                # route by why: unscorable prediction -> REQUEST-EVIDENCE;
                # ignored alternative -> REFRAME; else RUN-EXPERIMENT.
                if "observable" in why:
                    candidates.append(Verdict.REQUEST_EVIDENCE)
                elif "alternative" in why:
                    candidates.append(Verdict.REFRAME)
                else:
                    candidates.append(Verdict.RUN_EXPERIMENT)

        # Stage 9: verdict.
        if candidates:
            verdict = _highest_precedence(candidates)
        else:
            # No objection. Conditions bind an APPROVE-WITH-CONDITIONS when the
            # decision is B/C but adequately evidenced, or has open predictions.
            if reversibility in (Reversibility.B, Reversibility.C):
                verdict = Verdict.APPROVE_WITH_CONDITIONS
                conditions.append("re-review at each predicted-consequence horizon")
                if reversibility == Reversibility.C:
                    conditions.append("rollback path required before action")
            else:
                verdict = Verdict.APPROVE

        # Block-gate (L4 twin-condition; PR-DECISION-AUTHORITY-LIMITS-001).
        blocked = False
        if tier == ReviewTier.L4 and reversibility == Reversibility.C \
                and _max_evidence_level(obj) < ACIS_E3:
            blocked = True
            guards.append("BLOCK:tipo-c-and-evidence-below-E3")
            if verdict == Verdict.APPROVE:
                verdict = Verdict.REQUEST_EVIDENCE

        return _finish(obj, reg, ts, tier, verdict, cited, guards,
                       conditions, blocked=blocked)

    except Exception as exc:  # fail-open to DEFER (never raise)
        rec = DecisionRecord(obj=obj, ts=ts,
                             tier=getattr(obj, "review_tier", None),
                             verdict=Verdict.DEFER,
                             guards_fired=[f"fail-open:{type(exc).__name__}"])
        reg.append(rec)
        return rec


def _finish(obj, reg, ts, tier, verdict, cited, guards, conditions,
            *, blocked) -> DecisionRecord:
    obj.verdict = verdict
    rec = DecisionRecord(obj=obj, ts=ts, tier=tier, verdict=verdict,
                         cited_sources=cited, guards_fired=guards,
                         conditions=conditions, blocked=blocked)
    reg.append(rec)
    return rec
