# DRX yield experiment — results (2026-11-12)

Rule: `PREREGISTRATION.md` (committed `d56542c7` before any run finished). Analysis: `python tools/drx_yield_analysis.py
vault/research/drx_eval/yield --json .../ANALYSIS.json` (raw output in `ANALYSIS.json`). Engine v0.4.1 frozen (`04aceae9`).
27/27 cells ran, 0 lost. Runner: `run_yield.v3.ps1` (lock-aware, resumes, aborts on engine fast-fail).

## Pre-registered verdict

| | A 120 s / 25k (control) | B 240 s / 25k | C 120 s / 12k |
|---|---|---|---|
| Persisted learnings, mean of 9 | 4.89 | **11.78** | 5.33 |
| Paired diff vs A (mean / 2·SE) | – | **+6.89 / 4.56** | +0.44 / 3.64 |
| INSUFFICIENT runs (rc=3) | 3 | **0** | 4 |
| Verified-quote rate (pooled) | 0.886 | 0.849 (−0.037, guard 0.10) | 0.896 |
| Extraction timeouts / calls | 1 / 17 | 1 / 44 | 5 / 22 |
| Mean wall time | 528 s | **1308 s** | 593 s |

- **B beats A and is ADOPTABLE** (rules 2–3: diff > 2·SE, quote-rate drop 0.037 ≤ 0.10, INSUFFICIENT 0 ≤ 3).
- **C is not**: no demonstrated yield difference, and more INSUFFICIENT runs than A.
- **H1 is NOT SUPPORTED** (rule 5): A did not have more extraction timeouts than B (1 vs 1). The gain has another cause.

## The other cause, named (POST-HOC, exploratory — not part of the rule)
Script: `posthoc_kinds.py` (session scratchpad; logic reproduced below). LLM-call timeouts by kind:

| kind | A calls / timeouts | B calls / timeouts | C calls / timeouts |
|---|---|---|---|
| decompose (SERP query generation) | 27 / **5** | 53 / **0** | 27 / 3 |
| extract | 17 / 1 | 44 / 1 | 22 / 5 |

- The step that 120 s cuts is **query generation**, not extraction. In 3 of 9 pairs (m1_rep2, m1_rep3, m3_rep2)
  A's first `decompose` call timed out, the run produced 0 queries and ended INSUFFICIENT. Those 3 pairs carry
  34 of B's +62 total. The same call took B 233.4 s in one slow window (normal 16–45 s): a 120 s limit would
  have killed it too. The slow windows (~22:25–23:10 and ~00:19–00:28 local, 2026-11-11) hit every arm.
- Excluding those 3 pairs, B − A = +4.67 against 2·SE ≈ 5.23: still positive, not demonstrated. B also runs
  ~2.5× more extraction calls, so part of the remaining gain is plausibly deeper exploration, not tested here.

## Decision
Adopting B means a 240 s child timeout for every LLM call, at ~2.5× wall time. What the data supports is narrower:
**query generation must survive slow `claude -p` calls**. A per-kind timeout (decompose 240 s, rest 120 s) or one
retry on a decompose timeout is the cheaper candidate, and is a NEW hypothesis: it needs its own pre-registration
and runs before it can be claimed. HELD_OUT cases in `EVAL_SET.json` stay unrun.

## Infrastructure events (rule 6, excluded with reason, none counted as runs)
- First launch (`yield_INVALID_lock_2003/`): 27 × rc=3 in 1–2 s, a foreign deep_research run held the shared lock.
- 2026-11-11 21:40: `research_quality.py` vanished from the frozen engine dir (it lived in the ended prior session's
  scratchpad; its `.pyc` proves it was imported at 20:01). 23 cells failed at import in 7 s; set aside as
  `*_infra_importfail`, engine re-frozen from the repo (tracked source == `04aceae9`, survivors hash-identical), re-run.
- 2026-11-12 00:19: a foreign run held the lock; runner v3 waited 301 s instead of recording a run.
