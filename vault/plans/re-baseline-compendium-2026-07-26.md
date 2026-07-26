---
title: Claude Power Pack RE Baseline — Compendium Dataset Build
date: 2026-07-26
status: STOP-1 (Phase 0 complete; awaiting Owner approval of the revised architecture)
phases_complete: [-2, -1, 0]
corpus_sha256_zip: CFBDAB0C48709730551DC0C979A6089B5430C1D4B9A9088AA1596654B88321C4
---

# RE Baseline Compendium — Source Map, Evidence Ledger, Overlap Audit, Revised Plan

This file is the institutional backup of the inline plan delivered to the Owner.
Nothing in Phase 1+ begins until the Owner approves.

---

## PHASE -2 — Source Reality Map (COMPLETE)

| Source | Status | Evidence |
|---|---|---|
| `Downloads\Datasets Claude Power Pack RE Baseline.zip` | FOUND | 115,893 B, SHA256 `CFBDAB0C…21C4`, mtime 2026-07-26 12:24 |
| ZIP entries | 10 (1 dir + 9 txt) | Enumerated via `System.IO.Compression`; extraction complete, zero residue |
| Controlled extraction dir | scratchpad `corpus_extract\` | Fresh extract, not the pre-existing Downloads folder |
| The 9 "session attachments" | NOT attached to this session | They exist on disk; 7 are byte-identical loose copies in `Downloads\`, 2 (Ghidra 6, HY-WorldPlay 5) exist ONLY inside the archive |
| Quality references | `Downloads\! Promptsss\` (bang + space) | Distinct from the working dir `Downloads\Promptsss\`; both exist |

**Authoritative source = the ZIP**, not the loose files. Anyone reading only `Downloads\*.txt`
silently loses 2 of 9 pillars. Recorded as a corpus trap.

## PHASE -2 — Evidence Ledger (per-file, all read to EOF)

| # | Pillar | Bytes | Lines | Words | SHA256[:12] | Read | Integrity |
|---|---|---|---|---|---|---|---|
| 1 | FounderOS | 43,935 | 1,317 | 5,360 | DB8BC4DD35BD | EOF | clean |
| 2 | OpenMontage | 48,158 | 1,519 | 5,833 | 3229A49D6028 | EOF | clean |
| 3 | Colibrì | 48,907 | 1,554 | 6,018 | 7CD0237F2064 | EOF | clean |
| 4 | OSA Claude Code | 28,532 | 869 | 3,631 | FFBEF782E8BA | EOF | clean |
| 5 | HY-WorldPlay | 24,695 | 527 | 3,140 | C193CB165F8E | EOF | clean |
| 6 | Ghidra | 26,861 | 756 | 3,341 | BBAEBC94E95E | EOF | clean |
| 7 | Claude Institution | 25,599 | 656 | 3,230 | 336781C658FC | EOF | clean |
| 8 | Fable Succession | 29,634 | 857 | 3,739 | C395CAAB590B | EOF | clean |
| 9 | Fable World Demo / LAAS | 30,282 | 912 | 3,860 | 15F640431B5E | EOF | clean |
| | **TOTAL** | **306,603** | **8,969** | **38,152** | | 9/9 | 0 corrupt / 0 truncated / 0 empty |

## PHASE -1 — Corpus Map (COMPLETE)

Structural finding: files 1–3 carry an identical ~1,970-line meta-prompt preamble
(the RE doctrine: evidence discipline, Duplicate-to-Advantage verbs, Reality Contract,
21-section output structure). Files 4–9 carry **no preamble** — URL + analysis only.
Unique analytic content ≈ 24,000 words across nine "Resource Rounds" (R-001…R-009).

The corpus is **not a specification**. It is a nine-round reverse-engineering *journal*
that repeatedly and explicitly states it cannot see this workspace:

> "Las afirmaciones sobre tu workspace local y solapamientos exactos con Claude Power Pack
> siguen pendientes de un Reality Scan ejecutado dentro de Claude Code." (R-002 §10)

Every Duplicate-to-Advantage verdict in all nine rounds is therefore **provisional by the
corpus's own admission**. Phase 0 below is the Reality Scan the corpus asked for and could
not perform. Its findings supersede the corpus's provisional verdicts wherever they conflict.

**The nine pillars and the question each answers:**

| R | Pillar | Question it answers |
|---|---|---|
| 001 | FounderOS | Where does the operator observe and control? |
| 002 | OpenMontage | How is a mission declared and materialized? |
| 003 | Colibrì | Where does each cognitive resource reside, and how is it loaded? |
| 004 | OSA Claude Code | Who owns, supervises and recovers each live process? |
| 005 | HY-WorldPlay | How is coherence preserved across long horizons? |
| 006 | Ghidra | How does opaque heterogeneous reality become common semantics? |
| 007 | Claude Institution | What institutional force does a discovered rule deserve? |
| 008 | Fable Succession | How is frontier capability externalized before it is lost? |
| 009 | LAAS | How does an agent close its own loop against an external bar? |

---

## PHASE 0 — Overlap Audit (COMPLETE) — the corpus underestimated PP by an order of magnitude

**Measured PP surface:** 71 modules · 24 knowledge-base dataset families (~11 MB) ·
62 slash commands · 38 hooks · 322 tools · 1,101 graph coordinates (+448 cross-repo).

The corpus's provisional maps assumed a PP with roughly a dozen systems. The real stack
already owns most of what the corpus proposes to build, frequently at greater maturity
than the source repositories being reverse-engineered.

### Verified ownership (evidence-cited, not name-matched)

| Corpus mechanism | PP owner | Evidence | D2A |
|---|---|---|---|
| Rule Placement Compiler (R-007's headline) | `modules/rule_compiler/` | `schema.py` = admission gate; recognises FIELDED + IMPERATIVE forms; `digest.py` compiles the digest the global 4-trigger router reads | **REUSE — DO NOT BUILD** |
| Canonical state outside conversation (R-002) | `modules/done_gate/artifact_done_gate.py` | "done is an artifact on disk, not an exit code"; contract names artifact + shape, gate looks | **REUSE + EXTEND** |
| Context-conditioned capability transfer (R-005) | `modules/fable_distillation/fd_04_contrast.py` + `fd_04_prover.py` | teacher/student contrast is the live producer of `portability_proven` | **REUSE + EXTEND** |
| Closed institutional writeback loop (R-008/009) | `modules/fable_distillation/fd_07_flywheel.py` | Stop-chain child; classifies NEW/STRONGER/DUP/DISCARD; idempotent writeback; reports through CO-12 | **REUSE** |
| UI-is-a-runtime-projection, generalized (R-001) | `modules/liveness/reachability.py` | Discovery producer: coverage total BY CONSTRUCTION, not by hand-declared registry | **REUSE + EXTEND** |
| Undeclared side-effect detection (R-002/004) | `modules/contract_fabric/side_effect_ledger.py` | `UNDECLARED = OBSERVED − DECLARED`, DEFAULT-RECORD discipline | **REUSE** |
| Analyst correction loop (R-006) | `modules/decision_review/proactive_scanner.py` | Proposes with cited real-path evidence; never auto-applies | **EXTEND** |
| Intelligence egress gateway (R-004) | `modules/secret_firewall/redactor.py` (URB) | HR-SECRET-002/006 route every emission through redaction | **REUSE** |
| Just-in-time skill loading (R-002/003) | `tools/jit_skill_loader.py` + latent 80-token cards | Live on UserPromptSubmit, 40 KB-bounded, fail-open | **REUSE — DO NOT BUILD** |
| Semantic IR / evidence overlay (R-006) | `modules/graphify/` + `d2a_fabric` + `crawl_os` | 1,101 coordinates already indexed for this repo | **EXTEND — DO NOT BUILD a second graph** |
| Minimum-sufficient agent topology (R-001/007) | Windows batch caps + `parallel_mesh` | Empirically sealed caps (Agent solo; reads ≤4) | **GENERALIZE** |
| Epistemic ladder / self-certification cap (R-007/008) | `modules/fable_distillation/epistemic_ladder.py` | ACIS E0–E7; derived level caps at E3 | **REUSE** |
| Quality scored by criterion, not opinion (R-009, one vertical) | `agents/cdio-reviewer` + `modules/cdio/scorer` | Deterministic 0–100; APPROVE needs ≥80 AND zero critical | **GENERALIZE — this is the seed of the biggest gap** |

### Genuine gaps (grep-verified absence, not assumed)

A repo-wide case-insensitive search for the LAAS mechanism vocabulary
(`reference-delta`, `quality distance`, `anti-underbuild`, `human oracle`,
`observability-capable`, `phase zero`, `deviation ledger`) returned **zero files**.

| Gap | Why it is real | Nearest existing owner (to extend, not duplicate) |
|---|---|---|
| **G1 — Reference-delta engineering** | PP measures against internal gates only. It has no mechanism to place an artifact beside an external canonical reference, rank the deltas by impact, fix the top-k, and re-measure. | `cdio` proves it works for design; `sleepless_qa`, `uqf`, `sqi` are internal-bar instruments |
| **G2 — Quality distance accounting** | Every PP gate is binary (PASS/FAIL, APPROVE/BLOCK). None reports *residual distance* after a pass. "Done" erases the remaining gap. | `sqi` (exits ≠0 on silent decrease) is the closest; it measures direction, not distance |
| **G3 — Anti-underbuild floors** | The scaffold auditor catches stub *tokens*. Nothing catches a feature that is genuinely implemented but nominally shallow. | `output_contracts` OQS ≥70, `done_gate` |
| **G4 — Human oracle boundary** | No mechanism declares which properties the stack *cannot* self-verify and must route to the Owner. Silence currently reads as verified. | `owner_queue` exists as a queue; it has no admission criterion |
| **G5 — Observability-capable Phase Zero** | `/ultra` Phase 1 plans the feature. No phase proves the project can boot, observe, measure, reproduce and fail legibly *first*. | `/ultra` 7-phase, `sleepless_qa` |
| **G6 — Cognitive residency physics** | `executionos-lite` tiers the *task* (LIGHT→FORENSIC). Nothing tiers the *assets* by heat, or governs promotion/demotion/prefetch. | `memory-engine` hot/cold, `graphify` route compiler context pack, `daif_08_context_runtime` |
| **G7 — Governance regression harness** | 156 hard rules, and no harness that answers "did this rule change break normal tasks / raise false positives / raise token cost?" | `rule_compiler` validates form; nothing validates *effect* |
| **G8 — Source-vs-deployed drift detection** | Known recurring defect (canonical `hooks/` vs live `~/.claude/hooks/` split-brain) with no owning mechanism. Recorded in memory as recurring; still unowned. | `modules/liveness`, `hooks/` dispatcher |
| **G9 — Rule retirement engine** | Hard rules carry a retirement condition field. No process ever evaluates it. 156 rules only ever grows. | `hard_rules/residual.py` |
| **G10 — Execution-based succession proof** | FD proves *portability of judgment*. It does not make the student *execute* real tasks and measure negative transfer. This is the corpus's sharpest correct critique. | `fable_distillation` FD-00…07 |

### Wiring-gap register (built ≠ reached)

| Item | State | Source of claim |
|---|---|---|
| `session_resilience/acceptance.py` (recovery ACCEPTANCE arbiter) | Documented as having sat unwired and unreported | `modules/liveness/reachability.py` docstring |
| `SKILLBANK.md` | **STALE** — documents 12 commands / 14 modules / 14 tools against a measured 62 / 71 / 322 | This audit |
| `vault/knowledge_base/INDEX.md` | **STALE** — "latest entry 2026-04-24", 57 lessons; families sealed months later are absent | This audit |
| `ukdl_queue.py` `status` field | Field exists with no transition producer | Recorded prior finding |

`SKILLBANK.md` and the KB `INDEX.md` fail the same test `reachability.py` was written to
fix: both are **hand-curated indexes of what someone remembered**, so a surface nobody
enrolled is not scored missing — it is absent from the denominator, and absence reads as
health. Same defect class, different artifact. Both need discovery producers.

---

## STOP #1 — the requested A–J architecture would be ~60 % duplication

The prompt specifies ten dataset families (A–J), each Part I–XXV minimum, and explicitly
permits Claude Code to "rename, split, merge, convert into subfamilies". Phase 0 says it
must. Building families B, D, F, G, H as specified would re-author, under new names,
material that `contract_fabric`, `done_gate`, `session_resilience`, `daemon`, `zero-crash`,
`graphify`, `crawl_os`, `d2a_fabric`, `rule_compiler`, `hard_rules` and `fable_distillation`
already own — the precise failure the corpus's own doctrine forbids:

> "Changing the name of an existing capability does not make it new."

Approximate mechanism accounting across the nine rounds: **~55–60 % already owned at equal
or greater maturity · ~25 % partial (EXTEND) · ~15 % genuine gaps.**

## Revised architecture (proposed — 3 NEW families, 5 EXTEND passes, 1 integration spine)

**NEW families (each maps to a grep-verified gap, none duplicates an existing owner):**

- **CLAE — Closed-Loop Autonomous Engineering Laboratory** (G1–G5, Pillar I + the honest
  half of Pillar A). Reference-delta engineering, quality-distance accounting, anti-underbuild
  floors, human-oracle boundary, observability-capable Phase Zero, deviation governance,
  evidence-gated autonomy, autonomous toolsmith, incident-to-probe conversion. Generalizes
  the CDIO scorer out of design into every domain. Highest ROI in the set.
- **CRPF — Cognitive Residency & Pressure Fabric** (G6, Pillar C). Asset tiering, cognitive
  heat, predictive prefetch with harmless failure, honest admission control, warm-state vs
  canonical-state separation, semantic preservation under pressure, stable-ID doctor contract.
- **IGEF — Institutional Governance Evolution Fabric** (G7–G9, Pillar G gaps only —
  explicitly NOT the placement compiler, which `rule_compiler` owns). Governance regression
  harness, source-vs-deployed drift detection, rule retirement engine, risk-weighted
  (not count-weighted) lesson promotion.

**EXTEND passes — Parts appended to existing sealed families, no new family created:**

| Pass | Target family | Adds |
|---|---|---|
| E1 | `fable_distillation` | G10: student execution trials, negative-transfer eval, model succession registry, retirement eligibility |
| E2 | `session_resilience` + `session-continuity` | Reconstituted operational context, remote-anchor registry, bounded-horizon execution, drift measured at every handoff |
| E3 | `graphify` + `d2a_fabric` + `crawl_os` | Resource-adapter conformance, evidence-overlay layering, confidence propagation, dependent-conclusion invalidation |
| E4 | `contract_fabric` + `one_shot` + `karimo-harness` | Unified mission manifest, artifact contracts between stages, append-only decision genealogy with supersession |
| E5 | `daemon` + `zero-crash` + `session_resilience` | Semantic recovery contract (supervision ≠ recovery); **wire the unwired acceptance arbiter** |

**REFERENCE ONLY (documented, never built):** FounderOS UI/dashboard surface and connector
honesty (PP has no frontend and no connectors), Ghidra decompiler, HY-WorldPlay visual world
model, Colibrì MoE inference runtime, OSA's reverse-engineered signing.

**Transversal:** integration spine (the 21-stage cycle), UKDL three-level registration,
eval + benchmark suite, contamination gate, seal report.

## Scope reality (stated before approval, not discovered during)

Three new families at PP dataset depth (existing comparables: SQI 714 KB, CPP-IAS 3.4 MB,
D2A 1.8 MB) plus five extend passes is on the order of **90–110 Parts**. This is a
multi-session build. `RE_BASELINE_RESUMPTION.md` + `MISSION_STATE.md` + `DECISION_LOG.md` +
`OPEN_QUESTIONS.md` + `NEXT_ACTION.md` are created in Phase 1 and updated after **every**
sealed Part, per the session-continuity governance already binding on this repo.

## Contamination control

CommonWealth Ops, ecommerce, marketing, growth, commerce, merchant and profit-system
vocabulary is barred from every dataset artifact. The CW reference corpus is consulted for
depth calibration only and is named only in this planning file. A textual + semantic gate
runs before each family is sealed and again in Phase 6.

## Micro-commit boundaries

1. corpus inventory + evidence ledger + overlap audit (this file) ← **current**
2. compendium charter + approved architecture
3. one commit per sealed Part
4. one commit per registry / integration pass / eval suite
5. review fixes · final verification · institutional writeback

## Decision required from the Owner

Approve the revised 3-NEW + 5-EXTEND architecture, or direct the literal A–J ten-family
build despite the measured duplication.
