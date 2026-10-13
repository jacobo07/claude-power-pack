# WU-P4 receipt -- DONE
mission: id on the rehydration card is not visible to the worker (follows m-84c6e0072a10, Phase 3 DONE) | branch gsdx/pcc | nothing pushed
plans: Part A (plan) before 7d8fe6fa | 04-01 7d8fe6fa | 04-02 f732c4d7 | 04-03 4e14e7fb | 04-04 921784c3 | 04-05 b65b533e | verify+STATE+ROADMAP 59721db5
gates (verbatim, all Windows plane, logs/04-verify-*.log):
GSDX_INVALIDATION_PASS=26/26  threshold=26/26
GSDX_PCC_REPLAY_PASS=28/28  threshold=28/28
GSDX_PCC_SEMANTICS_PASS=48/48  threshold=48/48
GSDX_FRONTIER_PASS=40/40  threshold=40/40   (full suite, one laptop run)
liveness `modules/liveness/reachability.py` exit 0; 18 other goal suites green at baseline counts (04-05-suite-*.log); nothing ran on the Linux plane.
drills (Windows plane, valid clean-copy controls): d1 d2 d3 d4 d5 d6 d7 d8 all KILLED.
DENOMINATOR moved to DONE: D01 D10 D12 D13 D14 D20 D39 D45 R02 R12, and D23 (substrate only). D11 stays OPEN (PARTIAL, pure algebra). D24 stays OPEN (substrate, watcher is Phase 9).
deviations: inherited set derived from the log via rc.inherited_for(ctx), Context gains no field | Inh fixture got a `combine` knob | sweep emits the verification-set line only when events were recorded | d5 mutates the `unknown:` clause of tree_equal, not the whole body | candidate and inherit declared PLANNED in liveness (engine entrance is outside the scanner's aperture) | judge.py untouched, so closure is necessary-not-sufficient.
burn: end of Part A 3.3M tokens / 38 calls; end of run 36,389,469 tokens / 307 calls (session-budget state file; target 65M not reached).
open points: (1) UNRUN `tools/test_gsd_x_goal_mutation.py`: laptop timeout at 270 s, the kill left judge.py mutated (restored by git checkout, diff empty); recorded as OWNER DECISION NEEDED in STATE.md, pick = coordinator runs it on the Linux plane (GEX44). (2) No sweep path records `candidate.promoted` yet (D23/D24). (3) No engine path evaluates a non-AND claim via combine_states (D11).
HANDOFF choice: `done`, not PARTIAL. Every done-gate item holds, and the mutation suite is a coordinator Linux-plane item that Phase 4 did not touch; it is not hidden.
phase 5 size estimate: L (about 5-6 plans): judge VALIDATE vs REPLAY, bounded parallel replay, reviewer concurrency; it edits judge.py, the one file Phase 4 left alone, so run the mutation suite on the Linux plane first.
HANDOFF NOTE: WU-P4 done -- Phase 5 (W4 judge VALIDATE vs REPLAY) ready to compile
