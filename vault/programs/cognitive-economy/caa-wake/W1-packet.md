# caa-wake W1 — dependency-wait contract + zero-model wake consumer

Goal `caa-wake`, worktree `C:\Users\User\Apps\pp-caa-wake`, branch `ce/caa-wake`. Lease 1.3M + 0.3M reserve. Sonnet-class work, no Agent spawns.
Read ONLY: this packet; `vault/plans/event-driven-wake-caa-2026-10-08.md`; `tools/wake_check.py`; `tools/test_wake_flag_consumer.py`; `modules/gsd_x/goal/log.py`. Also read `git show ce/gen2-completion:tools/test_ce_t1_waiting.py`.
Do not read the bootstrap prompt or old coordinator transcripts.

## Durable output (mandatory)
Append each confirmed fact or decision to `vault/programs/cognitive-economy/caa-wake/W1-notes.md` AS YOU GO, before moving on. A cap hit costs the tail, never the whole.

## Build (EXTEND, do not fork)
1. **Wait record**: one JSON per wait under `~/.claude/state/mission-wait/` (dir overridable by env for tests). Required fields:
   - `wait_id`, `dependency_type` (`git_object` | `goal_state` | `owner_authority`);
   - `predicate` (`any_of`/`all_of` list of `{kind:"git_object", repo, ref, path}` and `{kind:"goal_status", goal, field, op, value}`);
   - `source`, `next` (`{action:"arm", cwd, command, max_cycles}` | `{action:"deterministic", argv}` | `{action:"none"}`);
   - `invalidators` (same predicate grammar), `owner_program`, `goal` (who pays), `created_at`;
   - `waits_on` (other wait_ids, for cycle detection).

   State lives on a gsd_x `GoalLog` per wait. States: WAITING -> SATISFIED -> CLAIMED -> CONSUMED | STALE | SUPERSEDED | DENIED. Transitions are seq-CAS appends, the singleflight. A receipt sha/blob id is recorded so replay is a DUPLICATE.
2. **Evaluator** (extend `wake_check.py`, or one sibling module it imports, with a CLI `--waits`):
   - Level-triggered: every pass re-evaluates every WAITING record against durable truth, so a dependency already true, or true while the evaluator was offline, is found.
   - `git_object` uses `git cat-file -e <ref>:<path>` and records the blob id (committed objects only, never the work tree).
   - It never invokes a model: reuse `run_gate`'s model-argv refusal and count `model_calls`.
   - Unreadable or unknown inputs -> REFUSED receipt and the state is unchanged (UNKNOWN is never SATISFIED).
3. **Wake admission** (deterministic, before any `next` action):
   - invalidators false;
   - downstream goal `mission_spend.py goal-status` remaining >= next lease;
   - no live mission already on `next.cwd` (`gsd_mission.py status`);
   - `route_admission` where it applies;
   - host free RAM >= 4 GB, or the launch is held (not denied).

   Verdicts: NO_WORK | DENIED | DETERMINISTIC | COGNITIVE | HELD, each with a receipt. DENIED and NO_WORK spend 0 model tokens. This is CAA's first canary (the 187,645-token coordinator case).
4. **Delta** (`--delta <wait_id>`): HEAD, the receipt blob, files changed since the plan's commit, live goals/missions overlapping `next.cwd`. JSON, no model.
5. **Cycle check**: a `waits_on` cycle -> DENIED on every member, with the cycle named.
6. Kill switch `CPP_MISSION_WAIT=off` -> evaluator no-op, records untouched.

## Proof (`tools/test_mission_wait.py`, V-WAIT-*, both poles each)
- Pre-satisfied dependency wakes on the first pass.
- Offline gap: satisfied, then evaluator run later -> wakes.
- Duplicate pass -> one CLAIM.
- Two concurrent evaluators -> one CLAIM (CAS).
- Invalidator true -> STALE, no launch.
- Goal exhausted -> DENIED, model_calls 0.
- No-work -> NO_WORK.
- Unreadable record -> REFUSED.
- Cycle -> DENIED.
- Kill switch.
- Work-tree-only file does NOT satisfy.

Fixtures: a throwaway `git init` repo plus a temp goals root; never the live state dir.

Mutants (each must turn a named gate red, using `tools/mutation_drill.py` on an isolated copy):
- edge-triggered evaluation;
- claim without CAS;
- skipped invalidator check;
- work-tree read instead of cat-file;
- UNKNOWN treated as satisfied.

Also run `tools/test_wake_flag_consumer.py` (must stay green) and port the gen2-completion waiting assertions that apply.

## Finish
- Write `vault/programs/cognitive-economy/caa-wake/W1-receipt.md`: decision / effect / proof (gate lines verbatim) / unknowns / spend / reforecast.
- Micro-commit by pathspec on ce/caa-wake. No push.
- Then arm W2 yourself: `gsd_mission.py arm` with cwd this worktree, command `Read vault/programs/cognitive-economy/caa-wake/W2-packet.md and execute it.`, rollover-protocol capsule-v2, max-cycles 6, max-hours 8. Write W2-packet.md first, from the plan's W2 row plus what you learned.
- End the turn with a HANDOFF NOTE. Do not wait on workers.
