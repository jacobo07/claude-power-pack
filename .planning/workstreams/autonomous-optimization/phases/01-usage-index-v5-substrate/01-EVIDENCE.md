# Phase 1 Evidence: usage_index v5 substrate

Phase commits (`git log --format='%h %s' 85fd564d..HEAD`): plan 01 `3d030e5e`, `5bc3c520`, `78407014`, `e96f1485` (summary `30a6433a`); plan 02 `ef8ecee0`, `446ee000`, `3f420085` (summary `34863cb1`); plan 03 `20f04c9b`, `40badfd9` (summary `8ed112a4`); plan 04 `2cf6e550`, `dd69209e` (summary `15bd2b80`); plan 05 `77e91179`, `e3f85e92` (summary `f4c1c603`). Phase-start commit `85fd564d`. Branch `mission/autonomous-optimization-gen2`. Plane: gex44. Spec of record: `vault/specs/autonomous-optimization.md` (AC-7). Every output below is from a fresh foreground process run at HEAD `f4c1c603` (before this evidence commit), except where a row names another commit.

## Criterion results

ROADMAP Phase 1 criteria and the clauses (1)-(5) of the frozen pillar O rule (`vault/programs/incremental-cognition/gen2/ledger.json` `frozen.pillars[O].rule`). Gate names are the `V-UX5-*` groups of `tools/test_usage_index_v5.py`; mutants are the `M*` entries of its `--drill` (source: the `KILLED` lines of `python3 tools/test_usage_index_v5.py --drill`).

| clause | artifact | proof command | observed line |
|---|---|---|---|
| ROADMAP 1 / rule (1): schema v5 with tool events (tool, input hash, path, result bytes), cwd, project/workstream attribution (mixed allowed), realpath + content identity | `tools/usage_index.py`, `tools/tis_observed.py` | `python3 tools/test_usage_index_v5.py` | `PASS V-UX5-SCHEMA: status=OK missing tables=[] missing files columns=[] schema_version=5`; `PASS V-UX5-TOOL-EVENT: rows=1 row=('Read', 'abb6d6e623ba2dbc', 49, 'C:/Users/User/Apps/proj/x.py', 3, 3, 0, 646)`; `PASS V-UX5-CWD`; `PASS V-UX5-IDENTITY-COLUMNS: ... rows differing from the path-derived identity (...)=[]`; `PASS V-UX5-OCCURRENCE`; mutant M3 (occurrence upsert removed) killed by V-UX5-OCCURRENCE |
| ROADMAP 1 / rule (2): migration re-reads zero already-ingested files, measured | `_migrate_v5` | `python3 tools/test_usage_index_v5.py` | `PASS V-UX5-MIGRATE-ZERO-REREAD: opens under the fixture root=0 status=OK files_opened=0 bytes_read=0 upserted=0 ... schema_version=5`; mutants M1 (`_migrate_spawns` gated on SCHEMA_VERSION) and M2 (`_migrate_v5` resets file sizes) both killed by it; `V-UX5-SPY-FIRES-ON-GROWTH` and `-V1` show the open() spy can fire |
| ROADMAP 2 / rule (3) control 1: mixed-project session attributed to both | `_attribute` | same | `PASS V-UX5-MIXED-BOTH: launched in alpha, reads under alpha and under registered beta: projects={'C--Users-User-Apps-alpha': {'home': 2}, 'C--Users-User-Apps-beta': {'touched': 1}} mixed=True` (control `V-UX5-MIXED-CONTROL`); mutant M13 killed by V-UX5-MIXED-BOTH |
| control 2: two distinct histories not merged | `content_id`, `dup_of` | same | `PASS V-UX5-HISTORIES-NOT-MERGED: two histories, one sessionId, shared prefix: files rows=2, content_ids distinct=True, dup_of=[None, None] ...`; mutant M8 (content id from head hash only) killed by it |
| control 3: junction alias counted once | `tis_observed.store_identity` | same | `PASS V-UX5-ALIAS-ONCE: alias listed before its target: files rows=2 (want 2), call_files rows/distinct keys=(2, 2) (want 2/2) ...` (+ `V-UX5-ALIAS-DISTINCT`, `V-UX5-ALIAS-OUTSIDE`); mutant M5 (store identity bypassed) killed by V-UX5-ALIAS-ONCE |
| control 4: `_archived` handled by a declared rule | `ARCHIVED_RULE` (meta `archived_rule`) | same | `PASS V-UX5-ARCHIVED-INDEXED`, `PASS V-UX5-V4-READERS-UNCHANGED`, `PASS V-UX5-ARCHIVED-RULE: default: live session only ... archived_excluded={'sessions': 1, 'files': 1, 'calls': 2, 'cache_read': 81} ...`; mutants M6 (archived written to calls) and M15 (exclusion removed from population) killed |
| control 5: parser failure surfaced, never a silent zero | `files.parse_errors` | same | `PASS V-UX5-PARSE-ERROR-SURFACED: two undecodable complete lines: files.parse_errors=2, refresh result parse_errors=2, meta last_refresh_status parse_errors=2; valid calls still ingested=2/2`; mutant M7 (counter removed) killed by it; `V-UX5-FILE-ERROR-TYPED` for an unreadable file |
| control 6: empty population refuses a verdict | `population()` | same | `PASS V-UX5-EMPTY-REFUSES: v4-shaped empty index: verdict=UNMEASURED ... cli exit=3 cli verdict=UNMEASURED; migrated empty scope: verdict=UNMEASURED reasons=['no file in scope']` (control `V-UX5-EMPTY-CONTROL`); mutant M4 (MEASURED on an empty scope) killed by it |
| ROADMAP 3 / rule (4): KME-L parity 102 / 34,871 / 11,549,646,300 on the GEX44 copy, dedup reconciled to the unit, plane gex44 | `gen2/evidence/O-parity-gex44.md` | `python3 tools/usage_index.py population --db /home/kobii/ao-scratch/p1/cold.sqlite --project-filter 'KobiiCraft-Core-Files\|kme-wt-arena2' --until 2026-10-03T16:13:37Z --select kme --host gex44 --expect KME-L --plane gex44` | exit 0, verdict EXACT, deltas empty; table under "Corpus measurements" |
| ROADMAP 4 / rule (5): refresh cost (wall, bytes) for a cold build and for a delta | `gen2/evidence/O-cost-gex44.md` | `python3 tools/usage_index.py refresh --all --db /home/kobii/ao-scratch/p1/cold.sqlite --proj /home/kobii/kme-corpus/projects --deadline 540` and the delta run | cold 128.069 s / 9,932,073,959 B read; delta 0.07 s / 709,630 B (table under "Corpus measurements") |

## Verifier output (fresh processes, after f4c1c603)

`python3 tools/test_usage_index_v5.py` (exit 0)
```
USAGE_INDEX_V5_PASS=71/71  threshold=71/71
```

`python3 tools/test_usage_index_v5.py --drill` (exit 0; M1-M18 each printed a `KILLED` line)
```
PASS DRILL-CLEAN-AFTER-MUTANTS unmutated rerun: 71/71 gates green
DRILL killed=18/18
```

`python3 tools/test_usage_index.py` (exit 0)
```
USAGE_INDEX_PASS=22/22  threshold=22/22
```

`python3 tools/test_usage_index_identity.py` (exit 0)
```
USAGE_INDEX_IDENTITY_PASS=11/11  threshold=11/11
```

`python3 tools/test_spawn_outcomes.py` (exit 0)
```
SPAWN_OUTCOMES_PASS=24/24  threshold=24/24
```

`python3 tools/test_kme_pillars.py` (exit 0)
```
KMEP_PASS=89/89  threshold=89/89  skipped=0  inconclusive=0
```

`python3 tools/test_incremental_cognition_program.py --generation 2 --status` (exit 0; before the ledger row of this phase is written, see Limits)
```
{"open": ["M", "O", "P", "Q", "R"], "closed": [], "violations": []}
```

`python3 tools/test_incremental_cognition_program.py --generation 2 --selftest` (exit 0)
```
ICP_GEN2_SELFTEST=PASS
```

`python3 tools/test_incremental_cognition_program.py --generation 2 --audit` (exit 0)
```
A7 ok recorded frozen_sha256 equals the live one
ICP_GEN2_AUDIT=PASS frozen_sha256=a8ac15d894a72c74eb71901b3081c7a6a20a0ee2d9da085a270dd015a204d39e
```

`python3 modules/liveness/reachability.py` (exit 1, inherited, reported as red)
```
modules: 490  |  REACHABLE: 310  |  ORPHAN: 180  |  UNKNOWN: 0  |  gate offenders: 59
| tower/ratchet | ORPHAN | - |
```
Its aperture is `modules/` only; `tools/usage_index.py` is outside its denominator, so this exit is not evidence about pillar O (neither `usage_index` nor `tis_observed` is named in its output).

Inherited reds, unchanged and not claimed green (01-BASELINE.md "after the change" table, run at `77e91179`): `tools/test_estate_shadow.py` `ESTATE_SHADOW_PASS=10/11` (`V-SHADOW-NESTED-PROJECT`); `tools/test_frontier_intelligence_os.py` `DATASET_FAMILY_VERDICT=FAIL` (`V-FIOS-LIVE-PATH-WIRED`); `tools/test_token_ground_truth_junction.py` crash `FileNotFoundError: [Errno 2] No such file or directory: 'cmd'`.

## Corpus measurements (plane: gex44)

Source files: `vault/programs/incremental-cognition/gen2/evidence/O-parity-gex44.md` (measured on `/home/kobii/kme-corpus/projects`, read-only: manifest of 10,577 files / 10,205,326,251 bytes hashes `6eab1abced4f04cf4b601c22cf3695e7d7ae3fd31898698fdc2b7625fd10e6a9` before and after, `cmp` identical), `O-cost-gex44.md`, `O-prg.md` (same directory).

### Parity

command: `python3 tools/usage_index.py population --db /home/kobii/ao-scratch/p1/cold.sqlite --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --until 2026-10-03T16:13:37Z --select kme --host gex44 --expect KME-L --plane gex44` -> exit 0, verdict EXACT.

| field | observed | frozen KME-L |
|---|---|---|
| sessions_active / dead | 102 / 0 | 102 / 0 |
| calls | 34,871 | 34,871 |
| cache_read | 11,549,646,300 | 11,549,646,300 |
| input / cache_write / output (secondary) | 69,846 / 209,909,403 / 37,878,881 | same |

### Reconcile to the unit (from the `reconcile` block of the same command)

| item | calls | cache_read |
|---|---|---|
| occurrence view (the parity unit) | 34,871 | 11,549,646,300 |
| unique API requests | 34,853 | 11,544,130,372 |
| first_writer (the v4 figure) | 34,853 | 11,544,130,372 |
| 18 keys shared between two selected sessions (867896c0 KME_STRONG, 18 calls; 9184ed39, 403 calls) | 18 | 5,515,928 |
| shared_outside (keys also present outside the selection) | 0 | 0 |
| dup files in scope | 0 | 0 |
| `_archived` excluded (1 session, 1 file) | 649 | 271,001,260 |
| skipped shapes | 50 files (`_preserved` 14, `_empty_shells` 36), 2,897,590 B | not ingested |

Unfiltered, the same index reproduces champion Run 5 (105 / 35,776 / 11,888,777,786): v5 default 103 / 34,999 / 11,583,711,413 plus `_archived` 1 / 649 / 271,001,260 plus the PP session the champion counts a second time through the directory symlink `C--Users-User-Apps-mcp-video-analyzer -> C--Users-User--claude-skills-claude-power-pack` (1 / 128 / 34,065,113) equals Run 5 exactly. The index walk does not follow directory symlinks (3 at the corpus root).

### Cost (O-cost-gex44.md; every command is in that file)

| run | files_read | bytes_read | wall_s | rchar_delta | maxrss_kb | DB bytes |
|---|---|---|---|---|---|---|
| v4 baseline (cited from 01-RESEARCH.md, not re-run), 6 dirs | 979 | 3,053,908,888 | 15.7 | n/a | 76 MB | 34.7 MB |
| v5 cold, whole corpus (cache evicted best-effort, residency not measured) | 3,965 | 9,932,073,959 | 128.069 | 158,621,987,249 | 89,760 | 489,816,064 |
| v5 warm cold, whole corpus | 3,965 | 9,932,073,959 | 118.661 | 158,621,987,249 | 89,672 | 489,816,064 |
| v5 no-op | 0 | 0 | 0.577 | 958,972,508 | 33,352 | 489,816,064 |
| v5 cold, 6-dir copy | 979 | 3,053,908,888 | 25.182 | 18,456,362,331 | 86,608 | 143,429,632 |
| v5 delta (5 appended files, +709,630 B) | 5 | 709,630 | 0.07 | 136,372,842 | 30,560 | 143,486,976 |

command (cold): `python3 tools/usage_index.py refresh --all --db /home/kobii/ao-scratch/p1/cold.sqlite --proj /home/kobii/kme-corpus/projects --deadline 540`. Delta equality: files_opened 5 = 5 appended files; bytes_ingested 709,630 = appended total (difference 0). On the v4 scope, v4 5.14 ns/B against v5 8.25 ns/B = 1.60x per byte; DB 4.1x larger.

### Production Reality (O-prg.md)

The real CLI on the real substrate: green exit 0 EXACT; `--perturb calls=34872` exit 1 DRIFTED (delta -34872); `--project-filter '^no-such-project$'` exit 3 UNMEASURED ("no file in scope", population null). Command lines are in `O-prg.md` (`command:` lines 21, 128, 243).

## Edge probe: interrupted or parallel refresh

Guarantee (plan 02): a refresh that is killed, fails mid-file, or runs concurrently with another converges to the rows of one clean build; no row of the file in flight survives a FAILED pass; a pass that started from a stale snapshot skips the file instead of double-ingesting it. Gates: `PASS V-UX5-CRASH-RESUME: crash injected after line 3 of the second file: status=FAILED; rows of that file left behind={'files': 0, 'calls': 0, 'call_files': 0, 'tool_events': 0, 'quota': 0, 'prompts': 0} (want all 0); the first file committed=True; ...`, `PASS V-UX5-STALE-SNAPSHOT-SKIPS: B started from a snapshot taken before A advanced both files: B skipped_concurrent=2 files_read=0 ...`, `PASS V-UX5-FRESH-SNAPSHOT-INGESTS` (control: an up-to-date snapshot ingests). Mutant M9 (per-file snapshot check always admits) is killed by V-UX5-STALE-SNAPSHOT-SKIPS. The CRASH-RESUME gate was found red first (the final meta commit of a FAILED pass committed the partial rows of the file in flight); fixed by `con.rollback()` plus the per-file `BEGIN IMMEDIATE` (commit `3f420085`).

## v4 reader compatibility

- Archived rule: `_archived` transcripts go to the v5 tables only (`ARCHIVED_RULE`, meta `archived_rule`); v4 readers keep their numbers (`PASS V-UX5-V4-READERS-UNCHANGED`, with a control that sees a difference; mutant M6 killed).
- Consumer set before and after (01-BASELINE.md: untouched tree vs "after the change" at `77e91179`, 20 rows, none worse): usage_index 22/22 same; identity crash -> 11/11 better; store-identity-consumers crash -> 12/12 better; fanout 17/17, root_progress 11/11, spawn_outcomes 24/24, spawn_policy_v2 26/26, async 12/12, goal_journey 7/7, execution_shape 14/14, displacement 16/16, kme_pillars 89/89, gsd_x identity 14/14 all same; estate_shadow 10/11, frontier_intelligence_os and token_ground_truth_junction red/crash as on the untouched tree.
- `vault/programs/cognitive-economy/gates/gate_baseline.py`: **UNMEASURED on this plane**. It reads the default index `~/.claude/state/usage_index/index.sqlite`, which does not exist on GEX44. Owner-bundle line `[O] (IC-gen2)` (b) carries it to the laptop.

## Ownership (EXTEND_EXISTING_OWNER)

Extended, by path: `tools/usage_index.py` (schema v5, `population`, `backfill_v5`, attribution), `tools/tis_observed.py` (`resolved_path`, `calls_from` stats and `end_offset`), `tools/test_usage_index_identity.py` and `tools/test_store_identity_consumers.py` (Linux symlink fallback for `junction()`), `tools/test_spawn_outcomes.py`. The only new code file of the phase is the pillar's own gate.

command: `git diff --name-only --diff-filter=A 85fd564d HEAD -- modules tools`
```
tools/test_usage_index_v5.py
```
No new module, database, runtime or ratchet. The champion classifier and pattern registry are loaded from `wiki/tools/kme_token_audit.py` (never copied; `git status --porcelain -- wiki/tools` printed nothing at plan 04).

## Product Delta

- A user or a later phase can ask which sessions belong to KME-L at an instant, and at what cost, from the index alone: `python3 tools/usage_index.py population --select kme --host gex44 --until <ISO> --expect KME-L` answers EXACT (exit 0) on the GEX44 corpus copy with the reconcile block, DRIFTED (exit 1) with per-field deltas, or UNMEASURED (exit 3) with named reasons.
- Every tool event is queryable with tool, input hash, normalized path and result size (`tool_events`), and no raw text is stored in the new tables (`PASS V-UX5-NO-RAW-TEXT` with its control).
- A session is attributed to several projects and workstreams at once (`file_attribution`, kind project / workstream / bucket, role home / touched), from a registry discovered from launch cwds, independent of ingest order.
- `_archived` history is ingested by a declared rule without changing any v4 number.
- Refresh cost is measured per call: `refresh` returns `wall_s`, `bytes_read`, `files_opened`, and the CLI adds `proc {rchar_delta, maxrss_kb}`; `refresh --all` cold-builds history, `backfill-v5` is the opt-in bounded path for a migrated index (reads only the bytes below each legacy file's committed offset; second run reads 0).
- The v4 -> v5 migration re-reads zero files (`files_opened=0 bytes_read=0`).

## Intelligence Delta

- A schema version bump can silently re-queue the spawn backfill: `_migrate_spawns` was gated on `SCHEMA_VERSION`, so bumping to 5 would have re-read every history file. It now has its own `SPAWN_SCHEMA` gate (plan 01; mutant M1 is the proof, killed by V-UX5-MIGRATE-ZERO-REREAD).
- v4 gave a silent zero for `_archived`: archived transcripts were walked past or merged without a rule. v5 declares the rule and counts what it excludes (`archived_excluded` 1 / 649 / 271,001,260 on the KME-L scope) (plan 02, 04-05).
- The 18-key / 5,515,928 cache_read gap between the occurrence view and the unique view is first-writer order dependence: v4 charged a shared API request to whichever session wrote it first; the occurrence view (every transcript copy counts) is the parity unit and does not depend on ingest order (`PASS V-UX5-RECONCILE-SHARED`, both orders: occurrence totals identical, first_writer differs 2 vs 3; mutant M17 killed). Source: 01-04 SUMMARY, 01-05 SUMMARY.
- Corrected assumption: 01-RESEARCH predicted session 867896c0 sits outside the KME selection. Measured: 867896c0 is KME_STRONG and **selected**, so the 18 shared keys are shared between two selected sessions (867896c0 and 9184ed39) and `shared_outside` is 0. Source: `O-parity-gex44.md`, 01-05 SUMMARY.
- Cost finding for the Owner (not fixed in this phase): SQLite page-cache misses make `rchar_delta` 5-16x the corpus bytes. strace attribution (O-cost-gex44.md): on the 6-dir cold build 15.40 GB of 18.46 GB are reads of the SQLite file itself (3.76 M reads, 108x the final DB size) and 3.05 GB corpus; the no-op reads 958,965,604 DB bytes and 0 corpus bytes. The corpus is read once; the amplification is the database. v5 is 1.60x slower per byte than v4 on the 6-dir scope with a 4.1x larger DB. Tuning is a separate change and an opportunity candidate, not a defect of parity.
- Two test suites carried a Windows-only identity helper (`junction()` shells out to `cmd /c mklink /J`); on Linux they crashed before any gate ran. A symlink fallback under `os.name != "nt"` made them runnable (plan 01; `test_token_ground_truth_junction.py` keeps the crash, out of scope).
- A FAILED refresh used to commit the partial rows of the file in flight through its final meta commit; found only because the crash gate was run red first (plan 02).
- The classifier must run on the champion's own functions: `population()` loads `classify`/`is_kme` and `KME_RE` from `wiki/tools/kme_token_audit.py` by path and checks pattern drift against the champion's current regex, not only the stored meta set (plan 03-04).
- UNMEASURED must be reachable and typed: a refused answer carries `population=None`, an empty selection refuses, and `expected` must carry every `VERDICT_FIELDS` integer so EXACT is never reached vacuously (plan 04).

## Limits and open items

- Owner-bundle lines (`vault/programs/incremental-cognition/gen2/owner-bundle.md`, pillar `[O] (IC-gen2)`): (a) after the Owner merges `mission/autonomous-optimization-gen2`, the laptop index migrates v4 -> v5 on its next refresh with zero re-read and `backfill-v5` brings history to MEASURED; (b) `python vault/programs/cognitive-economy/gates/gate_baseline.py` re-run on the laptop closes the UNMEASURED v4-reader row above.
- `gate_baseline.py` UNMEASURED on this plane (above).
- Tolerated parse errors: none needed in the KME-L scope (0 parse errors in scope, `parse_errors_tolerated` not used).
- Residual semantics, documented in 01-04 SUMMARY and not claimed closed by anything beyond the parity measurement: a streamed call whose copies straddle the freeze instant counts by its last copy's effective timestamp; `tool_events` is keyed (file, tool_use_id), so a tool_use id repeated inside one file counts once; relative tool paths before the first cwd line of a resumed pass land in `<unattributed>`; legacy files migrated from v4 stay UNMEASURED in population until `backfill-v5` runs.
- `rchar_delta` is process-level truth (DB page reads included), not a corpus byte count; cache residency during the cold build is not measured (fadvise DONTNEED best-effort).
- Inherited reds stay red and are reported verbatim above: estate_shadow 10/11, frontier_intelligence_os `V-FIOS-LIVE-PATH-WIRED`, token_ground_truth_junction crash, `modules/liveness/reachability.py` exit 1 (aperture `modules/` only).
- The programme `--generation 2 --final` is expected to stay FAIL on pillars M, P, Q, R (L3) and the four L8 lines; this phase realizes no dividend and `state.O` carries `savings: []`.
- Pillar O's terminal row is written by plan 01-06 Task 2 after this document is committed.
