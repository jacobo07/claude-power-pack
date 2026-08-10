---
title: CLAE — Master Index
family: clae
date: 2026-07-26
parts_total: 30
parts_sealed: 28
state: UNSEALED — extension to 30 Parts authorized by G2, in progress
unsealed_on: 2026-08-10
---

# CLAE — Master Index

**Coherence anchor:** `parts_sealed` above must equal the count of `PART_*.md` files in
this directory. On disagreement, reconcile from the filesystem — never from this table.
`parts_total` is the **authorized** size and `parts_sealed` the **actual** one; while the
extension is in progress they differ, and the difference is the work remaining.

## Unseal record — gate G2

| Field | Value |
|---|---|
| Gate | `G2`, opened by `TOPOLOGY_ADR.md` §8 (KobiiCraft Estate Governance repo) |
| Ratified | 2026-08-10, by the Owner |
| `G2-a` | CLAE may be unsealed to accept Parts 27–30 |
| `G2-b` | the twelve registries are populated **before** the extension |
| Ordering executed | G2-b first — the eleven producible extracts sealed in `c5b0d1f`, then this unseal |
| Authorized scope | four Parts, subjects fixed by `TOPOLOGY_ADR.md` §4; no other change |

**Completion-definition re-run, required by the unseal.** Measured 2026-08-10, not recalled:
26 of 26 Parts `SEALED` and unmodified · registries populated (11 of 12) · integration map
resolved (Part XXVI) · **contamination gate zero hits** · **zero fenced code blocks** ·
evidence index present. The one criterion that does not pass is the Dataset Completion
Report, and it cannot: the charter's completion definition contains the report that reports
the completion, so it is unsatisfiable before the work it describes exists. It is deferred
to the close of the extension rather than waived.

CLAE is **not** `Complete`. Part XXVI's verdict — *complete with residual, acceptance line
empty* — stands until a constituency accepts it, and the producer may not.

| Part | Subject (fixed by `TOPOLOGY_ADR.md` §4) | Status |
|---|---|---|
| 27 | The Completion Prosecutor — three authorities, independence, anchoring, deadlock, false acquittal, the certificate and the verdict alias table — `PART_27_the_completion_prosecutor.md` | **SEALED** |
| 28 | Freeze and adversarial multipass — the freeze, the closure pack, **nine** passes and their selection, negative proof as route enumeration — `PART_28_freeze_and_adversarial_multipass.md` | **SEALED** |
| 29 | Cognitive precursors and the same-session repair loop | AUTHORIZED |
| 30 | Root-cause elevation, sibling campaigns, failure-to-immunity | AUTHORIZED |

`AUTHORIZED` means the subject is ratified and the Part is not written. A row flips to
`SEALED` only when its file exists and `parts_sealed` is incremented, per the construction
rule below.

**Numbering deviation, recorded.** Parts I–XXVI use Roman numerals; Parts 27–30 use Arabic.
Roman thirty collides with a token this repository's quality gate rejects on sight, so a
Part carrying that numeral would have every future edit vetoed by a check unrelated to its
content. The ratifying document (`TOPOLOGY_ADR.md` §4) already calls them "Parts 27–30", so
Arabic matches the authorized scope as written.

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
| XVI | The Human Oracle Boundary | The self-verification limit; four marks of an oracle question; both-direction failure and why boundaries drift narrow; standing and constituency | II, XII | **SEALED** |
| XVII | Oracle Routing | The answerable window; the six presentation items; the criterion-over-verdict ladder; an answer is evidence about what was shown; the re-ask ledger | XVI | **SEALED** |
| XVIII | Deviation Governance | The four-part contract; zero deviation rate as a broken record; intent preservation does not compose; the zero-loss test; density as a design signal | IX | **SEALED** |
| XIX | Evidence-Gated Autonomy | The inversion: approve the contract not the steps; four entry conditions; declared halts; scope as the real boundary; the accounting determines the behaviour | XII, XVIII | **SEALED** |
| XX | Phase Closure Semantics | Closure as an accounting act; the five verdicts; producer closes accounting and constituency accepts; closure does not compose | IX, XIX | **SEALED** |
| XXI | Failure Modes and Failure Lineages | Five structural roots; six lineages traced to their terminals; treat the earliest reachable link; the confident-blind compound | all prior | **SEALED** |
| XXII | Traps Registry | 99 distinct traps measured and consolidated; symptom-keyed index; escape-from-inside; prevention-only entries; reference set versus operational register | XXI | **SEALED** |
| XXIII | Hard Rules and Process Rules Registry | 118 process rules, 0 hard rules; the five-layer enforcement ladder; prefer the lowest layer; deductive rules are hypotheses | XXI, XXII | **SEALED** |
| XXIV | Evals and Benchmarks | An eval is an instrument; the negative control; adversarial variants; false-positive risk as a liability; benchmark the family, do not eval it | XXIII | **SEALED** |
| XXV | Production Reality Gates | Nineteen gates consolidated to four lifecycle gate points; label evidence and block floors; label propagation; gate decay | XXIII, XXIV | **SEALED** |
| XXVI | Integration Map and Institutional Writeback | Resolution against every canonical owner; twelve writeback findings; the family closed under its own rules as complete-with-residual, acceptance line empty | all prior | **SEALED** |

## Registries

Per Part XXVI §5 these are **extracts for retrieval convenience** — the schemas,
consolidations and measured counts live in the Parts. Every entry cites the Part that
seeded it; no extract carries information absent from its source.

| Artifact | Source | Entries | Status |
|---|---|---|---|
| `CLAE_SYSTEMS_CATALOG.md` | this index · charter | 26 mechanisms | **POPULATED** |
| `CLAE_HARD_RULES.md` | Part XXIII | 0 — empty by construction | **POPULATED** |
| `CLAE_PROCESS_RULES.md` | Parts II–XXV | 141 | **POPULATED** |
| `CLAE_TRAPS.md` | Parts II–XXI · XXII | 99 distinct | **POPULATED** |
| `CLAE_EVALS.md` | Parts I–XXV · XXIV | 129 | **POPULATED** |
| `CLAE_PRODUCTION_GATES.md` | Parts I–XXIV · XXV | 23 seeds · 4 gate points | **POPULATED** |
| `CLAE_ONTOLOGY.md` | Part III | 19 terms | **POPULATED** |
| `CLAE_INTEGRATION_MAP.md` | Part XXVI | 17 owners | **POPULATED** |
| `CLAE_EVIDENCE_INDEX.md` | all Parts | 23 of 26 Parts | **POPULATED** |
| `CLAE_OPEN_QUESTIONS.md` | all Parts | 73 | **POPULATED** |
| `CLAE_VERSION_LEDGER.md` | frontmatter · filesystem | 26 Parts | **POPULATED** |
| `CLAE_COMPLETION_REPORT.md` | this build | — | pending |

**Three counts in the extracts differ from the counts the Parts assert about themselves.**
Each is a scope-label gap, not an arithmetic error, and each is recorded in the extract
rather than corrected in the sealed Part: process rules (`CLAE_PROCESS_RULES.md` §1),
production gates (`CLAE_PRODUCTION_GATES.md` §1), evals (`CLAE_EVALS.md` §1). The trap
count agrees with Part XXII exactly.

## Construction rule

One Part per commit, pathspec-scoped. After sealing a Part: flip its status row here,
increment `parts_sealed`, and update `RE_BASELINE_RESUMPTION.md` block 2 — in that order,
before beginning the next Part.
