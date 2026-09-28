# Phase 03 EVIDENCE -- P3 pre-flight P0 (zero model calls)

This file judges candidate mechanisms from the installed claude's own help text and static reading of its binary on GEX44; no model call and no arm was run to produce it.

## 0. Pre-checks

ANTHROPIC_API_KEY: UNSET
head: 1a22c739772957d500ce318c9d2fa8f465669374
branch: mission/cognitive-resource-os-gex44
measured_at_utc: 2026-09-28T13:36:41Z
claude_path: /home/kobii/.local/bin/claude
claude_resolved: /home/kobii/.local/share/claude/versions/2.1.283
claude_version: 2.1.283 (Claude Code)
binary_bytes: 241556664
binary_sha256: 1859583ce32920595c61ef868bee52e1b1594f7486db209935e01f1e5e804ae2

### 0a. Host facts relevant to P0

user_rules_dir: ABSENT
worktree_rules_dir: ABSENT
r1_files_in_user_rules: 0 of 3
prefix_inventory_rc: 0
prefix_inventory_rule_files: 0 (rule=0, rule_scoped=0; from modules/token-optimizer/prefix_inventory.py --json, by_kind)
prefix_inventory_unconditional_tokens_est: 26114 (ESTIMATE, GEX44 files; bytes/3.8, no tokenizer offline)
host_note: /home/kobii/.claude/rules does not exist on GEX44, and this worktree has no .claude/rules either. None of R1's three files (instrument-before-claim, destructive-state-authorization, real-context-reachability) is present. So on this host, arm A's own prefix does not contain R1 at all -- the ablation as defined cannot be run on GEX44 regardless of the P0 verdict below. This matches the planning-time facts recorded in 03-01-PLAN.md (re-measured here, not copied).

### 0b. Global-file bracket

B0_settings_json_sha256: 886b884375f2b12d31b7db6b387d8f747d235a7830b201ff32b06c3d8b8d871a
B0_claude_md_sha256: 31442ce249ed910c9bb601d442e8baf7c1417f918e6b069cbac17545c8a35152
B0_user_rules_dir: ABSENT
B0_credentials_stat: size=524 mtime=1790590674
B1_settings_json_sha256: 886b884375f2b12d31b7db6b387d8f747d235a7830b201ff32b06c3d8b8d871a
B1_claude_md_sha256: 31442ce249ed910c9bb601d442e8baf7c1417f918e6b069cbac17545c8a35152
B1_user_rules_dir: ABSENT
B1_credentials_stat: size=524 mtime=1790590674

## 1. Invocation log

- inv01: timeout 30 /home/kobii/.local/bin/claude --version -> raw/claude-version.txt rc=0
- inv02: timeout 30 /home/kobii/.local/bin/claude --help -> raw/claude-help.txt rc=0
- inv03: timeout 30 /home/kobii/.local/bin/claude auth --help -> raw/claude-subcommand-help.txt rc=0
- inv04: timeout 30 /home/kobii/.local/bin/claude auth login --help -> raw/claude-subcommand-help.txt rc=0
- inv05: timeout 30 /home/kobii/.local/bin/claude auth status --help -> raw/claude-subcommand-help.txt rc=0
- inv06: timeout 30 /home/kobii/.local/bin/claude setup-token --help -> raw/claude-subcommand-help.txt rc=0
- inv07: timeout 30 /home/kobii/.local/bin/claude doctor --help -> raw/claude-subcommand-help.txt rc=0
- inv08: timeout 30 /home/kobii/.local/bin/claude --version -> raw/claude-version-end.txt rc=0
model_calls: 0

## 2. Candidate mechanisms (ROADMAP criterion 1)

### 2a. Discovery (coverage by construction)

discovery_help_flags: 15 (raw/discovered-surface.txt section H)
discovery_env_vars: 22 (raw/discovered-surface.txt section E)
discovery_settings_keys: 3 (raw/discovered-surface.txt section S)
discovery_rule: raw/discovered-surface.txt sections H, E, S (fixed scans of 03-01-PLAN Task 2)
- triage[--agent]: NOT_P0 (help: "Agent for the current session. Overrides the 'agent' setting." -- selects an agent profile, does not change which memory/rule files load)
- triage[--append-system-prompt]: CANDIDATE C10
- triage[--bare]: CANDIDATE C06
- triage[--client-data-url]: NOT_P0 (help: "URL for a signed configuration document" -- model/config-document selection, unrelated to CLAUDE.md/rules loading)
- triage[--exclude-dynamic-system-prompt-sections]: NOT_P0 (help: moves per-machine sections cwd/env-info/memory-paths/git-status into the first user message; relocates where memory PATHS text is sent, does not drop memory CONTENT)
- triage[--mcp-config]: NOT_P0 (help: "Load MCP servers from JSON files or strings" -- MCP tool config, no relation to CLAUDE.md/rules)
- triage[--print]: NOT_P0 (run-mode flag for non-interactive output; also outside this phase's own invocation allowlist; does not change which memory/rule files load)
- triage[--restricted]: CANDIDATE C08
- triage[--safe-mode]: CANDIDATE C07
- triage[--setting-sources]: CANDIDATE C01
- triage[--settings]: CANDIDATE C02
- triage[--strict-mcp-config]: NOT_P0 (help: "Only use MCP servers from --mcp-config" -- MCP-only)
- triage[--system-prompt]: CANDIDATE C09
- triage[--system-prompt-snapshot]: NOT_P0 (help: records/reuses whatever prompt text is produced; does not itself change which files are read into that text)
- triage[--verbose]: NOT_P0 (help: "Override verbose mode setting from config" -- logging verbosity only)
- triage[CLAUDE_BG_SESSION_PERMISSION_RULES]: NOT_P0 (name denotes background-session tool PERMISSION rules, a different "rules" concept from the ~/.claude/rules memory files judged here)
- triage[CLAUDE_BRIDGE_OAUTH_TOKEN]: NOT_P0 (an OAuth bridge/device-pairing token; auth-adjacent, not a memory/rules-loading control)
- triage[CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD]: NOT_P0 (controls whether --add-dir directories also contribute their own CLAUDE.md -- an addition, not a way to drop the user's own ~/.claude/rules content)
- triage[CLAUDE_CODE_BRIDGE_CHILD_MACHINE_SETTINGS]: NOT_P0 (multi-machine bridge settings sync; unrelated to a single run's own rules loading)
- triage[CLAUDE_CODE_COORDINATOR_PROPAGATE_NESTED_MEMORY]: NOT_P0 (propagates memory INTO nested/coordinated sub-sessions; controls what a spawned session inherits, not whether the top-level arm itself loads R1)
- triage[CLAUDE_CODE_DISABLE_AUTO_MEMORY]: NOT_P0 (disables the auto-generated project MEMORY.md, a distinct kind from rule/rule_scoped per prefix_inventory.py's own APERTURE note)
- triage[CLAUDE_CODE_DISABLE_CLAUDE_MDS]: CANDIDATE C11
- triage[CLAUDE_CODE_DISABLE_HOME_SETTINGS_SEED]: NOT_P0 (a first-run/install-time seeding toggle for creating the home settings file, not a per-run suppression of already-installed rules)
- triage[CLAUDE_CODE_DISABLE_ORG_MEMORY]: NOT_P0 (org/managed-level memory, not the user's own rules dir)
- triage[CLAUDE_CODE_FLEETVIEW_SIMPLE]: NOT_P0 (a fleet-dashboard UI toggle, matched the scan only via its SIMPLE suffix; unrelated to memory loading)
- triage[CLAUDE_CODE_FORCE_EVALUATE_MEMORY]: NOT_P0 (forces re-evaluation/refresh of memory state, not an exclusion mechanism)
- triage[CLAUDE_CODE_HIDE_SETTINGS_HINT]: NOT_P0 (a UI hint-visibility toggle, cosmetic only)
- triage[CLAUDE_CODE_MANAGED_SETTINGS_PATH]: NOT_P0 (path override for the MANAGED/policy settings source, not the userSettings source R1 lives under; X08 shows Managed/policy files cannot even be excluded via claudeMdExcludes)
- triage[CLAUDE_CODE_MOCK_REMOTE_SETTINGS]: NOT_P0 (a test/mock toggle for remote-settings polling, dev-only)
- triage[CLAUDE_CODE_OAUTH_TOKEN]: NOT_P0 (supplies an auth token directly; relevant to the credential grading of C04/C05, not itself a rules-loading gate)
- triage[CLAUDE_CODE_POST_TURN_MEMORY]: NOT_P0 (timing control for auto-memory writes, not rules)
- triage[CLAUDE_CODE_REMOTE_SETTINGS_PATH]: NOT_P0 (remote/managed settings source path, not user rules)
- triage[CLAUDE_CODE_REMOTE_SETTINGS_POLL_MS]: NOT_P0 (polling interval for remote settings, unrelated to which files load)
- triage[CLAUDE_CODE_SAFE_MODE]: CANDIDATE C07
- triage[CLAUDE_CODE_SIMPLE]: CANDIDATE C06
- triage[CLAUDE_CONFIG_DIR]: CANDIDATE C04
- triage[CLAUDE_SECURESTORAGE_CONFIG_DIR]: NOT_P0 (a config dir specifically for the secure-storage/credential backend, distinct from CLAUDE_CONFIG_DIR; credential-adjacent, not a rules-relocation mechanism)
- triage[claudeMd]: NOT_P0 (describe text: "CLAUDE.md-style instructions injected as organization-managed memory. Only honored from managed/policy settings." -- an addition mechanism with no exclusion effect, and unsettable from user/project/local sources)
- triage[claudeMdExcludes]: CANDIDATE C02
- triage[omitClaudeMd]: NOT_P0 (describe text: "If true, the agent runs without the user, project and local CLAUDE.md files" -- a per-subagent field used with --agents JSON, scoped to a spawned custom agent rather than the top-level arm B session itself, and it names CLAUDE.md only, not rules)

### 2b. Candidate blocks

### C01 --setting-sources
- mechanism: --setting-sources project,local (the arm B invocation; the "user" source name is the one omitted from the comma-separated list)
- source: help:--setting-sources (raw/claude-help.txt); CLI-to-config mapping X02
- changes: --setting-sources takes a comma-separated allowlist of sources to load (user, project, local; raw/claude-help.txt). Omitting "user" turns the installed version's `ar("userSettings")` check false everywhere that check gates a load. The static trace (X04, X05) shows the user-level CLAUDE.md path (De) and the user-level rules dir (Ne) are BOTH added to the merged memory/rules file list only inside one `Bt` branch, and `Bt=Ie&&g===void 0&&HSe(_t,Oe)` requires `Ie` (=`ar("userSettings")`). The same source check also gates a separate, generic per-kind loader (X07) used for user-sourced agents/skills/commands, keyed by `source:"userSettings"`.
- touches_on_disk: with "user" omitted, the installed version stops reading ~/.claude/settings.json (X03: "User settings (~/.claude/settings.json)"), ~/.claude/CLAUDE.md, all of ~/.claude/rules/*.md (X06: `function oFe(){return De(Se(),"rules")}`, i.e. Ne resolves to `<home>/rules`), and user-level skills/agents/commands directories (X07). Writes nothing; this is a read-time filter.
- rules_effect: EXCLUDES_MORE_THAN_R1
- evidence_tier: E1+E2
- evidence: help:"--setting-sources <sources> Comma-separated list of setting sources to load (user, project, local)." (raw/claude-help.txt); X01 X02 X03 X04 X05 X06 X07; identifier_hop[oFe]=1 (function oFe( occurs once in the binary, per X06's identifier_hop line)
- credential: NONE_NEEDED
- global_edit: NONE
- auth_path: OAUTH_UNCHANGED
- other_prefix_changes: user CLAUDE.md, user settings.json, and user-sourced skills/agents/commands are all also excluded when "user" is omitted (X04, X05, X07) -- not limited to the three R1 rule files
- transcripts_visible: YES

### C02 --settings (claudeMdExcludes)
- mechanism: --settings {"claudeMdExcludes":["/home/kobii/.claude/rules/instrument-before-claim.md","/home/kobii/.claude/rules/destructive-state-authorization.md","/home/kobii/.claude/rules/real-context-reachability.md"]}
- source: help:--settings (raw/claude-help.txt); binary describe text X08
- changes: claudeMdExcludes accepts absolute paths or globs that are matched, after backslash normalisation, against files tagged User/Project/Local (X09). Supplying only this one key via --settings contributes it through the flagSettings source; every other value keeps whatever the enabled sources already provide. The matcher is wired directly as excludeMatcher:ye into the walk of the type:"User" rules directory (X10), and the schema's own describe text explicitly gives a .claude/rules/** glob as an example (X08) -- so this key is honored for rule files, not only CLAUDE.md files, despite its name.
- touches_on_disk: still reads ~/.claude/rules/*.md (X10: walks rulesDir:Ne=oFe()="<home>/rules" for type:"User"), but the three named files are filtered out by the matcher before being added to the prefix. The other 19 rule files, user CLAUDE.md, the rest of user settings.json, and user-level skills/agents/commands are unaffected -- no exclude pattern matches them. Writes nothing; --settings is CLI-ephemeral, not written to ~/.claude/settings.json.
- rules_effect: EXCLUDES_R1_ONLY
- evidence_tier: E1+E2
- evidence: help:"--settings <file-or-json> Path to a settings JSON file or a JSON string to load additional settings from" (raw/claude-help.txt); X08 (describe text incl. .claude/rules/** example); X09 (matcher construction, User/Project/Local scope, backslash normalisation); X10 (excludeMatcher:ye wired into the type:"User" rulesDir walk, same scope as X04/X05 -- shared Ne/Vt/tt/We); identifier_hop[pZe]=2(byte-identical dup, see X09); identifier_hop[FEn]=2(not identical, ye's binding is by local scope not a global hop, see X09/X10 note)
- credential: NONE_NEEDED
- global_edit: NONE
- auth_path: OAUTH_UNCHANGED
- other_prefix_changes: NONE
- transcripts_visible: YES

### C03 claudeMdExcludes in a cwd-scoped settings file
- mechanism: .claude/settings.local.json in the arm's own worktree containing {"claudeMdExcludes":["/home/kobii/.claude/rules/instrument-before-claim.md","/home/kobii/.claude/rules/destructive-state-authorization.md","/home/kobii/.claude/rules/real-context-reachability.md"]}
- source: settings-source table X03 (localSettings/projectSettings names); same claudeMdExcludes key as C02 (X08)
- changes: the same claudeMdExcludes matcher mechanism as C02 (X09), but supplied via a project- or local-scoped settings FILE rather than --settings. localSettings must be enabled for .claude/settings.local.json to be read (ar("localSettings"), on by default; projectSettings analogously for .claude/settings.json). pZe()'s matcher gates on the TYPE of the file being tested (User/Project/Local, X09), not on which source supplied claudeMdExcludes, so a project- or local-scoped value still filters the USER's own rules dir the same way C02's does.
- touches_on_disk: creates a NEW file inside the arm's own worktree (.claude/settings.local.json or .claude/settings.json), not under ~/.claude. Otherwise the same read pattern as C02 (still reads ~/.claude/rules/*.md, minus the three named files).
- rules_effect: EXCLUDES_R1_ONLY
- evidence_tier: E1+E2
- evidence: X03 (localSettings/projectSettings source-name text); X08, X09, X10 (same claudeMdExcludes matcher chain as C02)
- credential: NONE_NEEDED
- global_edit: NONE
- auth_path: OAUTH_UNCHANGED
- other_prefix_changes: the new .claude/settings.local.json (or settings.json) file changes the arm worktree's own git status -- new/untracked relative to arm A's environment, which the session's environment block reports
- transcripts_visible: YES

### C04 CLAUDE_CONFIG_DIR
- mechanism: CLAUDE_CONFIG_DIR=<new empty directory> (env var set for the arm's claude invocation)
- source: binary env-var scan (raw/discovered-surface.txt section E); X11 (Se() reads CLAUDE_CONFIG_DIR)
- changes: Se() -- the config-home function used pervasively (oFe()=rules dir per X06, and the same join-with-".claude" pattern for CLAUDE.md/settings) -- resolves to CLAUDE_CONFIG_DIR when set, else <home>/.claude (X11). Pointing it at a new empty directory means settings.json, CLAUDE.md, the rules dir, and credentials all stop resolving to the Owner's real ~/.claude -- the whole config tree moves, not just R1.
- touches_on_disk: would read (if present) <new-dir>/settings.json, <new-dir>/CLAUDE.md, <new-dir>/rules/*.md, <new-dir>/.credentials.json (X12), and would write session state/transcripts under <new-dir>/projects (X13) instead of ~/.claude/projects.
- rules_effect: EXCLUDES_MORE_THAN_R1
- evidence_tier: E1+E2
- evidence: discovery section E (CLAUDE_CONFIG_DIR); X11, X12, X13
- credential: NEEDS_COPY
- global_edit: NONE
- auth_path: CANNOT_ESTABLISH
- other_prefix_changes: the whole settings/CLAUDE.md/skills/agents/commands source tree moves with it (X11-X13), well beyond R1
- transcripts_visible: NO

### C05 alternate HOME
- mechanism: HOME=<new directory> (env var set for the arm's claude invocation; CLAUDE_CONFIG_DIR left unset)
- source: X11 (Se()'s fallback path when CLAUDE_CONFIG_DIR is unset: u(R(),".claude"))
- changes: structurally the same as C04 -- Se() falls back to R()+"/.claude" when CLAUDE_CONFIG_DIR is unset (X11). R()'s own definition could not be reliably resolved by static grep: "function R(" collides across dozens of unrelated modules in the bundle, so per the excerpt protocol's identifier-hop rule this specific hop is unestablished. The structural role (R(),".claude") parallels X12's D(lt(),".claude") pattern for the credential path's own home fallback, which is consistent with R() being a home-directory getter but is inference from pattern, not a byte-verified hop.
- touches_on_disk: CANNOT_ESTABLISH precisely which files move (same candidate categories as C04, but the exact fallback function is not uniquely traced)
- rules_effect: CANNOT_ESTABLISH_WITHOUT_MODEL_CALL
- evidence_tier: E2
- evidence: X11 (Se() fallback structure); X12 (the parallel D(lt(),".claude") pattern for credentials); identifier_hop[R]=many (not unique; "function R(" collides across dozens of unrelated modules -- link unestablished per the excerpt protocol)
- credential: NEEDS_COPY
- global_edit: NONE
- auth_path: CANNOT_ESTABLISH
- other_prefix_changes: HOME is read by more than claude alone; within claude, the same settings/CLAUDE.md/rules/skills/agents/commands tree as C04 would be affected if R() indeed feeds Se()'s fallback
- transcripts_visible: CANNOT_ESTABLISH

### C06 --bare
- mechanism: --bare (plus explicit --system-prompt-file/--add-dir/--mcp-config/--settings/--agents/--plugin-dir supplied by hand, per its own help text, to restore any needed context)
- source: help:--bare (raw/claude-help.txt)
- changes: help text: "Minimal mode: skip hooks..., LSP, plugin sync, attribution, auto-memory, background prefetches, keychain reads, and CLAUDE.md auto-discovery. Sets CLAUDE_CODE_SIMPLE=1. Anthropic auth is strictly ANTHROPIC_API_KEY or apiKeyHelper via --settings (OAuth and keychain are never read)."
- touches_on_disk: stops auto-discovering CLAUDE.md; auth reads ANTHROPIC_API_KEY or an apiKeyHelper file instead of the OAuth keychain credential (raw/claude-help.txt).
- rules_effect: CANNOT_ESTABLISH_WITHOUT_MODEL_CALL
- evidence_tier: E1
- evidence: help:"--bare Minimal mode: skip hooks..., CLAUDE.md auto-discovery. Sets CLAUDE_CODE_SIMPLE=1. Anthropic auth is strictly ANTHROPIC_API_KEY or apiKeyHelper via --settings (OAuth and keychain are never read)." (raw/claude-help.txt)
- credential: NEEDS_API_KEY
- global_edit: NONE
- auth_path: API_KEY_ONLY
- other_prefix_changes: hooks, LSP, plugin sync, attribution, auto-memory, background prefetches also disabled per the same help text -- far beyond R1
- transcripts_visible: CANNOT_ESTABLISH

### C07 --safe-mode
- mechanism: --safe-mode
- source: help:--safe-mode (raw/claude-help.txt)
- changes: help text: "Start with all customizations (CLAUDE.md, skills, installed plugins, hooks, MCP servers, custom commands and agents, output styles, workflows, custom themes, keybindings, and more) disabled... Admin-managed (policy) settings still apply. Auth, model selection, built-in tools and plugins, and permissions work normally. Sets CLAUDE_CODE_SAFE_MODE=1."
- touches_on_disk: CLAUDE.md is explicitly named as disabled; the rules directory is not separately named but is plausibly covered by the trailing "and more" -- not established either way from text alone.
- rules_effect: EXCLUDES_MORE_THAN_R1
- evidence_tier: E1
- evidence: help:"--safe-mode Start with all customizations (CLAUDE.md, skills, installed plugins, hooks, MCP servers, custom commands and agents, output styles, workflows, custom themes, keybindings, and more) disabled... Sets CLAUDE_CODE_SAFE_MODE=1." (raw/claude-help.txt)
- credential: NONE_NEEDED
- global_edit: NONE
- auth_path: OAUTH_UNCHANGED
- other_prefix_changes: skills, installed plugins, hooks, MCP servers, custom commands and agents, output styles, workflows, themes, keybindings all also disabled (help text) -- far beyond R1
- transcripts_visible: YES

### C08 --restricted
- mechanism: --restricted
- source: help:--restricted (raw/claude-help.txt)
- changes: help text: "removes the built-in tools that run commands or code (Bash, PowerShell, REPL...) and WebFetch unless --tools names them, and ignores user, project and local settings files (managed settings and --settings still apply...). Also confines the file tools..., refuses bypassPermissions, and lets only a person or the configured permission handler approve writes to settings, git and tool-configuration files."
- touches_on_disk: "ignores user, project and local settings files" names settings.json/settings.local.json; the help text never names CLAUDE.md or the rules directory.
- rules_effect: NO_EFFECT_ON_RULES
- evidence_tier: E1
- evidence: help:"--restricted Restricted mode: removes the built-in tools that run commands or code..., and ignores user, project and local settings files (managed settings and --settings still apply...)." (raw/claude-help.txt)
- credential: NONE_NEEDED
- global_edit: NONE
- auth_path: OAUTH_UNCHANGED
- other_prefix_changes: removes Bash/PowerShell/REPL/WebFetch tools and changes the permission-approval model for settings/git/tool-config writes -- a large difference from arm A regardless of rules_effect
- transcripts_visible: YES

### C09 --system-prompt
- mechanism: --system-prompt "<replacement text>" (or --system-prompt-file, named by --bare's help text)
- source: help:--system-prompt (raw/claude-help.txt); --bare's help text listing "--system-prompt[-file]" among the ways to "Explicitly provide context" once auto-discovery is off
- changes: replaces the session's system prompt text outright ("System prompt to use for the session", raw/claude-help.txt). Whether CLAUDE.md/rules content is normally carried inside that system prompt text (so replacing it also drops R1) or injected through a separate channel could not be traced to a specific code excerpt within this task's time budget.
- touches_on_disk: CANNOT_ESTABLISH (no excerpt located showing where CLAUDE.md/rules text is assembled into the request payload)
- rules_effect: CANNOT_ESTABLISH_WITHOUT_MODEL_CALL
- evidence_tier: E1
- evidence: help:"--system-prompt <prompt> System prompt to use for the session" (raw/claude-help.txt); help:"--bare ... Explicitly provide context via: --system-prompt[-file], --append-system-prompt[-file], --add-dir (CLAUDE.md dirs), --mcp-config, --settings, --agents, --plugin-dir." (raw/claude-help.txt; a LEAD only, per the plan's own leads list, not a conclusion)
- credential: NONE_NEEDED
- global_edit: NONE
- auth_path: OAUTH_UNCHANGED
- other_prefix_changes: replaces the entire default system prompt (tone/instructions beyond memory), itself a large, un-scoped difference from arm A regardless of whether it happens to drop R1
- transcripts_visible: YES

### C10 --append-system-prompt
- mechanism: --append-system-prompt "<text>"
- source: help:--append-system-prompt (raw/claude-help.txt)
- changes: "Append a system prompt to the default system prompt" (raw/claude-help.txt) -- additive only.
- touches_on_disk: none; does not remove any existing file from the read set.
- rules_effect: NO_EFFECT_ON_RULES
- evidence_tier: E1
- evidence: help:"--append-system-prompt <prompt> Append a system prompt to the default system prompt" (raw/claude-help.txt)
- credential: NONE_NEEDED
- global_edit: NONE
- auth_path: OAUTH_UNCHANGED
- other_prefix_changes: NONE beyond the appended text itself
- transcripts_visible: YES

### C11 CLAUDE_CODE_DISABLE_CLAUDE_MDS
- mechanism: CLAUDE_CODE_DISABLE_CLAUDE_MDS=1 (env var set for the arm's claude invocation)
- source: binary env-var scan (raw/discovered-surface.txt section E); X14
- changes: X14 shows a loader function (bZe) that returns [] immediately when this var is set, before it would otherwise push both the "Managed" content (g=Wut()) and, when ar("userSettings") is enabled, the "User" rules directory content (h=oFe() -- the same rules-dir function established in X06) via Q9(...). A second loader (_Mn) checks the same var at its own top for project-scoped CLAUDE.md. So this one var, despite its CLAUDE-MDS name, empties the managed content and the entire user rules directory in at least this code path, not just R1's three files.
- touches_on_disk: stops reading the user rules directory entirely (all ~22 files, not just the three R1 files), plus Managed-type content and, via _Mn, project-scoped CLAUDE.md.
- rules_effect: EXCLUDES_MORE_THAN_R1
- evidence_tier: E2
- evidence: X14 (bZe/_Mn both early-return [] on CLAUDE_CODE_DISABLE_CLAUDE_MDS; h=oFe() is the same rules-dir function established in X06)
- credential: NONE_NEEDED
- global_edit: NONE
- auth_path: OAUTH_UNCHANGED
- other_prefix_changes: NONE beyond the memory/rules content itself (X14 does not touch tools/permissions/hooks)
- transcripts_visible: YES

### C12 editing or moving the R1 files under ~/.claude/rules
- mechanism: add `paths:` front-matter to, or relocate, the three R1 files under ~/.claude/rules
- source: ROADMAP.md "Operating constraints (every phase)"; this plan's own C12 definition ("recorded so the direct route has a judgement... never performed")
- changes: would make the three files path-scoped (conditionally loaded) instead of unconditional, or move them elsewhere, directly editing/relocating files under ~/.claude/rules.
- touches_on_disk: writes to ~/.claude/rules/*.md directly.
- rules_effect: EXCLUDES_R1_ONLY
- evidence_tier: E1
- evidence: ROADMAP.md: "Never edit ~/.claude/settings.json, ~/.claude/rules/, ~/.claude/CLAUDE.md or credentials. Never relocate rules."; 03-01-PLAN.md Floor candidates: "C12 is recorded so the direct route has a judgement. It is never performed."
- credential: NONE_NEEDED
- global_edit: EDITS (~/.claude/rules/instrument-before-claim.md, ~/.claude/rules/destructive-state-authorization.md, ~/.claude/rules/real-context-reachability.md)
- auth_path: OAUTH_UNCHANGED
- other_prefix_changes: NONE beyond the three files' own scoping/location
- transcripts_visible: YES

## 3. Judgement against the P0 clause (ROADMAP criterion 2)

p0_clause: P0 How to run arm B without R and WITHOUT editing the Owner's global config or copying credentials. Candidates to test, in order: a `--setting-sources` / settings flag that skips user rules (verify it affects rules, not only settings); a per-run config dir only if it can reuse auth without copying the credential file. If none works: STOP, report, do not improvise.
rule: Judge each candidate block by testing its seven graded properties in this fixed order -- credential (must be NONE_NEEDED), global_edit (must be NONE), auth_path (must be OAUTH_UNCHANGED), transcripts_visible (must be YES), rules_effect (must be EXCLUDES_R1_ONLY), other_prefix_changes (must be NONE), evidence_tier (must be E1+E2) -- and write REJECTED at the first property in that order that fails to hold, naming that property. A block that holds on every one of the seven is ACCEPTABLE. The verdict (section 4) is PASS with the lowest-numbered ACCEPTABLE block's mechanism verbatim, or STOP when no block is ACCEPTABLE (or the API key is set, or the installed version changed between start and end).
judgement[C01]: REJECTED (rules_effect) the excerpts show --setting-sources without "user" drops the entire user rules directory (all ~22 files, not just R1's three) plus user CLAUDE.md and user-sourced skills/agents/commands (X04, X05, X06, X07) -- EXCLUDES_MORE_THAN_R1, not EXCLUDES_R1_ONLY.
judgement[C02]: ACCEPTABLE all seven graded properties hold: NONE_NEEDED / NONE / OAUTH_UNCHANGED / YES / EXCLUDES_R1_ONLY / NONE / E1+E2 (X08-X10 trace claudeMdExcludes through to excludeMatcher:ye on the type:"User" rulesDir walk).
judgement[C03]: REJECTED (other_prefix_changes) the new .claude/settings.local.json (or settings.json) file changes the arm worktree's own git status, a difference from arm A beyond the R1 exclusion itself; every other property (including rules_effect: EXCLUDES_R1_ONLY, same mechanism as C02) holds.
judgement[C04]: REJECTED (credential) X12 shows .credentials.json is read from the same CLAUDE_CONFIG_DIR-relocated directory, so the arm has no credential there without copying it -- exactly the protocol's own stated test for this candidate.
judgement[C05]: REJECTED (credential) graded NEEDS_COPY on the same structural basis as C04's byte-verified finding (X11's Se() fallback parallels X12's credential-path fallback); the P0 clause's own credential prohibition governs even where the exact code path (R()'s definition) is not uniquely traced.
judgement[C06]: REJECTED (credential) the installed version's own help text states --bare forces ANTHROPIC_API_KEY/apiKeyHelper auth (NEEDS_API_KEY), which this workstream's operating constraints forbid outright.
judgement[C07]: REJECTED (rules_effect) the help text names CLAUDE.md itself as disabled alongside a long list of other customizations, so even the narrowest honest reading (EXCLUDES_MORE_THAN_R1) is broader than R1's three files.
judgement[C08]: REJECTED (rules_effect) by its own help text this flag does not touch CLAUDE.md or the rules directory at all (NO_EFFECT_ON_RULES), so it does not achieve what P0 is asking for.
judgement[C09]: REJECTED (rules_effect) whether R1 content rides inside the system prompt at all could not be established from help text or a traced excerpt (CANNOT_ESTABLISH_WITHOUT_MODEL_CALL), and that value cannot carry a PASS per this plan's own must_haves.
judgement[C10]: REJECTED (rules_effect) an additive flag cannot remove R1 by definition (NO_EFFECT_ON_RULES).
judgement[C11]: REJECTED (rules_effect) X14 shows this single var empties the whole user rules directory (and Managed/project CLAUDE.md) together (EXCLUDES_MORE_THAN_R1), not R1's three files alone.
judgement[C12]: REJECTED (global_edit) editing or relocating files under ~/.claude/rules is a global-config edit (EDITS), forbidden outright by the operating constraints and by P0's own clause; not performed.

## 4. Verdict (ROADMAP criterion 3, CRO-03)

claude_version_end: 2.1.283 (Claude Code)
claude_resolved_end: /home/kobii/.local/share/claude/versions/2.1.283
B2_settings_json_sha256: 886b884375f2b12d31b7db6b387d8f747d235a7830b201ff32b06c3d8b8d871a
B2_claude_md_sha256: 31442ce249ed910c9bb601d442e8baf7c1417f918e6b069cbac17545c8a35152
B2_user_rules_dir: ABSENT
B2_credentials_stat: size=524 mtime=1790590674
global_bracket: UNCHANGED
credentials_stat: UNCHANGED
phase_status: COMPLETE
p0_verdict: PASS (--settings {"claudeMdExcludes":["/home/kobii/.claude/rules/instrument-before-claim.md","/home/kobii/.claude/rules/destructive-state-authorization.md","/home/kobii/.claude/rules/real-context-reachability.md"]})
p0_reason: C02 is the lowest-numbered ACCEPTABLE block (C01 was REJECTED at rules_effect). All seven graded properties hold for C02, backed by E1 (claudeMdExcludes' own describe text naming a .claude/rules/** example, X08) and E2 (X09-X10: the matcher is wired as excludeMatcher:ye into the type:"User" rulesDir walk). Every other floor block failed at its own first-checked property: C01/C07/C08/C09/C10/C11 at rules_effect, C03 at other_prefix_changes, C04/C05/C06 at credential, C12 at global_edit.
also_acceptable: none
version_scope: this verdict holds for claude 2.1.283 (Claude Code) as installed on GEX44 (Linux build, binary sha256 1859583ce3292059...). A host running another version must re-run this pre-flight before any counted run. Equivalence of the same version's Windows build is assumed, not measured.
host_applicability: section 0a records ~/.claude/rules ABSENT on GEX44 (0 of 3 R1 files present) and no rule/rule_scoped rows in prefix_inventory. So arm A on GEX44 carries no R1 at all -- this host cannot run the ablation as defined (arm B would have nothing to differ from) regardless of this PASS. The PASS names a mechanism (claudeMdExcludes) for whichever host actually has R1 in its own ~/.claude/rules -- per vault/plans/cognitive-resource-os-RESUMPTION.md section 1, that is the laptop (Windows, repo at C:\Users\User\.claude\skills\claude-power-pack), whose installed claude version is not recorded anywhere in this repo and so is not covered by version_scope above.
runtime_confirmation: none by design (zero model calls); the verdict rests only on the help text and the byte-verified excerpts cited in section 2b
cro03: SATISFIED
constraints_honoured: no model call (model_calls: 0; section 1's inv01-inv08 are all --version/--help forms); no interactive session; no candidate mechanism was exercised (C02 was judged from text and static excerpts only); no ~/.claude write except the plain temp files under TMP; .credentials.json was only stat-ed (sections 0b/4), never opened, copied or linked; no other mission's directory was read; commits used explicit pathspecs; nothing was pushed.
next: Phase 5 carries p0_verdict, version_scope and host_applicability into RESUMPTION and UKDL. The P1 A/A and every counted run wait for subscription quota and the Owner. Arm B-prime (R1 on demand) remains the protocol's separate arm and is not judged here.
