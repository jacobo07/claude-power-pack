# S22 PLAN: "Land the cheap lever": canonical R2 ctx widening, then a deterministic tail search

Status: PROPOSED, not armed. The Owner said "carry on with Tennis" (2026-11-09, laptop session 38d1a1b5). This
proposal awaits an explicit approval of its envelope; an owner turn authorises one act, and capital is never inferred.

## Facts it is built on (measured 2026-11-09 ~10:10Z, GEX44, t1 fba42ff2)
- S21 m-6302235f0a6c is at CHECKPOINT_COMPLETE. The coordinator re-ran gates W0-W5: all PASS, and W3 kills its
  instrument-fail mutant.
- Frontier 1198/1797 at launch and at close: **0 certificates**. Fresh 1.92M of 6M; gross 32.4M; USD 0 paid.
- R1 (diff-shape llm_fix on residue) scored 0/20 exact and is **retired**.
- R2 (class-level owner fix, Glob/Flags/Slot/Arg80253348 widening) moved **32 clustered fns: 0 -> 6 COMPILES**,
  with 0 exact, 0 regressions, controls 12/0/5 and **0 model tokens**.
  - Near misses: fn_8024E024 at 99.41% and fn_8025B344 at 89.05%.
  - The patch lives only in an isolated ctx copy, replayable from `w2/patch.json` (patched ctx sha 9907081b).
- Yield trend since S17 (+40): S18 +1, S19 +1, S20 0, S21 0. The model levers on the residue are spent; the
  deterministic compile-unblocking lever is the only one still moving state, and it costs nothing.

## Waves
- **W0. Reconcile and freeze.** Check that the frontier recount is 1198, that the original ctx hash is a976108…,
  and that controls are 12/0/5. Freeze the cohort by commit: the 6 newly compiling fns plus the 26 still-blocked
  clustered fns.
- **W1. Land R2 canonically.** Apply `w2/patch.json` through the canonical ctx path (not the isolated copy).
  Re-sweep the full regress set **and every certified fn that includes this ctx**. Gate: 0 regressions anywhere,
  FRONTIER_CHECK OK. One regression rolls the patch back.
- **W2. Deterministic tail search on the 6.** Use the existing operator vocabulary (register-order, declaration
  order, inline/const, field-width permutations) ranked by objdiff residual, with no model call. Certify anything
  exact through certify-solved.
- **W3. Next owner blockers on the 26.** Classify their remaining mwcc errors (float locals, undefined idents) by
  owning header. Apply at most 2 more class-level owner fixes of the R2 kind, each with the W1 regression gate.
  Still 0 model tokens.
- **W4. Optional, behind its own bar.** A model pass on near misses only (>= 95% native), capped at **1M fresh**.
  It runs only if W2 left a fn >= 95% and not exact. K3: 0 certified retires it for the tail.
- **W5. Closeout.** Frontier recount, yield per wave, promotions.json, checkpoint.

## Envelope (requested)
- Worker 8M processed, 0 top-ups. llm_fix <= 1M fresh (W4 only). 4 cycles / 8 h. Paid API USD 0.
- Stop rule: if W1 regresses anything it cannot roll back cleanly, or if W1+W2+W3 move 0 functions to COMPILES or
  exact, close as BUDGET_EXHAUSTED and **recommend closing the Tennis programme** at 1198/1797, unless a new
  mechanism (not a new prompt) is on the table.

## Invariants
cert_cxx unchanged; SDA NO; H2 sealed; no push; the worker never edits the PP; waits on pid or sentinel only. S21
must be closed (COMPLETED) before S22 arms; S21's authority does not transfer.
