---
id: SPEC-GOAL-SWEEP-SCHEDULED
title: Scheduled goal sweep -- autonomous goals advance with nobody watching
tier: T2
status: approved
covers: [goal-sweep-scheduled, sweep-all, goal-autonomous, state-centric-s2, test_gsd_x_goal_sweep_all]
owner_go: "y" (plan of record, 2026-10-02) + "b" (G-001 autonomous, production read-only bot gate accepted)
parent: vault/plans/state-centric-cognition-reality-scan-2026-10-02.md (S2); goal-spine plan C12
---

# SPEC -- Scheduled goal sweep

## Problem (measured 2026-10-02)

`modules/gsd_x/goal/sweep.py` exists and is tested, but nothing schedules it, no CLI marks a goal
autonomous, and the goal store does not record which root a goal runs in, so even a scheduled
sweep would have nothing to enumerate. The retry key carried repo HEAD, which moves every
7.6 min in the shared tree: every retry of a failing gate would count as new information.

## Behaviour

1. `gsd_x_goal.py autonomous --goal G --root R --on|--off --reason TEXT` appends
   `goal.autonomous {enabled, reason, root}`. The root must be a directory holding a git work
   tree whose repo id equals the goal's repo id; otherwise refused. `--off` needs no root check.
2. `sweep.autonomous_goals(base)` DISCOVERS goals from the store (every `<repo>/<goal>` dir that
   is a valid log). For each, the latest `goal.autonomous` event decides. Enabled without a
   recorded root, root missing on disk, or an unreadable log -> listed as skipped WITH the reason,
   never silently dropped.
3. `gsd_x_goal.py sweep-all [--dry-run]` = `sweep()` over those goals. Silent when nothing
   happened (existing render contract).
4. Every `sweep-all` run (including a refusal) writes `sweep_heartbeat.json` beside the autonomy
   record: `{ts, refused, acted, skipped, goals_seen}`, so a missed run is distinguishable from a
   quiet one.
5. The engine term of the retry key is `engine_identity` (fallback `runtime_identity` when the
   engine cannot be identified), so an unrelated commit is not new information.
6. Schedule: a Windows task `PP-GoalSweep` every 5 min, launched hidden like its sibling
   `PP-GsdLongRun-Sweep` (which is left untouched).

Unchanged: the autonomy precondition (judge + chaos green on this engine), gate-only dispatch,
reporting (never dispatching) anything that spends, the REALITY gate-class refusal.

## Acceptance (`python tools/test_gsd_x_goal_sweep_all.py`)

- autonomous on with a matching root -> discovered with that root (firing control).
- off, never marked, root missing, root of another repo (refused at write), enabled without
  root (legacy event) -> not swept, each with a named skip or refusal.
- retry key: two contexts differing only in repo HEAD produce the same engine term.
- heartbeat written on an acting run AND on a refused run.
- `sweep-all --dry-run` dispatches nothing.
- Existing suites unchanged: `test_gsd_x_goal_sweep.py`, mutation drill.

## Production Reality

`sweep_heartbeat.json` advancing every ~5 min on this host, and G-001's log gaining sweep-actor
events (gate epochs dispatched and harvested) after it is marked autonomous.

## Rollback

`gsd_x_goal.py autonomous --off`, or disable the `PP-GoalSweep` task, or revert. Goal logs are
append-only; nothing is rewritten.
