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
| P7G0 | m-302d70eabd59 | G0 freeze done, G0_DRILL 6/6 (e3b0b82); OVER its 1.2M stop | 1,332,106 |
| P3a | m-789229da3a6f | Phase 3a seam done, SEAM_DRILL 8/8 (dcd9178); OVER its 1.65M stop by 703k | 2,353,284 |
| total | | | 7,485,597 |

**CEILING EXCEEDED: 7.49M against ~6.8M.** No further lease is funded until the Owner decides.

Pattern: the dossier leases cost 1.02M / 1.37M / 1.33M / 2.35M; per model call ~125-147k. R1's per-phase figures
undercount by ~1.4-3.2x. Two of four leases ran past their hard stop (P7G0 +132k, P3a +703k): the envelope's stop did
not halt a running worker -- a control-plane defect to investigate before the next lease.

Remaining minimal path: Phase 2 GEX44 leg = the GAP-1 canonical runner + its A/A gate (GAP-10 RATIFIED 2026-10-03,
GAP-1 APPROVED 2026-10-03). Not funded.
