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

<!-- Sections 2-5 are written by Tasks 2 and 3. -->
