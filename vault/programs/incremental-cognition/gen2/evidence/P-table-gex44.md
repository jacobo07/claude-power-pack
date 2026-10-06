---
pillar: P
programme: IC-gen2 autonomous-optimization
plane: gex44
denominator: KME-L
corpus_root: /home/kobii/kme-corpus/projects
index: /home/kobii/ao-scratch/p1/cold.sqlite
head: b1023f3d7fc115c4f3622f7cce5238873b0b02ff
measured_at: 2026-10-06T23:30:43Z
---

# [P] (IC-gen2) KME-L challenger: champion vs scoped vs challenger table on the GEX44 corpus copy

Phase 2 criterion 3 (table) and the repeated-query inputs of criterion 5 (plan 02-05). Host `kobiicraft-gex44`
(`plane: gex44`). The real corpus `/home/kobii/kme-corpus/projects` and the Phase 1 index
`/home/kobii/ao-scratch/p1/cold.sqlite` are read-only inputs (hashes before and after in `## Read-only proof`); the
post-delta canary runs on a scratch copy of the six scoped directories under `/home/kobii/ao-scratch/p2/delta-root/`.
All scratch output (indexes, certificates, strace logs, bench JSON) lives under `/home/kobii/ao-scratch/p2/`, outside
the repo. This file holds counts, paths, digests and verdicts only, no transcript text (HR-SECRET-002). No command
used `~/.claude/projects`. The judgement against criterion 5 is plan 02-06's, not this file's.

## Post-delta canary (AO-07 canary, criterion 4 on real data)

Hashes recorded before any step of this plan (`/home/kobii/ao-scratch/p2/hash-before-0205.json`): corpus manifest
sha256 `29969e7d6ab1bb271373c5004f34b2390918234e344c09c8994dc986b0a69ce0` (10,577 files, 10,205,326,251 bytes), index sha256
`6ddd159a914d65dd7a786bf4c5366a79730b397e8d0f197259e60aef89a0dd07` (mtime_ns 1791321612414996448, no `-wal` / `-shm` / `-journal`).

### Step 1: fresh copy of the six scoped directories

command: `cd /home/kobii/kme-corpus/projects && for d in $(ls | grep -E 'KobiiCraft-Core-Files|kme-wt-arena2'); do cp -a "$d" /home/kobii/ao-scratch/p2/delta-root/; done`
-> 6 directories, 3,160,520,417 bytes. Inode check, `stat -c '%i %h %n'` on one copied file and its source: copy
inode 22845080 (1 link), source inode 30972926 (1 link); `find delta-root -type l` -> 0 symlinks, `find delta-root
-type f -links +1` -> 0 hard-linked files. The copy holds no CostaLuz directory.

### Step 2: index of the copy, population check, certificate

command: `python3 tools/usage_index.py refresh --all --db /home/kobii/ao-scratch/p2/delta.sqlite --proj /home/kobii/ao-scratch/p2/delta-root --deadline 540`
-> status OK, files_read 979, bytes_read 3,053,908,888, pending 0, wall_s 26.261
(one call, no PARTIAL).

command: `python3 tools/usage_index.py --db /home/kobii/ao-scratch/p2/delta.sqlite --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --until 2026-10-03T16:13:37Z --select kme --host gex44 --expect KME-L --plane gex44 population`
-> verdict `EXACT`, sessions_active 102, plane gex44.

command: `python3 -I wiki/tools/kme_pillars.py certify --denominator KME-L --until auto --expand --root /home/kobii/ao-scratch/p2/delta-root --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --index-db /home/kobii/ao-scratch/p2/delta.sqlite --cert /home/kobii/ao-scratch/p2/delta.cert.json`

```
KMEP-CERT verdict=CERTIFIED selected=102 uncovered=16 cert=/home/kobii/ao-scratch/p2/delta.cert.json
```

### Step 3: the delta (append script)

command: `python3 -I /home/kobii/ao-scratch/p2/append_delta.py`. The script reads the session ids from `population --detail`
on `delta.sqlite` (saved as `delta-population-detail.json`), skips archived sessions and the 5 sessions the index holds
no first timestamp for, takes the three smallest non-selected and the two smallest selected main transcripts whose last
byte is a newline, and appends one line
`{"type": "user", "timestamp": "2026-10-07T00:00:0<i>Z", "message": {"role": "user", "content": "post-freeze delta line <i>"}}`
(after the freeze instant `2026-10-03T16:13:37Z`, so the frozen answer must not move). Every write passes
`guard()`: realpath must be under `/home/kobii/ao-scratch/p2/delta-root/` and not a symlink, else `REFUSED`. Refusal
checked: the real corpus path and `delta-root/../x` both printed `REFUSED: ... is not a regular path under ...`.

| session | selected by the index | bytes before | appended | bytes after |
|---|---|---|---|---|
| bffabe58... (Core-Files) | not selected | 334417 | 122 | 334539 |
| ec14fa70... (Core-Files) | not selected | 632005 | 122 | 632127 |
| 22977936... (Core-Files) | not selected | 688823 | 122 | 688945 |
| 1f0ab85f... (kme-wt-arena2) | selected | 784420 | 122 | 784542 |
| a05c2e9d... (Core-Files) | selected | 1453187 | 122 | 1453309 |

Appended-bytes JSON (verbatim, `/home/kobii/ao-scratch/p2/delta-append.json`): five files, all under `/home/kobii/ao-scratch/p2/delta-root/`, total appended 610 bytes.

```json
{"root": "/home/kobii/ao-scratch/p2/delta-root/", "files": [{"file": "/home/kobii/ao-scratch/p2/delta-root/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/bffabe58-8c3c-4cc3-a8ce-cbb2a30d6ba7.jsonl", "session_key": "bffabe58-8c3c-4cc3-a8ce-cbb2a30d6ba7", "selected": false, "before": 334417, "appended": 122, "after": 334539}, {"file": "/home/kobii/ao-scratch/p2/delta-root/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/ec14fa70-b41d-4e71-b9e8-8d952387c9d7.jsonl", "session_key": "ec14fa70-b41d-4e71-b9e8-8d952387c9d7", "selected": false, "before": 632005, "appended": 122, "after": 632127}, {"file": "/home/kobii/ao-scratch/p2/delta-root/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/22977936-9c72-48c4-be08-353f1fbbe61c.jsonl", "session_key": "22977936-9c72-48c4-be08-353f1fbbe61c", "selected": false, "before": 688823, "appended": 122, "after": 688945}, {"file": "/home/kobii/ao-scratch/p2/delta-root/C--Users-User-Apps-kme-wt-arena2/1f0ab85f-7b46-4e9c-bbb2-474bf247a3ca.jsonl", "session_key": "1f0ab85f-7b46-4e9c-bbb2-474bf247a3ca", "selected": true, "before": 784420, "appended": 122, "after": 784542}, {"file": "/home/kobii/ao-scratch/p2/delta-root/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/a05c2e9d-f336-42b3-a097-cecf4b11199f.jsonl", "session_key": "a05c2e9d-f336-42b3-a097-cecf4b11199f", "selected": true, "before": 1453187, "appended": 122, "after": 1453309}], "appended_total": 610}
```

### Step 4: canary run, challenger and scoped on the copy

Challenger (forced, certificate `delta.cert.json`), the two steps, run from the repo root:

command (all): `python3 -I wiki/tools/kme_pillars.py all --denominator KME-L --until auto --expand --root /home/kobii/ao-scratch/p2/delta-root --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan challenger --index-db /home/kobii/ao-scratch/p2/delta.sqlite --cert /home/kobii/ao-scratch/p2/delta.cert.json --path-log /home/kobii/ao-scratch/p2/delta-path.jsonl --out-dir /home/kobii/ao-scratch/p2/delta-challenger` -> exit 0, wall 15.62 s (single run, residency not measured)
command (rank): `python3 -I wiki/tools/kme_replay.py rank --denominator KME-L --until auto --expand --root /home/kobii/ao-scratch/p2/delta-root --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan challenger --index-db /home/kobii/ao-scratch/p2/delta.sqlite --cert /home/kobii/ao-scratch/p2/delta.cert.json --path-log /home/kobii/ao-scratch/p2/delta-path.jsonl --out-dir /home/kobii/ao-scratch/p2/delta-challenger` -> exit 0, wall 12.94 s
Scoped on the same copy:
command (all): `python3 -I wiki/tools/kme_pillars.py all --denominator KME-L --until auto --expand --root /home/kobii/ao-scratch/p2/delta-root --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan scoped --out-dir /home/kobii/ao-scratch/p2/delta-scoped` -> exit 0, wall 31.06 s
command (rank): `python3 -I wiki/tools/kme_replay.py rank --denominator KME-L --until auto --expand --root /home/kobii/ao-scratch/p2/delta-root --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan scoped --out-dir /home/kobii/ao-scratch/p2/delta-scoped` -> exit 0, wall 25.46 s

Path records (`/home/kobii/ao-scratch/p2/delta-path.jsonl`, 2 records): both `plan_taken: index`, `deopt: null`. The
`stale` list of both records holds exactly 5 sessions and equals the five appended sessions (checked by set equality):

```
C--Users-User-Apps-kme-wt-arena2/1f0ab85f-7b46-4e9c-bbb2-474bf247a3ca
C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/22977936-9c72-48c4-be08-353f1fbbe61c
C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/a05c2e9d-f336-42b3-a097-cecf4b11199f
C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/bffabe58-8c3c-4cc3-a8ce-cbb2a30d6ba7
C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/ec14fa70-b41d-4e71-b9e8-8d952387c9d7
```

Read set of both records: sessions 110, files 372, bytes 1,649,876,803.
Composition, checked by set arithmetic on the session ids: 102 index-selected sessions + 5 no-first-timestamp
sessions (read raw by design, 02-03 guard `no_first_ts`, as in 02-04) + 3 newly stale non-selected sessions
= 110 sessions; the two stale selected sessions are already inside the 102. Files 372 = 369 + 3
(each newly stale session has one file). Bytes 1,649,876,803 = 1,648,220,948 (02-04 read set) + 1,655,611
(the three newly read files after the append) + 244 (2 x 122 appended to the already-read selected sessions).
The strace of the traced canary-cost run below opens 372 corpus files whose sessions equal that same
110-session set (checked from `opened_paths`). The plan's phrase "selected sessions plus the three stale" is
refined, not violated, by the five no-first-timestamp sessions already read raw in 02-04.

Equivalence, challenger vs scoped on the copy (the committed `--date` of the S run is the UTC date 2026-10-06):

command: `python3 -I tools/kme_equivalence.py compare --candidate /home/kobii/ao-scratch/p2/delta-challenger --committed /home/kobii/ao-scratch/p2/delta-scoped --date 2026-10-06`
```
KMEQ pillar=D verdict=SAME committed=24eabb83e006 candidate=24eabb83e006 sessions_scanned=568/568 verdict_map=n/a
KMEQ pillar=E verdict=SAME committed=168c1d9b08c1 candidate=168c1d9b08c1 sessions_scanned=568/568 verdict_map=n/a
KMEQ pillar=F verdict=SAME committed=d3fdd7d6cdc2 candidate=d3fdd7d6cdc2 sessions_scanned=568/568 verdict_map=n/a
KMEQ pillar=G verdict=SAME committed=f49f53940e90 candidate=f49f53940e90 sessions_scanned=568/568 verdict_map=n/a
KMEQ pillar=H verdict=SAME committed=b9bd0d5514fd candidate=b9bd0d5514fd sessions_scanned=568/568 verdict_map=SAME
KMEQ pillar=I verdict=SAME committed=127d7b430aab candidate=127d7b430aab sessions_scanned=568/568 verdict_map=n/a
KMEQ pillar=L verdict=SAME committed=a1745cb643ac candidate=a1745cb643ac sessions_scanned=568/568 verdict_map=n/a
KMEQ_VERDICT=SAME same=7/7
```

Equivalence, challenger on the copy vs the committed frozen files:

command: `python3 -I tools/kme_equivalence.py compare --candidate /home/kobii/ao-scratch/p2/delta-challenger --committed vault/programs/incremental-cognition/measurements`
```
KMEQ pillar=D verdict=SAME committed=24eabb83e006 candidate=24eabb83e006 sessions_scanned=568/568 verdict_map=n/a
KMEQ pillar=E verdict=SAME committed=168c1d9b08c1 candidate=168c1d9b08c1 sessions_scanned=568/568 verdict_map=n/a
KMEQ pillar=F verdict=SAME committed=d3fdd7d6cdc2 candidate=d3fdd7d6cdc2 sessions_scanned=568/568 verdict_map=n/a
KMEQ pillar=G verdict=SAME committed=f49f53940e90 candidate=f49f53940e90 sessions_scanned=568/568 verdict_map=n/a
KMEQ pillar=H verdict=SAME committed=b9bd0d5514fd candidate=b9bd0d5514fd sessions_scanned=568/568 verdict_map=SAME
KMEQ pillar=I verdict=SAME committed=127d7b430aab candidate=127d7b430aab sessions_scanned=568/568 verdict_map=n/a
KMEQ pillar=L verdict=SAME committed=a1745cb643ac candidate=a1745cb643ac sessions_scanned=568/568 verdict_map=n/a
KMEQ_VERDICT=SAME same=7/7
```

### Step 5: post-delta cost

Warm, N=5 untraced walls of the same 7-file query (the canary runs above were the warm-up; path log
`/home/kobii/ao-scratch/p2/delta-bench-path.jsonl`: 12 records = 10 untraced + 2 traced, every one `plan_taken: index`, `deopt: null`):

command: `python3 -I tools/strace_io_sum.py run --label challenger-post-delta --repeat 5 --trace-dir /home/kobii/ao-scratch/p2/delta-bench-trace-warm --corpus-root /home/kobii/ao-scratch/p2/delta-root --scope-regex 'KobiiCraft-Core-Files|kme-wt-arena2' --forbid-regex '(?i)costaluz' --index-path /home/kobii/ao-scratch/p2/delta.sqlite --step '<C step 1 on the copy>' --step '<C step 2 on the copy>'` (the two steps are the challenger commands of step 4 with `--path-log /home/kobii/ao-scratch/p2/delta-bench-path.jsonl --out-dir /home/kobii/ao-scratch/p2/delta-bench-out`; full text in `/home/kobii/ao-scratch/p2/bench/cmd-challenger-post-delta-step{1,2}.txt`)

```json
{"label": "challenger-post-delta", "n": 5, "wall_median_s": 28.758788, "wall_runs_s": [28.731407, 28.758788, 28.859836, 28.927118, 28.636859], "failed": [], "cache": {"mode": "not evicted (page cache as found)"}}
```

Bytes, one traced run (`--repeat 0 --trace-repeat 1`, strace logs in `/home/kobii/ao-scratch/p2/strace/challenger-post-delta-r0-s*.strace`):

command: `python3 -I tools/strace_io_sum.py run --label challenger-post-delta --repeat 0 --trace-repeat 1 --trace-dir /home/kobii/ao-scratch/p2/strace --corpus-root /home/kobii/ao-scratch/p2/delta-root --scope-regex 'KobiiCraft-Core-Files|kme-wt-arena2' --forbid-regex '(?i)costaluz' --index-path /home/kobii/ao-scratch/p2/delta.sqlite --step '<C step 1 on the copy>' --step '<C step 2 on the copy>'`

```json
{"verdict": "MEASURED", "raw_bytes": 3301460730, "raw_files_opened": 372, "unique_bytes": 1649876803, "cross_project_bytes": 0, "forbidden_bytes": 0, "forbidden_opens": 0, "index_bytes": 519078504, "other_bytes": 6163665, "open_set_sha256": "a986037f571d"}
```

by_project: `{"C--Users-User-Apps-kme-wt-arena2": {"bytes": 1569084, "files": 1}, "C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files": {"bytes": 3299891646, "files": 371}}`. `raw_bytes` is two processes (`all`, `rank`) each reading the set once; `index_bytes` is the
delta index (`delta.sqlite`, a six-directory index: smaller than the whole-corpus index of the main rows).
<!-- gsd:write-continue -->
