---
id: SPEC-GOAL-OBSERVE-RALPH
title: A goal observes a running Ralph mission without owning it
tier: T2
status: approved
covers: [goal-observe-ralph, bind-mission, state-centric-s3, test_gsd_x_goal_bind_mission]
owner_go: "y" (plan of record 2026-10-02, default 5: observe-only, never pause or re-arm) + "y" (start S3)
parent: vault/plans/state-centric-cognition-reality-scan-2026-10-02.md (S3); goal-spine plan C7 (observe-only)
---

# SPEC -- Observe a running Ralph mission from a goal

## Problem (measured 2026-10-02)

Ralph missions (`tools/gsd_mission.py`) are the live long-run path: 79 records, 3 RUNNING now
(InfinityOps, this repo, KobiiCraft Core Files), none bound to a goal. `providers/long_run.py`
can bind a v2 session or ARM a new v3 mission, but cannot adopt one that is already running,
and its `cancel` halts any mission it holds. No CLI reaches the provider, and the sweep observes
only gate epochs, so a long-run epoch would leave its goal at "could not observe" forever.

## Behaviour

1. `LongRunProvider.dispatch({"bind_mission": id, ...})` loads the mission; refuses a missing
   or TERMINAL one; writes the token marker `{mission_id, observe_only: true}` and returns
   handle `{mission_id, token, bound_at, observe_only: true}`. It never calls `arm`, never
   transitions the record.
2. `cancel` on an observe-only handle is REFUSED (EpochError naming the mission owner's own
   command). Armed (non-observe) handles keep today's behaviour.
3. `probe` finds a bound mission through its token marker (mission_id branch), so a crash
   between intent and handle adopts the binding instead of losing it.
4. `gsd_x_goal.py bind-mission --goal G --root R --mission ID --reason TEXT` opens one
   `cpp-gsd-long` epoch (hypothesis `initial`, key from revision + provider + scope + engine +
   mission id), dispatches the bind, marks it running. The mission's cwd must hold the goal's
   repository (repo id match), else refused before any append.
5. The sweep observes running epochs of BOTH providers and harvests/recovers each through its
   own provider. A long-run receipt carries no verdicts (unchanged): the mission ending proves
   nothing; the gates re-run on the tree it left.

Unchanged: one epoch per goal (a bound mission holds the slot while it runs), gate-only
dispatch by the sweep, no write to any mission record.

## Acceptance (`python tools/test_gsd_x_goal_bind_mission.py`, fixture mission store)

- bind a RUNNING fixture mission -> epoch running, handle observe_only, record bytes unchanged.
- bind a missing / COMPLETED mission -> refused, nothing appended.
- bind a mission whose cwd is another repository -> refused, nothing appended.
- cancel on the bound handle -> refused; record still RUNNING.
- probe with the epoch identity -> returns the bound handle.
- sweep pass while the mission RUNS -> no harvest, no new epoch (WAIT); after the fixture
  record turns COMPLETED -> harvested, epoch ended `completed`, no verdicts applied.
- Existing suites unchanged: long_run provider, sweep, sweep-all, mutation drill.

## Production Reality

One real RUNNING mission bound to a goal of the same repository, observed by `PP-GoalSweep`
until it ends. Needs an Owner-chosen goal: a goal's intent is the Founder's words, so no goal
is invented for a peer's mission.

## Rollback

Revert. A bound epoch can be ended with the existing epoch end path; the mission is untouched.
