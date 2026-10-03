---
phase: 02-capability-subject-and-archetypes
reviewed: 2026-10-03T00:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - modules/capability_runtime/archetypes.py
  - modules/capability_runtime/trait_scan.py
  - tools/capability_traits.py
  - tools/test_capability_archetypes.py
  - tools/test_capability_trait_scan.py
  - vault/liveness/reachability_registry.json
findings:
  critical: 1
  warning: 3
  info: 7
  total: 11
status: issues_found
---

# Phase 2: Code Review Report

**Reviewed:** 2026-10-03
**Depth:** standard (one pass, six files, no git diff widening)
**Files Reviewed:** 6
**Status:** issues_found

## Summary

The reader/producer split, the single `ceiling` function, the bounded reads and the
test-side controls and drills are carefully built, and most of the hardening claimed in the
module docstrings is real. The defects found are at the seams the docstrings do not
cover. The most serious is that the producer can publish ABSENT / OBSERVED for a trait while
a manifest it could not read or parse sits in the same repository. That is the exact
"absence read from a partly read manifest is a guess" case the code itself names in a
comment. Three further problems concern whether the cache is ever read for a worktree
mission, whether it stays fresh once the mission edits its own evidence, and whether the
intent detector can make REQUIRED out of ordinary prose.

Analysis was static (Read/Grep only; no interpreter was run, because the Bash bridge guard
blocks Python on this host). Each finding below states the code path that reaches it.

## Critical Issues

### CR-01: A trait reads ABSENT/OBSERVED when only some manifests parsed (manifest errors ignored)

**File:** `modules/capability_runtime/trait_scan.py:544-550` (with `480-506`)
**Issue:** `_read_manifest` records an unreadable, oversize (> `MANIFEST_READ_MAX`, 40 KB) or
unparsable manifest in `walk["manifest_errors"]` and does not count it as parsed; the comment at
line 495 says "absence read from it would be a guess". But `_entitle` never looks at
`manifest_errors`. Its only manifest guard is:

```python
if _has_dependency_detector(trait) and walk["manifests_parsed"] == 0:
    return archetypes.unjudged_reading("no-manifest-ecosystem")
...
return archetypes.reading(archetypes.ABSENT, archetypes.OBSERVED, (), "no %s evidence in a complete walk ...")
```

State that reaches it: a repo with a small parsed `requirements.txt` (`pytest` only) plus a
`pom.xml` over 40 KB (common in enterprise Java) declaring `hibernate-core`, or a
`pyproject.toml` that `tomllib` rejects, or any manifest hit by an `OSError`. `manifests_parsed`
is 1, `walk["unreadable"]` is 0 (a manifest read error increments only `manifest_errors`), the
walk is not truncated, so `persistent`, `external_effect`, `money`, `multi_actor`, `scheduled`,
`distributed` and `policy_layers` all read `ABSENT`, fact state `OBSERVED`, reason
"... in a complete walk". The reader passes that through untouched, and the module docstring
says a later phase turns ABSENT into a justified NOT_APPLICABLE (`TRAIT_NA_REASON`). An
unread repository earns a waiver, which is the defect this phase exists to prevent.

Why the guards miss it: `V-TSCAN-PARSE-MALFORMED` (test_capability_trait_scan.py:316) and
`V-TSCAN-MANIFEST-BOUNDED` (:388) each use fixtures whose ONLY manifest fails, so
`manifests_parsed == 0` trips the guard. No gate has one good manifest next to one bad one.

**Fix:** treat any manifest error as a place the walk could not see, in `_entitle` after the
`unreadable` check:

```python
if _has_dependency_detector(trait) and walk["manifest_errors"]:
    return archetypes.unjudged_reading("unreadable-subtree")   # or a new cause "manifest-unparsed"
```

(the error list is capped at 10, so also keep a counter, `walk["manifest_failed"]`, that is not
capped). Add a gate with a good `requirements.txt` plus an oversize `pom.xml` and assert
`persistent` is UNJUDGED, with the single-manifest-fails case as the control. If a new cause is
named, add it to `UNJUDGED_CAUSES` and the reachability gate.

## Warnings

### WR-01: REQUIRED is reachable from an ordinary verb and a generic object (the D7 shape at intent level)

**File:** `modules/capability_runtime/archetypes.py:203-280` (vocabulary), `644-697` (matcher), `721-725` (ceiling)
**Issue:** The `scheduled` detector pairs the verbs `run/execute/trigger` with the objects
`task(s)/job(s)/report/sync/process/backup`, and the `persistent` detector pairs
`add/create/write/update` with `table/data/record/schema`. Both are generic words in agent
prompts and in documentation work.

Traced input: `"Execute the tasks in 02-03-PLAN.md"`. After `_fold`, "execute" and "tasks" are
both present; the gap is about 5 characters, well inside `INTENT_WINDOW` (60), so
`intent_facts` returns `scheduled` PRESENT/EXTRACTED. In any repository whose `scheduled` trait is
structurally PRESENT (any `.github/workflows/*.yml` with `cron:`, or a `celery`/`schedule`/`cron`
dependency) `ceiling(PRESENT, True, False)` returns `(REQUIRED, structural+intent)`, so
BACKGROUND_JOB is REQUIRED for a prompt that builds nothing scheduled. Likewise
`"add a table of contents to the README"` reads `persistent` PRESENT and makes WORLD_MUTATION
REQUIRED in any prisma/migrations repo; the suite's own positive control for the detector is the
bare string `"add a table"` (`V-ARCH-NOUN-ONLY-NEG`, test_capability_archetypes.py:736), so it
cannot distinguish the two.

Why the guards miss it: the structural-anchor requirement stops vocabulary alone, but once the
anchor is PRESENT (the common case for the repos this targets) the intent half is satisfied by
the closed word lists; the module's own note (lines 193-199) says structure-only CONDITIONAL
compensates for intent MISSES, and nothing compensates for intent FALSE POSITIVES. The test
corpus (`NO_INTENT`, `NOUN_ONLY`) contains no generic-object prompt of this kind.

**Fix:** drop the weakest pairings from the REQUIRED path: remove `run`/`execute`/`trigger` from
the `scheduled` verbs (keep `schedule/programa/cron`-class verbs), and require an unambiguous
persistence object for `persistent` (`table` alone is too generic; use `database`, `migration`,
`schema`, `column`, `row`). Add negative controls ("Execute the tasks in the plan", "add a table of
contents") that assert strength is CONDITIONAL, alongside the existing positive ones.

### WR-02: A worktree mission never reads the cache the producer writes for it

**File:** `modules/capability_runtime/archetypes.py:314-334, 343-349`; `tools/capability_traits.py:114-118`
**Issue:** `subject_root` delegates to `canonical_repo`, which accepts a `.git` FILE as a VCS
marker and therefore returns the worktree directory itself, not the main checkout
(`modules/repo_identity/identity.py:85-88`). `produce_all` deliberately collapses every
estate repo through `main_repo_of`, writing `traits_<key of MAIN repo>.json`. A prompt whose root
is a worktree, which is how this mission and every `.claude/worktrees/*` mission runs, resolves
`cache_path` to `traits_<key of the WORKTREE>.json`, which `--all` never produces. Result:
`cache.state == NO_CACHE`, all ten traits UNJUDGED `no-cache`, indefinitely, for the primary
operating model. The comment at line 112-113 only reasons about the opposite direction.

It fails safe (UNJUDGED, never ABSENT), which is why it is a warning and not a blocker. But the
feature is silently dead for worktree work, and no gate covers a worktree root (`grep worktree`
over both test files finds only a comment).

**Fix:** have `subject_root` (or `cache_path`) map a worktree root to its main repo with the
same `main_repo_of` logic the producer uses (move it into `modules/repo_identity`, since the
module must not import `tools/`), then add a gate: create a fixture main repo plus a `.git`-file
worktree, produce for the main repo, assert `resolve(..., worktree_root)` reads FRESH.

### WR-03: Evidence re-stat makes the mission's own first edit turn the cache STALE

**File:** `modules/capability_runtime/trait_scan.py:627-645`; reader side `archetypes.py:510-520`
**Issue:** `_evidence_paths` lists every file or directory that produced positive evidence
except `data-file` kinds, and the reader flips the whole cache to STALE (all ten traits
UNJUDGED `stale`) when any listed path's `size` or `mtime_ns` moves. For dependency manifests
that is right, because their content decides the reading. For name-only markers it is not: a
`migrations/` or `alembic/` directory is evidence by NAME, but its mtime moves whenever a
migration is added; `prisma/schema.prisma` and `schema.sql` are evidence by name, but are edited
by the very work being asked for. `ui` samples (the first five `.tsx`/`.css` files in walk order)
and `code-module` files are ordinary source files edited daily.

Traced scenario: repo with `prisma/migrations/`, producer run this morning. Prompt 1, "add a
subscriptions table with its migration", reads FRESH, WORLD_MUTATION REQUIRED. The agent runs
`prisma migrate dev`, creating `prisma/migrations/2026..._subscriptions/`. The `migrations`
directory mtime changes; the next prompt in the same mission reads STALE, `persistent`
UNJUDGED, and WORLD_MUTATION drops to CONDITIONAL/intent for the rest of the mission. The
suite pins this behaviour (`V-ARCH-STALE-EVIDENCE-FILE`, test_capability_archetypes.py:1294, edits
`prisma/schema.prisma` and expects STALE), so it is deliberate, but the stated rationale for
excluding data files (a rewritten file pins the cache STALE, lines 634-638) applies equally here.

**Fix:** record per evidence item whether its content decided the reading and re-stat only
those (manifests parsed for dependencies, `cron:`/workload YAML, `vercel.json`). Name-only
markers and directories are already covered by the root and depth-2 fingerprints for deletion
and by the age bound. Keep the manifest-edit gate; replace the schema.prisma edit gate with one
that asserts it stays FRESH, and keep a delete-the-marker gate as the STALE case.

## Info

### IN-01: `repo_key` is lossy and the stored `repo` path is never compared

**File:** `modules/capability_runtime/archetypes.py:549`; `trait_scan.py:712`
**Issue:** `repo_key` replaces every non-alphanumeric with `-`, so `C:\a\my-app`, `C:\a\my_app` and
`C:\a\my app` share one cache file. The reader's guard `doc.get("repo_key") != repo_key(sroot)`
compares the colliding key to itself, so it cannot detect this. The depth-1 fingerprint usually
makes the second repo read STALE, but two structurally identical clones would share a FRESH
document. The document already stores `"repo": sroot`.
**Fix:** also require `os.path.normcase(doc.get("repo")) == os.path.normcase(sroot)` and
otherwise return `malformed("repo")`.

### IN-02: Depth-2 fingerprint comment says it skips what the producer skips; it does not

**File:** `modules/capability_runtime/archetypes.py:132-133`
**Issue:** `_FP_SKIP_DIRS = frozenset(_FAMILY_SKIP_DIRS)`, but the producer prunes `trait_scan.SKIP_DIRS`
(adds `vendor`, `obj`, `bin`, `Pods`, `Library`, `Temp`, `.gradle`, ...). The depth-2 fingerprint
therefore hashes the mtime and listing of `bin/` and `obj/` build output, so `_skippable` almost
never skips a .NET or Unity repository and rewalks it on every run. Harmless to correctness, but
the comment is false and the skip rule is weaker than documented.
**Fix:** share one skip set, defined in `archetypes.py` (the reader must not import
`trait_scan`) and extended by `trait_scan`, or correct the comment.

### IN-03: `os.replace` can fail on Windows while a reader has the cache open, and the producer never retries

**File:** `modules/capability_runtime/trait_scan.py:719-721`
**Issue:** The reader opens the cache with Python `open(path, "rb")`, which on Windows does not
share DELETE access. A producer `os.replace` in that window raises `PermissionError`, caught as
`FAILED` (nothing published, exit 1, ledger row). With the reader running on every prompt this is
rare but real. It self-heals on the next run.
**Fix:** retry `os.replace` three times with a 50 ms sleep before reporting FAILED.

### IN-04: `capability_traits.py` exit codes and ledger do not match the module docstring in the `--all` paths

**File:** `tools/capability_traits.py:20-27, 107-134`
**Issue:** The docstring says exit 2 means "root unresolvable" and "every production run appends one row". In
`--all`, an UNRESOLVABLE repo (a deleted project still on the estate list) is counted and the run
exits 0; an empty estate (`find_repos()` returning `[]`) prints `TRAITS 0 {}` and exits 0; an
exception from `find_repos`/`main_repo_of` propagates as a traceback with no ledger row, which is the
"task ran but left no trace" case the ledger exists for. `produce_one` also returns 2 before writing
a ledger row.
**Fix:** wrap the enumeration in try/except that writes a `{"outcome": "ENUMERATION_FAILED"}` row
and returns 1; return 1 when `repos` is empty; document UNRESOLVABLE-under-`--all` as exit 0 or
make it non-zero.

### IN-05: Registry note for `trait_scan` names the wrong proving test

**File:** `vault/liveness/reachability_registry.json:76`
**Issue:** The `capability_runtime/trait_scan` note says "Proven by tools/test_capability_archetypes.py".
That file exercises `trait_scan` end to end, but `tools/test_capability_trait_scan.py` exists for
exactly this module and is not named. `V-ARCH-LIVENESS-DECLARED` only checks the `Owner queue:`
path, so the note can drift unnoticed. The third new unit, `tools/capability_traits.py`, is not a
`modules/` entry so it needs no row; the notes do reference it correctly as the producer host.
**Fix:** name both test files in the note.

### IN-06: `V-ARCH-REAL-POLES` makes the exit code depend on mutable external repositories

**File:** `tools/test_capability_archetypes.py:2247-2293, 2318`
**Issue:** The gate scans two hard-coded repositories under `C:\Users\User\Desktop\...` and returns FAIL
(exit 1) when `InfinityOps` stops being persistent+external_effect PRESENT, for example after a
dependency rename, a branch checkout or a moved folder (missing path reads UNJUDGED, but a
changed repo reads FAIL). A phase gate that can go red from a change outside the repo and the
phase is a reliability defect in the gate. It is also hard-coded to one user's machine.
**Fix:** report the poles as OBSERVED evidence without feeding the exit code, or move the
expectation into a predeclared fixture snapshot.

### IN-07: A future-dated `produced_at` bypasses the reader's age backstop

**File:** `modules/capability_runtime/archetypes.py:559-575`
**Issue:** The age test is `age = now - produced_at; if age > TRAIT_MAX_AGE_S`. A document with
`produced_at` far in the future (clock step, restored backup, hand edit; the sanity check only
rejects values beyond +/-1e18) gives a negative age and is never age-stale. `trait_scan._skippable`
already guards `0 <= now - produced_at`, so the two sides disagree.
**Fix:** treat `age < -TRAIT_CLOCK_SKEW_S` (for example 3600) as stale with reason
"produced_at is in the future".

---

_Reviewed: 2026-10-03_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
