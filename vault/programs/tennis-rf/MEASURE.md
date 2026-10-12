# MEASURE W5a -- draw (recorded before candidates)
Seed 20261011 (random.Random), pool = 48 m2c L1 rows of W3 sample60. 6 clean (ut=0), 6 few (ut 1-2); each group sorted by insns, split in 6 equal strata, one seeded pick per stratum (evidence/w5a/draw.py, draw.json).
Clean: fn_8022F90C fn_80203FEC fn_8020711C fn_8021EAA8 fn_8020CC14 fn_80241018
Few: fn_801BD194 fn_80257978 fn_8025C600 fn_8022621C fn_80254440 fn_80252F34
Layers: NO_WORK none (no solved source exists); Resort donor: none (donor_proven empty for all 12, and Tennis has no Resort source for the exact-shape donors); det type repair: typerepair.py; model: 2 fns.
Job step NOT run: no Tennis oracle (W3b refusal, capsule is Hardwired Resort). 0 GEX44 jobs, JOBS.md untouched.
Token attribution method: UNKNOWN this session (no session-token tool run); calls ~14 total, ~4 on control/status reading. Floor/mean context not measured.
## W10c compile-verified rates (job 2 ksrmb-20261011-233503, judged)
n=12 functions (the W5a draw). Det type repair layer: 0/12 MATCH (7 refused by source lint UNK_FIELD before send; 5 sent, all BLOCKED). Model layer: 0/12 MATCH, 0/26 units MATCH, 0 PARTIAL; 1 fn BLOCKED_COMPILER compile_error (fn_801BD194), 4 fns BLOCKED_CONTEXT (no context/headers for the Tennis target). Verified rate = 0/12 (n=12); upper bound is not a rate. W3b A/A (job 1): 3/3 MATCH (oracle path works). Tokens/model calls: UNKNOWN. Residual: BLOCKED_CONTEXT needs Tennis context; no job 3.

## W12 draw (recorded before any candidate, 2026-10-12)
Seed 20261012, W5a method (evidence/w12/draw.py, draw.json). Pool = W3 sample60 L1 rows minus the 12 W5a picks (clean 10, few 14).
Clean: fn_80203E40 fn_8032CF78 fn_80230ABC fn_8027A154 fn_802128D4 fn_8021F8BC
Few: fn_80230BF8 fn_803315A0 fn_80279E44 fn_80278FEC fn_8021F3E4 fn_80253348
W12 set = these 12 + the 12 W5a functions (W11: 10 lint-clean, 2 excluded UNK_FIELD).