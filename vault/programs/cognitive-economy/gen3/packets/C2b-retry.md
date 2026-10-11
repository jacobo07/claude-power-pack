# C2b-retry -- arm-A pilot on GEX44: ONE send of the C2b-fix job, wait, repatriate, judge, records (draw 1-5)

Mission: the mission id on your rehydration card (write it in the receipt). Goal `cp50-c2`, bound to
C:\Users\User\Apps\recon_work\wt_cp50_c2 only. Authority: Owner "go ahead" 2026-10-11 to arming C2b-retry, which spends
RF Phase 7 job 2 of 4 (Phase 7 cap 4 = Owner "y" to CP50 plan D4, 2026-10-09). Exactly ONE `stage.py send`. No retry of a
refused or failed send, no second job, no ssh/scp of your own, no model or paid call by your code, never read
G0_HOLDOUT.json, never arm a mission, never push, never edit any file in wt_cp50_c2, never promote().
Envelope (route-C2b-retry.json): when the SESSION BUDGET warn advisory appears, go STRAIGHT to the receipt.
Hard limit 7 tool calls. 0 subagents. NO search tools (Glob/Grep). Read no file.

## State you inherit (verified by the coordinator, do not re-verify)
- C2b (job 1, ksrmb-20261010-203003) failed to compile every unit (no base types) and was judged STALE_INPUT (no
  CURRENT_CAPSULE.json). C2b-fix (PP `16774243`) fixed both: every unit now starts with the s8..f64 typedefs
  (UNITS_TYPED 50/50) and `recon_factory\gex44\CURRENT_CAPSULE.json` names cap1-ba8a3cfe2822 with manifest sha256
  feaee0636c04794f63593a27bd5e14c58e53b850a1019e45edb932e5e3629aba.
- Job to send: build tag `candidate-20261011T071346Z`, dir
  `C:\Users\User\Apps\recon_work\recon_factory\gex44\jobs\candidate-20261011T071346Z`. Prep
  `C:\Users\User\Apps\recon_work\recon_factory\cp50\c2bfix_prep_1_5\arm_a_prep.json`.
- stage.py already has `RF_CURRENT_PHASE = 7` (uncommitted, do not touch). wt_cp50_c2 cannot commit.
- Plain-arm (`-m2c-`) units may still fail to compile on m2c's unresolved `?` types. That is a MEASURED result.

## Conventions for every PowerShell call (the C2b worker lost 3 calls breaking these)
- **Pass `timeout: 600000` on EVERY PowerShell call.** A send takes ~3 minutes; with the default 120 s the harness moves
  it to the background and you end up polling. Never use `run_in_background`, never Start-Sleep, never re-read an output
  file to "check progress": each command runs in the FOREGROUND and you read its output once when the call returns.
- Never Set-Location. `$env:PYTHONIOENCODING='utf-8'; $env:MATCH_ACCEL_GEX44='C:\Users\User\Apps\recon_work\recon_factory\gex44'`.
  python = `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`; D =
  `C:\Users\User\Apps\recon_work\wt_cp50_c2\tools\wros\binary\decomp`. Redirect each command to `$env:TEMP\c2br_*.txt`
  and print the file in the SAME call.
- A refusal (PINS, NOT_IDLE, cap, STOP, custody, judge, records) is a RESULT: record it verbatim and go to the receipt.

## Call plan (7)
1. Pre-checks + send, ONE PowerShell call: `D\gex44\stage.py pins --verify`;
   `C:\Users\User\Apps\recon_work\wt_cp50_c2\tools\kobishield\slot_ledger.py --status`; `D\gex44\stage.py status`; then,
   ONLY if pins verify AND status shows no current job and queue_depth 0: `D\gex44\stage.py send candidate-20261011T071346Z`.
   Print everything. If the SEND line names a job id (`SEND=ACCEPTED` or `SEND=QUEUED_NOT_RUNNING job=ksrmb-...`), that
   job is real: continue with it, never resend. No job id = PARTIAL.
2. `D\gex44\stage.py wait <job_id> --max-seconds 540`. 3. Only if STILL_RUNNING: the same wait once more; still running
   after that = PARTIAL with the job id (the coordinator collects it later).
4. ONE PowerShell call, each step only if the previous one succeeded: `D\gex44\repatriate.py <job_id>` (expect
   `REPATRIATE=OK`); `D\gex44\candidate.py judge <job_id>`; `D\arm_a.py records --draw
   C:\Users\User\Apps\recon_work\wt_keosdtk_home\.planning\workstreams\recon-factory\phases\07-g0-freeze\G0_FREEZE.json
   --first 1 --last 5 --job C:\Users\User\Apps\recon_work\recon_factory\gex44\jobs\candidate-20261011T071346Z
   --prep C:\Users\User\Apps\recon_work\recon_factory\cp50\c2bfix_prep_1_5\arm_a_prep.json
   --out C:\Users\User\Apps\recon_work\recon_factory\cp50\c2b_records_1_5.jsonl`; then print the records file's line
   count, its sha256 (Get-FileHash) and the file itself. If the judge is not all-STALE, ALSO print, per unit, unit_id +
   runner_status + verdict from `recon_factory\gex44\candidate_ledger.jsonl` rows of this job (python -c, one line each).
5. ONE PowerShell call: write the receipt
   `C:\Users\User\.claude\skills\claude-power-pack\vault\programs\cognitive-economy\gen3\C2b-retry-receipt.md`
   with `[System.IO.File]::WriteAllText($p,$s,(New-Object System.Text.UTF8Encoding($false)))`, then commit it in PP by
   pathspec (git = `C:\Program Files\Git\cmd\git.exe`, `git -C C:\Users\User\.claude\skills\claude-power-pack add -- <path>;
   ... commit -F <msgfile> -- <path>`, message file written the same way) and print `git -C <PP> log -1 --format='%h %s'`.
6. Spare: one fix of a malformed command of YOUR making only; never a second send. 7. Final message: the HANDOFF line.

## Receipt (<= 20 lines)
Mission id, calls used, pre-check lines verbatim, SEND line, WAIT line(s), REPATRIATE line, judge summary line, records n
+ jsonl sha256, a per-function table (function id | units | best verdict | compiles k/n | wall_s) from the records and
ledger (unmeasured = absent, never 0), compile failures by arm (m2c vs m2cvs), Phase 7 jobs used (2 of 4), PP commit
hash, open points. Ending on a question counts as a failure. End with
`HANDOFF NOTE: C2b-retry done -- records <path> sha256 <h>` or `HANDOFF NOTE: C2b-retry PARTIAL -- <blocker>`.
