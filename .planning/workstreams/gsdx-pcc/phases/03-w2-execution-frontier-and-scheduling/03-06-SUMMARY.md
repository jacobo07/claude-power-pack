# 03-06 SUMMARY

Status: complete. Phase 3 verified (`03-VERIFICATION.md`, status passed).

- Liveness: `frontier` declared PLANNED; `reachability.py` exit 0. Engine term now `engine:b650bc5355d1...` (before-value not captured).
- Owner option (b) (51eb4ad0): `V-PCC-ADDITIVE-ONLY` scoped to the Phase 2 git range; `GSDX_PCC_SEMANTICS_PASS=48/48` (03-06-semantics.log).
- Drills m1-m8 all KILLED. m1, m2 on the Windows plane (03-06-drill.log); m1-m8 on the Linux plane, valid controls (03-06-drill-gex44.log). The Windows m3 attempt was CONTROL_INVALID (control 38/39) and is not counted.
- Cause of that 38/39: the fixture gate could finish before the sweep pass decided again, so the pass harvested and stopped at 1. Fixed in 298ba2c6 (gates block on a release file) with the red case `V-FRONTIER-SWEEP-EARLY-FINISH`; every assertion unchanged.
- Frontier suite at 298ba2c6: `GSDX_FRONTIER_PASS=40/40` x9 on the Linux plane. Not completed on the laptop (two runs killed for low memory, not restarted).
- DENOMINATOR: D04-D09, D27, D28, D33, D34 DONE; D25, D26 stay OPEN (policy and ledger only; executed speculation and racing are Phase 4).