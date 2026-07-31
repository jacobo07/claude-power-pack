---
title: USIRC STOP #1 — Dataset Architecture Decision Ledger
date: 2026-07-31
scope: the ~160 chartered dataset slots across categories A–M, decided by evidence
decision_classes: OWN_DATASET · GROUP_WITH_OTHERS · ALREADY_EXISTS · FOLD_AS_PART ·
  ANNEX_OR_INTEGRATION · EXCLUDE_AS_DUPLICATE · OUT_OF_SCOPE
---

# Dataset Architecture Decision Ledger

The prompt is explicit that the 160 candidates are a **coverage obligation, not an
instruction to create 160 datasets**, and that each element must be decided by
evidence. This ledger is that decision, taken at category and mechanism granularity —
the granularity at which the source actually names things. Inventing 160 individual
dataset identifiers the source never enumerates, in order to reject them one by one,
would be manufacturing the denominator; `PR-COVERAGE-BY-CONSTRUCTION-001` cuts in both
directions.

## Decision per category

| Cat | Chartered slots | Decision | Destination |
|---|---|---|---|
| **A** Constitution, authority, epistemology | ~8 | **ALREADY_EXISTS** | ACIS (E0–E7, No-Autopromotion), DAIF-03 §1.6/§4.5, crawl_os DS16, CLAE XVI–XVII, DRK-03 |
| **B** Evidence and acquisition | ~8 | **ALREADY_EXISTS** (6) + **FOLD_AS_PART** (2) | crawl_os DS01/02/03/10/16 own six; B7 folds into **crawl_os DS05**, already chartered and unbuilt; B8 folds into a new adapter under DS03's interface |
| **C** Universal System Model | ~12 | **OWN_DATASET at most 1** (C1) + **ALREADY_EXISTS** (6) | C1 is one schema on `graphify` types using DAIF-01 kinds. Doctrine for it is *one* dataset if the Owner wants doctrine at all — never twelve |
| **D** Fidelity and equivalence | ~15 | **EXCLUDE_AS_DUPLICATE** (14) + **ANNEX** (1) | DAIF-03 owns fidelity and the metric authority by Owner ruling; D3's instruments annex to CLAE Part XIII and DAIF-03's dimension set |
| **E** Reconstruction, compilation, replica | ~14 | **EXCLUDE_AS_DUPLICATE** | FD-03 (a "do not build" already on record), `one_shot`, `karimo-harness`, DAIF-02, CLAE Part XX |
| **F** QA, testing, differential verification | ~14 | **ALREADY_EXISTS** (12) + **ANNEX** (2) | OVO, replay harness, SQI, `sleepless_qa`, CLAE XXIV/XXV. F7 annexes to C1 as a view; F8's comparison is D3 |
| **G** Debugging and causal reconstruction | ~11 | **ALREADY_EXISTS** (9) + **ANNEX** (1) + **EXCLUDE** (1) | CRAIF, CEPS, `root_cause_taxonomy` CLASE 0–5, DRK-04. G2 annexes to CRAIF as an input instrument. The KADOS bridge is excluded — false premise |
| **H** Reverse engineering and archaeology | ~11 | **ALREADY_EXISTS** (5) + **REFERENCE** (2) + **ANNEX** (4) | crawl_os, `autoresearch`, `deep-research`, `ecc-reverse-engineering.md`. H4/H5 are reference-only: no consumer |
| **I** Migration, assimilation, synthesis | ~11 | **ALREADY_EXISTS** (8) + **REFERENCE** (2) + **GROUP** (1) | D2A, FD, AKOS, `cpp_ias`, `dataset_first`, `graphify`, DRK. I4/I5 have no consumer in PP |
| **J** Personal assistants | ~13 | **OUT_OF_SCOPE** | A product build governed by PP under an SDD-OS T2/T3 spec. Every runtime it needs is owned: DAIF-08, `memory-engine`, `agent-governance`, Recovery Control Plane (SCS C83), `session_resilience` |
| **K** Adapters and lenses | ~12 | **ANNEX_OR_INTEGRATION** | A lens is a command profile over one runtime — the source's own words. Commands ship after an engine exists, never before |
| **L** Console reconstruction laboratory | ~18 | **OUT_OF_SCOPE** (17) + **PROMOTE_AS_RULE** (1) | PP is domain-blind by constitution. L1's ordering law is generalized and registered against CLAE Part XXV and the Reality Contract |
| **M** Self-evaluation and self-improvement | ~13 | **EXCLUDE_AS_DUPLICATE** | CLAE XXII/XXIII/XXIV, SQI, FD-04, FIOS `evolution_engine`, `backlog_autopilot`, CLAE Part VII |

## Aggregate decision

| Class | Slots |
|---|---|
| ALREADY_EXISTS | ~46 |
| EXCLUDE_AS_DUPLICATE | ~41 |
| OUT_OF_SCOPE | ~30 |
| ANNEX_OR_INTEGRATION | ~14 |
| FOLD_AS_PART (into an existing family's chartered dataset) | ~2 |
| REFERENCE (analyzed, not built, no consumer) | ~4 |
| GROUP_WITH_OTHERS | ~1 |
| **OWN_DATASET** | **0–1** — only C1's doctrine, and only if the Owner wants doctrine authored ahead of the code |
| PROMOTE_AS_RULE | 1 |

## Why zero, stated plainly

A dataset family in this estate must clear the bar its own precedents set: a distinct
object no incumbent owns, more than one mechanism, more than one consumer, its own
lifecycle, and an admission based on a **measured** sweep rather than an asserted
absence. CLAE cleared it. CRPF, IGEF and E1–E5 did not, and were struck before a Part
was written.

USIRC's surviving residue has three mechanisms sharing one lifecycle and four
consumers, two of the three mechanisms fitting an existing taxonomy slot (CLAE Part
XIII). That is a module. The correct artifact for a module is code plus a registry
entry plus a liveness declaration — not a family, and emphatically not thirteen.

## The registry entries this ledger would create

If the Owner approves construction, exactly these registrations follow — no more:

1. `vault/liveness/reachability_registry.json` — one entry per OSR module, with a
   real class, never `PLANNED` without an Owner-queue row.
2. `modules/graphify` type registration — node and edge kinds for observed external
   systems. No new graph.
3. `vault/forensic/REPLAY_SCHEMA.md` — new ordered event kinds.
4. `vault/knowledge_base/clae/` — instrument rows appended to Part XIII's taxonomy,
   and one gate appended to Part XXV.
5. `vault/hard_rules/` — OSR-L1 through `rule_compiler`, which owns placement.

Five registrations against four existing owners. That is what "integration
architecture with new contracts, not a collection of redundant modules" — the source's
own stated intent in its section 1 — actually looks like when it is measured.
