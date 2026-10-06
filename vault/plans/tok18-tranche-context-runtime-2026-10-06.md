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

**Owner decision 2026-10-06: (b).** 6M is tranche-wide. Remaining is 2.65M minus this decision's calls
(~0.9M; the first WU1 step re-measures pane c77978f6 with self_spend). Per-unit caps, binding: WU1 0.6M,
WU2 0.4M, WU3 1.2M (miner + naive-trim arm + dependency-aware packet on 4 historical planner runs; UNDECIDED
admissible; no paid canary), WU4 0.3M. If the re-measured remainder is below their sum, WU4 is cut first, then WU3.
A unit that crosses its cap stops and writes a partial receipt; it never borrows from the next.

- pane c77978f6 final (planning): 5,856,325 processed / 33 calls / 0 subagents (stage0/self_spend.py under that sid). The 6M tranche was exhausted by planning (~98%). Cause: one pane re-sending ~170-190k context per call; 4th overrun with this cause. The "~0.9M for decision calls" estimate was wrong: actual 2.51M / 13 calls.
- Owner 2026-10-06: new execution envelope 1.2M (WU1 0.6 / WU2 0.4 / WU4 0.2), WU3 deferred until WU1 measures fresh-worker per-call cost; workers run as fresh subagents/panes with compiled packets, never in the planning pane.

| 7f13d6e2 | post-E1 Phase 1 (49 calls) + re-plan scan (this turn) | files 1 calls 53 processed 9,638,790 (ctx 9,574,887 out 63,903) subagent calls 0 subagent ctx 0 | |
- Tranche close (WU4): WU1 PARTIAL (--admit-cwd code, red test fixed b67f5d8f, wiring not done); WU2 DONE for code/fixture, production UNVERIFIED; WU4 DONE (LEARNINGS.md, ukdl-candidates.md); WU3 deferred.
- Spend: planning pane 5,856,325 / 33 calls (~98% of 6M); WU1 ~1.5M vs 0.6M cap; every fresh worker starts at ~96k, so allowance = budget / prefix.
- Owner items: re-baseline floor reference or explain +37,683 chars (memory_project +34,478 is cross-project); decide a consumer for WAKE_FLAG.json.
- Owner items: confirm PP-Vault-Summarize 02:00 run on 2026-10-07 (Get-ScheduledTask PP-Vault-Summarize | Get-ScheduledTaskInfo); UKDL candidates await promotion.

## PROPOSED addendum (pane 7f13d6e2, 2026-10-06; NOT approved; zero-model scan, transcript-measured)
- Phase 1 anatomy, 49 calls, ~8.6M (handoff's 8.16M/47 was read before the last 2 calls): resume 3 calls 0.37M;
  scan/archaeology 24 calls 3.72M (of which 8 greps hunting one number, 1.20M: the 12.5k was reconstructable arithmetic);
  authoring 10 calls 1.88M (B1 as 5 Edits on one file 0.92M); edit churn/anti-thrash/dry-run fix 7 calls 1.48M;
  driver run+verify+meter 3 calls 0.65M; closeout 2 calls 0.44M. Intelligence-requiring ~6-10 calls. Floor 120.8k at
  call 1, growth ~2.1k/call -> cost(n) ~= n x 121k + 1.05k x n^2. No duplicated text block in the raw transcript.
- Pre-call admission EXISTS: hooks/session_budget_guard.js (PreToolUse deny on stop/divergence/context/no-progress),
  dispatcher-wired. It is OPT-IN via mission_spend.py session-declare; no pane of this tranche declared, so it was inert.
- Feasibility at the measured floor: WU2 0.4M allows <=3 boundaries; a build+test+prove unit needs ~6 -> infeasible
  as an Opus pane. Remaining tranche after scan 3.35M + decision ~0.9M + this pane's planning turn: ~0.5M or less.
- T3 worktree HEAD a62fec6e does NOT contain a5a5e91b (merge-base rc 1): notice still owed.
- e1_runner.py calls bare git; test_cognitive_economy_program.py already has the canonical shutil.which + absolute fallback.
- Payback on known TCO: 9.17M runs + Phase 0 2.18M + Phase 1 ~8.6M >= 19.95M -> break-even >= 2,354 calls vs 8,784
  observed main calls: still past break-even on GROSS saving; NET saving (skill reloads) UNMEASURED.

**Owner decision 2026-10-06 (pane 7f13d6e2): "y" to the PROPOSED addendum (A+B, 2.0M HARD). Reconciled with the c77978f6 envelope above: Slice B IS WU2 and stays with c77978f6's WU2-packet.md under its own cap, so only Slice A is drawn here (0.8M); B's 0.8M is not drawn unless the Owner says so.**
Caps binding, no borrowing: A 0.8M, B 0.8M, reserve 0.4M (proof/repair, Owner-visible if touched). WU1/WU3/WU4 deferred
until A is live, then re-admitted through A's feasibility gate. One fresh pane per slice; read ONLY this card.
FIRST ACTION of every worker (before any other tool call): `python tools/mission_spend.py session-declare` for its own
session id with stop = its cap and a calls estimate; then self_spend reading at close into the Spend table.
Rules for the worker: one Write per new file (no Edit chains), batch reads, no searches for numbers derivable from
artifacts, the deterministic parts run as ONE script call.

### Slice A -- admission by construction (EXECUTION, ~6 calls, cap 0.8M)
Owners to EXTEND (no new system): hooks/session_budget_guard.js (PreToolUse deny; opt-in today), tools/mission_spend.py
(`session-declare`), tools/rollover.py (`certify`), tools/test_session_budget_guard.py.
A1 certify (kresume) declares the session budget from the unit's cap on its card, so a card-bound pane cannot run undeclared.
A2 declare runs feasibility: floor (this session's first-call context, else median first-call of recent same-cwd sessions
from usage_index) x minimum calls + growth + proof reserve > cap -> refuse with the numbers; unknown floor -> refuse, never allow.
A3 folded debt: e1_runner.py git via the shutil.which + absolute fallback already in test_cognitive_economy_program.py;
T3 notice (a5a5e91b holds a710f2a4's c0 paths; T3 HEAD a62fec6e lacks it) via a handoff file, never editing the T3 worktree;
receipt cost scope -> known TCO >= 19.95M, break-even >= 2,354, net UNMEASURED; <=4 UKDL entries after a duplicate check
(budget feasibility before start; admission must be default-on; measure from the artifact, not the commit message;
the authoring pane's context x calls is the budget).
A4 proof: red/green on a mutated copy for A1 and A2; one REAL fresh pane whose guard denies at the projected point.
A5 `tools/test_tok18_tranche.py` = the ONE master gate: guard + rollover tests, feasibility both poles, WU2 wake test,
cep_gen2 --status clean on touched units, Spend table <= authorized cap; missing evidence = FAIL, UNKNOWN never passes.

### Slice B -- WU2 wake mode (EXECUTION, ~6 calls, cap 0.8M) = WU2 above, admitted by A, plus predicted-vs-actual spend row.

Orchestrator close (measured, self_spend sid c77978f6 incl. subagents, 2026-10-06): session 12,819,555 processed / 74 calls; subagents 2,927,114 / 24 calls (WU1+WU2+WU4, authorized 1.6M); orchestrator pane after planning ~4.03M / 17 calls, UNBUDGETED (its own estimate was ~1.1M). Execution total ~6.96M vs 1.6M authorized. 5th overrun, same cause: the orchestrating pane re-sends ~190-230k per call; verification/dispatch calls belong in a fresh low-floor worker too. Tranche gate: floor 61/61 PASS, wake 5/5 PASS, organic floor check exit 1 measured; cep_gen2 --status rc=1 (W4-W9,R open, not claimed); WU3 deferred; nightly 02:00 run UNVERIFIED; spend clause FAILED.
