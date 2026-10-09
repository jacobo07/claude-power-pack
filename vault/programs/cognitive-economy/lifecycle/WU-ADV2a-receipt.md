# WU-ADV2a receipt -- Status: PARTIAL
- Part 1 DONE: GoalLedger.declare_cap(approval_id=) consume-once (salvage patch failed to apply; re-implemented by hand).
- Part 2 DONE: admit_route takes min(breaker remaining, halt_authority(rec)); no goal/unmeasurable = unchanged.
- tools/test_advance.py 4/4: V-LIFE-APPROVAL-ONCE (+different-id control), V-LIFE-ADMIT-GOAL-DEFER, V-LIFE-ADMIT-NO-GOAL-UNCHANGED.
- Mutants killed: consumed-check dropped (APPROVAL-ONCE FAIL); goal remaining not passed (ADMIT-GOAL-DEFER FAIL).
- test_halt_continues.py 19/0 (run() now admits with an injected halt_authority, needed since admission is goal-aware).
- test_mission_steward.py 18/18.
- NOT RUN (lease edge): ADM 43/43 suite, MC baseline suite. Run them before trusting this.
- NOT DONE: arm-chain of WU-ADV2b (needs remaining - open >= 700,000 measured; unmeasured this epoch).
- Next: run the ADM and MC suites, then arm WU-ADV2b: arm-chain --parallel-unit lc3-WU-ADV2b, packet WU-ADV2b.md, route route-WU-ADV2b.json, token-estimate 700000.
