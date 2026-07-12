# Prompt Pack — `brand-to-design-md`

**Objective.** Turn a live brand surface (a URL, or a set of screenshots) into a
complete, gate-passing DESIGN.md: nine canonical sections, real tokens, a declared
aesthetic family.

**When to use.** Onboarding an existing product into the Power Pack, or absorbing a
reference brand you have permission to build in the spirit of. The output is a
*starting system*, not a clone.

## The prompt

> Read `vault/knowledge_base/cdio/CDIO-06-aesthetic-families.md` and
> `modules/design-md/DESIGN.md.template`.
>
> Source: `<URL, or attached screenshots>`
>
> Produce a DESIGN.md for this brand. Rules:
>
> 1. **Extract, do not invent.** Every hex code, font family, radius, and spacing value
>    must come from the observed source. Where you cannot observe a value, say so
>    explicitly rather than filling it with a plausible default — an invented token is
>    indistinguishable from an inherited one, which is the failure mode this whole
>    system exists to prevent.
> 2. **Declare the family.** Classify the source into one of F1–F9 and state the
>    evidence (its palette, its type strategy, its density). If it is a remix, name the
>    base and the voice, and apply the CDIO-06 sec. 3 arbitration rules explicitly.
> 3. **Nine sections, all present:** Color Palette; Typography; Components; Spacing &
>    Layout; Imagery & Motion; Dark Mode; Accessibility; Use Cases; Export Format.
> 4. **Check the floors as you go.** Compute the actual contrast ratio of the body text
>    against its ground. If the source itself fails WCAG AA, do not reproduce the
>    failure — record the source's value, and emit a corrected token with a note. You
>    are extracting a system, not laundering a defect.
> 5. **Run the gate before you claim done:** `python tools/design_gate.py <path>`. An
>    output that BLOCKs is not a DESIGN.md, it is a draft.

## Expected output shape

A complete DESIGN.md: YAML front-matter (with `aesthetic_family`) plus the nine prose
sections, followed by the `design_gate.py` verdict as evidence.

## Gate

`python tools/design_gate.py <path>` → **APPROVE**. Any observed value you could not
extract must be listed as an explicit gap, not silently defaulted.
