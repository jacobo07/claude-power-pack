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
  LAPTOP_STEPS entry with the exact commands. A HOLD that cannot be corrected keeps the install refused. Ceiling 16M.
- [ ] **Phase 10: Closeout.** `vault/programs/bcap-2/done_gate.py` (aggregates the nine gates + liveness + ledger),
  UKDL/vault deltas scoped honestly, HANDOFF.md with per-item verdict. Ceiling 6M.

## Phase Details
Phases 1-9 are independent of each other except: Phase 2 reuses Phase 1's regression seam; Phase 6 and 8 reuse Phase 4-5
CDIO additions when present. Phase 10 depends on 1-9. Requirements BCAP2-01..10 map one-to-one to phases.
