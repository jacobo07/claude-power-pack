---
name: prd-generate
description: Auto-classify a task into an SDD-OS tier (0-3) and generate the matching PRD scaffold programmatically. Unlike the static /prd-tier0..3 templates, this picks the tier for you (via spec_gate.classify_tier) and emits the correct section set filled with field prompts. Tier 0 -> mini-spec; Tier 2 -> full PRD + Architecture Spec; Tier 3 -> full strategic spec set.
---

# /prd-generate -- tier-aware PRD generator

Composes `spec_gate.classify_tier` + the per-tier section sets. One step:
describe the task, get the right PRD scaffold for its tier.

## Run

```
python -m modules.sdd_os.prd_generator "build user auth system"
```

## Output
- Tier + size + spec-required flag,
- the markdown PRD scaffold with the exact sections that tier requires
  (e.g. Tier 2 -> Problem / Objective / FR / NFR / AC / Architecture Spec
  / Roadmap / Validation contract).

If you already know the tier, the static `/prd-tier<N>` templates remain.
