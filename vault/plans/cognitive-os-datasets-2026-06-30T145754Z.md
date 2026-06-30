# ULTRA-PLAN — Cognitive Operating System (Dataset Family)

**Session:** CognitiveOS-Datasets-2026-06-30 · **Mode:** ULTRA-PLAN · **Status:** FASE -1 complete, **awaiting STOP #1 approval**.
Output of this prompt = **architectural datasets only** (no code/pseudocode/JSON/APIs).
Central metric: **verifiable work finished per unit of compute cost** (time+tokens+RAM+risk), NOT "tokens used".
Root law: **effective context ceiling 60%, never exceeded** — projective, not reactive.

---

## FASE -1 — COGNITIVE OS REALITY SCAN REPORT

Two Explore agents mapped the live repo. Anchors confirmed on disk (EXTEND parents, never duplicate):
`tools/token_ground_truth.py`, `modules/wrapper/{turn_counter,auto_resumer,repo_coordinator,cost_gate,prelaunch}.py`,
`modules/cpc_os/{context_monitor,auto_reset_orchestrator,ram_guard,snapshot,handoff,work_state_saver,router}.py`,
`modules/spec_gate/gate.py` (classify_tier), `modules/cost_collapse/router.py` (NANO/MICRO/MACRO/ULTRA),
`tools/jit_skill_loader.py`, `modules/session_resilience/*` (G1-G6), `modules/zero-crash/hooks/context-watchdog.py`
(60%/70% thresholds), `extension/src/restore_guard.js`, `tools/build_pane_map.ps1`.

### Consolidated verdict (35 proposed systems → reality)

| Proposed system | Reality | Parent (cite) | Verdict |
|---|---|---|---|
| 60% Context Ceiling enforcement | PARTIAL | context-watchdog.py (60% snapshot / 70% advisory) | **EXTEND→NEW root** |
| Context Kill Switch (projective block) | ABSENT (reactive only) | context_monitor.assess() advisory | **NEW** |
| Operating Economics (unified cost model) | PARTIAL (scattered) | token_ground_truth + cost_gate | **EXTEND** |
| Work-Units / M-Tokens metric | ABSENT | none | **NEW** |
| Token Economy / throughput-per-token | PARTIAL | token_ground_truth (cache_ratio) | **EXTEND** |
| Economics Governor (global budget) | PARTIAL (advisory) | cost_gate.weekly_burn (66M est) | **EXTEND** |
| Budget Violation Registry | ABSENT | none | **NEW** |
| Cost-Aware Planner / Compute Budget Gov | PARTIAL (reactive) | cost_gate | **EXTEND** |
| Dynamic Cognitive Router | PARTIAL (3 separate routers) | classify_tier + cost_collapse.route + cost_gate hint | **EXTEND** |
| Model Escalation Router | PARTIAL | same three | **EXTEND (fold into router)** |
| Zero Token Layer (never reason twice) | ABSENT | jit dedupe is TTL-only | **NEW** |
| Cognitive Cache / Asset Registry | PARTIAL | audit_cache, jit session-dedupe | **EXTEND** |
| Knowledge Vault Router | PARTIAL | vault/knowledge_base + jit triggers | **EXTEND** |
| Context Virtual Memory (Hot/Warm/Cold/External) | ABSENT | jit = proto Hot/Warm only | **NEW (EXTEND jit base)** |
| Cognitive Garbage Collector (eviction) | PARTIAL (reactive reset) | auto_reset_orchestrator | **EXTEND** |
| Session Hibernation (freeze/compress/restore) | PARTIAL (delta, uncompressed) | snapshot_versioning.py | **EXTEND (add compress)** |
| Session Dedup | EXISTS | restore_guard.js + build_pane_map | **COVERED** |
| Parallel Session Scheduler (HARD limit) | ABSENT | repo_coordinator W4 = advisory only | **NEW** |
| Parallel Swarm Optimizer | ABSENT | none | **NEW** |
| Loop Budget | ABSENT (/loop unbounded) | none | **NEW** |
| Subagent Economics | ABSENT | token_ground_truth excludes subagent logs | **NEW** |
| External Automation Control Plane | ABSENT | none | **NEW** |
| Cursor Extension Enforcement (limits) | PARTIAL | restore_guard.js (dedup cold-start) | **EXTEND (document)** |
| Wrapper Layer Enforcement (limits) | PARTIAL | prelaunch W1-W7 (1.6s, fail-open) | **EXTEND (document)** |
| Production Reality Gate link (work=verified) | EXISTS | done-gates / Reality Contract | **COVERED (reuse)** |

### The crux — honest guarantee level of the 60% ceiling

A **physical** kill switch that prevents the model from reasoning past 60% **does not exist and cannot exist inside Claude Code**. An in-process hook can snapshot, warn, and inject advisories, but it cannot pre-empt the model mid-turn. Honest classification of every enforcement surface:

| Layer | What it CAN guarantee | 60%-ceiling reach |
|---|---|---|
| Prompt-only | nothing enforceable; advisory text | aspiration |
| Claude Code hook (in-process) | snapshot, projective WARNING, additionalContext nudge, debounce | **detect + advise, NOT block** |
| Wrapper (kclaude prelaunch, out-of-process pre-launch) | refuse to LAUNCH a session/loop projected to breach; pre-allocate budget | **block at launch boundary only** |
| Cursor extension | UI visualization, dedup-on-cold-start | surface state, no compute veto |
| Host-limited (Windows/Cursor/Claude Code internals) | — | cannot be PP-guaranteed |

**Therefore the "absolute 60% ceiling, no override" is achievable as a LAYERED guarantee**: projective hook advisory (in-turn) + wrapper launch-refusal (between turns/loops) + Owner discipline — **not as a single physical switch**. CO-00 must state this honestly or the contract is theater (Reality Contract).

### Proposed dataset family (11 datasets) — `vault/knowledge_base/cognitive_os/`

| ID | Dataset | Answers | EXTEND/NEW |
|---|---|---|---|
| CO-00 | Hard Context Budget Contract (60% root law, projective, honest guarantee ladder) | Q1, Q8 | NEW root (EXTEND context-watchdog) |
| CO-01 | Operating Economics & Cognitive Capital (unified cost + Work-Units/M-Tokens, link Reality Gate) | Q2 | EXTEND token_ground_truth+cost_gate |
| CO-02 | Economics Governor & Budget Violation Registry (global enforcement + RCA on breach) | Q2 | EXTEND cost_gate W5 |
| CO-03 | Dynamic Cognitive Router (Vault→asset→deterministic→Haiku→Sonnet→Opus cascade) | Q3 | EXTEND classify_tier+cost_collapse |
| CO-04 | Context Virtual Memory (Hot/Warm/Cold/External tiers) | Q5 | EXTEND jit_skill_loader |
| CO-05 | Zero Token Layer & Cognitive Asset Registry (+ Vault Router + Cognitive Cache) | Q4 | EXTEND Knowledge Vault |
| CO-06 | Cognitive Garbage Collector (hygiene, LRU/TTL/aging eviction) | Q5 | EXTEND auto_reset_orchestrator |
| CO-07 | Session Hibernation & Dedup (freeze/serialize/compress/restore) | Q6 | EXTEND snapshot_versioning |
| CO-08 | Parallel Session Scheduler & Swarm Optimizer (HARD hot-session cap — burn root cause) | Q6 | EXTEND repo_coordinator W4 |
| CO-09 | Loop & Subagent Economics (loop budget + per-subagent budget/model/context/cancel) | Q7 | NEW |
| CO-10 | Enforcement Guarantee Ledger (External Automation Control Plane; Prompt→Host honesty) | Q8 | NEW cross-cutting |

- **NEW (6):** CO-00 root, CO-09, CO-10, plus the genuinely-absent metric/scheduler cores inside CO-01/CO-08.
- **EXTEND (existing parents):** CO-01, CO-02, CO-03, CO-04, CO-05, CO-06, CO-07, CO-08.
- **COVERED / reuse (no new dataset):** Session Dedup (restore_guard), Production Reality Gate (done-gates), Token visibility (SCS C53).
- **SKIP-LOW-ROI:** Context Futures Market, Cognitive ROI Scoring as standalone — folded as a *section* inside CO-01 (a separate market dataset is speculative until the unified cost ledger exists).

### SCS ledger (cognitive-economy relevant; sparse, agent-confirmed)
C48 wrapper(W5 cost), C50 no-dup-panes, C53 TCO visibility, C55/C56 Session-Resilience datasets+code, C57/C58 G6, C59 weekly-burn, C60 kickbacks. Next free = **C61** (this build's seal). No prior cognitive-economy kernel exists — this family is the systemic answer to the 48h/49.2M burn (SCS C59 was the point response).

---

## FASE 2-4 (post-approval) — see inline ULTRA-PLAN in the prompt

Q1-Q8 architecture → 11 datasets (≥2500 words/Part, no code) → COGNITIVE_OS_INDEX.md (dependency graph, EXTEND/NEW/COVERED table, CO-00 highlighted as root) → V-gates 10/10 ×3 hermetic → SCS C61 → push REMOTE_DELTA 0 0.

**STOP #1 is blocking: no dataset is written until the Owner approves this scope.**
