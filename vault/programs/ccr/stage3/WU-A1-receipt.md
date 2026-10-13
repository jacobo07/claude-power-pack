# A1 receipt
Status: DONE

Plane: Linux plane GEX44, host 2.1.296. Branch mission/ccr-s3. Evidence: vault/programs/ccr/evidence-v4-stage3-A1.md.

## Result
1. **A4 patch applied cleanly** (`git apply`, no hand resolution). Estate gate on the real mod: before FAIL (10x 35,927 > 8,000 bytes), after **PASS** (10x 3,646). After the A1 edits it still passes (policy sha 5a7ddbd6a51c).
2. **`start` receipt** now carries `release` (`$.plugin.root`, the directory this process loaded), `releaseId` (from `<loaded dir>/RELEASE.json`, null on a dev load), `policyGen` (12-hex sha256 of the effective modes + the kernel text read), `effective` {main, subagent, unit, project} and `workClass`. `projectShell` now uses the same `effectiveModes()`, so the receipt and the behaviour cannot diverge. Mod tests 33/33, validate passed.
3. **`tools/ccr_release.py`**: `build` writes RELEASE.json into each release (not hashed, so release ids are unchanged in meaning). `rollback` records the restored release id instead of "rolled-back". New `status --sessions [--listing DIR] [--receipts DIR]...` joins the host's live-session listing `~/.claude/sessions/<pid>.json` (pid alive + Linux procStart reuse guard) with the newest `start` receipt per sid and reports CURRENT / STALE / DEV / UNKNOWN. UNKNOWN covers no receipt, a receipt from before A1, and no active release. Tests 20/20.
4. Probe: one `claude -p --model haiku` session (59fd86cb), whose start receipt is quoted in the evidence.

## Limits / notes
- The Windows `_alive` branch (ctypes) has not been executed. Only Windows path shapes were tested on Linux. The first real run is the LAPTOP_APPLY `status --sessions` below.
- `/usr/local/bin/claude` on GEX44 is 2.1.113. All checks used `~/.local/bin/claude` 2.1.296.
- Sessions already running on the laptop were started by a pre-A1 runtime, so they will show UNKNOWN until they restart. That is by design: a version is never inferred.

## K7
| unit | estimate | actual processed |
|---|---:|---:|
| A1 worker session 9dde3bfe (Opus) | 1,500,000 (packet budget) | 1,318,596 over 29 calls at receipt-writing time, plus this write/commit call and the final verification (about 2 x 50k). Expected final about 1.42M |
| probe 59fd86cb (haiku) | 15,000 | 14,600 |
| **total** | 1,515,000 | ~1.43M (under the 1.5M budget, under the 2.25M breaker) |

## Files
- mods/cpp-cognitive-runtime/hooks/policy.ts, register.ts, policy.test.ts (A4 patch + A1)
- tools/ccr_release.py, tools/test_ccr_release.py
- vault/programs/ccr/evidence-v4-stage3-A1.md, this receipt

## LAPTOP_APPLY
Run in PowerShell from the laptop worktree `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\ccr` (branch ccr/v4) after merging mission/ccr-s3 into it:

    Set-Location C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\ccr
    git merge --no-ff mission/ccr-s3
    claude plugin test mods/cpp-cognitive-runtime        # expect 33 pass, 0 fail
    python tools/test_ccr_release.py                      # expect CCR_PASS=20/20 (first run of the Windows _alive branch)
    python tools/ccr_estate_gate.py --mod mods/cpp-cognitive-runtime   # expect PASS
    # Guarded release: only if no Madzia driver (python.exe with kobiimii in its CommandLine) is running
    $madzia = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*kobiimii*' }
    if ($madzia) { "SKIP release: Madzia driver running, pid(s) $($madzia.ProcessId -join ',')" } else { python tools/ccr_release.py release }
    python tools/ccr_release.py status --sessions

Record the output of both last commands. If the release was skipped, record the skip line and the pids.

## For RESUMPTION_FILE (coordinator)
A1 DONE on GEX44 (2.1.296). The A4 patch is applied and the estate gate passes on the real mod (10x 3,646 / 8,000). The start receipt carries release, releaseId, policyGen, effective and workClass. `ccr_release.py status --sessions` reports CURRENT/STALE/DEV/UNKNOWN. Laptop release + status are pending in LAPTOP_APPLY (guarded on Madzia).
