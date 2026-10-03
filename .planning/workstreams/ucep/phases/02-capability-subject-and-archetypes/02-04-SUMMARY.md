---
phase: 02-capability-subject-and-archetypes
plan: 04
subsystem: capability-runtime
tags: [ucep, trait-cache, fingerprint, freshness, unjudged, read-only-reader, producer-cli, drills]

requires:
  - phase: 02-capability-subject-and-archetypes
    provides: 02-01 producer/reader split and cache schema; 02-03 trait_scan walk, evidence kinds and entitlement
provides:
  - archetypes.fingerprint(root, depth), evidence_stats(), root_manifest_stats(), MANIFEST_NAMES, TRAIT_MAX_AGE_S, CACHE_MAX_BYTES, freshness and validation in read_traits(), MSYS root form in subject_root(), now= on read_traits()/resolve()
  - trait_scan stored fingerprint block {fp1, fp2, root_manifests, evidence_files}, SKIP_WINDOW_S, skip-if-unchanged, force=/now= on produce()
  - tools/capability_traits.py out-of-band producer CLI with a symmetric production ledger
  - 18 new V-ARCH gates (55 total), three of them drills proving the reader gates can fail
affects: [02-05 subject signature, phase 6 prompt-path budget gate, Owner step O-1 (hosting the CLI)]

plan_head_before: e99168f9388772d837488a0678d6bafe71ed70d1

actuals:
  tokens: 18623
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "freshness is a cheap fingerprint plus a re-stat of the evidence files, with an age backstop: any mismatch reads STALE and every trait UNJUDGED, old readings kept only as cache.last_known"
    - "every unusable cache shape reads ten UNJUDGED with a named cause; the reader validates before it trusts (size cap, schema, ten keys, state vocabulary, repo_key, produced_at, fingerprint block, evidence paths)"
    - "a drill installs a mutation, re-runs the target predicate, and requires red + counter reached + the named sub-assertion + green after restore"
    - "a producer skip never rewrites the document, so it never extends its age"

key-files:
  created:
    - tools/capability_traits.py
  modified:
    - modules/capability_runtime/archetypes.py
    - modules/capability_runtime/trait_scan.py
    - tools/test_capability_archetypes.py

key-decisions:
  - "D-09 freshness constants: TRAIT_MAX_AGE_S = 7 days (the capsule's 24 h would read STALE every Monday on a laptop that was off; the fingerprint carries freshness, age is the backstop), SKIP_WINDOW_S = 24 h (a skip never extends a document's age, so a deep change is rewalked within a day of the scheduled run), CACHE_MAX_BYTES = 256 KiB, at most 32 evidence files recorded and re-stat'ed"
  - "fingerprint stats come from os.stat, never DirEntry.stat(): on NTFS the listing's cached directory mtime lags the real one and made two fingerprints of an untouched repository disagree"
  - "a data-file (database or world file, WEAK by name) is never an evidence file: a program rewrites it in normal use and re-stat'ing it would pin the cache STALE on any repository holding a live database"
  - "the CLI exits 1 for a FAILED single-root production too, not only under --all: a scheduler must not read a failure as success"
  - "hosting the CLI on a schedule stays Owner step O-1; nothing in this plan registers or schedules anything"

patterns-established:
  - "FINAL_GATES: a sweep gate that must see every artifact the process produced runs after all others"
  - "positive control for a counting wrapper: the same counters are shown to see a deliberate walk/scan/produce, and produce_all(None) is shown to reach a stubbed find_repos exactly once"

requirements-completed: [UCEP-02]

coverage:
  - id: D1
    description: "A cache is judged fresh by a depth-1 fingerprint (root listing plus root manifest stats), a re-stat of its evidence files and a 7 day age bound; a moved root manifest, an edited or deleted evidence file, or an old document reads STALE with every trait UNJUDGED `stale`, and a previously REQUIRED archetype falls to CONDITIONAL basis intent"
    requirement: UCEP-02
    verification:
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-STALE-MANIFEST"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-STALE-EVIDENCE-FILE"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-STALE-AGE"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-STALE-DEEP-BLINDSPOT"
        status: pass
    human_judgment: false
  - id: D2
    description: "Every unusable cache (no file, non-JSON, other schema, missing trait, unknown state, foreign repo_key, oversize, no produced_at, evidence path climbing out of the repo) reads ten UNJUDGED with a named cause and never ABSENT; slash, case, trailing-separator, subdirectory, .. and Git-Bash spellings of one repo share one cache file; a relative or missing path invents no key; nothing is written inside any repository"
    requirement: UCEP-02
    verification:
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-MISS-UNJUDGED"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-KEY-NORMALIZATION"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-CACHE-PATH-SAFE"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-CACHE-OUTSIDE-REPO"
        status: pass
    human_judgment: false
  - id: D3
    description: "The prompt-path reader performs zero walks, zero scans and zero produces and creates no file or directory, over a fresh, a stale and a missing cache"
    requirement: UCEP-02
    verification:
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-READ-ONLY"
        status: pass
    human_judgment: false
  - id: D4
    description: "The producer skips a rewalk when its depth-2 fingerprint and evidence stats are unchanged within 24 h (document and mtime untouched), and rewalks on force, on age, on a changed root manifest and on a changed evidence file"
    requirement: UCEP-02
    verification:
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-PRODUCER-SKIP"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-MANIFEST-NAMES-COVER"
        status: pass
    human_judgment: false
  - id: D5
    description: "tools/capability_traits.py is the out-of-band entry point (<root>, --all, --show, --force) with exit 0/1/2 and a ledger row for every production run, proven entirely inside a hermetic HOME"
    requirement: UCEP-02
    verification:
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-CLI-ONE"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-CLI-SHOW"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-CLI-UNRESOLVABLE"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-CLI-ALL-INJECTED"
        status: pass
    human_judgment: false
  - id: D6
    description: "The three reader gates can fail: a miss path that answers ABSENT, a reader that walks, and a fingerprint that ignores manifests each turn their target gate red for the drilled reason and green again after the restore"
    requirement: UCEP-02
    verification:
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-DRILL-ABSENT-ON-MISS"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-DRILL-READER-SCAN"
        status: pass
      - kind: unit
        ref: "tools/test_capability_archetypes.py#V-ARCH-DRILL-FP-IGNORES-MANIFEST"
        status: pass
    human_judgment: false

duration: 29min
completed: 2026-10-03
status: complete
---

# Phase 2 Plan 04: Reader freshness, cache refusal and the out-of-band producer CLI Summary

**A trait cache is now read safely on a prompt path: fingerprint, evidence re-stat and age make a moved repository read STALE then UNJUDGED, every malformed shape and every spelling of a repo path is handled, the reader is proven to walk and write nothing, and `tools/capability_traits.py` is the ledgered entry point that will host the producer.**

## Performance

- **Duration:** about 29 min
- **Started:** about 2026-10-03T18:24Z (taken from STATE's last session stamp; no start variable was captured)
- **Completed:** 2026-10-03T18:53Z
- **Tasks:** 3 (plus one follow-up test commit)
- **Files modified:** 4 (one created)

## Accomplishments

- Freshness end to end: `produce` stores `fp1`, `fp2`, the root manifest stats and the evidence-file stats (fingerprints taken before the walk); `read_traits` compares `fp1`, re-stats the evidence files, applies the 7 day bound, and on any mismatch returns STALE with ten UNJUDGED `stale` readings and the old ones only in `cache["last_known"]`.
- The reader refuses nine unusable shapes (including oversize before parsing, a `repo_key` that disagrees with its own filename, no `produced_at`, an evidence path that climbs out of the repo) with ten UNJUDGED and a named cause; Git-Bash `/c/...`, forward-slash, case, trailing-separator, subdirectory and `..` spellings share one cache file.
- Proven read-only: `V-ARCH-READ-ONLY` counts walk=0 scan=0 produce=0 over 20 `resolve` calls across a fresh, a stale and a missing cache, the `_HOME` listing is unchanged, and the same counters are shown to see a deliberate walk, scan and produce.
- Producer skip: an unchanged repository inside 24 h is not rewalked and its document is left byte-identical.
- `tools/capability_traits.py` with `<root>`, `--all`, `--show`, `--force`, exit 0/1/2 and one `traits_production.jsonl` row per production run.

## Task Commits

1. **Task 1 (tracer): fingerprint freshness end to end** - `25454743` (feat)
2. **Task 2: reader contract** - `d686f294` (feat)
3. **Task 3: producer CLI** - `a02455ed` (feat)
4. **Follow-up: pin the evidence-path traversal refusal** - `1f3c839b` (test)

**Plan metadata:** the `docs(02-04)` commit that carries this file.

## RED runs (recorded before GREEN)

- **RED run 02-04 Task 1:** rc=1, HEAD `e99168f9`, `CAPABILITY_ARCHETYPES_PASS=37/38`. Failing: `V-ARCH-STALE-MANIFEST` with `STALE-MANIFEST-NOT-DETECTED: after the edit cache=FRESH (want STALE)` and `STALE-TRAITS-NOT-UNJUDGED`. (A first run failed on a `TypeError` in the test's own message formatting; that was fixed before this RED was recorded, so the recorded failure is the planned one.)
- **RED run 02-04 Task 2:** rc=1, HEAD `25454743`, `CAPABILITY_ARCHETYPES_PASS=45/51`. Failing: `V-ARCH-STALE-EVIDENCE-FILE` (`VOLATILE-DATA-FILE-STALES-CACHE`), `V-ARCH-STALE-AGE` (constant absent, `AGE-NOT-DETECTED`), `V-ARCH-MISS-UNJUDGED` (`MISS-NOT-REFUSED` for repo-key-mismatch, oversize, produced-at-missing), `V-ARCH-KEY-NORMALIZATION` (`KEY-DIFFERS[git-bash]`, cache_path None), `V-ARCH-PRODUCER-SKIP` (`TypeError: produce() got an unexpected keyword argument 'force'`), `V-ARCH-DRILL-ABSENT-ON-MISS` (mutated red as intended; `restored ok=False` because the real reader still failed `V-ARCH-MISS-UNJUDGED`).
- **RED run 02-04 Task 3:** rc=1, HEAD `d686f294`, `CAPABILITY_ARCHETYPES_PASS=51/55`. Failing: `V-ARCH-CLI-ONE`, `V-ARCH-CLI-SHOW`, `V-ARCH-CLI-UNRESOLVABLE` (re-recorded with the CLI file set aside after the gate was tightened to require the word UNRESOLVABLE in stdout, since rc 2 is also what the interpreter returns for a missing script), `V-ARCH-CLI-ALL-INJECTED` (`ImportError`).

## GREEN lines (final run, all four suites exit 0)

```
CAPABILITY_ARCHETYPES_PASS=55/55  threshold=55/55
CAPABILITY_TRAIT_SCAN_PASS=27/27  threshold=27/27
FAMILY_BASELINES_PASS=20/20  threshold=20/20
FINJ_PASS=24/24  threshold=24/24
```

The archetype suite was run five times in a row after the producer skip landed (timestamp-sensitive code): 55/55 or 51/51 every time, no flake.

## Drill evidence (mutated predicate, counter reached, named sub-assertion, restored)

- `V-ARCH-DRILL-ABSENT-ON-MISS`: `unjudged_reading` replaced by an ABSENT-returning wrapper; mutated `V-ARCH-MISS-UNJUDGED` ok=False, wrapper calls=92, `READ-ABSENT[no-file]: a refused cache answered ABSENT for ['bulk', 'destructive', ...]`; restored ok=True.
- `V-ARCH-DRILL-READER-SCAN`: `fingerprint` replaced by a wrapper that pulls one item from `os.walk(root)`; mutated `V-ARCH-READ-ONLY` ok=False, wrapper calls=20, `READER-WALKED: os.walk calls=14 during 20 resolve calls`; restored ok=True.
- `V-ARCH-DRILL-FP-IGNORES-MANIFEST`: `MANIFEST_NAMES = frozenset()` plus a counting wrapper on `fingerprint`; mutated `V-ARCH-STALE-MANIFEST` ok=False, wrapper calls=10, `STALE-MANIFEST-NOT-DETECTED: after the edit cache=FRESH (want STALE)`; restored ok=True.

## V-ARCH-READ-ONLY latency (informational; the prompt-path budget gate is Phase 6)

`walk=0 scan=0 produce=0`, `_HOME` unchanged (90 paths). `resolve` (cache read, fingerprint, intent facts, family classification) over 20 mixed calls: median 7.28 ms / p95 16.21 ms in one run, median 10.21 ms / p95 18.05 ms in another, median 11.51 ms / p95 31.26 ms in a third. The figure moves with host load; it is far under the 3000 ms chain deadline and is not a gate here.

## Files Created/Modified

- `modules/capability_runtime/archetypes.py` - fingerprint, evidence re-stat, freshness, size/key/age validation, MSYS root form, `cache["last_known"]`
- `modules/capability_runtime/trait_scan.py` - stored fingerprint block, evidence paths, skip-if-unchanged, `force`/`now`
- `tools/capability_traits.py` - NEW out-of-band CLI and production ledger
- `tools/test_capability_archetypes.py` - 18 gates (38..55 after the tracer), `FINAL_GATES`, `EXPECTED = 55`

## Decisions Made

See `key-decisions` above. The D-09 freshness constants and why: `TRAIT_MAX_AGE_S` 7 days, `SKIP_WINDOW_S` 24 h, `CACHE_MAX_BYTES` 256 KiB, 32 evidence files.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fingerprint built on cached directory-listing stats disagreed with itself**
- **Found during:** Task 2 (`V-ARCH-PRODUCER-SKIP` returned WRITTEN instead of SKIPPED)
- **Issue:** `DirEntry.stat()` on Windows returns the listing's cached mtime/size. Measured: a freshly created directory listed an mtime 1 ms different from its own `os.stat` and kept it for seconds, so the depth-2 fingerprint taken at produce time differed from the one taken a moment later on an untouched repository.
- **Fix:** every fingerprint and manifest stat goes through `_live_stat` (`os.stat(entry.path)`).
- **Files modified:** `modules/capability_runtime/archetypes.py`
- **Verification:** skip gate green; five consecutive full runs green.
- **Committed in:** `d686f294`

**2. [Rule 2 - Missing Critical] A live data file must not be an evidence file**
- **Found during:** Task 2 design (reasoning, then pinned by a gate)
- **Issue:** the plan records every path that produced PRESENT or WEAK evidence. A WEAK `data-file` item (a `.sqlite`, `level.dat`) is rewritten by programs in normal use, so re-stat'ing it would pin the cache STALE on any repository that holds a live database; its content changes nothing the judgment uses.
- **Fix:** `_evidence_paths` skips kind `data-file`; a deletion at the root still moves the root fingerprint, elsewhere the age bound covers it. Sub-assertion (d) in `V-ARCH-STALE-EVIDENCE-FILE` drives it with a precondition that the walk saw the file. Consequence: that gate was RED against Task 1, where the plan predicted it might already pass.
- **Files modified:** `modules/capability_runtime/trait_scan.py`, `tools/test_capability_archetypes.py`
- **Committed in:** `d686f294`

**3. [Rule 2 - Missing Critical] Reader hardening beyond the listed shapes**
- **Found during:** Task 2
- **Fix:** `produced_at` is required and must be finite (NaN and infinity fail), an evidence path that is absolute, has a drive or backslash, or contains `..` makes the document `cache-malformed` instead of being stat'ed. The first is the eighth shape of `V-ARCH-MISS-UNJUDGED`; the second was unpinned until the follow-up commit `1f3c839b` added it as a ninth shape (still 55 gates). The plan listed seven shapes.
- **Files modified:** `modules/capability_runtime/archetypes.py`, `tools/test_capability_archetypes.py`
- **Committed in:** `d686f294`, `1f3c839b`

**4. [Rule 2 - clarification] CLI exit code 1 for a failed single-root production**
- **Found during:** Task 3
- **Issue:** the plan names exit 1 for `--all` only; a failed single production returning 0 would let a scheduler read a failure as success.
- **Fix:** exit 1 for any FAILED production, documented in the module docstring. No gate pins the single-root case (the plan's four CLI gates do not), so it rests on the docstring and the code.
- **Files modified:** `tools/capability_traits.py`
- **Committed in:** `a02455ed`

---

**Total deviations:** 4 auto-fixed (1 bug, 3 missing-critical/clarification). One extra commit (`1f3c839b`).
**Impact on plan:** each change narrows what the cache can wrongly claim; no scope outside the four planned files. `MANIFEST_NAMES` matches the plan's list exactly (19 names); `level.dat` and `schema.sql` were deliberately not added.

## Issues Encountered

- A test bug (a 2-tuple passed to a single `%s`) made the first Task 1 run fail for the wrong reason; fixed before recording RED.
- The CLI prints one line per repository, including `FAILED ... injected scan failure` in the injected `--all` gate; the gate now captures that output so a `FAIL` grep over the suite log stays clean (0 lines).

## Known Stubs

None. The one documented bound is deliberate and pinned: a module added below the root is caught only by the age backstop and the producer's depth-2 check (`V-ARCH-STALE-DEEP-BLINDSPOT`).

## Threat Flags

None beyond the plan's register. New surface: `tools/capability_traits.py` appends to `<state dir>/traits_production.jsonl` and writes cache files, both under the per-user state directory only (T-02-06 held: the real `~/.claude/state/tower` holds 0 `traits_*.json` and no ledger after every run).

## User Setup Required

None - no external service configuration. Hosting `tools/capability_traits.py --all` on a schedule is Owner step O-1 (`02-OWNER-QUEUE.md`) and was not done here. `--all` over the real estate was NOT run; O-1 hosts it after merge.

## Verification

- Real `traits_*.json` under `%USERPROFILE%\.claude\state\tower`: 0 (the value recorded in 02-01), checked after the final run; no `traits_production.jsonl` there either.
- `git diff --name-status e99168f9..HEAD` lists exactly: `M modules/capability_runtime/archetypes.py`, `M modules/capability_runtime/trait_scan.py`, `A tools/capability_traits.py`, `M tools/test_capability_archetypes.py`.
- No live file under `~/.claude/hooks` or `settings.json` was touched; nothing registered or scheduled.

## Next Phase Readiness

Ready for 02-05 (subject signature). The reader contract is frozen: `fingerprint`, `evidence_stats`, `read_traits(now=)`, `produce(force=, now=)` and the CLI are additive on top of the 02-01..03 API. Owner step O-1 (hosting the CLI) is the only thing standing between the cache and a populated estate.

## Self-Check: PASSED

All five created/modified files exist on disk; commits `25454743`, `d686f294`, `a02455ed`, `1f3c839b` exist; `commits: 4` was measured with `git rev-list --count e99168f9..HEAD` before this file's own commit.

---
*Phase: 02-capability-subject-and-archetypes*
*Completed: 2026-10-03*
