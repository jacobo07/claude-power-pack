# X2 receipt
Status: DONE

Unit WU-X2: recertify and record knowledge (goal ccr). Linux plane GEX44, host 2.1.296, branch mission/ccr-s3, base a364877b. Inputs: the A0-A7 receipts, evidence-v4-stage3-A0..A7.md, CERTIFICATE-v4.md, and the plan's "Effectiveness ladder" section. drive.log and the run streams were used only for K7 and settle values, measured with `tools/ccr_spend_census.py measure`, which makes 0 model calls.

## Certificate level: EFFECTIVENESS_PARTIAL (unchanged)
- PARTIAL: MET (Stage 2 B1+B2+B5+B6, unchanged).
- BOUNDARY_COST: NOT MET, 1 of 4.
  - MET: real_admission_intervention_with_correctness (A6 DETERMINISTIC_PATH, 4/4 exact, 0 model calls; isolated GEX44 store).
  - ABSTAIN:second_class_measured_saving:+7.95 % (+1.53 % with rehydration; bar 15 %).
  - ABSTAIN:class_forecast_heldout_p50_ape_lt_25pct:46.4 % (bounded-code n 24; long-textual 21.7 % on n 7 < 8).
  - ABSTAIN:ledgers_reconciled:UNKNOWN (booking not run; 12,968,143 post-census processed unbooked).
- LONG_HORIZON: NOT MET, 1 of 3.
  - MET: estate_elasticity_low_slope (10x -> 3,646 / 8,000 bytes).
  - ABSTAIN:a5_real_canary_positive_at_parity:n=1 of 3 per arm.
  - ABSTAIN:history_elasticity_low_slope_live:0.525 (replay only).
- Terminal: not claimed.
- Stage 3 negative knowledge is recorded in the certificate:
  - overruns: A2 4,359,814 vs 1.5M; A4 6,431,753 vs 3.0M; A6 6,070,930 vs 3.0M; A7 3,613,494 vs 3.0M; A0 1,781,551 vs 1.5M;
  - drive.log figures A2 4.30M / A4 6.35M;
  - the GEX44 breaker failed open: A4 `processed=` was empty after a string `message` line, the breaker never fired, and A4 ran 6.43M against a 2.25M stop.

## Delivered
- `vault/programs/ccr/CERTIFICATE-v4.md`: Stage 3 ladder plus the re-read Stage 2 ABSTAINs. Newly MET: forecast_vs_actual_on_ccr_run, on n 2 at LOW confidence, flagged as superseded by the held-out gate. New ABSTAINs: hard_floor_isolated, cws_tool_schema_saving, main_lean_canary. Never rounded up.
- `vault/programs/ccr/NEGATIVE_KNOWLEDGE.md`: 16 Stage 3 CBR lines, one per ABSTAIN, plus the overrun and breaker lines.
- `vault/knowledge_base/ukdl-universal.md`: 6 new ids, measured lessons only. Each id was grepped first and had 0 prior hits:
  - T-CCR-BREAKER-EMPTY-MEASUREMENT-FAILS-OPEN-001
  - T-CCR-STREAMJSON-OUTPUT-IS-PRESTREAM-001
  - PR-CCR-PER-CALL-FLOOR-IS-TOOL-SCHEMAS-001
  - PR-CCR-PRICE-REHYDRATION-NOT-ONLY-CAPSULE-001 (cross-refs the existing ccp-s16 rollover entry)
  - PR-CCR-FORECAST-BY-WORK-CLASS-001
  - PR-CCR-MAIN-LISTINGS-NAME-ONLY-001

  The A2 continuation overrun is recorded as evidence under the existing continuation-cost entry, not as a new id.
- No code and no mods/ edits in this unit. `vault/programs/ccr/RESUMPTION_FILE.md` was not touched.

## K7: estimate vs actual processed tokens, every session of this unit
| session | estimate | actual processed |
|---|---:|---:|
| X2 worker bf1bb90a-3941-4a94-9893-0c85558b7765 (Opus, GEX44) | 3,000,000 (packet budget) | 1,415,074 over 25 calls, measured just before this receipt. The receipt and commit calls add about 4 x 60k, so the final is about 1.65M |
| canary / probe sessions | 0 | 0 (no model calls) |
| **total** | 3,000,000 | ~1.65M (under budget, under the 4,500,000 breaker). Final: `python3 tools/ccr_spend_census.py measure /home/kobii/missions/ccr-s3-data/run-X2.jsonl` |

## LAPTOP_APPLY
PowerShell on the laptop. Bare `git` is not on the non-interactive PATH. Repo root `C:\Users\User\.claude\skills\claude-power-pack`, worktree `.claude\worktrees\ccr` (branch ccr/v4).

**Step 0. Bring the GEX44 branch over.** Use the same transport that brought A2-A5 over. Set `$gex` to that remote name or URL before running.

    $git = 'C:\Program Files\Git\cmd\git.exe'
    Set-Location C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\ccr
    & $git fetch $gex mission/ccr-s3:refs/remotes/gex44/mission-ccr-s3
    & $git log --oneline -1 refs/remotes/gex44/mission-ccr-s3     # expect the X2 commit (subject starts "docs(ccr-x2)")

**Step 1. Merge mission/ccr-s3 into ccr/v4** (worktree).

    if (& $git status --porcelain) { Write-Output "ABORT: worktree dirty"; exit 1 }
    & $git merge --no-ff --no-edit refs/remotes/gex44/mission-ccr-s3
    if ($LASTEXITCODE -ne 0) { & $git merge --abort; Write-Output "ABORT: merge conflict in worktree"; exit 1 }
    claude plugin test mods/cpp-cognitive-runtime                       # expect 38 pass, 0 fail (A7)
    claude plugin validate mods/cpp-cognitive-runtime                   # expect "Validation passed"
    python tools/test_ccr_release.py                                    # expect CCR_PASS=20/20 (first run of the Windows _alive branch)
    python tools/test_ccr_main_shadow.py                                # expect CCR_PASS=11/11
    python tools/ccr_estate_gate.py --mod mods/cpp-cognitive-runtime    # expect PASS

Do NOT run A4's `git apply vault/programs/ccr/stage3/a4/ccr-mod-a4.patch`. A1 already applied it (3665d157), so a second apply fails.

**Step 2. Merge ccr/v4 into the main tree.** Abort on dirty merged paths, never stash or reset, and revert on test failure.

    Set-Location C:\Users\User\.claude\skills\claude-power-pack
    $merged = & $git diff --name-only HEAD...ccr/v4
    $dirty  = & $git status --porcelain | ForEach-Object { $_.Substring(3) }
    $hit = $dirty | Where-Object { $merged -contains $_ }
    if ($hit) { Write-Output "ABORT: dirty merged paths: $hit"; exit 1 }
    & $git merge --no-ff --no-edit ccr/v4
    if ($LASTEXITCODE -ne 0) { & $git merge --abort; Write-Output "ABORT: merge conflict"; exit 1 }
    python tools/test_gsd_mission.py
    if ($LASTEXITCODE -ne 0) { & $git revert -m 1 --no-edit HEAD; Write-Output "REVERTED: test_gsd_mission failed"; exit 1 }
    python tools/test_goal_lease.py
    if ($LASTEXITCODE -ne 0) { & $git revert -m 1 --no-edit HEAD; Write-Output "REVERTED: test_goal_lease failed"; exit 1 }
    python tools/test_gsd_mission_ccr_a6.py

Expected:
- `MC_PASS=230/230`
- `GOAL_LEASE_PASS=21/21`
- `13 passed, 0 failed`

Known red at 3665d157, before A6, and not a revert trigger: cwd_align 15/16, legacy_characterization 24/33, sleep 5/6.

**Step 3. Release.** mods/ changed since the last release: A1 3665d157 and A7 a364877b both touch `mods/cpp-cognitive-runtime/hooks/{policy,register,policy.test}.ts`. A1 rule: guarded on Madzia.

    $madzia = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*kobiimii*' }
    if ($madzia) { "SKIP release: Madzia driver running, pid(s) $($madzia.ProcessId -join ',')" } else { python tools/ccr_release.py release }
    python tools/ccr_release.py status --sessions

Record both outputs. If the release was skipped, do not open the A7 canary pane: an old release ignores `CCR_MAIN_CANARY`.

**Step 4. Book the ledger.** This step closes `ledgers_reconciled`.
- First check that `goal-status --goal ccr` still shows L10 as the latest lease.
- A0's cap of 22,826,870 covers only the census.
- Post-census GEX44 spend is 12,968,143. X2 adds about 1.8M (estimate).
- So open the lease with cap 1.05 x (21,739,876 + 12,968,143 + 1,800,000) = **38,333,420**. This books spend that has already happened; it is not new capital (programme 120M, 'approve p95' 6830508e).

Commands:

    Set-Location C:\Users\User\.claude\skills\claude-power-pack
    python tools/mission_spend.py goal-status --goal ccr
    python tools/mission_spend.py goal-lease-open --goal ccr --succession-id ccr:book-s3 --cap 38333420 --prev-lease L10

Then:
1. Run the 16 `goal-settle --measured` lines from `vault/programs/ccr/evidence-v4-stage3-A0.md` section `## LAPTOP_APPLY`, unchanged.
2. Run the post-census rows below. The values were measured by `ccr_spend_census.py measure` on GEX44, except that the probe and canary values come from their unit receipts.

    python tools/mission_spend.py goal-settle --goal ccr --session 47649e90-2c69-43ee-a310-fa8a35cb967e --measured 1781551
    python tools/mission_spend.py goal-settle --goal ccr --session 9dde3bfe-a3e3-4307-8de8-4139f80da267 --measured 1470725
    python tools/mission_spend.py goal-settle --goal ccr --session 59fd86cb-2d58-4e90-aeea-e8bb994b5d2e --measured 14600
    python tools/mission_spend.py goal-settle --goal ccr --session 99d97182-1e6d-4a62-aeda-cc6321da9c54 --measured 14273
    python tools/mission_spend.py goal-settle --goal ccr --session 95ab3d08-26bd-47dd-988e-d3a8ca131c91 --measured 13365
    python tools/mission_spend.py goal-settle --goal ccr --session 228f7133-03c4-4504-8509-eb19e760272c --measured 10159
    python tools/mission_spend.py goal-settle --goal ccr --session 2ee1f371-b2f2-430f-a34a-62f2c8a54c4b --measured 3123
    python tools/mission_spend.py goal-settle --goal ccr --session ae35f5fe-8d58-494f-ac79-0325bfb8c214 --measured 1426157
    python tools/mission_spend.py goal-settle --goal ccr --session 2d004877-512b-47a0-ba16-2d405762e889 --measured 42540
    python tools/mission_spend.py goal-settle --goal ccr --session eeddc9ec-fe66-491c-8535-eb253c9afb6c --measured 2367697
    python tools/mission_spend.py goal-settle --goal ccr --session 8f18a9e7-524d-41ac-bbe2-2b3bebd4a8c1 --measured 1992980
    python tools/mission_spend.py goal-settle --goal ccr --session d084c077-d96e-4ea9-bbb3-595091013463 --measured 1710253
    python tools/mission_spend.py goal-settle --goal ccr --session 05d0d13f-a249-4f51-bdb9-5f68ac95c0ac --measured 3613494
    # X2 (this unit): take the final value on GEX44 with
    #   python3 tools/ccr_spend_census.py measure /home/kobii/missions/ccr-s3-data/run-X2.jsonl
    python tools/mission_spend.py goal-settle --goal ccr --session bf1bb90a-3941-4a94-9893-0c85558b7765 --measured <final X2>
    # Coordinator pane e10a9f08 (laptop-only): measure it from its own transcript, then settle it (A0 evidence).
    python tools/mission_spend.py goal-status --goal ccr

Notes on the booking:
- The A0 sid appears twice, first at 1,492,774 and then at 1,781,551. The watermark books only the 288,777 delta.
- The A2 sid 0c9c8dbd is already in the 16 rows at 4,359,814 (both streams). Do not settle it again.
- V1 r6-CCR stays UNKNOWN and is never booked as 0.

**Step 5 (optional, turns things on).** Do this only after the release.
- `copy vault\programs\ccr\stage3\a3\pgo-classes.json $env:USERPROFILE\.claude\ccr\state\pgo\pgo-classes.json`. This makes DEFLATE live by default for bounded-code slim launches (A6). Set `CPP_CCR_DEFLATE=off` to hold it.
- `copy vault\programs\ccr\stage3\a4\pgo\*.breakeven.json $env:USERPROFILE\.claude\ccr\state\pgo\`. The rotate advice is observe-only.
- The Owner's canary pane and its read-out are exactly as in WU-A7-receipt.md `## LAPTOP_APPLY`.

## Text for RESUMPTION_FILE (coordinator writes it)
CCR v4 Stage 3 closed on GEX44 by X2 (2026-10-14). Certificate: **EFFECTIVENESS_PARTIAL** (unchanged).

State:
- A0-A7 and X2 are committed on GEX44 mission/ccr-s3. They are not yet on laptop ccr/v4 or main.
- Stage 3 GEX44 spend is 29,007,409 processed (A0-A7, all sessions incl. probes and canaries, census-measured), plus X2 at about 1.65M.

Ladder:
- BOUNDARY_COST 1/4. Met: the real admission intervention (A6 DETERMINISTIC_PATH 4/4). ABSTAIN:
  - second-class saving +7.95 % / +1.53 % vs 15 %;
  - held-out forecast APE 46.4 % vs 25 % (long-textual 21.7 % on n 7 < 8);
  - ledgers unbooked.
- LONG_HORIZON 1/3. Met: estate elasticity. ABSTAIN: A5 canary n 1/3, history elasticity replay-only 0.525.

Negative knowledge:
- Overruns: A2 4.36M vs 1.5M, A4 6.43M vs 3.0M, A6 6.07M vs 3.0M, A7 3.61M vs 3.0M.
- The GEX44 breaker failed open on an empty measurement (string `message` line). Fix the driver to treat empty as over before the next GEX44 run.

Next actions, in order:
1. X2 LAPTOP_APPLY steps 0-2: fetch mission/ccr-s3 into ccr/v4, then ccr/v4 into main, then test_gsd_mission + test_goal_lease.
2. Step 3: guarded release, then `ccr_release.py status --sessions`.
3. Step 4: `goal-lease-open ccr:book-s3 --cap 38333420`, then all settles, then `goal-status --goal ccr`.
4. The Owner's A7 canary pane (`$env:CCR_MAIN_CANARY='1'; claude`), then `python tools/ccr_main_shadow.py --canary ...`.
5. A5 rounds 2-3 on GEX44 under a fresh budget (~2.94M) to move a5_real_canary from n 1 to n 3.
6. Fix the GEX44 driver breaker: empty measurement means over the limit, plus a test with a string `message` line.

## Commit
On branch mission/ccr-s3, pathspec only: CERTIFICATE-v4.md, NEGATIVE_KNOWLEDGE.md, ukdl-universal.md and this receipt. The hash is verified with `git log -1 --format='%h %s'` after the commit. The untracked `.pp-capabilities` and `docs/*/tools__ccr_release.py.md` files are not this unit's and are not committed.
