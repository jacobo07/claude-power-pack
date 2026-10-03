---
phase: 02-capability-subject-and-archetypes
plan: 01
subsystem: capability-runtime
tags: [ucep, capability-subject, archetypes, trait-cache, unjudged, liveness, hermetic-test]

requires:
  - phase: 01-baseline-integrity-repair
    provides: modules/tower (families matcher and fold, donegate NA_REASONS, capsule state-dir conventions)
provides:
  - modules/capability_runtime/archetypes.py -- trait/archetype vocabulary, read-only cache reader, resolve()
  - modules/capability_runtime/trait_scan.py -- off-path producer with atomic cache write
  - tools/test_capability_archetypes.py -- 12 hermetic V-ARCH gates with a literal EXPECTED count
  - two PLANNED liveness rows plus the Owner-queue record they point at
affects: [02-02 intent ceiling, 02-03 structural detectors, 02-04 freshness and CLI, 02-05 subject signature, phase 5 envelope compiler]

plan_head_before: 409dca8977d08a885d872745bda62d5ec479f75f

actuals:
  tokens: 12000
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "producer/reader split: the prompt path reads one cache file, an off-path producer walks"
    - "every miss is UNJUDGED with a named cause from a closed set, never ABSENT"
    - "predicates are named module-level functions pred_<gate>() so later drills can re-run them under a mutation"

key-files:
  created:
    - modules/capability_runtime/archetypes.py
    - modules/capability_runtime/trait_scan.py
    - tools/test_capability_archetypes.py
    - .planning/workstreams/ucep/phases/02-capability-subject-and-archetypes/02-OWNER-QUEUE.md
    - .planning/workstreams/ucep/phases/02-capability-subject-and-archetypes/02-liveness-before.json
  modified:
    - vault/liveness/reachability_registry.json

key-decisions:
  - "ARCHETYPE_ID_RE is anchored with \\Z instead of $, so an id with a trailing newline is refused; a control in V-ARCH-ID-SHAPE pins it"
  - "assess() derives fact_state as OBSERVED when the basis contains structural evidence, EXTRACTED for intent alone, UNKNOWN for none (the convention 02-02 states)"
  - "trait_scan reports a persistent PRESENT reading with reason `marker`; with no marker the trait stays UNJUDGED `no-structural-detector`, because a marker class alone is never entitled to say ABSENT"
  - "each gate predicate builds its own fixture repo and a fresh empty state dir under the temp HOME, so gates are order-independent"

patterns-established:
  - "hermetic HOME, USERPROFILE and CLAUDE_STATE_DIR set at module top before any modules import, plus an explicit state_dir= on every produce/read call"
  - "every green gate carries an instrument control that proves its detector can answer the other way"

requirements-completed: [UCEP-02]

coverage:
  - id: D1
    description: "A producer writes a structural trait cache off the prompt path and a read-only reader turns it plus the prompt into a subject; WORLD_MUTATION is REQUIRED only when persistent structure and a verb-object intent are both present, and a missing cache reads UNJUDGED (no-cache), never ABSENT"
    requirement: UCEP-02
    verification:
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-TRACER-PRODUCE"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-TRACER-WORLD_MUTATION"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-TRACER-MISS"
        status: pass
    human_judgment: false
  - id: D2
    description: "Shared vocabulary fixed in one place: ten traits in roadmap order, three single-segment archetype ids as conjunctions, a Strength namespace with no bare REQUIRED, the fact-state vocabulary imported from obligation, and a trait-to-N/A bridge into the donegate vocabulary"
    requirement: UCEP-02
    verification:
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-TRAITS-TEN"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-ID-SHAPE"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-ARCHETYPES-THREE"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-VOCAB-SHARED"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-NA-BRIDGE"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-NO-BARE-REQUIRED"
        status: pass
    human_judgment: false
  - id: D3
    description: "The reader cannot reach the walk: archetypes.py has no import of trait_scan and no os.walk reference (AST check with positive controls)"
    requirement: UCEP-02
    verification:
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-READER-NO-WALK-IMPORT"
        status: pass
    human_judgment: false
  - id: D4
    description: "Both new units are declared PLANNED in the liveness registry with a resolvable Owner-queue pointer from the commit that created them; the offender set is unchanged by name"
    requirement: UCEP-02
    verification:
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-LIVENESS-DECLARED"
        status: pass
      - kind: other
        ref: "modules.liveness.reachability.gate() offender set before/after, compared by unit name: equal, 63 = 63, no new offender"
        status: pass
    human_judgment: false

duration: 13min
completed: 2026-10-03
status: complete
---

# Phase 2 Plan 01: Capability subject tracer and vocabulary Summary

**Off-path trait cache (atomic `traits_<repo_key>.json`) read by a walk-free resolver that makes WORLD_MUTATION REQUIRED only on schema-marker PRESENT plus a verb-object intent, with ten traits, three single-segment archetypes and a donegate N/A bridge pinned by 12 hermetic gates**

## Performance

- **Duration:** about 13 min
- **Started:** 2026-10-03T17:19Z (approximate; the start time was not captured at spawn)
- **Completed:** 2026-10-03T17:32Z
- **Tasks:** 2 (1 tracer, 1 TDD auto)
- **Files modified:** 6 (5 created, 1 shared registry file with two added rows)

## Before records (Step 0)

- **PHASE2_BASE:** `409dca8977d08a885d872745bda62d5ec479f75f` (ledger file `gsd-plan-head-before-02-01`)
- **Dirty-path SET before** (`git status --porcelain`, sorted), and identical after the last task commit:
  ` M .planning/workstreams/ucep/STATE.md`, ` M vault/progress.md`, `?? .gsd/`, `?? .planning/workstreams/ucep/config.json`, `?? .planning/workstreams/ucep/milestone.lock`, `?? .planning/workstreams/ucep/state.json`. None of these was touched by this plan except STATE.md, which the close-out updates.
- **Real `traits_*.json` files under `C:\Users\User\.claude\state\tower`:** 0 (so no producer of that name existed; the tests only ever wrote under a temp HOME).
- **Precondition** (`git status --porcelain` over `modules/tower` and the Phase 1 test files): printed nothing, the Phase 1 code-fixer had landed.
- **Liveness BEFORE:** `passed=False rows=486 offenders=63`, committed as `02-liveness-before.json` in `98224610`.

## RED run 02-01 Task 1

HEAD at the time: `98224610` (the Step 0 commit; `modules/` held no `archetypes.py` or `trait_scan.py`). rc=1.

```
  PASS V-ARCH-HERMETIC-HOME                     Path.home()=C:\Users\User\AppData\Local\Temp\carch-home-ajnm7al3 expanduser=...
  FAIL V-ARCH-TRACER-PRODUCE                    module import failed: ar=ImportError: cannot import name 'archetypes' from 'modules.capability_runtime' ...
  FAIL V-ARCH-TRACER-WORLD_MUTATION             AttributeError: 'NoneType' object has no attribute 'produce'
  FAIL V-ARCH-TRACER-MISS                       AttributeError: 'NoneType' object has no attribute 'resolve'
  FAIL V-ARCH-LIVENESS-DECLARED                 capability_runtime/archetypes not PLANNED (None); capability_runtime/trait_scan not PLANNED (None)
CAPABILITY_ARCHETYPES_PASS=1/5  threshold=5/5
rc=1
```

Only V-ARCH-HERMETIC-HOME passed, as the plan requires, so the harness is not vacuous.

## GREEN line, Task 1 (commit `9c709359`)

`CAPABILITY_ARCHETYPES_PASS=5/5  threshold=5/5` rc=0. Re-run after the commit as the tracer feedback gate: same 5/5, logged `Tracer verified end-to-end -- expanding`. Regression: `FAMILY_BASELINES_PASS=20/20  threshold=20/20`, `FINJ_PASS=24/24  threshold=24/24`, both rc=0.

## RED run 02-01 Task 2

HEAD at the time: `9c709359`. rc=1, `CAPABILITY_ARCHETYPES_PASS=9/12  threshold=12/12`.

- **FAIL (3):** `V-ARCH-ID-SHAPE` (no `ARCHETYPE_ID_RE`), `V-ARCH-ARCHETYPES-THREE` (ids `['WORLD_MUTATION']`, wanted three), `V-ARCH-NA-BRIDGE` (no `TRAIT_NA_REASON`).
- **Already PASS in RED (4), each with its own instrument control so the green is not vacuous:**
  - `V-ARCH-TRAITS-TEN`: control rejects a reordered and a duplicated tuple.
  - `V-ARCH-VOCAB-SHARED`: `is` identity plus an AST import check; control runs the same check over `trait_scan.py`, which does not import the names, and must answer False.
  - `V-ARCH-NO-BARE-REQUIRED`: control shows the sibling `modules.tower.baselines` really does expose a module-level `REQUIRED`.
  - `V-ARCH-READER-NO-WALK-IMPORT`: controls found the reference in `trait_scan.py` (`os.walk reference`), in the alias form `_walk = os.walk`, in `from os import walk` and in an import of `trait_scan`.

## GREEN line, Task 2 (commit `7a17f6d4`)

`CAPABILITY_ARCHETYPES_PASS=12/12  threshold=12/12` rc=0; `FAMILY_BASELINES_PASS=20/20`, `FINJ_PASS=24/24`.

## Liveness before/after

| | rows | offenders | passed |
|---|---|---|---|
| before (`02-liveness-before.json`, base `409dca89`) | 486 | 63 | False |
| after Task 1 commit | 488 | 63 | False |
| after Task 2 commit (final) | 488 | 63 | False |

Compared by unit name: new offender names `[]`, cleared offender names `[]`, `capability_runtime/archetypes` and `capability_runtime/trait_scan` are not offenders (declared PLANNED), offender sets equal. The gate is red on 63 standing offenders before and after; this plan adds none and never ran `--baseline`.

## Accomplishments

- A real layout goes producer -> `traits_<repo_key>.json` in the per-user state dir -> read-only reader -> subject: a prisma fixture yields WORLD_MUTATION REQUIRED with evidence `prisma/schema.prisma` for "add a subscriptions table with its migration".
- A never-produced repo yields persistent UNJUDGED with cause `no-cache`, cache state `NO_CACHE`, no ABSENT reading anywhere, WORLD_MUTATION NONE.
- The vocabulary every later plan imports is fixed in one module: `TRAITS` (ten, roadmap order), `ARCHETYPES` (WORLD_MUTATION, EXTERNAL_EFFECT, BACKGROUND_JOB), `Strength` namespace, `UNJUDGED_CAUSES`, `TRAIT_NA_REASON`.
- The reader is proven walk-free by an AST gate with four positive controls; the producer writes only the state dir (fixture repo listing, `.git` included, is byte-identical before and after produce).

## Task Commits

1. **Step 0: liveness before record** - `98224610` (docs) -- only `02-liveness-before.json`
2. **Task 1 (tracer): produce -> cache -> read -> resolve** - `9c709359` (feat) -- five paths: `archetypes.py`, `trait_scan.py`, `test_capability_archetypes.py`, `reachability_registry.json` (hunk: the two new rows only), `02-OWNER-QUEUE.md`
3. **Task 2: vocabulary** - `7a17f6d4` (feat) -- `archetypes.py`, `test_capability_archetypes.py`

`git diff --name-status 409dca89..HEAD` lists exactly the six frontmatter paths (5 A, 1 M). Measured commit count `git rev-list --count 409dca89..HEAD` = 3 at SUMMARY write. Plan metadata commits follow (SUMMARY, then STATE/ROADMAP).

## TDD Gate Compliance

Task 2 is `tdd="true"`; the plan prescribes ONE commit per task, so the RED state is recorded as a run (stdout, rc, HEAD above) and not as a separate `test(02-01)` commit. `git log -E --grep='^test\(02-01\)'` therefore finds nothing, by the plan's design. Both RED runs were executed before any implementation line existed and are reproduced above.

## Decisions Made

See `key-decisions` above. The `\Z` anchor, the fact-state derivation and per-gate fixture isolation are the choices the plan left open.

## Deviations from Plan

### Auto-fixed Issues

None - no Rule 1-3 fix was needed; the plan executed as written.

### Execution-environment notes (not code deviations)

1. **Branch namespace.** The generic pre-commit assertion's `agent-*` allow-list for worktrees was not applied: this run is the sequential executor on the orchestrator-designated workstream branch `ucep/mission` (not a parallel per-agent worktree), HEAD was verified attached and not a protected branch before every commit, and the root pin guard passed (`PIN_OK`) before each commit.
2. **Bash guard escape.** The `windows-bash-bridge-guard` blocks `git` and `grep` in Bash chunks and no PowerShell tool was available to this executor, so git calls carry the guard's own documented `# bash-safe` marker and file reads of test output used the Read/Grep tools; python calls were not blocked. No guard was disabled.
3. **One instrument added beyond the plan.** `V-ARCH-ID-SHAPE` also rejects `"WORLD_MUTATION\n"` (consequence of using `\Z`).

**Total deviations:** 0 auto-fixed, 3 environment notes. **Impact:** none on scope; the six committed paths equal the frontmatter list.

## Issues Encountered

- The anti-thrash hook blocked a third consecutive Edit on the test file; resolved by a Read and consolidating the remaining change into one Edit. No effect on the result.

## Known Stubs

None. Every trait other than `persistent` reads UNJUDGED `no-structural-detector` and every archetype other than WORLD_MUTATION has no intent detector yet (reason `no-intent-detector`): these are named, tested UNJUDGED states, not filler values, and are scheduled for 02-02 (intent) and 02-03 (structural detectors).

## Threat Flags

None. The producer reads file names only (no contents), writes only under the per-user state dir, and has no network surface; the mitigations T-02-01..T-02-06, T-02-08 and T-02-10 are implemented as planned.

## User Setup Required

None - no external service configuration. Owner steps are recorded in `02-OWNER-QUEUE.md`: O-1 host the producer on the scheduled task (open, does not block this phase; until done every real-session read is `no-cache` -> UNJUDGED), O-2 optional SessionStart refresh (Phase 6), L-1 the liveness exit (Phase 5/6).

## Next Phase Readiness

- 02-02 can extend `intent_facts`/`assess` (bilingual intent, `ceiling`, demoters) against the fixed vocabulary; `_spans()` and `ceiling()` are intentionally not defined yet.
- 02-03 extends `trait_scan` with manifest and dependency detectors and the ABSENT entitlement rules; the `unjudged_reading` calls are routed through the `archetypes` module object so a drill can replace the helper for producer and reader alike.
- 02-04 adds freshness (fingerprint and age), MSYS-form roots and the CLI; `SKIPPED` is already reserved in `trait_scan`.
- No blockers.

## Self-Check: PASSED

- Created files all exist: `archetypes.py`, `trait_scan.py`, `test_capability_archetypes.py`, `02-OWNER-QUEUE.md`, `02-liveness-before.json` (FOUND for each).
- Commits exist: `98224610`, `9c709359`, `7a17f6d4` (each resolved with `git cat-file -e`).
- Plan-level verification re-run: `CAPABILITY_ARCHETYPES_PASS=12/12`, `FAMILY_BASELINES_PASS=20/20`, `FINJ_PASS=24/24`; `git diff --name-status` equals the six frontmatter paths; liveness offender sets equal by name.

---
*Phase: 02-capability-subject-and-archetypes*
*Completed: 2026-10-03*
