---
pillar: P
programme: IC-gen2 autonomous-optimization
plane: gex44
denominator: KME-L
corpus_root: /home/kobii/kme-corpus/projects
index: /home/kobii/ao-scratch/p1/cold.sqlite
forbid_regex: (?i)costaluz
head: 87fa25bbd63f9df2cf3cfbe51c195e370ebb7ed7
measured_at: 2026-10-06T23:23:12Z
---

# [P] (IC-gen2) KME-L challenger: cross-project exposure on the GEX44 corpus copy

Phase 2 criterion 3, second sentence: the KME-only challenger query opens no CostaLuz byte, shown at the OS layer with
two controls that fire. Host `kobiicraft-gex44` (`plane: gex44`), Owner-authorized read-only corpus copy, Phase 1
index opened `mode=ro`. Strace logs and every scratch output live under `/home/kobii/ao-scratch/p2/` (outside the repo,
never committed; they hold paths of every project and data prefixes). This file carries only summed counts, paths,
digests and verdicts, no transcript text. No command used `~/.claude/projects`.

## Method

Capture: `strace -f -y -e trace=openat,read,pread64,readv,preadv -o <log> <command>` (via `tools/strace_io_sum.py run
--repeat 0 --trace-repeat 1`, or directly for control 2), summed by `tools/strace_io_sum.py`. Columns (02-RESEARCH
section 3): `raw_bytes` = bytes returned by read-family calls on files under the corpus root; `raw_files_opened` =
distinct corpus files opened; `unique_bytes` = size of those files at summary time (not bytes read);
`cross_project_bytes` = transcript bytes read from files whose project directory does not match the scope regex
`KobiiCraft-Core-Files|kme-wt-arena2`; `forbidden_bytes` / `forbidden_opens` = bytes read from / opens of any path
matching `(?i)costaluz` (opens include directories); `index_bytes` = bytes read from the index DB and its
`-wal` / `-shm` / `-journal` siblings; `other_bytes` = reads on other paths. Caption: cross-project exposure counts
transcript bytes; the index DB is a whole-corpus file holding metadata rows of every project, CostaLuz included, read as
index bytes, column index_bytes.

Limits of the instrument, stated: the forbidden test is on the file PATH. A KME-project transcript may carry the string
in its own text (the Owner's email domain appears in the data prefix of three reads of KME-project subagent
transcripts in each challenger log: `grep -ci costaluz` on the logs gives 3 per challenger log); that is not a
CostaLuz file and is not counted as one. `lines_unparsed` is the count of trace lines the summer could not attribute
(process exit and signal lines, resumed reads without a return); a read-family line without a path annotation: 0 in
the 7-file logs (checked with a regex over the raw logs).

## Challenger, KME-only

Certificate (same question flags as the measuring run): `python3 -I wiki/tools/kme_pillars.py certify --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --index-db /home/kobii/ao-scratch/p1/cold.sqlite --cert /home/kobii/ao-scratch/p2/exposure-20261006T232312Z/kmel.cert.json` -> exit 0,
`KMEP-CERT verdict=CERTIFIED selected=102 uncovered=16 cert=/home/kobii/ao-scratch/p2/exposure-20261006T232312Z/kmel.cert.json`.

Population run (traced). command: `python3 -I tools/strace_io_sum.py run --label challenger-population --repeat 0 --trace-repeat 1 --trace-dir /home/kobii/ao-scratch/p2/exposure-20261006T232312Z/strace --corpus-root /home/kobii/kme-corpus/projects --scope-regex 'KobiiCraft-Core-Files|kme-wt-arena2' --forbid-regex (?i)costaluz --index-path /home/kobii/ao-scratch/p1/cold.sqlite --step 'python3 -I wiki/tools/kme_pillars.py population --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan challenger --index-db /home/kobii/ao-scratch/p1/cold.sqlite --cert /home/kobii/ao-scratch/p2/exposure-20261006T232312Z/kmel.cert.json --path-log /home/kobii/ao-scratch/p2/exposure-20261006T232312Z/pop-path.jsonl'`

```json
{
 "verdict": "MEASURED",
 "syscalls_parsed": 424148,
 "lines_unparsed": 181,
 "raw_bytes": 1649049934,
 "raw_files_opened": 369,
 "unique_bytes": 1648220948,
 "cross_project_bytes": 0,
 "forbidden_bytes": 0,
 "forbidden_opens": 0,
 "index_bytes": 902717748,
 "other_bytes": 2988412,
 "open_set_sha256": "f58f3283e947"
}
```

by_project (transcript files and bytes): `{"C--Users-User-Apps-kme-wt-arena2": {"bytes": 784420, "files": 1}, "C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files": {"bytes": 1648265514, "files": 368}}`

Path record of that run (`/home/kobii/ao-scratch/p2/exposure-20261006T232312Z/pop-path.jsonl`): plan_taken `index`, deopt `None`,
read_set.files 369 (equal to `raw_files_opened`), read_set.bytes 1,648,220,948
(equal to `unique_bytes`), stale `[]`.

The 7-file query (traced once; `all` then `rank` as two steps of one run, out-dir `/home/kobii/ao-scratch/p2/exp7/out`, certificate
`/home/kobii/ao-scratch/p2/exposure-20261006T231828Z/kmel.cert.json`, written by an earlier `--real-exposure` run for the
same question flags; run command: `python3 -I tools/strace_io_sum.py run --label challenger-7file --repeat 0 --trace-repeat 1
--trace-dir /home/kobii/ao-scratch/p2/exp7/strace --corpus-root /home/kobii/kme-corpus/projects --scope-regex
'KobiiCraft-Core-Files|kme-wt-arena2' --forbid-regex '(?i)costaluz' --index-path /home/kobii/ao-scratch/p1/cold.sqlite`
with the two steps:

step 1: `python3 -I wiki/tools/kme_pillars.py all --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan challenger --index-db /home/kobii/ao-scratch/p1/cold.sqlite --cert /home/kobii/ao-scratch/p2/exposure-20261006T231828Z/kmel.cert.json --path-log /home/kobii/ao-scratch/p2/exp7/path7.jsonl --out-dir /home/kobii/ao-scratch/p2/exp7/out`
step 2: `python3 -I wiki/tools/kme_replay.py rank --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan challenger --index-db /home/kobii/ao-scratch/p1/cold.sqlite --cert /home/kobii/ao-scratch/p2/exposure-20261006T231828Z/kmel.cert.json --path-log /home/kobii/ao-scratch/p2/exp7/path7.jsonl --out-dir /home/kobii/ao-scratch/p2/exp7/out`

```json
{
 "verdict": "MEASURED",
 "syscalls_parsed": 849201,
 "lines_unparsed": 362,
 "raw_bytes": 3298099868,
 "raw_files_opened": 369,
 "unique_bytes": 1648220948,
 "cross_project_bytes": 0,
 "forbidden_bytes": 0,
 "forbidden_opens": 0,
 "index_bytes": 1805435496,
 "other_bytes": 6163531,
 "open_set_sha256": "f58f3283e947"
}
```

by_project: `{"C--Users-User-Apps-kme-wt-arena2": {"bytes": 1568840, "files": 1}, "C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files": {"bytes": 3296531028, "files": 368}}`

Both path records of that run: kme_pillars.all plan_taken=index deopt=None files=369 bytes=1,648,220,948 stale=[]; kme_replay.rank plan_taken=index deopt=None files=369 bytes=1,648,220,948 stale=[].
`raw_bytes` of the 7-file run is about twice a single read of the set because the two commands each read it once
(`all` and `rank` are separate processes); `index_bytes` is likewise two reads of the index. `open_set_sha256` of the
population run and of the 7-file run are equal (`f58f3283e947`): the population run reads exactly the files the 7-file query reads.
The 7-file run's outputs compare SAME against the committed files: `KMEQ_VERDICT=SAME same=7/7`
(`python3 -I tools/kme_equivalence.py compare --candidate /home/kobii/ao-scratch/p2/exp7/out --committed vault/programs/incremental-cognition/measurements`).

`forbidden_bytes` is 0, `forbidden_opens` is 0 and `cross_project_bytes` is 0 for both runs.

## Negative control 1: filter plus CostaLuz

Same instrument, same forbid regex, same scope regex; only the question's filter gains `|CostaLuz`, with an explicit
`--until` and the scoped plan (this population is not the frozen one, so the command exits 3, allowed with
`--ok-exit 3`). command: `python3 -I tools/strace_io_sum.py run --label control-filter-costaluz --repeat 0 --trace-repeat 1 --trace-dir /home/kobii/ao-scratch/p2/exposure-20261006T232312Z/strace --corpus-root /home/kobii/kme-corpus/projects --scope-regex 'KobiiCraft-Core-Files|kme-wt-arena2' --forbid-regex (?i)costaluz --index-path /home/kobii/ao-scratch/p1/cold.sqlite --ok-exit 0 --ok-exit 3 --step 'python3 -I wiki/tools/kme_pillars.py population --denominator KME-L --until 2026-10-03T16:13:37Z --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2|CostaLuz' --plan scoped'`

```json
{
 "verdict": "MEASURED",
 "syscalls_parsed": 389560,
 "lines_unparsed": 0,
 "raw_bytes": 3159156316,
 "raw_files_opened": 1017,
 "unique_bytes": 3154856432,
 "cross_project_bytes": 98986782,
 "forbidden_bytes": 98986782,
 "forbidden_opens": 73,
 "index_bytes": 0,
 "other_bytes": 2142281,
 "open_set_sha256": "9915036952a3"
}
```

forbidden_bytes 98,986,782 (above 0), forbidden_opens 73, cross_project_bytes 98,986,782: the
detector fires when CostaLuz is read. (The corpus holds 44 CostaLuz `.jsonl` files / 99,693,228 bytes by
`find . -ipath '*costaluz*' -name '*.jsonl'`, quoted from the plan, not re-measured here; the forbidden figure also counts any
other file whose path contains the string.)

## Negative control 2: unscoped single scan

Full, not partial: the scan finished in 109 s wall under strace (wall includes strace overhead, one run, residency
not measured), exit 3 because the unfiltered population is not the frozen KME-L population
(`population_match: drifted`, 105 active sessions against the frozen 102, `corpus.sessions_scanned`
2538, 344 project dirs). Started 2026-10-06T23:21:04Z.
Never `--until auto` unscoped.

command: `timeout 590 strace -f -y -e trace=openat,read,pread64,readv,preadv -o /home/kobii/ao-scratch/p2/unscoped.strace python3 -I wiki/tools/kme_pillars.py population --plan champion --denominator KME-L --until 2026-10-03T16:13:37Z --expand --root /home/kobii/kme-corpus/projects`
command (sum): `python3 -I tools/strace_io_sum.py sum /home/kobii/ao-scratch/p2/unscoped.strace --corpus-root /home/kobii/kme-corpus/projects --scope-regex 'KobiiCraft-Core-Files|kme-wt-arena2' --forbid-regex '(?i)costaluz' --index-path /home/kobii/ao-scratch/p1/cold.sqlite`

```json
{
 "verdict": "MEASURED",
 "syscalls_parsed": 1348056,
 "lines_unparsed": 0,
 "raw_bytes": 10908828352,
 "raw_files_opened": 4015,
 "unique_bytes": 9934971549,
 "cross_project_bytes": 7848658818,
 "forbidden_bytes": 99816108,
 "forbidden_opens": 109,
 "index_bytes": 0,
 "other_bytes": 2142281,
 "open_set_sha256": "bcadfdc96cf3"
}
```

This single unscoped champion scan is the basis plan 02-05 uses for the champion row's byte columns.

## Comparison

| Run | raw_bytes | raw_files_opened | cross_project_bytes | forbidden_bytes | forbidden_opens | index_bytes |
|---|---|---|---|---|---|---|
| challenger population (KME-only) | 1,649,049,934 | 369 | 0 | 0 | 0 | 902,717,748 |
| challenger 7-file query (2 processes) | 3,298,099,868 | 369 | 0 | 0 | 0 | 1,805,435,496 |
| control 1: filter + CostaLuz (scoped) | 3,159,156,316 | 1017 | 98,986,782 | 98,986,782 | 73 | 0 |
| control 2: unscoped champion scan | 10,908,828,352 | 4015 | 7,848,658,818 | 99,816,108 | 109 | 0 |

The challenger reads 902,717,748 index bytes per process (the whole-corpus DB, metadata rows of every project);
that is a metadata read, reported in its own column and never mixed into the transcript columns. What the index read
costs against the transcript bytes it saves is the cost comparison of plan 02-05, not claimed here.

## Gate

command: `timeout 600 python3 -I tools/test_kme_challenger.py --real-exposure`

```
PASS V-KMEC-COSTALUZ-ZERO-REAL challenger {'forbidden_bytes': 0, 'forbidden_opens': 0, 'cross_project_bytes': 0, 'raw_bytes': 1649049934, 'raw_files_opened': 369, 'unique_bytes': 1648220948, 'index_bytes': 902717748} planned_files=369; control forbidden_bytes=98986782 forbidden_opens=73 cross_project_bytes=98986782 (halves: challenger=True control_fires=True)
PASS V-KMEC-EXPOSURE-READONLY manifest before=29969e7d6ab1 after=29969e7d6ab1; index sha before=6ddd159a914d after=6ddd159a914d mtime_ns equal=True
KMEC_EXPOSURE_PASS=2/2  threshold=2/2  skipped=0  inconclusive=0
```

Summary line: `KMEC_EXPOSURE_PASS=2/2  threshold=2/2  skipped=0  inconclusive=0`

## Read-only proof

Corpus manifest (sha256 of sorted `size mtime_ns relpath` lines from an `os.lstat` pass, no file opened) and index
sha256 + mtime_ns, taken by `--real-exposure` before and after its runs (functions `corpus_manifest`, `file_identity`):

| What | Before | After | Equal |
|---|---|---|---|
| corpus manifest sha256 | `29969e7d6ab1bb271373c5004f34b2390918234e344c09c8994dc986b0a69ce0` | `29969e7d6ab1bb271373c5004f34b2390918234e344c09c8994dc986b0a69ce0` | true |
| corpus files / bytes | 10,577 / 10,205,326,251 | 10,577 / 10,205,326,251 | true |
| index sha256 | `6ddd159a914d65dd7a786bf4c5366a79730b397e8d0f197259e60aef89a0dd07` | `6ddd159a914d65dd7a786bf4c5366a79730b397e8d0f197259e60aef89a0dd07` | true |
| index mtime_ns | 1791321612414996448 | 1791321612414996448 | true |

The 7-file run and control 2 ran outside the gate. A final check after them (same two functions, run at
2026-10-06T23:25:11Z) gives corpus manifest `29969e7d6ab1bb271373c5004f34b2390918234e344c09c8994dc986b0a69ce0` (10,577 files) and index sha256
`6ddd159a914d65dd7a786bf4c5366a79730b397e8d0f197259e60aef89a0dd07`, mtime_ns 1791321612414996448: equal to the before values above (true).
