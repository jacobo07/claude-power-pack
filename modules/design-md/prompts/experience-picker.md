# Prompt Pack — `experience-picker`

**Objective.** Turn a product description into exactly one declared CDIO-07 experience
contract, with the reasoning shown, so the DESIGN.md `experience:` block can be filled
with a decision instead of settled later by whoever writes the last component.

**When to use.** After `family-picker` and before the first interactive component. The
family governs how the surface looks; this governs what it does when touched and while
the user waits. Both are declarations, and both are cheap now and expensive to
retrofit.

**Do not use** to justify expression already built. The picker is a decision procedure,
and running it backwards to license an animation somebody already liked is exactly how
a preference acquires a contract's authority.

**Do not use** to raise a ceiling. Questions 2 and 3 can only narrow what question 1
set. A picker that ratchets toward more motion is not a decision procedure.

## The prompt

> Read `vault/knowledge_base/cdio/CDIO-07-experience-contract.md`.
>
> Product: `<one paragraph: what it does, who uses it, what the user's core task is,
> how often they return, and what a mistake on this surface costs them>`
>
> Run the three-question picker in CDIO-07 sec. 2, in order. For each question, state
> the answer AND the phrase in the product description that forces it — an inference,
> never a preference. Then:
>
> 1. Emit all twelve fields of the `experience:` block with the values the picker
>    produced. Every field, including the ones you would rather leave to a default:
>    a field left unstated is not a neutral default, it is a check that never runs.
> 2. Name the single field where you had the most latitude, and state what you traded.
>    If no field involved a real trade, you have not run the picker — you have filled
>    in a form.
> 3. From CDIO-07 sec. 5, name the specific floor this contract will collide with and
>    the concrete guard. Every posture above `restrained` collides with something.
> 4. State the **abstention test**: what would have to be true about this product for
>    `expressiveness: none` to be the correct answer? If the honest answer is "it
>    already is", declare `none` and stop — that is a complete, passing contract.
> 5. State the **over-delivery falsifier**: name one concrete behaviour that would
>    violate this contract by doing *too much*. A contract that can only be broken by
>    doing too little is not enforceable in both directions and is not a contract.
> 6. Run the coherence check yourself before emitting: a high ceiling with
>    `reduced_motion: absent`, a celebration policy above `never` with
>    `trust_posture: critical`, or a `motion_budget` above what `expressiveness`
>    permits. Any of these is refused at declaration time — fix it here, not later.
>
> Do not propose per-screen variations at this stage. One contract for the product. A
> surface that genuinely needs a different posture declares its own contract, which is
> a later deliberate act and never a way to avoid choosing now.

## Expected output shape

- Q1/Q2/Q3, each with an answer and the phrase from the product description that forces it
- The complete twelve-field `experience:` block, ready to paste into DESIGN.md
- **Latitude:** the field with the most room + the trade actually made
- **Floor collision:** the CDIO-07 sec. 5 hazard for this contract + the guard
- **Abstention test:** what would make `none` correct
- **Over-delivery falsifier:** the concrete behaviour that would breach this contract
  by doing too much
- **Coherence:** the three incoherence conditions, each checked and cleared

## Gate

The output is not done until the over-delivery falsifier is stated. A contract with no
condition under which *more* expression would be a violation cannot refuse anything —
it is a budget that only ever goes up, which is a preference wearing a decision's
clothes.

Emit the selector context from the finished document with
`python tools/design_gate.py --emit-context ./DESIGN.md`. Do not hand-write it: a
context object typed by hand is a filter that silently disagrees with the document it
claims to represent.
