# 02-02 SUMMARY -- legacy replay instrument, RED-first

PLAN_BASE = 142eafea (last 02-01 commit; `git diff --name-only 142eafea..HEAD -- modules` prints nothing)

## Done
- 13a0ee2c: byte-copied fixture of g-002 (50 events) and g-001 (123), MANIFEST.json each, `-text` pinned, secret scan clean, re-capture refused.
- 98609c4f: golden captured from the UNMODIFIED engine (`proof.py` absent), 6 scenarios (g002, g001, 4 synthetic), 22 legacy event types all covered by the corpus. `02-capture-golden.log` (EXIT=0, re-capture REFUSED), `02-replay-green-legacy.log` (`GSDX_PCC_REPLAY_PASS=13/13`).
- 15e8e2f1: seam gates added, RED: `02-replay-red.log` shows `GSDX_PCC_REPLAY_PASS=21/23`, EXIT=1; the only two FAILs are `V-PCC-REPLAY-IGNORE-NEW-TYPES-PCC` and `V-PCC-REPLAY-INTERLEAVED`, both `RED-first: modules.gsd_x.goal.proof absent`. M1-M4 PASS, CLEAN-AFTER-MUTANTS PASS, LIVE-STORE-UNTOUCHED SAME.
- Both proof-dependent gates dry-run against a throwaway stub proof module (not committed): both returned True, so their comparison logic is exercised before 02-03.

## Deviations (audit CODE rows applied, 02-AUDIT.md)
- G1: INTERLEAVED mask adds `decide.reason` (`at seq \d+` -> `at seq <seq>`) only when `operator.last_seq` is masked.
- G2: every gate body runs under `run_gate`; new gate `V-PCC-GATE-RAISE-SURVIVES` proves a raise prints `FAIL <gate> raised <Exc>: <msg>` and leaves the counters/summary intact.
- G3: synthetic repo id is hex; `syn_carry` = declare, accept two, satisfy one, revise, carry.
- G5: `syn_contract` budget is `{"max_epochs": 5}` only.
- Golden `volatile_paths` is empty for every scenario (two independent builds agreed byte-for-byte on all projections).
- PCC sample payloads (`pcc_sample_payloads`) follow spec S6/S7 field lists; 02-03 amends them if its real validators reject a field shape.

## Open
- DENOMINATOR D43/D44 stay OPEN: the instrument exists, the seam it judges lands in 02-03; evidence column records the instrument.
