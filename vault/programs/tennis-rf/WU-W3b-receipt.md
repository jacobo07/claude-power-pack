# W3b receipt
Status: DONE

Outcome: NAMED REFUSAL (packet step 5). Zero GEX44 jobs, zero local compiles, JOBS.md untouched, no code changed in wt_tennis_rf.
- PROVEN (read of source): the Tennis capsule is not a parametrisation, it is a second capsule builder. Blockers:
  1. `capsule_build.resolve_units` (l.251-320) derives units from the Resort ledger (probe_v2 MATCH == SEALED 5, 289 MATCH donors == EXPECTED_DONORS, MODEL 4, EXPECTED_UNITS 298) and refuses SEALED_SET_MISMATCH/DONOR_COUNT/MODEL_SET_MISMATCH/UNIT_COUNT; `resolve_targets` needs census+EXPECTED_TARGETS 2685. A Tennis unit set (3 donors, targets `tns:<addr>`) hits all of these.
  2. Paths Resort-hardwired in 6 modules: capsule_build.py:40-42, candidate.py:46-49, pack_inputs.py:22, reproduce.py:35, propagate.py:125 / sda_stub.py:91,113 (default arg candidate.ASM_DIR).
  3. Judge: `match.py:189` reads module-global `K.DOL` (Resort retail DOL); needs Tennis DOL `step0/disc/files/EU/sys/sports/SportsPackEP.dol` + Tennis DTK operands, via candidate.judge/l0_row (L0_PATH = main_L0.jsonl, Resort L0 corpus; no Tennis L0 exists).
  4. `F\CURRENT_CAPSULE.json` is a single shared pointer (custody.current_capsule, stage.py:416/440/1112/1155); send refuses unless it equals the sent capsule. Pointing it at Tennis would disturb Resort and cp50-c2 jobs; a per-programme F root (MATCH_ACCEL_GEX44) is the safe route but the GEX44-side runner/custody would need the same root.
  5. Pre-spend judge control (positive/negative on a Tennis object pair) cannot run without 3.
- Compiler caveat unchanged: 1-2 insn donors cannot detect a compiler mismatch (TENNIS-TOOLCHAIN.md).
- NOT_PROVEN: oracle reproduces a Tennis object byte-exact.
- Next unit (W5) must route around: do not assume a Tennis oracle. Either (a) schedule an explicit "tennis capsule" build unit: `--profile tennis` threading one profile dict (split/asm/obj/dol/L0/ids/counts/F-root) through the 6 modules, Resort default + drills green, then control then 1 job; or (b) cost Tennis A/B with oracle-less layers (shape/donor/m2c) and mark compile-verified rates UNKNOWN. Estimate for (a): >1 unit, ~600+ lines touched across capsule_build/candidate/reproduce/pack_inputs/stage/custody plus tests.
- Calls used: ~10.
