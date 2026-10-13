
- W11 step 1: fn_801BD194 compile_error = mwcceppc 10122 "identifier 's32' redeclared"/10127/10135 at line 1: the unit source has no typedef prelude. NOT a tool defect: all 26 units compile_failed in job 2; the 4 BLOCKED_CONTEXT are the same missing prelude. Fix = prepend M2C_TYPES (arm_a.py:127) + Tennis context in arm_a.compose. fn_801BD194 asm: tail-call fn_801BD1A0(arg0, 8, 0) (old candidate had 2 args).
rdict onto every unit with miss_class "environment".
  Hidden behind it: all 50 compiles aborted (raw m2c with unresolved `?` types, CXX built with `-lang c`), and the job
  contained no model step, so it could not have measured tokens per function.
- Economic impact: 1 of 4 Phase-7 jobs + the C2b worker session; the Tennis forecast was built on a number that
  never existed.
- Fix / prevention: W1 (CURRENT registration or pinned judge, zero-compile source lint, full stderr, reason classes),
  W2 (Fan-Out Readiness Certificate). Proof: W1/W2 receipts.

## K2 -- planned unit targets below measured physics (2026-10-11, arming)
- Symptom: the first chain tick's arm-chain for W1 refused `route RECOMPILE: floor 4,223,670 x 1.2 = 5,068,404 >
  target 2,500,000`.
- Root cause: the plan priced units at ~C1's per-call figure; route_admission's growth estimator (declared calls x
  2.4 physical, rising context) prices 25 declared calls at 4.22M. The admission was right; the plan was optimistic.
- Fix: routes resized from the estimator (S 1.6M/12, M 3.5M/20, L 6.4M/28; PP 5983db9d). Unit sum 36.1M: the
  programme's honest P50 is ~38M with W0, not 28M. Still inside the 55M hard stop.
- Prevention: size routes with `route_admission.py admit` BEFORE writing a plan's budget table.

## K3 -- a refused arm-chain deadlocks the chain when the goal has no GSD workstream (2026-10-11, arming)
- Symptom: after a RECOMPILE refusal the held PREPARED record makes gsdx_chain read the unit as `arm_refused`
  forever; it also counts as a live writer in the root (`wait_writer`), and if closed it reads as
  `stopped_without_done`.
- Root cause: `gsd_mission.arm --supersedes` requires a goal key (`goal_key(cwd, workstream)`); a mission armed without
  a GSD workstream has key None, so no supported path retires the refused record.
- Repair used: transition the never-launched record to HALTED keeping its owner_hold, then arm_chain again in the same
  script (scratch `rearm_w1.py`; old m-ea05f64a68b3, new m-3b3632860a22 RUNNING, worker 29a0ae3e read WU-W1).
- Prevention candidate (not this programme's scope): gsdx_chain re-arms a unit whose only record is a never-launched
  `arm-chain failed` hold once its route admits, retiring the old record itself.

## W5a: cohort 1 job step has no oracle (2026-10-11)
- Symptom: packet step 3 (one certified GEX44 job judging 12 candidates) cannot run.
- Trigger: W3b NAMED REFUSAL; capsule_build/candidate/match are Resort-hardwired, CURRENT_CAPSULE is one shared pointer.
- Root cause: oracle was built for one game; no --profile threading.
- Economic impact: every Tennis verdict is UNJUDGED; per-function token cost per VERIFIED function is UNKNOWN, not zero.
- Fix: tennis capsule unit (--profile) ~600 lines, or cost A/B oracle-less. Prevention: a packet needing an oracle should list the oracle as a prerequisite unit.
- Proof: evidence/w5a/measure/records.jsonl (12 rows, verdict UNJUDGED_NO_ORACLE).

## W7: m2c_producer asm_root appends "asm"
Symptom: FileNotFoundError .../out/asm/asm. Trigger: passing split out/asm as asm_root. Root cause: producer joins "asm" itself. Impact: one wasted launch (background start hid the error until read). Fix: pass .../out. Prevention: run first producer launches in the foreground. Proof: M2C_DONE rows=1797.

## W7: W3 receipt donor count
Symptom: "179 of 408 exact have proven donor". Root cause: 179 = 167 exact + 12 loose-only. Fix: W7 counts 167. Proof: tennis_fns.json grouped by match.

## W10b: CURRENT_CAPSULE is a local pointer; one shared F root made Tennis and Resort collide
- Symptom: Tennis send could only satisfy the W1 guard by moving the pointer Resort/cp50-c2 jobs use.
- Root cause: custody keyed the guard on one F root; the GEX44 runner never reads it (checks params sha vs payload MANIFEST).
- Impact: avoided a time-slice lock and a shared cap; Tennis jobs would otherwise burn cp50-c2's RF cap.
- Fix/prevention: own F root registered as a live root with cap 4; profile may set CURRENT only in its own root. Proof: test_tennis_judge.py e1-e4, d1-d3, m2, m3.
- Also: match.py/candidate judged Tennis against the Resort DOL (K.DOL); a Resort DOL silently gives DIFF, not an error. Proof: m1.

- W10c: judge expects tennis_L0.jsonl at the profile path, but write_inputs only writes it into a temp dir (copy from capsule data\L0_units.jsonl); repatriate.py is a separate step from stage wait; stage.py build refuses the WHOLE batch on one SOURCE_LINT hit, so pre-filter with source_lint.lint_unit (7/12 W5a fns have UNK_FIELD); send can return QUEUED_NOT_RUNNING after 180s - the job still runs, use stage wait.

## D6: entry_evidence stops at the prologue call, so every _savegpr callee reads "no args"
- Symptom: D5 admitted `void fn_801D022C(void)` (callee "reads no args") and reported SUPPORT unlock 3.
- Root cause: `factor.entry_evidence` breaks at the first CALL; `bl _savegpr_25` in the prologue precedes `mr r25,r3 ... mr r29,r7`, so min_gpr=0 for any callee with a save-gpr prologue (also misses varargs spill).
- Impact: D5 asm_admits was blind for those callees; its one SUPPORT is an unlock that exists only under an asm-false prototype. Same blindness may apply to D4 HELPER arity claims.
- Fix/prevention: skip `_savegpr_*`/`_savefpr_*` calls in entry_evidence (not done: tool lives in GEX44 d1d, D6 only measured); a SUPPORT must be re-run under an independently asm-checked prototype. Proof: evidence/d28/d6/variants.json (1 vs 4 variants).
