---
title: EGCC — Evidence-Grounded Governance Compiler & Constitutional Runtime — Phase 0 Ownership Audit
date: 2026-08-06
status: STOP #1 — BLOCKING, presented inline, no dataset written
verdict: MAJORITY_OWNED — 0 of 25 proposed datasets clear HR-NOVELTY-001 as GENUINELY_NEW_DATASET
source: "Downloads/Dataset Evidence-Grounded Governance Compiler & Constitutional Runtime 1.txt"
  — 7,263 lines, read to EOF across three passes
precedent: fourteenth consecutive mega-corpus proposal measured majority-or-fully owned
covers: [egcc, governance_compiler, constitutional_runtime, ownership_audit, stop1]
residue: three candidate residues, all sub-dataset scale; one premise refuted outright
---

# EGCC — Phase 0 Ownership Audit

## PHASE 0 — Environment reality scan (OBSERVED from disk, not recalled)

| Surface | Count | Instrument |
|---|---|---|
| Modules | 78 directories | `Get-ChildItem modules -Directory` |
| Knowledge families in `vault/knowledge_base/` | 26 | same, on `vault/knowledge_base` |
| `vault/` top-level domains | 69 | same, on `vault` |
| Governance docs | 11 | `governance/*.md` |
| Commands / agents | 67 / 12 | `commands/`, `agents/` |
| Corpus audits in `vault/plans/` | 18 STOP-bearing plans | `STOP_LEDGER.md` |
| Open STOP #1 | **8 OPEN** · 6 CONTRADICTED · 4 RESOLVED | `modules/owner_queue/stop_ledger.py` |
| HEAD | `9359b27` | `git log --oneline -5` |
| REMOTE_DELTA | `0 0` | `git rev-list --left-right --count origin/main...HEAD` |

**Decisive prior fact.** Two of the five most recent commits are `uceimr`. The UCEIMR
audit of **2026-08-04 — two days ago** — measured a fifteen-dataset family on
substantially this ground and returned `MAJORITY_OWNED, 0 of 15`. Its Sprint-2
expansion pass then drove the shipped `compute_expansion()` with the real family and
got `expansion_slots = 0`. The five narrow mechanisms it did find (G1–G5) are the
commits sitting at HEAD right now. EGCC arrives into an estate that finished auditing
this exact territory 48 hours ago and then shipped the residue.

## PHASE 1 — Ownership verdicts, all 25 proposed datasets

Verdicts are mechanism-tier. Every REJECT was reached by **opening** the nearest
incumbent, never by a phrase failing to grep
(`feedback_zero_cannot_fall`, `T-OWNERSHIP-AUDIT-ABSORPTION-BIAS-001`).

### Familia A — Constitution and constitutional philosophy

| DS | Proposed | Verdict | Real owner (verified this session) |
|---|---|---|---|
| A1 | Constitutional Foundations | REJECT | 156 compiled rules → 143 binding (`enforcement_scs_c92.md:43`); `acis_01_generation_zero_laws`; `craif_00`; `daif_00`; `clae` (26 Parts); `governance/` (11 docs); `capability_runtime/contract.py::validate` makes constitutional claims *executable*. Identical ground to UCEIMR DS01, SEIP A1, EFAIF DS01 — all REJECT. A sixth constitution adds no mechanism. |
| A2 | Jurisprudence, Precedent, Nullification | **REJECT — premise refuted** | `modules/hard_rules/residual.py` measured the corpus and found **prohibitions only, zero mandates**. Its thesis: *"prohibitions cannot contradict one another — they can only jointly shrink the set of legal moves. So there is no precedence to compute."* EGCC's constitutional court, precedence hierarchy and nullification machinery all presuppose that rules conflict. That premise is measured false on this corpus. The shipped answer is the **residual move**, asserted rather than assumed, with `UNSAFE_JOIN` / `UNDECIDABLE` / `NO_RESIDUAL` as honest refusals. Sealed as `feedback_prohibitions_do_not_conflict`. |
| A3 | Governance Ontology & Taxonomy | REJECT (drift half → Rc2) | Rule ontology: `rule_compiler/schema.py` (`Form`, `Reason`, 12 named rejection causes), `hard_rules/`, UKDL, `sqi/CANONICAL_ONTOLOGY.md`. Drift taxonomy exists but is **distributed** across `setup_os/drift_detector.py`, `sqi/baseline_guardian.py`, `osr/compare.py`, `cpc_os/topology_reconcile.py`, `liveness/`, `session_delta` — see Rc2. The source itself warns against a flat list ("una lista rígida terminaría convirtiéndose en burocracia", line 4420). |

### Familia B — Governance compilation

| DS | Proposed | Verdict | Real owner |
|---|---|---|---|
| B1 | Governance Evidence Engine (CrawlOS) | REJECT | `vault/knowledge_base/crawl_os/` — sealed dataset contracts incl. DS10 evidence-provenance-integrity (source/confidence/recency) and DS03 adaptive acquisition routing; plus `modules/akos_knowledge`, `autoresearch/`, `deep-research/`, `frontier_intelligence/question_harvester.py`. UCEIMR DS02 REJECT verbatim, and that source conceded the duplication itself. |
| B2 | Constitutional Compiler — policy → executable rules | REJECT | **`modules/rule_compiler` is this system, shipped.** `parser.py` · `schema.py` (form recognition, per-field rejection with named reasons, measured boilerplate detection) · `compiler.py` · `digest.py` (router digest, 2,154 B under a 4,096 cap) · `detectors.py` · `effect_harness.py` · `counterfactual.py`. Corpus: 156 → 143 binding, 13 rejected with per-field reasons. |
| B3 | Policy Abstraction & Semantic Equivalence | REJECT | `d2a_engine.detect_duplicate` → `DupeVerdict` → `map_gap` → `_anti_inflation` → `govern_build`; `modules/duplicate_to_advantage`; `vault/knowledge_base/d2a_fabric`. Promotion ladder owned by ACIS E0–E7. |

### Familia C — Constitutional runtime

| DS | Proposed | Verdict | Real owner |
|---|---|---|---|
| C1 | PDP/PEP/PAP/PIP + enforcement modes | EXTEND → **Rc1** | The four points exist unnamed: PAP = `vault/hard_rules/` + archives; PDP = `digest.py` + the CLAUDE.md router; PEP = the hook dispatcher (`Write`/`Edit`/`Bash` gates, `secret_firewall_gate.js`, `spec_gate`, `done_gate`); PIP = `graphify` (1,238 coordinates) + `_audit_cache`. Genuinely absent: an explicit `enforcement_level` field on `Rule` (the proposed 8-level ADVISORY…EMERGENCY_STOP ladder). `schema.py:110-122` carries `severity`, not enforcement level. **A field plus a gate, not a dataset.** |
| C2 | Constitutional Agents & Orchestration | REJECT | 12 agents in `agents/`; `modules/pp_agents`; `modules/agent-governance` (OWASP ASI); `modules/dispatcher`; `modules/parallel_mesh`. The source's own rule — prefer a deterministic tool over an agent — is already the PP `cdio-standards-librarian` / `graphify-librarian` cost contract (HR-COST-001). |
| C3 | Constitutional Observability & Traceability | REJECT | `modules/decision_review` (`accountability.py`, `decision_kernel.py`, `epistemic_algebra.py`, `outcome_recorder.py`) — the DecisionRecord **producer shipped at HEAD as G4**; `vault/decision_registry/`; `vault/rule_effects/`; `modules/liveness/liveness_ledger.py`. |
| C4 | Constitutional State Machine & Lifecycle | EXTEND — **already shipped 48h ago** | `capability_runtime/retirement.py` (retirement probes = UCEIMR G2, at HEAD); `backlog_autopilot/stop1_queue.py` (STOP #1 transition producer = G1, at HEAD); `owner_queue/stop_ledger.py` (the 18-plan disposition ledger). The defect EGCC names — a status field nobody can transition — is sealed as `feedback_status_field_nobody_can_transition` and was **fixed this week**. |

### Familia D — Evidence-grounded governance

| DS | Proposed | Verdict | Real owner |
|---|---|---|---|
| D1 | Evidence-Grounded Rule Generation | REJECT | `tools/bug_to_hardrule.py` → `hard_rules/extractor.py` + `writer.py` → `rule_compiler` schema gate. Rule-quality metrics are the 12 `Reason` codes, each with `REASON_HELP` prose. CEPS supplies the recurrence signal. |
| D2 | Risk-to-Rule Mapping & Invariant Extraction | REJECT | `modules/cascade_prevention` (C3/C4 detectors, `dangerous_cmds.py`), `modules/error_prevention/premise_verifier.py`, DRK-01…07 (DRK-02 reversibility/blast radius, DRK-03 evidence burden), `modules/arch-decision`. |
| D3 | Constitutional Supply Chain & Provenance | REJECT | crawl_os DS10; `modules/dataset_first`; `vault/decision_registry/`; `modules/secret_firewall` (7 HRs incl. supply-chain rotation doctrine); graphify typed edges. |

### Familia E — Drift, evolution, immunity

| DS | Proposed | Verdict | Real owner |
|---|---|---|---|
| E1 | Constitutional Drift Detection | EXTEND → **Rc2** | Owned in pieces at ≥ equal maturity per piece: `setup_os/drift_detector.py`, `sqi/baseline_guardian.py` + `weakening_detectors.py` + `weakening_baseline.py`, `osr/compare.py`, `cpc_os/topology_reconcile.py`, `modules/session_delta` (wired in the Stop chain), `modules/liveness`, `modules/sweep_enforcer`. Unowned: a single registry naming the families. **A view over existing detectors, not a detection system.** |
| E2 | Evolution & Amendment Protocol | REJECT | `modules/owner_queue` + `STOP_LEDGER.md` (disposition witnessed, never asserted; a plan may not witness itself); `ukdl_queue.py`; ACIS E0–E7 with `retirement_conditions` ("a law with no retirement condition is dogma, not science"); `modules/sqi` ratchet. |
| E3 | Immunity & Cross-Project Transfer | REJECT | **IAS-D2 owns "CROSS-PROJECT IMMUNITY" by name.** Plus `capability_runtime/derivatives.derive(project, overrides)` under HR-APA-016/017; `modules/setup_os`; `governance_vaccines.md`; the `compound-learnings` skill; FD-06/FD-07 flywheel live in the Stop chain. |

### Familia F — Evaluation and benchmarks

| DS | Proposed | Verdict | Real owner |
|---|---|---|---|
| F1 | Governance Benchmarks | **DO-NOT-BUILD** | SQI: 4 sealed datasets, 108,598 words, `run_sqi.py` (45/45 ×3), `BenchmarkScenario`, anti-Goodhart contract §5. **Fourth-time precedent on this exact ground**: PQC rejected 2026-07-12 · EFAIF DS20 DO-NOT-BUILD 2026-08-04 · SEIP G1 REJECT 2026-08-04 · UCEIMR DS13 DO-NOT-BUILD 2026-08-04. |
| F2 | Red Team & Adversarial Governance | REJECT | `sqi/redteam_protocol.py`; `vault/audits/sovereign_objection.md`; `modules/sleepless_qa`; `modules/bug-hunter`; `omni-singularity`; `output_contracts` slop veto. Bypass/gaming/capture each have a named owner. |
| F3 | Governance Economics & ROI | REJECT | `modules/cost_collapse` (route classes + OD3 ceilings), `modules/recall_roi`, `corpus_roi.py`, `token_irr.py`, `tools/tco_compact_gate.py`, `vault/tco/`. `effect_harness.py` supplies the benefit half — whether adopting a rule moved a metric. |
| F4 | Self-Evaluation & Metascience | REJECT | ACIS E0–E7 with the derived-level cap at E3 (no self-certification, `PR-ACIS-FALSIFIABILITY-001`); `sqi` guardian exits ≠0 on a silent decrease; `modules/uqf`. **This audit series is the mechanism** — 14 consecutive self-critical measurements against a discovered denominator. |

### Familia G — Twins and simulation

| DS | Proposed | Verdict | Real owner |
|---|---|---|---|
| G1 | Constitutional Digital Twins | REJECT — no consumer | Nothing here models a constitution as a twin, and nothing asks for one. Every question the twin was specified to answer already has an executable answer: "would removing this rule matter" → `effect_harness`; "would it have caught the incident" → `counterfactual.py`; "what depends on this rule" → graphify; "what is stale" → `liveness`. A twin whose queries are all already answered is a second source of truth, prohibited by `usirc/BOUNDARY_CONTRACT.md`. |
| G2 | Governance Simulation & Policy Testing | **REJECT — shipped** | `modules/rule_compiler/counterfactual.py` **is** the source's own headline mechanism (line 765: *"Si esta regla hubiera existido antes, ¿habría evitado realmente los fallos observados?"*). It binds rule id + recorded incident + runnable detector, replays the preserved input, and returns `WOULD_BLOCK` / `WOULD_NOT_BLOCK` / `UNMEASURABLE` — exiting 1 only on `WOULD_NOT_BLOCK`. Conflict simulation → `residual.py` `--audit-corpus`. |

### Familia H — Datasets, memory, architecture

| DS | Proposed | Verdict | Real owner |
|---|---|---|---|
| H1 | Constitutional Datasets & Institutional Memory | REJECT | `modules/dataset_first`; `modules/daif` (8 datasets / 160 Parts sealed); `modules/akos_knowledge`; graphify GK-08 negative-knowledge writeback; the distiller's Negative Knowledge Vault; `modules/memory-engine`. Episodic/semantic/procedural/negative memory is the shipped split. |
| H2 | Constitutional API & Developer Experience | REJECT | 67 commands; `modules/skill_router`; the hook dispatcher (PreToolUse/Stop chains); `modules/sdd_os` (`activation.py`, `pre_exec_gate.py`, `scaffold.py`); `modules/harness`. |
| H3 | Architecture Integration Map | REJECT | **USIRC, built 2026-07-31**: `SOURCE_OF_TRUTH_MAP` · `OWNERSHIP_OVERLAP_MATRIX` · `BOUNDARY_CONTRACT` · `INTEGRATION_RESPONSIBILITY_MATRIX` · `NON_DUPLICATION_LEDGER` · `DATASET_ARCHITECTURE_DECISION_LEDGER`. Identical to EFAIF DS26 and UCEIMR DS15, both ruled. |

**Result: 0 of 25 clear HR-NOVELTY-001 as `GENUINELY_NEW_DATASET`.**
Distribution: **21 REJECT · 1 DO-NOT-BUILD · 3 EXTEND**, and two of the three EXTENDs
were shipped 48 hours ago as UCEIMR G1/G2/G4.

## The source's own eighteen hard rules, individually

HR-GOV-001…018 were checked against the corpus rather than adopted. Fourteen are
already binding PP doctrine under other ids — 002 (no rule from a single weak source)
is `schema.py` evidence validation; 003 (enforcement must be declared) is Rc1, the one
genuine gap; 004 (unenforceable rules cannot masquerade as controls) is the 13-rule
rejection set; 005 (violation evidence) is the block-artifact ritual; 012 (executable
consequences) is Ley VI, quoted verbatim in `counterfactual.py:22`; 014 (failed rules
become knowledge) is CEPS + `KNOWN_FALSE_POSITIVES.md`; 017 (tested against historical
failures) **is `counterfactual.py` exactly**. Adopting them as new law would renumber
existing enforcement, which is `rule proliferation` — the pathology the source's own
Macrosistema 17 names.

## Residue register — three candidates, all sub-dataset

**Rc1 — `enforcement_level` is absent from the rule schema. (Principal.)**
`schema.py:110-122` carries `severity` but no declaration of *where* a rule binds
(advisory / static / build-time / deploy-time / runtime). The source's HR-GOV-003 is
correct and unowned. Consequence today: `digest.py` cannot route by binding point, and
a documentation-grade rule is indistinguishable from a deploy blocker in the compiled
DB. **Scope: one field, one validator branch, one digest change, one V-gate.** Tens of
lines, on a module shipped and tested.

**Rc2 — the drift ontology has no registry.**
Seven+ detectors exist and each works. No artifact names the families they cover, so
coverage cannot be stated and a missing family is invisible — the exact shape of
`feedback_hand_curated_audit_measures_memory` and `PR-COVERAGE-BY-CONSTRUCTION-001`.
The correct form is a **discovered** registry (enumerate detectors from disk, map each
to a family) — never the source's 160-class hand list, which the source itself rejects.
**Scope: NEW_VIEW over existing owners.** One module, one report.

**Rc3 — governance cost is measured; governance *coverage* of enforcement is not.**
`effect_harness` measures 3 rule effects against 156 compiled rules; that is UCEIMR
**G3, shipped at HEAD**. Named here only so it is not re-proposed as EGCC F3.

## Premise that did not survive contact

The prompt directs **mandatory CrawlOS research before deriving rules**. Measured: there
is **no `modules/crawl_os`** in this repo. `vault/knowledge_base/crawl_os/` holds dataset
*contracts* and a resumption file — a chartered specification, not an executable research
runtime. The executable research surfaces here are `autoresearch/`, `deep-research/`,
`frontier_intelligence/question_harvester.py`, and the harness `WebSearch`/`WebFetch`
tools. The research step as literally specified cannot execute; an equivalent step can.
This is reported rather than silently substituted (`feedback_audit_disproves_owner_premise`).

Research was **not** run this session because Phase 0 is declared blocking by the prompt
and returned a blocking verdict. Spending a research budget to ground rules for datasets
that measure owned would invert the gate's purpose.

## Governance defect surfaced

`STOP_LEDGER.md` records **8 OPEN STOP #1 plans**, the oldest from 2026-07-26 (11 days).
UCEIMR flagged a fifth simultaneous open STOP as "a queue with no transition producer —
the same defect the estate diagnoses in its own subsystems". EGCC would be the **ninth**.
The transition producer now exists (`stop1_queue.py`, G1). What does not exist is a
decision. **Resolving the open eight should precede opening a ninth.**

## Base rate after this audit

Fourteen consecutive proposal sets measured majority-or-fully owned against a
**discovered** denominator: AISHF · RE Baseline · KSF · UKR · IIG A–AD · CCFL-PDPF ·
Emergence · USIRC A–M · CRPF/IGEF/E1–E5 · CPP-APIR · EFAIF · SEIP/USSC · UCEIMR ·
**EGCC**. One family (CLAE) has ever survived, admitted by a measured zero.

## Standing obligations honoured

- `PR-COVERAGE-BY-CONSTRUCTION-001` — denominator discovered from disk (78 modules, 26
  KB families, 69 vault domains), never curated from the proposal's assumptions.
- `T-OWNERSHIP-AUDIT-ABSORPTION-BIAS-001` — every REJECT reached by opening the
  incumbent. Four candidate zeros (enforcement level, drift registry, digital twin,
  jurisprudence) were each re-tested; two survived as residue, one was refuted, one
  was found shipped.
- `HR-NOVELTY-001` — fired on this prompt; answered against a discovered sweep.
- `feedback_reality_scan_before_corpus_build` — classification precedes construction.
- Contamination (CW Ops / ecommerce / brand vocabulary): the reference roots were **not
  read**; nothing from them enters this artifact.

## Blocking condition

No dataset content, no module, no directory, no continuity file is written until the
Owner selects an option. Continuity files (`EGCC_RESUMPTION.md` et al.) are deliberately
**not** created: scaffolding a multi-session build that measured 0/25 would be the
Scaffold Illusion (Mistake #16).
