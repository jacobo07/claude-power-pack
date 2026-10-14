# A0 receipt
Status: DONE_WITH_LIMITS (budget: this session was at 1,492,774 processed at census time against the 1,500,000 unit budget, and its last turns (evidence, receipt, commit) take it past that, under the 2,250,000 breaker; V1 canary rows understate output (stream-json projections without a `result` line); V1 r6-CCR UNKNOWN)

Unit WU-A0 (accounting truth), branch mission/ccr-s3, base 72274ac4. Evidence: `vault/programs/ccr/evidence-v4-stage3-A0.md` (census table, findings, test output, LAPTOP_APPLY).

## Delivered
1. `tools/ccr_spend_census.py` (+ `tools/test_ccr_spend_census.py`, 6 tests OK). It reads pack projections, stream-json and raw transcripts. It dedups by message id with a per-field max, takes stream-json output from `result` lines, and reports a session with no usage as UNKNOWN, never 0. `census --data <dir> [--table]` builds the A0 rows: the Stage 2 ccr workers from missions.json, the V1 canary streams, and the GEX44 Stage 3 sessions from drive.log.
2. Census sum of known rows **21,739,876** processed. That is 16 rows plus r6-CCR UNKNOWN. A0 is included at census time. Lease cap = 1.05 x sum = **22,826,870**. `goal-settle --measured` already accepts a sid unknown to the laptop transcripts, so no `--external` flag was added (checked in a throwaway state dir).
3. `modules/provider_routing/ledger.py`: settle rows record `"lease"`, and `_gfold` books into it. Old rows fold into the lease that was current at the time. `correct` unwinds a lowering from the booking lease(s), newest first. Gate V-LEASE-CORRECT-UNWINDS-BOOKING-LEASE fails on the old ledger.
   Tests on GEX44: `GOAL_LEASE_PASS=21/21`, `MC_PASS=230/230`.

## Finding the coordinator must know
The drive.log `processed=` numbers (A2 4,302,121 / A3 1,678,774 / A4 6,352,270 / A5 2,012,075) undercount output. On stream-json assistant lines, `output_tokens` holds the pre-stream count. Census values: A2 4,359,814 / A3 1,711,442 / A4 6,431,753 / A5 2,043,483 (Linux plane GEX44, host 2.1.296). Have the driver measure with `ccr_spend_census.py measure` from now on, or read the `result` line.

## K7
| unit | estimate | actual processed (every session of this unit) |
|---|---:|---:|
| A0 | 800,000 (plan row A0), budget 1,500,000 | 1,492,774 at census time (session 47649e90, Linux plane GEX44, host 2.1.296). The final value is that plus the closing turns. Take it from `ccr_spend_census.py measure run-A0.jsonl` |

## LAPTOP_APPLY
Exact commands are in the evidence file, section `## LAPTOP_APPLY`. In order:
1. `goal-lease-open --goal ccr --succession-id ccr:book-s3 --cap 22826870 --prev-lease L10`
2. 16 `goal-settle --measured` lines, one per known census row.
3. A0's final re-settle (the watermark books only the delta).
4. Coordinator pane e10a9f08: settle from its own transcript (laptop-only).

Before step 1, check that `goal-status --goal ccr` still shows L10 as the latest lease. If any census sid is already settled on ccr, the watermark books only the excess. Merging mission/ccr-s3 brings the `_gfold` fix and the `lease` field. The booking does not depend on them.

## Text for RESUMPTION_FILE (coordinator owns it)
A0 DONE_WITH_LIMITS: census 21,739,876 known (r6-CCR UNKNOWN). Booking pending LAPTOP_APPLY into lease ccr:book-s3 (cap 22,826,870). `_gfold` correct now unwinds from the booking lease. drive.log undercounts output by ~1.3-1.9 %, so use `tools/ccr_spend_census.py`.
