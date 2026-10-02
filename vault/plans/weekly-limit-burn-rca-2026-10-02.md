# Weekly-Limit Burn — Forensic RCA (2026-10-02)

> Status: **ATTRIBUTION IN PROGRESS** — measurement layer repaired and reconciled (c05cfa3);
> causal attribution (P2) and the alarm rebuild (P5) open. Supersedes nothing: the
> 2026-06-30 RCA stays as written; section 5 says where it went wrong and why.

## 1. Incident

| field | value | label |
|---|---|---|
| Weekly reset | 2026-09-30 19:00 local (+02:00) = 17:00Z | Owner-reported |
| Observation | 2026-10-02 11:40 local = 09:40Z | Owner-reported |
| Elapsed | 40 h 40 min | derived |
| Meter | ~90 % of the **weekly** limit | Owner-reported; weighting UNKNOWN |
| Remote (GEX44) on same account | "mostly yes" | Owner-reported; not yet measured |

## 2. Usage reconstruction (window 17:00Z → 09:40Z)

Reader: `tools/token_ground_truth.py::window_usage` (dedup across files, last copy wins,
subagents included). Cross-checked by an independent scratch parser (global key dedup):
23,925 vs 23,929 calls, 6,230.5 M vs 6,231.7 M cache read, 19.12 M vs 19.13 M output.
**DIRECTLY MEASURED, two paths agree within 0.02 %.**

| category | tokens | raw share | est. weighted share* |
|---|---|---|---|
| cache read | 6,230.5 M | 97.9 % | ~72 % |
| cache write | 113.3 M | 1.8 % | ~16.5 % |
| output | 19.1 M | 0.3 % | ~11 % |
| uncached input | 0.16 M | ~0 | ~0 |
| calls | 23,925 (9,893 subagent, 194 sdk-cli) | | |

\* ESTIMATED with API list ratios (read 0.1x, write 1.25x, output 5x input). The real
weekly-limit weighting is not exposed in transcripts: UNKNOWN.

Shape (measured, first pass): 351 sessions; flat Pareto — top-1 session 1.5 %, top-10
11.7 %, top-50 46 % of cache read. Opus 5.5 = 84 % of calls / 86 % of cache read.
Activity ~500-700 calls/h around the clock, including 02:00-07:00 local; peak 1,524
calls/h at 23:00 local Oct 1. At observation: 19 `claude.exe` + 1 `claude --bg` daemon
live; advisory cache showed "29 hot session(s) on this repo (soft cap 2)".

## 3. Same window, previous weeks (measured, same reader)

| window ending | calls | subagent calls | cache read | cache write | output | ctx/call |
|---|---|---|---|---|---|---|
| 09-18 09:40Z | 13,952 | 2,359 | 4.83 B | 72 M | 13.6 M | 346k |
| 09-25 09:40Z | 14,888 | 5,004 | 5.44 B | 100 M | 15.6 M | 365k |
| **10-02 09:40Z** | **23,925** | **9,893** | **6.23 B** | **113 M** | **19.1 M** | **260k** |

Calls +61 % and subagent calls +98 % week over week; token volume only +15-23 %.
Whether the 09-25 window was near 90 % of its week is UNKNOWN (no meter reading).

## 4. Why nothing warned before 90 % (measured defects, CLASE 4)

1. `window_output` summed every transcript line: output grows while a call streams, so
   39.2 M was reported for 19.1 M. **Fixed c05cfa3.**
2. It never read `<session>/subagents/*.jsonl` (41 % of calls). **Fixed c05cfa3.**
3. One session file can exist under two project dirs: 3,044 calls, +12.7 % if summed per
   file. **Fixed c05cfa3** (global key).
4. `cost_gate.weekly_burn` alarms on **output only**, calibrated on June figures produced
   by defect 1. Output is ~11 % of the estimated weight. **Open (P5).**
5. The advisory runs in a detached bundle with a 40 s timeout that fails open to silence
   (`modules/wrapper/prelaunch.py:253`) over three full-corpus scans. **Open (P5).**
6. CO-08 did fire ("29 hot sessions, soft cap 2") but is informational only.

## 5. CLASE 0 — why the 2026-06-30 fix did not prevent this

The June RCA ruled cache out because the hit ratio was high (95.8 %) and concluded the
burn was output. Its 49.2 M output figure came from defect 1 (~2x) and excluded
subagents. The alarm it produced therefore watched the wrong quantity with an inflated
baseline. Trap: **a high cache-hit ratio says context is reused, not that it is cheap.**

## 6. Subagent attribution (measured, from `<agent>.meta.json` beside each transcript)

9,894 subagent calls, 2,294 M cache read. **100 % `requestShape: background`.**

| slice | calls | share of subagent cache read |
|---|---|---|
| "Execute plan" (gsd-executor + general-purpose) | 3,895 | 45.1 % |
| GSD plan / revise / research / fix / plan-check phases | ~2,600 | ~25 % |
| model `inherit` (runs at the Opus parent) | 5,437 | 53.5 % |
| model `sonnet` explicit | 3,638 | 36.7 % |
| model `opus` explicit | 819 | 9.8 % |
| project orca-dws-wt / recon match-accel / recon keosdtk-home | 5,916 | 67.7 % |

Actual serving model of subagent calls: Opus 6,234, Sonnet 3,657, Haiku 3.
The unattended GSD worktree runs are the subagent burn; the Owner keeps them running
(2026-10-02) — attribution only, nothing paused. Lever candidate (UNPROVEN, needs a
quality A/B): execution-phase subagents that inherit Opus instead of the Sonnet routing
in TCO rule 5.

## 7. Model mix, same window a week apart (measured, global dedup)

| | 09-23..25 | 09-30..10-02 |
|---|---|---|
| Opus main calls / cache read / ctx per call | 9,883 / 4.10 B / ~416k | 13,961 / 3.93 B / 282k |
| Opus subagent calls / cache read | 3,401 / 0.84 B | 6,234 / 1.45 B |
| Sonnet subagent cache read | 0.50 B (sonnet-5) | 0.84 B (sonnet-5-5) |
| Opus cache read total / output total | 4.94 B / 13.97 M | 5.38 B / 16.2 M |

Opus volume grew +9 % (cache read), almost all in subagents. Main sessions ran on
smaller contexts but more calls. Open for the Owner: the meter reading at the same
point of the previous week. If it was also high, the cause is the standing level
(~5 B Opus cache read per 40 h), not an anomaly.

## 8. Human-prompt proximity (DERIVED heuristic, main transcripts)

A human prompt = `type: user`, not a tool_result, not meta, not a command/system/
task-notification wrapper. 570 such prompts in the window; 23,925 calls, so **~42 model
calls per typed prompt**, ~11 M cache-read tokens each.

| main-call distance from last human prompt | calls | share of main cache read |
|---|---|---|
| < 10 min | 4,138 | 27.7 % |
| 10-60 min | 4,497 | 35.6 % |
| 1-4 h | 1,487 | 12.8 % |
| > 4 h | 242 | 2.4 % |
| no human prompt in that transcript | 3,671 | 21.4 % |

Far (>1 h or none) main cache read 1.44 B + worktree-project subagents 1.55 B: about
48 % of the window's cache read had no human prompt within the previous hour.
`entrypoint` marks only 194 calls as sdk-cli, so it cannot be the discriminator.

## 9. Correction — cache-read rate

Sections 2 and 4 used cache read at 0.1x input. The rate card verified on 2026-09-27
(`vault/plans/context-rent-2026-09-27.md`) has **Opus 5.5 cache read at 0.05x**, and
1h-TTL writes at 2x (5m: 1.25x). Re-estimated weight: cache read ~50-57 %, cache write
~25-35 % (depends on the 1h share, UNKNOWN here), output ~10-15 %. Still ESTIMATED;
the weekly-limit weighting itself remains UNKNOWN.

## 10. Startup floor vs growth (measured, transcripts born in the window)

| | first-call context, median (p10-p90) | share of their re-read that is floor |
|---|---|---|
| main (150) | 126k (70k-141k) | 46 % |
| subagent (219) | 95k (49k-101k) | 40 % |

Floor and history growth are levers of about the same size.

## 11. Interactive rollover is ON, but fires only at ~450k

Ledger `~/.claude/state/rollover/rollover-ledger.jsonl`, in-window rows: 126
shadow_candidate, 64 capsule_sealed, 55 SAFE_TO_FORGET / 5 REFUSED gates, 55 claimed,
54 resume_certified — rollover works. But:

- The active crossing is asked only at the advisory wall, `THRESHOLD_ADVISORY_PCT = 45`
  (`modules/zero-crash/hooks/context-watchdog.py:45`) ≈ 450k on a 1M window.
- The economic decider (`tools/rollover.py::decide`) runs at the 40 % snapshot tier in
  SHADOW only, and is called without `start_head` (`context-watchdog.py:1484`), so
  `at_boundary` (`rollover.py:538`) is true only for a clean tracked tree — which a shared
  tree never is. Result: **110 of 126 decisions = "worth it, but not at a work boundary"**,
  4 would_rollover, 12 unreadable. Median resident at decision 451k (break-even ~15 calls).

Every session therefore pays rent on the band between its ~126k floor and ~450k.

## 12. Open (next)

- GEX44 transcripts (same account per Owner) — not yet read.
- Weighted-burn alarm replacing the output-only one (P5). Calibration needs a meter
  reading paired with a measured window; this incident gives the first pair
  (90 % at this window).

## 13. Subagent inheritance (P0 of plan cognitive-control-plane-2026-10-02, MEASURED)

219 subagent transcripts born in the window, each joined to the parent call that
dispatched it (meta `toolUseId`). 0/219 start at >= 80 % of the parent's context;
spawnDepth 1 in all. First-call context is set by agent TYPE (general-purpose 98k,
gsd-executor 98k, carrier-verifier 49k, Explore 26k), not by the parent (155k-409k).
Subagents do NOT replay the parent transcript. Their cost is a ~95k floor x calls,
plus growth to ~232k average per call.

## 14. Meter reconciliation FAILS (C1, `tools/usage_index.py`, 2026-10-02)

The new incremental index reproduces §2 to the token (23,925 calls, 9,893 subagent,
6,230,548,450 cache read, 19,115,576 output): a third reader agrees. Then:

| week (from reset) | Owner meter | laptop calls | cache read | API-equiv USD | per meter-% |
|---|---|---|---|---|---|
| A 09-23 17:00Z -> 09-30 07:51Z | 75 % | 62,418 | 20.75 B | 8,041 | $107 |
| B 09-30 17:00Z -> 10-02 09:40Z | 90 % | 23,925 | 6.23 B | 2,275 | $25 |

B/A usage per meter-% is 0.23-0.38 in EVERY category (calls, subagent calls, cache
read, cache write, output, USD 0.24), so **no positive weighting of transcript-visible
usage reconciles the two readings**. Calibrated on A, B is predicted at 21 % (observed 90 %).
GEX44 (same account) measured read-only over ssh: 3,362 calls in A, 263 in B. It is not
the cause, and adding it widens the gap.

Replay of the rate-anomaly alarm over B (4 h steps): NORMAL throughout, 24 h burn
0.79-1.32x the 14-day median day. **By everything the transcripts record, the incident
window ran at the prior standing level (~$1.2k/day API-equivalent).** What changed is
the meter cost of that level, about 4x.

Hypotheses, UNVERIFIED, Owner-checkable only: (1) the weekly allowance changed about 4x
at the 09-30 reset (plan tier or limit policy; max20x/max5x = 4); (2) the meter counts
usage that no transcript records (claude.ai, Desktop, mobile, another machine);
(3) the 75 % reading was of a different meter. Until one is confirmed,
`vault/config/weekly_meter_readings.json` has the 75 % reading `suspended` and the alarm
shows NO percentage (UNKNOWN), only rates, the anomaly ratio and typed MONITOR_FAILURE.

## 15. The provider's own quota rows (C1b, 2026-10-02 evening)

Transcripts carry `quotaLimits` on the synthetic rows the harness writes when a call is
refused: `rateLimitType` (seven_day / five_hour), `status`, `resetsAt`,
`overageDisabledReason`. 511 rows since 09-16 (laptop). Decoded reset anchors:

| seven_day window (reset weekday, UTC) | resets seen | overage reason | rejected spans |
|---|---|---|---|
| Wed 17:00Z | 09-16, 09-23, 09-30, 10-07 | org_level_disabled | 09-16, 09-22, 09-26, 09-30, **10-02 11:54Z -> 10-07 17:00Z** |
| Sat 18:00Z | 09-27 (then 10-04) | out_of_credits | 09-24..09-27, 09-28/29 |
| other | 10-06 02:00Z | org_level_disabled | 09-30 14:49Z |

One account has one weekly window, so **at least two, probably three, accounts or orgs
write into this transcript store**. That is corroborated live: the Wed-17Z window has
refused calls since 10-02 11:54Z, yet this session went on calling, so it runs on another
account.

Ranked hypotheses for §14 (supersedes nothing; §14's three remain listed):
- **H4 (leading, consistent with every measured fact):** week A's laptop usage was spread
  across accounts, and the meter the Owner read covered one of them. By week B the others
  were refusing, so the usage concentrated on the one being read. This predicts a B/A
  ratio below 1 in every category at once, which is what §14 measured.
- H1 (allowance change) is not needed to explain the data, and not excluded.
- Transcripts carry no account id, so per-account attribution is impossible locally
  until the Owner names the accounts.

What this changes: the alarm now shows provider truth (window, rejected-since, until)
from these rows, and `NO_SIGNAL` when there are none. It never shows a fitted percentage.

Consequence: §5's lesson still stands, and a second one joins it. **An alarm calibrated
on transcripts cannot see a change in what the meter charges.** The control-plane levers
(agent floor, fan-out, concurrency) cut the standing level whatever the meter does.

## 16. Production Reality Gate on the real index (PRG-1/PRG-2, 2026-10-02 night)

Window 09-30 17:00Z -> 10-02 09:40Z, same reader. No model call.

**PRG-1 (fan-out ledger, `5b8057c`).** Anchor unchanged (23,925 calls / 6,230,548,450 cache
read). Root split: human 11,622 · mission 10,473 · continuation 1,637 · SDK 179 · unknown 14.
9,893/9,893 subagent calls linked to the prompt that spawned them. Human prompt fan-out median
12, p90 67, max 239. The max, f319ce75, is 214 parent calls + 25 subagent calls: depth, not
width. Two amplification shapes exist and need separate measures.

Two report defects found and fixed: the single-prompt view ignored the mission title
(mission prompts read HUMAN), and a subagent's project came from the spawn row's file.
Root cause of the second: `projects/C--Users-User-Apps-mcp-video-analyzer` is a JUNCTION to
the PP project dir; 148 sessions are indexed under both paths. Call totals are safe (dedup on
message id + request id); path-keyed rows (`spawns.file`) land on whichever alias was written
last. Calls themselves land on the real path only because `iterdir()` on NTFS lists it first:
correct by listing order, not by design.

Spawn outcomes: 240 spawns in the window, 39 with no transcript = 32 hook-denied + 7 other
errors, 0 with a result. A requested spawn is not an executed one.

**PRG-2 (estate shadow replay, `tools/estate_shadow.py`, decider unchanged).** Bands frozen
from 09-16..09-30 (957 spawns; p90 active_sessions 15, active_subagents 6, calls/h 1,132).
240 judged: BACKGROUND 88 allow / 15 would-defer, CRITICAL_VERIFY 80, INTERACTIVE 46, NORMAL 11.
**protected_deferred = 0.** All 15 would-defers reviewed (the whole set): every one a MISSION
root at BACKGROUND (orca-dws-wt 8, InfinityOps 7, 10-01 10:59Z..22:38Z); reasons 11 calls/h
(some with active_subagents), 2 active_sessions, 2 prompt fan-out over the envelope of 3.
Each names its band; each would be admitted when load drops below p90. 2 of the 15 had
already been hook-denied. Upper bound touched: 1,063 calls / 248,905,008 cache read, not a
saving. The junction does not inflate the load dims today: 0/128,567 baseline and 0/23,925
judged calls carry the alias path.

Preconditions recorded before any enforcement: (1) store identity by resolved path, not
listing order; (2) `estate_shadow.py:90` takes project from the spawn file (display only
today); (3) deferring a child can convert width into parent depth, invisible to replay, so
any saving stays an upper bound; (4) UNKNOWN roots map to BACKGROUND (`scheduler.py:325`);
(5) the decider sees load only, no owner or progress.
