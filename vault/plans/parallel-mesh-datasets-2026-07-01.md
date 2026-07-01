# Parallel Cognitive Mesh — Dataset Family — REALITY SCAN REPORT

> Session: ParallelCognitiveMesh-Datasets-2026-07-01
> Root law: "Parallel allowed. Duplicate cognition forbidden."
> Status: **STOP #1 — awaiting Owner scope approval.** No dataset written yet.
> Backup of the in-chat Reality Scan Report.

## 0. Critical dependency — SATISFIED

`vault/knowledge_base/cognitive_os/` exists: CO-00…CO-10 + INDEX + SCS C62,
architecture sealed **SCS C61**, live code sealed **SCS C62** (commit `bd09d1e`,
`tools/test_cognitive_os_build.py` = 68/68 hermetic). Parent present → proceed.

## 1. PROMPT PREMISE CORRECTION (loud, per HR-PREMISE-001 / audit-disproves-premise)

The prompt's CO-number→name map is **transposed for three nodes**. Real mapping
(verified from the file tree + INDEX):

| Prompt claim | REALITY | Owner's intent by NAME |
|---|---|---|
| CO-03 = Zero Token Layer | CO-03 = **Dynamic Cognitive Router** | Zero Token Layer is **CO-05** |
| CO-04 = Dynamic Router | CO-04 = **Context Virtual Memory** | Dynamic Router is **CO-03** |
| CO-05 = Context Virtual Memory | CO-05 = **Zero Token Layer & Asset Registry** | Context VM is **CO-04** |
| CO-08 = parallel cap | CO-08 = **Parallel Session Scheduler & Swarm** ✓ | correct |
| CO-07 = Session Hibernation | CO-07 = **Session Hibernation & Dedup** ✓ | correct |
| CO-01 = Operating Economics | CO-01 = **Operating Economics & Cognitive Capital** ✓ | correct |
| CO-10 = Honest Guarantee | CO-10 = **Enforcement Guarantee Ledger** ✓ | correct |

Intent-by-name is fully coherent; only the CO-numbers 03/04/05 were swapped.
This report uses the **real** numbers throughout.

## 2. HEADLINE — the Parallel Mesh INVERTS a sealed live hard cap

The prompt's founding philosophy — *"N panes paralelos del mismo repo están
permitidos; lo prohibido es duplicar razonamiento"* — is in **direct conflict**
with CO-08's live, sealed, tested enforcement:

- `modules/cognitive_os/scheduler.py` enforces `SAME_REPO_CAP = 1` and
  `HOT_CAP = 2`, **with no bypass flag** (CO-08 III.4 / CO-00 II.4). A 2nd hot
  pane on the same repo is **REFUSED**, not warned. Wired live in `kclaude.ps1`
  (rung-3 block). Tested 68/68.
- `modules/wrapper/repo_coordinator.py` (W4): `coordinate()` warns to offer
  RESUME on a 2nd same-repo pane; `parallel_burn()` flags 2+ panes firing
  >8k-char prompts within 60min as "the 48h-burn pattern."

So CO-08 was built to **suppress** same-repo parallelism because it observed the
48h burn as *duplicated context re-derivation*. The Parallel Mesh does not delete
that concern — it **replaces the blunt cap with a precise one**: allow N panes,
forbid duplicate *cognition* (via Intent Declaration + Findings Bus + Redundancy
Tax). This is a **doctrine recalibration of CO-08**, not a mere extension.

**→ Owner decision required (Q-A below).** Do not touch `scheduler.py` semantics
until the Owner rules on relaxing `SAME_REPO_CAP` for mesh-coordinated panes.

## 3. EXTEND / NEW / COVERED — per proposed system (real parents)

| # | Proposed system | In CO-0N? | Verdict | Real parent(s) / reused primitive |
|---|---|---|---|---|
| 1 | Repo Shared Brain | partial (store only) | **NEW** | CO-04 Context Virtual Memory (Warm tier = store); no "brain doc" today |
| 2 | Pane Intent Declaration | no (PID≠scope) | **NEW** | CO-08 + `harness/intent_lock.js` (PID/worktree lock, not scope decl) |
| 3 | Collision Detector | partial (size/time) | **NEW** | CO-08 / `repo_coordinator.parallel_burn` (detects by SIZE+TIME, not declared SCOPE) |
| 4 | Parallel Budget Auction | partial | **NEW** (EXTEND) | CO-01 (WU/MTok) + CO-02 governor (downgrade) + CO-08 (cap). No ROI auction among panes today |
| 5 | Shared Findings Bus | partial (research only) | **NEW** | CO-05 Asset Registry (store); reuse file-drop+dedup-cache pattern from `autoresearch/cross_signal_bus.py` |
| 6 | Reasoning Dedup Engine | **mostly yes** | **EXTEND** (near-COVERED) | CO-05 Zero Token ("answer without a model?") + CO-07 "& Dedup". New only = also check Bus + Brain |
| 7 | Cross Project Learning Network | partial | **EXTEND** | `vault/knowledge_base/` (global) + `token-optimizer/cross_project_dedup.py` (rule dedup) + `cross_signal_bus` cross-kw + CEPS global-promotion |
| 8 | Cognitive Compiler | **mostly yes** | **EXTEND** (near-COVERED) | `one_shot/compiler.py` `compile_contract` + CO-03 route + `spec_gate.classify_tier` |
| 9 | Deterministic Replacement | partial | **EXTEND** (near-COVERED) | CO-03 cascade already has a **"deterministic" rung** (Vault→asset→deterministic→Haiku→…). New = tracking/promotion layer |
| 10 | Speculative Prefetch Engine | no | **NEW** | CO-04 (tiers) + CO-05 (assets). Honest: prediction-limited → HOOK/wrapper |
| 11 | Cognitive Portfolio Manager | **mostly yes** | **COVERED / thin-EXTEND** | CO-01 *is* "Operating Economics & Cognitive Capital"; ROI Scoring already folded into CO-01 (INDEX line 86) |

## 4. RECOMMENDED SCOPE

**Create as NEW datasets (5) — genuine gaps, zero CO duplication:**

- `PM-01 Repo Shared Brain` — parent CO-04. Live shared state per repo (briefing,
  decisions, files, risks, plans, findings, traps), generated once, consumed by all.
- `PM-02 Pane Intent Declaration & Collision Detector` — parent CO-08 +
  intent_lock. Declare scope/files/mode/cost/ROI/model before execute; detect
  scope overlap → fuse / split / demote-to-reviewer / reuse. **This is the
  mechanism that makes the CO-08 recalibration safe.**
- `PM-03 Shared Findings Bus (+ Redundancy Tax)` — parent CO-05. Publish findings
  hot; consume-before-reason gate (absorbs the Reasoning-Dedup mechanism #6 so it
  is not a duplicate dataset). Cross-Pane Commit Protocol on close.
- `PM-04 Parallel Budget Auction & Concurrency Modes` — parent CO-01/CO-02/CO-08.
  ROI-priority; Green/Yellow/Red/Black modes; Opus Singleton rule.
- `PM-05 Speculative Prefetch Engine` — parent CO-04/CO-05. Prepare cheap assets ahead.

**Do NOT create standalone (fold as EXTEND sections / cross-refs) — Owner may override:**

- #6 Reasoning Dedup → mechanism lives in PM-03 + references CO-05. No standalone dataset.
- #8 Cognitive Compiler → EXTEND CO-03 + one_shot; only worth a thin dataset if it
  ORCHESTRATES (objective→deps→assets→route→budget→plan) beyond `compile_contract`.
- #9 Deterministic Replacement → EXTEND CO-03 deterministic rung (tracking layer).
- #11 Cognitive Portfolio Manager → **COVERED by CO-01**; recommend a CO-01 section,
  not a new dataset. (Highest duplicate-cognition risk of the 11.)

**Borderline standalone (Owner call):**

- #7 Cross Project Learning Network → real primitives exist but scattered
  (dedup + xkw + CEPS + vault). A `PM-06` that unifies the *promotion protocol*
  (local→global elevation) is defensible as NEW-orchestration. Recommend include.

## 5. HONEST IPC CONTRACT (V-HONEST-IPC, inherited from CO-10)

Claude Code has **no IPC between instances**. Every mesh coordination surface is
**shared files on disk**, polled at pane boundaries (launch / turn-start / close):

- Repo Shared Brain = a versioned `.md`/`.json` in the repo, not shared memory.
- Findings Bus = append-only file drop + dedup cache (same shape as
  `cross_signal_bus`), read at turn-start — **not** a live event stream.
- Collision Detector = reads other panes' declared-intent files + transcripts
  (ground truth), same as `scheduler.gather_hot_sessions` — **not** a lock server.
- Every mesh mechanism classified on CO-10's ladder: Prompt-only / Hook / Wrapper
  / Cursor-ext / Host-limited. No promise of automatic pane-to-pane conversation.

## 6. OPEN DECISIONS FOR OWNER (STOP #1 gate)

- **Q-A (CO-08 recalibration):** relax `SAME_REPO_CAP=1` → allow N mesh-coordinated
  same-repo panes gated by PM-02 Intent/Collision instead of a blunt cap? (Y = the
  mesh is real; N = mesh is advisory-only over the existing hard cap.)
- **Q-B (scope):** 5 NEW only / 5 NEW + PM-06 Cross-Project / 5 NEW + all borderline
  as standalone datasets?
- **Q-C (V-DEPTH):** CO-family accepted 560–1070 words/Part (Owner-ruled deviation,
  2026-06-30) because full 2500/Part was itself the burn the kernel prevents. This
  prompt demands >2500 words/Part × ~6 datasets ≈ +45–60k words. Honor the literal
  2500/Part, or inherit the CO-family's accepted-deviation depth?
