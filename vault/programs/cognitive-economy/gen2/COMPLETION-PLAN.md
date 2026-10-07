---
id: PLAN-CE-GEN2-COMPLETION
date: 2026-10-07
status: APPROVED 2026-10-07 (Owner 'y', pane 71ccfa86): items 1-3; executing T0
covers: [cognitive-economy-gen2-completion, selective-semantic-materialization, read-extinction, transport-extinction, process-lifecycle, forget-safety, autocompact-retirement, model-boundary-elimination, g2-return]
parents: [vault/programs/cognitive-economy/gen2/MISSION.md, vault/plans/tok18-tranche-context-runtime-2026-10-06.md, vault/specs/compiled-grammar-default.md]
mode: PLAN for the program (architecture settled: extend gen2). EXECUTION per tranche. No ULTRA.
---

# Cognitive Economy gen2 completion (Macro-Goal A) then G2 return (Macro-Goal B)

Workers read THIS card and the tranche they own. Not the Owner's source prompt (bootstrap source, cold), not any
transcript. State lives in `gen2/ledger.json`; this card is the compiled contract.

## Verified reality (2026-10-07, zero-model scans)
- Canonical owner EXISTS: Cognitive Economy gen2 (TOK-18 v2), approved 2026-10-05, boundary 150M processed,
  `spent_measured: null`. W1 W3 done, W2 deferred to gsd_mission owner. OPEN: W4 W5 W6 W7 W8 W9 R.
  `tools/test_cognitive_economy_program.py --generation 2 --final` -> FAIL 7 (exactly the open units); obligations
  UNASSESSED (`obligations_declared: false`).
- Owner gates still standing: W4/W5 not before 2026-10-11T18:00Z; W6 (capsule-v2 T8, zero-transcript proof) HELD.
- Execution substrate EXISTS: `tools/tranche_driver.py` (fresh workers in a git worktree, session-declare admission,
  V-DRIVER 21/21), `hooks/session_budget_guard.js` + `mission_spend.py session-declare` (admission by projection,
  968ed5a0), `tools/rollover.py` (kclear/kresume capsule claim + certify), WAKE_FLAG consumer on gsd_x GoalLog
  (e5a88eb3), `tools/gsd_dossier.py` (deterministic dossier, EDD canary 13/13), e1 task bank (11 cross-domain tasks),
  listing_floor_probe + floor_regression_gate (61/61).
- Floors (S1, measured): fresh-session first call 105,454 tokens; CPP hooks 3,051 (measured); host-forced UNDECIDED
  (<= 102,403, still holds 133,536 chars of CPP instruction files). Largest controllable item `~/.claude/CLAUDE.md`
  39,809 chars (Owner-only, HR-001); next in-repo: project CLAUDE.md HARD RULES mirror 21,230 chars incl. stub/test
  entries HR-001..007 (fix in compiler source).
- Dominant tax (5 overruns, one cause): an orchestrating pane re-sending ~170-230k per call; cost(n) ~ n*121k +
  1.05k*n^2. EDD: 76% of 32M was one-grep-per-call evidence acquisition in a 250k child; continuation epochs 21.5% tax.
- Measurement anomaly: `self_spend --session 71ccfa86` reports 83.9M / 411 calls with 47.8M in 284 subagent calls for
  a session that spawned no Agent. Attribution UNVERIFIED until T0 resolves it.
- G2 (Macro-Goal B) now: WU-G2b worker m-9d00610493fc finished 3 commits on GEX44 `worktree-wu-g2` (97412541) +
  RECEIPT-G2.json at 9,757,948 metered (est. 10M); supervisor marked BLOCKED "GSD NO_PHASES" because live daf90d00
  still judges by GSD phases, not the packet gate (G1 law not deployed). G1 record m-604666a514a3 stale RUNNING+hold.
  Stall breaker still blind to worktrees on live. All branches mirrored to GitHub 2026-10-07.

## Falsified prompt assumptions
UKDL path `knowledge-vault/UKDL/universal-knowledge.md` does not exist (real: `vault/knowledge_base/ukdl-universal.md`).
The G2 mission is not armed/running: it completed and is BLOCKED on a supervisor-law gap. Context Compiler is
ABSENT (skill-capability ledger L deferred it to TOK-18 WU3). "Build a new architecture" is falsified: >80% of the
named constructs map to existing gen2 units/owners (map below).

## Non-duplication map (do NOT build)
Context OS / Memory OS / Epoch OS / Transport OS / Governor OS / Hypervisor; a second Goal store (gsd_x GoalLog owns
it); a second continuation format (capsule-v2 + rollover.py); a second budget guard (session_budget_guard.js); a second
dossier (gsd_dossier.py); a second spend meter (mission_spend / self_spend); a second floor probe; a second
mission compiler (G2's gsd_compile.py) or waiter (G2's mission_wait.py); a new program gate (extend
test_cognitive_economy_program.py). D2A family run required before any NEW row (HR-NOVELTY-001).

## Construct -> owner map (EXTEND)
Measurement truth -> W4 + self_spend/usage_index. Forget Safety, transcript-free continuation, pane-loss, autocompact
retirement -> W6 on rollover.py/capsule-v2. Zero-hot WAITING -> WAKE_FLAG/GoalLog. SSM/ContextImages/Decision Capsules
-> TOK-18 WU3 Context Compiler on gsd_dossier. Read barrier/Read Extinction -> gsd_dossier + audit_cache. Tool/Agent
output quarantine, receipts, parentless orchestration -> tranche_driver + G2 mission_wait. Model-boundary admission,
reason codes, Proof of Non-Work -> session_budget_guard + packet `done_gate:`. Agent admission -> agent-solo-guard
lineage + tranche_driver. Proof compiler -> existing affected-test selection (owner to be resolved in T2 by dossier,
UNKNOWN today). Shadow/canary/policy versioning -> W5 champion/challenger + W7. Self-retirement -> CLAUDE.md compiler
source + E1 rule-move lineage. Self-hosting/deflation -> W8. UKDL/CBR -> W9 (pp-cbr-wt). Review -> R.

## Tranches (re-estimated bottom-up at each start; one fresh admitted worker per unit; this pane never orchestrates)
T0 EXECUTION, cap 3M: (a) resolve the self_spend attribution anomaly (uncertainty dominator: every envelope depends on
  it); (b) fill `budget_tokens.spent_measured`; (c) declare gen2 obligations C1-C14 below in the ledger so the gate
  measures them; (d) G2 deterministic re-verification as owner reuse (gates only, zero-model, read-only on GEX44; no
  deploy) because T5 consumes gsd_compile/mission_wait instead of rebuilding them.
T1 W6 EXECUTION, cap 8M: Forget-Safety check in rollover.py certify (machine continuation suffices without handoff
  prose); pane-loss, handoff-destruction and transcript-deletion tests on a canary mission; autocompact demoted to
  emergency fallback on certified paths; zero-hot WAITING via WAKE_FLAG; stale-pane lease revalidation.
T2 WU3 PLAN-local, cap 6M: Context Compiler sufficiency = gsd_dossier-backed ContextImage/Decision Capsule with
  projection pushdown, frozen naive-trim arm, 4 historical planner runs; verdict WIN/LOSE/UNDECIDED.
T3 W4 EXECUTION, cap 6M: offline replay over usage_index: KEEP vs DEALLOCATE epoch policy, model mix, read/transport
  classes; shadow policy recorded, never acting.
T4 EXECUTION, cap 6M: read/transport extinction step on the top high-rent class found by T3 (candidate: one-grep-per-
  call evidence acquisition -> dossier query); tool-output quarantine receipts in tranche_driver.
T5 W5 EXECUTION, cap 20M: champion vs challenger on a real backlog task (same scope/proof/authority), challenger =
  compiled packet + gsd_compile + mission_wait + admission + no parent relay.
T6 W7 EXECUTION, cap 6M: promote only primitives T3-T5 earned (canary -> certify -> CBR); policy versioned + rollback.
T7 EXECUTION, cap 4M: self-retirement: fix HARD RULES mirror compiler (drop stubs/test entries), measure floor delta
  with floor_regression_gate; `~/.claude/CLAUDE.md` retirements produced as Owner-applied diffs only (HR-001).
T8 W8 EXECUTION, cap 6M: self-hosting second pass; cross-domain benchmark from the e1 bank; deflation readout.
T9 W9+R EXECUTION, cap 5M: UKDL (duplicate check first), KV causal records, CBR baseline, independent review.
Then Macro-Goal B (below).

## Economics
Program cap = existing gen2 boundary 150M (no new authority asked). Bottom-up: tranches 70M + reserve 15M (repair/proof)
= 85M ceiling; central forecast ~55M. Per-call floor ~105k fresh => a unit's allowance = cap / (105k + growth).
Breakers: per-unit session-declare stop at its cap; context circuit breaker = admission projection; any tranche > 1.5x
forecast -> deopt and diagnose before the next. Never carry an Opus pane across units.

## Master Done-Gate (one command)
`python tools/test_cognitive_economy_program.py --generation 2 --final` exits 0, extended (T0) with obligations, each
an executable check, UNKNOWN never passes:
C1 ownership: D2A family run, no NEW system without 13Q. C2 state: transcript-deletion + handoff-destruction tests green.
C3 lifecycle: SAFE_TO_FORGET check both poles; /kclear->/clear->/kresume focus certified on a canary; autocompact not
the continuation on certified paths; WAITING with zero hot sessions. C4 recovery: pane-loss canary resumes model-free to
first verified progress. C5 context: WU3 verdict file; different boundaries receive different projections (both poles).
C6 read: one high-rent read class extinct or a certified step. C7 transport: tool/agent receipts on certified path;
transit waste measured down on a real workload. C8 boundaries: reason-coded boundaries; non-novel count down vs
champion. C9 agents: admission enforced; one historical Agent role eliminated or proven necessary. C10 proof: affected-
proof selection proven; healthy proof readless. C11 autonomy: one epoch policy auto-selected (KEEP in one workload,
DEALLOCATE in another); one policy shadowed then canaried; rollback exists. C12 baseline: one hot rule/mechanism retired
or proven not yet safe; UKDL/CBR entries exist. C13 economics: program spend <= 85M measured, no cost shifted to repair
or Owner. C14 original work: G2 state reconstructable from this card + GEX44 records without any transcript.

## Macro-Goal B (G2 return) -- preserved, not executed in A
Durable state: GEX44 `~/missions/grammar` branches grammar/default 7fa16098, grammar/g2-partial 713bd7ba,
worktree-wu-g2 97412541 (+RECEIPT-G2.json); records m-9d00610493fc BLOCKED, m-604666a514a3 stale, m-da6e925b5092 HALTED;
GitHub mirrors. On A's gate: Proof of Non-Work first (re-run gates on worktree-wu-g2), then remaining obligations from
reality: independent verification, stall-breaker worktree fix, G1 record cleanup, supervisor packet-gate law,
live deploy (Owner authority boundary). Run it under the new baseline as the first post-program canary.

## Owner-only items in the single approval
1. Plan + envelope (85M ceiling inside the existing 150M). 2. Lift the 2026-10-11 not-before on W4/W5 and the W6 hold.
3. Push stays Owner-granted per branch as today; ~/.claude edits stay Owner-applied.
