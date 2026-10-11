# W5a receipt
Status: DONE

Slice done: steps 1, 2, 4 on 12 functions; step 3 (the GEX44 job) NOT run, BLOCKED_ORACLE (W3b: no Tennis oracle). Zero jobs, zero compiles, JOBS.md untouched, no code in wt_tennis_rf.
Commits: PP only (vault/programs/tennis-rf: MEASURE.md, evidence/w5a/*, KNOWLEDGE.md, this receipt).

| layer | closed (candidate produced) | verified | tokens per verified fn |
|---|---|---|---|
| NO_WORK | 0 | 0 | n/a |
| Resort donor | 0 (donor_proven empty for all 12) | 0 | n/a |
| det type repair | 10 (6 clean as-is; 4 of 6 few lost all `?` via call-site-inferred prototypes) | 0 | UNKNOWN |
| model | 2 (fn_80254440, fn_80252F34; PMN in records) | 0 | UNKNOWN |

- PROVEN: draw seed 20261011 and list in MEASURE.md before work; typerepair.py ran (python -I): 12 rows, `?` 3,3,3,1,1,2 -> 0,0,0,0 for 4 fns, 6 clean already 0.
- NOT_PROVEN: any MATCH/PARTIAL/FAIL verdict; compile status; that inferred void/s32 prototypes match the asm; the 10 candidates are m2c text plus prototype fixes only (unkN fields remain in 7 of them).
- UNKNOWN: processed tokens per function, first-call floor, mean context (not measured; calls ~14, ~4 on control/status).
- Next unit must know: W5b cannot get verdicts either until a tennis-capsule unit exists (W3b option a). Without it, report Tennis A/B cost on oracle-less layers only. Transform is also weak: only 4 prototypes fixed, no SDK-header resolution.