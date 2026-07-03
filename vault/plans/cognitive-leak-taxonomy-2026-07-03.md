# Cognitive Cost Leak Taxonomy — Full Ecosystem Audit

**Session:** CognitiveLeakTaxonomy-2026-07-03
**Mode:** ULTRA-PLAN · FASE -1 (Reality Scan) → STOP #1
**Scope:** all computational-cost leaks of the PP + kClaude + Claude Code + Cursor + Windows stack — **not only tokens**.
**Reality contract:** every MAJOR leak carries real data (frequency + cost); families without data are labelled HYPOTHESIS with a verification method, never a fabricated ROI.

---

## 0. Observability gap map (what NO current tool can see)

| Tool | Measures | Blind to |
|---|---|---|
| `token_ground_truth.py` | per-session/window in·out·cache aggregates, cache ratio, high-consumers | all content behavior, tool calls, wall-time, OS processes |
| `cost_gate.py` (W5) | daily/weekly burn thresholds, compaction hint, model-tier hint | same; consumes ground-truth only, adds no new signal |
| `token_corpus_audit.py` (C68) | VOLUME: first-load, output dist, cache/repo, re-reads, hour-concurrency, ctx→output | behavior, RAM/CPU, latency, cross-pane coordination |
| `conversation_quality_audit.py` (C69) | BEHAVIOR: self-correct, owner-repeat, plan-divergence, repeated-Q, dup-scan | RAM/CPU, scheduled-task waste, latency, tool-dup, unused output |

**The entire non-token axis** — RAM/CPU idle work, scheduled-task waste, latency/Owner-wait, cross-pane coordination effectiveness — is measured by **zero** tools. That is the primary observability gap this taxonomy opens.

Baseline (refreshed 2026-07-03, 635 sessions): out=527M lifetime, **cacheR 96.3%**, **A3 low-cache outliers = 0**. Input side is saturated; cache is not a lever. Confirmed C68.

---

## 1. MEASURED leak families (real data)

### L-SCHED — Failing / unconditional scheduled tasks  *(NEW axis, previously invisible)*
- **Evidence (Windows probe 2026-07-03):** 13 PP scheduled tasks. **4 fail on every run** — `PP-Miner-V2` (result=2 FILE_NOT_FOUND), `PP-Normalize-Paths` (result=1), `PP-Sovereign-Miner` (result=1), `PP-Vault-Summarize` (result=2); `ClaudePP-SessionSnapshot` stale+erroring since 2026-06-25. Several fire **every ~5 min unconditionally** (`PP-Hibernation`, `KobiiNetworkHealthDaemonV2`, `ClaudeRAM-WSTrim`), plus `PP-Playwright-MCP-Watchdog` q8min, `pp-snapshot-writer` q15min, `PP-KickbacksGuard` q2min — regardless of whether any session is active.
- **Cost:** process spawn + Python/Node import cost, ~daily for the failing set, ~288×/day for the q5min set. No token cost; pure CPU/scheduler + host-RAM pressure (37 node procs / 231 MB co-resident now; reaper culling continuously).
- **PP system that should prevent it:** none — hibernation reaps *orphans*, not *failing scheduled work*.
- **Gap:** total. **Fix-ability: trivial** (repair or disable 4 tasks; gate q5min tasks on "session active").

### L-XPANE — Cross-pane first-load multiplication
- **Evidence:** A1 first-load mean **57,088 tok/session**; A5 peak hours run **17–26 concurrent sessions** (2026-07-02 21:00 = 25; 2026-07-01 17:00 = 26). Each pane cache-*creates* its own ~57k CLAUDE.md/skills prefix (Anthropic cache is per-conversation-prefix, not shared cross-pane).
- **Cost:** ~26 × 57k ≈ **1.48M cache-creation tokens co-resident at peak**, most of it byte-identical across panes. Compounds the prior sprint's first-load trim (Proposal A ~1,547 tok, Proposal B JIT relevance-gate ~3,349 tok) by the concurrency factor.
- **PP system:** JIT loader + CLAUDE.md firewall exist; neither accounts for the cross-pane multiplier.
- **Gap:** partial (per-session first-load measured; multiplier not). **Fix-ability: medium** (fix already drafted — propose-only per HR-001).

### L-SELFCORR — Agent self-correction (C69 P1)
- **Evidence:** 71 occurrences, **370,081 output tokens** — corpus's single largest behavioral cost.
- **Fix:** verify-before-emit gate (behavioral, wrapper-level; no new system). Prompt-flagged as highest ROI without a new system. **Fix-ability: medium.**

### L-REREAD — In-session file re-reads (C68 A4)
- **Evidence:** 190/635 sessions re-read a file ≥3×; **5,551 redundant re-reads** total.
- **Cost:** cache-side (low token $) but live-window churn + latency. **Fix-ability: medium** (per-session read-memo).

### L-CTXINFLATE — Context→output inflation (C68 A6)
- **Evidence:** mean output 865 (<60k ctx) → 1,847 (60–120k) → **2,335 (>120k), 2.7×**.
- **Ambiguity:** partly legitimate (harder work lands later in a session) vs partly leak (verbosity rises with a full window). **Requires care — quality risk.** Fix-ability: low.

### L-OWNERREPEAT — Owner re-sends unresolved instruction (C69 P2)
- **Evidence:** 19 occurrences, **74,530 tokens**, concentrated in error-retry sessions.
- **Fix:** "act, don't acknowledge" — next turn must carry the executing tool_use. **Fix-ability: medium.**

### L-REPEATQ — Agent re-asks answered question (C69 P5)
- **Evidence:** 33 occurrences, **90,349 tokens**.
- **Fix:** consult Findings Bus (PM-03) before asking — **but PM-03 effectiveness is unverified (see H2).** Fix-ability: medium, gated on H2.

### L-PLANDIV — Plan↔exec divergence (C69 P4)
- **Evidence:** 44 occurrences, **249,170 tokens** — but **UPPER BOUND** ("planned" includes read-context files); manual-review only, LOW confidence. **Not an auto-fix target.**

---

## 2. HYPOTHESIS families (no data yet — verification method given, no fabricated ROI)

| ID | Leak | Verification method (FASE 2 detector) |
|---|---|---|
| **H1** | Latency / Owner wait-time | per-turn `timestamp` deltas from `.jsonl`; flag turns whose wall-time ≫ output size |
| **H2** | PM-03 Findings-Bus effectiveness vs P5 | cross-ref P5 sessions against presence of `pm_03_bus` findings — does P5 drop where the bus has entries? |
| **H3** | Subagent output unused | match `Agent` dispatch → whether its result is referenced in later turns |
| **H4** | Tool-call duplication (beyond file re-reads) | hash `tool_use.input` per session; count repeated identical bash/grep |
| **H5** | Abandoned plans (posted, never executed) | plan-cue turn with **no** subsequent `Write` in the session |
| **H6** | Informal knowledge rediscovery | cross-session semantic near-dup of findings (extends C69 P3, which found 0 *formal* scans) |
| **H7** | Snapshot/recovery re-work | G4 PARTIAL/FAILED receipts × subsequent redo turns |

---

## 3. ROI ranking (frequency × cost × fix-ability)

### QUICK WINS — high impact, small fix, zero quality risk
1. **L-SCHED** — repair/disable 4 failing tasks + gate q5min tasks on session-active. Trivial fix, daily recurring waste, **no quality risk, no token risk**. → build the detector as a Windows-side extension + one-shot repair.
2. **L-XPANE** — first-load trim already drafted (Proposal A+B); A5 concurrency multiplies its value. Owner-side install (HR-001). → no new build; surface the multiplier + hand off.
3. **L-SELFCORR (P1)** — verify-before-emit gate. 370k tokens, behavioral, no new system. Highest token ROI.

### STRATEGIC INVESTMENTS — high cost, complex fix
4. **H2 → L-REPEATQ (P5)** — first VERIFY PM-03 is actually consulted; if unwired, wiring it resolves 90k tokens. Measure before build.
5. **L-OWNERREPEAT (P2)** — "act-don't-acknowledge" wrapper heuristic. 74k tokens.
6. **L-REREAD / L-CTXINFLATE** — read-memo + verbosity-under-pressure. Medium complexity, **quality risk on L-CTXINFLATE — handle last, carefully.**
7. **H1/H3/H4/H5** — new detectors; build only the ones whose measured frequency ≥ threshold (reality contract), extending C68/C69, not parallel infra.

### NOT WORTH / ALREADY COVERED — do not build
- **Cache ratio** — 96.3%, 0 outliers. No lever (C68).
- **Context re-load as a *token* leak** — cached at 96.3%, near-zero marginal token cost. It is a latency/compute cost only, folded into H1; not a token leak.
- **Output fat tail (A2, top-10% = 40.9%)** — dense unique reasoning, not reducible without quality loss (C68 verdict).
- **P4 auto-fix** — LOW-confidence upper bound; manual review only.
- **P3 formal dup-scan** — 0 occurrences.

---

## 4. Scope proposal for FASE 2 (pending Owner approval at STOP #1)

**Recommended build set (quick wins first, extend existing tools, no parallel .jsonl reader):**
- A) **L-SCHED detector + repair** — new Windows-side probe (schtasks health) + one-shot repair of the 4 failing tasks + session-active gate for q5min tasks. *Highest fix-ability, zero risk.*
- B) **H2 measurement** — PM-03-vs-P5 correlation, a read-only extension of `conversation_quality_audit.py`. Decides whether P5's fix is "wire PM-03" or "new gate". *Measure before build.*
- C) **L-SELFCORR** — verify-before-emit heuristic in the wrapper (behavioral). *Largest token ROI, no new system.*
- (defer H1/H3/H4/H5 detectors + L-REREAD/L-CTXINFLATE to a second wave, each gated on measured freq ≥ 5.)

**Constraints honored:** only detectors for gaps NOT covered by C68/C69; quick wins first; real data for every major leak; EXTEND `token_corpus_audit.py` / `conversation_quality_audit.py`, no parallel reader; CLAUDE.md + JIT threshold are propose-only (HR-001); no `git add -A`.

**Seal target on completion:** SCS **C70** (C67 Hibernation, C68 Token-Corpus, C69 taken ×2 → C70).

---

## FASE 2 — RESULTS (Owner-approved A+B+C, quick-wins first) — sealed 2026-07-03

### A) L-SCHED — detector + repair ✅
- **`tools/scheduled_task_health.py`** — pure `classify_task` (hermetic) + Windows `scan_live`. Live result: **13 tasks → {FAILING:5, HIGH_FREQ:5, OK:3}**. Verdicts carry non-destructive recommendations; the tool NEVER auto-mutates a task (verify-before-destructive: the 5 failures had 5 different root causes — a `--check` exits nonzero by convention, a task was misconfigured with no args, one had a missing input, two are long-running/superseded — blanket disable would have been a bug).
- **Repair shipped:** `vault_summarize.py` now finds the repo's `errors.md` via a script-relative PP-root fallback → verified working from `C:\Windows\Temp` (was hard exit-2 daily). Remaining host-side task-config fixes (miner_v2 no-args, session-snapshot supersession) are **surfaced as recommendations**, not blind-executed.
- **Self-caught FP:** first live run flagged a *weekly* task STALE (no sub-day interval → hit the 3-day absolute); raised the no-interval threshold to 8 days → FP gone, re-verified (STALE 0, OK 3).

### B) P5 / PM-03 — measure before build ✅
- **`conversation_quality_audit.pm03_health()`** added (extends the existing tool). **Measured: the PM-03 bus state dir does not exist → 0 findings ever published across all repos.** PM-03 is fully built but its wiring (SessionStart digest + Stop publish, Owner-side/HR-001) was never installed → the dedup mechanism is inert → **P5 (90k tok) persists.**
- **Verdict:** P5's fix is to **WIRE PM-03**, not build a new gate. The measurement saved building the wrong thing, and is now re-checked on every audit run.

### C) L-SELFCORR — verify-before-emit ✅
- **`modules/wrapper/verify_before_emit.py`** — pre-emission advisory (complement of HR-OUTPUT-002). Fires when a draft asserts completion with no verification signal in the draft or the evidence stream; silent on evidence/negation/no-claim. Fail-open. Wiring Owner-side (HR-001, documented). Targets the C69 P1 leak (370k tok).

### Done-gate
- `tools/test_cognitive_leak_taxonomy.py` — 5 V-gates, hermetic, **7/7 ×3**. V-NO-REGRESSION runs C68 + C69 suites in-process (both exit 0). V-EXTENDS-NOT-DUPLICATES confirms no parallel `.jsonl` reader.
- Sealed **SCS C70** + 4 UKDL entries. Deferred families (H1/H3/H4/H5, L-REREAD, L-CTXINFLATE) gated on measured freq ≥ 5 for a second wave; L-XPANE + PM-03 wiring surfaced Owner-side.
