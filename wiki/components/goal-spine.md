---
type: component
created: 2026-10-02
updated: 2026-10-02
sources: [2026-10-02-state-centric-reality-scan]
path: modules/gsd_x/goal/
status: LIVE
---

# Goal spine (GSD X goal)

Durable goal state that outlives sessions and workers. Built 2026-09-22..25 from the KobiiCraft
goal-spine plan; **LIVE since 2026-10-02**, when a scheduler first reached it
([[2026-10-02-state-centric-reality-scan]]).

## Parts and status

| part | what | status |
|---|---|---|
| goal log | append-only, hash-chained, CAS by exclusive create | LIVE |
| reconciler | next step as a pure function of durable state (`modules/gsd_x/goal/reconcile.py:165` @ `738ed40` is the only path to CONVERGED, and it needs a judge receipt) | LIVE |
| judge | re-runs every pinned gate at the final tree, separate from the builder | LIVE (G-001 PASS, 2026-10-02T20:44Z) |
| autonomy record | judge + chaos suites green on the engine that would run (`sweep.py:112` @ `738ed40`) | LIVE |
| scheduled sweep | `sweep_all` (`sweep.py:417` @ `738ed40`) via Windows task `PP-GoalSweep`, 5 min, gate epochs only | LIVE |
| goal discovery | from the store's directories, never a hand list (`sweep.py:184` @ `738ed40`) | LIVE |
| gate provider | runs a registered done gate, verdict tied to tree hash | LIVE |
| long-run provider, observe-only | adopt a running Ralph mission; cancel refused (`providers/long_run.py:247` @ `738ed40`) | LIVE in code; no real mission bound yet |
| codex / claude providers | spend quota; reported, never dispatched by the sweep | PLANNED for unattended use |

## Properties worth knowing

- **It refuses to run code nobody verified.** While engine files were dirty (edits, a mutation
  drill), every scheduled pass refused with a named reason (raw, S3 notes).
- **Silence is distinguishable from death.** `sweep_heartbeat.json` and `goal-sweep-pass.json`
  are written every pass, refusal included.
- **CONVERGED is re-derived on every read.** A later commit in the goal's worktree re-opens the
  obligations and the sweep re-gates them.

Related: [[goal-spine-connect-not-build]], [[verdict-pinned-to-what-runs]],
[[spec-acceptance-as-goal-obligations]].
