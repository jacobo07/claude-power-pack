# CCR v4 Stage 2 E1 - epoch economics with cache-write cost + thinking-carry lever

Weights (constants at top of tools/ccr_epoch_econ.py): read 0.1, write 1.25, input 1.0, output 5. Capsule 8,000. Rotation: ctx -> floor+capsule, pays one write of that prefix, drops carried growth. Min 5 calls/session. Bar: held-out saving >= 15 %.
Fit on TRAIN only: the arm with the best train saving is chosen (F's multiplier m and expected length are also train-fit). Evaluated on HELD-OUT.

## Commands
- `python tools/test_ccr_epoch_econ.py` -> exit 0 (V-CCREPOCH-LINEAR, -FLAT, -UNKNOWN; the clamp fix below came after the first full run, tests re-run green)
- `python tools/ccr_epoch_econ.py madzia <p4p2a3..a13 worker.stream.jsonl> --train 6` (a3-a8 train, a9-a13 held-out)
- `python tools/ccr_epoch_econ.py lobby <KobiiCraft-Core-Files projects dir> --cutoff 2026-10-01`

Caveat: the lobby dir is live; a rerun adds sessions, so the lobby A-cost moved 211.99M -> 212.17M between my two runs. A first run had no floor on the rotated ctx and produced a negative cost for E on compacted sessions; fixed (sim ctx >= rotated prefix) and everything below is from the fixed code.

## madzia-worker (train 6, held 5, unknown 0)  -> ABSTAIN:-0.2%
Chosen on train: F (m=1.0, expected length 32 calls).
| arm | held weighted cost | held processed | rotations | held saving | train saving |
|---|---|---|---|---|---|
| A | 1,126,536 | 7,484,580 | 0 | 0 | 0 |
| B k=10 | 1,265,492 | 5,177,866 | 12 | -12.3 % | -4.4 % |
| C k=20 | 1,155,028 | 6,262,104 | 5 | -2.5 % | 5.7 % |
| D k=40 | 1,192,392 | 7,847,295 | 1 | -5.8 % | 0.1 % |
| E 2x floor | 1,257,809 | 5,016,585 | 13 | -11.7 % | -7.2 % |
| F break-even | 1,128,540 | 7,142,498 | 2 | -0.2 % | 7.0 % |

## lobby (train 188, held 51, unknown 0, short <5 calls 336 excluded)  -> BEATS_A (D k=40, +21.1 %)
Chosen on train: D (train 21.9 %; E 21.7 % was within 0.2 pt). F fit m=0.25, expected length 251.
| arm | held weighted cost | held processed | rotations | held saving | train saving |
|---|---|---|---|---|---|
| A | 212,174,214 | 1,599,014,842 | 0 | 0 | 0 |
| B k=10 | 215,983,124 | 834,575,771 | 546 | -1.8 % | -1.6 % |
| C k=20 | 178,303,016 | 895,324,316 | 259 | 16.0 % | 16.5 % |
| D k=40 | 167,497,040 | 1,003,179,526 | 117 | 21.1 % | 21.9 % |
| E 2x floor | 169,018,551 | 1,088,570,665 | 221 | 20.3 % | 21.7 % |
| F break-even | 174,371,182 | 911,763,036 | 297 | 17.8 % | 4.3 % |

## Thinking-carry lever (madzia, all 11 streams; ccr_carry_fit thinking_sig rate 0.2885 tok/char, fit PLAUSIBLE)
| arm | thinking_sig carry as % of A's carry | thinking carry removed vs A |
|---|---|---|
| A | 31.8 % | 0 |
| B | 6.7 % | 78.8 % |
| C | 13.9 % | 56.2 % |
| D | 27.7 % | 13.0 % |
| E | 4.8 % | 85.0 % |
| F | 17.9 % | 43.8 % |
Rotation removes most thinking carry, but on Madzia the cache-write bill exceeds it: removal is not saving.

## Chosen rule and verdict
- madzia-worker: ABSTAIN:-0.2 % (best train arm F; held-out -0.2 %, no arm positive).
- lobby: BEATS_A with D (rotate every 40 calls), held-out +21.1 % (>= 15 %). Rotation at k=20 (16.0 %) and E (20.3 %) also clear the bar. Caveat: rotation here is a model (capsule 8k assumed, work after rotation assumed unchanged); processed tokens fall 37 %.
