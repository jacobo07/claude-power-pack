---
id: PLAN-POST-E1-META-WORK
date: 2026-10-06
status: APPROVED 2026-10-06 (Owner "y" to inline ULTRA-PLAN v2, scheduled-task wake INCLUDED); this file mirrors it
covers: [e1-closeout, e1-receipt, e1-payback, forecast-calibration, wake-conditions, meta-work-offline-experiment, packet-sufficiency, planner-elision, checker-elision, research-reuse, join-tax]
parents: [vault/plans/tok18-pre-rearm-optimization-RESUMPTION.md, vault/programs/cognitive-economy/e1/REPORT.md, vault/programs/cognitive-economy/gen2/evidence/gen3_t2/README.md]
mode: EXECUTION per phase, one fresh pane per phase (/kclear -> /kresume); PLAN only for local uncertainty
---

# Post-E1: compiled closeout, then the planning/research/checking frontier (offline)

Cost classes are kept apart: AUTHORING (model writes code), EXECUTION (0 model calls), LIVE (gated). The v1 4/6/9M
envelope priced supervision by a long Opus pane as if it were the work; it is superseded.

## Verified at approval (read-only)
HEAD 6124eec on feature/knowledge-acquisition, 126 ahead / 0 behind, 866 dirty paths (other panes). T3 owns worker
lifetime, role profiles, dispatch budget, paired_experiment VoI (worktree Apps\pp-gen3-t3, b89b483c). Pillar K owns
floor, pointers, connectors, startup surface. Never edit either.
E1: 22 runs, 9,172,196 / 17M, ALL_DECIDED, move 17b3188a live on both hosts, saving 8,477 tok/call (laptop, 6124eecf),
pointers 9,232 B. Done: fetch-back, state.B. Open: ledger B savings empty, 12.5k not superseded, no cleanup-survival test.

## Phase 0 (first fresh pane): ownership check before any build
Locate Mission Compiler / GSD X / Context Compiler / ledger writer. If any owns deterministic packet production,
the B3 work becomes CONNECT. Locate an existing registered scheduled task to carry the wake evaluator.

## Phase 1: E1 closeout (authoring 0.7M central, warn 1.0M, recompile 1.2M)
B1 (model-authored): receipt contract + closeout compile path, extending tools/cep_gen2.py (it already enforces saving
labels and not_before); cep_gen2 check fails a closed experiment without a receipt.
Driver run, ONE tool call, 0 model calls between steps, tests before each commit, abort on red:
D1 ledger B saving (measured per call; estate total projected) - D2 12.5k superseded - D3 calibration record
(rule-virtualization: forecast 12.5k, byte est 10.8k, measured 8,477, -32% / -22%, cause pointers keep 22% of bytes)
- D4 pointer-tax receipt - D5 cleanup-survival test (red/green + corrupt-usage control) - D6 payback state (activation
2026-10-05T12:35:40Z, break-even 1,082 calls, laptop transcripts only = lower bound) - D7 E1 receipt - D8 RESUMPTION section.
Semantic: UKDL/KV candidates; CBR candidates only (T3 R-cbr.md: tower not honestly writable).

## Phase 2: waits (authoring 0.4M)
B2: zero-model evaluator added to one existing registered scheduled task; never invokes a model.
W1: every project has >=3 sessions after the move -> run g3_k1_floor.py. W2: not_before 2026-10-11T18:00Z -> re-check
whether the GEX44 probe still changes a decision; if none, close NOT_NEEDED. Until then GEX44 = "same bytes, not probed".
Wait test: dormant runs log zero model calls; a fixture flip proves the wake.

## Phase 3: offline meta-work experiment (authoring 1.5M; execution 0; semantic review 0.5M)
Measured: InfinityOps planner 43.9M/3 runs (11.7%), research 40.6M/5 (10.8%), plan-checker 4.9M/3 (1.3%); KSR 49.7M
combined over 5 planner / 2 researcher / 5 checker runs (split to be mined); KME = control. Join tax unmeasured.
B3: per-family miner, join-tax miner (result size x carrying parent calls x 0.447 tok/char), parity guard, deterministic
packet assembler (extends source_packet.py), structural validators for checker dims 1,2,3,4,6, frozen experiment spec.
Units = 8 historical planner runs (small n, stated). Champion = actual meta spend + join. Candidate = packet from the git
tree at the last commit before the planner's first timestamp; variants P (research kept) and PR (earlier-phase claims only).
Parity guard positive control: that phase's PLAN injected -> refused; planner-coined IDs in candidate -> refused.
Sufficiency: executor-edited files + files read before first edit; pre-existing miss = page fault; planner-only decision
missed without DEOPT = unit FAIL. Excess = packet bytes never consumed. Strata rule-based, no weights, <=20-item review.
Pre-registered: WIN = >=50% units planner-elidable AND recall >=0.95 with DEOPT charged full champion AND >=25% net meta
reduction; LOSE = <25% elidable or recall <0.8; else UNDECIDED.

## Live (separate)
GEX44 probe ~0.1M only via W2. Canary: hand T3 c9-c10 the compiled packet and use its receipt; extra canary only if
still ambiguous, after 2026-10-11T18:00Z under T3's certified envelope, <=1.5M.

## Budget
Pre-live model-bound central 3.1M (2.2-4.4M), warn 3.5M, hard recompile 4.5M. Meter each pane with stage0/self_spend.py.

## Done-gates
E1 gate per Owner prompt; offline gate WIN/LOSE/UNDECIDED; canary admission gate; zero-model driver test, wait test,
parity-guard positive control with real output. Pathspec commits only, re-read HEAD first, never push (decision 7).
