---
name: prd-tier3
description: Render the SDD-OS Tier 3 (Strategic / Platform Task) full spec set. For foundational, ambitious, multi-module work that can become a reusable standard (new internal OS, new global standard, new agent system, universal framework, security layer, execution mode, provisioning system, spec-driven system, changes affecting all repos). Full PRD + Full Architecture Spec + Ambitious Roadmap + Governance Spec + Cross-Repo Applicability + Compatibility Matrix + Migration Strategy + Validation Contract + Regression Prevention + Standardization Rule + Kill Switches + Completion Rubric. Source. SDD-OS PARTE I sec. 3 (Tier 3). This is the highest tier (the plan's "Tier 4 / System-Arch" is folded here).
---

# /prd-tier3 -- Strategic / Platform spec set

Tier 3 = foundational / ambitious / multi-module / standard-defining.
The most rigorous gate. Includes the full Tier 2 PRD + Architecture Spec
(see `/prd-tier2`) PLUS the strategic layers below. **No execution
without the full spec set approved.**

```
## Tier 3 -- additional required specs (on top of the Tier 2 PRD)

### Governance Spec
- Who/what governs changes to this system; decision authority; review.

### Cross-Repo Applicability Spec
- How it activates in ANY repo (language/framework/size-agnostic).
- What it depends on; what it must NOT depend on.

### Compatibility Matrix
- Supported environments / versions / stacks; known incompatibilities.

### Migration Strategy
- How existing repos/users adopt it; backward-compat; phased rollout.

### Regression Prevention Plan
- Invariants that must never break; the tests/gates that protect them.

### Standardization Rule
- The reusable standard this establishes for future similar features.

### Future Feature Inheritance Rule
- The completion level future similar features must inherit (no
  standard regression).

### Kill Switches
- How to disable / roll back instantly under failure pressure.

### Completion Rubric
- The explicit, scored definition of "done" for this system.
```

## Done-gate (Tier 3)
- Full PRD + Architecture Spec + all strategic specs above exist + approved.
- Cross-repo applicability demonstrated, not asserted.
- Kill switch + rollback path exist and were exercised.
- Regression invariants protected by a gate.
- OQS for this surface meets the Tier 3 floor (>= 90).
