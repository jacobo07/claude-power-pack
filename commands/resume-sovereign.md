---
name: cpp-resume-sovereign
description: Fuzzy-search the Sovereign History Vault (46k+ records) and inject a recovered session as read-only context. Pairs with vault-heartbeat (Stop hook, 5-min throttle) and vault_search.py (FTS5 + dedup picker).
argument-hint: "<query> | <composer_id>"
---

# /cpp-resume-sovereign

Bring a past session back to life as **read-only context** for the
current turn. Source: `SOVEREIGN-HISTORY-VAULT.{jsonl,db}` (Cursor SQLite
turns + .jsonl transcripts, deduped, FTS5-indexed).

## Argument modes

`/cpp-resume-sovereign <free-text query>` — fuzzy search; you pick from
the top BM25 hits.
`/cpp-resume-sovereign <composer_id>` — direct retrieval (UUID-shaped).
`/cpp-resume-sovereign --list` — show top-N dedup'd resumeable
composers (excludes those already open in another Cursor pane via the
30s-cached `open-composers.json`). Rows whose composerId is a
RECOVERED-orphan (see below) are prefixed with the literal marker
`[REC] 🟩 ` — ASCII-first so a cp1252/conhost terminal that can't
render U+1F7E9 still shows `[REC]` (no tofu, no layout shift).

`/cpp-resume-sovereign --recovered` — list only the RECOVERED-orphan
composers: UUID-shaped composerIds with ≥1 `source LIKE
'recovered.old%'` vault row that are NOT a live `.jsonl`/`.jsonl.live`
filename and have 0 rows from `live%`/`backup`/`workspace`. These are
sessions salvaged from the corrupt `state.vscdb.old.fixed.db` whose
advances never reached a live transcript. Backed by
`python tools/vault_search.py --list-recovered [N]`. The set is cached
at `~/.claude/state/recovered-composers.json` (300 s TTL,
recompute-on-read) with a `projects` reverse-map consumed by the
`learning-sentinel.js` SessionStart advisory.

## Execution contract (what I do when invoked)

1. **Detect mode.** If the arg looks like a UUID (`[0-9a-f-]{36}`), go
   to step 3. If `--list`, run
   `python tools/vault_search.py --list-resumeable 30` and stop.
   Otherwise treat the rest as a fuzzy query.

2. **Search.** Run `python tools/vault_search.py --search "<query>"`.
   Capture the top 10 hits (composer_id, project, snippet, BM25 rank).
   Present them to you via `AskUserQuestion` (or use the first hit if
   the query was unambiguous).

3. **Retrieve.** Run
   `python tools/vault_search.py --get <composer_id>`. The output is
   already wrapped in
   `<retrieved-history readonly="true" composer_id="…">…</retrieved-history>`
   so the model treats it as data, not directives (prompt-injection
   guard).

4. **Project-filtered Laws injection.** Read
   `Downloads/PowerPack_Sovereign_Datasets/UNIVERSAL-TRANSCRIPT-LAWS.TXT`
   and Grep for the resumed session's project name (from the retrieval
   header). Emit only the matching `LAW-###` blocks under a heading
   `## Lessons relevant to this project's history`. Keeps the token tax
   bounded.

5. **Dedup warning (advisory).** Run
   `python tools/vault_search.py --list-open-composers` and check if
   the requested `composer_id` is currently bound to a Cursor pane.
   If so, emit a one-line warning: *"This composer is currently open in
   a Cursor tab — context injected here may diverge from the live
   pane."*

6. **Emit the assembled block.** Print the retrieval + the filtered
   laws to the response so the next turn has the recovered context.

## Honest limits

- **Read-only injection.** This does NOT reopen the session in Cursor
  or replay a `.jsonl` via native `/resume`. The recovered content
  becomes part of the current Claude Code turn's context — actionable
  but not "the prior session resumed in place".
- **Recovery yield is variable.** Cursor stores most chat content
  nested (`attachedCodeChunks`, hex blobs). Bubbles where neither
  structured walk nor byte-scrape surfaced text are skipped honestly;
  the retrieval may have fewer rows than Cursor's UI would show. See
  `_reconstructed/MANIFEST.json` for per-source recovery stats.
- **Vault freshness.** Sync runs as a Stop-hook (≥5 min throttle).
  Very recent turns may not be in the vault yet — run
  `python tools/merger.py --build` to force a sync.

## Underlying tools

- `tools/vault_search.py` — FTS5 + composer retrieval + open-composer
  cache + resumeable picker.
- `hooks/vault-heartbeat.js` — Stop hook, detached fire-and-forget,
  mkdir mutex, ≥5 min throttle.
- `tools/merger.py` — full vault rebuild (called by heartbeat in
  background).
- `tools/reconstructor.py` — physical `.recover` rebuild of corrupt
  SQLite stores (one-shot, already run; output in `_reconstructed/`).
