---
name: backlog-to-capability
description: Ascension campaign 1 -- reconcile every backlog obligation against the real tree (inventory, ledger, web slice gate, constitutive promotion). Backlog is not implementation, implementation is not activation, activation is not execution.
---

# /backlog-to-capability

Owner modules (all in `modules/backlog_autopilot/`, extending the backlog autopilot, nothing parallel):

1. Inventory (discovers obligations, never curated):
   `python3 -m modules.backlog_autopilot.inventory --verify --out vault/programs/ascension/phase1/obligation_inventory.json`
2. Ledger (state, owner, destination per obligation; two separate coverage metrics):
   `python3 -m modules.backlog_autopilot.ledger --verify --out vault/programs/ascension/phase2/reconciliation_ledger.json`
3. Web vertical slice (`modules/backlog_autopilot/webslice.py`): proven by `python3 tools/test_asc_webslice.py` (V-ASC-WEB).
4. Constitutive promotion into a tower baseline family (`modules/backlog_autopilot/promotion.py`):
   `python3 -m modules.backlog_autopilot.promotion <family> --deltas F --evidence F --authority A --reason R`
5. Whole-campaign gate: `python3 vault/programs/ascension/bcap-1/done_gate.py --campaign 1`

Never promote ACTIVATED to execution evidence without a recorded exit-0 run.
