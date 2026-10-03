---
phase: 02-capability-subject-and-archetypes
plan: 05
subsystem: capability-runtime
tags: [ucep, subject-signature, modifiers, trait-transition, unjudged-causes, real-poles, phase-gate, evidence]

requires:
  - phase: 02-capability-subject-and-archetypes
    provides: 02-01..02-04 vocabulary, ceiling, detectors, reader freshness, producer CLI (frozen API, additions only)
provides:
  - archetypes.subject_signature() and subject["signature"] (host-independent digest of trait, intent and archetype states)
  - archetypes.modifiers_for() and per-archetype modifiers / modifier_basis (consequence, never strength)
  - V-ARCH-TRANSITION-PERSISTENT, V-ARCH-TRANSITION-DISTRIBUTED, V-ARCH-SUBJECT-SHAPE, V-ARCH-CAUSES-REACHABLE (59 counted gates)
  - uncounted V-ARCH-REAL-POLES read of InfinityOps and ABSW2-Wii with CAPABILITY_ARCHETYPES_REAL_POLES
  - 02-EVIDENCE.md with the bracketed phase gate and a per-component Production Reality verdict (OBSERVED)
affects: [phase 5 envelope compiler (reads modifiers), phase 8 challenge 3 (attacks the transition property), phase 3, Owner step O-1]

plan_head_before: e1ad52a8bbcc7cc2e7658dcf6f4e9e0a17ecff65

actuals:
  tokens: 14117
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "a signature holds conclusions (states, strengths, bases, modifiers, family ids) and never where or when they were read, so equal structure signs equal in any directory"
    - "modifiers are reported beside the strength and never enter ceiling()"
    - "a coverage-by-construction gate iterates the closed vocabulary and carries an instrument control that adds an unreachable member and requires the gate to fail and name it"
    - "an uncounted real-repo pole: a contradicted pole fails the run, a missing path reads UNJUDGED and is never counted"

key-files:
  created:
    - .planning/workstreams/ucep/phases/02-capability-subject-and-archetypes/02-EVIDENCE.md
  modified:
    - modules/capability_runtime/archetypes.py
    - tools/test_capability_archetypes.py

key-decisions:
  - "the subject signature is sha256 (first 16 hex) over canonical JSON of the ten trait states, the ten intent states, [id, strength, basis, sorted modifiers] per archetype and sorted family ids; root, cache path and state, timestamps, evidence text, spans and reasons are excluded"
  - "modifiers_for() is a separate function called by assess(); a modifier counts when its structural reading is PRESENT or WEAK or its intent reading is PRESENT, and it never reaches ceiling(), so it cannot create or change a strength"
  - "a real pole whose walk was cut (truncated or budget hit) reads UNJUDGED for that pole, not FAIL; only a complete walk that contradicts the expectation fails the run"
  - "Phase 2 verdict is OBSERVED; PROVEN none, BLOCKED none"

patterns-established:
  - "FINAL_GATES and the counted/uncounted split: real_poles() runs after every counted gate and prints its own verdict line"

requirements-completed: [UCEP-02]

coverage:
  - id: D1
    description: "Adding persistent structure to a repository recompiles to a different subject: an ephemeral repo gaining prisma/schema.prisma and @prisma/client reads STALE at once, then WORLD_MUTATION CONDITIONAL/intent becomes REQUIRED/structural+intent, the signature and the stored fp1 change, and the same final structure in a second directory signs equal"
    requirement: UCEP-02
    verification:
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-TRANSITION-PERSISTENT"
        status: pass
    human_judgment: false
  - id: D2
    description: "A scheduled repo gaining docker-compose.yml keeps BACKGROUND_JOB REQUIRED with modifiers [] -> ['distributed'] (basis structural) and a different signature; intent-only destructive and bulk modifiers are EXTRACTED facts and leave the strength unchanged"
    requirement: UCEP-02
    verification:
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-TRANSITION-DISTRIBUTED"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-SUBJECT-SHAPE"
        status: pass
    human_judgment: false
  - id: D3
    description: "Every cause in UNJUDGED_CAUSES is reachable from a fixture, and a cause added to the set that nothing can reach makes the gate fail by name"
    requirement: UCEP-02
    verification:
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-CAUSES-REACHABLE"
        status: pass
    human_judgment: false
  - id: D4
    description: "On the real InfinityOps tree persistent and external_effect read PRESENT, and on ABSW2-Wii persistent does not read ABSENT (it reads UNJUDGED no-manifest-ecosystem); the check is read-only and uncounted"
    requirement: UCEP-02
    verification:
      - kind: other
        ref: "python tools/test_capability_archetypes.py -> CAPABILITY_ARCHETYPES_REAL_POLES=PASS"
        status: pass
    human_judgment: true
    rationale: "The result depends on this host's two repository trees; it is an observation recorded in 02-EVIDENCE.md, not a repeatable fixture, so a person reads it as evidence"
  - id: D5
    description: "The phase gate: 11 suite files green on one bracketed run, dirty-path SET unchanged, hermetic control empty, zero real traits_*.json, vault/tower byte-unchanged, no new liveness offender, only Phase 2 paths in the diff; 02-EVIDENCE.md states a verdict of OBSERVED"
    requirement: UCEP-02
    verification:
      - kind: other
        ref: "bash gate.sh run recorded in this SUMMARY and 02-EVIDENCE.md sections 2, 4, 5"
        status: pass
    human_judgment: true
    rationale: "Production Reality is a judgment about what was and was not observed on a live path; the Owner reads it, and O-1 (hosting the producer) is an Owner step"

duration: 15min
completed: 2026-10-03
status: complete
---

# Phase 2 Plan 05: Subject signature, consequence modifiers, phase gate and evidence Summary

**A trait transition now compiles to a different subject (ephemeral->persistent moves WORLD_MUTATION from CONDITIONAL/intent to REQUIRED with a new signature, local->distributed adds a `distributed` modifier on a still-REQUIRED BACKGROUND_JOB), every UNJUDGED cause is shown reachable, the producer is read on two real repositories, and one bracketed gate (59/59, 27/27, nine regression files) closes Phase 2 with an OBSERVED verdict.**

## Performance

- **Duration:** about 15 min
- **Started:** 2026-10-03T18:59:55Z
- **Completed:** 2026-10-03T19:15Z (approximate; last command before this file)
- **Tasks:** 3 (1 tracer, 1 TDD auto, 1 auto)
- **Files modified:** 3 (2 modified, 1 created)

## Before records

- **plan_head_before:** `e1ad52a8bbcc7cc2e7658dcf6f4e9e0a17ecff65` (ledger file `gsd-plan-head-before-02-05`). PHASE2_BASE (`02-liveness-before.json` head) = `409dca8977d08a885d872745bda62d5ec479f75f`.
- **Real `traits_*.json` under `C:\Users\User\.claude\state\tower` before the plan:** 0.

## RED run 02-05 Task 1

HEAD `e1ad52a8`, rc=1 (the test file edited, `archetypes.py` untouched):

```
  FAIL V-ARCH-TRANSITION-PERSISTENT             SIGNATURE-MISSING: s1=None s2=None
CAPABILITY_ARCHETYPES_PASS=55/56  threshold=56/56
rc=1
```

It is the only FAIL line, so the 02-04 gates and the gate's own preconditions (CONDITIONAL/intent before, STALE seen by the reader, WRITTEN on re-produce) held. GREEN: `CAPABILITY_ARCHETYPES_PASS=56/56  threshold=56/56` rc=0, with `CAPABILITY_TRAIT_SCAN_PASS=27/27`, `FAMILY_BASELINES_PASS=20/20`, `FINJ_PASS=24/24`. Tracer feedback gate: the Task 1 verify (suite exit 0, 56/56) was the run just taken after the commit's code; `<verify>` is automated-only and `human_verify_mode` is end-of-phase, so it re-ran green and expansion continued (`Tracer verified end-to-end -- expanding`). Task 1 gate evidence (GREEN run, before Task 2 changed the signature body): `CONDITIONAL/intent->REQUIRED/structural+intent sig=d361fef9ded648c0->fbf385f8fed15fd3 fp1=a3d1d02d577d4ab2->c4a802cdf383c9ab STALE seen; twin dir equal`.

## RED run 02-05 Task 2

HEAD `7c725e40`, rc=1, tests added first (new fixture kind `scheduled_cron`, three gates, the uncounted real-pole function):

```
  FAIL V-ARCH-TRANSITION-DISTRIBUTED  PRECONDITION: scheduled_cron BACKGROUND_JOB=REQUIRED modifiers=None (want REQUIRED, []); DISTRIBUTED-NOT-REPORTED: ... modifiers=None basis=None ...; INTENT-MODIFIERS-MISSING: WORLD_MUTATION modifiers=[] basis={}
  FAIL V-ARCH-SUBJECT-SHAPE           ENTRY-KEYS[fresh/BACKGROUND_JOB]: missing ['modifier_basis', 'modifiers']; ...
  PASS V-ARCH-CAUSES-REACHABLE        all 9 causes reachable (...)
CAPABILITY_ARCHETYPES_REAL_POLES=PASS
CAPABILITY_ARCHETYPES_PASS=57/59  threshold=59/59
rc=1
```

`V-ARCH-CAUSES-REACHABLE` held from its first run (every cause already had a fixture-reachable path); its instrument control is inside the gate (an added `zz-unreachable` cause must fail the predicate and be named). The real-pole line was already PASS in RED because it reads only the producer, which was complete since 02-04.

## Real-pole detail line (verbatim, GREEN run of Task 2 and, with the same trait states, the gate run)

```
  PASS V-ARCH-REAL-POLES InfinityOps (PASS; want persistent and external_effect PRESENT; held): files=4105 seconds=0.236 truncated=False budget_hit=False ecosystems=gradle,mix,npm,pip | persistent=PRESENT(dependency+marker) multi_actor=PRESENT(dependency) bulk=UNJUDGED(no-structural-detector) destructive=UNJUDGED(no-structural-detector) distributed=PRESENT(marker) external_effect=PRESENT(dependency) scheduled=PRESENT(dependency) money=PRESENT(dependency) policy_layers=ABSENT(no policy_layers evidence in a complete walk (ecosystems seen: gradle, mix, npm, pip)) ui=PRESENT(224 ui files) || ABSW2-Wii (PASS; want persistent not ABSENT; held): files=10127 seconds=0.275 truncated=False budget_hit=False ecosystems=- | persistent=UNJUDGED(no-manifest-ecosystem) multi_actor=UNJUDGED(no-manifest-ecosystem) bulk=UNJUDGED(no-structural-detector) destructive=UNJUDGED(no-structural-detector) distributed=UNJUDGED(no-manifest-ecosystem) external_effect=UNJUDGED(no-manifest-ecosystem) scheduled=UNJUDGED(no-manifest-ecosystem) money=UNJUDGED(no-manifest-ecosystem) policy_layers=UNJUDGED(no-manifest-ecosystem) ui=ABSENT(no ui evidence in a complete walk (ecosystems seen: none))
CAPABILITY_ARCHETYPES_REAL_POLES=PASS
CAPABILITY_ARCHETYPES_PASS=59/59  threshold=59/59
```

ABSW2-Wii `persistent` reads UNJUDGED `no-manifest-ecosystem`: "not ABSENT" holds, and it did not read WEAK (the plan allowed either).

## Phase gate output (code HEAD `9f3f38a0`, 2026-10-03T19:09:16Z to 19:09:55Z)

Driver: one shell script run from the worktree root, Python executed directly (no `timeout` wrapper); every file rc=0 with 0 FAIL lines:

```
test_capability_archetypes rc=0   CAPABILITY_ARCHETYPES_REAL_POLES=PASS  CAPABILITY_ARCHETYPES_PASS=59/59  threshold=59/59
test_capability_trait_scan rc=0   CAPABILITY_TRAIT_SCAN_PASS=27/27  threshold=27/27
test_family_baselines rc=0        FAMILY_BASELINES_PASS=20/20  threshold=20/20
test_family_injection rc=0        FINJ_PASS=24/24  threshold=24/24
test_tower_capsule rc=0           TOWER_CAPSULE_PASS=16/16  threshold=16/16
test_tower_inheritance rc=0       TOWER_INHERITANCE_PASS=17/17  threshold=17/17
test_tower_ratchet rc=0           TOWER_RATCHET_PASS=21/21  threshold=21/21
test_baseline_generations rc=0    BASELINE_GENERATIONS_PASS=18/18  threshold=18/18
test_tower_donegate rc=0          TOWER_DONEGATE_PASS=10/10  threshold=10/10
test_ucep_baseline_integrity rc=0 UCEP_BASELINE_INTEGRITY_PASS=40/40  threshold=40/40
test_ucep_donegate_exits rc=0     UCEP_DONEGATE_EXITS_PASS=17/17  threshold=17/17
```

**Dirty-path SET** (sorted `git status --porcelain`), BEFORE and AFTER, equal:

```
 M vault/progress.md
?? .gsd/
?? .planning/workstreams/ucep/config.json
?? .planning/workstreams/ucep/milestone.lock
?? .planning/workstreams/ucep/state.json
```

**Hermetic control:** empty directory `C:\Users\User\AppData\Local\Temp\ucep05\hermeticX`; the two new test files run with `HOME` and `USERPROFILE` set to it: both rc=0 (`59/59`, `27/27`). Recursive listing afterwards: only the directory itself, `entries under X: 0`.

**Real `traits_*.json` count:** 0 before, 0 after (equals the 02-01 value); `traits_production.jsonl` absent before and after.

**Immutability:** `git diff --quiet 409dca89 HEAD -- vault/tower` rc=0; `git status --porcelain -- vault/tower` 0 lines; the five generation files all EQUAL to the Phase 1 values (`1a501441...`, `bcb20d37...`, `98e8d33f...`, `2e54ac45...`, `2603cf39...`, full table in 02-EVIDENCE.md section 4).

**Liveness comparison** (read-only `gate()`, by unit name against `02-liveness-before.json`): `offenders 63 before 63 rows 488 new [] mine []`, rc=0. `capability_runtime/archetypes` PLANNED, `capability_runtime/trait_scan` PLANNED.

**Scope:** `git diff --name-only 409dca89 HEAD` outside `.planning/workstreams/ucep/` lists exactly `modules/capability_runtime/archetypes.py`, `modules/capability_runtime/trait_scan.py`, `tools/capability_traits.py`, `tools/test_capability_archetypes.py`, `tools/test_capability_trait_scan.py`, `vault/liveness/reachability_registry.json`; a diff over `modules/tower/families.py`, `modules/capability_runtime/applicability.py`, `modules/capability_runtime/__init__.py`, `modules/tower/capsule.py`, `tools/tower_capsule.py` and `vault/tower` printed 0 paths. Orchestration bookkeeping commits in the range (not executor plan code): `9e9953b3`, `e99168f9`, `e1ad52a8`, and the per-plan `docs(02-0N): update STATE and ROADMAP` commits.

Evidence document check (the required strings: `Production Reality`, `CAPABILITY_ARCHETYPES_PASS=59/59`, `CAPABILITY_TRAIT_SCAN_PASS=27/27`, `V-ARCH-DRILL-CEILING`, `V-ARCH-DRILL-READER-SCAN`, `V-ARCH-REAL-POLES`, `PP-Tower-Capsules`, `O-1`, `UNJUDGED`, `OBSERVED`): 0 missing. The only occurrences of the word PROVEN are its definition, `PROVEN | none` and the handoff line `no PROVEN`.

Full pointer: `.planning/workstreams/ucep/phases/02-capability-subject-and-archetypes/02-EVIDENCE.md`.

## Accomplishments

- `subject_signature(subject)` and `subject["signature"]`: a structural transition is a different compiled subject, and the same structure signs equal in two directories. The two signatures of the persistent transition (`a2e66bc6c0a0b8ea` -> `81cb73f56317c09c`) were identical across independent runs while the stored `fp1` differed with the temp directory.
- `modifiers_for()` and per-archetype `modifiers` / `modifier_basis`: `distributed` moves BACKGROUND_JOB's modifiers from `[]` to `['distributed']` with strength still REQUIRED (consequence, not complexity); intent-only destructive and bulk are recorded with basis `intent` and the same strength as without them.
- `V-ARCH-SUBJECT-SHAPE`: nine keys, JSON-safe, one entry per archetype with NONE listed (a fourth no-intent case proves a NONE entry exists to be omitted), modifier shape, over fresh, stale and missing caches.
- `V-ARCH-CAUSES-REACHABLE`: all nine causes have their own fixture, with an instrument control.
- `02-EVIDENCE.md`: scope, criterion table, RED records of all five plans, five-drill table, side effects, liveness, discretion choices, Owner assumptions, limits, Owner queue, per-component verdict.

## Task Commits

1. **Task 1 (tracer): subject signature** - `7c725e40` (feat) -- `archetypes.py`, `test_capability_archetypes.py`
2. **Task 2: modifiers, subject shape, reachable causes, real poles** - `9f3f38a0` (feat) -- same two files
3. **Task 3: phase gate and evidence** - `ad592dca` (docs) -- `02-EVIDENCE.md` only

Measured `git rev-list --count e1ad52a8..HEAD` = 3 at SUMMARY write. `git diff --name-status e1ad52a8..HEAD`: `A 02-EVIDENCE.md`, `M archetypes.py`, `M test_capability_archetypes.py`. **Plan metadata:** the docs commit carrying this file, then the STATE/ROADMAP/REQUIREMENTS commit.

## TDD Gate Compliance

Task 2 is `tdd="true"` and the plan prescribes one commit per task, so each RED state is a recorded run (stdout, rc, HEAD above) and not a `test(02-05)` commit; `git log -E --grep='^test\(02-05\)'` finds nothing, by the plan's design. Both RED runs executed before any implementation line of that task existed (the test edits precede the `archetypes.py` edits in each task).

## Decisions Made

See `key-decisions`. The plan left open: the exact signature body (named in the plan), the twin-directory construction for the host-independence check (the same transition applied to a second `ephemeral` fixture, so both directories have the same final structure), the fact that a cut real-pole walk reads UNJUDGED, and a fourth no-intent case in `V-ARCH-SUBJECT-SHAPE`.

## Deviations from Plan

### Auto-fixed Issues

None - no Rule 1-3 fix was needed.

### Choices the plan left to the executor, and small additions

1. **Real-pole cut walk.** The plan says a contradicted pole is FAIL and a missing path is UNJUDGED. A walk that hit the cap or the 60 s budget cannot contradict anything (the scan itself reads UNJUDGED for those causes), so it reads UNJUDGED for that pole. Neither real walk was cut (0.24 s and 0.28 s).
2. **Extra assertions.** `V-ARCH-SUBJECT-SHAPE` has a fourth case (no-intent prompt) so the "NONE entries are listed" claim has a NONE entry to test against, and a control line fails the gate if no NONE entry was seen. `V-ARCH-TRANSITION-DISTRIBUTED` also asserts the reader sees STALE after the compose file is added, that re-producing is WRITTEN, and that the intent-only modifiers are EXTRACTED and leave strength and basis equal to the same repository's plain prompt.
3. **`modifiers_for()` as its own public function** (the plan said `assess` adds the fields); `assess` calls it.
4. **Verify forms.** The plan gives each verify as PowerShell and Bash. No PowerShell tool was available, so the Bash forms were run. The liveness diff, the `vault/tower` diff and the scope check were run as their predicates (same code for liveness; `git diff --quiet`/`git status --porcelain` and `git diff --name-only` for scope, compared against the allowlist by reading the list; sha256 through Python `hashlib` instead of `Get-FileHash`). The suite, the string check on the evidence file and the exit codes are as specified.
5. **Hook friction, no effect on results.** The anti-thrash hook blocked a third consecutive Edit on the test file and on `archetypes.py`; a Read of the path cleared it each time. Two Edits to the test file were issued in one parallel batch in Task 1 and both applied.
6. **Branch namespace and Bash guard.** As in 02-01..02-04: sequential executor on `ucep/mission` (HEAD attached, not a protected branch, root pin guard passed before every commit); git calls carry the `# bash-safe` marker and outputs were read with Read and Grep. No guard was disabled.

**Total deviations:** 0 auto-fixed, 6 notes. **Impact:** none on scope; the three commits touch exactly the plan's frontmatter paths.

## Issues Encountered

None beyond the notes above. A `/tmp` path was unavailable to Bash on this host, so scratch logs were written under `...\AppData\Local\Temp\ucep05` (outside every repository).

## Known Stubs

None. `bulk` and `destructive` read UNJUDGED `no-structural-detector` on every repository, and four traits read UNJUDGED `no-intent-detector`: named, tested states, recorded in `02-EVIDENCE.md` section 8.

## Threat Flags

None new. T-02-15 (real-repo poles) held: `ts.scan` only, no state dir, no file created in either repository, KobiiSports Resort excluded. T-02-06 held (hermetic control empty, real `traits_*.json` count 0). T-02-16 (moved set) not triggered: dirty-path SET equal before and after. T-02-17 held (`vault/tower` unchanged, five sha equal). T-02-18 held (verdict OBSERVED, PROVEN none). T-02-09 held (`V-ARCH-CAUSES-REACHABLE` with its control).

## User Setup Required

None - no external service configuration. Owner items stay open in `02-OWNER-QUEUE.md`: O-1 (host `tools/capability_traits.py --all` on a schedule after merge), O-2 (optional Phase 6 refresh), and L-1 (a liveness exit, not an Owner action). Phase 1's A1 is also still open in STATE.md.

## Next Phase Readiness

Phase 2 is complete at the OBSERVED level. The subject carries `signature`, `modifiers` and `modifier_basis` for Phase 5's envelope compiler; nothing is wired into the prompt path (Phase 5 and 6). Until O-1 is done every real-session read of the trait cache is `no-cache` and UNJUDGED.

## Self-Check: PASSED

- Files exist: `modules/capability_runtime/archetypes.py`, `tools/test_capability_archetypes.py`, `02-EVIDENCE.md` (FOUND for each).
- Commits exist: `7c725e40`, `9f3f38a0`, `ad592dca`; `commits: 3` was measured with `git rev-list --count e1ad52a8..HEAD` before this file's own commit.
- Plan-level verification re-run at HEAD: `CAPABILITY_ARCHETYPES_PASS=59/59`, `CAPABILITY_TRAIT_SCAN_PASS=27/27`, nine regression files green, `CAPABILITY_ARCHETYPES_REAL_POLES=PASS`, liveness `new [] mine []`.

---
*Phase: 02-capability-subject-and-archetypes*
*Completed: 2026-10-03*
