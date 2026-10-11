# S5b receipt
Status: DONE

Commits: tools/gsd_mission.py claim_cost_for + tools/test_claim_cost_for.py (6/6), vault/plans/evc-u8-backtest.md, this receipt.

- U8 backtest: NOT_PROVEN. Actuals PROVEN (243.5M / 368.0M / 57.9M measured, ~1% under stated). No claim graph exists for
  any trace, so P50/P80/P95 coverage, bias and miss class cannot be computed. Detail in vault/plans/evc-u8-backtest.md.
- claim_cost population: PROVEN mechanism. `claim_cost_for(rec)` compiles `rec["claim_graph"]` (explicit claim_cost wins;
  missing/bad/phase graph -> None fallback). _auto_budget now calls it. Nothing sets `claim_graph` yet: the only graph
  found (io-liveqa claims-classified.json) is Live QA product, read-only for this programme, so not wired.
- U1 watermark wiring: NOT_PROVEN, not attempted (_cost_breaker meters live so as_of=now is vacuous). Candidate site:
  hold/status text that shows a stored snapshot to a human.
- Repo note: tools/gsdx_chain.py and tools/test_gsdx_chain.py are in UU (unmerged) state from another writer; untouched.
- Next unit must know: set `claim_graph` at arm time; then run the backtest on a mission with a pre-spend graph. ~14 calls used.
