# C9 retirements (2026-10-13)

## R1 rule: "Bash is not the default on Windows" bullet in ~/.claude/CLAUDE.md
- Enforced by: windows-bash-bridge-guard.js (PreToolUse Bash). Live test: hooks/_tests/test-bash-bridge-guard-v15.js, 31/31 (blocks git, pytest, python heredoc, grep, sed, tail; kill switch; fail-open).
- Removed: 213 chars net (399-char bullet replaced by a 186-char one-line pointer). File 19502 -> 19289 chars.
- Backup: C:\Users\User\.claude\backups\cdc-20261013-074826\CLAUDE.md
- Revert: Copy-Item C:\Users\User\.claude\backups\cdc-20261013-074826\CLAUDE.md C:\Users\User\.claude\CLAUDE.md -Force
- Not retired (guard absent or untested): run_in_background SOLO, batch caps, "every turn ends with text" (closer-guard has no test of that exact sentence), subagent <=2.
- Lost by retirement: the literal python/git PowerShell paths; the guard block message delivers them (see "PowerShell equivalent" in its output). If the guard is killed (CLAUDE_BASH_GUARD=off) the model no longer has them in prose.

## R2 role: green-path reviewer
- Replaced by: tools/tier_routing.review_policy (C5): reviewer skipped only when the unit is deterministic AND all affected suites are green; red/unobserved/non-deterministic -> reviewer. Tests: tools/test_tier_routing.py 15/15 (C5 receipt).
- Retired role: an LLM reviewer pass on a deterministic, fully green landing. Reinstated automatically by the policy on any red/unobserved.
- Revert: set the policy to always-review (no code path removed; the reviewer role itself still exists).
- NOT_PROVEN: that the live landing flow calls review_policy at every landing (C5 receipt: adoption not forced).
