done_gate: C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe tools/test_route_admission_expected.py
work_tree: C:\Users\User\Apps\pp-cost-collapse

# WU-E1 -- expected-completion estimator + calibration (expected-completion admission E1)

Spec (binding): `vault/specs/expected-completion-admission.md` (APPROVED; read "Four numbers", "Verdicts", "Phase-4
audit" A3/A4 and D3). Inputs: `vault/specs/cost-collapse.RECEIPT-T1.json`, `vault/specs/cost-collapse.RECEIPT-T2.json`.
Fresh worker, no parent transcript. This file is your scope, budget and done-gate.

## 0. Where you work
- The work tree above, branch `cost-collapse/main`. Do NOT create another worktree, do NOT edit
  `C:\Users\User\.claude\skills\claude-power-pack` or `C:\Users\User\Apps\pp-gsdx-pcc`. No GSD commands, no Agents.
  Pathspec commits with a message file; never push.
- Windows: PowerShell tool for git/python; git = `C:\Program Files\Git\cmd\git.exe`; python = the absolute path in
  `done_gate:`; `$env:PYTHONIOENCODING='utf-8'`. Redirect test output to a log; read only `_PASS=` and FAIL lines.
- Grep for functions; read only the ranges you need. `tools/route_admission.py` is 149 lines -- read it whole once.
  Use sys.executable in fixtures, never python3. Do not run mission_spend CLI with `python -I` (RECEIPT-T2 open point).

## 1. Calibration (deterministic, no model judgement)
Using `mission_spend.py autopsy` (reuse it; do not re-derive attribution), compute per top-level session:
calls n, first ctx F, mean ctx, g = 2 x (mean - F) / (n - 1), SEGMENTED where ctx drops > 30% (A3); subagent
transcripts feed their own profile, never `top-level-worker`. Sources, all on this host:
- T1 worker transcript `C:\Users\User\.claude\projects\C--Users-User-Apps-pp-cost-collapse\815cef7f-dd4f-42bd-b7d3-3a72d3a37efd.jsonl`
  (65 calls, 11,135,030 processed, mean 171.3k);
- T2 worker `...\559aeaca-cd01-4f5d-a120-0b5596745695.jsonl` (27 calls, 4,090,547, first 119,788, last 174,754);
- mission m-53847a002b65 (gsdx-pcc; 187.4M per RECEIPT-T2). Also report whether any of its spend is timestamped
  after 2026-10-07T19:30Z (the spec marks the 162.2M -> 187.4M delta UNVERIFIED; settle it with timestamps).
Write the result into `vault/config/route-floors.json` profiles as `growth_per_call` and `calls_err`, each
{value, n, basis, provenance}. A profile with no samples gets NO field (absent is not zero -> ESCALATE).
Record the calibration table in `vault/specs/expected-completion.CALIBRATION.json`.

## 2. Estimator (extend `tools/route_admission.py`; no new module)
Per worker: lower_bound = calls x (F + packet) (no margin, labelled `lower_bound`); expected = calls x (F + packet)
+ g x calls x (calls - 1) / 2; safety = expected at calls x (1 + calls_err). Proof/repair basis
`included_in_calibration` (A4). Verdicts ADMISSIBLE / WATCHED / RECOMPILE / ESCALATE exactly as the spec says, with
confidence = weakest input basis and n; LOW confidence (n < 5) -> SAFETY can only WATCH, never refuse (D3).
Keep the existing result keys (`need`, `need_with_margin`, ...) so `gsd_mission.py admit` and its tests keep working;
add `forecast: {lower_bound, expected, safety, hard, confidence, basis}` and `max_calls_per_process`. The verdict
becomes the challenger's once section 3 is green (D3); the old margin verdict stays in the result as `champion`.

## 3. Gates -- new `tools/test_route_admission_expected.py` (V-ADMIT-EXPECTED-*)
Both poles per gate, hermetic temp dir. Canary 1: T1 replay (48 planned calls) -> champion ADMISSIBLE at 6.45M,
challenger WATCHED, safety within 15% of actual 11,135,030. Canary 2: T2 replay (36 planned) -> challenger expected
reported vs actual 4,090,547 with the error stated. Canary 3: lower_bound present, labelled, and still refuses an
impossible route. Canary 4: two routes, same F, different g -> different expected and verdict. Absent g -> ESCALATE.
Mutation drills (copy module, revert hunk, assert red): growth term removed; unknown g treated as 0; lower_bound
reported as expected; LOW confidence allowed to refuse. Keep green: `tools/test_route_admission.py`,
`tools/test_gsd_mission_admission.py`, `tools/test_gsd_mission_envelope.py` (55/55), `tools/test_grammar_default.py`
(56/56), `tools/test_autopsy.py` (42/42). Commit after each section.

## 4. Chain (last act)
Write `vault/specs/expected-completion.RECEIPT-E1.json` (commits, gate lines, calibration summary; spend is the
meter's, not yours). If green: write `vault/specs/packets/WU-E2.md` (same header shape; scope = spec unit E2 with
audit A2: reuse the guard's warn additionalContext and closeout allowance) and `vault/specs/packets/route-E2.json`
(one top-level-worker, calls from your calibration). Commit. Your own mission is the non-terminal mission whose
`wu_packet` is WU-E1.md (`gsd_mission.py status`). Then, because the live sweep cannot complete a packet mission
yet (audit A1): `arm --cwd <work tree> --command "Execute the work unit in the wu_packet" --workstream cost-collapse
--no-launch --supersedes <your mission> --authority "vault/specs/expected-completion-admission.md APPROVED dae9ff40"`,
then `envelope --mission <new> --wu-packet vault/specs/packets/WU-E2.md --token-estimate 5M --model sonnet
--autocompact 250k`, then `admit --mission <new> --route vault/specs/packets/route-E2.json`. Record the verdict in
the receipt. If not green: do NOT arm E2; receipt with the red lines, end.

## Budget
At most 35 model calls; token estimate 5M. You are WATCHED: if your session guard says warn, write the receipt of
what is done and stop the section you are in. End with `HANDOFF NOTE:` and one line.
