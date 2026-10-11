# Phase 4 plan: distribution forecast and live reforecast (compact)

Landed: `tools/gsdx_reforecast.py` (f397d014; expected/lower/safety point forecast, gate `tools/test_gsdx_reforecast.py`, 13 checks).
Remaining: percentile output with confidence, the predictive DRAINING edge, the hardcoded LIVE path fix.
Python: `& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'`, `$env:PYTHONIOENCODING='utf-8'`.
One Edit per file per message. Do not touch `mission_spend.py` `judge()` semantics (only add a sibling function).

## Task 1: repo-relative spend path + percentile distribution with confidence
Files: `tools/gsdx_reforecast.py`, `tools/test_evc_distribution.py` (new).

Gates first (write `test_evc_distribution.py` with the `check()` pattern of `test_gsdx_reforecast.py` lines 1-12, run it, see RED):
- V-EVC-DIST-ORDER: `distribution(samples, spent)` returns keys `lower,p50,p80,p95,ceiling` with
  `lower <= p50 <= p80 <= p95 <= ceiling`. RED input: module has no `distribution` (ImportError counts as RED). Positive control: samples `[1,2,3,4,5,6,7,8,9,10]*1e5` -> p50 = 5.5e5 +-1, p95 >= 9.5e5.
- V-EVC-DIST-WIDE: samples with n < 5 -> `confidence == "WIDE"` and ceiling >= 2 x p95 (stated widening); n == 0 -> `confidence == "UNKNOWN"` and every percentile `None`. RED input: `[]` and `[3e5]`. Control: n = 12 -> `"NORMAL"`, ceiling == max(samples).
- V-EVC-DIST-ONEPOINT: n=1 must not produce a zero-width band (`p95 > p50`); RED input `[4e5]` against a naive percentile (all equal).
- V-EVC-DIST-LIVEPATH: `SPEND` is derived from `__file__` (`os.path.join(dirname(abspath(__file__)), "mission_spend.py")`), not a user path. RED: source scan finds the literal `C:\Users\User`. Control: scan of a string containing the literal is flagged (prove the scanner bites).
- V-EVC-DIST-CLI: CLI run (copy `run()` from test_gsdx_reforecast.py with `--goal-json`) emits `"distribution"` in the JSON and still emits the old `remaining/total/iterate/owner_needed` keys unchanged.

Implementation (`tools/gsdx_reforecast.py`):
1. Line 14: `SPEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mission_spend.py")`.
2. Wrap `main()` call (line 75) in `if __name__ == "__main__":` so the test can import `distribution` (put the module dir on `sys.path` in the test; run with plain `python`, not `-I`, for the import check; keep `-I` for the CLI check).
3. Add pure `distribution(samples, spent=0)` above `main()` (line 20): sort; linear-interpolated percentile; `n==0` -> UNKNOWN/None; `n<5` -> WIDE, band from `min(samples)*0.5` to `ceiling = 2*p95`; one sample -> p95 = 1.5 x sample; else NORMAL, ceiling = max. Every value is `spent + remaining`-free (remaining only; caller adds `used`).
4. In `main()` after `rem` (line 51): samples = per-pending-unit `route.envelope.target * FACTOR` list plus the plan-line expected values x M x s; `f["distribution"] = distribution(...)` with `total_distribution` = same plus `used`. Do not change existing keys.

Verify:
```
python tools\test_evc_distribution.py
python tools\test_gsdx_reforecast.py
```

## Task 2: predictive DRAINING edge as a pure function with its gate
Files: `tools/mission_spend.py`, `tools/test_evc_draining.py` (new).

Gates first:
- V-EVC-DRAIN-EDGE: `judge_predictive(rec, spent, p95_remaining, tail=0)` returns `{"drain": reason}` when `spent + p95_remaining + tail > authority`, where authority = `int(rec["token_estimate"]) * float(rec.get("token_trip_ratio") or DEFAULT_TRIP_RATIO)`. RED input: `token_estimate=1_000_000`, ratio default, `spent=600_000`, `p95_remaining=500_000` (below the hard breaker 0.6M < ratio x est, yet predicted over). Fails today: function does not exist. Positive control: `spent=100_000, p95_remaining=200_000` -> `drain is None`.
- V-EVC-DRAIN-BEFORE-BREAKER: for the RED input, `judge(rec, spent, fp)["trip"] is None` (hard breaker silent) while `judge_predictive(...)["drain"]` is set: the edge fires strictly before the breaker. Control: `spent > ratio x est` -> `judge` trips (existing behaviour untouched).
- V-EVC-DRAIN-FAILOPEN: `spent=None`, missing estimate, or `p95_remaining=None` (UNKNOWN confidence) -> `drain is None` (never drain on missing data). RED: each of the three inputs; mutate by removing the guard and see the gate fail.
- V-EVC-DRAIN-TAIL: protected tail counts: spent+p95 = authority - 1 passes, with `tail=2` drains. Boundary equality (`==`) does not drain.
- V-EVC-DRAIN-EXISTING: `python tools\test_mission_spend.py` unchanged-green.

Implementation:
1. `tools/mission_spend.py`: add `judge_predictive` directly after `judge` (ends line 394), pure, no I/O. Reason text states: spent, P95 remaining, tail, authority, and "spend may continue until the hard breaker; new work is not started".
2. Reuse `DEFAULT_TRIP_RATIO` already referenced at line 378.

Verify:
```
python tools\test_evc_draining.py
python tools\test_mission_spend.py
```

## Task 3: drive DRAINING from the supervisor and record it (mission record + ledger)
Files: `tools/gsd_mission.py`, `tools/test_evc_draining_wire.py` (new).

Decision (within authority): DRAINING is NOT added to `STATES` (line 71; Phase 5 owns the state set). It is an additive record field `lease_state = "DRAINING"` written by `transition(..., event="lease_draining", lease_state=..., drain=...)`, state and epoch unchanged, plus ledger event `lease_draining`. Check at implementation that `transition` (line 286) accepts extra record fields the way `cost_mark=` is passed at line 1440; if it whitelists keys, add `lease_state` and `drain` to that whitelist.

Gates first (inject `measure=` and `fingerprint=` like the existing `_cost_breaker` tests; find them with `Grep "_cost_breaker(" tools\test_*.py`; copy their fixture, isolated state dir, no real ledger):
- V-EVC-DRAIN-WIRE: a RUNNING rec with estimate 1M, measured spend 600k and an injected forecast with p95_remaining 500k -> after `_cost_breaker`, `rec["lease_state"] == "DRAINING"`, `rec["state"]` unchanged, no `owner_hold`. RED today: no wiring, `lease_state` absent. Control: spend 100k -> no field.
- V-EVC-DRAIN-LEDGER: the same run appends exactly one `lease_draining` ledger row with spent, p95_remaining, authority. Second pass with the same inputs appends none (idempotent: the field is already set).
- V-EVC-DRAIN-HARD-WINS: spend over ratio x estimate -> breaker still sets the Owner hold (existing path) and `lease_state` may remain DRAINING; the hold is not skipped.
- V-EVC-DRAIN-NOFORECAST: no forecast available (callable returns None or raises) -> `_cost_breaker` result identical to today and one `cost_breaker_unmeasured`-style ledger row on raise (fail-open, recorded).

Implementation (`tools/gsd_mission.py`):
1. Change signature at line 1408: add `forecast=None` (callable `rec -> p95_remaining|None`, default `_p95_remaining`).
2. New helper `_p95_remaining(rec)` above `_cost_breaker`: reads `rec.get("forecast_p95_remaining")` (written by the reforecast tool or the supervisor; None when absent). No subprocess here, so the supervisor pass stays cheap.
3. In `_cost_breaker`, after `verdict = ms.judge(...)` (line 1424) and in the `not verdict["trip"]` branch before the `mark` branch (line 1439): call `ms.judge_predictive`; if `drain` and `rec.get("lease_state") != "DRAINING"`: `lr.ledger_append(mid, "lease_draining", ...)` then return `transition(..., event="lease_draining", lease_state="DRAINING", ...)`. Wrap the forecast call in the same try/except pattern as lines 1425-1428.
4. `tools/gsdx_reforecast.py`: add optional `--mission-record PATH`; when given, write `forecast_p95_remaining` (from Task 1's `distribution.p95`, only when confidence != UNKNOWN) into that record file via the existing record write helper (find with `Grep "def save\|def _write" tools\gsd_mission.py`). If no safe helper exists, skip this flag and leave the field to the supervisor; write that decision to the progress file.

Verify:
```
python tools\test_evc_draining_wire.py
python tools\test_evc_draining.py
python tools\test_evc_distribution.py
python tools\test_gsdx_reforecast.py
python tools\test_mission_spend.py
python tools\test_owner_hold.py
python tools\test_goal_lease.py
```
Commit per task: `feat(evc-04-0N): task`. `test_session_budget_guard` V-SBG-LATENCY red is host load, not a regression.
