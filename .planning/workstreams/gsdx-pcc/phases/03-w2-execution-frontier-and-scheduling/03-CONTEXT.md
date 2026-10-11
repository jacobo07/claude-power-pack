# Phase 3: W2 Execution frontier and scheduling - Context

**Gathered:** 2026-10-11
**Status:** Ready for planning
**Mode:** Auto (UNATTENDED, WU-P3; discuss skipped; gray areas decided by the worker with a reason each)
**Mission:** m-84c6e0072a10 (from commit 1b7bcebc; the rehydration card was not in this session's context)

<domain>
## Phase Boundary

ROADMAP Phase 3: `decide()` becomes the first action of a compiled execution frontier; WAIT only when the frontier
is empty; the sweep dispatches N independent gate epochs under a resource bound. Requirements D04 D05 D06 D07 D08 D09
D25 D26 D27 D28 D33 D34. Depends on Phase 2 (proof seam `modules/gsd_x/goal/proof.py`, `GSDX_PCC_REPLAY_PASS=28/28`,
`GSDX_PCC_SEMANTICS_PASS=48/48`, which must not regress).

Out of scope: Phase 4 (candidate snapshots, causal binding, proof inheritance consumption), the root milestone, any
write to the main checkout or `~/.claude`, any push, any live store write. `judge.py` is not touched (S9).
</domain>

<decisions>
## Implementation Decisions (spec S8/S10 are locked; everything below is decided here)

### Shape
- **New pure module `modules/gsd_x/goal/frontier.py`** owns `compile_frontier(ctx) -> Frontier`, unit derivation,
  the graph, signals and admission. Reason: reconcile.py stays a thin consumer; Phase 2's `proof.py` pattern.
- **`decide(ctx)` keeps its signature (S8).** The current body becomes `_decide_legacy` byte-for-byte; `decide` calls it
  when `frontier_enabled()` is false, and otherwise wraps it. Reason: V-PCC-DECIDE-SIG and legacy equality (D43).
- **Switch default stays ON when unset (S10), but the DEFAULT posture is ECONOMY (parallel bound 1)**, so an existing
  goal that never sets a posture behaves as today even with the switch on. Reason: the scheduled sweep must not change
  behaviour on merge; concurrency is opt-in through the goal budget (D09), which is where the spec puts it.
- **Flag file for the switch** (S10 deferred this to the first consumer): `frontier_enabled()` = env `GSDX_FRONTIER`
  on AND no file `FRONTIER.off` in the sweep state dir. Either one off means legacy. Reason: the scheduled `PP-GoalSweep`
  cannot inherit an interactive env var; both sources only ever move toward the legacy (stronger) path.
- **Execution frontier ordering is a documented lexicographic key, never a merged score** (D33/D34 "separate
  signals"): critical-path contribution desc, failure risk desc, information gain desc, then legacy
  `cv.obligations` insertion order. Reason: a blended score hides which lens decided, and Phase 9 needs them apart.

### Derived read/write/resource sets (D07, "mechanical, not model-filled")
- A **gate unit** for obligation `o`: `reads` = gate pin files + the effective contract's `causal_paths`, or the
  token `tree:*` when none are declared; `writes` = `{run:<obligation id>}` (its private run dir, which the gate
  provider already creates per epoch); `resources` = exclusive environment names only: `{}` for `unit`, `{integration-env}`
  for `integration`, `{reality-env}` for `in_game`/`live`/any REALITY-plane obligation.
- **Unknown or empty gate class, or a contract that cannot be read: the unit declares `None` sets**, and by
  `proof.independent` (proof.py:528) an undeclared set is independent of nothing. Reason: Law 4, "undeclared
  conflicts with everything".
- Reuse `proof.independent`; do not write a second definition. `parallel_mesh` `CollisionDetector` is used only if
  premise-verification (03-RESEARCH) shows a pure entry point with synthetic ids; otherwise a note says why not.
- Shared CPU is not a resource name (it never serialises); exclusive named resources do.

### Frontiers and graph (D04, D05)
- Expectation = the goal's live obligations and contract items. Execution = justified actions with unit properties.
  Proof = `goal_closure.blocking` plus every claim whose Phase 2 `proof_states` is not FRESH/INHERITED. Invalidation =
  claims SATISFIED earlier whose state is now STALE/UNKNOWN. Reason: each is already derivable from existing projections.
- **Graph edges that matter, derived only:** work(o)->gate(o); gate(*)->closure barrier->judge; harvest(e)->units of
  e's obligation; resource edges between gates sharing an exclusive resource (ordered by the key above). Semantic
  obligation->obligation dependency is NOT derivable mechanically today, so it is not invented: no edge there means
  "no ordering claim", and it is safe only because gates write nothing but their own run dir. Recorded as a limit.

### Scheduling (D08, D09, D28, D33, D34)
- **Measured priors only.** Duration prior of an obligation = median of (ENDED.ts - RUNNING.ts) over its own prior gate
  epochs in the log; else median across the same gate class in this goal; else `None` (UNKNOWN). Reason: the envelope
  carries `ts`; nothing is estimated.
- **Unknown duration sorts as the longest** (dispatch first). Reason: running it creates the prior; it can only
  reorder, never skip or declare anything covered.
- Failure risk = measured fail fraction of that obligation's ended gate epochs (None with no history) times
  (1 + number of open claims sharing a read); information gain = binary entropy of the same measured pass fraction
  divided by the duration prior (None when either is unknown). Two fields, two functions, no shared accumulator.
- **Posture** lives in `state.budget["posture"]` in {ECONOMY, BALANCED, WALL_CLOCK}; absent or any other value ->
  ECONOMY. Deterministic-worker bound: 1 / 2 / 4, capped by `budget["max_parallel"]` when present. Environment
  workers are bounded by their exclusive resource (1 each). Cognitive and speculative classes get their own bound of 1
  and are never dispatched by the sweep (it only dispatches gates today). Reason: Concurrency of agents is not
  concurrency of verification (dataset 27); the cognitive scheduler is not imported.
- **Harvest and recover are never blocked by a WAIT on a sibling epoch** in frontier mode (legacy returns at the
  first running epoch; with N open epochs that would hide an ended one). With one open epoch this is identical.

### Concurrency at the write authority
- `epoch.begin` keeps refusing a second open epoch unless the caller passes the new epoch's `unit` and every open
  epoch carries a stored `unit` and all pairs are `proof.independent`, AND `frontier_enabled()`. The stored spec gains
  a `unit` key only on the frontier path. Fences keep strictly increasing; ingest still compares a receipt with its own
  epoch's fence (epoch.py:348-355). Reason: UWCP S1-8b put the rule at the authority, not at one caller.
- The sweep loops "decide, apply" while the decision is a gate NEXT_EPOCH, at most `bound` times, re-projecting each
  time. Reason: reuses `decide`; no second dispatcher.

### Speculation and racing (D25, D26)
- Land the **admission policy and yield ledger** as pure functions consumed by `compile_frontier` and the sweep
  report: speculative only for reversible, hermetic, unit-class work with expected saving > cost; racing candidates
  only with distinct worktree roots and the same contract; cancellation uses the existing CANCELLED outcome. The sweep
  does not dispatch cognitive hypotheses today, so the policy is REPORTED, not executed; D25/D26 are dispositioned
  against exactly what runs (no overclaim). Racing needs Phase 4's candidate snapshot to execute: recorded as the
  remaining part, not stubbed.

### Housekeeping
- `proof.cache` (repo root, 1 byte, 19:19) is written by the Phase 2 drill `d44-cache-write`: the mutant is
  `Path("proof.cache").write_text("x")`, and `tools/mutation_drill.py:150` runs the mutated test with no `cwd=`, so the
  relative path lands in the caller's cwd. Fix: the drill spec writes under the temp dir; delete the stray file. Own commit.

### RED list (verbatim; each driven red, then green)
- global WAIT with independent work
- unsafe parallel writes
- resource collision admitted as independent

### Claude's discretion
Names of V-FRONTIER-* gates, test layout, log file names, how many drill mutants beyond the three RED items (the
corpus items this phase owns: global WAIT despite independent work, unsafe parallel writes, resource collision
admitted as independent).
</decisions>

<canonical_refs>
- `vault/specs/gsdx-proof-conserving-convergence.md` S7 S8 S10 S12 S13 S14 (G17: landing `.py` under `goal/` changes `engine_identity`)
- dataset sections 3-8, 24-27, 32-33 (`C:\Users\User\Downloads\Dataset GSD X Incremental Construction Runtime 1.md`)
- `modules/gsd_x/goal/{reconcile,epoch,sweep,proof,convergence}.py`, `tools/mutation_drill.py`
- Phase 2: `02-VERIFICATION.md`, `02-EVIDENCE.md`
</canonical_refs>
