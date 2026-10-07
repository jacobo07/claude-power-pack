# Phase 2 Evidence: KME-L challenger

Phase commits (`git log --format='%h %s' 23f5a7f1..HEAD`, phase-start commit `23f5a7f1`): plan 01 `596d8460`, `aa961615` (summary `3be6c5be`); plan 02 `f30b167a`, `af842d8d`, `61eb3ee8`, `b9c8b273` (summary `a3aed405`); plan 03 `016bf57d`, `e71fd60e`, `1ca72e86` (summary `a97c2f0d`); plan 04 `87fa25bb`, `1ed02255` (summary `b1023f3d`); plan 05 `e06dafa7`, `9fb64b83`, `cd4b63cc` (summary `40597853`); plan 06 `21f0111a` (criterion 5), `3cf7e121` (ledger row OPP-002). Branch `mission/autonomous-optimization-gen2`. Plane: gex44 (host `kobiicraft-gex44`). Spec of record: `vault/specs/autonomous-optimization.md`. Pillar: [P] (IC-gen2). Every command output below is from a fresh foreground process run at HEAD `3cf7e121` (before this evidence commit), except where a row names another source. Corpus `/home/kobii/kme-corpus/projects` and index `/home/kobii/ao-scratch/p1/cold.sqlite` are read-only inputs; hashes before and after every real run are equal (rows below).

Verdict in one line: criterion 5 is a WIN for increment 1 under the rule fixed at planning time, `P-JUDGEMENT verdict=WIN wall_warm_s=29.580848/56.975624 raw_bytes=3298099868/6120339068 wall_ratio=1.926 bytes_ratio=1.856`. The result is narrowed (see Limits): the challenger still reads its selected sessions raw and additionally reads 1.81 GB of index.

## Criterion results

ROADMAP Phase 2 criteria 1-5. Gate names are the `V-KMEC-*` gates of `tools/test_kme_challenger.py` (21 hermetic, 7 in `--real`, 2 in `--real-exposure`) and `tools/test_kme_measure_tools.py` (14); mutants are the `M*` entries of the two `--drill` runs.

| ROADMAP criterion | gates / evidence file | command | observed result |
|---|---|---|---|
| 1. Access plan certified index -> project-scoped raw -> global raw only on explicit cross-project; guard failure deopts with a logged reason; invalidation keyed on source watermark, parser version, attribution version, metric definition | `V-KMEC-PLAN-ORDER`, `V-KMEC-KS4-FORCED`, `V-KMEC-CROSS-PROJECT-EXPLICIT`, `V-KMEC-PATH-LOG`, `V-KMEC-DEOPT-LOGGED` (10 guards, each with a control), `V-KMEC-KEYS-FOUR`, `V-KMEC-CERT-GUARDS`, `V-KMEC-METRIC-COVERAGE` | `python3 -I tools/test_kme_challenger.py` | `KMEC_PASS=21/21  threshold=21/21  skipped=0  inconclusive=0`; `PASS V-KMEC-DEOPT-LOGGED guards 10/10 [index_open/missing:ok, index_open/schema4:ok, population/DRIFTED:ok, population/UNMEASURED:ok, certificate:ok, parser:ok, attribution:ok, metric:ok, watermark/root_not_indexed:ok, shadow:ok]`. Drill: `python3 -I tools/test_kme_challenger.py --drill` -> `DRILL killed=15/15`, `PASS DRILL-CLEAN-AFTER-MUTANTS unmutated rerun: 21/21 gates green` |
| 2. The 7 KME-L measurement files (D, E, F, G, H, I, L) reproduce identically from the challenger | `P-equivalence-gex44.md`; `V-KMEC-EQUIV-REAL`, `V-KMEC-SESSIONS-SCANNED-568`, `V-KMEC-H-VERDICTS`, `V-KMEC-EQUIV-PERTURB-REAL`, `V-KMEC-REAL-INDEX-PATH`, `V-KMEC-REAL-READONLY` | `timeout 600 python3 -I tools/test_kme_challenger.py --real` (54 s wall) | `KMEQ_VERDICT=SAME same=7/7`; `sessions_scanned={'D': 568, 'E': 568, 'F': 568, 'G': 568, 'H': 568, 'I': 568, 'L': 568}`; H `verdict_map equal=True map={'P': 'FALSIFIED_OR_REJECTED_BY_EVIDENCE', 'G': 'FALSIFIED_OR_REJECTED_BY_EVIDENCE'}`; `plan_taken=index deopt=None stale=[] sessions=107 (selected 102 + no_first_ts 5) files=369 bytes=1648220948`; `KMEC_REAL_PASS=7/7  threshold=7/7  skipped=0  inconclusive=0`. The comparator can fail: `V-KMEC-EQUIV-PERTURB-REAL ['KMEQ_SELFTEST=PASS']` (one digit changed per file -> DIFFERENT) |
| 3. Champion vs scoped vs challenger table: wall, raw bytes, unique bytes, raw files opened, cross-project bytes exposed; a KME-only query opens zero CostaLuz bytes with a negative control that can fail | `P-table-gex44.md` (`## Table`, `## Data`); `P-exposure-gex44.md`; `V-KMEC-COSTALUZ-ZERO-REAL`, `V-KMEC-EXPOSURE-READONLY` | `timeout 600 python3 -I tools/test_kme_challenger.py --real-exposure` (about 76 s); table commands in `P-table-gex44.md` `## Runs` | table below; `PASS V-KMEC-COSTALUZ-ZERO-REAL challenger {'forbidden_bytes': 0, 'forbidden_opens': 0, 'cross_project_bytes': 0, 'raw_bytes': 1649049934, 'raw_files_opened': 369, ...}; control forbidden_bytes=98986782 forbidden_opens=73 cross_project_bytes=98986782 (halves: challenger=True control_fires=True)`; `KMEC_EXPOSURE_PASS=2/2  threshold=2/2  skipped=0  inconclusive=0` |
| 4. Stale-cache control: changing a source or the parser version invalidates exactly the affected closure | `V-KMEC-STALE-SOURCE`, `V-KMEC-STALE-NEW-FILE`, `V-KMEC-STALE-PARSER`, `V-KMEC-STALE-METRIC`, `V-KMEC-ATTR-VERSION`, `V-KMEC-PATTERN-DRIFT`, `V-KMEC-IN04-NO-FIRST-TS`, `V-KMEC-ROOT-NOT-INDEXED`; post-delta canary in `P-table-gex44.md` | `python3 -I tools/test_kme_challenger.py`; canary commands in `P-table-gex44.md` `## Post-delta canary` | after appending to one file only that session is stale and opened (`stale=['-home-x-core-fixture/n1'] opened=[agent-a1, k1, n1] (n2 untouched, never opened)`, output equal to the champion on the modified tree); parser digest `98e1d20be43d -> 44ff46eeab8c` deopts; real-data canary on a scratch copy: five appended sessions read as exactly the stale set, `KMEQ_VERDICT=SAME same=7/7` against the scoped run and against the committed files, 110 sessions / 372 files read (102 selected + 5 no-first-timestamp + 3 newly stale) |
| 5. If the challenger does not beat the scoped path on repeated queries, narrow or reject it and record why | `P-criterion5-gex44.md`; ledger row OPP-002 | `python3 -I -c '...'` recorded in `P-criterion5-gex44.md` `## Verdict` (re-run: extract the line starting `command:` and execute it) | `P-JUDGEMENT verdict=WIN wall_warm_s=29.580848/56.975624 raw_bytes=3298099868/6120339068 wall_ratio=1.926 bytes_ratio=1.856`. The rule was written in plan 02-06 before any Phase 2 number existed and the verdict is computed from the committed `## Data` block, not narrated. The win is recorded narrowed (Narrowed claim, Not claimed, Limits); no facts sidecar was built (orchestrator decision 1) |

### The table (copied values; source `P-table-gex44.md` `## Table` and `## Data`, N=5 untraced repetitions for walls, two traced repetitions for bytes)

| configuration | wall median s | raw bytes | unique bytes | raw files | index bytes | cross-project / CostaLuz bytes |
|---|---|---|---|---|---|---|
| scoped all+rank, warm | 56.976 | 6,120,339,068 | 3,055,976,146 | 995 | 0 | 0 / 0 |
| scoped all+rank, evicted best-effort (residency not measured) | 58.523 | 6,120,339,068 | 3,055,976,146 | 995 | 0 | 0 / 0 |
| challenger all+rank, warm | 29.581 | 3,298,099,868 | 1,648,220,948 | 369 | 1,805,435,496 | 0 / 0 |
| challenger all+rank, evicted best-effort (residency not measured) | 37.529 | 3,298,099,868 | 1,648,220,948 | 369 | 1,805,435,496 | 0 / 0 |
| challenger post-delta (scratch copy, six-directory index) | 28.759 | 3,301,460,730 | 1,649,876,803 | 372 | 519,078,504 | 0 / 0 |
| champion Run 5 (unscoped, cited from the frozen ledger) | 869 (cited) | 109,088,283,520 (derived: 10 x one unscoped scan) | 9,934,971,549 (derived) | 4,015 (derived) | 0 | 78,486,588,180 / 998,161,080 (derived) |
| Run 6 population / seven separate runs (scoped, cited) | 24 / 177 (cited) | UNMEASURED | UNMEASURED | UNMEASURED | 0 | UNMEASURED |

Command of the deciding computation (also in `P-criterion5-gex44.md`; its source is the `## Data` block of `P-table-gex44.md`): ratios scoped / challenger are 1.926 on warm wall and 1.856 on raw bytes; raw + index bytes are 6,120,339,068 scoped against 5,103,535,364 challenger (ratio 1.199, a 16.6 % saving on total read volume). The challenger additionally reads 1.81 GB of index (5.10 GB total against 6.12 GB for the scoped path), which the rule does not count and the verdict file states in plain words. "Evicted" rows are best-effort `posix_fadvise(DONTNEED)` of the six scoped directories and the index, residency not measured; no cold-cache claim is made from them.

## AO-07 mapping

Shadow, canary, certify, deopt are the lifecycle states of ROADMAP Phase 2 as the access plan implements them. Ledger status of the row is `canary`.

- **Shadow = `certify` per-session agreement plus 7-file equivalence.** `kme_pillars.py certify` scans the same scope with the champion classifier (no select), requires the population to equal the frozen fields exactly and the selected `(project, session)` pairs of the index and of the champion to be identical (dead sessions included); unequal -> exit 1, nothing written. Real data: `PASS V-KMEC-REAL-CERTIFIED rc=0 KMEP-CERT verdict=CERTIFIED selected=102 uncovered=16 ... shadow={'agree': True, 'champion_selected': 102, 'index_selected': 102}`; the 7 files `SAME same=7/7` (`--real` above). The post-scan `_shadow_check` runs on every challenger and auto query too.
- **Canary = post-delta on a scratch copy.** `P-table-gex44.md` `## Post-delta canary`: a fresh `cp -a` of the six scoped directories (3,160,520,417 bytes) under `/home/kobii/ao-scratch/p2/delta-root/`, five post-freeze lines appended by a realpath-guarded script (refusal shown for the real corpus path), challenger vs scoped vs committed `SAME 7/7`, read set 110 sessions / 372 files, wall median 28.759 s. The real corpus manifest sha256 `29969e7d6ab1...` is equal before and after.
- **Certify = certificate keys.** The certificate is keyed on the selection-parser digest (`98e1d20be43d` on the fixture), the metric-definition digests per pillar (`D, E, F, G, H, I, L, population`), the attribution version (1), the pattern set and the population definition, plus the per-file watermark (size, mtime_ns, row offset) and the `uncovered` map (`V-KMEC-KEYS-FOUR`, `V-KMEC-CERT-GUARDS`, `V-KMEC-METRIC-COVERAGE` with a control that drops one name). `SELECTION_SOURCES` are `tools/usage_index.py`, `wiki/tools/kme_token_audit.py`, `wiki/tools/kme_report.py`.
- **Deopt = guard table with the drill.** Ten guards (index_open missing, index_open schema 4, population DRIFTED, population UNMEASURED, certificate, parser, attribution, metric, watermark / root_not_indexed, shadow), each deopting with a logged reason under `--plan auto` (to scoped raw, or global raw only with `--cross-project`) and refusing with exit 3 under `--plan challenger` (`V-KMEC-DEOPT-LOGGED`, control all-green `taken=index deopt=None`). `--plan champion` is the default and stays callable (`V-KMEC-KS4-FORCED`). `python3 -I tools/test_kme_challenger.py --drill` kills 15 of 15 mutants and the unmutated rerun is 21/21 green.

## AO-09 mapping

- **Measured:** every equivalence and byte claim above comes from a run with a recorded command (`P-equivalence-gex44.md`, `P-exposure-gex44.md`, `P-table-gex44.md`), judged by instruments that can fail (the comparator's perturb selftest; the strace summer's CostaLuz control with 98,986,782 forbidden bytes; the drills `killed=15/15` and `killed=9/9 backstops_held=2/2`).
- **Extension of the owners:** `wiki/tools/kme_pillars.py` (+750 lines), `wiki/tools/kme_replay.py` (7), `wiki/tools/kme_token_audit.py` (10) extended in place (HR-NOVELTY-001 record: EXTEND_EXISTING_OWNER); the only new code files are the two measuring instruments `tools/strace_io_sum.py`, `tools/kme_equivalence.py` and the gates. Their reachability and the liveness result are in the regression set.
- **Equal:** the 7 KME-L files reproduce from the challenger (`SAME same=7/7`), also after the post-delta append.
- **Zero CostaLuz bytes:** a KME-only challenger query has `forbidden_bytes 0, forbidden_opens 0, cross_project_bytes 0` on every measured row above; the control (filter widened with `|CostaLuz`) reads 98,986,782 CostaLuz bytes over 73 opens, so the check can fail. The unscoped champion control scan reads 99,816,108 CostaLuz bytes per scan (`P-exposure-gex44.md`, control 2). Instrument limit: detection is by path, not by content (a transcript that mentions the string in its text is not counted).
- **Corpus untouched:** corpus manifest sha256 `29969e7d6ab1bb271373c5004f34b2390918234e344c09c8994dc986b0a69ce0` (10,577 files, 10,205,326,251 bytes) and index sha256 `6ddd159a914d65dd7a786bf4c5366a79730b397e8d0f197259e60aef89a0dd07` equal before and after `--real` and `--real-exposure` of this plan (`V-KMEC-REAL-READONLY manifest before=29969e7d6ab1 after=29969e7d6ab1 files=10577; index sha before=6ddd159a914d after=6ddd159a914d mtime_ns equal=True`; `V-KMEC-EXPOSURE-READONLY` same values).

## Regression set

Fresh foreground processes at HEAD `3cf7e121`, summary lines verbatim. Every suite exited 0 except `modules/liveness/reachability.py`.

`python3 -I tools/test_kme_challenger.py` (exit 0, 11.2 s)
```
KMEC_PASS=21/21  threshold=21/21  skipped=0  inconclusive=0
```

`python3 -I tools/test_kme_challenger.py --drill` (exit 0, 32.8 s)
```
PASS DRILL-CLEAN-AFTER-MUTANTS unmutated rerun: 21/21 gates green
DRILL killed=15/15
```

`timeout 600 python3 -I tools/test_kme_challenger.py --real` (exit 0, 54 s)
```
KMEC_REAL_PASS=7/7  threshold=7/7  skipped=0  inconclusive=0
```

`timeout 600 python3 -I tools/test_kme_challenger.py --real-exposure` (exit 0)
```
KMEC_EXPOSURE_PASS=2/2  threshold=2/2  skipped=0  inconclusive=0
```

`python3 -I tools/test_kme_measure_tools.py` (exit 0, 0.4 s)
```
KMET_PASS=14/14  threshold=14/14  skipped=0  inconclusive=0
```

`python3 -I tools/test_kme_measure_tools.py --drill` (exit 0)
```
PASS DRILL-CLEAN-AFTER-MUTANTS unmutated rerun: 14/14 gates green
DRILL killed=9/9 backstops_held=2/2
```

`python3 -I tools/test_kme_pillars.py` (exit 0)
```
KMEP_PASS=89/89  threshold=89/89  skipped=0  inconclusive=0
```

`python3 -I tools/test_kme_pillars.py --drill` (exit 0)
```
PASS DRILL-CLEAN-AFTER-MUTANTS unmutated rerun: 84/84 gates green
DRILL killed=20/20
```
(The drill's clean rerun counts 84 gates and the suite 89; the same pair was printed in the 02-01 and 02-03 summaries. Reported as observed, not investigated here.)

`python3 -I tools/test_kme_replay.py` (exit 0)
```
KMER_PASS=45/45  threshold=45/45  skipped=1  inconclusive=0
```
(The skip is `V-KMER-BUNDLE-SUMMARY-UAT`, no UAT file for phases 01-06 on this checkout; it skipped before Phase 2.)

`python3 -I tools/test_usage_index_v5.py` (exit 0)
```
USAGE_INDEX_V5_PASS=74/74  threshold=74/74
```

`python3 tools/test_usage_index.py` (exit 0)
```
USAGE_INDEX_PASS=22/22  threshold=22/22
```

`python3 tools/test_ao_p0.py` (exit 0)
```
AOP0_PASS=22/22  threshold=22/22
```

`python3 tools/test_incremental_cognition_program.py --generation 2 --status` (exit 0, with OPP-002 present)
```
{"open": ["M", "P", "Q", "R"], "closed": ["O"], "violations": []}
```

`python3 tools/test_incremental_cognition_program.py --generation 2 --selftest` (exit 0): `ICP_GEN2_SELFTEST=PASS`

`python3 tools/test_incremental_cognition_program.py --generation 2 --audit` (exit 0)
```
ICP_GEN2_AUDIT=PASS frozen_sha256=a8ac15d894a72c74eb71901b3081c7a6a20a0ee2d9da085a270dd015a204d39e
```

`python3 tools/test_incremental_cognition_program.py --generation 2 --final` (exit 1, expected and unchanged): `ICP_GEN2_VERDICT=FAIL failures=8` (L3 for M, P, Q, R, and four L8 lines), the frozen expected-open set that audit check A3 pins. Pillar P has no terminal in Phase 2.

`python3 modules/liveness/reachability.py` (exit 1, inherited, reported as red)
```
modules: 490  |  REACHABLE: 310  |  ORPHAN: 180  |  UNKNOWN: 0  |  gate offenders: 59
| tower/ratchet | ORPHAN | - |
```
Identical to the Phase 1 line in `01-EVIDENCE.md`. Its aperture is packages under `modules/` only (the tool prints "`tools/` is NOT scanned"); the Phase 2 files are `tools/strace_io_sum.py`, `tools/kme_equivalence.py`, `tools/test_kme_challenger.py`, `tools/test_kme_measure_tools.py` and `wiki/tools/kme_*.py`, all outside it. `git diff --stat 23f5a7f1..HEAD -- modules vault/liveness` prints nothing (Phase 2 changed no module and no registry entry), and `grep -nE 'strace_io_sum|kme_equivalence|kme_pillars|kme_replay|kme_token_audit|test_kme' ` over the tool's output returns no line: no offender names a Phase 2 file. No registry declaration was added, because a tool outside the aperture cannot appear as unreachable and declaring it would record a class for a module the tool never examines. The reachability of the two instruments is what the gates themselves show: `tools/test_kme_challenger.py` drives `tools/strace_io_sum.py` and `tools/kme_equivalence.py` on real data in `--real` and `--real-exposure`.

Inherited reds from Phase 1 (`01-BASELINE.md`) were not re-run in this plan and are unchanged: `tools/test_estate_shadow.py` `ESTATE_SHADOW_PASS=10/11`, `tools/test_frontier_intelligence_os.py` `DATASET_FAMILY_VERDICT=FAIL`, `tools/test_token_ground_truth_junction.py` crash.

## Product Delta

- A KME analyst can run the seven KME-L measurement queries without rescanning the scoped history: `python3 -I wiki/tools/kme_pillars.py all --denominator KME-L --until auto --expand --root /home/kobii/kme-corpus/projects --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --plan challenger --index-db /home/kobii/ao-scratch/p1/cold.sqlite --cert <cert.json> --path-log <log> --out-dir <dir>` then the same with `kme_replay.py rank`. After `kme_pillars.py certify` (one scoped champion scan, `KMEP-CERT verdict=CERTIFIED selected=102 uncovered=16`, 23.3 s) a query reads 369 files instead of 995.
- Cost per 7-file query (`all` + `rank`), warm median of 5: 29.581 s against 56.976 s for the scoped path (1.926x faster) and 869 s for the cited champion Run 5; raw bytes 3,298,099,868 against 6,120,339,068 (1.856x fewer); plus 1,805,435,496 index bytes the scoped path does not read. Evicted best-effort: 37.529 s against 58.523 s (residency not measured).
- A query is honest about how it was answered: every run can write one path record (`plan_taken`, `deopt`, `stale`, `read_set`, `keys`), a refused or stale index is never served silently (`--plan challenger` exits 3 with nothing written), and `--plan auto` falls back to scoped raw with the reason logged; `--plan champion` is untouched and remains the default (KS-4).
- A KME-only question opens zero CostaLuz bytes and zero cross-project bytes; the global raw scan runs only on an explicit `--cross-project`.
- Two reusable instruments: `tools/strace_io_sum.py` (open-set bytes, unique bytes by inode, a separate index column, a forbidden-path detector with a firing control) and `tools/kme_equivalence.py` (masked 7-file comparator that fails on one changed digit).
- Not delivered: a saving over real usage (no count of real queries exists), a facts sidecar, any change to the default plan.

## Intelligence Delta

- For six of seven files (D, E, F, G, H, L) the index answers only the selection, the population, the scope and the watermark; the metrics need transcript content the index does not hold (02-RESEARCH: only pillar I is close to index-only). So the challenger's saving is bounded by selecting fewer sessions: 369 of 995 files, 3.30 GB of 6.12 GB raw, and no row of the table shows a zero-raw answer. The name "zero-rescan" describes the scoped history, not the selected sessions.
- The index is not free: each query reads the whole-corpus SQLite file (902,717,748 bytes per process, 1,805,435,496 for `all` + `rank`), so on total read volume the saving is 16.6 % (5.10 GB against 6.12 GB), not 46.1 %. The wall win (1.93x) is larger than the byte win on total volume (the challenger's evicted-versus-warm gap is 7.9 s, the scoped path's 1.5 s; the cause of the difference was not isolated).
- The 568-sessions trap: every measurement file carries `corpus.sessions_scanned` = 568, while the index sees 552 sessions in the same six directories; the champion also counts 16 skipped-shape pseudo-sessions (`_preserved`, `_empty_shells`). A selected-files-only scan would have changed that field in all seven files. `scan_project(select=...)` therefore skips `scan_file` for refused files but still registers the session (`V-KMEC-SESSIONS-SCANNED-568` observes 568 on all seven).
- Closure exactness has more members than "selected sessions": the read set on real data is 107 sessions (102 selected + 5 sessions without a first timestamp, the IN-04 closure), and after the post-delta append 110 (adds 3 newly stale non-selected sessions). A guard that reads "selected only" would have been wrong by exactly those sessions; the gate asserts `sessions == selected + len(no_first_ts)`.
- A new KME session that appears after certification changes the frozen population, so it is a deopt (shadow guard), not a served answer (`V-KMEC-STALE-NEW-FILE` c); only sessions that leave the frozen answer unchanged (new non-KME file, vanished file, lines after the freeze instant) are read as stale and served.
- Metric digests must cover functions and classes, not only constants: a change to `burden`, `classify_read` or an observer class would otherwise leave every digest unchanged. The lists were derived from the source closure of each observer and `V-KMEC-METRIC-COVERAGE` regenerates that closure (control: dropping `VERIFY_CMD_RE` from H is reported).
- Instruments were wrong before the system was: the first `--real` run was 5/7 because two new gates expected the wrong printed shape; the challenger was already `SAME 7/7`. The strace summer parsed `lines_unparsed` 181 and 362 lines in the challenger logs (process exit / signal lines and resumed reads); zero reads lack a path annotation. A `grep -ci costaluz` over a challenger strace log is 3, from data bytes (an email domain) inside three KME transcripts, not from a path: forbidden bytes are counted by path only.
- The scoped path is nearly cache-insensitive on this NVMe host (58.5 s evicted against 57.0 s warm), so "cold versus warm" is not where the challenger's advantage comes from here; it comes from reading 369 files instead of 995.

## Limits

- **Narrowed scope.** The win is for the seven-file KME-L query on the GEX44 corpus copy against the scoped `all` + `rank` path. It is not a zero-raw-read result, not an index-bytes saving (the challenger reads 1,805,435,496 index bytes the scoped path does not read), and not a pillar G caching result: G reads its selected files raw every time and persists no text-derived cache (orchestrator decision 6).
- Whole-corpus index bytes: the index is one file holding metadata rows of every project, CostaLuz included, and no transcript text; its size is paid on every query. The post-delta row uses a six-directory index (519,078,504 bytes) and is not comparable on that column.
- Cache state: "evicted" rows are `posix_fadvise(DONTNEED)` best-effort, residency not measured; walls are medians of N=5 untraced repetitions (cold rows split 3 + 2), bytes come from two traced repetitions with identical open sets.
- The laptop plane is not measured. `plane: gex44` is on every record.
- Savings over real usage are not measured: no count of real KME-L queries exists on this plane. OPP-002 carries the per-query difference as a prediction, `realized_dividend` null.
- The certificate is invalidated by any edit to a selection source (`tools/usage_index.py`, `wiki/tools/kme_token_audit.py`, `wiki/tools/kme_report.py`, or the selection functions of `kme_pillars.py`) or to a metric definition; re-certification is one scoped champion scan (about 23 s on this corpus). A selection-source edit outside the keyed names would read stale until re-certified.
- Facts sidecar not built: increment 1 beat the scoped path, so orchestrator decision 1 leaves increment 2 unbuilt.
- Pillar P: frozen rule clause 6 (ratchet promotion, fresh worker, bypass gate) belongs to Phase 6. This phase writes no terminal for P: `--status` keeps P open, `--final` stays FAIL as pinned by audit check A3. The ledger row of this phase is OPP-002 at status `canary`, its evidence pinned by sha256, accepted by `--status`, `--selftest` and `--audit` with the frozen object unchanged.
- `requirements mark-complete` was not run by this plan; the orchestrator closes the phase after verification.
- Scratch retained outside the repo under `/home/kobii/ao-scratch/p2/` (3.16 GB scratch copy, delta index, certificates, strace logs, bench JSON, `p_judgement.py`, `gen_crit5.py`, `add_opp002.py`).
- Inherited reds are unchanged and not claimed green (regression set above).

## Next

- Phase 6: promote through `modules/tower/ratchet.promote` at project scope (it is currently an unreachable orphan in the liveness table, so the promotion path must be wired before it counts), make the challenger the default plan for the KME frozen questions, add a fresh-worker path-log test (a new process takes `plan_taken index` without a manual flag), and use `--real` (7 gates, about 54 s) and `--real-exposure` (2 gates, about 76 s) as the bypass regression gate; both exit 1 on any non-PASS including a skip.
- Re-measure on the laptop plane before any claim there.
- If the index read per query matters at promotion, price a narrower index read (an index query that touches fewer pages) as a new opportunity, not as a change to this one.
