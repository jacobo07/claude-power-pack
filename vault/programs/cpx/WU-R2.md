# WU-R2 -- Control-plane P&L + incident detector + coordinator cap (goal cpx)
Plan: vault/plans/cpx-control-plane-extinction-cp50-2026-10-11.md sections 3, 5, 7 (read those only). After R1 DONE.
Mode: short PLAN in this packet, then EXECUTION.
1. Control-plane P&L: coordinator processed tokens vs worker tokens per goal.
2. CONTROL_PLANE_TOKEN_INCIDENT detector + coordinator cap (D22/D23 promoted). Regression canary: 37.5M coordinator vs 8.6M workers MUST fire; 3b4f4757 (4,943,171 vs cap 1.5M) must fire.
3. status --mission single-mission filter.
4. Generated C2-RESUMPTION (from state, not hand-written), replacing the manual doc.
5. Meta-tax guard: if R1+R2+chains exceed 40% of P50 (about 3.5M of 9.5M), R2 stops at detector + cap.
Done-check: tests incl. the 37.5M-vs-8.6M canary pass; generated C2-RESUMPTION diffed vs 05d30d1a; commits.
Route: route-M.json.
Common: no Monitor, no waiting call, no Agent spawns, no GSD commands. Pathspec commits on feature/knowledge-acquisition (no push), message ends with the Co-Authored-By line from the commit attribution. Never tick a chain by hand. Receipt K7 row: estimate vs actual processed tokens. Receipt line 1 '# <ID> receipt', line 2 'Status: DONE'.
Receipt path: C:\Users\User\.claude\skills\claude-power-pack\vault\programs\cpx\WU-R2-receipt.md
