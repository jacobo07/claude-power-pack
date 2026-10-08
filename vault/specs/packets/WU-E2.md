done_gate: C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe tools/test_running_control.py
work_tree: C:\Users\User\Apps\pp-cost-collapse

# WU-E2 -- running control: warn is a checkpoint, EAC reforecast, CONTINUE/CHECKPOINT (expected-completion E2)

Spec (binding): `vault/specs/expected-completion-admission.md` (APPROVED; read "Running control", audit A2).
Inputs: `vault/specs/expected-completion.RECEIPT-E1.json`, `vault/specs/expected-completion.CALIBRATION.json`.
Fresh worker, no parent transcript. This file is your scope, budget and done-gate.

## 0. Where you work
- The work tree above, branch `cost-collapse/main`. Do NOT create another worktree, do NOT edit
  `C:\Users\User\.claude\skills\claude-power-pack` (the LIVE copy) or `C:\Users\User\Apps\pp-gsdx-pcc`. No GSD
  commands, no Agents. Pathspec commits with a message file; never push.
- Windows: PowerShell tool for git/python; git = `C:\Program Files\Git\cmd\git.exe`; python = the absolute path in
  `done_gate:`; `$env:PYTHONIOENCODING='utf-8'`. Redirect test output to a log; read only `_PASS=` and FAIL lines.
- Grep for functions; read only the ranges you need. Do not run mission_spend CLI with `python -I`.
- OUT OF SCOPE (carried to E3, do not touch): the D3 flip (`CHALLENGER_AUTHORITATIVE`), fixture re-sizing in
  test_route_admission / test_gsd_mission_admission, calls_err for slim-t2 / subagent profiles.

## 1. EAC reforecast (extend `tools/mission_spend.py`; no new module)
Add a pure function beside `judge`: EAC = spent + r x (ctx_now + g x r / 2), r = remaining calls = max(0,
planned_calls x (1 + calls_err) - calls_done). g and calls_err come from the profile in
`vault/config/route-floors.json` (E1 wrote them with provenance). Absent g -> verdict UNKNOWN (never 0).
`judge` gains a `forecast` field {eac, r, g, basis} and a decision: CONTINUE when EAC <= target x (1 + tolerance)
AND the progress fingerprint moved since the last mark; CHECKPOINT otherwise. The existing stall trip and the
2 x target hard trip are UNCHANGED and still win. Tolerance: a named constant, default 0.25, documented as chosen.

## 2. Warn becomes the checkpoint instruction (audit A2 -- REUSE, do not add a mechanism)
`hooks/session_budget_guard.js` already injects additionalContext past warn (~L130) and grants a closeout allowance
after a deny (~L150-163). Edit ONLY the worktree copy: the warn text becomes one imperative instruction -- write a
progress receipt (what is sealed, what remains, calls used) and stop the current section. The closeout allowance is
the checkpoint reserve (no new reserve). Sweep side: in `tools/gsd_mission.py` where the cost breaker reads `judge`,
CHECKPOINT = the existing owner hold with reason `checkpoint: EAC <eac> > target` (reuse the hold path).

## 3. Context-rent trigger (decision only; rotation belongs to ce-lifecycle)
In the same forecast: rotate_recommended = (ctx_now - F) x r > F + rehydration (rehydration = a named constant from
the profile floor, documented). Emit it as a field. Do NOT implement rotation; do not call kclear/kresume.

## 4. Gates -- new `tools/test_running_control.py` (V-RUNCTL-*), both poles per gate, hermetic temp dir
Canary 5: E1 replay (target 5M, warn hit at 6.3M) -> CHECKPOINT at warn. Canary 6: T2 replay (4.09M, 27 calls)
-> CONTINUE throughout. Canary 7: absent g -> UNKNOWN, never CONTINUE. Canary 10: fingerprint frozen while EAC is
under target -> CHECKPOINT (progress required). Canary 11: rotate_recommended true at T1-like ctx 206k/r=17, false
at T2-like ctx 150k/r=3. Mutation drills (copy module, revert hunk, assert red): growth term dropped from EAC;
absent g treated as 0; fingerprint check removed; hard trip overridden by CONTINUE. Keep green:
test_route_admission_expected 23/23, test_route_admission 21/21, test_gsd_mission_admission 43/43,
test_gsd_mission_envelope 55/55, test_grammar_default 56/56, test_autopsy 42/42. Commit after each section.

## 5. Chain (last act)
Write `vault/specs/expected-completion.RECEIPT-E2.json` (commits, gate lines; spend is the meter's, not yours).
If green: write `vault/specs/packets/WU-E3.md` (same header shape; scope = spec unit E3 reduced by audit A1 to
sweep-side dependent admission with metered predecessor receipts, canaries 8, 9, PLUS the E1 carry-over: the D3
flip with fixture re-sizing and calls_err for the profiles RECEIPT-E1 lists) and `vault/specs/packets/route-E3.json`
(one top-level-worker; size it with the expected-completion estimator, not the margin). Commit. Your own mission is
the non-terminal mission whose `wu_packet` is WU-E2.md (`gsd_mission.py status`). Then: `arm --cwd <work tree>
--command "Execute the work unit in the wu_packet" --workstream cost-collapse --no-launch --supersedes <your
mission> --authority "vault/specs/expected-completion-admission.md APPROVED dae9ff40"`, then `envelope --mission
<new> --wu-packet vault/specs/packets/WU-E3.md --token-estimate <route target> --model sonnet --autocompact 250k`,
then `admit --mission <new> --route vault/specs/packets/route-E3.json`. Record the verdict in the receipt.
If not green: do NOT arm E3; receipt with the red lines, end.

## Budget
At most 28 model calls; token estimate 5M. Forecast (E1 calibration, g=2310, F~112k): EXPECTED ~4.0M at 28 calls,
SAFETY ~5.9M at 38 -> WATCHED. E1 ran to warn on a comparable scope: when your session guard says warn, write
the receipt of what is sealed and stop. Section 5 is mandatory before section 4's mutation drills if you are past
22 calls. End with `HANDOFF NOTE:` and one line.
