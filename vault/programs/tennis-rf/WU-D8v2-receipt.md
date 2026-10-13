Status: PARTIAL (step 1 done; budget breaker fired at 15 calls; no send, no job used)

## Done
- Step 1: `evidence/d28/d8/draw.py` fixed (two bugs: a missing newline, and W pointing at evidence/ so the exclusion list matched 0 files in draw #0; draw #0 was never used and was discarded before any send). Final draw: seed 20261013, 40 fns (14/16/10 for D3 distance 1/2/3), 361 fns excluded from 28 sources, pools after exclusion d1=254, d2=1130, d3=22. Written to `evidence/d28/d8/draw.json`. NEVER REDRAW.
- Lint-clean in draw: 14 of 40 (all distance 1, size_insns 1). Full motif cover: 1 of 40 (a distance-2 fn). D3's pool is only 22, so distance 3 is nearly exhausted for D12.

## Not done
Steps 2-4: arm B/D candidate sources, JOBS.md rows 5-6 (still empty), send, tournament.json. Arm D has 1 full-cover fn, so it will be near-empty; report that rather than pad it. Distance-2 and 3 fns are not lint-clean, so arm B can only send the 14 distance-1 fns.

## Next exact action
1. On GEX44 build B sources (current certified header, 14 lint-clean fns) and D sources (motif cover) by script; E EMPTY, F = B union D.
2. Write JOBS.md row 5 BEFORE send (+3 donors, W12 route, `job_commands_kobii.py --preflight --require-return`); row 6 "UNUSED by D8v2".
3. Judge, write tournament.json (Wilson interval, tokens/MATCH, vs W12 12/22 and W10c 0/12).

## Plan delta
MDG 16, 19: not settled.
