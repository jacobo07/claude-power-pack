# CP50-prerequisite tranche -- ledger

Plan by plan, one lease and one receipt each. FULL_WSR is never a budget. CP50 itself waits for the ce-lifecycle
`lifecycle` sweep stage. That stage was WU-5 in ce-lifecycle-v. The goal moved v -> v2 -> v3, so it is now WU-CLOSE (L9) of
goal ce-lifecycle-v3 (worktree Apps\pp-ce-lifecycle-v3, RESUMPTION.md). Re-pointed 2026-10-09 by Owner "sí". At that time:
WU-S1 DONE, L1 INSTALLED, WU-ADV IN PROGRESS, no `lifecycle` stage in live tools/.
Correction, same day: the successor stage that WU-5 described is WU-ADV(2), and WU-CLOSE is the last unit of plan v3 S6
(ADV2 -> 1C -> 1D -> INST -> TRIP -> FLOOR -> GEX -> CLOSE, ~5.5M by the plan). Owner option A funded S0-S5 + S7, not S6.
Measured 13:15: goal ce-lifecycle-v3 remaining 2,934,095, open 396,885. WU-S3 epoch 1 (m-4ace4480521c) HALTED at 975,091
against its 950,000 stop. It was renewed by the chain as m-a1a658f26a16 (PREPARED), with one live writer, the sweep.
CP50 is therefore blocked on S2-S5 and then on S6 funding (the plan's option B), not on any action this pane can take.
2026-10-09 Owner "autorizo" to the question "ampliar el goal ce-lifecycle-v3 hasta unos 8,5M en total": cap 4,295,976 ->
8,500,000 (+4,204,024). The raise needs `goal-declare --owner`, which asks for the goal id on an interactive terminal, so
the Owner types it. Caveat stated to the Owner: the plan's own option B reads as an EXTENSION of ~8.5M (S1-S7 ~4.2M + S6
~5.5M). At an 8.5M total, S6 may still end in WAITING_FOR_AUTHORITY, now with an EAC from the corrected estimator.
APPLIED 2026-10-09: the Owner ran raise-cap-v3.ps1 in a plain PowerShell window. A `!` run had failed on EOF at the
confirmation prompt and changed nothing. Verified by an independent goal-status: cap 8,500,000, used 3,596,856,
settled 3,226,721, open 370,135, remaining 4,903,144. At that point S1-S3 were COMPLETED and S4 RUNNING (m-f3ad13bfd9bb).

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
| P2a | m-f501c31d6523 | Phase 2 local half, P2A_DRILL 7/7; committed zero-model by the main pane (1f72401); OVER its 1.85M stop by 546k | 2,396,336 |
| total | | | 9,881,933 |

**CEILING EXCEEDED: 7.49M against ~6.8M.** No further lease is funded until the Owner decides.
- 2026-10-08 Owner "fund it" + "b": funded P2a ONLY (local half, no send), on top of the exceeded ceiling. The tranche now
  stands at 9.88M. P2b (send, wait, judge) is not funded.
- 2026-10-09 Owner "fund it": P2b funded (one A/A job, BUILD=reproduce-20261008T211412Z only, from the main pane, no
  worker). No ceiling was named; the main pane set its own: 1.0M of session tokens.
- P2b job 1 ksrmb-20261009-072932 FAILED INVALID_CUSTODY on GEX44 (seq-qualified entity); fixed in recon 1c2b89f.
- 2026-10-09 Owner "si": job 2 ksrmb-20261009-075610 (last RF slot, cap 2/2) compiled 41/41, but FAILED TOOL_FAILURE
  (OUT 20 MB ceiling vs 88 MB of .diff.json) with no receipt. Unadmitted judge, md5-verified: 40/40 agree, mutant
  caught, 40/40 objects byte-identical; objdiff C3 unmeasured. P2b total main pane 16,832,965 over 65 calls.
  See P2b-receipt.md.
- 2026-10-09 Owner "go ahead": runner trims diff.json (recon cd412ed, judge rev 7377ff0f). Owner "autorizo un tercer
  cupo": RF cap 2 -> 3 (2b12075). Job 3 ksrmb-20261009-090602: runner PASS, ingested, **AA_GATE PASS (admissible)**,
  C1-C5 all PASS. P2b final main-pane spend: 27,600,379 over 98 calls. Phase 2 GEX44 leg: DONE.
- MAIN-PANE spend, counted separately from the worker table above (session ce1c3a41, deduplicated by message.id):
  10,812,318 over 64 calls before "fund it" (P2a close, meter, D11 step 1), and 12,177,177 over 49 calls for P2b,
  which is 12x its self-set 1.0M ceiling. A main-pane call costs ~250k here; a ceiling must be projected from that
  measured floor, never guessed.
- P2a meter: worker f4f23b86, 14 model calls, 56,399 output tokens. The same script reproduced P3a's 2,353,284 over 16
  calls exactly, as a control. Even with the guard's closeout calls the worker did not commit; the main pane committed.

Pattern: the dossier leases cost 1.02M / 1.37M / 1.33M / 2.35M; per model call ~125-147k. R1's per-phase figures
undercount by ~1.4-3.2x. Two of four leases ran past their stop (P7G0 +132k, P3a +703k). Investigated 2026-10-08: the in-session
guard (hooks/session_budget_guard.js) DID deny at the stop (P3a at 1,708,171); the overshoot is its closeout allowance
(up to 4 calls at ~160k each) spent on the receipt and commit the worker had not yet written. Not a defect. Rule for the
next lease: route stop = intended ceiling - ~0.65M, warn one call earlier, and the packet goes straight to receipt +
commit at the warn advisory; token_estimate = stop / 2 (supervisor breaker ratio is 2.0).

Remaining minimal path: Phase 2 GEX44 leg = the GAP-1 canonical runner + its A/A gate (GAP-10 RATIFIED 2026-10-03,
GAP-1 APPROVED 2026-10-03). Not funded.
