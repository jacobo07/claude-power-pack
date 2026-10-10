# WU-S5 -- Autonomy Convergence unit S5

Read `vault/programs/autonomy/PROGRAMME.md` first (session loop, continuation units, constraints).
Your scope: Plan section 3 row 'Estimator...' = EVC plans 88af526e + 836c1121 units U1 U3 U4 U5 U7 U8 at their prices.

## Do
FIRST: if an EVC mission is running or approved (missions with cwd C:\Users\User\Apps\pp-evc not terminal, or EVC receipts newer than 2026-10-10 12:00), this unit is NO_WORK: consume EVC's output, write DONE with the reason. Otherwise execute EVC U1 (freshness watermark + stale-snapshot guard), U3 (cost_to_completion primary, remove [1M,15M] clamp, confidence states), U4 (P50/P80/P95 from 610808c5), U5 (hold writes the guard budget for the live worker + canary drill), U7 (fresh-floor breakdown and cut; any global CLAUDE.md change is an Owner proposal file, not an edit), U8 (backtest 2 traces + 1 holdout). Use continuation units.

Receipt: `vault/programs/autonomy/WU-S5-receipt.md`.
