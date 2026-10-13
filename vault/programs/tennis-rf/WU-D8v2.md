# WU-D8v2 -- Ph8 reuse tournament (GEX44 cpu + job 5, job 6 only if needed)

Common brief: `D28-BRIEF.md`. Plan Ph8, MDG 16, 19. Supersedes WU-D8 (two attempts, m-54fb8e8f62d1 and m-c759749e651e,
both stopped by the 4-call budget of route-G, a gate-only route; this unit runs on route-M, 20 calls). Facts already
read by those attempts, reuse them instead of re-reading: `WU-D8-receipt.md` (PARTIAL), sections "Facts read" and
"Next exact action". Step 0 is settled: JOBS.md carries "Owner approved jobs 5-6 for D28 Ph8".

Arms: B (header), D (motif); A from W10c/W12 history (no rerun). E (D4 dominators certified first) is EMPTY: D6
certified 0 facts and D4's ranking is degree-driven (DISPOSITION.md); report it EMPTY/INCONCLUSIVE, not run. F = B+D,
reported as the union of B and D candidates, not a third send.

1. Held-out draw: `evidence/d28/d8/draw.py`, 40 functions not in W5a/W12 draws and not used by D2-D7 attribution (the
   exclusion list in WU-D8-receipt.md), seed recorded, stratified by D3 distance class 1-3. Never redraw. Write the set
   to `evidence/d28/d8/draw.json`; D12 draws exclude it.
2. Per arm, the candidate source for each drawn function by that arm's rule only (B: current certified header;
   D: motif cover from P1P2). Deterministic composition, on GEX44; a model step needs a Proof of Model Necessity line.
3. ONE job (job 5) carrying both arms plus 3 donor controls, W12 route, JOBS.md row 5 BEFORE send, custody read back.
   Use job 6 only if one batch cannot carry both arms (state why in row 6); else row 6 says "UNUSED by D8v2".
4. Verdict per arm: MATCH rate with Wilson interval, tokens per MATCH (measured), vs arm A history; donors 3/3 or the
   job is INVALID. `evidence/d28/d8/tournament.json`.
Done-check: tournament.json and JOBS.md rows committed (pathspec).
Receipt: `WU-D8v2-receipt.md`.
