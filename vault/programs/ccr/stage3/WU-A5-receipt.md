# A5 receipt
Status: DONE_WITH_LIMITS (canary 1 of 3 runs per arm: each CARRY run costs 1,426,157 processed; after round 1 the unit was at about 3.0M of its 3,000,000 budget, and rounds 2-3 (about 2.94M) would cross the 4,500,000 hard stop)

Unit: WU-A5, Lobby R1, the long-horizon textual work class. Linux plane GEX44, host 2.1.296, branch mission/ccr-s3.

## Done-check
`vault/programs/ccr/evidence-v4-stage3-A5.md` contains the offline table (section 1), the canary table (section 2) and the verdict (section 3).

## Results (Linux plane GEX44, host 2.1.296)
- **Offline, E1 arm D on 15 held-out Lobby sessions, 22 capsules measured at each rotation point:**
  - Capsule size: p50 222.5 tokens, max 342 (E1 assumed 8,000).
  - E1-D-8k: +6.49 % weighted.
  - **E1-D-measured: +7.95 %** (median session +5.20 %).
  - A4-D-measured (with measured rehydration): +1.53 % (median 0.0 %).
  - The result is positive, so not NO_WORK, but it is below the 15 % bar.
- **Canary on one bounded textual continuation from Lobby epoch e5, cut at call 40 (context 320,382), haiku, n = 1 per arm:**
  - CARRY: 1,426,157 processed, 559,925.5 weighted, PASS.
  - ROT: 42,540 processed, 38,615.2 weighted, PASS.
  - ROT's weighted saving is 93.1 %, with parity 1/1 vs 1/1.
  - The canary prices one step after the capsule. It does not price a full epoch rotation, because ROT does not re-create the epoch's ~194k floor.
- RAM admission before round 1: MemAvailable 58,405,848 kB. There was no RAM_HOLD and no runaway.

## Files
- `tools/ccr_lobby_a5.py`: the offline replay. Its three cost models use per-point measured capsules.
- `vault/programs/ccr/stage3/a5/a5-offline.json`: the offline replay, with per-session rows and capsules.
- `vault/programs/ccr/stage3/a5/canary.py`: the canary driver. It runs one round per invocation, appends to its output, enforces RAM admission and the runaway stop, and checks the answer.
- `vault/programs/ccr/stage3/a5/canary.json`: the canary output.
- `vault/programs/ccr/evidence-v4-stage3-A5.md`: the evidence.

Scratch, outside the repo:
- `ccr-s3-data/a5-work/{lobby-repo, canary-repo, transcript-copies, unit-a5.json}`
- the CARRY copy `~/.claude/projects/-home-kobii-missions-ccr-s3-data-a5-work-canary-repo/48365489-....jsonl`
- the run sessions `ae35f5fe` (CARRY fork) and `2d004877` (ROT)

## K7: estimate vs actual processed tokens, every session of this unit
| session | processed |
|---|---:|
| worker 26dfffd3 (this session; measured at 27 calls, just before this receipt) | 1,841,414 |
| canary CARRY ae35f5fe | 1,426,157 |
| canary ROT 2d004877 | 42,540 |
| **actual total (at receipt write)** | **3,310,111** |
| estimate (packet budget) | 3,000,000 |

The actual total is 1.10 times the estimate, under the 1.5x stop (4,500,000). The few closing calls that commit this receipt are not included.

## Follow-up (GEX44, not laptop)
To complete the planned 3 runs per arm, run under a fresh budget:

    cd /home/kobii/missions/ccr-s3 && python3 vault/programs/ccr/stage3/a5/canary.py --out vault/programs/ccr/stage3/a5/canary.json --round 2
    cd /home/kobii/missions/ccr-s3 && python3 vault/programs/ccr/stage3/a5/canary.py --out vault/programs/ccr/stage3/a5/canary.json --round 3

## LAPTOP_APPLY
None. This unit needs no ledger booking, release or live session.
