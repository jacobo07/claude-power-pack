---
phase: 05-critical-path-audit
plan: 02
subsystem: hook-critical-path
tags: [perf-05, hooks, guard, mutants, boundary-suite, deferral-candidates]
requires: [05-01]
provides:
  - tools/hook_critical_path_audit.py guard subcommand and guard_snapshots function
  - tools/test_hook_critical_path.py V-CRIT-GUARD-* gates (suite now 59/59)
  - phases/05-critical-path-audit/compare_runs.py (phase-local before/after judge)
  - phases/05-critical-path-audit/05-DEFERRAL-CANDIDATES.md (four candidates, none applied)
  - records/05-02-suite.txt, 05-02-guard-live.txt, 05-02-boundary-after.txt, 05-02-boundary-compare.txt, 05-02-reach-post.txt
affects: [05-03]
tech-stack:
  added: []
  patterns: [guard over a recorded baseline with planted in-memory mutants, preregistered before/after verdict rules, candidate ledger with falsifiers]
key-files:
  created:
    - .planning/workstreams/perf-construction/phases/05-critical-path-audit/compare_runs.py
    - .planning/workstreams/perf-construction/phases/05-critical-path-audit/05-DEFERRAL-CANDIDATES.md
    - .planning/workstreams/perf-construction/phases/05-critical-path-audit/records/05-02-suite.txt
    - .planning/workstreams/perf-construction/phases/05-critical-path-audit/records/05-02-guard-live.txt
    - .planning/workstreams/perf-construction/phases/05-critical-path-audit/records/05-02-boundary-after.txt
    - .planning/workstreams/perf-construction/phases/05-critical-path-audit/records/05-02-boundary-compare.txt
    - .planning/workstreams/perf-construction/phases/05-critical-path-audit/records/05-02-reach-post.txt
  modified:
    - tools/hook_critical_path_audit.py
    - tools/test_hook_critical_path.py
decisions:
  - Zero registration change held (D5-01): no file under hooks/ differs from the 05-01 baseline head, nothing was moved.
  - A comparison that is green on both sides but whose gate lines differ in text is NOT_SHOWN, not PASS (conservative reading of "every gate line matches").
  - The four DEFERRABLE rows are one pipeline and are listed all-or-none; a partial move breaks the learnings pipeline silently (dispatcher comment).
requirements: [PERF-05]
status: complete
commits: 3
plan_head_before: 744204daad9e1bf8956f19e26fefe6052248b7cb
actuals:
  tokens: 9800   # approximate: chars/4 over the added lines in tools/ (330 lines at about 65 chars) plus compare_runs.py and the ledger (17,553 chars); records excluded
  tasks: 3
  commits: 3
metrics:
  duration: not measured (start time not captured; records show the run spanning about 12:15 to 12:25 UTC on 2026-11-23)
  completed: 2026-11-23
---

# Phase 5 Plan 02: Guard, Boundary Before/After and Deferral Candidates Summary

PERF-05 criterion 2 now has an instrument that can fail: a guard that compares the dispatcher inventory to the recorded baseline, rejects each planted weakening by name, and reports zero violations and zero moved entries on the live repo. The boundary suite ran again after the guard under the same isolated HOME and its comparison with the before run is PASS. Four deferral candidates are written down and none is applied. Plane for every result: GEX44 (Linux, node v18, Python 3.12); the `~/.claude/settings.json` layer and every laptop timing are UNKNOWN and LAPTOP-ONLY.

## What was built

1. **`guard` subcommand and `guard_snapshots`** (`tools/hook_critical_path_audit.py`). Entries are keyed `container|script`. A baseline entry absent now is "moved". Violation codes are exactly `MOVED_NON_DEFERRABLE` (a non-DEFERRABLE entry left its container; UNKNOWN is not permission), `FLAG_WEAKENED` (block or critical true to false), `DROPPED_WORK` (a DEFERRABLE entry removed while `SessionEnd-chain` does not carry the script, including when that container is absent) and `DEADLINE_ON_BLOCKING_CHAIN` (a deadline added where the baseline had none, on a chain holding a BLOCKING-SAFETY entry). Added entries are reported, never violations. Classes of baseline entries come from `classify_inventory` with the real table, the same path the audit uses. Exit 0 only with zero violations; an unreadable or empty baseline exits 2 (no vacuous pass). With no `--current` it loads the live dispatcher.
2. **V-CRIT-GUARD gates** (`tools/test_hook_critical_path.py`, 18 new, suite `CRITPATH_PASS=59/59`). Mutants are in-memory deep copies of the recorded baseline; no repo file is edited. Each was rejected with its named code on the first run:
   - M1 remove a block entry, a critical entry, and a whole container (13 of 13 entries named): `MOVED_NON_DEFERRABLE`.
   - M2 block true to false and critical true to false: `FLAG_WEAKENED`. Reverse pole: false to true is allowed.
   - M3 remove an UNKNOWN entry: `MOVED_NON_DEFERRABLE`.
   - M4 add a deadline to `PreToolUse-Bash-chain`: `DEADLINE_ON_BLOCKING_CHAIN`. Controls: a deadline on `SessionEnd-chain` (no BLOCKING-SAFETY entry) and on a synthetic chain pass.
   - M5 remove `Stop-chain|./trace-flusher.js` and its SessionEnd twin: `DROPPED_WORK` (also with the whole `SessionEnd-chain` container absent).
   - Controls: identical snapshots exit 0 with moved 0; the same DEFERRABLE entry removed while its SessionEnd twin stays exits 0 with moved 1, violations 0.
   - The real table does have DEFERRABLE entries, so M5 and control 2 ran on a real entry. The labelled SYNTHETIC stand-in is exercised every run anyway (`V-CRIT-GUARD-SYNTHETIC-LABEL`), so it cannot be a dead branch.
3. **`compare_runs.py`** (phase-local, stdlib only, registered nowhere). Reads the line format the before record actually uses (`  [PASS] GATE-ID: detail`, a `HOOK_PASS=n/N  threshold=n/N` footer, a `# exit=N` footer), prints one line per gate and one `VERDICT:` line under the rules fixed before the runs (G4). It names no gate. Scratch-only proof that it can say all three verdicts (not committed, in `/tmp/p5-cmp`): a gate flipped to FAIL in the after copy gives FAIL, a red before copy gives NOT_SHOWN, and a text-drifted after copy gives NOT_SHOWN; the real pair gives PASS.
4. **`05-DEFERRAL-CANDIDATES.md`**: one section per DEFERRABLE row (trace-flusher, ads_sync, session_writeback, session_delta_stop), each with outputs, durability change, the Owner wiring precondition, falsifiers F-1 to F-3, status `CANDIDATE - NOT APPLIED` and the reversal, plus a "Not candidates" section naming the held UNKNOWN entries and the 14 whose source is not in this checkout.

## Results

| Check | Result | Record |
|---|---|---|
| Suite | `CRITPATH_PASS=59/59`, exit 0 | `records/05-02-suite.txt` |
| Live guard vs `05-01-inventory-baseline.json` | 113 baseline entries, moved 0, added 0, violations 0 | `records/05-02-guard-live.txt` |
| `git diff --stat 69e27e19 -- hooks/` and `git diff --quiet HEAD -- hooks/` | both empty, both rc 0 | this summary |
| Boundary suite after-run (isolated HOME `/tmp/p5-home`, same wrapper as the before run, no retry, no suite edit) | `HOOK_PASS=7/7`, exit 0 | `records/05-02-boundary-after.txt` |
| Boundary comparison | 7 gates SAME (PASS/PASS), footers equal, `VERDICT: PASS` | `records/05-02-boundary-compare.txt` |
| Reachability | pre 56 offenders, post 56, new 0, gone 0 (compared by unit name); no registry edit | `records/05-02-reach-post.txt` |

The PASS verdict has limits that the record states in its own text. Both runs ran under the scratch HOME, so one sub-check inside `V-HOOK-TRIGGER-REGISTERED` (the duplicate-invocation check against live `settings.json`) reports UNEVALUATED in both. The gate still passes on its other half (registered on the dispatcher surface). The run with the real HOME is LP-12, LAPTOP-ONLY / UNJUDGED. "Unchanged" holds because `hooks/` is byte-identical to the base, not because of this run alone.

The guard cannot see laptop wiring, and it does not check that the four DEFERRABLE entries move together. The dispatcher comment says a partial move breaks the learnings pipeline silently; the ledger states the candidates as all-or-none and names that as a group falsifier.

## Deviations from Plan

**1. [Rule 3 - Blocking] Isolated HOME through the scratch wrapper.** As in 05-01, the harness refuses `HOME=` on a command line, so the after-run used `/tmp/p5-scripts/run_boundary.py` (sets `HOME` and `USERPROFILE` to `/tmp/p5-home` via `env=` and runs the unmodified `tools/test_hook_boundary.py`), recorded through `record_run.py`. This is the same command as the before record, which is what makes the two comparable. No repo file changed.

**2. [Rule 2 - Scope] Extra controls beyond the seven listed behaviors.** Added the strengthening pole of M2, the no-blocking-entry deadline control (real and synthetic), the whole-container M1 and absent-`SessionEnd-chain` M5 variants, and refusal of an empty or missing baseline, because a guard whose pass path and refusal path are not both driven proves little. Commit f7ce4a98.

**3. [Interpretation] Text drift is NOT_SHOWN.** G4 says PASS needs "every gate line matches" but names no verdict for green-on-both-sides with differing text; I made that NOT_SHOWN (never PASS, never FAIL). It did not occur in the real pair.

## Findings

- `PreToolUse-Bash-chain` and the other blocking PreToolUse chains carry no deadline in the baseline, while `SessionStart-chain` (4000 ms) already holds a critical entry and a deadline. The guard only forbids ADDING a deadline; it does not flag that existing state, and does not flag a tightened deadline. That is a stated limit, not a defect found in the registry.
- M5 removes the SessionEnd twin too, so the mutant also trips `MOVED_NON_DEFERRABLE` on the twin (UNKNOWN). The gate asserts `DROPPED_WORK` is named for the Stop-chain key.

## Known Stubs

None.

## Threat Flags

None. No new network endpoint, auth path or trust boundary; the guard reads two JSON snapshots and, without `--current`, executes the repo's own dispatcher under the empty scratch HOME.

## Verification

- `python3 -I tools/test_hook_critical_path.py`: `CRITPATH_PASS=59/59  threshold=59/59`, exit 0.
- Live guard piped through the plan's assertion: `GUARD_LIVE_OK`.
- `compare_runs.py` through the plan's assertion: `COMPARE_VERDICT PASS` (exactly one `VERDICT:` line).
- Ledger assertion: `LEDGER_OK 4`.
- Privacy (D5-10): `grep -v '^#' FILE | grep -c /home/` is 0 for all five new records and the ledger.

## Self-Check: PASSED

- Files exist: tools/hook_critical_path_audit.py, tools/test_hook_critical_path.py, compare_runs.py, 05-DEFERRAL-CANDIDATES.md, and the five `05-02-*` records.
- Commits exist on branch worktree-agent-a1581518b9bd85c48: f7ce4a98 (guard and mutants), 7451bd0f (boundary after-run and comparison), 37129b7a (ledger and reachability).
- `git rev-list --count 744204da..HEAD` before the docs commit: 3.
