# WU-P4 -- GSD X proof-conserving convergence, Phase 4 (W3 candidate snapshots, invalidation, proof inheritance): PLAN, then EXECUTE

Mission: the id on your rehydration card (write it in the receipt). Follows m-84c6e0072a10 (Phase 3 DONE, f364de64).
Authority: Owner, 2026-10-12 chat: "aprobar 75M" -- 75M for the whole of Phase 4 (planning + execution).
cwd `C:\Users\User\Apps\pp-gsdx-pcc`, branch `gsdx/pcc`, workstream `gsdx-pcc`. UNATTENDED: nobody answers questions.

## Never
- Write the main checkout `C:\Users\User\.claude\skills\claude-power-pack`, `io-chatgpt-plugin`, `io-ucg`, or anything
  under `C:\Users\User\.claude` (global hooks/skills/settings). Never push. Never arm a mission. Never ssh to another
  host. Never plan or execute the repo's ROOT milestone (it belongs to another track). Never start Phase 5.
- Run `/gsd-discuss-phase` or anything that asks the Owner questions. Re-litigate STATE.md Decisions, Phase 2's
  resolved semantics (spec S1-S16, 02-VERIFICATION.md) or Phase 3's frontier contract (03-VERIFICATION.md).
- End a turn on a question. A decision the mission card's DECISION GATE reserves to the Owner goes into STATE.md as
  `OWNER DECISION NEEDED` (question, options, your pick); then continue with other runnable work.
- Weaken a gate, mark UNKNOWN as PASS, treat UNKNOWN impact as clean, or drop a red branch to save calls.

## Start (first 3 calls)
1. `node ~/.claude/gsd-core/bin/gsd-tools.cjs query workstream.set gsdx-pcc --raw --cwd .`
2. `git status --short; git log --oneline -5` (the repository wins over this packet).
3. Read, in order: ROADMAP.md operating constraints and the Phase 4 entry (Requirements D01 D10-D14 D20 D23 D24 D39
   D45 R02), STATE.md, DENOMINATOR.md rows Phase 4 owns, `phases/03-*/03-VERIFICATION.md`, the spec sections Phase 4
   needs. Do not reread 02-RESEARCH.md (92 KB) or the 2111-line dataset end to end; open only cited lines/sections.
   D25/D26 (executed speculation and racing) are Phase 4 work ONLY if DENOMINATOR.md assigns them to Phase 4; otherwise
   leave them OPEN and say so in the receipt.
If `phases/04-*/04-0N-PLAN.md` files already exist, skip straight to the first plan with no SUMMARY.

## Part A -- plan (budget: finish by ~15M processed)
Write into `phases/04-w3-candidate-snapshots-invalidation-proof-inheritance/`, committing each artifact as it lands
(write as you go; the breaker refuses 25 calls without an edit or commit):
1. `04-CONTEXT.md`: scope from the ROADMAP Phase 4 entry; every gray area decided by you with a one-line reason
   (no Owner questions); the RED list verbatim (false reuse after a relevant change; UNKNOWN treated as clean;
   fresh-required proof inherited; omitted proof without an INHERITED event; candidate changes under verification).
2. `04-RESEARCH.md`, <= 25 KB: premise-verify every function/module the plans will touch (HR-PREMISE-001), with
   file:line evidence; reuse Phase 2/3 seams (`modules/gsd_x/goal/proof.py`, the PCC events, `frontier.py`) rather
   than new stores. Candidate snapshots live on git objects, never a parallel copy store.
3. `04-0N-PLAN.md` (aim 4-6 plans, sequential waves, each with RED-first tasks, named gates, files, done criteria)
   and `04-VALIDATION.md`.
4. One `gsd-plan-checker` agent (Sonnet, solo in its message, bounded, "Prefer Read/Grep/Glob; avoid Bash, use
   PowerShell", findings to `04-PLAN-CHECK.md`). Fix blockers in place; record dispositions. One iteration only.
Research/planning subagents are allowed only for read-and-write-a-file work (they have no PowerShell); you commit.

## Part B -- execute
Same rules as WU-P3: plans 04-01..04-0N in order, INLINE with PowerShell. For each plan: RED first where it says so;
run exactly the gates it names, ONE suite per call; logs under the phase dir; `04-0N-SUMMARY.md`; commit by pathspec
(`git add -- <paths>; git commit -F <msgfile> -- <paths>`, message file UTF-8 no BOM; verify `git log -1 --format=%s`).
Update DENOMINATOR rows only with evidence. At phase end re-run the Phase 2 suites (`test_gsd_x_goal_pcc_replay.py`
28/28, `test_gsd_x_goal_pcc_semantics.py` 48/48) and the Phase 3 frontier suite (40/40): Phase 4 must not regress them.
Laptop RAM is scarce (about 2.5 GB free). Mutation drills (`tools/mutation_drill.py`, isolated copy + control): write
each spec as JSON under the phase dir `drills/`, run them one per call; if a run is killed for memory, do NOT retry it
-- mark it UNRUN in the SUMMARY and go on. The coordinator runs UNRUN drills on the Linux plane (GEX44) and wakes you
with the results; record them labelled "Linux plane", never as laptop evidence.
After the last plan: `04-VERIFICATION.md` (run every human_verification check yourself; label each gate with its
plane), STATE.md to Phase 4 complete (`current_phase: 5`, status planning), tick ROADMAP Phase 4, commit.

## Budget
Envelope `route-P4.json`: target 65M, warn 70M, stop 75M, 450 calls (breaker: 675 tool calls). Phase 3 measured
36.5M over 286 calls. At SESSION BUDGET warn: finish and commit the current plan, then go STRAIGHT to the receipt.
Read burn only from `~/.claude/state/session-budget-<your sid>.state.json` (`tokens`, `calls`). Never
`run_in_background` for a check you need this turn; pass `timeout: 600000` on long PowerShell calls; never poll an
output file. Global batch caps apply.

## Done-gate for this unit (deterministic)
`04-VERIFICATION.md` frontmatter `status: passed`; every `04-0N-SUMMARY.md` present; Phase 2, 3 and 4 suites green as
run in the verification log; every drill KILLED with a valid control on some labelled plane; STATE.md
`current_phase: 5`; `git status --short` clean except `vault/progress.md` and `LEARNINGS_PENDING.md`.

## Receipt
Write `.planning/workstreams/gsdx-pcc/packets/WU-P4-receipt.md` (<= 25 lines): mission id; plans with commit ids; gate
lines verbatim (`*_PASS=`) with their plane; DENOMINATOR rows moved; drills with verdict and plane; deviations;
measured burn at end of Part A and at the end; open points; Phase 5 size estimate from this phase's evidence. Commit
it. End with exactly one line:
`HANDOFF NOTE: WU-P4 done -- Phase 5 (W4 judge VALIDATE vs REPLAY) ready to compile` or
`HANDOFF NOTE: WU-P4 PARTIAL -- <next plan id> -- <blocker>`.
