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
model_calls: 0

## 2. Candidate mechanisms (ROADMAP criterion 1)

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

## 3. Judgement against the P0 clause (ROADMAP criterion 2)

p0_clause: P0 How to run arm B without R and WITHOUT editing the Owner's global config or copying credentials. Candidates to test, in order: a `--setting-sources` / settings flag that skips user rules (verify it affects rules, not only settings); a per-run config dir only if it can reuse auth without copying the credential file. If none works: STOP, report, do not improvise.
rule: Judge each candidate block by testing its seven graded properties in this fixed order -- credential (must be NONE_NEEDED), global_edit (must be NONE), auth_path (must be OAUTH_UNCHANGED), transcripts_visible (must be YES), rules_effect (must be EXCLUDES_R1_ONLY), other_prefix_changes (must be NONE), evidence_tier (must be E1+E2) -- and write REJECTED at the first property in that order that fails to hold, naming that property. A block that holds on every one of the seven is ACCEPTABLE. The verdict (section 4) is PASS with the lowest-numbered ACCEPTABLE block's mechanism verbatim, or STOP when no block is ACCEPTABLE (or the API key is set, or the installed version changed between start and end).
judgement[C01]: REJECTED (rules_effect) the excerpts show --setting-sources without "user" drops the entire user rules directory (all ~22 files, not just R1's three) plus user CLAUDE.md and user-sourced skills/agents/commands (X04, X05, X06, X07) -- EXCLUDES_MORE_THAN_R1, not EXCLUDES_R1_ONLY.
