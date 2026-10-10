# Autonomy Convergence -- common brief for every unit worker

Binding plan: `vault/plans/autonomy-convergence-MASTER-PLAN-2026-10-10.md` (68432ebe, Owner "y" 2026-10-10). Read
sections 1-4 once; your unit packet names the section that is yours. No orchestrator exists above you. The chain
(`chain.json` here, ticked by a zero-model scheduled task) arms the next unit when your receipt says DONE.

## Session loop
1. Work in `C:\Users\User\Apps\pp-ucda-wt` (branch feat/ucda). Do your unit: tests first, then code, pathspec
   micro-commits, Co-Authored-By line from the commit attribution. Never `git add -A`.
2. Close: overwrite your receipt `WU-<id>-receipt.md` beside your packet. Line 1 `# <id> receipt`, line 2
   `Status: DONE`, then commits, PROVEN / NOT_PROVEN / BLOCKED_* / INCONCLUSIVE per claim, calls used, what the next
   unit must know (<= 8 lines). Commit it.
3. **Unit too big for one session** (reserve rule: stop starting new work at 85 % of your calls): commit what is
   done, INSERT a continuation unit into `chain.json` IMMEDIATELY AFTER your own entry (id `<id>b`, `<id>c`...,
   `after` = your id, its own packet `WU-<id>b.md` stating exactly the remaining steps, same route, receipt beside it),
   then write your receipt `Status: DONE` (slice done) and commit packet + chain + receipt together. Never leave
   uncommitted work. Never write PARTIAL: the chain does not re-arm a unit that ended without DONE.
4. Blocked on something only the Owner can do: receipt `Status: BLOCKED_HUMAN` with the exact action. That stops the
   chain on purpose.

## Hard constraints
- Windows: git/python via the PowerShell tool, absolute paths (`C:\Program Files\Git\cmd\git.exe`,
  `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`). No Bash for git/python. No `Agent`, no GSD
  fan-out, no `/gsd-autonomous`, no `EnterWorktree` (you are already in the worktree).
- Live PP `C:\Users\User\.claude\skills\claude-power-pack` (branch feature/knowledge-acquisition, ~936 dirty paths,
  other writers): never edit it directly. Change it only by landing feat/ucda: rebase onto the then-current live HEAD,
  overlap check against live dirty paths, declared tests, `merge --ff-only`, in ONE command (S1 makes this a tool;
  use the tool once it exists). Never push. Other worktrees (pp-cost-collapse, pp-gsdx-factory-2, pp-dgl, pp-evc):
  read and cherry-pick only, never write into them.
- Sidecar Live QA (`C:\Users\User\Apps\io-liveqa`) is PRODUCT: read-only for this programme. Do not arm its missions.
- No GEX44 deploy, no Hermes install, no credential work, no push. Those are Owner-only.
- Missing state is not success; UNKNOWN spend is not zero; never write PASS for an unobserved claim.
- Every new guard ships with a test that drives its red branch (mutation drill).

## Reserve rule, measured (2026-10-10, S5 halted twice)
The session breaker stops a worker at 1.5 x the route's 30 calls (45) and then refuses writes outside `vault/plans/*.md`,
so a receipt or a chain edit after that point is impossible. Count your calls: at call 22 stop starting new work, at
call 25 at the latest insert the continuation unit and write the receipt. Investigation counts as calls.
