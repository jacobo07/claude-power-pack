---
phase: 01-usage-index-v5-substrate
reviewed: 2026-10-06T00:00:00Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - tools/usage_index.py
  - tools/tis_observed.py
  - tools/ic_gen2.py
  - tools/test_usage_index_v5.py
  - tools/test_usage_index_identity.py
  - tools/test_store_identity_consumers.py
  - tools/test_spawn_outcomes.py
findings:
  critical: 1
  warning: 2
  info: 5
  total: 8
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-10-06
**Depth:** standard
**Files Reviewed:** 7
**Status:** issues_found

## Summary

Read in full: `tools/usage_index.py` (all 2123 lines), the `tis_observed.py` and `ic_gen2.py` diffs, and the diffs of the three small test files. `tools/test_usage_index_v5.py` (2451 new lines) was NOT read line by line. Its assertions were not audited, and a green run of it should not be treated as evidence that the findings below are covered.

The migration, per-file transaction gate, backfill and content-identity logic read as sound. The defects are concentrated at the `population` boundary, which the phase requires to return UNMEASURED instead of a neutral answer. One was reproduced at runtime on a small synthetic index: CR-01.

## Critical Issues

### CR-01: `population --until <bad value>` silently drops the instant and returns MEASURED / EXACT for the whole index

**File:** `tools/usage_index.py:2112` (the guard it bypasses is at `:1784-1789`)
**Issue:** `main()` passes `until=_epoch(a.until) if a.until else None`. `_epoch` returns `None` for any string shorter than 19 characters or that fails to parse. A date-only value such as `--until 2026-09-01` therefore arrives in `population()` as `until=None`, which means "every row counts". The function's own `until is not an ISO instant` refusal at 1784-1789 only fires for a `str`, so the CLI path never reaches it.
Reproduced on a synthetic index whose only session starts 2026-10-01. `population --until 2026-09-01` printed:
`MEASURED None [] {'sessions_active': 1, 'calls': 1, ...}`.
No session existed at that instant, yet the verdict is MEASURED with the full population and `until: null`. With `--expect` it can be EXACT, a false PASS. This is the "absent becomes a neutral answer" failure the verb exists to prevent.
**Fix:** pass the raw string through and let `population` refuse it:
```python
res = population(con, until=a.until or None, ...)   # population() converts and refuses a bad value
```
Also make `population` reject a non-str, non-number `until` that converts to `None`.

## Warnings

### WR-01: Any non-OSError failure while ingesting one file aborts the whole refresh pass and the poison file is retried forever

**File:** `tools/usage_index.py:1157-1162` and `:1243-1245`
**Issue:** The per-file `try` around `calls_from` catches only `OSError`. `calls_from` also runs `on_line` -> `_ancestry_line` / `_v5_line`, which bind transcript-derived strings into SQLite (tool name, normalized path, cwd, title). Any other exception from a single transcript escapes to the outer `except Exception`, which sets status `FAILED` and stops indexing every later file. Examples are a `sqlite3` binding error for a string holding a lone surrogate such as `"\ud83d"` in a `file_path` or `cwd`, or `RecursionError` from `json.loads` on deeply nested input. The file's transaction rolls back, its row never advances, and every later pass hits the same line and fails again. One malformed line then pins the index at FAILED / MONITOR_FAILURE and starves all files sorted after it. I did not execute the surrogate case; it follows from reading the code. The phase asks for typed parse/file errors, but only OSError is typed.
**Fix:** catch `Exception` around the per-file ingest, not just `OSError`. Roll back, call `_record_file_error(...)`, and continue. `population` already turns `files.error` into an UNMEASURED reason.

### WR-02: First cwd of a legacy file that grew is treated as the session's launch root

**File:** `tools/usage_index.py:1128-1146` (state seeded with an empty `cwds_seen`), `:737-738` (`file_cwds` insert), `:855-869` (`_registry`), `:922`
**Issue:** For a legacy (v4-migrated) file that grows, `v5_from = old offset > 0` and ingest starts mid-file. `_v5_line` records the first cwd seen in the new bytes with `first_off = start`. `_registry` takes `min(first_off)` per main file as the launch cwd and builds `registry` / `homes` from it. `_attribute` includes all files with `v5_from IS NOT NULL`, which covers `v5_from > 0`. If the cwd changed during the session, a mid-file cwd becomes the home root. That mislabels home vs touched projects, shifts the registry digest, and triggers full re-attribution of every file. `first_ts` correctly checks `first_ok` (`v5_from == 0`), but the cwd path has no equivalent guard. The stated contract is that a legacy file's v5 facts are unknown, not guessed.
**Fix:** in `_registry`, join only files with `v5_from = 0`. Make `_attribute` skip the home role for `v5_from > 0` files, or record the home only when `first_ok`.

## Info

### IN-01: `expected_final_failures` treats a falsy terminal as open, unlike CE's `is None` test

**File:** `tools/ic_gen2.py:358`
**Issue:** CE's L3 (`tools/test_cognitive_economy_program.py:213`) emits "no terminal disposition" only for `terminal is None`. `ic_gen2` uses truthiness, so `terminal: ""` or `0` is expected as open here while CE does not emit that line. The audit still fails loudly (one A3 "expected line absent" plus an unexpected CE line), so this is a diagnostic mismatch, not a false pass.
**Fix:** `if (st or {}).get("terminal") is not None`.

### IN-02: `--perturb` is silently ignored when `--expect` is absent

**File:** `tools/usage_index.py:2101-2111`
**Issue:** The perturbation loop runs only inside `if a.expect:`. `population --perturb calls=1` with no `--expect` returns MEASURED and gives no hint that the flag did nothing.
**Fix:** return exit 2 with a usage message when `a.perturb` is set and `a.expect` is not.

### IN-03: `expected` field validation accepts booleans

**File:** `tools/usage_index.py:1968`
**Issue:** `isinstance(expected.get(k), int)` is True for `True` / `False`, so `{"calls": true, ...}` passes as 1 / 0 instead of being refused.
**Fix:** also require `not isinstance(v, bool)`.

### IN-04: A session whose files all lack `first_ts` silently vanishes when `until` is set

**File:** `tools/usage_index.py:1840-1844`
**Issue:** `exists()` returns False when no file has a `first_ts`. Such sessions drop out of the population and the reconcile counts with no reason recorded. A file with zero timestamped lines is possible.
**Fix:** add a reason (UNMEASURED) or a `no_first_ts` count to `reconcile` when `until` is set and such sessions exist.

### IN-05: `_census_skipped` labels `_preserved` / `_empty_shells` under `_archived/<project>/` as "other"

**File:** `tools/usage_index.py:422-423`
**Issue:** `first` is the first path component below the walk root. For archived roots walked via the `_archived` dir it is the project name, so `by_shape` undercounts `_preserved` / `_empty_shells`.
**Fix:** classify by any path component, not only the first, or compute the shape relative to the child project dir.

Also noted, not filed (no defined failure): `refresh` skips a file whose `stat()` fails (`:1099-1101`) without recording a typed file error. `attribution()` (`:957-960`) groups an archived session by `store` and `session_key` only, not `project`.

---

_Reviewed: 2026-10-06_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
