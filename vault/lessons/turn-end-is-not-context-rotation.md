# A turn that ends is not a context that ran out

**Date:** 2026-09-28 · **Fix:** `5eee90a` `717554f` `dce125b` `add6828` `5bf5729` ·
**Gate:** `tools/test_gsd_epoch.py` (V-EPOCH-*) · **Owner:** pane `claude-power-pack-c2`
**Epistemic status:** mechanism CONFIRMED (code read + ledger census + host probe + live mission);
the historical counts are CLASSIFIED from recorded reasons plus witnesses (basis named per epoch);
multi-rotation live proof: see "Live proof" below — state it exactly as that section does.

## Symptom
Across 43 missions, 499 fresh worker sessions had been launched, and the record read as "hundreds
of context rotations, production-proven". Measured: 434 were a worker's **turn ending**, 10 were the
context wall, 9 recoveries, 3 launch retries, 26 first launches, 18 renewals. The prior correction
("1 of 499 was the wall") was itself wrong in the other direction.

## Impact
- Every turn end paid the startup floor again: **186,856 tokens resident at call #1** (worker
  4aa2e2d3; 70 % of it the `instructions` attachment, 550,663 bytes), written as a 1-hour cache entry,
  and the worker's working memory was thrown away.
- No launch said why it happened, so turn continuation, recovery and rotation shared one counter;
  a certification counting fresh sessions could not tell them apart.

## Root causes
1. `plan_next` mapped *owner idle* → `relay`, and a relay was always a fresh `claude --bg`. The
   host's same-session primitive was never tried: after `claude stop`, `claude --bg --resume <sid>
   "<prompt>"` with **no other flag** continues the same id, transcript and context (probe
   `7a42f96f`: "SAME_SESSION_CONTINUED True CONTEXT_PRESERVED True"). With any flag the host starts
   a COPY ("keeps its own saved options, so the flags you passed started a copy").
2. The wall never reached the mission record. `hooks/mission_wall.js` writes only a flag file; the
   Stop hook then writes `handoff_already_asked`. The supervisor saw a wall-driven hand-off as an
   ordinary "turn ended" relay.
3. A finished background turn is listed by the host as `done` as well as `idle`; `done` read as
   DEAD and planned a *replace*, bypassing any turn-end logic (m-47fe0c6cb54a, 2026-09-28 00:01Z,
   last row `end_turn`, relaunched fresh as "owner dead").

## Why the defences failed
- **One counter for three events.** "Fresh sessions" stood in for "rotations"; nothing forced a cause.
- **An instrument that could only see one witness.** The "1 of 499" count keyed on `handoff_asked`;
  the mid-turn wall leaves a flag and `handoff_already_asked`, so it could never have found the others.
- **A synthetic relay certified the mechanism.** One W8 relay proved the *transport*; it said nothing
  about how often production rotated or why.

## Repair
`tools/gsd_epoch.py` decides at every turn end: a pending background child (main transcript or a
subagent sidechain, or an unconsumed notification) → HOLD, nothing stopped; wall witnessed for this
epoch or explicit hand-off → fresh `CONTEXT_ROTATION`; ≥ 300k resident tokens → fresh
`CONTEXT_ROTATION` (economic: a resumed process re-writes the prefix — probe turn 2 wrote 125,483 and
read 33,949 — so continuing costs ~current context and a fresh worker ~floor); otherwise the SAME
session continues. The continuation claim moves the mission to LAUNCHING at the same epoch, so a
rival supervisor loses its CAS. Every launch ledgers `launch_cause`; SessionStart `compact` →
`epoch_compacted`; `certify` counts a rotation only with five independent witnesses.
Kill switch: `CPP_MISSION_CONTINUATION=off`.

## Proof
Gates 71/71, including crash points (after stop, after claim, after wake, budget mid-continuation).
Mutation drills on an isolated copy of `tools/`: 11/11 killed. `test_gsd_mission` 190/190.
Adversarial review by pane e9 found F1 (continuation did not record `work_dir`) — fixed in `dce125b`.

## Live proof
Mission `m-916e905e23d4` (gsd-long-smoke worktree, wall 29/30/28 % ≈ 300k of 1M) was launched by
the production sweep with `launch_cause INITIAL/fresh`; the worker entered the worktree and grew
from 19 % to 24 % in ~50 min (its subagents do the work, so the parent grows slowly).
Result of the rotations: recorded in `vault/specs/parent-context-epoch-rotation.md`
§5 "Live proof (S10)", from `gsd_epoch.py certify`, never from the mission's own output.

## Transferable lesson
Name the lifecycle event before you count it. When a system restarts a unit of work, record **why**
at the moment it decides — turn end, context pressure, crash, retry, quota — and certify each class
by its own witnesses. A count of restarts is not a count of any one cause, and an instrument that
reads one witness can only ever confirm the cases that leave that witness.
