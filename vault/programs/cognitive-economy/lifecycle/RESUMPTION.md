# RESUMPTION -- ce-lifecycle-v (lifecycle vertical slice)

Identity: worktree C:\Users\User\Apps\pp-ce-lifecycle-v, branch ce/lifecycle-v off dcd3d82e. Card
vault/plans/ce-lifecycle-vertical-slice-plan-2026-10-08.md (APPROVED, Owner "y A"). Goal ce-lifecycle-v, cap 5,126,080
(remainder of the unchanged 8M program envelope; accounting in WU-0-receipt.md). Old goal ce-lifecycle: exhausted,
still holds root pp-ce-lifecycle (removed by WU-1 goal-unroot). Old worktree pp-ce-lifecycle is quiescent.
Thesis: one lifecycle decision for context and lease edges; refuse before the model; successor by the sweep, never by Owner.

Sealed: WU-0 (commit dcd3d82e; goal declared 10:04:33Z; WU-1 armed m-3403c155ecb8 PREPARED, route ADMISSIBLE
need=608,619 target=900,000, envelope wu_packet=WU-1.md token_estimate 1.15M, capsule-v2, max 6 cycles / 8 h).
Pending: WU-1..WU-8 (plan section 3).
AMENDMENT A1 (APPROVED 2026-10-08, vault/plans/ce-lifecycle-amendment-A1-executable-authority.md): WU-2 +0.15M
(ctx-rent lineage in the program envelope), WU-4 +0.35M (executable authority + mutation edge, 4 V-LIFE gates),
WU-5 production canary = ctx-rent S2 on pre-authorized tranche T-S2 1.9M. Every WU packet from WU-2 on must cite A1.

Decisions: one live writer mission on this branch; each WU writes the next packet + route; until WU-5 lands, the
WU's own worker (or any coordinator) arms the next packet whose predecessor receipt exists:
arm --cwd <this wt> --command /gsd-autonomous --no-launch --rollover-protocol capsule-v2 --parallel-unit lc-WU-N;
envelope --wu-packet <abs WU-N.md> --token-estimate <lease+reserve>; admit --route <abs route-WU-N.json>.
Hook deploys: recipes accumulate in receipts; WU-7 installer applies them (no Owner Copy-Item).

Next 3 actions:
1. When WU-1-receipt.md lands: re-run tools/test_process_lifecycle.py; exit 0 required.
2. Arm WU-2 as above (lease 1.25M).
3. Update this file.
Start: read only this file, then action 1.
