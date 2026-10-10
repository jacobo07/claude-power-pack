# WU-1 — land cost-collapse T1 + T2 on evc/e2

You are in `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\evc` (branch `evc/e2`). Work only here.
Use the PowerShell tool for git and python. git = `& 'C:\Program Files\Git\cmd\git.exe'`,
python = `& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'`. Set `$env:PYTHONIOENCODING='utf-8'` first.

## Do exactly this
1. `git cherry-pick -x f3b503e6` (T1: tools/gsd_mission.py, tools/test_grammar_default.py).
2. `git cherry-pick -x 2b5b0ea5` (T2: tools/mission_spend.py autopsy + forecast, tools/test_autopsy.py, 2 fixtures under vault/specs/fixtures/).
3. If a cherry-pick conflicts: resolve only inside the files that commit touches, keeping BOTH sides' behaviour;
   `git add` those paths; `git cherry-pick --continue`. If you cannot resolve it in 3 attempts:
   `git cherry-pick --abort` and stop with the report below (status BLOCKED).
4. Run, foreground, each once:
   - `python tools/test_grammar_default.py`
   - `python tools/test_autopsy.py`
   Record the exit code and the final summary line of each.
5. Stop.

## Never
No other edits. No reset, clean, restore, stash, amend, rebase, push or force. Do not touch `C:\Users\User\Apps\pp-evc`
or the live checkout. No subagents. No EnterWorktree. Do not ask questions.

## Report (your final message, nothing else)
```
WU-1 STATUS: DONE | BLOCKED:<reason>
HEAD: <git rev-parse --short=8 HEAD>
PICKED: <new sha for f3b503e6> <new sha for 2b5b0ea5>
TEST test_grammar_default: exit <n> — <summary line>
TEST test_autopsy: exit <n> — <summary line>
```
DONE requires both picks landed and both tests exit 0.
