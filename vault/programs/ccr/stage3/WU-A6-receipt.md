# A6 receipt
Status: DONE

Unit: WU-A6, real admission intervention (goal ccr). Linux plane GEX44, host 2.1.296, branch mission/ccr-s3. This is attempt 3, which resumed the uncommitted work of attempts 1 (eeddc9ec) and 2 (8f18a9e7).

## Done-check
`vault/programs/ccr/evidence-v4-stage3-A6.md` contains:
- the confidence map (section 1);
- the two-pole tests, the mutation drill and the regression run (section 2);
- the DEFLATE intervention with before/after (section 3);
- the real DETERMINISTIC_PATH run with correctness (section 4).

## Results
1. **Confidence gate.** Enforcement and DEFLATE act only at MEDIUM or HIGH; LOW observes.
   - The packet expected observe everywhere. In fact one class acts: **bounded-code is MEDIUM in A3** (n held-out 24, P80 coverage 70.8 %). It fails the gate on P50 APE 46.4 % only.
   - long-textual (n 7), lookup, generic and multimodal are LOW, so they observe.
   - W1 contract enforcement stays opt-in (`CPP_CCR_ADMISSION=enforce`).
   - DEFLATE is on by default for MEDIUM slim launches. Its off switch is `CPP_CCR_DEFLATE=off`. A `--bg` launch records `delivered: false`.
2. **Tests.** `python3 tools/test_gsd_mission_ccr_a6.py`: **13 passed, 0 failed**. Both poles are covered for each action.
   - Mutation drill: 6 of 6 mutations killed, each by its own gate; the control is 13/13.
   - The existing suites are green (test_gsd_mission.py MC_PASS=230/230, plus 13 others).
   - 3 suites are red **identically at HEAD 3665d157**, before A6: cwd_align 15/16, legacy_characterization 24/33, sleep 5/6.
3. **DEFLATE** (laptop projections). The real undeclared launch 9cdf4fbb (Madzia, 13 calls) has a first-call context of 75,550. The declared floor on its own project's unit workers is 18,137 (median), so D = 57,413 per call.
   - Processed: 1,233,784 -> 487,415 (**-746,369, 60.5 %**).
   - Weighted: 255,548.2 -> 128,893.1 (**-49.6 %**).
   - This is a counterfactual, not a re-run. It assumes 9cdf4fbb would be classified bounded-code; it is not in the A3 corpus.
4. **DETERMINISTIC_PATH** (Linux plane GEX44, host 2.1.296). The re-measure of A2-A5 ran through `gsd_mission.launch_worker` with **0 model calls** and output `{"A2": 4302121, "A3": 1678774, "A4": 6352270, "A5": 2012075}` (sha256 f6c3f228...).
   - Correctness: **4/4 values equal** the earlier measured numbers.

## Files
- `tools/gsd_mission.py`: the A6 wiring.
  - `_ccr_enforceable`, `UNIT_FOR_CLASS`, `deflate_unit`, `deterministic_script` and `_run_deterministic`.
  - The `_ccr_contract` A3 `pgo-classes.json` path.
  - The DEFLATE hook in `_launch_slim` and the `--bg` launch.
  - The `env` parameter of `_spawn_detached`.
  - The DETERMINISTIC_PATH branch in `launch_worker` before the epoch claim.
- `tools/test_gsd_mission_ccr_a6.py`: the 13 gates.
- `vault/programs/ccr/stage3/a6/`:
  - `survey.py`, `sessions.json`
  - `madzia_history.py`, `madzia_history.json`
  - `deflate_counterfactual.py`, `deflate_counterfactual.json`
  - `remeasure.py`
  - `det_route.py`, `det_route.out.json` (attempt 2), `det_route.r3.out.json` (this attempt)
  - `mutation_drill.py`, `mutation_drill.out.json`
- `vault/programs/ccr/evidence-v4-stage3-A6.md`

Scratch outside the repo:
- `ccr-s3-data/a6-det-state` and `ccr-s3-data/a6-det-state-r3` (isolated mission stores)
- `ccr-s3-data/a6-mutation/`

No `rm -r` was used. The mutation copies were deleted with `shutil.rmtree` on paths just created. The one HEAD worktree was removed with `git worktree remove`, without `--force`, after it was checked clean.

Not committed, and not this unit's: `.pp-capabilities` and `docs/*/tools__ccr_release.py.md` / `tools__test_ccr_release.py.md`. They were untracked at the start of the session.

## K7: estimate vs actual processed tokens, every session of this unit
| session | processed |
|---|---:|
| attempt 1 eeddc9ec (killed by the 2,250,000 breaker, 39 calls) | 2,367,697 |
| attempt 2 8f18a9e7 (hook_stopped on `rm -rf`, 37 calls) | 1,966,777 |
| attempt 3 d084c077 (this session; measured at 31 calls, just before this receipt) | 1,471,863 |
| **actual total (at receipt write)** | **5,806,337** |
| estimate: packet budget | 3,000,000 |
| estimate: plan row A6 | 1,200,000 |

- The actual total is **1.94 times the packet budget** and **4.8 times the plan estimate**. The two interrupted attempts account for 4,334,474 of it.
- This session alone is under its 3,000,000 budget.
- The DETERMINISTIC_PATH run made no model calls, so it adds nothing. The few closing calls that commit this receipt are not included.

## LAPTOP_APPLY
Prerequisite: the A6 commit on GEX44 `mission/ccr-s3` must be on laptop `ccr/v4` (worktree `.claude\worktrees\ccr`) the same way A2-A5 were brought over. Then, from the laptop main tree (PowerShell; bare `git` is not on the non-interactive PATH):

    Set-Location C:\Users\User\.claude\skills\claude-power-pack
    $git = 'C:\Program Files\Git\cmd\git.exe'
    $merged = & $git diff --name-only HEAD...ccr/v4
    $dirty  = & $git status --porcelain | ForEach-Object { $_.Substring(3) }
    $hit = $dirty | Where-Object { $merged -contains $_ }
    if ($hit) { Write-Output "ABORT: dirty merged paths: $hit"; exit 1 }
    & $git merge --no-ff --no-edit ccr/v4
    if ($LASTEXITCODE -ne 0) { & $git merge --abort; Write-Output "ABORT: merge conflict"; exit 1 }
    python tools/test_gsd_mission.py
    if ($LASTEXITCODE -ne 0) { & $git revert -m 1 --no-edit HEAD; Write-Output "REVERTED: test_gsd_mission failed"; exit 1 }
    python tools/test_gsd_mission_ccr_a6.py

Expected results:
- `MC_PASS=230/230`
- then `13 passed, 0 failed`

After the merge, DEFLATE is live by default for bounded-code slim launches on the laptop, but only once a `pgo-classes.json` sits in the CCR PGO dir. Set `CPP_CCR_DEFLATE=off` to hold it.

## Text for RESUMPTION_FILE (coordinator)
A6 DONE (attempt 3, d084c077), committed on mission/ccr-s3.
- DETERMINISTIC_PATH re-measured A2-A5 with 0 model calls, 4/4 values exact.
- DEFLATE acts only on bounded-code (A3 MEDIUM). Counterfactual on 9cdf4fbb: -746,369 processed (60.5 %), -49.6 % weighted.
- A6 suite 13/13; mutation drill 6/6 killed.
- Pre-existing red at 3665d157: cwd_align, legacy_characterization, sleep.
- K7 5,806,337 across 3 sessions vs a 3,000,000 budget.
- Next: the LAPTOP_APPLY merge of ccr/v4, then A7.
