# WU-4a — execute Phase 1 plan 01-01 (usage truth reader + gate scaffold) on evc/e2

You are in `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\evc` (branch `evc/e2`). Work only here.
Use the PowerShell tool for git and python. git = `& 'C:\Program Files\Git\cmd\git.exe'`,
python = `& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'`. Set `$env:PYTHONIOENCODING='utf-8'` first.

## The specification
`.planning/workstreams/evc/phases/01-usage-truth-plane/01-01-PLAN.md` is your full spec. Read it once, then do its
Tasks 1, 2 and 3 in order, writing each task's gates first and watching them fail before implementing (as it says).
Its `<read_first>` lists are the only other files you need; read only the line ranges they name.
Ignore its `<execution_context>` @-references (GSD workflow files): you are not running GSD.

## Overrides of the plan
- Commit once per task, by pathspec of that task's `<files>` only:
  `git commit -m "feat(evc-01-01): task <n> -- <name>" -- <files>`. (The plan says "do not commit"; this packet overrides it.)
- Do NOT write 01-01-SUMMARY.md or any other planning document.
- If a task's verify commands do not all exit 0 after 3 fix attempts, stop with BLOCKED; earlier task commits stay.

## Never
No edits outside the task's `<files>`. No reset, clean, restore, stash, amend, rebase, push or force. No subagents.
No EnterWorktree. No questions.

## Report (your final message, nothing else)
```
WU-4a STATUS: DONE | BLOCKED:<task n: reason>
HEAD: <git rev-parse --short=8 HEAD>
COMMITS: <sha task1> <sha task2> <sha task3>
GATES: <final summary line of tools/test_evc_usage_truth.py>, exit <n>
REGRESSIONS: <each other verify command of task 3: exit code>
```
