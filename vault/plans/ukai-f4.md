# ukai F4 -- vocabulary bridge, paraphrase aliases and a score floor for Prompt Recall

Goal `ukai-f4` (capital packet sha 0987991dd902, Owner "approve ukai-f4 only" 2026-10-11). cwd = C:\Users\User\Apps\pp-ukai-f4
(branch ukai/f4 from ukai/f3 4d25e7a0). Lease L1 cap 2,800,000. Route: vault/plans/route-ukai-f4.json (22 calls).
git = & 'C:\Program Files\Git\cmd\git.exe' -C 'C:\Users\User\Apps\pp-ukai-f4'; python = & 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'.
Never Set-Location; absolute paths only. Never read transcripts. Never write the LIVE recall index: every index build and
eval in this unit runs with $env:CPP_RECALL_DIR = a fresh temp dir and $env:CPP_RECALL_NO_SPAWN = '1'.

## Evidence
- vault/evals/recall/misses-baseline.md (F0): 14 of 18 misses are term-gate -- 8 Spanish queries, 6 English paraphrases
  (q03 q04 q15 q16 q27 q29). ES recall 0.43 vs EN 0.72. Negatives n03 (haiku) and n05 (football) return 2-5 hits; abstain rate 0.0.
- vault/plans/ukai-f3lite-receipt.md + vault/evals/recall/report-f3lite.json (F3-lite, the baseline for this unit):
  recall@5 0.72, MRR 0.679, FP rate 0.3333, p95 481 ms (one cold run, unverified). q18 is indexed but outranked.

## Obligation (scope -- nothing else)
0. Latency: run tools/recall_eval.py three times against one warm private index; record p95 of each run. This settles
   F3-lite's open point; it is a measurement, not an optimisation.
1. Gates FIRST (RED), in tools/test_recall_sources.py or a new tools/test_recall_bridge.py, each with a positive control:
   (a) a Spanish query reaches an English-only document through the bridge; (b) an English paraphrase reaches its target
   through an alias; (c) a query below the score floor returns zero hits (abstain) while a known HIT still returns.
   Record RED, commit.
2. Implement in modules/gsd_x/recall.py: query-time ES/EN term bridge plus paraphrase aliases (a small explicit table in
   the module or a data file under modules/gsd_x/, never a model call), and a minimum-score abstain. GREEN, commit.
3. Private index; run tools/recall_eval.py --db <that db> --label f4 writing vault/evals/recall/report-f4.json. Compare to
   report-f3lite.json: recall@5, MRR, FP rate, abstain rate, ES vs EN recall, latency p95 (warm), and per-query flips.
   Commit the report.
4. Receipt vault/plans/ukai-f4-receipt.md (<= 25 lines): `Status: DONE` (or PARTIAL + blocker), commits, gates red->green,
   before/after metrics table, every query that flipped in either direction, call count.

## Stop-loss and limits
- Stop if recall@5 falls below 0.72 twice after a local fix, if any query that is a HIT under F3-lite turns MISS (the
  score floor may not buy precision with recall), or if the lease nears its cap before step 3 is committed.
- Excluded: F2, F1, F5-F7, q49 (expected files outside the indexed roots); any file other than modules/gsd_x/recall.py
  (+ a bridge data file beside it), the recall tests and vault/evals/recall/ (+ the receipt). Do not copy anything into ~/.claude.
- Tuning the floor or the alias table against the eval set is overfitting: the receipt must say which entries were added
  for which query ids.

End with `HANDOFF NOTE: F4 done` (or the blocker).
