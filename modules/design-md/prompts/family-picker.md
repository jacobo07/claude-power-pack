# Prompt Pack — `family-picker`

**Objective.** Turn a product description into exactly one declared CDIO-06 aesthetic
family (F1–F9), with the reasoning shown, so the DESIGN.md `aesthetic_family` field can
be filled with a decision instead of a guess.

**When to use.** Before any token is written for a new product or a redesign. This is
the first design action, not a later refinement: `check_family_declared` BLOCKs a
surface with no family, and every token below the family is downstream of it.

**Do not use** to justify a family already chosen. The picker is a decision procedure;
running it backwards to rationalize a preference is how a default becomes a "choice".

## The prompt

> Read `vault/knowledge_base/cdio/CDIO-06-aesthetic-families.md`.
>
> Product: `<one paragraph: what it does, who uses it, what the user's core task is>`
>
> Run the three-question picker in CDIO-06 sec. 2, in order. For each question, state
> the answer AND the evidence from the product description that forces it — not a
> preference, an inference. Then:
>
> 1. Name the recommended family (F1–F9) and the runner-up.
> 2. State what the runner-up would have bought you and what it would have cost. If you
>    cannot articulate a real cost, you have not actually compared them.
> 3. From CDIO-06 sec. 5, name the specific floor this family will collide with, and
>    the concrete guard against it.
> 4. From CDIO-06 sec. 6, state the mismatch this family would represent if the product
>    description is wrong in one specific way — i.e. what would have to be true about
>    the product for this to be the wrong call. This is the falsifier.
> 5. Emit the `aesthetic_family` line, ready to paste into DESIGN.md.
>
> Do not propose a remix at this stage. One family. A remix is a later, deliberate act
> (CDIO-06 sec. 3), never a way to avoid choosing.

## Expected output shape

- Q1/Q2/Q3, each with an answer and the phrase from the product description that forces it
- **Recommended:** F<n> — <name>; **Runner-up:** F<m> — <name>, with the real trade
- **Floor collision:** the CDIO-06 sec. 5 hazard for this family + the guard
- **Falsifier:** the fact about the product that would make this the wrong family
- **`aesthetic_family: F<n>`**

## Gate

The output is not done until the falsifier is stated. A family recommendation with no
condition under which it would be wrong is a preference wearing a decision's clothes.
