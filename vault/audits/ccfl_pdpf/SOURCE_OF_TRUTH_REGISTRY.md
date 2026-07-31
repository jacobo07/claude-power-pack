---
title: CCFL-PDPF STOP #1 — Source of Truth Registry
date: 2026-07-31
rule: one object, one canonical owner. Every other family references it with context; none re-narrates it.
---

# Source of Truth Registry

For each object the CCFL-PDPF proposal touches, the canonical owner and the relation any
future work must take toward it. Relations: `OWNS` · `CONSUMES` · `PRODUCES` ·
`MAY_TRIGGER` · `MUST_NOT_OWN` · `MUST_NOT_DUPLICATE` · `SOURCE_OF_TRUTH` · `ENFORCEMENT_POINT`.

| Object | Canonical owner | Path | Any new work's relation |
|---|---|---|---|
| Cross-project immunity, pathogen fingerprints, exposure, quarantine, immunization | **IAS-D2** | `vault/knowledge_base/cpp_ias/04_SYSTEM_ECOLOGY_IMMUNOLOGY/ias_d2_immune_system.txt` | `MUST_NOT_OWN` · `PRODUCES` raw material into it |
| The ensemble as a first-class object; advantage algebra | **IAS-F1 / F2** | `vault/knowledge_base/cpp_ias/` | `MUST_NOT_OWN` |
| Institutional digital twin and simulation | **IAS-F3** | same | `MUST_NOT_DUPLICATE` |
| Ensemble observability and reliability | **IAS-E1 / E2** | same | `CONSUMES` |
| External evidence acquisition, Evidence Objects, provenance, authorization | **Crawl OS** | `vault/knowledge_base/crawl_os/` | `MAY_TRIGGER` a mission · `MUST_NOT_OWN` acquisition |
| Typed cognitive representations, obligation lifecycle, work-completion authority, context runtime, reality sync | **DAIF** | `vault/knowledge_base/d2a_fabric/` | `CONSUMES` types · `MUST_NOT_OWN` |
| Epistemic status of a claim (E0–E7), falsifier discipline, no-autopromotion | **ACIS** | `vault/knowledge_base/acis/` + `modules/decision_review/epistemic_algebra.py` | `SOURCE_OF_TRUTH` for confidence · `MUST_NOT_DUPLICATE` |
| Decision authentication, reversibility, blast radius, counterfactual horizons, precedent memory, prediction→outcome attribution | **DRK** | `vault/knowledge_base/decision_review/` + `modules/decision_review/` | `CONSUMES` · `MUST_NOT_OWN` |
| Measurement against an external reference: delta, distance, floors, oracle, deviation, closure; failure-mode lineage doctrine; traps; production-reality gates | **CLAE** | `vault/knowledge_base/clae/` | `CONSUMES` the lineage doctrine · `MUST_NOT_DUPLICATE` Parts XXI/XXII/XXV |
| Insight → Hard Rule / Process Rule / Trap / Part / benchmark / prompt fragment / discard | **FD-03** | `vault/knowledge_base/fable_distillation/` | `MUST_NOT_OWN` — ACIS already ruled this DO-NOT-BUILD |
| Rule admission and placement; retirement class registry | **`rule_compiler`** | `modules/rule_compiler/schema.py`, `digest.py` | `PRODUCES` candidate rules into it |
| Sealed production-bug contracts (156 rules) | **`hard_rules`** | `vault/hard_rules/` + `CLAUDE.md` router | `ENFORCEMENT_POINT` |
| In-session cascade detection and dangerous-action blocking | **`cascade_prevention`** | `modules/cascade_prevention/` | `CONSUMES` its detections |
| Per-session error events, recurrence counts, project→global promotion | **CEPS** | `vault/ceps/` | `SOURCE_OF_TRUTH` for observed incidents |
| Negative institutional knowledge / anti-recurrence | **`osa`** | `modules/osa/never_again.py`, `vault/osa/never_again_log.jsonl` | `PRODUCES` into it |
| Root-cause classes ranked by observed recurrence | **`root_cause_taxonomy.md`** | `vault/knowledge_base/root_cause_taxonomy.md` | `SOURCE_OF_TRUTH` for the archetype layer |
| "Where else did we make this decision" — live-tree sweep at seal time | **`sweep_enforcer`** | `modules/sweep_enforcer/rule_sweep.py` | `ENFORCEMENT_POINT` for sibling search |
| Executable-reality verification, weakening detection, red-team | **SQI** | `modules/sqi/`, `tools/run_sqi.py` | `CONSUMES` |
| Session cost, budget, routing, **the single telemetry instrument** | **CO-00…CO-14** | `modules/cognitive_os/co_12_telemetry.py` | `PRODUCES` signals into CO-12. A parallel accountant is forbidden (FD-07 Invariant 1) |
| Knowledge location, coordinate graph, typed edges | **`graphify`** | `modules/graphify/`, GK-00…12 | `CONSUMES` · `PRODUCES` edges via GK-04 |
| Reachability of a declared capability from a live surface | **`liveness`** | `modules/liveness/reachability.py` | `ENFORCEMENT_POINT` |
| Completion gating, output quality score | **`done_gate` / `output_contracts`** | `modules/done_gate/`, `modules/output_contracts/` | `ENFORCEMENT_POINT` |
| Duplication disposition (reinforce / extend / compose / extract / sovereign) | **D2A** | `modules/duplicate_to_advantage/d2a_engine.py` | `SOURCE_OF_TRUTH` for this audit's own dispositions |
| Frontier session execution, absence discovery, KB mutation proposals | **FIOS** | `modules/frontier_intelligence/` | `CONSUMES` |
| Credential defence and redaction | **`secret_firewall`** | `modules/secret_firewall/` | `ENFORCEMENT_POINT` |

## Boundary the prompt asked to be verified rather than assumed

The prompt supplied a proposed boundary set (Crawl OS / Evidence Intelligence Fabric /
CCFL-PDPF / Knowledge Vault / Anti-Defect Knowledge Compiler / MegaCycle OS / AIEF).
Measured against the repository:

- **Crawl OS** — confirmed, and further along than the prompt assumes (5 datasets sealed).
- **Evidence Intelligence Fabric** — **not a separate owner.** It is Crawl OS Dataset 10,
  sealed at 25 Parts. Treating it as a peer system would split one sealed dataset into two.
- **Knowledge Vault** — confirmed, but its governed-truth layer is distributed across
  `graphify` (location), UKDL (rules/traps), ACIS (epistemic status), and DAIF (types).
  There is no single "Vault" owner to extend; there are four.
- **Institutional Anti-Defect Knowledge Compiler** — **already FD-03.** Ruled DO-NOT-BUILD
  by ACIS on 2026-07-11.
- **MegaCycle OS** — no owner. The only boundary in the prompt's list that survives.
- **AIEF** — **collides with CPP-IAS**, which already occupies the ensemble level.
- **CCFL-PDPF** — its stated object collides with IAS-D2 at the cross-project layer and
  with CLAE Part XXI at the lineage layer; what survives is listed in
  `PROPOSED_DATASET_FAMILY.md`.
