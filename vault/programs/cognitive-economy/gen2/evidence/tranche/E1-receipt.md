# E1 receipt -- tranche gate truth (tools/cep_gen2.py::tranche)

Verdict: **PASS**

## What changed
- `tools/cep_gen2.py:307` -- `NOT_APPLICABLE` added to `TRANCHE_STATES`; `GREEN_STATES = ("PASS", "NOT_APPLICABLE")` at `:309`.
- `tools/cep_gen2.py:330` -- `owned_units`/`owned_units_reason` read from the manifest and every results file; `owned_declared` is true only when some source carries `owned_units` as a list.
- `tools/cep_gen2.py:369` -- violations = NOT_APPLICABLE only for explicit `[]` + non-empty reason; `[]` without reason and a missing key stay UNDECIDED (distinct evidence strings).
- `tools/cep_gen2.py:345` -- coordinator `final` (int, not bool) => spend = final - baseline, transcript not read; otherwise live metering with `coordinator=LIVE (not reproducible)` on the spend line (`:384`).
- `tools/cep_gen2.py:394` -- overall PASS = every clause in GREEN_STATES.
- `tools/test_cep_gen2_tranche.py:78` -- 9 new gates (explicit-empty NA, empty-no-reason, missing-key-with-reason, missing-key, manifest-declared NA, extra-clause NA green / NA without evidence, live grows and says so, frozen reproducible + transcript not read).

## Commands (exit codes)
- `python tools/test_cep_gen2_tranche.py` -> rc=0 `CEP2_TRANCHE_TEST_PASS=23/23  threshold=23/23`
- `python tools/cep_gen2.py --selftest` -> rc=0 `CEP2_SELFTEST=PASS`
- mutation (a) treat missing key as NOT_APPLICABLE -> test rc=1 red gates: V-CEP2-TRANCHE-MISSING-KEY-WITH-REASON-UNDECIDED, V-CEP2-TRANCHE-MISSING-KEY-UNDECIDED
- mutation (b) ignore `final` -> test rc=1 red gates: V-CEP2-TRANCHE-FROZEN-COORD-REPRODUCIBLE
- restored source byte-identical=True; re-run rc=0 `CEP2_TRANCHE_TEST_PASS=23/23  threshold=23/23`

## Physical tool calls
4 (1 read dump; 1 PowerShell call refused by the sandbox before running -- `del r[...]` in a here-string read as Remove-Item; 1 Write of the patch script; 1 run that patched, tested, mutated, committed and wrote this receipt).

## Semantic boundaries (named decisions)
1. NOT_APPLICABLE for `violations` requires BOTH an explicit list `owned_units: []` (manifest or any results file) AND a non-empty `owned_units_reason`; a reason without the key is still UNDECIDED.
2. Owned units now also union in from the manifest (previously ignored there).
3. An extra clause given as NOT_APPLICABLE needs an existing evidence file, the same bar as PASS -- otherwise it would be an unevidenced green.
4. `final` must be an int and not a bool; a frozen reading with a bad baseline is unknown spend (red), never 0.
5. Coordinator from the results file (no manifest coordinator) is labelled `coordinator=RESULTS`.
6. Not done here: project_integrity_map re-index (out of epoch scope).

COMMITS: a84fc15c
