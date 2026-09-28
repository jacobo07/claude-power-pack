# Phase 04 EVIDENCE -- Prefix cache-miss A/B (GEX44, subscription quota)

Every figure in this file comes from GEX44's own transcripts or its installed claude, not the laptop's.

## 0. Pre-checks (ROADMAP criterion 1)

ANTHROPIC_API_KEY: UNSET
anthropic_env_names: none
blocking_env_names: none
scrubbed_env_names: CLAUDECODE, CLAUDE_CODE_CHILD_SESSION, CLAUDE_CODE_ENTRYPOINT, CLAUDE_CODE_EXECPATH, CLAUDE_CODE_MESSAGING_SOCKET, CLAUDE_CODE_MESSAGING_TOKEN, CLAUDE_CODE_SESSION_ATTENDED, CLAUDE_CODE_SESSION_ID, CLAUDE_EFFORT, CLAUDE_JOB_DIR, CLAUDE_PID
home: /home/kobii

head: 6825d78a25da2cdc534c97a3b0cddaca6804b808
branch: mission/cognitive-resource-os-gex44
measured_at_utc: 2026-09-28T14:25:23Z

claude_path: /home/kobii/.local/bin/claude
claude_resolved: /home/kobii/.local/share/claude/versions/2.1.283
claude_version: 2.1.283 (Claude Code)
binary_bytes: 241556664
binary_sha256: 1859583ce32920595c61ef868bee52e1b1594f7486db209935e01f1e5e804ae2

auth_status_rc: 0
auth_loggedIn: true
auth_method: claude.ai
auth_api_provider: firstParty
auth_api_key_source: ABSENT
auth_subscription_type: max
auth_projects_directory: /home/kobii/.claude/projects
projects_dir_matches_instrument: YES
credentials_type: claudeAiOauth

credentials_evidence: `claude auth status --json` run under the runs' own scrubbed environment via ab_runner.py --auth-check, allowlisted keys only (AUTH_KEYS); grounded by excerpts X01 (authMethod ladder) and X02 (auth status field list); the OAuth token itself is never read by this plan.
credentials_file: stat only -- /home/kobii/.claude/.credentials.json size=524 mtime=1790590674; never opened, read, copied, hashed or linked by this plan.
precheck: PASS

### 0a. Installed flags and mechanisms

help_flags_used: -p/--print PRESENT, --model PRESENT, --session-id PRESENT, --output-format PRESENT (stream-json PRESENT), --verbose PRESENT, --strict-mcp-config PRESENT, --mcp-config PRESENT (all verified in raw/claude-help.txt)
max_turns_flag: ABSENT (the installed help lists no --max-turns)
one_call_mechanism: the trivial prompt. `--tools ""` is rejected because it changes the tool list under test. `--max-budget-usd` is rejected because the help names only "API calls", so its effect on subscription auth is not established without a run.
stream_json_init_fields: X03 -- subtype:"init",cwd:e.cwd,session_id:e.sessionId,tools:e.tools.map(name),mcp_servers:e.mcpClients.map({name,status,source}),model:e.model,permissionMode,slash_commands,apiKeySource (byte-verified in raw/static-excerpts.txt)
entrypoint_rule: X04 -- when the inherited CLAUDE_CODE_ENTRYPOINT is "cli" and print mode is on, it is set to "sdk-cli" (byte-verified in raw/static-excerpts.txt)
cheapest_model: haiku, tier 0 of haiku/sonnet/opus/fable-mythos (X05, byte-verified in raw/static-excerpts.txt)
auth_ladder: X01 -- claude.ai token source gives "claude.ai"; apiKeyHelper gives "api_key_helper"; any other token source gives "oauth_token"; ANTHROPIC_API_KEY gives "api_key"; "/login managed key" gives "claude.ai" with apiKeySource set (byte-verified in raw/static-excerpts.txt)
auth_status_fields: X02 -- loggedIn, authMethod, apiProvider, analyticsDisabled, projectsDirectory, configDirectory, plus forcedLoginMethod/apiKeySource when set, and email/orgId/orgName/subscriptionType for claude.ai auth (byte-verified in raw/static-excerpts.txt)

### 0b. Global-file bracket

B0_settings_json_sha256: 886b884375f2b12d31b7db6b387d8f747d235a7830b201ff32b06c3d8b8d871a
B0_claude_md_sha256: 31442ce249ed910c9bb601d442e8baf7c1417f918e6b069cbac17545c8a35152
B0_credentials_stat: size=524 mtime=1790590674
B0_user_rules_dir: ABSENT

### 0c. Tracer (fake claude, zero model calls)

selftest_tracer: ABRUN_SELFTEST_PASS=7/7  threshold=7/7
tracer_fake_run: A1 fake -> transcript located by session id (decoy ignored) -> tis_observed first-call figures -> MATCH

## 1. Pre-registration (committed before any counted run)

runner_sha256: 9414fd25dcf2b3517d477144fff7288d026cc01bcc79548fab5b5675a4f5bac0
rules_fingerprint: ab6454cd4087923d49c198d78588f4128388ad4d5745f0ec35bcdde87b1c07ea
thresholds: GAP_SUPPORT=0.3 B2_FLOOR=0.5 GAP_NULL=0.1 MISS_BAND=0.5 TTL_5M_BOUND_S=240 TTL_1H_BOUND_S=3300 REPLACEMENT_BUDGET=0
prompt: Reply with the single word OK.
model: haiku
argv_A: EXE -p 'Reply with the single word OK.' --model haiku --session-id SID --output-format stream-json --verbose
argv_B: EXE -p 'Reply with the single word OK.' --model haiku --session-id SID --output-format stream-json --verbose --strict-mcp-config --mcp-config /tmp/claude-1000/cro-p04-ab/empty-mcp.json
scratch_root: /tmp/claude-1000/cro-p04-ab
cwd_A: /tmp/claude-1000/cro-p04-ab/armA
cwd_B: /tmp/claude-1000/cro-p04-ab/armB
project_key_A: -tmp-claude-1000-cro-p04-ab-armA
project_key_B: -tmp-claude-1000-cro-p04-ab-armB
run_order: A1 A2 B1 B2
run_timeout_s: 240

hypothesis_operational: With the default MCP configuration, a second identical back-to-back `claude -p` session reuses materially less of its startup prefix from cache than the same pair with MCP stripped. In addition, Arm A's MCP surface (its init tool-name set or its MCP server status map) differs between its two sessions.
scratch_justification: S (/tmp/claude-1000/cro-p04-ab) is outside /home/kobii/.claude and outside every repo, so no repo CLAUDE.md chain, .claude settings, hooks or a moving `git status` leak into the prefix under test. It is owner-only, not a git repo, uniquely named, and outside every other mission's directory. It is left in place afterwards (OS-reclaimed /tmp) because its LIVE-LATCH is part of the rerun guard.
env_rule: The runner's environment minus every variable whose name starts with CLAUDE. ANTHROPIC_* (any) and BLOCKING_ENV (CLAUDE_CODE_OAUTH_TOKEN, CLAUDE_CONFIG_DIR, CLAUDE_CODE_USE_BEDROCK, CLAUDE_CODE_USE_VERTEX, CLAUDE_CODE_USE_FOUNDRY) are refused before launch at G1, never scrubbed; scrubbed_env() raises rather than strip one. Every other CLAUDE* name (the executor's own coupling variables) is scrubbed, never blocking.
metric: s = first_call_cache_read / first_call_context, where context = input + cache_creation + cache_read, both from tis_observed.read_session's SessionUsage fields (cache_creation 5m/1h split from the first call's own usage.cache_creation). Rounded to 6 dp. Per arm, delta = s2 - s1. gap_run2 = s_B2 - s_A2. delta_gap = delta_B - delta_A.
validity_rules: VR1 rc 0 and not timed out. VR2 exactly one `<id>.jsonl` match for the run's session id. VR3 read_session state MEASURED with first_call_context above 0. VR4 entrypoint sdk-cli. VR5 first-call model contains "haiku" and equals A1's. VR6 init apiKeySource none or absent when an init event is present. VR7 (run 2 only) the gap from run 1's last call ts to run 2's first call ts lies within [0, TTL bound] and both fall on the same host-local date; an unknown timestamp fails VR7.
manipulation_checks: M1 (Arm B stripped MCP) PASS iff both B init events are present with an empty mcp_servers list and no tool name starting mcp__; FAIL if either shows one; UNKNOWN otherwise. M2 (Arm A had MCP to vary) PASS iff A1 or A2 init lists at least one MCP server, in any status; FAIL iff both inits are present and list none; UNKNOWN otherwise. vA YES iff both A inits are present and their tools_sha256 or sorted (name,status) server lists differ; NO iff both present and equal; UNKNOWN otherwise.
ttl_rule: TTL bound is 3300s when run 1's first call wrote only 1h cache (ephemeral_1h above 0 and ephemeral_5m equal 0), otherwise 240s.
verdict_rule: R1 a pre-check or live guard refused -> UNJUDGED (BLOCKED: guard), launches 0. R2 any run INVALID, launches not 4, or the result incomplete -> UNJUDGED (invalid: runs + rule ids). R3 M1 not PASS -> UNJUDGED (manipulation: Arm B MCP strip not confirmed). R4 M2 not PASS -> UNJUDGED (no MCP server in Arm A's default configuration; arms not differentiated). R5 gap_run2 at least 0.3, s_B2 at least 0.5, and vA YES -> SUPPORTED. R6 absolute gap_run2 below 0.1, with s_A2 and s_B2 both below 0.5 -> REFUTED (both-miss). R7 absolute gap_run2 below 0.1 and vA YES -> REFUTED (variance-without-miss). R8 otherwise UNJUDGED, naming exactly one of: similar-reuse-variance-not-observed, B2-below-floor, gap-without-observed-variance, intermediate-gap, A-above-B.
replacement_budget: 0
replacement_budget_reason: ROADMAP criterion 2 fixes exactly 4 runs, so the P3 protocol's "max 2 replacements" is not used; a failed or timed-out run is recorded and the next run launches anyway.
version_drift_rule: All four runs use one sha256-pinned resolved binary. If the resolved version at the live run differs from the one recorded at pre-registration, record claude_version_drift:. The verdict is then scoped to the at-run version; drift does not invalidate the runs.
readout_recovery_rule: The only path to change ab_runner.py after pre-registration. If the runner fails AFTER launches (ab-live.json has complete: false), fix only the readout defect, adding a failing selftest case first. rules_fingerprint must stay byte-identical. Record runner_post_registration_diff: with the reason, then run --readout ... --write, which makes zero model calls.
n_limit_statement: n=2 runs per arm, i.e. one run-2 reuse observation per arm. No variance estimate is possible. One back-to-back pair can neither bound how often MCP tool-list variance occurs nor exclude a one-off cache eviction. The verdict describes GEX44, the at-run claude version and this MCP configuration at the recorded live window, not the laptop.
selftest: ABRUN_SELFTEST_PASS=14/14  threshold=14/14

## 2. Runs (ROADMAP criteria 2-3)

source: GEX44 transcripts, not the laptop's, read by session id through tools/tis_observed.py and never from CLI stdout.
preregistration_commit: 740b41b5f1b47cfc955f32b50974dbbf6ecaff6c 2026-09-28T16:40:50+02:00
live_window_utc: 2026-09-28T14:41:42Z .. 2026-09-28T14:42:07Z
launches: 4
runner_sha256_at_run: 9414fd25dcf2b3517d477144fff7288d026cc01bcc79548fab5b5675a4f5bac0
rules_fingerprint_at_run: ab6454cd4087923d49c198d78588f4128388ad4d5745f0ec35bcdde87b1c07ea
claude_at_run: /home/kobii/.local/share/claude/versions/2.1.283 1859583ce32920595c61ef868bee52e1b1594f7486db209935e01f1e5e804ae2
claude_version_drift: none

### A1 (Arm A, run 1; GEX44 transcript, not the laptop's)

A1_session_id: ac93009b-5638-4c4c-bf4d-7c4fb717576a
A1_sid_source: preassigned
A1_transcript: -tmp-claude-1000-cro-p04-ab-armA/ac93009b-5638-4c4c-bf4d-7c4fb717576a.jsonl (matches 1, project_key_match YES)
A1_rc: 0
A1_timed_out: false
A1_start_utc: 2026-09-28T14:41:42Z
A1_end_utc: 2026-09-28T14:41:51Z
A1_state: MEASURED
A1_entrypoint: sdk-cli
A1_calls: 1 (GEX44)
A1_model: claude-haiku-4-5-20251001
A1_first_call_input_tokens: 10 (GEX44)
A1_first_call_cache_read_input_tokens: 13689 (GEX44)
A1_first_call_context: 29205 (GEX44)
A1_first_call_cache_creation_input_tokens: 15506 (5m 0 / 1h 15506) (GEX44)
A1_reuse_share: 0.468721 (GEX44)
A1_init: tools 84, mcp_tools 51, mcp_servers [claude.ai Claude Docs:connected, claude.ai Gmail:connected, claude.ai Google Calendar:needs-auth, claude.ai Google Drive:connected, plugin:context7:context7:connected], apiKeySource none
A1_valid: VALID

### A2 (Arm A, run 2; GEX44 transcript, not the laptop's)

A2_session_id: 5d38ef4d-1d61-4523-9fea-59ad61c6755d
A2_sid_source: preassigned
A2_transcript: -tmp-claude-1000-cro-p04-ab-armA/5d38ef4d-1d61-4523-9fea-59ad61c6755d.jsonl (matches 1, project_key_match YES)
A2_rc: 0
A2_timed_out: false
A2_start_utc: 2026-09-28T14:41:51Z
A2_end_utc: 2026-09-28T14:41:57Z
A2_state: MEASURED
A2_entrypoint: sdk-cli
A2_calls: 1 (GEX44)
A2_model: claude-haiku-4-5-20251001
A2_first_call_input_tokens: 10 (GEX44)
A2_first_call_cache_read_input_tokens: 29195 (GEX44)
A2_first_call_context: 29205 (GEX44)
A2_first_call_cache_creation_input_tokens: 0 (5m 0 / 1h 0) (GEX44)
A2_reuse_share: 0.999658 (GEX44)
A2_init: tools 84, mcp_tools 51, mcp_servers [claude.ai Claude Docs:connected, claude.ai Gmail:connected, claude.ai Google Calendar:needs-auth, claude.ai Google Drive:connected, plugin:context7:context7:connected], apiKeySource none
A2_valid: VALID

### B1 (Arm B, run 1; GEX44 transcript, not the laptop's)

B1_session_id: 91b4f044-511b-416b-ba87-07557abd7bf0
B1_sid_source: preassigned
B1_transcript: -tmp-claude-1000-cro-p04-ab-armB/91b4f044-511b-416b-ba87-07557abd7bf0.jsonl (matches 1, project_key_match YES)
B1_rc: 0
B1_timed_out: false
B1_start_utc: 2026-09-28T14:41:57Z
B1_end_utc: 2026-09-28T14:42:03Z
B1_state: MEASURED
B1_entrypoint: sdk-cli
B1_calls: 1 (GEX44)
B1_model: claude-haiku-4-5-20251001
B1_first_call_input_tokens: 10 (GEX44)
B1_first_call_cache_read_input_tokens: 13689 (GEX44)
B1_first_call_context: 27627 (GEX44)
B1_first_call_cache_creation_input_tokens: 13928 (5m 0 / 1h 13928) (GEX44)
B1_reuse_share: 0.495494 (GEX44)
B1_init: tools 30, mcp_tools 0, mcp_servers [], apiKeySource none
B1_valid: VALID

### B2 (Arm B, run 2; GEX44 transcript, not the laptop's)

B2_session_id: 0cff6d2e-90d4-40b1-af98-d71487e342d4
B2_sid_source: preassigned
B2_transcript: -tmp-claude-1000-cro-p04-ab-armB/0cff6d2e-90d4-40b1-af98-d71487e342d4.jsonl (matches 1, project_key_match YES)
B2_rc: 0
B2_timed_out: false
B2_start_utc: 2026-09-28T14:42:03Z
B2_end_utc: 2026-09-28T14:42:07Z
B2_state: MEASURED
B2_entrypoint: sdk-cli
B2_calls: 1 (GEX44)
B2_model: claude-haiku-4-5-20251001
B2_first_call_input_tokens: 10 (GEX44)
B2_first_call_cache_read_input_tokens: 27617 (GEX44)
B2_first_call_context: 27627 (GEX44)
B2_first_call_cache_creation_input_tokens: 0 (5m 0 / 1h 0) (GEX44)
B2_reuse_share: 0.999638 (GEX44)
B2_init: tools 30, mcp_tools 0, mcp_servers [], apiKeySource none
B2_valid: VALID

## 3. Cross-arm comparison (ROADMAP criterion 3)

s_A1: 0.468721 (GEX44)
s_A2: 0.999658 (GEX44)
s_B1: 0.495494 (GEX44)
s_B2: 0.999638 (GEX44)
delta_A: 0.530937 (GEX44)
delta_B: 0.504144 (GEX44)
gap_run2: -2e-05 (GEX44)
delta_gap: -0.026793 (GEX44)
ttl_A: gap_s 5.179 bound_s 3300 same_local_date True
ttl_B: gap_s 4.783 bound_s 3300 same_local_date True
vA: NO (A1 and A2 init tools_sha256 and mcp_servers are identical)
M1: PASS
M2: PASS
comparison: run-2 against run-1 reuse in Arm A moved by 0.530937, in Arm B by 0.504144; the arms differ by gap_run2=-2e-05 in run-2 reuse, with vA=NO. Both arms' second run reached near-total cache reuse (99.97% Arm A, 99.96% Arm B) regardless of MCP configuration, and Arm A's MCP tool list and server statuses were byte-identical between A1 and A2 -- the tool-list surface simply did not vary in this observation.

## 4. Verdict (ROADMAP criterion 4, CRO-04)

verdict: UNJUDGED (similar-reuse-variance-not-observed)
rule_fired: R8
n_limit: n=2 runs per arm, i.e. one run-2 reuse observation per arm. No variance estimate is possible. One back-to-back pair can neither bound how often MCP tool-list variance occurs nor exclude a one-off cache eviction. The verdict describes GEX44, the at-run claude version and this MCP configuration at the recorded live window, not the laptop.
host_scope: GEX44 transcripts, not the laptop's; claude 2.1.283 (Claude Code); default MCP configuration for Arm A (claude.ai Claude Docs/Gmail/Google Calendar/Google Drive plus plugin:context7:context7) and --strict-mcp-config with an empty MCP config file for Arm B, at the recorded live window.
claude_version_end: 2.1.283 (Claude Code)
claude_resolved_end: /home/kobii/.local/share/claude/versions/2.1.283
B2_settings_json_sha256: 886b884375f2b12d31b7db6b387d8f747d235a7830b201ff32b06c3d8b8d871a
B2_claude_md_sha256: 31442ce249ed910c9bb601d442e8baf7c1417f918e6b069cbac17545c8a35152
B2_credentials_stat: size=524 mtime=1790590674
B2_user_rules_dir: ABSENT
global_bracket: UNCHANGED
credentials_note: the credential file is stat-ed only, never opened, read, copied or linked; claude may rewrite it on its own token refresh during the live window, but the B0 and B2 stat values here are byte-identical (size=524 mtime=1790590674), so no rewrite occurred during this run.
corpus_side_effect: 4 sdk-cli haiku sessions now sit under project keys -tmp-claude-1000-cro-p04-ab-armA and -tmp-claude-1000-cro-p04-ab-armB, which future GEX44 baselines should exclude.
phase_status: DONE
cro04: SATISFIED
constraints_honoured: ANTHROPIC_API_KEY UNSET throughout (subscription claudeAiOauth only); exactly 4 runs launched via one --live invocation with no retry or replacement (REPLACEMENT_BUDGET 0); nothing written under /home/kobii/.claude by this plan (only claude's own transcripts, plus its own possible credential refresh -- none occurred here); no tools/modules/vault/ROADMAP/STATE edit by this plan; explicit-pathspec commits only, no push; no reply text committed (raw/ab-live.json's json.dumps carries no result/text/content/message/stdout/email/orgId/orgName key).
next: The tool-list did not vary between A1 and A2 in this observation (vA NO -- Arm A's mcp_servers and tools_sha256 were identical across both runs, including the Google Calendar server sitting at needs-auth in both), so the cache-miss-from-MCP-variance hypothesis was not exercised by this run; both arms independently showed near-total run-2 cache reuse (~99.96-99.97%) regardless of MCP configuration, meaning no miss was observed to attribute to MCP variance or to anything else. Phase 5 should record this as UNJUDGED (similar-reuse-variance-not-observed) in RESUMPTION/UKDL, note CRO-04 is judged (not BLOCKED) with this specific outcome, and note that a future re-run of this harness would need the MCP surface to actually change between run 1 and run 2 (for example an auth-status flip or a plugin toggle) to exercise R5-R7 at all. This run establishes ab_runner.py and the tis_observed-based readout end-to-end against real subscription quota.
