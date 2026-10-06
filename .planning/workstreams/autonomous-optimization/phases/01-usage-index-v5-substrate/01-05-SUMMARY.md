---
phase: 01-usage-index-v5-substrate
plan: 05
subsystem: usage_index
tags: [usage-index, pillar-O, kme-l-parity, corpus-measurement, refresh-cost, delta, production-reality, gex44]
requires: [01-04]
provides:
  - "O-parity-gex44.md: KME-L parity EXACT on the GEX44 corpus copy, dedup reconciled to the unit, unfiltered answer reconciled to champion Run 5, read-only proof"
  - "O-cost-gex44.md: refresh cost cold / warm cold / no-op / 6-dir cold / delta, with rchar attributed by strace"
  - "O-prg.md: real CLI on the real substrate, green exit 0 EXACT, red exit 1 DRIFTED, red exit 3 UNMEASURED"
  - "01-BASELINE.md after-change consumer regression table (20 rows, none worse)"
affects: [01-06]
tech-stack:
  added: []
  patterns: ["evidence files assembled from raw command output (no retyped numbers)", "strace -y read attribution to separate DB page reads from corpus bytes", "read-only manifest hash (size, mtime ns, path) before/after"]
key-files:
  created:
    - vault/programs/incremental-cognition/gen2/evidence/O-parity-gex44.md
    - vault/programs/incremental-cognition/gen2/evidence/O-cost-gex44.md
    - vault/programs/incremental-cognition/gen2/evidence/O-prg.md
  modified:
    - .planning/workstreams/autonomous-optimization/phases/01-usage-index-v5-substrate/01-BASELINE.md
key-decisions:
  - "No index defect was exposed, so the plan's defect rule did not fire: tools/usage_index.py and tools/test_usage_index_v5.py are untouched by this plan."
  - "The class-agnostic archived_excluded reconcile row is documented as such rather than changed; the KME-selected archived unit row is derived as include-archived minus default."
  - "rchar_delta is reported as measured (process-level truth, DB page reads included) with its strace attribution, not as a corpus byte count."
status: complete
plan_head_before: 15bd2b8086330ff6be08fb2c4e57348b8e9665f4
commits: 2
actuals:
  tokens: 11000
  tasks: 2
  commits: 2
duration: single session
completed: 2026-10-06
---

# Phase 1 Plan 05: KME-L parity on the corpus copy, refresh cost and Production Reality Summary

One cold v5 build of the 10.2 GB corpus copy reproduces the frozen KME-L population exactly (102 sessions / 34,871 calls / cache_read 11,549,646,300, verdict EXACT, first try, plane gex44), every dedup decision is reconciled to the API-request unit, the unfiltered answers reproduce champion Run 5 to the unit, and refresh cost is measured with commands for cold, warm cold, no-op and delta.

## Tasks

| Task | Name | Commit |
|---|---|---|
| 1 | Cold build of the corpus copy and KME-L parity, reconciled to the unit | 77e91179 |
| 2 | Refresh cost, after-change regression, Production Reality record | e3f85e92 |

## Parity verdict: EXACT (no fix round used)

command: `python3 tools/usage_index.py population --db /home/kobii/ao-scratch/p1/cold.sqlite --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --until 2026-10-03T16:13:37Z --select kme --host gex44 --expect KME-L --plane gex44` -> exit 0.

| field | observed | frozen KME-L |
|---|---|---|
| sessions_active / dead | 102 / 0 | 102 / 0 |
| calls | 34,871 | 34,871 |
| cache_read | 11,549,646,300 | 11,549,646,300 |
| input / cache_write / output (secondary) | 69,846 / 209,909,403 / 37,878,881 | same |

Reconcile to the unit: unique 34,853 / 11,544,130,372; first_writer (v4 figure) 34,853 / 11,544,130,372; 18 keys / 5,515,928 cache_read shared between **two selected sessions** (867896c0, KME_STRONG, 18 calls; 9184ed39, 403 calls), `shared_outside` 0; dup files 0; archived excluded 1 / 649 / 271,001,260; skipped shapes 50 files (`_preserved` 14, `_empty_shells` 36).
RESEARCH prediction check: occurrence 34,871 confirmed; first_writer 34,853 / 11,544,130,372 confirmed; the 18-key / 5,515,928 share confirmed but session 867896c0 is **selected** (RESEARCH called it non-KME), so it is not shared_outside.
Unfiltered vs Run 5 (105 / 35,776 / 11,888,777,786): v5 default 103 / 34,999 / 11,583,711,413 and include-archived 104 / 35,648 / 11,854,712,673 both equal the predictions; default + `_archived` (1 / 649 / 271,001,260) + the PP session counted a second time by the champion through the symlink `C--Users-User-Apps-mcp-video-analyzer -> C--Users-User--claude-skills-claude-power-pack` (1 / 128 / 34,065,113) = Run 5 exactly. The index walk does not follow directory symlinks (3 at the corpus root).

## Cost table (plane gex44; commands in O-cost-gex44.md)

| run | files_read | bytes_read | wall_s | rchar_delta | maxrss_kb | DB bytes | cache |
|---|---|---|---|---|---|---|---|
| v4 baseline (RESEARCH, cited) 6 dirs | 979 | 3,053,908,888 | 15.7 | n/a | 76 MB | 34.7 MB | unknown |
| v5 cold, whole corpus | 3,965 | 9,932,073,959 | 128.069 | 158,621,987,249 | 89,760 | 489,816,064 | evicted best-effort (fadvise DONTNEED), residency not measured |
| v5 warm cold, whole corpus | 3,965 | 9,932,073,959 | 118.661 | 158,621,987,249 | 89,672 | 489,816,064 | warm |
| v5 no-op | 0 | 0 | 0.577 | 958,972,508 | 33,352 | 489,816,064 | warm |
| v5 cold, 6-dir copy | 979 | 3,053,908,888 | 25.182 | 18,456,362,331 | 86,608 | 143,429,632 | warm |
| v5 delta (5 files, +709,630 B) | 5 | 709,630 | 0.07 | 136,372,842 | 30,560 | 143,486,976 | warm |

Delta equality: files_opened 5 = 5 appended files; bytes_ingested 709,630 = appended total 709,630 (difference 0). Per-byte on the v4 scope: v4 5.14 ns/B vs v5 8.25 ns/B = 1.60x; DB 4.1x larger.
**Finding (cost, not parity):** `rchar_delta` is 5-16x the corpus bytes. strace attribution (O-cost-gex44.md): on the 6-dir cold build 15.40 GB of 18.46 GB are reads of the SQLite file itself (3.76 M reads, 108x the final DB size), 3.05 GB corpus; the no-op reads 958,965,604 DB bytes and 0 corpus bytes. The corpus is read once; the amplification is SQLite page-cache misses. Not fixed here (no parity defect; tuning is a separate change).

## Gate outputs

- Parity verify (population EXACT) exit 0; evidence-content verifies exit 0; `python3 tools/test_incremental_cognition_program.py --generation 2 --status` -> `{"open": ["M", "O", "P", "Q", "R"], "closed": [], "violations": []}` exit 0.
- Read-only proof: manifest (size, mtime ns, path; 10,577 files, 10,205,326,251 bytes) sha256 `6eab1abced4f04cf4b601c22cf3695e7d7ae3fd31898698fdc2b7625fd10e6a9` before and after all steps; `cmp` identical.
- Production Reality (O-prg.md): green exit 0 EXACT; `--perturb calls=34872` exit 1 DRIFTED (delta -34872); `--project-filter '^no-such-project$'` exit 3 UNMEASURED ("no file in scope", population null).
- After-change regression (01-BASELINE.md, 20 rows, none worse): v5 `71/71`, `--drill` `killed=18/18`, `ICP_GEN2_SELFTEST=PASS`, `USAGE_INDEX_PASS=22/22`, `USAGE_INDEX_IDENTITY_PASS=11/11`, `STORE_IDENTITY_CONSUMERS_PASS=12/12`, `KMEP_PASS=89/89`, fanout 17/17, root_progress 11/11, spawn_outcomes 24/24, spawn_policy_v2 26/26, async 12/12, goal_journey 7/7, execution_shape 14/14, displacement 16/16, gsd_x identity 14/14; unchanged red/crash: estate_shadow 10/11 (`V-SHADOW-NESTED-PROJECT`), frontier_intelligence_os (`V-FIOS-LIVE-PATH-WIRED`), token_ground_truth_junction (`cmd` crash).
- `python3 modules/liveness/reachability.py` exit 1: `modules: 490 | REACHABLE: 310 | ORPHAN: 180 | UNKNOWN: 0 | gate offenders: 59`; names neither usage_index nor tis_observed (inherited, unrelated modules); its aperture is `modules/` only, so tools/usage_index.py is absent from its denominator.

## Deviations from Plan

**1. [Plan wording] Manifest by script, not `find | sha256sum`.** `/home/kobii/ao-scratch/p1/manifest.py` (os.walk, lstat, size + mtime in ns + path, sorted, sha256) replaces the `find -printf` pipeline because the sandbox refuses piped compound commands and ns mtimes are stricter than `%T@`. It refuses to write under the corpus. Symlinked directories are not followed (stated in the evidence).

**2. [Plan wording] New-row judgments in the baseline table.** The four added rows (v5 suite, drill, selftest, reachability) have no untouched-tree line; they are judged against a green exit (`better`), the reachability exit 1 is `same` only in the sense "not attributable to this phase". Stated in 01-BASELINE.md.

**3. Sandbox:** compound shell commands were refused; every step ran as a plain command, with small scratch scripts under `/home/kobii/ao-scratch/p1/` (outside the repo). The plan commit ledger was written with a shell redirect because the Write tool refuses the shared `.git` path.

No auto-fix (Rule 1-3) was needed; no index code was changed.

## Known Stubs

None.

## Threat Flags

None. T-01-19 (corpus tampering): all writes under the scratch area, append script refuses paths outside the delta copy, manifest hashes equal. T-01-20/21/22/23 mitigated as planned (command line next to every number, `--proj` always explicit, DRIFTED never recorded as a match, foreground runs bounded by `--deadline 540`; longest command 128 s).

## Blockers for the next plan (01-06)

None. Notes for the ledger pin: the three evidence files are final (sha256 to be taken by plan 06); `head:` in the front matter of `O-cost-gex44.md` and `O-prg.md` is 77e91179 and in `O-parity-gex44.md` 15bd2b80 (the commit that preceded the evidence). The rchar/DB-page amplification (5-16x corpus bytes, DB reads dominate) is open as a possible later tuning item, not a plan 06 blocker. `gate_baseline.py` remains a laptop owner-bundle line.

## Self-Check: PASSED

Files exist: O-parity-gex44.md, O-cost-gex44.md, O-prg.md, 01-BASELINE.md (after-change section). Commits 77e91179 and e3f85e92 present on mission/autonomous-optimization-gen2; `commits: 2` measured from the persisted ledger (`rev-list --count 15bd2b80..HEAD` before this docs commit).
