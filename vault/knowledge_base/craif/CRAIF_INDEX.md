# CRAIF — Closed-Loop Repair & Activation Integrity Fabric — Master Index

> **The repair-execution axis of Claude Power Pack.** Founded 2026-07-21, from the AISHF
> source proposal (`Downloads\Dataset Claude Power Pack Autonomous Integrity & Self-Healing
> Fabric 1.txt`) after STOP #1 determined ~75-80% of the proposal was already owned by
> sealed corpus. CRAIF is the Duplicate-to-Advantage residue: the transactional repair
> execution nobody owns, and the activation-chain science nobody simulates.
>
> **Where SQI** governs whether executable reality is verified, **DRK** whether a decision
> is sound, **CPP-IAS D2** the immune taxonomy and quarantine, **`liveness/`** module and
> post-ship reachability, **DAIF** the Duplicate-to-Advantage doctrine itself — **CRAIF
> governs one thing none of them does: the transactional, authorized, reversible,
> independently-verified EXECUTION of a repair, and the end-to-end SIMULATION of whether a
> capability actually activates.**
>
> STOP #1 evidence + ownership matrix + content-tier verification: `vault/plans/aishf-corpus-2026-07-21.md`.
> Approved architecture (Phase 0, ULTRA-PLAN): same file §8 + chat record 2026-07-21.

---

## Root laws (from source, formalized as CRAIF-00 Articles)

> **Law 1 (Institutional Existence).** No capability of Claude Power Pack is considered to
> exist by being documented, installed, or implemented. It exists institutionally only when
> it is reachable, activates under the correct conditions, produces an observable result,
> can be independently verified, degrades detectably, and has an explicit route to repair,
> rollback, and learning.

> **Law 2 (Escape Attribution).** Every failure that requires Owner intervention must be
> evaluated as a potential failure of the detection, governance, repair, or learning system —
> not solely as a failure of the component where it appeared.

> **Law 3 (No Self-Granted Authority — CRAIF-native).** No repair runtime may expand its own
> authority tier, certify its own repair, or modify the approval criteria that govern it in
> the same transaction that applies a repair.

---

## Non-duplication contract (binding — the residue boundary)

CRAIF **never** owns: general capability/module reachability (`modules/liveness/reachability.py`
owns this) · post-ship drift/silence detection (`modules/liveness/liveness_ledger.py`) ·
repository reality or test reach (SQI-01/02) · blast radius, reversibility classification, or
decision authority in general (DRK) · the immune/pathogen taxonomy, quarantine, or containment
(CPP-IAS D2) · reality-sync / semantic drift (DAIF-21) · the Duplicate-to-Advantage doctrine
itself (DAIF-00) · deploy-target rollback mechanics (`modules/rollback/*`, reused as an adapter,
never forked) · escalation queueing (`owner_queue`, reused as an adapter).

CRAIF **owns**: the repair transaction that turns an existing Finding into a verified,
reversible change to institutional reachability or activation — and the simulation science
that proves a capability activates end-to-end. Every capability listed above is a **producer**
or **consumer** of CRAIF's contracts, never re-implemented inside CRAIF.

---

## The three datasets

| ID | Dataset | Owns | Parts | Status |
|---|---|---|---|---|
| **CRAIF-00** | Constitution & Canonical Ontology | ontology, L0-L4 ladder, negative fixtures, OIII metric, non-duplication contract, self-failure-modes | 16/16 | **`COMPLETE`** — 20,618 words, mean 1,289 w/Part |
| **CRAIF-01** | Transactional Repair Runtime & Authority Composition | R1 + R2: the repair transaction state machine, authority-in-use, sandbox/canary/rollback, failure modes, integration contracts | 20/20 | **`COMPLETE`** — 21,501 words, mean 1,075 w/Part (two honest expansion passes; a third was declined per CRAIF-00 XVI.6's own anti-padding law — see note below) |
| **CRAIF-02** | Activation Integrity & Simulation Science | R3 (+R4 metrics): activation-chain ontology, simulation harness, negative fixtures, integration boundary | 17 | `NOT_STARTED` |
| | **Total** | | **53** | |

**Depth contract** (inherited from SQI `CANONICAL_ONTOLOGY.md` / DAIF, verified at content-tier
this session): one `.txt` per dataset · `PART I` … `PART N` · numbered subsections (`X.Y`) ·
a `PART N FINAL LAW` closing every Part · **dense prose, no markdown headings/bullets/tables/
fences inside a dataset** · 1,200–2,500 words per Part · zero executable code · every claim
evidence-marked (VERIFIED · OBSERVED · INFERRED · HYPOTHESIS · PROPOSED · REJECTED).

**Executable runtime is explicitly OUT OF SCOPE for this corpus.** Dataset-first, per estate
convention (SQI/DAIF/DRK shipped dataset before engine). The repair engine (sandbox executor,
snapshot/rollback code, L3/L4 auto-apply) requires its own future Owner-approved gate.

---

## Part Map — CRAIF-00 Constitution & Canonical Ontology

| # | Title | Core content |
|---|---|---|
| I | Mission — the gap this constitution exists to close | detection-without-repair, presence-without-effectiveness; IAS-D2 Part XIV's own admission as founding evidence |
| II | Duplicate-to-Advantage Supremacy Doctrine | composes DAIF-00 root law; hierarchy: existing detector > existing decision authority > CRAIF's own runtime opinion |
| III | Ontology I — Finding taxonomy | Reachability / Quality / Drift / Immune-Threat Finding; normalization into Repair Intent |
| IV | Ontology II — Repair Intent & Candidate | Repair Intent, Repair Candidate, Diagnosis Evidence; canonical states |
| V | Ontology III — Authority objects | Repair Authority Decision, Preconditions, Scope/Blast-Radius Record |
| VI | Ontology IV — Verification & Outcome objects | Verification Contract, Activation Verification Contract, Rollback Contract, Repair Outcome, Repair Certificate, Failed Repair Record |
| VII | Ontology V — Learning objects | Learning Candidate, Guardian Promotion Candidate, Owner Escalation, Incident Closure, Certification Revocation |
| VIII | The Repair Authority Ladder L0–L4 | full mechanism: observe-only, auto-propose, sandbox, reversible-auto, production-auto; eligibility, prohibited classes, expiry, demotion |
| IX | Separation of Powers | Detection / Diagnosis / Authority / Execution / Verification / Learning as distinct roles; no role certifies itself |
| X | The Three Constitutional Laws | Institutional Existence, Escape Attribution, No Self-Granted Authority — full derivation |
| XI | Non-Duplication Contract | the explicit boundary (see above); what CRAIF may never become |
| XII | Founding Negative Fixtures | the 5 source incidents formalized as permanent benchmark cases |
| XIII | Owner Intervention Escape Rate & OIII | the constitutional metric: definition, composite formula, anti-Goodhart countermetrics |
| XIV | Failure Modes of CRAIF Itself | false healing, self-granted authority, thrashing, scanner/verifier collusion, local-to-global promotion error (mirrors IAS-D2 Part XIV structure) |
| XV | Evidence & Admissibility for Repair Claims | reuses ACIS ladder by reference; adds failing-before/passing-after as the repair-specific admissibility floor |
| XVI | Closing — unresolved questions, maturity model, done criteria for CRAIF-00 | |

## Part Map — CRAIF-01 Transactional Repair Runtime & Authority Composition

| # | Title | Core content |
|---|---|---|
| I | Mission & jurisdiction | the only system in the estate that EXECUTES a repair; composes CRAIF-00 |
| II | Repair Transaction State Machine | the full lifecycle as formal states/transitions |
| III | Intake & Evidence Freeze | |
| IV | Precondition & Scope Proof | |
| V | Candidate Generation & Selection | |
| VI | Authority Acquisition | L0-L4 ladder in operational use (composes CRAIF-00 VIII) |
| VII | Snapshot & Isolation | sandbox contract; composes `modules/rollback/*` as adapter |
| VIII | Sandbox Execution & Static Validation | |
| IX | Targeted, Regression & Activation Verification | composes SQI reconciliation + CRAIF-02's Activation Verification Contract |
| X | Canary & Controlled Rollout | |
| XI | Commit or Rollback Decision | |
| XII | Post-Repair Liveness Observation | composes `liveness_ledger` |
| XIII | Ledger Updates & Side-Effect Recording | |
| XIV | Learning Handoff & Guardian Promotion | composes CEPS / UKDL / CPP-IAS |
| XV | Failure Modes I | retry, timeout, partial failure, failed rollback, stale intent |
| XVI | Failure Modes II | concurrent collision, thrashing, dependency-unavailable, evidence corruption |
| XVII | Emergency Stop & Demotion | |
| XVIII | Integration Contracts | bidirectional Liveness/SQI/DRK/IAS/DAIF/owner_queue/rollback — the D2A packages formalized |
| XIX | Metrics | repair yield, false healing rate, MTTR, rollback rate, recurrence elimination (R4 instrumented) |
| XX | Worked Example & Done Criteria | the hook/settings-divergence incident walked end-to-end |

## Part Map — CRAIF-02 Activation Integrity & Simulation Science

| # | Title | Core content |
|---|---|---|
| I | Mission | the science nobody owns — not module-reach, not test-reach, but activation |
| II | Activation Chain Ontology | intent→trigger→skill-selection→loader→context-injection→hook→module→runtime-action→result→evidence→cleanup |
| III | Trigger Visibility Science | the bootstrap defect formalized |
| IV | Bootstrap Dependency Defect Taxonomy | Incident #1 as founding fixture |
| V | Synthetic & Real Activation Corpus Design | |
| VI | Positive, Negative & Ambiguous Activation Cases | |
| VII | Competing Skills, Priority & Deduplication | |
| VIII | Cross-Repo Activation | capability pointer, loader resolution, repo profile; Incident #4 as founding fixture |
| IX | Context Injection & Budget Constraints | |
| X | The Simulation Harness | architecture, replay, hermetic execution (composes SQI hermetic-replay by reference) |
| XI | Metrics | Activation Recall/Precision, False Invocation Rate, Cross-Repo Activation Rate, Loaded-but-Unused Ratio, Context Cost |
| XII | Activation Verification Contract | how CRAIF-01 proves an activation-repair restored the chain, not just changed a file |
| XIII | Negative Fixtures | all 5 founding incidents as permanent regression corpus |
| XIV | Failure Modes | false positive/negative activation, session-restart drift, worktree drift, stale pointer, partial activation |
| XV | Integration Contracts | JIT loader, SKILL.md, liveness/SQI boundary — explicit non-duplication |
| XVI | Worked Example | Incident #1 replayed as hermetic simulation, before/after |
| XVII | Done Criteria & Maturity Model | |

---

## Governance artifacts (to be produced alongside Part authoring)

| Artifact | Status |
|---|---|
| `CRAIF_INDEX.md` (this file) | `IN_PROGRESS` |
| D2A reinforcement proposals (8 packages) | `NOT_STARTED` |
| `CRAIF_ADVERSARIAL_REVIEW.md` | `NOT_STARTED` |
| `CRAIF_CONTAMINATION_AUDIT.md` | `NOT_STARTED` |
| `CRAIF_COMPLETION_REPORT.md` | `NOT_STARTED` |
| `RESUMPTION_FILE.md` (repo root, CRAIF section) | maintained after every sealed Part-batch |

## Density note (honest, not silent)

CRAIF-00 reached its 1,200-2,500 floor at a 1,289 w/Part mean after one expansion pass.
CRAIF-01, after two genuine expansion passes (worked examples, edge cases, cross-references
— verified against no repetition), settled at a 1,075 w/Part mean; several Parts remained
40-150 words short of 1,200. A third pass was deliberately declined: CRAIF-00 Part XVI.6
states a Part lengthened without new mechanism has not cleared the floor honestly regardless
of word count, and the marginal content available for a third pass was assessed as
repetition risk rather than genuine additional mechanism. CRAIF-01's practical achieved
floor is therefore documented as ~1,000-1,200 w/Part, not silently claimed as 1,200+.

## Build order

CRAIF-00 (all 16 Parts, dependency root) → CRAIF-01 (needs CRAIF-00's ontology + ladder) →
CRAIF-02 (needs CRAIF-00's ontology; cross-refs CRAIF-01 IX/XII) → D2A reinforcement packages →
adversarial review → Production Reality Gate report → UKDL writeback → sealing.

Micro-commits: pathspec-scoped, one per sealed Part-batch (4-6 Parts), never mixing datasets in
one commit.
