# W8B-READY -- inputs W8b must use beyond `WU-W8b.md` (written by WU-D10, 2026-10-13, after the receipt checks)

`WU-W8b.md` reforecasts from W12 only. Add these D28 inputs; where they conflict with W12-only inputs, the D28 value wins and is tagged.

## Receipt check (`tools/receipt_judge.py`, the certified reading)
| unit | status | note |
|---|---|---|
| D1c | DONE_WITH_LIMITS | limits in receipt (DETERMINISTIC_USED_MODEL not fed model-call count) |
| D1d | DONE | |
| D2 | DONE | |
| D3 | DONE | |
| D4 | **PARTIAL** (not DONE) | accepted by Owner (`evidence/d28/d4/DISPOSITION.md`): reproducible frontier, ranking NOT causal. Use the 3,429-var frontier, do NOT use dominator rank as unlock evidence |
| D5 (v2) | DONE | `WU-D5-receipt.md` |
| D6 | DONE | 0 certified facts; 276 -> 276 |
| D7 | DONE | |
| D8 | **NO RECEIPT** (jobs 5-6 pending) | tournament verdicts (arms B/D/E/F, tokens per MATCH) MISSING: W8b has no reuse-tournament rate; keep Scope-B compounding forecast tagged H |
| D9 | **NO RECEIPT** | synthesis probe missing; no synthesis rate |
D8/D9 are not inputs of D10's scope (D1c..D7); their absence is named so W8b does not wait or assume.

## Inputs W8b must read
1. Frontiers: `vault/plans/tennis-frontiers-2026-10-13.md` (measured inputs table; 7d/72h verdicts; falsifiers).
2. W13 packet (the next wave, its prediction and approval ask): `vault/programs/tennis-rf/WU-W13.md`. W8b forecasts W13's cost from its P50 2.5M / range 1.2-4.5M and expected MATCH 88-186 (D).
3. D-unit measurements (under `vault/programs/tennis-rf/evidence/d28/`): `d3/census.json`, `d3/autonomy.json` (distance 12/263/1307/92/92/31; effective remaining work: classes 2-5 unpriced); `d2/near_match.json` (0.556 compression); `d2/shock_attribution.json` (175 -> 276: 16 tag-dependent, 85 prototype-dependent); `d4/frontier.json` (3,429 vars); `d5/causal_unlock.json` and `d6` (single deltas unlock 0; 276 -> 276); `d7/replay.json` (closure 2.4%, 5-6x).
4. Spend: `python tools/mission_spend.py goal-lineage --goal tennis-rf` (2026-10-13: programme 100M, used 84.29M, 20 leases; D-unit usage 0.3-2.9M each). `JOBS.md`: 7 approved, 3 used, job 4 unused (D6), 5-7 reserved D8/D9; W13 needs more (see packet).
5. Retire from the W12-only forecast: the "structural_family"/"idiom_family" clustering and the D4 dominator rank as drivers of compounding (D1d INCONCLUSIVE; D4 red control falls).

## Items that change the forecast
- Compiled-learning forecast cannot assume knowledge shocks of +100 fns repeat (M: one shock, then 0).
- Scope-B admission conditions (HANDOFF section 2): the frontiers file states 7d and 72h NOT reachable on measured inputs; ADMIT would contradict it unless W13/joint-delta evidence overturns it.
- Token per function above class 1: UNKNOWN, not 0.