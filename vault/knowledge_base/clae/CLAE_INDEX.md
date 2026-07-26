---
title: CLAE — Master Index
family: clae
date: 2026-07-26
parts_total: 26
parts_sealed: 15
---

# CLAE — Master Index

**Coherence anchor:** `parts_sealed` above must equal the count of `PART_*.md` files in
this directory. On disagreement, reconcile from the filesystem — never from this table.

## Reading routes

- **Agent about to declare work done** → XX, IX, XVI, XXV.
- **Agent starting a long autonomous mission** → XII, XIX, XVII, XVIII.
- **Engineer implementing `modules/clae/`** → III, IV, VI, VII, IX, XIII, XXIII.
- **Reviewer auditing this family** → I, II, XXI, XXII, XXIV, XXVI.
- **First-time reader** → I → II → III, then any route above.

## Parts

| Part | Title | Responsibility | Depends on | Status |
|---|---|---|---|---|
| I | The Internal-Bar Trap | Why a stack that authors its own criteria cannot see its own ceiling; the Phase 0 evidence that PP has this defect | — | **SEALED** |
| II | Quality as Distance, Not Compliance | First principles: replacing the pass/fail predicate with a measured residual; the three-stage ladder and the retention thesis | I | **SEALED** |
| III | Ontology and Glossary | Reference · bar · delta · distance · floor · residual · oracle · probe · instrument · horizon · deviation; the ten-pair confusion matrix | I, II | **SEALED** |
| IV | The Reference Object | The five qualification conditions; reference classes; the regression-versus-ceiling direction label; manufacturing externality by discovery | III | **SEALED** |
| V | Reference Acquisition, Versioning and Provenance | The perishability principle; pin generations; three decays; residual change decomposition; custody as tamper-evidence | IV | **SEALED** |
| VI | Delta Extraction | The observability precondition; the five-level extraction ladder; paired observation; projection and structure traps; the noise floor | IV, V | **SEALED** |
| VII | Delta Impact Ranking | Impact versus severity; the four factors; dominance-then-frontier ordering; fixability bias and the counting trap; starvation | VI | **SEALED** |
| VIII | The Top-K Correction Cycle | k from attribution not capacity; whole-dimension re-measurement; the four outcomes; distance opened; first cycle validates the loop | VII | **SEALED** |
| IX | Quality Distance Accounting | Residual identity; joint publication; the three debts (quality, measurement, instrument); aggregation classes; unverified as a disposition | II, VIII | **SEALED** |
| X | Anti-Underbuild Floors | The six shapes of real-but-shallow work; the five floor properties; the declared escape; retirement at creation; promotion and demotion | IX | **SEALED** |
| XI | Floor Derivation Versus Floor Imposition | The four mismatches; the three thresholds as risk posture; qualitative floors travel and numeric ones do not; the sensitivity test | X | **SEALED** |
| XII | Observability-Capable Phase Zero | The six ordered capabilities; the thin-vertical rule; the envelope not determinism; partial Phase Zero as a declared measurement-debt register | VI | **SEALED** |
| XIII | The Instrument Taxonomy | Seven kinds and their native levels; selection by required level; perturbation under envelope; chain coverage as intersection; three-valued output | XII | **SEALED** |
| XIV | Autonomous Toolsmith Behaviour | The seeing-blocker trigger; the visible-detour asymmetry; four conditions; shrink-dont-stack; register or delete; book to instrument debt | XIII | **SEALED** |
| XV | Incident-to-Probe Conversion | The incident as a free known-answer case with a short expiry; probe versus fix versus test; fix-or-delete-never-mute; the probe as an agent memory of failure | XIII, XIV | **SEALED** |
| XVI | The Human Oracle Boundary | The declared set of properties the stack structurally cannot verify about itself | II, XII | pending |
| XVII | Oracle Routing | When to ask, which artifact to present, how an answer becomes durable evidence | XVI | pending |
| XVIII | Deviation Governance | Constraint-bounded substitution: prove the constraint, preserve intent, measure the loss | IX | pending |
| XIX | Evidence-Gated Autonomy | Gate structure that replaces per-step approval without becoming unbounded | XII, XVIII | pending |
| XX | Phase Closure Semantics | What closure means; residual visibility as a closure obligation | IX, XIX | pending |
| XXI | Failure Modes and Failure Lineages | How closed loops fail: blindness, bar inflation, metric theater, myopia, replanning amnesia | all prior | pending |
| XXII | Traps Registry | Named traps with trigger, symptom, detection and escape | XXI | pending |
| XXIII | Hard Rules and Process Rules Registry | Full UKDL-shaped rule records with origin, enforcement layer, eval and retirement condition | XXI, XXII | pending |
| XXIV | Evals and Benchmarks | Per-eval objective, setup, pass and fail criteria, adversarial variants, false-positive risk | XXIII | pending |
| XXV | Production Reality Gates | Autonomous Mission Gate · Phase Closure Gate · Residual Visibility Gate | XXIII, XXIV | pending |
| XXVI | Integration Map and Institutional Writeback | Resolution against every named canonical owner; what CLAE feeds and consumes | all prior | pending |

## Registries (populated as Parts seal)

| Artifact | Status |
|---|---|
| `CLAE_SYSTEMS_CATALOG.md` | pending |
| `CLAE_HARD_RULES.md` | pending (source: Part XXIII) |
| `CLAE_PROCESS_RULES.md` | pending (source: Part XXIII) |
| `CLAE_TRAPS.md` | pending (source: Part XXII) |
| `CLAE_EVALS.md` | pending (source: Part XXIV) |
| `CLAE_PRODUCTION_GATES.md` | pending (source: Part XXV) |
| `CLAE_ONTOLOGY.md` | pending (source: Part III) |
| `CLAE_INTEGRATION_MAP.md` | pending (source: Part XXVI) |
| `CLAE_EVIDENCE_INDEX.md` | pending |
| `CLAE_OPEN_QUESTIONS.md` | pending |
| `CLAE_VERSION_LEDGER.md` | pending |
| `CLAE_COMPLETION_REPORT.md` | pending |

## Construction rule

One Part per commit, pathspec-scoped. After sealing a Part: flip its status row here,
increment `parts_sealed`, and update `RE_BASELINE_RESUMPTION.md` block 2 — in that order,
before beginning the next Part.
