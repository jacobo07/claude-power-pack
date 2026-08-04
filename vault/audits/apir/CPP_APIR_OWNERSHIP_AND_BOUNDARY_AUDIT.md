---
title: CPP-APIR — Phase 0 Ownership and Boundary Audit
date: 2026-08-03
status: COMPLETE — feeds STOP #1
constitutional_key: "No new owner where an extension, composition, adapter, policy, contract, schema, evaluator or wiring resolves the need."
---

# Phase 0 — Ownership and Boundary Audit

Phase -1 established *what exists*. This phase decides *what form each surviving mechanism should
take*: owner · module · policy pack · capability · adapter · projection · compiler · runtime · ledger ·
evaluator · or nothing at all.

## 1. Form determination for the six proposed owners

| Proposed owner | Correct form | Rationale |
|---|---|---|
| Project Intelligence Model Compiler | **Extension of `setup_os/scanner.py`** — new emitters, same owner | The scanner already owns project reality with per-field provenance. What is absent is *graph* output (architecture / capability-demand / human-dependency), not a second scanner. A second project scanner would create the split-brain the estate has already paid for once (`feedback_hook_dispatcher_split_brain_mirror`). |
| Capability Applicability & Demand Engine | **New module** (`modules/capability_runtime/applicability.py`) | The object it ranks (capability contracts) does not exist, so no incumbent can be extended into it. It is a module because it has one lifecycle and ≤4 consumers — a module, by this estate's own precedent, is code + registry entry + liveness declaration, never a dataset family. |
| Capability Morphogenesis Engine | **Extension of `universal-meta-systems`** | The parent-plus-map-to-derivative shape already exists there and is correct. The delta is *specialization depth* — replacing noun substitution with the source's 6-component composition (Domain Pack + Runtime Adapter + Evidence Adapter + Quality Policy + Activation Policy + Contracts). That is a richer map, not a new engine. |
| JIT Capability Activation Runtime | **No new artifact — wiring only** | `hooks/hook-dispatcher.js` is the runtime. If capability contracts land, they register as dispatch entries. Building a second activation runtime beside the dispatcher is the exact split-brain failure named above. |
| Institutional Capability Synthesis Compiler | **No new artifact — already owned** | `d2a_engine.py` (1,037 lines) + `spec_gate.check_novelty_gate`. `HR-APA-011` is `HR-NOVELTY-001` restated. |
| Project Power Pack Assembly Compiler | **Extension of `setup_os` + one projection view** | Assembly = existing installer/registry/rollback, with the *selection input* changed from automations to a capability set. A projection, not a compiler. |

## 2. Boundary contract — who decides what

The source's own §VI ownership map is largely correct; it simply names systems this estate already
has under different names. Restated against real owners:

| Question | Sovereign owner (real) | Boundary — what it must NOT do |
|---|---|---|
| What is this project? | `setup_os/scanner.py` | Must not decide which capabilities activate |
| What does the repo's structure mean? | `modules/graphify` (1,217 coordinates) | Must not own project identity |
| Which capability applies, and how strongly? | **`capability_runtime` (proposed)** | Must not mutate repos; must not select models |
| Which model serves the task? | `cognitive_os/router.py` (CO-03) | Must not decide capability applicability |
| Which skill loads now? | `skill_router` + `jit_skill_loader` | Must not own capability contracts |
| When does anything fire? | `hooks/hook-dispatcher.js` | Must not compute applicability itself |
| Is a proposed system a duplicate? | `d2a_engine.py` + `spec_gate` novelty gate | Must not build; propose only |
| Is a declared thing actually reachable? | `modules/liveness` | Must not judge value, only reachability |
| Which knowledge may govern? | `crawl_os` / `akos_knowledge` / ACIS | Must not decide activation |
| What spec depth does this task need? | `sdd_os` (T0–T3) | Must not own the capability stack |
| Which learning ascends? | ACIS (E0–E7) | Must not self-certify (derived levels cap at E3) |
| What did an activation actually achieve? | **contested — see §3** | — |

## 3. The one genuine boundary conflict

**DS13 (Capability Activation & Effectiveness Ledger) collides with an already-approved residue.**

The CCFL-PDPF STOP #1 verdict (2026-07-31) approved **CDP — Cognitive Decision Provenance** as its
irreducible remainder, on this reasoning:

> *"CO-12 records session cost; CEPS records error events; nothing records claim/evidence/assumption/
> omitted-verification. The estate can answer what failed, never what decision structure made it
> possible."* (`ccfl_pdpf/STOP_1_VERDICT.md` G1)

DS13 proposes a record of: capability, trigger, reason, evidence, expected value, cost, outputs,
consumers, whether it changed a decision, whether it prevented a failure, false-positive activation.

These are **the same object at different granularity** — a per-event provenance record whose subject
is an activation rather than a decision. Building both produces two provenance ledgers, which is the
`Registry Without Runtime` anti-pattern the proposal itself lists (DS23).

**Ruling: DS13 is not a separate ledger. It is a subject type on CDP** — if CDP is built, activation
events are one of its record kinds. If CDP is not built, DS13 inherits its status rather than
overtaking it. This must be settled before either is constructed; two sessions approving two ledgers
independently is precisely how this estate acquired 77 modules.

## 4. What must NOT be built — do-not-build ledger

| Proposal | Do not build because |
|---|---|
| A second project scanner | `setup_os/scanner.py` owns it with provenance already |
| A second activation runtime | `hook-dispatcher.js` + 39 hooks is it |
| A second overlap/novelty auditor | `spec_gate.check_novelty_gate` (13 questions), live |
| A second synthesis proposer | `d2a_engine.py`, live via `hooks/d2a_gate.js:39` |
| A second liveness/integrity fabric | `modules/liveness` + `refcheck` + `sweep_enforcer` |
| A second economics runtime | `cost_collapse` + `recall_roi` + `corpus_roi` + `token_irr` |
| A second ascension ladder | ACIS E0–E7 with no-autopromotion |
| A second failure genome | CEPS + `craif` + CLAE |
| A second knowledge runtime or sovereignty layer | `crawl_os` (5 datasets sealed) + `akos_knowledge` |
| A second spec compiler | `sdd_os` T0–T3 + `one_shot/compiler.py` |
| A second provenance ledger | CDP owns provenance (§3) |
| A "Constitutional Kernel" dataset restating HR-APA | `rule_compiler` + 156 compiled rules; ≥14 of 18 already enforced |

## 5. Contamination and isolation boundary

- **Domain quarantine holds.** PP is domain-blind by constitution (USIRC category L ruling). KADOS,
  Wii, CommonWealth Ops and ecommerce vocabulary stay out of every artifact. The source's KADOS
  material is admitted **only** as failure evidence for the human-router class, never as an ecosystem
  or a naming source.
- **The morphogenesis extension is the contamination risk surface.** A per-project Domain Pack is by
  definition domain-specific; its containment rule is that the *kernel* never learns a domain noun.
  `HR-APA-017` (Universal Kernel Integrity) is the right rule and has no current enforcement surface —
  it would need one before any Domain Pack ships.

## 6. Residual uncertainty — declared, not hidden

| Item | Status |
|---|---|
| Whether one observed incident (KADOS fork session) clears the ROI bar that A–J set on 2026-08-03 | **UNKNOWN — Owner decision, the substance of STOP #1** |
| Whether CPP-ACI (STOP #1 since 2026-07-12, unbuilt) should be resolved before opening APIR | **UNRESOLVED — two open STOP #1s on overlapping ground is itself a governance defect** |
| Exact enforcement surface for `HR-APA-016` / `HR-APA-017` | **UNKNOWN — deferred to build time if approved** |
| 20 worktree files modified by a concurrent pane | **OBSERVED — not inspected; none in this audit's write path** |
