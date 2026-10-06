---
phase: 01-usage-index-v5-substrate
fixed_at: 2026-10-06
review: 01-REVIEW.md
scope: critical + warning
findings_in_scope: 3
fixed: 3
skipped: 0
commit: 6674ccc0
status: all_fixed
---

# Phase 1: Review Fix Report

Applied inline by the epoch-2 worker, not by a gsd-code-fixer subagent (the epoch-1 fixer was
stopped by the mission-wall notice). Each fix has a gate that was run red before the fix and a
mutant in the drill that turns it red again.

| Finding | Fix | Gate (red before, green after) | Mutant |
|---|---|---|---|
| CR-01 `--until` dropped to None | `main()` passes the raw string; `population()` refuses any `until` that does not parse: UNMEASURED, exit 3, reason names the value | V-UX5-POP-UNTIL-REFUSED (before: exit 0, MEASURED, full population for `--until 2026-09-01`) | M19 |
| WR-01 non-OSError aborts the pass | the per-file ingest (calls_from through commit) is one `try`; any `Exception` rolls the file back, is typed in `files.error` and the pass goes on | V-UX5-FILE-ERROR-ANY (before: lone surrogate in one file -> pass FAILED, other file 0/2 calls) | M20 |
| WR-02 legacy mid-file cwd named the home | `_registry` joins only main files with `v5_from = 0`; a legacy file read from mid-file has no home | V-UX5-LEGACY-HOME-UNKNOWN (before: home = the mid-file cwd `.../elsewhere`) | M21 |

Side effect handled: V-UX5-CRASH-RESUME injected a plain `RuntimeError` to stand in for a
process crash; the widened handler now types that as a file error, which is the intended
behaviour for an error. The gate now models a crash as a `BaseException` that escapes refresh,
with the connection closed uncommitted and reopened. Its claim is unchanged: no row of the file in
flight survives, and the next refresh equals the one-shot build. M3's source anchor moved with
the re-indent and was made unique.

## Evidence (this host, gex44 plane)

- `python3 tools/test_usage_index_v5.py` -> `USAGE_INDEX_V5_PASS=74/74`
- `python3 tools/test_usage_index_v5.py --drill` -> control 74/74, `DRILL killed=21/21`, clean rerun 74/74
- `python3 tools/usage_index.py population --db /home/kobii/ao-scratch/p1/cold.sqlite --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --until 2026-10-03T16:13:37Z --select kme --host gex44 --expect KME-L --plane gex44` -> exit 0, EXACT, deltas empty, 102 sessions / 34,871 calls / 11,549,646,300 cache_read
- same index, `--until 2026-09-01` -> UNMEASURED, reason "until '2026-09-01' is not an ISO instant"
- siblings: test_usage_index 22/22, test_usage_index_identity 11/11, test_store_identity_consumers 12/12, test_spawn_outcomes 24/24, test_tis_observed 25/25, test_ao_p0 22/22

## Not fixed (info, out of scope)

IN-01 to IN-05 stay open as recorded in 01-REVIEW.md. None is a false pass. They go to Phase 2
planning as candidates.
