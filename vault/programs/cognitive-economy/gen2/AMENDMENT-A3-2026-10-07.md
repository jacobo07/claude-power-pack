---
id: PLAN-CE-GEN2-AMENDMENT-A3
date: 2026-10-07
status: APPROVED 2026-10-07 Owner 'y' (pane 2aa0b0fb) to the inline master plan, decisions 1-6 at defaults
amends: COMPLETION-PLAN.md, AMENDMENT-A1-2026-10-07.md (A1 ECONOMIC_CONTAINMENT), ce/a2 AMENDMENT-A2 (STOPPED)
covers: [goal-binding-by-default, coordinator-extinction, per-call-autopsy, fresh-focus-floor, cross-machine-goal-authority, overshoot-bound, a1-reforecast]
source: Owner ULTRA prompt 2026-10-07 "Cognitive Economy next generation" (bootstrap source, cold: workers never read it)
mode: PLAN amendment to an existing owner. HR-NOVELTY-001: no new Budget/Context/Mission OS. EXECUTION per unit.
---

# Amendment A3 -- bind every pane to its goal, kill the coordinator, then cut the floor

Workers read THIS card + gen2/ledger.json + their own unit packet. Never the source prompt or a transcript.

## Verified reality (zero-model scan, 2026-10-07 ~20:45 local)
- Four cap breaches today, same mechanism each time (interactive coordinating panes, not workers):
  A1 42,307,381 / 20M (panes 423e33b0 24.7M + b9bd9469 16.5M; worker U1 1.10M / 11 calls);
  A2 27,612,077 / 20M (coordinator 16.92M / 71 calls ~238k/call; worker 10.70M / 61 calls ~175k/call);
  gen3 ~37.2M / 31M (T1c worker 1.75M / 17 calls; finishing pane 0f9b771b 10.08M / 66 calls ~153k/call);
  context-runtime-3 24.5M / 7.2M (coordinator 18.4M). Lesson was in memory at 11:27 and recurred 3x: prose, not mechanism.
- Pre-call goal reservation EXISTS: 31f1e714 + b79f4737 (merged c12138da): GoalLedger, goal-declare/renew/spawn/status,
  session_budget_guard goal mode, Agent lane. GOAL_PASS=45/45, mutation 10/10. Live dispatcher == mirror (6C8BF09F);
  settings Agent registration present. Live canary `canary-20261007` (3M cap, 2 sessions, Agent holds) started 20:43
  by pane 2a90c34a -- a concurrent writer; A3 consumes its verdict, never re-runs it.
- Gap: a goal binds only by CPP_GOAL env or cwd root. Every breaching pane ran unbound in a shared checkout. GEX44
  live PP daf90d00 has no admission -> GEX44 spend is UNKNOWN (fail-closed only if the goal lists hosts).
- Per-call economics: cost ~= calls x (floor ~105k fresh + growth to 150-240k). Floor >= ~50-70% of every call.
  Floor composition (host vs CPP) is UNMEASURED: T2 retired, A2-4 never ran.
- Unmerged owners: a1/u1, a1/a1-2 (turns.py --attribute, 18/18) in pp-a1; ce/a2 9 dirty paths (A2 meter worker).

## Units (each a bounded headless sonnet worker with a packet, cwd = goal root; no coordinating pane)
| unit | what | cap | done when |
|---|---|---|---|
| U0 | this pane: goal-declare ce-a3 (root Apps/pp-ce-a3, cap 12M incl. this pane), worktree off c12138da + merge a1/a1-2, packets, launch U1; then exit | 0.6M | goal-status shows ce-a3 bound; this pane makes no further calls |
| U1 | per-call autopsy (deterministic): turns.py --attribute series for 423e33b0, b9bd9469, 886d7bb9, 0f9b771b, e6e0eca7: calls, context/call, floor, growth, tool-output share, repeated reads, decisions; counterfactual = fresh packet worker | 1.2M | receipt with calls-vs-rent split per pane, top-5 rent classes |
| U2 | goal binding by default: an unbound session that writes a goal's declared program paths is denied until bound; coordinator sub-cap (goal-spawn --role coordinator --calls N); superseded-goal + stale-lease + late-usage tests | 2.5M | V-GOAL additions RED-before/GREEN-after, mutants killed; tiny-cap multi-pane canary 0 unauthorized overshoot beyond documented bound |
| U3 | Fresh Focus Floor: on/off probes per injected surface (SessionStart injections, UserPromptSubmit, rules, CLAUDE.md, skills/agents listing, MCP); host vs CPP split; retire top CPP renters via relevance gating; ~/.claude parts as Owner diffs | 2.5M | floor_regression_gate delta measured < 0, no V-gate regressions |
| U4 | cross-machine: GEX44 PP fast-forward + goal host listing + GEX44 meter row (Owner step for ~/.claude on GEX44) | 0.8M | a GEX44 worker bound to ce-a3 is admitted and settled in the laptop journal; unlisted host refused |
| U5 | UKDL (3 levels, dedupe), KV incident, CBR promotion, Cognitive CI wiring of V-GOAL + floor gate, A1 reforecast | 1.4M | C-checks green; A1 reforecast receipt |
Reserve: proof/repair 1.5M (not spendable by U1-U4). Operating target 8M. Hard cap 12M. Crossed cap = stop, never raised.

## Master Done-Gate (executable)
`python tools/test_goal_budget_admission.py` exit 0 incl. new gates; canary receipt evidence/goal-admission/CANARY.md
with zero unauthorized overshoot; U1 receipt; floor_regression_gate delta < 0 measured on a real fresh call; a GEX44
admit+refuse pair; `cep_gen2.py --tranche ce-a3` green; ce-a3 metered total <= 12M INCLUDING this pane; UNKNOWN never passes.
</content>
</invoke>
