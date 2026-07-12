# Prompt Pack — `audit-live-site`

**Objective.** Turn a live URL into a scored audit — hierarchy, spacing, accessibility,
and slop fingerprints — plus a punch list ordered by what actually costs the user
something.

**When to use.** Assessing a competitor, inheriting a codebase, or checking whether a
shipped surface still matches the DESIGN.md it claims to follow. This is the pack that
catches the most common fingerprint of all: a hero that ignores its own tokens.

## The prompt

> Read `vault/knowledge_base/cdio/CDIO-00-design-intelligence-kernel.md` (the five
> dimensions and their thresholds) and `CDIO-06` sec. 4 (the default fingerprints).
>
> Target: `<URL>`
>
> Audit it. The binding constraint, from CDIO-00: **a finding is only valid if it names
> a measurable criterion and the observed value that fails it.** "The hierarchy is weak"
> is not a finding. "Three elements share the largest type size (32px) and the same
> weight, so the eye has no landing point" is a finding. Emit only the second kind.
>
> Cover, with an observed value each:
>
> 1. **Legibility** — body contrast ratio (computed, not estimated), body font size at
>    375px width, line length in characters, body line-height.
> 2. **Hierarchy** — count of distinct type levels in the first viewport; the size ratio
>    between the top two; how many elements compete for "most important".
> 3. **Flow** — clicks to the primary conversion; form-field count versus the minimum
>    actually required.
> 4. **Trust** — concrete trust signals above the fold; any broken or empty state.
> 5. **Slop fingerprints** — walk the CDIO-06 sec. 4 table item by item and mark each
>    present/absent with the evidence. Do not skip the ones that are absent; a clean row
>    is a result.
>
> Then score with the CDIO-05 formula (start 100; critical −25, major −8, minor −2) and
> state the verdict: APPROVE (≥80, zero critical) / REVISE / BLOCK.
>
> Punch list: order by user cost, not by ease of fix. A 3:1 body contrast outranks a
> misaligned icon, always — even though the icon is the easier commit.
>
> If you find nothing, say so. Zero findings is a valid audit. Do not manufacture a
> finding to justify the invocation.

## Expected output shape

- A table: criterion | observed value | threshold | severity
- The computed score and the verdict
- A punch list ordered by user cost, each item naming the criterion it closes

## Gate

Every finding carries an observed value, or it is dropped before the report is written
(the scorer drops it anyway — `Verdict.is_valid`).
