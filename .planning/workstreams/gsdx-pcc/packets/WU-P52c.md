# WU-P52c -- PCC wave 5.2 (trust core), part 3 of 3: 05-2-04, 05-2-05, phase close, compile WU-P6

Mission: the id on your rehydration card. Follows WU-P52b (read its receipt only). 
cwd `C:\Users\User\Apps\pp-gsdx-pcc`, branch `gsdx/pcc`, workstream `gsdx-pcc`. UNATTENDED: nobody answers questions.
Authority: Owner, 2026-10-14 ("Aprobar 175M"; plan `.planning/workstreams/gsdx-pcc/CONTINUATION-PLAN-2026-10-14.md`).
Phase dir: `.planning/workstreams/gsdx-pcc/phases/05-2-trust-core/` (Part A is committed in 7e139cb3).
Base packet: `packets/WU-P52.md`. Its Never list and execution rules apply. Its Budget, Part A and Part C are superseded here.

## Why this unit is narrow (read it, it is the point)
WU-P52 (m-d563551d7aa9) was stopped by the semantic breaker TOKEN_INCIDENT: 25 tool calls without progress, spent
re-reading five phase docs before writing anything. Its receipt (untracked `packets/WU-P52-receipt.md`, do not edit it)
lists the next actions. Rules for you:
- Read ONLY what your plan(s) cite: the PLAN file, the exact file:line ranges it names, and 05-2-RESEARCH.md
  sections it points to. Never re-read a file you already read this session.
- Make progress every <= 12 calls: an Edit/Write of a test or module, or a commit. RED first, then commit the RED log.
- Do not try to read `~/.claude/state/session-budget-*.json`; the goal-budget guard refuses it. The driver measures burn.
- The concurrent-writers hook refuses a commit that contains hunks this session did not write. Commit only your own
  files; never stage `packets/WU-P52-receipt.md`, `*.partial.json`, other `*.residual.md`, `.claude/`, `vault/progress.md`,
  `LEARNINGS_PENDING.md`, `vault/specs/salvage/`.

## Execution
INLINE with PowerShell. Git: `& 'C:\Program Files\Git\cmd\git.exe' -C . ...`. Python
`C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`, `$env:PYTHONIOENCODING='utf-8'`. One suite per call,
`timeout: 600000`, logs under the phase dir `logs/`. Commit by pathspec with `-F <msgfile>` (UTF-8 no BOM, message ends
`Co-Authored-By: Claude Sonnet <noreply@anthropic.com>`), verify `git log -1 --format=%s`. Never push, never arm a
mission, never ssh, never write outside this worktree. A heavy run that RAM kills: mark it UNRUN, do not retry.
Each plan ends with its `05-2-0N-SUMMARY.md` (gates verbatim with plane `Windows laptop`, drills, deviations).

## Work
1. 05-2-04: D11 wiring. Non-AND claims are evaluated through the algebra (`proof.combine_states`), RED-first. SUMMARY, commit.
2. 05-2-05: `tools/gsdx_pcc_done.py` as a question registry (plan section 7): it exits 1 while any question is OPEN,
   UNKNOWN or single-plane where portability is claimed. Add V-DONE-COUNT>=40 and the MIGRATION-ONCE task; run the
   drills the plan names (`tools/mutation_drill.py`, one per call). SUMMARY, commit.
3. Phase close: regression once each (semantics 48/48, pcc_replay 28/28, frontier 40/40, invalidation 26/26,
   judge_validate 11/11, certificate, hermetic 5/5, trust, plus the 5.2 suites); liveness exit 0;
   `05-2-VERIFICATION.md` (plane per gate); DENOMINATOR rows N01 N02 N05 N16 N17 N19 N23 D11 moved with evidence;
   STATE.md to wave 5.2 complete, next Phase 6. Commit.
4. Compile `packets/WU-P6.md` + `packets/route-P6.json` (wave 6, mutant farm; plan sections 5-6).
   - Split it into narrow units from the start: WU-P6a/b/c..., each <= 45 calls. The chain reads ONE packet per
     unit id, so write `packets/WU-P6.md` as the first unit (P6a scope) and list the remaining units in its
     Part C, which compiles the next one.
   - Route rule (measured): calls x 118K x 1.2, plus >= 3 % margin, <= target.
   - Every packet carries this packet's "Why this unit is narrow" section.
   Commit.

## Done-gate
`05-2-VERIFICATION.md` status passed; `python tools/gsdx_pcc_done.py` runs and exits 1, naming OPEN questions
(expected at this stage); WU-P6 + route-P6 committed.
## Receipt
`packets/WU-P52c-receipt.md` (<= 20 lines). Line 2 must be exactly `Status: DONE` (or `Status: PARTIAL -- <blocker>`).
Then: mission id, commits, gate lines verbatim with plane, DENOMINATOR rows moved, open points. Commit it, end with
`HANDOFF NOTE: WU-P52c done` (or PARTIAL + next step), then end the session. Write the receipt at the latest when you
judge ~35 calls are used; a PARTIAL with an exact next step beats a cut with nothing.