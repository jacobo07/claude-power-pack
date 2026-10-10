# WU-S5 progress (second worker; stopped by session budget breaker at 47 calls > 1.5 x 30)

Status: PARTIAL, NOT DONE. No receipt, no S5b packet, chain.json NOT edited (the breaker blocked those writes).

## Committed on feat/ucda (do not redo)
- 17a5029c EVC U3/U4: cost_to_completion confidence (UNKNOWN/PROVISIONAL/CALIBRATED/INVALIDATED) + P50/P80/P95;
  gsd_mission.auto_headroom takes optional claim_cost, primary and UNCLAMPED (rate clamp stays as fallback only). CTC 24/24, envelope 57/57.
- 647514fb EVC U1/U4: mission_spend.stale_usage_guard + judge(as_of, now) watermark; gsdx_reforecast P50/P80/P95 (P80 labelled CHOSEN). 34/34, reforecast ALL PASS.
- 944ed790 EVC U5: gsd_mission.hold_guard_budget (called by set_owner_hold) writes stop=1 guard file per mission session;
  tools/test_hold_guard_budget.py drives the REAL guard to deny (6/6).
- NOT_PROVEN: U1 is not wired into gsd_mission._cost_breaker (its meter reads live, so as_of=now would be vacuous); only the API + tests exist.
- NOT_PROVEN: `claim_cost` is read from rec["claim_cost"] but nothing populates it yet.

## Uncommitted (commit it first)
- vault/plans/evc-u7-fresh-floor-OWNER-PROPOSAL.md (U7 breakdown + cut proposal; global CLAUDE.md untouched)
- this file

## Remaining (next exact actions, a fresh worker with a raised envelope)
1. Edit vault/programs/autonomy/chain.json: insert unit S5b after S5 (packet/route/receipt beside it, `after`: "S5") and set S6 `after` to "S5b".
2. Write vault/programs/autonomy/WU-S5b.md: EVC U8 backtest -- 2 traces (be97307b old Clock A 245.8M; ec66dcff intent/order 371.0M) + holdout
   (e0cd1dbb Clock A new 58.4M) vs compile_cost with observed=actual; report P50/P80/P95 coverage, bias, miss class; NOT_PROVEN if a source is missing; output vault/plans/evc-u8-backtest.md.
3. Write WU-S5-receipt.md (line 1 `# S5 receipt`, line 2 `Status: DONE`, commits above, claims PROVEN/NOT_PROVEN as listed) and commit packet + chain + receipt + U7 proposal together with pathspecs.
Owner may instead raise the envelope: python tools/mission_spend.py session-declare ...
