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
