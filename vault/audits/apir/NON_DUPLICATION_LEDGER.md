---
title: CPP-APIR — Non-Duplication Ledger
date: 2026-08-03
status: BINDING — this is the Option A verdict on disk. Written BEFORE any code, per build order step 1.
rule: "A row here is a DO-NOT-BUILD. Re-proposing it requires new measured evidence, not a new name."
---

# Non-Duplication Ledger

Every one of the 25 proposed CPP-APIR datasets is routed here to its real owner, or to the three
modules Option A authorizes. Nothing else is built.

## 1. Authorized construction (the entire build)

| Artifact | Covers | Form |
|---|---|---|
| `modules/capability_runtime/contract.py` | DS03 | New module (LIBRARY) |
| `modules/capability_runtime/applicability.py` | DS05 | New module (entrypoint) |
| `modules/capability_runtime/derivatives.py` | DS07 | New module (LIBRARY) |
| `setup_os/scanner.py` graph emitters | DS02 | Extension of an existing owner |
| `universal-meta-systems` specialization map | DS06 | Extension of an existing owner |
| `hook-dispatcher.js` capability registration | DS08 | Wiring only |

## 2. DO-NOT-BUILD — routed to owner

| # | Proposed dataset | Owner | Class |
|---|---|---|---|
| DS01 | Constitutional Kernel / HR-APA-001..018 | `modules/rule_compiler` + 156 compiled rules | OVERLAPS_EXISTING_OWNER |
| DS04 | Capability Supply Registry / Demand Observatory | `modules/liveness` (328 modules scored) + `backlog_autopilot` + `ias_c2` | EXISTS_PARTIALLY |
| DS08 | JIT Activation Runtime | `hooks/hook-dispatcher.js` (39 hooks) + `jit_skill_loader` | EXISTS_AND_WIRED |
| DS09 | Mission Capability Stack Compiler | `one_shot/compiler.py` + `frontier_intelligence/session_compiler` + `spec_gate` | OVERLAPS_EXISTING_OWNER |
| DS10 | Missing Capability Discovery | `d2a_engine.py` + `dataset_enricher.write_cross_project_patterns()` + `owner_queue` | EXISTS_AND_WIRED |
| DS11 | Capability Synthesis Compiler | `d2a_engine.py` (1,037 lines) + `spec_gate.check_novelty_gate` | EXISTS_AND_WIRED |
| DS12 | Project Power Pack Assembly | `modules/setup_os` (installer/registry/rollback/ROI/drift) | EXISTS_PARTIALLY → extension only |
| DS13 | Activation & Effectiveness Ledger | **CDP** (see §3) | DEFERRED — collision |
| DS14 | Learning / Capability Ascension | **ACIS** E0–E7 ladder + FD-00..07 + `compound-learnings` + CLAE | EXISTS_AND_WIRED |
| DS15 | Context / Cognitive Sovereignty | `cognitive_os/context.py` + `gc.py` + `rehydration.py` + DAIF-08 | EXISTS_AND_WIRED |
| DS16 | Knowledge Runtime / Sovereignty | `crawl_os` (5 datasets sealed) + `akos_knowledge` + `graphify` | EXISTS_AND_WIRED |
| DS17 | Adaptive Spec Compiler | `modules/sdd_os` (T0–T3 adaptive depth) + `one_shot/compiler.py` | EXISTS_AND_WIRED |
| DS18 | Evaluation / Benchmark Intelligence | SQI (`run_sqi.py` 45/45 ×3) + OVO + `done_gate` + `uqf` | EXISTS_AND_WIRED |
| DS19 | Integrity / Liveness / Self-Healing | `modules/liveness` + `refcheck` + `sweep_enforcer` + `osa` | EXISTS_AND_WIRED |
| DS20 | CLI / Agent Harness / Execution Surface | 65 commands + 12 agents + `dispatcher` + `harness` | EXISTS_AND_WIRED |
| DS21 | Governance / Authority / Escalation | `governance-overlay` + `owner_queue` + `cascade_prevention` + `hard_rules` | EXISTS_AND_WIRED |
| DS22 | Capability Economics | `cost_collapse/router.py` + `recall_roi` + `corpus_roi` + `token_irr` + `ias_c2/opportunity_cost.py` | EXISTS_AND_WIRED |
| DS23 | Failure Genome / Anti-Patterns | CEPS + `craif` + CLAE + `anti-antipatterns.md` + `KNOWN_FALSE_POSITIVES.md` | EXISTS_AND_WIRED |
| DS24 | Cross-Project Isolation | Domain-blind constitution (USIRC cat. L) + noun-map quarantine + `token-optimizer/cross_project_dedup.py` | EXISTS_PARTIALLY |
| DS25 | Institutional Operating Model / Mission Control | `cpp_ias` + `owner_queue` + `liveness_ledger` | EXISTS_AND_WIRED |

**19 rows do not get built.**

## 3. DS13 / CDP collision — settled

DS13 (activation provenance) and **CDP — Cognitive Decision Provenance** (approved as the CCFL-PDPF
residue, 2026-07-31) are the same object at two granularities: a per-event record of
claim / evidence / assumption / outcome.

**Ruling: one ledger, not two.** DS13 becomes a *record kind* on CDP when CDP is built. It does not
get its own store. `capability_runtime` therefore emits activation records in CDP's shape and does
**not** create a `vault/capability/activations.jsonl`. Until CDP exists, applicability decisions are
returned to the caller and not persisted — an unconsumed store would be the exact
`Registry Without Runtime` anti-pattern DS23 names.

## 4. Reopen conditions

A row above reopens only on **measured** evidence:

1. The named owner is shown by a live sweep to no longer hold the territory, or
2. A recorded incident is attributable to the gap, with a file/commit citation, or
3. The owner is retired or deprecated.

A new name for the same mechanism is not a reopen condition. Nine consecutive proposal sets in this
estate measured majority-owned; the tenth will too unless it is measured first.
