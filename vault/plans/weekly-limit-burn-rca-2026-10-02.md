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

## 9. Open (next)

- GEX44 transcripts (same account per Owner) — not yet read.
- Weighted-burn alarm replacing the output-only one (P5). Calibration needs a meter
  reading paired with a measured window; this incident gives the first pair
  (90 % at this window).
