# WU-D10 receipt
Status: DONE_WITH_LIMITS

Done-check: WU-W13.md, `vault/plans/tennis-frontiers-2026-10-13.md`, W8B-READY.md exist and are committed (pathspec).

## Receipt check (receipt_judge)
D1c DONE_WITH_LIMITS, D1d DONE, D2 DONE, D3 DONE, **D4 PARTIAL** (Owner-accepted, DISPOSITION.md), D5 DONE, D6 DONE, D7 DONE. Non-DONE named in W8B-READY (D4; D8/D9 have no receipt, outside D10's D1c..D7 scope).

## Results
- W13 packet: 254 class-1 lint-clean unsent fns + 40-fn class-2 probe; expected MATCH 88-186 (Wilson 0.347-0.731 on 12/22); 9 jobs at W12 batch size (2-3 if larger batches are accepted), **jobs 8+ NOT approved** (packet states the exact approval); tokens P50 ~2.5M (1.2-4.5M, basis: goal-lineage per-D-unit usage).
- Frontiers: 7-day and 72-hour NOT reachable on measured inputs (measured deterministic zone 15.3%, predicted MATCH 5.6-11%); falsifiers listed. Theoretical: <= 13,745 residual items, 3,429 distinct vars; compression 0.556 (n=9).
- UNKNOWN: model-needed fraction of classes 2-5, joint-delta unlock, capsule batch ceiling, price above class 1.
- Front matter of WU-W13.md parses via chain_pre (class SEARCH, no pre, reason in the file).
- No GEX44 job, no model work on functions. Residual sums computed from d3/residuals.jsonl and d4/frontier.json by a one-off script (sum 13,745; kinds counted).

## Plan delta
MDG 20 (W13 compiled): done as packet, blocked on job approval. MDG 21 (frontiers): 7d/72h not reachable on measured inputs, values above. MDG 22 (W8b inputs): W8B-READY written; D4 PARTIAL and D8/D9 missing named.