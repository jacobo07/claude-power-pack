# Incident: execution plane mismatch between directive, mission card and harness (2026-10-24 to 2026-10-25)

**Class:** EXECUTION PLANE MISMATCH -> THE PLACE WORK MUST HAPPEN AND THE PLACE THE WORKER MAY WRITE DISAGREE.
No code defect. Three authorities named three different places to work, and the mission ran for phases
1 to 7 on a workaround that was recorded, reversible and internal, but that changed how every commit
reached the branch.

## Symptom

- The Owner directive said to work in the clone with no worktree. The mission card bound the worker to the
  worktree `.claude/worktrees/flow-compression-w` (STATE.md lines 37 and 42).
- Executors could not write the clone. The harness guard for isolated agents refused writes outside the
  bound worktree, and the executor dispatch demands a fresh worktree (STATE.md line 94).
- Plans therefore ran through general-purpose agents in the bound worktree, and each commit was merged into
  the clone with a fast-forward-only merge afterwards. The bound branch `worktree-flow-compression-w` does
  not match the `agent-*` allow-list of the pre-commit branch assertion, so only the protected-branch case
  of that assertion was enforced (STATE.md line 56).
- In phase 8 the planner subagents were again blocked from writing the clone (STATE.md line 106).

## Timeline (local time, CEST)

| when | what | instrument |
|---|---|---|
| 2026-10-24 (epoch 6) | phases 1 to 4 done in the clone on branch mission/flow-compression; the stale worktree (f7ee5b7d) is not used (b9ff692d) | git log, STATE.md line 37 |
| 2026-10-24 20:52:35 | decision recorded: keep committing in the bound worktree and fast-forward merge into the clone (6e53b7a8) | STATE.md line 42 |
| 2026-10-24 22:08:50 | decision recorded: the allow-list does not match the bound branch; only the protected-branch case enforced (eaa3f426) | STATE.md line 56 |
| 2026-10-25 07:07:24 | phase 7: executors cannot write the clone, plans ran in the bound worktree (c1d17703) | STATE.md line 94 |
| 2026-10-25 | phase 8 by Owner directive: work in the clone, no worktree, no push (plan 08-01 context) | 08-01-PLAN.md |
| 2026-10-25 this phase | `git worktree list` shows the clone plus three linked worktrees | the command |

## Root cause

The directive, the mission card and the harness were written at different times by different authorities
and nothing reconciled them before the first executor was dispatched. The harness rule (isolated agents
write only inside their worktree) is correct; the directive (no worktree) is correct; they cannot both
hold for a subagent.

## Why the existing rule did not prevent it

The rules name the right plane for each side but have no step that compares them at arm time. The
pre-commit branch assertion assumed per-agent branch names, which the orchestrator-designated branch
never had.

## Earliest discoverable point

Arm time. A preflight that reads the directive, the mission card's bound path and the harness's write
boundary and requires them to agree would have refused the first dispatch with a named mismatch instead
of a runtime refusal.

## Repair

No code repair. Decisions recorded (b9ff692d, 6e53b7a8, eaa3f426, c1d17703), all reversible and internal:
bound worktree plus fast-forward-only merge for phases 5 to 7; the clone itself for phase 8 by Owner
directive. No push at any point.

## Test

There is no code gate for this class and none is invented. The evidence is the recorded decisions and the
scheduler check that the mission continued to advance.

- commit: b9ff692d
- commit: 6e53b7a8
- commit: eaa3f426
- commit: c1d17703
- check: init-progress

## Pattern

Before the first dispatch, the directive's plane, the mission card's bound path and the harness's write
boundary are compared, and a disagreement is a named stop, not a workaround found at run time.

## Open debt

- No arm-time check compares the three planes. Owner: the S2 arm preflight (not changed in this mission;
  FC-10 forbids new policy here).
- The pre-commit branch assertion still assumes `agent-*` names for linked worktrees.
