# LAPTOP RESULTS (ctx-rent-x), plane: laptop, 2026-10-31 ~16:05 local, run by pane f432029e on branch ctx-rent-x-w0 @ a0073a50

## L1: PASS
Command: `python tools/ctx_rent.py estate --since 2026-10-25T00:00:00Z --until 2026-11-01T00:00:00Z --out vault/programs/ctx-rent-x/estate-laptop-w0.json` (rc 0)
Total: 1,287 sessions, 43,031 calls, 7,473,949,368 processed, floor_rent 3,860,620,200 (51.7 %). active_release 0.1.0-b15bfc3d.

top-level by generation (sessions, calls, processed, floor_rent -> mean floor = floor_rent/calls):

| generation | sessions | calls | processed | mean floor | processed/call |
|---|---:|---:|---:|---:|---:|
| UNKNOWN | 73 | 10,043 | 2,269,174,028 | 99.7K | 226K |
| STALE fce69916 | 203 | 8,330 | 1,533,945,422 | 111.4K | 184K |
| STALE 7df93813 | 138 | 3,414 | 545,364,180 | 101.9K | 160K |
| STALE 40f2c160 | 34 | 2,252 | 531,039,483 | 101.7K | 236K |
| STALE f79e3c46 | 14 | 1,905 | 413,503,921 | 122.5K | 217K |
| STALE c42eb4e7 | 27 | 1,841 | 437,057,407 | 114.9K | 237K |
| STALE 82c98708 | 19 | 1,631 | 284,857,949 | 106.3K | 175K |
| STALE 384b03a0 | 71 | 1,023 | 142,520,620 | 103.3K | 139K |
| CURRENT b15bfc3d | 18 | 845 | 154,275,711 | 108.3K | 183K |
| STALE c5b18294 | 7 | 41 | 5,975,872 | 114.7K | 146K |

Other classes: subagent 621 sessions / 10,147 calls / 969.8M (all UNKNOWN); worker:background 37 sessions / 1,159 calls / 171.7M; worker:slim 25 / 400 / 14.7M (UNKNOWN).

Reading (laptop plane, MEASURED): the top-level mean floor sits at ~100-122K in EVERY CCR generation, including CURRENT.
CCR generation does not move the interactive floor, consistent with `main:'shadow'`. Top-level = 84.5 % of processed
(6.32B of 7.47B). The lever is the top-level floor + main enforcement (Phases 2-3), not generation rollout.

## L2: PASS
Command: `python tools/ccr_release.py --root %TEMP%/claude/ccr-scratch-root release --impact none` (rc 0), SCRATCH root so the
live `~/.claude/ccr` was not touched (ACTIVE.json still 0.1.0-b15bfc3d, ts 09:35:04).
RELEASE.json: `{"release": "0.1.0-7b5347c5", "version": "0.1.0", "source_commit": "a0073a50bb3d05a179716a5d90cdfa120ea188ae"}`: 40-hex.

## L3: PASS for rules, NOT APPLIED for agents (2026-10-31 ~17:00 local)
Harness `l3_probe_harness.py` (apply -> probe -> revert per arm, tree hash checked after every probe; before == after 2a73eb63).
Probe `claude -p "reply OK" --model haiku --output-format json`, empty git repo cwd, claude 2.1.316, N=4 per arm, CTCT then TCTC.
- agents_park (93 of 95 parked): control 74,083/74,099/74,099/73,953, treatment 64,310/64,318/64,318/64,631 -> **-9,664**, control spread 0.2 %.
- rules_to_skills (3 rules): control 74,573/74,469/74,116/74,137, treatment 69,662/69,677/69,677/69,698 -> **-4,645**, spread 0.61 %.
- memory_trim: EMPTY (no MEMORY.md over 200 lines on the laptop).
Kept applied: **rules_to_skills only** (backup `~/.claude/backups/ctx-rent-x-20261031T170348-keep-rules`; skill descriptions
and index lines rewritten with triggers by hand, which adds back ~0.25K est. of listing text).
NOT kept: agents_park. Agents used in the last 30 days (subagent_type scan, 4,663 transcripts) plus the gsd-/pp-/cdio-/kme- families
leave only 4 of 95 parkable; the 9.7K needs parking used agents. The non-destructive route is the existing CCR v4 A7 main-lean canary.

## L4: NOT RUN
Needs `hooks/session_start_hub.js`, which carries another pane's uncommitted edits in the shared tree; saving only ESTIMATE (~1.7K).

## L5: mission patch NOT applied (duplicate); canary run INCOMPLETE (memory reaper)
- Live `b15bfc3d` already ships `CCR_MAIN_CANARY=1` (`mainCanaryMode`, v4 A7): names-only skill/agent/MCP listings on interactive
  sessions, descriptions paged on demand. `CCR_MAIN_MODE` (908989eb) duplicates it: dropped (EXTEND > CREATE).
- Live `policy.ts` matches NO committed blob; `register.ts` matches the ccr-a2 line (d69d930a9). A release from this branch would
  have regressed live. Commit 35776051 records the live mod contents.
- Driver `l5_canary_driver.py` (ConPTY, real interactive `claude --model haiku`, PP root). 1 of 8 probes before the host memory
  reaper killed the run: A0 control call-1 93,396, receipt release 0.1.0-b15bfc3d canary off. Not restarted (reaper rule).

## Defects for the worker (Error -> Immunity)
1. floor_diet.py skill description = first non-heading line cut at 300 chars: mid-sentence, and a leading quote broke the YAML.
2. memory_trim keeps the HEAD 200 lines; memory indexes append at the END, so it would park the newest hooks.
3. Phase 3 built CCR_MAIN_MODE without finding CCR_MAIN_CANARY (v4 A7) in the live release: the worker read the branch, not live.
