# C2b -- arm-A pilot on GEX44: ONE send of the C2a job, wait, repatriate, judge, records (draw 1-5)

Mission: the mission id on your rehydration card (write it in the receipt). Goal `cp50-c2`, bound to
C:\Users\User\Apps\recon_work\wt_cp50_c2 only. Authority: Owner "y" 2026-10-10 to arming C2b, which spends RF Phase 7
job 1 of 4 (Phase 7 cap 4 = Owner "y" to CP50 plan D4, 2026-10-09). Exactly ONE `stage.py send`. No retry of a refused
or failed send, no second job, no ssh/scp of your own, no model or paid call by your code, never read G0_HOLDOUT.json,
never arm a mission, never push, never write under decomp_factory or match_accel_factory, never promote().
Envelope (route-C2b.json): when the SESSION BUDGET warn advisory appears, go STRAIGHT to the receipt.
Hard limit 10 tool calls. 0 subagents. NO search tools (Glob/Grep). Read no file except as listed below.

## State you inherit (verified by the coordinator, do not re-verify)
- C2a-fix done (PP `57d82012`): ARM_A_DRILL 8/8, BENCH_DRILL 8/8. Built job dir
  `C:\Users\User\Apps\recon_work\recon_factory\gex44\jobs\candidate-20261010T151142Z` (build tag
  `candidate-20261010T151142Z`, capsule cap1-ba8a3cfe2822, 50 units = 5 functions x arms/presets). Prep file
  `C:\Users\User\Apps\recon_work\recon_factory\cp50\c2a_prep_1_5\arm_a_prep.json`.
- `tools/wros/binary/decomp/gex44/stage.py` line 63 is `RF_CURRENT_PHASE = 3`; `RF_PHASE_JOB_CAPS` has `7: 4`. Phase 3's
  cap is spent, so a send at phase 3 is refused. The phase is read at SEND time (root_phase_cap).
- wt_cp50_c2 cannot commit (its `.ksr_vault` snapshot gate refuses every commit). Never commit there, never `--no-verify`.

## Conventions for every PowerShell call
Never Set-Location. `$env:PYTHONIOENCODING='utf-8'; $env:MATCH_ACCEL_GEX44='C:\Users\User\Apps\recon_work\recon_factory\gex44'`.
python = `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`; scripts by absolute path; D =
`C:\Users\User\Apps\recon_work\wt_cp50_c2\tools\wros\binary\decomp`. Redirect each command's output to a file under
`$env:TEMP\c2b_*.txt` and print it whole (outputs are short); never pipe to Select-Object -First.
A refusal (PINS, NOT_IDLE, cap, STOP, custody, judge, records) is a RESULT: record it verbatim and go to the receipt.

## Call plan (10)
1. Edit `D\gex44\stage.py`: `RF_CURRENT_PHASE = 3` -> `RF_CURRENT_PHASE = 7` (old_string = that exact line). Nothing else.
2. Pre-checks, ONE PowerShell call: `D\gex44\stage.py pins --verify`; `C:\Users\User\Apps\recon_work\wt_cp50_c2\tools\kobishield\slot_ledger.py --status`;
   `D\gex44\stage.py status`. Refuse (no send, go to receipt as PARTIAL) if pins do not verify, or status shows a
   current job or a non-empty queue.
3. Send, ONE PowerShell call: `D\gex44\stage.py send candidate-20261010T151142Z`. Expect `SEND=<result> job=ksrmb-...`.
   Anything but an accepted send: record verbatim, PARTIAL.
4. `D\gex44\stage.py wait <job_id> --max-seconds 540`. 5. Only if STILL_RUNNING: the same wait once more. Still running
   after that = PARTIAL with the job id (the coordinator collects it later); never a third wait.
6. ONE PowerShell call, each step only if the previous one succeeded: `D\gex44\repatriate.py <job_id>` (expect
   `REPATRIATE=OK`); `D\gex44\candidate.py judge <job_id>`; `D\arm_a.py records --draw
   C:\Users\User\Apps\recon_work\wt_keosdtk_home\.planning\workstreams\recon-factory\phases\07-g0-freeze\G0_FREEZE.json
   --first 1 --last 5 --job C:\Users\User\Apps\recon_work\recon_factory\gex44\jobs\candidate-20261010T151142Z
   --prep C:\Users\User\Apps\recon_work\recon_factory\cp50\c2a_prep_1_5\arm_a_prep.json
   --out C:\Users\User\Apps\recon_work\recon_factory\cp50\c2b_records_1_5.jsonl`; then print the records file's line
   count, its sha256 (Get-FileHash) and the file itself.
7. Write the receipt `C:\Users\User\.claude\skills\claude-power-pack\vault\programs\cognitive-economy\gen3\C2b-receipt.md`.
8. ONE PowerShell call (git = `C:\Program Files\Git\cmd\git.exe`, always `git -C <repo>`):
   a. `git -C <wt_cp50_c2> diff --output=C:\Users\User\.claude\skills\claude-power-pack\vault\backlog\2026-10-10_cp50-c2b-phase7.patch -- tools/wros/binary/decomp/gex44/stage.py`
   b. PP commit by pathspec of the receipt + that patch, message from a temp file written with
      `[System.IO.File]::WriteAllText($p, $s, (New-Object System.Text.UTF8Encoding($false)))`;
      `git -C <PP> add -- <2 paths>; git -C <PP> commit -F <msgfile> -- <2 paths>`; print `git -C <PP> log -1 --format='%h %s'`.
9. Spare (one fix of a malformed command of YOUR making only; never a second send). 10. Final message: the HANDOFF line.

## Receipt (<= 20 lines)
Mission id, calls used, pre-check lines verbatim, SEND line, WAIT line(s), REPATRIATE line, judge summary line, records n
+ jsonl sha256, a per-function table (function id | units | best verdict | compiles | wall_s) taken from the records
(unmeasured = absent, never 0), Phase 7 jobs used (1 of 4), PP commit hash, open points. Spend is metered by the control
plane. Ending on a question counts as a failure. End with `HANDOFF NOTE: C2b done -- records <path> sha256 <h>` or
`HANDOFF NOTE: C2b PARTIAL -- <blocker>`.
