---
phase: 01-usage-index-v5-substrate
plan: 04
subsystem: usage_index
tags: [usage-index, schema-v5, population, kme-classifier, archived-rule, reconcile, backfill, cold-build, mutation-drill]
requires: [01-03]
provides:
  - "population(): KME-L selection from the index alone with the champion's own classify/is_kme (loaded by path, no threshold copied), time cut on features and calls, occurrence-view calls, ARCHIVED_RULE in every answer, typed UNMEASURED refusals, reconcile block, EXACT/DRIFTED vs an expected record"
  - "backfill_v5(): opt-in, bounded re-read of only the bytes below each legacy file's committed offset; v5 tables only; reports bytes_reread; second run reads 0"
  - "CLI: population flags (--host, --tolerate-parse-errors, --expect KEY|JSON|FILE, --expect-file default DEFAULT_DENOM_FILE, --perturb, --detail, --plane), backfill-v5, refresh --all / --since-days 0, proc {rchar_delta, maxrss_kb}"
  - "tis_observed.calls_from(end_offset=)"
affects: [01-05, 01-06]
tech-stack:
  added: []
  patterns: ["champion functions applied to a feature dict built from stored rows", "bounded re-read through a committed-offset ceiling", "temp-table selection for reconcile joins", "source-text and in-process mutants driven from the gate file"]
key-files:
  created: []
  modified:
    - tools/usage_index.py
    - tools/tis_observed.py
    - tools/test_usage_index_v5.py
key-decisions:
  - "An UNMEASURED population answer carries population=None and the numbers actually seen under observed_partial: a refused answer never offers a number that could be read as the population (nor as zero)."
  - "Pattern drift is checked against the champion's CURRENT pattern set (recomputed from the loaded KME_RE) as well as meta pattern_set: a stale meta cannot launder hits measured under an older regex. select=all reads no pattern and is not refused for drift."
  - "An empty selection (select kme selects no session, or no session exists at the instant) refuses (UNMEASURED 'empty population'), not EXACT-with-zeros."
  - "expected must carry every VERDICT_FIELDS integer, else UNMEASURED: EXACT is never reachable by a vacuous record. Deltas are observed minus expected (perturb calls+1 -> delta -1)."
  - "A session exists at U when the earliest first_ts of its files is <= U; a file with no timestamp contributes nothing under a window (the champion's make_keep keeps nothing for it)."
  - "classifier cwd = first eligible recorded cwd of the session's main file by first_off, else the subagent files in path order (the champion's scan order)."
  - "reconcile shared_outside looks at outside files without the time cut (presence of the key, not its timing)."
  - "backfill_v5 takes proj for CLI symmetry only; candidates are the index's own legacy rows (stored absolute paths)."
status: complete
plan_head_before: 8ed112a4fc3b99215eac050a96aa158a15d87466
commits: 2
actuals:
  tokens: 22000
  tasks: 2
  commits: 2
duration: single session
completed: 2026-10-06
---

# Phase 1 Plan 04: population against the champion, opt-in backfill, cold build and cost surface Summary

The index now answers "which sessions are KME-L and what did they cost, as of an instant" the way the frozen champion does (parity pinned on a hermetic tree against `kme_pillars`: same existing sessions, same class per session, same selection, same totals), says UNMEASURED with named reasons whenever it cannot, shows every dedup decision in a reconcile block, and gives history a deliberate, visible, bounded way to reach v5 coverage.

## Tasks

| Task | Name | Commit |
|---|---|---|
| 1 | population() with the champion's classifier, time cut, archived rule, typed refusals and the reconcile block | 2cf6e550 |
| 2 | Opt-in history backfill, cold-build flag and cost counters on the CLI | dd69209e |

## Gate outputs

- `python3 tools/test_usage_index_v5.py` -> `USAGE_INDEX_V5_PASS=71/71  threshold=71/71`
- `python3 tools/test_usage_index_v5.py --drill` -> control 71/71, M1-M18 all KILLED, clean rerun 71/71, `DRILL killed=18/18` (no SURVIVED, no INVALID)
- `python3 tools/test_usage_index.py` -> `USAGE_INDEX_PASS=22/22  threshold=22/22`
- `python3 tools/test_usage_index_identity.py` -> `USAGE_INDEX_IDENTITY_PASS=11/11`; `test_store_identity_consumers.py` -> `STORE_IDENTITY_CONSUMERS_PASS=12/12`; `test_spawn_outcomes.py` -> `SPAWN_OUTCOMES_PASS=24/24`
- `python3 tools/test_kme_pillars.py` -> `KMEP_PASS=89/89  threshold=89/89  skipped=0  inconclusive=0` (as in 01-BASELINE.md)
- Consumers unchanged against 01-BASELINE: fanout 17/17, root_progress 11/11, spawn_policy_v2 26/26, async 12/12, goal_journey 7/7, execution_shape 14/14, displacement 16/16.
- `git status --porcelain -- wiki/tools` prints nothing; `grep -c "0.30" tools/usage_index.py` = 0; `VERDICT_FIELDS` / `DEFAULT_DENOM_FILE` present; `python3 tools/usage_index.py --help` lists `population` and `backfill-v5`; `--expect KME-L` resolves the frozen record (34871 calls / 11549646300 cache_read) without being used by any hermetic gate.

## Mutants registered

| Mutant | Kills |
|---|---|
| M15 archived exclusion removed from population (source text) | V-UX5-ARCHIVED-RULE |
| M16 time cut removed from the classifier feature query (source text) | V-UX5-KME-CLASSIFIER-PARITY |
| M17 session calls read from calls.file instead of call_files (source text) | V-UX5-RECONCILE-SHARED |
| M18 backfill reads without end_offset (in-process patch of calls_from) | V-UX5-BACKFILL-STOPS-AT-OFFSET |

## Gates added (each with a control that can return the other answer)

Task 1: V-UX5-KME-CLASSIFIER-PARITY (index vs champion: 10 existing sessions, 6 selected, all four classes, a session that turns KME only after U, a session that starts after U, a ts-less file, a subagent file, user-text hits, project-name, cwd and host rules, an `_archived` project) + V-UX5-KME-PARITY-NONDEGENERATE (the fixture could have failed: class flips without the cut, the host rule only fires for gex44, FUTURE absent), V-UX5-POP-EXACT, V-UX5-POP-DRIFTED (CLI exit 0 / 1, delta -1 on calls only), V-UX5-ARCHIVED-RULE (default / include_archived / twin), V-UX5-POP-REFUSES-PARSE (+ -TOLERATES-PARSE), V-UX5-POP-REFUSES-FILE-ERROR, V-UX5-POP-REFUSES-LEGACY (control: a cold build of the same tree is MEASURED), V-UX5-POP-REFUSES-PATTERN-DRIFT (controls: unchanged -> MEASURED, select all on a drifted index -> MEASURED), V-UX5-RECONCILE-SHARED (both ingest orders: occurrence totals identical, first_writer differs 2 vs 3, unique 3 of 4 occurrences, shared_outside 1 key).
Task 2: V-UX5-BACKFILL (bytes_reread equals the sum of the committed offsets, v4 counts and offsets unchanged, population EXACT afterwards, second run 0 bytes, every v5 row equals a cold build), V-UX5-BACKFILL-STOPS-AT-OFFSET, V-UX5-COLD-ALL (default 1 of 2, --all and --since-days 0 2 of 2), V-UX5-CLI-COST-KEYS (control: /proc/self/io unreadable -> rchar_delta null, maxrss still reported).

## Deviations from Plan

**1. [Plan wording] Task 1 gates were red first only through crashes**
- Gates were written before the implementation and run: the first run failed (`population()` had no `detail`, the CLI rejected `--host/--expect-file`), then went green in one pass once implemented. Each gate is shown able to fail by M15-M18 or by its paired control, not by a first-run red history.

**2. [Rule 2 - Missing critical] Refused answers carry no population number, empty selections refuse, expected records are validated**
- See key-decisions. Needed so UNMEASURED can never be read as a number and EXACT cannot be reached vacuously (pillar O rule 3).

**3. [Rule 2 - Missing critical] Pattern-set check against the live champion regex**
- The plan names meta pattern_set; the check also recomputes the champion's current set so a stale meta cannot hide a regex edit.

**4. [Plan wording] `backfill_v5(proj)`** is accepted but not used to select files (see key-decisions).

**5. Commit hook:** two- and three-file commits; no code-reviewer receipt was requested; no `--no-verify`; `vault/progress.md` (hook output) never committed. Git and test commands were split into plain separate calls because the sandbox refuses compound ones.

## Known limitations (documented, not stubs)

- A streamed call whose copies straddle the freeze instant U: `call_files.ts` is the LAST copy's effective ts, so the call counts only when its last copy is at or before U; the champion counts it with the maxima of the copies at or before U. Consecutive streamed copies are seconds apart; plan 05's corpus run against the frozen record measures whether it matters.
- `tool_events` is keyed (file, tool_use_id): a tool_use id repeated inside one file counts once; the champion counts each block. Same class of residual, same measurement (plan 05).
- `bytes_reread` counts bytes of lines processed (offsets are line-aligned, so it equals the sum of committed offsets); the kernel may read ahead one buffer past it (`proc.rchar_delta` shows the process-level truth).
- A resumed pass still cannot resolve relative tool paths before its first cwd line (from 01-03).
- Files with `v5_from > 0` or NULL stay UNMEASURED in population until `backfill-v5` runs; population names the verb in its reason.

## Threat Flags

None beyond the plan's register. T-01-15 (typed refusals each with an admitting control), T-01-16 (classifier loaded from the champion's files, parity gate + M16), T-01-17 (backfill writes v5 tables only, stops at the committed offset via end_offset, snapshot-checked per file, V-UX5-BACKFILL asserts v4 counts and offsets unchanged, M18), T-01-18 (deadline-bound, resumable, PARTIAL typed, opt-in verb) mitigated and gated.

## Blockers for the next plan

None. Handoff for plan 05 (corpus run, never in a hermetic gate): `python3 tools/usage_index.py population --select kme --host gex44 --until <freeze ISO> --expect KME-L --plane <label>` reads the frozen record by default; EXACT 0, DRIFTED 1 with per-field deltas, UNMEASURED 3 with reasons. A v4-migrated real index must `backfill-v5` first (reports bytes_reread; exit 0 only when status OK, else 2) or be cold-built with `refresh --all`; both print proc {rchar_delta, maxrss_kb}. `--detail` lists every session with class/share/selected/calls/cache_read; `reconcile` carries unique, shared_outside, first_writer, dup_files_in_scope, archived_excluded, archived_twins, skipped_shapes. `requirements mark-complete` applies nothing for these IDs (noted, not fought).

## Self-Check: PASSED

Files exist: tools/usage_index.py, tools/tis_observed.py, tools/test_usage_index_v5.py. Commits 2cf6e550 and dd69209e present on mission/autonomous-optimization-gen2; `commits: 2` measured from the persisted ledger (`rev-list --count 8ed112a4..HEAD` before this docs commit).
