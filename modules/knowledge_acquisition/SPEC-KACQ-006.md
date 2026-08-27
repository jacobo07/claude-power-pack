---
spec: SPEC-KACQ-006
title: Lens-conditioned source routing for a generated corpus
tier: 2
status: APPROVED
supersedes: none
extends: SPEC-KACQ-005
covers:
  - knowledge-acquisition-phase6
  - source-routing
  - question-routing
  - expert-routing
  - route-calibration
  - evidence-request-grouping
  - prompt-lens-detection
  - topic-identity
  - human-expert-queue
  - acquisition-prioritization
  - corpus-preclassification
---

# SPEC-KACQ-006 — Route the question before spending the query

Extends SPEC-KACQ-005. That spec decided what an answer is worth once it
existed. This one decides **whether the question should have been asked of this
source at all**, before a query is spent.

## 1. Why this exists, measured

Measured on the live registry on 2026-08-26, before any of this was designed.

**G1 — the pending corpus is generated, and the generator is recoverable.**
The 1,995 pending CWOPS2000 prompts decompose with **zero remainder** into
**399 topics x 5 templates**. Each template matches exactly 399 prompts. The
topic sets of the five templates intersect at 399/399 = **100%**: every topic
is asked through all five lenses. This is not an estimate; it is an exact
partition of the corpus with no unmatched rows.

**G2 — the lens, not the topic, decides whether the source can answer.**
Running the SPEC-KACQ-005 expectation deriver *unmodified* over all 2,162
pending prompts, `needs_first_hand_access` splits almost perfectly by template:

| Lens | n | first-hand |
|---|---|---|
| C -- real cases | 399 | **100.0%** |
| A -- thresholds | 399 | 0.3% |
| B -- internal patterns | 399 | 0.3% |
| D -- experiment | 399 | 0.3% |
| E -- pitfalls | 399 | 0.3% |

**G3 — the inherited 37% expert-routing rate does not hold on the pending
corpus.** Measured rate is **19.1%** (412/2,162), and **403 of 412 are lens C**.
The 37% came from 38 answers drawn entirely from SF30 families 00A-01, the most
boundary-prone slice of the corpus. Pending SF30 measures 5.4%.

**G4 — there is no calibration data for any of the five lenses.** All 38
assessed answers are SF30 free-form. Zero observed EVA behaviour exists for
92.3% of the pending corpus. This is the governing constraint of this spec.

**G5 — the scheduler lever already exists.** `store.claim_next` orders by
`priority ASC, ordinal ASC` and `prompt.priority` is already populated. Routing
must feed that ordering, not replace it.

## 2. Non-goals

Multi-source execution adapters. Automatic human outreach. Embedding-based
deduplication. Auto-marking a prompt satisfied by another prompt's answer.
Claim extraction. Standing contradiction detection. Any decimal "expected
information gain" score. This spec produces a routing verdict and two
artifacts; it executes nothing against a non-EVA source.

## 3. Contracts

**C1 — Lens identity is derived, never stored by hand.** A prompt's lens is
recovered from its text by exact template match. A prompt matching no template
is `FREEFORM`, which is a real lens and not an error. Derivation is pure: the
same text always yields the same lens, so a verdict is reproducible from raw
alone (inherits HR-DERIVED-NEVER-ENDANGERS-RAW-001).

**C2 — Topic identity is the template slot.** The varying span of a generated
prompt is its topic. Two prompts share a topic when their folded slots are
equal. This is exact string identity, not similarity: no embeddings, no
threshold, no false merges.

**C3 — A route verdict may never be stronger than the evidence for its lens.**
This is the coverage-substitution doctrine of SPEC-KACQ-005 applied to routing.
A lens with fewer than `MIN_LENS_OBSERVATIONS` assessed answers **cannot**
produce a verdict that diverts a prompt away from the source. Its prompts route
`EVA_VALID` or `UNCERTAIN` and still run. Only a lens with observed evidence can
earn `HUMAN_EXPERT`, `INTERNAL_EVIDENCE`, or `MULTI_SOURCE`.

**C4 — Routing away requires a boundary collision, not a hunch.** A prompt
diverts only when its derived expectation needs first-hand access **and** the
source has already declared a cohort-scoped ACCESS boundary covering that need.
The boundary ledger of SPEC-KACQ-005 is the only admissible evidence of
incapability. A VARIABILITY hedge never diverts anything: it describes the
question, not the source.

**C5 — `UNCERTAIN` is a destination, not a failure.** Anything the evidence
does not license is `UNCERTAIN` and remains in the EVA queue. Fail-open: a
routing defect costs ranking quality, never a captured answer, and never
silently drops a prompt from acquisition.

**C6 — Routing verdicts are versioned and never overwritten.** Same discipline
as assessment: unique per (prompt, router version), rebuildable from prompt text
plus the boundary ledger, so a verdict can be audited or recomputed without
re-querying.

**C7 — Route and priority are separate facts.** The route class says which
source should answer. The priority says when EVA should get to it. A prompt can
be `MULTI_SOURCE` and still high-priority for EVA. Conflating them would repeat
the gap/content conflation that SPEC-KACQ-005 had to undo.

**C8 — An evidence request is a grouping, not a question dump.** Prompts that
divert for the same reason against the same boundary collapse into one request
carrying the shared evidence requirement and the count of questions it unlocks.
The measure of this artifact is questions-unlocked-per-request, not row count.

## 4. Calibration

The corpus supplies a controlled experiment at no design cost: because every
topic exists in all five lenses (G1), topic can be held constant while lens
varies. The calibration probe is **3 topics x 5 lenses = 15 live prompts**,
foreground and bounded. It measures the lens effect directly.

Calibration is reported whether or not it is favourable. A weak result caps
routing at C3 and is recorded as the session's finding; it is not grounds for
routing anyway.

## 5. Acceptance

Falsifiable. Each row is checked against real registry data or the probe.

| # | Assertion | How it fails |
|---|---|---|
| A1 | Every pending CWOPS2000 prompt resolves to exactly one of five lenses | any unmatched row |
| A2 | Lens derivation is pure: same text, same lens, no DB read | a verdict that changes on re-run |
| A3 | The 399 topics of each lens are the same 399 | intersection < 399 |
| A4 | A lens below `MIN_LENS_OBSERVATIONS` never yields a diverting verdict | any diverted prompt whose lens lacks evidence |
| A5 | A VARIABILITY-only boundary diverts nothing | a divert citing a hedge |
| A6 | Every diverted prompt names the boundary it collided with | a divert with an empty reason |
| A7 | Re-running the router changes no stored verdict of the same version | a duplicate or mutated row |
| A8 | Every pending prompt appears in exactly one queue artifact | a prompt in both or neither |
| A9 | An evidence request names the questions it unlocks | a request with zero linked prompts |
| A10 | A router failure leaves the prompt runnable | a prompt lost to a classifier defect |

## 6. Done

A1-A10 hold against the live registry; the probe has run and its result is
reported honestly; the two artifacts are materialised from real rows; the
adversarial suite passes; and the remaining EVA runtime is restated from the
routed queue rather than inherited from the pre-routing estimate.
