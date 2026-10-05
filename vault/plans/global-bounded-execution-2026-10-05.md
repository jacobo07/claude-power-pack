---
id: PLAN-GLOBAL-BOUNDED-EXECUTION
date: 2026-10-06
status: APPROVED 2026-10-06 (Owner "Approve (Recommended)" to the inline ULTRA-PLAN; this file mirrors it)
covers: [global-bounded-execution, gen3-t3-recompile, wu-profile, budget-fast-path, dispatch-gate, rollover-idempotency, checkpoint-root, voi-admission, s7-decision]
parents: [vault/plans/gen3-t3-runtime-RESUMPTION.md, vault/plans/autonomous-optimization-2026-10-05.md, vault/specs/mission-envelope-and-compiled-wu.md]
mode: EXECUTION per Work Unit, one fresh worker per unit (/kclear -> /kresume); PLAN only for local uncertainty
done_gate: section "Done-gates" below; spend per unit declines across the programme (self-hosting gate)
---

# Global bounded execution -- Gen3 T3 recompiled (no new subsystem)

The old T3 roadmap (S3..S7, 50M cap, 20M checkpoint) is superseded. Unused cap is not carried forward.

## Measured at approval (zero-model, session d8d8d060 scratchpad t3_spend.py)
- T3 pane 2cc507fd: 22,007,631 processed, 91 calls, 0 subagents; first context 120.7k, peak 341.1k, average 241.8k.
  Floor carriage ~11.0M (50%), history rent ~11.0M (50%). Quartile average context 168k / 230k / 261k / 302k.
- Edit fragmentation: 21 edit calls on 3 files (session_budget_guard.js 11) ~ 5.1M. Irreducible design ~2-4M.
- Counterfactual (not a saving): rotating at the S1 boundary saves ~4.9M (22%).
- Live finding: the 2cc507fd handoff landed in the pp-gen3-t3 project memory while its transcript is under the PP
  project -- checkpoint root follows cwd (S3 target).

## Ownership (EXTEND / CONNECT only)
Work Unit = gsd_mission envelope (wu_packet, token_estimate, model, + profile). ContextImage = host floor at a profile +
source_packet hashed excerpts. Envelopes = mission_spend + session_budget_guard + _cost_breaker. Lifetime = rollover_econ.
Orchestration = gsd_mission Ralph. Counters = usage_index v5 (autonomous-optimization P1). Experiments = paired_experiment
(+ required VoI block). Proof = IC pinned-proof graph, done_gate. Floor/residency = IC Pillar K (other pane; never edit
its state). CBR = modules/tower: NOT writable honestly (donegate.judge and ratchet.promote have no live caller, R-cbr.md).
UWCP not adopted (no cross-plane coordination needed).

## Work graph (central / calls; hard stop remaining 20M, warn 13M; per unit 2x planned calls without new evidence -> recompile)
- c1 DONE 4eb924a6: S2 tree meter committed (SBT 6/6 re-run before commit).
- c0 this file + RESUMPTION.
- c2 R1 V-SBG-LATENCY: 5 runs HEAD~1 vs HEAD, attribute cause (0.8M / 6).
- c3 R2 fast path: per-file offset cursor + size/mtime skip over the known child set (<sid>/subagents, mission worker ids);
  tree reconciliation only as fallback; red/green + mutant (1.7M / 12).
- c4 R3 dispatch gate in agent-solo-guard (decide(payload,{dispatch:true})) + session_checkpoint.py exempt from the
  breaker; one fresh pp-code-reviewer (Sonnet) on the seam (2.4M / 15).
- c5 R3 land S1+S2+c3+c4 in the main checkout by patch apply only (another pane's hunk in session_budget_guard.js and
  test_session_budget_guard.py stays); hash-verified copy to ~/.claude/hooks; DEPLOY hard rules fetched first; live probe:
  one tiny subagent Read -> state file names the child transcript (0.9M / 6). HR-001: if the classifier refuses the
  ~/.claude write, ship the repo half and hand the Owner one Copy-Item line.
- c6-c7 R4 rollover state machine (sealed -> clear_pending -> cleared; Stop no-op while unchanged) and checkpoint root
  from the launch project, red/green each (1.7M / 12).
- c8 R5 envelope `profile` field + source_packet role sections + floor probes per profile (IC K probe) + context-mutation
  test (drop one required excerpt -> refuse or page) (1.9M / 10 + probes).
- c9-c10 R6 LOW micro-canary: holdings-client.server.ts:343 on canary/odr-p4-packets (io-odr-p4-canary), supervised
  gsd_mission, wu_packet + lean profile, hard stop 1.0M, <=15 calls, 0 orchestration model calls; no push, no deploy.
- c11 paired_experiment refuses a record without VoI (claim, cheaper alternative, decision changed, cost, stop) (1.1M / 8).
- c12 Vault: session_lessons.md + ukdl-candidates.md UC-13..; ukdl-universal process rules only for source-verified
  platform facts (prompt budget is not isolation; work packet is not ContextImage); T3 readout (1.1M / 8).
- R7 two-child live canary ONLY if c5's probe leaves ambiguity (+1.5M).
Bottom-up remaining: LOW ~9M / CENTRAL ~13M / HIGH ~20M.

## S7 (full Phase-4 replay): REJECTED by VoI, kept conditional
Offline (T2-0) proves lifetime grid + control-loop share; R5/R6 prove floor and known-transform cost; c5 probe (R7 if
needed) proves child enforcement. Only "aggregate saving on a multi-decision mission" is left, and the only decision it
changes is CBR promotion, which tower wiring blocks anyway. Phase 4 product scope is untouched (built, review APPROVE).

## Done-gates
Affected suites per unit (test_session_budget_tree, test_session_budget_guard incl. latency, hooks/tests/test-agent-solo-guard.js,
rollover tests, new checkpoint-root test, test_gsd_mission_envelope, test_paired_experiment); tools/test_hook_boundary.py;
modules/liveness/reachability.py; mutation drill red on each new guard branch; live probe evidence; R6 within envelope
with external metering; per-unit spend declines.
