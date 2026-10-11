# P04 — write the compact plan for Phase 4: Distribution forecast and live reforecast

You are in `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\evc` (branch `evc/e2`). Work only here.
Use the PowerShell tool for git and python. git = `& 'C:\Program Files\Git\cmd\git.exe'`,
python = `& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'`. Set `$env:PYTHONIOENCODING='utf-8'` first.
Never send two Edit calls to the same file in one message (refused on this host). No reset, clean, restore, stash, amend,
rebase, push or force. No subagents. No EnterWorktree. No questions. Budget: about 15 tool calls.

## Read (only these)
- `.planning/workstreams/evc/ROADMAP.md`: the `### Phase 4: Distribution forecast and live reforecast` section and the `Deflation dispositions` table row for phase 4.
- `.planning/workstreams/evc/WAVE1-RECEIPT-2026-10-11.md` (what already exists).
- The code anchors you need, by Grep first, then Read of the exact line ranges only.

## Disposition (overrides the ROADMAP criteria where they conflict)
`tools/gsdx_reforecast.py` is ALREADY landed (f397d014). Remaining: lower/P50/P80/P95/ceiling output with confidence (WIDE/UNKNOWN when the sample is small) and the predictive DRAINING edge (spent + P95 remaining > authority -> DRAINING before the hard breaker), with a gate that drives it. Fix the hardcoded LIVE mission_spend path in gsdx_reforecast.py.

## Write `.planning/workstreams/evc/phases/04-distribution-reforecast/04-PLAN.md` (at most 120 lines)
At most 3 tasks, numbered `### Task 1:` .. `### Task 3:`, each executable alone by a fresh worker in about 20 tool calls:
name; files (exact paths); gates first (named V-EVC-* checks in `tools/test_evc_<topic>.py` or an existing test file,
each with the input that makes it RED before the code exists and a positive control); implementation steps with the
exact functions and line anchors; verify commands (`python tools\test_x.py` lines) including the existing suites that
must stay green. No GSD workflow references, no STRIDE section, no research section.

## Receipt (mandatory, even when blocked) — the chain reads it
Write `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\evc\.planning\workstreams\evc\wave2\receipts\WU-P04-receipt.md` with the Write tool. First line exactly `Status: DONE` or `Status: BLOCKED: <reason>`, then the
report lines below. Then commit it together with your work (or alone when blocked):
`git commit -m "<message>" -- <your files> ".planning/workstreams/evc/wave2/receipts/WU-P04-receipt.md"`.

Commit message: `docs(evc-04): compact plan`. Files: `.planning/workstreams/evc/phases/04-distribution-reforecast/04-PLAN.md`.
Report lines: `PLAN: .planning/workstreams/evc/phases/04-distribution-reforecast/04-PLAN.md`, `TASKS: <n>`.


## Residual
Written by the steward for stopped mission m-ffa17244be6b. The programme chain may arm it (bounded residual re-arm); otherwise the Owner/coordinator does.
Continue from the work below; do not redo steps it already covers. Commit early.
- Partial receipt: C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\evc\.planning\workstreams\evc\wave2\WU-P04.md.partial.json
- RESUMPTION_FILE: none written by this mission
- Salvage: C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\evc\vault\specs\salvage\m-ffa17244be6b
- Uncommitted in the tree (35): ?? .planning/workstreams/evc/packets/WU-1.md.partial.json; ?? .planning/workstreams/evc/packets/WU-1.md.residual.md; ?? .planning/workstreams/evc/packets/WU-2.md.partial.json; ?? .planning/workstreams/evc/packets/WU-2.md.residual.md; ?? .planning/workstreams/evc/packets/WU-3.md.partial.json; ?? .planning/workstreams/evc/packets/WU-3.md.residual.md; ?? .planning/workstreams/evc/packets/WU-4a-t1.md.partial.json; ?? .planning/workstreams/evc/packets/WU-4a-t1.md.residual.md; ?? .planning/workstreams/evc/packets/WU-4a-t2.md.partial.json; ?? .planning/workstreams/evc/packets/WU-4a-t2.md.residual.md; ?? .planning/workstreams/evc/packets/WU-4a-t3.md.partial.json; ?? .planning/workstreams/evc/packets/WU-4a-t3.md.residual.md; ?? .planning/workstreams/evc/packets/WU-4b-t1.md.partial.json; ?? .planning/workstreams/evc/packets/WU-4b-t1.md.residual.md; ?? .planning/workstreams/evc/packets/WU-4b-t1c.md.partial.json; ?? .planning/workstreams/evc/packets/WU-4b-t1c.md.residual.md; ?? .planning/workstreams/evc/packets/WU-4b-t2.md.partial.json; ?? .planning/workstreams/evc/packets/WU-4b-t2.md.residual.md; ?? .planning/workstreams/evc/packets/WU-4b-t2c.md.partial.json; ?? .planning/workstreams/evc/packets/WU-4b-t2c.md.residual.md; ?? .planning/workstreams/evc/packets/WU-4b-t3.md.partial.json; ?? .planning/workstreams/evc/packets/WU-4b-t3.md.residual.md; ?? .planning/workstreams/evc/wave2/WU-P03-T1.md.partial.json; ?? .planning/workstreams/evc/wave2/WU-P03-T1.md.residual.md; ?? .planning/workstreams/evc/wave2/WU-P03-T2.md.partial.json; ?? .planning/workstreams/evc/wave2/WU-P03-T2.md.residual.md; ?? .planning/workstreams/evc/wave2/WU-P03-T3.md.partial.json; ?? .planning/workstreams/evc/wave2/WU-P03-T3.md.residual.md; ?? .planning/workstreams/evc/wave2/WU-P03.md.partial.json; ?? .planning/workstreams/evc/wave2/WU-P03.md.residual.md; ?? .planning/workstreams/evc/wave2/WU-P04.md.partial.json; ?? .planning/workstreams/evc/wave2/WU-P04.md.residual.md; ?? .pp-capabilities; ?? vault/programs/dgl/chain.json; ?? vault/specs/salvage/
