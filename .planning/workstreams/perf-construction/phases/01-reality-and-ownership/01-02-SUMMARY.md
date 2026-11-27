---
phase: 01-reality-and-ownership
plan: 02
subsystem: perf-metrology-evidence
tags: [evidence, owners, d1-decision, consumer-census, unavailable-input]
requires: [01-01]
provides:
  - "01-EVIDENCE.md closed at stage final: owners, D1 decision, section 4 record, verdict"
  - "consumer_census.py: read-only AST consumer census used by the D1 decision"
affects: [phase-02, phase-03, phase-04]
tech-stack:
  added: []
  patterns: ["consumer count by AST, not by name grep", "zero-hit search carries a positive control"]
key-files:
  created:
    - .planning/workstreams/perf-construction/phases/01-reality-and-ownership/consumer_census.py
    - .planning/workstreams/perf-construction/phases/01-reality-and-ownership/01-02-SUMMARY.md
  modified:
    - .planning/workstreams/perf-construction/phases/01-reality-and-ownership/01-EVIDENCE.md
decisions:
  - "D1: EXTEND capability_runtime (trace_context disqualified by its written decider-reader prohibition and has 0 production consumers)"
  - "UCR-CIF owner: vault/knowledge_base/ucr_cif/UCR_CIF_RESUMPTION.md (NAME_IN_HEADER); Constitutive Baseline Ratchet owner: modules/tower/ratchet.py (NAME_IN_SPEC)"
  - "iteracion-avanzada-universal.txt: UNAVAILABLE at the Windows path; in-clone copy NOT ADMITTED pending laptop comparison, nothing derived from its content"
  - "Phase 1 verdict: COMPLETE_WITH_UNKNOWNS (34 of 40 P-ids UNKNOWN)"
metrics:
  duration: "not measured (session was compacted once; no start timestamp survived)"
  completed: 2026-11-22
status: complete
commits: 3
plan_head_before: a0e12830bbf171de1166c6e3855b6ebf32a1f97a
actuals:
  tasks: 3
  commits: 3
---

# Phase 1 Plan 2: Owners, D1 decision, unavailable input, verdict Summary

Closed the Phase 1 evidence file: both owners located, D1 decided from a consumer census as EXTEND capability_runtime, the iteracion input recorded UNAVAILABLE with its in-clone copy NOT ADMITTED, verdict COMPLETE_WITH_UNKNOWNS.

## Tasks and commits

| Task | Name | Commit |
|------|------|--------|
| 1 | Owners of UCR-CIF and the Constitutive Baseline Ratchet | bc3f7e08 |
| 2 | Decide D1 from real consumers | 373fef0a |
| 3 | Record the unavailable input, close the verdict | 2eb8590b |

## Results

- **UCR-CIF owner:** the program root `vault/knowledge_base/ucr_cif/UCR_CIF_RESUMPTION.md` (basis NAME_IN_HEADER); runtime delegates (modules/tower, modules/gsd_x/tier.py, modules/duplicate_to_advantage) are listed separately.
- **Constitutive Baseline Ratchet owner:** `modules/tower/ratchet.py` (basis NAME_IN_SPEC; the name appears only in specs, S-23). Entry interface and gate command recorded, gate not run. Rejected alternatives: modules/sqi/ratchet.py, modules/sqi/baseline_guardian.py.
- **D1 decision: EXTEND capability_runtime.** Consumer census (S-25 to S-31): trace_context has 0 production consumers, 1 test, a PLANNED liveness class and a written rule that nothing that decides may read what it writes (modules/trace_context/context.py:15-17), which collides with the Phase 4 decider-readers. capability_runtime has 15 production consumers and no reader restriction. The falsifier and three inherited fit caveats are written into section 3: its timing seam `invoke` has 0 production callers, it has no TIMED_OUT or censored vocabulary, and any new package file is hashed into the resolver policy id unless added to NOT_POLICY.
- **iteracion-avanzada-universal.txt:** UNAVAILABLE at the Windows path (S-01, S-32, S-33). In-clone copy `vault/programs/cognitive-economy/a5/inputs/iteracion-avanzada-universal.txt`, 6862 bytes, sha256 `f7c579b1168e71b08093370820a0b6341e72447abf527450acbff20238bd27e3`, marked NOT ADMITTED pending laptop comparison (LP-02). Hash only; content never viewed or used.
- **Verdict:** COMPLETE_WITH_UNKNOWNS. Status counts: CONFIRMED_ACTIVE 4, PARTIALLY_FIXED 2, UNKNOWN 34, others 0.

## Success criteria (ROADMAP Phase 1)

| # | Criterion | Result |
|---|-----------|--------|
| 1 | P01-P40 table with status and evidence | MET (6 judged by code reading, 34 UNKNOWN with their searches) |
| 2 | Owners of UCR-CIF and Ratchet named or NOT FOUND with searches | MET |
| 3 | D1 decided from real consumers | MET (EXTEND capability_runtime) |
| 4 | iteracion file recorded UNAVAILABLE, not invented | MET |

## Verification

`check_evidence.py 01-EVIDENCE.md --repo . --stage final --require-judged P01,P03,P04,P06,P16,P17 --selftest`: 0 violations, 8 mutants executed, 0 accepted (a to h all rejected). Credential-shape scan over the phase directory: 0 hits, positive control 1 hit. `git status --porcelain` showed only the evidence file (plus the pre-existing untracked `.pp-capabilities`, not from this plan and not committed). No product code was edited and no repo test or gate was run.

## Deviations from Plan

**1. [Instruction from the lead, supersedes plan wording] iteracion-avanzada-universal.txt handled by hash only.** The plan expected "UNAVAILABLE, nothing read". The lead directed: record the in-clone copy's path, size and sha256 and mark it NOT ADMITTED. Done; the section 4 line keeps "UNAVAILABLE" and the existing id S-01 so the checker still passes.

**2. [Rule 3 - blocking] The unchanged rerun of the S-01 find did not complete.** The tool terminated it (exit 143, no count). The 160-path figure from plan 01-01 stands unrefreshed; bounded probes S-32 to S-35 were added and the gap is stated in the section 5 notes.

**3. [Rule 1 - plan drift] Tracer search rows S-03 and S-04 were path-spelling greps** that counted references, not consumers. They are kept unedited and superseded by the AST census rows S-25 and S-29.

**4. [Finding] The wiki component page for the Constitutive Baseline Ratchet is stale** (OBS-07): it says promote() has no caller and no B1 exists, but callers exist and web_surface has baselines B0 to B7.

**5. [Environment] Worktree guard refused compound shell commands.** Work was done with plain separate commands and scripts kept in the job tmp directory; no effect on results.

## Known Stubs

None.

## Threat Flags

None. No new surface; no product code, ~/.claude file or live install was touched; nothing was pushed.

## Open items for the lead

- Laptop: the origin audit (main at ed9de300, or the inline plan of pane 8fd6ace9) to define the 34 UNKNOWN P-ids; the LP-02 hash comparison for the iteracion file; the LP-01 measurement for P16 and P17.
- Phase 3 must write down the widening of capability_runtime scope and add the TIMED_OUT/censored vocabulary (D1 caveats a to c).

## Self-Check: PASSED

- 01-EVIDENCE.md, consumer_census.py and this file exist; commits bc3f7e08, 373fef0a and 2eb8590b exist on the worktree branch and `git rev-list --count a0e12830..HEAD` was 3 at write time.
- Final checker run recorded above.
