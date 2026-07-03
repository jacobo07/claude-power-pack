# SCS C70 — Cognitive-Leak-Taxonomy-by-default

**Sealed:** 2026-07-03
**Type:** process doctrine + tooling (non-token cost axis)
**Slot check:** C67 = Hibernation, C68 = Token-Corpus (volume), C69 = taken ×2
(conversation-quality behavior + graphify Knowledge-Navigation-Kernel) → this is **C70**.
**Siblings:** `[[scs_c68_token_corpus_doctrine]]` (volume), `[[scs_c69_conversation_quality]]` (behavior).

---

## Doctrine

The PP has a **complete taxonomy of computational-cost leaks beyond tokens**.
C68 measures volume, C69 measures behavior — but the entire **non-token axis**
(RAM/CPU idle work, scheduled-task waste, latency, cross-pane coordination
effectiveness) was measured by **zero** tools. C70 opens that axis. The taxonomy
is **living**: re-audit quarterly with `conversation_quality_audit.py` +
`scheduled_task_health.py`; add a family when a new one appears.

Backing taxonomy (real data, ROI-ranked, quick-wins-first):
`vault/plans/cognitive-leak-taxonomy-2026-07-03.md`.

## What shipped (FASE 2, Owner-approved A+B+C, quick-wins first)

| # | Leak | Deliverable | Evidence |
|---|---|---|---|
| **A** | **L-SCHED** — failing/idle scheduled tasks | `tools/scheduled_task_health.py` (pure `classify_task` + live `scan_live`) + `vault_summarize.py` cwd-repair | live: 13 tasks → 5 FAILING, 5 HIGH_FREQ; repair verified from arbitrary cwd |
| **B** | **P5 / PM-03** — measure before build | `conversation_quality_audit.pm03_health()` | **bus dir absent → 0 findings ever published**; PM-03 built-but-inert → P5 fix = WIRE PM-03, not a new gate |
| **C** | **L-SELFCORR** — self-correction redo (C69 P1, 370k tok) | `modules/wrapper/verify_before_emit.py` (pre-emission advisory) | fires on claim-without-evidence; silent on evidence/negation/no-claim |

**Deferred (gated on measured freq ≥ 5, second wave):** H1 latency, H3 subagent-
output-unused, H4 tool-call-dup, H5 abandoned-plans, H6 informal rediscovery,
H7 recovery re-work; plus L-REREAD / L-CTXINFLATE (the latter quality-risky).

**Surfaced, not built (Owner-side, HR-001):** L-XPANE first-load trim (the
17–26-concurrent-pane multiplier makes the drafted Proposal A/B compounding);
PM-03 wiring (SessionStart digest + Stop publish).

## Reality-contract highlights

- **Verify-before-destructive paid off:** the 5 "failing" tasks fail for 5
  *different* reasons (convention-nonzero `--check`, no-args misconfig, missing
  input, long-running, superseded). Blanket disable would have been a bug.
- **Measure-before-build paid off:** B proved PM-03 is inert, so P5's fix is
  wiring, not a new gate — saved building the wrong thing.
- **Self-caught FP:** the live detector first flagged a *weekly* task STALE;
  raised the no-interval absolute threshold to 8 days → FP gone, re-verified.

## Verification

`tools/test_cognitive_leak_taxonomy.py` — 5 V-gates
(V-TAXONOMY-COMPLETE, V-ROI-RANKED, V-FIXES-MEASURED, V-NO-REGRESSION,
V-EXTENDS-NOT-DUPLICATES), hermetic, **7/7 ×3**. V-NO-REGRESSION runs the C68 +
C69 suites in-process (both exit 0). Fixes **extend** the existing tools — no
parallel `.jsonl` reader (`scheduled_task_health` reads schtasks; `pm03_health`
lives inside `conversation_quality_audit`).

## Cross-references
- Taxonomy + ROI: `vault/plans/cognitive-leak-taxonomy-2026-07-03.md`
- UKDL: `ukdl-universal.md` — T-SCHEDULED-TASK-LEAK-001, T-VERIFY-BEFORE-EMIT-001,
  T-PM03-INERT-001, T-XPANE-FIRSTLOAD-LEAK-001
- Siblings: `[[scs_c68_token_corpus_doctrine]]`, `[[scs_c69_conversation_quality]]`
