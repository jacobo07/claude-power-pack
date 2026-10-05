# INCIDENT 2026-10-05: CW Ops budgeted with InfinityOps phase-role costs

**Where:** pane tua-x-96 (session 8d714d99), TUA-X, answering "lay out all the costs in tokens" before rearming Clock A
mission m-3a1a8b1f7fed.

**What happened:** the forecast for Clock A Phases 2-9 (200-280M) multiplied InfinityOps role costs (planner 14.6M/run,
researcher 8.9M, verifier 7.4M; A0 85adcbcf) by the CW Ops phase count, and Peak Commerce execution (60-150M) by its
historical lane count (10). The result went to the Owner as an A/B/C capital menu. Two more errors in the same answer:
- "155-160k fixed floor per call" was this pane's AVERAGE (8.84M / 56 calls) including conversation growth; the fresh
  first-call floor was 111.8k, and by the 58th call each call cost 223k.
- The TOK-18 Gen2.1 cap (15M, no live runs before 2026-10-11T18:00Z) was applied to CW Ops. It governs the Cognitive
  Economy experiments only; CW Ops missions carry no token envelope (24h / 12 cycles only, `token_estimate` unset).

**Root cause:** cost was derived from execution grammar (phases x roles, lanes x worker cost) instead of from the
obligations still needing new intelligence. The grammar's cost was real (measured cec68800: 3.2M of /gsd-autonomous
overhead to conclude "still blocked"), which made the extrapolation look grounded.

**Impact:** the Owner was asked to fund 270-440M for work the compiled plan bounds at ~37M ceiling / ~22M central
(plan vault/plans/cwops-compiled-execution-2026-10-05.md). No tokens were spent on the old menu.

**Corrected method:** scope freeze -> obligation graph from ROADMAP success criteria -> no-work / reuse pass -> root
decisions (Clock A: FX authority, hero frontier) -> fused Work Units -> semantic interrupts x fresh-worker call cost
-> LOW/CENTRAL/HIGH -> ceilings with call/context/progress breakers. Floor stated as first-call context, growth separately.

**Guard (pending, plan c2/c5):** mission `token_estimate` set to the compiled HIGH so the existing cost breaker parks
overrun; CBR candidate "expensive-mission compilation gate" (arm refuses a large budget without a compiled packet),
promoted only after Phase 1 and WU-A actuals exist. Until then this file and the plan are the record.

**Also observed (launch trap, existing doctrine):** passing the prompt after variadic `--add-dir` left the worker idle
(1731c3a4, 0 tokens) -- exactly gsd_mission.py launch-order note W8. Relaunched with variadics first, `--autocompact`
between, prompt last (b380e956).
