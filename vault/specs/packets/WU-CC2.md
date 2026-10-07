done_gate: C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe tools/test_autopsy.py
work_tree: C:\Users\User\Apps\pp-cost-collapse

# WU-CC2 -- mission_spend autopsy + forecast (cost-collapse T2)

Spec (binding): `vault/specs/cost-collapse.md` (program law, row T2). Input: `vault/specs/cost-collapse.RECEIPT-T1.json`.
Fresh worker, no parent transcript. This file is your scope, budget and done-gate.

## 0. Where you work
- The work tree above, branch `cost-collapse/main`. Do NOT create another worktree, do NOT edit
  `C:\Users\User\.claude\skills\claude-power-pack` or `C:\Users\User\Apps\pp-gsdx-pcc`. No GSD commands, no Agents.
  Pathspec commits with a message file; never push.
- Windows: PowerShell tool for git/python; git = `C:\Program Files\Git\cmd\git.exe`; python = the absolute path in
  `done_gate:`; `$env:PYTHONIOENCODING='utf-8'`. Redirect test output to a log; read only `_PASS=` and FAIL lines.
- Grep for functions in `tools/mission_spend.py`; read only the ranges you need. Use sys.executable in fixtures, never python3.

## 1. `mission_spend.py autopsy --mission M`
Per session and per subagent: calls, processed tokens, cache read/write, first/max/mean context, tool mix, stall windows
(gaps between consecutive calls above a threshold), fork exclusion (forked copies are not counted twice). Reuse
`mission_sessions`, `_attributed`, `session_tokens`; do not re-derive attribution.

## 2. `mission_spend.py forecast`
Obligation rows: units x calls x (floor + context image) x (1 + repair). Every row carries its basis and a confidence
label; a missing input is `unmeasured`, never zero (absent is not zero).

## 3. Gates
New `tools/test_autopsy.py` with V-AUTOPSY-* gates, each with both poles on synthetic transcripts (hermetic temp dir),
plus one mutation check per gate family (copy module, revert hunk, import copy, assert red). Reproduce
m-53847a002b65 to +-1% on processed tokens if its transcripts exist on this host; if not, say so in the receipt and
gate the reproduction on a recorded fixture, never skip silently. `tools/test_gsd_mission_envelope.py` stays 55/55,
`tools/test_grammar_default.py` stays green. Commit after each section.

## 4. Chain (last act)
Write `vault/specs/cost-collapse.RECEIPT-T2.json`. If your gate is green, write `vault/specs/packets/WU-CC3.md` for
row T3 of the spec (same header shape), commit, and arm it exactly as spec "PARENTLESS CHAIN" says
(`arm ... --no-launch`, then `envelope --wu-packet ... --token-estimate 15M --model sonnet --autocompact 250k`).
If not green, do NOT arm T3: receipt with the red lines, end.

## Budget
At most 50 model calls; token estimate 5M. End with `HANDOFF NOTE:` and one line.