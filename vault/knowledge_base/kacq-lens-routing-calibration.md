# Lens routing: the probe that refuted the plan

**Date**: 2026-08-27 · **Spec**: SPEC-KACQ-006 · **Router**: `kacq-route/1.0.0`

## What was believed

The pending EVA corpus (2,162 prompts) was thought to contain a large fraction
of questions the source structurally cannot answer, which should be diverted to
a human before spending roughly eleven hours of live querying. The inherited
figure was 37% expert-routing, extrapolated from 38 assessed answers.

## What the corpus turned out to be

The 1,995 pending CWOPS2000 prompts decompose with **zero remainder** into
**399 topics x 5 templates**. Each template matches exactly 399 prompts and the
five topic sets intersect at 399/399. The corpus is 399 questions asked five
ways, not 1,995 questions.

Running the existing expectation deriver unmodified over the pending corpus,
`needs_first_hand_access` was **19.1%** (412/2,162), not 37% -- and **403 of
412 belonged to a single template**, the case-data lens. The inherited 37% came
from a slice (SF30 families 00A-00C) that is the most boundary-prone part of
the corpus and is unrepresentative of what remains.

## The probe

Because every topic exists in all five lenses, topic can be held constant while
lens varies -- a controlled experiment the corpus supplied for free. Three
topics from three structurally different families (unit economics, creative
strategy, analytics) x five lenses = **15 live prompts, 380 seconds**.

15/15 COMPLETE, all paired, zero failures.

## What the probe found

| lens | n | extractable | ->expert | avg chars |
|---|---|---|---|---|
| REAL_CASES | 4 | **4** | **4** | **7,225** |
| PITFALLS | 4 | 4 | 0 | 6,081 |
| EXPERIMENT | 4 | 4 | 0 | 5,787 |
| THRESHOLD | 4 | 4 | 0 | 5,682 |
| INTERNAL_PATTERNS | 4 | 3 | 0 | 4,858 |

Predicted divert for REAL_CASES was 100% (400/400). Observed divert was 4/4 --
**the prediction was right**. And observed extractable was also 4/4, with the
longest answers in the corpus by a wide margin.

**Both facts are true at once.** The lens the inference said to divert produces
EVA's richest output. Had the corpus been routed on the pre-probe inference,
396 prompts averaging 7.2k characters would have been skipped to save 2.1
hours.

## The verdict that survived

Nothing diverts away from the source. 2,147 pending prompts route as:

- `EVA_HIGH_VALUE` **1,738** -- ask, no declared limit against them
- `MULTI_SOURCE` **409** -- ask anyway, and separately request the evidence

Estimated EVA runtime is **unchanged** at roughly 11 hours. Routing saved zero
queries and that is the honest result.

## What routing did buy

Six evidence requests unlock **409 questions**; the largest single request
unlocks **396** across 40 families -- one dataset of case outcomes segmented by
categoria, ticket, margen, canal, geografia and madurez. That is the compression
that mattered: not fewer queries to the source, but 396 questions to a human
collapsing into one artifact to ask for.

## Why the restraint was load-bearing

SPEC-KACQ-006 C3 forbids a lens with fewer than three observed answers from
diverting anything. Before the probe, every CWOPS lens had **zero**
observations. The contract is what made the wrong answer unreachable; the probe
is what replaced it with a measured one, for 15 prompts instead of 11 hours.

The same restraint absorbs an upstream false positive: `casos de` is a cohort
marker, so a methodology question about reviewing support cases derives as
CASE_DATA. Unmeasured, it still routes `EVA_VALID` and still runs.

## Open

- The governing boundary quoted in the evidence pack is the first cohort-scoped
  ACCESS declaration in the ledger ("No tengo un numero exacto de capital total
  disponible..."). A later one ("no tenemos acceso a los datos financieros
  detallados de otros clientes") is more representative of the collision. Both
  are cohort-scoped ACCESS and either is honest; the selection is by insertion
  order, not by aptness.
- `MIN_LENS_OBSERVATIONS = 3` gives each CWOPS lens n=4. That licenses a verdict
  but not a confident rate; a lens measured at 4/4 could still be 80% in truth.
- Account-level memory means the 15 probe answers are not fully independent of
  the 38 that preceded them.
