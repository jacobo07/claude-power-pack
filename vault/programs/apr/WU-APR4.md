# WU-APR4 -- Install live, EWC config, independent review

Common brief: `PROGRAMME.md`. Read `WU-APR2-receipt.md`, `WU-APR3-receipt.md` first. Route M. cwd
`C:\Users\User\Apps\wt_apr`. This is the only unit that writes code into the live checkout.

Steps:
1. Independent review BEFORE install. Dispatch ONE `pp-code-reviewer` agent (solo in its message; bounded prompt;
   write-as-you-go findings file `vault/programs/apr/REVIEW-APR.md`; "Prefer Read/Grep/Glob; avoid Bash, use
   PowerShell"), scope `git -C C:\Users\User\Apps\wt_apr diff 7501d939..HEAD -- tools`. When it returns, ONE `woz`
   agent the same way on `tools/gsdx_chain.py` only. Ask both to hunt: a seal on incomplete work, a FALSE_DONE that
   advances, double arm under event+tick, an unbounded retry, a silent stall with no alert, a budget escape, a chain
   without the new fields behaving differently. A reviewer that ran no checks cannot approve. Fix every HIGH/CRITICAL
   in wt_apr (commit), record MEDIUM/LOW dispositions in the review file.
2. Backward-compat snapshot: BEFORE install, run `tools/gsdx_chain.py tick --chain <c> --dry-run` with the LIVE code for
   every `vault/programs/*/chain.json` in the live checkout; save the actions to `vault/programs/apr/install-before.json`.
3. Install: for each APR commit not yet in the live checkout (APR-1 is already there as 741479f3), verify the touched
   files are clean in the live checkout and untouched by other commits since 7501d939, then `git cherry-pick` it there
   (live branch feature/knowledge-acquisition). If a file is dirty or moved, STOP that commit and record why -- never
   stash or reset another pane's work.
4. After install: the same dry-run over every chain -> `install-after.json`. Every action must be identical unless the
   difference is explained by a new field that chain declares (none do yet). Then run, from the live checkout, every
   suite named in WU-APR2/APR3. Any difference without a reason = revert your cherry-pick (`git revert`, not reset).
5. EWC config (Owner-approved): in `vault/programs/ewc/chain.json` set `"max_residuals": 2`; add `acceptance` blocks
   for EWC units NOT yet armed whose packets name a deterministic gate (read each WU-E*.md; use the exact test command
   the packet names, cwd `C:\Users\User\Apps\wt_ewc`). Where no deterministic gate exists, add none and say so. Do not
   touch a unit whose mission is running. Commit chain.json alone (pathspec), then a dry-run tick of ewc must not
   change its current action.
6. Register `PP-AprChain-Tick` if it is missing, cloned from `PP-EwcChain-Tick` (same wscript + hidden_launch.vbs
   pattern, 10 min, IgnoreNew, 15 min limit) pointing at `vault/programs/apr/chain_tick.ps1` -- only if the
   coordinator did not already register it (check first).
Receipt: review verdicts + every finding's disposition; installed commit ids in the live checkout; before/after diff
(expected empty); EWC chain.json commit; suites + counts from the live checkout.
