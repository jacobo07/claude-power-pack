# RESUMPTION -- ce-lifecycle-v2 (lifecycle vertical slice, recovery lineage)

Identity: worktree C:\Users\User\Apps\pp-ce-lifecycle-v2, branch ce/lifecycle-v2 off e71f3a0b. Goal ce-lifecycle-v2,
cap 3,247,012 (8M program remainder, worst-case opens; accounting in vault/plans/ce-lifecycle-WU-1R-recovery-plan-2026-10-08.md).
Predecessors: ce-lifecycle (exhausted), ce-lifecycle-v (bricked at -3,608,719 by the retroactive bind of pane fc54a743).
Thesis: one lifecycle decision for context and lease edges; refuse before the model; successor by the sweep, never by Owner.

Sealed: WU-0 (dcd3d82e); WU-1 step 1 (9bc030c9); salvage patch of WU-1 steps 2-4 (e71f3a0b, SALVAGE_PENDING_VERIFICATION).
Pending: WU-1F (armed, see below) -> WU-1B -> WU-1C -> WU-1D -> WU-1H; then WU-2.. per the vertical-slice plan and A1,
admitted only if the measured cost rate allows (2.95M safe authority buys ~85 model calls at 34K/call).

Decisions: one live writer; each unit commits, writes its receipt and arms the next if that packet + route exist.
The coordinator writes the next packet + route ahead of time. Arm recipe:
arm --cwd <this wt> --command /gsd-autonomous --no-launch --rollover-protocol capsule-v2 --max-cycles 3 --parallel-unit lc-WU-N;
envelope --mission <id> --wu-packet <abs WU-N.md> --token-estimate <lease+reserve>; admit --mission <id> --route <abs route-WU-N.json>.
Coordinators never cd into a goal root (git -C, absolute paths). Hook deploys: recipes in receipts, WU-7 applies them.

Next 3 actions:
1. When WU-1F-receipt.md lands: read its verdict. If WU-1B was armed, check `gsd_mission.py status`.
2. Write WU-1C.md + route-WU-1C.json (lease 0.4M + 0.1M, 12 calls) before WU-1B finishes.
3. Update this file.
Start: read only this file, then action 1.
