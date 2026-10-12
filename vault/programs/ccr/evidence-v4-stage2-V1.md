# Evidence v4 Stage 2 V1 -- real canary

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
