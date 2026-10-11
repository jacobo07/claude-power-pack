# WU-R5 -- Decisions + evidence (goal cpx)
Plan: vault/plans/cpx-control-plane-extinction-cp50-2026-10-11.md sections 6, 7c, 9 (read those only). After R2 DONE.
1. D24 NPV re-check against measured data; keep KEEP_PARKED unless the reprice trigger (>=2 UNKNOWN holds/week across chain programmes) is met.
2. D26 calibration rows; D26 resumes only on Owner activation after C3.
3. FIOS duplicate-cost measurement; optimize only if material (state threshold in receipt).
4. D11-D19 evidence-gated admission table (A1): one slice per row only when C3 + TRF W6/W7 show falling marginal verified cost; apply D14/D20 sequencing guards (binding); do not execute any row wholesale.
5. D27 REA Wii/PPC Enablement (amendment A2, plan section 9): read ONLY the `## D27` section of vault/plans/deferred-backlog.md (last section; Grep `^## D27`, do not read the whole file). Add a D27 row to the admission table: activation = cpx R6 receipt DONE + C3 two-arm result; gate = USE_REA only if P7 EVC < R6 dossier, else KEEP_CPP + EXTEND_UPSTREAM; D21 never waits on it. P0 (pin current upstream release from server.json + release tag, re-run W4 `rea --help` hang probe) MAY be armed as a small zero-model unit; if not armed, say why in the receipt.
Done-check: decision table file in vault/programs/cpx/ with a verdict per row (including D27) and its evidence line; commits.
Route: route-S.json.
Common: no Monitor, no waiting call, no Agent spawns, no GSD commands. Pathspec commits on feature/knowledge-acquisition (no push), message ends with the Co-Authored-By line from the commit attribution. Never tick a chain by hand. Receipt K7 row: estimate vs actual processed tokens. Receipt line 1 '# <ID> receipt', line 2 'Status: DONE'.
Receipt path: C:\Users\User\.claude\skills\claude-power-pack\vault\programs\cpx\WU-R5-receipt.md
