---
phase: 01-reality-and-ownership
verified: 2026-11-22T19:40:00Z
status: passed
verdict: passed_with_unknowns  # GSD routes only passed|gaps_found|human_needed; unknowns below stay open
score: 4/4 roadmap success criteria verified (criterion 1 with 34 of 40 P-ids UNKNOWN by design)
verified_head: a436e94b
behavior_unverified: 0
gaps: []
unknowns:
  - "34 of 40 P-ids (P02, P05, P07-P15, P18-P40) have no definition on this host; origin audit ed9de300 is not an object in this clone"
  - "iteracion-avanzada-universal.txt identity with the Windows original unproven (in-clone copy NOT ADMITTED)"
  - "P16/P17 laptop reading not taken (LP-01); judged at code level only"
  - "Whether Tower ratchet callers run on the live tree was not measured"
human_verification: []
---

# Phase 1: Reality and ownership - Verification Report

**Phase goal:** A verified world model so no later phase builds on an assumption.
**Plane:** GEX44 (code reading plus bounded read-only commands; no repo test suite, gate or benchmark run).
**Re-verification:** No, initial verification.
**Status: passed_with_unknowns.** All four roadmap success criteria are met on evidence I re-read in the code. The phase does NOT deliver a classification of 34 of the 40 P-ids; those are honestly UNKNOWN, not passed.

## Observable Truths (ROADMAP Phase 1 success criteria)

| # | Truth | Status | Evidence (re-observed, not taken from SUMMARY) |
|---|-------|--------|-----------------------------------------------|
| 1 | EVIDENCE.md holds a P01-P40 table, each with a status from the closed set and file:line or command evidence | VERIFIED (with unknowns) | 40 rows present (01-EVIDENCE.md lines 17-56). 6 rows judged by code reading (P01 PARTIALLY_FIXED, P03 PARTIALLY_FIXED, P04 / P06 / P16 / P17 CONFIRMED_ACTIVE); 34 rows UNKNOWN each citing searches S-06..S-10. Checker run by me: `check_evidence.py ... --stage final --require-judged P01,P03,P04,P06,P16,P17 --selftest` printed `violations=0`, 8 mutants executed, `accepted_mutants=0`, exit 0. |
| 2 | Owners of UCR-CIF and the Constitutive Baseline Ratchet named, or NOT FOUND with searches | VERIFIED | Both named, with basis labels and rejected alternatives (section 2) and searches S-16..S-24 each with a positive control. Paths exist on disk: `vault/knowledge_base/ucr_cif/UCR_CIF_RESUMPTION.md` (line 1 is `# UCR-CIF Compendium - RESUMPTION`), `modules/tower/ratchet.py` (`promote` at 196-199 and `revert` at 146-150 match the cited signatures). Basis is honestly NAME_IN_HEADER / NAME_IN_SPEC, and the UCR-CIF owner is explicitly a program document, not a runtime module. |
| 3 | D1 decided from real consumers | VERIFIED | Decision `EXTEND capability_runtime` (section 3). I re-confirmed the decisive facts: `modules/trace_context/context.py:15-17` states "nothing that decides ... may read what this module writes"; the only importer of trace_context outside the package is `tools/test_trace_context.py` (my own grep over modules/tools/hooks/scripts/lib); `vault/liveness/reachability_registry.json` marks `trace_context/__init__` PLANNED with consumer "not yet built"; `modules/capability_runtime/__init__.py:8-10` has the narrow-scope statement the caveat (a) cites. Falsifier and three fit caveats are written down. |
| 4 | iteracion-avanzada-universal.txt recorded UNAVAILABLE, not invented | VERIFIED | Section 4 records UNAVAILABLE at the Windows path (`/mnt` holds only `orca-s5-full`; no `/mnt/c`). In-clone copy recorded by size and sha256 only, marked NOT ADMITTED; I re-ran sha256sum and got `f7c579b1...bd27e3`, identical to the recorded value. Nothing in rows/D1/verdict derives from its content. The roadmap premise "not on this host" is correctly flagged as only half true (a copy exists in the clone). |

**Score:** 4/4 criteria verified; P-id classification coverage 6/40 judged, 34/40 UNKNOWN.

## Citation spot-checks (13 sampled, all matched the code)

| Citation | Claim in EVIDENCE.md | Observed |
|----------|---------------------|----------|
| tools/bench_all.py:714-721 | at_target counted and printed only | confirmed |
| tools/bench_all.py:719 | `rc = 0 if (not errors and not regressions) else 1` | confirmed verbatim |
| tools/bench_all.py:86-91 | timeout -> rc -1, FileNotFound -> -2, other -> -3 | confirmed |
| tools/bench_all.py:145-166 | uqf_scan / verify_spp record elapsed ms with rc stored, not gated (P03 unguarded sites) | confirmed |
| tools/bench_all.py:95-100 | session_start guard (`rc not in (0,1)` -> error) | confirmed (guarded site) |
| tools/bench_all.py:649-650 | baseline is `history[-1]` | confirmed |
| tools/verify_bench_all.py:153-158 | `best = min(vals)` decides confirmation | confirmed |
| tools/verify_bench_all.py:201 | "min of N samples" label | confirmed |
| tools/verify_bench_all.py:81 vs tools/bench_all.py:55 | ceps_record_ms 400 vs 25 | confirmed |
| tools/resource_admission.py:24-30, 70-80 | reads MemAvailable only; compares with floor | confirmed |
| tools/gsd_mission.py:1471, 2688, 7520 | resource_admission callers (all mission-worker paths) | confirmed (1471 is the import line, immediately followed by the `rsa.refusal` call; wording "before claim or spawn" is accurate for the surrounding block) |
| modules/trace_context/context.py:15-17 | AUTHORITY RULE | confirmed verbatim |
| vault/audits/perf_campaign_w0_reality.md:20-24 and ROADMAP lines 28/29/62-64 | P-id definition sources | confirmed at HEAD |

Owner paths checked: `modules/tower/ratchet.py`, `vault/knowledge_base/ucr_cif/UCR_CIF_RESUMPTION.md` (both exist and match their descriptions). S-08 reproduced: `git rev-parse --verify ed9de300^{commit}` exits 1 (origin audit ref absent), which is the stated reason 34 P-ids stay UNKNOWN.

## Requirements coverage

| Requirement | Status | Note |
|-------------|--------|------|
| PERF-01 (P01-P40 classified with evidence; UCR-CIF and Ratchet owners located; D1 decided) | SATISFIED WITH UNKNOWNS | Owners and D1 fully delivered. "P01-P40 classified" is delivered as 6 judged + 34 explicit UNKNOWN with search evidence. That is the strongest honest result available from this clone, but PERF-01's classification clause is not fully achieved in substance; it is carried as an open unknown, not a pass. |

No orphaned requirements for Phase 1 (only PERF-01 maps here).

## Anti-patterns and integrity checks

- No product code touched: `git diff --name-only a0e12830 HEAD` lists only ROADMAP.md, STATE.md, 01-02-SUMMARY.md, 01-EVIDENCE.md, consumer_census.py, all under `.planning/workstreams/perf-construction/`.
- UNKNOWN is never counted as PASS: the verdict is COMPLETE_WITH_UNKNOWNS and the checker's mutant h (plain COMPLETE with UNKNOWN rows) is rejected.
- Steps skipped by design: behavioral spot-checks and probes (documentation phase, instruction forbids running repo suites). The ratchet gates `tools/test_tower_ratchet.py` and `tools/test_ratchet_evidence.py` were not run (the evidence says so itself).
- HEAD advanced to a436e94b (marks Phase 1 executed in STATE/ROADMAP) after the 70e4423f named in the task; verification was done at a436e94b.

## Gaps

None blocking. The following are unknowns/risks (WARNING); none prevents Phase 2 from starting on the six judged rows:

1. **34 UNKNOWN P-ids.** P07 is named in the Phase 2 goal but has no description anywhere on this host; Phase 2 must not treat P07 as a fact. Closing needs the origin audit (main at ed9de300 or the inline plan of laptop pane 8fd6ace9). Laptop-only.
2. **P16/P17 are code-level only.** The laptop reading (LP-01) is unrun; the two rows share one combined source sentence, so their split is the executor's interpretation, flagged as such in the evidence.
3. **iteracion file identity unproven** (LP-02 hash comparison pending).
4. **D1 is a decision from consumer counts, not a fit proof.** The evidence is candid that capability_runtime's timing seam `invoke` has 0 production callers, has no TIMED_OUT/censored vocabulary, and that new files get hashed into the resolver policy id unless added to NOT_POLICY. Phase 3 inherits these as work and must write down the scope widening.
5. **Ratchet owner liveness not measured** (callers exist in code; whether they run on the live tree is unknown). The wiki component page is stale (OBS-07), recorded.
6. **Self-referential instrument.** check_evidence.py is a phase-local fixture written by the same phase it judges. I mitigated by re-running it with its mutation self-test and independently re-reading 13 citations, but the checker itself is not independently audited.

---

_Verified: 2026-11-22T19:40:00Z_
_Verifier: Claude (gsd-verifier)_
