# WU-D9 -- Ph9 synthesis probe (gated by D2 evidence)

Common brief: `D28-BRIEF.md`. Plan Ph9 ("only if Ph2 shows flag/codegen classes").

Step 0 (gate): read PP `evidence/d28/d2/near_match.json`. If no PARTIAL function has class FLAG/CODEGEN (or
SCHEDULING) with <= 16 insns, write the receipt `Status: DONE` with the line `NOT_ADMITTED: <counts per class>`
(NO_WORK is a result) and stop. If D8 is BLOCKED_HUMAN on jobs, this unit needs a job too: receipt
`Status: BLOCKED_HUMAN` naming "Owner: approve one GEX44 job for D28 Ph9" and stop.

If admitted and a job is approved:
1. For each admitted function (<= 16 insns): enumerate bounded source variants (operand order, temporaries,
   signedness, explicit casts; at most 32 variants per function) deterministically from its m2c output.
2. One job with all variants + 3 donor controls, W12 route, JOBS.md row BEFORE send.
3. Per function: first MATCHing variant (or none) and which variant dimension closed it. `synthesis.json`.
Receipt: `WU-D9-receipt.md`.
