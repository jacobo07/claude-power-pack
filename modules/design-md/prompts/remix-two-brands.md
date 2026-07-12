# Prompt Pack — `remix-two-brands`

**Objective.** Combine two DESIGN.md systems into one coherent system, arbitrating every
conflicting token explicitly instead of averaging them.

**When to use.** A product that needs one family's structure and another's character —
the eight canonical remixes in CDIO-06 sec. 3, or a new pairing you can defend.

**The failure this prevents:** averaging. Two palettes averaged produce mud; two type
scales averaged produce a scale with no hierarchy. A remix is a series of *decisions*,
each with a winner, not a blend.

## The prompt

> Read `vault/knowledge_base/cdio/CDIO-06-aesthetic-families.md` sec. 3 (arbitration).
>
> System A (the **base**): `<path to DESIGN.md, or family + tokens>`
> System B (the **voice**): `<path to DESIGN.md, or family + tokens>`
>
> First, assign the roles and defend the assignment: the **base** is the family that
> governs the surface the user must *operate*; the **voice** is the family that gives it
> character. Getting this backwards produces a beautiful product nobody can use. If you
> cannot say which system owns the user's task, stop — you are not ready to remix.
>
> Then arbitrate every conflicting token against the five rules:
>
> 1. Structure (spacing scale, grid, density, nesting depth, component geometry) → **base**, without exception.
> 2. Accent → **voice**. Exactly one accent hue survives. Two accents is indecision, not a remix.
> 3. Body type → **base**; display type → **voice**.
> 4. Neutrals → **voice** (neutrals carry temperature, and temperature is character).
> 5. Accessibility floors → **not arbitrable**. A remix that breaks a floor is rejected outright.
>
> Emit a conflict table: token | System A | System B | winner | which rule decided it.
> Every row must cite a rule. A row decided by taste is a row you have not arbitrated —
> go back and find the rule, or admit the remix is arbitrary.
>
> Then emit the merged DESIGN.md, and run `python tools/design_gate.py <path>`.
>
> Finally: state what was LOST. A remix that claims to keep the best of both is lying —
> rule 1 alone discards System B's entire spatial system. Name what died, so the next
> reader knows it was killed deliberately and not forgotten.

## Expected output shape

- Base/voice assignment with its defense
- A conflict table where every row cites the rule that decided it
- The merged DESIGN.md + the `design_gate.py` verdict
- An explicit list of what was discarded

## Gate

`python tools/design_gate.py <merged>` → **APPROVE**, and every conflict-table row cites
a rule. Rule 5 is checked last and cannot be traded: if the remix's accent fails contrast
on the merged ground, the remix is rejected, however good it looks.
