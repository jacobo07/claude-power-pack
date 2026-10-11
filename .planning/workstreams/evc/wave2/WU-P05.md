# P05 — write the compact plan for Phase 5: Spend capability and precise lease states

You are in `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\evc` (branch `evc/e2`). Work only here.
Use the PowerShell tool for git and python. git = `& 'C:\Program Files\Git\cmd\git.exe'`,
python = `& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'`. Set `$env:PYTHONIOENCODING='utf-8'` first.
Never send two Edit calls to the same file in one message (refused on this host). No reset, clean, restore, stash, amend,
rebase, push or force. No subagents. No EnterWorktree. No questions. Budget: about 15 tool calls.

## Read (only these)
- `.planning/workstreams/evc/ROADMAP.md`: the `### Phase 5: Spend capability and precise lease states` section and the `Deflation dispositions` table row for phase 5.
- `.planning/workstreams/evc/WAVE1-RECEIPT-2026-10-11.md` (what already exists).
- The code anchors you need, by Grep first, then Read of the exact line ranges only.

## Disposition (overrides the ROADMAP criteria where they conflict)
SHRINK: an Owner hold / SUSPENDED / cost-breaker trip writes the live worker's session-budget deny file (`~/.claude/state/session-budget-<sid>.json`, stop=1 — the U0 mechanism, measured to work) so the guard refuses its next gated tool call; RELAY_HELD is never displayed as paused; the guard counts subagent transcripts. All gates hermetic (temp dirs, injected state): NO live canary here (that is Phase 9).

## Write `.planning/workstreams/evc/phases/05-spend-capability/05-PLAN.md` (at most 120 lines)
At most 3 tasks, numbered `### Task 1:` .. `### Task 3:`, each executable alone by a fresh worker in about 20 tool calls:
name; files (exact paths); gates first (named V-EVC-* checks in `tools/test_evc_<topic>.py` or an existing test file,
each with the input that makes it RED before the code exists and a positive control); implementation steps with the
exact functions and line anchors; verify commands (`python tools\test_x.py` lines) including the existing suites that
must stay green. No GSD workflow references, no STRIDE section, no research section.

## Receipt (mandatory, even when blocked) — the chain reads it
Write `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\evc\.planning\workstreams\evc\wave2\WU-P05-receipt.md` with the Write tool. Lines 1-3 are a fixed title block and nothing else: `Status: DONE` (or `Status: BLOCKED: <reason>`),
`Unit: <unit id>`, `HEAD: <git rev-parse --short=8 HEAD>`. Line 4 blank. Report lines from line 5 on
(the receipt judge reads lines 1-3; evidence words there, e.g. 'stub', misjudge the receipt). Then commit it together with your work (or alone when blocked):
`git commit -m "<message>" -- <your files> ".planning/workstreams/evc/wave2/receipts/WU-P05-receipt.md"`.

Commit message: `docs(evc-05): compact plan`. Files: `.planning/workstreams/evc/phases/05-spend-capability/05-PLAN.md`.
Report lines: `PLAN: .planning/workstreams/evc/phases/05-spend-capability/05-PLAN.md`, `TASKS: <n>`.
