# WU-4b-t1 — Phase 1 plan 01-02, Task 1 ONLY, on evc/e2

You are in `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\evc` (branch `evc/e2`). Work only here.
Use the PowerShell tool for git and python. git = `& 'C:\Program Files\Git\cmd\git.exe'`,
python = `& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'`. Set `$env:PYTHONIOENCODING='utf-8'` first.

Precondition: `git log --oneline -20 --grep "evc-01-02: task"` must show 0 commit(s) and plan 01-01 must show 3 commits (--grep "evc-01-01: task"). If not, stop: BLOCKED precondition.

## The specification
`.planning/workstreams/evc/phases/01-usage-truth-plane/01-02-PLAN.md`: read its frontmatter, `<objective>`, `<context>`
and ONLY `Task 1` (the `<task>` block whose `<name>` starts "Task 1:"). Do that task exactly: gates first (watch them
fail), then implementation, then its `<verify>` commands. Read only the files and line ranges its `<read_first>` names, and
re-verify any line anchor before editing (earlier units changed tools/gsd_mission.py and tools/mission_spend.py).
Ignore `<execution_context>` @-references and any *-SUMMARY.md reference (not written; read the earlier task commits instead).
Do NOT start any other task.

## Finish
Commit by pathspec of that task's `<files>` only: `git commit -m "feat(evc-01-02): task 1 -- <task name>" -- <files>`.
No planning documents. If the verify commands do not all exit 0 after 3 fix attempts, stop with BLOCKED and do not commit.

## Never
No edits outside the task's `<files>`. No reset, clean, restore, stash, amend, rebase, push or force. No subagents.
No EnterWorktree. No questions.

## Report (your final message, nothing else)
```
WU-4b-t1 STATUS: DONE | BLOCKED:<reason>
HEAD: <git rev-parse --short=8 HEAD>
COMMIT: <sha or none>
VERIFY: <each verify command: exit code and its final summary line>
```