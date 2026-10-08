# CP50-prerequisite tranche -- ledger

Plan by plan, one lease and one receipt each. FULL_WSR is never a budget. CP50 itself waits for ce-lifecycle-v WU-5.

## Authority
- 2026-10-08 Owner "y y": fund the tranche, ~4.2M expected, 5.0M ceiling (R1 REFORECAST).
- 2026-10-08 Owner "y": ceiling raised to ~6.8M after P5's failed lease, to finish the minimal path to CP50
  (Phase 3a seam and Phase 2 GEX44 leg).

## Spend (measured from worker transcripts, usage deduplicated by message.id)
| lease | mission | result | processed |
|---|---|---|---|
| P5 | m-6d6bb4cef637 | FAILED, unpinned premise | 1,412,234 |
| P5b | m-bc6473bfe5bd | Phase 5 done, CENSUS_DRILL 4/4 | 1,015,198 |
| P6 | m-be59d97fa311 | Phase 6 done after main-pane fix, ROUTER_DRILL 7/7 | 1,372,775 |
| P7G0 | m-302d70eabd59 | armed, stop 1.2M | pending |
| total so far | | | 3,800,207 |

Remaining minimal path: Phase 3a seam (R1 expected 737,010), Phase 2 GEX44 leg (R1 expected 982,680; gated by the GAP-1
runner A/A gate, GAP-10 RATIFIED 2026-10-03).
