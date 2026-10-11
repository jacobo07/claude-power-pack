# C2c-fix -- candidate mode returns a TRIMMED diff.json (OUT stays under 20 MB), one gate, ONE local re-prepare (NO send)

Mission: the mission id on your rehydration card (write it in the receipt). Goal `cp50-c2`, bound to
C:\Users\User\Apps\recon_work\wt_cp50_c2 only. Authority: Owner "y" 2026-10-11 to the coordinator's C2c-fix proposal,
after C2b-retry came back PARTIAL (gen3/C2b-retry-receipt.md). Supersedes m-eab0a70eb117. NOTHING is sent to the VPS or
GEX44 (no `stage.py send`, no ssh, no scp), never read G0_HOLDOUT.json, never arm a mission, never push, never touch
stage.py, arm_a.py or capsule_build.py.
Envelope (route-C2c-fix.json): when the SESSION BUDGET warn advisory appears, go STRAIGHT to the receipt.
Hard limit 7 tool calls. 0 subagents. NO search tools (Glob/Grep). Read only what the plan names.
**Pass `timeout: 600000` on every PowerShell call; never run_in_background, never Start-Sleep, never re-read an output
file to check progress.** (The C2b-fix worker spent 8 extra calls polling a backgrounded run.)

## State you inherit (verified by the coordinator, do not re-verify)
- Job ksrmb-20261011-094630 (Phase 7 job 2 of 4): the types prelude worked (20 m2cvs units compiled and were diffed), but
  the runner ended `VERDICT=FAIL reason=TOOL_FAILURE`: "OUT would exceed 20971520 bytes without runner.log". Each unit's
  `diff.json` was ~7 MB (objdiff's report lists every symbol of the target object), 83 MB in all, so no receipt.json and
  no MANIFEST.json were written and repatriate said INVALID_CUSTODY.
- Cause: `tools/wros/binary/decomp/gex44/runner_lib.py` lines 1471-1472, candidate mode:
  ```
                  if (pct is None or float(pct) != 100.0) and os.path.isfile(os.path.join(udir, "fn.diff.json")):
                      shutil.copyfile(os.path.join(udir, "fn.diff.json"), os.path.join(out_units, uid + ".diff.json"))
  ```
  The other mode (lines 1311-1313) already calls `trim_objdiff_report(src, dst, unit["symbol"])` (runner_lib.py:971; it
  keeps only `symbol`'s entries, writes `{"schema": TRIM_SCHEMA, "symbol", "full_sha256", "full_bytes", ...}`, and
  parse_objdiff_percent reads the same percent from the trimmed file). That fix (2026-10-09, job ksrmb-20261009-075610)
  never reached the candidate path.
- `runner_lib.py` is copied into every job by stage.build (stage.py:47 STAGED_FILES), so a fresh build picks up the fix.

## The fix (two edits, nothing else)
A. runner_lib.py line 1472: replace the `shutil.copyfile(...)` with
   `trim_objdiff_report(os.path.join(udir, "fn.diff.json"), os.path.join(out_units, uid + ".diff.json"), unit["symbol"])`
   (same indentation; the `if` on 1471 stays).
B. test_candidate.py: right after the `V-CAND-TRACER` gate (ends at line 185), add
   `V-CAND-DIFF-TRIMMED`: `json.loads((out / "units" / "u-b.diff.json").read_bytes())` has
   `schema == runner_lib.TRIM_SCHEMA` and an int `full_bytes` (import runner_lib / json locally if the file does not).
   V-CAND-TRACER already pins that the judge still reads 75.0 from the returned diff, so it proves the trimmed file is
   readable.

## Call plan (7)
1. Read runner_lib.py offset 1470 limit 3. 2. Edit A.
3. Read test_candidate.py offset 180 limit 8. 4. Edit B (insert after the line ending
   `len(host.compiles())))` that closes V-CAND-TRACER).
5. ONE PowerShell call, never Set-Location, `$env:PYTHONIOENCODING='utf-8'`,
   `$env:MATCH_ACCEL_GEX44='C:\Users\User\Apps\recon_work\recon_factory\gex44'`, python
   `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`, absolute paths, D =
   `C:\Users\User\Apps\recon_work\wt_cp50_c2\tools\wros\binary\decomp`, all output to `$env:TEMP\c2cfix_run.txt`, then
   print only lines matching `_PASS=|_DRILL=|^FAIL|ARM_A_PREPARED|REFUSED|Refused|Error|Traceback|CURRENT_|TRIM_CALLS`:
   a. `D\gex44\test_candidate.py` (all PASS, including V-CAND-DIFF-TRIMMED), b. `D\gex44\test_batch_local.py` (all PASS),
   c. `D\test_arm_a.py` (10/10), d. ONLY if a-c pass: `D\arm_a.py prepare --draw
   C:\Users\User\Apps\recon_work\wt_keosdtk_home\.planning\workstreams\recon-factory\phases\07-g0-freeze\G0_FREEZE.json
   --first 1 --last 5 --out C:\Users\User\Apps\recon_work\recon_factory\cp50\c2c_prep_1_5`, e. python -c printing
   `CURRENT_OK capsule=<id>` if `recon_factory\gex44\CURRENT_CAPSULE.json` names the prep's capsule_id with its
   manifest_sha256 (else `CURRENT_BAD <why>`), and `TRIM_CALLS=<n>` = occurrences of `trim_objdiff_report(` in the NEW
   job dir's staged `runner_lib.py` (expect 3: the def and two calls). A refusal is a RESULT: record it verbatim.
6. ONE PowerShell call: write the receipt
   `C:\Users\User\.claude\skills\claude-power-pack\vault\programs\cognitive-economy\gen3\C2c-fix-receipt.md` with
   `[System.IO.File]::WriteAllText($p,$s,(New-Object System.Text.UTF8Encoding($false)))`; then
   `git -C <wt_cp50_c2> add -- tools/wros/binary/decomp/gex44/runner_lib.py tools/wros/binary/decomp/gex44/test_candidate.py`;
   `git -C <wt_cp50_c2> diff --cached --binary --output=C:\Users\User\.claude\skills\claude-power-pack\vault\backlog\2026-10-11_cp50-c2c-fix.patch`;
   commit receipt + patch in PP by pathspec (`git -C <PP> add -- <2 paths>; git -C <PP> commit -F <msgfile> -- <2 paths>`,
   message file written the same way); print `git -C <PP> log -1 --format='%h %s'`. git =
   `C:\Program Files\Git\cmd\git.exe`. **Never commit in wt_cp50_c2**, never `--no-verify`.
7. Final message: the receipt's HANDOFF line only.

## Receipt (<= 15 lines)
Mission id, calls used, drill/pass lines verbatim, ARM_A_PREPARED line (or the refusal verbatim), job dir, CURRENT line,
TRIM_CALLS line, PP commit hash, open points. Ending on a question counts as a failure. End with
`HANDOFF NOTE: C2c-fix done -- C2b-retry2 may send <job dir>` or `HANDOFF NOTE: C2c-fix PARTIAL -- <blocker>`.
