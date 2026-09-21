#!/usr/bin/env python3
"""resolver.py -- the one decision this capability owns.

    resolve(context) -> Decision

FOUR OUTCOMES, BECAUSE THREE IS THE BUG HERE.

`modules/cdicf/selector.js` established RECOMMEND / ABSTAIN / REQUIRE_APPROVAL with
exits 0 / 20 / 21, and that vocabulary is reused deliberately: a second decision
vocabulary in the same estate would make two gates' outputs incomparable for no gain.

But three outcomes cannot express this subject. `context.py` makes every fact optional
so that absence is visible, which manufactures two worlds that both look like ABSTAIN:

    we have the facts, and no archetype is justified     -> ABSTAIN          (20)
    we could not evaluate, because facts are missing     -> UNDETERMINED     (22)

Those need opposite fixes from the caller -- rethink the product, or go and measure --
and the estate has paid for this distinction three separate times:
`done_gate/strength_ladder` ("three outcomes, because two is the bug", UNDETERMINED
distinct from OVERSTATED), `cdio/scorer` (ABSTAIN with `score=None`, "not a fifth
quality band; it is the absence of a judgment"), and `capability_runtime/applicability`
gate 1.5 ("dormant, not blocked"). So exit 22 is added rather than overloading 20.

WHY THE VOCABULARY IS SHARED BUT THE IMPLEMENTATION IS NOT: CDICF decides which
component realises a semantic; this decides which topology a surface should have.
Different subjects, so this is not a duplicate capability under HR-APA-011. Its
ranking and index-narrowing logic solve a problem this does not have, and it is
JavaScript, which `modules/liveness/reachability.py` cannot see at all.

EVERY CITED ARCHETYPE ID COMES FROM `archetypes.REGISTRY` BY CONSTRUCTION. A decision
that names an id the registry does not hold would pass every unit test while being
unresolvable downstream, so the gate asserts it rather than trusting this sentence.

Stdlib-only. Domain-blind.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

from modules.surface_architecture import archetypes as A  # noqa: E402
from modules.surface_architecture import boundaries as B  # noqa: E402
from modules.surface_architecture.context import SurfaceContext, load  # noqa: E402

RECOMMEND = "RECOMMEND"
ABSTAIN = "ABSTAIN"
REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
UNDETERMINED = "UNDETERMINED"

EXIT = {RECOMMEND: 0, ABSTAIN: 20, REQUIRE_APPROVAL: 21, UNDETERMINED: 22}

# Reason codes. A caller branches on these; prose is for the human beside them.
# (T-PROSE-ONLY-REMEDY-001: an outcome a program cannot branch on forces the caller
# to match on English, which breaks silently.)
MISSING_MATERIAL_FACTS = "MISSING_MATERIAL_FACTS"
INVALID_CONTEXT_VALUES = "INVALID_CONTEXT_VALUES"
EVIDENCE_INCOMPLETE = "ARCHETYPE_EVIDENCE_INCOMPLETE"
NO_ARCHETYPE_JUSTIFIED = "NO_ARCHETYPE_JUSTIFIED"
AMBIGUOUS_TIE = "AMBIGUOUS_TIE"
ESCALATING_CONSTRAINT = "ESCALATING_CONSTRAINT"
BOUNDARY_CONFLICT = "BOUNDARY_CONFLICT"

# Constraints under which a machine may propose but not decide. Each is a fact whose
# consequence lands outside the product, so an automatic choice would be the system
# spending someone else's risk.
_ESCALATING = (
    ("regulated", "a rule outside the product governs this surface"),
    ("assurance_required", "a verified party is required, not merely a known one"),
    ("external_consequences", "the surface acts on the world on someone's behalf"),
)


@dataclass
class Decision:
    outcome: str
    reason_code: str = ""
    reason: str = ""
    archetype: str = ""
    boundaries: list = field(default_factory=list)
    rejected: list = field(default_factory=list)      # [{id, why}]
    undecided: list = field(default_factory=list)     # [{id, why}]
    missing_facts: list = field(default_factory=list)
    # Kept APART from missing_facts deliberately. "nobody looked" and "somebody
    # looked and wrote something outside the vocabulary" need opposite fixes from
    # the caller -- go and measure, versus correct what you wrote. Rendering them
    # under one label is the exact conflation context.py exists to prevent, and
    # the first smoke run of this module committed it.
    invalid_values: list = field(default_factory=list)
    escalations: list = field(default_factory=list)
    safeguards: list = field(default_factory=list)
    fallback: str = ""

    @property
    def exit_code(self) -> int:
        return EXIT.get(self.outcome, 2)

    def cited_archetype_ids(self) -> list:
        """Every registry id this decision names, anywhere. The drift gate asserts
        each one resolves -- including the ones in `rejected`, which is where an
        invented id would otherwise hide."""
        out = [self.archetype] if self.archetype else []
        out += [r["id"] for r in self.rejected if r.get("id")]
        out += [u["id"] for u in self.undecided if u.get("id")]
        if self.fallback:
            out.append(self.fallback)
        return sorted(set(out))

    def to_dict(self) -> dict:
        d = asdict(self)
        d["exit_code"] = self.exit_code
        return d

    def render(self) -> str:
        L = [f"{self.outcome}" + (f"  [{self.reason_code}]" if self.reason_code else "")]
        if self.archetype:
            L.append(f"  archetype: {self.archetype}")
        if self.reason:
            L.append(f"  {self.reason}")
        for f in self.missing_facts:
            L.append(f"  UNMEASURED  {f}   (nobody looked -- not a default)")
        for f in self.invalid_values:
            L.append(f"  INVALID     {f}   (measured, but outside the vocabulary)")
        for e in self.escalations:
            L.append(f"  ESCALATES   {e}")
        for r in self.rejected:
            L.append(f"  rejected    {r['id']}: {r['why']}")
        for u in self.undecided:
            L.append(f"  undecided   {u['id']}: {u['why']}")
        for p in self.boundaries:
            pos = p.get("position") or "-"
            L.append(f"  boundary    {p['boundary']:<12} {p['status']:<14} {pos}")
        for s in self.safeguards:
            L.append(f"  safeguard   {s}")
        return "\n".join(L)


def _specificity(arch) -> int:
    """How constrained an entry is: the number of conditions that had to hold.

    This is NOT a preference ranking between topologies, which LAW 10 forbids on this
    evidence. It is the observation that an archetype satisfying four measured
    conditions is pinned by more of the context than one satisfying none, so the
    less-constrained one is a residue rather than a rival.
    """
    return len(arch.requires) + len(arch.disqualifiers)


def resolve(ctx: SurfaceContext) -> Decision:
    """The decision. Refuses in four distinguishable ways before it recommends."""
    bad = ctx.invalid_values()
    if bad:
        return Decision(UNDETERMINED, INVALID_CONTEXT_VALUES,
                        "context carries values outside a closed vocabulary; "
                        "an unrecognised value must not resolve to a safe branch",
                        invalid_values=[f"{f}={v!r}" for f, v in bad])

    missing = ctx.missing_material_facts()
    if missing:
        return Decision(UNDETERMINED, MISSING_MATERIAL_FACTS,
                        "material facts were never measured; no archetype can be "
                        "justified and absence is not a default",
                        missing_facts=missing)

    verdicts = A.classify(ctx)
    yes = [A.BY_ID[i] for i, (v, _) in verdicts.items() if v == A.YES]
    unknown = [A.BY_ID[i] for i, (v, _) in verdicts.items() if v == A.UNKNOWN]

    rejected = [{"id": i, "why": "; ".join(r)}
                for i, (v, r) in sorted(verdicts.items()) if v == A.NO]
    undecided = [{"id": i, "why": "; ".join(r)}
                 for i, (v, r) in sorted(verdicts.items()) if v == A.UNKNOWN]
    placements = [p.to_dict() for p in B.plan(ctx)]

    if not yes:
        return Decision(ABSTAIN, NO_ARCHETYPE_JUSTIFIED,
                        "every archetype was disqualified by a measured fact",
                        boundaries=placements, rejected=rejected, undecided=undecided)

    top = max(_specificity(a) for a in yes)
    winners = [a for a in yes if _specificity(a) == top]

    # An UNKNOWN entry at least as constrained as the winner could overturn it once
    # measured. Reporting the winner anyway would be a confident answer that another
    # afternoon of measurement could flip -- so say so instead.
    contenders = [a for a in unknown if _specificity(a) >= top]
    if contenders:
        gaps = sorted({r.split(": ", 1)[-1]
                       for a in contenders for r in verdicts[a.id][1]})
        return Decision(UNDETERMINED, EVIDENCE_INCOMPLETE,
                        "an unmeasured archetype is at least as constrained as the "
                        "leader, so more measurement could change this answer",
                        boundaries=placements, rejected=rejected, undecided=undecided,
                        missing_facts=gaps)

    if len(winners) > 1:
        tied = ", ".join(sorted(a.id for a in winners))
        return Decision(
            ABSTAIN, AMBIGUOUS_TIE,
            f"more than one archetype is equally justified by the measured facts "
            f"({tied}); breaking the tie would invent a preference the evidence "
            "does not support",
            boundaries=placements, rejected=rejected, undecided=undecided)

    win = winners[0]
    conflicts = [p for p in placements if p["status"] == B.CONFLICT]
    escalations = [why for fld, why in _ESCALATING if getattr(ctx, fld, None) is True]

    if conflicts:
        return Decision(REQUIRE_APPROVAL, BOUNDARY_CONFLICT,
                        "a boundary has no position satisfying its own constraints; "
                        "a human must resolve the contradiction",
                        archetype=win.id, boundaries=placements, rejected=rejected,
                        undecided=undecided, escalations=escalations,
                        safeguards=list(win.safeguards), fallback=win.fallback)

    if escalations:
        return Decision(REQUIRE_APPROVAL, ESCALATING_CONSTRAINT,
                        "the archetype is justified, but a constraint places the "
                        "consequence outside the product; a machine may propose it "
                        "and may not choose it",
                        archetype=win.id, boundaries=placements, rejected=rejected,
                        undecided=undecided, escalations=escalations,
                        safeguards=list(win.safeguards), fallback=win.fallback)

    return Decision(RECOMMEND, "", win.summary, archetype=win.id,
                    boundaries=placements, rejected=rejected, undecided=undecided,
                    safeguards=list(win.safeguards), fallback=win.fallback)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Which surface architecture is justified, and where do its "
                    "boundaries fall?")
    ap.add_argument("context", help="path to a SurfaceContext JSON file")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        ctx = load(args.context)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"unreadable context {args.context}: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        return 3
    d = resolve(ctx)
    print(json.dumps(d.to_dict(), indent=2) if args.json else d.render())
    return d.exit_code


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["Decision", "resolve", "EXIT", "RECOMMEND", "ABSTAIN",
           "REQUIRE_APPROVAL", "UNDETERMINED", "MISSING_MATERIAL_FACTS",
           "INVALID_CONTEXT_VALUES", "EVIDENCE_INCOMPLETE",
           "NO_ARCHETYPE_JUSTIFIED", "AMBIGUOUS_TIE", "ESCALATING_CONSTRAINT",
           "BOUNDARY_CONFLICT"]
