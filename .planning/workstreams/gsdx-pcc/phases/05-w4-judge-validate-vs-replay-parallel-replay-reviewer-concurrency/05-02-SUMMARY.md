# 05-02 SUMMARY -- Bounded parallel replay (D16)

New `modules/gsd_x/goal/replay.py`: `replay_bound = min(frontier.bound, memory_bound(free RAM), GSDX_REPLAY_MAX)`,
1 when `GSDX_FRONTIER` is off; `run_bounded` admits two gates together only when `proof.independent` holds for their
`frontier.gate_unit`s, places results by index, and joins every started call before returning.
`judge.py` now collects pin-checked obligations into `pending`, replays them through `run_bounded`, and keeps the
receipt order. The five goal-mutation-suite anchor lines are textually intact (`        if moved:` still at 8 spaces).

## Gates (laptop plane)
- `GSDX_REPLAY_PARALLEL_PASS=14/14  threshold=14/14` (RED 12/14 in logs/05-02-red.log against the serial judge; green in 05-02-green.log)
- `GSDX_JUDGE_PASS=11/11` and `GSDX_JUDGE_VALIDATE_PASS=11/11` after the wiring (05-02-judge-suite.log, 05-02-validate-suite.log)

## Drills (laptop plane, control valid)
| id | mutant | verdict |
|----|--------|---------|
| d4 | run_bounded ignores independence | KILLED (V-RP-RESOURCE-SERIALISES) |
| d5 | memory_bound returns 4 below the floor | KILLED (V-RP-MEMORY-LOWERS) |

## Deviations
- Fixture bug found in the first RED run (set_budget needs `last_seq + 1`); fixed before the real RED.
- `tools/test_gsd_x_goal_mutation.py` UNRUN on the laptop (mutates live files); it needs the Linux plane.
- Default posture is ECONOMY, so existing goals replay serially exactly as before.
