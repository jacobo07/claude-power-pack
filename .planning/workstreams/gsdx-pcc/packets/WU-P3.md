# WU-P3 -- GSD X proof-conserving convergence, Phase 3 (W2 execution frontier and scheduling): PLAN, then EXECUTE

Mission: the id on your rehydration card (write it in the receipt). Follows m-e574a0e424e6 (Phase 2 DONE, 0fca7111).
Authority: Owner, 2026-10-11 chat: "y te doy ya 60M" -- 60M for the whole of Phase 3 (planning + execution).
cwd `C:\Users\User\Apps\pp-gsdx-pcc`, branch `gsdx/pcc`, workstream `gsdx-pcc`. UNATTENDED: nobody answers questions.

## Never
- Write the main checkout `C:\Users\User\.claude\skills\claude-power-pack`, `io-chatgpt-plugin`, `io-ucg`, or anything
  under `C:\Users\User\.claude` (global hooks/skills/settings). Never push. Never arm a mission. Never plan or execute the
  repo's ROOT milestone (it belongs to another track). Never start Phase 4.
- Run `/gsd-discuss-phase` or anything that asks the Owner questions. Re-litigate STATE.md Decisions or Phase 2's
  resolved semantics (spec S1-S16, 02-VERIFICATION.md).
- End a turn on a question. A decision the mission card's DECISION GATE reserves to the Owner goes into STATE.md as
  `OWNER DECISION NEEDED` (question, options, your pick); then continue with other runnable work.
- Weaken a gate, mark UNKNOWN as PASS, or drop a red branch to save calls.

## Start (first 3 calls)
1. `node ~/.claude/gsd-core/bin/gsd-tools.cjs query workstream.set gsdx-pcc --raw --cwd .`
2. `git status --short; git log --oneline -5` (the repository wins over this packet).
3. Read, in order: ROADMAP.md operating constraints and the Phase 3 entry, STATE.md, DENOMINATOR.md rows Phase 3
   owns, `phases/02-.../02-VERIFICATION.md`, the spec sections Phase 3 needs. Do not reread 02-RESEARCH.md (92 KB) or
   the 2111-line dataset end to end; open only cited lines/sections.
If `phases/03-*/03-0N-PLAN.md` files already exist, skip straight to the first plan with no SUMMARY.

## Part A -- plan (budget: finish by ~15M processed)
Write into `phases/03-w2-execution-frontier-and-scheduling/`, committing each artifact as it lands (write as you go;
the breaker refuses 25 calls without an edit or commit):
1. `03-CONTEXT.md`: scope from the ROADMAP Phase 3 entry; every gray area decided by you with a one-line reason
   (no Owner questions); the RED list verbatim (global WAIT with independent work; unsafe parallel writes; resource
   collision admitted as independent).
2. `03-RESEARCH.md`, <= 25 KB: premise-verify every function/module the plans will touch (HR-PREMISE-001), with
   file:line evidence; reuse Phase 2 seams (`modules/gsd_x/goal/proof.py`, the PCC events) rather than new stores.
3. `03-0N-PLAN.md` (aim 4-6 plans, sequential waves, each with RED-first tasks, named gates, files, done criteria)
   and `03-VALIDATION.md`.
4. One `gsd-plan-checker` agent (Sonnet, solo in its message, bounded, "Prefer Read/Grep/Glob; avoid Bash, use
   PowerShell", findings to `03-PLAN-CHECK.md`). Fix blockers in place; record dispositions. One iteration only.
Research/planning subagents are allowed only for read-and-write-a-file work (they have no PowerShell); you commit.

## Part B -- execute
Same rules as WU-P2: plans 03-01..03-0N in order, INLINE with PowerShell. For each plan: RED first where it says so;
run exactly the gates it names; logs under the phase dir; `03-0N-SUMMARY.md`; commit by pathspec
(`git add -- <paths>; git commit -F <msgfile> -- <paths>`, message file UTF-8 no BOM; verify `git log -1 --format=%s`).
Update DENOMINATOR rows only with evidence. Re-run the Phase 2 suites (`tools/test_gsd_x_goal_pcc_replay.py` 28/28,
`tools/test_gsd_x_goal_pcc_semantics.py` 48/48) at phase end: Phase 3 must not regress them.
After the last plan: `03-VERIFICATION.md` (run every human_verification check yourself), STATE.md to Phase 3 complete
(`current_phase: 4`, status planning), tick ROADMAP Phase 3, commit.
Housekeeping: `proof.cache` (1 byte, untracked, repo root) appeared during Phase 2's mutation drills at 19:19. Find
which drill/test writes it; fix the path (tmp dir) or gitignore it with a reason, in its own commit.

## Budget
Envelope `route-P3.json`: target 52M, warn 56M, stop 60M, 360 calls (breaker: 540 tool calls). At SESSION BUDGET warn:
finish and commit the current plan, then go STRAIGHT to the receipt. Never `run_in_background` for a check you need
this turn; pass `timeout: 600000` on long PowerShell calls; never poll an output file. Global batch caps apply.

## Done-gate for this unit (deterministic)
`03-VERIFICATION.md` frontmatter `status: passed`; every `03-0N-SUMMARY.md` present; Phase 2 and Phase 3 suites green
as run in the verification log; STATE.md `current_phase: 4`; `git status --short` clean except `vault/progress.md`.

## Receipt
Write `.planning/workstreams/gsdx-pcc/packets/WU-P3-receipt.md` (<= 25 lines): mission id; plans with commit ids; gate
lines verbatim (`*_PASS=`); DENOMINATOR rows moved; deviations; measured burn at end of Part A and at the end; open
points; Phase 4 size estimate from this phase's evidence. Commit it. End with exactly one line:
`HANDOFF NOTE: WU-P3 done -- Phase 4 (W3 candidate snapshots) ready to compile` or
`HANDOFF NOTE: WU-P3 PARTIAL -- <next plan id> -- <blocker>`.
