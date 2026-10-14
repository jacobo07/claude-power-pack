# 05-2 VALIDATION

| Requirement | Gate(s) | Suite / summary line | Plane |
|---|---|---|---|
| N01 revocation, bytes unchanged | V-TRUST-REVOKED-INVALID-BYTES-UNCHANGED, -CASCADES-LINEAGE | tools/test_gsd_x_goal_trust.py GSDX_TRUST_PASS | Windows |
| N02 lineage | V-TRUST-LINEAGE-FIELD, V-TRUST-AUTHORITY-FIELD | same | Windows |
| N05 monotonic | V-TRUST-MONOTONIC-REFUSED | same | Windows |
| N23 ledger seed | V-TRUST-LEDGER-SEED | same | Windows |
| N16 forgery >= 8 | V-FORGERY-F1..F12 + controls, V-FORGERY-COUNT | tools/test_gsd_x_goal_trust_forgery.py GSDX_TRUST_FORGERY_PASS | Windows |
| N17 environment | V-TRUST-ENV-* | tools/test_gsd_x_goal_trust_env.py GSDX_TRUST_ENV_PASS | Windows; Linux leg = coordinator (`gsdx_env_equiv.py --vector/--live`) |
| N19 platform vs portability | V-TRUST-PLANE-FIELD, V-TRUST-PORTABILITY-* | same | Windows (a PORTABILITY claim needs the coordinator's second plane) |
| D11 wiring | V-ALG-* | tools/test_gsd_x_goal_trust_algebra.py GSDX_TRUST_ALGEBRA_PASS | Windows |
| Done-gate registry | V-DONE-* | tools/test_gsdx_pcc_done.py GSDX_PCC_DONE_SELFTEST_PASS | Windows |
| Regression | semantics 48, replay 28, frontier 40, invalidation 26, judge_validate 11, hermetic 5 | existing suites | Windows |
| Mutation | drills t1..t7 | tools/mutation_drill.py | Windows (isolated copy) |

Each new suite prints `PASS <gate>` / `FAIL <gate>` lines (the mutation_drill format), a `*_PASS=n/m threshold=n/m` summary, and survives a gate body raising.
Instrument check (could it return the other answer?): every refusal has a paired control that is admitted; every RED is run and seen failing before GREEN; each drill has a control.
