done_gate: C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe tools/test_dependent_admission.py
work_tree: C:\Users\User\Apps\pp-cost-collapse

# WU-E3 -- dependent admission on metered receipts + D3 flip (expected-completion E3)

Spec (binding): `vault/specs/expected-completion-admission.md` (APPROVED; unit E3 as reduced by audit A1).
Inputs: `vault/specs/expected-completion.RECEIPT-E1.json`, `RECEIPT-E2.json`, `expected-completion.CALIBRATION.json`.
Fresh worker, no parent transcript. This file is your scope, budget and done-gate.

## 0. Where you work
- The work tree above, branch `cost-collapse/main`. No other worktree; do NOT edit the LIVE copy
  `C:\Users\User\.claude\skills\claude-power-pack` or `C:\Users\User\Apps\pp-gsdx-pcc`. No GSD commands, no Agents.
  Pathspec commits with a message file; never push.
- Windows: PowerShell tool for git/python; git = `C:\Program Files\Git\cmd\git.exe`; python = the absolute path in
  `done_gate:`; `$env:PYTHONIOENCODING='utf-8'`. Redirect test output to a log; read only `_PASS=` and FAIL lines.
  A suite run exceeds 120 s: run it in the background once and Read the output file when notified.

## 1. Sweep-side dependent admission (audit A1)
A successor mission is admitted against its predecessor's METERED receipt (spent processed tokens from
`mission_spend.processed_tokens`, never the predecessor's estimate). Canary 8: predecessor metered over its
target -> successor ESCALATE. Canary 9: predecessor metered within target -> successor admitted on its own forecast.
Absent receipt -> UNKNOWN, never admitted.

## 2. D3 flip with fixture re-sizing (E1 carry-over)
Set `CHALLENGER_AUTHORITATIVE` True. Re-size the thin fixtures in test_route_admission (8 FAIL) and
test_gsd_mission_admission (7+ FAIL) so they sit above the lower-bound edge, and give slim-t2 / subagent
profiles in `vault/config/route-floors.json` a `calls_err` with provenance (measured, else absent stays UNKNOWN
and its fixtures expect ESCALATE). Keep green: test_route_admission_expected, test_route_admission,
test_gsd_mission_admission, test_gsd_mission_envelope, test_grammar_default, test_autopsy, test_running_control.

## 3. Gate
New `tools/test_dependent_admission.py` (V-DEP-*), both poles per gate, hermetic temp dir, one mutation drill per
canary on a copied module. Commit after each section.

## Budget
At most 32 model calls; token estimate 6M (route-E3.json). When your session guard says checkpoint, write the
receipt `vault/specs/expected-completion.RECEIPT-E3.json` of what is sealed and stop. End with `HANDOFF NOTE:` and one line.