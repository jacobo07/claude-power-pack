# P05-T2 — Phase 5: Spend capability and precise lease states, Task 2 ONLY

You are in `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\evc` (branch `evc/e2`). Work only here.
Use the PowerShell tool for git and python. git = `& 'C:\Program Files\Git\cmd\git.exe'`,
python = `& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'`. Set `$env:PYTHONIOENCODING='utf-8'` first.
Never send two Edit calls to the same file in one message (refused on this host). No reset, clean, restore, stash, amend,
rebase, push or force. No subagents. No EnterWorktree. No questions. Budget: about 20 tool calls.

## Spec
`.planning/workstreams/evc/phases/05-spend-capability/05-PLAN.md`: read it once, then do ONLY `### Task 2:`. If that heading does not exist, write the receipt
`Status: DONE` with the line `NO_TASK: plan has fewer than 2 tasks` and stop (nothing else to commit).
Gates first and watch them FAIL (report which), then implement, then run every verify command the task lists.
Re-verify line anchors before editing: earlier units changed tools/gsd_mission.py and tools/mission_spend.py.
If the verify commands are not all exit 0 after 3 fix attempts: do not commit code; write the BLOCKED receipt with the
exact remaining step, and commit only the receipt.

## Receipt (mandatory, even when blocked) — the chain reads it
Write `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\evc\.planning\workstreams\evc\wave2\receipts\WU-P05-T2-receipt.md` with the Write tool. First line exactly `Status: DONE` or `Status: BLOCKED: <reason>`, then the
report lines below. Then commit it together with your work (or alone when blocked):
`git commit -m "<message>" -- <your files> ".planning/workstreams/evc/wave2/receipts/WU-P05-T2-receipt.md"`.

Commit message: `feat(evc-05): task 2 -- <task name>`. Files: only the task's files.
Report lines: `HEAD: <sha>`, `RED-FIRST: <which gates failed before the code>`, `VERIFY: <each command: exit + summary line>`.
