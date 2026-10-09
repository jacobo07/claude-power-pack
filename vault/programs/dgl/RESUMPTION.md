# RESUMPTION -- dgl (durable goal / disposable lease)

Identity: worktree C:\Users\User\Apps\pp-dgl, branch dgl/durable-goal-lease (local only). Goal `dgl` cap 17,000,000,
chain envelope 16.0M. Plan: vault/plans/durable-goal-lease-2026-10-09.md (Owner "y" 2026-10-09). Thesis: a goal is
durable, a lease is disposable; cwd is location, never economic authority.

State (2026-10-09 23:50 local):
- E0 DONE: P3b assets durable in the PP repo (bdbe4f35 by another pane + d0c2077b); chain committed 70c7d252.
- W1 armed by the chain tick: mission m-98529a59a4b6, ADMISSIBLE (need 1,704,024), sonnet, capsule-v2. Launched by
  the 5-min sweep.
- Chain driver: Task PP-DglChain-Tick (15 min) -> dgl_chain_tick.ps1 -> gsdx_chain.py tick --chain chain.json.
  Decisions: ~/.claude/state/gsdx-chain.jsonl rows with goal=dgl; wrapper log ~/.claude/state/dgl-chain-tick.log.
- P3b-2 is NOT running: control drift on the 5 PROVEN rows. W7 waits for D2-owner.md (Owner's a/b choice).

Decisions: no edits to tools/gsd_mission.py / tools/mission_steward.py while ce-lifecycle-v3 has them dirty. Succession lives
in a new module called from the chain tick. No coordinator pane; never Set-Location into a goal root.

Act only on: chain rows `stopped_without_done`, `arm_refused`, `refuse_envelope`, or AUTHORITY_REQUIRED.
Otherwise read the newest Wn-receipt.md and wait for the tick.

Start: read this file, then `gsd_mission.py status` and the last 5 dgl rows of gsdx-chain.jsonl.
