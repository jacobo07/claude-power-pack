---
phase: 02-kme-l-challenger
plan: 02
subsystem: kme-measurement
tags: [challenger, strace, open-set, equivalence, comparator, mutation-drill, forbidden-bytes]
requires:
  - phase: 02-kme-l-challenger
    provides: plan 02-01 access plans (no shared file; this plan builds the instruments the later runs use)
provides:
  - "tools/strace_io_sum.py: `sum` (raw / unique / cross-project / forbidden / index bytes, opens, by_project, UNMEASURED on an empty log) and `run` (N untraced walls with median, K traced sums, best-effort page-cache eviction, open_set_identical)"
  - "tools/kme_equivalence.py: `compare` (masked sha256 of the 7 KME-L files + sessions_scanned + H verdict map) and `selftest-perturb`, VOLATILE masking list"
  - "tools/test_kme_measure_tools.py: 14 V-KMEC gates, KMET_PASS=14/14, --drill 9/9 mutants killed + 2 backstops held"
affects: [02-03, 02-04, 02-05, 02-06]
plan_head_before: 3be6c5be127019636a9d2112de8f0a40604fd95f
actuals:
  tokens: 13464     # chars/4 over the +/- lines of tools/ (git diff 3be6c5be..HEAD, 53858 chars)
  tasks: 2
  commits: 4        # measured: git rev-list --count 3be6c5be..HEAD (the docs commit of this summary comes after)
tech-stack:
  added: []
  patterns:
    - "every detector ships with a positive control and a paired negative (forbidden bytes, perturbed digit)"
    - "gates call main(argv) in process so the drill can swap module attributes of both tools"
    - "an explicit backstop check (sessions_scanned, H verdict map) proven live by a mask that is deliberately too wide"
key-files:
  created:
    - tools/strace_io_sum.py
    - tools/kme_equivalence.py
    - tools/test_kme_measure_tools.py
  modified: []
key-decisions:
  - "UNMEASURED summaries carry null in every numeric column, not 0, so a consumer that skips the verdict still cannot read zero bytes"
  - "open_set_identical is null (not true) when fewer than two traced repetitions were measured; it is true/false only for K >= 2"
  - "A failed step aborts the rest of that repetition; the run is listed under `failed` and kept out of the median"
  - "compare prints extra fields why= and verdict_map= beside the planned ones; body-line differences are named by section heading (body:Numerator), never by content"
  - "--pillars accepts only distinct letters from DEFGHIL (exit 2 otherwise)"
requirements-completed: [AO-07, AO-09, AOP-P]
duration: ~5 min of clock time per `date` (start stamped at the commit ledger)
completed: 2026-10-07
status: complete
---

# Phase 2 Plan 02: Measuring instruments Summary

**An strace open-set summer that reports raw, unique, cross-project, forbidden and index bytes exactly on synthetic logs (and UNMEASURED, never zero, on an empty one), and a masked-sha256 comparator for the 7 KME-L files that is proven able to say DIFFERENT; both are covered by 14 gates and a 9-mutant drill.**

## What was built

**Task 1 (tracer, commit f30b167a): `tools/strace_io_sum.py`.** Stdlib only. `parse_syscalls` handles complete, `<unfinished ...>` and `<... resumed>` lines paired by PID, `read` / `pread64` / `readv` / `preadv` attributed to the `-y` fd path, and `openat` taken from the return annotation (strace already resolves symlinks there, so aliases appear as real paths in a real log; the unique-bytes key is still `(st_dev, st_ino)` taken at summary time). `forbidden_bytes` / `forbidden_opens` use `(?i)costaluz` against the full path, opens include directories. `index_bytes` is a separate column (index path plus `-wal` / `-shm` / `-journal`). `run` executes shlex-split steps with no shell, evicts with `posix_fadvise(DONTNEED)` before each repetition when asked, and traced repetitions run under `strace -f -y -e trace=openat,read,pread64,readv,preadv`.

**Task 2 (tdd, commits af842d8d RED, 61eb3ee8 GREEN, b9c8b273 drill): `tools/kme_equivalence.py`.** `VOLATILE` masks exactly front-matter and JSON `measured_at` and `command`, and `"commit": "<40 hex>"`. `compare` needs equal normalised sha, equal `corpus.sessions_scanned`, and for H an equal `details.consumed_owner_verdicts.pillars`; it prints `KMEQ pillar=... verdict=... first_diff_line=<n> key=<dotted json key | front-matter key | body:<section>>` and `KMEQ_VERDICT=... same=k/n`. `selftest-perturb` checks self copy SAME, volatile-only change SAME, one-digit population change DIFFERENT (and one H terminal change DIFFERENT) on each committed file, using its own volatilise / perturb helpers rather than `VOLATILE`.

## Verification (observed)

```
python3 -I tools/test_kme_measure_tools.py
PASS V-KMEC-SUM-EXACT rc=0 mismatches={} cross=7000
PASS V-KMEC-FORBID-FIRES positive control bytes=4000 opens=2; paired control without the lines=(0, 0); lowercase+spaced path bytes=150 opens=2
PASS V-KMEC-UNIQUE-INODE alias pair raw=200 unique=1000 files=2; vanished file listed unstattable=True
PASS V-KMEC-SUM-EMPTY-UNMEASURED [('empty', 3, 'UNMEASURED', 0), ('garbage', 3, 'UNMEASURED', 0)] cli /dev/null rc=3
PASS V-KMEC-RUN-REAL-STRACE rc=0 raw_bytes=12345 files=1 index_bytes=0 identical(K=2)=True median(N=0)=None
PASS V-KMEC-RUN-MEDIAN ... flaky failed=[True, False, False] ... all-failed median=None
PASS V-KMEC-EQUIV-SELF copies SSSSSSS rc=0; committed-vs-itself SSSSSSS rc=0; committed unchanged=True
PASS V-KMEC-EQUIV-VOLATILE-MASKED 7/7 files changed in measured_at/command (+H commit) and renamed 2026-10-09: SSSSSSS rc=0
PASS V-KMEC-EQUIV-PERTURB one population digit per file, DIFFERENT and exit 1: {'D': True, 'E': True, 'F': True, 'G': True, 'H': True, 'I': True, 'L': True}
PASS V-KMEC-EQUIV-SESSIONS D with sessions_scanned 552: DSSSSSS fields={'sessions_scanned': '552/568', 'key': 'corpus.sessions_scanned', ...}
PASS V-KMEC-EQUIV-H-VERDICTS H copy with one owner terminal changed and commit changed: SSSSDSS verdict_map=DIFFERENT
PASS V-KMEC-EQUIV-MISSING I absent: SSSSSMS rc=1; two D files: MISSING rc=1; unknown pillar X rc=2
PASS V-KMEC-EQUIV-NO-CONTENT D body line changed to carry a canary: DIFFERENT key=body:Numerator canary printed=False
PASS V-KMEC-EQUIV-SELFTEST real files rc=0 PASS; a directory missing L rc=1
KMET_PASS=14/14  threshold=14/14  skipped=0  inconclusive=0

python3 -I tools/test_kme_measure_tools.py --drill
PASS DRILL-CONTROL unmutated run: 14/14 gates green
KILLED M1..M9 (mask-every-line, mask-nothing, verdict-map check off, sessions check off, pread64 ignored,
               case-sensitive forbid, unique by path, empty log as zero, resumed lines dropped)
HELD B1, B2 (a mask that swallows the verdict map / sessions_scanned is still refused by the explicit check)
PASS DRILL-CLEAN-AFTER-MUTANTS unmutated rerun: 14/14 gates green
DRILL killed=9/9 backstops_held=2/2

python3 -I tools/kme_equivalence.py compare --candidate <measurements> --committed <measurements>
KMEQ pillar=D..L verdict=SAME (seven lines, sessions_scanned=568/568)   KMEQ_VERDICT=SAME same=7/7   rc=0
python3 -I tools/kme_equivalence.py selftest-perturb --committed <measurements>   -> KMEQ_SELFTEST=PASS
python3 -I tools/strace_io_sum.py sum /dev/null --corpus-root /home/kobii/kme-corpus/projects -> "verdict": "UNMEASURED", exit 3
git status --porcelain -- vault/programs/incremental-cognition/measurements  -> (empty)
```

Tracer gate: Task 1 `<verify>` was re-run end-to-end after the last Task 1 edit (null columns on UNMEASURED) and again before expanding to Task 2; both passed, so expansion proceeded. Smoke on a real log: the summer parsed `/home/kobii/ao-scratch/p1/delta2.strace` (3,762,438 syscalls, 610 MB) with `lines_unparsed` 0 (that log read a different root, so its corpus columns are 0; this checks the parser, not a measurement).

## Deviations from Plan

**1. [Rule 2 - correctness] UNMEASURED columns are null.** The plan requires the verdict UNMEASURED and exit 3; the JSON also reported `raw_bytes: 0` etc. A consumer that skipped the verdict would read zero bytes (T-02-10 spirit), so every numeric column is `null` on UNMEASURED. Commit f30b167a.

**2. [Rule 2 - correctness] `open_set_identical` is null for K < 2.** "Identical across K repetitions" is vacuously true for K = 1; reporting true would be a claim no comparison backs. It is true or false only when two or more traced repetitions were MEASURED (K = 2 is exercised in V-KMEC-RUN-REAL-STRACE). Downstream plans that want the flag must use `--trace-repeat` of at least 2.

**3. [Rule 3 - scope of RED] The TDD RED for Task 2 is an absent module.** `tools/kme_equivalence.py` is a new file, so the RED commit af842d8d fails the eight comparator gates with `ModuleNotFoundError` (KMET_PASS=6/14). That is a module-absent RED, not an assertion-level RED; no stub module was created to turn it into one (a stub that returns SAME would have been a scaffold). The GREEN commit turns all 14 green, and the drill then proves each assertion can fail.

**4. [Additions beyond the plan's gate list]** `V-KMEC-EQUIV-NO-CONTENT` (canary carried in a body line is never printed; covers the AO-09 safety prohibition and T-02-08), `V-KMEC-EQUIV-SELFTEST` (selftest PASS on the real files, FAIL on a directory missing L), and the two drill backstops B1 / B2. The plan listed 12 gates; there are 14.

**5. Pre-commit assertion.** The worktree branch is `mission/autonomous-optimization-gen2`, outside the `agent-*` namespace the generic allow-list expects; the orchestrator pinned this branch and the root-pin guard passed (exit 0) before every commit. The namespace check was not applied (same as plan 02-01).

**6. Requirement status left as is.** Per the unattended instructions, `requirements mark-complete` was not run for AO-07 / AO-09 / AOP-P (the phase is not done until 02-06); `requirements-completed` lists the IDs this plan advanced.

## Notes for the following plans

- `run` takes `--evict PATH` repeatedly; eviction is best-effort and the output says `cache: evicted best-effort, residency not measured`. A cold-cache claim in a later plan must quote that label, not "cold".
- strace's `-y` annotation is the resolved path, so on the real corpus the junction-made aliases collapse to one path before the summer sees them; `raw_files_opened` is then already distinct by real path and `unique_bytes` (stat of each opened path) agrees. `unique_bytes` is file size at summary time, not bytes read; compare it with `raw_bytes` for the re-read factor.
- `cross_project_bytes` is `null` unless `--scope-regex` is given (matched against the project directory name with `re.search`, like `--project-filter`), and counts only `.jsonl` bytes under the corpus root; the whole-corpus index is the separate `index_bytes` column (decision 2).
- `forbidden_opens` counts successful `openat` calls (directories included, repeated opens of one path counted each time); `forbidden_bytes` counts bytes read from any path matching the regex, inside or outside the corpus root.
- A traced step that fails (exit not in `--ok-exit`) leaves its repetition out of `open_set_identical` and out of the traced sums; `run` then exits 1.
- The comparator's candidate glob is `<P>-KME-L-*.md`, so a candidate directory must hold exactly one such file per pillar; when comparing a gen2 re-run, write the candidate files into a fresh directory (the gen1 files must stay untouched).
- `tools/` modules are not under `modules/`, so `modules/liveness/reachability.py` does not enrol them; they are reached by the plan 02-03 .. 02-06 commands and by `tools/test_kme_measure_tools.py`.

## Known Stubs

None.

## Threat Flags

None beyond the plan's threat model. T-02-06 (forbidden detector that cannot fire): V-KMEC-FORBID-FIRES plus drill M6. T-02-07 (comparator that masks too much): V-KMEC-EQUIV-PERTURB on all 7 files plus drill M1, and B1 / B2 for the explicit checks. T-02-08 (disclosure): V-KMEC-EQUIV-NO-CONTENT and the payload check in V-KMEC-SUM-EXACT; strace logs of the real-strace gate live in a scratch directory removed at exit. T-02-09 (tampering): the comparator only reads, V-KMEC-EQUIV-SELF and -SELFTEST re-hash the committed files before and after, and `git status --porcelain` on the measurements directory is empty. T-02-10: V-KMEC-SUM-EMPTY-UNMEASURED plus drill M8.

## Self-Check: PASSED

- FOUND: tools/strace_io_sum.py, tools/kme_equivalence.py, tools/test_kme_measure_tools.py
- FOUND commits: f30b167a, af842d8d, 61eb3ee8, b9c8b273 (`git log --oneline`)
- Each task commit touches only that task's files; the measurements directory is unchanged.
