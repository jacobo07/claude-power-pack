# 05-01 SUMMARY -- Judge VALIDATE vs REPLAY (D15)

Commit 970ea212. `judge.py` gains `_validate`: an inherited certificate is re-derived through `inherit.plan`
(which never reads the `proof.inherited` event, so a forged event cannot skip a gate). Any doubt replays.

## Gates (laptop plane)
- `GSDX_JUDGE_VALIDATE_PASS=11/11  threshold=11/11` (logs/05-01-green.log; RED in 05-01-red.log)
- `JUDGE` suite 11/11 (logs/05-01-judge-suite.log)

## Drills
| id | mutant | verdict | plane |
|----|--------|---------|-------|
| d1 | judge.py: skip the INHERIT-action check | KILLED (V-JV-FORGED-EVENT-REPLAYS), control valid | laptop |
| d2 | inherit.py: `blocked = ''` | KILLED (V-JV-DOUBT-REPLAYS), control valid | laptop |
| d3 | judge.py: `if moved and False:` | UNRUN -- reaped for low memory, not retried | coordinator Linux plane |

## Deviation
- Harness bug found in RED: the control fixture overwrote the marker env var; fixed by building it after the first fixture closed.
