# Ascension: Universal Backlog-to-Capability (campaign 1) — plan of record

Owner prompt: "CLAUDE POWER PACK — UNIVERSAL CAPABILITY ASSIMILATION, AUTONOMOUS ACTIVATION & CONSTITUTIVE BASELINE RATCHET"
(pasted 2026-11-16, laptop pane 72497d57). Owner decisions, given through questions on 2026-11-16:
- Start: run phase 0b inline, then arm. Then, at 726 MB free on the laptop, the Owner said **"hazlo en la GEX44"**.
- Budget: **120M authority + 3 x 40M top-ups**, 12 cycles, 24 h, permission auto.
- Zombie missions: close only after diagnosis. The diagnosis found none, so nothing was closed (see 0b below).

## Mission laws (binding, condensed from the Owner prompt)
1. Backlog is not implementation; implementation is not activation; activation is not execution; execution is not
   correct behaviour; green tests are not Production Reality.
2. Decision order: REUSE > EXTEND > MERGE > CONNECT > GENERALIZE > BUILD. Never build another CDIO, CDICF, CCF, vault,
   skill router, backlog autopilot, memory, scheduler, evidence system, quality evaluator or baseline ledger.
3. Never turn UNKNOWN into PASS, NOT OBSERVED into ABSENT, SOURCE FOUND into IMPLEMENTED, BACKLOG ITEM into AVAILABLE,
   INSTALLED into ACTIVATED, or REGISTERED into DELIVERED. Every verifier has a positive and a negative pole.
4. Two coverage metrics, each with its own denominator: RECONCILIATION coverage (obligations whose state, owner and
   destination are proven) and OPERATIONAL CAPABILITY coverage (applicable capabilities available, reachable and verified).
   Shrinking a denominator never raises either one.
5. Constitutive Promotion Gate: classify each capability as INCIDENTAL, PRODUCT-SPECIFIC, ARCHETYPE-ENHANCING or
   CONSTITUTIVE. Promote only the last two, and only with an inheritance proof: a later equivalent build receives the
   baseline automatically, and a deliberately incomplete one is rejected.
6. Error -> immunity: every significant bug goes to the vault, and to UKDL (HR / PR / TRAP) only with transfer evidence.
7. A large phase is not a reason for ULTRA-PLAN. EXECUTION mode is the default. Use PLAN mode only for the
   reconciliation-ledger home decision.
8. Kill switches block the affected action only, never all independent work.

## Reality Scan (laptop, 2026-11-16, HEAD 2f9386f6 feature/knowledge-acquisition)
- Owners that exist: modules/backlog_autopilot (engine, tracked, stop1_queue); modules/capability_runtime (applicability,
  agent_resolver, agent_spec, retirement, corpus_adapter, enrichment, invocation); modules/cdio (scorer,
  componentry_catalog, motion_patterns, legal_surface, bus_bridge, telemetry); modules/ccf (artifact_compiler,
  release_manager, evaluation_engine, trademark_scanner, cli, test_ccf). 102 modules in total.
- Taste Skill: `design-taste-frontend` IS installed in the LAPTOP ~/.claude/skills. Reachability, activation and
  consumer are UNKNOWN. That is a laptop-plane fact.
- Hypotheses still UNKNOWN: CCF artifact-integrity defects, Design Index refresh, ASTRYX / branding / Anime.js / 21
  design resources in the backlog, a constitutive-baseline module (possibly on branch ucr-cif/construction).
- Phase 0b (supervisor hygiene) is DONE on the laptop:
  - 46 "non-terminal" missions turned out to be parked holds with recorded reasons (cost hold, authority exhausted,
    age budget, Owner hold), and ORPHANED is already terminal. No supervisor defect was reproduced, and nothing was
    closed.
  - Residual: `gsd_mission.py status` shows `state: RUNNING` for parked missions, which is misleading. Phase 2
    candidate.
- The laptop tree has 2542 foreign dirty paths, so it is not the mission's base. The base is the committed HEAD
  2f9386f6.

## Plane
The mission runs on GEX44 in clone `~/missions/ascension`, worktree `.claude/worktrees/ascension`, branch
`mission/ascension-run`. Laptop-plane facts (laptop ~/.claude skills, hooks and settings, the laptop Claude Code)
cannot be judged on GEX44. Write them as numbered entries in `vault/programs/ascension/LAPTOP_STEPS.md` and mark them
BLOCKED-ON-LAPTOP.
