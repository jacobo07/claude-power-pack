# D2 -- P3b-2 control drift: Owner decision

Decision: (a) ACCEPT and re-judge the 5 sealed PROVEN rows through the bundle path.
Authority: Owner 2026-10-10, pane 42ce1ae6: "do the option with the highest reward" (delegated choice between a and b).

Why (a): the same evidence as (b) for less cost.
- The P3b-2 job already builds all 294 units (5 sealed + 289 donors). The local split-judge re-judges the 5 under the
  CURRENT match.py, which is the revalidation (b) asks for. 03b-01-SUMMARY.md step 10 already plans "the 5 sealed
  reconfirmed via the bundle path".
- (b) adds a separate revalidation lease (~1-2M) and may cost one of the 2 RF Phase 3 GEX44 slots.

Binding conditions for W7:
1. A sealed row whose bundle does not verify under the current match.py is REFUSED and named. It is never kept PROVEN
   on its old seal (drift=["match_py"] at SB.impact time, recon ac1f1ae).
2. The post-check is: SRC PROVEN after promote = exactly the set whose bundles verified, with each of the 5 reported
   individually (reconfirmed / refused). Do not use "5 + accepted donors".
3. Run SB.impact(load_store()) before promote() and attach its drift list to the W7 receipt.

## Outcome (appended 2026-10-10 by PP main pane a5308810; text above unchanged)

The Owner gave the same answer ("a") in main pane a5308810. **That pane already executed P3b-2**, so W7 is
**VERIFY-ONLY** (Owner 2026-10-10, "do the 5 items"; see the CHAIN.md W7 row). W7 must not send the remaining RF
Phase 3 job (2 of 2), and must not re-register, re-write bundles or re-promote.

How the binding conditions above were met:
- Job 1 of 2 ksrmb-20261009-214006: PASS, 294 units, custody ok, runner_lib 7377ff0f, task_sha 5bd8add8; repatriated
  tree 6f7b2c9d. RF_CURRENT_PHASE 3 = recon a5d57a0.
- register_src added=289 refused=0; assemble bundles=294 refused=0 (condition 1: no sealed row refused).
- Condition 3: SB.impact before promote, per sealed row: main:801A2CC0, main:8020EAD4, main:8026BE34, main:802B21A4,
  main:803571D8 each drift=[match_py, src_registry], bundle_verifies=True. Log: PP gen3/P3b2-steps6-8.log.
- Condition 2: promote 294; SRC PROVEN after = 294 = exactly the verified set; all 5 sealed RECONFIRMED (SEALED_LOST=[]);
  PROVEN_VIA_BUNDLE=294/294; POST_IMPACT_DRIFTING=0; P3B2_CHECK=PASS; ledger_sha256 0c247d0d816e5060...
- Evidence: PP vault/programs/cognitive-economy/gen3/P3B-RESUMPTION.md, RECON-FACTORY-HANDOFF-2026-10-10.md.
  Commits PP bdbe4f35, 00493bcb, 33516abe, 84d0a107.

W7 (E8) now verifies this state read-only and judges the lineage: whether P3b-2's spend landed on P3b/L2 = rf-p3b2.
