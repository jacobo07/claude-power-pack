---
phase: 03-kme-corpus-measurements
verified: 2026-10-04T00:00:00Z
status: human_needed
score: 7/7 GEX44-plane must-haves verified; 0/6 pillar terminals (D..I) -- open by design, Owner-run on KME-L
covered_files:
  - tools/test_incremental_cognition_program.py
  - tools/test_kme_pillars.py
  - vault/programs/incremental-cognition/owner-bundle.md
  - wiki/tools/kme_pillars.py
  - wiki/tools/kme_token_audit.py
covered_digest: "v1:sha256:dff2d59586764505331c3cc1b3e9b6722567fc463d705aae167d214b54abb4c5"
behavior_unverified: 0
overrides_applied: 0
human_verification:
  - test: "Owner-bundle [D]..[I] on the laptop (KME-L): population proof first, then d/e/f/g/h/i (and d on CPP-D-W7; e second_workload if the E primary says second_workload_required)"
    expected: "Six primary measurement files with terminal_evidence true and population_match exact; each pillar then takes its frozen-rule terminal; only then state.D..I are written and IC-D..IC-I ticked"
    why_human: "KME-L is the laptop transcript corpus, not on GEX44; the frozen rules name it"
  - test: "H on KME-L: confirm verification share against the predicted FALSIFIED_OR_REJECTED"
    expected: "KME-L share < 3 %"
    why_human: "KME-G smoke reads 7.3 % (>= 3 %) -- smoke only, but if KME-L agrees the predicted disposition for H will not hold and the owner decides"
  - test: "Coverage: tools/test_kme_pillars.py (2.7k lines) was only skimmed by 03-REVIEW; 03-REVIEW-FIX fixed WR-01..07 and IN-01 and IN-02 was out of scope"
    expected: "A full read-through of the gate file, or reliance on its 89/89 gates plus 20/20 mutation drill"
    why_human: "unreviewed portion is a coverage item, not a defect found"
---

# Phase 03: KME corpus measurements -- Verification Report

**Phase Goal:** each measured pillar gets a terminal by its frozen rule on KME-L / KME-G.
**Binding constraint (03-CONTEXT):** KME-L is not on GEX44. On this plane the phase builds and tests the instruments, smoke-runs them on KME-G labelled non-terminal, records owner-bundle lines, and leaves ledger state.D..I open. Open terminals are therefore human verification, not code gaps.
**Status:** human_needed. **Re-verification:** No (initial).

## Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Instruments exist for D..I, tested on both poles with positive controls and mutation drill | VERIFIED | `python3 tools/test_kme_pillars.py` -> KMEP_PASS=89/89 skipped=0; `--drill` -> killed=20/20, DRILL-CLEAN-AFTER-MUTANTS 84/84 |
| 2 | Per pillar D..I one measurement file naming denominator and `command:` | VERIFIED (smoke plane) | measurements/ has D,E,F,G,H,I-KME-G-2026-10-03.md; each has `denominator`, `plane: gex44`, `evidence_role: smoke`, `terminal_evidence: false`, `command:`, `population_match: exact`. Re-ran H command with `--out-dir /tmp` -> share/materiality/numerator identical |
| 3 | Materiality applied exactly; UNMEASURED never read as < 3 % | VERIFIED | `materiality()` (kme_pillars.py:227): drifted/empty/obs<1 -> UNMEASURED; lo>=0.03 -> ">= 3 %"; hi<0.03 -> "< 3 %"; else STRADDLES. Recomputed KME-G weighted 54,899,558.8: D 2.64-3.96 % STRADDLES, H 7.30-7.40 % >= 3 %, I 8.26 % >= 3 %, E 0 %, F 0.69-1.03 %, G 0 % (< 3 %). D-GEX44-B001 is UNMEASURED (obs < 1), not "< 3 %" |
| 4 | Second-workload file exists for every pillar whose KME-G smoke clears or straddles 3 % (D, H, I) | VERIFIED (caveat) | D-, H-, I-GEX44-B001-2026-10-03.md exist (named workload, smoke role, population_match not_frozen). Caveat: D-GEX44-B001 is UNMEASURED (only 4 hook attachments, signal not recorded for part of population), so it confirms nothing for D; E needs none (KME-G 0 %) |
| 5 | Owner-bundle [D]..[I] present and commands parse; [A]/[B]/[C] unchanged | VERIFIED | `V-KMEP-BUNDLE-ARGV-PARSES`: 11 commands parsed, none unparsable. `git diff e35c2753 HEAD -- owner-bundle.md`: 108 insertions, 0 removed lines |
| 6 | Frozen artifacts untouched; ledger terminals open; requirements unticked | VERIFIED | `git diff --stat e35c2753 HEAD -- tools/test_cognitive_economy_program.py vault/programs/incremental-cognition/ledger.json` empty; ledger `state` D..I all `{}`; REQUIREMENTS IC-D..IC-I `[ ]`; `V-KMEP-AUDIT-BYTE-IDENTICAL-REAL` (177 sessions) and `V-KMEP-KMEG-FROZEN-REAL` (frozen equal) pass |
| 7 | Program done-gate + regression suites green | VERIFIED | `test_incremental_cognition_program.py --selftest` ICP_SELFTEST=PASS; `--pillar D..I` -> only `FAIL L3 <P>: no terminal disposition` (expected, honest; R3 guard refuses smoke files). Regressions: gsd_mission 213/213, gsd_epoch 82/82, cwd_align 16/16, persistent_failure_park 28/28, provider_breaker 18/18, gex44_env_preflight 57/57, mission_launch_gate 20/20, gex44_env_deploy 19/19 |
| 8 | Pillar terminals D..I on KME-L | NOT VERIFIABLE HERE (human) | by design; see human_verification |

## Anti-patterns
No TBD/FIXME/XXX in kme_pillars.py, test_kme_pillars.py, kme_token_audit.py or the added ICP guard lines. No stubs found; the measurement files are produced by the real instrument and reproduced.

## Review
03-REVIEW: 0 critical, 7 warnings, 2 info; coverage partial (kme_pillars.py read in full, kme_token_audit hunks and ICP hunks read, test_kme_pillars.py only skimmed). 03-REVIEW-FIX: WR-01..07 and IN-01 fixed (8/8), IN-02 out of scope; gates added with RED/GREEN evidence. Listed as a coverage item, not a gap.

## Notes
- H KME-G smoke share (7.3 %) already exceeds the 3 % line the H prediction relies on; smoke only, but flag for the KME-L run.
- Worktree noise unrelated to the phase: `vault/progress.md` modified and untracked `docs/{arch,changelog,constitution}/*kme_pillars*` generated by session hooks; not part of the phase deliverables. The orchestrator should decide whether to commit them.

## Gaps
None.

_Verified: 2026-10-04 -- Claude (gsd-verifier)_
