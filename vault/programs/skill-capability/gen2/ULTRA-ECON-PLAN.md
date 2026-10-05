# /ultra execution economics -- Phase 3 revised plan (pane e1cb7fc6, 2026-10-05)

Inputs: OWNER-BRIEF-ECON-2026-10-05.md (spec), OWNER-DECISIONS-ECON-2026-10-05.md (D1-D6, binding),
ULTRA-ECON-PHASE1-NOTES.md (reality). No implementation code in this document (brief kill-switch).

## Binding envelope
- D1: everything before the Gen 2 launch decision <= 30 M processed tokens; at 24 M only deterministic work or
  cognition needed to close the analysis. Metered by tools/usage_index.py windows (laptop) + the same reader over
  GEX44 transcripts, both summed; meter reading recorded at every wave boundary in gen2/SPEND.md.
- D2: Sonnet live canary = 4 bounded WUs, up to 6, sequential stop, inside D1.
- D3: independent review at integration boundaries only; extra review for high-risk / new architecture /
  authority / critical runtime / ambiguous test signal.
- D4: admission gates SHADOW -> CANARY -> ENFORCED; leave shadow at >= 100 eligible decisions per gate, <= 2 %
  false blocks, 0 critical false blocks, no measured quality/proof loss; kill-switch + rollback mandatory.
- D5: Gen 2 admitted only at >= 50 % reduction of avoidable cost vs the Gen 1 old-architecture replay; target
  <= 100 M; 100-150 M autonomous only with bottom-up proof the extra buys irreducible cognition/proof; > 150 M stop
  and ask once. No phase-average budget, ever.
- D6: pillar E is Gen 1 closeout; runs only after CE E1 (m-f011d7fdebc9, another pane's) is COMPLETED/HALTED.

## Owners extended (no parallel OS)
- Spend / telemetry: tools/usage_index.py (CE pillar A instrument).
- Mission runtime: tools/gsd_mission.py + tools/gsd_long_run.py (Ralph), on GEX44.
- Model routing: the mission clone's .planning/config.json `model_profile` / `models` / `model_overrides`
  (~/.claude/gsd-core/references/model-profiles.md). vault/config/model-routing.json is advisory and does not reach
  GSD spawns (Phase 1 finding); CCP C4 + modules/cost_collapse keep policy ownership (handoffs/M.md).
- Lean child context: modules/capability_runtime/agent_spec.py + cpp-carrier-* agents.
- Non-convergence / marginal cognition: CE pillar J detector owner (handoffs/J.md); turns gate gates/gate_turns.py.
- Spawn admission: hooks/agent-solo-guard.js (already gates Agent dispatch; extend, do not add a second hook).
- Program state: vault/programs/skill-capability/ledger.json; UKDL ukdl-universal.md; CBR owner for ratchet.

## Tasks (wave order; each ends with its verification)
W0 Preflight
 0.1 Record spend baseline (laptop window + GEX44 since Gen 1 end) in gen2/SPEND.md. Verify: two readings, commands quoted.
 0.2 Commit gen2 notes + OWNER-BRIEF-ECON + OWNER-DECISIONS-ECON + this plan, pathspec only. Verify: git show --stat lists only them; %s matches.
 0.3 SSH preflight to GEX44 (key ~/.ssh/kobicraft_gex44, BOM-free script file); read E1 mission status read-only. Verify: status line quoted.
W1 Gen 1 closeout (clear work only)
 1.1 Fetch Gen 1 run branch (tip 4b74882c) + da110005 to the laptop as refs (no merge yet). Verify: rev-parse both.
 1.2 Read LAPTOP-CLOSEOUT runbook from that ref; execute its already-clear steps; laptop C-fixed rows
     (8a79561d, 87a4d014) in results-delivery.jsonl committed own-hunk. Verify: runbook's own checks.
 1.3 Pillar E: deferred until E1 terminal (D6); then run its bounded harness with available controls. Verify: harness verdict + spend delta.
W2 Reality Compiler (deterministic first)
 2.1 Extract the 20 Gen 2 frontier items from da110005's gen2 plan into gen2/frontier.json.
 2.2 Classify each (ALREADY_SATISFIED / EXISTING_OWNER / EXISTING_CAPABILITY / DETERMINISTIC / MEASUREMENT_ONLY /
     KNOWN_PATTERN / COMPOSITION / TRUE_NOVELTY / BLOCKED / REJECTED) from git, ledgers, liveness, registries, tests.
     LLM only for items the deterministic sources leave ambiguous; each item: evidence, owner, deps, proof, reason.
     Verify: every item classified exactly once; ambiguous set listed with why.
W3 Offline replay of Gen 1 (deterministic, on GEX44 transcripts)
 3.1 Pre-register (frozen commit BEFORE running) the bucket rules: MECHANICALLY_AVOIDABLE, LIKELY_AVOIDABLE,
     NEEDS_LIVE_VALIDATION, IRREDUCIBLE_OR_ASSURANCE, UNSETTLED; CAF proxy and FCF definitions; materiality 3 %.
 3.2 Extend usage_index (or a sibling read-only reader) to attribute per call: role, model, context, child startup
     floor (written vs shared-prefix read), repeated file reads by content hash, test reruns under an unchanged tree,
     waiting/poll calls, child outputs never consumed, review->fix loop cost, phase boundaries' setup cost.
 3.3 Run over the 81 transcripts; pull compact results only. Verify: totals reconcile to 488.6 M / 2,759 calls
     (+/- 0); a seeded known-avoidable fixture lands in its bucket; a control lands outside it.
 3.4 Answer the brief's replay done-gate questions in gen2/REPLAY.md with denominators and commands.
W4 Execution policy (implement only replay-ranked, high-ROI levers)
 4.1 Routing: model_overrides in the mission clone config per measured task family.
 4.2 Review at integration boundaries (D3) as mission policy.
 4.3 Spawn admission + model-call admission in SHADOW (extend agent-solo-guard / J detector), decision log,
     kill-switch env + rollback note. Known-red: a plan whose budget is phase-count x phase-average is rejected.
 4.4 Lean child context via compiled AgentSpec for executor/fixer roles if replay shows the startup floor material.
 4.5 Proof reuse / waiting=sleep only if replay shows them >= 3 %; otherwise recorded as falsified for Gen 1.
W5 Sonnet canary (D2): 4 WUs low/medium risk, same proof contract, Opus baseline from replay; stop at 4 if decisive.
W6 Work Graph + bottom-up budget: gen2/WORK-GRAPH.json (every item once, every model WU states its uncertainty,
   every Agent a consumer, every phase a reason); budget per WU with interval; D5 admission verdict in gen2/ADMISSION.md.
W7 If admitted (D5): arm Gen 2 Ralph mission on GEX44 with the W4 policy; gates stay SHADOW until D4 criteria.
   If 150 M+: one decision packet to Owner, stop.
W8 UKDL / CBR candidates (no duplicates), final handoff in the brief's field list.

## Phase 5 fix injection (ULTRA-ECON-AUDIT.md gaps 1-12; these lines override the tasks above)
- G4/G5 meter: D1 processed = in+cw+cr+out, per program session id (laptop) + mission clone project dirs (GEX44),
  anchored at the brief (2026-10-05 08:55:43Z). Reading at Phase 5: 27.09 M (SPEND.md). D1 scope is an Owner question.
- G6 allocation (only if D1 is re-anchored or raised): parent orchestration <= 3 M; W1 closeout 2 M; E 6 M (after E1);
  W2 2 M; W3 3 M; W4 4 M; W5 6 M; W6 2 M; reserve 2 M. Past 80 %: continue W3 replay + W6 compile only; stop W5, E,
  2.2 LLM classification.
- SELF-HOSTING (new, from SPEND.md): pane c85f3eb9 averaged ~404 k processed per call after the brief, the largest
  cost so far. The parent pane rolls over (/kclear -> /kresume) at every wave boundary and never carries a wave's raw
  output; deterministic work runs as scripts whose compact results are read, not as model turns.
- G12 0.3: target kobii@gex44 (verify host alias in ~/.ssh/config first); the extended reader is copied at a pinned
  commit and its remote sha256 checked before 0.1-GEX44 and 3.3.
- G9: W5 and every GEX44 model call gated on an E1 terminal read, same as 1.3.
- G7 4.1: read the GEX44 clone .planning/config.json + its gsd-core resolver; one single-spawn probe confirms the model
  id in the child transcript before W5.
- G8 W5: frozen commit before W5 with WU selection rule, proof contract, pass/fail oracle, sequential-stop rule; matched
  task families (same family under Opus in the replay), not averages.
- G1/G2 4.3: admission gates live in tools/gsd_mission.py (the frozen J owner; progress fingerprint scoped to the
  mission's own branch per J.md), not in agent-solo-guard.js (win32-only, dead on GEX44). Liveness = count of real
  GEX44 gate decisions; zero after a cycle = gate dead, not clean. Kill-switch env + rollback commit named.
- G3 W7: processed-token halt in gsd_mission.py budget_exhausted from usage_index over the mission's own transcripts,
  set at the admitted upper interval, never > 150 M; known-red drill trips it.
- G10 W6: WORK-GRAPH.json carries all 8 Work Graph predicates and ADMISSION.md all 9 economic predicates as checked
  fields; the D5 verdict is computed from them and refuses on any missing.
- G11: the budget-compile check is a W6 tool with tests/fixtures: red = phase-count x phase-average budget, green =
  per-WU bottom-up budget. Owner recorded as one_shot/cost_collapse handoff (handoffs/M.md).

## Done-gates
- D1 meter never above 30 M before W7; SPEND.md shows every wave's reading.
- REPLAY.md answers all 14 replay questions; totals reconcile exactly.
- WORK-GRAPH.json: 20/20 items once; ADMISSION.md cites D5 thresholds with numbers.
- Admission gate test suite includes the known-red phase-average plan and a green control.
