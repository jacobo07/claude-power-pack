---
phase: 03-construction-metrology-contract
plan: 01
subsystem: capability_runtime / construction metrology
tags: [metrology, ttfmc, ttfur, ttvd, censoring, transcripts]
requires: [phase 1 D1 owner decision, phase 2 percentile and record_run fixture]
provides:
  - construction_metrology owner module (events, eight-state vocabulary, bounded scan, report)
  - PROPOSED definitions contract for TTFMC, TTFUR, TTVD pinned to the code by a gate
affects: [03-02, 03-03]
key-files:
  created:
    - modules/capability_runtime/construction_metrology.py
    - tools/construction_metrology_report.py
    - tools/test_construction_metrology.py
    - vault/specs/construction-metrology-contract.md
  modified:
    - modules/capability_runtime/agent_resolver.py
decisions:
  - "Definitions are PROPOSED, never Owner-defined (D-02); LP-04..LP-06 carry the laptop-side confirmation."
  - "TTVD end is a proxy: first ok Bash result after the first change (command text is never read, D-05)."
  - "Closure, not the absence of the event alone, decides NOT_APPLICABLE vs UNOBSERVED for TTFMC and TTVD."
status: complete
requirements: [PERF-03]
duration: ~35 min
completed: 2026-11-22
commits: 5
plan_head_before: 194062f9
actuals:
  tokens: 13100
  tasks: 2
  commits: 5
---

# Phase 3 Plan 01: Construction metrology tracer and PROPOSED contract Summary

One human turn in a Claude Code transcript now becomes a classified sample and a plane-labelled TTFUR/TTFMC/TTVD percentile line, with the module in `NOT_POLICY`, the percentile connected to its one owner, and the written PROPOSED definitions pinned to the code by a gate (METRO_PASS=9/9).

## Branch and commits

Branch: `worktree-agent-a3e908db461be7ab4` (the isolated worktree branch given by the orchestrator; base `mission/perf-construction` at 194062f9). Nothing pushed.

| Commit | Subject |
|---|---|
| 57dc895b | docs(03-01): record baselines of eight existing gates and reachability offender set |
| 18404f01 | test(03-01): RED gates for the construction-metrology tracer (module absent) |
| 00e7d004 | feat(03-01): tracer from human turn to plane-labelled TTFUR percentile line |
| f8e69469 | test(03-01): RED gates for TTFMC, TTVD, applicability and the contract match |
| 3c53c9e7 | feat(03-01): PROPOSED TTFMC/TTFUR/TTVD contract and TTFMC and TTVD events |

Records (all under `.planning/workstreams/perf-construction/phases/03-construction-metrology-contract/records/`): `03-01-baseline.txt`, `03-01-reach-before.json`, `03-01-T1.red.txt` (0/4, exit 1, pristine=yes), `03-01-T1.green.txt` (4/4), `03-01-T2.red.txt` (5/9, exit 1, pristine=yes), `03-01-T2.green.txt` (9/9). Both red records verify with `record_run.py --verify ... --expect fail --pristine-required`. The Task 1 policy-id gate failed on the hash inequality (with-file `cd354ea6f17b608b` vs without `169abc7fce15ce84`), not only on membership.

## Baseline table (recorded before the first edit, plane GEX44)

| Command | Exit | Count |
|---|---|---|
| tools/test_capability_invocation.py | 0 | 13/13 |
| tools/test_capability_runtime.py | 0 | 33/33 |
| tools/test_agent_resolver.py | 0 | 33/33 |
| tools/test_agent_telemetry.py | 0 | 20/20 |
| tools/test_capability_consumption.py | 0 | 11/11 |
| tools/test_capability_directory.py | 0 | 3/3 |
| tools/test_reachability.py | 0 | 15/15 |
| tools/test_git_invocation.py | 1 | 6/7 (V-GITINV-NO-GROWTH, 14 pre-existing offenders, full output recorded) |
| modules/liveness/reachability.py | 1 | 56 pre-existing offenders (524 modules), names in `03-01-reach-before.json` |

After the plan, the same seven passing gates are unchanged (telemetry 20/20, consumption 11/11, directory 3/3, reachability 15/15, invocation 13/13, runtime 33/33, resolver 33/33); `test_git_invocation.py` still 6/7 with the same 14 offenders (none of the new files in the list).

## Policy id

Live `policy_hash()` before: `169abc7fce15ce84`. After: `f113a59d0dc99c56`. The one-time move is caused by editing `agent_resolver.py` itself (the `NOT_POLICY` line plus one comment sentence), because that file is hashed; precedent: the agent_telemetry and agent_resolver_cli additions. The metrology file never moves it: after Task 2 edited the module the live id is still `f113a59d0dc99c56`, and V-METRO-POLICY-ID-UNMOVED proves identical ids with the file, without it and edited, equal to live.

## Hand mutation check of the contract gate

Run in process on the committed code, nothing edited on disk: (1) `METRICS["TTFUR"]["end"]` changed to a different identifier -> FAIL "TTFUR: end 'ASSISTANT_TEXT' != 'ASSISTANT_ANY'"; (2) `HORIZON_S["TTVD"]` = 7201 -> FAIL horizon mismatch; (3) FAILED removed from `CENSORED_STATES` -> FAIL "FAILED: censored 'yes' != 'no'". The contract gate fails on each mutant (0 pass, 3 fail).

## Real-data smoke (instrument: this CLI, plane GEX44, capped sample)

`tools/construction_metrology_report.py --max-files 20 --max-bytes 50000000 --seed 0`: 20 of 4576 files, 27.8 MB read, capped=yes, labelled CAPPED SAMPLE. TTFUR N_total=26 measured=24 censored=2 p50=19.22 s, p90=72.63 s, p95=87.23 s (UNJUDGED rules apply below n=5/10/20); TTFMC measured=9, NOT_APPLICABLE=9, UNOBSERVED=8; TTVD measured=8, NOT_APPLICABLE=9, UNOBSERVED=9. Only counts, states and timings were printed. This is a smoke of the pipeline, not a finding about construction speed, and says nothing about the laptop.

## Deviations from Plan

**1. [Rule 3 - Blocking] Commit message files not under the git dir.** The plan asks for message files in `<absolute-git-dir>/gsd-msgs/`. The Write tool refused paths outside the worktree (the git dir is the shared checkout), so messages were written to `/tmp/p3msgs/*.msg` and committed with `git commit -F <file> -- <pathspec>`. Same protocol otherwise (explicit pathspec, subject verified after each commit).

**2. [Rule 2 - Correctness] Synthetic/API-error assistant lines are not an end event.** The plan's ASSISTANT_TEXT predicate did not exclude `message.model == "<synthetic>"` or `isApiErrorMessage`, although the privacy list names both fields. Such lines are recorded as `ASSISTANT_SYNTHETIC` so an API error cannot be measured as a fast first response; plan 03-02's FAILED handling can build on it. Sidechain lines are skipped entirely for the same reason.

**3. [Rule 2 - Correctness] Extra UNOBSERVED reasons.** `start_without_timestamp`, `end_without_timestamp` and `end_before_start` (all censored, value null, never 0) were added to the closed reason vocabulary so a missing or inverted timestamp cannot produce a number.

**4. Scan cap semantics.** A file that would push `bytes_read` over `--max-bytes` is skipped and counted, and the scan continues with later (smaller) files; the plan text said "until a cap would be exceeded". Both are labelled `capped`; skip-and-continue uses the byte budget better.

**5. Per-sample list in the report.** Each metric block carries `samples` (state, reason, value or null) in addition to `values`, so a censored sample is visible as `null` in the JSON (needed by V-METRO-TRACER-UNOBSERVED-CENSORED).

## Unmet / handed over

- Reachability: `python3 modules/liveness/reachability.py` now lists 57 offenders, the 56 baseline units plus the new `capability_runtime/construction_metrology` (the CLI is not a hook, command or agent). The DORMANT declaration in `vault/liveness/reachability_registry.json` is owned by plan 03-02 (its files_modified and must_haves), not by this plan; until it lands the new unit is an undeclared offender.
- FAILED, TIMED_OUT, INCONCLUSIVE, SKIPPED_BY_POLICY and UNAVAILABLE are declared in `STATES` and the contract but not yet reachable from input shapes: plan 03-02.
- The module and CLI inspect only metadata; no canary string appears in any output (checked in the two tracer gates and in-process by `scan_lines`); the full canary and closed-schema gates belong to 03-02.
- LP-04 (definitions), LP-05 (laptop run) and LP-06 (TTVD proxy) are LAPTOP-ONLY and written in the contract with falsifiers.

## Known Stubs

None. No placeholders, mocks or empty catches in the shipped module or CLI.

## Threat Flags

None beyond the plan's threat model: the new surface is a read-only transcript reader, bounded by file and byte caps, printing counts and timings only.

## Self-Check: PASSED

Files exist: module, CLI, test file, contract, six records, this summary. Commits 57dc895b, 18404f01, 00e7d004, f8e69469, 3c53c9e7 present in `git log`. `python3 tools/test_construction_metrology.py` prints METRO_PASS=9/9, `python3 tools/test_agent_resolver.py` 33/33. `git status --porcelain` clean before this summary; none of `tools/bench_all.py`, `tools/verify_bench_all.py`, `tools/tis_observed.py` or `modules/capability_runtime/__init__.py` changed.
