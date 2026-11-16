# Roadmap: ascension (campaign 1 — Universal Backlog-to-Capability)

Authority: `vault/plans/ascension-backlog-capability-2026-11-16.md`. Read it first. Do NOT re-scan what its Reality Scan already
states; verify it only where a phase depends on it. EXTEND existing owners (backlog_autopilot, capability_runtime, cdio, ccf,
baseline_ledger, UKDL, liveness). Never create a parallel system.

PLANE: **GEX44** (Owner "hazlo en la GEX44", 2026-11-16; the laptop had 726 MB free). You run in
`~/missions/ascension/.claude/worktrees/ascension`, branch `mission/ascension-run`. Never call EnterWorktree. Commit with the
repo-local identity, one causal delta per commit. Do NOT push. Use Bash (Linux). The laptop coordinator fetches your branch.
**Never touch GEX44's live `~/.claude` or `~/.claude/skills/claude-power-pack`**: agora-mission-sweep runs that tree.
Laptop-plane items go to `vault/programs/ascension/LAPTOP_STEPS.md` as numbered, copy-pasteable entries, marked
BLOCKED-ON-LAPTOP. Then continue with independent work.

EXECUTION mode. Plan each phase inline. Do NOT dispatch gsd-planner or gsd-phase-researcher. At most 2 bounded subagents.
Before every phase, use a discriminating experiment first, not a mass test run. After each phase:
- Measure your own spend (`python tools/mission_spend.py session-tree --session <sid>`) and record it in STATE.md, or record
  UNMEASURED.
- Write a 5-line meta-analysis in STATE.md: wrong assumptions, unreachable knowledge, determinism gained, UNKNOWN, next.

UNKNOWN or UNMEASURED is never PASS. Every gate you write must be driven from both poles: a seeded positive that it catches,
and a clean case that passes. Two materially identical failures mean you pivot the method; never try a third time.

## Phases

- [ ] **Phase 1: Obligation inventory.** Deterministic discovery of obligations from what EXISTS: vault/backlog, vault/plans
  (pending and approved-unexecuted), OWNER_QUEUE, handoffs and RESUMPTION files, audits, vendor/skills and skills/, commands,
  agents, capability_runtime registry, liveness registry PLANNED entries, and historical absorption programmes (seeds: Taste
  Skill, Meta ASTRYX, Brand Identity & Logos, 21 design resources, Anime.js, Synsation UX, UI/UX Pro Max, Addy Osmani agent
  skills, Design Index, CCF). Extend backlog_autopilot (tracked.py or engine.py). Output: a reproducible inventory artifact
  plus a tool. Gate: a seeded omitted obligation makes the gate FAIL, and a semantic duplicate collapses to one identity.
  Ceiling 20M.
- [ ] **Phase 2: Reconciliation ledger.** For each obligation: canonical id, provenance, owner, existing implementation,
  entrypoint, real consumer, tests, execution evidence, license, next action, close or retire condition. Use the existing
  epistemic states. Map onto CPP's contract; do not invent an enum. Report RECONCILIATION coverage and OPERATIONAL CAPABILITY
  coverage with independent denominators. Also fix the misleading `gsd_mission status` label: show a parked or held mission
  as parked, not RUNNING. Do this RED -> GREEN in test_gsd_mission. Gate: a seeded false absorption (a name in a dataset,
  no code) is REJECTED; a blocked item cannot vanish from the denominator. Ceiling 25M.
- [ ] **Phase 3: Web vertical slice.** Build or modify a REAL small web surface: a repo fixture under a sandbox dir, rendered
  in headless Chromium on GEX44. Use the flow: intent -> product type -> existing identity -> DESIGN.md (experience contract)
  -> capability_runtime.applicability selection -> CDIO componentry/motion/legal_surface -> license check -> build -> real
  render -> interaction check -> CDIO scorer verdict -> Production Reality check. Mandatory cases, each with an observed
  verdict:
  - a useful resource selected;
  - an unsuitable one rejected;
  - a backlog-only resource NOT announced as available;
  - an installed-but-unreachable skill detected;
  - an incompatible license refused;
  - a technically incompatible dependency refused;
  - `expressiveness: none` honoured;
  - an existing design system not overwritten;
  - a too-close-to-a-brand reference refused;
  - a tool that reports success without its artifact caught;
  - a green test over broken behaviour caught;
  - a feature a fresh agent cannot discover flagged.
  Gate: one done_gate command that exercises all of them from both poles. Ceiling 30M.
- [ ] **Phase 4: CCF integrity.** Re-audit with current evidence: real bytes kept, artifact manifest, generated logo ==
  published kit, risk block before provider invocation, positive evidence before a publish state. If a defect is already
  fixed, prove it and do not re-implement. If it is present: reproduce, RED, fix in the existing owner, GREEN, regression.
  No paid provider calls. Ceiling 12M.
- [ ] **Phase 5: Constitutive Baseline Ratchet + inheritance.** Run the Phase-3 deltas through the Constitutive Promotion
  Gate. Promote only ARCHETYPE-ENHANCING or CONSTITUTIVE items, through the existing baseline owner (locate it first:
  baseline_ledger / ucr-cif / UKDL). Inheritance proof: a fresh `claude -p` agent (~/.local/claude-lf1, stdin </dev/null),
  given only normal institutional context, builds a second equivalent web surface. It discovers the baseline, the done-gate
  rejects a deliberately incomplete variant, and it passes the correct one. Ceiling 20M.
- [ ] **Phase 6: Immunity, liveness, closeout.** Route the incidents found to the vault and UKDL candidates (HR/PR/TRAP),
  scoped honestly. Run `python modules/liveness/reachability.py` and wire, declare or delete every new module. Write the
  global `vault/programs/ascension/done_gate.py --campaign 1` (aggregates the phase gates) and HANDOFF.md (Owner summary +
  engineering handoff per the plan's §30). Mark campaign 1 COMPLETE only if every in-scope gate passes; otherwise mark it
  PARTIALLY PROVEN with the exact residual. Ceiling 13M.

## Phase Details

### Phase 1: Obligation inventory
**Depends on**: nothing. Requirement ASC-01.

### Phase 2: Reconciliation ledger
**Depends on**: Phase 1. Requirement ASC-02. PLAN mode only for where the ledger lives; recommended: extend
backlog_autopilot/tracked.py.

### Phase 3: Web vertical slice
**Depends on**: Phase 2 (uses the ledger to tell available from backlog-only). Requirement ASC-03.

### Phase 4: CCF integrity
**Depends on**: nothing (runs after Phase 3 by order). Requirement ASC-04.

### Phase 5: Constitutive Baseline Ratchet + inheritance
**Depends on**: Phase 3. Requirement ASC-05.

### Phase 6: Immunity, liveness, closeout
**Depends on**: Phases 1-5. Requirement ASC-06.
