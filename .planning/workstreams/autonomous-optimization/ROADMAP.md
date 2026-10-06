# Roadmap: Autonomous Optimization (autonomous-optimization workstream) -- IC gen2

Plan of record: `vault/plans/autonomous-optimization-2026-10-05.md` (Owner APPROVED 2026-10-05).
Parent programme: incremental-cognition (`vault/plans/incremental-cognition-program-2026-10-03.md`).
Prior measurement (do NOT redo while dependencies are unchanged): `vault/plans/zero-rescan-reality-scan-2026-10-05.md`
and `vault/programs/incremental-cognition/measurements/*-KME-L-2026-10-05.md`.
Done-gate: `python tools/test_incremental_cognition_program.py --final`, extended in P0 so it also judges the gen2
ledger (pillars M, O, P, Q, R), plus the Phase 6 Production Reality probe.

Mission terms: autonomous-optimization, zero-rescan, opportunity-lifecycle, kme-l-challenger, usage-index-v5,
optimization-ratchet.

Thesis: GSD X observes how work is done, detects recurring avoidable cost, prices it, builds the smallest
challenger, proves it equal-or-stronger, promotes it through the EXISTING ratchet, and future work inherits it.
EXTEND before NEW. No new OS, runtime, database, scheduler or ratchet. UNKNOWN / INCONCLUSIVE / UNMEASURED are
never PASS; a predicted saving is never a realized one; a challenger is allowed to lose.

## Operating constraints (every phase)

- Run plane: GEX44, clone `~/missions/autonomous-optimization`. One writer per checkout. Never push from inside an
  ssh body; the Owner/laptop fetches the worker branch back.
- KME-L corpus on this plane = the Owner-authorized COPY at `/home/kobii/kme-corpus/projects` (frozen at the
  2026-10-05 copy; 3 laptop junctions recreated as relative symlinks). Pass it as the root explicitly; NEVER
  point a KME-L measurement at GEX44's own `~/.claude/projects`. Label every such result `plane: gex44`.
- Laptop-only (record as one `[<P>]` line in `vault/programs/incremental-cognition/gen2/owner-bundle.md`, then
  continue with other work): deploying into the laptop's live install or scheduled tasks (`PP-Sovereign-Miner`),
  the laptop inheritance test, anything under the laptop's `~/.claude/` (HR-001).
- Never edit: CE/SC/IC-gen1 ledgers' `frozen` objects, `tools/test_cognitive_economy_program.py`,
  `tools/test_skill_capability_program.py`, root `.planning/STATE.md`. UKDL entries are inserted in their section,
  never at the tail.
- `tools/gsd_mission.py` is out of scope for this programme.
- Commits: explicit pathspec, one coherent falsifiable increment each (measurement, instrument fix, detector,
  contract, benchmark, challenger, negative control, integration, canary, promotion, regression gate, knowledge).
  Verify `git log -1 --format=%s` after each.
- Never ask the Owner mid-run: write the owner-bundle line, mark the item AUTHORIZATION_BOUND, continue.
- Every phase commits EVIDENCE.md (Product Delta + Intelligence Delta) and its ledger rows before ending.
- Agent Teams: default zero. Spawn only for an independent uncertainty with a consumer, solo in its batch, with a
  durable-output clause and a bound. Compact artifacts back, never prose reports.
- No identical retry: a retry needs a stated causal delta. 2 identical failures -> pivot (Regla 12).
- Meta-optimization stop: defer when marginal dividend < cost, noise > expected gain, recurrence too low, or the
  critical path has higher-value work. Record deferred opportunities; never block completion on low-ROI polish.

## Phases

- [x] **Phase 0: Spec, gen2 freeze, novelty gate** - pillar M reopen, O-R pre-registered (completed 2026-10-06)
- [ ] **Phase 1: usage_index v5 substrate** - pillar O (PLAN mode)
- [ ] **Phase 2: KME-L challenger** - pillar P
- [ ] **Phase 3: Generic opportunity detectors + discovery eval** - pillar Q
- [ ] **Phase 4: Opportunity record, pricing, autonomy envelope** - pillar M
- [ ] **Phase 5: Second workload taken by the loop** - pillar R
- [ ] **Phase 6: Ratchet, inheritance, regression, overhead** - pillars M, P, R
- [ ] **Phase 7: Red team and closeout** - UKDL, Vault, IC ledger N, handoff

## Phase Details

### Phase 0: Spec, gen2 freeze, novelty gate

**Goal**: the programme is pre-registered before any edit.
**Depends on**: nothing.
**Success criteria**:

1. `vault/specs/autonomous-optimization.md` (T3, `covers:` front matter) with PRD, arch, acceptance, rollback,
   kill switches.
2. `vault/programs/incremental-cognition/gen2/ledger.json` + `FROZEN_AT`: pillars M, O, P, Q, R with predicted
   terminal and rule; gen1 `frozen` untouched. The IC done-gate wrapper judges gen2 too; `--selftest` kills a
   mutant per new rule.
3. `modules/spec_gate` novelty check recorded: classification EXTEND_EXISTING_OWNER with file:line evidence from a
   discovered sweep, or the slice stops.
4. Champion numbers frozen with their commands (zero-rescan plan, Run 5 and Run 6).
5. Instrument fix found while arming (first opportunity of this programme, recorded as an opportunity row):
   `tools/gex44_env_preflight.py` judges `pp_install` by commit-hash ancestry of `PP_COMMIT_FLOOR`, so a `-x`
   cherry-pick of the floor reads `pp_install_stale` although the code is present (live install 4856b50d holds
   25a10ce5 / 308da56b = picks of 5962571c / 60e7947d; PFP 28/28, LG 20/20 on GEX44). Fix: accept the floor when
   HEAD contains it OR a commit carrying `(cherry picked from commit <floor>)` OR an equal patch-id. Red test first
   (pick-only history -> READY; unrelated history -> still NOT_READY; mutant dropping the hash path -> red).
   The live GEX44 install is updated only through its normal fast-forward sync, never by hand.

**Plans:** 5/5 plans complete

Plans:
**Wave 1**

- [x] 00-01-PLAN.md -- T3 spec `vault/specs/autonomous-optimization.md` + HR-NOVELTY-001 record + `tools/test_ao_p0.py` (criteria 1, 3)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 00-02-PLAN.md -- preflight `pp_install` floor-by-pick fix, red first, drill M7-M10, OPP-001 evidence, `[P0]` owner-bundle line (criterion 5)
- [x] 00-03-PLAN.md -- IC-gen2 ledger draft + `tools/ic_gen2.py` judge + `--generation 2` dispatch + G2 rules and selftest (criterion 2)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 00-04-PLAN.md -- champion Run 5 / Run 6 frozen with pinned evidence, OPP-001 row, `--generation 2 --audit` (criteria 4, 5)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 00-05-PLAN.md -- automated pre-freeze audit gate, two-commit freeze (ledger, then FROZEN_AT), 00-EVIDENCE.md (criterion 2)

### Phase 1: usage_index v5 substrate

**Goal**: execution history is ingested once per content identity into queryable structured state.
**Depends on**: Phase 0.
**Success criteria**:

1. Schema v5 adds tool events (tool, input hash, path, result bytes), cwd, project/workstream attribution (mixed
   allowed), realpath + content identity. Migration is incremental: no re-read of files already ingested.
2. Negative controls go red when they should: mixed-project session attributed to both; two distinct histories not
   merged; junction alias counted once; `_archived` handled by declared rule; parser failure surfaced, never a
   silent zero; empty population refuses a verdict.
3. Population parity against the frozen KME-L denominator (102 sessions / 34,871 calls / cache_read
   11,549,646,300) on the GEX44 copy, with dedup reconciled to the unit.
4. Refresh cost measured (wall, bytes) for a cold build and for a delta.

**Plans:** 6 plans

Plans:
**Wave 1**

- [ ] 01-01-PLAN.md -- baseline consumer set + Linux identity suite; v5 tracer: zero-reread migration, tool events, call occurrences, typed population; drill M1-M4

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 01-02-PLAN.md -- path identity, declared `_archived` rule (v5-only), skipped-shape census, parser/file failures surfaced, content identity, interrupted/parallel refresh guarantees

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 01-03-PLAN.md -- effective timestamps, cwds, registered pattern hits + user-text hits, project/workstream attribution from a discovered registry

**Wave 4** *(blocked on Wave 3 completion)*

- [ ] 01-04-PLAN.md -- population with the champion classifier from the index, time cut, archived rule, typed refusals, reconcile block; backfill-v5, refresh --all, cost counters

**Wave 5** *(blocked on Wave 4 completion)*

- [ ] 01-05-PLAN.md -- GEX44 corpus copy: KME-L parity reconciled to the unit, cold/warm/no-op/delta cost, PRG, after-change regression

**Wave 6** *(blocked on Wave 5 completion)*

- [ ] 01-06-PLAN.md -- 01-EVIDENCE.md (Product + Intelligence Delta), gen2 state.O, AOP-O row, [O] owner-bundle lines, STATE

### Phase 2: KME-L challenger

**Goal**: ordinary KME analytics stop rescanning raw history.
**Depends on**: Phase 1.
**Success criteria**:

1. `kme_pillars` access plan: certified index -> project-scoped raw -> global raw only on an explicit cross-project
   question. Guard failure deopts with a logged reason. Invalidation keyed on source watermark, parser version,
   attribution version, metric definition.
2. Equivalence: the 7 KME-L measurement files (D, E, F, G, H, I, L) reproduce identically from the challenger.
3. Champion vs scoped vs challenger table: wall, raw bytes, unique bytes, raw files opened, cross-project bytes
   exposed. A KME-only query opens zero CostaLuz bytes (negative control proves the check can fail).
4. Stale-cache control: changing a source or the parser version invalidates exactly the affected closure.
5. If the challenger does not beat the scoped path on repeated queries, narrow or reject it and record why.

### Phase 3: Generic opportunity detectors + discovery eval

**Goal**: recurring waste is discovered from execution evidence, not named by the Founder.
**Depends on**: Phase 1.
**Success criteria**:

1. Detectors extend CO-12 (no new top-level component): read amplification (same path + content read N times),
   scan amplification (bytes read / evidence consumed), repeated identical command with unchanged inputs, retry
   without causal delta, model call answering a deterministic question. Cheap always-on counters; detail only on
   anomaly.
2. Discovery eval: the KME-L hotspot is found without any KME-specific signature; plus one seeded hotspot found,
   one known no-optimization case not flagged, one low-ROI case rejected. Report detected / missed / false positive.
3. Detector overhead measured.

### Phase 4: Opportunity record, pricing, autonomy envelope

**Goal**: optimization lifecycle is explicit, priced and bounded.
**Depends on**: Phase 3.
**Success criteria**:

1. Durable opportunity rows in the existing ledger convention (no new database): evidence, scope, workload class,
   frequency, current cost, hypothesis, owner search result, predicted dividend, build + proof + carrying cost,
   risk, reversibility, champion, challenger, status, retirement condition, realized dividend.
2. Lifecycle states derived from repo conventions, covering observed -> priced -> shadow -> canary -> certified ->
   promoted, and rejected / narrowed / superseded / retired. No direct jump to promoted.
3. Autonomy envelope from current governance: derived/index/cache and reversible tooling autonomous; architecture,
   authority, global settings, irreversible -> owner bundle. Tests drive both sides.
4. Per-opportunity budget; a branch whose predicted payback deteriorates re-evaluates or stops.

### Phase 5: Second workload taken by the loop

**Goal**: one optimization goes from detected hotspot to certified improvement without being requested.
**Depends on**: Phase 4.
**Success criteria**:

1. The loop itself raises, prices and accepts the next candidate (expected: `tools/sovereign_miner.py`, the only
   automatic full-corpus parse; take whatever the detectors rank first if reality offers better).
2. Shadow agreement measured, canary on the GEX44 copy, certified with realized dividend.
3. Laptop scheduled-task deploy is a `[R]` owner-bundle line.

### Phase 6: Ratchet, inheritance, regression, overhead

**Goal**: future applicable work inherits the better path automatically.
**Depends on**: Phases 2 and 5.
**Success criteria**:

1. `modules/tower/ratchet.promote` at project scope for the KME-L path; family scope for the anti-rescan principle
   only if Phase 5 transfer evidence supports it.
2. Inheritance: a FRESH worker asked a KME question without naming the index takes the index path (path log shows
   the hit).
3. Regression: bypassing the index turns a gate red.
4. Overhead (refresh + detectors) < realized savings, both with commands.
5. Production Reality: real CLI -> real substrate -> measured effect (REGISTERED != ACTIVE != REACHABLE !=
   EFFECTIVE).

### Phase 7: Red team and closeout

**Goal**: the gate survives an adversary and a fresh worker.
**Depends on**: Phase 6.
**Success criteria**:

1. Independent adversarial review (oneshot-architect-auditor) against the brief's FINAL RED TEAM list; every
   material finding reopens its phase.
2. UKDL Hard / Process / Trap entries for every bug and wrong assumption; Knowledge Vault capture; IC ledger N.
3. Session-close meta-analysis (found / built / rejected / ROI error / what to retire).
4. Done-gate exit 0; HANDOFF block.
