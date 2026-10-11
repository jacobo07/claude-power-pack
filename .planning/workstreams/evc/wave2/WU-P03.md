# P03 — write the compact plan for Phase 3: Work-class profiles and confidence

You are in `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\evc` (branch `evc/e2`). Work only here.
Use the PowerShell tool for git and python. git = `& 'C:\Program Files\Git\cmd\git.exe'`,
python = `& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'`. Set `$env:PYTHONIOENCODING='utf-8'` first.
Never send two Edit calls to the same file in one message (refused on this host). No reset, clean, restore, stash, amend,
rebase, push or force. No subagents. No EnterWorktree. No questions. Budget: about 15 tool calls.

## Read (only these)
- `.planning/workstreams/evc/ROADMAP.md`: the `### Phase 3: Work-class profiles and confidence` section and the `Deflation dispositions` table row for phase 3.
- `.planning/workstreams/evc/WAVE1-RECEIPT-2026-10-11.md` (what already exists).
- The code anchors you need, by Grep first, then Read of the exact line ranges only.

## Disposition (overrides the ROADMAP criteria where they conflict)
SHRINK: `tools/cost_to_completion.py` becomes the primary estimator; the [1M,15M]/2 auto envelope is kept only as a labelled emergency fallback; add the confidence states (UNKNOWN/EXPLORATORY/PROVISIONAL/CALIBRATED/DEGRADED/INVALIDATED) and the miss taxonomy. Reuse `vault/config/route-floors.json` profiles and `route_admission.record_actual` misses.

## Write `.planning/workstreams/evc/phases/03-work-class-profiles/03-PLAN.md` (at most 120 lines)
At most 3 tasks, numbered `### Task 1:` .. `### Task 3:`, each executable alone by a fresh worker in about 20 tool calls:
name; files (exact paths); gates first (named V-EVC-* checks in `tools/test_evc_<topic>.py` or an existing test file,
each with the input that makes it RED before the code exists and a positive control); implementation steps with the
exact functions and line anchors; verify commands (`python tools\test_x.py` lines) including the existing suites that
must stay green. No GSD workflow references, no STRIDE section, no research section.

## Receipt (mandatory, even when blocked) — the chain reads it
Write `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\evc\.planning\workstreams\evc\wave2\receipts\WU-P03-receipt.md` with the Write tool. First line exactly `Status: DONE` or `Status: BLOCKED: <reason>`, then the
report lines below. Then commit it together with your work (or alone when blocked):
`git commit -m "<message>" -- <your files> ".planning/workstreams/evc/wave2/receipts/WU-P03-receipt.md"`.

Commit message: `docs(evc-03): compact plan`. Files: `.planning/workstreams/evc/phases/03-work-class-profiles/03-PLAN.md`.
Report lines: `PLAN: .planning/workstreams/evc/phases/03-work-class-profiles/03-PLAN.md`, `TASKS: <n>`.
