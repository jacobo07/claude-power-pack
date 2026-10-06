---
phase: 01-usage-index-v5-substrate
plan: 02
subsystem: usage_index
tags: [usage-index, schema-v5, path-identity, archived-rule, parse-errors, content-identity, concurrency, mutation-drill]
requires: [01-01]
provides:
  - "_iter_files_v5: (path, is_sub, store, project, archived, session_key) from tis_observed.store_identity, _archived opened one level down through the same producer"
  - "tis_observed.resolved_path (file identity) and calls_from stats head_sha/tail_sha"
  - "ARCHIVED_RULE (meta archived_rule): archived transcripts go to v5 tables only; v4 readers keep their answers"
  - "meta skipped_shapes census (count, bytes, by_shape, samples, walk_errors; count 0 recorded)"
  - "files.parse_errors / files.error surfaced; refresh keys parse_errors, files_with_errors, skipped_shapes, skipped_concurrent"
  - "content_id + dup_of groups (equal content_id AND equal call-key sets, order-independent)"
  - "per-file BEGIN IMMEDIATE with snapshot check (_snapshot, _begin_file); refresh(snapshot=...)"
affects: [01-03, 01-04, 01-05, 01-06]
tech-stack:
  added: []
  patterns: ["per-file write transaction with a compare-with-snapshot admission check", "source-text and in-process mutants driven from the gate file", "open() spy for no-read claims"]
key-files:
  created: []
  modified:
    - tools/usage_index.py
    - tools/tis_observed.py
    - tools/test_usage_index_v5.py
key-decisions:
  - "A failed refresh now rolls back the file in flight: before this plan the final meta commit of a FAILED pass committed that file's partial rows (found by V-UX5-CRASH-RESUME going red first)"
  - "A file that cannot be read gets files.error with size=-1 (retried every pass) and, when never read, v5_from NULL so population reports it UNMEASURED, never zero"
  - "dup_of needs equal content_id AND equal call-key sets (id-less keys compared with the path blanked); content_id alone never merges"
  - "population lets a live twin win over its archived twin when include_archived is set (the declared rule); no corpus file has such a twin today"
  - "CREATE INDEX IF NOT EXISTS files_content runs in every refresh (not inside the version-gated migration) so an index already stamped v5 gets it too"
status: complete
plan_head_before: 587016adc0e3316ff3e2ac6fc75c819329194d04
commits: 3
actuals:
  tokens: 13200
  tasks: 3
  commits: 3
duration: single session
completed: 2026-10-06
---

# Phase 1 Plan 02: usage_index v5 file identity and concurrency Summary

Every `files` row now knows its resolved path, store, project, archived flag and session; `_archived` history is indexed by a declared rule without moving any v4 number; odd shapes, bad lines and unreadable files are counted or typed rather than absent; copies are recognised without merging distinct histories; and an interrupted or parallel refresh converges to the rows of one clean build, each with a gate and a killing mutant.

## Tasks

| Task | Name | Commit |
|---|---|---|
| 1 | Path identity, declared `_archived` rule, skipped-shape census | ef8ecee0 |
| 2 | Parser/file failures surfaced; content identity and duplicate groups | 446ee000 |
| 3 | Interrupted and parallel refresh guarantees (AOP-O edge probe) | 3f420085 |

## Gate outputs

- `python3 tools/test_usage_index_v5.py` -> `USAGE_INDEX_V5_PASS=34/34  threshold=34/34`
- `python3 tools/test_usage_index_v5.py --drill` -> control 34/34, M1-M9 all KILLED, clean rerun 34/34, `DRILL killed=9/9`
- `python3 tools/test_usage_index.py` -> `USAGE_INDEX_PASS=22/22  threshold=22/22`
- `python3 tools/test_usage_index_identity.py` -> `USAGE_INDEX_IDENTITY_PASS=11/11  threshold=11/11`
- `python3 tools/test_store_identity_consumers.py` -> `STORE_IDENTITY_CONSUMERS_PASS=12/12  threshold=12/12`, `PASS V-SIC-UX-ONE-PRODUCER`
- `python3 tools/test_spawn_outcomes.py` -> `SPAWN_OUTCOMES_PASS=24/24  threshold=24/24`
- Consumer set unchanged against 01-BASELINE.md: fanout 17/17, root_progress 11/11, spawn_policy_v2 26/26, async 12/12, goal_journey 7/7, execution_shape 14/14, displacement 16/16; estate_shadow 10/11 is the pre-existing V-SHADOW-NESTED-PROJECT red.

Red-first: each task's gate groups were run before the implementation (Task 1: 14/19, Task 2: 21/30, Task 3: 31/33 with V-UX5-CRASH-RESUME showing partial rows of the crashed file committed).

## Mutants registered

| Mutant | Kills |
|---|---|
| M5 store identity bypassed (in-process patch of `store_identity`) | V-UX5-ALIAS-ONCE |
| M6 archived guard around the calls upsert inverted (source text) | V-UX5-V4-READERS-UNCHANGED, V-UX5-ARCHIVED-INDEXED |
| M7 bad-line counter removed from `tis_observed` (source text via `UX._tis`) | V-UX5-PARSE-ERROR-SURFACED |
| M8 content id from head hash only (in-process patch of `_content_id`) | V-UX5-HISTORIES-NOT-MERGED |
| M9 `_begin_file` always admits (in-process patch) | V-UX5-STALE-SNAPSHOT-SKIPS |

## Deviations from Plan

**1. [Rule 1 - Bug] A FAILED refresh committed the partial rows of the file in flight**
- Found during: Task 3 (V-UX5-CRASH-RESUME red-first run): after an injected exception, tool_events and prompts rows of the crashed file were committed by the pass's final meta `con.commit()`.
- Fix: `con.rollback()` in refresh's typed-failure branch, plus the per-file `BEGIN IMMEDIATE`. Commit 3f420085.

**2. [Rule 3 - Blocking] `files_content` index broke the v4 downgrade helper**
- `ALTER TABLE ... DROP COLUMN content_id` refuses while an index uses the column. `downgrade_to_v4` in the gate file now drops the index first. Commit 446ee000.

**3. [Rule 2 - Missing critical] index on files.content_id**
- `_dup_groups` selects by content_id on every ingest; without an index that is a full scan per file. Added `files_content`.

**4. [Plan wording] extra gates beyond the plan's list**
- V-UX5-ARCHIVED-TWIN-LIVE-WINS (the declared twin clause of ARCHIVED_RULE needed an enforcement and a control), V-UX5-PARSE-ERROR-STABLE (an unchanged re-refresh does not re-count), V-UX5-FILE-ERROR-CLEARS (error clears once the file is readable). V-UX5-FILE-ERROR-TYPED uses mode 000 as non-root and falls back to an injected PermissionError when open() succeeds under mode 000 (root), instead of skipping.

**5. [Plan wording] `_fill_path_identity(con)`** takes no `proj`: the identity derives from the path string alone, so the argument would be unused.

**6. Commit hook:** no code-reviewer receipt was requested for the three-file commits; no `--no-verify` used. `vault/progress.md` (hook output) was never committed.

## grep record (plan Task 1)

`_iter_files` has no caller outside tools/usage_index.py: `grep -rn "_iter_files" --include=*.py` shows the other definitions (modules/sweep_enforcer, rule_compiler, drift_registry, tools/graphify_knowledge.py) are unrelated functions of their own modules. It is kept as a wrapper yielding live `(path, is_sub)`.

## Known notes / not stubs

- `requirements mark-complete AO-03`: reported not-found in 01-01; the plan frontmatter lists AOP-O and AO-03. See the state-update note below; not fought.
- `tool_events.pat_hits`, `user_hits`, `file_cwds`, `file_attribution`, `patterns` remain empty (plan 03 scope). `files.first_ts/last_ts/pat_ver` are not filled by this plan.
- Legacy rows migrated from v4 get identity columns without a read, but `head_sha/tail_sha/content_id` stay NULL until the file next grows (they need bytes); such files are not duplicate-grouped. This is typed unknown, not a stub.
- The census walks `os.walk` over every store on each refresh (listing only, T-01-10 accepted); its cost belongs to plan 05's no-op refresh wall measurement.
- `tools/test_token_ground_truth_junction.py` still crashes on Linux (cmd mklink), out of scope.

## Threat Flags

None beyond the plan's register. T-01-06 (alias/outside link: V-UX5-ALIAS-OUTSIDE, M5), T-01-07 (archived pollution: V-UX5-V4-READERS-UNCHANGED with a difference-seeing control, M6), T-01-08 (hidden parse failures: M7), T-01-09 (double ingestion: V-UX5-STALE-SNAPSHOT-SKIPS, M9) mitigated and gated.

## Blockers for the next plan

None. Handoff: `files.dup_of` / `content_id` exist for plan 04's population `dup` handling; `population()` already honours `archived` and the live-twin rule. New path columns must go through `_PATH_COLUMNS` / `_path_columns(con)` (`files.resolved` was added). `refresh()` now accepts `snapshot=` and returns `skipped_concurrent`, `parse_errors`, `files_with_errors`, `skipped_shapes`.

## Self-Check: PASSED

Files exist: tools/usage_index.py, tools/tis_observed.py, tools/test_usage_index_v5.py. Commits ef8ecee0, 446ee000, 3f420085 present on mission/autonomous-optimization-gen2; `commits: 3` measured from the persisted ledger (`rev-list --count 587016ad..HEAD`).
