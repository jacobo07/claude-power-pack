# 03-04 SUMMARY: write authority and sweep dispatch of N independent gate epochs

Status: DONE. RED `03-04-red.log` 27/34 against HEAD epoch.py + sweep.py (BEGIN-REFUSES, UNSAFE-WRITES, BEGIN-DERIVES, BEGIN-ADMITS, LOSTRACE fail with `TypeError: begin() got an unexpected keyword argument 'unit'`; SWEEP-N and SWEEP-BOUND fail with 1 dispatch). GREEN `03-04-green.log`: `GSDX_FRONTIER_PASS=34/34  threshold=34/34` (suite takes ~180 s: six real sweeps with 6 s gates, every one awaited).

Delivered:
- `epoch.begin(..., unit=None)`: the unit is re-derived from the log (`frontier.gate_unit`) and compared; a mismatch is refused ("unit does not match derived"). A second open epoch is admitted only if the switch is on, a unit was given, every open epoch stored one, and every pair is independent; otherwise the original refusal, byte for byte. Legacy specs gain no key.
- `sweep_goal`: the dispatch moved to `_start_gate`; after the first dispatch, with bound > 1 and the switch on, up to bound-1 further gates are decided on a fresh projection (`decide_now`), each re-checked by `begin`. LostRace/EpochError end the pass and are recorded in `acted`. The first epoch also carries its unit when bound > 1 (without it a second could never be admitted).

Measured: WALL_CLOCK dispatched 3 of 3, ECONOMY 1; `max_parallel: 2` under WALL_CLOCK gave 2; 5 ready under WALL_CLOCK gave 4; BALANCED gave 2; all gates completed and all obligations SATISFIED after draining.

Deviations / notes:
- Dry-run reports only the first "would run": a dry run writes nothing, so there is no projection to decide the next one from.
- A gate that ends before the pass finishes is harvested by the next pass rather than letting this pass start another (the second decision is HARVEST); the sweep gates use 6 s gates so the pass completes while all run. Measured once at 2.5 s: the 5-ready case dispatched 3, not 4.
- `test_gsd_x_goal_claude_providers.py` read 19/20 once during a loaded run and 20/20 on the immediate rerun; it does not touch the changed code paths. Recorded, not explained.
- `test_gsd_x_goal_mutation.py` refuses to run on modified targets; it is rerun after this commit.
