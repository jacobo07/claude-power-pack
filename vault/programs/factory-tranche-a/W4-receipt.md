# W4 receipt

Tests: `python tools/test_w4_benchmark.py` -> W4_PASS=6/6, exit 0. `python tools/w4_benchmark.py` exit 0, wrote W4-benchmark.json and .md.

## Verdicts (numbers in W4-benchmark.md)
- Cost <= 40% of old arm: PASS for all 4 units, vs both the executor session ($2.719) and the worker epoch ($3.500), at transcript model and at Opus 5.5. Highest is W3c at $0.869 at Opus 5.5 (limit $1.088). Caveat: the old figures cover different work, so this is indicative, not like-for-like.
- Slim first call <= 20k: W3a 19,271 PASS; W3b 19,661 PASS; W3c 20,023 FAIL (by 23 tokens); W3d 18,605 PASS.
- Cache-hit >= 85%: W3a 83.3% FAIL; W3b 90.2% PASS; W3c 94.6% PASS; W3d 84.4% FAIL. Pooled 91.6% PASS.
- W3d cap trip: the breaker hook did fire, with the text "SESSION BUDGET TRIPPED (processed 61,515 + next call ~22,033 + closeout reserve 88,132 would cross stop 150,000)". That matches the receipt's 61,515. It is a projected-reserve trip, not a stop at 150k. The transcript's total processed is 107,917, and later closeout calls were allowed. "At or near cap" is NOT established by the measured numbers: the trip came at 41% of the stop, by projection.
- Second consumer (an unrelated PP task): OPEN, not run.

## Open items
- Rows that carry no 5m/1h cache-write split would be priced as 5m; all four sessions carry the split.
- The W3c call-1 and W3a/W3d cache-hit misses need an Owner decision (a threshold miss, not an error).

COMMITS: b630cb9b
