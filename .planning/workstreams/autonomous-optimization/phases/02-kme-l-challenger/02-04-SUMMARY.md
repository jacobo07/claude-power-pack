---
phase: 02-kme-l-challenger
plan: 04
subsystem: kme-analytics
tags: [challenger, equivalence, certify, shadow, strace, costaluz, exposure, real-corpus, gex44]
requires:
  - phase: 02-kme-l-challenger
    provides: plan 02-02 strace_io_sum.py and kme_equivalence.py (compare, selftest-perturb)
  - phase: 02-kme-l-challenger
    provides: plan 02-03 certify, guard chain, path record schema 2
  - phase: 01-usage-index-v5-substrate
    provides: /home/kobii/ao-scratch/p1/cold.sqlite (schema 5, population EXACT for KME-L)
provides:
  - "tools/test_kme_challenger.py --real: 7 real-corpus gates (KMEC_REAL_PASS=7/7), re-runnable as a Phase 6 regression gate"
  - "tools/test_kme_challenger.py --real-exposure: V-KMEC-COSTALUZ-ZERO-REAL (challenger zero + firing control in one gate) and V-KMEC-EXPOSURE-READONLY (KMEC_EXPOSURE_PASS=2/2)"
  - "P-equivalence-gex44.md: certification, KMEQ_VERDICT=SAME same=7/7, sessions_scanned 568 on all 7, H verdict map equal, comparator negative control, two path records, read-only proof"
  - "P-exposure-gex44.md: challenger population and 7-file query under strace with forbidden_bytes 0, control 1 (filter + CostaLuz) and control 2 (unscoped scan) firing, read-only proof"
affects: [02-05, 02-06]
plan_head_before: a97c2f0d8b4aa5b9b99a003cbfcf0bf6a4347b98
actuals:
  tokens: 11211     # chars/4 over the +/- lines of tools and the two evidence files (git diff a97c2f0d..HEAD, 44845 chars)
  tasks: 2
  commits: 2        # measured: git rev-list --count a97c2f0d..HEAD (the docs commit of this summary comes after)
tech-stack:
  added: []
  patterns:
    - "real-corpus gates run one shared sequence once and every gate reads its record; an absent corpus or index is a SKIP and the mode exits 1"
    - "every real run writes under a fresh /home/kobii/ao-scratch/p2/<mode>-<UTC stamp>/ and hashes the corpus manifest and the index before and after"
    - "a detector gate carries its firing control in the same gate (challenger zero AND filter+CostaLuz above zero)"
key-files:
  created:
    - vault/programs/incremental-cognition/gen2/evidence/P-equivalence-gex44.md
    - vault/programs/incremental-cognition/gen2/evidence/P-exposure-gex44.md
  modified:
    - tools/test_kme_challenger.py
key-decisions:
  - "The challenger's planned read set on the real corpus is 107 sessions / 369 files / 1,648,220,948 bytes: the 102 index-selected sessions plus the 5 sessions the index holds no first timestamp for (read raw by design, 02-03 guard no_first_ts / IN-04). The plan's 'index-selected sessions only' and 364-file prediction are refined, not violated: the output is SAME on all 7 files."
  - "Exposure is path-based (forbid regex on opened paths). The string 'costaluz' also occurs in the data prefix of three reads of KME-project transcripts (an email domain), which is not a CostaLuz file; recorded as a limit in the evidence, not counted."
requirements-completed: [AO-07, AO-09, AOP-P]
duration: ~25 min
completed: 2026-10-07
status: complete
---

# Phase 2 Plan 04: Real-corpus equivalence and CostaLuz exposure Summary

**On the GEX44 corpus copy the challenger certifies (102 sessions, shadow agrees), reproduces all seven KME-L measurement files (`KMEQ_VERDICT=SAME same=7/7`, 568 sessions scanned each, H verdict map equal), and a KME-only query opens 0 CostaLuz bytes at the OS layer while two controls report 98,986,782 and 99,816,108 forbidden bytes; the corpus and the Phase 1 index are byte-for-byte unchanged.**

## What was built

**Task 1 (tracer, commit 87fa25bb).** `--real` mode in `tools/test_kme_challenger.py`. One shared sequence (`real_run`): corpus manifest (sha256 over sorted `size mtime_ns relpath` from an lstat walk, no file opened) and index sha256 + mtime_ns; `certify` with `--cert` under a fresh `/home/kobii/ao-scratch/p2/real-<stamp>/`; `kme_pillars.py all` and `kme_replay.py rank` with `--plan challenger --index-db --cert --path-log --out-dir`; `kme_equivalence.py compare`; `selftest-perturb`; manifest and index hash again. Seven gates read that record. Absent corpus or index: every gate SKIPs and the mode exits 1.

**Task 2 (commit 1ed02255).** `--real-exposure` mode: certify once, then two traced `population` runs through `tools/strace_io_sum.py run --repeat 0 --trace-repeat 1` (scope regex = the KME filter, forbid regex `(?i)costaluz`, index path recorded): the challenger run, and the control with filter `...|CostaLuz`, `--until 2026-10-03T16:13:37Z`, scoped plan, `--ok-exit 3`. The gate fails if the challenger half or the control half fails. Outside the gate the evidence adds the 7-file query under strace (steps `all` + `rank`) and the unscoped single champion scan.

## Verification observed

`timeout 600 python3 -I tools/test_kme_challenger.py --real` (final run, exit 0):

```
PASS V-KMEC-REAL-CERTIFIED rc=0 KMEP-CERT verdict=CERTIFIED selected=102 uncovered=16 ... shadow={'agree': True, 'champion_selected': 102, 'index_selected': 102} wall_s=23.5
PASS V-KMEC-EQUIV-REAL rc=0 KMEQ pillar=D..L verdict=SAME | KMEQ_VERDICT=SAME same=7/7
PASS V-KMEC-SESSIONS-SCANNED-568 sessions_scanned={'D': 568, 'E': 568, 'F': 568, 'G': 568, 'H': 568, 'I': 568, 'L': 568}
PASS V-KMEC-H-VERDICTS KMEQ pillar=H verdict=SAME verdict_map equal=True map={'P': 'FALSIFIED_OR_REJECTED_BY_EVIDENCE', 'G': 'FALSIFIED_OR_REJECTED_BY_EVIDENCE'}
PASS V-KMEC-EQUIV-PERTURB-REAL rc=0 ['KMEQ_SELFTEST=PASS']
PASS V-KMEC-REAL-INDEX-PATH ... plan_taken=index deopt=None stale=[] sessions=107 (selected 102 + no_first_ts 5) files=369 bytes=1648220948 (both records)
PASS V-KMEC-REAL-READONLY manifest before=29969e7d6ab1 after=29969e7d6ab1 files=10577; index sha before=6ddd159a914d after=6ddd159a914d mtime_ns equal=True
KMEC_REAL_PASS=7/7  threshold=7/7  skipped=0  inconclusive=0
```

`timeout 600 python3 -I tools/test_kme_challenger.py --real-exposure` (final run, exit 0):

```
PASS V-KMEC-COSTALUZ-ZERO-REAL challenger {'forbidden_bytes': 0, 'forbidden_opens': 0, 'cross_project_bytes': 0, 'raw_bytes': 1649049934, 'raw_files_opened': 369, 'unique_bytes': 1648220948, 'index_bytes': 902717748} planned_files=369; control forbidden_bytes=98986782 forbidden_opens=73 cross_project_bytes=98986782 (halves: challenger=True control_fires=True)
PASS V-KMEC-EXPOSURE-READONLY manifest before=29969e7d6ab1 after=29969e7d6ab1; index sha before=6ddd159a914d after=6ddd159a914d mtime_ns equal=True
KMEC_EXPOSURE_PASS=2/2  threshold=2/2  skipped=0  inconclusive=0
```

Hermetic default `python3 -I tools/test_kme_challenger.py` -> `KMEC_PASS=21/21  threshold=21/21  skipped=0  inconclusive=0`; `--drill` -> `DRILL killed=15/15`, `DRILL-CLEAN-AFTER-MUTANTS 21/21`. Evidence-file checks (the two `python3 -c` presence checks) printed `[]`. `git status --porcelain vault/programs/incremental-cognition/measurements/` is empty. A final manifest and index hash after every step of the plan (including the 7-file and unscoped runs) equals the before values (`/home/kobii/ao-scratch/p2/final-check.json`, recorded in P-exposure-gex44.md).

## Measured numbers (commands in the evidence files)

| Quantity | Value |
|---|---|
| certify | CERTIFIED, 102 selected, shadow agree, uncovered 16, 23.5 s |
| KMEQ | D, E, F, G, H, I, L all SAME; sessions_scanned 568/568 on each |
| challenger runs | `all` 16.1 s, `rank` 13.3 s (single runs, residency not measured); plan_taken index, no deopt, stale [] |
| planned read set | 107 sessions / 369 files / 1,648,220,948 bytes (53.97 % of the plan's 3,053,908,888-byte scoped figure, which was not re-measured here) |
| challenger population (strace) | raw_bytes 1,649,049,934; raw_files_opened 369; forbidden 0 / 0; cross_project 0; index_bytes 902,717,748 |
| challenger 7-file (2 processes) | raw_bytes 3,298,099,868; 369 files; forbidden 0 / 0; cross_project 0; index_bytes 1,805,435,496; same open_set_sha256 as the population run |
| control 1 (filter + CostaLuz, scoped) | forbidden_bytes 98,986,782; forbidden_opens 73; raw_files_opened 1,017 |
| control 2 (unscoped champion scan, full, 109 s) | raw_bytes 10,908,828,352; 4,015 files; cross_project 7,848,658,818; forbidden_bytes 99,816,108; forbidden_opens 109 |

## Deviations from Plan

**1. [Design] Planned read set is 107 sessions, not 102.** The path record's read set holds the 102 index-selected sessions plus the 5 sessions without a first timestamp (02-03 IN-04 closure, guard `no_first_ts`). The plan's truth "index-selected sessions only" and its 364-file / 1,648,219,354-byte prediction are off by exactly those 5 sessions (5 files, 1,594 bytes). The gate V-KMEC-REAL-INDEX-PATH asserts `sessions == selected + len(no_first_ts)`, so any session beyond those two sets would still fail. The output is SAME on all 7 files, so the extra raw reads do not change an answer.

**2. [Design] Gate written first against a wrong reading of two outputs.** The first `--real` run was 5/7: V-KMEC-H-VERDICTS expected a printed map where the comparator prints `verdict_map=SAME`, and V-KMEC-REAL-INDEX-PATH expected 102 sessions (item 1). Both were errors of the new gate, not of the challenger; equivalence was already `SAME same=7/7`. The gates were corrected (H now also reads and compares the two verdict maps itself) and `--real` was run again; the evidence comes from the final green run. The plan's "run once" therefore became three runs of `--real` (one red, two green; the last one captured to a file for the evidence). No challenger defect appeared, so the defect rule (fix rounds, `BLOCKED: equivalence`) did not trigger.

**3. [Rule 2 - correctness] Extra gate V-KMEC-EXPOSURE-READONLY.** The plan listed one exposure gate; the acceptance criteria also require the read-only hashes, so the mode asserts them as a second gate (2/2 instead of 1/1). Stricter than the plan, nothing relaxed.

**4. [Instrument limit, recorded] Path-based forbid detection.** `grep -ci costaluz` on each challenger strace log gives 3: the string is in the data prefix of three reads of KME-project subagent transcripts (an email domain), not a CostaLuz path. The gate and the evidence count paths only; the limit is stated in P-exposure-gex44.md under Method. The same note applies to `lines_unparsed` (181 and 362 in the challenger logs: process exit / signal lines and resumed reads; zero reads lack a path annotation).

**5. [Process] The 7-file strace run used the certificate of an earlier `--real-exposure` run** (`exposure-20261006T231828Z`, same question flags), not the one of the final gate run; both certificates are for the identical question and the commands in the evidence name the one used.

## Known Stubs

None.

## Threat Flags

None beyond the plan's threat model. T-02-16 (tampering): V-KMEC-REAL-READONLY and V-KMEC-EXPOSURE-READONLY plus the final check, all equal. T-02-17 (CostaLuz read): V-KMEC-COSTALUZ-ZERO-REAL with its firing control. T-02-18: strace logs stay in `/home/kobii/ao-scratch/p2/`, evidence holds summed JSON only. T-02-19: the equivalence gate requires `KMEQ_VERDICT=SAME same=7/7`; nothing was DIFFERENT. T-02-20: the unscoped control used an explicit `--until`, ran 109 s under `timeout 590`, and finished (not partial).

## Notes for the following plans

- **02-05 cost table:** control 2 is the champion's byte basis for the unscoped scan (raw 10,908,828,352; unique 9,934,971,549; 4,015 files; wall 109 s under strace, one run). The challenger rows are the population run and the 7-file run above; the challenger also reads the index DB (902,717,748 bytes per process, about 1.84 GB for the 7-file query) in its own `index_bytes` column. Do not mix the two columns; the challenger's transcript bytes are about 1.65 GB per process against about 3.16 GB for the scoped control.
- `--real` takes about 54 s and `--real-exposure` about 76 s; both write a fresh run directory under `/home/kobii/ao-scratch/p2/` (never cleaned automatically).
- Certificates must be made with the same question flags as the run; the real modes build both from one `real_question()`.
- Phase 6 can call `--real` / `--real-exposure` as regression gates; exit 1 on any non-PASS including SKIP.

## Requirement status

`requirements mark-complete` was not run (unattended instruction): AO-07, AO-09 and AOP-P stay as they are until 02-06.

## Self-Check: PASSED

- FOUND: tools/test_kme_challenger.py (`--real`, `--real-exposure`), vault/programs/incremental-cognition/gen2/evidence/P-equivalence-gex44.md, vault/programs/incremental-cognition/gen2/evidence/P-exposure-gex44.md
- FOUND commits: 87fa25bb (Task 1), 1ed02255 (Task 2)
