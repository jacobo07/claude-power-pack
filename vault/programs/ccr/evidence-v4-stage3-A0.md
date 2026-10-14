# CCR v4 Stage 3 -- A0 evidence: accounting truth

Unit WU-A0, branch mission/ccr-s3, base 72274ac4. Census by `tools/ccr_spend_census.py census --data /home/kobii/missions/ccr-s3-data`
(processed = input + cache_read + cache_creation + output, deduplicated by message id). Rows labelled
"Linux plane GEX44, host 2.1.296" were measured on GEX44 from full stream-json. Rows labelled "laptop projection" were measured
on GEX44 from the content-free projections of laptop sessions.

## Census

| row | session | plane | source | processed |
|---|---|---|---|---:|
| Stage 2 E1 (m-8630677b026a) | 001c9e4e-ba04-4d19-8fbe-78f4304e11f9 | laptop projection | /home/kobii/missions/ccr-s3-data/pack/sessions/001c9e4e-ba04-4d19-8fbe-78f4304e11f9.jsonl | 534,881 |
| Stage 2 M1 (m-bc2b5c94f9cf) | 605d38ef-7bae-4702-a0d6-faa7b14264e1 | laptop projection | /home/kobii/missions/ccr-s3-data/pack/sessions/605d38ef-7bae-4702-a0d6-faa7b14264e1.jsonl | 592,699 |
| Stage 2 W1 (m-06a50f8e8f80) | 3bf62077-d19e-4f84-af67-f95747fa3bce | laptop projection | /home/kobii/missions/ccr-s3-data/pack/sessions/3bf62077-d19e-4f84-af67-f95747fa3bce.jsonl | 928,392 |
| Stage 2 V1 (m-d668c76f3a2e) | f995c8ec-fc72-4021-931e-4d796e17f39d | laptop projection | /home/kobii/missions/ccr-s3-data/pack/sessions/f995c8ec-fc72-4021-931e-4d796e17f39d.jsonl | 1,335,490 |
| Stage 2 X1 (m-d7844573c944) | 82b1fe63-fc1b-4901-9a65-85a312275b5d | laptop projection | /home/kobii/missions/ccr-s3-data/pack/sessions/82b1fe63-fc1b-4901-9a65-85a312275b5d.jsonl | 428,897 |
| V1 canary attempt1-stream-r1-OFF | ext-ccr-v1-attempt1-r1-OFF | laptop projection | /home/kobii/missions/ccr-s3-data/pack/v1/attempt1-stream-r1-OFF.jsonl | 457,404 |
| V1 canary stream-r1-OFF | ext-ccr-v1-r1-OFF | laptop projection | /home/kobii/missions/ccr-s3-data/pack/v1/stream-r1-OFF.jsonl | 312,365 |
| V1 canary stream-r2-CCR | ext-ccr-v1-r2-CCR | laptop projection | /home/kobii/missions/ccr-s3-data/pack/v1/stream-r2-CCR.jsonl | 89,475 |
| V1 canary stream-r3-OFF | ext-ccr-v1-r3-OFF | laptop projection | /home/kobii/missions/ccr-s3-data/pack/v1/stream-r3-OFF.jsonl | 468,726 |
| V1 canary stream-r4-CCR | ext-ccr-v1-r4-CCR | laptop projection | /home/kobii/missions/ccr-s3-data/pack/v1/stream-r4-CCR.jsonl | 81,674 |
| V1 canary stream-r5-OFF | ext-ccr-v1-r5-OFF | laptop projection | /home/kobii/missions/ccr-s3-data/pack/v1/stream-r5-OFF.jsonl | 470,607 |
| V1 canary r6-CCR (killed by host memory reaper, no stream) | -- | laptop projection | -- | UNKNOWN |
| Stage 3 A2 | 0c9c8dbd-68ba-4499-b3d6-514fc304962e | Linux plane GEX44, host 2.1.296 | /home/kobii/missions/ccr-s3-data/run-A2.jsonl, /home/kobii/missions/ccr-s3-data/run-A2.r1.jsonl | 4,359,814 |
| Stage 3 A3 | 2fd33286-45a0-4e79-918a-8a771c32b9d8 | Linux plane GEX44, host 2.1.296 | /home/kobii/missions/ccr-s3-data/run-A3.jsonl | 1,711,442 |
| Stage 3 A4 | d37c61fb-9dd2-449d-90ba-4e530acc1671 | Linux plane GEX44, host 2.1.296 | /home/kobii/missions/ccr-s3-data/run-A4.jsonl | 6,431,753 |
| Stage 3 A5 | 26dfffd3-3389-4872-80ba-c05fa3c48461 | Linux plane GEX44, host 2.1.296 | /home/kobii/missions/ccr-s3-data/run-A5.jsonl | 2,043,483 |
| Stage 3 A0 | 47649e90-2c69-43ee-a310-fa8a35cb967e | Linux plane GEX44, host 2.1.296 | /home/kobii/missions/ccr-s3-data/run-A0.jsonl | 1,492,774 |
| **sum (known rows)** | | | | **21,739,876** |

Sum of known rows: **21,739,876**. UNKNOWN (never booked as 0): V1 r6-CCR. The run was killed by the host memory reaper, and no stream exists.
The A0 row is this session at census time. Its final value is larger (see LAPTOP_APPLY).

### Findings while measuring
- **stream-json undercounts output.** On a stream-json `assistant` line, `output_tokens` holds the count from before the reply streamed:
  A3 sums to 341 over 32 messages, while its `result` line says 33,009. Input and cache fields agree exactly. The census therefore
  takes each session's output as max(per-message sum, sum of its `result` lines). That moves the GEX44 Stage 3 figures above the
  drive.log / packet numbers: A2 4,302,121 -> 4,359,814; A3 1,678,774 -> 1,711,442; A4 6,352,270 -> 6,431,753; A5 2,012,075 -> 2,043,483.
  The drive.log `processed=` therefore understates by about 1.3-1.9 %.
- **The V1 canary rows understate output by a bounded amount.** They are projections of stream-json, and no `result` line was kept.
  For example, r1-OFF records 15 output tokens over 4 messages. Output is the only field affected. The undercount is of the
  order of the run's real output, a few thousand tokens per run, and it is not recoverable from the pack.
- Laptop transcript projections (Stage 2 workers) do carry the final output counts. For example, E1 records 14,180 output tokens and none of its 16 messages is below 20.
  E1 534,881 / M1 592,699 / W1 928,392 reproduce the plan's figures exactly.
- V1 canary sessions carry no session id in the pack. They are booked under explicit ids `ext-ccr-v1-<run>`. If their real laptop
  sids are ever settled to ccr too, that would book twice. Settle them only under one name.
- `goal-settle --measured` never consults a transcript (`tools/mission_spend.py` goal_settle: the transcript lookup runs only when
  `measured is None`; `_SID_RE` accepts any `[A-Za-z0-9._-]{1,128}`). An unknown or GEX44 sid is therefore accepted as-is, and no
  `--external` flag was added. This was checked on GEX44 in a throwaway GSD_LONG_RUN_STATE_DIR: settle of 0c9c8dbd... at 4,359,814 and of
  ext-ccr-v1-r1-OFF -> ok, rows carry `"lease": "L2"`.

## `_gfold` fix (modules/provider_routing/ledger.py)
- Every settle row now records its booking lease (`"lease"`), on all three append sites (renew, tombstoned renew, settle_stopped).
- In the fold, settle books into the recorded lease. An old row without the field books into the lease that was current when it
  was written, which is the fold's current lease at that row, so old journals fold unchanged.
- `correct` lowering a mark now takes the delta off the leases that booked that sid, newest booking first. A later lease is untouched.
  A raise is booked into the current lease.
- Gate V-LEASE-CORRECT-UNWINDS-BOOKING-LEASE: settle a=3M in L1, open L2, settle b=1M, correct a->2M. Result: L1.settled 2M,
  L2.settled 1M (unchanged), total_used 3M = corrected goal settled, current used 1M. The fold also matches with `lease` stripped
  from every row. Against the unpatched ledger the gate FAILS (`GOAL_LEASE_PASS=20/21`).

## Test output (GEX44)
```
python3 tools/test_goal_lease.py      -> GOAL_LEASE_PASS=21/21
python3 tools/test_gsd_mission.py     -> MC_PASS=230/230
python3 tools/test_ccr_spend_census.py -> Ran 6 tests ... OK
```

## LAPTOP_APPLY

Repo root `C:\Users\User\.claude\skills\claude-power-pack`, run from the worktree `.claude\worktrees\ccr` (branch ccr/v4) after merging mission/ccr-s3 (the `lease` field on settle rows and the `_gfold` fix ship with it; the lease open and the settles work with or without it). Order matters: the lease opens first, so every settle books into ccr:book-s3.

```powershell
cd C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\ccr
python tools/mission_spend.py goal-lease-open --goal ccr --succession-id ccr:book-s3 --cap 22826870 --prev-lease L10
python tools/mission_spend.py goal-settle --goal ccr --session 001c9e4e-ba04-4d19-8fbe-78f4304e11f9 --measured 534881
python tools/mission_spend.py goal-settle --goal ccr --session 605d38ef-7bae-4702-a0d6-faa7b14264e1 --measured 592699
python tools/mission_spend.py goal-settle --goal ccr --session 3bf62077-d19e-4f84-af67-f95747fa3bce --measured 928392
python tools/mission_spend.py goal-settle --goal ccr --session f995c8ec-fc72-4021-931e-4d796e17f39d --measured 1335490
python tools/mission_spend.py goal-settle --goal ccr --session 82b1fe63-fc1b-4901-9a65-85a312275b5d --measured 428897
python tools/mission_spend.py goal-settle --goal ccr --session ext-ccr-v1-attempt1-r1-OFF --measured 457404
python tools/mission_spend.py goal-settle --goal ccr --session ext-ccr-v1-r1-OFF --measured 312365
python tools/mission_spend.py goal-settle --goal ccr --session ext-ccr-v1-r2-CCR --measured 89475
python tools/mission_spend.py goal-settle --goal ccr --session ext-ccr-v1-r3-OFF --measured 468726
python tools/mission_spend.py goal-settle --goal ccr --session ext-ccr-v1-r4-CCR --measured 81674
python tools/mission_spend.py goal-settle --goal ccr --session ext-ccr-v1-r5-OFF --measured 470607
python tools/mission_spend.py goal-settle --goal ccr --session 0c9c8dbd-68ba-4499-b3d6-514fc304962e --measured 4359814
python tools/mission_spend.py goal-settle --goal ccr --session 2fd33286-45a0-4e79-918a-8a771c32b9d8 --measured 1711442
python tools/mission_spend.py goal-settle --goal ccr --session d37c61fb-9dd2-449d-90ba-4e530acc1671 --measured 6431753
python tools/mission_spend.py goal-settle --goal ccr --session 26dfffd3-3389-4872-80ba-c05fa3c48461 --measured 2043483
python tools/mission_spend.py goal-settle --goal ccr --session 47649e90-2c69-43ee-a310-fa8a35cb967e --measured 1492774
# A0 (this session) was measured at census time; its last turns come after. Re-settle it with the FINAL value
# (watermark: only the delta books). Take it on GEX44 with: python3 tools/ccr_spend_census.py measure /home/kobii/missions/ccr-s3-data/run-A0.jsonl
#   python tools/mission_spend.py goal-settle --goal ccr --session 47649e90-2c69-43ee-a310-fa8a35cb967e --measured <final>
# Coordinator pane e10a9f08 (laptop-only, not measurable from GEX44): measure it from its own transcript, then
python tools/mission_spend.py goal-settle --goal ccr --session e10a9f08-<full sid>
python tools/mission_spend.py goal-status --goal ccr
```
