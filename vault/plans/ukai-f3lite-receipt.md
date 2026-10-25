# ukai F3-lite receipt
Status: DONE
Commits (branch ukai/f3): 8f3f8e79 RED gate, 6d56dd11 sources added, plus report+receipt commit (this one).
Gate tools/test_recall_sources.py: RED 1/4 (control PASS, lesson/hard-rules-pp FAIL) -> GREEN 4/4. test_recall_eval 11/11.
Change: modules/gsd_x/recall.py default_sources() globs PP_ROOT/vault/lessons/*.md (kind lesson) and vault/hard_rules/HARD_RULES.md (kind hard-rules-pp), scope global.
Index: private temp CPP_RECALL_DIR, CPP_RECALL_NO_SPAWN=1; 2573 files, 8122 chunks. Live index untouched.

| metric | baseline | f3lite |
|---|---|---|
| recall@5 | 0.64 | 0.72 |
| MRR | 0.5857 | 0.679 |
| FP rate (negatives) | 0.3333 | 0.3333 |
| foreign memory share | 0.4612 | 0.4286 |
| latency p95 ms | 181.22 | 481.12 (single run, cold temp index; unverified as regression) |

q19 MISS->HIT (rank 1), q48 MISS->HIT (rank 1); q18 source-not-indexed -> MISS/ranking (now indexed, outranked: F4 scope).
Also flipped MISS->HIT: q17, q49. No query went HIT->MISS.
Open point: p95 latency rose 2.7x; not re-measured warm (out of scope, no second run). Report: vault/evals/recall/report-f3lite.json
Calls: ~14.