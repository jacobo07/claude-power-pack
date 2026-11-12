# S34K-C — certify the 16 oracle-covered KSR exacts under a NEW additive profile

Owner decision 2026-11-12 (session c84eb8e1): "1. rec" = the coordinator recommendation. That is a NEW additive
profile that meets all six S26C conditions. `ksr-v5r-s25stage` and the historical `ksr-v5r` stay byte-identical. The
other option, letting the existing profile read a second oracle file, would change a profile that 582 certificates rest
on, and was not chosen.

## Facts in hand (measured this session)
- S34K (m-25a9e4f31c97, t1 5f60926a..2e7f1c71) ran the unchanged `tools/s26c_oracle.py` on DOL sha 855e4ffe over 16 ids,
  using the frozen cohort `evidence/ascension/s34k/oc/cohort.json` (ids_sha256 e2f18501, committed 5f60926a before any
  oracle run). Result: MATCH 16/16. Controls: positive 300/300, shift4 16/16, byteflip 16/16. A2 pool 16/16; the S28K
  control 15/15. Judge AGREE.
- Coordinator independent check INDEP_S34K_PASS (`vault/programs/ascension/indep/indep_s34k.py`). It uses its own ELF
  and DOL readers. Stage target fn bytes = original DOL = the S30K candidate's own_fn_sha256, 16/16. The +4 negative
  differs 16/16. Sizes 8-92 B. Own relocation words are masked, not resolved.
- Blocker: `ksr_lane._oracle_verdicts()` reads the profile's `oracle` path, plus a `target_oracle_summary.json` beside it.
  The s25stage profile points at `evidence/ascension/s26c/target_oracle.jsonl` (2,837 rows, none of the 16), so
  target_proven is 0/16.
- `PROFILES` (modules/recon_fabric/ksr_lane.py:36) is an explicit additive table. `use_profile` refuses an unknown name or
  a stage-manifest sha mismatch. `use_subset` restricts a non-historical profile to a frozen id list, and every receipt
  carries the list's sha. `_RESERVED` keeps the historical paths for the historical profile.

## The six S26C conditions, mapped
1. Independent target oracle: S34K's oracle16.jsonl, plus the coordinator re-check above.
2. Original DOL bytes: DOL sha 855e4ffe, the same file the historical certifier binds.
3. Frozen pilot committed before the draw: the cohort, committed 5f60926a before any oracle run. The certify step
   reads it with `use_subset`.
4. Pre/post controls: the s30k_cert flow, unchanged in logic: pre and post control runs on the pinned capsule (CTRL_CAP).
5. A2 negatives: from the S34K pool `oc/a2_pool.json`, rebuilt from the main-capsule hash and size, 16/16 admissible.
6. Historical receipts unchanged: cert1-ksr 8,687 lines sha 02c80ae3, and the s25stage receipts (582) byte-identical
   before and after. Separate counters: new lane, cert and frontier dirs. Nothing is merged into any headline; that
   stays an Owner act.

## Phases (worker mission; the coordinator only judges)
- Phase 1: C0 freeze (cap 0.8M). Copy oracle16.jsonl byte-identical to
  `evidence/ascension/s34kc/oracle/target_oracle.jsonl`. S34K wrote NO summary, and the unchanged `_oracle_verdicts`
  (ksr_lane.py:433) returns {} without a `target_oracle_summary.json` beside the oracle that says `instrument: "OK"` and
  `stage_manifest_sha256` = 396511350197a137... So DERIVE that summary from S34K `oc/controls.json` + `oc/result.json`.
  It is "OK" only if those files record positive 300/300, shift4 16/16 and byteflip 16/16; otherwise "INSTRUMENT_FAIL"
  and stop. Bind the oracle, the summary, the cohort and the DOL by sha in `evidence/ascension/s34kc/freeze.json`.
  Commit before any profile code.
- Phase 2: C1 profile (cap 2.0M). Add `PROFILES["ksr-v5r-s25stage-oc"]`: the same stage, manifest and sha as s25stage,
  sym_rule addr, oracle = the C0 path, population_ids = the S34K cohort, own lane/cert/front/partial dirs,
  owner_turn = the Owner turn that approves this plan. Gate `tools/test_s34kc_profile.py`: the two existing entries
  are dict-equal to the ones pinned at the current HEAD; the new dirs are disjoint from `_RESERVED` and from s25stage;
  a wrong oracle sha is refused; a subset outside the cohort is refused. Planted mutants, each must be red.
- Phase 3: C2 certify (cap 2.5M). Run the s30k_cert flow with `use_profile("ksr-v5r-s25stage-oc")` and
  `use_subset(cohort)` through the UNCHANGED `certify.decide`: pre/post controls, A2 negatives from the S34K pool,
  receipts into the new cert dir only. Gate `tools/test_s34kc_certify.py`. Stop rule: any control violation, or a
  historical or s25stage receipt byte changed, means nothing is kept.
- Phase 4: C3 closeout (cap 0.7M). Re-run the 19 prior gates + the S34K gates + the two new gates into regress.txt.
  Write `checkpoint_s34kc.md` stating new canonical certificates per profile, by function identity.
- Total cap 6.0M processed, 0 fresh, USD 0, no push, no headline merge, no change to any existing profile.

## Coordinator judgment at the checkpoint
Re-run the new gates. Run `indep_v2` (the source found by content hash, flags from `ksr_lane.arms()[arm]`, compiled bytes
vs the original DOL) on EVERY new receipt; there are only 16, so no sampling. Check receipts sha 02c80ae3/8687 and the
s25stage receipts. If certificates land, that gives E5's precondition: MethodGraph learns TARGET_UNPROVEN ->
oracle_coverage_a2 as solved, and the 45 fallback exacts (q_fallback_cert) become the reuse candidate.

## Arming
A new mission record in t1 (like S27): arm --no-launch, then `authority --tokens 6M` bound to the Owner turn that
approves this plan, 4 cycles / 8 h. The KSR autopilot lane stays PARKED while this runs, so there is one writer. It is
un-parked only after the judgment.
Rollback: revert the t1 commits of this mission. The existing profiles and receipts are never touched.
