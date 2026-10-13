# Roadmap: GSD X -- proof-conserving convergence (gsdx-pcc)

Spec of record: `vault/specs/gsdx-proof-conserving-convergence.md` (T3, Owner-approved 2026-10-07).
Denominator: `.planning/workstreams/gsdx-pcc/DENOMINATOR.md` -- every row ends dispositioned with evidence.
Design input: `C:\Users\User\Downloads\Dataset GSD X Incremental Construction Runtime 1.md` (read once; materialise slices by section number thereafter).
Iteration lens (apply before W1 freeze, after each wave whose evidence overturns an assumption, at final convergence):
`C:\Users\User\Downloads\Promptsss\Prompts pa iterar\Universal\iteracion-avanzada-universal.txt`.

Principle: GSD X minimizes TIME TO PROVEN CONVERGENCE. Proof strength never decreases. UNKNOWN escalates to the
stronger path. Every speedup comes from safe concurrency, proven proof reuse, better impact precision, earlier
discriminating evidence, or less reconstruction -- never from removing a check.

## Operating constraints (every phase)

- Repo: worktree `C:\Users\User\Apps\pp-gsdx-pcc`, branch `gsdx/pcc`. This mission is the ONLY writer here.
  Never write the main checkout `C:\Users\User\.claude\skills\claude-power-pack` (another mission lives there),
  `C:\Users\User\Apps\io-chatgpt-plugin`, `C:\Users\User\Apps\io-ucg` or any other repo: pilot work happens in
  fresh `git worktree add` copies under `C:\Users\User\Apps\gsdx-pilot-*` on branches `gsdx-pilot/<slice>`,
  never pushed, no deploy, no live service.
- Git: `& 'C:\Program Files\Git\cmd\git.exe' -C <repo> ...`. Python:
  `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`, `$env:PYTHONIOENCODING='utf-8'`.
  Elixir: `mix` via scoop (`C:\Users\User\scoop\apps\elixir\current\bin`). PowerShell tool, not Bash, for every
  git/python/mix call.
- Micro-commits: one coherent verified delta each, `git commit -F <msgfile>` (one msgfile per commit), message ends
  with the Co-Authored-By line from the session. Verify `git log -1 --format=%s` after every commit. Never push.
- Liveness: each new module is wired in the SAME commit, or declared in `vault/liveness/reachability_registry.json`
  with its owner-queue line; `python modules/liveness/reachability.py` exit 0 at every phase end.
- Tests: hermetic (`GSDX_GOALS_ROOT`/HOME redirected to a temp dir); no test writes the live goal store, the live
  mission ledger or `~/.claude/state`. Pattern: `tools/test_family_injection.py:79-84`. Summary line
  `<SUITE>_PASS=n/m  threshold=n/m`.
- Every optimisation lands RED-first: the failure it prevents is driven and seen red before the fix.
- Mutation evidence through `tools/mutation_drill.py` (isolated copy + control). Never `mutation_probe` live mode.
- Never edit `~/.claude/settings.json`, `~/.claude/CLAUDE.md`, `~/.claude/rules/`, `~/.claude/hooks/`, credentials.
  A live-hook change is an OWNER STEP recorded in the phase EVIDENCE.md.
- Authority: adapter maturity ceiling PROBATION (Owner D-O4). Universal/constitutional promotion = the new tower
  family `software_construction` (Owner D-O2); a scope wider than that stops at PENDING_OWNER, recorded, continue.
- Never ask the Owner mid-run: write the blocker into the phase EVIDENCE.md, mark the row BLOCKED/UNJUDGED, continue
  with any other unblocked phase.
- Every phase ends with `EVIDENCE.md`: commands, exit codes, observed output, Production Reality verdict
  (PROVEN / OBSERVED / UNJUDGED / BLOCKED -- never upgraded), denominator rows moved, UKDL entries written.
- Every bug found -> Incident -> root cause -> class (lens CLASE 0-6) -> regression -> guard -> UKDL
  (`vault/knowledge_base/ukdl-universal.md`, ids HR-/PR-/T-) where universal.
- Two materially identical failures of one approach -> pivot (Regla 12). A no-progress epoch changes strategy.

## Phases

- [x] **Phase 1: W0 Reality, baseline and incumbent measurement** (completed 2026-10-07)
  Premise-verify every API the spec names (HR-PREMISE-001: evidence_bundle, mutation_drill, change_impact,
  parallel_mesh pure fns, tower). Fix R01 (gate supervisor drops gate output on Windows, providers/gate.py:72)
  red-first, mutation-drilled, UKDL T-entry. Measure the incumbent: per-suite wall time of the GSD X goal suites,
  judge replay time, a real goal's sweep->judge timeline; record UNKNOWN where unmeasurable. Done: gate_provider
  18/18; `EVIDENCE.md` with the incumbent table.
- [x] **Phase 2: W1 Convergence semantics (ULTRA-PLAN, the only one)** (completed 2026-10-11)
  Resolve proof states, certificate validity, causal fingerprint, freshness classes, frontier semantics, event
  types, kill switches, legacy-log replay. Dispatch `oneshot-architect-auditor` on the amended spec; inject every
  gap. Then land the compatibility seam: new event types + projections with ZERO behaviour change; every
  existing suite unchanged and green; a replay test over a recorded legacy goal log. Return to EXECUTION.
- [x] **Phase 3: W2 Execution frontier and scheduling** (completed 2026-10-12)
  `compile_frontier` projection (four frontiers, convergence graph edges that matter, read/write/resource sets
  derived mechanically), `decide()` = first frontier action (legacy callers unchanged), WAIT only when the
  execution frontier is empty, sweep dispatches N independent gate epochs under a resource bound, critical path
  from measured priors (UNKNOWN allowed), information-gain and failure-first as separate signals, posture
  ECONOMY/BALANCED/WALL_CLOCK on the goal budget. RED: global WAIT with independent work; unsafe parallel writes;
  resource collision admitted as independent.
- [x] **Phase 4: W3 Candidate snapshots, invalidation, proof inheritance** (completed 2026-10-13)
  Candidate snapshot (git objects), causal fingerprint, `proof.produced/inherited/invalidated` events,
  freshness classes, minimal sufficient verification (UNKNOWN -> FULL). RED: false reuse after a relevant change;
  UNKNOWN treated as clean; fresh-required proof inherited; omitted proof without an INHERITED event; candidate
  changes under verification.
- [x] **Phase 5: W4 Judge VALIDATE vs REPLAY, parallel replay, reviewer concurrency**
  Judge validates certificates independently or replays; independent replays concurrent (bounded); reviewer bound
  to a candidate via evidence_bundle tickets, staled exactly where bytes moved (close the A->B->A hole). RED:
  builder self-certification; gate weakening accepted; stale review surviving mutation.
- [ ] **Phase 6: W5 Mutant farm**
  Mutation contract by failure class; isolated candidate-derived mutants (drill discipline) in parallel; each
  killed for the right reason (control + signature); canonical candidate intact; final composition proof still
  owed. RED: a mutant that crashes / fails setup counted as killed.
- [ ] **Phase 7: W6 Universal impact adapter contract + Elixir pilot**
  Adapter contract inside the change_impact owner (direct, transitive, unknown frontier, change class per GK-13
  vocabulary, unmapped surfaces, authority). Python adapter = today's graph. Elixir adapter (modules, behaviours,
  config, umbrella apps, migrations, supervision, protocols) in SHADOW on a pilot worktree of io-chatgpt-plugin,
  incumbent full `mix test` in parallel; PROBATION at most. Every other ecosystem in the denominator: explicit
  fallback to FULL proven reachable. Adapter maturity as append-only events. RED: unsupported adapter authorising
  selective execution; adapter still TRUSTED/PROBATION after a discrepancy.
- [ ] **Phase 8: W7 Continuation objects and boundary context images**
  Per-job briefs from brief.py (mutation / repair / reviewer / fresh worker); continuation object sealed at
  epoch boundaries; convergence monotonicity: no-progress epoch detected from frontier delta. RED: handoff loses a
  blocking frontier.
- [ ] **Phase 9: W8 Latency observatory, shadow corpus, historical replay**
  TTPD and the non-collapsed metric set as projections; `tools/gsdx_shadow.py` old-vs-new comparison; replay of
  the io-ucg Phase-6 class and the Vault incidents (stale evidence, self-certification, live-mutant). X vs X' only
  where honest. Zero false coverage on any promoted scope.
- [ ] **Phase 10: W9 Production Reality, fresh agent, UKDL, baseline ratchet, meta-analysis**
  Real goal on a fresh fixture repo through the real CLI + sweep + judge; fresh-agent test (cpp-carrier-verifier
  with repo only); tower family `software_construction` B0 + goal-brief injection so `claude -p` goal workers
  inherit it; UKDL HR/PR/T entries; meta-analysis; `tools/gsdx_pcc_done.py`.

## Phase Details

Requirements are DENOMINATOR row ids (`REQUIREMENTS.md`: the requirement set IS the denominator). A row listed in
two phases is closed by the later one; the earlier one lands its part.

### Phase 1: W0 Reality, baseline and incumbent measurement

**Goal**: Every API the spec names is premise-verified, R01 is fixed red-first, and the incumbent full path is
measured so every later speedup has an honest baseline.
**Depends on**: Nothing
**Requirements**: R01
**Success Criteria** (what must be TRUE):

  1. HR-PREMISE-001 premise check recorded for evidence_bundle, mutation_drill, change_impact, parallel_mesh pure
     fns and tower (real signatures cited file:line in EVIDENCE.md).
  2. R01 (gate output lost on Windows, `providers/gate.py:72`) driven red, fixed, mutation-drilled; gate_provider
     suite 18/18; UKDL T-entry written.
  3. Incumbent table in EVIDENCE.md: per-suite wall time of the GSD X goal suites, judge replay time, one real
     goal's sweep->judge timeline; UNKNOWN recorded where unmeasurable.

**Plans:** 6/6 plans complete

Plans:
**Wave 1**

- [x] 01-01-PLAN.md -- R01 red-first: gate supervisor std handles, mutation drill with control, UKDL T-entry (wave 1)
- [x] 01-02-PLAN.md -- reality-baseline instrument: guarded hermetic suite timing, in-copy runs, UNKNOWN rows, table (wave 1)
- [x] 01-03-PLAN.md -- goal timeline instrument: recorded goal over a verified copy, hermetic fixture via the real CLI (wave 1)
- [x] 01-04-PLAN.md -- HR-PREMISE-001 record with a failing control, liveness debt frozen by name, DENOMINATOR R10 (wave 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-05-PLAN.md -- incumbent measurement: every goal suite, mutation suite in a copy, timelines, judge replay (wave 2)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-06-PLAN.md -- phase-end gates, 01-EVIDENCE.md with Production Reality verdicts, R01 dispositioned (wave 3)

### Phase 2: W1 Convergence semantics (ULTRA-PLAN, the only one)

**Goal**: Proof states, certificate validity, causal fingerprint, freshness classes, frontier semantics, event
types, kill switches and legacy-log replay are resolved in the spec, audited, and land as a zero-behaviour-change
compatibility seam.
**Depends on**: Phase 1
**Requirements**: D01, D03, D10, D43, D44
**Success Criteria** (what must be TRUE):

  1. Amended spec audited by `oneshot-architect-auditor`; every gap injected.
  2. New event types + projections land with ZERO behaviour change; every existing goal suite unchanged and green.
  3. A replay test over a recorded legacy goal log passes.

**Plans:** 6 plans

Plans:
**Wave 1**

- [ ] 02-01-PLAN.md -- spec Semantics S1-S16 resolved in place, ULTRA Q&A in STATE, premises verified, auditor dispatched solo, every gap injected or dispositioned (wave 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 02-02-PLAN.md -- legacy fixture (g-002/g-001 byte copy + manifests), golden from the unmodified engine, replay suite committed RED-first (wave 2)

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 02-03-PLAN.md -- proof.py event seam: ledger projection, CAS writer, kill switches, liveness declared; replay suite green (wave 3)

**Wave 4** *(blocked on Wave 3 completion)*

- [ ] 02-04-PLAN.md -- proof states, certificate validity, causal fingerprint, typed contract, freshness; legacy map equals _needs_a_gate_here (wave 4)

**Wave 5** *(blocked on Wave 4 completion)*

- [ ] 02-05-PLAN.md -- five laws as executable invariants, D44 scanners, declared additive vocabulary, spec-resolved gate (wave 5)

**Wave 6** *(blocked on Wave 5 completion)*

- [ ] 02-06-PLAN.md -- on-disk drills, 19 suites at Phase 1 counts, liveness, no-legacy-edit, 02-EVIDENCE.md, D43/D44 DONE (wave 6)

### Phase 3: W2 Execution frontier and scheduling

**Goal**: `decide()` becomes the first action of a compiled execution frontier; WAIT only when the frontier is
empty; sweep dispatches N independent gate epochs under a resource bound.
**Depends on**: Phase 2
**Requirements**: D04, D05, D06, D07, D08, D09, D25, D26, D27, D28, D33, D34
**Success Criteria** (what must be TRUE):

  1. `compile_frontier` projection (four frontiers, read/write/resource sets derived mechanically); legacy
     `decide()` callers unchanged.
  2. RED-first: global WAIT with independent work, unsafe parallel writes, resource collision admitted as
     independent -- each seen red, then green.
  3. Critical path from measured priors (UNKNOWN allowed); information-gain and failure-first as separate signals;
     posture ECONOMY/BALANCED/WALL_CLOCK on the goal budget.

### Phase 4: W3 Candidate snapshots, invalidation, proof inheritance

**Goal**: Proofs bind to candidate snapshots by causal fingerprint; inheritance is explicit and never applies to
fresh-required evidence; UNKNOWN impact forces FULL.
**Depends on**: Phase 3
**Requirements**: D01, D10, D11, D12, D13, D14, D20, D23, D24, D39, D45, R02
**Success Criteria** (what must be TRUE):

  1. Candidate snapshot on git objects + causal fingerprint + `proof.produced/inherited/invalidated` events.
  2. Minimal sufficient verification set with UNKNOWN -> FULL.
  3. RED-first: false reuse after a relevant change; UNKNOWN treated as clean; fresh-required proof inherited;
     omitted proof without an INHERITED event; candidate changes under verification.

### Phase 5: W4 Judge VALIDATE vs REPLAY, parallel replay, reviewer concurrency

**Goal**: The judge validates certificates independently or replays them (bounded concurrency); reviewers bind to
a candidate and are staled exactly where bytes moved.
**Depends on**: Phase 4
**Requirements**: D15, D16, D17, R05
**Success Criteria** (what must be TRUE):

  1. Judge VALIDATE and REPLAY paths; independent replays concurrent under a bound.
  2. A->B->A hole in evidence_bundle closed.
  3. RED-first: builder self-certification; gate weakening accepted; stale review surviving mutation.

### Phase 6: W5 Mutant farm

**Goal**: Mutation contract by failure class, executed as isolated candidate-derived mutants in parallel, each
killed for the right reason.
**Depends on**: Phase 4
**Requirements**: D18, D19, R04, R11
**Entry obligation (R11)**: before any mutation speedup claim, measure the incumbent mutation suite itself in an
isolated copy: `python tools/gsdx_reality_baseline.py suites --suite tools/test_gsd_x_goal_mutation.py --in-copy
--runs 1 --timeout 3600 --out <PHASE_DIR>/06-incumbent-mutation.jsonl --log-dir <PHASE_DIR>/incumbent-logs` (`--out`
and `--log-dir` are required by the tool, `tools/gsdx_reality_baseline.py:370-371`).
Phase 1 left it UNKNOWN (memory-pressure reaper; Owner decision 2026-10-07 to keep it UNKNOWN there).
**Success Criteria** (what must be TRUE):

  1. Mutants derived in isolated copies (drill discipline), control + kill signature per mutant; canonical
     candidate intact.
  2. RED-first: a mutant that crashes / fails setup is NOT counted as killed.
  3. Live-mode mutation_probe never used by the farm; R04 recorded as debt.

### Phase 7: W6 Universal impact adapter contract + Elixir pilot

**Goal**: Impact adapters behind one contract inside the change_impact owner; Elixir adapter runs in SHADOW on a
pilot worktree; every other ecosystem falls back to FULL provably.
**Depends on**: Phase 4
**Requirements**: D21, D22, D37, D38, D41, R06, R07, R08
**Success Criteria** (what must be TRUE):

  1. Adapter contract (direct, transitive, unknown frontier, change class in GK-13 vocabulary, unmapped surfaces,
     authority); Python adapter = today's graph.
  2. Elixir adapter in SHADOW on a `gsdx-pilot-*` worktree of io-chatgpt-plugin, incumbent full `mix test` in
     parallel; maturity at most PROBATION, as append-only events.
  3. RED-first: unsupported adapter authorising selective execution; adapter still TRUSTED/PROBATION after a
     discrepancy. Every other denominator ecosystem: FULL fallback proven reachable.

### Phase 8: W7 Continuation objects and boundary context images

**Goal**: Per-job briefs and a sealed continuation object at epoch boundaries; no-progress detected from frontier
delta.
**Depends on**: Phase 3
**Requirements**: D29, D30, D31, D32
**Success Criteria** (what must be TRUE):

  1. Per-job briefs from brief.py (mutation / repair / reviewer / fresh worker).
  2. Continuation object sealed at epoch boundaries; convergence monotonicity checked from the frontier delta.
  3. RED-first: handoff loses a blocking frontier.

### Phase 9: W8 Latency observatory, shadow corpus, historical replay

**Goal**: TTPD and the non-collapsed metric set as projections; old-vs-new shadow comparison; historical replay
with zero false coverage on any promoted scope.
**Depends on**: Phase 5, Phase 6, Phase 7
**Requirements**: D02, D24, D35, D36, D37, D40, D46, R08
**Success Criteria** (what must be TRUE):

  1. TTPD + metric set projections over GoalLog.
  2. `tools/gsdx_shadow.py` report; false_coverage == 0 on every promoted scope.
  3. Replay of the io-ucg Phase-6 class and the Vault incidents (stale evidence, self-certification, live-mutant).

### Phase 10: W9 Production Reality, fresh agent, UKDL, baseline ratchet, meta-analysis

**Goal**: A real goal converges through the real CLI + sweep + judge on a fresh fixture repo, a fresh agent
confirms it, and the `software_construction` family baseline is inherited by goal workers.
**Depends on**: Phase 8, Phase 9
**Requirements**: D03, D47, R03, R09, R10
**Success Criteria** (what must be TRUE):

  1. Production Reality evidence: a real GoalLog with produced/inherited/invalidated proofs and a judge receipt
     using VALIDATE and REPLAY.
  2. Fresh-agent report PASS; tower family `software_construction` B0 + goal-brief injection verified.
  3. `python tools/gsdx_pcc_done.py` exit 0 (the final done-gate below).

## Final done-gate (Phase 10 builds `tools/gsdx_pcc_done.py` to run exactly these)

1. Every `tools/test_gsd_x_goal_*.py` suite exit 0 (gate_provider 18/18).
2. New suites exit 0: `test_gsd_x_goal_frontier`, `test_gsd_x_goal_certificate`, `test_gsd_x_goal_invalidation`,
   `test_gsd_x_goal_judge_validate`, `test_gsd_x_goal_mutant_farm`, `test_gsd_x_impact_adapters`,
   `test_gsd_x_goal_latency`, `test_gsd_x_goal_shadow`, `test_gsd_x_baseline_inheritance_pcc` (names may be
   refined in W1; the spec records the final list).
3. `tools/mutation_drill.py` kills every mutant class in DENOMINATOR "mutation corpus".
4. `tools/gsdx_shadow.py report` false_coverage == 0 on every promoted scope.
5. `python modules/liveness/reachability.py` exit 0.
6. Production Reality evidence file with a real GoalLog showing produced/inherited/invalidated proofs and a judge
   receipt using VALIDATE and REPLAY.
7. Fresh-agent report PASS.
8. `python tools/family_baseline.py verify software_construction` exit 0 + inheritance test.
9. DENOMINATOR fully dispositioned; worktree clean; `python tools/gsdx_pcc_done.py` exit 0.

</content>
</invoke>
