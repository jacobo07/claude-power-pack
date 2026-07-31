---
title: CCFL-PDPF STOP #1 — Capability Coverage Matrix
date: 2026-07-31
scope: the 35 candidate datasets named in the source prompt, each measured against the discovered denominator in SYSTEM_INVENTORY.md
states: EXISTS_AND_COMPLETE · EXISTS_BUT_UNWIRED · EXISTS_BUT_PARTIAL · EXISTS_UNDER_DIFFERENT_NAME · DECLARED_BUT_ORPHANED · CONFLICTING_OWNER · DUPLICATED · MISSING · DEPRECATED · UNKNOWN_REQUIRES_EVIDENCE
---

# Capability Coverage Matrix — 35 candidates

Confidence is stated per row. **HIGH** = the owning artifact was opened and read this
session. **MEDIUM** = the owner was located by name and by a measured hit-count but the
artifact body was not read in full. No row is marked from memory.

| # | Candidate dataset | State | Current owner (evidence) | Conf. | Duplication risk if built | Proposed disposition |
|---|---|---|---|---|---|---|
| DS01 | AIEF Constitutional Architecture | **CONFLICTING_OWNER** | `cpp_ias` F1 Federation Ontology + F2 Advantage Algebra — 59,662 w governing "the ensemble as a first-class object … never re-governing any of them at its own level" (`CPP_IAS_INDEX.md`) | HIGH | **Severe** — a second ensemble-level constitution is a duplicate sovereign | **REJECT** |
| DS02 | Observable Cognitive Execution Trace | **EXISTS_BUT_PARTIAL** | CO-12 `co_12_telemetry.py`; `vault/ceps/events.jsonl`; PM-03 bus; GK-08 session writeback; `pp_agents/signals/*` | HIGH | Medium — a second telemetry accountant is forbidden (FD-07 Invariant 1, CO-12 honesty rule) | **RESIDUE — extend CO-12 with a decision-provenance record; never a second instrument** |
| DS03 | Claim–Evidence–Reality Graph | **EXISTS_UNDER_DIFFERENT_NAME** | ACIS E0–E7 ladder; DAIF-01 Part VIII confidence lattice; `epistemic_algebra.py` (`fact_grade_permitted` makes "an inference may never be typed as a fact" executable); DRK-03 evidence burden; Crawl OS DS10 Evidence Provenance (25 Parts SEALED) | HIGH | **Severe** | **REJECT — compose the four existing owners** |
| DS04 | Cognitive Failure Lineage / Defect Genealogy | **EXISTS_BUT_PARTIAL** | CLAE **Part XXI Failure Modes and Failure Lineages** ("six lineages traced to their terminals; treat the earliest reachable link"); `cascade_prevention` A→B→C chains; `vault/ceps/patterns.db`; DRK-05 decision genome and precedent registry | HIGH | Medium | **RESIDUE — a persisted per-incident lineage object; the doctrine already exists in CLAE XXI** |
| DS05 | Failure Ontology and Archetype Registry | **DUPLICATED** | `root_cause_taxonomy.md` CLASE 0–5 ranked by *observed* recurrence; CEPS 9-category taxonomy; IAS-D2 seven pathogen classes with mutation-surviving fingerprints; CLAE Part XXII **99 traps**; UKDL; 156 hard rules | HIGH | **Severe** — the proposal's ~50 archetype names are a vocabulary over an existing corpus | **REJECT as a family — EXTEND the existing taxonomy with any archetype the corpus lacks** |
| DS06 | Predictive Defect Intelligence / Latent Enumeration | **EXISTS_BUT_PARTIAL** | `sweep_enforcer/rule_sweep.py` — *runs* the sweep at seal time against the live tree and refuses a rule that fixed only its triggering file; IAS-D2 exposure scanner; `unknown_unknown_generator.py` majority-absence over a discovered cohort; DRK `proactive_scanner.py`; SQI `weakening_detectors.py` | HIGH | High | **EXTEND `sweep_enforcer` — it already answers "where else did we make this decision"** |
| DS07 | Counterfactual Reliability and Historical Replay | **EXISTS_AND_COMPLETE** | **DRK-04 Counterfactual Simulation and Horizons** (4,147 w, 3-trajectory, adaptive horizons); `accountability.py` prediction→outcome scoring with reasoning/execution/luck/context separation; IAS-F3 Digital Twin governance-impact simulation; the rule-effect harness shipped as IGEF residue `9df175b` | HIGH | **Severe** | **REJECT** |
| DS08 | Mutation and Adversarial Defect Laboratory | **EXISTS_BUT_PARTIAL** | SQI `weakening_detectors.py` + `redteam_protocol.py`; IAS-D2 failure-mutation intelligence; `auto-testing/detectors.py`; `evolution_engine.py` (mutates knowledge assets, not code) | HIGH | Medium — nothing executes code-level mutants and reports a kill rate | **RESIDUE — narrow: a historical-family kill-rate instrument over the existing detectors** |
| DS09 | Preventive Gate and Reliability Policy Compiler | **EXISTS_AND_COMPLETE** | `modules/rule_compiler/schema.py` (admission + placement, 156 rules); `hard_rules/extractor.py`; `tools/bug_to_hardrule.py`; the digest router | HIGH | **Severe** — IGEF was struck on 2026-07-29 for proposing exactly this | **REJECT** |
| DS10 | Crawl OS Constitutional Architecture | **EXISTS_AND_COMPLETE** | `crawl_os_01_constitutional_architecture.txt`, **25/25 Parts SEALED**, 32,888 w, commit `c8772b5` | HIGH | **Severe** — forking an in-flight family | **REJECT** |
| DS11 | Multi-Engine Acquisition and Browser Runtime | **EXISTS_BUT_PARTIAL** | Crawl OS DS03 Adaptive Acquisition Strategy Routing **SEALED** (25/25); DS04/05/06 are the family's *named next actions* in `CRAWLOS_RESUMPTION.md` | HIGH | **Severe** | **REJECT — this is Crawl OS's own queue** |
| DS12 | Evidence Intelligence, Provenance, Digital Evidence Objects | **EXISTS_AND_COMPLETE** | `crawl_os_10_evidence_provenance_integrity_fabric.txt`, **25/25 SEALED**, 33,665 w, commit `dd5c9d2` | HIGH | **Severe** | **REJECT** |
| DS13 | Structural Content Validation and Extraction Integrity | **EXISTS_BUT_PARTIAL** | Crawl OS DS01 Part V §5.9 charter + DS10 anomaly-signal taxonomy; the source's own `EMPTY_PAGE_ACCEPTED_AS_CONTENT` family is a Crawl OS failure class | MEDIUM | High | **REJECT — belongs to Crawl OS** |
| DS14 | Temporal Truth, Change Intelligence, Knowledge Freshness | **EXISTS_BUT_PARTIAL** | Crawl OS Change Intelligence (chartered); **DAIF-21 Reality Synchronization and Semantic Change** SEALED, 36,331 w | HIGH | **Severe** | **REJECT** |
| DS15 | Institutional Anti-Defect Knowledge Compiler | **EXISTS_UNDER_DIFFERENT_NAME** | **FD-03** — ACIS states verbatim: *"FD-03 IS this system"*; it already routes every insight to Hard Rule / Process Rule / Trap / dataset Part / benchmark / prompt fragment / discard | HIGH | **Severe** | **REJECT** |
| DS16 | Knowledge Vault Causal Memory Architecture | **EXISTS_AND_COMPLETE** | `graphify` GK-00…12, 1,190 live coordinates, typed edges, GK-04 write-back; DAIF-01/02 typed representations | HIGH | **Severe** | **REJECT** |
| DS17 | Active Preventive Retrieval and Context Compilation | **EXISTS_AND_COMPLETE** | GK-06 Route Compiler; `jit_skill_loader.py`; `gatekeeper-semantic.js`; `akos_knowledge` injector; **DAIF-08 Context Assembly and Mission Runtime** 40,125 w | HIGH | **Severe** | **REJECT** |
| DS18 | Negative Institutional Knowledge / Anti-Recurrence | **EXISTS_AND_COMPLETE** | `modules/osa/never_again.py` + `never_again_log.jsonl`; CLAE Part XXII traps; UKDL Traps; DRK-05 decision anti-patterns | HIGH | **Severe** | **REJECT** |
| DS19 | MegaCycle OS Constitutional Architecture | **MISSING (mechanism partial)** | No owner by name (3 corpus hits, all in planning files). Partial mechanism: `backlog_autopilot` (a 55-line scoring function, **no lifecycle**), `owner_queue`, `evolution_engine`, DRK `proactive_scanner` | HIGH | Low | **RESIDUE — strongest candidate** |
| DS20 | Institutional Improvement Opportunity Graph | **EXISTS_BUT_PARTIAL** | `backlog_autopilot.what_now` ranks a flat list; `owner_queue` escalates; IAS-B1 leverage discovery + IAS-C2 demand forecasting govern ensemble leverage | HIGH | High vs IAS-B1/C2 | **EXTEND `backlog_autopilot` — a graph, not a rival ranker** |
| DS21 | Multi-Horizon Prediction and Campaign Compilation | **EXISTS_BUT_PARTIAL** | DRK-04 owns adaptive temporal horizons; IAS-C2 owns demand forecasting; no campaign object exists | HIGH | High | **RESIDUE — the campaign object only** |
| DS22 | Cycle Promotion, Constitutionalization, Entropy Control | **MISSING (partially pre-answered)** | `rule_compiler` M4's live predicate is already risk-weighted (`CRITICAL or recurrence >= 3`), so the "recurrence alone must not promote" critique is *partly* already satisfied; no cycle lifecycle exists | HIGH | Low | **RESIDUE** |
| DS23 | MegaCycle Execution, Verification, Reality Governance | **EXISTS_BUT_PARTIAL** | `done_gate`, `output_contracts` (OQS ≥ 70), CLAE Part XXV 19 gates → 4 lifecycle points, `liveness` | HIGH | High | **REJECT — verification is owned; only the cycle's own scorecard is residue** |
| DS24 | Meta-Cycle Governance and Self-Evolution | **EXISTS_BUT_PARTIAL** | `evolution_engine.py` proposes and never applies (`T-FIOS-EVOLUTION-LOCK-001`); DRK-07 self-evolution; IAS-G1 topology optimization | HIGH | High | **FOLD into DS19–22 residue** |
| DS25 | Cross-Project Immunity and Federated Learning | **EXISTS_AND_COMPLETE** | **IAS-D2**, 25 Parts / 36,040 w, whose stated distinct object is verbatim *"CROSS-PROJECT IMMUNITY"*, with a written boundary against `cascade_prevention`, `osa`/CEPS, `hard_rules`, `secret_firewall`, `refcheck`, `sweep_enforcer`. Plus CEPS project→global promotion and `tools/dataset_enricher.py` cross-project escalation (commit `cf4f163`, 2026-07-31) | HIGH | **Severe — this is the proposal's own headline capability, already owned at 25 Parts** | **REJECT** |
| DS26 | Production Reality, Institutional DONE, Completion Governance | **EXISTS_AND_COMPLETE** | `done_gate`; `output_contracts` OQS; **DAIF-07 Obligation Lifecycle and Work Completion Authority** 38,435 w; CLAE Part XXV; HR-OUTPUT-002/003; the Reality Contract | HIGH | **Severe** | **REJECT** |
| DS27 | Reliability Economics, Cost Governance, ROI | **EXISTS_AND_COMPLETE** | CO-00/01/02; `cost_collapse`; `recall_roi`; `token_irr.py`; IAS-C1/C2; `corpus_roi` | HIGH | **Severe** | **REJECT** |
| DS28 | Evaluation, Benchmarking, Reliability Measurement | **EXISTS_AND_COMPLETE** | SQI (`run_sqi.py` exits non-zero on a silent decrease, 45/45 ×3); CLAE Part XXIV; `vault/benchmarks`; `bench_all.py` | HIGH | **Severe** | **REJECT** |
| DS29 | Security, Privacy, Authorization, Sovereignty | **EXISTS_AND_COMPLETE** | `secret_firewall` (7 sealed HRs, URB redaction bus); **Crawl OS DS16 Authorization, Compliance and Safety** 25/25 SEALED, ~34,733 w, zero-hit contamination baseline | HIGH | **Severe** | **REJECT** |
| DS30 | Agent, Hooks, Skills, Runtime Integration | **EXISTS_AND_COMPLETE** | `modules/liveness/reachability.py` + `reachability_registry.json`; `hook-dispatcher.js`; `skill_router`; `harness` | HIGH | **Severe** | **REJECT** |
| DS31 | Deployment, Operations, Observability, Recovery | **EXISTS_AND_COMPLETE** | `deployment`, `monitoring`, `rollback`, `session_resilience`, `zero-crash`, IAS-E1/E2, `governance/DEPLOY_GOVERNANCE.md` | HIGH | **Severe** | **REJECT** |
| DS32 | AIEF Integration | **CONFLICTING_OWNER** | same as DS01 | HIGH | **Severe** | **REJECT** |
| DS33 | Constitutional Laws, Standards, Governance Compendium | **EXISTS_AND_COMPLETE** | 156 compiled hard rules + digest router; `governance/*`; `ukdl-universal.md`; `CLAUDE.md` router | HIGH | **Severe** | **REJECT** |
| DS34 | Reference Scenarios, Failure Campaigns, Casebooks | **EXISTS_BUT_PARTIAL** | `session_lessons.md`; `scs/` C44…C95; `vault/plans/*` audits; `never_again_log.jsonl` | HIGH | Medium | **RESIDUE — the canonical negative-fixture set, including the ABI-layout case; a fixture set, not a family** |
| DS35 | Evolution Roadmap, Maturity Model, Future Research | **EXISTS_AND_COMPLETE** | ACIS E0–E7 ladder with the No-Autopromotion Invariant; DAIF 12-state lifecycle; D2A maturity; `ROADMAP.md` | HIGH | **Severe** | **REJECT** |

## Tally

| Disposition | Count |
|---|---|
| **REJECT** (owned at equal or greater maturity) | **26** |
| **EXTEND** an existing owner | **3** (DS06, DS20, plus DS05's archetype delta) |
| **RESIDUE** — genuine, unowned, worth building | **6 rows collapsing to 4 work items** (DS02, DS04, DS08, DS34 as fixtures; DS19/21/22/24 as one cycle-lifecycle item) |
| Measured as already owned | **~83 %** |

This lands inside the estate's own measured base rate: six prior proposals scored
55–80 % owned, and of 22–30 candidates in each, 0–1 survived as a family.
