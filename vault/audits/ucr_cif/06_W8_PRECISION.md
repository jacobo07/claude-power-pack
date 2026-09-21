# W8 — Applicability Precision at Real Prompt Length

Sealed 2026-09-22. Spec: `vault/specs/ucr-cif-w8-applicability-precision.md`.
Subject: `modules/ucr_cif/disposition_consumer.py`, the single selector both
doors consume.

**Verdict in one line: the saturation defect moved by a real, measured amount
and the precision it was expected to buy did not arrive — and the reason is
now measured rather than guessed, which reorders the frontier.**

---

## 1. The instrument was broken before the subject was

W7 closed with a one-line success criterion: *re-run `tools/ucr_cif_shadow.py`
and watch `P1-ANY-OWNER`'s holdout precision*. Following it literally would
have produced **byte-identical numbers** and read as "the repair did nothing".

`ucr_cif_shadow.py` scores policies over `owners_routed` in a **persisted
control report**. It never calls `select_for`. It is a replay of a recording,
so no change to the producer of that recording can reach it. Only
`tools/ucr_cif_reach.py --funnel`, which drives the live chain
`sdd_tier -> check_spec_gate -> select_for`, re-derives the field.

This was found before any edit was made, and it is the wave's first finding.

## 2. A stored baseline from another session is not a control

W7 recorded holdout `P1` precision at **23.5 %** over **2,350** cases.
Re-deriving the control **today with the unchanged selector** gave **20.0 %**
over **2,306** cases. Nothing had been modified. The population had moved:
the funnel replays the most recent sessions, and sessions had rolled.

Comparing a treatment against W7's stored figure would have manufactured a
**+3.5-point swing out of history drift alone** — in either direction,
depending on which way the day went. Both halves of this wave were therefore
re-derived, twenty minutes apart, and even then the two runs shared only
**1,792 of 2,395 / 2,201** cases. Every number below is computed on the
**shared** population, which is the only honest comparison available.

## 3. What the repair did, on the identical 683 xl cases

| | before | after | Δ |
|---|---|---|---|
| xl routing ≥ 1 owner | 680/683 = **99.6 %** | 641/683 = **93.9 %** | −5.7 pts |
| mean owners when routed (cap 5) | 4.76 | **3.98** | −0.78 |
| owner slots over 800 judgeable | 3,528 | **2,812** | −20.3 % |
| any owner routed | 754/800 = 94.3 % | 715/800 = 89.4 % | −4.9 pts |

The cap stopped being near-always binding, which was the mechanical claim.
The volume bias also loosened where it was worst: `cdicf` 501 → 220 (−56 %)
and `sqi` 469 → 326 (−30 %), while the three largest owners fell only ~9 %
(`knowledge_acquisition` 739 → 670, `governance-overlay` 738 → 655,
`deep-research` 712 → 631). They are **still** the three most-routed.

## 4. Precision did not move, and the reason is visible

Holdout `P1-ANY-OWNER`: **20.0 % before, 20.0 % after**. TP 12, FP 48 in both.
Calibration moved one false positive (32.8 % → 33.3 %).

The mechanism is not mysterious: of **128 shared labelled cases, exactly one**
changed its fire decision. The oracle can only judge prompts where git history
says where the work landed, and the repair barely touched that subset. With 31
RELEVANT cases in the labelled population, one case is ~0.8 points — **below
this oracle's resolution**, and reporting it as an effect would be exactly the
false precision this programme keeps catching.

**The acceptance criterion "precision rises from 23.5 %" is NOT met.** Stated
plainly, not softened.

## 5. The true-positive floor held — nothing was bought by refusing

TP 12 → 12, recall 100 % → 100 %. The repair removed 716 owner slots and lost
**zero** true positives. That is the one acceptance criterion that mattered
most and it is met: this wave did not buy a number by routing nothing.

## 6. The lexical clause is exhausted, and that is the finding

Sweeping the ceiling over 40 real long documents (proxies for xl prompts, not
real prompts — stated because it matters):

| bar | routed | owner slots | mean when routed |
|---|---|---|---|
| 1 | 40/40 (100 %) | 197 | 4.92 |
| 2 | 40/40 (100 %) | 139 | 3.48 |
| **3** | **17/40 (42 %)** | **27** | **1.59** |
| 4 | 2/40 (5 %) | 4 | 2.00 |
| 5 | 1/40 (2 %) | 1 | 1.00 |
| 6 | 0/40 (0 %) | 0 | — |

There is a **cliff between 3 and 4**, and it is not a tuning artefact. The
corpus's own distinctive supply is median **3**, p75 4, p90 6: 784 of 996
units hold ≥ 2 distinctive terms, 605 hold ≥ 3, and only 404 hold ≥ 4. A bar
of 4 refuses on **supply** rather than on relevance, which is why the ceiling
is pinned to the median and why `V-W8-BAR-NEVER-EXCEEDS-MEASURED-SUPPLY`
recomputes that median from the live ledger rather than from a literal.

So the headroom above the shipped setting is **zero**. A very long prompt
contains three distinctive terms of almost any owner, and the only way to ask
for more is to ask for more than the median unit possesses.

> **Applicability precision is not reachable by tightening the lexical
> distinctive-term clause. The clause is now at its measured ceiling and the
> ceiling is set by the evidence family itself, not by the threshold.**

## 7. The characterization stays green, and must NOT be inverted

`PR-W7-X1-SELECTOR-SATURATION-ON-LONG-PROMPTS` asserts `rate > 0.90`. The rate
is **93.9 %**. It still passes, so it is left exactly as it is. Inverting a
characterization that has not turned would destroy the evidence of a defect
that is still present — the instruction was to invert it *when it goes red*,
and it did not.

Note its instrument dependency: it reads the canonical
`w7_reach_control.json`, which this wave deliberately did not overwrite. The
paired controls live beside this audit's evidence instead, so W7's recorded
measurement stays exactly as W7 took it.

## 8. What this wave changes for the next one

Action 2 of the W7 frontier — *drive the 503 ABSTAIN down with a second
evidence family* — was ranked **second**, below selector precision, and read
as a stock-growth task. This wave's measurement promotes it and changes what
it is for:

- it is not about ABSTAIN volume, it is **the only remaining precision lever**;
- the families named in the brief and still unbuilt — explicit owner
  declaration, test ownership, command/hook ownership, git history — are
  **structural, not lexical**, so none of them is subject to the supply cliff
  measured above;
- a structural signal answers "which owner" with evidence that a long prompt
  cannot supply by coincidence, which is precisely the failure mode of the
  lexical family at 20,000 characters.

Widening remains refused. `05_W7_REACH.md` §9's reopening condition — *P1
becomes viable exactly when its precision stops collapsing* — is **not** met,
and this wave is evidence that it will not be met by threshold work.

## 9. Evidence

| artifact | what it holds |
|---|---|
| `tools/test_w8_applicability_precision.py` | 17/17, both mechanisms independently discriminative, positive control included |
| `vault/governance/mutation_plans/ucr_cif_w8.json` | 6 directed mutations, ALL_CAUGHT, restore verified at source **and** runtime |
| paired controls (`before` / `after`) | re-derived 20 minutes apart; shared population 1,792 cases / 800 judgeable / 683 xl |

Suites green after the change: selection 22/22, consumption 19/19 (+PR 7/7),
spec boundary 22/22, reach 27/27, W8 17/17.

## 10. What is NOT proven

- No precision improvement was demonstrated. The wave's headline acceptance
  criterion failed and is recorded as failed.
- The sensitivity sweep uses **repository documents as proxies** for xl
  prompts. Real prompts are longer and more vocabulary-rich — which is why
  they clear bar 3 at 93.9 % where the proxies clear it at 42 % — so the
  sweep bounds the mechanism, it does not measure production.
- No absolute hook latency is reported. The host ran at 10–20 % free memory
  throughout; the funnel is CPU-bound and shared the machine with the suites.
- The labelled oracle remains 128 shared cases with 31 positives. Any claim
  finer than ~3 points is below its resolution.
