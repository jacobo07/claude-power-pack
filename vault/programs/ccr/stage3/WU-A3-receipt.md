# A3 receipt
Status: DONE_WITH_LIMITS

Limits, each with its number:
1. **Gate not met by any class.** The best class with enough held-out sessions is `bounded-code`: P50 APE 46.4 % (gate < 25 %) and P80 coverage 70.8 % on n = 24 held-out. `long-textual` scores APE 21.7 % and coverage 85.7 %, but on n = 7 held-out, which is under the gate's 8.
2. **`multimodal` has n = 0** in the Work Unit corpus. Image share is 0.0 in all 125 sessions, so multimodal runs as the generic cold start at LOW confidence.
3. **`gsd_mission` is not switched to `pgo-classes.json`.** It still reads `<pgo dir>/<ccr_class>.json`.

All numbers come from the Linux plane GEX44, host 2.1.296.

## Deliverables
- `tools/ccr_pgo.py`: added `classify`, `projection_facts`, `corpus`, `fit_class`, `judge`, `time_split`, `loo`, `confidence`, `build_by_class` and `pick_class`. It gains `build --by-class`. `contract` picks the class model and emits confidence, and a LOW contract demotes SPLIT/DEFLATE to `ADMIT_LOW_CONFIDENCE` plus an `advisory` field.
- `tools/test_ccr_pgo.py`: CCRPGO_PASS=16/16 (7 existing + 9 A3). `tools/test_gsd_mission_ccr_contract.py`: 5 passed, 0 failed.
- `vault/programs/ccr/stage3/a3/pgo-classes.json` (models + held-out metrics) and `vault/programs/ccr/stage3/a3/corpus.json` (125 content-free session rows).
- `vault/programs/ccr/evidence-v4-stage3-A3.md`: the per-class table and the V1 re-forecast.

## Headline
- **Corpus:** 119 Work Unit owner sessions + 6 V1 streams = 125 sessions, 165,297,659 processed tokens.
- **Classes:** bounded-code 80, long-textual 25, generic 11, lookup 9, multimodal 0.
- **V1 re-forecast:** the task now classifies as `lookup`. A lookup model fit only on pre-V1 data forecasts P50 93,545, which is +4.5 % on r2-CCR (89,475) and +14.5 % on r4-CCR (81,674). The old contract was 13.2x and 14.4x over.
- **OFF arm:** the same task's OFF runs (312-471k) sit outside that model's P80. The arm is a cost driver that the class does not encode.

## K7 (processed tokens, every session of this unit)
| item | estimate | actual |
|---|---:|---:|
| plan estimate (stage-3 plan row A3) | 1,500,000 | -- |
| packet budget / stop at 1.5x | 3,000,000 / 4,500,000 | -- |
| this worker session `2fd33286-45a0-4e79-918a-8a771c32b9d8` (GEX44 `~/.claude/projects/-home-kobii-missions-ccr-s3/`) | -- | 1,450,688 at call 29, before the evidence/receipt/commit turns. The final total is roughly 1.9M (about 6 more calls at about 75k context each). The coordinator should re-measure from the transcript |
| canary / probe sessions | 0 | 0 (no model calls were made, so the RAM admission did not apply. MemAvailable read 56,261,924 kB at the start) |

## LAPTOP_APPLY
None is required for correctness. To make the class models available to laptop admission once `gsd_mission` is wired (limit 3):

    cp vault/programs/ccr/stage3/a3/pgo-classes.json ~/.claude/ccr/state/pgo/pgo-classes.json
