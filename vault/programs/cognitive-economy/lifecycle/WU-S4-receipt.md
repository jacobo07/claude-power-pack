# WU-S4 receipt -- predictive lease edge + physical-call pricing

Status: DONE (code by worker m-f3ad13bfd9bb; proof re-run + commit + receipt by coordinator 3339c6c2, zero model work)

## Gates (re-run by the coordinator in a child process; logs in scratchpad s4/)
- test_session_budget_guard.py SBG_PASS=20/20.
  - V-LIFE-EDGE-BEFORE-STOP: the first edge is at call 5, 322,500 < stop 500,000 (WU-1H3 replay).
  - Also passing: V-LIFE-EDGE-QUIET-EARLY, V-LIFE-EDGE-KILL, V-LIFE-EDGE-MUTANT-RED.
- test_route_estimator.py EST_PASS=9/9.
  - V-EST-PHYSICAL-1H4: 7 declared calls -> 17 physical -> 550,545 vs 442,155 actual (+24%).
  - V-EST-PHYSICAL-CONTROL passes.
- ADM 43/43, HALT 16/0, LIFE 6/0.

## Economics of this unit
- 528,376 tokens, 26 physical calls for 6 declared steps (4.3x, the worst ratio so far).
- The calls wall (26 > 1.5 x 16) denied the receipt write. It was containment working, not a code fault.

## Faults found (inputs to WU-S5)
- F1: gsd_mission marked the mission COMPLETED although no receipt existed and nothing was committed (the worker said
  so in its result). halt_continue never ran because the state was not HALTED. Missing receipt != success.
- F2: the worker wrote the patch to <root>/install/ instead of lifecycle/install/. The coordinator moved it.
- F3: the calls wall left no closeout allowance for the receipt, yet the token breaker has 4 closeout calls.

## Install
install/L2-edge.patch, sha256 26299356086712843A423E7AF9DC9CF953A3064A3899907742AB2D1EF8A6E3E3, base e86cafc4.
Not installed: the combined install follows WU-S5.
