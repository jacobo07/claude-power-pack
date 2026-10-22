# E3 evidence: forecast gate, code-map page, fresh epoch, canary

## Forecast-gate refusal on an over-floor (under-priced) route

`route_admission.forecast_gate(forecast, calls, profile, floors)`: a forecast for N calls cannot be below N x the profile's measured first-call floor (every call re-reads at least that context). Wired into `gsd_mission.set_envelope` for a phase lease that carries `max_calls` (the profile is `phase_lease.profile`, else the mission's `worker_profile`, else `top-level-worker`); `CPP_FORECAST_GATE=off` is the kill switch. UNKNOWN (no measured floor, or a non-positive-integer input) is a refusal, never OK.

Observed through the real entry point (canary, mission `m-canary`, 6 calls, top-level-worker floor 110,835):
```
CANARY OK   forecast-gate-refuses phase lease refused (forecast gate UNDERPRICED): forecast 665,009 < 6 calls x top-level-worker floor 110,835 = 665,010
CANARY OK   forecast-gate-control-admits forecast 665,010 = 6 calls x 110,835
```
One token below the bound is refused, the bound itself is admitted.

## Code-map page for gsd_mission.py (UCRE first rung)

`python -I tools/code_map.py map|page FILE [--store DIR]`: symbol index with line ranges, keyed by the file's sha256 so an edited file can never be served a stale page. `.py` only; any other suffix, or an unparseable file, is refused rather than guessed. On the E3 `gsd_mission.py` (351,130 B, 5,921 lines): the page is 21,917 B (6.2% of the file) and 207 lines, 205 symbols. The part the 49c0ae70 worker paged 24 times:

```
L1628-1663 (36) def _phase_breaker - CCR v5 A2: judge the mission's phase lease (tools/phase_lease.py) against measured spend. ...
L2347-2458 (112) def set_envelope - Set the launch envelope of a live mission (spec mission-envelope-and-compiled-wu): ...
L2581-2665 (85) def admit_route - Judge the mission's compiled work unit against its route (tools/route_admission.py) ...
L4918-4937 (20) def arm_chain - Atomic arm (WU-1H addendum C): arm --no-launch, envelope, admit. ...
```
`set_envelope` is 112 lines at a known range, where the worker re-read the 5,600-line file in chunks.

## Fresh epoch per plan

A packet change already moved `wu_packet_epoch` (so `gsd_epoch` rotates to a fresh worker). A phase lease for ANOTHER phase is another plan and now moves it the same way; re-setting the same phase does not:
```
CANARY OK   epoch-same-phase-keeps wu_packet_epoch None
CANARY OK   epoch-new-phase-moves wu_packet_epoch 1 owner epoch 1
```

## Canary

`python -I tools/ccr_canary.py` drives the Envelope 0-3 mechanisms through their real entry points on a throwaway mission (zero model calls), each refusal with its control:
```
CANARY OK   boundary-at-cap-runs 6 of 6 calls
CANARY OK   boundary-over-cap-holds 7 of 6 calls
CANARY OK   code-map-miss-then-hit gsd_mission.py: file 360,505 B -> map 22,202 B
CANARY OK   code-map-edit-misses new sha, new page
CANARY_RESULT=PASS 8/8
```
(The canary ran on the working-tree `gsd_mission.py`, 360,505 B, which also holds other panes' uncommitted hunks; the 351,130 B figure above is the committed file.)

`V-CANARY-RED-WHEN-GATE-OFF` shows it can fail: with `CPP_FORECAST_GATE=off` the canary exits 1 on `forecast-gate-refuses`.

## Test output (clean checkout of HEAD + the E3 files)
```
FORECAST_GATE_PASS=17/17  threshold=all     tools/test_forecast_gate.py
BOUNDARY_PASS=22/22  PHASE_LEASE_PASS=23/23  PHASE_LEASE_MISSION_PASS=15/15
ADM_PASS=43/43  ENVELOPE_PASS=67/67  EPOCH_PASS=92/92  CTX_PASS=10/10
```

## Limits
- The canary uses injected meters and a temp state dir; it is not a live-mission run, and the code-map page is not yet read by any worker or hook (no UCRE serve path is wired, only the page store and its hit/miss rule).
- The forecast gate covers a phase lease that carries `max_calls`; an envelope `token_estimate` without a lease is still judged only by route admission.
- The code map is Python-only; JS/PowerShell files are refused.
- The canary imports the test harness of `test_boundary_authority.py` for its mission setup (shared, not re-implemented).
- Still open from earlier units: `vault/config/measured-ctx1.json` is not populated, and PGO has one real transcript, so no cap is derived from data.
- Envelope 4+ is not touched; it returns to the Owner with this receipt.
