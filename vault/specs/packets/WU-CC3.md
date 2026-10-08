done_gate: C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe tools/test_grammar_compile.py
work_tree: C:\Users\User\Apps\pp-cost-collapse

# WU-CC3 -- G2: compile by default (cost-collapse T3)

Spec (binding): `vault/specs/cost-collapse.md` (program law, row T3). Inputs: `vault/specs/cost-collapse.RECEIPT-T1.json`,
`vault/specs/cost-collapse.RECEIPT-T2.json`. Also read `vault/specs/compiled-grammar-default.md` (owner of laws 1-7) and the
G2 section of `vault/specs/mission-envelope-and-compiled-wu.md`. Fresh worker, no parent transcript. This file is your scope,
budget and done-gate.

## 0. Where you work
- The work tree above, branch `cost-collapse/main`. Do NOT create another worktree, do NOT edit
  `C:\Users\User\.claude\skills\claude-power-pack` or `C:\Users\User\Apps\pp-gsdx-pcc`. No GSD commands, no Agents.
  Pathspec commits with a message file; never push.
- Windows: PowerShell tool for git/python; git = `C:\Program Files\Git\cmd\git.exe`; python = the absolute path in
  `done_gate:`; `$env:PYTHONIOENCODING='utf-8'`. Redirect test output to a log; read only `_PASS=` and FAIL lines.
- Grep for functions before reading; read only the ranges you need. Use sys.executable in fixtures, never python3.
  Note: `python -I` drops the script directory from sys.path, so tools that import siblings must not be run with `-I`.
- `origin/grammar/g2-partial` is already merged on this branch: read what exists (`tools/gsd_dossier.py`,
  `tools/edd_canary_gate.py`, `tools/gsd_mission.py` packet gate) before writing anything; extend, do not re-derive.

## 1. `tools/gsd_compile.py`
Per roadmap phase: a dossier + a packet (header shape of `vault/specs/packets/WU-CC2.md`: `done_gate:`, `work_tree:`,
scope, budget) and an envelope derived from route floors, not from a guess. Use `mission_spend.autopsy` / `forecast`
(T2) for floor and context-image inputs; a missing input is `unmeasured`, never zero.

## 2. `tools/mission_wait.py`
Waiting holds zero hot cognition: a wait that polls with a model call is a failure. Deterministic wait on a file/process
condition with a hard wall-clock timeout and a graceful did-not-complete exit.

## 3. `/cpp-gsd-long` compiles by default
Legacy grammar only under `CPP_MISSION_GRAMMAR=legacy`, and that choice is ledgered. Rule: never wake a context above
its window -- a resume compiles a fresh packet instead of resuming the stale context.

## 4. Gates
New `tools/test_grammar_compile.py` with V-GRAMMAR-COMPILE-* and V-WAIT-* gates, each with both poles, plus one mutation
check per gate family (copy module, revert hunk, import copy, assert red). Stay green: `tools/test_autopsy.py` 42/42,
`tools/test_grammar_default.py` 56/56, `tools/test_gsd_mission_envelope.py` 55/55, `tools/test_gsd_mission.py` 225/225.
Commit after each section.

## 5. Chain (last act)
Write `vault/specs/cost-collapse.RECEIPT-T3.json`. If your gate is green, write `vault/specs/packets/WU-CC4.md` for row T4
of the spec (same header shape), commit, and arm it exactly as spec "PARENTLESS CHAIN" says (`arm ... --no-launch`, then
`envelope --wu-packet ... --token-estimate 6M --model sonnet --autocompact 250k`). If not green, do NOT arm T4: receipt
with the red lines, end. If `arm` refuses (singleflight against your own live mission), record the exact commands in the
receipt `open_points` as T1 and T2 did.

## Budget
At most 70 model calls; token estimate 15M. End with `HANDOFF NOTE:` and one line.
