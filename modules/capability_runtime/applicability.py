#!/usr/bin/env python3
"""applicability.py -- Capability Applicability Engine (CPP-APIR DS05).

Decides which capability contracts apply to a mission, and how strongly.

The three routers this estate already has each route the wrong object: skills
(`skill_router`), models (`cognitive_os/router`), task shape
(`spec_gate.classify_tier`). All three decide by keyword match. The source
document rejects that mechanism explicitly, so keyword overlap is ONE of six
benefit factors here, never the decision.

Ordering is load-bearing. The four blocking verdicts are DETERMINISTIC GATES
evaluated BEFORE any score, because a composite score must never be mapped onto
a hard conjunct -- a blocked capability that scores well is still blocked, and a
score threshold cannot express "the evidence does not exist".

  gate 1  anti-trigger hit          -> NOT_APPLICABLE
  gate 2  owner unresolved          -> BLOCKED_BY_UNRESOLVED_OWNER
  gate 3  required evidence absent  -> BLOCKED_BY_MISSING_EVIDENCE
  gate 4  scope already held        -> REJECTED_AS_DUPLICATE
  gate 5  runtime/prereq unmet      -> CAPABILITY_INSUFFICIENT

Only then does the score choose among MANDATORY / RECOMMENDED /
AVAILABLE_ON_TRIGGER / NOT_APPLICABLE.

Stdlib-only. Fail-open at the boundary: an unreadable contract set yields no
verdicts, never a crash.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.capability_runtime.contract import (  # noqa: E402
    COST_SCALE, FAILURE_SCALE, MATURITY_SCALE, CapabilityContract, Cost,
    FailureRisk, Maturity, load_contracts,
)


class Verdict(str, Enum):
    MANDATORY = "MANDATORY"
    RECOMMENDED = "RECOMMENDED"
    AVAILABLE_ON_TRIGGER = "AVAILABLE_ON_TRIGGER"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    CAPABILITY_INSUFFICIENT = "CAPABILITY_INSUFFICIENT"
    BLOCKED_BY_MISSING_EVIDENCE = "BLOCKED_BY_MISSING_EVIDENCE"
    BLOCKED_BY_UNRESOLVED_OWNER = "BLOCKED_BY_UNRESOLVED_OWNER"
    REJECTED_AS_DUPLICATE = "REJECTED_AS_DUPLICATE"


BLOCKING = frozenset({
    Verdict.CAPABILITY_INSUFFICIENT, Verdict.BLOCKED_BY_MISSING_EVIDENCE,
    Verdict.BLOCKED_BY_UNRESOLVED_OWNER, Verdict.REJECTED_AS_DUPLICATE,
})

MANDATORY_SCORE = 0.55
RECOMMENDED_SCORE = 0.35


@dataclass
class MissionContext:
    """What the runtime knows when it asks the question."""
    description: str = ""
    available_evidence: list = field(default_factory=list)
    runtime: str = ""
    resolved_owners: list = field(default_factory=list)
    satisfied_prerequisites: list = field(default_factory=list)
    held_scopes: list = field(default_factory=list)     # scopes already covered
    budget_pressure: bool = False


@dataclass
class Applicability:
    capability_id: str
    verdict: Verdict
    score: float
    reason: str
    escalates: bool = False
    factors: dict = field(default_factory=dict)

    @property
    def blocked(self) -> bool:
        return self.verdict in BLOCKING


def _norm(items) -> set:
    return {str(x).strip().lower() for x in (items or []) if str(x).strip()}


def _hits(text: str, phrases) -> list:
    """Word-boundary-anchored phrase presence. A naive substring test makes
    short tokens match unrelated words and destroys precision."""
    t = (text or "").lower()
    out = []
    for p in phrases or []:
        p = str(p).strip().lower()
        if p and re.search(r"\b" + re.escape(p) + r"\b", t):
            out.append(p)
    return out


def _ratio(part: int, whole: int, *, empty: float = 1.0) -> float:
    """Fraction satisfied. An EMPTY requirement is fully satisfied by
    definition -- stated explicitly so it is a decision, not an accident of
    an all([]) truth value."""
    return empty if whole == 0 else part / whole


def evaluate(c: CapabilityContract, ctx: MissionContext) -> Applicability:
    """One contract against one mission. Gates first, score second."""
    text = ctx.description or ""

    # --- gate 1: an anti-trigger is a veto, whatever else matches.
    anti = _hits(text, c.anti_triggers)
    if anti:
        return Applicability(c.id, Verdict.NOT_APPLICABLE, 0.0,
                             f"anti-trigger matched: {', '.join(anti)}")

    # --- gate 2: HR-APA-018. Only enforced when the caller supplies the set.
    if ctx.resolved_owners and c.owner.strip().lower() not in _norm(ctx.resolved_owners):
        return Applicability(c.id, Verdict.BLOCKED_BY_UNRESOLVED_OWNER, 0.0,
                             f"owner {c.owner!r} is not resolved in this project")

    # --- gate 3: evidence the capability cannot run without.
    need_ev, have_ev = _norm(c.required_evidence), _norm(ctx.available_evidence)
    missing_ev = sorted(need_ev - have_ev)
    if missing_ev:
        return Applicability(c.id, Verdict.BLOCKED_BY_MISSING_EVIDENCE, 0.0,
                             f"required evidence absent: {', '.join(missing_ev)}")

    # --- gate 4: HR-APA-011 at runtime. Scope already held by a live owner.
    dup = sorted(_norm(c.scope) & _norm(ctx.held_scopes))
    if dup:
        return Applicability(c.id, Verdict.REJECTED_AS_DUPLICATE, 0.0,
                             f"scope already held: {', '.join(dup)}")

    # --- gate 5: the capability exists but cannot serve this project as-is.
    if c.compatible_runtimes and ctx.runtime:
        if ctx.runtime.strip().lower() not in _norm(c.compatible_runtimes):
            return Applicability(c.id, Verdict.CAPABILITY_INSUFFICIENT, 0.0,
                                 f"runtime {ctx.runtime!r} not in compatible set")
    need_pre = _norm(c.prerequisites)
    missing_pre = sorted(need_pre - _norm(ctx.satisfied_prerequisites))
    if missing_pre:
        return Applicability(c.id, Verdict.CAPABILITY_INSUFFICIENT, 0.0,
                             f"prerequisites unmet: {', '.join(missing_pre)}")

    # --- scoring. Five benefit factors in [0,1], three cost penalties.
    # Compatibility is deliberately NOT a factor: gate 5 already rejects an
    # incompatible runtime, so any survivor scores 1.0 on it. A constant term
    # is not a factor, and a factor that cannot vary is decoration.
    trig = _hits(text, c.triggers)
    relevance = _ratio(len(trig), len(c.triggers or []), empty=0.0)
    # counterfactual term: what breaks if this capability is NOT activated.
    risk_reduction = FAILURE_SCALE[FailureRisk(c.failure_risk_if_omitted)] / 4.0
    leverage = COST_SCALE[Cost(c.expected_leverage)] / 3.0
    evidence = _ratio(len(need_ev & have_ev), len(need_ev))
    maturity_fit = MATURITY_SCALE[Maturity(c.maturity)] / 4.0

    benefit = (relevance * 0.30 + risk_reduction * 0.25 + leverage * 0.15
               + evidence * 0.15 + maturity_fit * 0.15)

    act = COST_SCALE[Cost(c.activation_cost)] / 3.0
    ctxc = COST_SCALE[Cost(c.context_cost)] / 3.0
    ops = COST_SCALE[Cost(c.operational_cost)] / 3.0
    penalty = act * 0.10 + ctxc * (0.15 if ctx.budget_pressure else 0.08) + ops * 0.05

    score = max(0.0, min(1.0, benefit - penalty))
    factors = {"relevance": round(relevance, 3),
               "risk_reduction": round(risk_reduction, 3),
               "leverage": round(leverage, 3), "evidence": round(evidence, 3),
               "maturity_fit": round(maturity_fit, 3),
               "penalty": round(penalty, 3)}

    high_stakes = FAILURE_SCALE[FailureRisk(c.failure_risk_if_omitted)] >= 3
    if score >= MANDATORY_SCORE and high_stakes:
        v, why = Verdict.MANDATORY, "high omission risk with a strong match"
    elif score >= RECOMMENDED_SCORE:
        v, why = Verdict.RECOMMENDED, "net benefit exceeds activation cost"
    elif trig:
        v, why = Verdict.AVAILABLE_ON_TRIGGER, "trigger matched, benefit marginal"
    else:
        v, why = Verdict.NOT_APPLICABLE, "no trigger matched and no standing risk"

    return Applicability(c.id, v, round(score, 3),
                         f"{why} (score={score:.2f})", c.escalates, factors)


def evaluate_all(ctx: MissionContext, contracts=None, contracts_dir=None) -> list:
    """Every contract against one mission, strongest first. Fail-open."""
    try:
        cs = contracts if contracts is not None else load_contracts(contracts_dir)
    except Exception:  # noqa: BLE001 -- a load error never blocks a mission
        return []
    order = {Verdict.MANDATORY: 0, Verdict.RECOMMENDED: 1,
             Verdict.AVAILABLE_ON_TRIGGER: 2}
    out = [evaluate(c, ctx) for c in cs]
    return sorted(out, key=lambda a: (order.get(a.verdict, 3), -a.score))


def compile_stack(ctx: MissionContext, contracts=None, contracts_dir=None) -> dict:
    """HR-APA-005: the MINIMUM sufficient capability stack.

    Activates MANDATORY + RECOMMENDED only. AVAILABLE_ON_TRIGGER stays dormant
    (HR-APA-014) and is reported, not loaded. Escalating capabilities are
    surfaced separately -- automatic activation grants no authority to change
    architecture or production (HR-APA-010).
    """
    results = evaluate_all(ctx, contracts, contracts_dir)
    activate = [a for a in results
                if a.verdict in (Verdict.MANDATORY, Verdict.RECOMMENDED)]
    return {
        "activate": [a.capability_id for a in activate],
        "escalate": [a.capability_id for a in activate if a.escalates],
        "dormant": [a.capability_id for a in results
                    if a.verdict == Verdict.AVAILABLE_ON_TRIGGER],
        "blocked": {a.capability_id: a.verdict.value
                    for a in results if a.blocked},
        "results": results,
    }


def main(argv=None) -> int:
    import argparse
    import json
    ap = argparse.ArgumentParser(description="Capability applicability engine")
    ap.add_argument("mission", nargs="*", help="mission description")
    ap.add_argument("--evidence", default="", help="comma-separated available evidence")
    ap.add_argument("--runtime", default="")
    ap.add_argument("--held-scopes", default="", help="comma-separated scopes already covered")
    ap.add_argument("--budget-pressure", action="store_true")
    ap.add_argument("--contracts-dir", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    def _split(s):
        return [x.strip() for x in (s or "").split(",") if x.strip()]

    ctx = MissionContext(description=" ".join(args.mission),
                         available_evidence=_split(args.evidence),
                         runtime=args.runtime,
                         held_scopes=_split(args.held_scopes),
                         budget_pressure=args.budget_pressure)
    stack = compile_stack(ctx, contracts_dir=args.contracts_dir)
    if args.json:
        print(json.dumps({k: v for k, v in stack.items() if k != "results"},
                         indent=2))
        return 0
    if not stack["results"]:
        print("no capability contracts found "
              f"(looked in {args.contracts_dir or 'vault/capability_runtime/contracts'})")
        return 0
    print(f"activate: {stack['activate'] or '(none)'}")
    if stack["escalate"]:
        print(f"  escalate to Owner (HR-APA-010): {stack['escalate']}")
    print(f"dormant:  {stack['dormant'] or '(none)'}")
    for cid, v in stack["blocked"].items():
        print(f"blocked:  {cid} -> {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
