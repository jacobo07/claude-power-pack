Status: DONE_WITH_LIMITS (closed by hand in the coordinator pane, Owner option 1, 2026-10-14; residuals exhausted)

## Result (`evidence/d28/d8/tournament.json`)
- Job 5 `ksrmb-20261014-114911` (build candidate-20261014T114813Z, capsule cap1-fee7b09f053d, CERTIFY READY
  e33fd892...): 31 units = 14 arm-B fns x O4p+O2 + 3 donors. JOBS.md row 5 written before the send. Repatriated
  (tree ee183b7d...), judged. Donors 3/3 MATCH, so the job is valid. Job 6 UNUSED.
- Arm B (reused ctx_run1 m2c + Tennis header, 0 model calls per fn), O4p: **12/14 MATCH, Wilson95 0.601-0.960**.
  Split by size: 1-insn fns (`blr`, one shared byte hash) 8/8; fns of 2+ insns **4/6 (0.300-0.903)**. Misses:
  fn_80223804 (4 insns, SIZE 5 vs 4) and fn_8027AA7C (23 insns, SIZE 22 vs 23). O2 never beats O4p.
- Over the whole draw: 12/40 = 0.300 (0.181-0.454). Arm B only reaches the 14 lint-clean fns. The other 26
  (distance 2-3) have no candidate under any arm.
- Versus arm A, W12 12/22 (0.347-0.731): the intervals overlap. Without the trivial fns, B's 4/6 does not separate
  from A. No arm ranking is claimed.
- D: EMPTY/INCONCLUSIVE (no motif->C emitter exists). E: EMPTY/INCONCLUSIVE (D6 certified 0 facts, D4 ranking is
  degree-driven). F = B.
- Tokens: the D8v2 leases sum to 3,215,410 (L26+L27+L28 at handoff), so each O4p MATCH costs at least 267,951.
  That is coordination/tooling spend, not generation, and it excludes this closing session.

## Instrument defect found and how it was handled
- `candidate.py judge` calls oracle2 against the PROFILE L0 (`w10/factory/corpus/tennis_L0.jsonl`, 25 rows = the
  W12 draw). Every held-out unit came back `ORACLE_REFUSED "L0 row ... is None"`, i.e. 31 ledger rows read 3 MATCH,
  28 PARTIAL/oracle_disagreement. Those rows stay as written: the ledger is an append-only chain with no supersede
  path. The ledger's "3 MATCH" is the instrument's blindness, not a result.
- `evidence/d28/d8/rejudge_l0.py` re-ran oracle2 + classify_unit on the same returned, re-hashed objects with the
  batch's own L0 (`w8/inputs/tennis_L0.jsonl`) -> `rejudge_l0.json`. That run is the judgment used above.
- The profile L0 was add-merged with the 14 held-out rows (backup `tennis_L0.jsonl.pre-d8v2`, 25 -> 39 rows) so
  D9/D12b do not repeat this. The judge should read the batch L0 or refuse; it should not silently refuse per unit.
  A tooling fix is still owed in wt_tennis_rf.
- Correction to the earlier PARTIAL receipt: "lint-clean 14, all size_insns 1" was wrong. The retail L0 gives
  1/2/4/16/22/22/23 insns. 8 are 1 insn.

## Env needed to reproduce
`KSR_CAPSULE_PROFILE=tennis`, `MATCH_ACCEL_GEX44=<wst_tennis>\w10\F` (without it, stage resolves the Resort CURRENT
and refuses TARGET_NOT_IN_CAPSULE), cwd = `wt_tennis_rf\tools\wros\binary\decomp\gex44`. Steps: `stage.py build
--mode candidate --capsule CURRENT --units w8\units\job5.jsonl`, `certify`, JOBS row, `send`, `wait`,
`repatriate.py <job>`, `candidate.py judge <job>`. Units come from `w8\mk_units.py` plus `w12\sel.py`.

## Plan delta
MDG 16 (reuse tournament): only B is measurable. D and E have no producer, so the tournament cannot rank arms.
MDG 19: B transfers to held-out lint-clean fns at a rate consistent with W12. Its reach is capped by lint
eligibility (14/40). That cap is the binding constraint, not match quality.
