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

UPDATE 2026-10-08 ~15:30 UTC (coordinator claude-power-pack-c8):
- WU-1B DONE b62f9019 (receipt committed; LIFE 6/6, GOAL 54/54, HOOK 7/7, MC 224/225 pre-existing; 3 mutants killed).
  Mission m-8b571c4b78f7 then HALTED on its envelope. Its worker deferred the WU-1C arm to "a fresh pane" (TRAP).
- CORRECTED 15:50 UTC: an unidentified pane (not -3a, not -85; both denied it) briefly rewrote WU-1C as a slot swap,
  then reverted it and instead committed the Amendment C scope as an addendum to WU-1H (2bed6e14). Canonical chain:
  WU-1C (roots, 79350a8e) -> WU-1D -> WU-1H (+ Amendment C addendum). WU-1C2 (3c1c5f3e) is SUPERSEDED: a duplicate of
  WU-1C that nothing arms. Never arm it.
- m-1783bda2a44b = WU-1C. Hold released 15:50 UTC after the packet sha matched its envelope byte for byte (the revert
  had left CRLF-only differences; normalised to LF).
- Install hazard: the live checkout's hooks/session_budget_guard.js has six commits not on this branch
  (31f1e714..ffd8f9e9, merge-base 86ad6f16). WU-1B's Copy-Item recipe would REVERT them. The install must be a
  3-way merge. Install owner = a3b-r R3 (Amendment C C5), with one first-activation Owner command (HR-001).
- Route admission printed remaining=None, so it does not read goal authority. Packets carry the check until fixed.
- Authority at 15:20 UTC: remaining 1,426,798, open 489,605 (WU-1B leases, releasable). WU-1C+1C2+1D will
  likely exhaust it; WU-2+ and ctx-rent need ONE semantic authority decision.

Next 3 actions:
1. Sweep launches m-1783bda2a44b (WU-1C); confirm it via `gsd_mission.py status`.
2. Chain: WU-1C -> WU-1D -> WU-1H (each arms the next; WAITING_FOR_AUTHORITY if short).
3. After WU-1-receipt: a3b-r R3 installs by 3-way merge; then the reclassify op for fc54a743.
Start: read only this file, then action 1.
