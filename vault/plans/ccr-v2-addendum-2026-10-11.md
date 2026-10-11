---
covers: [ccr-v2-addendum, utvm, semantic-cse, context-metrics, ucre, ccr-writer-ownership]
status: AWAITING_OWNER
goal: ccr
amends: vault/plans/ccr-v2-enforcement-2026-10-11.md (97bf6803) — that plan stays canonical
---
# CCR v2 — addendum (2026-10-11 22:20)

A second Owner prompt asked for this programme's master plan again. This file does NOT replace v2. It records
the reality delta since 97bf6803 and the gaps between v2 and the second prompt.

## 1. Reality delta since 97bf6803 (verified 22:17–22:22)
| Fact | Evidence |
|---|---|
| Another writer is executing v2 now: uncommitted `unit` tier in `mods/cpp-cognitive-runtime/hooks/{policy,register,policy.test}.ts` (+164/−11, mtimes 22:05–22:09) | `git diff --stat -- mods/cpp-cognitive-runtime` |
| Goal ccr: cap 36.88M, used 5.17M (was 4.15M in v2 §0), **open lease 1.03M** → a bound session is spending | `mission_spend.py goal-status --goal ccr` |
| Active release still 0.1.0-feaae8b0; no v2 release cut | `ccr_release.py status` |
| Madzia worker pid 17144 (21:53) still live → R4 must wait for a driver boundary | process list |
| Mods 2.1.296: `tool.list` exists only as an op (d.ts L6955/L7241), never as an event → **tool removal NOT_SUPPORTED** confirmed; `tool.describe` `isDeferred` "moves the tool behind ToolSearch" (L4219-4231), core built-ins still UNKNOWN (P1) | `bundled-skills/2.1.296/.../claude-code.d.ts` |
| v2 §0 "CCR paths clean" is now false | above |

## 2. Review note for the active writer (not applied; their files)
`WORK_CLASSES['bounded-code-worker'].tools` = the boundary.py `--tools` closure moved verbatim into the mod. That is the
named trap "hardcoded tool list copied into the Mod" (Law 13). Acceptable only as a **seed** that PGO overwrites from
fault/usage receipts, labelled as such, with a test that a recorded ToolSearch fault widens the class closure.

## 3. Gaps between v2 and the second prompt (adopted into v2 scope)
- **UTVM L1/L2 — reuse, do not build.** L0 = the raw `.jsonl` transcript plus the v2 page store. L1/L2 = extend the existing
  Prompt Recall BM25 index (`modules.gsd_x.recall`) over turns/tools/files/commits. L3 = goal state + receipts +
  Semantic Delta. L4 = the compiled closure. Proof gate: an old transcript fact is recalled after epoch destruction via
  one page, without replay.
- **Metrics (receipt-derived, `tools/ccr_metrics.py`, offline):** CRA = cache_read / (fresh input + creation);
  Context Survival Ratio = blocks referenced at call n+1 / blocks carried; Resume Amplification = successor call-1
  input / sealed Semantic Delta bytes; Materialization Avoidance Rate = available-not-materialized / available, per
  surface; Context Productivity = accepted transitions / processed input. UNKNOWN stays UNKNOWN (no zero-fill).
- **UCRE:** first rung only in this programme. Repeated Read of an unchanged sha in one Work Class → semantic hit from
  the page store (receipt `ucre:hit`). Derivation and embodied-guarantee rungs → backlog, not scope.
- **Semantic CSE:** v2's exact paragraph hash stays. No embedding dedupe (no evidence it pays).
- **Done-gates 1–29** map onto v2 rings: DG1–4 = R0 · DG5–14 = R0+R1 · DG15–19 = R1 multi-call · DG20 = PGO · DG21 = R2 ·
  DG22 = R4 · DG23 = R2/R3 · DG24–25 = R5 · DG26–29 = closeout.

## 4. Capital
No cap raise now. The first tranche (finish the unit tier, R0 probes P1–P6 + H-275, R1 first-call 6-arm benchmark)
fits inside the remaining 31.7M (≈8M P50). Reforecast from measured R1 numbers before asking for more.
Whole programme with the §3 additions: lower bound 12M · LOWER 28M · P50 43M · P80 55M · P95 68M (confidence medium).

## 5. The Owner decision this addendum adds
ONE writer for `mods/cpp-cognitive-runtime/**`. Two panes executing v2 at once means two writers in policy.ts.
