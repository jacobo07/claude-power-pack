---
name: prd-tier0
description: Render the SDD-OS Tier 0 (Micro Task) mini-spec. For trivial, localized, reversible changes with no systemic impact (typo, copy, local rename, minor validation). Inline mini-spec + acceptance + minimal validation; no full PRD unless the change touches critical behavior. Source. SDD-OS PARTE I sec. 3 (Tier 0).
---

# /prd-tier0 -- Micro Task mini-spec

Tier 0 = trivial, localized, reversible, no systemic impact. Spec must
fit inline. If the change turns out to touch critical behavior, escalate
to `/prd-tier1`+.

Fill and paste at the top of the working prompt:

```
## Tier 0 mini-spec
- Change: <one line -- exactly what changes>
- Why: <one line -- the reason / what it fixes>
- Files: <the 1-2 files touched>
- Acceptance: <the single observable condition that proves it is done>
- Validation: <the one check you will run -- build / lint / open the file>
- Reversible: yes (state the 1-step undo if not obvious)
```

## Done-gate (Tier 0)
- Change matches the spec line exactly (no scope creep).
- The acceptance condition is observed, not assumed.
- No existing behavior changed beyond the stated change.
