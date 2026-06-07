#!/usr/bin/env python3
"""PRD Generator -- SDD-OS runtime (build-everything BLOQUE A / A1).

Composes spec_gate.classify_tier (Sprint 2) to pick the right tier, then
emits a FILLED PRD scaffold for that tier -- the runtime counterpart of
the static `commands/prd-tier{0,1,2,3}.md` templates. Tier-aware: a Tier 0
task gets a mini-spec; a Tier 3 task gets the full strategic spec set.

Does NOT duplicate classify_tier -- it imports it (SCS C28: compose).
Output is a structured PRD (sections + fields), renderable to markdown.
stdlib-only.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field

from modules.spec_gate import classify_tier

# Section sets per tier (mirrors the prd-tier*.md templates, dataset
# PARTE I secs. 3+5+6). Each entry: (section title, [field prompts]).
_TIER_SECTIONS: dict[int, list[tuple[str, list[str]]]] = {
    0: [
        ("Mini-spec", ["Change (one line)", "Why", "Files",
                       "Acceptance (single observable condition)",
                       "Validation (the one check)"]),
    ],
    1: [
        ("Brief", ["Goal (observable)", "Non-goals"]),
        ("Acceptance criteria", ["AC-001", "AC-002"]),
        ("Impact map", ["Files/modules touched", "Contracts touched",
                        "Regression surface"]),
        ("Test plan", ["Happy path", "Edge/error case"]),
    ],
    2: [
        ("Problem", ["Current pain", "Risk of not solving",
                     "Errors it prevents"]),
        ("Objective (observable)", ["Objective"]),
        ("Non-objectives", ["Out of scope"]),
        ("Users / actors", ["Actors"]),
        ("Functional requirements", ["FR-001", "FR-002"]),
        ("Non-functional requirements", ["NFR-001"]),
        ("Acceptance criteria", ["AC-001", "AC-002"]),
        ("Architecture Spec", ["Components affected", "Contracts",
                               "Failure modes", "Rollback/fallback"]),
        ("Roadmap", ["Step 1 (+done-gate)", "Step 2 (+done-gate)"]),
        ("Validation contract", ["Happy path", "Error cases",
                                 "Regression check", "Proof of real behavior"]),
    ],
    3: [
        ("Problem", ["Current pain", "Risk", "Errors prevented"]),
        ("Objective (observable)", ["Objective"]),
        ("Non-objectives", ["Out of scope"]),
        ("Functional requirements", ["FR-001", "FR-002"]),
        ("Acceptance criteria", ["AC-001", "AC-002"]),
        ("Architecture Spec", ["Components", "Contracts", "Failure modes",
                               "Rollback"]),
        ("Governance Spec", ["Decision authority", "Review"]),
        ("Cross-Repo Applicability", ["Activation in any repo",
                                      "Dependencies / must-not-depend-on"]),
        ("Compatibility Matrix", ["Supported envs", "Known incompatibilities"]),
        ("Migration Strategy", ["Adoption", "Backward-compat", "Phasing"]),
        ("Regression Prevention", ["Invariants", "Protecting gates"]),
        ("Standardization Rule", ["Reusable standard established"]),
        ("Kill Switches", ["Instant disable/rollback"]),
        ("Completion Rubric", ["Scored definition of done"]),
    ],
}

_TIER_NAME = {0: "Micro Task", 1: "Standard Task",
              2: "Feature / System Task", 3: "Strategic / Platform Task"}


@dataclass
class PRDSection:
    title: str
    fields: list[str]


@dataclass
class PRD:
    description: str
    tier: int
    tier_name: str
    size: str
    requires_spec: bool
    sections: list[PRDSection] = dc_field(default_factory=list)

    def section_titles(self) -> list[str]:
        return [s.title for s in self.sections]


def generate_prd(description: str) -> PRD:
    """Classify the task tier and build the matching PRD scaffold."""
    tr = classify_tier(description)
    secs = [PRDSection(t, list(f)) for t, f in _TIER_SECTIONS[tr.tier]]
    return PRD(
        description=description, tier=tr.tier,
        tier_name=_TIER_NAME[tr.tier], size=tr.size,
        requires_spec=tr.requires_spec, sections=secs)


def render_prd(prd: PRD) -> str:
    lines = [
        f"# PRD -- Tier {prd.tier} ({prd.tier_name})",
        "",
        f"**Task:** {prd.description}",
        f"**Size:** {prd.size}  ·  **Spec required:** "
        f"{'yes' if prd.requires_spec else 'no (mini-spec inline)'}",
        "",
    ]
    for s in prd.sections:
        lines.append(f"## {s.title}")
        for fld in s.fields:
            lines.append(f"- {fld}: <...>")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="SDD-OS PRD Generator")
    ap.add_argument("task", help="task description")
    args = ap.parse_args(argv)
    print(render_prd(generate_prd(args.task)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
