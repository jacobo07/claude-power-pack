---
id: PLAN-TOK18-TRANCHE-CONTEXT-RUNTIME
date: 2026-10-06
status: APPROVED 2026-10-06 (Owner "y" to inline PLAN, pane c77978f6); this file is the compiled work card
covers: [floor-gate-wiring, floor-gate-cwd-comparability, wake-mode, context-compiler-sufficiency, naive-trim-arm, tranche-distill]
parents: [vault/programs/cognitive-economy/gen2/MISSION.md, vault/plans/post-e1-meta-work-2026-10-06.md, vault/plans/tok18-pre-rearm-optimization-RESUMPTION.md]
mode: PLAN (architecture settled; owners verified). EXECUTION per unit; PLAN only inside WU3.
---

# TOK-18 tranche: floor gate wired, wake mode, Context Compiler sufficiency

Workers read THIS card and the unit they own. Not the source prompt, not the approving transcript.

## Envelope (WU0, Owner-authorized 2026-10-06)
Hard cap 6M processed tokens for the whole tranche (central ~4M). This re-authorizes post-E1 Phase 2 and 3
(HR-COST-002 cleared for them only). Meter every pane with `stage0/self_spend.py` under its own sid; append the
reading to the Spend table below before closing a pane. Crossing 6M = stop and one Owner question.
One fresh pane per unit (/kclear -> /kresume). Never carry a long Opus pane across units: the three prior
overruns (Gen2.1 15M cap, GGMC 23.07M vs 15M, Phase 1 8.16M vs 1.2M) share one cause, ~170k context x calls.

## Verified at approval (read-only scan, HEAD 5d5b2477)
- Owner = gen2 TOK-18 ledger. Gen1 rejections stand (F 1.88, K 2.67, P 0.50, C-tools 0.002, D <=0.19, E 2.78 %).
- Held, NOT in this tranche: W4/W5 (not before 2026-10-11T18:00Z), W6 (Owner HELD), Gen3 T3 worktree, Pillar K
  floor/pointer content. Context Compiler is ABSENT (skill-capability ledger row L defers it here).
- Finding: `tools/floor_regression_gate.py` has no live caller (owner-bundle names it as debt), and
  `floor/reference.json` is not comparable from organic sessions: `--check --project-dir <pp project>` and
  `--check --session c77978f6-...` both exit 2 `not_comparable: fields differ: cwd`. The startup-floor trend is
  therefore UNMEASURED; no number is quoted.

## Units
WU1 floor gate wired (EXECUTION, ~0.6M). First read Pillar K ledger/plan (`vault/plans/pillar-k-resident-prefix-2026-10-05.md`);
if K claims gate wiring, write a handoff instead of editing. Else: (a) organic sessions comparable (per-cwd reference
or an explicit cwd-admission the gate reports; decide after reading `not_comparable`); (b) `--check` attached to an
EXISTING zero-model scheduled task (candidates: PP-LivenessCheck, PP-Vault-Summarize; not PP-SelfEval), exit 2 logged
UNKNOWN, never green; (c) first measured floor number with its command. Proof: fixture red/green, mutation drill on a
copy (inflated rule file -> exit 1), one row written by the real task's own run.
WU2 wake mode (EXECUTION, ~0.4M) = post-E1 Phase 2 as written there. Wait test: dormant runs 0 model calls; fixture flip wakes.
WU3 Context Compiler sufficiency (PLAN locally, ~2.5M) = post-E1 Phase 3 as written there, PLUS a naive-trim arm
(same byte budget, truncation, no dependency awareness) pre-registered in the frozen spec BEFORE any run.
Verdict WIN/LOSE/UNDECIDED by the frozen thresholds; the naive arm reports recall and silent misses side by side.
WU4 distill (EXECUTION, ~0.5M): UKDL/KV/CBR after a duplicate check. Candidates: (1) the authoring pane's
context x calls is the budget, not the work; (2) a regression gate whose reference compares only from a probe cwd
is silent on real sessions. Update gen2 ledger units touched.

## Tranche done-gate (all exit 0 / PASS; UNKNOWN never passes)
1. `python tools/cep_gen2.py --status`: no violations; closed units carry receipts.
2. `python tools/test_floor_regression_gate.py` + one real organic `--check` returning 0 or 1 (never 2) + a row from the scheduled task's own run.
3. Wake test (WU2) green with both poles.
4. WU3 verdict file with real parity-guard positive-control output and the naive-trim arm.
5. Tranche spend (Spend table) <= 6M.
Program gate `python tools/test_cognitive_economy_program.py --generation 2 --final` cannot pass this tranche
(W4-W6, W9, R held); it is not claimed.

## Rules
Pathspec commits only, re-read HEAD first, never push. Never edit T3 worktree or another pane's mission.
Two equivalent failures = change the method.

## Spend
| pane | unit | processed | calls |
|---|---|---|---|
| c77978f6 | scan + plan | 3,346,671 (ctx 3,331,606, out 15,065; 0 subagents) | 20 |

Projection at write time: sunk 3.35M + units central 4.0M = 7.35M > 6M cap. Per HR-COST-002 no unit starts until
the Owner picks: (a) the 6M cap applies to WU1-WU4 only (scan sunk), or (b) the 6M cap holds tranche-wide and the
units shrink to <= 2.65M (WU3 cut to 1.2M: miner + naive-trim arm on 4 planner runs, verdict UNDECIDED-allowed).
Cause is the same as the prior three overruns: ~167k context per call in the approving pane.
