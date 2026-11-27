---
phase: 05-critical-path-audit
verified: 2026-11-23T14:00:00Z
status: passed
verdict: passed_with_unknowns  # GSD routes only passed|gaps_found|human_needed; unknowns below stay open
score: 3/3 roadmap success criteria verified on GEX44 (every wall-time statement, the laptop registry and the real-laptop boundary run UNJUDGED)
verified_head: 14090473
behavior_unverified: 0
gaps: []
unknowns:
  - "LAPTOP-ONLY: no wall time of any real hook chain was measured on any plane. Nothing here says a hook is slow or fast, or that deferring the four candidates would shorten a Stop turn. The 54.9 s Stop-chain figure in dispatcher comments is a claim from a comment and stays unmeasured. LP-10 is the only path to it and is UNJUDGED"
  - "LAPTOP-ONLY: which events the laptop ~/.claude/settings.json registers, and whether SessionEnd calls the dispatcher, were never seen by this phase. The guard sees the repo dispatcher registry only (the tool prints `settings layer: UNKNOWN (LAPTOP-ONLY, LP-09)`). LP-09 UNJUDGED"
  - "LAPTOP-ONLY: the A/B judge was exercised by me on synthetic samples with an invented laptop host name. It is behaviour-pinned on fixtures, not on a laptop collection. The minimum of 7 MEASURED samples per arm and the A/A noise rule are PROPOSED and uncalibrated. The judge checks the recorded host name and a LIVE_DISPATCHER scope label, not the sample `os` key; a hand-forged laptop-named file would be judged. LP-10, LP-11 UNJUDGED"
  - "SC2 is met by the empty change: Phase 5 moved nothing, so 'any change moves only DEFERRABLE work' holds vacuously and the boundary suite 'after' run is a control for 'no registration change', not a before/after of a move. The guard is the instrument that would police a future move; I falsified it with planted mutants. The four DEFERRABLE rows were NOT moved and the guard does not enforce that the four move together (all-or-none is a documented precondition, not a check)"
  - "51 of 113 registry entries (45 percent) stay UNKNOWN, including entries whose names read like gates (process-sandbox, ovo-push-gate, graph_first_gate, uqf_pre_edit_gate). UNKNOWN is a permitted class in the criterion and is never treated as movable. It is the conservative outcome, but the third class is large and its residue needs evidence the repo does not hold. Owner decision (10) stands"
  - "The boundary suite was green on both recorded runs under an isolated HOME. Gate V-HOOK-TRIGGER-REGISTERED needs a real settings.json to evaluate its duplicate-invocation sub-check; the real-HOME run is LP-12, LAPTOP-ONLY. (My own run under this host's real HOME was 7/7 and reported a double invocation of cdio_visual_advisory.js on GEX44's settings plus dispatcher; that is a GEX44 observation, REPORTED not failed, and says nothing about the laptop)"
  - "Pre-existing, unchanged by name and not claimed fixed: 56 reachability offenders, tools/test_git_invocation.py 6/7. tools/test_s9_redteam.py was not re-run (814 s) and its Phase 4 caveat stands"
human_verification: []
---

# Phase 5: Critical-path audit - Verification Report

**Phase goal:** Name what runs synchronously while the user waits and what could move.
**Plane:** GEX44 (kobicraft-gex44, Linux, Python 3.12.3, node v18, stdlib only). Every number below was observed by me on this host in this session. The laptop was not measured and nothing here is a laptop result.
**Re-verification:** No, initial verification. HEAD 14090473 (plans 05-01, 05-02, 05-03 merged).
**Status: passed_with_unknowns.** The three roadmap success criteria are met on evidence I re-observed. Nothing failed. The unknowns above are not counted as passes.

Method: re-ran the phase suite, the classifier, the guard against the recorded baseline, the boundary suite and the cheap earlier gates; counted the dispatcher registry myself with a separate node script (not the phase tool); fed the guard five mutated snapshots of my own and a control; drove the pure A/B judge with synthetic samples across ten decision branches; re-ran the sampler with a decoy dispatcher; diffed `hooks/` against the base. SUMMARY.md and 05-EVIDENCE.md were used only to know where to look. Scratch files were written to /tmp only.

## Observable Truths (ROADMAP Phase 5 success criteria)

| # | Truth | Status | Evidence (re-observed) |
|---|-------|--------|------------------------|
| 1 | Inventory of hooks per event from the repo's hook registry, each classed BLOCKING-SAFETY / DEFERRABLE / UNKNOWN | VERIFIED (GEX44; the laptop settings layer is LAPTOP-ONLY, LP-09) | `python3 -I tools/hook_critical_path_audit.py classify` exits 0, prints `VIOLATIONS (0)` and a named `RESIDUAL UNKNOWN (51, named)` list, with per-container class and basis counts. My independent count (a node script that evals the `EVENT_MAP` and `CHAIN_MAP` literals of `hooks/hook-dispatcher.js`, not the phase loader): 20 containers, 113 entries, Stop-chain 27, SessionEnd-chain 5, PreToolUse-Bash-chain 15, PostToolUse-Bash-chain 4, and the same per-container counts as the evidence file. The class table `vault/config/hook-critical-path-classes.json` holds exactly four DEFERRABLE rows, all `DEF_ACCOUNTING_DUP`, each citing a line range. I spot-read the citations: `hooks/hook-dispatcher.js:411-414` lists ads_sync, session_writeback, trace-flusher and session_delta_stop in SessionEnd-chain; `hooks/trace-flusher.js:237-244` posts and unlinks; `hooks/session_delta_stop.js:1-8` writes the learnings file; `tools/ads_sync.py:98-101` and `modules/graphify/session_writeback.py:226-229` match. The dispatcher's own comment (`hooks/hook-dispatcher.js:380-405`) confirms the stated precondition (Owner wires SessionEnd, delete the standalone sentinel, only then retire the four Stop-chain duplicates, all-or-none). UNKNOWN is a closed, named, never-moved class, not a pass. |
| 2 | Any change moves only DEFERRABLE work and keeps `tools/test_hook_boundary.py` green | VERIFIED (vacuously for the move, falsified for the guard; see unknowns) | Zero change was made: `git diff --stat 4fa606d7 -- hooks/` is empty (exit 0), and `git diff --name-only 0a94118a..HEAD` outside `.planning/` lists only `tools/bench_all.py`, `tools/hook_critical_path_audit.py`, `tools/resource_admission.py`, `tools/test_bench_gate.py`, `tools/test_bench_integrity.py`, `tools/test_hook_critical_path.py`, `tools/test_resource_pressure.py`, `vault/config/hook-critical-path-classes.json`, `vault/config/resource-floors.json`. No `hooks/`, no `tools/test_hook_boundary.py`, no `settings.json` in the phase commits. `python3 tools/test_hook_boundary.py` (my run, this host's real HOME): `HOOK_PASS=7/7 threshold=7/7`, exit 0. The recorded before/after under an isolated HOME (`records/05-02-boundary-compare.txt`) says `VERDICT: PASS - before green and every gate line identical`. The guard is the instrument that polices a future move. `guard --baseline records/05-01-inventory-baseline.json` on the live dispatcher: `moved=0 added=0 violations=0`, rc 0. My own mutants on a snapshot of the live inventory: remove `closer-guard.js` (block and critical) from Stop-chain gives `MOVED_NON_DEFERRABLE`, rc 1; flip `block` true to false on a PreToolUse-Bash entry gives `FLAG_WEAKENED`, rc 1; add a 5000 ms deadline to Stop-chain gives `DEADLINE_ON_BLOCKING_CHAIN`, rc 1; remove `trace-flusher.js` from both Stop-chain and SessionEnd-chain gives `DROPPED_WORK` and `MOVED_NON_DEFERRABLE`, rc 1; control, remove `trace-flusher.js` from Stop-chain only (SessionEnd twin kept): `moved=1 violations=0`, rc 0. So the guard answers yes and no. `python3 tools/test_hook_critical_path.py`: `CRITPATH_PASS=134/134 threshold=134/134`, exit 0 (34 s). Limits of the guard: it does not require the four deferrables to move together and cannot see the laptop settings.json. |
| 3 | A laptop measurement procedure (before/after, host-state matched) is written and marked LAPTOP-ONLY / UNJUDGED | VERIFIED (a written procedure, not a measurement) | `05-EVIDENCE.md` section 7 holds LP-09 (enumerate the real registry), LP-10 (A, A-replicate, then B Stop-chain wall, host-state matched via the schema-2 host bucket), LP-11 (durability and work-preserved), LP-12 (boundary with the real HOME). Each carries a command, a sample-size rule, a falsifier and a record to bring back, each is headed LAPTOP-ONLY / UNJUDGED, and no laptop number appears. I executed the shape of the named commands: `collect --arm A`, `--arm A_REPLICATE`, `--arm B --out` all run (decoy dispatcher, `SHAPE_ONLY`), `ab-judge --samples ... --laptop-host ... [--work-preserved]` exists with those flags, `tools/measure_hook_event.py --event` exists. A decoy collector file is refused by the judge on its scope (`REFUSED: samples file scope is 'SHAPE_ONLY'`, rc 2) and a GEX44 host name is refused (`host 'kobicraft-gex44' is the GEX44 host`, rc 2). My synthetic drive of the pure `ab_verdict` (fabricated host `lap-1`, 8 samples per arm, A/A spread about 3 ms): B 500 against A 1000 gives `B_FASTER`; B 1001 gives `NO_DIFFERENCE_DETECTED`; B 1500 gives `B_SLOWER`; `work_preserved False` gives `UNKNOWN WORK_NOT_SHOWN_PRESERVED`; required host the GEX44 name gives `UNKNOWN`; B samples recorded on the GEX44 host give `PLANE_MISMATCH`; 3 samples in B give `INSUFFICIENT_SAMPLES`; B all RED gives `HOST_PRESSURE`; B plus three TIMED_OUT gives `CENSORING_ASYMMETRY`; no A_REPLICATE gives `NO_AA_CONTROL`. The judge can say no and unknown, not only faster. The result of the procedure is NOT_SHOWN until the laptop returns the named records. |

**Score:** 3/3 criteria verified; 0 present-but-behavior-unverified truths. The behavior-dependent claims (guard rejects a dropped blocking hook, judge refuses a wrong plane) each have a behavioural pole I drove myself.

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tools/hook_critical_path_audit.py` | inventory, classify, guard, ab-judge, collect | VERIFIED | five subcommands in `--help`; stdlib only; each run above |
| `tools/test_hook_critical_path.py` | V-CRIT suite with mutants and controls | VERIFIED | 134/134 re-run, exit 0 |
| `vault/config/hook-critical-path-classes.json` | class table with evidence and basis | VERIFIED | four DEFERRABLE rows with outputs, durability notes and cited lines that resolve |
| `phases/05-critical-path-audit/records/05-01-inventory-baseline.json` | baseline for the guard | VERIFIED | 113 entries; the guard accepts the live dispatcher against it |
| `phases/05-critical-path-audit/compare_runs.py` | boundary before/after comparison | VERIFIED | its recorded verdict is on file; I re-ran the suite it wraps, not the wrapper |
| `05-DEFERRAL-CANDIDATES.md` | list, nothing applied | VERIFIED | four candidates, status CANDIDATE - NOT APPLIED, preconditions, falsifiers, reversal positions |
| `05-EVIDENCE.md`, `records/` | commands, exit codes, plane labels | VERIFIED | 15 record files; numbers I re-ran match |

## Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| `classify` | `hooks/hook-dispatcher.js` registry | node child with in-memory append wrapper under an empty temp HOME | WIRED (113 entries equal my own count) |
| `guard` | baseline snapshot, class table | `--baseline`, default table | WIRED (five mutants and a control) |
| `ab-judge` | `bench_all` host pressure and bucket, percentile owner | by-path owner loads (`OWNER_ERROR` guard, `BlockedError`) | WIRED (pressure, bucket and percentile branches fired in my drive) |
| `collect` | per-sample fresh HOME, list argv, timeout kill | `sample_once` | WIRED (decoy run; suite gates for isolation and kill pass) |
| Phase 5 | `hooks/` | none | NOT TOUCHED by design (D5-01), empty diff |

## Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Real data | Status |
|----------|---------------|--------|-----------|--------|
| classify per-container counts | registry entries | the live `hooks/hook-dispatcher.js` literals | yes (113, reproduced by an independent parse) | FLOWING |
| guard current snapshot | live inventory | same loader | yes (live run `current=live dispatcher`) | FLOWING |
| collector sample host_state | `bench_all.read_host_state` schema 2 | live host reading | yes (fields present on every sample; no timing printed) | FLOWING |
| judge timing statistics | collector samples | laptop file only | none on GEX44 by design | NOT EXERCISED ON A REAL TIMING (LAPTOP-ONLY) |

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Phase suite | `python3 tools/test_hook_critical_path.py` | `CRITPATH_PASS=134/134`, exit 0 | PASS |
| Classify | `python3 -I tools/hook_critical_path_audit.py classify` | exit 0, violations 0, 51 named residual | PASS |
| Guard vs baseline | `... guard --baseline records/05-01-inventory-baseline.json` | `moved=0 added=0 violations=0`, rc 0 | PASS |
| Guard mutants (mine) | five snapshots, see truth 2 | rc 1, 1, 1, 1 and a control rc 0, codes as named | PASS |
| Boundary suite | `python3 tools/test_hook_boundary.py` | `HOOK_PASS=7/7`, exit 0 | PASS |
| Judge branches (mine) | pure `ab_verdict`, 10 cases | all as expected | PASS |
| Sampler shape smoke | `collect ... --arm A / A_REPLICATE / B` with a decoy | `scope: SHAPE_ONLY`, states MEASURED, no timing, judge refuses rc 2 | PASS |
| Bench integrity / gate / pressure | `test_bench_integrity` 53/53, `test_bench_gate` 24/24, `test_resource_pressure` 17/17 | exit 0 | PASS |
| hooks unchanged | `git diff --stat 4fa606d7 -- hooks/` | empty | PASS |
| Reachability | `python3 modules/liveness/reachability.py --json` | rc 1, 56 offenders, set equal by name to `records/05-01-reach-pre.txt` (0 new, 0 gone), no phase tool among them | PASS (unchanged; debt pre-existing) |
| Privacy | grep of `/home/kobii` and a Windows user path over the tool, table, phase markdown and record bodies | empty (header lines excluded) | PASS |

## Probe Execution

No phase-declared `probe-*.sh`. SKIPPED. The red records, planted-mutant suites and my own mutants stand in as falsification evidence.

## Requirements Coverage

| Requirement | Source | Description | Status | Evidence |
|-------------|--------|-------------|--------|----------|
| PERF-05 | 05-01, 05-02, 05-03 | critical-path inventory; only DEFERRABLE work moved; laptop procedure written | SATISFIED on GEX44 (inventory, guard, procedure); "only DEFERRABLE work moved" holds because nothing moved | truths 1-3; laptop items UNJUDGED |

No orphaned requirement IDs mapped to Phase 5.

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| phase code and docs | - | TBD / FIXME / XXX / TODO / HACK grep | none | empty |
| `records/05-03-final-gates.txt` | header | records `head: aa124969`; the evidence file cites HEAD `ae6fd9d9` for the same run | Info | recorded provenance is off by a few commits; I re-ran the suite and cheap gates at HEAD 14090473 and they match, so no claim rests on it |
| `tools/hook_critical_path_audit.py` | 629-633, 754-772 | host and scope labels are read from the sample file, not the sample `os` key | Warning | a forged laptop-named file would be judged; recorded as an unknown, not a defect for the stated use |

## Human Verification Required

None blocking on this host. LP-09 to LP-12 are laptop items listed as unknowns, not items awaiting a human here.

## Gaps Summary

No gaps. The phase delivers an inventory with a named residual, a class table, a guard whose both poles I falsified, a boundary comparison, a deferral ledger that applies nothing, and a host-matched laptop procedure with a judge that refuses the wrong plane. What it does not deliver, and says so: any wall time, the laptop settings layer, a calibrated sample size, a move of the four DEFERRABLE entries, and classification of the 51 UNKNOWN entries.

---

_Verified: 2026-11-23_
_Verifier: Claude (gsd-verifier)_
