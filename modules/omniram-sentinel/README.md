# OmniRAM-Sentinel — Doctrine for Disk-First / Lazy-Loading

**Scope:** Universal blueprint for any future Power-Pack-managed project (web app, plugin, game, native binary). Codifies the jcode-extracted patterns that survived audit (vault/research/jcode_extraction.md, BL-0014/0017/0018) into project-time defaults.

**Not a runtime.** This document is a checklist. There is no `omniram-sentinel.exe` to install. The "sentinel" is the pattern-matching that should happen at design-review time on any new module.

---

## The Three Disciplines

### 1. Disk-First, Not Memory-Resident
**Rule:** Persistent state lives on disk. Process RAM is for working set only.

**Why:** Hooks fork-and-die (BL-0017). Long-running processes get killed by OOM, restart, or laptop sleep. Anything not on disk at the moment of crash is lost. jcode's ~10 MB-per-additional-session scaling vs Claude Code's 76-318 MB comes from this discipline (vault/research/jcode_extraction.md §1).

**How to apply:**
- New feature must declare its persistent state before its in-memory state.
- Any "cache" that exists only in RAM needs a justification ("this regenerates in <100ms from disk", or "this is per-call working set"). If neither, it goes on disk.
- `_audit_cache/`, `vault/`, `~/.claude/lazarus/`, `/tmp/claude-*-<session>.json` are the canonical disk-state locations.

### 2. Lazy-Loading via Index, Not Glob-on-Demand
**Rule:** Anything that scans a directory tree on every call is a budget fault.

**Why:** Globbing `~/.claude/skills/**/SKILL.md` on every PreToolUse call (155 paths) costs 30-100ms per call. Reading a pre-built `vault/skills_heat_map.json` (one file, parsed once) costs <10ms. jcode loads skills "via embedding hits, NOT startup-loaded" (jcode_extraction §3); we map this pattern via static index files.

**How to apply:**
- New domain (skills, commands, configs, plugins) gets an indexer in `tools/<thing>_indexer.py` that emits a flat `vault/<thing>_index.json`.
- Hooks read the index, never the source tree.
- Index regenerates on demand (after add/remove) or via a SessionStart hook if size warrants.
- Reference implementations: `tools/skill_heat_map_indexer.py` (BL-0016), `vault/skills_heat_map.json`, `vault/commands_index.json` (BL-0020).

### 3. Atomic Persistence, Not Naive Write
**Rule:** Any write to a file shared across processes goes through `lib/atomic_write.{py,js}`.

**Why:** Windows under `defaultMode: bypassPermissions` + concurrent Cursor windows = race conditions on `baseline_ledger.jsonl`, `vault/sleepy/INDEX.md`, `pending_resume.txt`. ERROR_SHARING_VIOLATION (Win32:32) when AV/indexer holds a file. Naive `fs.writeFileSync` torn writes leave half-written JSON. (BL-0014, BL-0018).

**How to apply:**
- Write goes to `<target>.tmp.<pid>.<rand>` first → fsync → `os.replace`/`fs.renameSync`.
- Wrap rename in EPERM/EBUSY/EACCES retry with exponential backoff (≥5 retries, 25→400ms).
- Append-only logs use `atomic_append_jsonl` (read-modify-write under atomic-replace). High-frequency? Use a real DB.
- Empirical guard: `os.O_BINARY` on Windows os.open (Python only; Node fs uses binary by default). See `memory/feedback_windows_text_mode_compounding.md`.

---

## Integration Checklist (apply at module birth)

When proposing a new module / feature:

- [ ] Persistent state declared (path + format + lifecycle)
- [ ] No in-memory cache claims to be the source of truth
- [ ] If scanning > 10 files at runtime: indexer + JSON exists
- [ ] All shared-state writes route through `atomic_write`
- [ ] Cold-start budget declared (target: <100ms for hooks, <500ms for indexers)
- [ ] No assumption that hooks hold state across invocations (BL-0017)
- [ ] No assumption that hooks can dispatch slash commands (BL-0003)
- [ ] Performance numbers benchmarked, not estimated (`vault/benchmarks/`)

If you can't tick all 8, the module isn't OmniRAM-Sentinel-compliant. Either restructure, or document the deviation with a citation.

---

## What This Doctrine Does NOT Promise

- **It does not reduce Claude Code's harness RAM.** The harness is a closed binary; we cannot modify it. Per jcode's own README, jcode's 167 MB vs Claude Code's 386 MB is a **2.3x** advantage from a different runtime, not from disciplined hook design.
- **It does not auto-trigger user actions.** No hook can dispatch `/clear`, `/compact`, `/kclear` — slash-command dispatch is user-only (BL-0003). Sentinel hooks advise; they never act.
- **It does not eliminate every theoretical race.** Append-only JSONL under high concurrency still requires a real DB. Atomic-replace narrows the window; it doesn't close it.

The doctrine is **discipline applied consistently**, not a magic harness.

---

## Citations

- `vault/research/jcode_extraction.md` — verified jcode patterns (1jehuang/jcode @ master)
- `vault/baseline_ledger.jsonl` — BL-0003 (slash-command limit), BL-0014 (atomic_write.py), BL-0016 (heat-map), BL-0017 (no-hook-RAM-state), BL-0018 (atomic_write.js + advisor)
- `lib/atomic_write.py` + `lib/atomic_write.js` — reference implementations
- `tools/skill_heat_map_indexer.py` — reference indexer
- `memory/feedback_windows_text_mode_compounding.md` — Windows newline footgun
