---
pillar: P
programme: IC-gen2 autonomous-optimization
plane: gex44
denominator: KME-L
corpus_root: /home/kobii/kme-corpus/projects
index: /home/kobii/ao-scratch/p1/cold.sqlite
head: a97c2f0d8b4aa5b9b99a003cbfcf0bf6a4347b98
measured_at: 2026-10-06T23:16:14Z
---

# [P] (IC-gen2) KME-L challenger equivalence on the GEX44 corpus copy

Phase 2 criterion 2 (governing spec `vault/specs/autonomous-optimization.md`, AOP-P, CP-6). Everything below was
measured on host `kobiicraft-gex44` (`plane: gex44`) against the Owner-authorized, read-only corpus copy
`/home/kobii/kme-corpus/projects` and the Phase 1 index `/home/kobii/ao-scratch/p1/cold.sqlite` (opened `mode=ro`).
All scratch output lives in `/home/kobii/ao-scratch/p2/real-20261006T231614Z` (outside the repo, never committed). No command used `~/.claude/projects`.
The question is the committed KME-L question (`--denominator KME-L --until auto --expand`, filter
`KobiiCraft-Core-Files|kme-wt-arena2`, freeze instant `2026-10-03T16:13:37Z`); the committed files compared against
are `vault/programs/incremental-cognition/measurements/{D,E,F,G,H,I,L}-KME-L-2026-10-05.md` (never edited).
The sequence was driven by `python3 -I tools/test_kme_challenger.py --real`; its per-step record is
`/home/kobii/ao-scratch/p2/real-20261006T231614Z/real-run.json`. Wall times are single warm-ish runs, residency not measured (no cold claim).
No transcript text appears in this file: only counts, paths, digests and verdicts.

## Certification (AO-07 shadow + certify)

command: `python3 -I wiki/tools/kme_pillars.py certify --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --index-db /home/kobii/ao-scratch/p1/cold.sqlite --cert /home/kobii/ao-scratch/p2/real-20261006T231614Z/kmel.cert.json`
-> exit 0, wall 23.503 s (one champion scoped scan of the same scope: the shadow).

```
KMEP-CERT verdict=CERTIFIED selected=102 uncovered=16 cert=/home/kobii/ao-scratch/p2/real-20261006T231614Z/kmel.cert.json
```

- selected sessions: 102 (selected-set digest `2821247d3d0e`)
- shadow: agree=true, champion_selected=102, index_selected=102
- uncovered (in-scope files the index does not hold: `_preserved` / `_empty_shells`, vouched by exact size + mtime_ns): 16
- index population: EXACT (the certify guard chain refuses anything else)
- key digests (12-char prefixes): parser `98e1d20be43d`; population metric `245431451e75`;
  D `75832a1525df` E `4848cdf4490b` F `0830e1bff542` G `f49e7f94e675` H `66b415a59f13` I `7ad7a3091169` L `677f6c3c6b37`;
  pattern_set `ea55662c2460`; attr_registry `68eac513ab01` (attr_version 1, schema_version 5)

## Equivalence

Challenger runs (challenger plan, certificate above, path log `/home/kobii/ao-scratch/p2/real-20261006T231614Z/path.jsonl`, out-dir `/home/kobii/ao-scratch/p2/real-20261006T231614Z/challenger`):

command (all): `python3 -I wiki/tools/kme_pillars.py all --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan challenger --index-db /home/kobii/ao-scratch/p1/cold.sqlite --cert /home/kobii/ao-scratch/p2/real-20261006T231614Z/kmel.cert.json --path-log /home/kobii/ao-scratch/p2/real-20261006T231614Z/path.jsonl --out-dir /home/kobii/ao-scratch/p2/real-20261006T231614Z/challenger`
-> exit 0, wall 16.15 s; stderr `KMEP-PATH plan=challenger taken=index deopt=none read_files=369`

command (rank): `python3 -I wiki/tools/kme_replay.py rank --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan challenger --index-db /home/kobii/ao-scratch/p1/cold.sqlite --cert /home/kobii/ao-scratch/p2/real-20261006T231614Z/kmel.cert.json --path-log /home/kobii/ao-scratch/p2/real-20261006T231614Z/path.jsonl --out-dir /home/kobii/ao-scratch/p2/real-20261006T231614Z/challenger`
-> exit 0, wall 13.398 s; stderr `KMEP-PATH plan=challenger taken=index deopt=none read_files=369`

command (compare): `python3 -I tools/kme_equivalence.py compare --candidate /home/kobii/ao-scratch/p2/real-20261006T231614Z/challenger --committed /home/kobii/missions/autonomous-optimization/.claude/worktrees/ao-gen2/vault/programs/incremental-cognition/measurements`
-> exit 0, wall 0.03 s. Verbatim:

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

Reading the lines: `committed=` and `candidate=` are the 12-char prefixes of the masked sha256 (masked fields: front
matter and JSON `measured_at` and `command`, and the H `commit`); they are equal on all seven files. Each file has
`corpus.sessions_scanned` 568 on both sides (`sessions_scanned=568/568`). The H line carries `verdict_map=SAME`: the
consumed owner-verdict map of the candidate equals the committed one, and it is not empty:
`{'P': 'FALSIFIED_OR_REJECTED_BY_EVIDENCE', 'G': 'FALSIFIED_OR_REJECTED_BY_EVIDENCE'}` (read from both files by the gate
V-KMEC-H-VERDICTS, which printed `verdict_map equal=True`).

Candidate file names carry the run date (`*-KME-L-2026-10-06.md`); the comparator pairs by pillar letter and
denominator and the committed names carry 2026-10-05 (`--date` default). The population lines printed by the
instrument itself were `population=exact cutoff=exact_at_freeze` for D to I and `population=exact` for L.

## Comparator negative control

The comparator is shown able to say DIFFERENT on the same committed files.

command: `python3 -I tools/kme_equivalence.py selftest-perturb --committed /home/kobii/missions/autonomous-optimization/.claude/worktrees/ao-gen2/vault/programs/incremental-cognition/measurements`
-> exit 0. Verbatim:

```
KMEQ_SELFTEST pillar=D self=SAME volatile=SAME perturb=DIFFERENT
KMEQ_SELFTEST pillar=E self=SAME volatile=SAME perturb=DIFFERENT
KMEQ_SELFTEST pillar=F self=SAME volatile=SAME perturb=DIFFERENT
KMEQ_SELFTEST pillar=G self=SAME volatile=SAME perturb=DIFFERENT
KMEQ_SELFTEST pillar=H self=SAME volatile=SAME perturb=DIFFERENT h_verdict=DIFFERENT
KMEQ_SELFTEST pillar=I self=SAME volatile=SAME perturb=DIFFERENT
KMEQ_SELFTEST pillar=L self=SAME volatile=SAME perturb=DIFFERENT
KMEQ_SELFTEST=PASS
```

(self copy SAME, volatile-only change SAME, one population digit changed DIFFERENT, and for H one owner-verdict terminal
changed DIFFERENT, on each of the seven committed files.)

## Path log

command: the same two challenger commands as above, with `--path-log /home/kobii/ao-scratch/p2/real-20261006T231614Z/path.jsonl`; the file holds exactly two
records. The planned read set is the 102 index-selected sessions plus 5 sessions the index
holds no first timestamp for, which the challenger reads raw by design (02-03, guard `no_first_ts`, review IN-04):
107 sessions / 369 files / 1,648,220,948 bytes
(plan figure before the run: about 364 files / 1,648,219,354 bytes; the difference of 5 files and 1,594 bytes is those
5 sessions). Both records: `plan_taken: index`, `deopt: null`, `read_set.stale: []`. The records are written through
the redactor and hold paths, ids, digests and counts, no transcript text.

Record 1 (`kme_pillars.py all`):

```
{"cross_project": false, "denominator": "KME-L", "deopt": null, "guards": [{"guard": "index_open", "ok": true, "reason": "schema 5"}, {"guard": "kind", "ok": true, "reason": "KME-L/kme"}, {"guard": "certificate", "ok": true, "reason": "question equal"}, {"guard": "pattern", "ok": true, "reason": "ea55662c2460"}, {"guard": "attribution", "ok": true, "reason": "version 1"}, {"guard": "parser", "ok": true, "reason": "98e1d20be43d"}, {"guard": "metric", "ok": true, "reason": "population 245431451e75; pillars changed: []"}, {"guard": "population", "ok": true, "reason": "EXACT"}, {"guard": "watermark", "ok": true, "reason": "0 stale session(s)"}, {"guard": "no_first_ts", "ok": true, "reason": "5 session(s) without a first timestamp read raw (review IN-04): C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/126de64c-d528-4d6b-b77f-a77d74d0753f, C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/161dfd64-7543-4a36-a241-6435d53d0873, C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/8de07739-aba3-42d1-92c4-1d75416f35e2, +2 more"}], "index_db": "/home/kobii/ao-scratch/p1/cold.sqlite", "keys": {"metric": {"D": "75832a1525dfb805f3ef3d168e58cc2be681ac5a172f62bbc20f450482ed8da7", "E": "4848cdf4490be165704538c3c2ae7987dd2f8a70846cc51f1498f37c1dd2ba96", "F": "0830e1bff542930dd05774320016ae6b93ca325ac749c565eabe02e6e0e9d48a", "G": "f49e7f94e675587d97b7453d4ab69e4d9c6bbc72615f6fa97fdf7efd659dd4eb", "H": "66b415a59f13fbcc480b436305278daa0f2cc30eae7c3b9520c83e593e175e9c", "I": "7ad7a3091169af6246791f30945f5b00bd184c2174f6916914264dbdb7b659ed", "L": "677f6c3c6b37f1dcb6d742d34cc70e1e2c6a4075a5fe97127e82af5841037bb1", "population": "245431451e75a6c3582031b66820f511dc00f99a9fc5ce20fefa7d133175cda9"}, "parser": "98e1d20be43d06105cbb43d36bcb797905c77e44b3f325f096e17806476cc115"}, "metric_changed": [], "plan_requested": "challenger", "plan_taken": "index", "plane": "gex44", "project_filter": "KobiiCraft-Core-Files|kme-wt-arena2", "read_set": {"basis": "planned", "bytes": 1648220948, "files": 369, "no_first_ts": ["C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/126de64c-d528-4d6b-b77f-a77d74d0753f", "C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/161dfd64-7543-4a36-a241-6435d53d0873", "C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/8de07739-aba3-42d1-92c4-1d75416f35e2", "C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/e67512c1-b768-4b3b-a31d-8bc2781d6c2b", "C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/e9cea8f0-9d23-4910-9410-b99595454ad9"], "sessions": 107, "stale": []}, "schema": 2, "sessions_registered": 568, "subcommand": "all", "tool": "kme_pillars", "until": "2026-10-03T16:13:37Z"}
```

Record 2 (`kme_replay.py rank`):

```
{"cross_project": false, "denominator": "KME-L", "deopt": null, "guards": [{"guard": "index_open", "ok": true, "reason": "schema 5"}, {"guard": "kind", "ok": true, "reason": "KME-L/kme"}, {"guard": "certificate", "ok": true, "reason": "question equal"}, {"guard": "pattern", "ok": true, "reason": "ea55662c2460"}, {"guard": "attribution", "ok": true, "reason": "version 1"}, {"guard": "parser", "ok": true, "reason": "98e1d20be43d"}, {"guard": "metric", "ok": true, "reason": "population 245431451e75; pillars changed: []"}, {"guard": "population", "ok": true, "reason": "EXACT"}, {"guard": "watermark", "ok": true, "reason": "0 stale session(s)"}, {"guard": "no_first_ts", "ok": true, "reason": "5 session(s) without a first timestamp read raw (review IN-04): C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/126de64c-d528-4d6b-b77f-a77d74d0753f, C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/161dfd64-7543-4a36-a241-6435d53d0873, C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/8de07739-aba3-42d1-92c4-1d75416f35e2, +2 more"}], "index_db": "/home/kobii/ao-scratch/p1/cold.sqlite", "keys": {"metric": {"D": "75832a1525dfb805f3ef3d168e58cc2be681ac5a172f62bbc20f450482ed8da7", "E": "4848cdf4490be165704538c3c2ae7987dd2f8a70846cc51f1498f37c1dd2ba96", "F": "0830e1bff542930dd05774320016ae6b93ca325ac749c565eabe02e6e0e9d48a", "G": "f49e7f94e675587d97b7453d4ab69e4d9c6bbc72615f6fa97fdf7efd659dd4eb", "H": "66b415a59f13fbcc480b436305278daa0f2cc30eae7c3b9520c83e593e175e9c", "I": "7ad7a3091169af6246791f30945f5b00bd184c2174f6916914264dbdb7b659ed", "L": "677f6c3c6b37f1dcb6d742d34cc70e1e2c6a4075a5fe97127e82af5841037bb1", "population": "245431451e75a6c3582031b66820f511dc00f99a9fc5ce20fefa7d133175cda9"}, "parser": "98e1d20be43d06105cbb43d36bcb797905c77e44b3f325f096e17806476cc115"}, "metric_changed": [], "plan_requested": "challenger", "plan_taken": "index", "plane": "gex44", "project_filter": "KobiiCraft-Core-Files|kme-wt-arena2", "read_set": {"basis": "planned", "bytes": 1648220948, "files": 369, "no_first_ts": ["C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/126de64c-d528-4d6b-b77f-a77d74d0753f", "C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/161dfd64-7543-4a36-a241-6435d53d0873", "C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/8de07739-aba3-42d1-92c4-1d75416f35e2", "C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/e67512c1-b768-4b3b-a31d-8bc2781d6c2b", "C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files/e9cea8f0-9d23-4910-9410-b99595454ad9"], "sessions": 107, "stale": []}, "schema": 2, "sessions_registered": 568, "subcommand": "rank", "tool": "kme_replay", "until": "2026-10-03T16:13:37Z"}
```

## Read-only proof

The manifest is the sha256 of the sorted `size mtime_ns relpath` lines of an `os.lstat` pass over every file under the
corpus root (no file opened); the index identity is the sha256 of the DB file bytes plus `os.stat` mtime_ns. Both were
taken by `tools/test_kme_challenger.py --real` before the first command and after the last one (functions
`corpus_manifest` and `file_identity`).

| What | Before | After | Equal |
|---|---|---|---|
| corpus manifest sha256 | `29969e7d6ab1bb271373c5004f34b2390918234e344c09c8994dc986b0a69ce0` | `29969e7d6ab1bb271373c5004f34b2390918234e344c09c8994dc986b0a69ce0` | true |
| corpus files / bytes | 10,577 / 10,205,326,251 | 10,577 / 10,205,326,251 | true |
| index sha256 | `6ddd159a914d65dd7a786bf4c5366a79730b397e8d0f197259e60aef89a0dd07` | `6ddd159a914d65dd7a786bf4c5366a79730b397e8d0f197259e60aef89a0dd07` | true |
| index mtime_ns | 1791321612414996448 | 1791321612414996448 | true |
| index size / sidecars (-wal -shm -journal) | 489,816,064 / none | 489,816,064 / none | true |

`git status --porcelain vault/programs/incremental-cognition/measurements/` is empty after the run (checked at commit time).

## Gate

command: `timeout 600 python3 -I tools/test_kme_challenger.py --real`

```
PASS V-KMEC-REAL-CERTIFIED rc=0 KMEP-CERT verdict=CERTIFIED selected=102 uncovered=16 cert=/home/kobii/ao-scratch/p2/real-20261006T231614Z/kmel.cert.json selected=102 shadow={'agree': True, 'champion_selected': 102, 'index_selected': 102} wall_s=23.503 err=''
PASS V-KMEC-EQUIV-REAL rc=0 KMEQ pillar=D verdict=SAME | KMEQ pillar=E verdict=SAME | KMEQ pillar=F verdict=SAME | KMEQ pillar=G verdict=SAME | KMEQ pillar=H verdict=SAME | KMEQ pillar=I verdict=SAME | KMEQ pillar=L verdict=SAME | KMEQ_VERDICT=SAME same=7/7
PASS V-KMEC-SESSIONS-SCANNED-568 sessions_scanned={'D': 568, 'E': 568, 'F': 568, 'G': 568, 'H': 568, 'I': 568, 'L': 568}
PASS V-KMEC-H-VERDICTS KMEQ pillar=H verdict=SAME verdict_map equal=True map={'P': 'FALSIFIED_OR_REJECTED_BY_EVIDENCE', 'G': 'FALSIFIED_OR_REJECTED_BY_EVIDENCE'}
PASS V-KMEC-EQUIV-PERTURB-REAL rc=0 ['KMEQ_SELFTEST=PASS']
PASS V-KMEC-REAL-INDEX-PATH kme_pillars.all plan_taken=index deopt=None stale=[] sessions=107 (selected 102 + no_first_ts 5) files=369 bytes=1648220948; kme_replay.rank plan_taken=index deopt=None stale=[] sessions=107 (selected 102 + no_first_ts 5) files=369 bytes=1648220948
PASS V-KMEC-REAL-READONLY manifest before=29969e7d6ab1 after=29969e7d6ab1 files=10577; index sha before=6ddd159a914d after=6ddd159a914d mtime_ns equal=True
KMEC_REAL_PASS=7/7  threshold=7/7  skipped=0  inconclusive=0
```

Summary line: `KMEC_REAL_PASS=7/7  threshold=7/7  skipped=0  inconclusive=0`
