# 02-03 SUMMARY -- PCC event seam (proof.py)

PLAN_BASE = bafb0fad (last 02-02 commit)

## Done
- 735170c0: `modules/gsd_x/goal/proof.py` (the only added file under `modules/gsd_x/goal`): NEW_TYPES, REQUIRED_FIELDS, `check_payload`, `ProofLedger`, `project_proofs`, `append_pcc` (CAS via `log.append(state.last_seq + 1, ...)`), registry entry `gsd_x/goal/proof` PLANNED with OWNER_QUEUE. `02-03-red.log` (FAIL V-PCC-ENVELOPE, proof absent, EXIT=1) and `02-03-green.log`: `GSDX_PCC_SEMANTICS_PASS=2/2`, `GSDX_PCC_REPLAY_PASS=23/23`. Liveness: `gate offenders: 0`.
- 62bdec3c: malformed raises only in proof.py, newer `v` goes to `ledger.unsupported`, writer refusals with a positive control, CAS `LostRace` with unchanged file set, export/restore round trip through `tools/gsd_x_goal.py` (`GSDX_PCC_SEMANTICS_PASS=8/8`).
- 56e3f3f8: `switch_on` / `inheritance_enabled` (call-time, typo means OFF), `V-PCC-SWITCH-PARSE`, `V-PCC-SWITCH-CALL-TIME`, `V-PCC-SWITCH-FRONTIER-INERT`. Final: `GSDX_PCC_SEMANTICS_PASS=10/10`, `GSDX_PCC_REPLAY_PASS=24/24`. Incumbents (`02-03-incumbent-quick.log`): RECONCILE 22/22, CONV 29/29, EPOCH 19/19, JUDGE 11/11, ENGINE_ID 14/14, SWEEP 14/14.

## Deviations
- `project_proofs` returns a `ProofLedger`, so the replay gate `V-PCC-REPLAY-IGNORE-NEW-TYPES-PCC` counts records across the four ledger lists (its 02-02 draft called `len()` on the ledger); fixed in the suite, not in the module.
- Gates 62bdec3c were green on first run; vacuity is covered by positive controls (valid append in WRITER-REFUSES and WRITER-CAS, valid payload in ENVELOPE).

## Open
- D43/D44 stay OPEN until the 02-05 invariant scanners and 02-06 evidence close them.
