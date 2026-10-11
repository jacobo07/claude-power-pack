# Phase 3 Research: W2 Execution frontier and scheduling

**Researched:** 2026-10-11 (WU-P3, worker-written; HR-PREMISE-001 applied)
**Scope:** premise-verify every function/module Phase 3 touches. Reuse Phase 2 seams; no new stores.

## 1. Verified premises (file:line, read this session)

| # | Premise | Evidence | Verdict |
|---|---|---|---|
| P1 | `decide(ctx: Context) -> Decision` is a pure function of `Context` | `reconcile.py:124-244`; no I/O, no clock besides `ctx.now` | HOLDS |
| P2 | `Decision` is frozen with `kind, reason, epoch_id, spec, provider, hypothesis, info_key, packet` | `reconcile.py:49-58` | HOLDS (legacy equality compares all 8 fields) |
| P3 | `Context` fields: `state, tree_hash, scope_hash, observations, judge, now, budget, providers, blocked_on, engine` | `reconcile.py:61-74` | HOLDS. `budget` is a Context field but `sweep` passes `state.budget` (`sweep.py:311`) |
| P4 | Step order in `decide`: RECOVER(dispatching) -> per-epoch loop returning WAIT/HARVEST at the FIRST running epoch -> BLOCKED(stop) -> closure -> blocked_on -> budget -> NEXT_EPOCH(gate, ungated[0]) -> NEXT_EPOCH(work, failing[0]) -> ESCALATE | `reconcile.py:129-244` | HOLDS. This is the global WAIT: `reconcile.py:140-150` returns on the first running epoch, hiding later epochs and all independent work |
| P5 | Step 5 never excludes an obligation that has an OPEN gate epoch; it relies on the one-open-epoch rule plus `info_key` dedupe | `reconcile.py:200-208`: `judged` counts only COMPLETED/FAILED; the dedupe tests only `UNSUCCESSFUL` outcomes | **NEW HAZARD** for N epochs: frontier mode must exclude obligations with an open epoch itself (`epoch.begin` refuses same `info_key` while open, `epoch.py:278-279`, but `decide` would still select it first and starve the rest) |
| P6 | `epoch.begin` refuses a second open epoch | `epoch.py:283-286` (`still_open`) | HOLDS. The exact place to relax, by `unit` independence |
| P7 | Fence minted as `max(fence)+1`; CAS append at `last_seq+1` makes two racers one-winner (`LostRace`) | `epoch.py:288-296` | HOLDS. Concurrent begin from one stale state loses at CAS |
| P8 | `ingest_receipt` compares a receipt with ITS OWN epoch's fence and run_token, and refuses a fence newer than anything projected | `epoch.py:330-356` | HOLDS: N concurrent fenced epochs ingest independently; no change needed |
| P9 | `project_epochs` / `open_epochs` return all epochs / non-ended ids | `epoch.py:239-263` | HOLDS. `EpochRecord.spec` is the stored spec (`epoch.py:224-236`) so a `unit` key stored in `spec` survives projection |
| P10 | Gate provider is built per `sweep_goal` on `log.dir/"runs"`; files are keyed by `run_token` (`gate-{token}.json/.result.json/.log`) | `sweep.py:288`; `providers/gate.py:53,64,121` | HOLDS: two concurrent gate epochs have distinct tokens, so their run files cannot collide. The unit `writes={run:<obligation>}` is therefore accurate and conservative |
| P11 | `sweep_goal` dispatches ONLY `NEXT_EPOCH` with `provider=="gate"`; RECOVER, HARVEST handled; everything else is reported | `sweep.py:317-391` | HOLDS. Cognitive/work providers are never dispatched by the sweep |
| P12 | `sweep_goal` observes EVERY running gate epoch before `decide` | `sweep.py:296-299` | HOLDS: `ctx.observations` already holds all of them; the frontier path needs no new observation code |
| P13 | `sweep_goal` is one pass and returns `acted: list[str]` | `sweep.py:278-391` | HOLDS. The N-dispatch loop lives inside it (re-project after each begin) |
| P14 | `proof.independent(a, b)` is pure; any unit lacking list/tuple/set `reads`/`writes`/`resources` is independent of nothing; conflict = `W&(R|W)` or `W_b&R_a` or shared resource | `proof.py:~528-540` (read in context) | HOLDS. Reuse, do not redefine (D07, spec S8) |
| P15 | Phase 2 kill-switch helpers are env-only, read at call time; ON only for unset/empty/on/1/true/yes | `proof.py` kill-switch block (Phase 2 spec S10; `test_gsd_x_goal_pcc_semantics.py` drives it) | HOLDS. `frontier_enabled()` composes it with the flag file |
| P16 | `sweep.state_dir()` honours `GSDX_GOALS_ROOT` and returns the parent of `goals` | `sweep.py` (read earlier in session) | HOLDS. Hermetic tests redirect it; the flag file `FRONTIER.off` lives there |
| P17 | `goal_closure(st, tree).blocking / may_close` and `project_convergence(st).obligations` (insertion-ordered dict of obligation objects with `identifier, plane, disposition, done_gate, gate_class, gate_pin, verdict`) | `reconcile.py:161,185`; `sweep.py:352-369` | HOLDS |
| P18 | `cv.REALITY_PLANES`, `cv.RUNTIME_GATE_CLASSES`, `cv.PLANES`, `cv.ALWAYS` exist | `sweep.py:352`; `test_gsd_x_goal_reconcile.py:36-38` | HOLDS |
| P19 | `Observation` states `OBS_UNKNOWN/OBS_ENDED/OBS_LOST/OBS_RUNNING`; `Observation(state, outcome, detail)` | `reconcile.py:139-150`, `epoch.py:86` | HOLDS |
| P20 | Test fixture `ctx_for(lg, **kw)` builds `rc.Context(state=gc.project(lg), tree_hash, scope_hash, providers, now)` | `tools/test_gsd_x_goal_reconcile.py:52-55`; `build(base, gid, ...)` at `:33-49` | HOLDS: the new suite reuses this shape, but is its own file with its own fixtures (no import of a test module) |
| P21 | Semantics suite hermetic pattern: temp HOME/USERPROFILE/GSDX_GOALS_ROOT set BEFORE engine import; `check/run_gate` that survives a raise; summary `GSDX_PCC_SEMANTICS_PASS=n/m  threshold=m/m` | `test_gsd_x_goal_pcc_semantics.py:11-104` | HOLDS. Frontier suite copies this skeleton |
| P22 | `set_budget` stores `dict(budget)` without key validation, so `posture` / `max_parallel` can live in `state.budget` | `contract.py:156` (read earlier) | HOLDS; to re-verify with a RED test in 03-02 that `posture` round-trips through the log |
| P23 | Mutation drill harness runs the mutated test with no `cwd=` | `tools/mutation_drill.py:150` | HOLDS: root cause of `proof.cache` (d44 mutant writes a relative path) |
| P24 | `parallel_mesh` `CollisionDetector` | `pm_02_intent.py:40-70,180-215` normalises scope by lowercase/tokenise | **REJECTED for reuse**: it works on free-text scopes, not declared sets; `proof.independent` is the spec-named predicate (S8). Recorded as non-use |

## 2. Hazards the plans must neutralise

1. **P5 starvation hazard.** With N open epochs, `ungated[0]` can name an obligation that already has an open epoch. Frontier mode builds the execution frontier from `ungated` MINUS obligations with any non-ended epoch whose `spec.obligation` matches.
2. **Legacy equality must hold with the switch off AND with no PCC events** (spec S8). Safest construction: `_decide_legacy` is the current body verbatim; `decide` calls it when `frontier_enabled()` is false, and otherwise calls `frontier.decide_frontier(ctx, _decide_legacy)`, which returns the legacy `Decision` unchanged unless the legacy result is WAIT (then and only then a justified independent action may replace it) or the legacy path would WAIT on an earlier running epoch while a later epoch is HARVEST/RECOVER (frontier lets the later harvest through).
3. **Default posture ECONOMY (bound 1).** With bound 1 and one open epoch the frontier path returns exactly what legacy returns, so merging this phase cannot change a scheduled sweep. Concurrency is opt-in via `state.budget["posture"]`.
4. **G17.** Any new/changed `.py` under `modules/gsd_x/goal/` changes `engine_identity` (`retry_engine_term`, `sweep.py:307`), which is a term of `info_key`. Expect existing keys to differ across the landing commit; the existing suites must be run after the edit, not assumed.
5. **Liveness.** `frontier.py` is reached by `reconcile.decide`, and by `sweep.py`, both already wired; run `python modules/liveness/reachability.py` after landing.
6. **Window for a stale `state`.** `sweep_goal` passes the `state` projected before `decide`. The N-dispatch loop must re-project (`gc.project(log)`) after every `begin`/`mark_running`, as `sweep.py:337,341,384` already does, or the second `begin` will fail the CAS (`LostRace`), which must be caught and stops the loop (not retried blind).

## 3. Reuse map (no new stores)

| Need | Reused seam | New code |
|---|---|---|
| independence | `proof.independent` | none |
| proof-state of a claim | `proof.proof_states` (Phase 2) | none |
| closure barrier | `convergence.goal_closure` | none |
| event log | `GoalLog` / `epoch.begin` stored `spec["unit"]` | one key in the stored spec, frontier path only |
| kill switch | `proof` env-switch helper + `FRONTIER.off` file | `frontier_enabled()` |
| duration prior | `ENDED.ts - RUNNING.ts` from log envelope `ts` | pure function over `state` events |
| posture/bounds | `state.budget` | pure function |

No sidecar, no cache, no table. Phase 3 persists nothing new except the optional `unit` key on a frontier-path epoch spec.

## 4. Measurement plan (what the suite must observe, not assume)

- Legacy equality: replay `decide` on every log prefix of the committed Phase 2 corpus (`tools/fixtures/gsdx_legacy_goals/**`) with the switch OFF and ON(posture default); require field-equal Decisions. Measured in the suite, count printed.
- RED 1 (global WAIT): a goal with one running epoch (observation RUNNING) and one independent ungated obligation and posture WALL_CLOCK: legacy returns WAIT; frontier returns NEXT_EPOCH for the independent one.
- RED 2 (unsafe parallel writes): two gate units whose `writes` intersect, or one with undeclared sets: the frontier must NOT return a second NEXT_EPOCH, and `epoch.begin` must still refuse.
- RED 3 (resource collision): two gate units sharing an exclusive resource (`integration-env`) with otherwise disjoint reads/writes: not independent, serialised.
- Each RED is also driven through `tools/mutation_drill.py` against a mutant of `frontier.py` (isolated temp copy with control), requiring KILLED.

## 5. Limits recorded, not hidden

- No semantic obligation->obligation edges (not mechanically derivable); safe only because gates write their own run dir (P10).
- Cognitive/speculative workers are bounded and reported but never dispatched by the sweep (P11): D25/D26 land as admission policy + yield ledger, executed racing is Phase 4+ (needs candidate snapshots).
- Duration priors and information gain are measured from this goal's own log only; with no history they are UNKNOWN and the order falls back to legacy insertion order.

## 6. Open points (decided, to re-verify at execution)

- P22 `posture` round-trip through `set_budget`: RED test in 03-02.
- Whether `ctx.budget` or `state.budget` is authoritative for posture: use `ctx.budget`, falling back to `ctx.state.budget` (sweep passes the same dict).
