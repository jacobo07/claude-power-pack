---
title: "CLAE — Version Ledger"
family: clae
type: registry
kind: extract
sources: [all 26 Parts, frontmatter and filesystem]
derivation: mechanical extraction from the sealed Parts; no entry carries information absent from its source
status: POPULATED
date: 2026-08-10
---

# CLAE — Version Ledger

> **What this file is.** Part XXVI §5 defines the twelve companion artifacts as *"extracts for retrieval convenience"* — the schemas, consolidations and measured counts live in the Parts. This file locates entries; it does not restate, resolve or extend them.
> **Reading rule.** Every row cites the Part that seeded it. Where a row's source is ambiguous, the ambiguity is transcribed rather than resolved.

## 1. Parts

| Part | File | Status | Date | Depends on | Feeds | Lines |
|---|---|---|---|---|---|---|
| I | `PART_I_the_internal_bar_trap.md` | SEALED | 2026-07-26 | [] | [II, III, XXI, XXII, XXIII] | 319 |
| II | `PART_II_quality_as_distance.md` | SEALED | 2026-07-26 | [I] | [III, VII, IX, XXI] | 449 |
| III | `PART_III_ontology_and_glossary.md` | SEALED | 2026-07-26 | [I, II] | [IV, V, VI, VII, IX, X, XIII, XVI, XVIII, XXII, XXIII] | 441 |
| IV | `PART_IV_the_reference_object.md` | SEALED | 2026-07-26 | [III] | [V, VI, IX, XVI, XXI] | 431 |
| V | `PART_V_reference_acquisition_and_provenance.md` | SEALED | 2026-07-26 | [IV] | [VI, IX, XV, XXI] | 399 |
| VI | `PART_VI_delta_extraction.md` | SEALED | 2026-07-26 | [IV, V] | [VII, VIII, XII, XIII, XVI] | 398 |
| VII | `PART_VII_delta_impact_ranking.md` | SEALED | 2026-07-26 | [VI] | [VIII, IX, XVII, XXI] | 359 |
| VIII | `PART_VIII_the_topk_correction_cycle.md` | SEALED | 2026-07-26 | [VII] | [IX, XIV, XIX, XXI] | 379 |
| IX | `PART_IX_quality_distance_accounting.md` | SEALED | 2026-07-26 | [II, VIII] | [X, XVIII, XX, XXI, XXV] | 388 |
| X | `PART_X_anti_underbuild_floors.md` | SEALED | 2026-07-26 | [IX] | [XI, XVIII, XIX, XX, XXV] | 362 |
| XI | `PART_XI_floor_derivation_versus_imposition.md` | SEALED | 2026-07-26 | [X] | [XVIII, XIX, XXIII, XXV] | 378 |
| XII | `PART_XII_observability_capable_phase_zero.md` | SEALED | 2026-07-26 | [VI] | [XIII, XIV, XV, XVI, XIX] | 365 |
| XIII | `PART_XIII_the_instrument_taxonomy.md` | SEALED | 2026-07-26 | [XII] | [XIV, XV, XXIV, XXV] | 385 |
| XIV | `PART_XIV_autonomous_toolsmith_behaviour.md` | SEALED | 2026-07-26 | [XIII] | [XV, XIX, XXI, XXV] | 382 |
| XV | `PART_XV_incident_to_probe_conversion.md` | SEALED | 2026-07-26 | [XIII, XIV] | [XIX, XXI, XXII, XXIV] | 380 |
| XVI | `PART_XVI_the_human_oracle_boundary.md` | SEALED | 2026-07-26 | [II, XII] | [XVII, XIX, XXI, XXV] | 355 |
| XVII | `PART_XVII_oracle_routing.md` | SEALED | 2026-07-26 | [XVI] | [XIX, XX, XXI, XXV] | 374 |
| XVIII | `PART_XVIII_deviation_governance.md` | SEALED | 2026-07-26 | [IX] | [XIX, XX, XXI, XXV] | 388 |
| XIX | `PART_XIX_evidence_gated_autonomy.md` | SEALED | 2026-07-26 | [XII, XVIII] | [XX, XXI, XXV] | 395 |
| XX | `PART_XX_phase_closure_semantics.md` | SEALED | 2026-07-26 | [IX, XIX] | [XXI, XXV, XXVI] | 363 |
| XXI | `PART_XXI_failure_modes_and_lineages.md` | SEALED | 2026-07-26 | [I, II, III, IV, V, VI, VII, VIII, IX, X, XI, XII, XIII, XIV, XV, XVI, XVII, XVIII, XIX, XX] | [XXII, XXIII, XXIV, XXV] | 341 |
| XXII | `PART_XXII_traps_registry.md` | SEALED | 2026-07-26 | [XXI] | [XXIII, XXIV, XXV, XXVI] | 323 |
| XXIII | `PART_XXIII_rules_registry.md` | SEALED | 2026-07-26 | [XXI, XXII] | [XXIV, XXV, XXVI] | 319 |
| XXIV | `PART_XXIV_evals_and_benchmarks.md` | SEALED | 2026-07-26 | [XXIII] | [XXV, XXVI] | 336 |
| XXV | `PART_XXV_production_reality_gates.md` | SEALED | 2026-07-26 | [XXIII, XXIV] | [XXVI] | 334 |
| XXVI | `PART_XXVI_integration_map_and_writeback.md` | SEALED | 2026-07-26 | [I, II, III, IV, V, VI, VII, VIII, IX, X, XI, XII, XIII, XIV, XV, XVI, XVII, XVIII, XIX, XX, XXI, XXII, XXIII, XXIV, XXV] | — | 289 |

**Coherence anchor:** `parts_sealed` in `CLAE_INDEX.md` must equal the count of `PART_*.md` files. Measured: **26** files, all `SEALED`.

## 2. Registry extracts

| Artifact | Source | Status |
|---|---|---|
| `CLAE_SYSTEMS_CATALOG.md` | `CLAE_INDEX.md` · charter | POPULATED |
| `CLAE_HARD_RULES.md` | Part XXIII | POPULATED |
| `CLAE_PROCESS_RULES.md` | Parts II–XXV | POPULATED |
| `CLAE_TRAPS.md` | Parts II–XXI · XXII | POPULATED |
| `CLAE_EVALS.md` | Parts I–XXV · XXIV | POPULATED |
| `CLAE_PRODUCTION_GATES.md` | Parts I–XXIV · XXV | POPULATED |
| `CLAE_ONTOLOGY.md` | Part III | POPULATED |
| `CLAE_INTEGRATION_MAP.md` | Part XXVI | POPULATED |
| `CLAE_EVIDENCE_INDEX.md` | all Parts | POPULATED |
| `CLAE_OPEN_QUESTIONS.md` | all Parts | POPULATED |
| `CLAE_VERSION_LEDGER.md` | frontmatter · filesystem | POPULATED |
| `CLAE_COMPLETION_REPORT.md` | this build | pending — Part XXVI §5 |

## 3. Provenance of this ledger

Every row is read from Part frontmatter or the filesystem. No row is recalled. Line counts are LF counts, which is the measure the depth floor uses.
