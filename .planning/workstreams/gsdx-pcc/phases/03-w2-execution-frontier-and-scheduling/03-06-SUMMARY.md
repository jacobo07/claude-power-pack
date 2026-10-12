# 03-06 SUMMARY -- PARTIAL

Status: partial. Phase 3 is NOT verified; `03-VERIFICATION.md` was not written. DENOMINATOR rows not moved.

## Done
- Liveness: `frontier` declared PLANNED; `reachability.py` exit 0.
- Engine identity (G17): term now `engine:b650bc5355d1...`; before-value not captured. engine_identity 14/14.
- Owner option (b) applied (51eb4ad0): `V-PCC-ADDITIVE-ONLY` scoped to the Phase 2 git range 98609c4f..0fca7111, no hash re-pinned, control and empty-range sentinel. `GSDX_PCC_SEMANTICS_PASS=48/48`. STATE.md Decisions updated, blocker cleared.
- Drills m1, m2 KILLED.
- Regression of 03-06-regress.log was taken before option (b); semantics read 47/48 there and 48/48 afterwards (not re-captured in a committed log).

## Not done
- m3: CONTROL_INVALID. The clean copy read 38/39 (`V-FRONTIER-SWEEP-BOUND` failed). The in-place rerun to diagnose was killed by the harness for low memory and not restarted. Cause unknown.
- m4-m8: UNRUN.
- 03-EVIDENCE.md, 03-VERIFICATION.md, DENOMINATOR rows, STATE current_phase 4, ROADMAP tick: not done (drill gate unmet and a gate is red under load).
