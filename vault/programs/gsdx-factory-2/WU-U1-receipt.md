Status: DONE -- U1 WIDEN census ran: tam-ds-8 judged 33/33, 0 solved (recorded negative), certified stays 519/1797; follow-up packet is WIDEN cohort 4.

# WU-U1 receipt (gsdx-factory-2 OPEX U1)

Closed by the coordinator pane (fc4dce34) after worker 1 (m-dfd1cc5d2d41, sid db7d26c9) hit its 2.4M session stop.

## What the worker did, and why it stopped
- Built `campaign pin --from-next` plus the CP1 gate in 18 tool calls, ~118K processed per call, and hit the
  session breaker at 2,134,105 processed. The mission record's `cost_mark` reads 2,423,107.
- It did not commit anything. Its first test run died on `dict(pkt, class=...)`, a SyntaxError because `class`
  is a Python keyword.
- It could not write this receipt. The harness bgIsolation guard refuses Write/Edit from a background session
  into the PP main checkout. It did not route around the guard.
  - Fixed in the chain: PP `b297f576` makes the chain refuse to arm any unit whose receipt sits in a main
    checkout (gate V-CHAIN-REFUSES-MAIN-CHECKOUT-RECEIPT, mutant killed).

## GEX44 `~/missions/t1-campaign`, branch `t1/campaign` (local, unpushed)
- e5cf47a3 feat(recon_fabric): campaign pin --from-next -- pin a next packet's exact cohort (U1)
- d9b222b4 evidence(campaign): U1 WIDEN census -- tam-ds-8 certifies 0 by search (519/1797)
- c5aeb342 evidence(t1): second campaign next packet -- WIDEN, cohort 4 (U1 follow-up)

## Gates
- CP1_PASS=16/16, NEXT_PASS=22/22, FR1_PASS=15/15, after the one-line keyword fix.
- New gate V-RF-CP1-FROM-NEXT:
  - Red: a certified fn, a foreign operator set, a non-WIDEN packet and a stale key are each refused.
  - Control: the same cohort gives the same pin bytes, and `check` replays the pin clean after a certification.
- `campaign check --pin tam-ds-8`: CAMPAIGN_PIN OK.

## Run (tam-ds-8, sl-2648aafa7cb2, batch 4, depth 3, 400 evals, seed 7)
- 33 subjects: 29 EXHAUSTED, 4 BUDGET_EVALS (fn_80207488, fn_80228BA8, fn_80233F8C, fn_80254D04), 0 solved.
  Verdict: INCOMPLETE.
- Interrupt candidates (MISSING_OPERATOR): REGISTER_MAPPING_CONFLICT, REGISTER_MAPPING_CONSISTENT.
- Certified before -> after: 519 -> 519 (`evidence/frontier/counters.json` certified_by: cert1 490, ledger 12,
  search 17). Nothing to certify.

## Follow-up `campaign next`
- `evidence/campaign/next/002-census.json`, class WIDEN, cohort 4: the 4 BUDGET_EVALS functions.
- sha256 884aaee0744cb9e13e05e3580f8a0a821dadf3ecccee1ca27f813e8d712cb40f
- Budget line: P50 600K, hard 1.5M.
- It is not CLASS_INTERRUPT, as the packet expected: R2 does not count a BUDGET_EVALS result as searched.

## UNKNOWNs / findings
- Planner loop risk. R2 re-proposes a BUDGET_EVALS function under the same operators, and the packet carries
  no larger eval budget. Re-pinned at 400 evals, it would plausibly hit BUDGET_EVALS again and be
  re-proposed again. This needs either an R2 rule that treats a BUDGET_EVALS result at a given `max_evals` as
  searched, or a packet that carries a larger budget.
- The REGISTER_MAPPING interrupt is the real U2 input once the 4 are settled.
- The coordinator's inline spend for the close is not separately measured. It is booked through the coordinator
  session's own settle.

## Spend
- Worker 1: 2,423,107 processed (`cost_mark`), route stop 2.4M.
