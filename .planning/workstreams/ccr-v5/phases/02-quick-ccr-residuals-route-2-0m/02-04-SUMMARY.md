---
phase: 02-quick-ccr-residuals-route-2-0m
plan: 04
subsystem: ccr-phase-closure
tags: [ccr, evidence, spend-booking, coverage-audit, iteration-pass]
requires: [02-01, 02-02, 02-03]
provides:
  - "02-EVIDENCE.md: graded verdicts for the three ROADMAP clauses, coverage audit, iteration pass, residuals, hand-offs"
  - "goal ccr spend booked for session af436132 (25,095,992 processed)"
  - "STATE.md / ROADMAP.md: Phase 2 complete, Phase 3 next"
affects: [phase-3, phase-4, phase-8, phase-9, phase-11]
key-files:
  created:
    - .planning/workstreams/ccr-v5/phases/02-quick-ccr-residuals-route-2-0m/02-EVIDENCE.md
    - .planning/workstreams/ccr-v5/phases/02-quick-ccr-residuals-route-2-0m/02-CONTEXT.md (committed here as the phase's auto-generated context)
  modified:
    - .planning/workstreams/ccr-v5/STATE.md
    - .planning/workstreams/ccr-v5/ROADMAP.md
key-decisions:
  - "Grades never upgraded: clause 1 OBSERVED (no real launch), clause 2 PROVEN for the extracted spent()/over() property only, clause 3 PROVEN"
  - "Residual (a) widened from the brief using the OUTPUT-DOMAIN gate output (5 of 8 corruption variants print 0); not patched"
  - "12.55x spend breach recorded, stop-loss decision left to the coordinator (Phase 1 was never booked on L13)"
requirements-completed: [REQ-2]
status: complete
completed: 2026-10-15
commits: 1
plan_head_before: 44291071c763f88bd100a19cee66297f3d8e6b52
actuals:
  tasks: 2
  commits: 1
---

# Phase 2 Plan 04: Phase 2 evidence, spend booking and closure Summary

Every gate the phase produced was re-run from the worktree (DRV 14/14, PGOINST 14/14, CCRPGO 16/16, a6 13/0, contract 5/0, `ccr_pgo.py verify` exit 0; all exit 0, none INCONCLUSIVE), the three clauses were graded in `02-EVIDENCE.md`, the session was booked on goal `ccr`, and Phase 2 is marked complete with Phase 3 next.

## Results

- Gates re-run before the commit and again after it with identical exit codes; `git diff --name-only 0316acff..HEAD -- mods/` is empty, so no CCR release was required.
- A fresh read-only `sha256sum` on gex44 (exit 0, 2026-10-15T07:39:07Z) equals the committed `drive3.sh` sha256 `9f74c589...1dd7`.
- Live PGO directory: three files, `Get-FileHash` equal to the committed sources. Main-tree and worktree `RESUMPTION_FILE.md` both hash to `749FF9A9...37E1`, equal to the 02-03 capture.
- Spend: `python tools/mission_spend.py goal-settle --goal ccr --session af436132-9889-4908-972f-0a81204d9776 --measured 25095992` exit 0, `used` 25,095,992, `remaining` 53,904,008, cap 79,000,000 unchanged. Ratio to the 2.0M route: 12.55x.
- Commit `d38839b8` (`ccr-v5 p2: Phase 2 evidence, plans and STATE`): exactly `02-EVIDENCE.md`, `02-CONTEXT.md`, `STATE.md`, `ROADMAP.md`; no deletions; subject verified with `git log -1 --format=%s`; worktree clean afterward.
- Secret scan over the four committed files: 0 matches.

## Grades

| Clause | Grade |
|---|---|
| 1 PGO install, DEFLATE read, hold | OBSERVED (file identity PROVEN; shrink UNJUDGED; scheduler-wide hold BLOCKED with Owner step) |
| 2 Driver versioned, breaker regression | PROVEN for the extracted `spent()`/`over()` fail-closed property; remote identity OBSERVED; full-driver run UNJUDGED |
| 3 RESUMPTION_FILE committed | PROVEN (seal belongs to Phase 4, UNJUDGED) |

## Open residuals (carried verbatim into the EVIDENCE)

(a) `spent()` prints 0 for a missing/misnamed stream file and for all-string-message streams (also string, null and list usage, list message, empty file), so it never trips: OPEN, not patched. (b) DEFLATE is live by default for bounded-code slim launches; `CPP_CCR_DEFLATE=off` does not reach Task Scheduler, only removing `pgo-classes.json` does; persisting the variable is an Owner decision. (c) Main-tree `RESUMPTION_FILE.md` is dirty with the bytes ccr/v5 commits (Phase 3 note; autocrlf=true, compare with `Get-FileHash`). (d) Real-launch DEFLATE saving UNJUDGED.

## Deviations from Plan

**1. [Scope - orchestrator instruction] ROADMAP.md edited and STATE.md edited directly.** The plan lists only STATE.md; the orchestrator asked for Phase 2 complete / Phase 3 next in both files, and `gsd-tools state` verbs were not used (they failed with `plan_position_unreadable` in earlier plans). Scoped Edits, Phase 2 lines only (frontmatter progress, Current Position, Performance Metrics, Session).

**2. [Rule 3 - Blocking] Evidence file was untracked.** The first `git commit -- <paths>` failed (`pathspec ... did not match any file(s) known to git`) because `02-EVIDENCE.md` had not been `git add`ed; nothing was committed. Cause fixed by adding it with the other untracked file, then the commit succeeded. Not a retry of the same shape.

**3. [Tooling] No PowerShell tool.** Every shell action ran as `powershell.exe -File <ps1 in %TEMP%>`; no guard escape markers were used. A first ssh script used `< $null`, which PowerShell rejects at parse time; replaced by `$null | ssh ...` (different shape, read-only `sha256sum`).

**4. [Spend scope] Booked the whole session lineage.** The plan says "the whole session transcript"; the coordinator's main transcript is 7,914,104 tokens and its six subagent transcripts 17,181,888, and `mission_spend`'s own attribution counts `<sid>/subagents/*.jsonl` as the session's. The number is a snapshot (07:38:07Z); this executor's later calls are unbooked and fall to the next watermark-delta settle.

**5. [Deferred] UKDL seed.** The iteration prompt asks for a UKDL entry; the plan scopes writes to the evidence and STATE, so the candidate trap is recorded in the EVIDENCE for Phase 11. The main-tree `ukdl-universal.md` carries a foreign writer's bytes and was not touched.

## Known Stubs

None.

## Threat Flags

None.

## Self-Check: PASSED

- FOUND: `02-EVIDENCE.md` (all required sections, `DRV_PASS=`, `PGOINST_PASS=`, 38 grade words, Iteration pass, Coverage, goal-settle)
- FOUND: commit `d38839b8` on `ccr/v5`; `git log -1 --format=%s` equals the message first line; status clean
- Post-commit gate re-run: same six exit codes (all 0) and verdict lines as the pre-commit run
