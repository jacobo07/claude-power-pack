---
status: APPROVED (Owner "Aprobar todo", 2026-10-07, laptop session 08cb0d86) -- executing; see Execution log
covers: [edd-canary, edd-economics, compiled-execution, planner-extinction, deterministic-dossier, model-boundary-budget, edd-reforecast]
extends: vault/specs/orca-p4-compiled-execution-canary.md
---

# EDD (m-ee81e1595007) as a compiled-execution canary

## Verified reality (2026-10-06T21:56Z, GEX44, `edd-stage/edd_autopsy.py`, deterministic)
- RUNNING epoch 1, owner 19305de8 (pid 1933658 alive), token_estimate None, no hold; limits 40 cycles / 72 h only.
- 123 calls, 28,522,749 processed in 14.4 min (21:42:07-21:56:30). Main (Opus) 30 calls 5.22M, idle since
  21:44:31 waiting on ONE child: gsd-phase-researcher (Sonnet) 93 calls 23.30M, context 77k -> 372k.
- Product so far: commit 0372b5f5 (auto CONTEXT.md, discuss skipped) + untracked 01-RESEARCH.md. 0 obligations closed.
- GEX44 live daf90d00: `envelope` (token-estimate, model, autocompact, wu-packet, continue-max-tokens), `hold`/`release`.
  Breaker and hold PARK, never kill: a running turn keeps spending until `claude stop`.

## Autopsy (tool-shape classification; 123 calls)
| class | calls | processed | share |
|---|---|---|---|
| EVIDENCE_ACQUISITION (grep/sed/read, one per call) | 93 | 21.65M | 76% |
| STATE_READ (gsd-tools queries, git) | 15 | 2.82M | 10% |
| TEST_OR_BENCH_CONTROL | 5 | 1.67M | 6% |
| MUTATION (planning files) | 6 | 1.61M | 6% |
| CONTROL_LOOP + SPAWN + NARRATIVE | 4 | 0.77M | 3% |
Semantic decisions: <= 3 calls (CONTEXT write, researcher spawn, one narrative). Cost driver is context-residency
rent: the child re-sends a growing context (mean ~250k) for each single grep, so cost grows ~quadratically in calls.
Main floor 99k at call 0; main context grew 131k -> 224k by reading two GSD workflow documents into itself.
Grammar ahead for Phase 1: researcher (scan) -> planner (Orca: 121 calls/spawn) -> executor (scans again to write
the matrix). The same repository archaeology is paid three times.

## Challenger for the canary slice = EDD Phase 1 (reality scan + ownership matrix + spec)
- WU-1a ZERO MODEL: `tools/gsd_dossier.py` composes existing owners (import/caller graph of modules/gsd_x,
  `modules/liveness/reachability.py`, graphify query, D2A NON_DUPLICATION_LEDGER, dataset concept extraction) into
  a <= 40k-token dossier + raw refs on disk; salvages 01-RESEARCH.md as an input.
- WU-1b one fresh Sonnet worker via `envelope --wu-packet` (no parent transcript): writes OWNERSHIP_MATRIX.md and
  vault/specs/edd.md. Boundary budget <= 25 calls, ceiling 120k; reasons AMBIGUITY / NOVELTY (13Q on NEW rows) /
  PAGE. A context miss pages a file range; it never guesses.
- WU-1c ZERO MODEL proof: `tools/edd_canary_gate.py` (written first, seen red).
- Review only if NEW rows exist: one Sonnet reviewer on those rows, <= 8 calls.
- Hypothesis to falsify: Phase 1 at 3-8M vs champion grammar (researcher alone already 23.3M and still running).

## Envelope (this tranche only)
Canary attempt token_estimate 8M, trip ratio 1.5 (hold at 12M); tranche cap 25M including dossier build, review,
KV/UKDL/CBR and reserve. Over -> hold, never silent. Phases 2-7 are NOT funded until the canary reforecast exists.
Phase 2+ direction (unfunded): benchmark/holdout/mutation execution as deterministic runners (reuse
tools/mutation_drill.py); models only design fixtures and interpret contradicting results.

## Master Done-Gate
`python tools/edd_canary_gate.py` exits 0 only if: mission token_estimate is non-null and no unbounded worker runs;
every dataset concept has a matrix row with resolving file:line for producer and consumer; spec has `covers:`;
NEW rows carry the 13Q proof; the packet receipt (tokens, calls, reason codes) exists and metered canary spend
<= 12M; forecast-vs-actual and a Phase 2-7 reforecast from EDD evidence exist; KV/UKDL/CBR entries named in the
receipt exist; reachability exit 0 for new tools.

## Execution log
- 22:00:16Z stop: `gsd_mission hold` + `claude stop 19305de8` (pid gone in 1 s). Frozen spend of m-ee81e1595007:
  32,062,568 processed / 132 calls (main Opus 30 calls 5.22M; researcher Sonnet 102 calls 26.84M, ctx to 407k).
  9 researcher calls (+3.5M) landed between the plan (28.5M) and the stop.
- GEX44 `mission/edd-run` 89dac301: `tools/gsd_dossier.py` (81 concepts, 31 modules, 67 KB dossier in 6 s, zero
  model), `tools/edd_canary_gate.py` (red 1/13 before execution; G9 rewritten because reachability.py scans
  modules/ only and could never see tools/ -- a vacuous pass), WU-1 packet. dc20be77: partial RESEARCH.md salvaged.
- Canary record m-99b4cc7104f9: `arm --no-launch --supersedes m-ee81e1595007` (old -> HALTED), hold, envelope
  token_estimate 6M (trip 12M at default ratio 2.0, stall 3M), model sonnet, autocompact 120k, wu_packet WU-1
  (sha256 761051cb), max 3 cycles / 6 h, release. Launch is the agora sweep's.- Attempt 1 m-99b4cc7104f9 BLOCKED 22:13Z: autocompact 120k < measured floor 95.7k + dossier (3 compactions, 0.49M,
  compaction cost UNKNOWN). My error: window guessed, not derived from the floor (UC-18). Superseded.
- Attempt 2 m-51b4175db047 (autocompact 250k): matrix 81 rows + vault/specs/edd.md + receipt for 3,310,496 metered
  (work session 16 calls 2.60M; 2 continuation epochs 0.71M = 21.5% tax, UC-19). HALTED at max-cycles 3.
- Done-gate superseded note: the "reachability exit 0" clause above was replaced by G9 produced -> named -> read.
- RESULT 2026-10-06T22:5xZ: `python3 tools/edd_canary_gate.py` -> EDD_CANARY_GATE=13/13 at GEX44 mission/edd-run
  9640aecf; gate_ukdl_candidates PASS (19). Sampled quality 6/8 (C-15 wrong owner, C-54 wrong status), 28 rows
  UNKNOWN -> Phase 1 NOT done; repair packet WU-1R unfunded. Reforecast remaining EDD ~36M/~95M/~215M (canary/
  REFORECAST.md). Orchestrating Opus pane 08cb0d86 cost 17.41M / 56 calls since 21:52Z (UC-20): tranche ~21.2M
  measured of 25M cap; stopped there.
- WU-1R (Owner-approved 2026-10-07, m-84da090be030) RAN: 1,958,619 / 16 calls, 30 rows settled, 0 UNKNOWN, 0
  unresolvable (19 DATASET_ONLY, 8 PARTIAL, 2 DOCUMENTED_ONLY, 1 UNDER_ANOTHER_NAME). Independent sample (seed 42)
  then fixed C-17, C-01, C-07. GEX44 mission/edd-run f7ed6c5a; gate 13/13 re-run 2026-10-08. **Phase 1 DONE: 5.76M
  total vs 32.06M stopped champion.** The mission record still reads RUNNING under a stall-breaker hold with its pid
  gone (UC-14): stale, held, never relaunched.
- Next = Phase 2 (gold sets + benchmark before operators), UNFUNDED. Reforecast for Phases 2-7: 36M / 95M / 215M
  (REFORECAST.md). Checked 2026-10-08 from laptop pane 88df3ab3, read-only over ssh.
- Owner 2026-10-08: Phase 2 approved with a 14M PROGRAMME ceiling, which is not a worker budget. Units run in
  sequence: P2-A -> evidence -> P2-B -> evidence -> P2-C. No Opus coordinator. On GEX44 a per-unit lease only PARKS at
  sweep cadence (WU-1R overshot its stall budget by 0.46M, 31%) and no goal guard exists, so the leases are not
  enforceable per call. Under the Owner's own rule, therefore, ONLY P2-A is authorised.
- P2-A armed as m-5373d6f4cda7 (mission/edd-run b17f7aa2, b199b8ee); it supersedes stale WU-1R m-84da090be030.
  - Zero-model dossier first: 28 pre->post hunks across 10 categories, deterministic.
  - Lease bottom-up: 1.6M x 1.25 = 2.0M, first progress 0.8M.
  - Context: capsule-v2 rotation, no autocompact (600k safety net only), Owner "instead of autocompact /kclear
    /clear /kresume".
  - P2-A arms an independent auditor (p2a-audit, 0.625M).
  - `tools/edd_p2_admit.py judge` writes ADMISSION-P2A.json, ADMIT_P2B or FREEZE (FREEZE if >30% over forecast, the
    audit fails, or spend is UNKNOWN). It never arms P2-B.
  - EDDP2 gates 8/8; a mutant goes red.
- P2-A RESULT (MEASURED, 12:39): gold set 11 escapes + 2 searched absences (c2076d3f).
  - Auditor m-4bb8952b2903: E01 correct, E02 correct, E11 WRONG (guard already present in pre, nothing escaped).
  - Admission (aacfb632): **FREEZE**. Audit below the bar, and P2-A was +50% over forecast (19 calls vs 12
    planned; 2,397,234 vs 1.6M). The auditor was -21% (4 calls, 394,286). Progress-free spend 0 for both.
  - Reforecast factor 1.498: P2-B ~3.0M, P2-C ~2.7M. Phase 2 spend so far ~2.79M of the 14M ceiling.
  - Causes: (1) the close protocol (hash, sample, arm, receipt) cost ~5 calls the bottom-up count omitted;
    (2) E07-E11 rest on code comments with no pre->post hunk, so they are pre-fixed, not escapes replayable on
    skyparty_pre. The P2-A receipt flagged both.
  - Arming defect, mine: stall < trip on a worktree unit (the fingerprint reads the clone root). Caught at 12:34 and
    fixed by transition before any sweep judged it (ab958f71).
- P2-A REPAIR (deterministic, no model; GEX44 mission/edd-run):
  - c0e9c6d7 added `tools/edd_p2_close.py` (close = 1 call, not ~5), a `pre_fixed` class, and measured cost-model
    clearance. 2ff24d33 moved E07-E11 to pre_fixed, so the replay set is E01-E06. It also recorded the cost-model
    correction (COSTMODEL.json, evidence unit P2-A-AUDIT2). The v1 audit was kept as AUDIT-P2A.v1.json.
  - f135b8e0 froze skyparty_gold.json at sha256 7b37553aa548. Sample (seed 42): E01 E05 E06.
  - 2e3c837d: a running unit cannot clear the cost model, because its own tail goes uncounted. P2-A-AUDIT judged
    itself at 4 calls and finished at 7 (~0.72M by transcript; breaker 1,007,807; attribution gap UNKNOWN).
    Clearance now needs the evidence unit's process to have exited.
  - Arming AUDIT2 was first REFUSED at 10:50Z by goal singleflight: the finished auditor m-4bb8952b2903 still sat
    under its breaker hold. Finished workers linger under holds and block the goal. After it was closed as
    COMPLETED (Owner y, pane 88df3ab3), the same close re-ran from pane 24ca0218 on 2026-10-08. It armed
    **P2-A-AUDIT2 m-79f84cdd34dc**: sonnet, estimate 420,000 x 1.25, lease = stall 525,000, capsule-v2, no
    autocompact, max-cycles 2, unit p2a-audit2, released for the sweep. Receipt 31102277.
  - Next: after AUDIT2 exits, run `edd_p2_admit.py judge`. P2-B stays unarmed (Owner authorised P2-A only).
- P2-A-AUDIT2 RESULT (MEASURED, post-exit judge, GEX44 270bf3c3): **FREEZE**, factor 1.659.
  - Audit: E01 correct; E05 and E06 minor, because both entries call themselves LATENT, so "escape" is the wrong
    framing.
  - Cost: AUDIT2 took 7 calls and 696,658 tokens vs a 420k forecast (+66%). It ran the judge itself while still
    alive (dd030e9a) and saw 4 calls, 386,580 (-8%). The tail was 3 calls and ~0.31M. This repeats the 2e3c837d
    defect at the unit level.
  - Phase 2 spend: ~3.80M of the 14M ceiling.
  - The record still reads RUNNING under a breaker hold with its pid gone, so it lingers like m-4bb8952b2903.
- P2-A-R2 (Owner 2026-10-08: "sí, cerrar el record", P2-B stays FROZEN; pane 24ca0218; deterministic, no model):
  - Zombie m-79f84cdd34dc moved RUNNING -> COMPLETED after an assert that its pid was gone. The goal is free.
    Recorded as debt: automatic terminal settlement.
  - 7046dd61 adds a `latent` class. E05 and E06 left the replay set; the replayable set is E01-E04 and the
    sample is E01 E02 E04. An escape whose own text says LATENT is now refused.
  - The same commit changes the judge. It returns INCONCLUSIVE (exit 3, writes nothing) while any unit's process
    lives, and refuses an audit packet that tells its worker to run the judge. The packet no longer does.
  - EDDP2 25/25, and the new gates are red on the old judge.
  - 6c187881 COSTMODEL: the evidence unit is P2-A-AUDIT3. Its forecast is 500,000 = AUDIT2's audit-only first 5
    calls (488,773). 1.659 stays as the observed factor of a defective unit, not a multiplier.
  - 95bc9460 gold re-frozen at sha256 8c86b86d13d7. The deterministic pre-audit PASSED before arming.
  - **P2-A-AUDIT3 m-c597a68e7077** armed: sonnet, 500,000 x 1.25, lease = stall 625,000, capsule-v2, no
    autocompact. Receipt 57bcf46c.
  - Lifecycle root cause: `tools/gsd_mission.py:520-524` (`plan_next`). Any owner_hold returns `none` before
    liveness is asked, so a DEAD owner under a hold can never reach a terminal state. `goal_conflicts` counts every
    non-terminal record, so the goal stays blocked.
- LIFECYCLE FIX (Owner "y" 2026-10-08, pane 24ca0218):
  - laptop 03234663 / GEX44 live d91bdfd8: under a hold, a DEAD owner (positive evidence only) now settles to
    HALTED with the hold kept. OWNER_HOLD gates are red against the old code.
  - First real pass 16:14:08Z: zombie m-604666a514a3 (grammar, RUNNING under a stall-breaker hold since
    2026-10-06 23:45Z) was settled by the sweep itself.
  - Incident, mine: closing m-79f84cdd34dc with `owner_hold=None` let `_cost_breaker` trip on a COMPLETED record.
    `set_owner_hold` raised, and the raise crashed EVERY sweep pass from ~15:35Z. AUDIT3 sat PREPARED. The same
    class had crashed 264 passes over ~24 h before (m-da6e925b5092, from 2026-10-07 07:37Z).
  - Hold restored on the record. Structural fix: laptop e582e818 + f8d01322 / GEX44 ddfb8a26 -- the breaker and
    auto-budget skip terminal records. Drill red with the production error verbatim.
  - Sweep rc=0 from 16:36Z. AUDIT3 LAUNCHING epoch 1.
- AUDIT3 m-c597a68e7077 RESULT (MEASURED; external judge after process exit; GEX44 f249b521):
  - Audit 2c53d228: E01, E02 and E04 all **correct**. The quality gate PASSES.
  - Spend: 7 calls, 692,049 vs 500,000 (+38%). The packet no longer asked for the judge and the worker did not run
    it. The 7 calls were packet, sample, gold, evidence, one verification grep, write+commit, final message.
  - My forecast omitted the final-message call every unit pays (~104k) and left no slack for one verification
    read. Fact: all three audits cost 7 calls (707,206 / 696,658 / 692,049, spread 2%) whatever the packet asked.
    An audit unit is ~7 x 99k, dominated by the per-call floor.
  - Lifecycle, third variant: the breaker tripped in the pass BEFORE adoption, so the record froze at LAUNCHING
    with no owner. Fix: laptop afdfa22d / GEX44 8e2c0303. A held LAUNCHING whose host row for this launch id is
    finished settles to HALTED and records who ran. The real sweep settled it at 16:47:08Z with rc=0.
  - Worker process: the host's pid 301196 is a `bg-spare` that claimed the job, so it is 5 h old for a 28 min job.
    The job was done and idle. `claude stop f92cdad1` made it exit, and spend did not move afterwards.
  - Verdict: **FREEZE on economics only**. P2-A +50%, AUDIT +41%, AUDIT2 +66%, AUDIT3 +38%; nothing cleared,
    factor 1.659. Phase 2 spend ~4.49M of the 14M ceiling.
- P2-B does not exist: no packet, no scope, no holdout spec. Only the 2.0M forecast and the Owner's description
  ("creates the holdouts that will judge new machinery"). It cannot be auto-armed on a PASS until written.
- P2-B (Owner y 2026-10-08, pane 24ca0218: no standalone ~0.7M probe; P2-B is the prospective cost test):
  - Sweep blast radius + silence (laptop 30086f18 / GEX44 live f07aaf01): `_auto_budget`/`_cost_breaker`/`plan_next`
    ran outside supervise's per-mission isolation, so ONE raise ended every pass for every mission (the 264-pass
    and ~1 h outages). Now isolated. `sweep_health` judged only age and timeouts, so a pass crashing on time read
    OK: stage rc != 0 now reads FAILING, the heartbeat carries `fail_streak`, and `supervise --actions-only` keeps
    error rows and exits 3. Real pass 19:14:38Z: rc=0, fail_streak 0, SWEEP OK. No push channel from GEX44 to the
    Owner exists: detection is at `status`, not a notification (debt).
  - Known red: laptop V-MC-SUP-HOST-UNANSWERED-NOT-BLOCKED, cause measured: `_auto_budget`'s
    `envelope_auto_assigned` transition refreshes `updated_at`, the staleness clock plan_next reads, delaying the
    UNKNOWN surface by up to 30 min once per record (stub it out and the gate passes). Laptop build only. GEX44 live's
    known red is a different gate, V-MC-PLAN-FACTS-REFUSES-OVERLAP, identical before and after f07aaf01.
  - m-e3ed7e14a5e2 (other workstream) is PREPARED by design: launch held, cwd and work_dir lineages diverged. Untouched.
  - P2-B = ROADMAP Phase 2 criterion 2: 4 holdouts (checkout, background job, SaaS onboarding, renamed game) + 5
    negative controls (one per class), question discipline both ways, inputs/ (tested side) apart from answers/.
    Criterion 3 (V-EDD-BENCH + BEFORE score) is P2-C; Reference Frontier stays Phase 5.
  - edd-run 2dfd1d30 `tools/edd_p2b.py`: lint (structure, grading-frame words, origin vocabulary, verbatim 6-word
    answer runs), seal, guard (wired into edd_p2_chain.py: only Phase-2 units or audits may name holdouts/answers;
    Phase 3 refused until sealed), judge (PASS/FREEZE/FAIL, INCONCLUSIVE while running, forecast must predate the
    record, +-30% either way). Both judges: a terminal record closes a unit's boundary (bg-spare pid, AUDIT3).
    EDDP2B 29/29, EDDP2 26/26, two mutants red. Residual: the guard reads packets, not a worker's file reads; a
    Phase-3 judge must scan its transcript for holdouts/answers reads (named Phase-3 done-gate item).
  - 038387fa froze FORECAST-P2B.json BEFORE arming: P2-B 11 calls 1,380,000 (band 1.1-1.8M); P2-B-AUDIT 7 calls
    725,000 (band 0.69-0.80M), the evidence unit of the corrected audit model in COSTMODEL.json.
  - **P2-B armed m-0729ac737bec** (162d2ead): sonnet, lease 1,725,000, capsule-v2, no autocompact, unit p2b.
- P2-B RESULT (MEASURED; external judges after both records settled HALTED by the sweep, 19:53:08Z; edd-run 9cc55257):
  - Work: 8 calls, 892,740 (forecast 11 / 1,380,000; -35%). Lint passed first time, sealed 85a2cea5 (9 cases, 18
    files), auditor armed 5c1dfd3e. The 3 forecast calls never needed were the fix slack and one write turn: the
    model was over-provisioned, not missing a component.
  - **Incident, continuation tax**: the worker's host row read done, the sweep asked GSD (whole EDD workstream,
    phases 2-7 pending: "work remains") and launched epoch 2 a0c6a8bf, which spent **20 calls / 2,130,930 in 55 s**
    on capsule resume/certify and a re-check of the seal, mutating nothing. REFORECAST UC-19 had measured this tax
    (21.5%) and named the fix; it was never built. Held + stopped by me (both jobs `done`). Fix: laptop 1dad0c27 /
    GEX44 live 1872e9a1 -- a record's `done_check` (argv) is asked before GSD and any continuation; edd-run 5edf5d94
    -- edd_p2_chain.py REQUIRES `--done-check`, `edd_p2b.py done` answers for P2-B and P2-B-AUDIT. The judge now
    prices every epoch of a unit by ledger worker ids (the owner alone is one epoch; mission_spend's directory-wide
    count adds a concurrent unit in the same cwd -- the breaker still uses it: debt).
  - Quality: 0 wrong, 0 leak. H06 correct; H01, H02 minor (answer keys thin: H01 misses same-day release to the
    next waitlisted person and the atomic claim race). **P2-B verdict FREEZE** (2 minors + cost 28 calls 3,023,670,
    +119% with the tax).
  - **Audit model validated prospectively**: P2-B-AUDIT 7 calls 718,216 vs 725,000 (-0.9%). The P2-A judge's own rule
    now clears P2-A/AUDIT/AUDIT2/AUDIT3: ADMISSION-P2A reads ADMIT_P2B.
  - Phase 2 spend ~4.49M + 3.02M + 0.72M = ~8.23M of the 14M ceiling (2.13M of it the fixed tax).
  - Trap hit by me: `claude stop` inside an ssh `bash -s` script read the rest of the script from stdin as a prompt
    (a model replied; the lines after it never ran). Always `</dev/null` for `claude` in a remote script.