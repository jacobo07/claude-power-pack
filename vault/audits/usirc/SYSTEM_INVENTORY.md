---
title: USIRC STOP #1 — System Inventory (discovered denominator)
date: 2026-07-31
method: filesystem enumeration + measured vocabulary sweep. Every count below was
  produced this session by counting the thing, never by reading a registry someone
  maintains by hand (PR-COVERAGE-BY-CONSTRUCTION-001).
source_document: "Downloads/Dataset Claude Power Pack Universal System Intelligence &
  Reconstruction Civilization 1.txt" — 6,395 lines / 85,908 bytes, read to EOF
---

# System Inventory — the denominator this audit measures against

## 1. Observed counts (2026-07-31, this session)

| Surface | Count | How measured |
|---|---|---|
| Python module packages | **75** | `(Get-ChildItem modules -Directory).Count` |
| Knowledge-base dataset families | **26** | `(Get-ChildItem vault\knowledge_base -Directory).Count` |
| Vault governance sub-surfaces | **64** | `(Get-ChildItem vault -Directory).Count` |
| Hooks | **38** | `(Get-ChildItem hooks -File).Count` |
| Commands | **64** | `(Get-ChildItem commands -Filter *.md).Count` |
| Repo-local agents | **12** | `(Get-ChildItem agents -Filter *.md).Count` |
| Tools (`.py`) | **289** | `(Get-ChildItem tools -File -Filter *.py).Count` |
| Files swept for the vocabulary measurement | **1,350** | `.md/.txt/.py/.js/.json` under `vault/knowledge_base`, `modules`, `tools`, `commands`, `hooks`, `governance`, `agents`, `rules`, `knowledge` |
| Graph coordinates | 1,190 local (+460 cross-repo) | GK-12 advisory, observed live this session |
| Compiled hard rules | 156 | `vault/hard_rules/compiled/rules_db.json` |

The sibling audit `vault/audits/ccfl_pdpf/SYSTEM_INVENTORY.md` (same date, concurrent
pane, **untracked**) recorded 63 vault sub-surfaces where this one measures 64. Both
were measured; the delta is a directory created between the two runs. Recorded rather
than silently reconciled.

## 2. The 26 knowledge families

`acis` · `cdio` · `clae` · `cognitive_os` · `cpcsc` · `cpp_aci` · `cpp_ias` · `craif` ·
`crawl_os` · `d2a_fabric` · `dataset_first` · `decision_review` ·
`duplicate_to_advantage` · `enforcement` · `fable_distillation` ·
`frontier_intelligence_os` · `graphify` · `parallel_mesh` · `pp_dataset` · `scs` ·
`sdd_os` · `session_resilience` · `setup_os` · `sqi` · `testing` · `visual-patterns`

## 3. Every surface the source document names, verified on disk

The source asserts a list of PP surfaces it claims to have inspected. All were probed
with `Test-Path` this session:

| Surface named by the source | Present |
|---|---|
| `modules/cdio` · `vault/knowledge_base/cdio` · `hooks/cdio_visual_advisory.js` | YES |
| `modules/autoresearch/video_analyzer.py` | YES |
| `tools/replay_harness.py` · `vault/forensic/REPLAY_SCHEMA.md` | YES |
| `modules/omnicapture` | YES |
| `modules/oracle/ovo-protocol.md` · `commands/omni-verification-oracle-audit.md` · `tools/oracle_{delta,chaos,cascade}.py` | YES |
| `modules/mirror_discovery` · `vault/standards/mirror-parity-law.md` | YES |
| `modules/{duplicate_to_advantage,liveness,craif,arch-decision,auto-testing,dataset_first,akos_knowledge,decision_review}` | YES |
| `modules/{sqi,sleepless_qa,done_gate,output_contracts,uqf,sdd_os,daif,cascade_prevention,ias_c2,contract_fabric}` | YES |
| **KADOS** — named 5× as a bridge target | **ABSENT.** One mention repo-wide, inside `vault/plans/ksf-compendium-2026-07-26.md`. It is not a PP system. |
| `modules/crawl_os` | ABSENT as a module; the family is `vault/knowledge_base/crawl_os` (19 datasets, 5 SEALED, build ACTIVE) |

**Finding I-1.** The source's inventory of PP is accurate on 9 of 10 rows. Its single
structural error is load-bearing: it routes causal-divergence output to **KADOS**, a
system that does not exist in this repo, and names it alongside CRAIF as if both were
peers here. Every USIRC design element that depends on "hand the divergence to KADOS"
rests on an unverified premise (CLASE 1, `root_cause_taxonomy.md`).

## 4. Measured vocabulary sweep (1,350 files)

The admission instrument that CLAE passed and CRPF/IGEF failed: sweep the proposal's
own distinctive vocabulary against the corpus and report file-hit counts.

| Term | Files | Reading |
|---|---|---|
| `evidence coverage` | **0** | |
| `coverage contract` | **0** | |
| `fidelity tensor` | **0** | |
| `golden trace` | **0** | |
| `production equivalence` | **0** | |
| `divergence graph` | **0** | |
| `earliest causal` | **0** | |
| `universal system model` | **0** | |
| `reconstruction graph` | **0** | |
| `doppelganger` / `executable twin` | **0** | |
| `behavioral genome` | **0** | |
| `hypothesis lattice` | **0** | |
| `shadow execution` | **0** | |
| `capability transplant` | **0** | |
| `intentional divergence` | **0** | |
| `known differences ledger` | **0** | |
| `pixel diff` / `perceptual diff` / `image diff` | **0** | the only genuinely absent *instrument* class |
| `hidden state` | 1 | |
| `epistemic debt` | 2 | |
| `fidelity budget` | 3 | DAIF-03 |
| `reverse engineer` | 3 | `ecc-reverse-engineering.md` is a practice record, not a system |
| `visual regression` / `visual baseline` | 3 | |
| `behavioral equivalence` | **7** | DAIF-03 owns the term outright |
| `digital twin` | **21** | `cpp_ias` F3 |
| `counterfactual` | **28** | DRK-04 |
| `state machine` | **45** | PP's own state machines, not reconstruction of an observed one |
| `production reality` | **49** | CLAE Part XXV consolidates 19 gates |
| `replay` | **54** | `tools/replay_harness.py` + REPLAY_SCHEMA |
| `provenance` | **122** | crawl_os DS10, 25 Parts, sealed |

**Finding I-2 — and the reason this table cannot be read naively.** A zero is a
statement about *vocabulary*, never about *mechanism*
(`feedback_zero_cannot_fall`: a gate bounded by its vocabulary reads an unrecognized
idiom as 0, and 0 never falls). Every zero above was therefore re-tested against the
mechanism, not the phrase, in `CAPABILITY_OVERLAP_MATRIX.md`. Nineteen of the
twenty-one zeros resolved to a named owner under different words. Two did not:
image-domain differential instruments, and a typed model of an *external* observed
product.

## 5. Families load-bearing for this proposal (measured state)

| Family | State | Object it owns |
|---|---|---|
| **`crawl_os`** | 19 datasets, **5 SEALED** (01, 02, 03, 10, 16), ~117k words, build **ACTIVE**, next action named (DS04) | verifiable acquisition of external evidence · Evidence Object · provenance and integrity (DS10, 25 Parts) · **authorization, compliance and safety (DS16, 25 Parts)** · adaptive acquisition strategy routing (DS03) · mission compilation (DS02, 16-field contract) |
| **`d2a_fabric`** (DAIF) | **8/8 SEALED, 160/160 Parts**, 292,276 words | typed cognitive representations (DAIF-01 ontology, DAIF-02 twelve CIRs) · **DAIF-03 Fidelity, Loss Budget and Behavioral Equivalence (20 Parts, 38,694 w) — and the absorbed metric authority** · DAIF-04 contract fabric · DAIF-07 obligation and work-completion authority · DAIF-08 context assembly and mission runtime · **DAIF-21 reality synchronization and semantic change** |
| **`clae`** | **26/26 SEALED** | measurement against an **external reference**: the reference object, reference acquisition/versioning/provenance, delta extraction, delta impact ranking, the top-K correction cycle, quality-distance accounting, anti-underbuild floors, the **instrument taxonomy (Part XIII)**, the **human oracle boundary and routing (XVI–XVII)**, deviation governance, **99 traps (XXII)**, **118 process rules (XXIII)**, evals (XXIV), **19 production-reality gates (XXV)** |
| **`acis`** | ACIS-00/01, `epistemic_ladder.py` live | the epistemic status of every claim: ladder E0–E7, falsifier discipline, **the No-Autopromotion Invariant**, `epistemic_algebra.py` |
| **`craif`** | sealed, conformance checker + `/craif-conformance` live | causal investigation completeness: candidates, evidence, closure |
| **`decision_review`** (DRK) | DRK-00…07, kernel + 4 modules live | decision soundness before acting; **DRK-04 counterfactual simulation and horizons**; prediction-vs-outcome accountability |
| **`cpp_ias`** | 14 datasets, 478,208 words | the PP *ensemble*: **F3 institutional digital twin (32,802 w)**, D2 immune system, observability fabric, capability economics |
| **`sqi`** | executable; `run_sqi.py` exits non-zero on a silent decrease | verification that executable reality is real: weakening detectors, red-team protocol, baseline guardian, environment qualification |
| **`fable_distillation`** (FD) | FD-00…07 sealed | frontier delta → portable advantage; **FD-03 routes every insight to Hard Rule / Process Rule / Trap / dataset Part / benchmark / prompt fragment / discard**; FD-04 six-lens transfer test |
| **`frontier_intelligence_os`** | 4 engines live | `unknown_unknown_generator.py` (structural absence over a discovered cohort) · `evolution_engine.py` (KB mutation proposals, Owner-gated) |
| **`graphify`** | live, GK-00…12 | knowledge location and the causal coordinate graph. **Standing rule: it owns the semantic IR; no successor stands up a second graph.** |
| **`sleepless_qa`** | dumpers · verdict · healer | evidence bundles from a running app; `verdict/visual.py` = LLM verdict on a **single** screenshot (working/broken), not a reference comparison |
| **`osa`** | `gpu_eyes.py` (SSH+Xvfb+scrot), `never_again.py` | screen **capture** with graceful degradation; `visual_qa_passed` is `None` when no capture exists |
| **`omnicapture`** · `tools/replay_harness.py` · `modules/oracle` | live | runtime reality · deterministic replay (MATCH/DIFF/SHIM_ERROR/SKIPPED) · the oracle protocol OVO |
| **`liveness`** | `reachability.py` + registry | whether a declared capability is reachable from a real surface |

## 6. Prior-art record this audit inherits

`vault/knowledge_base/COMPENDIUM_CLOSURE_REPORT.md` (2026-07-29) records **six
consecutive corpus proposals measured as majority-owned**: AISHF 75–80 %, RE Baseline
55–60 %, KSF 70–80 %, CRPF ~80 %, IGEF 0 of 4, E1–E5 15 of 17. Of four chartered
families, one was built.

Since that report, **three more** audits ran, all on 2026-07-30/31:

| Audit | Candidates | Survivors |
|---|---|---|
| IIG Compendium (`vault/plans/iig-compendium-2026-07-30.md`) | 30 (A–AD) | 0 families; 1 Hard Rule (HR-NOVELTY-001, now sealed) |
| Emergence Runtime (`92e2fb0`, `5163fc2`) | 1 | 0 — `EXTEND_EXISTING_OWNER` (`tools/dataset_enricher.py`) |
| CCFL-PDPF (`vault/audits/ccfl_pdpf/`, untracked, concurrent pane) | 1 family | 0 families; 4 narrow gaps (G1–G4) |

**USIRC is the ninth proposal measured against this denominator.** The base rate is
not context — it is the strongest single piece of prior evidence bearing on this
STOP, and HR-NOVELTY-001 fired on this prompt automatically for exactly that reason.
