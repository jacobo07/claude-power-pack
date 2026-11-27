---
phase: 03-construction-metrology-contract
plan: 03
subsystem: capability_runtime / construction metrology
tags: [metrology, live-run, evidence, GEX44, capped-sample]
requires: [03-02 full contract and gates]
provides:
  - one bounded, labelled, validated live run over this host's transcripts (plane GEX44)
  - post-live regression of every phase gate
  - 03-EVIDENCE.md, the phase evidence file
affects: []
key-files:
  created:
    - .planning/workstreams/perf-construction/phases/03-construction-metrology-contract/records/03-03-live.txt
    - .planning/workstreams/perf-construction/phases/03-construction-metrology-contract/records/03-03-live.json
    - .planning/workstreams/perf-construction/phases/03-construction-metrology-contract/records/03-03-final-gates.txt
    - .planning/workstreams/perf-construction/phases/03-construction-metrology-contract/03-EVIDENCE.md
decisions:
  - "Exactly one live run, default caps and seed, never repeated; the numbers are a CAPPED SAMPLE of this host only."
  - "Evidence verdict PASS for the three ROADMAP criteria, with the definitions kept PROPOSED and TTVD kept a proxy."
status: complete
requirements: [PERF-03]
duration: ~25 min
completed: 2026-11-23
commits: 2
plan_head_before: 8ef8d33937e7aacbe2b79b68b2f5d9d6bc417779
actuals:
  tokens: 11000
  tasks: 2
  commits: 2
---

# Phase 3 Plan 03: Live GEX44 run and phase evidence Summary

The construction-metrology report ran once over this host's real transcripts (200 of 4576 files, 199998680 of 6189100855 bytes, seed 0, `capped=yes`), exit 0, header `plane: GEX44`, both closed-schema validators passing. The phase evidence file ties every number to its instrument, plane and N.

## Commits

| Task | Commit | Subject |
|------|--------|---------|
| 1 | 2bb7b6d9 | docs(03-03): live GEX44 construction-metrology run |
| 2 | 34e26f04 | docs(03-03): phase 3 evidence |

The count of 2 is measured from the ledger base (`plan_head_before`) to HEAD before this summary commit. The summary and state commit follows it.

## Live run

- Command: `python3 -I record_run.py --out PH/records/03-03-live.txt --expect pass --timeout 600 -- python3 tools/construction_metrology_report.py --root /home/kobii/.claude/projects --max-files 200 --max-bytes 200000000 --seed 0 --json-out PH/records/03-03-live.json`. Recorder footer `# exit=0`. One run only.
- Records: `records/03-03-live.txt` (header `# head: 8ef8d339`) and `records/03-03-live.json`.
- Validators: `--validate` on the JSON exit 0 (VALIDATE_OK); `--validate-text` on the text exit 0 (VALIDATE_TEXT_OK); `grep -c '^plane: GEX44$'` returns 1; JSON `plane` GEX44, `plane_source` hostname; the `CAPPED SAMPLE` line is present.
- Numbers (N_total 218 for each metric, copied from the record): TTFMC measured 18, censored 5, p50 111.54, p90 218.91, p95 UNJUDGED (n=18 < 20); TTFUR measured 80, censored 5, p50 15.53, p90 52.15, p95 83.94; TTVD measured 16, censored 7, p50 124.34, p90 272.84, p95 UNJUDGED (n=16 < 20). INCONCLUSIVE and UNAVAILABLE are 0 for all three metrics, so they are reachable only through their fixture gates. 133 of 218 starts are SKIPPED_BY_POLICY. These describe a capped sample of this host, not the population and not the laptop.
- Privacy: only the CLI opened transcript files. No transcript file was read, listed, grepped or printed by any other command, and no glob of the transcript root appears in any command. `03-EVIDENCE.md` holds no store name, file name or canary string (grep count 0).

## Final gates

`records/03-03-final-gates.txt` re-runs the eight baseline gates plus the metrology suite and the reachability gate. Comparison with `03-02-gates-after.txt`: every gate result is unchanged (13/13, 33/33, 33/33, 20/20, 11/11, 3/3, 15/15, git_invocation 6/7 with the same 14 offenders, metrology 38/38); only volatile lines differ (telemetry timings and ids, one random temp directory name, HEAD). The reachability offender set is identical by name (56 = 56), `passed=False`, and the metrology unit is not listed (declared DORMANT). `policy_hash()` is `f113a59d0dc99c56`, unchanged since 03-01.

## Evidence verdict

PASS for ROADMAP criteria 1, 2 and 3, each row of the evidence table citing a command, an exit code and a record. The evidence states that the definitions are PROPOSED, TTVD is a proxy, the sample is capped, and a GEX44 distribution is not evidence about the laptop. LP-04, LP-05 and LP-06 are copied with procedure and falsifier; `P-ids touched: none`.

## Deviations from Plan

None in scope or method. Three notes:

1. The planning-time probe saw 4575 files and 1913 stores; the live run saw 4576 files and 1919 stores. The store grows while sessions run. This is why the plan forbids a second run, and the evidence says so.
2. Commit messages were written as files under `/tmp/p3msgs` and committed with `git commit -F <file> -- <pathspec>`, as in plans 03-01 and 03-02 (the Write tool refuses paths in the shared git directory).
3. The final-gates record was produced by a small stdlib runner kept outside the repository (`/tmp/p3msgs/final_gates.py`, not committed). It emits the same `## <command> exit=<rc>` sections, last five lines per gate and the full `test_git_invocation.py` output, as the 03-01 baseline.

No defect was found in the module or CLI. No code file was changed by this plan.

## Known Stubs

None.

## Threat Flags

None. No new network, auth or trust-boundary surface; this plan only ran the existing read-only CLI and wrote records and evidence.

## Unmet

Nothing in the plan is unmet. Standing, by design: definitions PROPOSED (LP-04), no laptop distribution (LP-05), TTVD proxy (LP-06), the DORMANT liveness row awaiting its Phase 5 consumer.

## Self-Check: PASSED

Files exist: the two live records, the final-gates record, `03-EVIDENCE.md`, this summary. Commits 2bb7b6d9 and 34e26f04 are present in `git log`. `python3 tools/test_construction_metrology.py` prints METRO_PASS=38/38. `git status --porcelain` was clean before this summary; none of `tools/bench_all.py`, `tools/verify_bench_all.py`, `tools/tis_observed.py` or `modules/capability_runtime/__init__.py` changed.
