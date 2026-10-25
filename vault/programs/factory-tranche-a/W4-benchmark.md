# W4 benchmark: slim-t2 units vs W1 baseline

Measured from transcripts (read-only); pricing vault/pricing/anthropic_2026-10.json. Processed = input + cache read + cache write (output excluded). Calls = deduplicated assistant usage rows.

| unit | calls | call-1 | processed | input | cache read | cw 5m | cw 1h | output | hit | $ transcript model | $ @Opus 5.5 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| W3a | 7 | 19271 | 180180 | 14 | 150153 | 0 | 30013 | 4243 | 83.3% | $0.178 | $0.355 |
| W3b | 13 | 19661 | 435607 | 26 | 393072 | 0 | 42509 | 8872 | 90.2% | $0.298 | $0.596 |
| W3c | 22 | 20023 | 930639 | 44 | 880814 | 0 | 49781 | 14737 | 94.6% | $0.435 | $0.869 |
| W3d | 5 | 18605 | 107917 | 10 | 91075 | 0 | 16832 | 1323 | 84.4% | $0.090 | $0.179 |

Old-arm comparators (W1): gsd-executor $57.1/21 = $2.719 per session; worker epoch $28.0/8 = $3.500. Limit = 40% of each. The old figures cover different work, so the ratio is indicative, not like-for-like.

## Done-gate

| criterion | unit | verdict | number |
|---|---|---|---|
| cost<=40% vs executor_per_session @transcript model | W3a | PASS | $0.178 vs limit $1.088 (old $2.719) |
| cost<=40% vs executor_per_session @Opus 5.5 | W3a | PASS | $0.355 vs limit $1.088 (old $2.719) |
| cost<=40% vs worker_per_epoch @transcript model | W3a | PASS | $0.178 vs limit $1.400 (old $3.500) |
| cost<=40% vs worker_per_epoch @Opus 5.5 | W3a | PASS | $0.355 vs limit $1.400 (old $3.500) |
| first call <=20k | W3a | PASS | 19271 |
| cache-hit >=85% | W3a | FAIL | 83.3% |
| cost<=40% vs executor_per_session @transcript model | W3b | PASS | $0.298 vs limit $1.088 (old $2.719) |
| cost<=40% vs executor_per_session @Opus 5.5 | W3b | PASS | $0.596 vs limit $1.088 (old $2.719) |
| cost<=40% vs worker_per_epoch @transcript model | W3b | PASS | $0.298 vs limit $1.400 (old $3.500) |
| cost<=40% vs worker_per_epoch @Opus 5.5 | W3b | PASS | $0.596 vs limit $1.400 (old $3.500) |
| first call <=20k | W3b | PASS | 19661 |
| cache-hit >=85% | W3b | PASS | 90.2% |
| cost<=40% vs executor_per_session @transcript model | W3c | PASS | $0.435 vs limit $1.088 (old $2.719) |
| cost<=40% vs executor_per_session @Opus 5.5 | W3c | PASS | $0.869 vs limit $1.088 (old $2.719) |
| cost<=40% vs worker_per_epoch @transcript model | W3c | PASS | $0.435 vs limit $1.400 (old $3.500) |
| cost<=40% vs worker_per_epoch @Opus 5.5 | W3c | PASS | $0.869 vs limit $1.400 (old $3.500) |
| first call <=20k | W3c | FAIL | 20023 |
| cache-hit >=85% | W3c | PASS | 94.6% |
| cost<=40% vs executor_per_session @transcript model | W3d | PASS | $0.090 vs limit $1.088 (old $2.719) |
| cost<=40% vs executor_per_session @Opus 5.5 | W3d | PASS | $0.179 vs limit $1.088 (old $2.719) |
| cost<=40% vs worker_per_epoch @transcript model | W3d | PASS | $0.090 vs limit $1.400 (old $3.500) |
| cost<=40% vs worker_per_epoch @Opus 5.5 | W3d | PASS | $0.179 vs limit $1.400 (old $3.500) |
| first call <=20k | W3d | PASS | 18605 |
| cache-hit >=85% | W3d | FAIL | 84.4% |
| cache-hit >=85% pooled | pooled | PASS | 91.6% |

## W3d cap-trip probe

Total processed at last call: 107917 of a 150,000 stop. Budget-hook texts seen in the transcript:
- 2026-10-25T16:04:43.002Z (after 3 calls): `SESSION BUDGET TRIPPED (processed 61,515 + next call ~22,033 + closeout reserve 88,132 would cross stop 150,000 (target 120,000).) -- closeout call 1/4 allowed: record the spend row and the handoff, then stop.`
- 2026-10-25T16:05:25.963Z (after 4 calls): `SESSION BUDGET TRIPPED (processed 85,071 + next call ~23,556 + closeout reserve 94,224 would cross stop 150,000 (target 120,000).) -- closeout call 2/4 allowed: record the spend row and the handoff, then stop.`

The hook text is a projected-reserve trip (processed + next call + closeout reserve would cross the stop), not a trip at processed ~150k. Whether that counts as 'at or near its cap' is the Owner's call; the receipt's claimed 61,515 is compared with the transcript's hook text above.

## Open

- Second consumer (an unrelated PP task): NOT RUN in this tranche. OPEN, not pass.
