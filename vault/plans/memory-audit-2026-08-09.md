---
title: Memory and context capture audit — router integrity and session writeback
date: 2026-08-09
tier: T2
status: STOP #1 — awaiting Owner decision
covers: [memory_router, memory_md, session_writeback, knowledge_capture, router_freshness]
---

# Phase 0 — Reality scan

## Substrate map (three stores, discovered not assumed)

| store | path | role today |
|---|---|---|
| project memory | `~/.claude/projects/C--Users-User--claude-skills-claude-power-pack/memory/` | canonical MEMORY.md + 103 knowledge files |
| PP vault | `~/.claude/skills/claude-power-pack/vault/` | 73 subdirs, 286 knowledge_base files, 23 lessons, 125 plans |
| global vault | `~/.claude/knowledge_vault/` | core doctrine, `ukdl/` (7 files, untouched since 2026-05-26) |

Canonical MEMORY.md: `~/.claude/projects/C--Users-User--claude-skills-claude-power-pack/memory/MEMORY.md`.
39 other MEMORY.md files exist, one per project id. No `~/.claude/MEMORY.md`.
Live UKDL corpus: `vault/knowledge_base/ukdl-universal.md` (4668 lines, 2026-08-08).

## Premise correction

The brief assumes MEMORY.md may be acting as a store. Measured, it is not.

| metric | value |
|---|---|
| entries | 109 |
| entries that are pointers | 109 |
| entries holding inline knowledge | 0 |
| mean hook length | 78 chars |
| max hook length | 181 chars |

Category B is empty. The constitutional principle is already satisfied on the
no-inline axis. The defect is the inverse: the router is stale, and its bridge
into the vault does not resolve.

# Phase 1 — Gap register

## F1 — CRITICAL — the vault bridge resolves 0 of 7

8 links do not resolve. One root cause: relative depth counted from the project
directory instead of from `memory/`. `../../skills/...` resolves to
`~/.claude/projects/skills/...`, which does not exist. Correct prefix is
`../../../skills/...`.

All 8 destination files were verified present at the corrected path.

7 of the 8 are the only pointers MEMORY.md has into the PP vault. The router
therefore reaches 0 of ~441 vault knowledge artifacts. The 8th
(`_audit_cache/insights.json`) resolves to `~/.claude/_audit_cache`; the file
lives at `skills/claude-power-pack/_audit_cache/insights.json`.

## F2 — CRITICAL — 23 rules sealed, 0 indexed

MEMORY.md last gained an entry 2026-08-04. Between that date and 2026-08-08,
`ukdl-universal.md` gained 23 rule identifiers absent from the 2026-08-04
baseline of that same file (9 further identifiers on added lines were
re-references to rules that already existed, and are excluded).

Router coverage of those 23: zero.

Instrument: added-line identifier extraction from `git log -p`, cross-checked
against `git show <baseline>:vault/knowledge_base/ukdl-universal.md`.

## F3 — HIGH — no session-close writeback reaches the router

Every MEMORY.md reference across the hook set is read-only:
- `hooks/session-init.js:220-228` — line-count lint, warns above 200
- `hooks/memory-rotation.js:98-111` — same check, warn only

`hooks/learning-sentinel.js` runs at SessionEnd and is the closest candidate.
Its terminal writes are a `LEARNINGS_PENDING.md` marker at cwd and a proposal
under `~/.claude/cache/compound-proposals/`. Neither is MEMORY.md, and neither
is the vault.

Router growth is therefore model-driven, not mechanism-driven: it happens when
the agent remembers, and F2 measures what happens when it does not.

## F4 — HIGH — the sentinel is input-starved

| input it reads | files present |
|---|---|
| `.claude/cache/learnings/*.md` | 1 |
| `memory/sessions/session_*.md` | 0 |

Doctrine mandates one session log per session under `memory/sessions/`. The
directory holds none. Accumulated unconsumed output: 98 proposals in
`~/.claude/cache/compound-proposals/`.

## F5 — MEDIUM — 2 orphan memory files

On disk, absent from the index: `feedback_bl0013_windows_filelock.md`,
`feedback_kickbacks_hijacks_cli_statusline.md`.

## F6 — MEDIUM — 119 of 125 plans unreferenced

No file in the memory corpus names them. Instrument caveat: this is a filename
match, so a plan whose content was promoted into `knowledge_base/` under a
different name scores as unreferenced. The number bounds the reachable set; it
does not prove 119 losses. A content-level check must precede any action here.

## F7 — MEDIUM — two UKDL locations, one inert

`~/.claude/knowledge_vault/ukdl/` holds 7 files, newest 2026-05-26.
`vault/knowledge_base/ukdl-universal.md` is 4668 lines, current to 2026-08-08.
The global router in CLAUDE.md points at the former.

# Proposed repair

R1 — repair the 8 links (depth prefix + the insights path). Restores the only
bridge from router to vault.

R2 — index the 23 sealed rules by one durable pointer to the UKDL corpus plus
individual entries only for cross-cutting rules, not 23 new lines. MEMORY.md is
at 111 of its 200-line budget; a one-line-per-rule policy converts the router
back into a store and re-creates the defect the brief set out to prevent.

R3 — index the 2 orphans. Defer F6 pending the content-level check.

R4 — a router freshness gate, discovered rather than curated: derive the set of
sealed rule identifiers from the UKDL corpus, derive the set reachable from
MEMORY.md, and fail when a sealed rule is unreachable. Same construction covers
link integrity, so F1 and F2 both become non-silent. This applies
PR-COVERAGE-BY-CONSTRUCTION-001 to the router itself.

# Rules to seal on completion

- HR-MEMORY-IS-ROUTER-001 — MEMORY.md indexes, it does not store.
- PR-SESSION-WRITEBACK-001 — a session that seals knowledge updates the router.
- T-KNOWLEDGE-STRANDED-IN-PLANS-001 — plans is staging; unreferenced after one
  session means unreachable.
- T-ROUTER-BRIDGE-UNRESOLVED-001 — a pointer whose target exists but whose path
  does not resolve reads as an index entry and delivers nothing. Verify
  resolution, not existence.
