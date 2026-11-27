Creation speed on the laptop: UNKNOWN
# Hand-back: perf-construction campaign (Phase 6, PERF-06)

Written unattended on 2026-11-23 on GEX44 (Linux, Python 3.12, stdlib only). The counts in this file are not typed from memory: the INVENTORY line in section 4 is recomputed from the phase files by `.planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/handoff_check.py`, and the check fails when one of them drifts. Every path is repo-relative.

## 1. Owner summary
What you can rely on, and what you cannot:
1. All five phases (1 to 5) closed `passed_with_unknowns`; none is clean. Phase 6 adds this hand-back and changes none of that.
2. Built and proven on GEX44 only: a benchmark runner that cannot hide a failed sample and compares only against host-matched history (Phases 2 and 4).
3. A timing contract for creation with censoring and an instrument-fail state; its definitions are PROPOSED, not yours, and its time-to-verify is a proxy (Phase 3).
4. A host pressure reader whose process-count refusal exists and is tested, but no launch path calls it yet (Phase 4).
5. A critical-path audit and no-change guard over the hook registry; it moved nothing, so no hook was made faster or slower (Phase 5).
6. NOT shown: anything about the laptop, any wall time of a real hook chain, and any change in how long creation takes. There are 12 laptop-only items, every one UNJUDGED; zero are laptop-judged.
7. Inheritance (matrix in `.planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/06-INHERITANCE.md`): the Phase 2 and Phase 4 proofs are "inherited by a standing gate"; the Phase 3 and Phase 5 proofs are "inherited only by a command someone must run" (the map's own words), so if those two are broken no standing gate fails.
8. Ratchet: CONNECTED_SCRATCH, live BLOCKED. Four of five proposed entries are promotable under an Owner authority; nothing live was written.
9. UKDL: five candidates in an append-only file, one new rule and four pointers to existing owners; none promoted into any aggregate.
10. There are 13 Owner decisions, each with the safe, reversible pick taken unattended; they are listed next.

Owner decisions needed (the pick taken is the safest one and can be reversed):
- (1) `tools/verify_bench_all.py` exits 0 for an in-band absolute-target miss and only prints a note. Pick: keep. Reverse: make it fail.
- (2) Should a vgate suite exiting 1 count as an instrument error? Pick: failure count only.
- (3) The claude process ceiling is PROPOSED_UNCALIBRATED (GEX44 probes only). Pick: keep it. Reverse: one value in `vault/config/resource-floors.json`.
- (4) The count refusal is not passed by any launch path. Pick: leave unwired until laptop evidence (LP-07, LP-08) exists.
- (5) A host with UNKNOWN pressure counts like RED for regression (INCONCLUSIVE). Pick: yes, never judge an unmeasured host.
- (6) The host schema bump restarts the regression windows (first runs print UNJUDGED). Pick: accept.
- (7) `tools/verify_bench_all.py` stays unedited and does not read host pressure. Pick: leave.
- (8) Phase 5 makes no hook registration or dispatcher change. Pick: change nothing.
- (9) Five accounting hooks in the Stop chain are duplicated by the SessionEnd chain. Pick: leave them in the Stop chain (SessionEnd is per session, and what the laptop registers is UNKNOWN, LP-09).
- (10) Hook classification is conservative (UNKNOWN until evidence) and the minimum samples per arm are PROPOSED. Pick: accept.
- (11) Wire the Phase 3 and Phase 5 suites into a standing gate? Pick: no. The `bench-gate` row has a 30 s budget; measured suite costs disagree between sessions (planning about 10 s and about 34 s, this phase about 3 s and about 10 s, one run each), so fit is unsettled. Reverse: add a SUITE-WIRED gate with a negative control, as Phases 2 and 4 did.
- (12) Create the `perf_construction` family and a live baseline generation B0? Pick: no. Steps for the Owner: `vault/tower/candidates/perf_construction.md`, section "To promote (Owner)".
- (13) Promote the UKDL candidates into the aggregates? Pick: no. They stay in `vault/knowledge_base/candidates/perf-construction-20261123.md`.

## 2. Engineering handoff
Owners (this campaign connected to them, it did not redefine them):

| Owner | Role | Gate and expected marker |
|-------|------|--------------------------|
| `tools/bench_all.py` | benchmark runner, host-matched regression, failed samples stay in | `tools/test_bench_integrity.py` marker `BENCHINT_PASS=53/53`; `tools/test_bench_gate.py` marker `BENCH_GATE_PASS=24/24` |
| `tools/resource_admission.py` | host pressure reader and classifier | `tools/test_resource_pressure.py` marker `PRESSURE_PASS=17/17` |
| `modules/capability_runtime/construction_metrology.py` | creation timing contract, censoring | `tools/test_construction_metrology.py` marker `METRO_PASS=38/38` |
| `tools/hook_critical_path_audit.py` | hook registry audit, guard, A/B judge | `tools/test_hook_critical_path.py` (run with `-I`) marker `CRITPATH_PASS=134/134` |
| `modules/tower/ratchet.py` | baseline ratchet owner (Phase 1) | `ratchet_connect.py selftest` marker `RATCHET_SELFTEST=12/12` |

Re-run block (the manifest of plan 06-01; it runs every standing gate of Phases 2 to 5 against its recorded count, with a closed verdict set, and never counts a skipped row as passed):

```
python3 -I .planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/inherit_check.py manifest
```

Phase 6 instruments, all in `.planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/` (phase-local, stdlib, registered nowhere): `inherit_check.py` (manifest and mutant matrix), `ratchet_connect.py` and `ratchet-entries.json` (the five proposed entries through the real ratchet owner on a scratch root), `ukdl_candidate_check.py`, `handoff_check.py` (this file's check). Their records are in `.planning/workstreams/perf-construction/phases/06-ratchet-ukdl-and-hand-back/records/`.

What changed since the mission base, from `git diff --stat a0e12830 HEAD -- tools modules vault hooks`: 18 paths, hooks unchanged. Tools: `tools/bench_all.py`, `tools/resource_admission.py`, `tools/verify_bench_all.py`, `tools/test_bench_gate.py`, `tools/test_bench_integrity.py`, `tools/test_resource_pressure.py`, `tools/construction_metrology_report.py`, `tools/test_construction_metrology.py`, `tools/hook_critical_path_audit.py`, `tools/test_hook_critical_path.py`. Modules: `modules/capability_runtime/agent_resolver.py` (policy id, three lines) and `modules/capability_runtime/construction_metrology.py`. Vault: `vault/config/hook-critical-path-classes.json`, `vault/config/resource-floors.json`, `vault/liveness/reachability_registry.json`, `vault/specs/construction-metrology-contract.md`, and the two candidate files `vault/tower/candidates/perf_construction.md` and `vault/knowledge_base/candidates/perf-construction-20261123.md`. `hooks/` shows an empty diff against the mission base and against `4fa606d7`. The whole branch is 179 files changed against the mission base, counted at the head stated in the INVENTORY line (before the Phase 6 close commit), mostly planning records.

Pre-existing debt, unchanged by name and not claimed fixed: 56 reachability offenders (`modules/liveness/reachability.py`), `tools/test_git_invocation.py` at 6 of 7, and `tools/test_s9_redteam.py` at 111 of 114, which is UNJUDGED (814 s, not run unattended, no clean control run exists).

The metrology unit: its row in `vault/liveness/reachability_registry.json` is class DORMANT. Phase 5 does consume it by code: `tools/hook_critical_path_audit.py:58` imports `CENSORED_STATES` and `STATES` from it. The Phase 5 final reachability record still lists the unit as ORPHAN with class DORMANT, so the reachability tool does not count that import as reaching it; nobody edited the row.

## 3. Laptop-only checklist
Each row is LAPTOP-ONLY and UNJUDGED. The record column names a file that does not exist yet (NEW:); if one already exists in the tree the check fails and this file must be revised. No GEX44 number may fill a laptop slot, and every laptop record must begin with the output's own host and os keys.

| LP | Status | Laptop value | Procedure (source) | Record to bring back | Falsifier |
|----|--------|--------------|--------------------|----------------------|-----------|
| LP-01 | LAPTOP-ONLY / UNJUDGED | UNJUDGED | `.planning/workstreams/perf-construction/phases/01-reality-and-ownership/01-EVIDENCE.md:176` | `NEW:.planning/workstreams/perf-construction/phases/01-reality-and-ownership/LP-01-laptop-revival-probe.txt` | free memory and process count stay healthy through a revival |
| LP-02 | LAPTOP-ONLY / UNJUDGED | UNJUDGED | `.planning/workstreams/perf-construction/phases/01-reality-and-ownership/01-EVIDENCE.md:178` | `NEW:.planning/workstreams/perf-construction/phases/01-reality-and-ownership/LP-02-laptop-file-hash.txt` | any length or digest difference |
| LP-03 | LAPTOP-ONLY / UNJUDGED | UNJUDGED | `.planning/workstreams/perf-construction/phases/02-benchmark-integrity/02-EVIDENCE.md:54` | `NEW:.planning/workstreams/perf-construction/phases/02-benchmark-integrity/records/LP-03-laptop-host-buckets.txt` | two idle back-to-back runs land in different host buckets |
| LP-04 | LAPTOP-ONLY / UNJUDGED | UNJUDGED | `.planning/workstreams/perf-construction/phases/03-construction-metrology-contract/03-EVIDENCE.md:109` | `NEW:.planning/workstreams/perf-construction/phases/03-construction-metrology-contract/records/LP-04-owner-definitions.txt` | a definition names a different start or end event |
| LP-05 | LAPTOP-ONLY / UNJUDGED | UNJUDGED | `.planning/workstreams/perf-construction/phases/03-construction-metrology-contract/03-EVIDENCE.md:110` | `NEW:.planning/workstreams/perf-construction/phases/03-construction-metrology-contract/records/LP-05-laptop-distribution.txt` | a laptop header that says GEX44, or GEX44 numbers filled in |
| LP-06 | LAPTOP-ONLY / UNJUDGED | UNJUDGED | `.planning/workstreams/perf-construction/phases/03-construction-metrology-contract/03-EVIDENCE.md:111` | `NEW:.planning/workstreams/perf-construction/phases/03-construction-metrology-contract/records/LP-06-verify-proxy-sample.txt` | proxy end and human judgement of verified disagree in most turns |
| LP-07 | LAPTOP-ONLY / UNJUDGED | UNJUDGED | `.planning/workstreams/perf-construction/phases/04-host-pressure-admission/04-EVIDENCE.md:109` | `NEW:.planning/workstreams/perf-construction/phases/04-host-pressure-admission/records/LP-07-laptop-reader.txt` | a record whose os is linux or whose host is the GEX44 name, or an unreadable count shown GREEN |
| LP-08 | LAPTOP-ONLY / UNJUDGED | UNJUDGED | `.planning/workstreams/perf-construction/phases/04-host-pressure-admission/04-EVIDENCE.md:111` | `NEW:.planning/workstreams/perf-construction/phases/04-host-pressure-admission/records/LP-08-laptop-ceiling.txt` | timings at high counts are not slower than at low counts beyond run spread |
| LP-09 | LAPTOP-ONLY / UNJUDGED | UNJUDGED | `.planning/workstreams/perf-construction/phases/05-critical-path-audit/05-EVIDENCE.md:83` | `NEW:.planning/workstreams/perf-construction/phases/05-critical-path-audit/records/LP-09-laptop-registry.txt` | a record whose os is linux, a chain absent from the registry, or a duplicate invocation |
| LP-10 | LAPTOP-ONLY / UNJUDGED | UNJUDGED | `.planning/workstreams/perf-construction/phases/05-critical-path-audit/05-EVIDENCE.md:89` | `NEW:.planning/workstreams/perf-construction/phases/05-critical-path-audit/records/LP-10-laptop-ab-judge.txt` | the judge exits 2, or B does not beat the A to A noise |
| LP-11 | LAPTOP-ONLY / UNJUDGED | UNJUDGED | `.planning/workstreams/perf-construction/phases/05-critical-path-audit/05-EVIDENCE.md:95` | `NEW:.planning/workstreams/perf-construction/phases/05-critical-path-audit/records/LP-11-laptop-durability.txt` | an output present in the baseline normal session is missing in the candidate one |
| LP-12 | LAPTOP-ONLY / UNJUDGED | UNJUDGED | `.planning/workstreams/perf-construction/phases/05-critical-path-audit/05-EVIDENCE.md:101` | `NEW:.planning/workstreams/perf-construction/phases/05-critical-path-audit/records/LP-12-laptop-boundary.txt` | a footer below full count, a differing gate line, or a reported duplicate |

## 4. Known unknowns
Counts come from the `unknowns:` list of each phase verification file (`.planning/workstreams/perf-construction/phases/01-reality-and-ownership/01-VERIFICATION.md` and its siblings 02 to 05); the sentences below paraphrase and re-type no number from them.
- Phase 1: 4 unknowns. Most reference ids have no definition on this host, one in-clone file is not admitted, the laptop reading of the admission claim was not taken, and whether the ratchet callers run on the live tree was not measured.
- Phase 2: 6 unknowns. One reference id is blocked on a missing origin audit, the Windows host-state reading is unobserved, live regression verdicts are UNJUDGED for want of matched history, two gate scripts were not run live, and two Owner questions are open.
- Phase 3: 6 unknowns. The definitions are PROPOSED, no laptop distribution exists, the verify end is a proxy, the unit is DORMANT, live percentiles are below the minimum sample, and one test-strength gap was found by mutation.
- Phase 4: 8 unknowns. The Windows and macOS count parsers are fixture-only, the ceiling is uncalibrated, the motivating laptop case is not explained by the count pole, the s9 red-team caveat stands, one gate script is unedited, launch admission still judges RAM only, and two behaviour extensions are recorded decisions.
- Phase 5: 7 unknowns. No wall time of any real hook chain was measured, the laptop registry was never seen, the A/B judge is fixture-pinned only, the no-change criterion is met vacuously, a large share of registry entries stay UNKNOWN, and the boundary suite ran under an isolated HOME.
- Phase 6 inheritance rows: MX4 (Phase 3 censoring) and MX5 (Phase 5 FLAG_WEAKENED) came out OWN_SUITE_ONLY, no standing gate defends them; SURVIVED_ALL is none. Five mutants, one per owner, are a spot check, not a proof of every condition. Whether anything schedules the `bench-gate` row is UNKNOWN (no scheduler found in the repo).
- The s9 red-team (`tools/test_s9_redteam.py`) is UNJUDGED.
- Final gate run (one run, no retry, record named 06-03-T3.final-gates.txt in the Phase 6 records directory): 15 rows, 14 judged, 12 PASS, 2 BASELINE_MATCH, 1 SKIPPED_BY_POLICY, 0 FAIL, 0 NOT_RUN. The two BASELINE_MATCH rows are the pre-existing debt (git invocation 6 of 7, and the reachability offenders, equal by name); they are not passes. The skipped row is the s9 red-team, which is not a pass. The hook-boundary row ran under a fresh temporary HOME, so its duplicate-invocation sub-check stays UNEVALUATED (LP-12). Tree checks (record 06-03-T3.tree.txt): tools, modules, hooks and vault/config unchanged, ledger and floors hashes SAME.
- Largest single unknown: how long creation takes on the laptop, which is the Owner's complaint. Nothing in this campaign observes it; LP-05 is the first step toward it.

INVENTORY unknowns=4,6,6,8,7 lp=12 lp_ids=LP-01,LP-02,LP-03,LP-04,LP-05,LP-06,LP-07,LP-08,LP-09,LP-10,LP-11,LP-12 owner_decisions=13 changed_files=179 head=823d46157ea2

## 5. Exact next task
LP-05, the laptop construction distribution: the only item that answers the Owner's complaint directly. Run it with LP-07, LP-08 and LP-10 in the same laptop session, because their readings are easier to interpret beside it. On the laptop, from a checkout containing this branch, one command (save its printed output as the record):

```
python tools/construction_metrology_report.py --root <laptop transcript root> --max-files 200 --max-bytes 200000000 --seed 0
```

Record: `NEW:.planning/workstreams/perf-construction/phases/03-construction-metrology-contract/records/LP-05-laptop-distribution.txt`
Falsifier: the record header says GEX44 or the plane is not a laptop label, or GEX44 numbers were filled into it; the header must say UNDECLARED or a laptop plane label.
