# WU-3 — land dgl W1b + W2 (lease epochs, workspace registry, closed-lease fence) on evc/e2

You are in `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\evc` (branch `evc/e2`). Work only here.
Use the PowerShell tool for git and python. git = `& 'C:\Program Files\Git\cmd\git.exe'`,
python = `& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'`. Set `$env:PYTHONIOENCODING='utf-8'` first.

## Do exactly this, in this order (branch dgl/durable-goal-lease)
`git cherry-pick -x` each of: 58b83582 c5f22af9 1bfb30cf d3f397ff b2dc5812 db9c2153 47aa4d77 31f9b5f4

Conflicts:
- In `tools/mission_spend.py` (WU-1 already added autopsy/forecast there): keep BOTH sides; the dgl additions are new
  CLI subcommands and functions, the WU-1 ones are autopsy/forecast. Never delete either side.
- In any file under `vault/` or `.planning/` (plans, receipts): take the evc/e2 side (`git checkout --ours <path>`).
- Anything else, or a conflict you cannot resolve in 3 attempts: `git cherry-pick --abort` and stop with BLOCKED
  naming the commit and file. Commits already picked stay.
Then run once each, foreground: `python tools/test_goal_lease.py`, `python tools/test_workspace_lease.py`. Stop.

## Never
No other edits. No reset, clean, restore, stash, amend, rebase, push or force. No subagents. No EnterWorktree. No questions.

## Report (your final message, nothing else)
```
WU-3 STATUS: DONE | BLOCKED:<reason>
HEAD: <git rev-parse --short=8 HEAD>
PICKED: <count>/8 (<list of new shas>)
TEST test_goal_lease: exit <n> — <summary line>
TEST test_workspace_lease: exit <n> — <summary line>
```
DONE requires 8/8 picked and both tests exit 0.
