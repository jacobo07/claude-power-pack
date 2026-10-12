# WU-D10 -- Ph10 W13 compiled from evidence + frontiers; opens W8b (laptop light + GEX44 reads)

Common brief: `D28-BRIEF.md`. Plan Ph10 and section 7, MDG 20, 21, 22. Inputs: every D-unit receipt (D1c..D7),
`evidence/d28/`, MEASURE.md, JOBS.md, `goal-lineage --goal tennis-rf` for spend.

Steps:
1. `WU-W13.md` (a PACKET, not run here): the next production wave compiled from evidence: which functions (by
   distance class from D3 and the D6/D7 unlock), which certified facts it relies on, expected MATCH rate from
   measured rates only, job count needed (jobs 5+ are NOT approved: state the approval it needs), token estimate
   with its basis. Front matter per D1c (`class:` and any `pre:` deterministic steps).
2. Frontiers in `vault/plans/tennis-frontiers-2026-10-13.md`: 7-day, 72-hour and theoretical (plan section 7), each
   with the measured inputs (model-needed fraction, verification rate, autonomous rate, exception queue) replacing
   the plan's preliminary numbers, and what is still UNKNOWN. Tag figures M / D / H.
3. Write `vault/programs/tennis-rf/W8B-READY.md`: the inputs W8b must use beyond its packet (D-unit measurements,
   the frontiers file, W13 packet path), so the existing W8b unit (`WU-W8b.md`) reforecasts with D28 evidence.
   This file is what lets the chain arm W8b: write it last, after the receipt checks below pass.
4. Check every D-unit receipt is DONE via `tools/receipt_judge.py` (the certified reading); a non-DONE one is named
   in your receipt and W8B-READY says which inputs are missing.
Done-check: WU-W13.md, the frontiers file and W8B-READY.md exist and are committed (pathspec).
Receipt: `WU-D10-receipt.md`.
