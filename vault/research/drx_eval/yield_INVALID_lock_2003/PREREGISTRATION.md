# DRX yield experiment — pre-registration (written before any run of it finished)

Engine: deep_research v0.4.1 (`04aceae9`), frozen copy. Runner: 3 arms x 3 DEV missions x 3 reps = 27 runs,
arm order rotated per (mission, rep). 12-query cap, depth 2, breadth 3, Haiku 4.5 via isolated `claude -p`.

| Arm | LLM timeout | Content chars per source |
|---|---|---|
| A (control) | 120 s | 25 000 |
| B | 240 s | 25 000 |
| C | 120 s | 12 000 |

Hypothesis H1 (from U6, n=3): requiring verbatim quotes lengthens extraction past the 120 s timeout, which
costs yield. Prediction: A has more extraction timeouts than B and C, and lower yield.

## Metrics (per run)
- Primary: persisted learnings (yield).
- Guardrails: ledger persisted_verified_span_rate; INSUFFICIENT runs (rc=3); wall time.
- Mechanism: extraction calls that timed out; extraction call duration (from the per-call LLM log).

## Decision rule (fixed now)
1. Pair each B (and C) run with the A run of the same mission and rep. Let d = yield(arm) - yield(A), n = 9.
2. An arm BEATS A on yield if mean(d) > 2 * sd(d) / sqrt(9). Otherwise: no demonstrated difference.
3. An arm is ADOPTABLE only if it beats A AND its pooled verified-quote rate is not lower than A's by more
   than 0.10 AND it has no more INSUFFICIENT runs than A.
4. If both B and C are adoptable, prefer the lower mean wall time.
5. H1 is SUPPORTED only if A shows more extraction timeouts than the winning arm AND the yield loss is larger
   in A-runs that had an extraction timeout than in A-runs that did not. Otherwise H1 is NOT supported, even
   if an arm wins (the gain would then have another cause, to be named, not assumed).
6. Failed runs stay in the denominators. No run is re-done or dropped after its result is seen; a run lost
   to an infrastructure failure (process killed, no report) is reported as such and excluded with its reason.
7. HELD_OUT cases in `EVAL_SET.json` are not run in this experiment.
