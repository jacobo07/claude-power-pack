---
title: USIRC STOP #1 — Ownership and Overlap Audit
date: 2026-07-31
verdict_source: CAPABILITY_MATRIX_A_TO_F.md + CAPABILITY_MATRIX_G_TO_M.md
---

# Ownership and Overlap Audit

## 1. The finding that decides this STOP

The source's own founding claim is:

> *"Claude Power Pack ya tiene gran parte de los órganos necesarios, pero no tiene un
> propietario unificado del proceso 'evidencia externa → reconstrucción completa →
> réplica ejecutable → prueba de fidelidad'."*

**That claim is correct, and it is also the whole of what survives.** Measured against
a discovered denominator of 1,350 files, 75 modules and 26 dataset families:

- Every **organ** the pipeline needs has an owner, at greater maturity than the source
  assumes: evidence acquisition and authorization (`crawl_os`, 5 datasets SEALED,
  ~117k words), fidelity and behavioral equivalence (**DAIF-03**, 20 Parts, 38,694 w),
  measurement against an external reference (**CLAE**, 26/26 SEALED), causal
  investigation (`craif`), counterfactual simulation (**DRK-04**), replay
  (`tools/replay_harness.py`), runtime truth (`omnicapture`), oracles (`modules/oracle`
  + OVO), production-reality gating (**CLAE Part XXV**, 19 gates), epistemic status
  (**ACIS** E0–E7 + the No-Autopromotion Invariant).
- What is genuinely absent is **not a civilization and not 160 datasets**. It is three
  things, each of which is a schema or an instrument: a typed model of an external
  running product (C1), a comparison instrument for rendered artifacts (D3), and a
  two-execution alignment for earliest-divergence (G2).

A missing *control plane* over owned organs is an integration problem. This estate has
struck three families in the past five days for exactly this shape.

## 2. Overlap against every system the prompt named

The prompt enumerated 40+ systems to check. All were probed. None is absent.

| Named system | Verdict | Evidence |
|---|---|---|
| Duplicate-to-Advantage | Owns build/reuse/extend/compose; root law `PR-DUPLICATE-TO-ADVANTAGE-001` | `modules/duplicate_to_advantage/`, `D2A_INDEX.md`, engine 25/25 gates |
| Ownership Audit | Owns this very procedure; nine prior executions on record | `COMPENDIUM_CLOSURE_REPORT.md`, `vault/plans/*-audit-*.md` |
| Liveness | Owns reachability of a declared capability from a real surface | `modules/liveness/reachability.py` + registry |
| CDIO | Owns design **quality** scoring; explicitly **not** fidelity to a reference | `modules/cdio/`, `vault/knowledge_base/cdio/`, `hooks/cdio_visual_advisory.js` |
| video analysis | Owns download, frames, transcript, vision scoring — nothing temporal | `modules/autoresearch/video_analyzer.py`, read this session |
| autoresearch | Owns competitive intelligence, 3–4× daily | `modules/autoresearch/` |
| replay harness | Owns deterministic replay + MATCH/DIFF/SHIM_ERROR/SKIPPED + aggregate verdicts | `tools/replay_harness.py`, `vault/forensic/REPLAY_SCHEMA.md` |
| OmniCapture | Owns runtime reality: errors, telemetry, network, performance, state dumps | `modules/omnicapture/` |
| OVO and oracle infrastructure | Owns the oracle protocol and three executable oracles | `modules/oracle/ovo-protocol.md`, `tools/oracle_{delta,chaos,cascade}.py` |
| auto-testing · SQI · sleepless QA | Own test generation, executable-reality verification, weakening detection, red-team, baseline guardian, evidence bundles from a running app | `modules/{auto-testing,sqi,sleepless_qa}/`, `run_sqi.py` |
| baseline guardian · weakening detection | Owned inside SQI | `modules/sqi/weakening_detectors.py` |
| done gates · output contracts · zero-issue gates | Own completion | `modules/{done_gate,output_contracts}/`, OQS ≥ 70, HR-OUTPUT-001…003 |
| mirror discovery · mirror parity | Own installed-vs-repo parity. **Correctly identified by the source as a conceptual false positive** — they do not govern product replicas | `modules/mirror_discovery/`, `vault/standards/mirror-parity-law.md` |
| digital twins · IAS | Own the **institutional** twin of PP itself | `cpp_ias` F3, 32,802 w |
| KADOS | **DOES NOT EXIST** in this repo | one mention repo-wide, in `vault/plans/ksf-compendium-2026-07-26.md` |
| CRAIF | Owns causal investigation completeness; conformance checker live at 7/8, exit 1 | `modules/craif/`, `/craif-conformance` |
| causal reconstruction · forensic probes | Owned by CRAIF + CEPS + `vault/forensic/` + `root_cause_taxonomy.md` CLASE 0–5 | read this session |
| arch-decision · decision review | Own architectural decisions and decision soundness; **DRK-04 counterfactual** | `modules/{arch-decision,decision_review}/` |
| dataset-first | Owns whether a dataset is needed at all | `modules/dataset_first/transduction.py` |
| AKOS knowledge · knowledge capture | Own external-knowledge distillation | `modules/akos_knowledge/` |
| UQF · evidence-first · provenance | Own code quality, the false-positive catalog, and evidence provenance | `modules/uqf/`, crawl_os DS10 (`provenance` in 122 files) |
| context compilation | Owned by DAIF-08 + `graphify` GK-06 + `jit_skill_loader` | manifest read |
| production reality | Owned by CLAE Part XXV + the Reality Contract + `scaffold-auditor.js` | 49 files |
| SDD-OS · spec gate | Own T0–T3 classification and the spec gate | `modules/{sdd_os,spec_gate}/` |
| DAIF | Owns typed representations, **fidelity and loss budget**, obligations, context runtime, reality sync. 8/8 SEALED, 160 Parts | `d2a_fabric/DAIF_INDEX.md` |
| cascade prevention | Owns the in-session dangerous-action gate, 5 HR-CASCADE rules | `modules/cascade_prevention/` |
| agent orchestration | Owned by `agent-governance` + `pp_agents` + `parallel_mesh` | 12 repo-local agents |
| knowledge graphs | Owned by `graphify`; **no second graph permitted** | GK-00…12, 1,190 coordinates |
| institutional learning · failure taxonomies | Owned by FD-03, CEPS, `never_again_log.jsonl`, `root_cause_taxonomy.md`, CLAE Part XXII (99 traps) | read this session |
| migration | **No owner — and no consumer.** PP has no legacy-migration surface | measured |
| observability | Owned by `omnicapture` + `cpp_ias` observability fabric + CO-12 | |
| memory systems | Owned by `memory-engine` + DAIF-08 + `cognitive_os` residency | |
| capability registries | Owned by `liveness` registry + `cpp_ias` capability economics | |

**Of 34 named systems, 32 hold territory the proposal claims. One (KADOS) does not
exist. One (migration) is absent and has no consumer.**

## 3. Systems the proposal treats as new that are demonstrably in flight

1. **Evidence acquisition (prompt DS09–16).** `crawl_os` is not a proposal. It is an
   approved 19-dataset family with 5 sealed datasets, a live `CRAWLOS_RESUMPTION.md`,
   a hermetic 22-gate suite (`tools/test_crawl_os.py`) and **DS04 named as its next
   action**. Building DS09–16 forks an active build mid-flight.
2. **Fidelity (prompt DS29–43).** DAIF-03 is sealed at 20 Parts and, by an explicit
   Owner ruling recorded in its own §1.7, **absorbed the canonical Metric-Authority
   candidate**. A second fidelity authority is prohibited, not merely redundant.
3. **The reconstruction compiler (prompt DS44–57).** ACIS-00's overlap table already
   records the verdict: *"Knowledge-to-Production Compiler → REFERENCE — do not build
   — FD-03 IS this system."* Re-proposing it is the second occurrence of a decision
   already taken.
4. **Differential QA (prompt DS58–71).** CLAE Part XXV consolidated 19
   production-reality gates and Part XXII catalogued 99 traps on 2026-07-29 — two days
   before this proposal was submitted.

## 4. Absorption-bias check

`T-OWNERSHIP-AUDIT-ABSORPTION-BIAS-001` warns that title-tier verdicts move in one
direction. Three corrections applied:

- Every `EXISTS_*` verdict cites a file opened this session or a measured hit count.
  Rows resting on a family name plus a count are marked MEDIUM in the matrices, and
  there are 11 of them.
- The five `MISSING` verdicts were *sought* rather than assumed: D3 was tested by
  opening all three visual surfaces in the estate; B8 by reading `video_analyzer.py`;
  G2 by reading what `replay_harness` actually compares. A `MISSING` reached by not
  finding a word would be the same defect in the opposite direction.
- The inherited denominator defect is carried forward: `cpp_ias`'s own
  `13_REGISTRIES/SYSTEM_REGISTRY.md` omits DAIF and Crawl OS, so IAS-versus-DAIF
  overlap has never been tested at content tier. This does not weaken any verdict
  above — every crawl_os and DAIF row rests on those families' own body text or
  manifest, never on the IAS registry.
