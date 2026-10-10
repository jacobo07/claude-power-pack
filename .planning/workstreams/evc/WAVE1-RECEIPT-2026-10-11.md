# EVC wave 1 — receipt (2026-10-11)

Mechanism: one slim-t2 mission per work unit (`gsd_mission arm-chain`, `route_admission` ADMISSIBLE before launch),
sequential, one writer, branch `evc/e2` in `.claude/worktrees/evc`. The sweep auto-launches any armed mission: arm the
next unit only after the previous one is terminal.

| Unit | Result | Commit(s) | Processed |
|---|---|---|---|
| WU-1 cost-collapse T1+T2 | T2 kept; T1 reverted (needs 10 unlanded grammar commits, e.g. 924bdad6, d4f18ca8) | 38da72ba, revert d40031c8 | 0.49M |
| WU-2 gsdx_reforecast | DONE | f397d014 | 0.08M |
| WU-3 dgl W1b+W2 (8 picks) | DONE | 3ccbb1ee..bd5642a4 | 0.29M |
| WU-4a-t1..t3 plan 01-01 | DONE | eab907ee, f4908b3c, caa6a2be | 0.41 + 0.63 + 0.51M |
| WU-4b-t1 / t1c plan 01-02 T1 | t1 BLOCKED (call cap; parallel same-file edits refused), t1c DONE | e6b65ddc | 0.59 + 0.38M |
| WU-4b-t2 / t2c plan 01-02 T2 | t2 BLOCKED (call cap), t2c DONE | 81a53207 | 0.67 + 0.54M |
| WU-4b-t3 plan 01-02 T3 | DONE | df86d0fd | 0.48M |
| Close-out | autopsy fork-meter parity gate follows the deduped meter | d7ca40d4 | (coordinator) |
| **Total wave 1** | | | **5.07M** (cap 9.5M) |

Programme spend: epoch 1 2.64M + epoch 2 31.80M + wave 1 5.07M = **39.51M** (enforced stop 65M).

## Regression at close (evc/e2 d7ca40d4)
13 suites. 12 green: usage_truth 30/30, mission_spend 30/30, autopsy 42/42, gsdx_reforecast, goal_lease 10/10,
workspace_lease 10/10, owner_hold 32/32, surface 6/6, steward 22/22, lineage 11/11, envelope 55/55, usage_index 22/22.
`test_session_budget_guard` V-SBG-LATENCY red (232-1495 ms vs < 50 ms) **also on the live install at the same moment**:
host load (RAM 1-2 GB free), not an EVC regression.

## Debt
- Red-first unproven: 01-01 Task 3 gates; 01-02 Task 2 statement-form gates.
- 01-02 T2c narrowed the source-scan regex itself (`hold\b` -> `owner[ _]hold\b`) because capsule/provider holds matched; review.
- Snapshot `measured_at` uses the real clock, not the injected `now` (usage_truth called without now); no gate checks it.
- `gsdx_reforecast.py` hardcodes the LIVE `mission_spend.py` path.
- 01-03 (price table file) not executed: `usage_index.py` already prices every category (disposition).
- Packet lessons: 01-02-class tasks need ~25-35 calls (15 was too tight); forbid parallel same-file edits; grep commit
  subjects as `evc-01-0x): task`.
