# WU-R6 -- Deterministic evidence dossier + cache (goal cp50-c2). ZERO model calls.
Plan: vault/plans/cpx-control-plane-extinction-cp50-2026-10-11.md section 7c. After R3 DONE.
1. Per-function dossier for draw 1-5: instructions, m2c pseudocode, callers/callees, xrefs, SDA/data refs, Resort-shape donor. Tools: DTK + m2c + Ghidra 12.1.2 headless (PowerPC:BE:32). Do not use or install REA (REJECT for PPC, tennis-rf/REA-DISPOSITION.md).
2. Content-addressed cache keyed by binary sha256 + function address.
3. Record size per dossier; cache-hit drill (second run = 100% hits, no recompute).
Done-check: dossiers for draw 1-5, size table, cache-hit drill output; zero model calls asserted.
Route: route-S.json.
Common: no Monitor, no waiting call, no Agent spawns, no GSD commands. Pathspec commits on feature/knowledge-acquisition (no push), message ends with the Co-Authored-By line from the commit attribution. Never tick a chain by hand. Receipt K7 row: estimate vs actual processed tokens. Receipt line 1 '# <ID> receipt', line 2 'Status: DONE'.
Receipt path: C:\Users\User\.claude\skills\claude-power-pack\vault\programs\cp50-c2\WU-R6-receipt.md
