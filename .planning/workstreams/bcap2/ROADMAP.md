# Roadmap: bcap2 (BCAP-2 — absorb the 9 open absorption backlogs)

Authority: `vault/plans/bcap-2-absorption-2026-11-19.md`. Read it first, then each phase's backlog file in `vault/backlog/`
(that file is the phase spec). Campaign 1 (`vault/plans/ascension-backlog-capability-2026-11-16.md`,
`vault/programs/ascension/bcap-1/HANDOFF.md`) already built the inventory, ledger, webslice, CCF integrity and promotion
gate: use them, do not rebuild them.

PLANE: **GEX44**. You run in `~/missions/bcap2/.claude/worktrees/bcap2`, branch `mission/bcap-2-run`. Never call
EnterWorktree. Commit with the repo-local identity, one causal delta per commit. Do NOT push. Use Bash (Linux), python3.
**Never touch GEX44's live `~/.claude` or `~/.claude/skills/claude-power-pack`** (agora-mission-sweep runs that tree).
Laptop-plane items go to `vault/programs/bcap-2/LAPTOP_STEPS.md`, numbered, copy-pasteable, BLOCKED-ON-LAPTOP; then continue.

EXECUTION mode. Plan each phase inline. Do NOT dispatch gsd-planner or gsd-phase-researcher. At most 2 bounded subagents.
Each phase: Reality Scan of the spec's named owners first (one discriminating experiment, not a mass test run) ->
REUSE/EXTEND/CONNECT/DECLINE ledger written to `vault/programs/bcap-2/<item>/REUSE_LEDGER.md` -> minimal implementation in
the existing owner -> gate `tools/test_bcap2_<item>.py` driven from both poles (seeded failure caught, clean case passes)
-> liveness (`python3 modules/liveness/reachability.py`: wire or declare every new module) -> ledger row updated with
exit-0 evidence -> backlog file Status line + `vault/plans/deferred-backlog.md` row updated with the closing commit.
After each phase record spend (`python3 tools/mission_spend.py session-tree --session <sid>` or UNMEASURED) and a 5-line
meta-analysis in STATE.md. UNKNOWN or UNMEASURED is never PASS. Two materially identical failures = pivot the method.
If a phase hits its ceiling: commit what is proven, mark the item PARTIALLY_PROVEN with named residuals, move on.

## Phases

- [ ] **Phase 1: CPP-DBG-001 causal bug diagnosis.** Spec `2026-10-11_diagnosing-bugs-causal-proof-ratchet.md`. Extend
  CRAIF/OSR/instrument-before-claim/done_gate, no new debugging OS. Contracts DBG-C01..C08; the 20 adversarial fixtures are
  the gate's poles (cover at least the 12 the host can run; name the rest). One real historical CPP bug reproduced by a
  red-capable loop. Automatic routing on "broken/fails/slow/regression" without naming the skill. Ceiling 14M.
- [ ] **Phase 2: CPP-TDD-001 evidence-first TDD.** Spec `2026-10-11_tdd-evidence-first-vertical-slice-ratchet.md`.
  Extend test-gaps / mutation ratchet / done_gate; share the regression seam with Phase 1 without conflating owners.
  Ceiling 12M.
- [ ] **Phase 3: CPP-AGSK-001 Addy Osmani agent skills, selective.** Spec
  `2026-10-11_addyosmani-agent-skills-selective-absorption.md`. Pin upstream commit + licence; classify each skill
  ALREADY OWNED / EXTEND / CONDITIONAL / REJECT; absorb only EXTEND items into existing skills (latent-card + JIT, never
  always-on). Ceiling 12M.
- [ ] **Phase 4: Anime.js into PP Design.** Spec `2026-10-10_animejs-design-absorption.md`. Owner: modules/cdio motion
  (CDIO-11 componentry, motion_patterns) + CDIO-07 experience contract (reduced-motion floor is CRITICAL). Ceiling 10M.
- [ ] **Phase 5: Synsation UX interaction patterns.** Spec `2026-10-13_synsation-ux-patterns-absorption.md`. Owner:
  vault/knowledge_base/cdio + modules/cdio. Ceiling 10M.
- [ ] **Phase 6: CDIO modern SaaS styles.** Spec `2026-10-02_cdio-modern-saas-styles.md`. Finish from the PROVISIONAL F1
  variant (97d08474); all three styles as selectable, scored CDIO styles. Ceiling 8M.
- [ ] **Phase 7: Brand Identity & Logos.** Spec `2026-10-21_cdio-brand-identity-logo-absorption.md`. Owner modules/ccf
  (campaign 1 fixed D1-D5; residuals: PDF embeds a hash not the image, trademark scanner low recall). Evidence-gated
  GitHub absorption per the spec's release gates. No paid provider calls (fake provider in tests). Ceiling 14M.
- [ ] **Phase 8: 21 design resources, universal absorption.** Spec
  `2026-10-30_cdio-21-design-resources-universal-absorption.md`. All 36 falsification gates as poles of
  `tools/test_bcap2_design21.py`; licence per resource; principles-only where the licence forbids code. Ceiling 18M.
- [ ] **Phase 9: CPP-RUFLO-001 secure absorption + hardened install.** Spec
  `2026-10-11_ruflo-security-absorption-sovereign-updates.md`. Order is binding: (a) passive source/metadata review at the
  pinned baseline and current release; (b) every HOLD gets a CPP-owned correction with a RED->GREEN gate; (c) only then
  install the hardened version in an isolated sandbox per plan law 6, and run its smoke there; (d) laptop activation =
  LAPTOP_STEPS entry with the exact commands. A HOLD that cannot be corrected keeps the install refused.
  INPUT (Owner 'si', 2026-11-19): read `vault/programs/bcap-2/ruflo-research/informe_carencias_ruflo.md` first (notes beside it). It updates the spec's HOLD list: v3.78.0 (2026-11-19); 8 GitHub advisories of 2026-11-05 (1 critical browser_open flag injection, 4 high, 3 moderate) + open #3294 (MCP session cross-client), #4750 (unsigned pattern downloads), #3157 (deps), unsandboxed plugins, opt-in MCP policy, no npm provenance attestation, @claude-flow/swarm not republished in 3.78.0. Each is a HOLD for step (b). Its 8 prioritized gaps (verification oracle, task-level A/B eval, review-queue/batch control, deploy safety, intent escalation, file-ownership partition, supply-chain defense, token budget) are what the CPP overlay must add; map each to Phases 1-2 owners where they already exist instead of rebuilding. Ceiling 16M.
- [x] **Phase 10: Closeout.** `vault/programs/bcap-2/done_gate.py` (aggregates the nine gates + liveness + ledger),
  UKDL/vault deltas scoped honestly, HANDOFF.md with per-item verdict. Ceiling 6M.

## Phase Details

### Phase 1: CPP-DBG-001 causal bug diagnosis
**Goal**: close BCAP2-01 per plan law 4.
**Depends on**: nothing. Requirement BCAP2-01.

### Phase 2: CPP-TDD-001 evidence-first TDD
**Goal**: close BCAP2-02 per plan law 4.
**Depends on**: Phase 1 (shares its regression seam). Requirement BCAP2-02.

### Phase 3: CPP-AGSK-001 Addy Osmani agent skills, selective
**Goal**: close BCAP2-03 per plan law 4.
**Depends on**: nothing. Requirement BCAP2-03.

### Phase 4: Anime.js into PP Design
**Goal**: close BCAP2-04 per plan law 4.
**Depends on**: nothing. Requirement BCAP2-04.

### Phase 5: Synsation UX interaction patterns
**Goal**: close BCAP2-05 per plan law 4.
**Depends on**: nothing. Requirement BCAP2-05.

### Phase 6: CDIO modern SaaS styles
**Goal**: close BCAP2-06 per plan law 4.
**Depends on**: Phases 4-5 when present. Requirement BCAP2-06.

### Phase 7: Brand Identity & Logos
**Goal**: close BCAP2-07 per plan law 4.
**Depends on**: nothing. Requirement BCAP2-07.

### Phase 8: 21 design resources, universal absorption
**Goal**: close BCAP2-08 per plan law 4.
**Depends on**: Phases 4-5 when present. Requirement BCAP2-08.

### Phase 9: CPP-RUFLO-001 secure absorption + hardened install
**Goal**: close BCAP2-09 per plan law 4.
**Depends on**: nothing. Requirement BCAP2-09.

### Phase 10: Closeout
**Goal**: close BCAP2-10 per plan law 4.
**Depends on**: Phases 1-9. Requirement BCAP2-10.
