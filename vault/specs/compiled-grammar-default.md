---
status: APPROVED (Owner "y", 2026-10-07, laptop session 08cb0d86)
covers: [compiled-grammar-default, mission-admission, packet-completion, renewal-guard, gsd-compile, mission-wait]
extends: vault/specs/edd-compiled-execution-canary.md, vault/specs/orca-p4-compiled-execution-canary.md
---

# The compiled-execution grammar is the automatic default for long GSD missions

## Why (measured, GEX44, 2026-10-06/07)
- EDD Phase 1 under the planner/researcher/executor grammar: 32,062,568 processed / 132 calls, 0 obligations closed;
  one researcher did one grep per call at 77k-407k context. Armed with no token envelope.
- Same phase as a compiled packet over a zero-model dossier: 3,310,496 (gate 13/13; sampled quality 6/8).
- Traps found running it: autocompact 120k below the measured worker floor 95.7k -> thrash, BLOCKED (UC-18); a
  finished packet relaunched for 2 more epochs (UC-19, 21.5% of the canary); at the cycle limit the supervisor
  RENEWED the mission (meter reset) and started re-running the finished packet (m-b63653ec5676); hold/breaker park
  but never stop an in-flight turn (UC-14); the orchestrating pane cost 17.41M vs the work's 2.60M (UC-20).
Evidence n=1 on a SCAN phase: the default keeps a sampled-quality audit and a logged legacy switch.

## Laws
1. ONE AUTHORITY AT THE EFFECT. Every path that starts a worker (arm, sweep relaunch, turn continuation, context
   rotation, renewal) passes the same admission inside the launch function, not beside one caller.
2. NO ENVELOPE, NO LAUNCH. A record without `token_estimate` is refused at launch, unless it carries an explicit
   `unbounded` authority (who, where recorded) set by a CLI flag. Absent is never read as unlimited.
3. WINDOW FROM THE FLOOR. `autocompact` (when set) must be >= measured floor of the worker profile
   (vault/config/route-floors.json) + packet bytes / 4 + working margin (default 40k). Unknown floor -> refuse with
   the derivation, never guess. Refusals name the numbers.
4. A PACKET ENDS ITS MISSION. A packet may declare `done_gate: <command>` (first line matching `^done_gate:`). At
   every point where the supervisor would continue, rotate or renew a packet mission, it first runs that gate in the
   work tree (bounded timeout): exit 0 -> COMPLETED with a ledger row carrying the gate's output tail; non-zero or
   timeout -> today's behaviour. A renewal never re-launches a packet whose gate passes.
5. COMPILE BY DEFAULT (G2). `/cpp-gsd-long` compiles a dossier + packet per roadmap phase and arms with
   `--wu-packet`; the old grammar runs only with `CPP_MISSION_GRAMMAR=legacy`, recorded in the ledger.
6. ORCHESTRATION BELOW THE MODEL (G2). Waiting, renewal-guarding and spend measurement are a tool
   (`tools/mission_wait.py`), not a model pane polling status.
7. KILL SWITCH. `CPP_MISSION_GRAMMAR=legacy` restores laws 2-5 to today's behaviour, and every use is ledgered.

## Packets
- G1 (laws 1-4, 7) in tools/gsd_mission.py + tests. Gate: `python3 tools/test_grammar_default.py` (V-GRAMMAR-*)
  plus the existing `tools/test_gsd_mission.py` and `tools/test_gsd_mission_envelope.py` with no new red.
- G2 (laws 5-6): tools/gsd_compile.py (uses tools/gsd_dossier.py), tools/mission_wait.py, commands/cpp-gsd-long.md.
  Gate: V-GRAMMAR-COMPILE-* + a live arm of EDD Phase 2 with no manual step, metered.

## Acceptance (G1)
- V-GRAMMAR-NO-ENVELOPE-REFUSED: launch of a record without token_estimate refuses on every launch path (arm with
  launch, sweep plan launch, continuation, renewal); with `--unbounded --authority` it launches and ledgers it.
- V-GRAMMAR-WINDOW-FLOOR: envelope/launch refuses autocompact below floor+packet+margin, admits at/above it; the
  refusal text carries the three numbers; an unknown profile floor refuses.
- V-GRAMMAR-PACKET-GATE-COMPLETES: a packet mission whose done_gate exits 0 goes COMPLETED instead of continuing,
  rotating or renewing; a failing gate keeps today's path; a gate that times out is not a pass.
- V-GRAMMAR-RENEWAL-NO-RERUN: a budget halt of a packet mission whose gate passes creates no successor.
- V-GRAMMAR-LEGACY-SWITCH: legacy restores old behaviour and writes a ledger row.
- Mutation: removing the launch-boundary check, or the gate-before-continue check, turns the matching test red.
- Existing V-MC and envelope suites: no new failures (GEX44 has 1 pre-existing environmental red,
  V-MC-PLAN-FACTS-REFUSES-OVERLAP; report it, do not fix it here).

## Rollback
Revert the G1 commits; or `CPP_MISSION_GRAMMAR=legacy` live without a revert. The live install changes only by an
explicit deploy step (cherry-pick + smoke + rollback point), which is a separate Owner-visible action.

## G1 result (independently verified 2026-10-07, laptop session 08cb0d86)
d4f18ca8 + a42e57ff (worker m-604666a514a3, 7,927,113 metered vs 8M estimate). V-GRAMMAR 41/41 incl. 4 mutation
drills red + unmutated control green; V-MC 224/225 with the same single red at base 4053b006
(V-MC-PLAN-FACTS-REFUSES-OVERLAP, pre-existing); ENVELOPE 39/39. The stall breaker parked G1 as a false positive:
its progress fingerprint reads the clone root and cannot see the worker's worktree (class of UC-04).
Review findings carried into WU-G2: F1 the done_gate line is read from a packet the worker can edit (sha256 recorded
but not checked) -> self-certified completion; F2 the gate runs in work_dir/cwd, not the worktree the work is in.
