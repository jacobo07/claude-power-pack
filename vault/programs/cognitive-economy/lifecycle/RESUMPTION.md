# RESUMPTION -- ce-lifecycle-v2 (lifecycle vertical slice, recovery lineage)

Identity: worktree C:\Users\User\Apps\pp-ce-lifecycle-v2, branch ce/lifecycle-v2 off e71f3a0b. Goal ce-lifecycle-v2,
cap 3,247,012 (8M program remainder, worst-case opens; accounting in vault/plans/ce-lifecycle-WU-1R-recovery-plan-2026-10-08.md).
Predecessors: ce-lifecycle (exhausted), ce-lifecycle-v (bricked at -3,608,719 by the retroactive bind of pane fc54a743).
Thesis: one lifecycle decision for context and lease edges; refuse before the model; successor by the sweep, never by Owner.
Master plan: vault/plans/ce-lifecycle-v2-bootstrap-master-plan-2026-10-08.md (APPROVED, Owner "y" 2026-10-08).

Sealed: WU-0 (dcd3d82e); WU-1 step 1 (9bc030c9); salvage patch (e71f3a0b); WU-1F (e634546d, UNREPRODUCED 7/8,
run 1 INTERFERENCE). WU-1B armed BY THE WU-1F WORKER as m-8b571c4b78f7 and launched by PP-GsdLongRun-Sweep: no pane,
no Owner step (production evidence for the bootstrap canary, 2026-10-08 ~14:52 UTC).
Running: WU-1B (m-8b571c4b78f7). Packets written ahead: WU-1C, WU-1D, WU-1H (+ routes).
Chain: WU-1B -> WU-1C -> WU-1D (closes WU-1, writes WU-2 packet, consolidated deploy recipe) -> WU-1H (halt continues)
-> WU-2 only if remaining - open >= lease + reserve + 300K.

Decisions: one live writer; each unit commits, writes its receipt and arms the next if that packet + route exist.
The coordinator writes the next packet + route ahead of time. Arm recipe:
arm --cwd <this wt> --command /gsd-autonomous --no-launch --rollover-protocol capsule-v2 --max-cycles 3 --parallel-unit lc-WU-N;
envelope --mission <id> --wu-packet <abs WU-N.md> --token-estimate <lease+reserve>; admit --mission <id> --route <abs route-WU-N.json>.
Coordinators never cd into a goal root (git -C, absolute paths).
Install: after WU-1D's receipt, the coordinator applies its consolidated recipe to the live checkout by pathspec
commit (the live guard is ~/.claude/skills/claude-power-pack/hooks/session_budget_guard.js via the dispatcher),
verifies sha256 + the four suites there, then appends a `reclassify` journal op for fc54a743 (6,855,731 ->
PRE_BINDING_PROGRAM_CAPEX) on ce-lifecycle-v. WU-1H's gsd_mission.py change is installed the same way after its receipt.
Open debt: deterministic approval consumer (arm the next listed unit when a COMPLETED unit's receipt exists but it did
not arm) -- today the chain is worker-driven; packet it after WU-1H. ctx-rent untouched until then.

Next 3 actions:
1. When WU-1B-receipt.md lands: read its verdict; check that WU-1C was armed (`gsd_mission.py status`).
2. When WU-1-receipt.md lands: perform the install described above.
3. Update this file.
Start: read only this file, then action 1.
