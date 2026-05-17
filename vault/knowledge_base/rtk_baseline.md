# RTK Token-Killer — Power Pack Baseline

**Status:** built + locally committed + empirically verified; **live activation is Owner-gated**; branch push **OVO-blocked** (see end).

## What RTK is

RTK ("Rust Token Killer", `rtk` v0.40.0, MIT, github.com/rtk-ai/rtk) is a
single Rust binary that filters/compresses shell command output before it
reaches the LLM context. It is a per-command output rewriter, **not** an
agent orchestrator or runtime kernel. Empirically measured here: **80.5%**
cl100k token reduction on `git --no-pager log --stat -50`, content preserved.

## Architecture (as built)

| Component | Path | Role |
|-----------|------|------|
| Binary | `~/.claude/bin/rtk.exe` | sha256-pinned v0.40.0 (provenance: `vendor/rtk/UPSTREAM_REF.md`) |
| Hook | `modules/rtk-core/rtk-rewrite.js` | Node PreToolUse rewriter. Reads stdin JSON, runs `rtk rewrite <cmd>`, maps exit 0/1/2/3 to `hookSpecificOutput`. Anchors the emitted command to the **absolute** binary path (`~/.claude/bin` is not on PATH). Fail-open on any parse/spawn/timeout error. |
| Registrar | `tools/settings_merger.py register-pretool` | Backup-safe (`.bak` + bounded-diff rollback) PreToolUse append with `matcher` injection. Verified: 12 to 13, append-only, idempotent, live file byte-identical when run against a temp copy. |
| DONE gate | `tools/verify_rtk_fusion.py` | Exercises the real hook path (synthetic PreToolUse JSON, hook, raw vs rewritten, tiktoken cl100k delta). PASS at or above 60% / WARN 0-60% / FAIL at or below 0% or under 50 tok (resolution-failure guard). |
| Agents | `vendor/rtk/agents/{rtk-testing-specialist,rust-rtk}.md` | Optional specialists; cold-load — require `/restart` after Owner copy. |

## Compliance line (CLAUDE.md)

"RTK proxy must be active/available." Deliberately **no numeric 80.5%
assertion** as a universal — that ratio is command/repo specific; forcing it
across unrelated features would be a false universal (Owner directive Q6).

## Owner activation (auto-mode denies agent self-persistence — these are Owner `!`-lines)

```
! python "C:/Users/User/.claude/skills/claude-power-pack/tools/settings_merger.py" register-pretool --node-script "C:/Users/User/.claude/skills/claude-power-pack/modules/rtk-core/rtk-rewrite.js" --matcher Bash --timeout 10
! cp "C:/Users/User/.claude/skills/claude-power-pack/vendor/rtk/agents/"*.md "C:/Users/User/.claude/agents/"
```
…then `/restart`; verify with `rtk gain` after a few Bash calls.

## Push status — BLOCKED (honest)

`git push` was **not** executed. OVO council verdict on the working-tree
delta = **B** (`delta_id fea25aff`). The audited tree carries an unresolved
incomplete-delivery marker file (the integrity gate failed three times on
2026-05-16: one CRITICAL `intent_lock.js:146` Infinity-timeout finding plus
several HIGH unfinished-code markers in non-RTK files) and 139 uncommitted
new files. The RTK subset itself is clean; it is blocked only because OVO
audits the whole tree and the `.powerpack` push-gate is active. Per the Q4
hard-gate, B below A means push halted and verdict logged to
`vault/audits/verdicts.jsonl`. Unblock path: resolve the flagged
incompletions (real fixes for the CRITICAL finding and the unfinished
markers), re-run OVO; or land the RTK commits via a separate clean branch
off `origin/main`.
