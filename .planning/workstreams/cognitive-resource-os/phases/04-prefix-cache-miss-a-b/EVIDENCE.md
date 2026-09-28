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
