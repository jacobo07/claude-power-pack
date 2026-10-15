# WU-R1 -- judge contract, supersede row, l0_path coupling fix, discriminative control fixture, D12 negative knowledge

Plan: `vault/plans/recon-factory-locality-routing-2026-10-15.md` sections 2, 3, 9, 10 (Owner approved 2026-10-15 "y").
Common brief: `D28-BRIEF.md`. Budget: <= 2.5M; stop and write the receipt at 2.2M.

Facts already established (do not re-derive): candidate.py oracle receives obj bytes, symbol, entity, asm unit only
(:516); producer/variant/strategy/source are copied into the row after the verdict (:452-454); L0 is a locator
(start, insns, bytes_sha256), read via `_P["l0"]` (:52, :225-235) chosen by env KSR_CAPSULE_PROFILE. D8v2's 12 MATCH
live only in `evidence/d28/d8/rejudge_l0.json` because the ledger refused them (profile L0 lacked the rows).

Steps (wt_tennis_rf D/gex44 unless noted):
1. Judge contract `D/gex44/JUDGE_CONTRACT.md`: may know (target locator, DOL words, DTK asm operands, compiler sha,
   preset), must not know before the verdict (producer, backend, arm, variant, strategy, model, cost), output fields,
   provenance. Test `test_judge_contract.py`: fails if `oracle`/`oracle2` signature gains any forbidden name, or if the
   verdict path reads a forbidden row field before the verdict is computed (inspect + a runtime spy). Mutation drill:
   add `producer` to oracle2's args -> red.
2. Coupling fix: `judge_tree` and `cmd_judge` take `--l0` explicitly; when a unit's entity is absent from the profile L0
   and no `--l0` was given, refuse with `L0_ROW_ABSENT` naming the entity (was a silent ORACLE_REFUSED). Test both.
3. Supersede: append-only row `kind: "supersede"` {supersedes: candidate_id, reason, evidence (file + sha256), verdict
   recomputed by the same oracle with the batch L0}. Ledger readers fold supersede rows. Apply it to D8v2's 12 MATCH by
   recomputing (not copying) from the returned objects of job ksrmb-20261014-114911. Canonical MATCH must read 27.
4. Control fixture `D/gex44/control_fixture.py`: from a sealed MATCH donor that reads a struct field, emit two sources:
   correct width (predicted MATCH) and u8->u32 (predicted non-MATCH, diff at that load). Add a pure rule
   `discriminative(pred_correct, pred_wrong)` = predictions differ; a control whose arms are predicted equal is labelled
   NON_DISCRIMINATIVE and not admitted. The two sources are judged later in the pilot's job (WU-P1); here only build +
   local compile check if the toolchain is local, else mark PENDING_JOB.
5. PP vault (pathspec commit in PP): `vault/programs/tennis-rf/evidence/d28/d12/TRANSFER.md` = the T0/T1/T2 matrix of plan
   section 3 with sample sizes and the Wilson 95% upper bound for 0/91; D12c wrong-width control recorded
   NON_DISCRIMINATIVE; the exact scoped negative statement ("under tested Tennis D12 helper/layout interventions, no
   cross-function held-out closure beyond targeted helper effects; T1 for helper families UNMEASURED").

Limits: no GEX44 job, no model calls on functions, no capsule edit. The oracle's verdict logic does not change.
Done-check: all new tests exit 0 + the mutation drill goes red; ledger fold reports 27 canonical MATCH.
Receipt `WU-R1-receipt.md`: contract, test output lines, supersede rows written (ids), fixture state, commits.
