# WU-P2 -- GSD X proof-conserving convergence, Phase 2 (W1 convergence semantics): EXECUTE the 6 committed plans

Mission: the id on your rehydration card (write it in the receipt). Supersedes m-53847a002b65 (HALTED under the
2026-10-07 economic hold). Authority: Owner "approve everything", 2026-10-11 chat, to the coordinator's proposal: release
the hold, resume in the compiled grammar, ~40M cap for Phase 2 only, then re-forecast Phase 3 from Phase 2's measured burn.
cwd `C:\Users\User\Apps\pp-gsdx-pcc`, branch `gsdx/pcc`, workstream `gsdx-pcc`. UNATTENDED: nobody answers questions.

## Never
- Write the main checkout `C:\Users\User\.claude\skills\claude-power-pack`, `io-chatgpt-plugin`, `io-ucg`, or anything
  under `C:\Users\User\.claude` (global hooks/skills/settings). Never push. Never arm a mission. Never plan or execute the
  repo's ROOT milestone (it belongs to another track).
- Re-plan Phase 2, re-run its research, or re-litigate STATE.md Decisions. The plans are checked (02-PLAN-CHECK.md:
  0 blockers, all dispositions applied). A plan defect found while executing is fixed in place, recorded as a
  deviation in that plan's SUMMARY, and execution continues.
- End a turn on a question. A decision the mission card's DECISION GATE reserves to the Owner goes into STATE.md as
  `OWNER DECISION NEEDED` (question, options, your pick); then continue with other runnable work.
- Weaken a gate, mark UNKNOWN as PASS, or drop a red branch to save calls.

## Start (first 3 calls)
1. `node ~/.claude/gsd-core/bin/gsd-tools.cjs query workstream.set gsdx-pcc --raw --cwd .`
2. `git status --short; git log --oneline -5` (the repository wins over this packet).
3. Read, in order: `vault/specs/gsdx-proof-conserving-convergence.md` (only the sections the plan you are executing
   cites), `.planning/workstreams/gsdx-pcc/ROADMAP.md` operating constraints, `STATE.md`, then
   `phases/02-w1-convergence-semantics-ultra-plan-the-only-one/02-CONTEXT.md` and `02-0N-PLAN.md` for the next plan
   with no `02-0N-SUMMARY.md`. Do NOT read 02-RESEARCH.md (92 KB) end to end; open only the lines a plan cites. Do not
   reread the 2111-line dataset; open only the section numbers a DENOMINATOR row cites.

## Work
Execute 02-01 .. 02-06 in order (6 sequential waves), INLINE in this session with PowerShell -- the same choice Phase 1
made (subagents have no PowerShell; the Windows Bash guard blocks git/python there). For each plan:
- RED first where the plan says so; run exactly the gates the plan names; keep logs under the phase dir as Phase 1 did.
- Write `02-0N-SUMMARY.md`, then commit by pathspec (`git add -- <paths>; git commit -F <msgfile> -- <paths>`), message
  file written with UTF-8 no BOM; verify `git log -1 --format=%s` matches. One coherent verified delta per commit.
- Update the DENOMINATOR rows the plan closes, with evidence (commit + log path). Rows only move with evidence.
After 02-06: phase verification (`02-VERIFICATION.md`; run every human_verification check yourself), set STATE.md
frontmatter to Phase 2 complete, run the GSD transition to Phase 3, commit.

Optional, only if budget remains below the warn line: one `pp-code-reviewer` agent (solo in its message, bounded,
"Prefer Read/Grep/Glob; avoid Bash, use PowerShell", findings file `phases/02-.../02-REVIEW.md`) over
`git diff 7a3223a1..HEAD -- modules tools`. Fix HIGH/CRITICAL, record MEDIUM/LOW dispositions.

## Budget
Envelope in `route-P2.json` (target 30M, warn 34.5M, stop 40M). When the SESSION BUDGET warn advisory appears, finish
and commit the current plan, then go STRAIGHT to the receipt. Never `run_in_background` for a check you need this turn;
pass `timeout: 600000` on long PowerShell calls; never poll an output file. Batch caps from the global CLAUDE.md apply.

## Done-gate for this unit (deterministic)
`02-VERIFICATION.md` frontmatter `status: passed`; every `02-0N-SUMMARY.md` present; the phase's own suites green as
run in the verification log; STATE.md `current_phase: 3`; `git status --short` clean except `vault/progress.md`.

## Receipt
Write `.planning/workstreams/gsdx-pcc/packets/WU-P2-receipt.md` (<= 25 lines): mission id; plans done with commit ids;
gate lines verbatim (`*_PASS=` lines); DENOMINATOR rows moved; deviations; measured burn if visible; open points; the
Phase 3 size estimate from this phase's evidence. Commit it. End with exactly one line:
`HANDOFF NOTE: WU-P2 done -- Phase 3 (W2 execution frontier) ready to compile` or
`HANDOFF NOTE: WU-P2 PARTIAL -- <next plan id> -- <blocker>`.
