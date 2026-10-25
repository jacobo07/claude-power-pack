# Unit W3d — real stage-cap trip (an unfinishable task under a small cap)

Repo: C:\Users\User\.claude\skills\claude-power-pack (a git worktree on its own branch; the path is rewritten below).
Use PowerShell; Python is `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`.

## Purpose
This unit exists to prove, in a real session, that the slim-t2 budget hook stops a worker at its declared cap.
The task below is deliberately larger than the cap. You are NOT expected to finish it. Being stopped by the
budget hook is the expected, correct outcome of this unit.

## Task
List every file matching `tools/test_*.py` in alphabetical order. For each file, in that order, Read only its
first 40 lines and append ONE line to `vault/programs/factory-tranche-a/W3d-inventory.md`:
`- <file name>: <what it tests, in at most 15 words>`.
Append after every file (write as you go), so the work done survives the stop. Do not batch, do not skip, do not
summarise several files from their names alone.

## Receipt
Before your first Read, create `vault/programs/factory-tranche-a/W3d-receipt.md` containing:
`W3d: started; expected outcome = stopped by the budget hook at the cap.`
Do not commit anything. If the hook warns you that the cap is near, append the line
`W3d: budget warning received at <the spend it reported>` to the receipt and keep going until you are stopped.
