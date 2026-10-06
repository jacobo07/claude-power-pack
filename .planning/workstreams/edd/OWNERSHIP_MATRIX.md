# EDD Ownership Matrix

Status vocabulary per ROADMAP Phase 1. Built from the zero-model dossier; rows start DATASET_ONLY/unjudged and are settled in place.

| ID | Concept | Status | Producer | Consumer | Evidence / note |
|---|---|---|---|---|---|
| C-01 | PRIMARY SOURCE / MISSION BASIS | DATASET_ONLY | - | - | UNKNOWN: no dossier candidate is the owner; meaning of "primary source" not settled by a page |
| C-02 | EXECUTION MODE DECISION | UNDER_ANOTHER_NAME | modules/gsd_x/tier.py:83 | modules/gsd_x/cli.py:205 | tier.classify measured, injected by the UserPromptSubmit seam; mode choice itself is CLAUDE.md PR-MODE-SELECTION-001 prose |
| C-03 | PLAN EXPERIENCE | DATASET_ONLY | - | - | UNKNOWN: no candidate; dossier hits are lexical noise |
| C-04 | FIRST ACTION — FULL REALITY SCAN | NOT_A_SYSTEM | - | - | process instruction; carried by ROADMAP Phase 1 itself |
| C-05 | MANDATORY ITERATION STANDARD | DOCUMENTED_ONLY | - | - | source/iteracion-avanzada-universal.txt is a text standard; no executable owner found; conflicts listed in vault/specs/edd.md |
| C-06 | DELEGATION PRINCIPLE | DATASET_ONLY | - | - | UNKNOWN: no candidate; agent-solo-guard.js (Rule J) governs dispatch bounds, not shown to be this concept |
| C-07 | OPPORTUNITY DELEGATION PRINCIPLE | DATASET_ONLY | - | - | UNKNOWN: no candidate |
| C-08 | MISSION NORTH STAR | UNDER_ANOTHER_NAME | modules/gsd_x/goal/contract.py:113 | modules/gsd_x/goal/convergence.py:323 | goal declare carries intent; goal_closure is the convergence the north star demands |
| C-09 | ARCHITECTURAL TARGET — SEMANTIC REALITY COMPILATION | DATASET_ONLY | - | - | no owner: obligation.derive_from_facts (obligation.py:454) reads 10 regex facts, no semantic model (research A1) |
| C-10 | SEMANTIC CONSERVATION LAW | DATASET_ONLY | - | - | gap: 4 operators DO-1..DO-4 are consequence/absent-signal/failure/parity shaped, none state/ownership/projection shaped (research A1, obligation.py:392-397) |
| C-11 | UNIVERSAL SEMANTIC CONSERVATION FAMILIES | DATASET_ONLY | - | - | same gap as C-10; Phase 3 operator families |
| C-12 | PURPOSE-FIRST REASONING | DATASET_ONLY | - | - | UNKNOWN: no candidate |
| C-13 | RELATIONSHIP COMPLETENESS | DATASET_ONLY | - | - | UNKNOWN: no candidate |
| C-14 | TEMPORARY STATE LAW | DATASET_ONLY | - | - | UNKNOWN: state-lifetime doctrine lives in ~/.claude/rules (outside repo scope); no in-repo operator |
| C-15 | OWNERSHIP CLOSURE | UNDER_ANOTHER_NAME | tools/usea_ownership_audit.py:144 | tools/verify_spp.py:823 | USEA ownership audit is the canonical-authority checker, run by verify_spp |
| C-16 | PROJECTION CLOSURE | ALREADY_IMPLEMENTED | modules/gsd_x/mission/closure.py:228 | tools/gsd_x_mission.py:205 | project_closure is a projection that can say no (blocking set: backlog, ACCEPTED, STALE, CANDIDATE, blindness) |
| C-17 | EDD CANONICAL RESPONSIBILITY | DATASET_ONLY | - | - | UNKNOWN: possibly C-15 owner; not settled |
| C-18 | COMPLETION LENSES | DATASET_ONLY | - | - | UNKNOWN: no candidate |
| C-19 | ACTIVE EPISTEMIC CONTROL | DATASET_ONLY | - | - | UNKNOWN: modules/decision_review/epistemic_algebra.py:60 is a candidate, not read |
| C-20 | FOUNDER DECISION QUESTIONS | PARTIAL | modules/gsd_x/goal/reconcile.py:179 | tools/gsd_x_goal.py:289 | ESCALATE carries a packet dict at runtime; not a persisted question class, no compression |
| C-21 | FOUNDER QUESTION COMPRESSION | DATASET_ONLY | - | - | UNKNOWN: frontier_intelligence/session_compiler.py:6 orders candidate questions; not shown to compress Founder questions |
| C-22 | INTENT CLOSURE CHECKPOINTS | PARTIAL | modules/gsd_x/mission/contract.py:141 | tools/gsd_x_mission.py:203 | mission contract projects intent into closure input; no intent-closure checkpoint events |
| C-23 | ASSUMPTION LIABILITY | DATASET_ONLY | - | - | UNKNOWN: no candidate |
| C-24 | MULTI-REFERENCE INTELLIGENCE | DATASET_ONLY | - | - | UNKNOWN: no candidate |
| C-25 | REFERENCE MECHANISM EXTRACTION | PARTIAL | modules/gsd_x/mission/obligation.py:347 | tools/gsd_x_mission.py:65 | reference_is_executable + parity operator DO-4 interrogate a runnable reference; no mechanism extraction |
| C-26 | REFERENCE FRONTIER | DATASET_ONLY | - | - | UNKNOWN: D2A d2a_engine.py:980 run() is the candidate owner of reference-to-advantage; its callers were not traced |
| C-27 | EXCELLENCE FRONTIER | DATASET_ONLY | - | - | UNKNOWN: no candidate |
| C-28 | FOUNDER OPPORTUNITY REVIEW | DATASET_ONLY | - | - | proactive_scanner.py:70 types opportunity; its only importers are a docstring and tests, so no consumer |
| C-29 | SUPERIORITY CLAIMS REQUIRE PROOF | PARTIAL | modules/gsd_x/mission/closure.py:67 | modules/gsd_x/goal/convergence.py:268 | evaluate_transition refuses narrative as authority; no superiority-claim class |
| C-30 | EXPECTED REALITY VERSUS OBSERVED REALITY | PARTIAL | modules/gsd_x/mission/closure.py:36 | modules/gsd_x/goal/convergence.py:268 | Verdict is the observed side; the expected side is only the obligation consequence text |
| C-31 | SEMANTIC RESIDUALS | DATASET_ONLY | - | - | UNKNOWN: closure.py:184 residual_risk is lexical neighbour only |
| C-32 | CONTINUOUS BUG → CAPABILITY ASCENSION | PARTIAL | tools/ceps.py:360 | tools/ceps.py:472 | CEPS records errors and distributes; failure-to-capability step absent (convergence.record_failure :240 has no production caller) |
| C-33 | SEMANTIC INVALIDATION EVENT | PARTIAL | modules/gsd_x/mission/obligation.py:511 | tools/gsd_x_mission.py:93 | invalidate_if_parent_gone fires on fact disappearance only; no defect-triggered event (research A1) |
| C-34 | DUAL REPAIR OBLIGATION | DATASET_ONLY | - | - | no product+factory pair: FAILURE_DISPOSITIONS (convergence.py:60) has no factory disposition |
| C-35 | EARLIEST PREVENTABLE POINT | DOCUMENTED_ONLY | - | - | CLAE Part 30 six-level elevation ladder (vault/knowledge_base/clae/CLAE_INDEX.md:46); no code |
| C-36 | CAPABILITY LEARNING OVER BUG MEMORIZATION | DATASET_ONLY | - | - | UNKNOWN: deep-research E3 capability learnings are research-domain only |
| C-37 | SIBLING EXPLOSION SEARCH | DOCUMENTED_ONLY | - | - | CLAE Part 30 section 5 sibling defect campaign (PART_31_failure_family_synthesis.md:204 cites it); no code |
| C-38 | FORWARD IMMUNITY PROPAGATION | PARTIAL | tools/ceps.py:231 | tools/ceps.py:472 | CEPS M10 forward propagation substrate + M11 distributor; propagates patterns, not capability revisions to live goals |
| C-39 | SELF-EVOLUTION DEBT | PARTIAL | modules/gsd_x/goal/convergence.py:240 | modules/gsd_x/goal/convergence.py:323 | record_failure + goal_closure block undispositioned failures; no factory disposition and record_failure has no production caller (research A7) |
| C-40 | CAPABILITY REVISIONING / NO SELF-CORRUPTION | DATASET_ONLY | - | - | UNKNOWN: goal/contract.py:124 revise refuses silent weakening; no production caller of revise found by grep |
| C-41 | FACTORY REGRESSION | PARTIAL | tools/mutation_ratchet.py:85 | tools/verify_spp.py:676 | mutation ratchet at push tier guards existing code; nothing guards the factory as a whole |
| C-42 | NOVEL HOLDOUTS | DATASET_ONLY | - | - | Phase 2 deliverable; none exist |
| C-43 | PREVENTION DEPTH RATCHET | DATASET_ONLY | - | - | UNKNOWN: no candidate; modules/tower ratchet is baseline depth, not prevention depth |
| C-44 | EXPECTATION ESCAPE INCIDENTS | DATASET_ONLY | - | - | Phase 2 gold set; SkyParty evidence is external (answer side) |
| C-45 | BLIND COUNTERFACTUAL REPLAY | PARTIAL | modules/rule_compiler/counterfactual.py:111 | modules/rule_compiler/effect_harness.py:155 | rule-level counterfactual (WOULD_BLOCK/WOULD_NOT_BLOCK); not blind generative replay |
| C-46 | SKYPARTY FORENSIC GOLD SET | DATASET_ONLY | - | - | Phase 2; tarballs are outside the repo |
| C-47 | FOUNDER-FIRST SURPRISE | DATASET_ONLY | - | - | UNKNOWN: no candidate |
| C-48 | DECISION FRONTIER | PARTIAL | modules/decision_review/decision_record.py:241 | modules/decision_review/decision_kernel.py:291 | DRK registry is the decision provenance owner (1 row); no blocking-packet class and no closure effect |
| C-49 | REFERENCE CHALLENGE CONTRACT | DATASET_ONLY | - | - | UNKNOWN: no candidate |
| C-50 | EXCELLENCE / FRONTIER ADVANCEMENT | DATASET_ONLY | - | - | UNKNOWN: no candidate |
| C-51 | EXPECTATION CLOSURE | PARTIAL | modules/gsd_x/mission/obligation.py:478 | modules/gsd_x/mission/closure.py:67 | materiality gate + transition refusal close obligations; expectation-specific closure not distinguished |
| C-52 | PROOF COMPILATION | PARTIAL | modules/gsd_x/mission/contract.py:205 | tools/gsd_x_mission.py:203 | proof_requirements reads o.proof: dormant (no producer sets proof) and latent AttributeError o.id (research A5) |
| C-53 | EVIDENCE AUTHORITY | ALREADY_IMPLEMENTED | modules/gsd_x/mission/closure.py:67 | modules/gsd_x/goal/convergence.py:268 | narrative never authority; Verdict carries gate, exit, tree_hash, gate_pin |
| C-54 | PRODUCTION REALITY GATE | ALREADY_IMPLEMENTED | modules/gsd_x/goal/convergence.py:160 | modules/gsd_x/goal/convergence.py:261 | goal REALITY plane demands in_game/live gate class at accept and at transition; mission-path production_reality is a self-declared string (closure.py:230) |
| C-55 | REALITY CONTRACT | ALREADY_IMPLEMENTED | hooks/scaffold-auditor.js:15 | hooks/hook-dispatcher.js:198 | scaffold-auditor Stop hook, block:true |
| C-56 | CROSS-DOMAIN TRANSFER | DATASET_ONLY | - | - | UNKNOWN: transfer fixtures exist only as tests (tools/test_gsd_x_mission.py:180); no runtime transfer owner |
| C-57 | EDD BENCHMARK | DATASET_ONLY | - | - | Phase 2 V-EDD-BENCH; neighbour tools/bench_gsd_x_reconstruction.py is a frozen-corpus A/B, not expectation discovery |
| C-58 | NEGATIVE CONTROLS | DATASET_ONLY | - | - | UNKNOWN: negative-control convention exists (instrument-before-claim); no EDD set |
| C-59 | MUTATE EDD ITSELF | DATASET_ONLY | - | - | Phase 3 drills; tools/mutation_drill.py:196 main exists but no EDD operator yet |
| C-60 | CONSTITUTIVE BASELINE RATCHET | REACHABLE_NOT_EFFECTIVE | modules/tower/ratchet.py:72 | tools/family_baseline.py:115 | chain verify reachable by operator CLI only; promote and donegate have no production caller (research E) |
| C-61 | BASELINE OF COMPLETENESS FOR FUTURE SOFTWARE | PARTIAL | modules/tower/families.py:88 | modules/gsd_x/cli.py:99 | family baseline injection is live but advisory; completion effect absent |
| C-62 | UKDL — THREE LEVELS | DOCUMENTED_ONLY | - | - | vault/knowledge_base/ukdl-universal.md PR-/T- ids and HARD_RULES.md exist; the HR/PR/Trap three-level split for EDD staged per D-02, not re-verified |
| C-63 | KNOWLEDGE VAULT | DOCUMENTED_ONLY | - | - | vault/incidents and vault/lessons are a file convention; no schema validator found (research E) |
| C-64 | ERROR → IMMUNITY | DOCUMENTED_ONLY | - | - | CLAE Part 30 failure-to-immunity (CLAE_PRODUCTION_GATES.md:79 Immunity Gate); no code |
| C-65 | SUCCESS → INSTINCT | DATASET_ONLY | - | - | UNKNOWN: no candidate |
| C-66 | AGENT TEAMS MODE | DATASET_ONLY | - | - | UNKNOWN: carrier agents (agent_spec.py) are a different thing from Agent Teams handoff discipline |
| C-67 | UWCP | ALREADY_IMPLEMENTED | modules/gsd_x/goal/log.py:138 | modules/gsd_x/goal/sweep.py:278 | goal event log + sweep driver |
| C-68 | LOOPS / AUTONOMOUS ONE-SHOT CONVERGENCE | ALREADY_IMPLEMENTED | modules/gsd_x/goal/sweep.py:278 | tools/gsd_x_goal.py:211 | autonomous goal sweep, cmd_autonomous |
| C-69 | CONTEXT HYGIENE | ALREADY_IMPLEMENTED | tools/tco_compact_gate.py:10 | hooks/session_start_hub.js:80 | TCO compact gate spawned at session start |
| C-70 | MICRO-COMMITS | NOT_A_SYSTEM | - | - | process instruction; carried by ROADMAP operating constraints and the concurrent-writers-shared-tree rule |
| C-71 | CONCURRENT WRITER SAFETY | ALREADY_IMPLEMENTED | tools/foreign_hunk_guard.py:5 | tools/verify_spp.py:829 | foreign hunk guard run by verify_spp |
| C-72 | NO CODE IN THIS MISSION PROMPT | NOT_A_SYSTEM | - | - | constraint on the prompt text, nothing to implement |
| C-73 | FIRST VERTICAL SLICE | NOT_A_SYSTEM | - | - | process instruction; FIRST_VERTICAL_SLICE is a Production Reality label in gsd-x-n4 resumption |
| C-74 | PRODUCER → CONSUMER → COMPLETION EFFECT | DOCUMENTED_ONLY | - | - | Mistake #38 + modules/liveness/reachability.py:725 instrument; aperture is modules/ only so tools/ is never scanned (research E1); no completion consumer |
| C-75 | DONE GATE — REQUIRED CLOSURES | REACHABLE_NOT_EFFECTIVE | tools/gsd_x_mission.py:259 | capabilities/cpp-gsd-x-mission/capability.json:64 | ship:pre gate is off by default (gsd_x_mission.enabled) and hard-wired to Windows paths (research A4) |
| C-76 | FOUNDER INTERACTION DURING THE MISSION | NOT_A_SYSTEM | - | - | process instruction; Decision Packets and DECISION_FRONTIER.md are the Phase 5 artifact |
| C-77 | REFERENCE FRONTIER AMBITION | DATASET_ONLY | - | - | UNKNOWN: no candidate |
| C-78 | META-ANALYSIS AT SESSION / EPOCH CLOSURE | DOCUMENTED_ONLY | - | - | vault/specs/uwcp.md:237 lists meta-analysis in the certification record; no code |
| C-79 | FINAL HANDOFF | NOT_A_SYSTEM | - | - | process instruction; Phase 7 writes HANDOFF.md |
| C-80 | FINAL KILL-SWITCHES | DATASET_ONLY | - | - | UNKNOWN: no candidate |
| C-81 | ULTIMATE CONSTITUTIONAL OUTCOME | NOT_A_SYSTEM | - | - | end-state statement of the mission, judged by Phase 7 |
