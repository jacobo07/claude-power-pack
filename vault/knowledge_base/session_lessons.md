# Session Lessons — Atomic Learning

Append-only log of concrete, non-derivable learnings per session.
One entry per `/kclear` with a `lesson` field. Keep each entry short and
self-contained — if a future reader can't grok it without the conversation,
rewrite it.

---

## 2026-05-03 — BL-0046/47/48 empirical seal + BL-0049 self-mod-guard finding

**Session:** `omni-max-empirical-2026-05-03`

Five non-derivable findings:

1. **Self-modification guard ≠ bypassPermissions** — even with `defaultMode: bypassPermissions` in `~/.claude/settings.json`, edits to `~/.claude/CLAUDE.md` AND `~/.claude/skills/claude-power-pack/parts/core.md` AND `vault/knowledge_base/session_lessons.md` were denied with reason "Self-Modification". Harness explicitly treats `(y/n)` confirmation prompts as "awaiting confirmation, not explicit authorization". To unlock: add a Bash permission rule like `"Edit(file:~/.claude/CLAUDE.md)"` to `permissions.allow` in `~/.claude/settings.json`. **Update `feedback_bypasspermissions_defeats_deny.md`.**

2. **Permission rules HOT-RELOAD mid-session** — unlike hooks (which load once per session per `feedback_settings_session_load.md`, requires `/restart`), `permissions.allow` entries in settings.json are picked up immediately. Verified empirically 2026-05-03: Owner added `"Edit(file:~/.claude/CLAUDE.md)"` mid-session, the next `Edit` call to that path passed without restart. **NEW finding** — distinguish hot-reload (permissions) from cold-load (hooks).

3. **`zero-fiction-gate.js` SOFT_PATTERNS only match line-leading comments** — regex `(^|\\n)\\s*(\\/\\/|#|\\/\\*|\\*)\\s*(TODO|FIXME|HACK|XXX)\\b` (`zero-fiction-gate.js:54`). Inline `function foo() { /* TODO */ }` does NOT trigger soft advisory. Anti-false-positive design. Test fixtures must use line-leading comments.

4. **`context-watchdog.py` cross-project snapshot is empirically green** — BL-0046 probe confirms tier-1 (65%) lands in `<cwd>/vault/progress.md` when `vault/` exists, falls through to `<cwd>/.claude/progress.md` when bare project. Tier-2 (72%) emits `additionalContext` with literal `CONTEXT THRESHOLD CROSSED`. Verified across 2 scratch projects with SHA-256 mutation evidence (`vault/audits/probe_global_watchdog.json`).

5. **Primary-cerebrum coverage gap: 0/5 decoded projects have per-project vault** — BL-0047 probe shows globals all present (`~/.claude/CLAUDE.md`, `~/.claude/vault/INDEX.md`, `~/.claude/knowledge_vault/INDEX.md`, GAL ledger) but only 1/5 projects has `_knowledge_graph/INDEX.md` and 0/5 have per-project `vault/INDEX.md` or `progress.md`. The "primary brain" is global-only — per-project enrichment requires `/cpp-vault-setup` or `/cpp-obsidian-setup` runs (`vault/audits/probe_vault_load.json`).

---

## 2026-04-22 — Shipped 5 MC-OVO cycles on claude-power-pack: sleepless_qa atomic landing (34 fi

**Session:** `kpp-supremacy-v7000-marathon`

Before promoting any inline-one-liner failure to an audit recommendation, run the canonical tool (--help / official CLI). Mistake #52: my ad-hoc script's bug got misattributed to the audited file.

---

## 2026-04-25 — Shipped multi-session Lazarus (tools/lazarus_revive_all.py + /lazarus all/window

**Session:** `5ed443a6-0735-4409-a264-06be1c43bceb`

AGPL-3.0 and research-only licenses prohibit metadata stripping. When Owner asks to absorb OSS repos, refuse + offer vendor/NOTICE.md + adapter pattern with license retention.

---

## 2026-04-26 — Shipped MC-OVO-107 partial: JS cascade populator via esprima (tools/cascade_popu

**Session:** `unknown`

ANALYSIS_STALEMATE with full reason string > silent skip. Honest partial graph proves limits matter as much as positive findings; fake completeness is worse than acknowledged gaps.

---

## 2026-04-27 — Shipped: /ovo-audit canonical Spanish RESULT format + Anti-Echo Gate; bug-hunter

**Session:** `unknown`

Doctrinal-disqualification-first: verify upstream API/model existence (gh + vendor docs) BEFORE writing adapter. 0 cycles vs probe-fail-fix. Saved 3+ scaffold-illusions this session.

---

## 2026-04-27 — Lazarus multi-pane sovereignty cascade: lister --exclude-live + current-session

**Session:** `a4f80c66-4ab0-472a-a45a-a4a716de0173`

When N panes consume a shared FIFO concurrently, atomic-claim via mkdir-mutex (atomic on NTFS) prevents simultaneous reads popping the same entry. Without lock, all panes pick the first item -> silent collision.

---

## 2026-04-29 — Lazarus multi-pane fixes (MC-LAZ-23 bindings auto-populate, MC-LAZ-24 clean-exit

**Session:** `35da8c8f-3d0c-44ce-a25b-912050c91802`

ULTRA-PLAN MODE prompts with multiple gated MCs: reply 1-line (X MCs gated, wait for Y event) instead of full analysis. Each verbose response burns 5-7k against a 200k budget.

---

## 2026-04-30 — Zero-touch Win repair chain: rebuild es-ES ISO + setup.exe rejected 0xC1900204 M

**Session:** `0a2b14ee-87e9-4886-848d-2027da82494d`

Docker on broken VMP: enable Hyper-V backend instead of WSL2 (Hyper-V often already enabled). Win setup.exe /Auto Upgrade rejects 0xC1900204 if ISO build too close to installed.

---

## 2026-05-01 — Power-pack hardened over 2 days, 9 commits / 10 BL laws shipped: plugin scanner

**Session:** `f21c4d94-7929-4667-afef-0a69c56e07d3`

Stale project-memory entries that drive DESTRUCTIVE remediation must be live-probed before action — the MC-SYS-09 misfire spawned REPAIR_WINDOWS_v2.bat against a Docker that was already working (memory was 2 days stale). BL-0008 codifies probe-before-repair.

---

## 2026-05-03 — Hardened claude-power-pack across 7 phases: 11 commits (9 pushed to origin/main,

**Session:** `unknown`

User-authored security gates (secret-scanner, ovo-push-gate, readonly-prompts-guard) are the contract, not obstacles. Surface as blocked, ask for explicit auth — never bypass.

---

## 2026-05-03 — Phases V-VIII shipped + OVO audit verdict A recorded + 2 pending commits pushed

**Session:** `unknown`

OVO Phase A breadcrumb expires at 120s. Long-running audit turns must re-run --json before --record-verdict, or the verdict is rejected with no orphan write.

---

## 2026-05-03 — Phase IX globalization: per-project progress.md (BL-0043), terminal-slot recorde

**Session:** `unknown`

MCP env-var expansion IS supported by Claude Code launcher including digit-leading names. Verified empirically via 21st.dev deferred tools appearing post-restart.

---

