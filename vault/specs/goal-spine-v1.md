---
covers: [goal-spine, goal spine, durable goal, goal convergence, goal reconciler, execution epoch, goal revision]
status: IN-PROGRESS
tier: T3
approved: 2026-09-22 (Owner, inline ULTRA plan)
---

# Goal Spine v1 — durable Goal convergence over existing runtimes

## Objective
A Goal handed over once is owned to convergence across sessions, agents, context
resets, failures and bounded execution epochs. Completion is never declared because
one agent, one GSD milestone or one `/cpp-gsd-long` run finished.

## Scope — the only truths the spine owns
Goal intent (verbatim), identity, revision, outcome contract, declared required
obligation ids, authority, budget, lifecycle state, persisted convergence receipt.
Measured 2026-09-22: no existing Power Pack or KobiiCraft module owns any of these.

## Reused, never re-owned
| Truth | Owner |
|---|---|
| GSD phase / milestone | GSD |
| Mission Contract (called with in-process intent + obligations) | `modules/gsd_x/mission/contract.py` |
| Obligation type, lifecycle, persistence (goal-scoped namespace) | `modules/gsd_x/mission/{obligation,store}.py` |
| Closure arithmetic — **the judge** | `modules/gsd_x/mission/closure.py` |
| Evidence strength | `modules/done_gate/strength_ladder.py` |
| Epoch runtime, budget, resume, started-signal | `/cpp-gsd-long` (`tools/gsd_long_run.py`) |
| Owner decisions | `modules/owner_queue` |
| Production Reality | the project's verifier (KobiiCraft: `scripts/verify_change.py`) |

## Acceptance criteria
1. A Goal survives process restart and is reconstructed from durable state alone.
2. A whitespace-only intent edit is not a new revision; a semantic edit is.
3. A Goal cannot be declared without required obligation ids.
4. CONVERGED is reachable only from a convergence verdict computed by GSD X closure,
   and only when every declared required obligation is present and closed.
5. An empty or missing obligation store never converges a Goal.
6. BLOCKED requires a named external condition from a closed set.
7. Two writers cannot both save the same Goal version.
8. An epoch is STARTED only when the exact prepared command was submitted after it
   was prepared; a marker is never written for a session the spine does not own.
9. A retry with an unchanged structured fingerprint is refused.
10. A provider DONE without evidence satisfies nothing.

Gates: `tools/test_goal_spine.py` (`V-GOAL-*`), plus
`tools/test_gsd_x_mission_goal_scope.py` for the GSD X extension.

## Non-goals
Goal Hypervisor, Execution Colonies, Method Router marketplace, Factory Treasury,
Goal Civilization, Futures Simulator, Proof Market, Self-Play, Portfolio Intelligence,
BMAD, Superpowers-as-orchestrator, autonomous keystrokes into panes, a second GSD
lifecycle, a second evidence store, a second promotion authority.

## Rollback
Revert `modules/goal_spine/` and the goal-scope extension in GSD X's store (its
default path is unchanged, so the revert is inert for existing missions). Goal state
lives only under `~/.claude/state/goal-spine/`.

## Status
Plan of record: `~/.claude/plans/shimmying-conjuring-hanrahan.md`.
This file is updated as each stage lands.

| Stage | Commit | Evidence |
|---|---|---|
| G2 GSD X goal-scope + `o.id` crash fix | `141d1ae` | `test_gsd_x_mission_goal_scope.py` 5/5 (1/5 before); `test_gsd_x_mission.py` 17/17 unchanged |
| G1 Goal record + store | (this commit) | `test_goal_spine.py` 15/15 |

### Mutation record — G1
Judged by the pre-existing `tools/mutation_probe.py` (auto-generated mutants), not
only by a hand-picked drill. The hand-picked drill first scored 6/6 against a suite
that the independent probe then scored **store 4/15, goal 18/24**. After closing the
real gaps: **store 11/15, goal 21/24.** Every remaining survivor is classified:

| Survivor | Class | Why |
|---|---|---|
| store:75, store:94 (`indent`, `ensure_ascii`, `sort_keys`) | EQUIVALENT | JSON formatting; the round-trip is byte-for-byte identical in meaning |
| goal:112 (`version` default 0→1) | EQUIVALENT | `store.save` overwrites `version` from `expected_version` |
| goal:104-105 (budget constants) | NOT YET REACHABLE | consumed first by the reconciler (G5), whose cap gates pin them |

Two instrument failures in this stage, both mine: a hostile-namespace gate that
counted `TypeError` as a refusal and went green 6/6 against code with no namespace
support; and a scratchpad drill that scored a CRASHED suite as a SURVIVED mutant.
