---
pillar: O
programme: IC-gen2 autonomous-optimization
plane: gex44
denominator: KME-L
corpus_root: /home/kobii/kme-corpus/projects
db: /home/kobii/ao-scratch/p1/cold.sqlite
head: 15bd2b8086330ff6be08fb2c4e57348b8e9665f4
measured_at: 2026-10-06T21:17:00Z
---

# [O] KME-L population parity on the GEX44 corpus copy

Pillar O clause 4 (governing spec `vault/specs/autonomous-optimization.md`). Everything below was measured on host
`kobiicraft-gex44` (`plane: gex44`) against the Owner-authorized, read-only corpus copy `/home/kobii/kme-corpus/projects`
(10,577 files, 10,205,326,251 bytes by the manifest below). The scratch DB and every log live under
`/home/kobii/ao-scratch/p1/`, outside the repo and outside the corpus. No command used `~/.claude/projects`.
The frozen target is the KME-L record `vault/programs/incremental-cognition/denominators/kme_audit_2026-10-03.json`:
102 sessions / 0 dead / 34,871 calls / cache_read 11,549,646,300 (read by `--expect KME-L`, never typed into a command).

## Cold build

Cache state: **evicted best-effort via posix_fadvise DONTNEED, residency not measured**.
command: `python3 /home/kobii/ao-scratch/p1/evict.py /home/kobii/kme-corpus/projects` -> `evicted_files=4015 failed=0`
(opens each `*.jsonl` read-only and calls `os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)`; no byte read or written).

command: `python3 tools/usage_index.py refresh --all --db /home/kobii/ao-scratch/p1/cold.sqlite --proj /home/kobii/kme-corpus/projects --deadline 540`
-> exit 0, one pass (status OK, no PARTIAL, so no resume pass). Every pass's JSON (`/home/kobii/ao-scratch/p1/cold.log`):

```json
{"status": "OK", "files_read": 3965, "calls_upserted": 269224, "pending": 0, "backfill_pending": 0, "error": "", "files_opened": 3965, "bytes_read": 9932073959, "bytes_ingested": 9932073959, "files_seen": 3965, "wall_s": 128.069, "skipped_shapes": {"count": 50, "bytes": 2897590, "by_shape": {"_preserved": 14, "_empty_shells": 36, "other": 0}, "samples": ["/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/0a2b14ee-87e9-4886-848d-2027da82494d.jsonl", "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/198b9c4d-3feb-4828-8f4e-1cfb8bfdcec4.jsonl", "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/56c745d6-1cc9-4ab4-b0f1-875ada2495d7.jsonl", "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/7b7cd78e-8573-4b27-8504-2d079dac59f3.jsonl", "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/87a4a691-1166-4b00-9bbd-d3846616d836.jsonl"], "walk_errors": 0}, "parse_errors": 0, "files_with_errors": 0, "skipped_concurrent": 0, "pattern_error": null, "proc": {"rchar_delta": 158621987249, "maxrss_kb": 89760}}
```

DB size after the build: `stat -c %s /home/kobii/ao-scratch/p1/cold.sqlite` -> 489,816,064 bytes.
The build ingested 3,965 transcripts (9,932,073,959 bytes, all of it as bytes_ingested) and skipped 50 files by shape
(`_preserved` 14, `_empty_shells` 36, 2,897,590 bytes). 0 parse errors, 0 files with errors, 0 walk errors.

## Parity

command: `python3 tools/usage_index.py population --db /home/kobii/ao-scratch/p1/cold.sqlite --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --until 2026-10-03T16:13:37Z --select kme --host gex44 --expect KME-L --plane gex44`
-> **exit 0, verdict EXACT**, `deltas` empty, `reasons` empty, `parse_errors_tolerated` not needed (0 parse errors in scope).
Full answer (`/home/kobii/ao-scratch/p1/parity.json`):

```json
{
 "verdict": "EXACT",
 "reasons": [],
 "host": "gex44",
 "until": 1791044017.0,
 "select": "kme",
 "population": {
  "sessions_active": 102,
  "sessions_dead": 0,
  "calls": 34871,
  "input": 69846,
  "cache_write": 209909403,
  "cache_read": 11549646300,
  "output": 37878881
 },
 "per_project": [
  {
   "project": "C--Users-User-Apps-kme-wt-arena2",
   "sessions_active": 1,
   "sessions_dead": 0,
   "calls": 1,
   "cache_read": 540
  },
  {
   "project": "C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files",
   "sessions_active": 101,
   "sessions_dead": 0,
   "calls": 34870,
   "cache_read": 11549645760
  }
 ],
 "reconcile": {
  "archived_excluded": {
   "sessions": 1,
   "files": 1,
   "calls": 649,
   "cache_read": 271001260
  },
  "archived_twins": {
   "sessions": 0,
   "files": 0,
   "calls": 0,
   "cache_read": 0
  },
  "dup_files_in_scope": 0,
  "skipped_shapes": {
   "count": 50,
   "bytes": 2897590,
   "by_shape": {
    "_preserved": 14,
    "_empty_shells": 36,
    "other": 0
   },
   "samples": [
    "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/0a2b14ee-87e9-4886-848d-2027da82494d.jsonl",
    "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/198b9c4d-3feb-4828-8f4e-1cfb8bfdcec4.jsonl",
    "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/56c745d6-1cc9-4ab4-b0f1-875ada2495d7.jsonl",
    "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/7b7cd78e-8573-4b27-8504-2d079dac59f3.jsonl",
    "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/87a4a691-1166-4b00-9bbd-d3846616d836.jsonl"
   ],
   "walk_errors": 0
  },
  "unique": {
   "calls": 34853,
   "input": 69810,
   "cache_write": 209540353,
   "cache_read": 11544130372,
   "output": 37858159
  },
  "first_writer": {
   "calls": 34853,
   "cache_read": 11544130372
  },
  "shared_outside": {
   "keys": 0,
   "cache_read": 0,
   "sessions": []
  }
 },
 "secondary": {
  "input": {
   "observed": 69846,
   "expected": 69846,
   "match": true
  },
  "cache_write": {
   "observed": 209909403,
   "expected": 209909403,
   "match": true
  },
  "output": {
   "observed": 37878881,
   "expected": 37878881,
   "match": true
  }
 },
 "deltas": {},
 "plane": "gex44"
}
```

| field | observed (index) | expected (frozen KME-L) | delta |
|---|---|---|---|
| sessions_active | 102 | 102 | 0 |
| sessions_dead | 0 | 0 | 0 |
| calls | 34,871 | 34,871 | 0 |
| cache_read | 11,549,646,300 | 11,549,646,300 | 0 |
| secondary input / cache_write / output | 69,846 / 209,909,403 / 37,878,881 | same | 0 |

Per-session rows: `--detail` run to `/home/kobii/ao-scratch/p1/parity-detail.json`
(command: same as above plus `--detail`, exit 0, verdict EXACT, 552 session rows of which 102 selected).
The two known divergences from 01-04 (a streamed call straddling the freeze instant; a tool_use id repeated inside one
file) did not change any number: the parity is exact on the corpus.

## Reconcile to the unit

Unit: one API request = `msgid|requestId` (the call key). The frozen figure is the **occurrence view**: each selected
session counts every key it contains, so a key present in two selected sessions is counted twice. Every row below is the
`reconcile` block of the parity command above unless a different command is named.

| view | sessions | calls | cache_read | unit / reason |
|---|---|---|---|---|
| occurrence (gated) | 102 | 34,871 | 11,549,646,300 | per (session, key) summed over selected sessions; equals the champion and the frozen record |
| unique | 102 | 34,853 | 11,544,130,372 | distinct keys over the whole selection (`reconcile.unique`) |
| shared between selected sessions (derived: occurrence - unique) | 2 | 18 | 5,515,928 | 18 keys carried by both session 867896c0-a893-49dc-8010-0c731250e5ae (KME_STRONG, 18 calls, 5,515,928) and session 9184ed39-689e-4cc5-a791-421cf27e8dc4 (KME_STRONG, 403 calls, 183,268,169); both selected, both in project KobiiCraft-Core-Files; all 18 of 867896c0's keys are in 9184ed39 |
| shared_outside (selected key also in a non-selected session) | 0 sessions | 0 keys | 0 | `reconcile.shared_outside`; confirmed independently by `/home/kobii/ao-scratch/p1/dupkeys.py` (read-only SQL: the only keys present in more than one file inside the filter scope are the 18 above and 63 keys of non-selected session ad530b2d, 12,638,149 cache_read, which is not in the population) |
| first_writer (v4 `calls` table) | - | 34,853 | 11,544,130,372 | `reconcile.first_writer`: a key is credited to the file that wrote it first. Equals the v4 figure predicted by RESEARCH (34,853 / 11,544,130,372) |
| dup files in scope | - | - | - | `dup_files_in_scope` = 0 |
| archived excluded (this scope) | 1 session / 1 file | 649 | 271,001,260 | `reconcile.archived_excluded`: session 7ae8e754 under `_archived/...KobiiCraft-Core-Files`, excluded by ARCHIVED_RULE; `archived_twins` = 0 |
| skipped shapes | - | - | - | 50 files, 2,897,590 bytes: `_preserved` 14, `_empty_shells` 36, other 0 |

Difference between the occurrence and the v4 first-writer figures: 18 calls and 5,515,928 cache_read, exactly the
shared-between-selected row (34,871 - 34,853 = 18; 11,549,646,300 - 11,544,130,372 = 5,515,928).

Prediction check against RESEARCH (confirmed or refuted, never assumed):

- occurrence view 34,871: **confirmed** (observed 34,871).
- v4 first-writer figure 34,853 / 11,544,130,372: **confirmed** (observed 34,853 / 11,544,130,372).
- "18 keys / 5,515,928 cache_read shared between session 9184ed39 and 867896c0": **confirmed as to keys, count and cache_read;
  refuted as to the role of 867896c0.** RESEARCH called it a non-KME session; the index and the champion classifier select it
  (KME_STRONG), so the 18 keys are shared between two *selected* sessions and `shared_outside` is 0, not 18. That is why the
  occurrence view (the frozen unit) still counts them twice and equals the champion without any dedup adjustment.

## Unfiltered vs champion Run 5

commands (no `--project-filter`, no `--expect`, so the answer is MEASURED, not EXACT; both exit 0):

- default: `python3 tools/usage_index.py population --db /home/kobii/ao-scratch/p1/cold.sqlite --until 2026-10-03T16:13:37Z --select kme --host gex44 --plane gex44` (`/home/kobii/ao-scratch/p1/unfiltered-default.json`)
- include archived: the same plus `--include-archived` (`/home/kobii/ao-scratch/p1/unfiltered-archived.json`)

Run 5 is the champion's unfiltered answer frozen in the gen2 ledger (`frozen.champion.run5`).

| view | sessions | calls | cache_read | source |
|---|---|---|---|---|
| champion Run 5 | 105 | 35,776 | 11,888,777,786 | frozen, not re-run |
| v5 default (observed) | 103 | 34,999 | 11,583,711,413 | unfiltered-default.json |
| v5 default (predicted) | 103 | 34,999 | 11,583,711,413 | RESEARCH; observed = predicted |
| v5 include-archived (observed) | 104 | 35,648 | 11,854,712,673 | unfiltered-archived.json |
| v5 include-archived (predicted) | 104 | 35,648 | 11,854,712,673 | RESEARCH; observed = predicted |
| unit row: `_archived` | 1 | 649 | 271,001,260 | include-archived minus default (session 7ae8e754); equals the champion `_archived` row |
| unit row: PP alias | 1 | 128 | 34,065,113 | session 8ce177ec-01bd-4738-aa5d-15d6e4a9a582 under `C--Users-User--claude-skills-claude-power-pack`: the corpus copy holds `C--Users-User-Apps-mcp-video-analyzer` as a **symlink** to that directory; the index walk does not follow directory symlinks, so the session is counted once, the champion counted it a second time through the alias |

Reconciliation, exact: default 103 + 1 (`_archived`) + 1 (alias) = 105 sessions; 34,999 + 649 + 128 = 35,776 calls;
11,583,711,413 + 271,001,260 + 34,065,113 = 11,888,777,786 cache_read. Run 5 is reproduced to the unit with nothing left over.

Other reconcile facts from the same commands:

- `archived_excluded` in the unfiltered default answer is 155 sessions / 255 files / 7,588 calls / 1,874,478,123 cache_read.
  That row is **class-agnostic** (every archived session in scope, KME or not); only 1 / 649 / 271,001,260 of it is a selected
  KME session. Read it as "archived sessions the rule removed", not "KME archived sessions".
- Under `--include-archived`: `dup_files_in_scope` = 122 (archived `claude-mem-observer-sessions` alias files whose content
  duplicates another archived file), `unique` calls 35,630 vs occurrence 35,648 (the same 18 shared keys), `first_writer`
  stays 34,981 / 11,578,195,485: archived files write `call_files` rows only (the v4 `calls` table never holds them), so
  the v4 first-writer view cannot see the 649 archived calls by construction.
- `shared_outside` is 0 keys in both unfiltered answers.
- Three directory symlinks exist at the corpus root (`C--Users-User-Apps-mcp-video-analyzer`,
  `C--Users-kobig-Desktop-Cursor-Projects-TUA-X-CW-UGC-SYSTEM`, `C--Users-User-Desktop-Cursor-Projects-provisional--recovered-transcripts`);
  the index does not walk them and does not list them in the skipped-shape census (they are not `files`).

## Read-only proof

Manifest: size, mtime in nanoseconds and path of every file, sorted, hashed (`/home/kobii/ao-scratch/p1/manifest.py`,
which refuses to write under the corpus). Symlinks are not followed.

command: `python3 /home/kobii/ao-scratch/p1/manifest.py /home/kobii/kme-corpus/projects /home/kobii/ao-scratch/p1/manifest-before.txt`
-> `files=10577 bytes=10205326251 sha256=6eab1abced4f04cf4b601c22cf3695e7d7ae3fd31898698fdc2b7625fd10e6a9`
(manifest before, taken 2026-10-06 before the cache eviction and the cold build).

After every step of this plan (both whole-corpus cold builds, the no-op, the `cp -a` of the six filter directories, the
traced runs) the same command was run again into `manifest-after.txt`:
command: `python3 /home/kobii/ao-scratch/p1/manifest.py /home/kobii/kme-corpus/projects /home/kobii/ao-scratch/p1/manifest-after.txt`
-> `files=10577 bytes=10205326251 sha256=6eab1abced4f04cf4b601c22cf3695e7d7ae3fd31898698fdc2b7625fd10e6a9`.
command: `cmp /home/kobii/ao-scratch/p1/manifest-before.txt /home/kobii/ao-scratch/p1/manifest-after.txt` -> identical
(equal manifest hash, equal file count and byte count: no file under the corpus was created, removed, resized or
re-timestamped). `git status --porcelain` lists no path under the corpus or the scratch area (both are outside the repo).
