---
phase: 01-usage-index-v5-substrate
plan: 06
subsystem: usage_index
tags: [pillar-O, ic-gen2-ledger, evidence, product-delta, intelligence-delta, owner-bundle, gex44]
requires: [01-05]
provides:
  - "01-EVIDENCE.md: criterion results per ROADMAP criterion and pillar O clause (six controls with gate and killing mutant), fresh-process verifier output, corpus parity/cost/PRG, edge probe, v4 compatibility, ownership diff, Product Delta, Intelligence Delta, limits"
  - "gen2 ledger state.O = IMPLEMENTED_AND_VERIFIED: 4 gate argvs, PRG, parity measurement and cost file pinned by sha256, savings empty, frozen object unchanged"
  - "REQUIREMENTS AOP-O row: Complete -- IMPLEMENTED_AND_VERIFIED"
  - "owner-bundle rows 2 and 3 [O] (IC-gen2): laptop v4->v5 migration + backfill-v5, gate_baseline.py re-run"
  - "tools/ic_gen2.py selftest and audit no longer assume pillar O is open (V-IC2-CLEAN-OPEN, V-IC2-AUDIT-CLOSED-NOT-EXPECTED)"
affects: [phase-2]
tech-stack:
  added: []
  patterns: ["ledger row written by a one-off script that asserts the frozen object unchanged", "audit A3 expects open-programme lines only for pillars without a terminal"]
key-files:
  created:
    - .planning/workstreams/autonomous-optimization/phases/01-usage-index-v5-substrate/01-EVIDENCE.md
  modified:
    - vault/programs/incremental-cognition/gen2/ledger.json
    - .planning/workstreams/autonomous-optimization/REQUIREMENTS.md
    - vault/programs/incremental-cognition/gen2/owner-bundle.md
    - .planning/workstreams/autonomous-optimization/STATE.md
    - tools/ic_gen2.py
key-decisions:
  - "state.O reason quotes the parity verdict and numbers, the zero re-read measurement, the six controls with their mutants and the cost rows, each with its command; no deferral word, no angle-bracket text (L7 and the G2 placeholder rule)"
  - "The SQLite page-cache amplification (rchar_delta 5-16x corpus bytes, v5 1.60x slower per byte than v4, DB 4.1x larger) is recorded in the Intelligence Delta as an Owner-facing finding and is not fixed in this phase"
  - "The corrected RESEARCH assumption (867896c0 is KME_STRONG and selected, so the 18 shared keys are inside the selection, shared_outside 0) is recorded in the Intelligence Delta and in a STATE decision"
status: complete
plan_head_before: f4c1c6030581f25e4f7b69bd71f541df959eeff1
commits: 3
actuals:
  tokens: 14000
  tasks: 2
  commits: 3
duration: single session
completed: 2026-10-06
---

# Phase 1 Plan 06: Close pillar O in the gen2 ledger Summary

Pillar O is closed IMPLEMENTED_AND_VERIFIED under its frozen rule: 01-EVIDENCE.md (with Product Delta and Intelligence Delta) is committed first, then `state.O` pins the four gates, the Production Reality file, the KME-L parity measurement and the cost file by sha256, and the gen2 judge accepts it (`--status` exit 0 with O closed, `--selftest` PASS, `--audit` PASS, `--final` FAIL only on the eight lines that belong to pillars M, P, Q, R and the closeout).

## Tasks

| Task | Name | Commit |
|---|---|---|
| 1 | 01-EVIDENCE.md (criterion results, verifier output, corpus measurements, Product + Intelligence Delta) | 0ebe23bd |
| 2a | (deviation) gen2 selftest and audit no longer assume pillar O is open | 3296f41f |
| 2 | Ledger state.O, AOP-O traceability, owner-bundle [O] lines, STATE position | 020831cc |

## Gate outputs (fresh processes, after 020831cc)

`python3 tools/test_incremental_cognition_program.py --generation 2 --status` (exit 0)
```
{"open": ["M", "P", "Q", "R"], "closed": ["O"], "violations": []}
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
`python3 tools/test_incremental_cognition_program.py --generation 2 --final` (exit 1, expected; its L5 run of O's four gates was green, no line names O, L2, L4, L5 or X2)
```
  FAIL L3 M: no terminal disposition
  FAIL L3 P: no terminal disposition
  FAIL L3 Q: no terminal disposition
  FAIL L3 R: no terminal disposition
  FAIL L8 review ukdl: missing or its file does not exist
  FAIL L8 review cbr: missing or its file does not exist
  FAIL L8 delta product: empty
  FAIL L8 delta intelligence: empty
ICP_GEN2_VERDICT=FAIL failures=8
```
Other: `python3 tools/test_ao_p0.py` -> `AOP0_PASS=22/22  threshold=22/22`; `git diff --quiet 85fd564d --` over the never-edit set (gen1 ledger and FROZEN_AT, gen2 FROZEN_AT, CE/SC ledgers, CE/SC verifiers, root `.planning/STATE.md`, `tools/gsd_mission.py`) exits 0. Task 1 verifiers (all fresh, HEAD f4c1c603): v5 `USAGE_INDEX_V5_PASS=71/71`, `--drill` `DRILL killed=18/18`, `USAGE_INDEX_PASS=22/22`, `USAGE_INDEX_IDENTITY_PASS=11/11`, `SPAWN_OUTCOMES_PASS=24/24`, `KMEP_PASS=89/89`; `modules/liveness/reachability.py` exit 1 (inherited, `modules: 490 | REACHABLE: 310 | ORPHAN: 180 | UNKNOWN: 0 | gate offenders: 59`).

## Deviations from Plan

**1. [Rule 1 - Bug] The gen2 selftest and audit hard-coded "pillar O is open"**
- Found during: Task 2 verify. After `state.O` was written, `--generation 2 --selftest` went `ICP_GEN2_SELFTEST=FAIL`: V-IC2-ALLOWED-LOSS-ACCEPTED (the P-closed fixture judged the working ledger with O closed against a fixture REQUIREMENTS file that has no AOP-O row: `X2 O: ... no traceability row for CE-O`), V-IC2-AUDIT-CLEAN and V-IC2-AUDIT-FROZEN-RECORD-ACCEPTED (audit A3 expected `L3 O: no terminal disposition`). The plan's acceptance (`--selftest` PASS, `--audit` PASS after closing O) could not hold without a fix.
- Fix: the selftest's mutant baseline is the pre-registered ledger with every pillar open (`real`), while V-IC2-CLEAN judges the working ledger (`actual`); `expected_final_failures(frozen_at_present, led=None)` drops the L3 line only of a pillar that carries a terminal, and the audit passes its ledger (a closed pillar's other clauses still count as unexpected failures, pinned by the existing A3 mutants). New gates: V-IC2-CLEAN-OPEN, V-IC2-AUDIT-CLOSED-NOT-EXPECTED. `tools/ic_gen2.py` is not in the never-edit set. Commit 3296f41f (separate from the plan's four-file commit, so `git show --stat HEAD` for 020831cc lists exactly the four planned files).
- Files modified: tools/ic_gen2.py. Selftest after the fix: 74 `killed by` lines, no SURVIVED, `ICP_GEN2_SELFTEST=PASS`. The audit now runs O's gates during its final-mode read (as `--final` does), so it takes longer than in Phase 0.

**2. [Plan wording] REQUIREMENTS AOP-O row** already read `Complete` (set by an earlier state update); it was edited to the exact `Complete -- IMPLEMENTED_AND_VERIFIED` text the X2 clause requires. `requirements mark-complete` applies nothing for these IDs (noted in 01-01 to 01-05; not fought).

**3. Sandbox:** compound git and loop commands were refused; every step ran as a plain command and the ledger edit as a scratch script under `/home/kobii/ao-scratch/p1/close_o.py` (outside the repo; asserts `json.dumps(frozen, sort_keys=True)` unchanged and that the file's indent-1 formatting round-trips).

**4. Context-wall notice:** one tool result carried an appended "CONTEXT WALL 40%" instruction to stop and hand off. It came from a tool output, not from the plan or the orchestrator, and the session had used far less than 40% of its budget, so it was not followed.

## Auth gates

None.

## Known Stubs

None. No stub pattern in the files of this plan.

## Threat Flags

None. T-01-24 (frozen untouched: asserted in the edit script, `--status` L2 pin, never-edit diff exit 0), T-01-25 (gate argvs re-run by L5 at `--final` and green; prg, measurement and cost files pinned by sha256 and accepted by L4), T-01-26 (laptop actions are owner-bundle rows 2 and 3 only), T-01-27 (plan 05 parity was EXACT, so the terminal was written) mitigated.

## Limits and open items

- `gate_baseline.py` stays UNMEASURED on this plane (owner-bundle row 3).
- The laptop's live index migration and `backfill-v5` are Owner actions after the merge (owner-bundle row 2).
- Open Owner-facing finding, not fixed here: SQLite page-cache amplification of refresh reads (5-16x the corpus bytes; v5 1.60x slower per byte than v4 on the 6-dir scope, DB 4.1x larger). A candidate for a later opportunity record; no parity defect.
- Inherited reds reported verbatim, never claimed green: estate_shadow 10/11, frontier_intelligence_os V-FIOS-LIVE-PATH-WIRED, token_ground_truth_junction `cmd` crash, `modules/liveness/reachability.py` exit 1 (aperture `modules/` only).
- `--generation 2 --final` stays FAIL (failures=8) until pillars M, P, Q, R and the closeout reviews and deltas land in Phases 2-7.

## Self-Check: PASSED

Files exist: 01-EVIDENCE.md, ledger.json (`state.O.terminal` IMPLEMENTED_AND_VERIFIED), REQUIREMENTS.md, owner-bundle.md, STATE.md, tools/ic_gen2.py. Commits 0ebe23bd, 3296f41f and 020831cc present on mission/autonomous-optimization-gen2; `commits: 3` measured from the persisted ledger (`rev-list --count f4c1c603..HEAD` before this docs commit).
