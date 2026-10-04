# Handoff [N] -- event-driven cognition -> existing zero-LLM sweeps

Pillar: [N] event-driven cognition. Terminal: MERGED_INTO_EXISTING_OWNER (frozen rule: "zero-LLM scheduled
sweeps exist; no build").

Owners (frozen): `tools/goal_sweep.ps1`, `tools/gsd_long_run_sweep.ps1`.

## What was verified (2026-10-03 ~16:11 +02:00)

- Both are registered Task Scheduler entries, live, last result 0:
  `PP-GoalSweep state=Ready last=2026-10-03T16:10:48 result=0 next=16:15:47`;
  `PP-GsdLongRun-Sweep state=Ready last=2026-10-03T16:11:06 result=0 next=16:16:05`
  (command: `Get-ScheduledTask -TaskName <n> | Get-ScheduledTaskInfo`).
- Heartbeats prove each pass ran, not only that it is scheduled:
  `~/.claude/state/goal-sweep-pass.json` `{"outcome":"ran","rc":0,"timed_out":false,"secs":44.8}`;
  `~/.claude/state/gsd-sweep-heartbeat.json` stages mission rc 0 (27.2 s) and v2 rc 0 (1.3 s);
  `~/.claude/state/gsd-x/sweep_heartbeat.json` `goals_seen: 1, acted: [], refused: ""`.
- Zero model calls in the sweeps themselves: `goal_sweep.ps1` runs `gsd_x_goal.py sweep-all`, gate epochs only,
  "anything that spends an account is reported, never dispatched" (header lines 5-6); `gsd_long_run_sweep.ps1`
  runs `gsd_mission.py supervise` then the retired v2 stage (header lines 5-8). A supervise pass may CONTINUE a
  mission worker; that model work is the mission's own, not the sweep's.
- `python tools/test_gsd_x_goal_sweep.py` -> `GSDX_GOAL_SWEEP_PASS=14/14` (incl. V-SWEEP-NO-CODEX-EPOCH,
  V-SWEEP-SILENT-WHEN-IDLE).

## What the owner keeps

Scheduling, the lease/heartbeat contract, bounded stages. The campaign builds nothing for [N].
