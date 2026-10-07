# CE-T1a receipt (written by the COORDINATOR, bc576038, from observed evidence)

The worker (80283aee, 989,449 processed of 1.4M cap) committed d465eaef but ended before writing this receipt
(same shape as CE-T0b). Driver verdict stays FAIL (receipt absent at check time); this file records the
independent re-verification, it does not rewrite that verdict.

## What changed (d465eaef: 4 files, +130/-5)
- `tools/cep_gen2.py`: spend clause judges `spent_measured` as int or `{value, unknown}`; value vs boundary;
  unknown / non-int -> fail (UNKNOWN never passes).
- `tools/rollover.py`: Forget-Safety check before `certify_flow` retires a capsule (exit 9 when the capsule alone
  cannot carry the continuation).
- `tools/test_cep_gen2_obligations.py`, `tools/test_rollover.py`: both-pole cases.

## Re-verification (coordinator, 2026-10-07, HEAD f33c1663)
- `python tools/test_cep_gen2_obligations.py` rc=0 (mutants killed, V-OBL-LIVE-LEDGER-assessed)
- `python tools/test_rollover.py` rc=0 ROLLOVER_PASS=64/64
- `python tools/test_rollover_capsule_v2.py` rc=0 CAP2_PASS=36/36
- Downstream consumers T1b (PASS) and T1c (PASS) built on these functions.
- Not re-checked here: the worker's mutant for the dict-unknown branch (named in the packet) -- UNVERIFIED.

COMMITS: d465eaef
