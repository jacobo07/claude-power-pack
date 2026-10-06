# Phase 2: KME-L challenger - Research

**Researched:** 2026-10-06 (plane: gex44, host `kobicraft-gex44`, worktree `ao-gen2`, python 3.12.3)
**Domain:** extending the KME measuring instruments (`wiki/tools/kme_pillars.py`, `kme_replay.py`) with an index-first access plan over `tools/usage_index.py` v5
**Confidence:** HIGH on what exists and what the index lacks (every file below was read this session); MEDIUM on the recommended design (no challenger exists yet; its cost is a prediction, tagged ASSUMED where so)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
(CONTEXT.md `## Implementation Decisions / Carried facts`, copied)
- Champion Run 5, unscoped: wall 869 s, read 101.53 GB (spec line 61). Champion Run 6, scoped to `KobiiCraft-Core-Files|kme-wt-arena2`: 24 s, 2.83 GB (spec line 62). These are the numbers to beat.
- Frozen KME-L denominator: 102 sessions, 34,871 calls, cache_read 11,549,646,300 (`vault/programs/incremental-cognition/denominators/kme_audit_2026-10-03.json`).
- Phase 1 substrate: `tools/usage_index.py` v5. `population --select kme --until 2026-10-03T16:13:37Z --expect KME-L` on `/home/kobii/ao-scratch/p1/cold.sqlite` is EXACT (01-EVIDENCE.md, re-run 2026-10-06 after the review fixes). The index reports MEASURED / EXACT / DRIFTED / UNMEASURED and refuses (UNMEASURED) on a legacy file, parse errors, file errors, pattern drift, or an unreadable `--until`.
- Corpus: `/home/kobii/kme-corpus/projects` (Owner-authorized copy), passed explicitly as a root; results are labelled `plane: gex44` (spec line 163).

### Claude's Discretion
(recorded choices, copied)
- The challenger is an EXTENSION of `wiki/tools/kme_pillars.py` (and `kme_token_audit.py` / `kme_replay.py` where they produce the measurement files) that reads from the usage_index; no new parallel engine (AO-09 "challenger by extension", HR-NOVELTY-001). Reason: the owners exist and the spec names them.
- The champion and the scoped path stay callable unchanged (KS-4); the challenger is opt-in until certified.
- Any UNMEASURED answer from the index is a deopt to the scoped raw path with the index's reason logged, never a zero or a partial number.
- Equivalence is byte-identical output of the 7 measurement files, compared by hash, with a negative control (one perturbed file must be reported as different).
- Cross-project exposure is measured by the files actually opened (strace or an open-hook), not by the selector's intention; the negative control is a deliberately unscoped run that must show non-zero CostaLuz bytes.
- Never write the literal slop marker words in any file (Owner directive 2026-10-06); build such lists from fragments.

### Deferred Ideas (OUT OF SCOPE)
None beyond the info-level review notes (IN-02 `--perturb` without `--expect` ignored; IN-03 booleans accepted as counts in `expected`; IN-04 a session with no `first_ts` drops out under `--until` without a reason). The planner may fold IN-04 in if the challenger relies on `--until`.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AO-07 | champion/challenger, shadow/canary/certify/deopt (gate 9-10) | Sections 2, 4, 6: three-tier plan, guard list, deopt reason log, KS-4 forced-plan switch, champion-vs-scoped-vs-challenger table protocol |
| AO-09 | KME-L measured, challenger by extension, equal-or-stronger, no unrelated-project raw reads (gate 14-18) | Sections 1, 2, 3: the 7 files, per-file index gap, equivalence comparator, strace open-set measurement with a CostaLuz control |
</phase_requirements>

## Summary

The seven KME-L measurement files are committed under `vault/programs/incremental-cognition/measurements/` (`{D,E,F,G,H,I,L}-KME-L-2026-10-05.md`). D..I come from `wiki/tools/kme_pillars.py`, L from `wiki/tools/kme_replay.py rank`; all seven were produced by the SCOPED champion (`--project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --until auto --expand`). I re-ran the scoped champion for D..I in one scan (`all`, 30.9 s) into a scratch out-dir and diffed against the committed files: they are byte-identical except `measured_at`, `command`, and in H the `commit` of `consumed_owner_verdicts` (it embeds git HEAD). So the champion is deterministic and the equivalence comparator is a normalised byte compare with exactly those three volatile fields masked.

The central finding for planning: **the v5 stored rows answer the population, the selection, the scope, the watermark and (almost) pillar I, and nothing else.** The index deliberately stores no attachment, no tool-result content hash, no command text, no assistant text, no compaction positions (HR-SECRET-002, `tools/usage_index.py:717-722`). Pillars D, E, F, G, H and L each need those. A challenger that is "index rows only" cannot reproduce six of the seven files. The honest design is a three-tier access plan whose middle tier is new and cheap: **index-selected raw** (open only the files of the sessions the index selected: 364 of 979 scoped files, 1,648,219,354 of 3,053,908,888 bytes = 54.0 %, measured below), optionally topped by a **per-file derived-facts sidecar** keyed on the index's `content_id` so a repeated query opens zero raw bytes.

The scoped path is already a 36x win over the champion (869 s to 24 s); the challenger may legitimately lose to it (ROADMAP criterion 5, frozen rule P allowed loss D-OQ4). Plan the work so the cheap, certain gain (index-selected raw, no new store) lands and is measured first; the facts sidecar is a second increment whose cost/benefit decides between `IMPLEMENTED_AND_VERIFIED` (possibly narrowed) and `FALSIFIED_OR_REJECTED_BY_EVIDENCE`.

**Primary recommendation:** extend `kme_pillars.py` with `--plan auto|challenger|scoped|champion` (KS-4), a guard chain over `usage_index.population()` + watermark/version checks, a JSONL path log with deopt reasons, and an open-set measurement tool (strace based) that gives the five table columns; ship index-selected raw first, measure, then decide on the facts sidecar.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Which sessions are KME-L, at what cost, as of an instant | `tools/usage_index.py` `population()` (index) | `wiki/tools/kme_pillars.py` (consumer) | Champion classifier is loaded by path inside the index; no second selector may exist (`usage_index.py:1725-1737`) |
| Access plan, guards, deopt, path log, KS-4 switch | `wiki/tools/kme_pillars.py` (new code) | `wiki/tools/kme_replay.py` (reuses ctx) | The owner of the measuring run context (`_prepare`, `_resolve`, `_measure`) |
| Observer computation D..I, L | raw transcript bytes (scoped) | per-file facts sidecar (optional) | Observers read line text the index does not keep |
| Invalidation (watermark, parser, attribution, metric) | index `files` + `meta` rows | sidecar keyed on the same ids | Reuses `content_id`, `pat_ver`, `attr_version` already stored |
| Exposure measurement (files opened, bytes, cross-project) | OS layer (`strace`) | `/proc/self/io` as cross-check | A selector's intention is not evidence; opens are |
| Equivalence judgement | new gate in `tools/test_kme_*.py` | committed measurement files | Normalised byte compare plus a perturbed negative control |

## 1. The seven KME-L measurement files

All seven live in `vault/programs/incremental-cognition/measurements/` [VERIFIED: `ls -la`, 7 files dated Oct 5 21:22, commit `7ea78fa3` "measure(incremental-cognition): rows 4-10 D-I + L on KME-L, plane gex44, population exact"].

| File | Producer (instrument) | Observer class | Committed `command:` (front matter line 13/14) |
|---|---|---|---|
| `D-KME-L-2026-10-05.md` | `wiki/tools/kme_pillars.py d` | `DObserver` (`kme_pillars.py:458`) | `python3 wiki/tools/kme_pillars.py d --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files\|kme-wt-arena2'` |
| `E-...` | `kme_pillars.py e` | `EObserver` (`:580`) | same with `e` |
| `F-...` | `kme_pillars.py f` | `FObserver` (`:748`) | same with `f` |
| `G-...` | `kme_pillars.py g` | `GObserver` (`:1038`) | same with `g` |
| `H-...` | `kme_pillars.py h` | `HObserver` (`:1398`) | same with `h` |
| `I-...` | `kme_pillars.py i` | `IObserver` (`:1551`) | same with `i` |
| `L-...` | `wiki/tools/kme_replay.py rank` | `RolloverObserver`, `RereadObserver(kp.EObserver)`, `RetryObserver` (`kme_replay.py:266,304,377`) | `python3 wiki/tools/kme_replay.py rank --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files\|kme-wt-arena2'` |

`OBSERVERS = {"D": DObserver, ... "I": IObserver}` [VERIFIED: `kme_pillars.py:1619`]; pillar L is NOT in `OBSERVERS`: it is a separate scan by `kme_replay.py`, which "scans the transcripts ONCE through kme_pillars' own run context ... imported, never forked" [VERIFIED: `kme_replay.py` docstring]. `RULE_DENOMINATORS = {"D": ("KME-L", "CPP-D-W7"), "E": ("KME-L",), ...}` [VERIFIED: `kme_pillars.py:83-84`]: the D file for CPP-D-W7 is not one of the seven.

Champion copies:
- The seven committed files above are the gen1 ledger champion evidence (the gen1 ledger `vault/programs/incremental-cognition/ledger.json` cites them; gen1 is never edited).
- Champion runs: `vault/programs/incremental-cognition/gen2/evidence/champion/` holds `run5-summary.txt`, `run6-summary.txt`, `run5-r4-population.log`, `run6-r4-population.log`, `gex44_ic_rows.sh` [VERIFIED: `ls`].
  - `run5-summary.txt`: `STEP r4-population exit=3 killed=no wall_s=869 peak_rss_MB=184 read_GB=101.53`
  - `run6-summary.txt` (verbatim steps): `r4-population wall_s=24 read_GB=2.83`, `r4-d-kmel 26 s 2.85`, `r5-e 24 s 2.77`, `r6-f 24 s 2.73`, `r7-g 28 s 2.85`, `r8-h 24 s 2.65`, `r9-i 25 s 2.80`, `r10-l-rank 26 s 2.82`, plus `r4-d-w7 exit=3 54 s 10.04` (not one of the seven).
  - Sum of the seven scoped file runs in Run 6: wall 26+24+24+28+24+25+26 = 177 s, read 2.85+2.77+2.73+2.85+2.65+2.80+2.82 = 19.47 GB (arithmetic on the summary lines). `read_GB` is the process `rchar` from `/proc/<pid>/io` (`gex44_ic_rows.sh:17-31`), so it counts page-cache hits and every read, not disk bytes.

**Fair scoped baseline (measured now, this session):** `python3 -I wiki/tools/kme_pillars.py all --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --out-dir /tmp/p2r-champ` took real 30.9 s and wrote D..I in ONE scan (`all` is the one-scan form). So the scoped cost of the whole 7-file query is `all` (about 31 s) plus `kme_replay rank` (about 26 s per Run 6) = about 57 s and about 2.8 GB x 2 scans, not 177 s. The spec's "24 s / 2.83 GB" is the population-only step. Table rows must say which scoped form they compare against.

**Reproducibility of the champion (measured):** diff of the 6 re-run files vs the committed ones shows only these differing lines: `measured_at` (front matter and the JSON block), `command` (front matter and JSON block), and in H the `commit` hash inside `consumed_owner_verdicts` (front matter line and JSON block), because `ce_owner_verdicts` runs `git rev-parse HEAD` / `git show HEAD:<ledger>` [VERIFIED: `kme_pillars.py:1365-1397`]. Committed H shows `"commit": "61909502f69ba01e81db9f935f13efce0a8f0c3e"`, the re-run `4426b82d645f61307cdcd8c7ec77ca8fb1b19030`. The filename date differs too (`-2026-10-06` vs `-2026-10-05`).

**Equivalence comparator (prescriptive):** normalise the three volatile fields (`measured_at`, `command`, H `commit`, wherever they occur, front matter and JSON block) and compare sha256 of the rest. L also embeds `rollover_growth: 100000` and `ranked_ids: ["late_rollover", "identical_rereads", "unchanged_precondition_retries"]` [VERIFIED: `L-KME-L-2026-10-05.md` front matter]; I did not re-run L (not required to characterise the comparator). The comparator MUST be paired with a negative control: flip one digit in a copy and require a DIFFERENT verdict (Claude's-discretion decision, CONTEXT).

**Trap, `corpus.sessions_scanned`:** every file carries a `corpus` block with `"project_dirs": 6, "sessions_scanned": 568` [VERIFIED: `D-KME-L-2026-10-05.md:297-298`, `L-KME-L-2026-10-05.md:488-489`]. The index sees 552 sessions in the same 6 dirs (`population --detail` returned 552 rows) because the champion also counts `_preserved` / `_empty_shells` pseudo-sessions: 552 + 16 skipped shapes = 568 (`skipped_shapes` for the 6-dir tree is `"count": 16` per `O-cost-gex44.md`; `kme_token_audit.scan_project` treats the first path component of any `.jsonl` as a session id, `kme_token_audit.py` lines ~213-228). A challenger that scans only the selected files, or answers from the index, will print a different `sessions_scanned` unless it computes it as index sessions + skipped-shape census. This is a certain byte-diff if overlooked.

## 2. Index coverage gap per measurement file

What `tools/usage_index.py` v5 stores [VERIFIED: `usage_index.py:82-118`, quoted]:
`files(path, offset, size, mtime_ns, is_sub, entrypoint, + v5: resolved, store, project, archived, session_key, first_ts, last_ts, parse_errors, error, v5_from, head_sha, tail_sha, content_id, dup_of, pat_ver)`; `calls(k, file, ts, model, is_sub, entrypoint, inp, cw, cw5, cw1, cr, out)`; `call_files(k, file, ts, model, inp, cw, cw5, cw1, cr, out)`; `tool_events(file, tool_use_id, off, ts, tool, input_hash, input_bytes, path, pat_hits, result_bytes, result_chars, is_error, result_off)`; `user_hits(file, off, ts, pat_hits)`; `file_cwds(file, cwd, first_off, first_ts)`; `file_attribution(file, kind, name, role, n)`; `subagents(file, session, agent_type, tool_use_id, depth, model_meta)`; `patterns`, `meta`.
Counts on the Phase 1 DB (read-only query): files 3,965; calls 261,250; call_files 269,224; tool_events 303,998; user_hits 503; file_cwds 5,047; file_attribution 8,391; subagents 1,411.
By design no text is stored: "never the input or result text, HR-SECRET-002" [VERIFIED: `usage_index.py:719-722`].

| File | Raw inputs the observer reads (cite) | Answerable from v5 rows | Gap (needs raw bytes or a new store) |
|---|---|---|---|
| D | `type == "attachment"` lines: `attachment.type` (`hook_*`), `hookName`/`hookEvent`, additional-context char count `context_chars(a)`; compaction positions and the usage-call ordinal `idx` for `resident_calls` (`kme_pillars.py:458-548`) | `tool_uses` (tool_events count) and call counts | attachments (no table), compact_boundary positions (none), per-line call ordinal |
| E | Read `file_path` + `offset/limit/pages` range, Edit/Write counters, sha256 of the extracted Read result text, image blocks, stub-prefix class, compaction segment (`:580-692`) | Read events and path (`tool_events.tool/path`), `result_chars` | result content hash, read range, image flag, stub class, segment, residency |
| F | gsd doc `Read` paths (path column is enough), result chars, `attachment` type `file` content, skill-body / command-body user text prefixes, `gsd-tools ... init` command regex on Bash text, human-prompt turn counter, residency (`:748-917`) | Read path | attachments, user-text classes and turn count, Bash command text (index keeps only `input_hash`), residency |
| G | assistant `text` blocks split into sentences, falsification / sealed / re-test regexes, human-prompt turns, call spans, per-call weighted prefix (`:1038-1235`) | per-call weighted cost (`call_files`) | the assistant text itself (never stored by design), turn starts, call ordinals |
| H | Bash/PowerShell command text -> `verify_segment`, `cmd_signature`; `res_chars` of its result; residency; subagent `agentType`; and git HEAD CE-ledger verdicts (`:1398-1535`, `:1365`) | `subagents.agent_type`, call cost (`call_files`), `result_chars` | command text (only `input_hash` stored), residency; plus a non-corpus input (git HEAD) |
| I | per file: first non-synthetic call's `inp+cw+cr`, later calls, subagent type from meta.json, inline `isSidechain` lines (`:1551-1617`) | first call (call_files; ordering by file position is not stored, `ts` order may differ), `subagents.agent_type`, main vs sub (`is_sub`) | `isSidechain` flag per session, a position column for "first call", the meta.json `absent` semantics |
| L | `rollover` (per-call context, floor, compaction restarts, inline sidechain), `identical_rereads` (= E per thread), `unchanged_precondition_retries` (tool key = stripped Bash text or canonical input JSON, result presence, intervening writes, issuing message output tokens) (`kme_replay.py:136-520`) | call usage (`call_files`) | everything E needs plus tool-input keys (index `input_hash` is over `json.dumps(sort_keys=True)`; the retry key uses the stripped command text, so the hashes are not interchangeable), thread identity, compaction points |

Conclusion (VERIFIED by the reads above): only pillar I is close to index-only; D, E, F, G, H, L need data the index does not hold. Population (`sessions_active/dead/calls/input/cache_write/cache_read/output`, plus the weighted denominator), selection (`_kme_selector`), scope and watermark are index-answerable and are what every file's `Population` block and `corpus` block need.

Index answer for the scoped population, measured this session on `/home/kobii/ao-scratch/p1/cold.sqlite`:
- `python3 -I tools/usage_index.py population --db .../cold.sqlite --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --until 2026-10-03T16:13:37Z --select kme --host gex44 --expect KME-L --plane gex44` -> exit 0, verdict `EXACT`, real 0.98 s, 0 corpus files opened (strace: `grep -c kme-corpus` = 0 over 121 `openat` lines). Bytes read from the DB file: 899,150,356 in 219,547 reads (the DB is 489,816,064 bytes: read amplification of 1.8x). This is INDEX bytes and must appear in the table in its own column, never folded into "raw bytes".
- Same command with no `--project-filter` and no `--host`: verdict `DRIFTED`: 103 sessions, 34,999 calls, cache_read 11,583,711,413 vs frozen 102 / 34,871 / 11,549,646,300. The extra session lives in `C--Users-User--claude-skills-claude-power-pack` (128 calls). So the frozen KME-L population is only reproduced WITH the scope filter; this is why Run 5 (unscoped, `--until auto`) ended `exit=3` after 10 locator scans: the locator bisects for a cutoff that does not exist (`run5-r4-population.log`: `"method": "not_found", "scans": 10`).
- Selected sessions inside the scope (`population --detail`, 552 session rows): 102 selected (101 `KME_STRONG`, 1 `KME_PATH`), 412 `NONE`, 38 `KME_WEAK`. Joining the selected `(project, session_key)` pairs to `files` (archived = 0): **364 files, 1,648,219,354 bytes of 979 files / 3,053,908,888 bytes = 54.0 %**. That is the floor for "index-selected raw" with no new store.

Per-project split of the KME-L population (frozen file match, scoped run, `run6-r4-population.log` per_project): `...KobiiCraft-Core-Files` 101 sessions / 34,870 calls / cache_read 11,549,645,760, and `C--Users-User-Apps-kme-wt-arena2` 1 / 1 / 540.

## 3. Measuring files opened, raw bytes, unique bytes, cross-project bytes

Existing instrument: `/home/kobii/ao-scratch/p1/strace_sum.py` (host-local scratch, outside the repo) sums bytes returned by `read`/`pread64` per path from an `strace -y` log and collapses every path under `/home/kobii/kme-corpus` into one bucket `<corpus jsonl>` [VERIFIED: file read]. It cannot separate projects, count distinct opens, or compute unique bytes. The plan must add a repo-tracked tool (suggested `tools/strace_io_sum.py`) with the columns below and a positive control; it must not be the scratch file.

Strace is available: `/usr/bin/strace`, `strace -- version 6.8` [VERIFIED: `which strace; strace -V`]; ptrace works unprivileged here (the traced `population` run above succeeded). Recommended capture: `strace -f -y -e trace=openat,read,pread64 -o <log> <command>`; the Phase 1 evidence used the same shape with `-e trace=pread64,read` (`O-cost-gex44.md`). Add `readv,preadv` to the trace set only if a mutant that uses them is in the drill (SQLite default does not mmap).

Column definitions to pin (these are decisions the planner must write down):
- **wall**: untraced wall of the command (strace inflates it: the traced no-op refresh took 3.741 s vs 0.577 s untraced, `O-cost-gex44.md`). Take wall from separate untraced runs; take bytes from traced runs. Report cold (evicted with `/home/kobii/ao-scratch/p1/evict.py`, which uses posix_fadvise DONTNEED, residency unverified) and warm separately.
- **raw bytes**: sum of bytes returned by `read`/`pread64` on paths under the corpus root that end in `.jsonl` (counts re-reads).
- **unique bytes**: sum of file sizes of the distinct physical corpus files opened (key on `(st_dev, st_ino)`, because the corpus has 3 junctions: "4,368 paths -> 4,007 realpaths -> 3,884 contents" per `vault/plans/zero-rescan-reality-scan-2026-10-05.md` line 23).
- **raw files opened**: distinct corpus paths with a successful `openat`.
- **cross-project bytes exposed**: raw bytes on corpus paths whose project dir is outside the allowed scope set; the CostaLuz sub-count matches `(?i)costaluz` anywhere in the path (both spellings `...Cursor-Projects-CostaLuz-Lawyers` and `...Cursor Projects-CostaLuz Lawyers`, the `-companion` dirs, and `_archived/*costaluz*/.../subagents`).
- **index bytes** (extra column, required for honesty): bytes read from the SQLite file(s). The challenger trades raw bytes for index bytes; omitting this column would make the challenger look better than it is.

CostaLuz measured size in the corpus (read-only `find`, this session): `find . -ipath '*costaluz*' -name '*.jsonl'` = 44 files, 99,693,228 bytes (13 files directly in `C--Users-User-Desktop-Cursor-Projects-CostaLuz-Lawyers` plus subagents and `_archived` copies). The reality-scan note says "22 files / 99 MB" for the live dir; use the case-insensitive full-path sum, 44 files, so an archived copy cannot hide.

Negative control for "a KME-only query opens zero CostaLuz bytes":
- Primary (cheap, 99.7 MB extra): run the same scoped query with `--project-filter 'KobiiCraft-Core-Files|kme-wt-arena2|CostaLuz'`; the measurement tool must report non-zero CostaLuz bytes (about 99.7 MB if every file is opened). If the tool reports zero here, the check cannot fail and is void.
- Secondary (CONTEXT wording, "deliberately unscoped run"): one unscoped SINGLE-scan query with an explicit `--until 2026-10-03T16:13:37Z` (never `--until auto`: unscoped auto is 10 scans = 101 GB, 869 s). Corpus whole is 9,932,073,959 bytes (`O-cost-gex44.md`), about 9.5 GB per scan, at the scoped rate (2.8 GB in about 25 s) roughly 85 s untraced and several minutes under strace. Time-box with `timeout 170`; if it does not finish, record "not run: exceeds the 3-minute bound" rather than a number.
- Exposure at the index layer: the Phase 1 DB is a whole-corpus DB (3,965 files, includes CostaLuz rows). A query against it reads SQLite pages that contain CostaLuz metadata (paths, hashes, counts) though no transcript byte. The metric above counts transcript bytes only; the planner must state that scope explicitly and decide (open question 2) whether a KME-scope DB is required.

Read-only proof for the corpus: reuse `/home/kobii/ao-scratch/p1/manifest.py` (manifest sha256 before/after = `6eab1abced4f04cf4b601c22cf3695e7d7ae3fd31898698fdc2b7625fd10e6a9`, `O-cost-gex44.md` "Read-only proof"). Also assert the index DB's sha/mtime unchanged by a query. `usage_index.connect()` runs `con.executescript(SCHEMA)` (CREATE IF NOT EXISTS) on every open [VERIFIED: `usage_index.py:153-158`], so a "reader" is not literally read-only at the API level; the challenger should open the DB with `sqlite3.connect("file:...?mode=ro", uri=True)` for pure reads, or copy the DB for tests.

## 4. Invalidation keys

Exist today [VERIFIED by reading `usage_index.py` and a read-only query of `meta`/`files`]:
- Per file: `files.size`, `files.offset`, `files.mtime_ns`, `files.content_id` = `sha256(f"{end}|{head_sha}|{tail_sha}")[:32]` (`usage_index.py:986-990`), `files.head_sha`, `files.tail_sha`, `files.v5_from`, `files.pat_ver`, `files.error`, `files.parse_errors`.
- Pattern identity: `PATTERN_SOURCES = (("kme", "wiki/tools/kme_token_audit.py", "KME_RE"),)` (`:649`); `meta.pattern_set` = `ea55662c24602695a4260561d40e06d2dcdd0f74007624b4f7e4a3220ae7ccc9`; `patterns.kme.version` = `28807a6c1485`; every file's `pat_ver` equals that set (3,965 of 3,965); `population()` goes UNMEASURED on drift against `_live_pattern_set()` (`:1740`).
- Attribution: `ATTR_VERSION = 1` (`:815`), `meta.attr_version` = `1`, `meta.attr_registry` = `68eac513ab01541ffa50cee65495fb7f92ba8c8db58650f765823ddca45ca08a` (digest of the discovered root registry, `_registry` `:848-873`).
- Schema: `SCHEMA_VERSION = 5` (`:79`), `meta.schema_version` = `5`; it is a migration marker, not a re-read trigger (`SPAWN_SCHEMA = 4`, `:80`).

Missing for criterion 4 ("source watermark, parser version, attribution version, metric definition"):
1. **Parser version** of the code that fills the rows and (new) the facts: nothing records it. `pat_ver` covers only the KME regex; the line parser `_v5_line` and the observers have no version or digest. Add a digest over the sources that determine the numbers: `wiki/tools/kme_token_audit.py`, `wiki/tools/kme_report.py`, `wiki/tools/kme_pillars.py` (observer section), `wiki/tools/kme_replay.py`, `tools/usage_index.py`. Suggested key: `sha256` of the concatenated file bytes per owner group, stored beside the facts.
2. **Metric definition** is absent: the constants and definition strings live in code (`WEIGHTS`, `CPT_LO`, `CPT_HI`, `THRESHOLD` at `kme_pillars.py:78-81`; `H_DEFINITION`, `ESTIMATE_MODEL*`, `ROLLOVER_GROWTH`). Key it per pillar (hash of that pillar's constants + definition strings) so changing D's chars-per-token does not invalidate E's facts.
3. **Source watermark check at query time**: a stat of the in-scope files compared with `files.size`/`mtime_ns`, plus a directory listing of the scoped store dirs for new files. `refresh()` can only be pointed at a whole root (`_iter_files_v5(proj)` enumerates every store via `_tis.store_identity`, `usage_index.py:346-361`); there is no store/project filter, so a "scoped refresh" does not exist. The no-op refresh walks 10,577 files (metadata only, 0 bytes, 0.577 s) and so touches CostaLuz directory entries.
4. **Closure definition**: the dependency of an answer is {file watermarks of the selected sessions} x {parser digest} x {attribution/pattern/selector identity} x {pillar metric digest}. "Invalidates exactly the affected closure" means: change one transcript -> only that file's facts (all pillars) and the aggregates of its session recompute; change one pillar's metric digest -> only that pillar's facts recompute; change the parser digest -> everything recomputes; every other entry reports a hit. Appending to a file recomputes the whole file (observer state is not resumable: E keeps per-path last-hash maps, G turn counters, D/E residency need the final call count), unlike `refresh`, which resumes at the byte offset.

## 5. Test conventions

- `tools/test_kme_pillars.py` (2,746 lines): hermetic synthetic transcript trees under a scratch dir; gates are `(name, fn)` tuples in a list (`("V-KMEP-AUDIT-BYTE-IDENTICAL-REAL", g_audit_byte_identical_real)` at `:2310`, `("V-KMEP-AUDIT-BYTE-IDENTICAL", g_audit_byte_identical)` at `:2534`); `--drill` runs the mutation drill; summary line `KMEP_PASS=n/m  threshold=m/m  skipped=..  inconclusive=..` (`:2554`). SKIP and INCONCLUSIVE are counted apart and never a PASS. Run now: `python3 -I tools/test_kme_pillars.py` -> `KMEP_PASS=89/89  threshold=89/89  skipped=0  inconclusive=0` in 13.3 s [VERIFIED: ran it].
- `V-KMEP-AUDIT-BYTE-IDENTICAL` pins `kme_token_audit.scan_file` with `observer=None, keep=None` byte-identical to the frozen instrument (comment at `kme_token_audit.py:76-80`). Any change to `kme_token_audit.py` must leave that default path untouched.
- `tools/test_usage_index_v5.py` (2,581 lines): gates call `gate(name, cond, evidence)`; groups run under `guarded(name, fn)` so a crash is a FAIL of its own; module globals `UX` and `TIS` are swapped to run mutants; `MUTANTS` list at `:2493`, `run_drill()` at `:2539`, `python3 tools/test_usage_index_v5.py --drill` prints `DRILL killed=k/n` and requires: control green first, every mutant killed, clean re-run after. Final line `USAGE_INDEX_V5_PASS=n/m  threshold=m/m` (`:2576`). Phase 1 recorded `DRILL killed=18/18` then 21/21 after the review fixes (STATE.md decisions). Not re-run here (it was out of the call budget); the Phase 2 plan must re-run it as a regression guard if `usage_index.py` is touched.
- Rule from `~/.claude/rules/python/testing.md` applies: V-<DOMAIN>-<NAME> naming, a paired control for every refusal, AAA sections, no mocking inside the unit under test.
- Zero-open spy convention: Phase 1 proves "zero re-read" with a spy on `builtins.open` (`import builtins` at the top of `test_usage_index_v5.py`, gate `V-UX5-MIGRATE-ZERO-REREAD`). Reuse that for the hermetic "index hit opens no corpus file" gate; use strace only for the real-corpus table.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib (`sqlite3`, `hashlib`, `json`, `subprocess`, `re`, `argparse`) | 3.12.3 on this host [VERIFIED: `python3 --version` via preflight recorded in the spec] | challenger, facts sidecar, comparator | every owner file is stdlib-only; no package install is needed |
| `tools/usage_index.py` v5 | `SCHEMA_VERSION = 5` | certified index | the substrate Phase 1 certified |
| `wiki/tools/kme_pillars.py`, `kme_replay.py`, `kme_token_audit.py`, `kme_report.py` | repo HEAD | champion and owners to extend | pinned by `V-KMEP-*` |
| `strace` | 6.8 | open-set and byte measurement | already used by Phase 1 evidence |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| strace | `/proc/<pid>/io` rchar | what Run 5/6 used; counts page-cache and the SQLite file, cannot name files, cannot show CostaLuz; keep only as a cross-check |
| facts sidecar DB | new tables inside `usage_index.py` SCHEMA | in-DB is simpler to join but changes a module that has just been certified (schema bump, drill re-run); the sidecar can `ATTACH` the index and leave Phase 1 untouched |
| Python `open` spy | `LD_PRELOAD` / eBPF | not needed; strace is installed |

**Installation:** none. **Version verification:** no external package is recommended, so no registry check applies.

## Package Legitimacy Audit

No external packages are installed or recommended by this phase (stdlib plus in-repo modules plus the OS `strace` binary, which is present). Packages removed due to [SLOP] verdict: none. Packages flagged [SUS]: none. Package legitimacy check not run: nothing to check.

## Architecture Patterns

### System Architecture Diagram

```
query: kme_pillars {d..i|all} / kme_replay rank  --plan auto  --denominator KME-L  [--project-filter F]
   |
   v
[KS-4 switch: --plan champion|scoped|challenger|auto, default unchanged until certified]
   |
   +-- champion  -> existing full scan (unchanged)            -----------------------+
   +-- scoped    -> existing scan restricted by --project-filter (unchanged)  --------+--> measurement file(s)
   +-- challenger/auto:                                                               |
         G0 index certified? usage_index.population(select=kme, until, filter, expect=frozen) == EXACT
            no (DRIFTED / UNMEASURED / no DB / schema < 5) -> DEOPT(reason from index) -> scoped raw
         G1 watermark: stat of in-scope files == index size/mtime_ns; no new file in scoped store dirs
            no -> DEOPT("watermark: <file>") -> scoped raw (or refresh-then-retry, planner choice)
         G2 versions: pattern_set == live; attr_version == ATTR_VERSION; parser digest; metric digest
            no -> invalidate the closure -> recompute those entries
         G3 scope: query names a cross-project question? only then global raw is allowed
         |
         v
   tier A  facts hit (per file x pillar, key = content_id + parser + metric): merge facts, open 0 raw files
   tier B  facts miss: open ONLY the files of index-selected sessions (364 files / 54.0 % bytes), run observers,
           (optionally) write facts for next time
   tier C  scoped raw (project dirs) = deopt target;  global raw only on explicit cross-project question
         |
         v
   population / corpus block taken from the index (sessions_scanned = index sessions + skipped-shape census)
   path log (JSONL): plan requested, plan taken, each guard + verdict, deopt reason, files opened, bytes
         |
         v
   measurement files (same renderer, same redaction) -> normalised byte compare with committed champion files
```

### Recommended Project Structure
```
wiki/tools/kme_pillars.py        # + --plan, guard chain, path log, challenger tiers (extension, not a new engine)
wiki/tools/kme_replay.py         # + same --plan flag, reuses kme_pillars ctx
tools/strace_io_sum.py           # new, tracked: open-set / raw / unique / cross-project / index bytes, with positive control
tools/test_kme_challenger.py     # new gate file (V-KMEC-*), hermetic + real-corpus gates, --drill
vault/programs/incremental-cognition/gen2/evidence/P-*.md   # table, equivalence, stale-cache, exposure evidence
```
(Where to put the facts sidecar code is the planner's call; keeping it inside `kme_pillars.py` keeps "extension of the owner".)

### Pattern 1: guard chain with typed deopt
**What:** each guard returns `(ok, reason)`; the first failure logs `{"guard": name, "reason": reason}` and the run continues on the next tier. An index `UNMEASURED` always deopts with the index's own `reasons` strings (CONTEXT decision); never print a partial number.
**When to use:** every `--plan auto|challenger` run.
**Example:**
```python
# Source: shape of tools/usage_index.py population() verdicts [VERIFIED: usage_index.py:1687-1691]
POP_EXIT = {"MEASURED": 0, "EXACT": 0, "DRIFTED": 1, "UNMEASURED": 3}
res = usage_index.population(con, until=until, project_filter=pf, select="kme", host=host, expected=frozen_fields)
if res["verdict"] != "EXACT":
    log_deopt(guard="index_certified", reason=res["verdict"] + ": " + "; ".join(res["reasons"]) )
    return run_scoped_raw(...)
```

### Pattern 2: forced path (KS-4)
`--plan champion` (full scan, ignores the filter only if the caller gave none, exactly today), `--plan scoped` (today's `--project-filter` path), `--plan challenger` (fail rather than deopt silently: a deopt is an error exit with the reason), `--plan auto` (challenger with deopt). Unknown values fail closed (exit 2). Prove it with a gate that forces each plan and reads the path log.

### Anti-Patterns to Avoid
- **Claiming zero raw bytes while reading the whole index file:** the population query reads 899,150,356 bytes of SQLite. Report index bytes in their own column.
- **Locator scans on a drifted population:** unscoped `--until auto` produced 10 scans (Run 5). If the index says DRIFTED at the freeze instant, deopt with the index's deltas; do not bisect on raw.
- **A second selector or a copied threshold:** selection is `usage_index._kme_selector` (champion classifier loaded by path). No threshold may be re-typed.
- **Editing committed measurement files or the gen1 ledger:** write candidates to `--out-dir` in scratch (`write_measurement` creates exclusively; `_prepare` refuses an out-dir inside a scanned root, `kme_pillars.py:~1965`).
- **Reading "KME-only" from the filter regex:** exposure is the opened set (CONTEXT).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| KME session selection | a new classifier or share threshold | `usage_index._kme_selector` / `population(select="kme")` | already EXACT against the frozen denominator; a copy drifts |
| Population EXACT/DRIFTED verdict | a new comparator | `usage_index.population(expected=...)` + `kme_pillars.compare_population` | typed UNMEASURED reasons already exist |
| Content identity | mtime/size comparison alone | `files.content_id` (end + head/tail sha) | Phase 1 chose it to survive junction aliases and copies |
| Per-pillar observers | rewrites of D..I, L | the existing observer classes fed from the selected files | the files must reproduce byte for byte |
| Redaction of written files | custom scrubber | `modules.secret_firewall.redact` via `_load_redact()` | `main()` refuses to write when it is unavailable |
| File-open accounting | an in-process monkeypatch as the only proof | strace (OS layer) plus a `builtins.open` spy for hermetic gates | a Python spy cannot see an `sqlite3` or subprocess read |

**Key insight:** the cheapest honest gain is selecting files with the certified index; the expensive part (observer facts) should be built only if repeated-query measurements justify it.

## Runtime State Inventory

Not a rename/refactor phase: omitted. State this phase will create or touch: (a) a facts sidecar DB if built (scratch, outside the repo, never committed; may contain text-derived tokens for G), (b) path log files, (c) scratch measurement output dirs. The index `/home/kobii/ao-scratch/p1/cold.sqlite` and the corpus are read-only inputs.

## Common Pitfalls

### Pitfall 1: `sessions_scanned` and `project_dirs` in every file's `corpus` block
**What goes wrong:** byte diff on all seven files. **Why:** the champion counts 568 pseudo-sessions (552 + 16 skipped shapes) in the scoped dirs; an index answer or a selected-files-only scan sees fewer. **How to avoid:** derive both fields from the index (session count + skipped-shape census for the scoped stores) and gate them. **Warning sign:** only the `corpus` block differs in the diff.

### Pitfall 2: Volatile fields make a naive hash compare red forever
**What goes wrong:** `measured_at`, `command`, H's `commit` differ on every run. **How to avoid:** the normalised comparator of section 1, with a perturbed-file control proving it still detects a real difference. H also depends on git HEAD (`ce_owner_verdicts`), a non-corpus input: a HEAD where the CE ledger terminals for P and G changed would legitimately change H.

### Pitfall 3: Unscoped population is DRIFTED, so "global raw" can never certify
**What goes wrong:** a challenger that falls through to global raw spends 10 scans. **How to avoid:** global raw only on an explicit cross-project question; for KME-L the scope filter is part of the denominator's definition (the frozen file records no dir list, so the filter `KobiiCraft-Core-Files|kme-wt-arena2` is the convention to carry, from Run 6).

### Pitfall 4: The index is not free and contains every project
**What goes wrong:** "0 raw bytes" with 899 MB of index reads, and CostaLuz rows inside the DB. **How to avoid:** the extra index-bytes column; decide on a KME-scope DB (open question 2).

### Pitfall 5: `--until` semantics differ between champion and index
**What goes wrong:** champion `make_keep` drops lines by effective timestamp (own, else last seen in the file); the index uses `coalesce(own ts, files.first_ts)` per row, and a session with no `first_ts` vanishes under `--until` with no reason (review IN-04, 5 in-scope files, 0 calls). Parity is EXACT today, but any new facts keyed on `ts` must reuse the champion's inherit rule. Fold IN-04 into the challenger's guard (report such sessions as a reason or a count).

### Pitfall 6: G stores text, and its tie-break depends on scan order
**What goes wrong:** G's records and candidates hold assistant-text words (`content=frozenset(cw)`, `subject_raw`), and the match key is `(timestamp, self._seq)` where `_seq` is the global scan order (`kme_pillars.py:1038-1135`). A per-file cache keeps text-derived tokens (HR-SECRET-002 surface; the measurement file passes through `redact` only at write time, so redacting inside the cache could change a token and break equality) and a merged scan order differs from `os.walk` order on timestamp ties. **How to avoid:** keep any G cache local scratch, never committed, uncommitted by `.gitignore`/path choice; assign `_seq` by a deterministic order; or give G a deopt-only treatment (G always reads its selected files raw) and narrow the claim explicitly.

### Pitfall 7: Observer state is not resumable
Appending to a transcript forces a whole-file recompute of its facts (E last-hash maps, D/E residency need the final `len(order)`). Cost scales with the changed file, not the delta. Measure it; the 5-file / 709,630-byte delta in `O-cost-gex44.md` is the right fixture shape.

### Pitfall 8: Scope of "no unrelated-project raw reads" must include the watermark guard
A no-op `refresh` and a directory walk touch CostaLuz directory entries (no bytes). A guard that opens or hashes a file outside scope breaks the criterion; stat in-scope files only and list only in-scope store dirs.

### Pitfall 9: Guards that cannot fail
Every guard needs a mutant in the drill (a guard that always admits, a watermark check that always passes) and a paired control where the same guard admits. See `~/.claude/rules` guard-event-reachability and instrument-before-claim doctrine (load those skills when writing the gates).

## Code Examples

### Normalised equivalence compare (sketch, values from section 1)
```python
# volatile fields confirmed by diff of committed vs re-run files (this session)
VOLATILE = (r'^(measured_at: ).*$', r'^(command: ).*$', r'^( *"measured_at": ).*$', r'^( *"command": ).*$',
            r'"commit": "[0-9a-f]{40}"')
def normalised_sha(text): ...   # re.sub each pattern with a fixed token, then sha256 of the result
# control: flip one digit of a copy -> normalised_sha differs (must be asserted in the same gate)
```

### Open-set summary shape (tools/strace_io_sum.py contract)
```text
input : strace -f -y -e trace=openat,read,pread64 log, --corpus-root, --scope-regex, --forbid-regex '(?i)costaluz'
output: {"raw_bytes": n, "raw_files_opened": n, "unique_bytes": n, "cross_project_bytes": n,
         "forbidden_bytes": n, "index_bytes": n, "by_project": {...}}
control: a synthetic log containing a forbidden-path read must give forbidden_bytes > 0
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Unscoped population, 10 locator scans (Run 5) | project-scoped raw (Run 6) | Run 6, 2026-10-05 | 869 s to 24 s, 101.53 GB to 2.83 GB (36.2x, 35.9x) |
| Raw rescan per query | certified index for population/selection/scope (Phase 1) | Phase 1, dd1c910a | population EXACT in 0.98 s with 0 corpus opens |
| (this phase) | index-selected raw, optional facts sidecar | Phase 2 | selected files only: 54.0 % of scoped bytes before any cache |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | A sidecar facts DB (ATTACH to the index) is preferable to new tables inside `usage_index.py` | Standard Stack, Architecture | If Owner prefers in-index tables, a schema bump and drill re-run are required; Phase 1 certification must be re-earned |
| A2 | Per-file facts are small enough that a warm query beats the scoped path on wall and raw bytes | Summary, Section 4 | Unmeasured. If false the right outcome is the allowed loss (`FALSIFIED_OR_REJECTED_BY_EVIDENCE`) or a narrowed claim |
| A3 | strace overhead inflates wall 2-6x, so wall must come from untraced runs | Section 3 | Seen once (3.741 s vs 0.577 s on a no-op); if bytes also drift under strace the table needs a second instrument |
| A4 | `usage_index._result_text` length equals `kme_token_audit.text_of` length for every tool_result shape | Section 2 (F, H, L) | If not equal, index `result_chars` cannot feed F/H/L byte-identically |
| A5 | The frozen KME-L scope is the filter `KobiiCraft-Core-Files|kme-wt-arena2` (convention from Run 6; the frozen JSON has no dir list) | Pitfall 3 | If another dir ever holds KME-L sessions the scoped path under-counts; the index `per_project` view is the discovery check |
| A6 | Selected-session file share (54.0 %) holds when re-measured at plan time | Section 2 | Corpus copy and index are fixed inputs, so low risk; re-measure in the plan's first task |

## Open Questions

1. **Facts sidecar: build it in this phase or stop at index-selected raw?**
   - Known: index-selected raw is certain (364 files, 1.648 GB, no new store) and ships through the existing observers; the sidecar adds invalidation machinery and a text-bearing cache for G.
   - Unclear: whether warm repeated queries need the sidecar to beat the scoped path (they do not need it to beat on raw bytes, they probably need it to beat on wall: observers are CPU-bound, 24-31 s per scan at roughly 3 GB, so reading 54 % may give about 16 s).
   - Recommendation: plan two increments: (1) tiers A/B-selected, guards, path log, KS-4, table; measure; (2) sidecar only if (1) does not beat the scoped path on the pre-agreed wall + raw-bytes comparison; otherwise record the narrowed result. Safest default under an unattended run: ship (1), record (2) as a decision.
2. **Whole-corpus index versus a KME-scope index.**
   - Known: the Phase 1 DB holds all projects; a population query reads 899 MB of it. `refresh` has no store filter, so a scoped DB cannot be built without a small `usage_index` extension.
   - Recommendation: keep the cross-project metric to transcript bytes, state it in the table caption, and propose the store filter as a follow-up; do not touch `usage_index.py` in Phase 2 unless the planner wants to re-run the full 71/71 + drill.
3. **Comparing against which scoped baseline?** `all` + `rank` (about 57 s, 2 scans) versus the seven separate runs (177 s, 19.47 GB). Recommendation: report both rows; judge criterion 5 against the cheaper (`all` + `rank`) so the challenger cannot win on a handicapped baseline.
4. **What counts as "repeated queries"?** Recommendation: N = 5 identical queries, median wall and raw bytes, cold and warm cache, plus a post-delta query (5 appended files).
5. **H depends on git HEAD.** Recommendation: the comparator masks `commit`; the gate also asserts the masked `pillars` verdict map equals the committed one.
6. **IN-04 fold-in.** Recommendation: fold in, it is a guard reason the challenger needs on any `--until` query.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| python3 | everything | yes | 3.12.3 | none needed |
| strace | open-set measurement | yes | 6.8 (`/usr/bin/strace`) | `/proc/<pid>/io` rchar for totals only (cannot name files; the CostaLuz check would be void) |
| git | H's CE-ledger read | yes | 2.43.0 (spec preflight) | H returns UNMEASURABLE per `ce_owner_verdicts` |
| Corpus `/home/kobii/kme-corpus/projects` | measurements | yes | 344 top-level dirs | none; read-only |
| Phase 1 index `/home/kobii/ao-scratch/p1/cold.sqlite` | guards, selection | yes | schema 5, 489,816,064 B | rebuild: `usage_index.py refresh --all` (128 s, 9.9 GB cold; outside this research's budget) |
| `/home/kobii/ao-scratch/p1/{evict.py,manifest.py,strace_sum.py}` | cold cache, read-only proof | yes (scratch, not in repo) | n/a | re-create inside the repo's tools |

No blocking dependency is missing.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | repo-native gate scripts (no pytest): `V-<DOMAIN>-<NAME>` gates, `--drill` mutation drill, summary line `*_PASS=n/m threshold=m/m` |
| Config file | none |
| Quick run command | `python3 -I tools/test_kme_pillars.py` (89/89 in 13.3 s now) and the new `python3 -I tools/test_kme_challenger.py` |
| Full suite command | the two above with `--drill`, plus `python3 -I tools/test_usage_index_v5.py` and `--drill` if `usage_index.py` changed, plus `python3 tools/test_incremental_cognition_program.py --generation 2 --final` for the ledger wiring |

### Phase Requirements -> Test Map
| Criterion / Req | Behavior | Test type | Automated command (proposed names) | Negative control |
|---|---|---|---|---|
| 1 / AO-07 access plan | tier order A -> B -> C; global raw only on explicit cross-project flag | hermetic unit | `V-KMEC-PLAN-ORDER` | a query with the cross-project flag unset must never open an out-of-scope fixture file (spy) |
| 1 / AO-07 deopt | guard failure falls back and logs the reason | hermetic unit | `V-KMEC-DEOPT-LOGGED` | each guard (index missing, schema < 5, DRIFTED, UNMEASURED, watermark, pattern drift) driven red once, with the reason string asserted; control: all green takes tier A/B |
| 1 / KS-4 | forced `--plan champion|scoped` is honoured; unknown plan exits 2 | hermetic unit | `V-KMEC-KS4-FORCED` | forced champion on a fixture must open the out-of-scope file; forced challenger with a failing guard exits non-zero |
| 1 invalidation keys | the four keys are recorded and each change is detected | hermetic unit | `V-KMEC-KEYS-FOUR` | one mutant per key (watermark ignored, parser digest constant, attribution version ignored, metric digest constant) |
| 2 / AO-09 equivalence | D, E, F, G, H, I, L reproduce the committed files after normalising `measured_at`, `command`, H `commit` | real-corpus | `V-KMEC-EQUIV-REAL-{D,E,F,G,H,I,L}`: run the challenger with `--out-dir` in scratch, compare with `vault/programs/incremental-cognition/measurements/*-KME-L-2026-10-05.md` | perturb one digit in a copy of each: comparator must say DIFFERENT (`V-KMEC-EQUIV-PERTURB`); also assert `corpus.sessions_scanned == 568` |
| 3 table | wall, raw bytes, unique bytes, files opened, cross-project bytes (+ index bytes) for champion (cited Run 5), scoped (Run 6 cited + re-measured), challenger cold / warm / post-delta | real-corpus | `python3 tools/strace_io_sum.py` over `strace -f -y -e trace=openat,read,pread64` logs; evidence file `gen2/evidence/P-table-gex44.md` | synthetic log with a known byte count must be summed exactly (`V-KMEC-SUM-EXACT`) |
| 3 / 4 KME-only opens zero CostaLuz | `forbidden_bytes == 0` for the challenger run | real-corpus | `V-KMEC-COSTALUZ-ZERO-REAL` | control: same query with `|CostaLuz` added to the filter must report > 0 (about 99.7 MB over 44 files); a synthetic log fixture also pins the detector in the hermetic suite |
| 4 stale cache | change one source file -> exactly that closure invalidated, others hit; parser version change -> all; metric change -> only that pillar | hermetic (scratch copy of a fixture tree, never the corpus) | `V-KMEC-STALE-SOURCE`, `V-KMEC-STALE-PARSER`, `V-KMEC-STALE-METRIC` | paired controls: unchanged tree -> all hits; mutant that invalidates everything or nothing must be killed |
| 5 allowed loss | challenger vs scoped on N=5 repeats; narrow or reject with a falsification artifact naming [P] (IC-gen2) | measurement + ledger | judged by `tools/ic_gen2.py` rows for P (`P-falsified-without-artifact`, allowed loss `FALSIFIED_OR_REJECTED_BY_EVIDENCE`, `ic_gen2.py:52,153,872-882`) | the artifact is required to carry the table; a P close without an artifact naming [P] is rejected by the existing gate |
| Read-only | corpus manifest sha and index DB sha unchanged | real-corpus | `python3 -I /home/kobii/ao-scratch/p1/manifest.py` before/after (port it into tools if gated) | a deliberate touch of a scratch copy must change the manifest |

### Sampling Rate
- **Per task commit:** `python3 -I tools/test_kme_pillars.py` and the new gate file (hermetic part, seconds).
- **Per wave merge:** both with `--drill`, then the real-corpus equivalence gates (each scoped run is about 25-31 s).
- **Phase gate:** full list above green, the table committed, the negative controls shown red once, before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `tools/test_kme_challenger.py` - covers criteria 1, 2, 4 and the hermetic part of 3 (does not exist yet).
- [ ] `tools/strace_io_sum.py` - tracked replacement for the scratch `strace_sum.py`, with per-project, distinct-open, unique-byte and forbidden-regex columns.
- [ ] A fixture transcript tree builder reusing `test_kme_pillars.py` helpers (`scratch()`, synthetic transcripts) with an out-of-scope "CostaLuz-like" project dir.
- [ ] Decide the comparator's normalisation list in code and pin it with the perturb control.
- [ ] Framework install: none.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | no remote interface |
| V3 Session Management | no | n/a |
| V4 Access Control | yes (data scope) | the scope filter and open-set measurement; CostaLuz transcripts are client-confidential data the KME query must never open |
| V5 Input Validation | yes | `--project-filter` is compiled with `re.compile` and a failure exits 2 (`_prepare`); `--plan` unknown value fails closed; `--until` parsed by `parse_instant` |
| V6 Cryptography | partial | sha256 identity only (`hashlib`); no custom crypto; redaction through `modules.secret_firewall.redact` |
| V8 Data protection | yes | HR-SECRET-002: nothing written to a committed file carries raw text; a facts cache for G holds text-derived tokens, keep it out of the repo |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Challenger writes into a scanned corpus | Tampering | existing `_prepare` refusal of `--out-dir` inside `--root`; manifest before/after |
| Cross-project data exposure through the index or a watermark walk | Information disclosure | open-set measurement with a forbidden regex; stat/list in-scope dirs only; state that the index file holds all projects (open question 2) |
| Secret in a derived cache or measurement file | Information disclosure | `redact()` before any committed write; cache stays in scratch; HR-SECRET-002/006 |
| Stale cache served as fresh | Spoofing/Repudiation | four-key invalidation, typed deopt, path log |
| Regex denial of service from a user filter | Denial of service | low risk (local CLI); optional timeout on the run (`timeout 170` convention) |

## Sources

### Primary (HIGH confidence): files read this session
- `.planning/workstreams/autonomous-optimization/phases/02-kme-l-challenger/02-CONTEXT.md`, `REQUIREMENTS.md`, `STATE.md`, `ROADMAP.md` (criteria lines 146-149)
- `vault/specs/autonomous-optimization.md` (lines 55-70, 95-105, 155-189) and `vault/plans/autonomous-optimization-2026-10-05.md` (lines 22-30, 46-58)
- `wiki/tools/kme_pillars.py` (observers, `scan`, `population`, `_prepare`, `_measure`, `_resolve`, `_result`, `main`, `ce_owner_verdicts`), `wiki/tools/kme_token_audit.py` (whole), `wiki/tools/kme_replay.py` (header and class list), `wiki/tools/kme_report.py` (`is_kme`)
- `tools/usage_index.py` (SCHEMA, `_v5_line`, patterns, attribution, `population`, `main`), `tools/test_kme_pillars.py` and `tools/test_usage_index_v5.py` (conventions), `tools/ic_gen2.py` (pillar P judge)
- `vault/programs/incremental-cognition/gen2/ledger.json` (frozen rule P and state.O), `.../gen2/evidence/O-cost-gex44.md`, `.../champion/*`, `.../measurements/*-KME-L-2026-10-05.md`, `.../denominators/kme_audit_2026-10-03.json`
- Commands run: `usage_index population` (scoped EXACT and unscoped DRIFTED, with strace), `kme_pillars all` scoped into `/tmp/p2r-champ` and diff vs committed, `test_kme_pillars.py` (89/89), read-only SQL on `cold.sqlite`, `find -ipath '*costaluz*'`

### Secondary (MEDIUM)
- `/home/kobii/ao-scratch/p1/strace_sum.py` and the Phase 1 strace outputs (host-local scratch)
- `vault/plans/zero-rescan-reality-scan-2026-10-05.md` (junction counts, Run 5 diagnosis)

### Tertiary (LOW)
- none; unmeasured predictions are tagged in the Assumptions Log

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, stdlib and in-repo owners only.
- Architecture: MEDIUM, the three-tier plan is derived from measured costs (54.0 % selected bytes, 0.98 s index answer, 899 MB index reads) but no challenger has been built or timed.
- Pitfalls: HIGH for 1-5, 8 (observed or read in code); MEDIUM for 6, 7, 9 (read in code, behaviour under the sidecar unmeasured).

**Research date:** 2026-10-06
**Valid until:** the corpus copy, the Phase 1 index and the 7 committed files are fixed inputs; re-check if any of `wiki/tools/kme_*.py` or `tools/usage_index.py` changes (their digests are the parser version).

## RESEARCH COMPLETE
