#!/usr/bin/env python3
"""Evidence-governed transition, and a closure projection that can say no.

Two separate questions, deliberately not merged:

  * may THIS obligation move to SATISFIED?  -> `evaluate_transition`
  * may the MISSION close?                  -> `project_closure`

WORKER NARRATIVE IS NOT AUTHORITY. An executor reporting that it finished is a
claim about itself. The only thing that moves an obligation to SATISFIED here is
a verdict produced by a gate that ran -- carrying the gate's identity, its exit
status and what it observed. A report with no verdict is not weak evidence; it
is evidence of nothing, and it is refused with a different reason from a verdict
that failed, because those need different fixes.

This module does not replace the Done Gate, the strength ladder or Production
Reality, and it does not own a phase. It asks WHAT PROOF IS REQUIRED and reads
the answer the gate gives. GSD decides what the mission's phase is; this decides
whether a derived obligation has earned its state.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .obligation import (ACCEPTED, CANDIDATE, DEFERRED, NOT_APPLICABLE,
                         REJECTED, SATISFIED, STALE, Obligation)

# Transition outcomes. Three, never two: "refused" and "could not judge" are
# different facts about the world and only one of them is about the obligation.
ALLOWED = "ALLOWED"
REFUSED = "REFUSED"
UNJUDGEABLE = "UNJUDGEABLE"


@dataclass(frozen=True)
class Verdict:
    """What a gate that actually ran produced.

    The trailing fields are optional and unused by the mission path. The goal
    spine requires them: a verdict it cannot tie to a tree, a revision, a
    class of gate and the exact gate files that ran cannot tell a local unit
    test from a live check, nor evidence about today's tree from last week's.
    """
    gate: str
    exit_status: int
    observed: str
    tree_hash: str = ""
    revision: str = ""
    gate_class: str = ""
    gate_pin: tuple = ()          # ((path, sha256), ...) of the gate files that ran

    @property
    def passed(self) -> bool:
        return self.exit_status == 0


@dataclass(frozen=True)
class TransitionResult:
    outcome: str
    reason: str

    @property
    def allowed(self) -> bool:
        return self.outcome == ALLOWED


def evaluate_transition(ob: Obligation, verdict: Verdict | None,
                        narrative: str | None = None) -> TransitionResult:
    """Decide whether `ob` may move to SATISFIED.

    `narrative` exists in this signature on purpose: the executor's own account
    is accepted as INPUT and is never consulted as AUTHORITY. Leaving the
    parameter out would hide the decision; taking it and ignoring it makes the
    refusal explicit and testable.
    """
    if ob.disposition in (REJECTED, NOT_APPLICABLE, DEFERRED):
        return TransitionResult(REFUSED,
                                f"{ob.identifier} is {ob.disposition}; it has no "
                                "satisfied state to reach")
    if ob.disposition == STALE:
        return TransitionResult(REFUSED,
                                f"{ob.identifier} is STALE -- its causal parent no "
                                "longer holds, so proving it proves nothing")
    if ob.disposition == CANDIDATE:
        return TransitionResult(REFUSED,
                                f"{ob.identifier} has not been judged material; a "
                                "candidate is not work and cannot be completed")
    if not ob.done_gate.strip():
        return TransitionResult(UNJUDGEABLE,
                                f"{ob.identifier} names no done gate, so no "
                                "observation could settle it")
    if verdict is None:
        extra = (" The executor reported completion; that is a claim about "
                 "itself and is not evidence.") if narrative else ""
        return TransitionResult(REFUSED,
                                f"{ob.identifier} requires {ob.done_gate!r} and no "
                                f"gate verdict was supplied.{extra}")
    if not verdict.passed:
        return TransitionResult(REFUSED,
                                f"{ob.identifier}: {verdict.gate} ran and returned "
                                f"{verdict.exit_status} -- {verdict.observed}")
    return TransitionResult(ALLOWED,
                            f"{ob.identifier}: {verdict.gate} observed "
                            f"{verdict.observed!r}")


def satisfy(ob: Obligation, verdict: Verdict | None,
            narrative: str | None = None) -> tuple[Obligation, TransitionResult]:
    res = evaluate_transition(ob, verdict, narrative)
    if res.allowed:
        ob.disposition = SATISFIED
        ob.disposition_reason = res.reason
    return ob, res


# --- evidence blindness ------------------------------------------------------
# What the fact source could NOT say. Until this existed, a fact that could not
# be measured was simply absent from the list the operators read, `_has()`
# returned False, no obligation was derived, and `project_closure` -- which can
# only block on obligations that EXIST -- reported ALLOWED. So "we measured it
# and it does not hold" and "we could not measure it" produced a byte-identical
# receipt, which is the defect this whole wave exists to close.
#
# UNMEASURED is a distinct source, not an empty Blindness. A receipt built
# without consulting any facts document and one built from a document with
# nothing unknown are different claims about the world, and collapsing them
# would commit, inside this module's own artifact, exactly the error it exists
# to prevent.

UNMEASURED = "unmeasured"


@dataclass(frozen=True)
class Blindness:
    """Facts the source could not establish, split by whether they matter.

    GATING names decide whether an obligation exists, so an unknown one means
    nobody can say what the mission owes. ENRICHING names only extend an
    obligation that already exists; an unknown one costs a sentence of
    explanation, never a verdict, and must not hold a wave.
    """
    source: str = UNMEASURED
    gating_unknown: tuple = ()
    enriching_unknown: tuple = ()
    gating_stale: tuple = ()
    enriching_stale: tuple = ()

    @property
    def measured(self) -> bool:
        return self.source != UNMEASURED

    @property
    def blocks(self) -> bool:
        return bool(self.gating_unknown or self.gating_stale)

    @property
    def disclosures(self) -> list[str]:
        """Everything worth SAYING that is not worth BLOCKING for."""
        out = []
        for n in self.enriching_unknown:
            out.append(f"{n} could not be measured; it only enriches an "
                       "obligation, so no verdict changed")
        for n in self.enriching_stale:
            out.append(f"{n} was computed from a source that has since changed; "
                       "it only enriches an obligation, so no verdict changed")
        return out


# --- closure ----------------------------------------------------------------

@dataclass
class Closure:
    may_close: bool
    blocking: list[str] = field(default_factory=list)
    explicit_requirements: list[str] = field(default_factory=list)
    derived_accepted: list[dict] = field(default_factory=list)
    derived_dispositioned: list[dict] = field(default_factory=list)
    residual_risk: list[str] = field(default_factory=list)
    production_reality: str = ""
    blindness: Blindness = field(default_factory=Blindness)

    def render(self) -> str:
        out = [f"MISSION CLOSURE: {'ALLOWED' if self.may_close else 'DENIED'}", ""]
        out.append("EXPLICIT (stated by the human)")
        out += [f"  - {r}" for r in self.explicit_requirements] or ["  (none)"]
        out.append("")
        out.append("DERIVED, REQUIRED")
        out += [f"  - [{d['disposition']}] {d['id']}: {d['text'][:88]}"
                for d in self.derived_accepted] or ["  (none)"]
        out.append("")
        out.append("DERIVED, DISPOSITIONED WITHOUT BECOMING WORK")
        out += [f"  - [{d['disposition']}] {d['id']}: {d['disposition_reason'][:76]}"
                for d in self.derived_dispositioned] or ["  (none)"]
        # Rendered ALWAYS, including when nothing is blind. A receipt that only
        # mentions blindness when it exists cannot distinguish "the facts were
        # read and nothing was unknown" from "no facts were ever consulted",
        # and that is the same collapse this section exists to undo.
        bl = self.blindness
        out += ["", f"EVIDENCE BLINDNESS (source: {bl.source})"]
        if not bl.measured:
            out.append("  - no facts document was consulted; this receipt says "
                       "nothing about what could not be measured")
        else:
            rows = ([f"  - UNKNOWN, gating: {n}" for n in bl.gating_unknown]
                    + [f"  - STALE, gating: {n}" for n in bl.gating_stale]
                    + [f"  - UNKNOWN, enriching only: {n}"
                       for n in bl.enriching_unknown]
                    + [f"  - STALE, enriching only: {n}"
                       for n in bl.enriching_stale])
            out += rows or ["  - nothing unknown, nothing stale"]
        if self.blocking:
            out += ["", "BLOCKING"] + [f"  - {b}" for b in self.blocking]
        if self.residual_risk:
            out += ["", "RESIDUAL RISK"] + [f"  - {r}" for r in self.residual_risk]
        out += ["", f"PRODUCTION REALITY: {self.production_reality}"]
        return "\n".join(out)


def project_closure(contract, obligations: list[Obligation],
                    explicit_backlog_empty: bool,
                    production_reality: str = "UNPROVEN",
                    blindness: Blindness | None = None) -> Closure:
    """Compile a closure receipt from what the owners already hold.

    This is a PROJECTION. It stores nothing and it is not consulted as truth by
    anything else -- re-running it after the facts move produces a different
    answer, which is the property a second ledger would destroy.

    The load-bearing rule: an empty explicit backlog does not authorise
    closure. That is the whole point. A mission whose stated tasks are all done
    and whose derived material obligation is open is NOT complete, and saying so
    is the difference between a plan the human remembered to write and the
    engineering the work actually required.
    """
    accepted = [o for o in obligations if o.disposition == ACCEPTED]
    stale = [o for o in obligations if o.disposition == STALE]
    satisfied = [o for o in obligations if o.disposition == SATISFIED]
    closed_out = [o for o in obligations
                  if o.disposition in (REJECTED, NOT_APPLICABLE, DEFERRED)]
    candidates = [o for o in obligations if o.disposition == CANDIDATE]

    blocking: list[str] = []
    if not explicit_backlog_empty:
        blocking.append("explicit backlog is not empty")
    for o in accepted:
        blocking.append(f"{o.identifier} is ACCEPTED and unproven -- "
                        f"requires {o.done_gate!r}")
    for o in stale:
        blocking.append(f"{o.identifier} is STALE and undispositioned -- a parent "
                        "stopped holding and nobody decided what that means")
    for o in candidates:
        blocking.append(f"{o.identifier} is still CANDIDATE -- never judged")

    # THE ABSENCE THAT USED TO BE SILENT. A gating fact nobody could measure
    # derives no obligation, so without these two loops there is nothing in
    # `blocking` to find and this projection reports ALLOWED -- over a mission
    # whose requirements are simply unknown. Absence of evidence is not
    # evidence that no obligation is owed.
    bl = blindness if blindness is not None else Blindness()
    for n in bl.gating_unknown:
        blocking.append(
            f"fact {n!r} could not be measured, and an operator gates on it -- "
            "no obligation was derived from it, and that is not evidence that "
            "none is required")
    for n in bl.gating_stale:
        blocking.append(
            f"fact {n!r} was computed from a source that has since changed or "
            "can no longer be read, and an operator gates on it -- it cannot "
            "serve as current proof until it is reproduced")

    residual = [f"{o.identifier} deferred: {o.disposition_reason}"
                + (f" (revisit when {o.revisit_when})" if o.revisit_when else "")
                for o in obligations if o.disposition == DEFERRED]

    # The human's own words, verbatim and unsplit. An earlier version broke the
    # intent on " and " to produce a requirement list, which read well and was a
    # fabrication: prose does not decompose into requirements on a conjunction,
    # and a receipt that invents structure the human never wrote is lying about
    # the one thing it exists to report faithfully. Deriving requirements from
    # intent is what the operators do, with provenance; this field is the raw
    # sentence so a reader can always see what was actually asked for.
    intent = (contract.value("human_intent") or "").strip()
    explicit = [" ".join(intent.split())] if intent else []

    return Closure(
        may_close=not blocking,
        blocking=blocking,
        explicit_requirements=explicit,
        derived_accepted=[o.to_dict() for o in accepted + satisfied + stale],
        derived_dispositioned=[o.to_dict() for o in closed_out],
        residual_risk=residual,
        production_reality=production_reality,
        blindness=bl,
    )
