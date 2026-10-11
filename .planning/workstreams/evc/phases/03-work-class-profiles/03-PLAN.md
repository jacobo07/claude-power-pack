# Phase 3 — Work-class profiles and confidence (compact plan)

Disposition: SHRINK. `tools/cost_to_completion.py` (CTC) is the primary estimator; the `[1M,15M]/2` auto envelope
(`gsd_mission.py` `_auto_budget` 1364, `auto_headroom` 1347, `_BUILTIN_BUDGET` 1331) stays only as a labelled emergency
fallback. Add confidence states and the miss taxonomy. Reuse `vault/config/route-floors.json` profiles and
`route_admission.record_actual` (route_admission.py:72) misses. No new profile store.

Python: `& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'` with `$env:PYTHONIOENCODING='utf-8'`.
Tasks are sequential (2 uses 1, 3 uses 1+2). One Edit per file per message.

Existing anchors: CTC `compile_cost` 64 (returns `profile_source` per class: prior|profile|actual), `PRIORS` ~45,
`MODEL_CLASSES` 44, `main` 129. RA `MISS_FACTOR` 1.25 (line 61), `is_degraded` 62, `max_ratio` 68, `record_actual` 72.

### Task 1: Confidence state machine and miss taxonomy (pure module)
Files: create `tools/evc_confidence.py`; create `tools/test_evc_confidence.py`.
Gates first (write the test, run it RED: `ModuleNotFoundError` for evc_confidence is the red; then each check red against a
stub returning `"UNKNOWN"`/`"UNKNOWN"`):
- V-EVC-CONF-STATES: `state(n=0, misses=[])=="UNKNOWN"`; n=1..2 -> EXPLORATORY; n=3..4 -> PROVISIONAL; n>=5 with no
  misses -> CALIBRATED. Positive control: n=5 and a single 1.1x hit stays CALIBRATED.
- V-EVC-CONF-DEGRADED: CALIBRATED with 1 material miss (actual > 1.25 x need) -> DEGRADED. Control: 1.25x exactly is no miss.
- V-EVC-CONF-INVALIDATED-3: three comparable material misses (same taxonomy kind, reuse `ra.is_degraded` on the miss list)
  -> INVALIDATED. Control: three misses of three different kinds -> DEGRADED, not INVALIDATED.
- V-EVC-CONF-INVALIDATED-OOM: one miss with actual >= 10 x need -> INVALIDATED; the same with `isolated_anomaly=True`
  (a proof string, non-empty) -> DEGRADED. Control: 9.9x -> DEGRADED.
- V-EVC-CONF-TAXONOMY: `TAXONOMY` is exactly the 13 names CALL_COUNT, CONTEXT_GROWTH, WORK_CLASS_MISCLASSIFICATION,
  PROOF_TAIL, CLOSEOUT_TAIL, REPAIR, CONTROL_PLANE_LEAK, SEMANTIC_SCOPE, STALE_USAGE_TRUTH, RESOURCE_ANOMALY,
  PROVIDER_BEHAVIOR_CHANGE, PROFILE_TRANSFER, UNKNOWN; `classify_miss(need, actual, evidence)` returns one of them;
  evidence `{"calls_ratio": 2.0, "ctx_ratio": 1.0}` -> CALL_COUNT, `{"ctx_ratio": 2.0}` -> CONTEXT_GROWTH, `{}` -> UNKNOWN
  (never guessed). `FIOS_MAP` maps every taxonomy name to a FIOS bucket string; check no name is missing.
- V-EVC-CONF-ADMIT: `may_admit_large(state)` False for UNKNOWN/INVALIDATED, True for CALIBRATED/PROVISIONAL; DEGRADED
  True only with `tranche=True`. Control: INVALIDATED with tranche stays False.
Implementation: constants `STATES`, `TAXONOMY`, `FIOS_MAP`, `LARGE_TOKENS = 1_000_000`; functions `state(n, misses,
isolated_anomaly="")`, `classify_miss(need, actual, evidence)`, `may_admit_large(state, tranche=False)`. Misses are the
`{"need","actual"[, "kind"]}` dicts `record_actual` stores; import `route_admission as ra` for `MISS_FACTOR`/`is_degraded`.
Pure, no IO, no clock.
Verify: `python tools\test_evc_confidence.py` (all PASS); `python tools\test_route_admission.py`; `python tools\test_cost_to_completion.py`.

### Task 2: CTC as primary estimator, with confidence and the retained profile misses
Files: `tools/cost_to_completion.py`; `tools/route_admission.py` (record_actual accepts optional `kind`); `tools/test_evc_confidence.py`
(append gates); `tools/test_cost_to_completion.py` and `tools/test_route_admission.py` must stay green unchanged.
Gates first (append to test_evc_confidence.py, run RED before the code):
- V-EVC-CTC-CONFIDENCE: `compile_cost` output carries `confidence` = `{class: state}` for every MODEL_CLASSES entry. RED today:
  the key is absent. Input: the claim set used by test_cost_to_completion (`claims`, `FLOORS`) with no profiles -> every
  class `UNKNOWN`; with `profiles={"novel": {"calls":5,"ctx_tokens":120000,"n":6}}` -> novel `CALIBRATED`. Positive control:
  the existing V-CTC-CANDIDATE-EXACT numbers are unchanged.
- V-EVC-CTC-INVALIDATED-CANNOT-ADMIT: a profile with `misses` = three 3x `CALL_COUNT` entries -> output
  `admit_large: false` and `fallback: "conservative"` (ceiling used as candidate); a CALIBRATED profile -> `admit_large: true`.
- V-EVC-MISS-KIND: `ra.record_actual("top-level-worker", 100, 300, path=tmp, kind="PROOF_TAIL")` stores `kind` in the miss;
  a call without `kind` stores none (existing JSON shape unchanged; test_route_admission stays green). Use a tmp copy of
  route-floors.json, never the live file.
Implementation: in `compile_cost` (line 64-126) read `o.get("n")` and `o.get("misses")` from the `profiles` layer
(inside the `for layer, name` loop, ~line 83), call `evc_confidence.state`, add `confidence`, `admit_large`, `fallback` keys
to the returned dict (additive only; keep every existing key). When any used class is INVALIDATED/UNKNOWN and the candidate
exceeds `LARGE_TOKENS`, set `fallback` to `"conservative"` and `admit_large` False. `record_actual`: add keyword `kind=None`;
append `{"need","actual"}` plus `"kind"` only when given. `main` (129): print `confidence` in the JSON; exit codes unchanged.
Verify: `python tools\test_evc_confidence.py`; `python tools\test_cost_to_completion.py`; `python tools\test_route_admission.py`.

### Task 3: Demote the auto envelope to a labelled emergency fallback
Files: `tools/gsd_mission.py` (`_auto_budget` 1364, call site ~3055); `tools/test_gsd_mission_envelope.py` (append);
`vault/config/mission-budget-defaults.json` untouched.
Gates first (append to test_gsd_mission_envelope.py, RED before the code):
- V-EVC-ENV-LABEL: `_auto_budget` on a live record with no estimate writes `token_estimate_src == "auto-fallback"` and a
  `token_estimate_basis` starting `EMERGENCY FALLBACK`. RED today: src is `"auto"`. Control: an operator-set estimate
  (`token_estimate_src` other than auto) is never rewritten by `_auto_budget`.
- V-EVC-ENV-CTC-FIRST: when the record carries `claims` (a claim graph) and `compile_cost` returns COMPILED with
  `admit_large` true, `_auto_budget` sets `token_estimate = ceil(candidate.with_margin / ratio)` with src `"ctc"` and
  basis naming CTC; without claims it falls back to the labelled auto path. RED today: no claims path exists.
  Control: `Refused` from `compile_cost` (e.g. phase keys) falls through to the fallback, never raises.
- V-EVC-ENV-GREP: no other writer sets `token_estimate_src` to `"auto"`: `Grep "token_estimate_src.*\"auto\""` in `tools/`
  excluding tests returns 0 hits after the change; find any reader (`Grep "token_estimate_src"`) and make each accept
  `"auto-fallback"` wherever it compared `== "auto"` (fix those lines; list them in the commit body).
Implementation: in `_auto_budget` before `auto_headroom` try `import cost_to_completion as ctc; ctc.compile_cost(
rec["claims"], route_admission.load_floors())` only if `rec.get("claims")` is a dict doc; on success emit event
`envelope_auto_assigned` with src `"ctc"`; else keep the existing computation but change src to `"auto-fallback"` and
prefix the basis `EMERGENCY FALLBACK ([1M,15M]/2 clamp, no claim graph): `. Keep the failure path (ledger row
`envelope_auto_unassigned`) as is. Do not change `auto_headroom` or `_BUILTIN_BUDGET`.
Verify: `python tools\test_gsd_mission_envelope.py` (55 prior checks + new, all PASS); `python tools\test_evc_confidence.py`;
`python tools\test_cost_to_completion.py`; `python tools\test_route_admission.py`; `python tools\test_evc_usage_truth.py`;
`python tools\test_evc_gsdx_reforecast.py` if present (else skip, say so).
