---
phase: 00-spec-gen2-freeze-novelty-gate
plan: 05
subsystem: ic-gen2-ledger
tags: [ic-gen2, freeze, frozen-at, audit-gate, evidence, d-oq3, d-oq4]
requires: [00-04]
provides:
  - "gen2/evidence/freeze-audit.md: suite record, --audit output, expected red, 24-criterion to pillar-rule table (29 rows)"
  - "commit A afcdceea (pre-registration) and commit B 8752562a (gen2/FROZEN_AT alone): IC-gen2 frozen"
  - "00-EVIDENCE.md with Product Delta and Intelligence Delta; STATE.md position at Phase 1"
  - "tools/ic_gen2.py fixture resolver that can hide a real path (A7 mutant hermetic)"
affects: [01-usage-index-v5]
tech-stack:
  added: []
  patterns: ["machine audit plus recorded criterion-by-criterion read as the gate of a one-way step", "frozen sha256 recorded before the freeze, compared with the live one by A7 after it", "simulated post-freeze state (temporary FROZEN_AT naming HEAD) to prove the post-freeze path before committing it"]
key-files:
  created:
    - vault/programs/incremental-cognition/gen2/evidence/freeze-audit.md
    - vault/programs/incremental-cognition/gen2/FROZEN_AT
    - .planning/workstreams/autonomous-optimization/phases/00-spec-gen2-freeze-novelty-gate/00-EVIDENCE.md
  modified:
    - tools/ic_gen2.py
    - .planning/workstreams/autonomous-optimization/STATE.md
key-decisions:
  - "The tool defect that turned the audit red was fixed in its own commit (75517767) before the pre-registration commit, so commit A contains only the audit record and the audited head is a clean tree"
  - "The criteria table carries 29 rows for 24 criteria: a criterion carried by two clauses of one or two pillars gets one row per clause"
requirements-completed: [AO-01, AO-02]
duration: ~8 min wall (14:27:16Z to 14:35Z)
completed: 2026-10-06
status: complete
commits: 4
plan_head_before: f616bc4fd7d3cb068a1f527789ff48f360dff71f
actuals:
  tokens: 6409
  tasks: 3
  commits: 4
---

# Phase 0 Plan 05: IC-gen2 freeze and phase evidence Summary

**IC-gen2 is frozen: the audited pre-registration is commit `afcdceea` (frozen sha256 `a8ac15d894a7...`), `gen2/FROZEN_AT` = that sha in its own commit `8752562a`, the L2 pin refuses an in-memory edit, `--generation 2 --final` is the expected red `failures=9` (no L2), and 00-EVIDENCE.md closes Phase 0 with Product and Intelligence Delta. Plane: gex44.**

## Performance

- Tasks: 3 of 3 complete (task 1 tracer, tasks 2 and 3 auto); 4 commits before this file (1 fix, A, B, evidence), the SUMMARY commit follows
- Files: 3 created, 2 modified (`actuals.tokens` is chars/4 over the new record, the evidence file and the tools/STATE/FROZEN_AT diff: 25,635 chars)

## Accomplishments

- Task 1 gate: every suite ran in a fresh process; all exited 0 except `--generation 2 --final` (exit 1, exactly 10 lines). The criterion-by-criterion read mapped all 24 ROADMAP criteria of Phases 1-6 (4+5+3+4+3+5, re-counted from the file) to verbatim clauses of the pillar rules; the plan's verify one-liner printed `29 [] []`. No `frozen` text needed a change.
- Commit A `afcdceea302c8662b6b8c87c30d6eb8ed8dcba18` adds only `freeze-audit.md`; `git show afcdceea:<gen2 ledger>` parsed, its `frozen` hashes to the recorded `a8ac15d894a72c74eb71901b3081c7a6a20a0ee2d9da085a270dd015a204d39e`, and the file is byte-identical to the working copy (`cmp`).
- Commit B `8752562a42c9e82aefe18bd1fe9c211fc262f229`: `gen2/FROZEN_AT` only, one insertion, content equal to `HEAD~1` (A).
- Post-freeze, fresh processes (HEAD 8752562a): `--generation 2 --status` exit 0, `violations: []`; `--generation 2 --final` exit 1 with 9 FAIL lines (L3 x5, L8 x4, no L2) and `ICP_GEN2_VERDICT=FAIL failures=9`; `--generation 2 --audit` exit 0 with `A3 ... (9 lines, frozen)` and `A7 ok recorded frozen_sha256 equals the live one`; both selftests PASS; L2 drill printed `[] ['L2 frozen pre-registration differs from its copy at FROZEN_AT']` (plan command, exit 0, `problems(led, None, False)` signature unchanged).
- Acceptance diffs: `git diff --quiet 3f48f2e3 HEAD` over gen1 IC/CE/SC ledgers, gen1 FROZEN_AT, both CE/SC verifiers, root `.planning/STATE.md`, `tools/gsd_mission.py` exits 0; `git diff --name-only --diff-filter=A 3f48f2e3 HEAD -- modules` is empty.
- Task 3: 00-EVIDENCE.md with every section and verdict line the verify command names (`[]` missing); gen1 `--final` quoted verbatim as inherited state. STATE.md Current Position / Session Continuity updated (frontmatter and Decisions untouched; root STATE.md untouched).

## Task Commits

| Task | Commit | Subject |
|---|---|---|
| 1 (fix found by the gate) | 75517767 | fix(00-05): IC-gen2 A7 mutant hermetic once the freeze-audit record exists |
| 2 (commit A) | afcdceea | feat(autonomous-optimization): P0 IC-gen2 freeze -- pre-registration M,O,P,Q,R audited (ICP_GEN2_AUDIT=PASS) |
| 2 (commit B) | 8752562a | chore(autonomous-optimization): FROZEN_AT = afcdceea (IC-gen2 pre-registration commit) |
| 3 | 9f713809 | docs(00-05): phase 0 evidence (Product + Intelligence Delta) + STATE position |

Tracer gate: Task 1 produced the full chain (suites, audit, criteria table, record) and its verify commands were re-run end to end after the fix before any expansion: audit PASS, table `29 [] []`, `FROZEN_AT` absent. Tracer verified end-to-end, expanding.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The A7 selftest mutant survived once the audit record existed on disk (fix round 1 of 2)**
- **Found during:** Task 1, the first audit run after writing `freeze-audit.md`
- **Issue:** `--generation 2 --audit` printed `FAIL V-IC2-MUT-A7-frozen-without-record SURVIVED (expected a A7 line, got [])`, A2 (selftest passes) failed and the verdict was `ICP_GEN2_AUDIT=FAIL ... failures=1`. The mutant (FROZEN_AT present, no record) read the record path from the real repo, which now held the record. Plan 00-04 could not see it because the record did not exist yet.
- **Fix:** `Fx` (the fixture resolver) treats a `files` value of None as hiding that path; the mutant hides `FREEZE_AUDIT_REL`. Verified both pre-freeze and in a simulated post-freeze state (temporary `gen2/FROZEN_AT` naming the then-HEAD, which holds the same ledger; removed afterwards): A3 `(9 lines, frozen)`, A7 `recorded frozen_sha256 equals the live one`, selftest PASS, `--final` 9 lines.
- **Files modified:** tools/ic_gen2.py
- **Commit:** 75517767
- The whole Task 1 sequence was re-run from the start after the fix (all green), and the record's `head` is the fix commit. `frozen` text was not touched, so the audited sha256 is the one 00-04 recorded.

### Other notes

- `git add` of the new files before a pathspec commit (git refuses pathspec commits of untracked paths); no other path was staged.
- The suite row for `--audit` in the record quotes `A7 ok (not frozen yet)` and refers to the Audit section for the verdict line, so the record holds exactly one `ICP_GEN2_AUDIT=PASS frozen_sha256=...` line, as A7 and the acceptance regex require.
- Commit A's message and the record carry no ledger change: the plan allowed a ledger edit only if the audit forced one.

**Total deviations:** 1 auto-fixed (Rule 1, in a tool, not in `frozen`). **Impact:** one extra commit; the freeze content and its sha256 are exactly what 00-04 audited.

## Authentication Gates

None.

## Known Stubs

None. Gen2 `deltas`, `reviews` and terminal dispositions are empty by design until their phases (reported by `--generation 2 --final`, exit 1, `failures=9`).

## Threat Flags

None. T-00-22: the gate ran before commit A and the frozen hash was recomputed from `git show afcdceea:<ledger>`; T-00-23: SHA_A was captured from `git rev-parse HEAD` immediately after A, B is pathspec-only and `git show --stat` lists one file; T-00-24: the L2 drill refuses an edited in-memory copy; T-00-25: gen1 red lines quoted verbatim, every number sits next to a command; T-00-26: one fix round used of two.

## Issues Encountered

- Host command guard refuses compound git lines (variables, `;`, pipes); every git command was run plain and separate.
- The anti-thrash hook blocked a third consecutive Edit on one file without a Read; one Read cleared it.
- `python3 tools/test_mission_launch_gate.py` prints this host's own preflight reasons `['auth_expired', 'hooks_broken']` inside its passing gates (LG 20/20); environment facts, not programme claims.

## Next Phase Readiness

Phase 1 (usage_index v5 substrate, PLAN mode) can start. The programme judge is `python3 tools/test_incremental_cognition_program.py --generation 2 --status` (must stay exit 0; L2 now pins `frozen`). Inherited gen1 red lines stay as quoted in 00-EVIDENCE.md. The ROADMAP/STATE progress counters were not changed (orchestrator owns them).

## Self-Check

- FOUND: `vault/programs/incremental-cognition/gen2/evidence/freeze-audit.md`, `vault/programs/incremental-cognition/gen2/FROZEN_AT`, 00-EVIDENCE.md, `tools/ic_gen2.py`.
- FOUND commits 75517767, afcdceea, 8752562a, 9f713809 on `mission/autonomous-optimization-gen2` (`git rev-list --count f616bc4f..HEAD` = 4 before this file).
- All Task 1-3 acceptance criteria and the plan-level verification commands were run after the last commit (see Accomplishments).

## Self-Check: PASSED
