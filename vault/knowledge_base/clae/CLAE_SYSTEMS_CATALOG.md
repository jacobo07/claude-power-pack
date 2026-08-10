---
title: "CLAE — Systems Catalog"
family: clae
type: registry
kind: extract
sources: [CLAE_INDEX.md Parts table · CLAE_CHARTER.md scope and non-scope]
derivation: mechanical extraction from the sealed Parts; no entry carries information absent from its source
status: POPULATED
date: 2026-08-10
---

# CLAE — Systems Catalog

> **What this file is.** Part XXVI §5 defines the twelve companion artifacts as *"extracts for retrieval convenience"* — the schemas, consolidations and measured counts live in the Parts. This file locates entries; it does not restate, resolve or extend them.
> **Reading rule.** Every row cites the Part that seeded it. Where a row's source is ambiguous, the ambiguity is transcribed rather than resolved.

The mechanisms this family defines, one row per Part, transcribed from the `Responsibility` column of `CLAE_INDEX.md`. No mechanism is named here that is not named there.

## 1. Mechanisms by Part

| Part | Mechanism | Depends on |
|---|---|---|
| I | Why a stack that authors its own criteria cannot see its own ceiling; the Phase 0 evidence that PP has this defect | — |
| II | First principles: replacing the pass/fail predicate with a measured residual; the three-stage ladder and the retention thesis | I |
| III | Reference · bar · delta · distance · floor · residual · oracle · probe · instrument · horizon · deviation; the ten-pair confusion matrix | I, II |
| IV | The five qualification conditions; reference classes; the regression-versus-ceiling direction label; manufacturing externality by discovery | III |
| V | The perishability principle; pin generations; three decays; residual change decomposition; custody as tamper-evidence | IV |
| VI | The observability precondition; the five-level extraction ladder; paired observation; projection and structure traps; the noise floor | IV, V |
| VII | Impact versus severity; the four factors; dominance-then-frontier ordering; fixability bias and the counting trap; starvation | VI |
| VIII | k from attribution not capacity; whole-dimension re-measurement; the four outcomes; distance opened; first cycle validates the loop | VII |
| IX | Residual identity; joint publication; the three debts (quality, measurement, instrument); aggregation classes; unverified as a disposition | II, VIII |
| X | The six shapes of real-but-shallow work; the five floor properties; the declared escape; retirement at creation; promotion and demotion | IX |
| XI | The four mismatches; the three thresholds as risk posture; qualitative floors travel and numeric ones do not; the sensitivity test | X |
| XII | The six ordered capabilities; the thin-vertical rule; the envelope not determinism; partial Phase Zero as a declared measurement-debt register | VI |
| XIII | Seven kinds and their native levels; selection by required level; perturbation under envelope; chain coverage as intersection; three-valued output | XII |
| XIV | The seeing-blocker trigger; the visible-detour asymmetry; four conditions; shrink-dont-stack; register or delete; book to instrument debt | XIII |
| XV | The incident as a free known-answer case with a short expiry; probe versus fix versus test; fix-or-delete-never-mute; the probe as an agent memory of failure | XIII, XIV |
| XVI | The self-verification limit; four marks of an oracle question; both-direction failure and why boundaries drift narrow; standing and constituency | II, XII |
| XVII | The answerable window; the six presentation items; the criterion-over-verdict ladder; an answer is evidence about what was shown; the re-ask ledger | XVI |
| XVIII | The four-part contract; zero deviation rate as a broken record; intent preservation does not compose; the zero-loss test; density as a design signal | IX |
| XIX | The inversion: approve the contract not the steps; four entry conditions; declared halts; scope as the real boundary; the accounting determines the behaviour | XII, XVIII |
| XX | Closure as an accounting act; the five verdicts; producer closes accounting and constituency accepts; closure does not compose | IX, XIX |
| XXI | Five structural roots; six lineages traced to their terminals; treat the earliest reachable link; the confident-blind compound | all prior |
| XXII | 99 distinct traps measured and consolidated; symptom-keyed index; escape-from-inside; prevention-only entries; reference set versus operational register | XXI |
| XXIII | 118 process rules, 0 hard rules; the five-layer enforcement ladder; prefer the lowest layer; deductive rules are hypotheses | XXI, XXII |
| XXIV | An eval is an instrument; the negative control; adversarial variants; false-positive risk as a liability; benchmark the family, do not eval it | XXIII |
| XXV | Nineteen gates consolidated to four lifecycle gate points; label evidence and block floors; label propagation; gate decay | XXIII, XXIV |
| XXVI | Resolution against every canonical owner; twelve writeback findings; the family closed under its own rules as complete-with-residual, acceptance line empty | all prior |

## 2. What CLAE owns

- The **Reference** object — what qualifies as canonical, how it is acquired, versioned and
  provenanced, and why an internally-authored bar is not one.
- The **Delta** — extraction, observability, impact ranking, top-k correction, termination.
- **Quality Distance Accounting** — the residual ledger that survives a passing gate.
- **Anti-underbuild floors** — domain-derived minima, and why imported floors fail.
- **The Human Oracle Boundary** — the declared set of properties the stack cannot verify
  about itself, and the routing that converts a human answer into durable evidence.
- **Observability-Capable Phase Zero** — the proof that a project can boot, observe,
  measure, reproduce, compare and fail legibly, established before the first feature.
- **Autonomous toolsmith behaviour** and incident-to-probe conversion.
- **Deviation governance** — constraint-bounded substitution that preserves intent.
- **Evidence-gated autonomy** — the gate structure that replaces per-step approval.

## 3. What CLAE does not own

| Not owned by CLAE | Canonical owner | Relationship |
|---|---|---|
| Design scoring rubric | `modules/cdio/scorer` | CLAE generalizes its *shape*; CDIO keeps its criteria |
| Code quality scoring | `modules/uqf` | consumes CLAE's residual ledger |
| Index-direction monitoring | `modules/sqi` | SQI detects decrease; CLAE supplies distance |
| Empirical verification runs | `modules/sleepless_qa` | executes; CLAE decides against what |
| Artifact existence gate | `modules/done_gate` | CLAE adds residual after its pass |
| Slop-token detection | `hooks/scaffold-auditor` | CLAE adds the shallow-but-real case it cannot see |
| Owner-facing queue | `modules/owner_queue` | CLAE supplies the admission criterion it lacks |
| Reachability of modules | `modules/liveness` | CLAE reuses its by-construction discovery discipline |

## 4. Boundary

Part XXVI §2's finding governs every row above: **CLAE adds fields, criteria and vocabulary to existing surfaces and replaces none of them.** A mechanism listed in §1 is doctrine, not an implementation — `modules/clae/` is named in the charter as the executable side *"once Parts are implemented"*, and Part XXVI §5 records that no Part has been applied to a live correction loop. Reading §1 as a component inventory would be the error the family names in Part I.
