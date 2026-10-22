# E2 evidence: boundary ledger, call profile, boundary authority

## Boundary ledger on one real mission

`python -I tools/boundary_ledger.py ledger --transcript <49c0ae70 transcript>`: the worker the plan (`vault/plans/ccr-v5-economic-kernel-2026-10-15.md` section 1) measured by hand. The tool reproduces the plan's hand counts from the transcript alone:

| measure | tool output | plan section 1 |
|---|---:|---|
| model calls | 103 | 103 |
| discovery calls (only Read/Grep/Glob) | 54 | ~55 read/search |
| parallel calls (2+ tools in one call) | 37 | 37 |
| test runs (Bash or PowerShell) | 17 | 17 |
| write calls (Edit/Write) | 28 | ~28 |
| `gsd_mission.py` Reads | 24 | 24 |
| calls that re-read an already-read file | 23 (ratio 0.223) | not in the plan |

Other re-read files: `mission_spend.py` 6, `session_budget_guard.js` 4, `hook-dispatcher.js` 2, `amr_fence.js` 2.
The first run counted 0 test runs because the worker ran every test through the PowerShell tool and the classifier only knew Bash; fixed (`SHELLS`) and pinned by `V-BND-LEDGER-CLASSES`.

## Call profile (PGO)

`boundary_ledger.py suggest` turns measured per-unit call counts into a `max_calls`: p80 (nearest rank) x (1 + margin 0.25), and refuses below 3 units. On the one real transcript it prints `max_calls: null, "1 measured unit(s) < 3: no call profile to suggest from"`. No cap is suggested from fewer than three finished units, and the 0.25 margin is a chosen value, not a measured one.

## Boundary authority (max_calls in the phase lease)

`phase_lease.make_lease(max_calls, calls_base)`; `judge(..., calls)`: more calls than the cap since the lease base is a TRIP whatever the tokens say; an unmeasured count, or one below its base, is BLOCKED. `gsd_mission.set_envelope` measures `calls_base` itself (`mission_spend.processed_calls`, a caller-supplied base is not used) and refuses when the count is unmeasurable; `_phase_breaker` parks a mission over its cap with a phase-breaker cost hold and stops the worker. CLI: `envelope --phase-lease N --phase-forecast .. --phase-state .. --phase-max-calls K`.

The refusal observed in a test (`tools/test_boundary_authority.py`, paired with a control that is admitted):
```
PASS V-BND-JUDGE-AT-CAP-OK the cap itself is allowed
PASS V-BND-JUDGE-OVER-CAP-TRIPS boundary breaker: phase 1 made 7 calls > max_calls 6; reforecast before release
PASS V-BND-JUDGE-TOKENS-FINE-STILL-TRIPS tokens were 10 of a 1,000,000 forecast
PASS V-BND-CONTROL-AT-CAP-RUNS at the cap nothing is held
PASS V-BND-OVER-CAP-HOLDS {'reason': 'cost breaker (phase lease): boundary breaker: phase 1 made 7 calls > max_calls 6; reforecast before release', ...
```

## Test output
```
BOUNDARY_PASS=22/22  threshold=all        tools/test_boundary_authority.py
PHASE_LEASE_PASS=23/23                    tools/test_phase_lease.py
PHASE_LEASE_MISSION_PASS=15/15            tools/test_gsd_mission_phase_lease.py
ADM_PASS=43/43  CTX_PASS=10/10  EST_PASS=9/9
MSPEND_PASS=40/41                         tools/test_mission_spend.py (FAIL V-MSPEND-HOLD-PLAN-NONE; identical at 1cbd1cb5, before E1/E2)
```

## Limits
- No cap is derived from data yet: PGO needs three finished units of one kind, and this unit had one real transcript. No lease with `max_calls` has been set on a live mission.
- `processed_calls` counts distinct message ids in the mission's own transcripts, the same attribution rule as `processed_tokens`; it has no live-mission run behind it, only the injected-meter tests.
- `test_mission_spend.py` was already 40/41 before this unit; not touched here.
- "Gate" in the plan row is the phase breaker (`_phase_breaker`, run by `supervise`); no new hook was registered.
- Correction to E1: commit `15b71b82` had put the E1 context-check block in the wrong place in `gsd_mission.py` (a SyntaxError at that commit, pushed to `origin/ccr/v5`); the E2 commit restores it. Cause: `git apply --cached --unidiff-zero` of a zero-context insertion. Re-run `test_gsd_mission_admission.py` (43/43) passes on the repaired file.
