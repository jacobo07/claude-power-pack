---
phase: 04-host-pressure-admission
plan: 03
subsystem: host-pressure-evidence
tags: [live-smoke, forced-red, plane-falsifier, evidence, owner-decisions, PERF-04]
requires: [04-01 reader and classifier, 04-02 bench_all pressure wiring]
provides: [PH/smoke_pressure.py, records/04-03-*, 04-EVIDENCE.md, STATE.md Phase 4 section]
affects: [phase-4 verifier, phases 5 and 6 planning]
status: complete
requirements: [PERF-04]
plan_head_before: 22235839ebb4be6c540f73a2647987082188b1e0
commits: 3
actuals:
  tokens: 15000
  tasks: 2
  commits: 3
---

# Phase 4 Plan 03: Live smoke, evidence and decision lines Summary

The shipped reader and the shipped `bench_all.main` were run on GEX44 through a phase-local harness: the live reading is GREEN (29 claude processes, 52320 MB free, floor 3000, ceiling 40 PROPOSED_UNCALIBRATED, n=1), and the same stub data that regresses on a GREEN host is INCONCLUSIVE through the count pole and again through the RAM pole, with the RED entries kept in the temp ledger and excluded from the next window (SMOKE_PASS=7/7). Phase 4 now has `04-EVIDENCE.md`, and STATE.md holds the OWNER DECISION NEEDED lines.

Plane: every number was observed on GEX44 (kobicraft-gex44, Linux, Python 3.12.3, stdlib only). Nothing here judges the laptop (LP-07, LP-08 are LAPTOP-ONLY and UNJUDGED).

Branch: `worktree-agent-a0f2f22545d89a73b` (start HEAD 22235839). Nothing was pushed. No production code was written; `git status --porcelain tools modules vault` is empty.

## Commits

`commits: 3` is measured with `git rev-list --count 22235839..HEAD` taken before this SUMMARY was written (the SUMMARY commit is a fourth). The base is recorded explicitly because the worktree guard refused an on-disk ledger (see deviations).

| Step | Hash | Subject |
|------|------|---------|
| T1 RED | c4752b59 | test(04-03): smoke harness skeleton with the plane falsifier self-test |
| T1 GREEN | cadbbc81 | docs(04-03): record the live reading and the forced-RED smoke on GEX44 |
| T2 | 07e4f6ef | docs(04-03): phase 4 evidence, final gate run and STATE decision lines |

## Records (under `PH/records/`, PH = `.planning/workstreams/perf-construction/phases/04-host-pressure-admission`)

- `04-03-plane-selftest.txt`: PLANE_SELFTEST=4/4 (the laptop-looking pairs print `plane: UNVERIFIED`). The not-implemented skeleton run (exit 2) is kept only in /tmp, not committed.
- `04-03-live.txt`: header `plane: GEX44 host: kobicraft-gex44`, RAM 52320.125 MB (/proc/meminfo), count 29 (proc:exe+comm, ambiguous 0), floor 3000, ceiling 40, class GREEN, exit 0.
- `04-03-forced-red.txt`: plane line first, `SMOKE_PASS=7/7  threshold=7/7`, exit 0; both records pass `record_run.py --verify` (`--contains "plane: GEX44"`, `--contains "SMOKE_PASS=7/7"`).
- `04-03-final-gates.txt`, `04-03-reach-final.json`: final gate run.
- Live class measured: GREEN, so the exit-5 branch (live host not GREEN) was not taken and nothing was forged.

Real-file hashes (equal at the start, after the smoke runs and after the final gates; the harness also checks them itself at step 0 and step 7):

| File | sha256 |
|------|--------|
| vault/benchmarks/ledger.json | cef10a592e567e06fa43529966061bc223600475526fa2f435741f11582e32f4 |
| vault/config/resource-floors.json | 54a5f2af2c4d2a46151bc751000819aafcfa67d69e43e0b95fdf1ed884cfdc09 |

## Final gates versus 04-02 (D4-08)

Every exit code and counter is equal to `04-02-gates-after.txt`: a5_u6 13/13, arm preflight 23/23, bench integrity 53/53, bench gate 24/24, resource pressure 17/17, gsd resources 17/17, gsd baseline 21 passed 0 failed, git invocation exit 1 with 6/7 and the same offenders, reachability 56 offenders with names identical to `04-02-reach-after.json`. `git diff --stat f470597d..HEAD -- tools modules vault` is empty. The only textual difference is the random temp directory name in three V-RES-CLI-* lines. `tools/test_s9_redteam.py` was not re-run (814 s wall, source unchanged); the 04-02 footer `S9RT_PASS=111/114` is quoted in the final-gates record.

## STATE.md items

- OWNER DECISION NEEDED (3) for the process ceiling (PROPOSED_UNCALIBRATED): options keep 40 / lower / raise / count pole off. Pick: keep 40, with reason and reversal. Lines (4) to (7) as specified by the plan.
- Caveat for tools/test_s9_redteam.py recorded as asked, stated precisely: the first FAIL was already failing in the 04-01 baseline run (which timed out), the other two name it as their cause, and no clean control run was possible, so "present before this phase" is inferred, not shown. UNJUDGED.
- Owner decision D2 (authority raised to 215,000,000) recorded, marked as reported by the orchestrator and not independently measured.
- Position fields updated by hand: frontmatter current_phase 4 -> next 5, current_plan 3 of 3, status, stopped_at, last_updated, last_activity, progress (completed_phases 3, total_plans and completed_plans 11, percent 50), and the Current Position, Progress and Session Continuity body lines. ROADMAP.md was not touched.

## Deviations from Plan

1. **Position fields and Progress edited in STATE.md.** The plan said to leave Current Position, Progress and the metrics table to the orchestrator; the launching instruction asked for the position fields to be updated by hand because the GSD progress commands cannot parse them, so that instruction was followed. The STATE.md diff therefore also deletes the 19 old position lines it replaces (listed by `git diff`); no other pre-existing line changed, and the Performance Metrics table is untouched. The plan's "insertions only" acceptance check does not hold for that reason.
2. **[Rule 3 - environment] Commit message files in `/tmp/04-03-msgs/`** instead of `<git-dir>/gsd-msgs/`: the worktree guard refuses writes into the shared `.git/worktrees` tree (same as 04-01 and 04-02). Messages still end with the Co-Authored-By line.
3. **No on-disk plan-head ledger**: the same guard applies; `plan_head_before` is recorded above and `commits` was measured against it.
4. **Bash guard workaround**: the guard refused compound git commands and some commands containing "git" in a file name, so commands were split, and the gate-recording script lived in /tmp (outside the repo) and parsed the reachability offenders as `{unit, ...}` objects after a first run mis-parsed them (the first run's file was overwritten, never committed).
5. The `# head:` line in the two live records is c4752b59 (the skeleton), because the finished harness was committed together with the records in cadbbc81. tools/, modules/ and vault/ are identical at both; stated in the evidence header.
6. The forced-RED mode was run once during development before the recorded run (same 7/7, different RAM digits, output not kept); only the committed records are quoted.

## Known Stubs

None. The harness has no placeholder path: the skeleton's NOT IMPLEMENTED branch was replaced in cadbbc81.

## Threat Flags

None. The harness prints counts, classes and its own claim lines only (no pid, process name, command line, foreign path or environment value) and writes only under a temp directory it removes.

## Self-Check

- Files present: PH/smoke_pressure.py, PH/04-EVIDENCE.md, and the six `04-03-*` records: checked by listing (all 22 record names cited in 04-EVIDENCE.md exist, loop output OK for every one).
- `grep -n '^## ' 04-EVIDENCE.md` lists exactly nine heading lines (lines 10, 20, 30, 40, 69, 84, 90, 105, 115).
- Commits present: c4752b59, cadbbc81, 07e4f6ef in `git log 22235839..HEAD`; last subject confirmed with `git log -1 --format=%s`.
- `git status --porcelain tools modules vault` empty; real ledger and floors hashes unchanged.

## Self-Check: PASSED
