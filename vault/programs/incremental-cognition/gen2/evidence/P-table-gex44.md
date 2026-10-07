---
pillar: P
programme: IC-gen2 autonomous-optimization
plane: gex44
denominator: KME-L
corpus_root: /home/kobii/kme-corpus/projects
index: /home/kobii/ao-scratch/p1/cold.sqlite
head: e06dafa748713179d5cc4668d234ded5ad7e832a
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
The strace of a traced canary-cost repetition (`/home/kobii/ao-scratch/p2/strace/`, first traced run; the later two-repetition run opens the identical set, `open_set_identical` true) opens 372 corpus files whose sessions equal that same
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

Bytes, two traced repetitions with identical opened-file sets (`--repeat 0 --trace-repeat 2`, strace logs in `/home/kobii/ao-scratch/p2/strace2/challenger-post-delta-r{0,1}-s*.strace`; this JSON replaces an earlier one-repetition traced run whose result was identical, `raw_bytes` 3301460730, `raw_files_opened` 372, `index_bytes` 519078504). The two steps are the challenger commands of step 4 with `--path-log /home/kobii/ao-scratch/p2/delta-bench-path-2.jsonl --out-dir /home/kobii/ao-scratch/p2/delta-bench-out-2` (4 records, all `plan_taken: index`, `deopt: null`, stale 5):

command: `python3 -I tools/strace_io_sum.py run --label challenger-post-delta --repeat 0 --trace-repeat 2 --trace-dir /home/kobii/ao-scratch/p2/strace2 --corpus-root /home/kobii/ao-scratch/p2/delta-root --scope-regex 'KobiiCraft-Core-Files|kme-wt-arena2' --forbid-regex '(?i)costaluz' --index-path /home/kobii/ao-scratch/p2/delta.sqlite --step '<C step 1 on the copy>' --step '<C step 2 on the copy>'`

```json
{"verdict": "MEASURED", "raw_bytes": 3301460730, "raw_files_opened": 372, "unique_bytes": 1649876803, "cross_project_bytes": 0, "forbidden_bytes": 0, "forbidden_opens": 0, "index_bytes": 519078504, "other_bytes": 6163665, "open_set_sha256": "a986037f571d"}
```

by_project: `{"C--Users-User-Apps-kme-wt-arena2": {"bytes": 1569084, "files": 1}, "C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files": {"bytes": 3299891646, "files": 371}}`. `raw_bytes` is two processes (`all`, `rank`) each reading the set once; `index_bytes` is the
delta index (`delta.sqlite`, a six-directory index: smaller than the whole-corpus index of the main rows).
## Runs

Setup (all rows below): real corpus `/home/kobii/kme-corpus/projects` and index `/home/kobii/ao-scratch/p1/cold.sqlite`,
both read-only. Question Q: `--denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2'`.
Scoped query S: `python3 -I wiki/tools/kme_pillars.py all <Q> --plan scoped --out-dir /home/kobii/ao-scratch/p2/bench-out-scoped` then
`python3 -I wiki/tools/kme_replay.py rank <Q> --plan scoped --out-dir /home/kobii/ao-scratch/p2/bench-out-scoped`. Challenger query C: the same two steps with
`--plan challenger --index-db /home/kobii/ao-scratch/p1/cold.sqlite --cert /home/kobii/ao-scratch/p2/bench.cert.json --path-log <log> --out-dir /home/kobii/ao-scratch/p2/bench-out-challenger`
(forced, so a deopt would exit 3 and fail the run). Certificate:
command: `python3 -I wiki/tools/kme_pillars.py certify <Q> --index-db /home/kobii/ao-scratch/p1/cold.sqlite --cert /home/kobii/ao-scratch/p2/bench.cert.json`
-> `KMEP-CERT verdict=CERTIFIED selected=102 uncovered=16`. Each configuration ran in the foreground under `timeout 590` (or less);
the cold configurations were split 3 + 2 repetitions (same label, union taken). Evicted = best-effort `posix_fadvise(DONTNEED)` of the six
scoped directories (6,948 files) and the index before every repetition: the cache state is labelled **evicted best-effort, residency not measured**, never
"cold" as a measured state. The warm configurations ran one unrecorded warm-up query first. Walls are untraced repetitions only; the
reported wall is the sum of the two steps (`all` + `rank`) of one repetition; bytes come only from the traced runs below.

### Walls, N=5 per configuration

**scoped-warm** (S, page cache as found after one warm-up query)

command: `python3 -I tools/strace_io_sum.py run --label scoped-warm --repeat 5 --trace-dir /home/kobii/ao-scratch/p2/bench/tr/scoped-warm --corpus-root /home/kobii/kme-corpus/projects --scope-regex 'KobiiCraft-Core-Files|kme-wt-arena2' --forbid-regex '(?i)costaluz' --index-path /home/kobii/ao-scratch/p1/cold.sqlite --step 'python3 -I wiki/tools/kme_pillars.py all --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan scoped --out-dir /home/kobii/ao-scratch/p2/bench-out-scoped' --step 'python3 -I wiki/tools/kme_replay.py rank --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan scoped --out-dir /home/kobii/ao-scratch/p2/bench-out-scoped'` -> JSON `/home/kobii/ao-scratch/p2/bench/scoped-warm.json`

```json
{"label": "scoped-warm", "mode": "warm", "wall_runs_s": [56.975624, 57.181243, 57.926827, 56.415992, 56.063434], "n": 5, "wall_median_s": 56.975624, "failed": [], "cache": {"mode": "not evicted (page cache as found)"}}
```

**scoped-cold** (S, evicted best-effort, residency not measured)

command: `python3 -I tools/strace_io_sum.py run --label scoped-cold --repeat 3 --trace-dir /home/kobii/ao-scratch/p2/bench/tr/scoped-cold-a --evict /home/kobii/kme-corpus/projects/C--Users-User-Apps-kme-wt-arena2 --evict /home/kobii/kme-corpus/projects/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files --evict /home/kobii/kme-corpus/projects/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files--audit-cache --evict /home/kobii/kme-corpus/projects/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files-KobiCraftServer --evict /home/kobii/kme-corpus/projects/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files-KobiCraftServer-plugins-kobicore --evict /home/kobii/kme-corpus/projects/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files-sentient-videos --evict /home/kobii/ao-scratch/p1/cold.sqlite --corpus-root /home/kobii/kme-corpus/projects --scope-regex 'KobiiCraft-Core-Files|kme-wt-arena2' --forbid-regex '(?i)costaluz' --index-path /home/kobii/ao-scratch/p1/cold.sqlite --step 'python3 -I wiki/tools/kme_pillars.py all --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan scoped --out-dir /home/kobii/ao-scratch/p2/bench-out-scoped' --step 'python3 -I wiki/tools/kme_replay.py rank --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan scoped --out-dir /home/kobii/ao-scratch/p2/bench-out-scoped'` -> JSON `/home/kobii/ao-scratch/p2/bench/scoped-cold-a.json`
command: `python3 -I tools/strace_io_sum.py run --label scoped-cold --repeat 2 --trace-dir /home/kobii/ao-scratch/p2/bench/tr/scoped-cold-b --evict /home/kobii/kme-corpus/projects/C--Users-User-Apps-kme-wt-arena2 --evict /home/kobii/kme-corpus/projects/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files --evict /home/kobii/kme-corpus/projects/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files--audit-cache --evict /home/kobii/kme-corpus/projects/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files-KobiCraftServer --evict /home/kobii/kme-corpus/projects/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files-KobiCraftServer-plugins-kobicore --evict /home/kobii/kme-corpus/projects/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files-sentient-videos --evict /home/kobii/ao-scratch/p1/cold.sqlite --corpus-root /home/kobii/kme-corpus/projects --scope-regex 'KobiiCraft-Core-Files|kme-wt-arena2' --forbid-regex '(?i)costaluz' --index-path /home/kobii/ao-scratch/p1/cold.sqlite --step 'python3 -I wiki/tools/kme_pillars.py all --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan scoped --out-dir /home/kobii/ao-scratch/p2/bench-out-scoped' --step 'python3 -I wiki/tools/kme_replay.py rank --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan scoped --out-dir /home/kobii/ao-scratch/p2/bench-out-scoped'` -> JSON `/home/kobii/ao-scratch/p2/bench/scoped-cold-b.json`

```json
{"label": "scoped-cold", "mode": "evicted best-effort, residency not measured", "wall_runs_s": [58.175961, 58.523155, 59.525624, 58.672375, 57.989338], "n": 5, "wall_median_s": 58.523155, "failed": [], "cache": {"mode": "evicted best-effort, residency not measured", "evicted": 4632, "failed": 0, "repetitions_evicted": 2}}
```

**challenger-warm** (C, page cache as found after one warm-up query)

command: `python3 -I tools/strace_io_sum.py run --label challenger-warm --repeat 5 --trace-dir /home/kobii/ao-scratch/p2/bench/tr/challenger-warm --corpus-root /home/kobii/kme-corpus/projects --scope-regex 'KobiiCraft-Core-Files|kme-wt-arena2' --forbid-regex '(?i)costaluz' --index-path /home/kobii/ao-scratch/p1/cold.sqlite --step 'python3 -I wiki/tools/kme_pillars.py all --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan challenger --index-db /home/kobii/ao-scratch/p1/cold.sqlite --cert /home/kobii/ao-scratch/p2/bench.cert.json --path-log /home/kobii/ao-scratch/p2/bench-path.jsonl --out-dir /home/kobii/ao-scratch/p2/bench-out-challenger' --step 'python3 -I wiki/tools/kme_replay.py rank --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan challenger --index-db /home/kobii/ao-scratch/p1/cold.sqlite --cert /home/kobii/ao-scratch/p2/bench.cert.json --path-log /home/kobii/ao-scratch/p2/bench-path.jsonl --out-dir /home/kobii/ao-scratch/p2/bench-out-challenger'` -> JSON `/home/kobii/ao-scratch/p2/bench/challenger-warm.json`

```json
{"label": "challenger-warm", "mode": "warm", "wall_runs_s": [29.580848, 29.400441, 29.548201, 29.731905, 29.96619], "n": 5, "wall_median_s": 29.580848, "failed": [], "cache": {"mode": "not evicted (page cache as found)"}}
```

Path records of the 5 untraced repetitions (10 = 5 repetitions x 2 steps): `/home/kobii/ao-scratch/p2/bench/path-challenger-warm.jsonl`: 10 records, plan_taken/deopt/stale/files/bytes = [('index', 'None', 0, 369, 1648220948)]

**challenger-cold** (C, evicted best-effort, residency not measured)

command: `python3 -I tools/strace_io_sum.py run --label challenger-cold --repeat 3 --trace-dir /home/kobii/ao-scratch/p2/bench/tr/challenger-cold-a --evict /home/kobii/kme-corpus/projects/C--Users-User-Apps-kme-wt-arena2 --evict /home/kobii/kme-corpus/projects/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files --evict /home/kobii/kme-corpus/projects/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files--audit-cache --evict /home/kobii/kme-corpus/projects/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files-KobiCraftServer --evict /home/kobii/kme-corpus/projects/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files-KobiCraftServer-plugins-kobicore --evict /home/kobii/kme-corpus/projects/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files-sentient-videos --evict /home/kobii/ao-scratch/p1/cold.sqlite --corpus-root /home/kobii/kme-corpus/projects --scope-regex 'KobiiCraft-Core-Files|kme-wt-arena2' --forbid-regex '(?i)costaluz' --index-path /home/kobii/ao-scratch/p1/cold.sqlite --step 'python3 -I wiki/tools/kme_pillars.py all --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan challenger --index-db /home/kobii/ao-scratch/p1/cold.sqlite --cert /home/kobii/ao-scratch/p2/bench.cert.json --path-log /home/kobii/ao-scratch/p2/bench-path.jsonl --out-dir /home/kobii/ao-scratch/p2/bench-out-challenger' --step 'python3 -I wiki/tools/kme_replay.py rank --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan challenger --index-db /home/kobii/ao-scratch/p1/cold.sqlite --cert /home/kobii/ao-scratch/p2/bench.cert.json --path-log /home/kobii/ao-scratch/p2/bench-path.jsonl --out-dir /home/kobii/ao-scratch/p2/bench-out-challenger'` -> JSON `/home/kobii/ao-scratch/p2/bench/challenger-cold-a.json`
command: `python3 -I tools/strace_io_sum.py run --label challenger-cold --repeat 2 --trace-dir /home/kobii/ao-scratch/p2/bench/tr/challenger-cold-b --evict /home/kobii/kme-corpus/projects/C--Users-User-Apps-kme-wt-arena2 --evict /home/kobii/kme-corpus/projects/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files --evict /home/kobii/kme-corpus/projects/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files--audit-cache --evict /home/kobii/kme-corpus/projects/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files-KobiCraftServer --evict /home/kobii/kme-corpus/projects/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files-KobiCraftServer-plugins-kobicore --evict /home/kobii/kme-corpus/projects/C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files-sentient-videos --evict /home/kobii/ao-scratch/p1/cold.sqlite --corpus-root /home/kobii/kme-corpus/projects --scope-regex 'KobiiCraft-Core-Files|kme-wt-arena2' --forbid-regex '(?i)costaluz' --index-path /home/kobii/ao-scratch/p1/cold.sqlite --step 'python3 -I wiki/tools/kme_pillars.py all --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan challenger --index-db /home/kobii/ao-scratch/p1/cold.sqlite --cert /home/kobii/ao-scratch/p2/bench.cert.json --path-log /home/kobii/ao-scratch/p2/bench-path.jsonl --out-dir /home/kobii/ao-scratch/p2/bench-out-challenger' --step 'python3 -I wiki/tools/kme_replay.py rank --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan challenger --index-db /home/kobii/ao-scratch/p1/cold.sqlite --cert /home/kobii/ao-scratch/p2/bench.cert.json --path-log /home/kobii/ao-scratch/p2/bench-path.jsonl --out-dir /home/kobii/ao-scratch/p2/bench-out-challenger'` -> JSON `/home/kobii/ao-scratch/p2/bench/challenger-cold-b.json`

```json
{"label": "challenger-cold", "mode": "evicted best-effort, residency not measured", "wall_runs_s": [37.928528, 37.297473, 37.451222, 37.529019, 37.783499], "n": 5, "wall_median_s": 37.529019, "failed": [], "cache": {"mode": "evicted best-effort, residency not measured", "evicted": 4632, "failed": 0, "repetitions_evicted": 2}}
```

Path records (`/home/kobii/ao-scratch/p2/bench/path-challenger-cold.jsonl`): 10 records, plan_taken/deopt/stale/files/bytes = [('index', 'None', 0, 369, 1648220948)]

### Bytes, two traced repetitions per path

**scoped-traced** (S)

command: `python3 -I tools/strace_io_sum.py run --label scoped-traced --repeat 0 --trace-repeat 2 --trace-dir /home/kobii/ao-scratch/p2/bench/tr/scoped-traced --corpus-root /home/kobii/kme-corpus/projects --scope-regex 'KobiiCraft-Core-Files|kme-wt-arena2' --forbid-regex '(?i)costaluz' --index-path /home/kobii/ao-scratch/p1/cold.sqlite --step 'python3 -I wiki/tools/kme_pillars.py all --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan scoped --out-dir /home/kobii/ao-scratch/p2/bench-out-scoped' --step 'python3 -I wiki/tools/kme_replay.py rank --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan scoped --out-dir /home/kobii/ao-scratch/p2/bench-out-scoped'` -> JSON `/home/kobii/ao-scratch/p2/bench/scoped-traced.json`

```json
{"label": "scoped-traced", "open_set_identical": true, "failed": [], "traced": [{"verdict": "MEASURED", "raw_bytes": 6120339068, "raw_files_opened": 995, "unique_bytes": 3055976146, "cross_project_bytes": 0, "forbidden_bytes": 0, "forbidden_opens": 0, "index_bytes": 0, "other_bytes": 4500551, "lines_unparsed": 0, "run": 0, "open_set_sha256": "6309f6db454d"}, {"verdict": "MEASURED", "raw_bytes": 6120339068, "raw_files_opened": 995, "unique_bytes": 3055976146, "cross_project_bytes": 0, "forbidden_bytes": 0, "forbidden_opens": 0, "index_bytes": 0, "other_bytes": 4500551, "lines_unparsed": 0, "run": 1, "open_set_sha256": "6309f6db454d"}]}
```

**challenger-traced** (C)

command: `python3 -I tools/strace_io_sum.py run --label challenger-traced --repeat 0 --trace-repeat 2 --trace-dir /home/kobii/ao-scratch/p2/bench/tr/challenger-traced --corpus-root /home/kobii/kme-corpus/projects --scope-regex 'KobiiCraft-Core-Files|kme-wt-arena2' --forbid-regex '(?i)costaluz' --index-path /home/kobii/ao-scratch/p1/cold.sqlite --step 'python3 -I wiki/tools/kme_pillars.py all --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan challenger --index-db /home/kobii/ao-scratch/p1/cold.sqlite --cert /home/kobii/ao-scratch/p2/bench.cert.json --path-log /home/kobii/ao-scratch/p2/bench-path.jsonl --out-dir /home/kobii/ao-scratch/p2/bench-out-challenger' --step 'python3 -I wiki/tools/kme_replay.py rank --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan challenger --index-db /home/kobii/ao-scratch/p1/cold.sqlite --cert /home/kobii/ao-scratch/p2/bench.cert.json --path-log /home/kobii/ao-scratch/p2/bench-path.jsonl --out-dir /home/kobii/ao-scratch/p2/bench-out-challenger'` -> JSON `/home/kobii/ao-scratch/p2/bench/challenger-traced.json`

```json
{"label": "challenger-traced", "open_set_identical": true, "failed": [], "traced": [{"verdict": "MEASURED", "raw_bytes": 3298099868, "raw_files_opened": 369, "unique_bytes": 1648220948, "cross_project_bytes": 0, "forbidden_bytes": 0, "forbidden_opens": 0, "index_bytes": 1805435496, "other_bytes": 6163481, "lines_unparsed": 362, "run": 0, "open_set_sha256": "f58f3283e947"}, {"verdict": "MEASURED", "raw_bytes": 3298099868, "raw_files_opened": 369, "unique_bytes": 1648220948, "cross_project_bytes": 0, "forbidden_bytes": 0, "forbidden_opens": 0, "index_bytes": 1805435496, "other_bytes": 6163481, "lines_unparsed": 362, "run": 1, "open_set_sha256": "f58f3283e947"}]}
```

Path records of the challenger traced run (`/home/kobii/ao-scratch/p2/bench/path-challenger-traced.jsonl`): 4 records, plan_taken/deopt/stale/files/bytes = [('index', 'None', 0, 369, 1648220948)]

Every challenger path record of the bench (warm, cold and traced) shows `plan_taken: index` and `deopt: null`, stale 0, 369 files, 1,648,220,948 bytes. `raw_bytes` of a 7-file run is two processes (`all`, `rank`) each reading its set once; `index_bytes` is likewise two reads of the index. `open_set_identical` is true for both pairs and for the post-delta pair.

Equivalence of the bench configuration itself (one fresh run of each plan into an empty out-dir, then compare against the committed files): challenger `KMEQ_VERDICT=SAME same=7/7`, scoped `KMEQ_VERDICT=SAME same=7/7` (commands: C and S as above with `--out-dir /home/kobii/ao-scratch/p2/bench-eq-challenger` / `bench-eq-scoped`; `python3 -I tools/kme_equivalence.py compare --candidate <dir> --committed vault/programs/incremental-cognition/measurements`). The repeated bench out-dirs accumulate suffixed files and compare as `MISSING reason=ambiguous`, which is why the checks use fresh dirs.

## Table

| row | plan | cache | n | wall (median s) | raw bytes | unique bytes | raw files opened | cross-project bytes | CostaLuz bytes | index bytes | source |
|---|---|---|---|---|---|---|---|---|---|---|---|
| champion Run 5 (unscoped, cited) | champion | n/a | 1 | 869 (cited) | 109,088,283,520 (derived) | 9,934,971,549 (derived) | 4,015 distinct (derived) | 78,486,588,180 (derived) | 998,161,080 (derived) | 0 (no index) | ledger frozen.champion.run5; bytes: 10 x 02-04 unscoped scan |
| Run 6 population (scoped, cited) | scoped | page cache as found | 1 | 24 (cited, rchar 2.83 GB) | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED | 0 (no index) | ledger frozen.champion.run6 |
| Run 6 seven separate runs D..I, L (scoped, cited) | scoped | page cache as found | 7 | 177 (cited sum, rchar 19.47 GB) | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED | UNMEASURED | 0 (no index) | ledger frozen.champion.run6 |
| scoped all+rank, evicted | scoped | evicted best-effort, residency not measured | 5 | 58.523 | 6,120,339,068 | 3,055,976,146 | 995 | 0 | 0 | 0 | bench JSON scoped-cold-a/b, scoped-traced |
| scoped all+rank, warm | scoped | warm | 5 | 56.976 | 6,120,339,068 | 3,055,976,146 | 995 | 0 | 0 | 0 | bench JSON scoped-warm, scoped-traced |
| challenger all+rank, evicted | challenger | evicted best-effort, residency not measured | 5 | 37.529 | 3,298,099,868 | 1,648,220,948 | 369 | 0 | 0 | 1,805,435,496 | bench JSON challenger-cold-a/b, challenger-traced |
| challenger all+rank, warm | challenger | warm | 5 | 29.581 | 3,298,099,868 | 1,648,220,948 | 369 | 0 | 0 | 1,805,435,496 | bench JSON challenger-warm, challenger-traced |
| challenger post-delta (scratch copy) | challenger | warm | 5 | 28.759 | 3,301,460,730 | 1,649,876,803 | 372 | 0 | 0 | 519,078,504 | bench JSON challenger-post-delta-warm/-traced; index = delta.sqlite (six-directory index) |

Caption: Cross-project bytes count transcript bytes outside the KME-L scope; index bytes are reads of the SQLite index, a whole-corpus file that holds metadata rows of every project (CostaLuz included) and no transcript text.

Reading the columns. `wall` is the median of N=5 untraced repetitions of the two-step 7-file query (`all` then `rank`), never a traced wall; the three cited rows carry the wall of the frozen champion runs. `raw bytes` is the strace read-family sum on corpus files for the two processes of one query; `unique bytes` is the size of the distinct files opened; `raw files opened` is the distinct-file count; `CostaLuz bytes` is the forbid-regex (`(?i)costaluz`) path match; `index bytes` is the challenger's read of the index DB, in its own column and never added to `raw bytes`. Cited rows say `rchar` where the figure is process rchar (every read, page cache included), a different instrument from the strace column. `UNMEASURED` means no strace was taken on that run; it is not zero. The champion Run 5 byte columns are derived: ten locator scans times the single unscoped scan of 02-04 (`raw_files_opened` is the distinct-file count of one scan, 4,015; the ten scans open each file ten times). The post-delta row runs on the scratch copy of the six scoped directories with its own six-directory index (`delta.sqlite`), so its `index bytes` are not comparable to the whole-corpus index of the other challenger rows, and its CostaLuz column is zero by construction of the copy. The evicted rows are best-effort page-cache eviction, residency not measured.

## Data

```json
{
 "plane": "gex44",
 "denominator": "KME-L",
 "n_per_configuration": 5,
 "scoped": {
  "warm": {
   "wall_median_s": 56.975624,
   "wall_runs": [
    56.975624,
    57.181243,
    57.926827,
    56.415992,
    56.063434
   ],
   "n": 5,
   "cache": "warm (one unrecorded warm-up query first)",
   "source_json": [
    "/home/kobii/ao-scratch/p2/bench/scoped-warm.json"
   ]
  },
  "cold": {
   "wall_median_s": 58.523155,
   "wall_runs": [
    58.175961,
    58.523155,
    59.525624,
    58.672375,
    57.989338
   ],
   "n": 5,
   "cache": "evicted best-effort, residency not measured",
   "source_json": [
    "/home/kobii/ao-scratch/p2/bench/scoped-cold-a.json",
    "/home/kobii/ao-scratch/p2/bench/scoped-cold-b.json"
   ]
  },
  "raw_bytes": 6120339068,
  "unique_bytes": 3055976146,
  "raw_files_opened": 995,
  "cross_project_bytes": 0,
  "forbidden_bytes": 0,
  "index_bytes": 0,
  "open_set_sha256": "6309f6db454d",
  "traced_repetitions": 2,
  "trace_json": "/home/kobii/ao-scratch/p2/bench/scoped-traced.json",
  "plan": "scoped all+rank",
  "steps": [
   "python3 -I wiki/tools/kme_pillars.py all --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan scoped --out-dir /home/kobii/ao-scratch/p2/bench-out-scoped",
   "python3 -I wiki/tools/kme_replay.py rank --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan scoped --out-dir /home/kobii/ao-scratch/p2/bench-out-scoped"
  ]
 },
 "challenger": {
  "warm": {
   "wall_median_s": 29.580848,
   "wall_runs": [
    29.580848,
    29.400441,
    29.548201,
    29.731905,
    29.96619
   ],
   "n": 5,
   "cache": "warm (one unrecorded warm-up query first)",
   "source_json": [
    "/home/kobii/ao-scratch/p2/bench/challenger-warm.json"
   ]
  },
  "cold": {
   "wall_median_s": 37.529019,
   "wall_runs": [
    37.928528,
    37.297473,
    37.451222,
    37.529019,
    37.783499
   ],
   "n": 5,
   "cache": "evicted best-effort, residency not measured",
   "source_json": [
    "/home/kobii/ao-scratch/p2/bench/challenger-cold-a.json",
    "/home/kobii/ao-scratch/p2/bench/challenger-cold-b.json"
   ]
  },
  "raw_bytes": 3298099868,
  "unique_bytes": 1648220948,
  "raw_files_opened": 369,
  "cross_project_bytes": 0,
  "forbidden_bytes": 0,
  "index_bytes": 1805435496,
  "open_set_sha256": "f58f3283e947",
  "traced_repetitions": 2,
  "trace_json": "/home/kobii/ao-scratch/p2/bench/challenger-traced.json",
  "plan": "challenger all+rank",
  "steps": [
   "python3 -I wiki/tools/kme_pillars.py all --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan challenger --index-db /home/kobii/ao-scratch/p1/cold.sqlite --cert /home/kobii/ao-scratch/p2/bench.cert.json --path-log /home/kobii/ao-scratch/p2/bench-path.jsonl --out-dir /home/kobii/ao-scratch/p2/bench-out-challenger",
   "python3 -I wiki/tools/kme_replay.py rank --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan challenger --index-db /home/kobii/ao-scratch/p1/cold.sqlite --cert /home/kobii/ao-scratch/p2/bench.cert.json --path-log /home/kobii/ao-scratch/p2/bench-path.jsonl --out-dir /home/kobii/ao-scratch/p2/bench-out-challenger"
  ]
 },
 "challenger_post_delta": {
  "warm": {
   "wall_median_s": 28.758788,
   "wall_runs": [
    28.731407,
    28.758788,
    28.859836,
    28.927118,
    28.636859
   ],
   "n": 5,
   "cache": "warm (canary runs just before)",
   "source_json": [
    "/home/kobii/ao-scratch/p2/bench/challenger-post-delta-warm.json"
   ]
  },
  "raw_bytes": 3301460730,
  "unique_bytes": 1649876803,
  "raw_files_opened": 372,
  "cross_project_bytes": 0,
  "forbidden_bytes": 0,
  "index_bytes": 519078504,
  "open_set_sha256": "a986037f571d",
  "traced_repetitions": 2,
  "trace_json": "/home/kobii/ao-scratch/p2/bench/challenger-post-delta-traced.json",
  "plan": "challenger all+rank on scratch copy",
  "steps": [
   "python3 -I wiki/tools/kme_pillars.py all --denominator KME-L --until auto --expand --root /home/kobii/ao-scratch/p2/delta-root --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan challenger --index-db /home/kobii/ao-scratch/p2/delta.sqlite --cert /home/kobii/ao-scratch/p2/delta.cert.json --path-log /home/kobii/ao-scratch/p2/delta-bench-path.jsonl --out-dir /home/kobii/ao-scratch/p2/delta-bench-out",
   "python3 -I wiki/tools/kme_replay.py rank --denominator KME-L --until auto --expand --root /home/kobii/ao-scratch/p2/delta-root --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan challenger --index-db /home/kobii/ao-scratch/p2/delta.sqlite --cert /home/kobii/ao-scratch/p2/delta.cert.json --path-log /home/kobii/ao-scratch/p2/delta-bench-path.jsonl --out-dir /home/kobii/ao-scratch/p2/delta-bench-out"
  ],
  "corpus_root": "/home/kobii/ao-scratch/p2/delta-root",
  "index": "/home/kobii/ao-scratch/p2/delta.sqlite"
 },
 "cited": {
  "run5": {
   "wall_s": 869,
   "rchar_GB": 101.53,
   "locator_scans": 10,
   "population_match": "drifted",
   "source": "gen2 ledger frozen.champion.run5; evidence/champion/run5-summary.txt",
   "derived_bytes": {
    "basis": "10 x the 02-04 unscoped single scan (P-exposure-gex44.md, control 2: raw 10,908,828,352, 4,015 files, 109 s under strace, one run)",
    "raw_bytes": 109088283520,
    "unique_bytes": 9934971549,
    "raw_files_opened": 4015,
    "raw_file_opens": 40150,
    "cross_project_bytes": 78486588180,
    "forbidden_bytes": 998161080,
    "index_bytes": 0,
    "label": "derived, not measured on Run 5 itself"
   }
  },
  "run6_population": {
   "wall_s": 24,
   "rchar_GB": 2.83,
   "source": "gen2 ledger frozen.champion.run6; evidence/champion/run6-summary.txt step r4-population",
   "raw_bytes": "UNMEASURED",
   "unique_bytes": "UNMEASURED",
   "cross_project_bytes": "UNMEASURED",
   "forbidden_bytes": "UNMEASURED"
  },
  "run6_seven_runs": {
   "wall_s": 177,
   "wall_s_each": [
    26,
    24,
    24,
    28,
    24,
    25,
    26
   ],
   "rchar_GB": 19.47,
   "rchar_GB_each": [
    2.85,
    2.77,
    2.73,
    2.85,
    2.65,
    2.8,
    2.82
   ],
   "pillars": "D E F G H I L",
   "source": "evidence/champion/run6-summary.txt steps r4-d-kmel, r5-e, r6-f, r7-g, r8-h, r9-i, r10-l-rank (r4-d-w7 excluded)",
   "raw_bytes": "UNMEASURED",
   "unique_bytes": "UNMEASURED",
   "cross_project_bytes": "UNMEASURED",
   "forbidden_bytes": "UNMEASURED"
  },
  "rchar_note": "read_GB in the cited rows is process rchar (every read, page cache included), not the strace raw_bytes column"
 },
 "baseline_for_criterion_5": "scoped all+rank (orchestrator decision 3)",
 "units": {
  "wall_median_s": "seconds, sum of the two steps (all + rank), median of 5 untraced repetitions",
  "raw_bytes": "strace read-family bytes on corpus files, two processes (all, rank), one traced repetition (the two repetitions are equal)",
  "index_bytes": "strace read-family bytes on the index DB, kept apart from raw_bytes"
 }
}
```

Computed by `/home/kobii/ao-scratch/p2/gen_table_t3.py` from the bench JSON under `/home/kobii/ao-scratch/p2/bench/`: wall medians from `wall_runs` of the untraced repetitions (split cold calls united), bytes from the traced JSON after asserting `open_set_identical` true and the two traced repetitions equal. Plan 02-06 reads this block with `json.loads` of the fence above; the fixed rule needs `scoped.warm.wall_median_s`, `challenger.warm.wall_median_s`, `scoped.raw_bytes`, `challenger.raw_bytes` and `challenger.index_bytes`. The judgement is 02-06's.

## Read-only proof

command: `python3 -I -c 'import test_kme_challenger as t; print(t.corpus_manifest(), t.file_identity())'` (tools/test_kme_challenger.py functions `corpus_manifest`, `file_identity`; lstat walk, no file opened for the manifest), run before the first step of plan 02-05 and after the last (`/home/kobii/ao-scratch/p2/hash-before-0205.json`, `hash-after-0205.json`).

| What | Before | After | Equal |
|---|---|---|---|
| corpus manifest sha256 | `29969e7d6ab1bb271373c5004f34b2390918234e344c09c8994dc986b0a69ce0` | `29969e7d6ab1bb271373c5004f34b2390918234e344c09c8994dc986b0a69ce0` | true |
| corpus files / bytes | 10,577 / 10,205,326,251 | 10,577 / 10,205,326,251 | true |
| index sha256 | `6ddd159a914d65dd7a786bf4c5366a79730b397e8d0f197259e60aef89a0dd07` | `6ddd159a914d65dd7a786bf4c5366a79730b397e8d0f197259e60aef89a0dd07` | true |
| index mtime_ns | 1791321612414996448 | 1791321612414996448 | true |
| index sidecars (-wal, -shm, -journal) | {'-wal': False, '-shm': False, '-journal': False} | {'-wal': False, '-shm': False, '-journal': False} | true |

The delta was written only to `/home/kobii/ao-scratch/p2/delta-root/` (guard in `append_delta.py`, refusal shown above); the scratch copy, `delta.sqlite`, certificates, strace logs and bench JSON stay in `/home/kobii/ao-scratch/p2/` (not deleted, not committed).

