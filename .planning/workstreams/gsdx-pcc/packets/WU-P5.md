# WU-P5 -- GSD X proof-conserving convergence, Phase 5 (W4 judge VALIDATE vs REPLAY, parallel replay, reviewer concurrency): PLAN, then EXECUTE

Mission: the id on your rehydration card (write it in the receipt). Follows m-3964348fe5e4 (Phase 4 DONE, dc590090;
coordinator re-anchored two mutation drills in f5337729, Linux plane 58/58).
Authority: Owner, 2026-10-13 chat: "approve 80M" -- 80M for the whole of Phase 5 (planning + execution).
cwd `C:\Users\User\Apps\pp-gsdx-pcc`, branch `gsdx/pcc`, workstream `gsdx-pcc`. UNATTENDED: nobody answers questions.

## Never
- Write the main checkout `C:\Users\User\.claude\skills\claude-power-pack`, `io-chatgpt-plugin`, `io-ucg`, or anything
  under `C:\Users\User\.claude` (global hooks/skills/settings). Never push. Never arm a mission. Never ssh to another
  host. Never plan or execute the repo's ROOT milestone (it belongs to another track). Never start Phase 6.
- Run `/gsd-discuss-phase` or anything that asks the Owner questions. Re-litigate STATE.md Decisions, Phase 2's
  resolved semantics (spec S1-S16), Phase 3's frontier contract or Phase 4's inheritance contract (their VERIFICATIONs).
- End a turn on a question. A decision the mission card's DECISION GATE reserves to the Owner goes into STATE.md as
  `OWNER DECISION NEEDED` (question, options, your pick); then continue with other runnable work.
- Weaken a gate, mark UNKNOWN as PASS, let a builder certify its own work, or drop a red branch to save calls.
- Run `tools/test_gsd_x_goal_mutation.py` on the laptop: it mutates LIVE files and a timeout kill left `judge.py`
  mutated in Phase 4. If a plan edits a line that suite anchors on (grep its anchors first), re-anchor that drill to
  the new line with the SAME mutant and gate, record it in the SUMMARY, and list the suite as UNRUN for the coordinator.

## Start (first 3 calls)
1. `node ~/.claude/gsd-core/bin/gsd-tools.cjs query workstream.set gsdx-pcc --raw --cwd .`
2. `git status --short; git log --oneline -5` (the repository wins over this packet).
3. Read, in order: ROADMAP.md operating constraints and the Phase 5 entry (Requirements D15 D16 D17 R05), STATE.md,
   DENOMINATOR.md rows Phase 5 owns, `phases/04-*/04-VERIFICATION.md`, the spec sections Phase 5 needs. Do not reread
   02-RESEARCH.md (92 KB) or the 2111-line dataset end to end; open only cited lines/sections.
If `phases/05-*/05-0N-PLAN.md` files already exist, skip straight to the first plan with no SUMMARY.

## Part A -- plan (budget: finish by ~15M processed)
Write into `phases/05-w4-judge-validate-vs-replay-parallel-replay-reviewer-concurrency/`, committing each artifact as
it lands (write as you go; the breaker refuses 25 calls without an edit or commit):
1. `05-CONTEXT.md`: scope from the ROADMAP Phase 5 entry; every gray area decided by you with a one-line reason
   (no Owner questions); the RED list verbatim (builder self-certification; gate weakening accepted; stale review
   surviving mutation), plus the A->B->A hole in evidence_bundle that success criterion 2 must close.
2. `05-RESEARCH.md`, <= 25 KB: premise-verify every function/module the plans will touch (HR-PREMISE-001), with
   file:line evidence; reuse Phase 2-4 seams (`proof.py`, the PCC events, `frontier.py`, `inherit.py`, candidate
   snapshots) rather than new stores. `judge.py` was untouched by Phase 4: read it before planning around it.
3. `05-0N-PLAN.md` (aim 4-6 plans, sequential waves, each with RED-first tasks, named gates, files, done criteria)
   and `05-VALIDATION.md`. Parallel replay is bounded: name the bound and how it is lowered under memory pressure.
4. One `gsd-plan-checker` agent (Sonnet, solo in its message, bounded, "Prefer Read/Grep/Glob; avoid Bash, use
   PowerShell", findings to `05-PLAN-CHECK.md`). Fix blockers in place; record dispositions. One iteration only.
Research/planning subagents are allowed only for read-and-write-a-file work (they have no PowerShell); you commit.

## Part B -- execute
Same rules as WU-P4: plans 05-01..05-0N in order, INLINE with PowerShell. For each plan: RED first where it says so;
run exactly the gates it names, ONE suite per call; logs under the phase dir; `05-0N-SUMMARY.md`; commit by pathspec
(`git add -- <paths>; git commit -F <msgfile> -- <paths>`, message file UTF-8 no BOM; verify `git log -1 --format=%s`).
Update DENOMINATOR rows only with evidence. At phase end re-run the Phase 2 suites (`test_gsd_x_goal_pcc_replay.py`
28/28, `test_gsd_x_goal_pcc_semantics.py` 48/48), the Phase 3 frontier suite (40/40) and the Phase 4 invalidation
suite (26/26): Phase 5 must not regress them.
Laptop RAM is scarce. Mutation drills (`tools/mutation_drill.py`, isolated copy + control): write each spec as JSON
under the phase dir `drills/`, run them one per call; if a run is killed for memory, do NOT retry it -- mark it UNRUN
in the SUMMARY and go on. The coordinator runs UNRUN drills and the goal mutation suite on the Linux plane (GEX44);
record such results labelled "Linux plane", never as laptop evidence.
After the last plan: `05-VERIFICATION.md` (run every human_verification check yourself; label each gate with its
plane), STATE.md to Phase 5 complete (`current_phase: 6`, status planning), tick ROADMAP Phase 5, commit.

## Budget
Envelope `route-P5.json`: target 70M, warn 75M, stop 80M, 480 calls (breaker: 720 tool calls). Phases 3 and 4
measured about 37M each over about 300 calls. At SESSION BUDGET warn: finish and commit the current plan, then go
STRAIGHT to the receipt. Read burn only from `~/.claude/state/session-budget-<your sid>.state.json` (`tokens`,
`calls`). Never `run_in_background` for a check you need this turn; pass `timeout: 600000` on long PowerShell calls;
never poll an output file. Global batch caps apply.

## Done-gate for this unit (deterministic)
`05-VERIFICATION.md` frontmatter `status: passed`; every `05-0N-SUMMARY.md` present; Phase 2-5 suites green as run in
the verification log; every drill KILLED with a valid control on some labelled plane, or listed UNRUN for the
coordinator; STATE.md `current_phase: 6`; `git status --short` clean except `vault/progress.md` and
`LEARNINGS_PENDING.md`.

## Receipt
Write `.planning/workstreams/gsdx-pcc/packets/WU-P5-receipt.md` (<= 25 lines): mission id; plans with commit ids; gate
lines verbatim (`*_PASS=`) with their plane; DENOMINATOR rows moved; drills with verdict and plane; items left for the
coordinator's Linux run; deviations; measured burn at end of Part A and at the end; open points; Phase 6 size
estimate from this phase's evidence. Commit it. End with exactly one line:
`HANDOFF NOTE: WU-P5 done -- Phase 6 (W5 mutant farm) ready to compile` or
`HANDOFF NOTE: WU-P5 PARTIAL -- <next plan id> -- <blocker>`.
After that commit, end the session: no further work in this unit.
