---
title: UCR-CIF Compendium — Phase 3 D2A / Ownership Audit (first pass)
date: 2026-08-25
status: MEASURED — 28 spine systems through three independent instruments
instruments:
  - modules/duplicate_to_advantage/d2a_engine.py --family-file --repo-evidence
  - vocabulary sweep over 4,458 files / 59 MB (acronym + distinctive terms)
  - capability sweep (function under any name, acronym deliberately excluded)
governing_law: PR-DAIF-D2A-PLUS-DEFAULT-001 · PR-COVERAGE-BY-CONSTRUCTION-001 · HR-NOVELTY-001
---

# Phase 3 — D2A / Ownership Audit, first pass

## 1. The estate's own engine

`d2a_engine.py --family-file --repo-evidence` on the 28 spine systems extracted from the
source corpus:

```
FAMILY SIZING: 28 proposed -> 4 recommended
KEEP   (4)  genuinely new, no sealed parent, no sibling overlap
DEFER (24)  could not confidently name a parent
STOP #1: overlap 0% <= threshold 50% -- expansion not offered
```

### 1.1 KEEP — the measured residue

| System | Engine coverage | Independent corroboration |
|---|---|---|
| **Certified Engineering Primitives & Golden Paths** | 35 % | **capability sweep: 2 hits estate-wide** — `golden path`, `certified primitive`, `paved road`, `blessed path` |
| **Human Intervention Ledger** | 45 % | capability sweep 1,441 hits but dispersed across 370 files; no owning module, no ledger artifact |
| **RCFC Recursive Causal Funnel Compiler** | 17 % — lowest of all 28 | capability sweep 441 hits, dominated by `ias_f3_digital_twin` and `cpcsc_a2_theory_generator` — adjacent, not the same object |
| **Constitutional Microkernel & Self-Hosting Governance** | 33 % | capability sweep 3,796 hits, but on *rule volume* (`hard_rules`, `rule_compiler`); the microkernel object — a small irreducible invariant set plus separated proposal / evaluation / ratification / execution planes — is not present |

Two independent instruments agree on **Certified Primitives & Golden Paths**. That is the
strongest novelty signal in the audit, and it is the only one where a vocabulary sweep and
a capability sweep both return near-zero.

### 1.2 DEFER — and why this output is not usable as-is

**All 24 DEFER rows returned coverage = exactly 45 %.** That is the engine's plausibility
floor, not a measurement. A score that is identical across 24 items ranks nothing — the
same defect already sealed in this estate as *constant factors rank nothing*. The engine
resolved the four it could and capped the rest.

**Therefore: DEFER means UNKNOWN. It is not evidence of novelty, and it is not evidence of
ownership.** Reading these 24 as "genuinely new" would be exactly the error that struck
CRPF, IGEF and E1–E5. Every one requires a per-system evidence sweep before a verdict.

## 2. Where the manual sweeps *did* resolve ownership

The engine could not name parents; targeted sweeps could. These are file-cited and
outrank the engine's DEFER on the same systems:

| Source system | Owner on disk | Evidence |
|---|---|---|
| **External Reality Acquisition / Crawl OS** | `vault/knowledge_base/crawl_os/` | 12 Parts · 181,996 words · `crawl_os_03_adaptive_acquisition_strategy_routing`, `crawl_os_10_evidence_provenance_integrity_fabric` · 829 vocabulary hits, 741 inside the family |
| **Universal Reference Convergence Engine** | `vault/knowledge_base/clae/` | 37 Parts · `PART_I_the_internal_bar_trap`, `PART_IX_quality_distance_accounting`, `CLAE_CHARTER` — CLAE's chartered boundary is *measurement against an external reference and the loop that closes on it* |
| **Construction Intelligence Record** | `daif_02_cir_fabric_v1.txt` | 469 vocabulary hits in that single file; 34,826 words |
| **Epistemic Type System / Claim-Evidence** | `daif_01_type_system_v1.txt` + ACIS ladder | 33,509 words; DAIF-01 chartered as CREATE for exactly this object |
| **IFC-RLAAS capital allocation** | `cpp_ias/ias_c1_capability_portfolio.txt` | 34,894 words; `NON_DUPLICATION_LEDGER` candidates 21–30 route capital allocation, ROI, opportunity cost and investment thesis here |
| **UFIA-EBF failure immunity** | `cpp_ias/ias_d2_immune_system.txt` + `cascade_prevention` + CEPS | 37,907 words; ledger candidates 41–50 (pathogen registry, immunization, failure mutation, exposure scan) |
| **SEEIP digital twin / experiment compiler** | `cpp_ias/ias_f3_digital_twin.txt` | 37,031 words; ledger candidates 101–110 (mission sim, scenario, counterfactual) |
| **Institutional State Runtime / event log** | `craif_01_repair_runtime_v1.txt` · `setup_os_02_setup_transaction_registry_rollback` · `modules/rollback` | 278 + 86 + 75 hits; transaction registry and rollback already exist as sealed objects |
| **Institutional Compression / knowledge debt** | `d2a_fabric` + `modules/token-optimizer/executionos_compressor.py` | 2,008 hits; DAIF-03 fidelity/loss owns compression accounting |

## 3. Systems still genuinely UNKNOWN after this pass

Not resolved by any of the three instruments. Each needs a dedicated sweep in Phase 3b
before receiving any verdict:

`UCR-CIF` (the umbrella itself) · `UBC` + `Mission Baseline Capsule` + `Project/Mission
Genome` · `HIC-OAR` as a whole (distinct from its Ledger) · `UDFLL` · `KIFS/USIFB` ·
`Constitutive Baseline Ratchet` · `Universalization Compiler & Portable Packs` ·
`Resident Institutional Kernel` · `Capability Authority Registry` · `Knowledge
Compiler/Linker` · `Meta-Failure Genome` · `Institutional SLOs & Chaos Mutation` ·
`Autonomous Convergence Contract` · `Long-Horizon Campaign Infrastructure`

### 3.1 UBC — RESOLVED against my own earlier note

An earlier draft of this audit recorded that a grep for UBC's function returned **zero
matches across all 84 modules**, and concluded "adjacent machinery exists; the compiler may
not." **That conclusion was wrong, and the grep was the reason it was wrong.**

`modules/capability_runtime/applicability.py` opens:

> *"Capability Applicability Engine (CPP-APIR DS05). Decides which capability contracts
> apply to a mission, and how strongly."*

That is UBC's core function, already built. It also already encodes the doctrine the source
demands of UBC:

| Source requirement for UBC | Already in `applicability.py` |
|---|---|
| activate only applicable capabilities | `Verdict.NOT_APPLICABLE` + six-factor benefit score |
| negative triggers | **gate 1 anti-trigger** → `NOT_APPLICABLE` |
| graded activation, not binary | `MANDATORY` / `RECOMMENDED` / `AVAILABLE_ON_TRIGGER` |
| evidence must exist before enforcement | **gate 3** `BLOCKED_BY_MISSING_EVIDENCE` |
| authority before reinvention | **gate 2** `BLOCKED_BY_UNRESOLVED_OWNER` |
| do not duplicate a held scope | **gate 4** `REJECTED_AS_DUPLICATE` |
| never collapse to one score | *"a composite score must never be mapped onto a hard conjunct"* — four deterministic gates run **before** any score |

The grep returned zero because it searched the source's vocabulary
(`minimum sufficient`, `maturity capsule`) while the module uses its own
(`applicability`, `contract`, `verdict`). **Zero cannot fall: a gate bounded by its
vocabulary reads an unrecognised idiom as absence.** This is the second time in this audit
that a zero was UNKNOWN rather than novelty, and the first where the zero was mine.

**Revised verdict: UBC is substantially OWNED by `capability_runtime`.** The residual delta
is narrower than the whole compiler and must be scoped precisely in Phase 3b — plausibly
only (a) the persisted **Mission Baseline Capsule** artifact and (b) the **Project / Mission
Genome** inputs, neither of which `MissionContext` currently materializes.

Relevant precedent: **CPP-APIR itself measured 25 proposed datasets at ~80 % owned** and the
Owner chose the capability layer over the corpus. `capability_runtime` is what that ruling
produced. This is the sixth consecutive majority-owned corpus proposal in this estate.

### 3.2 Phase 3b — six more resolved from the capability sweep

Probing the **function under any name**, with the source's acronym excluded from the query.
Top owning files, not just hit counts, so a parent can actually be named:

| Source system | Resolved owner | Evidence (top files by hit) |
|---|---|---|
| **Universalization Compiler / Portable Packs** | `fable_distillation` | `fd_04_intelligence_decay_and_transfer_proof_detector` (144) · `fd_07_fable_learning_flywheel` (50). FD-04 already separates *truth-proof* from *transfer-proof* and runs a real contrast harness — precisely the source's causal-abstraction-then-transfer-validation pipeline. **OWNED.** |
| **Institutional State Runtime / event log** | `craif` + `setup_os` | `craif_01_repair_runtime_v1` (278) · `setup_os_02_setup_transaction_registry_rollback` (86) · `setup_os_01` (80) · `modules/rollback` (75). Transaction registry and rollback are built objects, not proposals. **OWNED.** |
| **TTPE / TTIA latency metrics** | `cpp_ias` IAS-E1 | `ias_e1_observability_fabric` (75) · `crawl_os_10_evidence_provenance_integrity_fabric` (45). **OWNED.** |
| **Autonomous Convergence Contract** | `d2a_fabric` DAIF-04 | `daif_04_contract_fabric_v1` (57) · `ias_e1` (28) · `pp_dataset_13_resource_governor_os` (23). The contract object exists; the *convergence-loop semantics* may be a thin delta. **MOSTLY OWNED.** |
| **KIFS / USIFB integrity + foresight** | `cpp_ias` (dispersed) | `ias_f3_digital_twin` (56) · `ias_c2_demand_forecasting` (36) · `ias_g1_architecture_intelligence` (30) · `crawl_os_10` (33). Spread across three IAS datasets rather than one owner. **EXTEND, not CREATE.** |
| **Proof-Carrying Capabilities** | `craif` + `sqi` + `daif` | `craif_00_constitution` (50) · `sqi_00_constitution` (42) · `dataset_first/dfp_02` (27) · `daif_04` (25) · `daif_01` (24). Certificate / expiry / revalidation are already constitutional in three families. **EXTEND.** |

**Resolved to date: 16 of 28** — 9 in §2, 6 here, plus UBC in §3.1.

Still unresolved, requiring dedicated sweeps: `UCR-CIF` (the umbrella itself) · `HIC-OAR`
as a whole, distinct from its Ledger · `UDFLL` · `Constitutive Baseline Ratchet` ·
`Capability Authority Registry` · `Knowledge Compiler / Linker` · `Meta-Failure Genome` ·
`Institutional SLOs & Chaos Mutation` · `Long-Horizon Campaign Infrastructure`.

**A third state, distinct from owned and absent.** `Resident Institutional Kernel` returns
5,789 hits, but its top files are `vault/.arch-index/index.json` (127), `ukdl-universal.md`
(75), `knowledge_vault/core/apex-completion-standard.md` (45) and `apex_baseline_doctrine.md`
(43) — **dispersed across documents with no owning module.** Dispersion-without-an-owner is
neither ownership nor absence, and it is the state most easily misread as a gap: the
vocabulary is everywhere, so a keyword probe says "owned", while nothing executes it, so a
reachability probe says "absent". Held UNRESOLVED pending a check against `hooks/` and
`modules/daemon/` — the latter is already recorded in `OWNER_QUEUE.md` as holding zero `.py`
files.

## 4. Source inventory scale (Phase 1, partial)

| Range | Concepts | Status |
|---|---:|---|
| 1 – 17,500 | ~60 recorded (head truncated in transit; re-run queued) | partial |
| 17,500 – 35,000 | **259** | complete |
| 35,000 – 52,500 | **70** | complete, written to file |
| 52,500 – 75,350 | — | in flight |

New acronyms surfaced that appear in **neither** the mission brief's §6 seed list nor the
first extraction pass: `UGPEP`, `ACC`, `UERAL`, `KSEIP`, `UPSEIP`, `UEFB`, `EFR`, `SEIP`,
`FICR`, `PSR`, `GPIR`, `HCC`, `LHAY`, `WPIP`, `KADOS`, `ORCA`, `KIFM`.

The KIND distribution matters more than the raw count: the large majority of the 259 in
range 2 are **laws, traps, metrics and packs** distilled from donor corpora (EssentialsX,
LuckPerms, KME, Fable 5 / LAAS, Wii), not systems. A law belongs *inside* a dataset and in
UKDL; it does not receive a dataset of its own. Final system-vs-law counts are Phase 2.

## 5. The source's own architectural ruling

At source lines **30,124–30,186** the corpus explicitly decides **not** to build USIFB as
its own mega-silo with its own databases, graphs and detectors, but as *analysis modes and
discovery strategies layered over six shared institutional planes*. The range-2 inventory
agent independently recorded this as a recurring structural pattern across the whole range.

This is the same shape as the CRPF strike, where the donor corpus's own duplicate-to-
advantage map had already scored its mechanisms as EXTEND. **The source is not asking for
sixty sovereign fabrics. It is asking for shared primitives with many analysis modes over
them** — which is what the D2A verdicts above would produce.

## 5. Phase 3b COMPLETE — the final nine, and a measurement flaw caught first

### 5.1 The flaw: the mission's own artifacts contaminated its own denominator

The first run of this sweep returned `SOURCE_INVENTORY_FULL.json` as the **top hit for 7 of
10 probes**. That file is *this mission's own inventory*, committed an hour earlier, and it
quotes the source corpus's vocabulary verbatim. The sweep was measuring my own output and
would have reported it as estate ownership — `HIC-OAR` would have scored 96 hits instead of
its true 0.

**Measuring your own artifact is not evidence.** The sweep now excludes every path matching
`ucr_cif` / `ucr-cif` before the corpus is built. Recorded in `03_MISSION_TRAPS.md`.

This is a general hazard for any audit that writes into the tree it audits, and it grows
with each commit: the longer a corpus mission runs, the more its own output pollutes its
own denominator.

### 5.2 Results, self-contamination removed

| # | System | Hits | Files | Verdict |
|---|---|---:|---:|---|
| 2 | **HIC-OAR (whole)** | **0** | **0** | **TRUE ZERO at capability level** |
| 4 | **Constitutive Baseline Ratchet** | 4 | 4 | near-zero, 1 hit/file — dispersed mentions, no owner |
| 3 | **UDFLL** | 4 | 2 | near-zero (`deep-research` 2, `sqi_02` 2) |
| 7 | **Meta-Failure Genome** | 5 | 5 | near-zero, 1 hit/file — no owner |
| 1 | **UCR-CIF umbrella** | 8 | 2 | near-zero; 7 of 8 in `pp_dataset_18_order_of_magnitude_compounding_os` — adjacent, not the same object |
| 6 | Knowledge Compiler / Linker | 56 | 39 | **EXTEND** → `daif_01_type_system_v1` (10) |
| 5 | Capability Authority Registry | 60 | 21 | **PARTIAL** — top hit `vault/audits/upac/SYSTEM_OWNERSHIP_OVERLAP_MAP.md` (23) is an *audit artifact*, not a runtime registry |
| 9 | Long-Horizon Campaign | 240 | 110 | **OWNED/EXTEND** → `daif_07` (18) · `modules/cognitive_os/rehydration.py` (11) · hibernation plan + `test_hibernation.py` |
| 8 | Institutional SLOs & Chaos Mutation | 572 | 129 | **OWNED** → `ias_e2_cognitive_reliability` (100) · `tools/oracle_chaos.py` (21) |
| 10 | Resident Institutional Kernel | 4,393 | 483 | **DISPERSED** — `hooks/` (100) and `tools/` (384) carry the mechanism; no owning module |

`HIC-OAR` returning a **true zero** across ten distinct functional probes — `work class`,
`one-shot rate`, `supervision depth`, `autonomy pack`, `certified one-shot`,
`avoidable human`, `intervention ledger`, `autonomy maturity`, `human burden` — is the
strongest novelty signal in the entire audit. It is also consistent: the engine independently
kept `Human Intervention Ledger` as one of only four KEEPs.

### 5.3 Final tally — 28 spine systems

| Verdict | Count | Systems |
|---|---:|---|
| **CREATE candidate** (capability-level near-zero, two independent instruments) | **6** | HIC-OAR (+ its Ledger) · Certified Primitives & Golden Paths · Constitutive Baseline Ratchet · UDFLL · Meta-Failure Genome · RCFC |
| **EXTEND** | 8 | UBC · IFC · UFIA-EBF · SEEIP · KIFS/USIFB · Knowledge Compiler/Linker · Proof-Carrying Capabilities · Autonomous Convergence Contract |
| **REFERENCE / OWNED** | 10 | Crawl OS · URCE · CIR · Epistemic Types · Universalization/Portable Packs · Institutional State Runtime · TTPE/TTIA · Institutional SLOs & Chaos · Long-Horizon Campaign · UCR-CIF umbrella (adjacent to `pp_dataset_18`) |
| **UNRESOLVED** | 4 | Constitutional Microkernel (33 %) · Capability Authority Registry (audit-only owner) · Resident Institutional Kernel (dispersed) · Mission Baseline Capsule / Project Genome (UBC residual) |

**CREATE rate: 6 of 28 = 21 %** — inside this estate's measured historical band
(CPP-IAS 9 %, DAIF 36 %, RE Baseline 25 %) and arrived at by measurement rather than by
matching the band.

**HR-NOVELTY-001 still applies.** None of the six is admitted until the 13-question proof
is answered against a discovered sweep. This audit sizes the candidate set; it does not
approve it.

## 6. What this audit does not claim

- It does **not** claim the 24 DEFER systems are owned. They are unresolved.
- It does **not** claim the 4 KEEP systems are approved for construction. HR-NOVELTY-001
  requires the 13-question proof against a discovered sweep before any new institutional
  system is admitted; that proof has not been run.
- It does **not** close Phase 1. One range is still in flight and one needs re-running.
