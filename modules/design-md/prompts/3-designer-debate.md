# Prompt Pack — `3-designer-debate`

**Objective.** Force a genuinely contested design decision through three independent
voices, then synthesize — preserving the minority reports rather than dissolving them
into a compromise.

**When to use.** A design decision with two or more defensible answers, where the cost
of the wrong one is systematic (a family choice, a navigation model, a density
decision). Not for settled questions; a debate over a decided thing is theater.

**The failure this prevents:** a single voice reasoning alone converges on the safe,
average answer, and the average of three good designs is a bad design.

## The prompt

> Three designers review the same surface. They do not see each other's critiques until
> all three are written. Each must ground findings in observed values (CDIO-00).
>
> Surface: `<the artifact, URL, or component>`
> Decision at stake: `<the specific question, stated as a fork with named options>`
>
> **Voice 1 — the minimalist.** Believes every element must earn its place; that
> clarity is subtraction. Argues from cognitive cost and hierarchy. Their failure mode
> is timidity — a product so restrained it says nothing. Name it if you see it.
>
> **Voice 2 — the maximalist.** Believes a product people remember beats a product
> people approve of; that character is a feature. Argues from differentiation and
> emotional response. Their failure mode is noise — decoration mistaken for design.
> Name it if you see it.
>
> **Voice 3 — the data-focused.** Believes the user's task is the only arbiter. Argues
> from flow, conversion, error rates, and accessibility floors. Their failure mode is
> an optimized local maximum with no soul — a surface that converts today and is
> replaced next year. Name it if you see it.
>
> Each voice: a position, the observed values supporting it, and the strongest argument
> AGAINST its own position. A voice that cannot argue against itself has not thought.
>
> **Synthesis.** Do not average. Pick the winning position and say why the others lose
> on this specific surface. Then graft: name the one thing each losing voice was right
> about, and carry it into the winner.
>
> **Minority report.** Each losing voice writes one sentence: the condition under which
> it would have been right. These are the falsifiers of the decision — keep them, they
> are what you check when the surface underperforms.

## Expected output shape

- Three independent critiques, each with a self-rebuttal
- A synthesis that picks, not blends, and grafts explicitly
- Two minority reports, each stating its falsifying condition

## Gate

If the synthesis reads as "a bit of each", the debate failed. A decision that made no
one lose was never a decision.
