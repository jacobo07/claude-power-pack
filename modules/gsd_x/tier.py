#!/usr/bin/env python3
"""The ExecutionOS Lite tier, measured instead of self-assessed.

Today the tier reaches the model as a constant string. `power-pack-reminder.js`
line 34 hands over `LIGHT | STANDARD | DEEP | FORENSIC. Default LIGHT.` from a
zero-argument function returning a constant array, and the model places itself
on that ladder. CLAUDE.md already seals the problem with that -- "Tier
self-assessment is NOT the gate (T-PP-SILENT-SKILL-001)" -- and the estate
already owns the thing that could decide it instead: an evidence-conditioned
applicability engine with five deterministic gates evaluated before any score.

The engine is reachable only when an operator types `/capability`. So this
module is not a new decider. It is the translation between a predicate that
exists and a vocabulary that is already on the wire.

WHY NO NEW VOCABULARY. The first design of this module invented
BYPASS/LIGHT/STANDARD/GSD_PHASE/MISSION. Two of those tokens already occupy the
same event with a different meaning (load depth, not mission weight), so the
model would have received one word carrying two ladders. REUSE precedes CREATE,
and the incumbent's ladder is the one the model is already told to use.

ABSTAIN IS NOT A TIER. A UserPromptSubmit hook holds a prompt string and nothing
else: no resolved owners, no gathered evidence, no runtime facts. So it must ask
the engine with those fields empty, and any capability that would otherwise
apply comes back BLOCKED_BY_MISSING_EVIDENCE or BLOCKED_BY_UNRESOLVED_OWNER.
Those four verdicts mean "wanted here and cannot run" -- they are a statement
about the asker, not about the mission's weight. Mapping them onto the low end
of the ladder would make silence look like a measured LIGHT; mapping them onto
the high end would fire on every build-shaped prompt. They get their own answer,
and it names the fact that was missing so the reader can supply it.

THE FLOOR IS REPORTED, NOT HIDDEN. When nothing matches, the answer is LIGHT --
which is exactly what the constant string already says. A run that returns LIGHT
by floor has added nothing, and `by_floor` says so, so the rate is measurable
rather than flattering. A tier engine that silently bottoms out on every prompt
is indistinguishable from the constant it replaced, and that is the failure this
module is most likely to have.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.capability_runtime.applicability import (  # noqa: E402
    Applicability, MissionContext, Verdict, evaluate_all,
)

# The incumbent ladder, spelled exactly as power-pack-reminder.js:34 spells it.
# Not re-ordered and not extended: if these strings drift from that line, the
# model receives two ladders and neither is authoritative.
LIGHT = "LIGHT"
STANDARD = "STANDARD"
DEEP = "DEEP"
FORENSIC = "FORENSIC"
ABSTAIN = "ABSTAIN"

LADDER = (LIGHT, STANDARD, DEEP, FORENSIC)


@dataclass
class TierVerdict:
    tier: str
    by_floor: bool = False
    drivers: list = field(default_factory=list)      # (capability_id, verdict)
    missing: list = field(default_factory=list)      # why we could not judge
    reason: str = ""

    @property
    def abstained(self) -> bool:
        return self.tier == ABSTAIN

    @property
    def informative(self) -> bool:
        """Did this run say anything the constant string does not already say?"""
        return not self.by_floor and not self.abstained


def classify(results: list) -> TierVerdict:
    """Applicability verdicts -> one tier. Gates first, counts second.

    Mirrors the engine's own ordering discipline: a blocking verdict is decided
    before any counting, because a composite count must never be mapped onto a
    hard conjunct.
    """
    if not results:
        return TierVerdict(
            LIGHT, by_floor=True,
            reason="no capability contract matched; floor answer, same as the "
                   "constant string",
        )

    applies = [r for r in results if not r.blocked]
    blocked = [r for r in results if r.blocked]

    mandatory = [r for r in applies if r.verdict is Verdict.MANDATORY]
    recommended = [r for r in applies if r.verdict is Verdict.RECOMMENDED]
    triggered = [r for r in applies if r.verdict is Verdict.AVAILABLE_ON_TRIGGER]
    positives = mandatory + recommended + triggered

    # Gate: something wanted to speak and could not, and nothing POSITIVE was
    # established. That is an absence of observation, not an observation of
    # absence.
    #
    # The obvious spelling of this gate -- `blocked and not applies` -- was
    # wrong, and measurably so. On a real repo prompt nine of ten contracts
    # returned BLOCKED_BY_MISSING_EVIDENCE while ONE returned NOT_APPLICABLE,
    # and that single dormant contract made `applies` non-empty and suppressed
    # the abstention the other nine had earned. NOT_APPLICABLE is not a positive
    # signal; it is a capability declining to speak. Only a positive verdict may
    # cancel an abstention.
    if blocked and not positives:
        missing = sorted({_missing_fact(r) for r in blocked})
        return TierVerdict(
            ABSTAIN,
            drivers=[(r.capability_id, r.verdict.value) for r in blocked],
            missing=missing,
            reason="capabilities matched but could not be evaluated: "
                   + "; ".join(missing),
        )

    if len(mandatory) >= 2:
        tier, driving = FORENSIC, mandatory
    elif len(mandatory) == 1:
        tier, driving = DEEP, mandatory
    elif recommended:
        tier, driving = STANDARD, recommended
    elif triggered:
        tier, driving = LIGHT, triggered
    else:
        return TierVerdict(
            LIGHT, by_floor=True,
            drivers=[(r.capability_id, r.verdict.value) for r in applies[:3]],
            reason="every matching capability resolved NOT_APPLICABLE; floor "
                   "answer, same as the constant string",
        )

    return TierVerdict(
        tier,
        drivers=[(r.capability_id, r.verdict.value) for r in driving],
        reason=f"{len(driving)} capability/ies at {driving[0].verdict.value}: "
               + ", ".join(r.capability_id for r in driving[:4]),
    )


def _missing_fact(r: Applicability) -> str:
    if r.verdict is Verdict.BLOCKED_BY_MISSING_EVIDENCE:
        return "required evidence was not gathered"
    if r.verdict is Verdict.BLOCKED_BY_UNRESOLVED_OWNER:
        return "the owner is unresolved"
    if r.verdict is Verdict.CAPABILITY_INSUFFICIENT:
        return "a runtime prerequisite is unmet"
    if r.verdict is Verdict.REJECTED_AS_DUPLICATE:
        return "the scope is already held"
    return "unknown blocking verdict"


def _silence_dormant(results: list, prompt: str, contracts, contracts_dir) -> list:
    """Drop blocked verdicts whose contract never matched the prompt.

    A blocked verdict means "this capability wanted to run and could not". That
    is only true if the capability was ADDRESSED. The engine's evidence gate is
    evaluated before its dormancy gate, so a contract whose triggers are absent
    from the prompt still comes back BLOCKED when its evidence is unmet -- and
    one contract in this estate (`cdicf-installer`) requires evidence no prompt
    can ever carry, so it is blocked on every prompt ever submitted.

    Left in, that single contract turns every ordinary prompt into ABSTAIN:
    measured, `que hora es` abstained. An abstention that fires on everything
    carries no information and trains the reader to ignore it, which is worse
    than the floor answer it replaced.

    So a blocked result survives only if its contract's own triggers hit the
    prompt, using the engine's word-boundary matcher rather than a second one.
    Non-blocking verdicts are never touched.

    CURRENTLY MASKED, DELIBERATELY KEPT (measured 2026-09-20). The Capability
    Runtime has since fixed the ordering at its source: gate 1 returns
    NOT_APPLICABLE for an untriggered contract BEFORE the evidence gate is
    reached, citing the same measured symptom this filter was written for. With
    upstream correct the engine yields blocked=0 on every prompt in every
    evidence configuration tested (['source','tests'], ['source'], []), so this
    function has nothing to filter and no test can observe it working.

    That makes it unreachable today, NOT dead. Driven with gate 1 disabled, the
    original defect returns exactly -- cdicf-installer comes back
    BLOCKED_BY_MISSING_EVIDENCE for `que hora es` -- and this filter removes it
    (blocked 1 -> 0). It is a live backstop against an upstream regression, which
    is why it stays.

    What it cannot repair is the tier: with dormancy off, every contract reaches
    scoring and the trivial prompt climbs to FORENSIC. That gap is observed by
    V-GSDX-TRIVIAL-CEILING, and the `ordering-reverted` mutation in
    tools/test_gsd_x_mutation.py is what proves both halves. The mutation that
    used to sit on THIS function was retired as equivalent: a mutant of
    unreachable code cannot change an observable, so scoring it as an uncaught
    regression measured nothing.
    """
    blocked = [r for r in results if r.blocked]
    if not blocked:
        return results
    try:
        from modules.capability_runtime.applicability import _hits
        from modules.capability_runtime.contract import load_contracts
        cs = contracts if contracts is not None else load_contracts(contracts_dir)
        triggers = {c.id: list(getattr(c, "triggers", []) or []) for c in cs}
    except Exception:                                 # noqa: BLE001
        return results        # cannot tell -> keep every blocked verdict
    kept = []
    for r in results:
        if not r.blocked:
            kept.append(r)
        elif _hits(prompt or "", triggers.get(r.capability_id, [])):
            kept.append(r)
    return kept


def observable_evidence(root: Path | None = None) -> list:
    """Evidence tokens this process can VERIFY, never ones it can assume.

    The contracts require named evidence -- `source`, `tests`. Those are facts
    about the working tree, and a hook can check them: either there are source
    files under the root or there are not. Supplying a token because it is
    plausible would manufacture exactly the confidence this module exists to
    avoid; supplying one because it was just observed is the opposite.

    Anything NOT checkable from a prompt and a directory stays absent, and the
    ABSTAIN branch is the designed consequence of that absence.
    """
    root = root or Path.cwd()
    found = []
    try:
        if any(root.glob("*.py")) or any(root.glob("*/*.py")) \
                or any(root.glob("*.js")) or any(root.glob("*/*.js")):
            found.append("source")
        if (root / "tests").is_dir() or any(root.glob("t*/test_*.py")):
            found.append("tests")
    except Exception:                                 # noqa: BLE001
        return []
    return found


def classify_prompt(prompt: str, *, contracts=None, contracts_dir=None,
                    evidence=None, root: Path | None = None) -> TierVerdict:
    """The whole path, from a raw prompt to a tier. Fail-open at the boundary.

    Owners, prerequisites and held scopes stay EMPTY: a hook cannot establish
    them and guessing would defeat the point. Evidence is the exception, and
    only because it is observable -- see `observable_evidence`.
    """
    try:
        ev = observable_evidence(root) if evidence is None else list(evidence)
        ctx = MissionContext(description=prompt or "", available_evidence=ev)
        results = evaluate_all(ctx, contracts=contracts, contracts_dir=contracts_dir)
        return classify(_silence_dormant(results, prompt, contracts, contracts_dir))
    except Exception as exc:                      # noqa: BLE001 -- boundary
        # A tier engine that raises must never cost the user their prompt. The
        # floor answer is the incumbent's own default, so failing open here
        # degrades exactly to the behaviour that exists today.
        return TierVerdict(
            LIGHT, by_floor=True,
            reason=f"tier engine failed open ({type(exc).__name__}); floor answer",
        )
