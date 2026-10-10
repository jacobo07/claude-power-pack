# WU-2 — land gsdx_reforecast (610808c5) on evc/e2

You are in `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\evc` (branch `evc/e2`). Work only here.
Use the PowerShell tool for git and python. git = `& 'C:\Program Files\Git\cmd\git.exe'`,
python = `& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'`. Set `$env:PYTHONIOENCODING='utf-8'` first.

## Do exactly this
1. `git cherry-pick -x 610808c5` (adds tools/gsdx_reforecast.py and tools/test_gsdx_reforecast.py only).
   It comes from branch gsdx-factory/v2: pick THIS commit only, never merge or pick anything else from that branch.
2. If it fails because an import the tool needs does not exist on this branch: `git cherry-pick --abort` and stop with
   status BLOCKED naming the missing module. Do not write the missing module.
3. Run once, foreground: `python tools/test_gsdx_reforecast.py`. Record exit code and final summary line.
4. Stop.

## Never
No other edits. No reset, clean, restore, stash, amend, rebase, push or force. No subagents. No EnterWorktree. No questions.

## Report (your final message, nothing else)
```
WU-2 STATUS: DONE | BLOCKED:<reason>
HEAD: <git rev-parse --short=8 HEAD>
PICKED: <new sha>
TEST test_gsdx_reforecast: exit <n> — <summary line>
```
DONE requires the pick landed and the test exit 0.
