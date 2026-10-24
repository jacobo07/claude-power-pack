---
phase: 05-s5-terminal-reconciliation
plan: 01
completed: 2026-10-24
status: complete
---

# Summary 05-01
Landed S5: `gsd_epoch.is_terminal_row` closes an epoch on any terminal transition row (a state mention without `seq` does not);
`gsd_mission.resolve_receipt` / `receipt_name` are the single receipt resolver and suffix owner (steward and slim_finished go through them);
`tools/mission_reconcile.py` (`reconcile`, `dispose`) classifies a stop as RECOVERED_DONE / CONTINUATION / FAILED / AMBIGUOUS read-only; the supervisor writes one `terminal_reconciled` annotation row (switch `CPP_TERMINAL_RECONCILE=off`).

Measured on this host: open terminal epochs 24/53 before, 0/53 after; resolver disagreements 0. The 149 h figure stays LAPTOP-ONLY and unmeasured here.

Gates: test_s5_reconcile 42/42 (10 mutants red), test_gsd_epoch 111/111, test_gsd_mission 234/234, mission_steward 26/26, receipt_judge 5/5, mission_recovery 69/69, arm_preflight 16/16, rotation_invariant 17/17 (+1 inconclusive), s3 11/11, s4 14/14.
Debt not ours (identical on baseline): V-AMCR-ONE-RESOLVER-INVENTORY (mission_continuity 37/38), cpp_gsd_long_routing 8/9 (live command path absent in the sandboxed HOME).
