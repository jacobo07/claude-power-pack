---
title: USIRC STOP #1 — Capability Overlap Matrix, categories G–M and aggregate
date: 2026-07-31
continues: CAPABILITY_MATRIX_A_TO_F.md
---

# Capability Overlap Matrix — G to M

## Category G — Debugging and causal reconstruction (prompt DS72–82)

| # | Mechanism | Verdict | Owner, verified | Conf |
|---|---|---|---|---|
| G1 | T0 root condition / T1 first internal divergence / T2 first observable divergence / T3 terminal failure (sec 15) | **EXISTS_BUT_PARTIAL** | `craif` owns causal-investigation completeness — candidates, evidence, closure — and ships a conformance checker at 7/8, exit 1, deliberately not silenced. `root_cause_taxonomy.md` **CLASE 0–5** ranks by observed recurrence. Both classify the *mechanism*; neither positions a divergence in *execution time* | HIGH |
| G2 | Aligning two executions to find the earliest causal divergence rather than the first visible one | **MISSING** | Measured 0 for `earliest causal` and `divergence graph`. `replay_harness` compares one run against recorded expectations — a trace against a baseline, never two live traces aligned | HIGH |
| G3 | "Hand the divergence to KADOS" (secs 15, 7, 99) | **PREMISE FAILURE** | **KADOS does not exist in this repo.** One mention repo-wide, inside a plan file. Every USIRC bridge to it rests on an unverified premise — CLASE 1 in `root_cause_taxonomy.md` | HIGH |
| G4 | Universal Bug Reconstructor — reproducibility score, minimal reproducer, causal hypothesis lattice, next probe, regression test, learning candidate (sec 37) | **EXISTS_BUT_PARTIAL** | `modules/bug-hunter` + CRAIF + CEPS + `tools/bug_to_hardrule.py` (incident → sealed rule) + CLAE **Part XV Incident-to-Probe Conversion**: "the incident as a free known-answer case with a short expiry; fix-or-delete-never-mute" | HIGH |
| G5 | Cross-Layer Trace: click → handler → command → request → authorization → persistence → event → worker → response → render (sec 36) | **EXISTS_BUT_PARTIAL** | `omnicapture` owns runtime reality — errors, telemetry, network, performance, state dumps. The gap is instrumentation of a *third-party* app, which is B7 | MEDIUM |
| G6 | Regression Genome — missing wiring, stale state, ordering, hidden dependency, contract mismatch, incomplete migration, race, visual and semantic and operational drift (sec 65) | **DUPLICATED** | `root_cause_taxonomy.md` CLASE 0–5 — CLASE 0, "module built but not auto-activated", is the source's *missing wiring* and this estate's single most-recurring error — plus CEPS `patterns.db` with 20 empirical scoring runs and `vault/osa/never_again_log.jsonl` recurrence counts | HIGH |
| G7 | Counterfactual Reconstruction — predict unobserved behavior, produce a falsification experiment (sec 14) | **EXISTS_AND_COMPLETE** | **DRK-04 Counterfactual Simulation and Horizons**, 4,147 w, three-trajectory simulation with adaptive horizons; `accountability.py` separates reasoning error from execution error, luck and context change. Measured: `counterfactual` in 28 files | HIGH |

**Category G: 0 of 11 chartered datasets survive. G2 is the third genuine gap — one
instrument. G3 is a defect in the source to be corrected, never built.**

## Category H — Reverse engineering and archaeology (prompt DS83–93)

| # | Mechanism | Verdict | Owner, verified | Conf |
|---|---|---|---|---|
| H1 | Black-box / grey-box / white-box routes, each claim labelled with its route (sec 8) | **EXISTS_UNDER_DIFFERENT_NAME** | The ACIS ladder + crawl_os DS10 provenance class + DAIF-03 epistemic fidelity. The route *is* an evidence class | HIGH |
| H2 | Screenshot-to-Architecture must experiment, not guess (sec 79) | **EXISTS_BUT_PARTIAL** | crawl_os DS03's **observed-reason discipline** is the same law: no escalation without an observed reason. The experiment executor for a live app is B7 | HIGH |
| H3 | System Archaeology Runtime — old versions, changelogs, manuals, backups, binaries, protocols, testimonies (sec 19) | **EXISTS_BUT_PARTIAL** | crawl_os acquisition + AKOS distillation + `deep-research`. No historical-corpus reconstruction object | MEDIUM |
| H4 | Temporal Product Twin — the product modelled across versions (sec 20) | **MISSING** | Downstream of C1 | MEDIUM |
| H5 | Design Archaeology — infer which UI elements are legacy, which flows carry debt (sec 51) | **MISSING** | `cdio` scores design *quality*, never design *history*. Genuinely absent, and with no consumer in PP | HIGH |
| H6 | Competitive Architecture Intelligence — capability maps of observable products (sec 50) | **EXISTS_UNDER_DIFFERENT_NAME** | `modules/autoresearch` (competitive intelligence, 3–4× daily) + `frontier_intelligence` + `deep-research` + `agent-reach` | MEDIUM |
| H7 | A practice record for reverse-engineering an external system | **EXISTS_AND_COMPLETE** | `vault/knowledge_base/ecc-reverse-engineering.md` — the estate has already reverse-engineered and absorbed a 246-skill external system and recorded the analysis | HIGH |

**Category H: 0 of 11 chartered datasets survive. The proposal's thinnest-covered
category still produces no family.**

## Category I — Migration, assimilation, synthesis (prompt DS94–104)

| # | Mechanism | Verdict | Owner, verified | Conf |
|---|---|---|---|---|
| I1 | System Assimilation: Observe → Reconstruct → Evaluate → Abstract → Generalize → Assimilate → Govern → Reuse (sec 47) | **EXISTS_AND_COMPLETE** | **D2A** root law `PR-DUPLICATE-TO-ADVANTAGE-001`: *no duplication ends in rejection; it becomes reinforcement, extension, composition, shared infrastructure, or — only for the irreducible remainder — a sovereign dataset*. This audit is that law executing | HIGH |
| I2 | Capability Transplantation — extract a capability, reconstruct its contracts, adapt it to the host (sec 48) | **EXISTS_UNDER_DIFFERENT_NAME** | D2A `run_family()` + FD (frontier delta → portable advantage) + FD-04's six-lens transfer test, which *re-executes* the capability on the target substrate and grades the output | HIGH |
| I3 | Cross-System Synthesis Engine — combine the best patterns of several systems without their debt (sec 49) | **EXISTS_BUT_PARTIAL** | `cpp_ias` advantage algebra + `frontier_intelligence/evolution_engine.py`, whole-KB mutation proposals, Owner-gated | MEDIUM |
| I4 | Reconstruction-to-Migration: legacy → twin → parity → dual-run → cutover (sec 45) | **MISSING** | No legacy-migration surface exists in PP | HIGH |
| I5 | Shadow Execution — the new system receives the same inputs without serving users (sec 46) | **MISSING** | Measured 0. A real technique with **no consumer in PP** — PP is doctrine and tooling, not a traffic-serving system | HIGH |
| I6 | System-to-Standard promotion: Observation → Pattern → Mechanism → Platform capability → Standard → Constitutional rule (sec 86) | **EXISTS_AND_COMPLETE** | **FD-03** routes every insight to Hard Rule / Process Rule / Trap / dataset Part / benchmark / prompt fragment / discard; `rule_compiler` owns admission and placement — *"no successor system may contain a second placement compiler"*, standing and unconditional; `tools/bug_to_hardrule.py` | HIGH |
| I7 | System-to-Dataset — each reconstruction may yield datasets | **EXISTS_AND_COMPLETE** | `dataset_first` decides whether a dataset is needed at all; `transduction.py`. The source concedes it: *"Dataset-first decidiría si realmente se necesita cada uno."* | HIGH |
| I8 | System-to-Knowledge-Graph export | **EXISTS_AND_COMPLETE** | `graphify` GK-00…12, 1,190 coordinates, live GK-12 advisory | HIGH |
| I9 | System-to-Decision-Engine — accumulated patterns drive future decisions | **EXISTS_AND_COMPLETE** | `decision_review` DRK kernel + 4 live proactive detectors + precedent memory | HIGH |
| I10 | Economic Reconstruction / Operational Twin / ROI Engine (secs 43, 44, 70, 97) | **EXISTS_AND_COMPLETE** | `cpp_ias` **Capability Economics** (`ias_c1_capability_portfolio`, `ias_c2_demand_forecasting`) + `cognitive_os` `economics.py` + CO-12 telemetry + `cost_collapse` + HR-COST-001/002/003 | HIGH |

**Category I: 0 of 11 chartered datasets survive.**

## Category J — Personal assistants / PAROS (prompt DS105–117)

| # | Mechanism | Verdict | Owner / disposition | Conf |
|---|---|---|---|---|
| J1 | Interaction Shell, Conversation Runtime, Personal Intelligence Runtime, Agent Runtime, Action Runtime, Constitutional Runtime (sec 7) | **OUT_OF_SCOPE — a product, not doctrine** | PP is project-agnostic institutional doctrine and ships no user-facing product. Building a chat application is a **product build governed by PP**, requiring an SDD-OS T2/T3 spec — not thirteen PP dataset families | HIGH |
| J2 | Constitutional Runtime (governance, policies, evidence, ownership, completion, safety, observability, knowledge promotion) | **EXISTS_AND_COMPLETE** | A verbatim restatement of what PP already is. The source says so: *"Claude Power Pack no debería vivir dentro de la UI… sus capacidades actuarían como servicios constitucionales."* | HIGH |
| J3 | Recovery Control Plane | **EXISTS_AND_COMPLETE** | Already built and named: Recovery Control Plane, SCS C83; plus `session_resilience`, Lazarus, and `tools/recovery_epoch_gate.py`, which wired the acceptance arbiter on 2026-07-14 | HIGH |
| J4 | Memory Runtime and Context Compiler | **EXISTS_AND_COMPLETE** | `memory-engine` + **DAIF-08 Context Assembly and Mission Runtime** (20 Parts) + `cognitive_os` residency CO-13/14 | HIGH |
| J5 | Agent Runtime — delegation, teams, missions, permissions, sandboxes, budgets, retries, escalation, verification | **EXISTS_AND_COMPLETE** | `agent-governance` (OWASP ASI) + `pp_agents` + `parallel_mesh` + `one_shot` budgets + `zero-crash` sandboxing | HIGH |
| J6 | Replica / Essence / **Ascension** modes; Intentional Divergence Ledger (secs 8, 9) | **EXISTS_UNDER_DIFFERENT_NAME** | CLAE **Part XVIII Deviation Governance** — a four-part deviation contract, *"zero deviation rate as a broken record"*, intent preservation, the zero-loss test, density as a design signal. That is the intentional-divergence ledger, generalized and sealed | HIGH |
| J7 | Self-Evolving Assistant Interface; Capability-Adaptive UI; Runtime Truth Projection; Architecture-to-UI Consistency Gate (secs 56–60) | **EXISTS_UNDER_DIFFERENT_NAME (the law) / OUT_OF_SCOPE (the UI)** | "No UI for a capability that does not exist" **is** the Reality Contract plus `liveness` reachability, stated for a UI surface. PP has no UI surface to gate | HIGH |

**Category J: 0 of 13 chartered datasets survive.** The assistant is a product the
Owner may legitimately want; it is not PP institutional doctrine, and PP already owns
every runtime that would govern it.

## Category K — Adapters and lenses (prompt DS118–129)

| # | Mechanism | Verdict | Owner / disposition | Conf |
|---|---|---|---|---|
| K1 | Surface / Motion / Behavior / Architecture / Production / Wii lenses (sec 77) | **NEW_VIEW at most** | The source states the correct disposition itself: *"En vez de productos separados, existirían lenses"* and *"serían perfiles o targets del compilador"*. A lens is a command profile over one runtime | HIGH |
| K2 | The five proposed commands — reconstruct, reconstruction-audit, fidelity-audit, divergence-investigate, reconstruction-compile | **DEFERRED** | Commands are cheap and correct **after** a runtime exists. Shipping commands with no engine is the Scaffold Illusion, Mistake #16 | HIGH |

**Category K: 0 of 12 chartered datasets survive.**

## Category L — Wii System Reconstruction Laboratory (prompt DS130–147)

| # | Mechanism | Verdict | Owner / disposition | Conf |
|---|---|---|---|---|
| L1 | *"Reaching a visible state does not prove the architectural contracts required to reach it were satisfied"* — the proposed constitutional law | **EXISTS_UNDER_DIFFERENT_NAME, and it is the best single idea in the source** | Generalized, this is the Reality Contract + CLAE Part XXV gates + Mistake #16 Scaffold Illusion + `liveness`. This estate's sealed memory states it twice: *"compiles ≠ works"* (Mistake #16) and *"static verification does NOT prove runtime works"* (Mistake #17). **Residue: nothing states it as an ordering claim** — that a reached terminal state does not witness the *sequence* of prerequisite contracts | HIGH |
| L2 | Wii instrumentation: DOL / REL / BRRES / BRLYT / BRLAN, Dolphin captures, RAM dumps, Gecko traces, GX capture, hardware-versus-emulator divergence, frame-aligned divergence, Kamek mission pack | **OUT_OF_SCOPE for PP** | Measured: zero Wii reconstruction surface in this repo — 20 hits, all incidental (one crash-research note, `sdd_os/active_repos.txt`, unrelated). `wii-dev-best-practices` is a **global skill**, and Wii work lives in other repos. PP is domain-blind by constitution: `core.md` PATH RULE, and E11 forbids project-specific names in global skills | HIGH |

**Category L: 0 of 18 chartered datasets survive. One Hard Rule candidate — L1,
generalized and domain-blind — is the entire yield of the largest category.**

## Category M — Self-evaluation and self-improvement (prompt DS148–160)

| # | Mechanism | Verdict | Owner, verified | Conf |
|---|---|---|---|---|
| M1 | Reconstruction Benchmark Platform, eight benchmark families (sec 66) | **EXISTS_UNDER_DIFFERENT_NAME** | CLAE **Part XXIV Evals and Benchmarks** — *"an eval is an instrument; benchmark the family, do not eval it"* — with negative controls, adversarial variants, and false-positive risk as a liability. Plus SQI's executable suite | HIGH |
| M2 | Ground-Truth Corpus with evidence withheld and recovery measured (sec 67) | **EXISTS_UNDER_DIFFERENT_NAME** | **FD-04's six-lens transfer test** is precisely this: re-execute the capability on the target substrate and grade the output. `fd_04_prover`, `fd_04_contrast.py`, plus this estate's sealed finding that 3 of 3 judgments reproduced on a smaller model | HIGH |
| M3 | Self-Improving Reconstruction Loop; Meta-Reconstruction (secs 88, 89) | **EXISTS_AND_COMPLETE** | `frontier_intelligence/evolution_engine.py` (Owner-gated KB mutation) + SQI `weakening_detectors.py` + baseline guardian + CLAE Part XXVI institutional writeback + `graphify` GK-08 session writeback | HIGH |
| M4 | Reconstruction Difficulty Index / Risk Forecast / Fidelity Frontier / ROI Engine (secs 68–70) | **EXISTS_UNDER_DIFFERENT_NAME** | CLAE **Part VII Delta Impact Ranking** — impact versus severity, four factors, dominance-then-frontier ordering, starvation — plus `backlog_autopilot`, `cost_collapse`, `recall_roi`, one_shot OD3 budget ceilings | HIGH |
| M5 | Reconstruction Failure Modes — 18 named traps (sec 90) | **DUPLICATED** | **CLAE Part XXII: 99 traps**, symptom-keyed, measured and consolidated. Spot-check of the source's list against it: *happy-path equivalence*, *pixel perfection without semantics*, *mocked production*, *test derived from the same faulty inference*, *code-before-understanding* and *overfitting to one session* all map to sealed traps or to this repo's Mistakes Registry #1–#32 | MEDIUM — mapped by symptom; the 99 not read individually |
| M6 | Reconstruction Ledger of Truth — claim, source, confidence, owner, version, tests, contradictions, status (sec 61) | **DUPLICATED** | ACIS per-claim status + crawl_os DS10 supersession and change-history + `vault/decision_registry/records.jsonl` + DAIF-21 | MEDIUM |
| M7 | Multi-Agent Reconstruction Society, twelve constitutional agents (sec 28) | **DUPLICATED** | 12 repo-local agents + `pp_agents` + `agent-governance` + `parallel_mesh`. The roles map: Fidelity Auditor → `pp-code-reviewer`; Causal Investigator → `pp-ceps-analyst` and `craif`; Production Reality Examiner → `omni-singularity`; Knowledge Distiller → FD; Adversarial Reviewer → SQI redteam; Reconstruction Governor → `owner_queue` | MEDIUM |
| M8 | Reconstruction Debate Protocol — design the experiment that settles the disagreement (sec 29) | **EXISTS_BUT_PARTIAL** | ACIS `T-ACIS-MODEL-CONSENSUS-001` + CLAE XVII oracle routing + `graphify-route-governor`, which arbitrates competing librarian proposals into one route. Gap: the *discriminating-experiment designer* — the same gap as C6 and B3 | MEDIUM |
| M9 | Context Compilation for reconstruction — minimal packages per agent (sec 94) | **EXISTS_AND_COMPLETE** | **DAIF-08** + `graphify` GK-06 Route Compiler + `cognitive_os` residency + `jit_skill_loader` | HIGH |

**Category M: 0 of 13 chartered datasets survive.**

---

## Aggregate

| | |
|---|---|
| Categories chartered by the prompt | **13** (A–M) |
| Chartered dataset slots | **~160** |
| Mechanisms audited individually | **89** |
| Mechanisms with a verified owner (`EXISTS_*` or `DUPLICATED`) | **77 of 89 — 87 %** |
| Mechanisms `MISSING` with a real PP consumer | **5** — B7, B8/D3, C1, F7, G2 |
| Mechanisms `MISSING` with **no** PP consumer | **4** — H4, H5, I4, I5 |
| Premise failures in the source | **1** — G3, KADOS |
| Out of scope for PP (a product, or another repo's domain) | **2 categories** — J and L2 |
| **Dataset families justified** | **0** |
| **Narrow mechanisms justified** | **5, plus 1 Hard Rule candidate (L1)** |

### The three convergent gaps, restated as one sentence

PP can measure distance from a reference (CLAE), can prove a representation faithful
(DAIF-03), can acquire and authorize external evidence (crawl_os), can investigate a
cause (CRAIF) and can locate any of its own knowledge (graphify) — but it has **no
typed model of a third-party running product (C1), no instrument that compares a
rendered build against a captured reference (D3), and no way to align two executions
to find where they first diverged (G2).** Everything else the source proposes is a
renaming of territory that already has an owner.
