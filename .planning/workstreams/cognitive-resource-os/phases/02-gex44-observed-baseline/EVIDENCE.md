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

## 3. Laptop comparison (ROADMAP criterion 3)

"Instrument can explain" means a factor that tis_observed/budget_monitor MEASURED on GEX44 differs from the
laptop in a direction consistent with the difference -- an attribution candidate, never a proven cause.

| metric | entrypoint | laptop (source, scope) | GEX44 | same definition? | instrument can explain | instrument cannot explain |
|--------|------------|-------------------------|-------|-------------------|--------------------------|-----------------------------|
| first_call_shared_share_median | sdk-cli | 1.9% (L1, commit 10299f8; scope not recorded) | 30.0%; excl. this repo's dir: 30.0%; GEX44 transcripts, not the laptop's | partly (L1's scope is not recorded) | POPULATION (3 sdk-cli sessions total this window vs a much larger laptop population), WINDOW (this corpus spans at most ~7 days, little time for an earlier session to seed a shared cache) | PREFIX CONTENT, MISS CAUSE, LAPTOP PROVENANCE (L1 scope unrecorded), HOST CONFIG |
| first_call_shared_share_median | cli | 16.4% (L1, commit 10299f8; scope not recorded) | 46.6%; excl. this repo's dir: 46.6%; GEX44 transcripts, not the laptop's | partly (L1's scope is not recorded) | POPULATION (13 cli sessions, mostly mission workers, not the laptop's population), SESSION SHAPE (higher calls-per-session here gives more chances to land inside an earlier session's still-cached front), WINDOW | PREFIX CONTENT, DRIVER (entrypoint does not distinguish a human cli session from a mission-worker one), LAPTOP PROVENANCE, HOST CONFIG |
| share_1h_write_usd_7d | sdk-cli | 79.9% ($72.00 of $90.06) (L2, commit 10299f8; population: budget_monitor-style iter_calls incl. subagents, ts >= now-7d, entrypoint == sdk-cli; pricing file not named) | 98.6%; excl. this repo's dir: 98.6%; GEX44 transcripts, not the laptop's | yes (same population definition: iter_calls incl. subagents, sdk-cli only, trailing 7d) | TTL MIX (cache_write_1h_tokens/cache_write_tokens reads 100.0% on GEX44's 3 calls -- almost the whole write is 1h), SESSION SHAPE (median 1 call/session both hosts), MODEL MIX (single model, claude-opus-5-5) | PREFIX CONTENT, MISS CAUSE, DRIVER |
| usd_7d | sdk-cli | $90.06 (L2, commit 10299f8; same population as above) | $0.53; excl. this repo's dir: $0.53; GEX44 transcripts, not the laptop's | yes | POPULATION (3 sdk-cli calls this week on GEX44 vs 272 on the laptop's window -- far less programmatic usage on this host right now), SESSION SHAPE | DRIVER, HOST CONFIG |
| calls_7d | sdk-cli | 272 (L2, commit 10299f8) | 3; excl. this repo's dir: 3; GEX44 transcripts, not the laptop's | yes | POPULATION, WINDOW | DRIVER |
| sessions_7d | sdk-cli | 62 (L2, commit 10299f8) | 3; excl. this repo's dir: 3; GEX44 transcripts, not the laptop's | yes | POPULATION | DRIVER |
| calls_per_session_median_7d | sdk-cli | 1 (L2, commit 10299f8) | 1; excl. this repo's dir: 1; GEX44 transcripts, not the laptop's | yes | SESSION SHAPE (values match; no difference to attribute) | none |
| sessions_le2_calls_7d | sdk-cli | 47 of 62 (L2, commit 10299f8) | 3 of 3; excl. this repo's dir: 3 of 3; GEX44 transcripts, not the laptop's | yes | SESSION SHAPE, POPULATION (n=3 saturates at 100% where n=62 does not) | DRIVER |
| first_call_context_median | all | 168631 (95000-227000) (L3, commit 9fa1017; that repo's transcripts only, unsplit by entrypoint) | 52916 (mixed cli+sdk-cli, all-projects native summary); excl. this repo's dir: 52913; GEX44 transcripts, not the laptop's | no (L3 is repo-only and unsplit; this row compares GEX44's mixed-entrypoint native figure, not a per-entrypoint one) | PREFIX SIZE (a different repo's tool list, MCP set, CLAUDE.md and rules text produce a different measured prefix), POPULATION | PREFIX CONTENT, HOST CONFIG, LAPTOP PROVENANCE |
| entrypoint_file_mix | all | 378 cli, 22 sdk-cli of 400 (L4, commit ca69a04) | 13 cli, 3 sdk-cli MEASURED-attributed, 26 MEASURED_ZERO unattributed of 42 (section 2a/0a); GEX44 transcripts, not the laptop's | partly (entrypoint is attributed from a session's first REAL call; a MEASURED_ZERO session reads as neither cli nor sdk-cli on GEX44 -- whether the laptop's 400-file count included any zero-call sessions is unrecorded) | POPULATION, SELF-MEASUREMENT (this worktree's own sessions read as 1 of the 13 cli sessions, section 2c) | DRIVER, LAPTOP PROVENANCE |
| startup_prefix_share_estimate | all | about 50% (ESTIMATE) (L3, commit 9fa1017; call-weighted, that repo only) | 36.4% (ESTIMATE, all-projects); excl. this repo's dir: 35.6%; GEX44 transcripts, not the laptop's | no (both are the same kind of estimate, on different corpora, and both label it ESTIMATE) | PREFIX SIZE, SESSION SHAPE (calls-per-session differs between the two corpora) | PREFIX CONTENT, HOST CONFIG |

### 3a. What the instrument can and cannot explain

- GEX44's sdk-cli first-call shared-share (30.0%) reads higher than the laptop's L1 figure (1.9%), but the
  measured population is 3 sessions against the laptop's unrecorded (larger) one -- POPULATION and WINDOW are
  candidate factors; PREFIX CONTENT (what actually differs between two sessions' tool lists / MCP set /
  environment block) is not measured by either instrument, so no claim is made about the shared-share LEVEL being
  comparable across hosts.
- GEX44's cli first-call shared-share (46.6%) also reads well above the laptop's L1 16.4%; SESSION SHAPE (this
  host's cli sessions are mostly mission workers making many calls, section 2b calls_per_session_median 39) is a
  measured factor consistent with more chances to land a cache hit, but DRIVER (mission worker vs human) is not
  something entrypoint records, so this is an attribution candidate, not a finding.
- GEX44's sdk-cli 1h-write share of spend (98.6%) reads above the laptop's L2 79.9%; both hosts' median session
  makes exactly 1 call (SESSION SHAPE matches), and GEX44's cache_write_1h_tokens/cache_write_tokens is 100.0%,
  so every write in this small sample was 1h -- consistent in direction, but MISS CAUSE (content mismatch vs TTL
  expiry vs cache scope) is not separable from a single cache_read figure.
- GEX44's sdk-cli USD/calls/sessions over 7 days (\$0.53 / 3 / 3) are far below the laptop's L2 (\$90.06 / 272 /
  62); POPULATION explains the gap in scale (this host currently runs far less programmatic sdk-cli traffic than
  the laptop's measured window), consistent with the workstream's own recent activity being mostly cli
  (orchestrator/planner/executor) rather than sdk-cli.
- The entrypoint file mix is not measured on the same definition on both hosts: GEX44 can only attribute
  entrypoint to a session that made at least one real call (26 of 42 session files here are MEASURED_ZERO and
  read as neither cli nor sdk-cli), while the laptop's L4 400-file count does not record whether it excluded
  zero-call sessions -- this is an instrument gap (section 4), not a measured difference.
- GEX44's startup_prefix_share_estimate (36.4% all-projects) reads below the laptop's L3 ~50% ESTIMATE; both are
  the same call-weighted estimate formula on different corpora (PREFIX SIZE, SESSION SHAPE differ), but neither
  figure is comparable across hosts without knowing what fraction of each corpus's prefix bytes are MCP-tool-list
  driven -- HOST CONFIG (Windows laptop estate vs this Linux host) is a candidate the instrument cannot separate.
- Open question for Phase 4: whether the cross-session prefix miss (low first_call_shared_share_median on both
  hosts, at very different levels) follows MCP tool-list variance between sessions, as the laptop's 10299f8
  commit message suspected but did not measure ("five timed out this session"). Neither host's instrument reads
  which MCP servers were connected on a given call, so this stays UNJUDGED until Phase 4's A/B.

## 4. Tool defects (ROADMAP criterion 4)

tool_defects: none

No tool defect (Defect procedure cases a/b/c) fired in this plan. All three gates re-run in Task 1
(tools/test_tis_observed.py, tools/test_budget_monitor_observed.py, tools/test_pricing_source.py) held their
Phase-1 pass counts (25/25, 7/7, 5/5) with no `[FAIL]` line and no traceback. `tools/tis_report.py --observed
--all-projects` exited 0 with a valid summary (section 1). `assumption_checks.multi_entrypoint_files` read 0
(section 2a), so the one-entrypoint-per-file contract (case c) held. `reconcile.overall` read MATCH on the first
snapshot run (section 2d), so no arithmetic mismatch (case b) was found. No path under `tools/` or `modules/`
changed in this plan (`git status --porcelain=v1 -- tools modules` prints nothing after Task 2's commit).

instrument_gaps:
- The native `tis_observed.summarize()` splits only `startup_shared_share_median` by entrypoint; no tool emits
  the 1h cache-write spend share or a per-entrypoint 7-day USD figure -- `by_entrypoint.py` composes these from
  `iter_calls` + `cost_usd` (section 2). Follow-up for Phase 5; not changed here.
- No tool attributes `entrypoint` to a `MEASURED_ZERO` session (it is only set from a session's first REAL call),
  so a per-entrypoint file-mix count undercounts against a laptop figure (L4) that may not exclude zero-call
  sessions the same way (section 3, entrypoint_file_mix row). Follow-up for Phase 5; not changed here.
- The laptop's L1 first-call-shared-share population/scope (all-projects vs repo-only) is not recorded in its
  source commit (10299f8); this plan's `own_dir_present`/excluding-scope split (section 2c) is the mechanism this
  workstream now has for that distinction, but it cannot retroactively resolve the laptop's own scope. Follow-up
  for Phase 5; not changed here.
- The laptop's L2 pricing file is not named in its source commit; 383cb37 (anthropic_2026-09.json) precedes
  10299f8 so it was probably the same file, but that is unverified (context section, laptop reference). Follow-up
  for Phase 5; not changed here.

## 5. Phase verdict (CRO-02)

inputs: api_key=UNSET, run_state=MEASURED, reconcile=MATCH, tool_defects=none
phase_verdict: MEASURED

cro02: SATISFIED

Constraints honoured: no model call made (this phase reads transcripts only); no package installed; nothing
pushed (`git status -sb` shows no upstream push made by this plan); every commit used an explicit pathspec
(section 0/1/2 commits touch only EVIDENCE.md and by_entrypoint.py); no edit under `~/.claude/settings.json`,
`~/.claude/rules/`, `~/.claude/CLAUDE.md`, credentials, or `/home/kobii/.claude/skills/claude-power-pack` (the
live install); no other mission's directory used; transcripts read read-only throughout (no tool wrote into
`~/.claude/projects`, and `budget_monitor.main()` -- which appends telemetry -- was never called, only
`_aggregate_observed()` directly); EVIDENCE.md holds aggregates only (no transcript text, no session ids, no
per-project directory names; leak/tag checks re-run clean after every task's commit).

next: Phase 4 reads first-call `cache_read_input_tokens`/`cache_creation_input_tokens` through this same
instrument (tis_observed) for its A/B; the `_shared_by_entrypoint` and `by_entrypoint.py` composition already
built here are directly reusable. Phase 5 relabels RESUMPTION.md and ukdl-cognitive-resource-os.md's laptop
figures (L1-L4) by host, per this phase's assumption-delta decision, and folds in this section's
`instrument_gaps:` bullets as open follow-ups.
