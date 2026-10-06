---
phase: 01-usage-index-v5-substrate
verified: 2026-10-06T21:58:00Z
status: passed
score: 4/4 must-haves verified
covered_files:
  - .planning/workstreams/autonomous-optimization/REQUIREMENTS.md
  - .planning/workstreams/autonomous-optimization/phases/01-usage-index-v5-substrate/01-01-PLAN.md
  - .planning/workstreams/autonomous-optimization/phases/01-usage-index-v5-substrate/01-01-SUMMARY.md
  - .planning/workstreams/autonomous-optimization/phases/01-usage-index-v5-substrate/01-02-PLAN.md
  - .planning/workstreams/autonomous-optimization/phases/01-usage-index-v5-substrate/01-02-SUMMARY.md
  - .planning/workstreams/autonomous-optimization/phases/01-usage-index-v5-substrate/01-03-PLAN.md
  - .planning/workstreams/autonomous-optimization/phases/01-usage-index-v5-substrate/01-03-SUMMARY.md
  - .planning/workstreams/autonomous-optimization/phases/01-usage-index-v5-substrate/01-04-PLAN.md
  - .planning/workstreams/autonomous-optimization/phases/01-usage-index-v5-substrate/01-04-SUMMARY.md
  - .planning/workstreams/autonomous-optimization/phases/01-usage-index-v5-substrate/01-05-PLAN.md
  - .planning/workstreams/autonomous-optimization/phases/01-usage-index-v5-substrate/01-05-SUMMARY.md
  - .planning/workstreams/autonomous-optimization/phases/01-usage-index-v5-substrate/01-06-PLAN.md
  - .planning/workstreams/autonomous-optimization/phases/01-usage-index-v5-substrate/01-06-SUMMARY.md
  - tools/test_spawn_outcomes.py
  - tools/test_store_identity_consumers.py
  - tools/test_usage_index_identity.py
  - tools/test_usage_index_v5.py
  - tools/tis_observed.py
  - tools/usage_index.py
covered_digest: "v1:sha256:a6befd94d3177aaeb2796c9b26a61a3c01ae1920e9fffd543090852f57b63163"
behavior_unverified: 0
overrides_applied: 0
---

# Phase 1: usage_index v5 substrate -- Verification Report

**Phase Goal:** execution history is ingested once per content identity into queryable structured state.
**Verified:** 2026-10-06T21:58:00Z
**Status:** passed
**Plane:** gex44 (worktree ao-gen2; tools/ at cd905ef9, branch HEAD moved to 2c637b72 during verification with docs only)
**Re-verification:** No -- initial verification (no prior 01-VERIFICATION.md)

Written incrementally; each criterion's verdict is appended as it is checked.

## Criterion verdicts

### SC1 -- schema v5 (tool events, cwd, attribution, realpath + content identity); migration re-reads nothing: VERIFIED

- Code read: `tools/usage_index.py:79` `SCHEMA_VERSION = 5`; DDL lines 103-117 add `call_files`, `tool_events(tool, input_hash, path, result_bytes, ...)`, `user_hits`, `file_cwds`, `file_attribution(kind, name, role)`, `patterns`; `_V5_COLUMNS` (line 128-135) adds `files.resolved`, `store`, `project`, `session_key`, `content_id`, `dup_of`, `head_sha`, `tail_sha`, `v5_from`, `parse_errors`, `error`.
- `_migrate_v5` (line 223) is additive only: ALTER TABLE ADD COLUMN + meta stamp under BEGIN IMMEDIATE; no transcript open, no offset write. `SPAWN_SCHEMA = 4` decouples the spawn backfill from the version bump.
- Fresh run at HEAD cd905ef9: `python3 tools/test_usage_index_v5.py` exit 0, `USAGE_INDEX_V5_PASS=74/74`. Lines: `PASS V-UX5-SCHEMA ... schema_version=5`; `PASS V-UX5-TOOL-EVENT: rows=1 row=('Read', 'abb6d6e623ba2dbc', 49, 'C:/Users/User/Apps/proj/x.py', 3, 3, 0, 646)`; `PASS V-UX5-CWD`; `PASS V-UX5-IDENTITY-COLUMNS`; `PASS V-UX5-MIGRATE-ZERO-REREAD: opens under the fixture root=0 ... files_opened=0 bytes_read=0 upserted=0 ... snapshot equal=True`.
- The zero-reread gate is not vacuous: its open() spy patches builtins.open, io.open and os.open (test file lines 165-199), and two positive controls show it fires (`V-UX5-SPY-FIRES-ON-GROWTH: opened=['S2.jsonl'] bytes_read=323 appended=323`, `V-UX5-SPY-FIRES-ON-V1: files re-read=2/2`). Mutants M1 and M2 are killed by it in the fresh drill (below).
- Fresh drill: `python3 tools/test_usage_index_v5.py --drill` exit 0, `PASS DRILL-CONTROL unmutated run: 74/74`, `DRILL killed=21/21`, `PASS DRILL-CLEAN-AFTER-MUTANTS 74/74`; `git status` after the drill shows no source change (mutants restored).

### SC2 -- negative controls go red when they should: VERIFIED

Each control is a gate in the fresh 74/74 run, each has a positive control or a mutant that the fresh drill kills:

| control | gate line (fresh run) | red-capable proof |
|---|---|---|
| mixed-project session attributed to both | `PASS V-UX5-MIXED-BOTH: projects={'...alpha': {'home': 2}, '...beta': {'touched': 1}} mixed=True` | `V-UX5-MIXED-CONTROL` (single-project -> mixed=False); M13 KILLED |
| two distinct histories not merged | `PASS V-UX5-HISTORIES-NOT-MERGED: files rows=2, content_ids distinct=True, dup_of=[None, None]` | M8 (content id from head hash only) KILLED; `V-UX5-DUP-ORDER-INDEPENDENT` covers true duplicates |
| junction alias counted once | `PASS V-UX5-ALIAS-ONCE: files rows=2 (want 2), call_files rows/distinct keys=(2, 2)` | `V-UX5-ALIAS-DISTINCT`; M5 KILLED. Plane note: on Linux the alias is a symlink (Windows junction not reproducible here) |
| `_archived` handled by declared rule | `PASS V-UX5-ARCHIVED-RULE`, `V-UX5-ARCHIVED-INDEXED`, `V-UX5-V4-READERS-UNCHANGED` (with a control that sees a difference) | M6, M15 KILLED |
| parser failure surfaced, never a silent zero | `PASS V-UX5-PARSE-ERROR-SURFACED: files.parse_errors=2 ... valid calls still ingested=2/2`; `V-UX5-FILE-ERROR-TYPED`; `V-UX5-FILE-ERROR-ANY` (review WR-01) | M7, M20 KILLED; population turns such files into UNMEASURED reasons (`usage_index.py` population, "carry a file error") |
| empty population refuses a verdict | `PASS V-UX5-EMPTY-REFUSES ... cli exit=3 verdict=UNMEASURED` | `V-UX5-EMPTY-CONTROL` (one session -> MEASURED); M4 KILLED; also observed on the real index: `--project-filter '^no-such-project$'` -> exit 3, UNMEASURED ['no file in scope'], population None |

Review CR-01 (a non-ISO `--until` silently dropped to a full population) is closed: re-run on the real index, `--until 2026-09-01` -> exit 3, UNMEASURED, reason "until '2026-09-01' is not an ISO instant", population None; gate `V-UX5-POP-UNTIL-REFUSED`, mutant M19 KILLED.

### SC3 -- KME-L parity on the GEX44 copy, dedup reconciled to the unit: VERIFIED

- Re-run (this verifier, foreground): `python3 tools/usage_index.py population --db /home/kobii/ao-scratch/p1/cold.sqlite --project-filter 'KobiiCraft-Core-Files|kme-wt-arena2' --until 2026-10-03T16:13:37Z --select kme --host gex44 --expect KME-L --plane gex44` -> exit 0, `"verdict": "EXACT"`, `"deltas": {}`, population sessions_active 102 / dead 0 / calls 34,871 / cache_read 11,549,646,300; secondary input 69,846, cache_write 209,909,403, output 37,878,881 all match.
- The expectation is not self-supplied: `--expect KME-L` resolves through `_load_expected` to `DEFAULT_DENOM_FILE = vault/programs/incremental-cognition/denominators/kme_audit_2026-10-03.json`, whose only commit is `18e928af` (2026-10-03, P0 freeze), before the phase.
- Drift is reachable: same command with `--perturb calls=34872` -> exit 1, DRIFTED, deltas `{'calls': {... 'delta': -34872}}`.
- Reconcile to the unit, independently recounted by this verifier with a read-only SQL pass over `call_files` on the same DB (scope files 979, non-archived): 18 keys occur twice, shared only by sessions 867896c0 and 9184ed39, extra occurrences 18 and extra cache_read 5,515,928, dup_of rows in scope 0. This equals the reconcile block: occurrence 34,871 / 11,549,646,300 minus unique 34,853 / 11,544,130,372 = 18 / 5,515,928; `shared_outside` 0; `dup_files_in_scope` 0; `archived_excluded` 1 session / 649 calls / 271,001,260 cache_read named, not silently dropped.
- Build-time caveat found and closed by this verifier: `cold.sqlite` was built at 23:20 CEST, before the review-fix commit `6674ccc0` (23:48) that re-indented the per-file ingest (WR-01) and changed `_registry` (WR-02). So the recorded parity proves the query at HEAD, not the ingest at HEAD. Closed by rebuilding the KME-L scope with HEAD code: copied the 6 KME-L scope dirs (`*KobiiCraft-Core-Files*`, `*kme-wt-arena2`, 3,160,520,417 B) from `/home/kobii/kme-corpus/projects` to `/home/kobii/ao-verify-p1/projects`, then `python3 tools/usage_index.py refresh --all --db /home/kobii/ao-verify-p1/head.sqlite --proj /home/kobii/ao-verify-p1/projects --deadline 380` at HEAD 2c637b72 (tools/ identical to cd905ef9) -> status OK, files_opened 979, bytes_read 3,053,908,888, parse_errors 0, files_with_errors 0, wall_s 26.123. The same population command against `head.sqlite` -> exit 0, EXACT, deltas {}, 102 / 34,871 / 11,549,646,300, unique 34,853 / 11,544,130,372, shared_outside 0, dup 0. (archived_excluded is 0 there because the corpus-level `_archived` session was not in the copied dirs; the default rule excludes it either way, so the population is unchanged.)
- `/home/kobii/ao-scratch/p1/cold.sqlite` sha256 identical before and after this verifier's reads (`sha256sum -c` OK).

### SC4 -- refresh cost measured (wall, bytes) for a cold build and for a delta: VERIFIED

- Recorded (not re-run, per instruction: whole-corpus cold build is 2+ min / 10 GB): `vault/programs/incremental-cognition/gen2/evidence/O-cost-gex44.md` lines 23-30 and the raw CLI JSON in `/home/kobii/ao-scratch/p1/cold-pass1.json` agree: cold whole corpus files_opened 3,965, bytes_read 9,932,073,959, wall_s 128.069, rchar_delta 158,621,987,249, maxrss 89,760 kB; warm cold 118.661 s; no-op 0 files / 0 B / 0.577 s; 6-dir cold 979 / 3,053,908,888 B / 25.182 s; delta 5 appended files / 709,630 B / 0.07 s.
- Re-measured by this verifier at HEAD on its own copy (`/home/kobii/ao-verify-p1`): cold 979 files / 3,053,908,888 B / 26.123 s / rchar_delta 18,454,732,123 / maxrss 86,672 kB (agrees with the recorded 6-dir cold within 1 s); no-op `files_opened 0, bytes_read 0, calls_upserted 0, wall_s 0.023`; delta after appending 590,437 B to 3 transcripts -> `files_opened 3, bytes_read 590,437, bytes_ingested 590,437, wall_s 0.063, rchar_delta 88,973,425`. Delta bytes read equal the appended bytes exactly (difference 0).
- Counters are first-class outputs of `refresh` (`wall_s`, `bytes_read`, `files_opened`, CLI `proc.rchar_delta`, `proc.maxrss_kb`), so the cost is measurable on every run, not only in this phase.
- Recorded finding carried, not a gap of this criterion: rchar is 5-16x corpus bytes because of SQLite page reads (strace attribution in O-cost-gex44.md); v5 is 1.60x slower per byte than v4 with a 4.1x larger DB. The criterion asks for measurement, which exists; tuning is an opportunity candidate.

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP Phase 1 SC) | Status | Evidence |
|---|---|---|---|
| 1 | Schema v5: tool events, cwd, project/workstream attribution (mixed allowed), realpath + content identity; migration re-reads zero ingested files | VERIFIED | SC1 above; 74/74 fresh; zero-reread gate with firing spy controls; M1, M2 killed |
| 2 | Six negative controls go red when they should | VERIFIED | SC2 table; each gate has a positive control or a killed mutant (M4-M8, M13, M15, M19, M20) |
| 3 | KME-L parity 102 / 34,871 / 11,549,646,300 on GEX44, dedup reconciled to the unit | VERIFIED | EXACT on the recorded index AND on an index rebuilt at HEAD by this verifier; 18 / 5,515,928 recounted independently |
| 4 | Refresh cost (wall, bytes) measured for cold and delta | VERIFIED | recorded whole-corpus figures cross-checked against raw JSON; 6-dir cold, no-op and delta re-measured at HEAD |

**Score:** 4/4 truths verified (0 present, behavior-unverified). Behavior-dependent truths (zero-reread migration, crash/parallel refresh convergence) are exercised by passing named gates (`V-UX5-MIGRATE-ZERO-REREAD`, `V-UX5-CRASH-RESUME`, `V-UX5-STALE-SNAPSHOT-SKIPS`), each with a killed mutant.

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `tools/usage_index.py` | schema v5, `_migrate_v5`, `population`, `backfill_v5`, attribution | VERIFIED | 2,124 lines; exercised by 74 gates and the real CLI on the GEX44 corpus |
| `tools/tis_observed.py` | `resolved_path`, store identity | VERIFIED | `test_tis_observed.py` 25/25; called from usage_index lines 392, 1026, 1220 |
| `tools/test_usage_index_v5.py` | pillar gate + drill | VERIFIED | 74/74, drill killed=21/21, clean rerun 74/74 |
| `vault/programs/incremental-cognition/gen2/evidence/O-parity-gex44.md`, `O-cost-gex44.md`, `O-prg.md` | corpus evidence | VERIFIED | figures agree with raw scratch JSON and with this verifier's re-runs |
| frozen denominator `vault/programs/incremental-cognition/denominators/kme_audit_2026-10-03.json` | external expectation | VERIFIED | single commit 18e928af (P0 freeze), predates the phase |

### Key Link Verification

| From | To | Via | Status |
|---|---|---|---|
| `population --expect KME-L` CLI | frozen denominator | `_load_expected` -> `DEFAULT_DENOM_FILE` | WIRED |
| `population()` | champion classifier | `_kme_selector` loading `wiki/tools/kme_token_audit.py` by path | WIRED (EXACT depends on it; M16 killed) |
| `refresh` per-file ingest | `tis_observed.resolved_path` / store identity | `files.resolved`, alias dedup | WIRED (M5 killed) |
| IC gen2 ledger | pillar O closed | `test_incremental_cognition_program.py --generation 2 --status` | WIRED: `{"open": ["M","P","Q","R"], "closed": ["O"], "violations": []}`; `--selftest` PASS; `--audit` PASS frozen_sha256 a8ac15d8... |

### Behavioral Spot-Checks (all run fresh by this verifier, foreground)

| Behavior | Command | Result | Status |
|---|---|---|---|
| pillar gate | `python3 tools/test_usage_index_v5.py` | exit 0, 74/74 | PASS |
| mutation drill | `python3 tools/test_usage_index_v5.py --drill` | exit 0, killed=21/21, control and clean rerun 74/74 | PASS |
| parity, recorded index | population ... `--expect KME-L` on cold.sqlite | exit 0 EXACT | PASS |
| parity, index rebuilt at HEAD | refresh + population on `/home/kobii/ao-verify-p1/head.sqlite` | exit 0 EXACT | PASS |
| drift reachable | same + `--perturb calls=34872` | exit 1 DRIFTED | PASS |
| bad `--until` refused | `--until 2026-09-01` | exit 3 UNMEASURED | PASS |
| empty scope refused | `--project-filter '^no-such-project$'` | exit 3 UNMEASURED | PASS |
| v4/sibling consumers | test_usage_index 22/22, identity 11/11, store_identity_consumers 12/12, spawn_outcomes 24/24, tis_observed 25/25 | all exit 0 | PASS |

### Probe Execution

No probe scripts are declared by the phase plans; skipped.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| AOP-O | 01-01..06 | usage_index v5 substrate | SATISFIED | SC1-SC4 above; gen2 ledger closes O with no violations |
| AO-09 | 01-01..03 | KME-L measured (Phase 1 share: the measured denominator from the index) | SATISFIED for the Phase 1 share | EXACT parity at HEAD; challenger part belongs to Phase 2 |
| AO-03 | 01-01..06 | cheap always-on observation (Phase 1 share: incremental refresh with cost counters) | SATISFIED for the Phase 1 share | no-op 0 B / 0.023 s, delta reads exactly the appended bytes; detector part belongs to Phase 3 |

No orphaned requirement: REQUIREMENTS.md maps only AO-03 and AO-09 (plus pillar row AOP-O) to Phase 1.

### Anti-Patterns Found

Debt-marker scan (the four standard markers plus HACK) over `tools/usage_index.py`, `tools/tis_observed.py`, `tools/test_usage_index_v5.py`: none.

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `tools/usage_index.py` | 1840-1844 (review IN-04) | a session whose files all lack `first_ts` drops out under `--until` with no reason recorded | Warning | Measured exposure: 5 of 979 KME-L scope files (7 of 3,965 corpus-wide) have NULL `first_ts`; all 5 carry 0 calls and 0 cache_read, so parity is unaffected. Still a silent-drop path for a future population with timestamp-less files carrying calls. |
| `tools/usage_index.py` | 2101-2111 (IN-02) | `--perturb` ignored without `--expect` | Info | diagnostic only |
| `tools/usage_index.py` | 1968 (IN-03) | booleans accepted as expected ints | Info | no false EXACT on real records |
| `tools/usage_index.py` | 422-423 (IN-05) | skipped-shape census labels under `_archived/` as other | Info | census detail only |

### Human Verification Required

None for the phase's must-haves. Plane notes (informational, already carried by the Owner bundle `[O] (IC-gen2)`, not must-haves of this roadmap phase): the laptop v4 -> v5 migration of the real `~/.claude/state/usage_index/index.sqlite` is proven only on a v4-shaped fixture here (GEX44 has no v4 index), and `vault/programs/cognitive-economy/gates/gate_baseline.py` stays UNMEASURED on this plane. The junction-alias control runs with a Linux symlink, not a Windows junction.

### Gaps Summary

No gap blocks the phase goal. Every ROADMAP Phase 1 criterion was re-derived from code and fresh runs, not from SUMMARY text. One discrepancy in the recorded evidence was found and closed: the parity index predates the review-fix commit, so this verifier rebuilt the KME-L scope at HEAD and re-obtained EXACT. Inherited reds named in 01-EVIDENCE.md (estate_shadow 10/11, frontier_intelligence_os, token_ground_truth_junction crash, liveness reachability exit 1 over `modules/` only) were not re-run and are outside this phase's criteria. Verifier side effects: created `/home/kobii/ao-verify-p1/` (a 3.16 GB copy of the KME-L scope dirs, an index, and JSON outputs; appended 590,437 B to three copied transcripts for the delta run). The original corpus and `/home/kobii/ao-scratch/p1/` were only read. That directory can be removed by the caller.

---

_Verified: 2026-10-06T21:58:00Z_
_Verifier: Claude (gsd-verifier)_
