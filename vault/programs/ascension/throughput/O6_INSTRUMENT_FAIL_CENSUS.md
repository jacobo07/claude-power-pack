# O6: INSTRUMENT_FAIL census (Ascension throughput T1, 2026-11-22, pane 37612bb0)

Source: GEX44 `agora/ascension-autopilot/ledger.jsonl`, every `evo_decision` with `cls == INSTRUMENT_FAIL` (38 rows,
11-12..11-22). The spend is the `generation_closed.spend` of the same lane that follows the decision. Dataset:
`o6_instrument_fail.json` (ts, lane, action, spend, instruments). Measured spend of those generations: **200.9M**.

## Classes

| class | n | spend | deterministic before arming? |
|---|---|---|---|
| A. population / control-pool size below its declared floor (`n=2<22`, `2<24`, `4<24`, `0/428<24`, `held-out 3<6`, `n_fn 37<60`, `11 fn<120`, `min_eligible 3, saw 1`, "plantable count", "population floor", "adequacy") | 21 (+2 H-S49FM ">=10 certified fixtures" read as A) | 97.2M (+11.4M) | **yes**: the floor is in the plan and the pool is countable from the product before the generation runs |
| B. a classifier / discriminator / probe failed its own positive control (wp_gcw*, EGG2, H-GAMETC fingerprint, R4 canary, frame balance, N-callee model) | about 12 | about 70M | no: that is the method's own result (semantic; the judge's to read) |
| C. a method route that missed its coverage clause (H-S182T C6, H-LINK-EXT, partial-path) | about 3 | about 20M | no |

Lanes for class A: TENNIS 8, KSR 6, WIIPARTY 4, WSR 3. All four keep producing it (latest 11-22 04:45Z TENNIS S287T).

## Recommendation (W3, not built in T1)

Admit a generation only after a **pool-adequacy preflight** that answers deterministically "does the frozen pool reach
the floor the plan declares?". This is a cheap CPU count on the product (the same predicate the worker checks after
spending about 5M). Mechanism: the planner's phase line already carries the floor (`n>=22`, `>=24`, `>=60`). Make the
planner emit `POOL_FLOOR: <name> >= N via <command>`. The autopilot runs the command before arming. Below the floor, the
plan returns to the planner with the count (a kept-judgment re-plan, about 0.6M) instead of a generation that fails at
its first gate. Expected saving: up to about 100M per two weeks at the current rate (class A), a little over 10% of
all generation spend. No change to any certification predicate: the generation the preflight refuses would have
produced INSTRUMENT_FAIL, never a certificate.

## Not concluded
- Spend attribution is the following `generation_closed` of the lane. A decision with no close before the next arm
  reads 0.0M (2 rows), so class A spend is a lower bound.
- The A/B/C split is by instrument wording, not by reading each checkpoint. Treat it as a hypothesis for W3, which
  must verify it on 5 sampled checkpoints before building the gate.
