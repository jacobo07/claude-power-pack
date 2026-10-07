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

- [ ] **Phase 1: W0 Reality, baseline and incumbent measurement**
  Premise-verify every API the spec names (HR-PREMISE-001: evidence_bundle, mutation_drill, change_impact,
  parallel_mesh pure fns, tower). Fix R01 (gate supervisor drops gate output on Windows, providers/gate.py:72)
  red-first, mutation-drilled, UKDL T-entry. Measure the incumbent: per-suite wall time of the GSD X goal suites,
  judge replay time, a real goal's sweep->judge timeline; record UNKNOWN where unmeasurable. Done: gate_provider
  18/18; `EVIDENCE.md` with the incumbent table.
- [ ] **Phase 2: W1 Convergence semantics (ULTRA-PLAN, the only one)**
  Resolve proof states, certificate validity, causal fingerprint, freshness classes, frontier semantics, event
  types, kill switches, legacy-log replay. Dispatch `oneshot-architect-auditor` on the amended spec; inject every
  gap. Then land the compatibility seam: new event types + projections with ZERO behaviour change; every
  existing suite unchanged and green; a replay test over a recorded legacy goal log. Return to EXECUTION.
- [ ] **Phase 3: W2 Execution frontier and scheduling**
  `compile_frontier` projection (four frontiers, convergence graph edges that matter, read/write/resource sets
  derived mechanically), `decide()` = first frontier action (legacy callers unchanged), WAIT only when the
  execution frontier is empty, sweep dispatches N independent gate epochs under a resource bound, critical path
  from measured priors (UNKNOWN allowed), information-gain and failure-first as separate signals, posture
  ECONOMY/BALANCED/WALL_CLOCK on the goal budget. RED: global WAIT with independent work; unsafe parallel writes;
  resource collision admitted as independent.
- [ ] **Phase 4: W3 Candidate snapshots, invalidation, proof inheritance**
  Candidate snapshot (git objects), causal fingerprint, `proof.produced/inherited/invalidated` events,
  freshness classes, minimal sufficient verification (UNKNOWN -> FULL). RED: false reuse after a relevant change;
  UNKNOWN treated as clean; fresh-required proof inherited; omitted proof without an INHERITED event; candidate
  changes under verification.
- [ ] **Phase 5: W4 Judge VALIDATE vs REPLAY, parallel replay, reviewer concurrency**
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
