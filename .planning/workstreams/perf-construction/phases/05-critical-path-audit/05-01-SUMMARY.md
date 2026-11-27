---
phase: 05-critical-path-audit
plan: 01
subsystem: hook-critical-path
tags: [perf-05, hooks, dispatcher, inventory, classification, baselines]
requires: [04-03]
provides:
  - tools/hook_critical_path_audit.py (inventory + classify CLI)
  - vault/config/hook-critical-path-classes.json (DECLARED class table)
  - tools/test_hook_critical_path.py (CRITPATH suite, 41 gates)
  - records/05-01-inventory-baseline.json, 05-01-boundary-before.txt, 05-01-reach-pre.txt, 05-01-reach-post.txt
affects: [05-02, 05-03]
tech-stack:
  added: []
  patterns: [structural loader of the dispatcher registry under an empty HOME, mechanical safety floor then annotation table, coverage by construction]
key-files:
  created:
    - tools/hook_critical_path_audit.py
    - tools/test_hook_critical_path.py
    - vault/config/hook-critical-path-classes.json
    - .planning/workstreams/perf-construction/phases/05-critical-path-audit/records/05-01-tracer.txt
    - .planning/workstreams/perf-construction/phases/05-critical-path-audit/records/05-01-suite.txt
    - .planning/workstreams/perf-construction/phases/05-critical-path-audit/records/05-01-inventory-baseline.json
    - .planning/workstreams/perf-construction/phases/05-critical-path-audit/records/05-01-boundary-before.txt
    - .planning/workstreams/perf-construction/phases/05-critical-path-audit/records/05-01-reach-pre.txt
    - .planning/workstreams/perf-construction/phases/05-critical-path-audit/records/05-01-reach-post.txt
  modified: []
decisions:
  - Zero registration change (D5-01): the audit classes entries and moves nothing; hooks/ is byte-identical to the base.
  - ceps_promote_stop stays UNKNOWN because hooks/graph_first_gate.js reads its output mid-session.
  - learning-sentinel is held UNKNOWN: its source emits model context on one path and the Stop branch was not separated.
requirements: [PERF-05]
status: complete
commits: 3
plan_head_before: dc2ef58b803295b2cbec571aeb579bf13454fe71
actuals:
  tokens: 14400   # chars/4 over tools/ and vault/ files created (57,522 chars); records excluded
  tasks: 3
  commits: 3
metrics:
  duration: not measured (session resumed after context compaction; start time lost)
  completed: 2026-11-23
---

# Phase 5 Plan 01: Hook Critical-Path Inventory and Classification Summary

The synchronous per-event hook work is now inventoried from the dispatcher registry itself (113 entries, 20 containers), every entry carries a class and a basis code under a mechanical safety floor, and the baselines 05-02 compares against are on record. Plane for every number: GEX44 (Linux, node v18, Python 3.12). The `~/.claude/settings.json` layer is UNKNOWN and LAPTOP-ONLY (LP-09); it is not read.

## What was built

1. **`tools/hook_critical_path_audit.py`**: a node child loads `hooks/hook-dispatcher.js` under an empty scratch HOME (`/tmp/p5-home`, 30 s timeout), appends an export of `EVENT_MAP`/`CHAIN_MAP`/deadline constants to the source in memory only, and prints a sentinel JSON line. Any load failure exits 2; there is no regex fallback. Each entry is resolved (`repo` / `live-only` / `fixture`, with a containment check), its source is scanned for deny shapes and model-context emission (whole-line comments skipped for the context scan), and a mechanical class is assigned. `classify` joins the class table: flags, deny shape, unresolved, row, no row. Exit 1 on any table violation.
2. **`vault/config/hook-critical-path-classes.json`**: 25 rows (status DECLARED; 20 Stop-chain, 5 SessionEnd-chain) plus 4 container notes. The table only annotates discovered entries; a key present in no container is `STALE_ROW` and fails the audit. A DEFERRABLE row is accepted only through guards (resolvable source, no flags, no deny shape, no model-context emission in code lines, file:line evidence on the entry's own source and a real line, named outputs, durability note, and SessionEnd twin for `DEF_ACCOUNTING_DUP`).
3. **`tools/test_hook_critical_path.py`**: `CRITPATH_PASS=41/41  threshold=41/41`. Every detector is driven from both poles with hermetic temp files: load cross-check against the dispatcher's own exported `CHAIN_MAP`, decoy dispatchers (no EVENT_MAP, throws, empty) exit 2 with a valid control exit 0, deny-pattern positives and a clean control, flag and deny floors against a DEFERRABLE row, one mutant per DEFERRABLE guard plus acceptance of a fully guarded row, coverage, stale row and stale container note, and isolation (read-only HOME gives the same 113 entries and leaves nothing behind).

## Measured results

| Quantity | Measured | Planner prototype |
|---|---|---|
| Entries | 113 | 113 |
| Containers | 20 (11 chains, 9 event defaults) | 20 |
| Unresolved entries (source not in this checkout) | 18 (fixture or live-only) | 18 |
| Stop-chain entries | 27 | 27 |
| Deny-shape entries, chain containers | 29 (26 distinct scripts) | 27 |
| Deny-shape entries, all containers | 44 (33 distinct scripts) | not given |
| block/critical flagged entries | 21 | not given |

The one difference from the prototype is the deny-shape count in chains: 29 versus 27. This tool counts entries (a script registered in two chains counts twice) and applies the four patterns named in the plan, including `process.exit(2)`/`sys.exit(2)`/`SystemExit(2)`/`os._exit(2)`/`exitCode=2`; the planner's method for 27 is not recorded, so the two-entry gap is reported as measured fact and not reconciled. It cannot make anything less safe: deny-shape entries only ever raise an entry to BLOCKING-SAFETY.

Classification result (`classify` exits 0, 0 violations):

| Class | Entries |
|---|---|
| BLOCKING-SAFETY | 58 (50 from the mechanical floor: flag or deny shape; 8 from table rows, all because the entry injects context or a message) |
| DEFERRABLE | 4 (`DEF_ACCOUNTING_DUP`: trace-flusher, ads_sync, session_writeback, session_delta_stop, all Stop-chain entries that SessionEnd-chain also lists) |
| UNKNOWN | 51, every one named in the `RESIDUAL UNKNOWN` list the tool prints |

UNKNOWN is not PASS. Of the 51: 14 are unresolved with no flag or deny shape (`UNRESOLVED_LIVE_ONLY`; source absent from the checkout, the other 4 of the 18 unresolved entries are held BLOCKING by their block/critical flag), 13 carry a table row saying UNKNOWN with a named missing fact (`TABLE_UNKNOWN`: 8 Stop-chain entries plus the 5 SessionEnd-chain twins, an inert container whose wiring is LAPTOP-ONLY, LP-09), and 24 have no table row (`NO_TABLE_ROW`) because their evidence was not read in this plan (D5-05: stop when the evidence runs out).

## Baselines recorded

- `records/05-01-inventory-baseline.json`: 113 entries, 20 containers, `hooks_clean: true`, dispatcher sha256 prefix `465234ea08c5`, recorded at commit 69e27e19.
- `records/05-01-boundary-before.txt`: `tools/test_hook_boundary.py` run under the scratch HOME with `hooks/` pristine, `HOOK_PASS=7/7  threshold=7/7`, exit 0. No gate failed. One sub-check inside `V-HOOK-TRIGGER-REGISTERED` reports the duplicate-invocation check UNEVALUATED because `/tmp/p5-home/.claude/settings.json` does not exist: that is the isolated-HOME result, labelled LAPTOP-ONLY (LP-12) and not substituted with another run.
- Reachability: pre-state 56 offenders (`05-01-reach-pre.txt`), post-state 56 (`05-01-reach-post.txt`), the offender set unchanged by name (0 new, 0 gone). No liveness registry row was needed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Evidence validity for non-DEFERRABLE rows**
- **Found during:** Task 2 classify run.
- **Issue:** the plan's guards checked evidence only for DEFERRABLE rows, so a BLOCKING-SAFETY or UNKNOWN row could cite a nonexistent line unnoticed.
- **Fix:** `evidence_problems(..., require_own=False)` is applied to every other row; failures are `ROW_EVIDENCE` violations. Non-DEFERRABLE rows may cite a file other than the entry's own source (for example the dispatcher line or a consumer such as `graph_first_gate.js`).
- **Files modified:** tools/hook_critical_path_audit.py. **Commit:** 69e27e19.

**2. [Rule 3 - Blocking] Isolated HOME cannot be set on the command line here**
- **Issue:** the execution harness refuses commands that set `HOME=`, so the plan's `env HOME=/tmp/p5-home python3 ...` form for the boundary suite could not run as written.
- **Fix:** a scratch wrapper outside the repo (`/tmp/p5-scripts/run_boundary.py`) sets `HOME`/`USERPROFILE` to `/tmp/p5-home` through subprocess `env=` and runs the unmodified suite; RR recorded the wrapper command. The suite and `hooks/` were not edited.
- **Files modified:** none in the repo. **Commit:** f18ff762.

**3. [Rule 2 - Scope] Comment-aware model-context scan**
- **Issue:** a whole-file context scan flagged `ads_sync.py` for a comment that says it never emits `additionalContext`, which would have blocked a genuine accounting duplicate for a non-reason.
- **Fix:** whole-line comments (`#`, `//`, `*`, `/*`) are skipped for the context scan only; the deny scan is unchanged, so the floor is not weakened. Both poles pinned in `V-CRIT-SCAN-POLES-CONTEXT`.

### Findings that shaped classes

- `ceps_promote_stop.py` looks write-only, but `hooks/graph_first_gate.js:166-169` reads `promoted.jsonl` per tool call, so it is not DEFERRABLE.
- `learning-sentinel.js` is a SessionEnd duplicate but its source emits `additionalContext` and spawns a detached claude child, so it fails the NO_MODEL_CONTEXT guard and is held UNKNOWN.
- The four DEFERRABLE entries are classes, not moves: the SessionEnd-chain is inert until the Owner wires it in settings.json (HR-001), and moving them trades per-turn durability for per-session; an abnormal exit never reaches SessionEnd. Each row's `durability_note` states that.

## Known Stubs

None. The `.pp-capabilities` file in the worktree root is untracked tooling output and was not added.

## Threat Flags

None. The audit executes only the repo's own dispatcher, under an empty scratch HOME with a 30 s timeout, and writes nothing into `hooks/`.

## Pre-existing failure observed (out of scope)

`tools/test_git_invocation.py` exits 6/7 on this base with 14 unfrozen offenders (for example `tools/ccn_bench.py`, `tools/test_kme_pillars.py`); none is a file this plan created or modified, and the Phase 4 final record already shows the same 6/7 list. This plan's `_git_exe()` uses `modules.execution_env.git_exe` with a `shutil.which` fallback and adds no offender.

## Verification

- `python3 -I tools/test_hook_critical_path.py`: `CRITPATH_PASS=41/41  threshold=41/41`, exit 0 (`records/05-01-suite.txt`).
- `python3 -I tools/hook_critical_path_audit.py classify`: exit 0, 0 violations, 113 entries.
- `git diff --quiet HEAD -- hooks/`: clean.
- Privacy (T-05-03): `grep -v '^#' FILE | grep -c /home/` is 0 for all six committed records.

## Self-Check: PASSED

- Files exist: tools/hook_critical_path_audit.py, tools/test_hook_critical_path.py, vault/config/hook-critical-path-classes.json, and the six records under `records/`.
- Commits exist on branch worktree-agent-acdcada083373b371: a522485e (tracer), 69e27e19 (classify table and suite), f18ff762 (baselines).
- `git rev-list --count dc2ef58b..HEAD` before the docs commit: 3.
