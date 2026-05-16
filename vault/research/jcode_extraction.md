# jcode Pattern Extraction (MC-SYS-24)

**Source:** `https://github.com/1jehuang/jcode` (default branch: `master`)
**Audit date:** 2026-05-02
**Audit method:** WebFetch (raw.githubusercontent.com paths)
**Repo nature:** Independent Rust-based AI coding agent harness — NOT a fork of claude-code/opencode/codex.

---

## Verified Facts (from raw README + AGENTS.md fetches)

| Property | Value |
|---|---|
| Primary language | Rust 94.2% (Python, Swift, Shell, JS, PowerShell minor) |
| Time-to-first-frame | 14.0 ms (vs Claude Code 590.7 ms — 3436.9 ms) |
| RAM single session | 167.1 MB w/ local embeddings (vs Claude Code 386.6 MB) |
| RAM scaling | +10.4 MB / session (vs competitors 76.5 — 318.4 MB) |
| Persistence model | Named resumable sessions (`jcode --resume fox`) |
| Memory model | Semantic vector embeddings + cosine similarity, **passive injection** (no explicit memory tool calls) |
| Skill loading | Dynamic via embedding hits, NOT startup-loaded |
| Multi-agent | Swarm feature, file-change notifications between agents, automatic conflict detection |
| Build layout | `~/.jcode/builds/{current,stable,versions/<version>/}` + `~/.local/bin/jcode` symlink |
| Logs | `~/.jcode/logs/<date>.log` |

---

## Patterns Applicable to claude-power-pack

### 1. Passive Memory Injection (high value)
**jcode pattern:** "automatically recalls relevant information to the conversation without actively calling memory tools" via cosine similarity on embeddings.

**Power-pack analogue:** `gatekeeper-semantic.js` PreToolUse hook already injects neural summaries from `_audit_cache/source_map.json` (advisory). The jcode lesson is to push this further — **every memory file should have an embedding**, and the PreToolUse hook should rank-inject the top-3 by similarity to the user prompt instead of glob-matching.

**Action item (out of scope this sprint):** future BL — add `tools/memory_embed.py` to compute embeddings for `memory/*.md`. Current BL-0016 heat-map is keyword-based and sufficient for skill triage.

### 2. Atomic Writes via File-Change Notifications
**jcode pattern:** Swarm agents broadcast file-change events; receivers detect conflicts. This is event-driven, not lock-based.

**Power-pack analogue:** Windows `defaultMode: bypassPermissions` + concurrent Cursor windows means we have multiple agents touching shared files (`baseline_ledger.jsonl`, `vault/sleepy/INDEX.md`, `pending_resume.txt`). The race condition this introduces is exactly what BL-0014 addresses.

**Action item (THIS sprint, BL-0014):** `lib/atomic_write.py` — write-to-tmp + `os.replace()` atomic swap, with PermissionError retry for Windows ERROR_SHARING_VIOLATION (AV/indexer holding file). NOT a swarm broadcast (out of scope), just the safe-write primitive.

### 3. Lazy Skill Loading via Embedding Index
**jcode pattern:** Skills do NOT load at startup; they activate "via embedding hits."

**Power-pack analogue:** Native Claude Code already does deferred-tool resolution (155 skills are cited by name in system reminders, full schemas fetched on-demand via ToolSearch). What's missing is a **PreToolUse advisory layer** that ranks skills by relevance to the current Bash/Edit/Read action and injects "consider also: X, Y" into additionalContext.

**Action item (THIS sprint, BL-0016):** `tools/skill_heat_map_indexer.py` — scan `~/.claude/skills/**/SKILL.md`, extract `description:` field + first-paragraph keywords, emit compact JSON to `vault/skills_heat_map.json`. Hook consumes this; no on-the-fly directory scan.

### 4. Daily Date-Stamped Logs
**jcode pattern:** `~/.jcode/logs/<YYYY-MM-DD>.log` rotation.

**Power-pack analogue:** Already implemented (`memory/sessions/session_YYYY-MM-DD_HHMM.md` per CLAUDE.md "Session Logging" rule). No action needed.

### 5. Tiered Binary Layout
**jcode pattern:** `current` / `stable` / `versions/<v>/` + `~/.local/bin` PATH precedence.

**Power-pack analogue:** Power-pack is a skill bundle, not a CLI binary. Pattern not applicable. Noted for any future native-binary direction.

---

## Patterns NOT Applicable (rejected on inspection)

- **Swarm multi-agent broadcast**: requires custom IPC layer; Claude Code's harness doesn't expose this. Advisory-only is the realistic ceiling (per BL-0009).
- **30+ provider OAuth**: Power-pack is Claude-only by design.
- **Browser automation via Firefox bridge**: out of scope; Playwright plugin already covers UI verification.
- **Voice input** (`jcode dictate`): out of scope.

---

## Cited URLs (all 200 OK except where noted)

- `https://github.com/1jehuang/jcode` — repo root, 200 OK
- `https://raw.githubusercontent.com/1jehuang/jcode/master/README.md` — 200 OK
- `https://raw.githubusercontent.com/1jehuang/jcode/master/AGENTS.md` — 200 OK
- `https://raw.githubusercontent.com/1jehuang/jcode/master/PLAN_MCP_SKILLS.md` — 200 OK
- `https://raw.githubusercontent.com/1jehuang/jcode/main/AGENTS.md` — **404** (default branch is `master`, not `main`; recorded for forensic parity)
- `https://github.com/1jehuang/jcode/tree/main/docs` — **404** (same reason)

---

## Verdict

**3 of 5 jcode patterns map to actionable Power-Pack laws (BL-0014, BL-0015, BL-0016).** None require harness-level access we don't have. All three produce verifiable artifacts (atomic-write helper, Stop-hook ledger row, heat-map JSON).

The "JCode Singularity" framing is rhetorical; the real win is **3 hardening primitives**, each independently testable, each addressing an empirical pain point already in the baseline ledger (concurrent writes BL-0001..13, context-loss BL-0003/04, skill discovery latency).
