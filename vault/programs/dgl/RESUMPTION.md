# RESUMPTION -- dgl (durable goal / disposable lease)

Identity: worktree C:\Users\User\Apps\pp-dgl, branch dgl/durable-goal-lease (also on origin: the W1b worker pushed it
unprompted). Goal `dgl` cap 17,000,000, chain envelope 16.0M. Plan: vault/plans/durable-goal-lease-2026-10-09.md
(Owner "y" 2026-10-09). Thesis: a goal is durable, a lease is disposable; cwd is location, never economic authority.

State (2026-10-10 11:40 local): PARKED in the PP backlog, entry D13 of vault/plans/deferred-backlog.md
(Owner: "put the rest of the mission in the backlog of claude power pack").
- W1 PARTIAL (design only). W1b DONE (lease epochs + succession CAS, test_goal_lease 10/10). W2 DONE eaadf11f
  (workspace_registry.py, binding precedence, fenced hooks, test_workspace_lease 10/10). Receipts: Wn-receipt.md.
- The chain refused W3 on envelope: used 11,154,078 + need 5,100,000 > 16,000,000. Task PP-DglChain-Tick is DISABLED.
- W3 packet + route are committed and ready. P3b-2 was already run by main pane a5308810, so W7 is verify-only.
- Bootstrap still needed until W3/W5: unit_done.py done_check, attached by dgl_chain_tick.ps1 on every arm (without it a
  packet mission stalls BLOCKED on GSD NO_PHASES).

Decisions: no edits to tools/gsd_mission.py / tools/mission_steward.py while ce-lifecycle-v3 has them dirty. Succession lives
in a new module called from the chain tick. No coordinator pane; never Set-Location into a goal root.

Next (only after the Owner raises the dgl cap; ~20-25M more for W3-W8, `--owner` on a TTY):
1. Raise the cap and the chain.json envelope together.
2. Enable-ScheduledTask PP-DglChain-Tick; the next tick arms W3.
3. Act only on chain rows `stopped_without_done`, `arm_refused`, `refuse_envelope`, or AUTHORITY_REQUIRED.

Start: read this file and backlog D13, then `gsd_mission.py status` and the last 5 lines of ~/.claude/state/dgl-chain-tick.log.
