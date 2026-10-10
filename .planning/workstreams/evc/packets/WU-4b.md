# WU-4b — execute Phase 1 plan 01-02 (one spend/hold renderer; no frozen figure shown as current) on evc/e2

You are in `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\evc` (branch `evc/e2`). Work only here.
Use the PowerShell tool for git and python. git = `& 'C:\Program Files\Git\cmd\git.exe'`,
python = `& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'`. Set `$env:PYTHONIOENCODING='utf-8'` first.

Precondition: WU-4a (plan 01-01) is committed on this branch. Check with
`git log --oneline -5 --grep "evc-01-01"`; if fewer than 3 such commits exist, stop with BLOCKED: 01-01 not landed.

## The specification
`.planning/workstreams/evc/phases/01-usage-truth-plane/01-02-PLAN.md` is your full spec. Read it once, then do its
Tasks 1, 2 and 3 in order, gates first (watch them fail), then implementation. Its `<read_first>` lists are the only
other files you need; read only the line ranges they name, and re-verify the line anchors it gives before editing
(WU-1 and WU-3 changed tools/gsd_mission.py and tools/mission_spend.py since the plan was written).
Ignore its `<execution_context>` @-references and the 01-01-SUMMARY.md reference (not written; read the 01-01 commits instead).

## Overrides of the plan
- Commit once per task, by pathspec of that task's `<files>` only:
  `git commit -m "feat(evc-01-02): task <n> -- <name>" -- <files>`.
- Do NOT write 01-02-SUMMARY.md or any other planning document.
- If a task's verify commands do not all exit 0 after 3 fix attempts, stop with BLOCKED; earlier task commits stay.

## Never
No edits outside the task's `<files>`. No reset, clean, restore, stash, amend, rebase, push or force. No subagents.
No EnterWorktree. No questions.

## Report (your final message, nothing else)
```
WU-4b STATUS: DONE | BLOCKED:<task n: reason>
HEAD: <git rev-parse --short=8 HEAD>
COMMITS: <sha task1> <sha task2> <sha task3>
GATES: <final summary line of tools/test_evc_usage_truth.py>, exit <n>
REGRESSIONS: <each other verify command: exit code>
```
