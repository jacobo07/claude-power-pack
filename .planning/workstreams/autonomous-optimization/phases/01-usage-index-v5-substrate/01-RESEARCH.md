# Phase 1: usage_index v5 substrate - Research

**Researched:** 2026-10-06
**Domain:** SQLite incremental ingest of Claude Code JSONL transcripts (EXTEND `tools/usage_index.py`; reuse `tools/tis_observed.py::store_identity`)
**Plane:** gex44 (every number below was measured on `/home/kobii/kme-corpus/projects`, read-only; scratch DBs under `/tmp/ao_probe/`)
**Confidence:** HIGH on current-code facts and the parity reproduction (measured this session); MEDIUM on the v5 design (proposal, to be fixed by the PLAN-mode design step); LOW on whole-corpus cost (not measured, by instruction)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- EXTEND `tools/usage_index.py` (schema v5) and reuse `tools/tis_observed.py::store_identity` for realpath + content
  identity. No new database, no new top-level module (HR-NOVELTY-001 record from Phase 0 = EXTEND_EXISTING_OWNER).
- Corpus on this plane = the Owner-authorized COPY `/home/kobii/kme-corpus/projects` (9.6 GB, frozen 2026-10-05,
  contains `_archived` and 3 relative symlinks recreated from laptop junctions). Pass it as the root explicitly;
  NEVER point a measurement at GEX44's own `~/.claude/projects`. Every result labelled `plane: gex44`.
- The index DB for measurements lives outside the repo and outside the corpus (e.g. under the job/mission scratch
  area); the corpus copy is read-only input.
- Parity target is the frozen KME-L denominator (102 sessions / 34,871 calls / cache_read 11,549,646,300). Any
  mismatch is reconciled to the unit (which sessions/calls differ and why), never rounded away.
- UNKNOWN / INCONCLUSIVE / UNMEASURED are never PASS. Parser failure is surfaced, never a silent zero. An empty
  population refuses a verdict.
- Never edit: CE/SC/IC-gen1 ledgers' `frozen` objects, gen2 `frozen` object, `tools/test_cognitive_economy_program.py`,
  `tools/test_skill_capability_program.py`, root `.planning/STATE.md`, `tools/gsd_mission.py`.
- Commits: explicit pathspec, one falsifiable increment each; verify `git log -1 --format=%s`.
- Phase ends with `01-EVIDENCE.md` (Product Delta + Intelligence Delta) and its gen2 ledger state rows for pillar O.

### Claude's Discretion
Table layout for tool events, attribution encoding (mixed allowed), the declared `_archived` rule, and the test
harness shape (follow existing V-gate style, e.g. `tools/test_ao_p0.py`).

### Deferred Ideas (OUT OF SCOPE)
None.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AO-03 (phase-1 part) | cheap always-on observation during normal execution | v5 ingest adds tool events / cwd / attribution inside the SAME single read pass `calls_from(on_line=...)`; no second parse. Cold build over the frozen KME scope (3.05 GB) = 15.7 s / 76 MB RSS on v4 (section Measured baseline), so the per-byte cost of v5 additions is the quantity to measure. |
| AO-09 (phase-1 part) | KME-L measured; population parity with the frozen denominator | Frozen 102 / 34,871 / 11,549,646,300 reproduced exactly from the champion parser in 21.6 s on the copy; v4 index reproduces all but ONE session, reconciled to the unit (18 calls / 5,515,928 cache_read). Exact filter + classifier pinned below. |
| AOP-O | usage_index v5 substrate (pillar O rule, 5 clauses) | Pillar rule quoted verbatim below; each clause mapped to a gate in Validation Architecture. |
</phase_requirements>

## Summary

`tools/usage_index.py` is a single-pass, offset-cursor SQLite indexer (v4: `files/calls/quota/prompts/spawns/subagents/meta`). It already reads each transcript once, byte-offset incrementally, through `tis_observed.calls_from(path, offset, on_line=...)`. Phase 1 is therefore an ADDITIVE v5 on the same pass: add tool events, cwd, project attribution, file content identity and per-file parse-error counters, plus a population/parity verb. No new module, no new DB.

Three facts shape the plan more than anything else. (1) A naive `SCHEMA_VERSION = 5` bump would make `_migrate_spawns` re-queue the v3/v4 spawn backfill and RE-READ every transcript holding an unanswered spawn, which violates "re-reads zero already-ingested files"; the spawn gate must be pinned to its own version constant. (2) The frozen KME-L population is defined by a CONTENT classifier (`KME_STRONG`: share of tool calls whose input matches a regex), evaluated only on lines up to the freeze instant, and counted per file (not globally de-duplicated); an index that stores only per-call usage cannot reproduce it, so v5 must keep time-sliceable per-tool-event pattern hits. (3) v4 attributes a cross-file duplicate call to whichever file it ingests first (order-dependent); that is exactly the 18-call parity gap, so v5 needs an occurrence table (`call_files`) beside the globally de-duplicated `calls`.

**Primary recommendation:** Implement v5 as additive DDL + one `_migrate_v5` that opens zero files (modeled on `_migrate_spawns`, with its own version gate), extract tool events/cwd/pattern-hits inside the existing `on_line` callback, add per-file `parse_errors`/`first_ts`/`last_ts`/`v5_from` columns, add a `population` verb that returns a typed verdict (`EXACT|DRIFTED|UNMEASURED`), and drive all six negative controls from both poles in a new `tools/test_usage_index_v5.py` (V-UX5-*). First Wave-0 task: make `tools/test_usage_index_identity.py` runnable on Linux (its `junction()` shells out to `cmd`, 0 PASS today).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Transcript parse + ingest (tool events, cwd, hits) | `tools/usage_index.py::refresh` via `tis_observed.calls_from(on_line)` | - | Only incremental single-pass reader; ten other parsers exist and must not gain an eleventh. |
| Store/realpath identity (junction/symlink alias dedup) | `tools/tis_observed.py::store_identity` | `usage_index._canonicalize` (row rewrite) | Declared "THE producer of store identity" (docstring); consumed, never re-derived. |
| Project/workstream attribution | `usage_index` (ingest-time, stored) | - | Must be stored so queries are index-only; derived from record cwd + tool paths, not from store dir names (lossy). |
| Population / parity verdict | `usage_index` CLI verb (reads DB only) | `wiki/tools/kme_token_audit.py` (pattern source) | Verdict logic must refuse empty populations; classifier patterns have one source of truth. |
| Cost measurement (wall, bytes) | `refresh()` return dict + executor harness | `/proc/self/io` rchar cross-check | Counters belong where the read happens. |
| Reader compatibility | `modules/wrapper/cost_gate.py`, `modules/frontier_intelligence/token_irr.py`, 6 `tools/*.py` via `ux.connect` | - | Additive-only DDL keeps them working. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib (`sqlite3`, `json`, `hashlib`, `re`, `ntpath`/`posixpath`, `os`, `time`) | CPython 3.12.3 [VERIFIED: `python3 --version` this session] | Everything | usage_index imports only stdlib + `tis_observed` + `pricing_source` [VERIFIED: tools/usage_index.py:32-51] |
| SQLite | 3.45.1 [VERIFIED: `sqlite3.sqlite_version` this session] | Index; supports `ON CONFLICT DO UPDATE` and JSON1 (`json_extract`) | already used by the upserts at usage_index.py:474-483 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Per-event `pat_hits` JSON for the classifier | store raw tool-input text | Raw text bloats the DB and puts secrets on disk (HR-SECRET-002 spirit); hashes + counters are enough. |
| Global-only `calls` dedup | add `call_files` occurrence table | Global-only is order-dependent per session (measured: 18 calls); occurrence table makes per-session views reproducible and totals still de-duplicated. |
| Full-file hash re-computed per delta | head/tail fingerprint + per-file size | A full hash re-reads ingested bytes on every append; see Open Question 2. |

**Installation:** none. No external packages: the Package Legitimacy Gate is N/A (no `npm`/`pip`/`cargo` install in this phase). **Package Legitimacy Audit: none required (stdlib only).**

## Current-State Facts (all verified this session)

### usage_index v4
- `SCHEMA_VERSION = 4` and `V2 = 2` [VERIFIED: tools/usage_index.py:65-66]. Tables `files(path PK, offset, size, mtime_ns, is_sub, entrypoint)` (+ `cur_prompt`, `title` added in v2), `calls(k PK, file, ts, model, is_sub, entrypoint, inp, cw, cw5, cw1, cr, out)` (+ `session`, `prompt_id`, `agent_id`), `quota`, `prompts`, `spawns`, `subagents`, `meta` [VERIFIED: usage_index.py:67-89].
- Skip rule is stat-based, NOT content-hash: `if prev and prev[1] == st.st_size and prev[2] == st.st_mtime_ns: continue` [VERIFIED: usage_index.py:449-450]; read resumes at `offset = prev[0] if prev else 0` (451-455); a shrunken file restarts from 0 after deleting its `calls`/`quota` rows (457-460). The line reader stops before a trailing line with no newline: `if not raw.endswith(b"\n"): break` [VERIFIED: tools/tis_observed.py:145-146].
- File shapes ingested: only `*.jsonl` and `*/subagents/*.jsonl` under each store dir [VERIFIED: usage_index.py:252-255].
- Migration mechanism: `connect()` runs the v1->v2 full re-read only when version `< V2` (usage_index.py:118-127); later versions migrate inside `refresh()` via `_canonicalize` then `_migrate_spawns`, each in `BEGIN IMMEDIATE` with the version re-checked inside (usage_index.py:152-158, 318). Backup is `sqlite3 backup()` + sha256 + `integrity_check` (276-293).
- Cross-file call dedup is GLOBAL: key is `f"{key[0]}|{key[1]}"` = `msgid|requestId`; only identity-less calls are file-scoped (`off|<file>|<offset>`) [VERIFIED: usage_index.py:341-344]. `ON CONFLICT(k) DO UPDATE` keeps the first row's `file` (usage_index.py:477-483) => per-file attribution of a duplicated call depends on ingest order.
- Silent parse loss exists TODAY: `calls_from` does `except json.JSONDecodeError: continue` with no counter [VERIFIED: tis_observed.py:151-154]; only the reference `_calls_in` counts `bad`. Phase 1 criterion 2 ("parser failure surfaced") needs a counter here.
- Typed outcome: `refresh()` returns `{status: OK|PARTIAL|FAILED, files_read, calls_upserted, pending, ...}` and records `meta.last_refresh_status` [VERIFIED: usage_index.py:422-429, 505-515]. No `bytes_read`/`wall_s` yet (needed for criterion 4).
- CLI: `refresh|window|burn|replay|holdout`, `--db`, `--proj`, `--deadline` (default 600), `--since-days` (default 21) [VERIFIED: usage_index.py:782-793]. `--since-days` prunes by mtime, so a cold full build MUST pass a large `--since-days` or `since_epoch=None`.
- Default DB `~/.claude/state/usage_index/index.sqlite` via env `CPP_USAGE_INDEX` [VERIFIED: usage_index.py:53-54]; it does not exist on GEX44 (`ls` empty), so every GEX44 measurement needs `--db <scratch>`.
- Importers / liveness: `modules/wrapper/cost_gate.py:197-198` imports `burn` and `advisory_line` (live caller); `modules/frontier_intelligence/token_irr.py:135-167` reads the DB through a read-only URI, never `connect()`; `ux.connect` is called by `tools/estate_shadow.py:340`, `tools/floor_probe.py:258`, `tools/fanout_ledger.py:418`, `tools/root_progress.py:379`; `tools/rollover_replay.py:280` imports it. [VERIFIED: grep this session] => additive DDL only; never rename/retype an existing column.

### store_identity
- Quote: `def store_identity(base=None) -> tuple[list[Path], dict[str, str]]:` returns "(each transcript store under `base` once, {listed spelling: resolved path})" [VERIFIED: tools/tis_observed.py:349-359]. Identity is `os.path.realpath(sub)` of each IMMEDIATE child directory of `base`, keyed `os.path.normcase(str(real))`, first listing wins; aliases map listed spelling -> resolved path (364-372).
- It dedupes STORE DIRECTORIES only (one level). It says nothing about files and does not look inside `_archived`.
- Corpus has 3 symlinked project dirs [VERIFIED: `ls -la`]: `C--Users-User-Apps-mcp-video-analyzer -> C--Users-User--claude-skills-claude-power-pack`, `C--Users-kobig-Desktop-Cursor-Projects-TUA-X-CW-UGC-SYSTEM -> C--Users-User-Desktop-Cursor-Projects-TUA-X-CW-UGC-SYSTEM`, `C--Users-User-Desktop-Cursor-Projects-provisional--recovered-transcripts -> C--Users-User-Desktop-Cursor-Projects-provisional`. Relative symlinks resolve through `os.path.realpath` exactly like junctions.

### `_archived` today (silent zero found)
- `_archived` is one top-level child of the projects root whose children are PROJECT dirs (`_archived/<project>/<uuid>.jsonl`), i.e. one level deeper than any other store [VERIFIED: `find`]: 150 top files (209,543,673 B) + 105 subagent files (17,372,143 B) = 255 files. `_iter_files` globs `sub.glob("*.jsonl")` and `sub.glob("*/subagents/*.jsonl")` on `_archived` itself, which matches NONE of them. So the v4 index silently ingests zero `_archived` calls today. No archived file has a live twin by project+filename (150 checked, 0 same name) [VERIFIED: /tmp/ao_probe/mixed_archived.py].
- The frozen champion treats `_archived` as one "project" with pseudo-sessions: Run 5 `per_project` shows `_archived` 1 session / 649 calls / 271,001,260 cache_read when unfiltered [VERIFIED: gen2/evidence/champion/run5-r4-population.log].

### Other corpus shapes the two globs miss [VERIFIED: /tmp/ao_probe/shapes.py, full path census, no content read]
| shape | files | bytes |
|---|---|---|
| `<proj>/<sid>.jsonl` (top) | 2,299 | 7,392,051,210 |
| `<proj>/<sid>/subagents/agent-*.jsonl` | 1,411 | 2,313,106,933 |
| `_archived/<proj>/<sid>.jsonl` | 150 | 209,543,673 |
| `_archived/<proj>/<sid>/subagents/*.jsonl` | 105 | 17,372,143 |
| `<proj>/_empty_shells/*.jsonl` | 41 | 1,165,665 |
| `<proj>/_preserved/**` (Core-Files only; 8 subagent + 1 + 3 `*.preserved-20260521.jsonl`) | 9 + 1 | ~1.7 MB |
Total jsonl in these shapes 4,015 files. The champion's `os.walk` counts the `_preserved` and `_empty_shells` files as pseudo-sessions named `_preserved` / `_empty_shells` (rel path first component). In the Core-Files scope `_preserved` has 139 calls and class `KME_WEAK` (not in the KME population); `_empty_shells` has 0 calls [VERIFIED: /tmp/ao_probe/kme_ref.py]. Note `*.jsonl.bak-*` files are ignored by both walkers (suffix is not `.jsonl`).

## The KME-L denominator: exact producer and filter

- Frozen numbers live in `vault/programs/incremental-cognition/denominators/kme_audit_2026-10-03.json` under `KME-L`: `"sessions_active": 102`, `"sessions_dead": 0`, `"calls": 34871`, `"cache_read": 11549646300` [VERIFIED: file read this session]. (CONTEXT.md writes 11,549,646,300; identical.)
- Producing script: `wiki/tools/kme_pillars.py` (`population` subcommand) over `wiki/tools/kme_token_audit.py::scan_project` + `kme_report.is_kme`. The Run 6 command that reproduced it exactly [VERIFIED: vault/programs/incremental-cognition/measurements/D-KME-L-2026-10-05.md front matter]:
  `python3 wiki/tools/kme_pillars.py d --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2'`
  with `until: "2026-10-03T16:13:37Z"` (`FREEZE_INSTANT`, kme_pillars.py:73-74 region) and result `until_located.method: "exact_at_freeze"`.
- Population filter, verbatim:
  - dir scope: `project_filter.search(d)` on each child dir name (kme_pillars.py:1638-1639). That regex matches 6 dirs: Core-Files, `-KobiCraftServer`, `--audit-cache`, `-sentient-videos`, `-KobiCraftServer-plugins-kobicore`, and `kme-wt-arena2` (the space-named Core Files dirs do NOT match). Run 6 `corpus`: `"project_dirs": 6, "sessions_scanned": 568`.
  - session identity: `sid = rel.split('/')[0].replace('.jsonl', '')` inside each project dir (kme_token_audit.py:221-222) => one session = main file + its `<sid>/subagents/*` files; counts are `s['main'] + s['sub']`.
  - call dedup: PER FILE, key `(msg.get('id') or o.get('uuid'), o.get('requestId'))`, max per usage field, `<synthetic>` skipped, assistant lines only (kme_token_audit.py:109-153, 177-178).
  - time cut: `make_keep(None, until)` drops every line with timestamp > until; a timestamp-less line inherits the previous timestamp in its file (kme_pillars.py:291-314). Features (tool uses, user hits) accumulate ONLY from kept lines, so the CLASS itself is evaluated at the freeze instant.
  - KME selection: `is_kme(s)` = class in `KME_PATH|KME_STRONG`, or host `gex44` and project matches `kobii-a[0-9]` [VERIFIED: wiki/tools/kme_report.py:35-39]. `classify`: `PATH_KME_RE.search(s['project']) or (s['cwd'] and PATH_KME_RE.search(s['cwd']))` -> `KME_PATH`; `share >= 0.30 or (s['user_kme_hits'] >= 2 and share >= 0.10)` -> `KME_STRONG`, where `share = tool_uses_kme / tool_uses` [VERIFIED: kme_token_audit.py:233-242]. Patterns: ``KME_RE = re.compile(r'KobiMapEngine|KobiiMapEngine|\bKME\b|\bkme[-_/\\]|mapengine|map_engine|KMEIP', re.I)`` and ``PATH_KME_RE = re.compile(r'kme|mapengine', re.I)`` (kme_token_audit.py:10-11). `tool_uses_kme` counts a tool_use whose `json.dumps(input, ensure_ascii=False)` has >= 1 KME_RE hit (kme_token_audit.py:120-126); `user_kme_hits` counts hits in human-typed user text excluding `<command-name>` in the first 400 chars, `Base directory for this skill` in the first 200, length >= 20000, and `isMeta` lines (kme_token_audit.py:33-42, 163-166).
  - `sessions_dead` = selected sessions with 0 calls; with a time window active a session none of whose lines were kept "does not exist yet" (kme_pillars.py:1651-1672).
- Why unfiltered runs drifted (Run 5, `population_match: "drifted"`): +`_archived` 1/649/271,001,260, plus one PP session counted twice through the `mcp-video-analyzer` alias (128 calls, 34,065,113 cache_read, x2) = 105/35,776/11,888,777,786. Those are SCOPE differences, reconciled to the unit in 00-RESEARCH/zero-rescan plan lines 61-65 [CITED: vault/plans/zero-rescan-reality-scan-2026-10-05.md:59-67].

### Parity reproduction measured THIS session (scratch, read-only on the corpus)
- Champion parser, scoped to the 6 dirs, host gex44, until=freeze (`/tmp/ao_probe/kme_ref.py`, 21.6 s): **KME active sessions 102, calls 34871, cr 11549646300** (exact frozen match). All 568 scanned sessions: 66,092 calls; classes `KME_STRONG` 101 (+`KME_PATH` 1 = arena2), `KME_WEAK` 39, `NONE` 427.
- v4 `usage_index` cold build over the same 6 dirs (`/tmp/ao_probe/time_v4_core.py`): 979 files, 3,053,908,888 B, 67,206 upserts -> 67,188 call rows, wall 15.7 s, RSS 76 MB, DB 34.7 MB; no-op re-refresh 0.104 s (0 files read). `calls <= until`: 65,935.
- Joined per session (by file path -> `(project, first path component)`): the KME sessions sum to 34,853 calls / 11,544,130,372 cache_read under v4; exactly ONE session differs: `9184ed39` ref 403 calls / 183,268,169 cr vs v4 385 / 177,752,241. Delta = **18 calls / 5,515,928 cache_read**. Cause measured: those 18 `(msgid|requestId)` keys also occur in `867896c0-a893-49dc-8010-0c731250e5ae.jsonl` (a different, non-KME session in the same project) and v4's first-writer-wins `calls.file` assigned them there; `9184ed39`'s own 3 files hold 403 unique keys, 0 keys shared among themselves [VERIFIED: /tmp/ao_probe/dup_probe.py, dup_probe2.py]. So: per-session occurrence view = 34,871 (frozen); globally de-duplicated unique-call view = 34,853. Both are valid answers to different questions; the plan must report both and name the unit ("API request = msgid|requestId").
- Zero null-timestamp calls in the v4 index of these dirs; `ts <= until` agrees with the champion's per-line cut for all 101 other sessions (no streamed call straddles the freeze in this scope).

## Transcript record shape (sampled from the corpus copy)

[VERIFIED: /tmp/ao_probe/sample_shape.py, sample_shape2.py on 16 mid-size Core-Files transcripts and one arena2 file]
- Top-level line keys: `type` (`assistant|user|attachment|queue-operation|atis-latch|last-prompt|custom-title|system|...`), `sessionId`, `timestamp`, `uuid`, `parentUuid`, `isSidechain`, `entrypoint`, `cwd`, `version`, `gitBranch`. `cwd` is on most lines but not all (arena2 file: 22 of 28 lines).
- `cwd` is the RECORDING machine's path: `"C:\\Users\\User\\Apps\\kme-wt-arena2"`. It must be parsed as a Windows path (`ntpath`) on GEX44 and must NEVER be passed to `os.path.realpath` here. Store-dir name == `re.sub(r"[^A-Za-z0-9]", "-", cwd)` of the launch cwd (`project_key`, tis_observed.py:340-346) for 16/16 sampled sessions, so the home project is recoverable from the store dir; the reverse (dir name -> path) is lossy.
- tool_use block inside an assistant `message.content` list: `{"type": "tool_use", "id": "toolu_015sAvzHzgj6pbppx3oaMJxr", "name": "Read", "input": {"file_path": "C:\\Users\\User\\.claude\\skills\\claude-power-pack\\commands\\compound.md"}, "caller": {"type": "direct"}}`.
- Tool names seen in the sample (counts): PowerShell 523, Read 302, Edit 271, Grep 214, Write 149, Bash 35, Glob 26, Agent 10, AskUserQuestion 8, ToolSearch 6, SendMessage 4, Skill 3. Existing code accepts `SPAWN_TOOLS = ("Agent", "Task")` [VERIFIED: usage_index.py:352].
- tool_result sits in a LATER `type=user` line: block `{"tool_use_id": ..., "type": "tool_result", "content": <str|list>}` (block keys exactly `tool_use_id, type, content`; `is_error` appears only on errors); content type counts in the sample: `str` 1512, `list` 42. The same user line carries `toolUseResult` (dict for Read: `{"type":"text","file":{"filePath","content",...}}`), `sourceToolAssistantUUID`, `promptId`, optional `toolDenialKind` (38/1554). `_spawn_results` already derives a result body from str-or-list-of-`text` items (usage_index.py:189-191); reuse that exact flattening for `result_bytes`.
- cwd varies inside a session (4 of 16 sampled), but only to SUBDIRECTORIES of the same project (e.g. `...\KobiiCraft Core Files\KobiCraftServer\plugins\KobiMapEngine`), so a cwd change is not by itself "mixed project".
- Mixed-project reality [VERIFIED: /tmp/ao_probe/mixed_archived.py, all 565 top-level Core-Files transcripts]: 221 of 565 sessions issue at least one tool call on an absolute path outside the Core-Files root; of 31,741 absolute tool paths 14,489 are outside it. Top outside prefixes: `C:/Users/User/AppData/Local` 5,077, `.../Desktop/Repos-GitHub` 3,833, `.../Desktop/Cursor Projects` 1,229, `.../.claude/projects` 762, `.../.claude/skills` 523, `.../Apps/kme-wt-arena3` 519, `.../Apps/kme-wt-arena2` 484, `.../Apps/cpp-goal-spine-wt` 311. => "mixed allowed" is the NORM; a rule that attributes every outside path would flag 39 % of sessions, and non-project locations (AppData, `.claude/projects`) are noise, not projects.

## Architecture Patterns

### System flow (data flow, one read pass)
```
projects root --store_identity--> canonical store dirs (+alias map)
   |  _iter_files: shape A top/*.jsonl, shape B */subagents/*.jsonl, shape C _archived/<proj>/... (declared)
   |  unmatched *.jsonl found by os.walk --> meta.skipped_shapes (typed count + sample paths; never silent)
   v
stat gate (size+mtime_ns) --unchanged--> skip (0 bytes)
   | changed/new
   v
calls_from(fp, offset, on_line) -- single read of NEW bytes only
   |-- usage lines ---------> calls (global key)  + call_files (k, file)   [occurrence]
   |-- tool_use blocks -----> tool_events (id, tool, input_hash, path, pat_hits, ts, file)
   |-- user tool_result ----> UPDATE tool_events.result_bytes/result_chars/is_error
   |-- cwd field -----------> file_cwds (distinct cwd + first offset) -> attribution rows
   |-- user human text -----> user_hits (sparse, only when a registered pattern hits)
   |-- bad line / OSError --> files.parse_errors, files.error  (surfaced in refresh() status)
   v
files row: offset, size, mtime_ns, first_ts, last_ts, v5_from, content fingerprint
   v
population(con, scope, until) --> {verdict: EXACT|DRIFTED|UNMEASURED, per_project, reconcile rows}
```

### Recommended structure (all inside existing files)
```
tools/usage_index.py          # SCHEMA_VERSION=5, _migrate_v5, v5 on_line extractors, population verb
tools/tis_observed.py         # only if calls_from needs a bad_lines out-param (additive, default-compatible)
tools/test_usage_index_v5.py  # NEW V-UX5-* gates (a test file, not a new module)
tools/test_usage_index_identity.py  # Wave-0 fix: junction() falls back to os.symlink on Linux
```

### Proposed v5 DDL (PLAN-mode design for approval; every column additive, none alters v4)
```sql
-- files: identity + coverage + errors
ALTER TABLE files ADD COLUMN realpath TEXT;     -- os.path.realpath(path) at ingest (file-level, not tool paths)
ALTER TABLE files ADD COLUMN store TEXT;        -- top-level dir under the root ('_archived' for archived)
ALTER TABLE files ADD COLUMN project TEXT;      -- project dir name ('_archived/<proj>' -> <proj>)
ALTER TABLE files ADD COLUMN archived INTEGER;  -- declared _archived rule
ALTER TABLE files ADD COLUMN session_key TEXT;  -- path-derived sid (== kme_token_audit sid)
ALTER TABLE files ADD COLUMN first_ts REAL; ALTER TABLE files ADD COLUMN last_ts REAL;
ALTER TABLE files ADD COLUMN parse_errors INTEGER; ALTER TABLE files ADD COLUMN error TEXT;
ALTER TABLE files ADD COLUMN v5_from INTEGER;   -- byte offset from which v5 rows are complete; NULL = legacy, UNMEASURED
ALTER TABLE files ADD COLUMN content_id TEXT;   -- see Open Question 2
CREATE TABLE IF NOT EXISTS call_files(k TEXT, file TEXT, PRIMARY KEY(k, file));   -- occurrence view
CREATE TABLE IF NOT EXISTS tool_events(tool_use_id TEXT PRIMARY KEY, file TEXT, ts REAL, tool TEXT,
  input_hash TEXT, path TEXT, path_project TEXT, workstream TEXT, pat_hits TEXT,   -- JSON {"kme":n} only when >0
  result_bytes INTEGER, result_chars INTEGER, is_error INTEGER);   -- NULL result_* = no result seen yet, NOT zero
CREATE TABLE IF NOT EXISTS user_hits(file TEXT, off INTEGER, ts REAL, pat_hits TEXT, PRIMARY KEY(file, off));
CREATE TABLE IF NOT EXISTS file_cwds(file TEXT, cwd TEXT, first_off INTEGER, n INTEGER, PRIMARY KEY(file, cwd));
CREATE TABLE IF NOT EXISTS file_projects(file TEXT, project TEXT, role TEXT, evidence TEXT, n INTEGER,
  PRIMARY KEY(file, project, role));    -- role: home|touched ; project '<unattributed>' is a typed bucket
CREATE TABLE IF NOT EXISTS patterns(name TEXT PRIMARY KEY, regex TEXT, version INTEGER);   -- registered classifier patterns
```
This is a PROPOSAL (values are design choices, not in-repo constants). Rationale per table is in the Pitfalls and Don't Hand-Roll sections.

### Pattern 1: zero-reread additive migration (copy `_migrate_spawns` shape, own gate)
**What:** one `_migrate_v5(con)` called from `refresh()` after `_migrate_spawns`; `BEGIN IMMEDIATE`, re-read `meta.schema_version` inside, `ALTER ... ADD COLUMN` guarded by `PRAGMA table_info`, `CREATE TABLE IF NOT EXISTS`, `INSERT OR REPLACE INTO meta VALUES('schema_version','5')`. It opens no transcript, queues nothing, touches no offset. Legacy files keep `v5_from IS NULL` (typed UNMEASURED for v5 facts).
**Critical:** `_migrate_spawns` currently exits early on `int(row[0]) >= SCHEMA_VERSION` (usage_index.py:152). Bumping `SCHEMA_VERSION` to 5 without introducing `SPAWN_SCHEMA = 4` for that function makes a v4 DB re-run the spawn-backfill queue, whose `todo` is every file having a spawn with `result_ts IS NULL OR input_hash IS NULL` (usage_index.py:165-167); `_backfill_spawns` then re-opens those files (217). That is a re-read of already-ingested files.
**Measuring "zero re-reads":** wrap `builtins.open`/`os.open` (and `Path.open`) in the gate and assert zero calls whose path is under the fixture root during `connect()+_migrate_v5`; also assert `refresh()` returns `files_opened == 0` and `bytes_read == 0` on the first post-migration refresh of an unchanged tree. The existing precedent measures a migration by row equality (V-UXID-MIGRATION-TOTALS); that does not prove no read happened.

### Pattern 2: legacy coverage is typed, not zero
After migration, a pre-existing file has `v5_from = NULL`. When it later grows, only the NEW bytes produce v5 rows and `v5_from` is set to that offset. A reader asking "tool events for file F" must see coverage, never an empty set read as "no tools". History backfill is an explicit opt-in verb (`backfill-v5`, deadline-bound, reports bytes re-read separately) and is NOT part of migration or default refresh. A cold build on the corpus (the parity and cost measurements) has `v5_from = 0` everywhere.

### Pattern 3: attribution as a set with a role (mixed allowed)
`file_projects` holds one row per (file, project, role). Role `home` = the store project. Role `touched` = project of a tool path or cwd that falls under a DIFFERENT registered project root. Mixed = more than one distinct project for a session. Derive the root registry from data (distinct launch cwds in `file_cwds`), never a hand list (PR-COVERAGE-BY-CONSTRUCTION-001, project CLAUDE.md Liveness Standard corollary). Match by path-SEGMENT prefix on normalized Windows paths (case-insensitive, `\` -> `/`), never string prefix: a string prefix wrongly makes `...Core-Files` own `...Core-Files-KobiCraftServer`. A path under the session's own home root stays `home` even if a nested directory is itself a registered root (KobiCraftServer is a store dir too). Paths under no registered root (`AppData/Local`, `.claude/projects`) go to the typed `<unattributed>` bucket (visible, counted, never dropped, never a project). Workstream: nullable regex on tool paths and cwd (`.planning/workstreams/<ws>/`); mixed allowed the same way. [Design recommendation; thresholds and registry source are Claude's-discretion items for the plan.]

### Pattern 4: classifier features are stored per EVENT, time-sliceable
Because the frozen class is evaluated at `until`, store `pat_hits` per tool_use and sparse `user_hits` per qualifying user text, so `share(until)` and `user_kme_hits(until)` are SQL over `ts <= until`, and a session's class can be recomputed at any instant. Register `KME_RE` once in `patterns` by importing the compiled pattern string from `wiki/tools/kme_token_audit.py` at ingest (single source of truth) and assert in a gate that the stored `regex` equals `kme_token_audit.KME_RE.pattern`. Do NOT hard-copy the regex.

### Anti-Patterns to Avoid
- **Re-deriving session identity from in-line `sessionId`:** parity uses the path-derived `(project, first component)`; `_preserved`/`_empty_shells` would otherwise vanish or merge.
- **A `file` column that depends on ingest order** for any per-session figure (the measured 18-call gap).
- **Attributing by store dir name alone:** 221/565 sessions touch other roots.
- **Counting an unmatched file as "no data":** `_archived`, `_preserved`, `_empty_shells` are present and un-ingested today (silent zero class).
- **Storing raw tool input/result text:** hashes and byte counts only (HR-SECRET-002 spirit; `spawns.result_head` already keeps 200 chars, do not widen it).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Store/junction/symlink dedup | a second realpath walker | `tis_observed.store_identity` | declared single producer; usage_index consumes it (usage_index.py:240-245 comment) |
| Atomic additive migration | ad hoc ALTER at connect | `_migrate_spawns` pattern (`BEGIN IMMEDIATE`, in-txn version recheck) | two concurrent refreshes migrate once; reader never write-locks (audit G2) |
| Pre-destructive backup | custom copy | existing `_backup()` (sha256 + integrity_check) | already verified path |
| Tool_result text flattening | new str/list handling | the logic in `_spawn_results` | same two shapes (str, list of `text` items) |
| Input equivalence key | new hash scheme | `hashlib.sha256` truncated to 16 hex like `spawn_input_hash`, over canonical JSON (`sort_keys`, fixed separators) | consistent with v4; do not reuse `spawn_input_hash` itself (it hashes only subagent_type+prompt) |
| Parity verdict vocabulary | invent states | kme_pillars' `population_match: exact|drifted` + exit codes 0/2/3 (`EXIT_OK, EXIT_USAGE, EXIT_UNMEASURED = 0, 2, 3`, kme_pillars.py:78-region) | consumers (ledger, gates) already speak it |
| Windows path handling on Linux | `os.path` on recorded paths | `ntpath`/`PureWindowsPath` when `^[A-Za-z]:[\\/]` | records carry Windows paths; `os.path.realpath` would resolve against the wrong machine |

**Key insight:** every hazard in this phase is a place where an existing instrument returns "0" or "ok" for a thing it never looked at (archived shape, bad lines, order-dependent attribution, version-gate reuse). Build each new fact with a typed absence and a control that can return the other answer.

## Common Pitfalls

### Pitfall 1: SCHEMA_VERSION bump re-queues the spawn backfill (re-read)
**What goes wrong:** `_migrate_spawns` is gated on `SCHEMA_VERSION`; a v4 DB at version 4 sees `4 < 5`, re-queues files with unanswered spawns, `refresh()` re-reads them.
**How to avoid:** introduce a spawn-specific version constant; add a gate with a seeded v4 DB containing a spawn lacking `result_ts`, spy on `open`, assert 0 opens.
**Warning signs:** `meta.spawn_backfill` non-empty after v5 migration; `backfill_pending > 0` in the first refresh.

### Pitfall 2: `calls_from` swallows undecodable lines
**What goes wrong:** `except json.JSONDecodeError: continue` (tis_observed.py:153-154) loses a line with no trace; a corrupted transcript yields fewer calls and `status: OK`.
**How to avoid:** count per file into `files.parse_errors`; surface `parse_errors` and `error` in `refresh()`'s return and in `meta.last_refresh_status`; `population()` refuses (`UNMEASURED`) when any in-scope file has `parse_errors > 0` unless explicitly tolerated and then reports the count. Unterminated final line is NOT an error (read next pass).
**Warning signs:** `files_read > 0`, `calls_upserted == 0` for a file with size > 0.

### Pitfall 3: first-writer-wins attribution
Measured: 18 calls / 5,515,928 cache_read moved from session `9184ed39` to `867896c0`. A per-session or per-project view built on `calls.file` is a function of directory listing order. **Avoid** with `call_files`.

### Pitfall 4: time cut and class are coupled
Classifying on whole-file features and cutting calls at `until` afterwards will mis-class sessions that kept running after the freeze (3 files in the copy were still growing at copy time per the zero-rescan plan). **Avoid** with event-level `pat_hits` and `ts <= until` on BOTH the call sum and the feature counts; treat a session whose first kept timestamp > until as non-existent, not dead (kme_pillars.py:1658-1659), which needs `files.first_ts`.

### Pitfall 5: `--since-days` default prunes a cold build
`refresh` CLI defaults `--since-days 21` and skips files older than that by mtime (usage_index.py:445-446, 788). A "cold build" on the frozen 2026-10-05 copy would silently index only recent files. Pass `since_epoch=None` (add `--all` / `--since-days 0`) and assert `files_read == files_total`.

### Pitfall 6: Windows-only test helper
`tools/test_usage_index_identity.py:63-66` builds junctions with `["cmd", "/c", "mklink", "/J", ...]`; on this host it dies with `FileNotFoundError: 'cmd'` and 0 PASS [VERIFIED: ran it this session]. The "junction alias counted once" control cannot run on GEX44 until `junction()` falls back to `os.symlink` (the corpus itself uses relative symlinks).

### Pitfall 7: path normalization across planes
Tool paths and cwd are Windows strings from the laptop; GEX44's own sessions are POSIX. Normalize by shape, never resolve on disk, and keep the file-level `realpath` (transcript file) separate from tool-path strings. "realpath + content identity" in criterion 1 refers to the transcript file.

### Pitfall 8: scoping drift reads as corpus drift
Run 5 showed 105 vs 102 was pure scope (archived + alias). A parity result MUST print the reconcile table (per project, per scope rule) so a mismatch names its unit.

## Don't-do / Security Domain

> `security_enforcement` not disabled in config (absent = enabled); local-data tool, no network.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input validation | yes | transcript JSON is untrusted data: parse with `json.loads` guarded per line, never `eval`; all SQL parameterized (existing code uses `?` everywhere); paths are strings, never executed or joined onto the filesystem |
| V6 Cryptography | yes (hashing only) | `hashlib.sha256` for input hashes/fingerprints; no hand-rolled hash |
| V8 Data protection | yes | tool inputs/results may contain secrets: store hash + byte counts + normalized path only; never raw text (HR-SECRET-002); scratch DBs stay under `/tmp`/mission scratch, not the repo |
| V12 File handling | yes | corpus is read-only input; refuse writes under the corpus; a symlink to a dir OUTSIDE the root is a distinct store kept under its resolved path (store_identity docstring) |
| V2/V3/V4 | no | no authn/session/access-control surface |

| Threat | STRIDE | Mitigation |
|--------|--------|-----------|
| Crafted JSONL with huge line / invalid UTF-8 | DoS / Tampering | `errors="replace"` decode already used (tis_observed.py:148); per-line try/except now COUNTED; per-file error isolation |
| Symlink in corpus pointing outside root | Info disclosure | store_identity keeps it as its own resolved store; gate asserts index never opens a path outside the declared root |
| Path-traversal strings inside tool inputs | Tampering | tool paths are data only; never `open()`ed |

## Runtime State Inventory
Not a rename/refactor phase (additive schema). One state item is nonetheless real: **stored data** — any existing v4 index file (laptop `~/.claude/state/usage_index/index.sqlite`, laptop-only, HR-001 territory) will be migrated in place by the first v5 refresh there; that deployment is a laptop-only owner-bundle line, not a Phase 1 action. On GEX44 no default index exists (`ls ~/.claude/state/usage_index` empty), so Phase 1 creates scratch DBs only. Live service config / OS-registered state / secrets / build artifacts: none, verified by `grep -rn usage_index` over `hooks commands` returning nothing and `cost_gate`/`token_irr` being the only runtime readers.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| python3 | all | yes | 3.12.3 | - |
| sqlite3 (stdlib) | index | yes | 3.45.1 (`ON CONFLICT`, JSON1) | - |
| Corpus copy | parity, cost | yes | `/home/kobii/kme-corpus/projects`, 9.6 G, 344 top entries | none (HARD constraint) |
| `/proc/self/io` (rchar) | bytes cross-check | yes (Linux) | - | count `end-offset` sums only |
| Scratch dir for DBs | measurement | yes | `/tmp/ao_probe` used this session; use mission scratch for the real run | - |

Whole-corpus cold build (9.6 GB) NOT run (instructed). Free disk for the scratch DB was not measured; v4 DB for the 3.05 GB KME scope is 34.7 MB, so the whole-corpus v5 DB is expected tens to low hundreds of MB [ASSUMED extrapolation].

## Validation Architecture

> `workflow.nyquist_validation` treated as enabled (key absent from the instructions; not set false).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | repo V-gate scripts (plain Python, `ok(gate, cond, evidence)`, final line `X_PASS=n/n  threshold=n/n`); AAA + paired controls per `~/.claude/rules/python/testing.md` |
| Config file | none |
| Quick run command | `python3 tools/test_usage_index.py && python3 tools/test_usage_index_v5.py` |
| Full suite command | quick + `python3 tools/test_usage_index_identity.py` + the consumer set below + `python3 tools/test_incremental_cognition_program.py --generation 2 --selftest` |

Baseline measured this session: `python3 tools/test_usage_index.py` -> `USAGE_INDEX_PASS=22/22  threshold=22/22`. `python3 tools/test_incremental_cognition_program.py --generation 2 --status` -> `{"open": ["M", "O", "P", "Q", "R"], "closed": [], "violations": []}`. `python3 tools/test_usage_index_identity.py` -> crashes, 0 PASS (Windows `cmd`). Consumer regression set (not run here, run in Wave 0 to baseline): `tools/test_estate_shadow.py`, `test_fanout_ledger.py`, `test_root_progress.py`, `test_spawn_outcomes.py`, `test_spawn_policy_v2.py`, `test_async_spawns.py`, `test_goal_journey.py`, `test_execution_shape.py`, `test_displacement.py`, `test_store_identity_consumers.py`, `test_frontier_intelligence_os.py`, `test_token_ground_truth_junction.py`.

### Phase Requirements -> Test Map
| Req / clause | Behavior | Test type | Command (hermetic fixture unless noted) | Exists? |
|--------------|----------|-----------|-----------------------------------------|---------|
| O(1) schema | v5 tables/columns exist; tool event has tool, input hash, path, result bytes; cwd; attribution; realpath + content id | unit | `python3 tools/test_usage_index_v5.py` (V-UX5-SCHEMA, V-UX5-TOOL-EVENT, V-UX5-CWD) | Wave 0 |
| O(2) zero re-read | v4 DB -> v5 migration opens 0 files, 0 bytes; offsets untouched; spawn backfill NOT re-queued | unit with `open` spy | V-UX5-MIGRATE-ZERO-REREAD (+ control: a v1/v2-era DB or a deliberately grown file DOES read, so the spy can fire) | Wave 0 |
| O(3a) mixed project | one session with tool paths under two registered roots -> attributed to BOTH (roles home+touched); control: single-project session -> exactly one; unregistered path -> `<unattributed>`, not a project | unit | V-UX5-MIXED-BOTH, V-UX5-MIXED-CONTROL | Wave 0 |
| O(3b) distinct histories | two files same sessionId, diverging content -> two file rows, two content ids, shared prefix calls counted once globally and present in BOTH occurrence views; control: two byte-identical files -> one content identity, second recorded as duplicate, calls counted once | unit | V-UX5-HISTORIES-NOT-MERGED, V-UX5-COPY-ONCE | Wave 0 |
| O(3c) junction alias | symlink/junction alias of a store counted once; control: distinct dir with same file names counted twice; out-of-store link kept under resolved path | unit (symlink on Linux) | extend `test_usage_index_identity.py` + V-UX5-ALIAS-ONCE | partial (identity file broken on Linux) |
| O(3d) `_archived` | declared rule: archived files indexed with `archived=1`, excluded from default population, included on explicit flag, never double-counted with live; control: flag flips the count; undeclared/odd shapes land in `meta.skipped_shapes` with count > 0 | unit | V-UX5-ARCHIVED-RULE, V-UX5-SHAPE-SKIP-VISIBLE | Wave 0 |
| O(3e) parser failure | file with bad lines -> `parse_errors` = n, refresh status not plain OK-with-zero, `population()` refuses/flags; control: clean file -> `parse_errors` 0 and OK; unterminated tail is NOT counted as an error | unit | V-UX5-PARSE-ERROR-SURFACED, V-UX5-PARTIAL-LINE-NOT-ERROR | Wave 0 |
| O(3f) empty population | `population()` on 0 sessions -> `UNMEASURED` (never EXACT/PASS); control: non-empty -> EXACT/DRIFTED | unit | V-UX5-EMPTY-REFUSES | Wave 0 |
| O(4) parity | on `/home/kobii/kme-corpus/projects` scoped by the Run-6 filter, at `until=2026-10-03T16:13:37Z`: 102 / 34,871 / 11,549,646,300 via occurrence view; unique view 34,853 / 11,544,130,372 reconciled to the 18 shared keys; unfiltered reconcile table reproduces archived + alias rows | integration (corpus, minutes) | `python3 tools/usage_index.py population --root /home/kobii/kme-corpus/projects --db <scratch> --scope kme-l --until 2026-10-03T16:13:37Z` (verb to be created) | Wave N, measurement step |
| O(5) cost | cold build wall + bytes (+ rchar) and delta (append to scratch copies) wall + bytes == appended bytes | integration/measurement | `refresh --all --root ... --db <scratch>` twice; delta on scratch COPY (corpus is read-only) | executor step |
| ledger | pillar O row `{terminal, reason, evidence}` in gen2 `state`; `--generation 2 --selftest` stays green | gate | `python3 tools/test_incremental_cognition_program.py --generation 2 --status|--selftest` | exists |

### Negative-control design rules (each must be driven red then green)
1. Each refusal gate is paired with a control where the SAME instrument admits the case (a judge that refuses everything must not pass; precedent `tools/test_ao_p0.py` docstring: "a mutant passes only when the judge reports the defect AND the matching clean control was clean").
2. Mutants to kill (apply to a temp copy of `usage_index.py`, run the gate, require RED): drop the occurrence insert; make `population()` return EXACT on an empty set; remove the `parse_errors` increment; remove the archived exclusion; bypass `store_identity` dedup; make migration touch a file offset; pin `_migrate_spawns` back to `SCHEMA_VERSION` (must turn the zero-re-read gate red).
3. A `population()` verdict is typed: `EXACT | DRIFTED | UNMEASURED`; `DRIFTED` and `UNMEASURED` exit non-zero; absent value is never zero.
4. Parity numbers are asserted as literals only on the real corpus step; hermetic gates assert relationships (counts equal fixture-known values), not corpus constants.

### Sampling Rate
- **Per task commit:** `python3 tools/test_usage_index.py && python3 tools/test_usage_index_v5.py` (hermetic, seconds; v4 gate alone ran in well under 150 s timeout).
- **Per wave merge:** + identity gate + consumer regression set + `--generation 2 --selftest`.
- **Phase gate:** hermetic suite green, THEN the two corpus measurement steps (parity, cost) with commands and output pasted into `01-EVIDENCE.md`, every row labelled `plane: gex44`.

### Wave 0 Gaps
- [ ] `tools/test_usage_index_v5.py` - covers all O clauses (new test file).
- [ ] `tools/test_usage_index_identity.py` - `junction()` Linux fallback (`os.symlink`), so "junction alias counted once" runs on GEX44.
- [ ] Baseline run of the consumer set above on the untouched tree (none were executed in this research).
- [ ] Decide Open Questions 1-4 in the PLAN design step before the first code edit (ROADMAP: PLAN mode).

## Measured Cost Baseline (v4, for the criterion-4 comparison)
| Build | Scope | Files | Bytes | Wall | RSS | DB | Notes |
|---|---|---|---|---|---|---|---|
| v4 cold | 276 small dirs (symlink root) | 181 | 122,241,986 | 0.70 s | 31 MB | 0.59 MB | 828 calls; not representative |
| v4 cold | KME-L frozen scope (6 dirs) | 979 | 3,053,908,888 | 15.7 s | 76 MB | 34.7 MB | page-cache state unknown (probes earlier read these files); label as WARM-ish |
| v4 no-op re-refresh | same | 0 read | 0 | 0.104 s | - | - | stat gate only |
| champion scan | same 6 dirs, 568 sessions | - | ~2.83 GB read (Run 6) | 21.6 s here / 24 s Run 6 | 99 MB | - | one pass over the scope |
| champion unscoped population | whole corpus | - | 101.53 GB read | 869 s | 184 MB | - | 10 scans (Run 5) |
The whole-corpus v5 cold build and a v5 delta are the executor's measured steps; the executor should record wall, `bytes_read` from `refresh()`, `rchar` delta from `/proc/self/io`, and whether the page cache was cold (`rchar` counts cache hits, per zero-rescan Run 5 note).

## State of the Art
| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Per-run rescan of raw transcripts by ~10 parsers; unscoped KME population 869 s / 101.5 GB | Index once, query many (this phase builds the substrate; Phase 2 consumes it) | scoped champion already 36x cheaper before any index (zero-rescan plan:85-88) |
| first-writer-wins call attribution | occurrence table + global unique view | per-session reproducibility |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The occurrence view (call_files) will reproduce 34,871 exactly (inferred from the single-session join, not built yet) | Parity | If another cross-file effect exists the executor must reconcile it to the unit; plan keeps the reconcile table mandatory |
| A2 | Whole-corpus v5 DB is tens to low hundreds of MB | Environment | Disk/time budget wrong; measure on the executor step |
| A3 | `NotebookEdit` carries its path under `notebook_path` (not `file_path`) | Pattern for tool path extraction | Path NULL for notebook edits; kme uses `file_path` for `NotebookEdit` (kme_token_audit.py:51-52), so treat `file_path` first and add `notebook_path` only if sampled |
| A4 | Tool event rows for the KME scope are ~39k (kme D file `tool_uses: 38982`) and < 1M for the whole corpus | DDL sizing | Larger DB; no design impact |
| A5 | Page cache was warm for the 15.7 s v4 timing | Cost baseline | The cold-disk figure is higher; the executor must state cache state |
| A6 | Fork/resume transcripts are what share the 18 keys between `9184ed39` and `867896c0` (cause of sharing not inspected beyond key identity) | Pitfall 3 | None for the design: occurrence table is correct regardless of cause |

## Open Questions

1. **Occurrence view vs unique view as the parity headline.**
   - Known: occurrence = 34,871 (frozen), unique = 34,853; gap is 18 shared keys.
   - Unclear: which the Owner treats as "the unit". 
   - Recommendation: gate on the occurrence view reproducing the frozen number, report the unique view and the 18-call reconcile row beside it, label the unit "API request = msgid|requestId" for cost questions (project rule: dedup reconciled to the unit).
2. **Content identity scheme under append-only growth.**
   - Known: a full-file hash re-reads ingested bytes on every append; a head-only hash cannot distinguish forks sharing a head.
   - Recommendation to decide at plan time: `content_id = sha256(size_at_ingest || sha256(first 64 KiB) || sha256(last 64 KiB read at ingest end))` computed from buffers already read in the same pass, recomputed only when the file changes; "distinct histories" are never merged on `content_id` or `sessionId` alone (file identity stays `realpath`; merging happens only at the call key); a byte-identical copy detected by equal `(size, head, tail)` plus equal call-key set is marked `dup_of` and ingested once. Measure and report the tail-overlap bytes in the delta cost.
3. **`_archived` declared rule.** Recommended text: "`_archived/<project>/...` files are indexed with `archived=1`, `project=<project>`; default population queries exclude archived; `--include-archived` includes it; archived and live never merge (no live twin was found among 150 files)." Confirms Run 6 (frozen scope excludes it). Alternative (include by default) would break parity (adds 1 session / 649 calls).
4. **Odd shapes (`_preserved`, `_empty_shells`).** Recommended: not sessions; counted in `meta.skipped_shapes` (count + sample paths) so absence is typed. Verify at the executor step that the 102-session set is unchanged with them excluded (they were KME_WEAK / 0 calls in this scope).
5. **Does Phase 2 need `result_chars` (kme measures chars)?** Recommended: store both `result_bytes` (criterion text) and `result_chars` now; cheaper than a second ingest.

## Project Constraints (from CLAUDE.md)
- Project `CLAUDE.md` (`/home/kobii/missions/autonomous-optimization/CLAUDE.md`): Reality Contract (no stubs/placeholders/empty catch); Liveness Standard: before declaring a module done run `python modules/liveness/reachability.py` (usage_index is existing and cost_gate-wired, so no new registration expected; still run it); HR-NOVELTY-001 (EXTEND_EXISTING_OWNER recorded in Phase 0); HR-SECRET-002/006 (no raw secrets in stored text or emitted context); commits with explicit pathspec, verify `git log -1 --format=%s` and amend if the shared `COMMIT_EDITMSG` race swapped the message; DONE requires observed test output (Completion Gates: tsc N/A, lint, tests, scaffold audit, empirical evidence).
- Global rules applied: `~/.claude/rules/python/testing.md` (AAA, V-gate naming `V-<DOMAIN>-<NAME>`, final `DOMAIN_PASS=n/n threshold=n/n`, mock only at boundaries, paired controls, fail-open branches need dedicated tests); never-hang doctrine (any measurement run backgrounded must be read on notification, no polling); instrument-before-claim (every measured figure above names its command); SDD-OS: T2+ requires a covering spec (`vault/specs/autonomous-optimization.md`, `covers:` front matter) before the first edit.
- Phase constraints: do not edit gen2 `frozen`, CE/SC/IC-gen1 ledgers' `frozen`, the two forbidden test files, root `.planning/STATE.md`, `tools/gsd_mission.py`.

## Sources

### Primary (HIGH confidence; read/ran this session)
- `tools/usage_index.py` (whole file), `tools/tis_observed.py` lines 30-418, `tools/test_usage_index.py`, `tools/test_usage_index_identity.py` (junction helper), `tools/ic_gen2.py` (state row shape, G2 rules), `tools/test_ao_p0.py` (gate style).
- `wiki/tools/kme_token_audit.py`, `wiki/tools/kme_pillars.py` (scan/population/make_keep), `wiki/tools/kme_report.py:35-39`.
- `vault/programs/incremental-cognition/gen2/ledger.json` (pillar O rule), `.../denominators/kme_audit_2026-10-03.json`, `.../gen2/evidence/champion/run5|run6-r4-population.log`, `.../measurements/D-KME-L-2026-10-05.md`, `vault/plans/zero-rescan-reality-scan-2026-10-05.md`.
- Corpus probes: `/tmp/ao_probe/{sample_shape,sample_shape2,shapes,mkroot,time_v4,time_v4_core,kme_ref,join_v4,dup_probe,dup_probe2,mixed_archived}.py` (outputs quoted above; scripts are scratch, not repo files).

### Secondary / Tertiary
- None. No web or Context7 lookups were needed (stdlib + repo-internal domain; no external packages).

## Metadata
**Confidence breakdown:**
- Current-code facts: HIGH - read with line numbers.
- KME-L filter/classifier and parity reproduction: HIGH - champion parser re-run reproduced the frozen numbers exactly this session.
- v5 schema/attribution design: MEDIUM - proposal; Open Questions 1-5 to be fixed in the PLAN design step.
- Whole-corpus cost: LOW - deliberately not measured.

**Research date:** 2026-10-06
**Valid until:** until `tools/usage_index.py`, `tis_observed.py`, `kme_token_audit.py` or the corpus copy change (re-verify the parity reproduction if any of them does).
