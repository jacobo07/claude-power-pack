---
title: UCEIMR — Universal Capability Evolution & Institutional Mining Runtime — Phase 0 + Phase 1 Audit
date: 2026-08-04
status: STOP #1 — BLOCKING, presented inline, no dataset written
verdict: MAJORITY_OWNED — 0 of 15 proposed datasets clear HR-NOVELTY-001 as GENUINELY_NEW_DATASET
source: "Downloads/Dataset Universal Capability Evolution & Institutional Mining Runtime 1.txt"
  — 594 lines / 15,250 bytes, read to EOF in one pass
precedent: thirteenth consecutive mega-corpus proposal measured majority-or-fully owned
residue: one missing adapter (R1, the source's own thesis), one orphan field (R2)
---

# UCEIMR — Mechanism-Level Corpus Boundary Audit

## PHASE 0 — Environment Reality Scan (OBSERVED, from disk, not recalled)

| Surface | Count | Instrument |
|---|---|---|
| Modules | 55 with `__init__.py` (78 dirs) | `Glob modules/*/__init__.py` |
| Knowledge families with an INDEX | 17 | `Glob vault/knowledge_base/*/*INDEX*` |
| Corpus audits in `vault/plans/` | 16 in 9 days | 07-27 → 08-04 |
| HEAD | `baf90c4` | `capability_runtime`: producer, graph emitters, specialization depth |
| REMOTE_DELTA | `0 0` | `git rev-list --left-right --count HEAD...origin/main` |

**Decisive prior fact.** The SEIP audit run earlier today
(`vault/plans/seip-corpus-2026-08-04.md:33`) recorded **UCEIMR — 0 files — does not
exist; source delegates "capability mining" to it.** This brief is the other half of
that dependency: SEIP declined to duplicate capability mining by delegating it to
UCEIMR, and UCEIMR now proposes to own it. Neither existed. The delegation was
circular, and this audit closes the circle by measuring the ground directly.

## PHASE 1 — Ownership audit, all 15 proposed datasets

Verdicts are mechanism-tier. Every REJECT was reached by **opening** the nearest
incumbent, never by a phrase failing to grep
(`feedback_zero_cannot_fall`, `T-OWNERSHIP-AUDIT-ABSORPTION-BIAS-001`).

| DS | Proposed | Verdict | Real owner (verified this session) |
|---|---|---|---|
| 01 | Constitutional Kernel | REJECT | `capability_runtime/contract.py::validate` makes three of the seven proposed constitutional laws **executable, not declarative**: "no capability without a real consumer" → HR-APA-006/007 (`contract.py:148-156`); "traceable lineage" → `derivatives.lineage()`; "ROI + cost of ignorance" → `expected_leverage` + `failure_risk_if_omitted` fields. Plus `craif_00` · `daif_00` · `acis_01_generation_zero_laws` · 156 compiled HARD RULES. A fifth constitution adds no mechanism. Same ground as EFAIF DS01 and SEIP A1, both REJECT today. |
| 02 | Evidence Mining & Source Intelligence | REJECT | `crawl_os/` — 5 sealed datasets incl. `crawl_os_10_evidence_provenance_integrity_fabric` (evidence objects with source/confidence/recency) and `crawl_os_03_adaptive_acquisition_strategy_routing` — plus `modules/akos_knowledge`, `autoresearch/youtube_firehose.py`, `video_analyzer.py`, `whisper_bridge.py`. **The source concedes this itself** (line 672: "eso duplicaría CrawlOS + Knowledge Runtime"). Multi-pass extraction is a prompt change inside AKOS, not a dataset. Identical to SEIP E2/E3, ruled today. |
| 03 | Pattern Mining & Phenomenology | REJECT | **ACIS owns the proposed lifecycle verbatim.** `acis_00_epistemic_ladder_and_theorem_schema.md:120` — `retirement_conditions`: "a law with no retirement condition is dogma, not science". E0–E7 is proposed→corroborated→theory→law→retired. Cross-source epistemics → crawl_os DS03 + SQI §3 admissibility. Pattern→law promotion → `rule_compiler` + `tools/bug_to_hardrule.py`. |
| 04 | Capability Mining & Gap Detection | **EXTEND — carries residue R1** | `d2a_engine.map_gap()` + `registry_gaps()` own gap detection; `frontier_intelligence/unknown_unknown_generator.py` (FIOS II-1) owns Institutional Unknown Discovery with a **stronger** mechanism than proposed — structural asymmetry against a discovered peer cohort, not "what do experts assume". `question_harvester.py` owns directed research generation. The unowned part is the adapter, not the capability. See R1. |
| 05 | Overlap Audit & Novelty Gate | REJECT | `d2a_engine`: `detect_duplicate` → `DupeVerdict` → `map_gap` → `_anti_inflation` → `govern_build`, plus `run_family()` for family sizing. The proposed 13-question Novelty Gate **is already shipped** as `spec_gate/gate.py::check_novelty_gate` and fired on this very prompt. Runtime enforcement additionally exists as `applicability.py` gate 4 → `REJECTED_AS_DUPLICATE`. |
| 06 | Architectural Mutation Generator | REJECT | `d2a_engine.gen_vertical` / `gen_horizontal` / `_score_candidate` / `optimize_portfolio` generate scored architectural candidates; DRK-01…07 adjudicate (DRK-04 = counterfactual simulation, DRK-02 = reversibility/blast radius, DRK-03 = evidence burden); `modules/arch-decision`; `sqi/weakening_detectors.py` ships a working `mutation_probe`. |
| 07 | Capability Proposal Generator & Prioritization | REJECT | `CapabilityContract` **is** the proposal schema field-for-field: impact→`expected_leverage`, cost-of-ignorance→`failure_risk_if_omitted`, overlap→`non_scope`+gate 4, consumer proof→`consumers`, lineage→`parent`, priority→`applicability.evaluate()`. The proposed EIV product is that scorer, already tuned against the constant-factor trap (`feedback_constant_factors_rank_nothing`; `applicability.py:182-194` makes relevance NECESSARY, not weighted). Portfolio → `optimize_portfolio` + `backlog_autopilot` + `corpus_roi.py` + `token_irr.py`. |
| 08 | Adaptive Capability Evolution Runtime (APIR) | REJECT | **This is `modules/capability_runtime`, shipped 2026-08-03/04** *because* the APIR corpus was refused at ≈80 % owned. Per-project specialization → `derivatives.derive(project, overrides)` under HR-APA-016/017; per-mission routing → `MissionContext` + `compile_stack`. Cross-project transfer → IAS-D2, which owns "CROSS-PROJECT IMMUNITY" by name. |
| 09 | Capability Lineage Graph | REJECT | `derivatives.lineage()` (cycle-safe genealogy) + `graphify` GK-00…12 with 1,238 coordinates and typed edges. **A second graph is prohibited unconditionally** by `vault/audits/usirc/BOUNDARY_CONTRACT.md`. The source instructs reuse of graphify — this row agrees with the source. |
| 10 | Universal Failure Learning | **EXTEND — carries residue R2** | CEPS 9-category taxonomy + `governance_vaccines.md` + graphify GK-08 negative-knowledge writeback + `KNOWN_FALSE_POSITIVES.md` + CCFL-PDPF failure lineage + the distiller's Negative Knowledge Vault. Negative learning is already first-class. Unowned: nothing **evaluates** `retirement_condition`. See R2. |
| 11 | Research Mission Compiler & Saturation | REJECT | `crawl_os_02_crawl_intent_and_mission_compilation` — sealed, and named almost verbatim. Saturation/closure/reopen → crawl_os DS03 escalation ladder, **already chartered as a USIRC EXTEND row and re-ruled EXTEND as SEIP E5 today**. Chartering it a third time is the duplication, not the fix. |
| 12 | Institutional Compounding | REJECT | FD-03 insight triage → FD-06 permanent-advantage writeback → FD-07 flywheel (**live in the Stop chain**) + `federated_ledger.py` + `corpus_roi.py` + `recall_roi` + SQI §7 compounding pipeline + the `compound-learnings` skill. |
| 13 | Evaluation & Benchmarks | DO-NOT-BUILD | SQI: 4 sealed datasets, 108,598 words, `run_sqi.py` (45/45 ×3), `BenchmarkScenario`, anti-Goodhart contract §5. **Thrice-set precedent on this exact ground**: PQC rejected 2026-07-12, EFAIF DS20 DO-NOT-BUILD 2026-08-04, SEIP G1 REJECT 2026-08-04. |
| 14 | Threat Model & Institutional Pathologies | REJECT | IAS-D2 immune system + `sqi/redteam_protocol.py` + `vault/audits/sovereign_objection.md` + `output_contracts` slop veto + `KNOWN_FALSE_POSITIVES.md`. Every named pathology has a named owner; "capability inflation" is `_anti_inflation()` literally, and "institutional narcissism" is what this audit series *is*. |
| 15 | Unified Architecture & Integration Map | REJECT | **USIRC, built 2026-07-31**: `SOURCE_OF_TRUTH_MAP` · `OWNERSHIP_OVERLAP_MATRIX` · `BOUNDARY_CONTRACT` · `INTEGRATION_RESPONSIBILITY_MATRIX` · `NON_DUPLICATION_LEDGER` · `DATASET_ARCHITECTURE_DECISION_LEDGER`. Identical to EFAIF DS26, ruled this morning. |

**Result: 0 of 15 clear HR-NOVELTY-001 as `GENUINELY_NEW_DATASET`.**
Distribution: 12 REJECT · 1 DO-NOT-BUILD · 2 EXTEND (both carrying residue).

## The 13 proposed meta-systems, individually

| # | Meta-system | Owner |
|---|---|---|
| 1 | Universal Capability Mining Runtime | `capability_runtime` (object) + R1 (adapter missing) |
| 2 | Institutional Pattern Extraction | ACIS E0–E7 + `rule_compiler` |
| 3 | Cross-Source Consensus | crawl_os DS03 + SQI §3 admissibility |
| 4 | Opportunity Evolution | `frontier_intelligence/evolution_engine.py` + `autoresearch/signal_scorer.py` |
| 5 | Missing Capability Detector | `d2a_engine.map_gap` + `registry_gaps` + `unknown_unknown_generator` |
| 6 | Architectural Mutation Generator | `d2a_engine.gen_vertical/horizontal` + DRK-01…07 |
| 7 | Universal Enterprise Research Compiler | `crawl_os_02` mission compilation |
| 8 | Adaptive Capability Evolution Runtime | `capability_runtime.derivatives` + `applicability` |
| 9 | Capability Lineage Graph | `derivatives.lineage()` + graphify (2nd graph prohibited) |
| 10 | Universal Failure Learning | CEPS + `governance_vaccines` + GK-08 · **R2 open** |
| 11 | Research Compounding | FD-03/06/07 + `corpus_roi` |
| 12 | Capability Proposal Generator | `CapabilityContract` + `optimize_portfolio` |
| 13 | Institutional Unknown Discovery | `unknown_unknown_generator` + `question_harvester` |

Twelve of thirteen are owned at equal or greater maturity. The thirteenth (#1) is owned
as an *object* and unowned as a *producer* — which is R1.

## Residue Register

**R1 — No producer converts EXTERNAL evidence into a capability contract. (Principal.)**

`tools/seed_capability_contracts.py:2-13` states the condition in its own docstring:
the capability layer *"shipped as a reader with no writer"*, and the seeder that fixed
it seeds *"from capabilities THIS repo actually has… none describes an aspiration."*
It is an **introspective** producer. Grep for every writer of a contract returns exactly
that one file.

So the estate can acquire evidence (crawl_os, AKOS, autoresearch), rank capabilities
(`applicability`), specialize them (`derivatives`), audit overlap (`d2a`) and score
portfolios (`optimize_portfolio`) — and there is **no path from mined corpus to a
`Proposal`**. That is precisely the sentence the source is built on: *convert sources
into capabilities, not knowledge* (line 674).

**Shape of the real fix, sized honestly:** one adapter that reads the existing
AKOS/autoresearch signal store, emits `d2a.Proposal` objects into the **already-shipped**
`d2a.run()` → `Stop1Menu` path, and on Owner approval calls the **already-shipped**
`save_contract()`. Propose-only — a miner that admits its own capabilities is a gate that
grades itself (`sqi_scs_c93`). One module, one V-gate, on the order of 300–500 lines.
**Not fifteen datasets, and not a new family.**

**R2 — `retirement_condition` is an orphan field.**

`contract.py:115` defines it and eight seeded contracts populate it — e.g.
`duplicate_detection.json:58`: *"proposals stop measuring majority-owned across three
consecutive audits."* **Nothing evaluates it.** This is the sealed
`feedback_orphan_field_dead_recovery_path` shape: a field defined and consumed with no
producer/evaluator reads as healthy while being dead. It is also exactly DS10's
`RETIRED_BY_EVIDENCE`. Scope: one evaluator + one probe kind on an existing registry.
Sub-dataset scale, and it composes with R1 (a miner that can retire is the negative half
of a miner that can propose).

## Contamination (HR-04)

The source is saturated with CommonWealth Ops / PCIOS vocabulary — operator resonance,
enterprise fit, category reconstructability, brand formation surface. **None of it enters
this artifact or any downstream one.** The reference roots were not read (the SQI
fabrication contract, `sqi/CANONICAL_ONTOLOGY.md` §9, already encodes the depth floor;
re-deriving it from the same references is the duplication the audit exists to prevent —
ruling sealed in `iic-corpus-architecture-2026-07-12.md` §1, re-applied by EFAIF and SEIP
today). The mining mechanism was extracted; the domain was discarded.

## Governance defect surfaced

Accepting this as a build opens the **fifth simultaneously-unresolved STOP #1**:
CPP-ACI (2026-07-12, unbuilt) · CPP-APIR (08-03) · EFAIF (08-04) · SEIP (08-04) · UCEIMR.
APIR flagged two as a defect; EFAIF flagged the third; SEIP flagged the fourth as
`feedback_status_field_nobody_can_transition` at portfolio tier. A fifth is no longer a
queue — it is a queue with no transition producer, which is the same defect the estate
diagnoses in its own subsystems. **Resolving the open four should precede opening a fifth.**

## Base rate after this audit

Thirteen consecutive proposal sets measured majority-or-fully owned against a
**discovered** denominator: AISHF · RE Baseline · KSF · UKR · IIG A–AD · CCFL-PDPF ·
Emergence · USIRC A–M · CRPF/IGEF/E1–E5 · CPP-APIR · EFAIF · SEIP/USSC · **UCEIMR**.
One family (CLAE) has ever survived, admitted by a measured zero rather than an assertion.

## Standing obligations honoured

- `PR-COVERAGE-BY-CONSTRUCTION-001` — denominator discovered from the filesystem, never curated.
- `T-OWNERSHIP-AUDIT-ABSORPTION-BIAS-001` — every REJECT reached by opening the incumbent.
  Three candidate zeros (corpus→contract producer, `retirement_condition` evaluator,
  research-saturation) were each re-tested against the mechanism; two survived as residue.
- `feedback_reality_scan_before_corpus_build` — classification precedes construction.
- `HR-NOVELTY-001` — fired on this prompt; answered against a discovered sweep.
- `HR-UCEIMR-02` (the source's own rule) — upheld, and it is what rejects DS02.

## Blocking condition

No dataset content, no module, no directory is written until the Owner selects an option.
