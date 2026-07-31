---
title: USIRC STOP #1 — Capability Overlap Matrix, categories A–F
date: 2026-07-31
continues_in: CAPABILITY_MATRIX_G_TO_M.md
rule: one row per MECHANISM the source names, never per section title. Every verdict
  cites an artifact opened this session or a measured count. A row resting on a family
  name plus a count is marked MEDIUM and says so.
verdicts: EXISTS_AND_COMPLETE · EXISTS_BUT_PARTIAL · EXISTS_UNDER_DIFFERENT_NAME ·
  EXISTS_BUT_UNWIRED · DECLARED_BUT_ORPHANED · CONFLICTING_OWNER · DUPLICATED ·
  MISSING · DEPRECATED · UNKNOWN_REQUIRES_EVIDENCE
note: the source numbers its sections in roman numerals; they are cited here in decimal,
  because some roman forms trip this estate's literal write-gate — a documented false
  positive in governance/KNOWN_FALSE_POSITIVES.md.
---

# Capability Overlap Matrix — A to F

Categories A–M are the prompt's own coverage obligation. "sec N" cites the source
document's numbered section.

## Category A — Constitution, authority, epistemology (prompt DS01–08)

| # | Mechanism (source) | Verdict | Owner, verified | Conf |
|---|---|---|---|---|
| A1 | Six epistemic classes: Observed · Measured · Derived · Hypothesized · Required · Verified (sec 2) | **EXISTS_UNDER_DIFFERENT_NAME** | `acis` ladder **E0–E7** + falsifier discipline + `epistemic_ladder.py`; term `epistemic` hits 40+ files | HIGH |
| A2 | "No hypothesis may silently degrade into a fact" (sec 2, second law) | **EXISTS_AND_COMPLETE** | ACIS **No-Autopromotion Invariant**. Independently re-derived by DAIF-03 §4.5 as **epistemic laundering**, a strict-zero-tolerance REFUSE — read in full this session | HIGH |
| A3 | Epistemic Admission Gate — no claim enters canon without provenance, scope, version | **EXISTS_AND_COMPLETE** | DAIF-03 §1.6 duty to refuse + §4.5; CO-12 **Telemetry-Before-Claims**; crawl_os DS10 provenance chain | HIGH |
| A4 | Epistemic Debt with severity, owner, repayment plan (sec 41) | **EXISTS_BUT_PARTIAL** | CLAE Part IX names **three debts — quality, measurement, instrument** — with a disposition per unverified item; DRK-05 institutional debt; ACIS E0. Gap: no single per-incident debt object carrying a repayment plan | HIGH |
| A5 | Reconstruction Authorization Manifest — ownership, permitted sources, permitted techniques, secrets excluded, retention, output policy (sec 23) | **EXISTS_AND_COMPLETE** | **crawl_os DS16 Authorization, Compliance and Safety** — 25 Parts, ~34,733 w, SEALED: four-stage adjudication, "possession is not permission", three-class restricted-action taxonomy, operator approval, data-minimization ceiling, audit trail, re-adjudication | HIGH |
| A6 | Reconstruction Confidence Economy — confidence rises and falls by evidence class (sec 40) | **EXISTS_UNDER_DIFFERENT_NAME** | crawl_os DS10 confidence + DRK-03 evidence *burden* as f(reversibility, blast radius) + ACIS ladder. DRK-03 explicitly separates evidence level from evidence burden to stop exactly this substitution | HIGH |
| A7 | Mission-Specific Truth Kernel (sec 93) | **DUPLICATED** | crawl_os **DS02 Crawl Mission Contract** — 16 fields: objective, entities, sources, depth, freshness, required evidence, permitted domains, max cost, stop conditions, output schema, confidence requirement — plus `one_shot` contract and DAIF-08 mission runtime | HIGH |
| A8 | Anti-Hallucination Architecture — what evidence, what inference, what falsifies (sec 92) | **EXISTS_AND_COMPLETE** | ACIS falsifier discipline + code-review **Proof Triad** (snippet + scenario + why-guards-fail, `rules/common/code-review.md`) + UQF | HIGH |
| A9 | Independent Oracle Principle — the generator may not be the sole verifier (sec 91) | **EXISTS_AND_COMPLETE** | CLAE **Part XVI Human Oracle Boundary** ("the self-verification limit") + **Part XVII Oracle Routing**; ACIS `T-ACIS-MODEL-CONSENSUS-001`: "E3→E4 needs a different actor, not consensus among agents of the same model" | HIGH |
| A10 | Reconstruction Memory Hierarchy L0 raw → L6 decision intelligence (sec 96) | **EXISTS_UNDER_DIFFERENT_NAME** | DAIF-02 **twelve CIRs** (CIR-0 locators … CIR-11) + `cognitive_os` CO-13/14 residency + FD-03 promotion routing | HIGH |

**Category A: 0 of 8 chartered datasets survive. 10 of 10 mechanisms owned.**

## Category B — Evidence and acquisition (prompt DS09–16)

| # | Mechanism | Verdict | Owner, verified | Conf |
|---|---|---|---|---|
| B1 | Evidence Adapter Protocol — one envelope per adapter (source, timestamp, provenance, licence, integrity, scope, confidence, limitations) | **EXISTS_AND_COMPLETE** | crawl_os **DS03** uniform adapter interface — discover/map/fetch/render/interact/extract/normalize/validate/persist/replay — plus DS01's Evidence Object schema (Part VII) | HIGH |
| B2 | Evidence Ledger, with the Observation as the atomic unit | **EXISTS_AND_COMPLETE** | crawl_os **DS10 Evidence Provenance and Integrity Fabric**, 25 Parts, 33,665 w: lifecycle state machine, provenance-chain assembly, dual-hash, chain of custody, tamper evidence, supersession, dispute resolution, replay, negative evidence | HIGH |
| B3 | Active Evidence Acquisition Planner — design the most informative next experiment; rank by gain × importance × risk ÷ cost (sec 12) | **EXISTS_BUT_PARTIAL** | crawl_os **DS03 Adaptive Acquisition Strategy Routing**: attempt-cheapest-first seven-rung ladder, observed-reason discipline gating every escalation, site memory, de-escalation. Gap: DS03 escalates on an *observed failure reason*; it does not rank a *hypothesis-discriminating* experiment | HIGH |
| B4 | Evidence Compression Without Meaning Loss (sec 95) | **EXISTS_AND_COMPLETE** | **DAIF-03** is precisely this dataset — "a compilation that cannot demonstrate fidelity does not ship" — plus AKOS distillation. Read in full this session | HIGH |
| B5 | Evidence Invalidation Graph — a new version invalidates screenshots, baselines, tests, hypotheses (sec 62) | **EXISTS_UNDER_DIFFERENT_NAME** | **DAIF-21 Reality Synchronization and Semantic Change**, 20 Parts, 36,331 w, SEALED | MEDIUM — manifest read, body not opened this session |
| B6 | Change Intent Classifier — evolution / regression / environment variance / data variance / rendering variance / unknown (sec 64) | **EXISTS_BUT_PARTIAL** | DAIF-21 + `tools/replay_harness.py` verdict classes (MATCH/DIFF/SHIM_ERROR/SKIPPED) + CEPS taxonomy. Gap: no rendering- or data-variance discrimination, because no rendering comparison exists (see D3) | MEDIUM |
| B7 | Session evidence from a **running application**: DOM, CSSOM, accessibility tree, HAR, WebSocket, storage, input timeline | **MISSING — but already chartered** | crawl_os **DS05 Browser Interaction** is named in DS03's forward-compatibility boundaries as *not yet built*. An unbuilt Part of an ACTIVE family, not a gap for a new one | HIGH |
| B8 | Video adapters: state-change segmentation, interaction detection, temporal alignment, transition extraction, input-to-output correlation | **MISSING** | `modules/autoresearch/video_analyzer.py` read this session: ffmpeg frames at fixed intervals, transcript, vision scoring. Zero segmentation, zero transition extraction, zero temporal alignment | HIGH |

**Category B: 0 of 8 chartered datasets survive.** Building DS09–16 would **fork
`crawl_os` mid-flight** — that family has a live resumption file and a named next
action (DS04). B7 and B8 are the residue, and B7 belongs to crawl_os by charter.

## Category C — Universal System Model (prompt DS17–28)

| # | Mechanism | Verdict | Owner, verified | Conf |
|---|---|---|---|---|
| C1 | A node and edge ontology over an **external observed product** (Product, Capability, Surface, State, Transition, Contract, Invariant, FailureMode, RecoveryPath, Evidence, Hypothesis, Test, Oracle, Divergence, Decision, Opportunity) | **MISSING** | Measured 0 hits for `universal system model` and `reconstruction graph`. The nearest owners model something else: `graphify` models **this repo** (1,190 coordinates); `cpp_ias` models **the PP ensemble**; DAIF-01/02 model **cognitive work**; crawl_os models **external documents**. Nothing types an external *running product* | HIGH |
| C2 | A canonical typed ontology with kinds, strength, scope, lifecycle | **EXISTS_AND_COMPLETE** | **DAIF-01 Cognitive Type System and Canonical Ontology**, 20 Parts, 33,509 w. Any USM must adopt DAIF-01's kind and Strength discipline, never invent a parallel one | HIGH |
| C3 | The model as an intermediate representation that many backends compile from | **EXISTS_AND_COMPLETE** | **DAIF-02 CIR-0…11**, 20 Parts, 34,826 w — "the compilation substrate of Claude Power Pack" | HIGH |
| C4 | A second graph to hold the model | **CONFLICTING_OWNER — prohibited** | `RE_BASELINE_RESUMPTION.md` block 3, standing and unconditional: *"`graphify` owns the semantic IR; it never stands up a second graph."* A USM is node **types** on the existing graph | HIGH |
| C5 | Nine reconstruction layers (surface, interaction, behavioral, state, contract, architecture, operational, intent, evolution) | **EXISTS_BUT_PARTIAL** | contract → DAIF-04 + `contract_fabric`; operational → `omnicapture` + `cpp_ias` observability; intent → DAIF-03 §3.2 CIR-3 intent slots (intention, expected result, explicit and implicit criteria, priorities, prohibitions, non-goals, definition of done); evolution → DAIF-21. The surface, interaction and state layers of an external product: unowned (= C1) | HIGH |
| C6 | Architecture Hypothesis Lattice — competing candidate architectures with discriminating experiments (sec 21) | **EXISTS_BUT_PARTIAL** | `decision_review/epistemic_algebra.py` + DRK-04 three-trajectory counterfactual simulation + the ACIS ladder hold the machinery for competing claims. Gap: no *architecture-candidate* object, no discriminating-experiment scheduler | MEDIUM |
| C7 | Reconstructed Architecture and Target Architecture must never merge (sec 22) | **EXISTS_UNDER_DIFFERENT_NAME** | `arch-decision` + ACIS status separation + DAIF-03 §4.5. The *law* is owned; the two-model artifact is not, because there is no model (= C1) | MEDIUM |

**Category C: 0 of 12 chartered datasets survive. C1 is the strongest genuine gap in
the proposal — and it is one schema, not twelve datasets.**

## Category D — Fidelity and equivalence (prompt DS29–43)

| # | Mechanism | Verdict | Owner, verified | Conf |
|---|---|---|---|---|
| D1 | Fidelity as a multidimensional conjunction, never a single percentage; per-dimension coverage, tolerance, severity, confidence, evidence (sec 10, Fidelity Tensor) | **EXISTS_AND_COMPLETE** | **DAIF-03 §1.4** — ten dimensions, each with its own test, threshold and failure mode; **§1.2 prohibits averaging by name**: "fidelity is not a weighted mean of ten scores; it is a conjunction over ten dimensions". Read in full this session | HIGH |
| D2 | Fidelity Budget — a declared per-mission divergence allowance (sec 11) | **EXISTS_AND_COMPLETE** | DAIF-03 **loss budget** bound to a declared task class (execution carrier / reasoning carrier / orientation carrier), with zero-tolerance kinds enumerated. `fidelity budget` measured in 3 files, all DAIF | HIGH |
| D3 | Visual, geometric and temporal differential instruments: pixel diff, perceptual diff, component-geometry diff, semantic tree diff, tolerance masks, animation timing ±25 ms | **MISSING** | Measured **0 files** for `pixel diff` / `perceptual diff` / `image diff`. The three visual surfaces that exist do something else: `osa/gpu_eyes.py` **captures** (SSH+Xvfb+scrot; `visual_qa_passed=None` when no capture exists); `sleepless_qa/verdict/visual.py` asks a vision model whether **one** screenshot looks broken; `autoresearch/vision_scorer.py` scores an image. **None compares a build against a reference artifact.** All three opened this session | HIGH |
| D4 | Behavioral equivalence — the same outputs under the same inputs | **EXISTS_AND_COMPLETE** | DAIF-03 owns the term (`behavioral equivalence`, 7 files, all DAIF) and defines it as the **definitive** test with nine instrumental proxies; it composes FD-04's six-lens transfer test as its behavioral instrument | HIGH |
| D5 | Contract equivalence | **EXISTS_AND_COMPLETE** | **DAIF-04 Institutional Contract Fabric** (20 Parts, 39,939 w) + `modules/contract_fabric/side_effect_ledger.py` | HIGH |
| D6 | Operational and production equivalence; "production-ready is a verifiable property" (sec 34, sec 24) | **EXISTS_AND_COMPLETE** | **CLAE Part XXV — 19 production-reality gates consolidated to four lifecycle gate points** — plus this repo's Reality Contract and the `scaffold-auditor.js` Stop hook. Measured: `production reality` in 49 files | HIGH |
| D7 | Metric authority — who owns a metric, what it may claim, how it resists Goodhart | **EXISTS_AND_COMPLETE — and explicitly closed** | DAIF-03 §1.7: *"it absorbs, by the Owner's ruling, the canonical Metric-Authority candidate… a fidelity fabric that did not own its own metrics would be a fabric whose numbers anyone could redefine."* Every DAIF-03 metric ships a countermetric. **A second fidelity metric authority is prohibited by a sealed Owner ruling** | HIGH |
| D8 | An F0–F6 fidelity ladder for an observed product | **EXISTS_BUT_PARTIAL** | The ladder's *discipline* is DAIF-03 plus CLAE's distance accounting. Its lower *rungs* — visual, motion, interaction — have no instrument (= D3) | HIGH |

**Category D: 0 of 15 chartered datasets survive. D3 is the second genuine gap — an
instrument class, admissible under CLAE Part XIII's instrument taxonomy.**

## Category E — Reconstruction, compilation, replica (prompt DS44–57)

| # | Mechanism | Verdict | Owner, verified | Conf |
|---|---|---|---|---|
| E1 | Reconstruction Compiler Federation: model → web / desktop / mobile / API / schema / test suite / docs / runbook / dataset / knowledge graph / mission pack (sec 27) | **DUPLICATED — decision already taken** | `acis`-00's own overlap table records the verdict verbatim: *"Knowledge-to-Production Compiler → REFERENCE — do not build — FD-03 IS this system."* Quoted in `vault/audits/ccfl_pdpf/OWNERSHIP_OVERLAP_AUDIT.md` §3.2. FD-03 routes every unit to Hard Rule / Process Rule / Trap / Part / benchmark / prompt fragment / discard | HIGH |
| E2 | Self-Verifying Implementation Mission Pack — context, requirements, constraints, non-goals, evidence, tests, oracles, done gates, prohibited shortcuts (sec 26) | **EXISTS_AND_COMPLETE** | `one_shot` compiled contract (scope / out_of_scope / done_gate / budget; HR-ONESHOT-001…003) + `karimo-harness` PRD ingest + `spec_gate` + `done_gate` + DAIF-07 work-completion authority | HIGH |
| E3 | Proof-Carrying System Artifact — no artifact without the evidence that justifies it (sec 25) | **EXISTS_UNDER_DIFFERENT_NAME** | DAIF-03 **provenance fidelity** (the path back to source must be reconstructible) + crawl_os DS10 chain of custody + CO-12 Telemetry-Before-Claims + the Reality Contract | HIGH |
| E4 | Incremental Proof Milestones, a gate per level (sec 71) | **DUPLICATED** | The DAIF lifecycle `DISCOVERED → … → SEALED` (12 states; only SEALED means finished) + `liveness` classes + the `/ultra` 7-phase gate ladder | HIGH |
| E5 | Reconstruction Completion Standard — Truth / Model / Build / Proof / Institution (sec 72) | **DUPLICATED** | Zero-Issue Delivery + CLAE **Part XX Phase Closure Semantics** (five verdicts; the producer closes accounting, the constituency accepts) + Part XXV gates + `done_gate` + `output_contracts` OQS ≥ 70 | HIGH |
| E6 | Executable System Doppelgänger — a controllable twin that injects faults, alters timing, substitutes dependencies (sec 16) | **EXISTS_BUT_PARTIAL** | `cpp_ias` **F3 Institutional Digital Twin and Simulation** (32,802 w) simulates *PP itself*; `tools/oracle_chaos.py` injects faults. Gap: no twin of an *external* product — downstream of C1, not independent of it | MEDIUM |
| E7 | Universal Reconstruction Protocol, Phases −2 through 12 (sec 73) | **DUPLICATED** | `/ultra` ONESHOT 7 phases + SDD-OS T0–T3 classification + the Phase −3/−2/−1 audit shape this estate has now executed nine times | HIGH |

**Category E: 0 of 14 chartered datasets survive.**

## Category F — QA, testing, differential verification (prompt DS58–71)

| # | Mechanism | Verdict | Owner, verified | Conf |
|---|---|---|---|---|
| F1 | Oracle federation: visual · semantic · behavioral · temporal · data · security · accessibility · recovery · performance · architecture · intent (sec 30) | **EXISTS_BUT_PARTIAL** | `modules/oracle` + `ovo-protocol.md` + `tools/oracle_{delta,chaos,cascade}.py` own the **protocol**; CLAE XVI/XVII own oracle boundary and routing; SQI owns benchmark oracles. The source concedes it itself: *"OVO debe recibir nuevos oráculos… No debe reemplazarse OVO."* The missing oracles are D3's instruments | HIGH |
| F2 | Behavioral replay of ordered sessions; new event types for UI action, stream, interrupt, tool call (sec 6.4) | **EXISTS_BUT_PARTIAL** | `tools/replay_harness.py` + `vault/forensic/REPLAY_SCHEMA.md` own deterministic replay with MATCH/DIFF/SHIM_ERROR/SKIPPED and aggregate verdicts. The source's own instruction: *"Debe extender el Replay Harness existente, no reemplazarlo."* New event types are a schema EXTEND | HIGH |
| F3 | Reality Mutation Testing — slow network, outage, stale cache, clock skew, duplicated and reordered events, expired credential, memory pressure (sec 33) | **EXISTS_UNDER_DIFFERENT_NAME** | `tools/oracle_chaos.py` + SQI `redteam_protocol.py` + `cascade_prevention/pre_mortem.py` | MEDIUM |
| F4 | Architecture Contract Testing — no component reads a source it does not own; every external dependency has a timeout; every irreversible operation confirms (sec 34) | **EXISTS_AND_COMPLETE** | This repo's Hard Rules already assert these verbatim (`core.md`: "Every external call: finite timeout, retry > 0, error handler") + `contract_fabric` + `sweep_enforcer`, which refuses a rule that fixes only its triggering file | HIGH |
| F5 | Journey-level QA — the unit of test is a mission, not a page (sec 32) | **EXISTS_UNDER_DIFFERENT_NAME** | `sleepless_qa` dumpers (web / cli / python_daemon / minecraft) produce EvidenceBundles over a run; the `webapp-testing` skill; Playwright MCP | MEDIUM |
| F6 | Unknown Unknowns Engine — states with an entry and no exit, events with no consumer, data written and never read, capabilities with no observability, **knowledge with no consumer** (sec 38) | **EXISTS_AND_COMPLETE** | `frontier_intelligence/unknown_unknown_generator.py` (structural absence over a **discovered** cohort) + `liveness/reachability.py` + D2A. The source names the connection itself. This estate's sealed memory holds the identical findings — orphan module, orphan field, write-without-read | HIGH |
| F7 | Reconstruction Coverage Map — Capabilities × States × Environments; every unknown becomes an evidence mission (sec 39) | **MISSING** | No three-axis coverage object exists. It is a *view* over C1's model; without C1 there is nothing to plot | HIGH |
| F8 | Semantic Visual QA — a visually identical control with no handler is a critical divergence (sec 31) | **EXISTS_BUT_PARTIAL** | The *law* is owned: the Reality Contract bans action-less controls and `scaffold-auditor.js` enforces it at write time. The *comparison* is not (= D3) | HIGH |

**Category F: 0 of 14 chartered datasets survive.**

→ Continues in `CAPABILITY_MATRIX_G_TO_M.md`.
