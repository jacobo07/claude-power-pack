---
pillar: O
plane: gex44
denominator: KME-L
head: 77e911796da94d2c90a6469a6df3acb8be196082
measured_at: 2026-10-06T21:35:00Z
---

# [O] Refresh cost on the GEX44 corpus copy: cold, warm cold, no-op, delta

Pillar O clause 5 (governing spec `vault/specs/autonomous-optimization.md`). `plane: gex44`, host `kobiicraft-gex44`,
Linux 6.8, python3.12. `denominator: KME-L` names the scope reference: the 6-dir scope is the directory set of the Run 6
filter `KobiiCraft-Core-Files|kme-wt-arena2` (the KME-L directories). Corpus root (read-only):
`/home/kobii/kme-corpus/projects`; whole-corpus builds read it in place, the 6-dir and delta runs use a real copy
(`cp -a`, inode checked: copy 31486968 vs source 30972926 for `C--Users-User-Apps-kme-wt-arena2/1f0ab85f-...jsonl`) under
`/home/kobii/ao-scratch/p1/delta-root/`. All DBs and logs are under `/home/kobii/ao-scratch/p1/`.
Counters are the CLI's own JSON (`files_read`, `bytes_read`, `bytes_ingested`, `wall_s`, `proc.rchar_delta`,
`proc.maxrss_kb`); `rchar_delta` is `/proc/self/io` rchar of the whole process (every `read`/`pread` byte, corpus AND
the SQLite file), so it is not the corpus byte count; the attribution is measured separately below.

## Summary table

| run | scope | files_read | bytes_read | bytes_ingested | wall_s | rchar_delta | maxrss_kb | DB bytes | cache |
|---|---|---|---|---|---|---|---|---|---|
| v4 baseline (RESEARCH, cited, not re-run) | 6 dirs | 979 | 3,053,908,888 | n/a | 15.7 | n/a | 76 MB | 34.7 MB | unknown |
| v5 cold, whole corpus | 4,015 jsonl in 10,577 files (3,965 ingested) | 3,965 | 9,932,073,959 | 9,932,073,959 | 128.069 | 158,621,987,249 | 89,760 | 489,816,064 | evicted best-effort via posix_fadvise DONTNEED, residency not measured |
| v5 warm cold, whole corpus | same | 3,965 | 9,932,073,959 | 9,932,073,959 | 118.661 | 158,621,987,249 | 89,672 | 489,816,064 | warm: immediately after the cold build (second fresh DB) |
| v5 no-op | same, existing `cold.sqlite` | 0 | 0 | 0 | 0.577 | 958,972,508 | 33,352 | 489,816,064 | warm |
| v5 cold, 6-dir copy | 979 files | 979 | 3,053,908,888 | 3,053,908,888 | 25.182 | 18,456,362,331 | 86,608 | 143,429,632 | warm (just copied) |
| v5 delta, 6-dir copy | 5 appended files | 5 | 709,630 | 709,630 | 0.07 | 136,372,842 | 30,560 | 143,486,976 | warm |

## v4 baseline

source: `01-RESEARCH.md` "v4 cost baseline" (KME scope of 6 dirs): 979 files, 3,053,908,888 B, 15.7 s, RSS 76 MB,
DB 34.7 MB, cache state unknown; no-op 0.104 s. Taken from RESEARCH, not re-measured here (v4 code is not run in this plan).

## v5 cold, whole corpus (cache evicted best-effort)

command: `python3 tools/usage_index.py refresh --all --db /home/kobii/ao-scratch/p1/cold.sqlite --proj /home/kobii/kme-corpus/projects --deadline 540` (preceded by `python3 /home/kobii/ao-scratch/p1/evict.py /home/kobii/kme-corpus/projects` -> `evicted_files=4015 failed=0`)

```json
{"status": "OK", "files_read": 3965, "calls_upserted": 269224, "pending": 0, "backfill_pending": 0, "error": "", "files_opened": 3965, "bytes_read": 9932073959, "bytes_ingested": 9932073959, "files_seen": 3965, "wall_s": 128.069, "skipped_shapes": {"count": 50, "bytes": 2897590, "by_shape": {"_preserved": 14, "_empty_shells": 36, "other": 0}, "samples": ["/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/0a2b14ee-87e9-4886-848d-2027da82494d.jsonl", "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/198b9c4d-3feb-4828-8f4e-1cfb8bfdcec4.jsonl", "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/56c745d6-1cc9-4ab4-b0f1-875ada2495d7.jsonl", "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/7b7cd78e-8573-4b27-8504-2d079dac59f3.jsonl", "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/87a4a691-1166-4b00-9bbd-d3846616d836.jsonl"], "walk_errors": 0}, "parse_errors": 0, "files_with_errors": 0, "skipped_concurrent": 0, "pattern_error": null, "proc": {"rchar_delta": 158621987249, "maxrss_kb": 89760}}
```

## v5 warm cold, whole corpus

command: `python3 tools/usage_index.py refresh --all --db /home/kobii/ao-scratch/p1/cold2.sqlite --proj /home/kobii/kme-corpus/projects --deadline 540`

```json
{"status": "OK", "files_read": 3965, "calls_upserted": 269224, "pending": 0, "backfill_pending": 0, "error": "", "files_opened": 3965, "bytes_read": 9932073959, "bytes_ingested": 9932073959, "files_seen": 3965, "wall_s": 118.661, "skipped_shapes": {"count": 50, "bytes": 2897590, "by_shape": {"_preserved": 14, "_empty_shells": 36, "other": 0}, "samples": ["/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/0a2b14ee-87e9-4886-848d-2027da82494d.jsonl", "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/198b9c4d-3feb-4828-8f4e-1cfb8bfdcec4.jsonl", "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/56c745d6-1cc9-4ab4-b0f1-875ada2495d7.jsonl", "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/7b7cd78e-8573-4b27-8504-2d079dac59f3.jsonl", "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/87a4a691-1166-4b00-9bbd-d3846616d836.jsonl"], "walk_errors": 0}, "parse_errors": 0, "files_with_errors": 0, "skipped_concurrent": 0, "pattern_error": null, "proc": {"rchar_delta": 158621987249, "maxrss_kb": 89672}}
```

## v5 no-op

command: `python3 tools/usage_index.py refresh --all --db /home/kobii/ao-scratch/p1/cold.sqlite --proj /home/kobii/kme-corpus/projects --deadline 540`

```json
{"status": "OK", "files_read": 0, "calls_upserted": 0, "pending": 0, "backfill_pending": 0, "error": "", "files_opened": 0, "bytes_read": 0, "bytes_ingested": 0, "files_seen": 3965, "wall_s": 0.577, "skipped_shapes": {"count": 50, "bytes": 2897590, "by_shape": {"_preserved": 14, "_empty_shells": 36, "other": 0}, "samples": ["/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/0a2b14ee-87e9-4886-848d-2027da82494d.jsonl", "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/198b9c4d-3feb-4828-8f4e-1cfb8bfdcec4.jsonl", "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/56c745d6-1cc9-4ab4-b0f1-875ada2495d7.jsonl", "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/7b7cd78e-8573-4b27-8504-2d079dac59f3.jsonl", "/home/kobii/kme-corpus/projects/C--Users-User--claude-skills-claude-power-pack/_empty_shells/87a4a691-1166-4b00-9bbd-d3846616d836.jsonl"], "walk_errors": 0}, "parse_errors": 0, "files_with_errors": 0, "skipped_concurrent": 0, "pattern_error": null, "proc": {"rchar_delta": 958972508, "maxrss_kb": 33352}}
```

files_read 0, files_opened 0, bytes_read 0 (wall_s 0.577 includes the walk of 10,577 files and the skipped-shape census).
A traced repeat on `cold2.sqlite` (`strace -f -y -e trace=pread64,read -o noop.strace python3 tools/usage_index.py refresh --all ...`,
wall_s 3.741 under tracing, files_opened 0) attributes the 958,972,508 rchar bytes as 958,965,604 bytes from the SQLite
file (234,235 reads) and 0 bytes from the corpus:

```
     958965604 bytes    234235 calls  /home/kobii/ao-scratch/p1/cold2.sqlite
        180358 bytes        33 calls  /home/kobii/missions/autonomous-optimization/.claude/worktrees/ao-gen2/tools/usage_index.py
        141860 bytes         2 calls  /usr/lib/python3.12/__pycache__/typing.cpython-312.pyc
        133446 bytes         2 calls  /usr/lib/python3.12/__pycache__/inspect.cpython-312.pyc
        101682 bytes         2 calls  /usr/lib/python3.12/__pycache__/argparse.cpython-312.pyc
        100279 bytes         2 calls  /usr/lib/python3.12/__pycache__/ast.cpython-312.pyc
         90762 bytes         2 calls  /usr/lib/python3.12/__pycache__/ipaddress.cpython-312.pyc
         80708 bytes         2 calls  /usr/lib/python3.12/__pycache__/enum.cpython-312.pyc
total 960999761
```

## v5 cold, 6-dir copy (same scope as the v4 baseline)

command: `python3 tools/usage_index.py refresh --all --db /home/kobii/ao-scratch/p1/delta.sqlite --proj /home/kobii/ao-scratch/p1/delta-root --deadline 540`

```json
{"status": "OK", "files_read": 979, "calls_upserted": 67206, "pending": 0, "backfill_pending": 0, "error": "", "files_opened": 979, "bytes_read": 3053908888, "bytes_ingested": 3053908888, "files_seen": 979, "wall_s": 25.182, "skipped_shapes": {"count": 16, "bytes": 2067258, "by_shape": {"_preserved": 12, "_empty_shells": 4, "other": 0}, "samples": ["/home/kobii/ao-scratch/p1/delta-root/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/_empty_shells/1290765e-f04a-494f-8d81-9c37985cda5a.jsonl", "/home/kobii/ao-scratch/p1/delta-root/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/_empty_shells/6ce862a6-aff6-44a1-9dd2-f0a36c949ce7.jsonl", "/home/kobii/ao-scratch/p1/delta-root/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/_empty_shells/944a88b8-0073-487b-9b5e-60bdfdd812a0.jsonl", "/home/kobii/ao-scratch/p1/delta-root/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/_empty_shells/c9f6f49e-1a0c-43fa-a9f1-9518a126b87b.jsonl", "/home/kobii/ao-scratch/p1/delta-root/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/_preserved/43532dab-f714-4e7e-ad98-c5e0602765c8.preserved-20260521.jsonl"], "walk_errors": 0}, "parse_errors": 0, "files_with_errors": 0, "skipped_concurrent": 0, "pattern_error": null, "proc": {"rchar_delta": 18456362331, "maxrss_kb": 86608}}
```

Same 979 files and 3,053,908,888 bytes as the v4 baseline row. Per-byte comparison on this scope:
v4 15.7 s / 3,053,908,888 B = 5.14 ns/B (RESEARCH, command not re-run); v5 25.182 s / 3,053,908,888 B = 8.25 ns/B
(command above): v5/v4 = 1.60x slower per byte, RSS 86,608 kB vs 76 MB (1.1x), DB 143,429,632 B vs 34.7 MB (4.1x).
The v5 DB additionally stores per-file `call_files`, `tool_events` and the file-identity columns that v4 lacked.

Attribution of this run's rchar (a second cold build of the same tree into `delta2.sqlite`, traced on the DB paths only:
`strace -f -y -e trace=pread64,read -P .../delta2.sqlite -P .../delta2.sqlite-wal -P .../delta2.sqlite-journal -o delta2.strace python3 tools/usage_index.py refresh --all --db /home/kobii/ao-scratch/p1/delta2.sqlite --proj /home/kobii/ao-scratch/p1/delta-root --deadline 540`;
that run's JSON: bytes_read 3,054,618,518 because the five appended files are now in the tree, rchar_delta 18,457,252,185, wall 80.89 s under tracing):

```
   15402524720 bytes   3761407 calls  /home/kobii/ao-scratch/p1/delta2.sqlite
             0 bytes      1031 calls  /home/kobii/ao-scratch/p1/delta2.sqlite-journal
total 15402524720
```

15,402,524,720 of 18,457,252,185 rchar bytes (83 %) are reads of the SQLite file itself (3,761,407 reads, about 4 KB each,
108 times the final DB size), 3,054,618,518 are corpus bytes (the remaining 108,947 bytes are the interpreter and the repo source). The corpus is read once.
The same shape explains the whole-corpus figure: rchar 158,621,987,249 vs 9,932,073,959 corpus bytes (16x), deterministic
across the cold and the warm run (identical to the byte). This is a cost finding recorded for plan 06 / a later tuning
step (page-cache misses of the default SQLite cache on random-key inserts and lookups); it is not a corpus re-read.

## v5 delta on the scratch copy

Appending (`python3 -I /home/kobii/ao-scratch/p1/append_delta.py`, which refuses any path outside
`/home/kobii/ao-scratch/p1/delta-root/`): the last 100 complete lines (141,926 bytes) of
`.../KobiiCraft-Core-Files/837d43a5-e86a-4156-beb3-26e130af7000.jsonl` were appended to five other copied main transcripts
(`00aca75c`, `014f76f5`, `02235a49`, `03b8ab0e`, `03ffe2b1`), each +141,926 bytes, **appended total 709,630 bytes**:

```json
{
 "source": "/home/kobii/ao-scratch/p1/delta-root/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/837d43a5-e86a-4156-beb3-26e130af7000.jsonl",
 "lines": 100,
 "bytes_per_file": 141926,
 "files": [
  {
   "file": "/home/kobii/ao-scratch/p1/delta-root/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/00aca75c-5292-48ff-8a14-21a742c2285a.jsonl",
   "before": 2537515,
   "appended": 141926,
   "after": 2679441
  },
  {
   "file": "/home/kobii/ao-scratch/p1/delta-root/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/014f76f5-e1af-4d31-a8a3-c9fdc1d29dee.jsonl",
   "before": 1211058,
   "appended": 141926,
   "after": 1352984
  },
  {
   "file": "/home/kobii/ao-scratch/p1/delta-root/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/02235a49-b52c-46ef-950a-e0430af9af4c.jsonl",
   "before": 3988451,
   "appended": 141926,
   "after": 4130377
  },
  {
   "file": "/home/kobii/ao-scratch/p1/delta-root/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/03b8ab0e-7920-492d-8115-36e835c31e59.jsonl",
   "before": 1011521,
   "appended": 141926,
   "after": 1153447
  },
  {
   "file": "/home/kobii/ao-scratch/p1/delta-root/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/03ffe2b1-46ce-4d4f-bac6-d6b50dc3f15c.jsonl",
   "before": 4383655,
   "appended": 141926,
   "after": 4525581
  }
 ],
 "appended_total": 709630
}
```

command: `python3 tools/usage_index.py refresh --all --db /home/kobii/ao-scratch/p1/delta.sqlite --proj /home/kobii/ao-scratch/p1/delta-root --deadline 540`

```json
{"status": "OK", "files_read": 5, "calls_upserted": 40, "pending": 0, "backfill_pending": 0, "error": "", "files_opened": 5, "bytes_read": 709630, "bytes_ingested": 709630, "files_seen": 979, "wall_s": 0.07, "skipped_shapes": {"count": 16, "bytes": 2067258, "by_shape": {"_preserved": 12, "_empty_shells": 4, "other": 0}, "samples": ["/home/kobii/ao-scratch/p1/delta-root/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/_empty_shells/1290765e-f04a-494f-8d81-9c37985cda5a.jsonl", "/home/kobii/ao-scratch/p1/delta-root/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/_empty_shells/6ce862a6-aff6-44a1-9dd2-f0a36c949ce7.jsonl", "/home/kobii/ao-scratch/p1/delta-root/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/_empty_shells/944a88b8-0073-487b-9b5e-60bdfdd812a0.jsonl", "/home/kobii/ao-scratch/p1/delta-root/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/_empty_shells/c9f6f49e-1a0c-43fa-a9f1-9518a126b87b.jsonl", "/home/kobii/ao-scratch/p1/delta-root/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/_preserved/43532dab-f714-4e7e-ad98-c5e0602765c8.preserved-20260521.jsonl"], "walk_errors": 0}, "parse_errors": 0, "files_with_errors": 0, "skipped_concurrent": 0, "pattern_error": null, "proc": {"rchar_delta": 136372842, "maxrss_kb": 30560}}
```

Delta equality: **files_opened 5 == 5 appended files; bytes_ingested 709,630 == appended total 709,630; bytes_read 709,630**
(difference 0), 979 files seen, 974 untouched. wall_s 0.07, rchar_delta 136,372,842 (the process also read the existing
143 MB DB once, the same SQLite-page behaviour measured above), maxrss 30,560 kB, DB 143,429,632 -> 143,486,976 bytes.
Of the 100 appended lines 40 were upserted as calls.

## Read-only proof

`manifest-after.txt` equals `manifest-before.txt` (see `## Read-only proof` in `O-parity-gex44.md`): sha256
`6eab1abced4f04cf4b601c22cf3695e7d7ae3fd31898698fdc2b7625fd10e6a9` before and after all steps of this plan.
