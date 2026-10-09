---
covers: [prompt-recall, recall, memory-catalog, unindexed-memories, gsd_x-recall]
tier: T2
status: active
date: 2026-10-09
---

# Prompt Recall: relevance-ranked knowledge on every prompt

## Problem
A session starts with pointers, not knowledge. `MEMORY.md` indexes are at 13-21k chars and
cannot grow, and ~912 memory files across 12 projects have no pointer at all, so nothing ever
surfaces them. UKDL (1.3 MB, 635 ids) and HARD-RULES (370 KB) reach a session only if the model
happens to open them. The Tower baseline injects lessons "ranked by kind, NOT by relevance".

## Owner
`modules/gsd_x/cli.py` already owns knowledge injection on UserPromptSubmit (spec §7 of the
Tower hand-over: one effect, one owner). Recall is a fourth block of that owner, implemented in
`modules/gsd_x/recall.py`. No new hook, no new chain member, no new spawn.

## Design
- **Sources:** every `~/.claude/projects/*/memory/*.md` (index files excluded), UKDL, HARD-RULES,
  CLAE process rules and traps.
- **Chunks:** memory file = one chunk (frontmatter description + body). Rule stores split at a
  `#`-`####` heading or a paragraph opening with a bold id (`**`ID`**`).
- **Index:** isolated FTS5 sidecar `~/.claude/state/recall/recall.db` (own tables, never
  `turns_fts`), tokenizer `unicode61 remove_diacritics 2`. A `files` table holds
  (path, mtime_ns, size) so refresh re-chunks only changed files and drops removed ones.
- **Query:** content terms of the prompt (EN+ES stopwords dropped), kept only if the index knows
  them and they sit in <=15% of chunks, rarest 12 OR-joined, bm25 ranked, the current project's
  memories boosted. A hit must contain >=3 distinct query terms (>=30% of them for long prompts;
  all of them for a 2-term prompt). Prompts with <2 usable terms abstain.
- **Readers never wait:** the index is WAL and hook-side readers time out at 0.2 s. Top 5, one per file, snippet <=260 chars, path given so
  the model can open the full entry.
- **Session dedupe:** a chunk shown once in a session is not shown again in it.
- **Refresh:** the hook never builds. If the index is missing or older than 10 min it launches a
  detached `--refresh` guarded by an exclusive lock file (stale after 10 min), so N panes start
  at most one refresh. An attempt stamp limits launches to one per 10 min even when every
  refresh fails. The prompt it fires on uses the index as it is.

## Unindexed memories
`tools/memory_catalog.py` writes `MEMORY_CATALOG.md` in each memory dir (every memory file with
no pointer in `MEMORY.md`, one line each from its frontmatter) and adds ONE idempotent pointer
line to that `MEMORY.md`. Findability comes from recall; the catalog makes them visible to a
human and to a model reading the index.

## Acceptance (tools/test_prompt_recall.py, V-RECALL-*)
1. A planted memory is returned for a prompt about it (positive) and NOT for an unrelated prompt
   (negative control).
2. A 1-term prompt abstains.
3. Editing a file re-indexes it; deleting a file removes its chunks.
4. The same chunk is not shown twice in one session; a new session sees it again.
5. Missing db, unreadable db, or any exception yields "" (fail-open).
6. Bold-id and heading chunking split a UKDL-shaped file into the expected count.
7. Catalog: lists exactly the unindexed files; a second run changes nothing.
8. Query latency on the live index is measured and printed.

## Kill switches and rollback
`CPP_RECALL=off` disables the block. Rollback = revert the commit and delete
`~/.claude/state/recall/`. The catalog line in each `MEMORY.md` is one line, removable by hand.
