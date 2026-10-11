# ukai F4 receipt
Status: PARTIAL -- bridge + aliases implemented and gated; score floor NOT calibrated; eval (step 3) NOT run; lease edge hit.
Commits (branch ukai/f4): 71830c35 RED gate, 294ea611 bridge/alias implementation (WIP, floor inert).

Step 0 latency (one private index, 2587 files / 8139 chunks, CPP_RECALL_DIR temp, NO_SPAWN=1; live index untouched), recall_eval x3:
p95 312.38 / 149.28 / 154.57 ms (p50 95.19 / 86.16 / 82.85). First run carried OS-cache warm-up; steady warm p95 ~150 ms.
F3-lite's 481 ms was therefore a cold-run artefact, not a 2.7x regression (baseline 181 ms was a different, smaller index).
Metrics at F3-lite state, stable across 3 runs: recall@5 0.72, MRR 0.679, FP 0.3333, abstain 0.0, en 0.8056, es 0.5.

Gates tools/test_recall_bridge.py (V-RECALL-BRG-*): RED 2/6 -> now 5/6.
 PASS ES-TO-EN + control, ALIAS + control, FLOOR-CONTROL. FAIL FLOOR-ABSTAIN (long-misc.md still returned).
 Regression: test_prompt_recall 34/34, test_recall_eval 11/11.
Change: modules/gsd_x/recall.py -- bridge() loads modules/gsd_x/recall_bridge.json (equivalence groups, no model call);
 _known() expands each prompt term to its known variants; hits now carry "score"; MIN_SCORE constant exists but is 0.0 (no floor yet).
 Side effect: tools/recall_eval.py classify_miss uses select_terms and raw hay terms, so miss_class under-credits bridged matches.

Alias table provenance (overfitting disclosure): groups tagged "for" in recall_bridge.json were written after reading the
miss list and the target memories: q03 q04 q07 q15 q16 q17 q24 q26 q27 q29 q34 q39 q40 q45; gate groups: ES-TO-EN, ALIAS.
Untagged groups are general vocabulary. Expect eval flips on exactly those ids; that is in-sample, not generalisation.

Flipped queries: none measured (step 3 not run). Calls: ~19.

NEXT: (1) pick MIN_SCORE from the score distribution of F3-lite HITs vs n03/n05 (hits now expose "score"); gate FLOOR-ABSTAIN must go green
without any F3-lite HIT turning MISS; (2) python tools/recall_eval.py --db <private db> --label f4; (3) compare to report-f3lite.json, fill flips here.
