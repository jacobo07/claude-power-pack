# S18 PLAN: "Model Compounding": iterate the IMPROVED, then the model on NO_COMPILE

Status: APPROVED in principle (Owner "go ahead", 2026-11-07, session 280f506f, after the coordinator's diagnosis
"qué te impide tener ya todas las funciones resueltas"). Runs as a retarget of the S17 mission m-6d8ccba44d39 at its
W2 checkpoint, INSIDE the standing S17 authority (40M processed, 0 top-ups; model pool on the subscription, no USD
cap). If S17's remaining authority is too small for W5+W6, the top-up is a separate Owner question.

## Facts it is built on (measured 2026-11-07, GEX44)
- S17 W2 yield. These are the first model certifications since S11, all via certify-solved:
  - REG_ONLY: pilot 3/20, scaled 14/83, so 17/103;
  - INSERT_DELETE: pilot 4/20, scale (66) running at 16:14Z;
  - frontier 1156 -> 1173 (+4 pending recount).
- The INSERT_DELETE pilot left 16 IMPROVED, many close to exact (98.03, 92.42). A single llm_fix pass ends at
  IMPROVED; nothing has fed the residual diff back for a second pass.
- About 345 NO_COMPILE stop on mwcc type errors. W1 deterministic shared fixes certified 0 of them, and the model has
  never been run on them.

## Waves
- **W5. IMPROVED compounding.** Every IMPROVED from W2 (REG_ONLY + INSERT_DELETE), sorted by match % descending.
  Each pass runs llm_fix with the previous best source plus its objdiff residual as context (extend llm_fix; no
  second pool). Freeze the cohort by commit first. Stop the wave when a pass certifies < 1 per 10M tokens.
- **W6. Model on NO_COMPILE.** A 20-function pilot from the largest mwcc error class (IMPLICIT_CONVERSION 65,
  ILLEGAL_OPERANDS 61, NOT_STRUCT 53, UNDEFINED_IDENT 48). The prompt carries the recovered type context the owners
  already hold: shared_types, m2c_proto, om_skeleton offsets, d12_struct. K3 applies: 0/20 retires the class; >= 2/20
  scales it. At most 4 classes.
- **W7. Fold and closeout.** Fold winning prompt shapes into the hotpath and re-sweep at no model cost. Then the
  frontier recount and the yield per 1M tokens per wave, promotions.json, checkpoint.

## Invariants
cert_cxx unchanged; SDA NO; H2 sealed and excluded; no push; the worker never edits the PP. Paid API USD 0.
Waits: pid or sentinel only. The self-match pgrep guard is live on GEX44 since 2026-11-07 16:13Z.
