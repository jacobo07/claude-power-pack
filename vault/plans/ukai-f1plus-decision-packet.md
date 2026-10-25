# UKAI F1+ decision packet (from the F0 baseline)

Evidence: `vault/evals/recall/report-baseline.json` and its rendering `vault/evals/recall/misses-baseline.md`
(50 positives, 6 negatives, 2970 indexed files, measured 2026-10-10T16:48:25). Harness `tools/test_recall_eval.py`
11/11 at commit 9f5fe9f3. Plan: `vault/plans/ukai-2026-10-10.md`. This packet decides nothing; the Owner does.

Sample-size caveat: with 50 positives, one query moves recall@5 by 0.02. Read differences under ~0.1 as noise.

## What F0 measured

| metric | value |
|---|---|
| recall@5 | 0.64 (32/50) |
| recall@5 EN / ES | 0.7222 (n=36) / 0.4286 (n=14) |
| MRR | 0.5857 |
| negative false-positive rate | 0.3333 (2/6) |
| foreign-memory hit share | 0.4612 |
| stale hit share | 0.0 |
| latency p50 / p95 | 107 ms / 181 ms |
| misses by class | term-gate 14, source-not-indexed 3, ranking 1 |

## Phase-by-phase: what the evidence says

| phase | evidence from F0 | reading |
|---|---|---|
| F4 vocabulary bridge | 14/18 misses are term-gate. 8 of the 14 are Spanish queries, 6 are English paraphrases (q03, q04, q15, q16, q27, q29). ES recall 0.43 vs EN 0.72. | The plan's own trigger ("only if F0 shows misses") is met. The English paraphrase misses mean an ES/EN dictionary alone will not close it; aliases for paraphrase are needed too. |
| F3 federation | 3 source-not-indexed misses: q18 `vault/lessons/parallel-explore-cascade.md`, q19 `vault/lessons/plan-files-not-allowlisted.md`, q48 `vault/hard_rules/HARD_RULES.md`. | Narrow and specific: the PP `vault/lessons/` and `vault/hard_rules/` stores are not recall sources. Graphify coordinates are NOT shown missing by this set. |
| F2 scope isolation | 46% of hits are foreign-project memories. | Supports F2. Caveat: "foreign" is not "private"; the set has no planted private memory, so leakage of a private fact is still UNMEASURED. F2's own negative test is what measures it. |
| F1 delivery ledger | Not measurable by F0 (offline eval). | Not evidenced for or against; it is the prerequisite for any live "was it used" claim. |
| F5 freshness/adversarial | stale hit share 0.0. | No stale exposure in this index; F5 is not pulled forward by evidence. |
| (no phase) false positives | n03 (haiku) and n05 (football) each returned 2-5 hits. No score floor / abstain exists (abstain rate 0.0). | Not owned by any planned phase. Candidate: a minimum-score abstain inside F4, measured on the same 6 negatives plus more. |
| q49 ranking | Expected files live outside the indexed roots (GEO-audit corpus). | Out of scope for recall as built; single query. |

## Options for the Owner

- **A. Evidence order:** F3-lite (index `vault/lessons/` + `vault/hard_rules/`, 3 misses) -> F4 (14 misses, plus a
  score-floor for the 2 false positives) -> F2 -> F1. Each phase re-runs `test_recall_eval.py` against this baseline.
- **B. Plan order as written:** F1 -> F7.
- **C. Stop at F0:** the baseline and harness are committed and reusable as-is.

## Cost

The only measured anchor is F0 itself: 2,667,322 tokens settled on goal ukai-f0. There is no measured per-phase
cost for F1+, so none is quoted here. Goal `ukai` (5M) is closed and excluded; F1+ needs its own capital packet,
sized after the first phase's per-call cost is measured.
