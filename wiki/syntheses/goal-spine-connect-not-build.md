---
type: synthesis
created: 2026-10-02
updated: 2026-10-02
sources: [2026-10-02-state-centric-reality-scan]
---

# Goal spine: connect, not build

Question: what did it take to make "state-centric" work real in PP? Answer: almost no new
capability. Wiring, and fixing the two things that made the wiring impossible
([[2026-10-02-state-centric-reality-scan]]).

## What was missing (measured)

| gap | evidence | fix |
|---|---|---|
| no caller | 0 hooks/commands/tasks reach `modules/gsd_x/goal` | `PP-GoalSweep` task + `sweep-all` (`61914f9`, `e9cb7b5`) |
| precondition unsatisfiable | record pinned to HEAD; median 7.6 min between commits | pinned to engine closure (`c4c45b7`); [[verdict-pinned-to-what-runs]] |
| no way to enumerate | store keyed by repo id, no path; no CLI to mark autonomous | `autonomous --root`, discovery from store (`61914f9`) |
| retry key on HEAD | every unrelated commit = "new information" | engine term (`61914f9`) |
| REALITY obligation without class | sweep would refuse it forever | re-accepted `in_game` (goal log, 2026-10-02) |
| long runs unobservable | sweep observed gate epochs only | per-provider observe/harvest (`738ed40`) |

New code: ~700 lines incl. tests. New concepts: none.

## Proof

G-001 (wake the GEX44 smoke runner, read the Lobby hotbar through the production proxy):
7 obligations re-proved by the scheduler with nobody watching, one per 5-min pass, 19:14Z-20:30Z;
`ob-reality` `GOALLIVE_PASS=4/4` via a real bot; judge PASS at 20:44Z, 34 s, every pinned gate
re-run (goal log, 2026-10-02). Owner authorised unattended production read-only contact ("b",
Owner, 2026-10-02).

## Pattern

Interpretation: this is [[overview]] points 5-6 again: machinery built, tested, unreachable.
The difference here is that the missing piece was small and the machinery was sound, so the
cheapest path to the capability was a caller, not a redesign. PP's own HR-NOVELTY-001 predicted
this (6 of 6 prior mega-proposals were mostly owned already).

## Not proven

- Observe-only Ralph binding on a real mission: needs an Owner goal (no goal is invented for a
  peer's mission).
- Transfer to a second repo with zero engine change (goal-spine L3).
- Any work epoch (Codex/Claude) unattended: still report-only by design.

Related: [[goal-spine]], [[spec-acceptance-as-goal-obligations]], [[mutation-anchor-rot]].
