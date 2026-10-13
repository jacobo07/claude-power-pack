# Evidence v4 Stage 2 V1 -- real canary

## Attempt 2 (2026-10-13, Owner-approved guard 1.5M) -- current

Verdict: **PASS on saving, with one limit.** Weighted saving of CCR vs OFF is at least **54.2 %** (gate >= 15 %). Parity was 5/5 on the runs that finished. Run r6-CCR was killed mid-call by the Claude Code host's memory reaper, so the CCR arm has n=2: its contract was recorded, but it has no summary. The bound does not depend on r6. With two CCR values known (37,324 and 18,973), the median of three is at most 37,324, whatever r6 would have produced.

| run | arm | calls | input | cache_read | cache_creation | output | processed | weighted (0.1/1.25/1/5) | answer | match |
|---|---|---|---|---|---|---|---|---|---|---|
| r1 | OFF | 4 | 8 | 247,996 | 64,346 | 15 | 312,365 | 105,315 | p4p2a12;PASS;NOT_IMPROVED | yes |
| r2 | CCR | 4 | 8 | 64,873 | 24,571 | 23 | 89,475 | 37,324 | p4p2a12;PASS;NOT_IMPROVED | yes |
| r3 | OFF | 6 | 12 | 438,698 | 29,976 | 40 | 468,726 | 81,552 | p4p2a12;PASS;NOT_IMPROVED | yes |
| r4 | CCR | 4 | 8 | 72,351 | 9,292 | 23 | 81,674 | 18,973 | p4p2a12;PASS;NOT_IMPROVED | yes |
| r5 | OFF | 6 | 12 | 462,697 | 7,862 | 36 | 470,607 | 56,289 | p4p2a12;PASS;NOT_IMPROVED | yes |
| r6 | CCR | -- | -- | -- | -- | -- | -- | -- | killed (host memory reaper) | UNKNOWN |

- Weighted: OFF median 81,552. CCR median of the 2 known runs is 28,149 (-65.5 %). The upper bound of the median of 3 is 37,324 (-54.2 %).
- Processed: OFF median 468,726; CCR median 85,575 (-81.7 %).
- Per call: OFF 78,091 / 78,121 / 78,434; CCR 22,369 / 20,418. The saving comes from the per-call floor (context per call), not from the number of calls. That matches the unit floor of 21,031 in the contract. The source is the work-unit lean floor; tool-output projection plays little part here, because the task reads small files.
- Forecast vs actual (CCR runs): the contract gave P50 1,179,457 and P80 2,164,496; actual was 89,475 and 81,674, so the forecast is **13.8x high**. The class model was built from Madzia a9-a13 driver workers (P50 28 calls) and does not fit a 4-call bounded lookup. The contract still ADMITs correctly, but its number is not a usable forecast for this class.
- modes.json: absent before and absent after. The script's `finally` block did not run (the process was killed during the CCR arm, which deletes modes.json), so `canary-meta.json` was rewritten by the coordinator from the per-run summaries and records the abort.
- Commands: `C:\Users\User\Apps\ccr_v1\run_canary.py` with `GUARD=1500000` (env `CCR_V1_GUARD`); streams in that dir; attempt 1 artefacts kept in `C:\Users\User\Apps\ccr_v1\attempt1`. The run was made from the coordinator pane, not by a worker (cheaper: about 6 haiku sessions, ~1.5M processed in total).

## Attempt 1 (2026-10-13 01:2x, guard 400K) -- superseded

Verdict: FAIL:runaway (first run, arm OFF, processed 457,404 > 400,000 guard). The canary stopped after 1 of 6 runs, so the weighted saving of CCR vs OFF was NOT measured (no number).

| run | arm | calls | input | cache_read | cache_creation | output | processed | weighted (0.1/1.25/1/5) | answer | match |
|---|---|---|---|---|---|---|---|---|---|---|
| r1 | OFF | 6 | 12 | 394,835 | 62,497 | 60 | 457,404 | 117,917 | p4p2a12;PASS;NOT_IMPROVED | yes |

Ground truth (script, no model): `p4p2a12;PASS;NOT_IMPROVED`. Parity 1/1 (OFF only). No CCR run, so no CCR contract was recorded or compared (forecast vs actual: n/a). Class model from Madzia a9-a13: calls P50 28, processed P50 1.19M, P80 2.09M, far above this bounded task.

Findings:
- The OFF floor is about 76K tokens per call (394,835 cache_read over 6 calls plus 62,497 creation). The global harness context alone exceeds the 400K per-run guard in a 6-call task, so the guard cannot pass at this scale under `claude -p` with the user's global settings.
- The packet says the unit JSON key is `cls`; the source (hooks/policy.ts parseWorkUnit) reads `class`. The runner uses `class`.
- modes.json was originally absent. The OFF arm wrote {"project":"off"} (sha256 a9dcb4565dcfea32f2158e15577eb2cf36212c34c9297d3c42adb798e9bfcdcc) and it was restored by deletion (ABSENT equals original ABSENT).
- Runtime receipts were written even in the OFF arm (link/row/attach/compose/call/usage), so shadow measurement continues.

Commands: scripts in C:\Users\User\Apps\ccr_v1 (truth.py, run_canary.py, prompt.txt, pgo.json); streams stay in that scratch dir; summaries in vault/programs/ccr/stage2/v1/. A rerun needs an Owner-raised per-run guard (e.g. 1.5M) or a lighter harness.
