# Phase 02 EVIDENCE -- GEX44 observed baseline

Every figure below was measured from GEX44's own transcripts (read-only, /home/kobii/.claude/projects), not the
laptop's, on measured_at_utc.

## 0. Pre-checks

ANTHROPIC_API_KEY: UNSET
head: c8b73ae5a3a6502d45dcb9c2e2b1b55418c70d4f
branch: mission/cognitive-resource-os-gex44
measured_at_utc: 2026-09-28T12:35:27Z
gate_tis_observed: rc=0 TISOBS_PASS=25/25  threshold=25/25
gate_budget_monitor_observed: rc=0 BUDGETOBS_PASS=7/7  threshold=7/7
gate_pricing_source: rc=0 PRICESRC_PASS=5/5  threshold=5/5

No `[FAIL]` line in any of the three gate logs (grep -c '\[FAIL\]' over each log: 0/0/0).

### 0a. Corpus inventory

| metric | value | source |
|--------|-------|--------|
| project_dirs | 11 | GEX44 transcripts, not the laptop's (c1) |
| session_files | 42 | GEX44 transcripts, not the laptop's (c2) |
| subagent_files | 39 | GEX44 transcripts, not the laptop's (c3) |
| corpus_bytes | 82027379 | GEX44 transcripts, not the laptop's (c4) |
| oldest_session_file_date | 2026-09-22 | GEX44 transcripts, not the laptop's (c5) |
| newest_session_file_date | 2026-09-28 | GEX44 transcripts, not the laptop's (c5) |

- c1: `find /home/kobii/.claude/projects -mindepth 1 -maxdepth 1 -type d | wc -l`
- c2: `find /home/kobii/.claude/projects -mindepth 2 -maxdepth 2 -name '*.jsonl' | wc -l`
- c3: `find /home/kobii/.claude/projects -path '*/subagents/*.jsonl' | wc -l`
- c4: `du -sb /home/kobii/.claude/projects`
- c5: `find /home/kobii/.claude/projects -mindepth 2 -maxdepth 2 -name '*.jsonl' -printf '%TY-%Tm-%Td\n' | sort | sed -n '1p;$p'`

The planning-time note (context section, measured earlier the same day) recorded 72 MB and 35 subagent files; this
run reads 82027379 bytes (~78 MB) and 39 subagent files, and session_files/project_dirs are unchanged (42/11) --
the corpus grew between the planning-time snapshot and this measurement, consistent with mission workers still
writing transcripts on this host. Re-measured, not copied, per the plan's "re-measure them" instruction.

## 1. tis_report --observed --all-projects (ROADMAP criterion 1)

command: `python3 tools/tis_report.py --observed --all-projects`
tis_report_rc: 0
run_state: MEASURED (GEX44 transcripts, not the laptop's)

| metric | value | source |
|--------|-------|--------|
| sessions | 42 | GEX44 transcripts, not the laptop's |
| by_state | MEASURED_ZERO=26, MEASURED=16 | GEX44 transcripts, not the laptop's |
| calls | 559 | GEX44 transcripts, not the laptop's |
| subagent_calls | 1388 | GEX44 transcripts, not the laptop's |
| startup_context_median | 52916 | GEX44 transcripts, not the laptop's |
| startup_context_min | 28076 | GEX44 transcripts, not the laptop's |
| startup_context_max | 66549 | GEX44 transcripts, not the laptop's |
| startup_prefix_share_estimate | 0.3738 ESTIMATE | GEX44 transcripts, not the laptop's |
| startup_shared_share_median[sdk-cli] | 0.2996 | GEX44 transcripts, not the laptop's |
| startup_shared_share_median[cli] | 0.4656 | GEX44 transcripts, not the laptop's |
| duplicate_usage_lines_collapsed | 559 | GEX44 transcripts, not the laptop's |
| synthetic_skipped | 8 | GEX44 transcripts, not the laptop's |
| bad_lines | 0 | GEX44 transcripts, not the laptop's |
| project_dirs | 11 | GEX44 transcripts, not the laptop's |

cwd_key_check_rc: 0
cwd_key_sessions: 1 (GEX44 transcripts, not the laptop's)
t1_moved_lines: 0

The cwd project-key check (`python3 tools/tis_report.py --observed`, no `--all-projects`) resolved this worktree's
cwd to an existing transcript directory (name omitted, per-project directory names are not recorded here) holding
1 session (state MEASURED, 68 calls, 238 subagent calls). `project_key` therefore resolves correctly on this Linux
host, unlike gate V-TISOBS-PROJECT-KEY which only exercises a Windows path literal. This confirms the "sessions
running this workstream are inside the corpus they measure" note from planning time (section 2b/2c of this file
report the excluding-this-repo scope separately).

## 2. Per-entrypoint baseline (ROADMAP criterion 2)

reproducer: .planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/by_entrypoint.py
command: `python3 .planning/workstreams/cognitive-resource-os/phases/02-gex44-observed-baseline/by_entrypoint.py`
reproducer_rc: 0
selftest: BYEP_SELFTEST_PASS=9/9  threshold=9/9
measured_at_utc: 2026-09-28T12:45:28Z
window: trailing 7 days, cutoff 2026-09-21T12:45:28Z
pricing_file: vault/pricing/anthropic_2026-09.json (status ok, fetched 2026-09-27T00:00:00Z)
reconcile: MATCH
reconcile_attempts: 1
t2_moved_lines: 0

USD figures are API-rate equivalents of subscription usage, not charges. Section 1's separate `tis_report` read
(Task 1, measured_at_utc 2026-09-28T12:35:27Z) can differ slightly from this section's snapshot (measured_at_utc
2026-09-28T12:45:28Z) because transcripts are still being written by mission workers on this host between runs
(section 1's all-projects `calls` read 559; this snapshot's native `calls` reads 591 -- both are correct readings
of a moving corpus, not a discrepancy).

The trailing-7d `calls` row counts every call from `tis_observed.iter_calls`, which includes subagent calls by
default (matching `budget_monitor._aggregate_observed`'s own definition, so R5/R6 reconcile against it). The
all-time `calls` row instead mirrors `tis_observed.summarize`'s native `calls` field, which counts only
main-session calls and tracks `subagent_calls` separately. The two rows are therefore not on the same basis by
design -- reusing each instrument's own definition rather than inventing a third one.

### 2a. Assumption checks

| metric | value | source |
|--------|-------|--------|
| multi_entrypoint_files | 0 | GEX44 transcripts, not the laptop's |
| calls_without_ttl_split | 0 | GEX44 transcripts, not the laptop's |
| sessions_under_multiple_entrypoints_7d | 0 | GEX44 transcripts, not the laptop's |
| unpriced_models_7d | 0 | GEX44 transcripts, not the laptop's |
| corpus span | earliest 2026-09-24T20:41:32Z, latest 2026-09-28T12:45:25Z, span_days 3 | GEX44 transcripts, not the laptop's |
| own_dir_present | true | GEX44 transcripts, not the laptop's |

Every call in the corpus carries an unambiguous TTL-split (`calls_without_ttl_split: 0`) and every session-file
carries exactly one `entrypoint` value (`multi_entrypoint_files: 0`), consistent with the planning-time shape
probe. `corpus.earliest_call_utc`/`latest_call_utc` are narrower than section 0a's file-mtime span
(2026-09-22 to 2026-09-28) because they are drawn from each call's own `ts` field, not file mtimes -- the oldest
file's first calls predate this window and its later calls fall inside it.

### 2b. All projects

| metric | window | cli | sdk-cli | source |
|--------|--------|-----|---------|--------|
| sessions | all-time | 13 | 3 | GEX44 transcripts, not the laptop's |
| sessions_by_state | all-time | MEASURED=13 | MEASURED=3 | GEX44 transcripts, not the laptop's |
| calls | all-time | 588 | 3 | GEX44 transcripts, not the laptop's |
| subagent_calls | all-time | 1429 | 0 | GEX44 transcripts, not the laptop's |
| first_call_context_median | all-time | 52966 | 33776 | GEX44 transcripts, not the laptop's |
| startup_shared_share_median | all-time | 46.6% | 30.0% | GEX44 transcripts, not the laptop's |
| calls_per_session_median | all-time | 39 | 1 | GEX44 transcripts, not the laptop's |
| state_7d | trailing 7d | MEASURED | MEASURED | GEX44 transcripts, not the laptop's |
| sessions_7d | trailing 7d | 13 | 3 | GEX44 transcripts, not the laptop's |
| calls_7d | trailing 7d | 2017 | 3 | GEX44 transcripts, not the laptop's |
| calls_per_session_median_7d | trailing 7d | 85 | 1 | GEX44 transcripts, not the laptop's |
| sessions_le2_calls_7d | trailing 7d | 0 | 3 | GEX44 transcripts, not the laptop's |
| usd_7d | trailing 7d | $123.26 | $0.53 | GEX44 transcripts, not the laptop's |
| usd_1h_write_7d | trailing 7d | $16.15 | $0.53 | GEX44 transcripts, not the laptop's |
| share_1h_write_usd_7d | trailing 7d | 13.1% | 98.6% | GEX44 transcripts, not the laptop's |
| share_1h_write_tokens_7d | trailing 7d | 23.7% | 100.0% | GEX44 transcripts, not the laptop's |
| ttl_assumed_calls_7d | trailing 7d | 0 | 0 | GEX44 transcripts, not the laptop's |
| unpriced_calls_7d | trailing 7d | 0 | 0 | GEX44 transcripts, not the laptop's |
| usd_by_model_7d | trailing 7d | opus-5-5 $71.69, sonnet-5 $51.58 | opus-5-5 $0.53 | GEX44 transcripts, not the laptop's |

A `(MEASURED_ZERO)` group also exists (26 sessions, all-time only, no `sdk-cli`/`cli` column -- omitted from this
table per the Evidence-file conventions, since only `| metric |` rows carry data and the group is neither cli nor
sdk-cli). No other real entrypoint group was discovered; the only non-cli/sdk-cli key in `by_entrypoint` is the
state-parenthesized `(MEASURED_ZERO)` group.

### 2c. Excluding this repo's own project dir (the measuring run)

| metric | window | cli | sdk-cli | source |
|--------|--------|-----|---------|--------|
| sessions | all-time | 12 | 3 | GEX44 transcripts, not the laptop's |
| sessions_by_state | all-time | MEASURED=12 | MEASURED=3 | GEX44 transcripts, not the laptop's |
| calls | all-time | 520 | 3 | GEX44 transcripts, not the laptop's |
| subagent_calls | all-time | 1166 | 0 | GEX44 transcripts, not the laptop's |
| first_call_context_median | all-time | 52943 | 33776 | GEX44 transcripts, not the laptop's |
| startup_shared_share_median | all-time | 46.6% | 30.0% | GEX44 transcripts, not the laptop's |
| calls_per_session_median | all-time | 33.5 | 1 | GEX44 transcripts, not the laptop's |
| state_7d | trailing 7d | MEASURED | MEASURED | GEX44 transcripts, not the laptop's |
| sessions_7d | trailing 7d | 12 | 3 | GEX44 transcripts, not the laptop's |
| calls_7d | trailing 7d | 1686 | 3 | GEX44 transcripts, not the laptop's |
| calls_per_session_median_7d | trailing 7d | 63.5 | 1 | GEX44 transcripts, not the laptop's |
| sessions_le2_calls_7d | trailing 7d | 0 | 3 | GEX44 transcripts, not the laptop's |
| usd_7d | trailing 7d | $105.82 | $0.53 | GEX44 transcripts, not the laptop's |
| usd_1h_write_7d | trailing 7d | $14.54 | $0.53 | GEX44 transcripts, not the laptop's |
| share_1h_write_usd_7d | trailing 7d | 13.7% | 98.6% | GEX44 transcripts, not the laptop's |
| share_1h_write_tokens_7d | trailing 7d | 25.6% | 100.0% | GEX44 transcripts, not the laptop's |
| ttl_assumed_calls_7d | trailing 7d | 0 | 0 | GEX44 transcripts, not the laptop's |
| unpriced_calls_7d | trailing 7d | 0 | 0 | GEX44 transcripts, not the laptop's |
| usd_by_model_7d | trailing 7d | opus-5-5 $61.42, sonnet-5 $44.41 | opus-5-5 $0.53 | GEX44 transcripts, not the laptop's |

This scope excludes the one project dir belonging to this worktree's own path (`own_dir_present: true`, section
2a). The delta between 2b and 2c (1 cli session, 68 calls, 238 subagent calls, ~$17.44 of the trailing-7d cli
spend) is exactly the orchestrator/planner/executor sessions running this workstream, confirming the
planning-time note that this run is measuring transcripts that include its own activity.

### 2d. Reconciliation

- R1 (sum of group sessions vs native sessions): MATCH
- R2 (sum of group calls vs native calls): MATCH
- R3 (each MEASURED group's startup_shared_share_median vs native startup_shared_share_median[key]): MATCH
- R4 (tis_report.main(["--observed","--all-projects"]) sessions/calls vs native): MATCH
- R5 (trailing_7d sdk-cli calls vs budget_monitor._aggregate_observed calls): MATCH
- R6 (trailing_7d sdk-cli usd vs budget_monitor._aggregate_observed usd, abs diff under 1e-6): MATCH

overall: MATCH (reconciled on the first snapshot run; no rerun needed).

<!-- Sections 3-5 are written by Task 3. -->
