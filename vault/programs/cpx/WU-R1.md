# WU-R1 -- Rule router + canary (goal cpx)
Plan: vault/plans/cpx-control-plane-extinction-cp50-2026-10-11.md sections 2, 5 (read those only). Do NOT read vault/plans/deferred-backlog.md whole; use ToC grep + line ranges.
Mode: short PLAN in this packet, then EXECUTION.
1. Build a rule router: arming a cp50-c2 unit surfaces the D21/D22/D23/D24/D26 rows (by id, targeted lines) without materializing the backlog.
2. Tests V-RR-*: RED first (arm cp50-c2 unit -> rows surfaced; unrelated unit -> none; missing backlog -> fail soft, logged).
3. Canary drill via tools/mutation_drill.py style (never mutate a live-loaded file).
Done-check: V-RR-* pass; canary drill output in receipt; commits listed.
Route: route-M.json (cpx chain, after B0).
Common: no Monitor, no waiting call, no Agent spawns, no GSD commands. Pathspec commits on feature/knowledge-acquisition (no push), message ends with the Co-Authored-By line from the commit attribution. Never tick a chain by hand. Receipt K7 row: estimate vs actual processed tokens. Receipt line 1 '# <ID> receipt', line 2 'Status: DONE'.
Receipt path: C:\Users\User\.claude\skills\claude-power-pack\vault\programs\cpx\WU-R1-receipt.md
