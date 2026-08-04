---
title: CPP-APIR — Phase -1 Repository Reality Audit
date: 2026-08-03
status: COMPLETE — blocking gate cleared, no dataset content written
source: "Dataset Claude Power Pack Adaptive Project Intelligence Runtime 1.txt" (4,623 lines, read to EOF)
method: discovered denominator, mechanism-level verification, source-before-assumption
---

# Phase -1 — Repository Reality Audit

## 0. Evidence base

| Input | State |
|---|---|
| Primary source | `Downloads\Dataset Claude Power Pack Adaptive Project Intelligence Runtime 1.txt` — 72,357 B, 4,623 lines, **read to EOF** (two passes; architecture proper begins line 3316) |
| Repo HEAD | `9988c99` (`git fetch origin` clean; 20 files modified in worktree by a concurrent pane — none in the audit's write path) |
| Discovered denominator | **77 modules · 26 knowledge families · 65 commands · 39 hooks · 12 agents** — enumerated from the filesystem this session, not recalled |
| Prior audits read | `ccfl_pdpf/STOP_1_VERDICT.md`, `usirc/DATASET_ARCHITECTURE_DECISION_LEDGER.md`, `EMERGENCE_NOVELTY_AUDIT.md`, `plans/gap-reverification-2026-08-03.md`, `cpp_aci/MASTER_BUILD_PLAN.md` |
| Code read directly | `setup_os/scanner.py`, `cognitive_os/registry.py`, `cognitive_os/router.py`, `skill_router/skill_index.py`, `universal-meta-systems/runtime/executor.py`, `liveness/liveness_ledger.py` (grep) |

Claims below are marked **OBSERVED** (artifact opened this session), **VERIFIED** (mechanism read, not
name matched), or **INFERRED**. No claim rests on a filename.

## 1. The source's own coverage estimate, tested

The source states (line 3045): *"Claude Power Pack ya contiene aproximadamente el 55–65 % de los
mecanismos necesarios."*

**Measured: ~80 % owned.** The source underestimated incumbent coverage by roughly 15–25 points —
the documented direction of error for a proposal that cannot inspect the workspace
(`PR-COVERAGE-BY-CONSTRUCTION-001`). This matters because the source's build recommendation (6 new
owners) was sized against its own lower estimate.

## 2. The six proposed owners, verified against mechanism

| # | Proposed owner | Verdict | Incumbent (evidence) |
|---|---|---|---|
| **1** | Project Intelligence Model Compiler | **EXISTS_PARTIALLY → REQUIRES_EXTENSION** | `modules/setup_os/scanner.py` (324 lines) is *already named* "Project Intelligence Scanner". It emits a 33-field `ProjectProfile` where **every field carries its detection `Source`** (`detected_from_file` / `_config` / `_command` / `inferred_from_structure` / `missing` / `unknown`) so "an inference is never presented as a fact" — the source's own epistemic requirement, already implemented. Persisted via `--save` → `modules/setup_os/registry.py`. **VERIFIED** |
| **2** | Capability Applicability & Demand Engine | **EXISTS_PARTIALLY → REQUIRES_EXTENSION** | Three routers exist and each routes the wrong object: `skill_router/skill_index.py` routes **skills** by word-boundary keyword match on description text; `cognitive_os/router.py` (CO-03) routes **models** through a 6-rung cheapest-first cascade; `spec_gate.classify_tier` routes **task shape**. None routes *capabilities*, and the source explicitly rejects the mechanism all three use: *"La aplicabilidad no puede ser sólo keyword matching"* (line 3521). **VERIFIED** |
| **3** | Capability Morphogenesis Engine | **EXISTS_PARTIALLY → REQUIRES_EXTENSION** | `modules/universal-meta-systems/runtime/executor.py` already implements the *shape*: parent corpus + repo noun-map → specialized plan, read-only w.r.t. the parent, genealogy retained via `source_path`. But its specialization mechanism is **noun substitution**, and it says so honestly: *"The specificity is exactly as rich as the noun-map — no richer."* This is precisely the shape `HR-APA-016` (No Name-Level Specialization) declares invalid. The incumbent implements the anti-pattern the proposal forbids. **VERIFIED** |
| **4** | JIT Capability Activation Runtime | **EXISTS_AND_WIRED** | `hooks/hook-dispatcher.js` with `CHAIN_MAP`/`EVENT_MAP` over **39 hooks** is the event-driven activation runtime; `modules/liveness/reachability.py:80-86` seeds from that real dispatch table. Event-triggered activation, dormant-by-default sleepy skills, and JIT loading are live. **OBSERVED** |
| **5** | Institutional Capability Synthesis Compiler | **EXISTS_AND_WIRED** | `modules/duplicate_to_advantage/d2a_engine.py` — **1,037 lines**, arch-duplicate → best-adjacent-capability search, propose-never-build — reached live by `hooks/d2a_gate.js:39`. Overlap audit before creation is `spec_gate.check_novelty_gate` (the 13-question `HR-NOVELTY-001`), which fired on *this very prompt*. `HR-APA-011` ("Synthesis Requires Overlap Audit") is already enforced. **OBSERVED** |
| **6** | Project Power Pack Assembly Compiler | **EXISTS_PARTIALLY** | `modules/setup_os/` ships `secure_installer.py`, `registry.py`, `rollback` path, `roi_analyzer.py`, `drift_detector.py`, `backlog_generator.py` — project-local installation with registry and rollback, which is the assembly compiler's stated job. What it assembles is automations, not a capability projection. **VERIFIED** |

**Tally: 0 of 6 proposed owners is `GENUINELY_NEW`. 2 are `EXISTS_AND_WIRED`. 4 are
`REQUIRES_EXTENSION` of a named incumbent.**

## 3. The 25 proposed datasets, classified

| Class | Count | Datasets |
|---|---|---|
| `EXISTS_AND_WIRED` / `OVERLAPS_EXISTING_OWNER` | **19** | DS01, DS04, DS08, DS09, DS10, DS11, DS13*, DS14, DS15, DS16, DS17, DS18, DS19, DS20, DS21, DS22, DS23, DS24, DS25 |
| `REQUIRES_EXTENSION` | **4** | DS02, DS05, DS06, DS12 |
| `GENUINELY_NEW` (thin, contingent) | **2** | DS03, DS07 |

Selected ownership evidence (full map in the Ownership audit):

- **DS01 Constitutional Kernel / HR-APA-001..018** → `modules/rule_compiler` + **156 compiled rules**.
  At least 14 of the 18 HR-APA rules are already enforced by a live surface: `HR-APA-003`/`011` =
  `HR-NOVELTY-001`; `HR-APA-007` (No Unconsumed Intelligence) = the **Liveness Standard** +
  `liveness_ledger.py`'s producer-without-consumer probe; `HR-APA-014` (Dormant by Default) = the
  sleepy-skill doctrine; `HR-APA-013` (Context Compiled Not Accumulated) = `cognitive_os/context.py`
  + `gc.py`; `HR-APA-009` (Reversible) = `modules/rollback` + `cascade_prevention`. **OBSERVED**
- **DS14 Learning Ascension Ladder** → **ACIS** is literally the E0–E7 ascension ladder with a
  no-autopromotion rule; plus FD-00..07, `compound-learnings`, CLAE. **OBSERVED**
- **DS18 Evaluation** → SQI (`run_sqi.py`, 45/45 ×3), OVO, `done_gate`, `uqf`. **OBSERVED**
- **DS19 Integrity/Liveness** → `modules/liveness` (328 modules scored), `refcheck`,
  `sweep_enforcer`, `osa`. This is the single most-owned row in the proposal. **OBSERVED**
- **DS22 Economics** → `cost_collapse/router.py`, `recall_roi`, `corpus_roi` (wired 07-31),
  `token_irr`, `ias_c2/opportunity_cost.py`. **OBSERVED**
- **DS23 Failure Genome** → CEPS, `craif`, CLAE, `anti-antipatterns.md`,
  `governance/KNOWN_FALSE_POSITIVES.md`. **OBSERVED**

\* **DS13 (Activation Evidence Ledger) carries an overlap warning, not a clean verdict.** See §5.

## 4. What is genuinely absent — stated precisely

One coherent residue, expressible in a sentence:

> **Every registry in this estate is module-level, skill-level, or model-level. None is
> capability-level, and nothing specializes a capability per-project beyond substituting nouns.**

Concretely, three objects do not exist anywhere in 77 modules:

1. **The Capability Contract** (DS03) — an object carrying triggers, anti-triggers, required
   evidence, consumers, activation cost, failure-risk-if-omitted. `vault/liveness/reachability_registry.json`
   scores **modules**; a module is not a capability.
2. **The applicability computation** (DS05) — the multi-factor score and its verdict set
   (`MANDATORY` / `RECOMMENDED` / `AVAILABLE_ON_TRIGGER` / `NOT_APPLICABLE` / `CAPABILITY_INSUFFICIENT`).
   Nothing computes it; three routers keyword-match instead.
3. **The derivative registry** (DS07) — parent capability, specialization delta, inherited vs
   overridden contracts, upgrade path. `universal-meta-systems` retains genealogy for *meta-systems*
   only, and only at noun depth.

## 5. Counter-evidence the Owner must weigh

This audit is obliged to report evidence against its own residue.

**The A–J gap re-verification of 2026-08-03 — today, same corpus — already evaluated candidate A
("Capability Runtime") and ruled:**

> *"Residue: no capability-level (as distinct from module-level) registry exists — **low ROI, no
> failure attributable to it**."* (`vault/plans/gap-reverification-2026-08-03.md:58`)

That is a recorded verdict against building DS03. It cannot be silently overridden.

**What has changed since that ruling:** the CPP-APIR source supplies the failure evidence the A–J
pass said was missing. The KADOS fork exercise (source lines 1–3013) is a documented session in which
the **Owner personally performed** capability-applicability reasoning and capability specialization
across 22 candidate forks, because no PP surface performs either. The source names this failure class
itself: *"un humano actúa constantemente como router"* (line 3947). The Missing-Capability signal set
it lists is satisfied by the estate's own history, not by the proposal's assertion.

**Honest weight:** that is **one** observed incident. It converts "no failure attributable" to "one
failure attributable". Whether one incident clears the bar is the Owner's call, and it is the
substance of STOP #1 — not a judgment this audit should make silently.

## 6. Base rate, stated so it is not mistaken for the verdict

This is the **ninth** consecutive proposal set in this estate to measure majority-owned (AISHF, RE
Baseline, KSF, UKR Compendium, IIG A-AD, CCFL-PDPF 35, Emergence, A–J, now CPP-APIR at ~80 %). The
base rate is the correct prior on any tenth proposal.

It is **not** the finding here. The finding is measured per-mechanism, and it differs from its
predecessors in one respect worth recording: CPP-APIR's residue is the *only* one of the nine that
names a **layer** the estate lacks (capability) rather than an **instance** of a layer it already has.
Nine of nine were majority-owned; this one's remainder is structurally different from noise.

## 7. Prohibitions honored

- No dataset content written. Phase -1 was blocking and is now cleared.
- No owner proposed where extension, composition, adapter, policy, contract, schema, evaluator or
  wiring resolves the need — 4 of 6 proposed owners are downgraded to extensions on that ground.
- `git add -A` not used; no repo mutation outside `vault/audits/apir/` and `vault/plans/`.
- CommonWealth Ops / ecommerce / brand terminology: **0 imports**. Reference material was profiled
  for depth discipline only, per the CPP-ACI precedent.
- KADOS is treated as a stress case supplying failure evidence, never as an ecosystem.
