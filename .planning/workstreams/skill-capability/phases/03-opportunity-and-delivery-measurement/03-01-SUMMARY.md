---
phase: 03-opportunity-and-delivery-measurement
plan: 01
subsystem: pillar-C-delivery-measurement
tags: [delivery, recall, precision, opportunity, pillar-C, gate]
status: complete
requirements: [SC-C]
key-files:
  created:
    - tools/test_skill_delivery.py
    - vault/programs/skill-capability/delivery_fixture.json
    - vault/programs/skill-capability/evidence/C-delivery.md
  modified:
    - tools/skill_invocations.py
    - tools/test_skill_invocations.py
commits: 2
plan_head_before: 96bd5acac38a1a52b716aa128191cba07f00afde
actuals:
  tasks: 2
  commits: 2
---

# Phase 3 Plan 01: C delivery gate over fixture window F Summary

One gate (`tools/test_skill_delivery.py`) derives opportunity, delivery, recall and precision from card rows plus transcripts through the extended owner `tools/skill_invocations.py`, proven on a known-answer fixture, driven red by seven mutants and one subprocess run.

## Commits

- `9bf10e9f` feat(03-01): C -- skill delivery gate tracer over fixture window F, owner row bounds (Task 1)
- `e8f62a83` test(03-01): C -- delivery gate red drills, subprocess red run, owner bounds clause (Task 2)

## Task 1 (tracer)

- Owner: `row_epoch`, `since`/`until` on `count_file`, `bound_rows` on `scan`, `untimed_rows` aperture. Unbounded output unchanged; `scan` positional signature unchanged.
- Gate result on window F: opportunities 8, measured 6, UNMEASURED 2, delivered 4 (card 3, invocation-only 1, card-and-invocation 1), recall `4/6 = 0.667 (n=6)`, precision `n=4 (< 5, not estimated)`.
- CE contract: the real `_check_evidence("C", {kind: prg, ...})` printed `[]` for the rendered evidence file.

## Task 2 (red drills)

- RED observation: with the drills added and `V-SD-EVIDENCE-CURRENT` not yet written, the gate printed
  `FAIL V-SD-DRILL-STALE-EVIDENCE no clause V-SD-EVIDENCE-CURRENT exists to kill the mutant` and `SD_PASS=14/15`.
  After the clause was added the gate went to `SD_PASS=17/17`.
- Subprocess red run: `python3 tools/test_skill_delivery.py --fixture /tmp/sd-s4-moved.json` (S4 Skill call moved to 11:00:30) exited `rc=1` and printed
  `FAIL V-SD-DELIVERY delivered: measured 3, expected 4; by_invocation_only: measured 0, expected 1`.
- Drills (each killed by its own clause, controls ok): MENTION, NO-UNTIL, ABSENT-AS-NONE, UNTIMED-AS-NONE (A-1), PASS-AFTER, SMALL-N-RATIO, STALE-EVIDENCE, plus DRILL-CLEAN positive control.

## Verification lines

- Gate: `SD_PASS=17/17`, exit 0.
- `python3 tools/test_skill_invocations.py`: `PASS V-SKINV-ROW-BOUNDS`, `SKINV_PASS=11/12`; the only FAIL is the pre-existing laptop-plane `V-SKINV-REAL-TYPED: positive-control transcript not found`.

## Deviations from Plan

**1. [Orchestrator amendment A-1] extra fixture session S8.** Added S8 (`opportunity` at 12:00, transcript whose only Skill row is untimed). Its delivery is UNMEASURED and excluded from the recall n. Consequence: the plan's figures move to opportunities 8 (was 7) and UNMEASURED 2 (was 1); delivered, recall `4/6`, precision are unchanged. `V-SD-UNMEASURED-NOT-ZERO` checks both S6 and S8. An extra drill `UNTIMED-AS-NONE` kills the mutant that reads a session with only untimed rows as not delivered.

**2. [Mutant shapes]** The mutants M-MENTION and M-NO-UNTIL are applied as promotions of a measured "not delivered" (M-MENTION: the name appears in the transcript text; M-NO-UNTIL: `until` set to 1e12, still through `count_file`), instead of replacing the detector outright. A literal replacement would also flip S8's UNMEASURED state and turn the named control clause V-SD-UNMEASURED-NOT-ZERO red, which the plan requires to stay ok. M-PASS-AFTER yields 9 opportunities (plan: 8) because of S8.

**3. [Rule 3 - tooling] new files needed `git add <path>` before `git commit -- <paths>`** (pathspec commit refuses untracked paths). First attempt failed with no commit made; second succeeded. Explicit paths only.

**4. [A-2]** Every gate read states `encoding="utf-8"`, every write `newline="\n"`.

Task 2's re-render of `C-delivery.md` was byte-identical to Task 1's, so it is not in the Task 2 commit's file list (the plan's acceptance listed three files).

## Known Stubs

None.

## Threat Flags

None. The fixture is synthetic; the gate's default mode reads no ~/.claude, no network, no git.

## Self-Check: PASSED

Files found: tools/test_skill_delivery.py, vault/programs/skill-capability/delivery_fixture.json, vault/programs/skill-capability/evidence/C-delivery.md. Commits 9bf10e9f and e8f62a83 present in `git log`.
