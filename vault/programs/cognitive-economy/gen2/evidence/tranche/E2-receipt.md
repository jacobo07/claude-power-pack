# E2 receipt -- coordinator enforcement + call accounting (tools/tranche_driver.py)

verdict: PASS

## What changed
- tools/tranche_driver.py:96 `declare_coordinator` -- runs `mission_spend.py session-declare --session <coord sid>` from REPO cwd with
  --stop = baseline (spend() of the coordinator, unknown -> 0) + allowance, --target/--warn at 80%/90% of the allowance above baseline,
  --calls-estimate 6 (`COORD_CALLS`). Refusal records `coordinator_admission.verdict=REFUSED` and logs COORDINATOR_ADMISSION_REFUSED.
  --since not passed: the stop already includes the whole-transcript baseline, which is what the guard counts by default.
- tools/tranche_driver.py:113-115 `drive(..., manifest=None, calls_count_fn=calls_of)` -- declare before the packet loop; refused -> no packet runs.
  Without a manifest (or without sid/allowance) behaviour is unchanged.
- tools/tranche_driver.py:38 `calls_of` -- reuses `mission_spend.session_tokens(transcript)["calls"]` (no second counter); transcript
  found like spend(); no transcript -> None. NOTE: session_tokens counts tool_use blocks (its docstring), the guard's own definition.
- tools/tranche_driver.py:50 `boundaries` -- 1 per packet unless a `BOUNDARIES:` line gives a count or ;/,-separated items.
- tools/tranche_driver.py:154 each step result gains `calls` and `boundaries`.
- tools/tranche_driver.py:169,186-187 `--manifest` option; main returns 1 on a refused coordinator (an empty step set must not read as all-PASS).
- tools/test_tranche_driver.py:90-125 six new gates: COORDINATOR-DECLARED-FIRST (stop 500+1000=1500, before launch),
  STEP-CALLS-AND-BOUNDARIES, COORDINATOR-REFUSED-NOTHING-LAUNCHED, NO-MANIFEST-UNCHANGED, CALLS-FROM-TRANSCRIPT (fixture of 2 calls ==
  session_tokens == 2; absent -> None), BOUNDARIES-LISTED.

## Commands (exit codes)
- `python tools/test_tranche_driver.py` -> 0, DRIVER_PASS=27/27
- mutation (a) coordinator declare skipped (`if False:`) -> 1, DRIVER_PASS=25/27 (DECLARED-FIRST, REFUSED-NOTHING-LAUNCHED red)
- mutation (b) `calls` dropped from the step result -> 1, DRIVER_PASS=26/27 (STEP-CALLS-AND-BOUNDARIES red)
- restored -> 0, DRIVER_PASS=27/27; `git commit -F <msg> -- tools/tranche_driver.py tools/test_tranche_driver.py` -> 0

## Accounting
- physical tool calls: 7 (Read x2, Grep, Write, Edit, PowerShell x2) over 5 model calls
- semantic boundaries: 3 -- (1) coordinator baseline = its measured spend, stop = baseline + allowance, no --since;
  (2) calls = session_tokens tool_use count reused, unknown = None; (3) refused coordinator makes main exit 1.

Not done: no live run against a real manifest/coordinator session (fakes only); real admission outcome unobserved.

BOUNDARIES: coordinator-stop-baseline; calls-reuse-session_tokens; refused-coordinator-exit-1
COMMITS: 317e86a4