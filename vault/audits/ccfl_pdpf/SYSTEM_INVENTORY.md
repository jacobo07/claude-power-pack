---
title: CCFL-PDPF STOP #1 — System Inventory (discovered denominator)
date: 2026-07-31
method: filesystem discovery, not recall. Counts are observed, not asserted.
source_document: Downloads/Dataset Claude Cognitive Failure Lineage & Predictive Defect Prevention Fabric 1.txt (5,292 lines, 112,467 bytes, read to EOF)
---

# System Inventory — the denominator this audit measures against

`PR-COVERAGE-BY-CONSTRUCTION-001` is active: every number below was produced by
enumerating the filesystem, never by consulting a registry that someone maintains
by hand. Five prior audits in this estate were wrong because a component absent
from the denominator read as a gap.

## Observed counts (2026-07-31)

| Surface | Count | How measured |
|---|---|---|
| Python module packages | **75** | `modules/*` directories |
| Knowledge-base dataset families | **26** | `vault/knowledge_base/*` directories |
| Vault governance sub-surfaces | **63** | `vault/*` directories |
| Hooks | **38** | `hooks/*` files |
| Commands | **64** | `commands/*.md` |
| Repo-local agents | **12** | `agents/*.md` |
| Graph coordinates | **1,190** local (+460 cross-repo) | GK-12 advisory, live |
| Compiled hard rules | **156** | `vault/hard_rules/compiled/rules_db.json` |

## The 26 knowledge families

`acis` · `cdio` · `clae` · `cognitive_os` · `cpcsc` · `cpp_aci` · `cpp_ias` ·
`craif` · `crawl_os` · `d2a_fabric` · `dataset_first` · `decision_review` ·
`duplicate_to_advantage` · `enforcement` · `fable_distillation` ·
`frontier_intelligence_os` · `graphify` · `parallel_mesh` · `pp_dataset` · `scs` ·
`sdd_os` · `session_resilience` · `setup_os` · `sqi` · `testing` · `visual-patterns`

## The families that matter for this proposal (measured size and state)

| Family | State | Observed scale | Object it owns |
|---|---|---|---|
| **`cpp_ias`** (CPP-IAS) | 14 datasets, repatriated 2026-07-20 | **478,208 words** | the *ensemble* of PP's modules and families, one level up. Includes **D2 Institutional Immune System and Failure-Mutation Intelligence** (36,040 w, 25 Parts) and **F3 Institutional Digital Twin and Simulation** (32,802 w) |
| **`d2a_fabric`** (DAIF) | **8/8 SEALED**, 160/160 Parts | 292,276 words | typed, evidence-grounded, resumable representations of cognitive work; obligation lifecycle; context runtime; reality synchronization |
| **`crawl_os`** | 19-dataset family, **5 SEALED** (01, 02, 03, 10, 16), build ACTIVE, next action named (DS04) | ~117,000 words | verifiable acquisition of external evidence, Evidence Objects, provenance, authorization |
| **`clae`** | **26/26 SEALED** 2026-07-29 | 26 Parts | measurement against an external reference: delta, distance, floors, oracle boundary, deviation, closure. Part XXI is *Failure Modes and Failure Lineages*; Part XXII is a **99-trap registry**; Part XXIII holds **118 process rules**; Part XXV consolidates **19 production-reality gates** |
| **`decision_review`** (DRK) | DRK-00…07 written, kernel + 4 modules live | 9 units | whether a decision is correct/necessary/proportional/reversible/evidenced *before* the stack acts, and whether the reasoning was sound in hindsight. **DRK-04 is Counterfactual Simulation and Horizons** |
| **`acis`** | ACIS-00/01, `epistemic_ladder.py` live | 2 datasets | the **epistemic status** of every claim: ladder E0–E7 + falsifier discipline + the No-Autopromotion Invariant |
| **`cognitive_os`** (CO) | CO-00…CO-14, 11 modules | 16 files | session cost, context budget, routing, telemetry (**CO-12**), residency |
| **`frontier_intelligence_os`** (FIOS) | 4 engines live, execution-first | code + 1 index | frontier session execution; **`unknown_unknown_generator.py`** (structural-absence discovery over a DISCOVERED cohort); **`evolution_engine.py`** (whole-KB mutation proposals, Owner-gated) |
| **`fable_distillation`** (FD) | FD-00…07 sealed | 8 datasets | frontier delta → portable advantage. **FD-03 routes every insight to Hard Rule / Process Rule / Trap / dataset Part / benchmark / prompt fragment / discard** |
| **`sqi`** | executable, `run_sqi.py` exits non-zero on silent decrease | 4+ datasets | verification that executable reality is real; **`weakening_detectors.py`**, **`redteam_protocol.py`**, `baseline_guardian.py` |
| **`duplicate_to_advantage`** (D2A) | engine live, 25/25 gates | — | what happens when something already partly exists |

## Modules load-bearing for this proposal

| Module | Observed contents | Relevance |
|---|---|---|
| `cascade_prevention` | `engine.py`, `blocker.py`, `pre_mortem.py`, `dangerous_cmds.py`, `surfaces.py`, `types.py` | in-session cascade chains A→B→C; five HR-CASCADE rules |
| `sweep_enforcer` | `rule_sweep.py` | **runs the sweep at seal time against the live tree** — a rule that fixes only the file that triggered it is refused; proposes a collapse when it governs ≥2 sites |
| `osa` | `never_again.py` + `vault/osa/never_again_log.jsonl` | negative institutional knowledge, recurrence counts |
| `hard_rules` | `extractor.py`, `residual.py`, digest router | 156 sealed rules; `tools/bug_to_hardrule.py` converts an incident to a rule |
| `rule_compiler` | `schema.py`, `digest.py` | rule admission and placement; retired-class tracking |
| `error_prevention` | `premise_verifier.py` | a plan's named APIs/files verified before code is written against them |
| `liveness` | `reachability.py` + registry | whether a shipped module is reachable from a live surface |
| `backlog_autopilot` | `engine.py` (a scoring function), `tracked.py` | `what_now` ranking; **no lifecycle, no promotion/demotion states** |
| `owner_queue` | `owner_queue.py` | escalation queue to the Owner |
| `decision_review` | `decision_kernel.py`, `decision_record.py`, `accountability.py`, `providers.py`, `proactive_scanner.py`, `epistemic_algebra.py` | decision authentication + **prediction-vs-outcome scoring** + 4 evidence-mandatory proactive detectors on a daily task |
| `frontier_intelligence` | `session_compiler.py`, `unknown_unknown_generator.py`, `token_irr.py`, `evolution_engine.py` | frontier execution + absence discovery + KB mutation proposals |
| `cognitive_os` | `co_12_telemetry.py`, `economics.py`, +9 | the single telemetry instrument; no parallel accountant permitted |

## Persisted failure record already on disk

- `vault/ceps/events.jsonl` + `vault/ceps/patterns.db` — the cascade/error event store, with 20 empirical scoring runs.
- `vault/osa/never_again_log.jsonl` — the NEVER_AGAIN log with recurrence counts.
- `vault/knowledge_base/root_cause_taxonomy.md` — **CLASE 0–5**, ranked by *observed* recurrence, each naming its causal mechanism and its structural fix.
- `vault/knowledge_base/session_lessons.md`, `vault/knowledge_base/scs/` (SCS C44…C95) — the sealed incident casebook.
- `vault/hard_rules/compiled/rules_db.json` — 156 rules, each carrying the incident that produced it.

## Prior-art record this audit inherits

`vault/knowledge_base/COMPENDIUM_CLOSURE_REPORT.md` (2026-07-29) records **six consecutive
corpus proposals measured as majority-owned**: AISHF 75–80 %, RE Baseline 55–60 %,
KSF 70–80 %, CRPF ~80 %, IGEF 0 of 4 mechanisms, E1–E5 15 of 17 mechanisms. Of four
chartered families, **one was built**. The standing obligation sealed by Owner ruling on
that date: *run the overlap audit against a complete, discovered denominator BEFORE any
construction.* This file is that denominator.
