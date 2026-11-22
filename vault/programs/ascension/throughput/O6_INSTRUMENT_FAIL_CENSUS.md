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

## W3 step 0: the 5-checkpoint verification (2026-11-22 15:20Z, pane a52cc240, read-only on GEX44)

Each sampled decision was matched to its `evo_decision` row in `ledger.jsonl` (same lane and minute). Each checkpoint
was then read at its path in the lane repo.

| lane / gen | instrument | checkpoint says | countable before arming? |
|---|---|---|---|
| TENNIS S31T (11-12) | H-T1a control pool n=2<22 | "the frozen control rule yields a pool of n=2 ... against the pre-registered 22". Reopen condition: "frozen pool demonstrated >= 22 **at freeze time**" | **A, yes**. A rule applied over existing certified fns |
| WSR S103R (11-16) | H-CCVER held-out 3<6 | a cohort of literal refused-alias fns, with a sha256-pinned split | **A, yes**. A selection over existing data |
| KSR S134K (11-17) | H-S131SA pool 4<24 | "only 4 valid certified stmw-saving units with a source (9 certified stmw units across 10959 CERTIFIED rows)" | **A, yes**. A count over the receipts |
| WIIPARTY S147W (11-18) | H-FN-LINK n_fn 37<60 | "n_fn=37 **completed** (<60 required) ... 10 TUs LINK_FAIL" | **NO, misclassified.** n_fn counts functions that finished linking, so it is a result of the method |
| TENNIS S277T (11-22) | H-S263TW population floor | census of 164 pool fns -> eligible 24 -> admitted after disjointness 1. `tools/s263t_census.py` reads only original DOL bytes | **A, yes**. But the generation wrote and froze the census tool itself |

Findings that change the W3 design:
1. **Class A is about 4/5 of what the wording counted.** A floor on "completed" or "linked" items is a method result,
   not a pool size. Restated bound: about 97M x 0.8 = about 78M per two weeks, a lower-bound attribution as before.
2. **In 4 of the 4 true A cases, the generation wrote the counting tool** (s31t_scan, the ccver cohort, the S134K
   control census, s263t_census.py). No command exists for the autopilot to run before arming. So "the planner emits
   `POOL_FLOOR ... via <command>`, the autopilot runs it" holds only when the command reads artifacts that already exist.
   Two shapes are viable:
   - (a) `POOL_FLOOR` is admitted only over existing tools and receipts. A plan whose count needs new code gets no
     preflight. Cheap, but it would have missed all 4 samples.
   - (b) A **count-first phase**: P1 is bounded to building the pool and freezing it, with a small authority slice
     (for example 1.5M), and the mission halts at P1 when the count is below the declared floor. It catches all 4.
     It is a mission-terms change, applied by the planner prompt plus a halt predicate.
3. Neither shape touches a certification predicate. A refused generation would have produced INSTRUMENT_FAIL.

Choosing (a) or (b), and deploying either to the live autopilot, is the Owner's decision. Nothing was built or deployed.
