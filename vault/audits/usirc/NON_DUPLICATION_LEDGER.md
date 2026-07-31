---
title: USIRC STOP #1 — Non-Duplication Ledger
date: 2026-07-31
rule: one row per thing NOT built, with the owner that made it unnecessary. A ledger
  of avoided work is the product of an audit; a ledger of built work is the product of
  a build.
---

# Non-Duplication Ledger

## 1. Not built, because an owner exists

| Would have built | Owner that made it unnecessary | Cost avoided (charter's own allocation) |
|---|---|---|
| Epistemology and claim-status family | ACIS E0–E7 + No-Autopromotion Invariant | ~8 datasets |
| Authorization / trust-boundary family | crawl_os DS16, 25 Parts SEALED | folded into the 8 above |
| Evidence acquisition, ledger, provenance, integrity family | crawl_os DS01/02/03/10/16, 5 SEALED, ~117k words, build ACTIVE | ~8 datasets |
| Fidelity, loss budget, equivalence family | DAIF-03, 20 Parts, 38,694 w, plus the absorbed metric authority | ~15 datasets |
| Reconstruction compiler federation | FD-03 — decision already recorded in ACIS-00 as "do not build" | ~14 datasets |
| Differential QA, oracles, replay, production-gate family | `modules/oracle`/OVO + `tools/replay_harness.py` + SQI + `sleepless_qa` + CLAE Part XXV (19 gates) | ~14 datasets |
| Causal debugging family | CRAIF + CEPS + `root_cause_taxonomy.md` CLASE 0–5 + DRK-04 | ~11 datasets |
| Reverse-engineering and archaeology family | crawl_os + `autoresearch` + `deep-research` + `ecc-reverse-engineering.md` | ~11 datasets |
| Migration, assimilation, synthesis family | D2A + FD + AKOS + `cpp_ias` advantage algebra | ~11 datasets |
| Personal-assistant family | Out of scope: a product, not doctrine. Every runtime it needs already exists | ~13 datasets |
| Lens / adapter family | A lens is a command profile; the source says so itself | ~12 datasets |
| Console reconstruction laboratory | Out of scope: another repo's domain; PP is domain-blind by constitution | ~18 datasets |
| Self-evaluation and benchmark family | CLAE Part XXIV + SQI + FD-04 + FIOS `evolution_engine` | ~13 datasets |
| A second knowledge graph for the model | `graphify`, standing and unconditional | — |
| A second fidelity metric authority | DAIF-03 §1.7, by Owner ruling | — |
| A second rule-placement compiler | `rule_compiler`, standing and unconditional | — |
| A second evidence-custody record | crawl_os DS10 | — |
| A second oracle protocol | OVO | — |
| A second telemetry accountant | `cognitive_os` CO-12 | — |
| A second replay engine | `tools/replay_harness.py` | — |

**Total avoided: ~148 of ~160 chartered dataset slots, plus six prohibited second
authorities.**

## 2. Not built, because there is no consumer

| Would have built | Why not |
|---|---|
| Legacy-migration runtime (I4) | PP has no legacy system to migrate and no traffic to cut over |
| Shadow execution (I5) | PP serves no traffic. A dual-run has nothing to run against |
| Design archaeology (H5) | Genuinely absent and genuinely unowned — and nothing in the estate would read its output. Under `liveness` doctrine that is an Owner-queue candidate, not a build |
| Temporal product twin (H4) | Downstream of a model that does not exist yet. Building the twin first inverts the dependency |

`feedback_write_without_read_incomplete_system`: a writer with no reader is
documentation, not capability. These four would each ship as a writer with no reader.

## 3. Not built, because the premise was false

| Would have built | The premise, and why it failed |
|---|---|
| A KADOS bridge, in four places | KADOS does not exist in this repo — one mention repo-wide, inside a plan file. CLASE 1: a plan assuming an API that does not exist |
| "PP has no evidence acquisition owner" | crawl_os has 5 sealed datasets and a named next action. The source inspected `video_analyzer.py` and `autoresearch` but not the crawl_os family |
| "PP has no fidelity owner" | DAIF-03 predates this proposal by weeks and absorbed the metric authority by explicit ruling |
| "The reconstruction compiler is new" | ACIS-00 recorded "do not build — FD-03 IS this system" before the proposal was written |

## 4. What this ledger costs if ignored

The four struck families of the RE Baseline Compendium were allocated ~66–80 Parts.
They were struck **before** construction by exactly this procedure, and the closure
report names the saving as the compendium's actual product: *"Seven shipped repairs,
all of them removals of duplication or closures of a wiring gap. Not one new family."*

At the DAIF/crawl_os realized rate of roughly 1,300–1,800 words per Part and 20–25
Parts per dataset, ~148 avoided dataset slots is on the order of **4–6 million words**
of authored corpus, every page of it restating an owner that already exists.
