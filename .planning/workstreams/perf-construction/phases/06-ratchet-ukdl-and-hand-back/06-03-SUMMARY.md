---
phase: 06-ratchet-ukdl-and-hand-back
plan: 03
subsystem: hand-back
tags: [perf-construction, handoff, generated-counts, laptop-checklist, PERF-06]
requires:
  - phase: 06-01
    provides: inheritance map, manifest command, mutant matrix
  - phase: 06-02
    provides: ratchet status CONNECTED_SCRATCH LIVE=BLOCKED, UKDL candidate file
provides:
  - handoff_check.py (inventory, check, tree, selftest 13/13 with a mutant control)
  - HANDOFF.md (five sections, first line "Creation speed on the laptop: UNKNOWN", 12-row LAPTOP-ONLY / UNJUDGED checklist, next task LP-05)
  - 06-EVIDENCE.md (D6-01..D6-10 map, three success criteria, meta-analysis, carried debt)
  - final gate record and tree record
affects: []
tech-stack:
  added: []
  patterns: [counts derived and recomputed at check time, NEW: record paths that must not exist, closed forbidden-claim list]
key-files:
  created:
    - .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/handoff_check.py
    - .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/HANDOFF.md
    - .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/06-EVIDENCE.md
    - .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/records/06-03-T1.selftest.txt
    - .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/records/06-03-T1.tracer.txt
    - .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/records/06-03-T2.check.txt
    - .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/records/06-03-T3.final-gates.txt
    - .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/records/06-03-T3.tree.txt
    - .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/records/06-03-T3.selftest.txt
    - .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/records/06-03-T3.check.txt
  modified:
    - .planning/workstreams/perf-construction/STATE.md
key-decisions:
  - "Changed-file count is taken at the head the HANDOFF states, so the commit that adds the hand-back cannot move its own count"
  - "OWNER DECISION NEEDED (11) to (13) already existed once each in STATE.md (from 06-01 and 06-02); the Phase 6 block refers to them and adds no second copy"
requirements-completed: [PERF-06]
status: complete
duration: ~45 min
completed: 2026-11-23
commits: 3
plan_head_before: 0c5a1436ff77e5ded816ba6b56e7c0e1673150d9
actuals:
  tokens: 31000
  tasks: 3
  commits: 3
---

# Phase 6 Plan 03: Hand-back Summary

HANDOFF.md hands the campaign back on one checked page whose first line is `Creation speed on the laptop: UNKNOWN`: every count is recomputed by `handoff_check.py` from the phase files, and the 12 laptop items are listed LAPTOP-ONLY / UNJUDGED with the next task fixed to LP-05.

## Results

- **Checker** (`handoff_check.py`, `HANDOFF_SELFTEST=13/13`, `records/06-03-T3.selftest.txt`): inventory from the real files (unknowns per phase 4,6,6,8,7; 12 LP ids; 13 Owner decision ids; changed files at the stated head), refusals for a missing or reordered section, a wrong first line, each changed INVENTORY field and prose count, a removed or invented LP row, a number in a laptop slot, a bad pointer, each of 20 forbidden claims, a missing path, an absolute home or Windows path, an existing `NEW:` record, and a wrong next task. Mutant control: with the number comparison disabled in memory the same wrong INVENTORY lines are accepted. Absent is not zero: an empty phases directory yields None per phase with named problems.
- **Tracer** (`records/06-03-T1.tracer.txt`): minimal document passed `check` end to end before the full text replaced it.
- **HANDOFF.md** (`records/06-03-T3.check.txt`, `HANDOFF_CHECK=PASS`, also still passing at the final HEAD): five sections in order; owner summary lists all 13 Owner decisions with the pick taken; engineering handoff names the five owners, markers and the manifest re-run command; checklist rows for LP-01 to LP-12 each point at a path and line that mention the id; next task LP-05 with LP-07, LP-08 and LP-10 as companions.
- **Final gates** (`records/06-03-T3.final-gates.txt`, one run, no retry, exit 0): 15 rows, 14 judged, 12 PASS, 2 BASELINE_MATCH (git invocation 6/7, 56 reachability offenders equal by name: pre-existing debt, not passes), s9 red-team SKIPPED_BY_POLICY (UNJUDGED), 0 FAIL, 0 NOT_RUN. The manifest footer line `INHERIT_PASS=14/14` counts the two BASELINE_MATCH rows; HANDOFF and STATE state 12 PASS plus 2 BASELINE_MATCH.
- **Tree** (`records/06-03-T3.tree.txt`, `HANDOFF_TREE=PASS`): tools, modules, hooks, vault/config unchanged; only paths inside the phase directory or STATE.md dirty; ledger and floors sha256 SAME as before the manifest.
- **STATE.md**: one appended Phase 6 block, 9 added lines, 0 deleted; position fields, ROADMAP.md, REQUIREMENTS.md and ROOT milestone untouched.
- **Metrology unit** (asked for by the plan): registry row stays DORMANT; Phase 5 consumes it by import (`tools/hook_critical_path_audit.py:58`, `CENSORED_STATES`, `STATES`), and the Phase 5 final reachability record still lists it as ORPHAN / DORMANT.

## Task commits

1. Task 1 (tracer): 7f768010
2. Task 2 (HANDOFF.md, 06-EVIDENCE.md): 823d4615
3. Task 3 (final gates, tree, STATE.md block, regenerated INVENTORY): 4434b359

## Deviations from Plan

**1. [Rule 3 - Blocking] OWNER DECISION NEEDED (11) to (13) were already in STATE.md.** The 06-01 and 06-02 executors had each added their decision lines, so appending them again would make the plan's own verify (`grep -c` equals 3) read 6 and break the "exists once each" rule. The Phase 6 block refers to them in words without the literal pattern; the grep returns 3. Reversible, STATE.md additions only.

**2. [Rule 2 - Missing] Changed-file count is computed at the head the document states, not at the HEAD of check time.** Counting at check-time HEAD would make every later commit, including the one that adds HANDOFF.md, turn the check red. The checker verifies the stated head resolves and recomputes the count at it; the document says "counted at the head stated". Stable across the three commits (verified at the final HEAD).

**3. [Rule 2 - Missing] `NEW:` convention and `tree` subcommand.** Laptop record files do not exist yet, so a plain backticked path would fail the existence check. Record cells use `NEW:<path>`: the parent directory must exist and the file must not (a laptop record appearing means the hand-back must be revised, F1). The three tree checks live in a `tree` subcommand with an allowlist classifier and its own selftest gate (13th gate); its selftest record is `06-03-T3.selftest.txt`, the T1 record (12/12) is kept as taken.

**4. [Rule 1 - Bug] Plan verify grep with a backreference** needs `/usr/bin/grep -E` (ugrep rejects it), as in 06-02. Run that way it matches `HANDOFF_SELFTEST=13/13`.

**5. A wrong expansion of TTFMC in my first draft of 06-EVIDENCE.md** ("time to first model content") was corrected against `vault/specs/construction-metrology-contract.md` (time to first material change, proposed) before the Task 2 commit.

The plan lists no per-commit ledger file path in a worktree git dir (writing to the shared git dir was refused); `plan_head_before` was taken from `git rev-parse HEAD` at start and `commits: 3` measured with `git rev-list --count` from it.

TDD note: Task 1's RED shape is the in-file mutant control and the per-refusal gates; no separate red record was committed (same as 06-01 and 06-02).

## Known Stubs

None.

## Threat Flags

None. No network endpoint, auth path or schema; no absolute home or Windows user path in HANDOFF.md, 06-EVIDENCE.md or the records (grep clean).

## Issues / Gaps for the orchestrator

- Position fields, ROADMAP.md, REQUIREMENTS.md and the ROOT milestone are yours to advance (Phase 6 executed 3/3, awaiting verification).
- If STATE.md gains another `OWNER DECISION NEEDED (n)` or a phase VERIFICATION file changes, `handoff_check.py check` fails by design: regenerate the INVENTORY line with `handoff_check.py inventory`.
- Nothing was pushed. `tools/test_s9_redteam.py` was not run.

## Self-Check: PASSED

- Files exist: handoff_check.py, HANDOFF.md, 06-EVIDENCE.md and the seven 06-03 records.
- Commits found: 7f768010, 823d4615, 4434b359 (`git rev-list --count 0c5a1436..HEAD` = 3).
- Re-runs at the final HEAD: `HANDOFF_SELFTEST=13/13`, `HANDOFF_CHECK=PASS`, working tree clean before this file.
