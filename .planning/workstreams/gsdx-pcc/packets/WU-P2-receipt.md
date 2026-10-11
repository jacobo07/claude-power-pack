# WU-P2 receipt -- mission m-e574a0e424e6 -- PARTIAL

- Plans: 02-01 (summary 142eafea), 02-02 (bafb0fad), 02-03 (63db7439), 02-04 (340c792d), 02-05 (f234ad16), 02-06 tasks a051673e, c8c58d91, 425db6d3, 0b46f2bd. HEAD 0b46f2bd.
- Gates: `GSDX_PCC_REPLAY_PASS=28/28` `GSDX_PCC_SEMANTICS_PASS=48/48`; 17 incumbent suites at Phase 1 counts, 0 DIFFERS; guard SAME; `gate offenders: 0`; 12/12 drills `MUTANT KILLED`.
- DENOMINATOR moved: D43 DONE, D44 DONE; D01, D03, D10 OPEN with Phase 2 evidence text.
- Deviations: two drill blind spots fixed once in the semantics suite (a051673e); copy_dirs gained the phase dir; fixture judge replay 4.8 s / 12.3 s vs Phase 1 0.4 s on a saturated host (OBSERVED, judge.py unchanged); UKDL append shows 1 EOF-newline "deletion". Detail in 02-06-SUMMARY.md.
- Burn: about 37.3M processed (warn 34.5M, stop 40M), 321 tool calls vs 210 estimated. The SESSION BUDGET BREAKER (320 > 1.5 x 210) then blocked PowerShell.
- NOT DONE, uncommitted in the worktree: `02-06-SUMMARY.md`, `02-VERIFICATION.md` (status: passed), STATE.md (`current_phase: 3`, edited), this receipt, the untracked `packets/` dir.
- NOT DONE: ROADMAP.md tick of the Phase 2 checkbox (line 53); the commit of the files above; the optional `pp-code-reviewer` pass (`02-REVIEW.md`).
- Open points: none beyond the above; D01/D03/D10 close in Phases 4/10; R12 fix is Phase 4.
- Next exact action: raise the envelope (`python tools/mission_spend.py session-declare ...`) or rotate, then run `git add -- <the files above>; git commit -F <msgfile> -- <the files above>`, subject `docs(gsdx-pcc-02): Phase 2 complete -- verification passed, STATE to Phase 3`, then tick ROADMAP line 53 and commit.
- Phase 3 size estimate: L, comparable to Phase 2 (about 30-37M tokens, about 6 plans); confidence low, zero calibration samples.

HANDOFF NOTE: WU-P2 PARTIAL -- commit Phase 2 close files (02-06-SUMMARY, 02-VERIFICATION, STATE, receipt) -- session budget breaker blocked PowerShell
