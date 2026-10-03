---
phase: 02-capability-subject-and-archetypes
plan: 03
subsystem: capability-runtime
tags: [ucep, trait-scan, declared-dependencies, entitlement, unjudged, weak-evidence, junction, secret-safety]

requires:
  - phase: 02-capability-subject-and-archetypes
    provides: 02-01 producer/reader split and vocabulary; 02-02 ceiling() and bilingual intent facts
provides:
  - trait_scan._entitle() -- the one function that decides ABSENT vs UNJUDGED with a cause precedence
  - eight declared-dependency parsers (npm, pip, pyproject, mix, maven, gradle, cargo, go) and DEP_SIGNALS for seven traits
  - MARKER_SIGNALS (persistent, distributed, scheduled, multi_actor, policy_layers), UI count threshold, WEAK data-file and source-module classes
  - junction/symlink prune, vendored-tree skip, secret-file refusal, bounded manifest reads
  - tools/test_capability_trait_scan.py -- 27 hermetic V-TSCAN gates
affects: [02-04 freshness and CLI, 02-05 subject signature, phase 5 envelope compiler, phase 7 R-3 calibration]

plan_head_before: f90e491139bde76ef163a937cb1d9a6a5321071e

actuals:
  tokens: 18785
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "one entitlement function: positives win whatever the walk did; with none, a fixed cause precedence yields UNJUDGED or ABSENT"
    - "declared names only: parsed per ecosystem, matched by exact equality with `_` and `-` folded, never a substring or free text"
    - "every `nothing found` gate carries a control in which the same detector finds the thing"
    - "a link test control: the junction gate disables the prune and requires the walk to enter the link"

key-files:
  created:
    - tools/test_capability_trait_scan.py
  modified:
    - modules/capability_runtime/trait_scan.py
    - tools/test_capability_archetypes.py

key-decisions:
  - "An over-limit manifest (> 40 KiB) is recorded in manifest_errors and does not count as parsed, in every format, because absence read from a partly read manifest would be a guess"
  - "A go.mod `// indirect` requirement is not a declared dependency; a pom `<dependencyManagement>` entry and a plugin's own dependencies are not the project's"
  - "`_` and `-` fold together at match time (`slack_sdk`, `psycopg2_binary`); parsers return names as declared, lower-cased, and evidence strings carry that spelling"
  - "ui evidence is up to five sample file paths and the count rides in the reading reason (`25 ui files`)"
  - "a content-marker file that cannot be opened raises the walk's `unreadable` count, so a blind spot reads UNJUDGED unreadable-subtree instead of ABSENT"
  - "a Windows thumbnail cache `Thumbs.db` is not WEAK persistent evidence"

patterns-established:
  - "a secret-shaped basename is counted as a file and never opened: one guard in the walk loop covers manifests and marker reads"
  - "producer seams are module globals (`_walk`, `os.path.islink`/`isjunction` called by attribute) so a gate can mutate them and require the result to change"

requirements-completed: [UCEP-02]

coverage:
  - id: D1
    description: "A trait without positive evidence reads ABSENT only when its walk completed with a parsed manifest where a dependency detector exists; a cut (cap or budget), unreadable or blind walk reads UNJUDGED with the precise cause, and positives found before a cut are kept"
    requirement: UCEP-02
    verification:
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-TRUNCATED"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-BUDGET"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-BLIND-ECOSYSTEM"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-UNREADABLE-SUBTREE"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-NO-STRUCTURAL-DETECTOR"
        status: pass
    human_judgment: false
  - id: D2
    description: "Structural traits come from declared dependency names in eight ecosystems and from named markers; descriptions, lookalike names and dev-only declarations never produce a PRESENT reading; data files, source modules and policy directories are WEAK"
    requirement: UCEP-02
    verification:
      - kind: unit
        ref: "tools/test_capability_trait_scan.py#V-TSCAN-PARSE-NPM..GOMOD (8 parser gates)"
        status: pass
      - kind: unit
        ref: "tools/test_capability_trait_scan.py#V-TSCAN-DEP-NOT-TEXT"
        status: pass
      - kind: unit
        ref: "tools/test_capability_trait_scan.py#V-TSCAN-SUBSTRING-NOT-DEP"
        status: pass
      - kind: unit
        ref: "tools/test_capability_trait_scan.py#V-TSCAN-DEV-ONLY-WEAK"
        status: pass
      - kind: unit
        ref: "tools/test_capability_trait_scan.py#V-TSCAN-DEP-POLES"
        status: pass
      - kind: unit
        ref: "tools/test_capability_trait_scan.py#V-TSCAN-DATAFILE-WEAK"
        status: pass
      - kind: unit
        ref: "tools/test_capability_trait_scan.py#V-TSCAN-CODE-MODULE-WEAK"
        status: pass
      - kind: unit
        ref: "tools/test_capability_trait_scan.py#V-TSCAN-PERSIST-VOCAB-SUPERSET"
        status: pass
    human_judgment: false
  - id: D3
    description: "Each archetype is REQUIRED end to end (fixture repo -> producer -> cache -> resolve) for its Spanish and English prompt with evidence naming the manifest and dependency, and drops to CONDITIONAL basis intent when that dependency is absent"
    requirement: UCEP-02
    verification:
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-POSITIVE-WORLD_MUTATION"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-POSITIVE-EXTERNAL_EFFECT"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-POSITIVE-BACKGROUND_JOB"
        status: pass
    human_judgment: false
  - id: D4
    description: "The producer never descends vendored, generated or linked trees, never opens .env, key or certificate files, reads manifests bounded, and stores only relative forward-slash paths and dependency names"
    requirement: UCEP-02
    verification:
      - kind: unit
        ref: "tools/test_capability_trait_scan.py#V-TSCAN-SKIP-VENDORED"
        status: pass
      - kind: unit
        ref: "tools/test_capability_trait_scan.py#V-TSCAN-JUNCTION-SKIP"
        status: pass
      - kind: unit
        ref: "tools/test_capability_trait_scan.py#V-TSCAN-NO-SECRET-READ"
        status: pass
      - kind: unit
        ref: "tools/test_capability_trait_scan.py#V-TSCAN-EVIDENCE-SHAPE"
        status: pass
      - kind: unit
        ref: "tools/test_capability_trait_scan.py#V-TSCAN-MANIFEST-BOUNDED"
        status: pass
      - kind: unit
        ref: "tools/test_capability_trait_scan.py#V-TSCAN-PARSE-MALFORMED"
        status: pass
    human_judgment: false
  - id: D5
    description: "Marker-class detectors for distributed, scheduled, multi_actor, policy_layers and ui (file-count threshold) judge by exact names, directory shapes and the decisive token of a named file"
    requirement: UCEP-02
    verification:
      - kind: unit
        ref: "tools/test_capability_trait_scan.py#V-TSCAN-MARKER-PERSISTENT"
        status: pass
      - kind: unit
        ref: "tools/test_capability_trait_scan.py#V-TSCAN-MARKER-DISTRIBUTED"
        status: pass
      - kind: unit
        ref: "tools/test_capability_trait_scan.py#V-TSCAN-MARKER-SCHEDULED"
        status: pass
      - kind: unit
        ref: "tools/test_capability_trait_scan.py#V-TSCAN-MARKER-MULTI-ACTOR"
        status: pass
      - kind: unit
        ref: "tools/test_capability_trait_scan.py#V-TSCAN-MARKER-POLICY-WEAK"
        status: pass
      - kind: unit
        ref: "tools/test_capability_trait_scan.py#V-TSCAN-UI-THRESHOLD"
        status: pass
    human_judgment: false
  - id: D6
    description: "The persistent source-module signal (R-3) ships WEAK and provisional; its calibration against KobiiSports Resort is Phase 7"
    requirement: UCEP-02
    verification: []
    human_judgment: true
    rationale: "Whether a save/persistence/storage segment predicts real persistence in the Owner's repositories is an empirical calibration this phase deliberately does not perform"

duration: 22min
completed: 2026-10-03
status: complete
---

# Phase 2 Plan 03: Declared-dependency detectors and honest absence Summary

**A walk that was cut, starved, blind or partly unreadable can no longer read ABSENT: `_entitle()` decides every trait, eight declared-dependency parsers and five marker classes supply STRONG and WEAK evidence, junctions and secret files are never entered, and each archetype is REQUIRED end to end only while its anchor dependency exists (37/37 and 27/27 gates)**

## Performance

- **Duration:** 22 min
- **Started:** 2026-10-03T18:00:12Z
- **Completed:** 2026-10-03T18:21:04Z (last task commit and final gate run)
- **Tasks:** 3 (1 tracer, 2 TDD auto)
- **Files:** 3 (1 created `tools/test_capability_trait_scan.py`, 2 modified)

## RED runs (before any implementation line of the task existed)

**RED run 02-03 Task 1.** HEAD `f90e491139bde76ef163a937cb1d9a6a5321071e`, `tools/test_capability_archetypes.py`, rc=1, `CAPABILITY_ARCHETYPES_PASS=29/33  threshold=33/33`, exactly the four planned failures:

```
FAIL V-ARCH-TRUNCATED          far: persistent=UNJUDGED/no-structural-detector (want UNJUDGED/truncated, never ABSENT or no-structural-detector)
FAIL V-ARCH-BUDGET             persistent=UNJUDGED/no-structural-detector; no trait carries budget-exhausted (reasons=['no-structural-detector'])
FAIL V-ARCH-BLIND-ECOSYSTEM    zero_manifest persistent=UNJUDGED/no-structural-detector (want UNJUDGED/no-manifest-ecosystem); CONTROL: ephemeral persistent=UNJUDGED/no-structural-detector fact_state=UNKNOWN (want ABSENT/OBSERVED)
FAIL V-ARCH-UNREADABLE-SUBTREE AttributeError: module 'modules.capability_runtime.trait_scan' has no attribute '_walk'
```

**RED run 02-03 Task 2.** HEAD `994200c4`, rc=1 for both files.

- `tools/test_capability_archetypes.py`: `CAPABILITY_ARCHETYPES_PASS=33/36`; the three V-ARCH-POSITIVE-* gates fail (`('CONDITIONAL', 'intent') evidence=[]`, no pip parser and no external_effect or scheduled detector).
- `tools/test_capability_trait_scan.py`: `CAPABILITY_TRAIT_SCAN_PASS=2/14`. Seven parser gates fail with `AttributeError ... no attribute '_parse_requirements'` and its siblings; MALFORMED, DEP-NOT-TEXT, DEV-ONLY-WEAK and MANIFEST-BOUNDED fail on their controls (`scheduled=UNJUDGED` where the control needs PRESENT). Two pass already, each with a control: `V-TSCAN-PARSE-NPM` (the npm parser landed in Task 1) and `V-TSCAN-SUBSTRING-NOT-DEP` (control `pg` PRESENT held since Task 1).

**RED run 02-03 Task 3.** HEAD `d2c26ee98ce9a74199e00c22a25beb3fae8f1864`, rc=1 for both files.

- `tools/test_capability_archetypes.py`: `CAPABILITY_ARCHETYPES_PASS=36/37`; `V-ARCH-NO-STRUCTURAL-DETECTOR` fails on its control, `{'distributed': 'ABSENT', 'ui': 'UNJUDGED'}`.
- `tools/test_capability_trait_scan.py`: `CAPABILITY_TRAIT_SCAN_PASS=17/27`. Ten FAIL: DATAFILE-WEAK, CODE-MODULE-WEAK, MARKER-DISTRIBUTED, MARKER-SCHEDULED, MARKER-MULTI-ACTOR, MARKER-POLICY-WEAK, UI-THRESHOLD, JUNCTION-SKIP, NO-SECRET-READ, PERSIST-VOCAB-SUPERSET. Three PASS already: MARKER-PERSISTENT (the 02-01 inline check), SKIP-VENDORED (the skip set from 02-01) and EVIDENCE-SHAPE.
- The junction red evidence measured RESEARCH A10: on this host `os.walk(followlinks=False)` DOES descend a directory junction. A fixture holding 2 files read `files with link 128 == without 2`, with evidence paths like `linkloop/linkloop/linkloop/...`.

## GREEN lines

| After | Archetypes | Trait scan | Regression |
|---|---|---|---|
| Task 1 (`994200c4`) | `33/33  threshold=33/33` rc=0 | -- | `FAMILY_BASELINES_PASS=20/20`, `FINJ_PASS=24/24` |
| Task 2 (`d2c26ee9`) | `36/36  threshold=36/36` rc=0 | `14/14  threshold=14/14` rc=0 | 20/20, 24/24 |
| Task 3 (`275f14e1`) | `37/37  threshold=37/37` rc=0 | `27/27  threshold=27/27` rc=0 | 20/20, 24/24 |

The tracer feedback gate (Task 1's `<verify>` re-run end to end before expansion) is the Task 2 RED run: all 33 earlier gates still PASS there. Logged `Tracer verified end-to-end -- expanding`.

## Task 2 -> Task 3 transient (marker-only repos)

Between the Task 2 and Task 3 commits (commits `d2c26ee9` .. `275f14e1`) a trait whose marker class did not exist yet read ABSENT for a repository holding only that marker, because a neutral manifest was parsed and the walk was complete. The Task 3 RED run shows it exactly: `docker-compose.yml`, `fly.toml`, `k8s/app.yaml` -> distributed ABSENT; the workflow with `cron:` and `vercel.json` with `crons` -> scheduled ABSENT; `plugin.yml` -> multi_actor ABSENT; ui read UNJUDGED `no-structural-detector`. The Task 3 commit closes it. Marker-only repos in that one-commit window were never produced into a real cache (the producer is not yet hosted, Owner queue O-1).

## Detector vocabularies (final sizes)

- **PARSERS:** 9 basenames over 8 ecosystems (`package.json`, `requirements.txt`, `pyproject.toml`, `mix.exs`, `pom.xml`, `build.gradle`, `build.gradle.kts`, `cargo.toml`, `go.mod`).
- **DEP_SIGNALS:** 113 names. persistent 32, external_effect 28, money 9, multi_actor 13, scheduled 14, distributed 10, policy_layers 7 (always WEAK).
- **MARKER_SIGNALS:** 5 traits (persistent, distributed, scheduled, multi_actor, policy_layers). persistent: 2 strong files, 2 strong dirs, 4 weak extensions, 1 weak file, 1 weak dir. `CODE_MODULE_SEGMENTS` 7, `CODE_MODULE_EXTENSIONS` 14, `UI_EXTENSIONS` 13, `UI_PRESENT_MIN` 20.
- Traits with no structural detector, by design: `bulk`, `destructive` (UNJUDGED `no-structural-detector` on every repository).

## Accomplishments

- `_entitle(trait, found, walk)` is the single decision point. PRESENT if any STRONG evidence, else WEAK, whatever the walk did; with none, the cause precedence is no-structural-detector, truncated, budget-exhausted, unreadable-subtree, no-manifest-ecosystem, then ABSENT with the ecosystems seen in the reason.
- Four real-repo failure modes from RESEARCH F5 are each pinned by a gate with a control: a description string cannot fire `scheduled`; `vector-math` cannot match `ecto`; three zero-manifest repos read UNJUDGED not ABSENT; a Unity package cache cannot produce a migration marker.
- The junction defect was reproduced before it was fixed (128 files vs 2) and the gate shows it can fail: with the link test disabled the same scan enters the link.
- `.env*`, `*.key`, `*.pem` and `id_rsa*` are counted as files and never opened; the open wrapper over `builtins.open`, `io.open` and `trait_scan.open` recorded `app.yaml, ci.yml, package.json, vercel.json` and nothing secret-shaped, with a positive control that `package.json` was seen.
- Each archetype is REQUIRED end to end in Spanish and English with evidence such as `requirements.txt:sqlalchemy`, `package.json:resend`, `requirements.txt:apscheduler`, and CONDITIONAL basis `intent` (anchor ABSENT) when the dependency is removed.

## Task Commits

1. **Task 1 (tracer): entitlement, package.json parser, truncation/budget/unreadable bookkeeping** - `994200c4` (feat)
2. **Task 2: eight parsers, dependency-class detectors, archetype positives, new producer test file** - `d2c26ee9` (feat)
3. **Task 3: marker classes, WEAK data and source-module signals, UI threshold, junction and vendored skip, evidence shape, no secret reads** - `275f14e1` (feat)

Measured `git rev-list --count f90e4911..HEAD` = 3 at SUMMARY write. `git diff --name-status f90e4911..HEAD` lists exactly `M modules/capability_runtime/trait_scan.py`, `M tools/test_capability_archetypes.py`, `A tools/test_capability_trait_scan.py` (the plan's three frontmatter paths). The diff against the 02-02 task head `9d1b57c4` additionally shows the 02-02 close-out files (ROADMAP, STATE, 02-02-SUMMARY), which predate this plan.

**Plan metadata:** the SUMMARY commit and the STATE/ROADMAP commit follow.

## TDD Gate Compliance

Tasks 2 and 3 are `tdd="true"`, and the plan prescribes ONE commit per task, so each RED state is recorded as a run (stdout, rc, HEAD above), not as a separate `test(02-03)` commit. `git log -E --grep='^test\(02-03\)'` therefore finds nothing, by the plan's design. All three RED runs executed before any implementation line of that task existed; the only test edit after a RED run was the PIP fixture's expected spelling (see Deviations).

## Decisions Made

See `key-decisions`. The plan left open: the over-limit manifest rule, how `// indirect` Go requirements and pom BOM entries count, the ui evidence shape, and name folding.

## Deviations from Plan

### Auto-fixed Issues

None - no Rule 1-3 fix was needed.

### Choices the plan left to the executor, and small additions

1. **Test expectation changed after RED (Task 2).** The PIP fixture first expected `psycopg2-binary` from `psycopg2_binary`; the plan lists `slack_sdk` (underscore) and `psycopg2-binary` (hyphen) as signal names, so folding at match time was the consistent design, and the parser now returns the name as declared. The RED run was unaffected (every parser gate failed on a missing attribute).
2. **`Thumbs.db` ignored (Task 3).** A Windows thumbnail cache matches the plan's `.db` weak extension; it is excluded and `V-TSCAN-DATAFILE-WEAK` carries a control for it.
3. **Extra gate assertions.** `V-TSCAN-UI-THRESHOLD` also asserts the edge (19 files WEAK, 20 files PRESENT); `V-TSCAN-MARKER-SCHEDULED` asserts a commented `# cron:` line reads nothing; `V-TSCAN-MARKER-DISTRIBUTED` covers `helm/` StatefulSet, `deploy/` CronJob and a Deployment YAML outside the named directories.
4. **Rich fixture is built in the gate** (`make_rich_repo`, a `persistent_prisma` repo plus extra files) rather than as a `make_repo` kind; behaviour identical to the plan's `rich` repo.
5. **Unused parameter.** `_file_markers` still receives `rel_dir`, which only the call site uses; harmless and left to avoid a further edit round.

**Total deviations:** 0 auto-fixed; 5 notes above. **Impact:** none on scope; the committed paths equal the frontmatter `files_modified`.

### Execution-environment notes (not code deviations)

- **Branch namespace and Bash guard.** As in 02-01 and 02-02: the sequential executor on the orchestrator-designated branch `ucep/mission` (HEAD attached and not a protected branch, root pin guard `PIN_OK` before every commit); git calls carry the guard's `# bash-safe` marker and test output was read with Read and Grep. No guard was disabled.
- **Anti-thrash hook.** It blocked a third consecutive Edit or Write on the same path four times (including a commit-message path reused from an earlier plan); each time a Read of the path or a fresh message filename cleared it.

## Issues Encountered

None beyond the environment notes. The Task 3 junction gate creates a real directory junction inside a temp fixture and removes only the link in `finally`; nothing outside the fixture was touched.

## Known Stubs

None. `bulk` and `destructive` read UNJUDGED `no-structural-detector` on purpose (no honest structural signal exists), and the persistent source-module class is WEAK and provisional by design (R-3, calibration is Phase 7, coverage item D6 is marked human-judgment for that reason).

## Threat Flags

None new. T-02-03 (secret reads), T-02-04 (junction loops and vendored caches), T-02-12 (adversarial manifests) and T-02-13 (text and substring spoofing) are mitigated as planned and covered by `V-TSCAN-NO-SECRET-READ`, `V-TSCAN-JUNCTION-SKIP`, `V-TSCAN-SKIP-VENDORED`, `V-TSCAN-PARSE-MALFORMED`, `V-TSCAN-MANIFEST-BOUNDED`, `V-TSCAN-SUBSTRING-NOT-DEP` and `V-TSCAN-DEP-NOT-TEXT`. T-02-06 holds: the new test file sets the hermetic HOME before importing `modules` and calls `scan` directly, so it writes no cache.

## User Setup Required

None - no external service configuration. The producer is still not hosted on a schedule (Owner queue O-1 from 02-01), so every real-session read is `no-cache` -> UNJUDGED until that step is done.

## Next Phase Readiness

- 02-04 can add freshness (fingerprint and age), MSYS-form roots and the CLI against a producer whose readings are now honest; `SKIPPED` and `produce()`'s document shape are unchanged, and the walk record gained `manifests_parsed`, `ecosystems`, `unreadable`, `manifest_errors`.
- The 02-01/02-02 `archetypes` API is untouched (this plan edits only `trait_scan.py` and the two test files).
- Phase 7 owns the R-3 calibration of the source-module signal.
- No blockers.

## Self-Check: PASSED

- Created and modified files exist: `modules/capability_runtime/trait_scan.py`, `tools/test_capability_archetypes.py`, `tools/test_capability_trait_scan.py` (FOUND for each).
- Commits exist: `994200c4`, `d2c26ee9`, `275f14e1` (each in `git log f90e4911..HEAD`).
- Plan-level verification re-run at HEAD `275f14e1`: `CAPABILITY_ARCHETYPES_PASS=37/37`, `CAPABILITY_TRAIT_SCAN_PASS=27/27`, `FAMILY_BASELINES_PASS=20/20`, `FINJ_PASS=24/24`, all rc=0; the diff against the plan head lists only the three frontmatter paths.

---
*Phase: 02-capability-subject-and-archetypes*
*Completed: 2026-10-03*
