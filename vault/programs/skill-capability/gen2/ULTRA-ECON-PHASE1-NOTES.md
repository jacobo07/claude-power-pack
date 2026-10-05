# /ultra (execution economics for Skill Capability Gen 2) -- Phase 1 notes, pane c85f3eb9, 2026-10-05

Status: Owner brief = "/ultra-plan ... redesign execution economics; DO NOT launch the 48 h / 16-cycle / ~0.8 B Gen 2
run". /ultra protocol loaded; Phase 1 (reality scan) IN PROGRESS; Phase 2 (6 questions, mandatory stop) NOT yet emitted.
The Owner brief text is in this pane's transcript (pasted block starting "/ultra-plan"); copy it verbatim next to
OWNER-BRIEF-2026-10-05.md as OWNER-BRIEF-ECON-2026-10-05.md before planning.

## Done this step (verified)
- GEX44 timer `sc-gen2-arm.timer` DISABLED (inactive, not listed); log line appended to
  /home/kobii/missions/skill-capability-data/arm-gen2.log. Units + arm_gen2.py remain on disk, unused.
- GEX44 missions in /home/kobii/missions/skill-capability: m-e06956b05759 HALTED, m-3d8e5c151705 HALTED (halted by
  this pane with a non-budget reason so it cannot renew; its blocked worker was reaped by the sweep 09:13:38Z).
- GEX44 clone root + run branch at da110005 (rearm commit: OWNER-BRIEF-2026-10-05.md, gen2 plan, ROADMAP phases
  10-11). The 0.8 B estimate inside vault/plans/skill-capability-gen2-2026-10-05.md is now SUPERSEDED by the Owner.

## Measured (GEX44, deterministic, no model calls)
Gen 1 total (81 transcripts): 488.6 M processed; cache_read 473.7 M, cache_write 14.4 M, out 0.45 M, input 5.5 k;
2,759 calls; Opus 2,334 / Sonnet 424.
Subagent breakdown (76 subagent files, 70 with meta.json agentType):
| agentType | agents | calls | cache_read | out | avg first ctx | Opus/Sonnet calls |
| gsd-executor | 27 | 920 | 136.0 M | 77.8 k | 86.6 k | 602 / 318 |
| gsd-code-fixer | 10 | 485 | 90.5 M | 26.9 k | 83.4 k | 458 / 27 |
| gsd-planner | 12 | 399 | 66.8 M | 13.4 k | 87.1 k | 399 / 0 |
| gsd-code-reviewer | 9 | 220 | 29.1 M | 3.2 k | 72.1 k | 187 / 33 |
| gsd-verifier | 8 | 193 | 22.1 M | 16.6 k | 85.6 k | 175 / 18 |
| gsd-plan-checker | 10 | 95 | 9.8 M | 1.8 k | 84.7 k | 67 / 28 |
Reading: every child starts at ~72-87 k tokens of context before doing anything (startup floor = listing + CLAUDE.md
+ hooks, not parent history); review->fix loops (reviewer 29 M + fixer 90.5 M = 120 M, ~25 % of Gen 1) and planners on
Opus (67 M) are the largest addressable families; executors are the real work. Parent sessions = remainder (~119 M).

## Still to scan (Phase 1), cheapest first
1. Existing owners -- the cognitive-economy program (vault/programs/cognitive-economy/ledger.json) already owns most of
   this brief: pillars F reread, G CSE, H turns per advancement, K tool-output admission, L compile-out, M model
   allocation, N event-driven, O cognitive IR, P proof reuse; its mission m-fdefb0fca0c0. Read its state.* before
   proposing anything (EXTEND/CONNECT, never a parallel owner). Also: tools/usage_index.py, tools/gsd_epoch.py census,
   vault/config/model-routing.json + modules/cost_collapse/router.py, modules/capability_runtime/agent_spec.py (compiled
   AgentSpec = lean child context already exists), hooks agent-solo-guard / prompt_minimalism_gate, D2A ledger.
2. Iteration prompt C:\Users\User\Downloads\Promptsss\Prompts pa iterar\Universal\iteracion-avanzada-universal.txt.
Then: Phase 1 summary + Phase 2 six questions (mandatory stop).

## Phase 1 closed (pane e1cb7fc6, 2026-10-05, after /kresume RESUME_CERTIFIED at 891a56e)
- Brief verified against telemetry: 2,312 subagent calls = sum of the role table above (920+485+399+220+193+95);
  weighted 78 M = 5.5k + 0.1*473.7M + 2*14.4M + 5*0.45M. Both brief numbers reproduce.
- Pricing (vault/pricing, 2026-09-27): cache_read is $0.20/MTok on BOTH Opus 5.5 and Sonnet 5. At Opus rates Gen 1 =
  cache_read ~$95 + cache_write $72 (5m) to $115 (1h) + output ~$9. Model routing cannot touch the cache_read half;
  its ceiling is half of cache_write+output, IF every call moved (upper bound, not a saving).
- Avg processed per call ~177 k. 70 typed children's first-call context sums to ~6.4 M (written vs read from a shared
  prefix NOT yet split). Child count x startup floor and calls x carried context are the two dominant multipliers.
- vault/config/model-routing.json maps gsd-executor -> Sonnet, yet executors ran 602/920 calls on Opus: the file
  does not control GSD spawns. The mechanism that does is not traced yet (Phase 6 premise).
- Existing owners (EXTEND, no parallel OS): CE closed 20/20 (CLOSE.md); M -> CCP C4 + modules/cost_collapse
  (routing experiments need Owner, handoffs/M.md); D/E context lifetime merged to existing owners; J non-convergence
  detector (3.51 %) handed off = the marginal-cognition gate's owner; F/K/P falsified below 3 % on D-W7 (re-test on Gen 1
  only, not assumed); modules/capability_runtime/agent_spec.py + cpp-carrier-* agents = lean child context already
  exists. CE E1 mission m-f011d7fdebc9 may still hold GEX44 quota (another pane's).
- Gen 2 plan with the 20 frontier items exists ONLY in the GEX44 clone (da110005); not on the laptop.
- Gen 1 transcripts (81) are on GEX44: the replay is deterministic python there, compact results pulled back.
- Phase 2: six questions emitted to the Owner in pane e1cb7fc6. STOP until answered.
