# Roadmap: creative-cap (Creative Capability Assimilation & Magic UI Coverage)

Authority: `vault/plans/creative-capability-assimilation-2026-11-21.md` (Owner-approved 2026-11-21, "Approve as written").
Read it first: its Reality Scan is the measured baseline.
Owner done-gates (each needs an executable check with an observed exit code; unrun = not PASS): G1 Magic UI reality
reconciled + causes named + measured discovery gain; G2 traceable inventories, uninvestigated = pending; G3 licence
compliance per resource and distribution mode; G4 discovery without library names; G5 selector differs by context and
abstains; G6 real implementation; G7 render quality + identity kept; G8 perf + a11y; G9 negative tests; G10 seeded
mutations caught; G11 evidence from the real path; G12 UKDL/Knowledge Vault; G13 constitutive baseline wired to consumers;
G14 fresh-agent test; G15 microcommits; G16 honest spend; G17 no false completion; G18 recoverable handoff.
Principle: absorption != availability != discoverability != selection != implementation != verified quality != inheritance.
NO FORCED EFFECTS: the absence of an effect must be able to win.

PLANE: **GEX44** (Linux; laptop refused the arm at 1.6 GB free RAM, Owner "do it on GEX44"). You run in the mission clone
`~/missions/creative-cap` (or its `.claude/worktrees/<name>` on your own `mission/creative-cap-run` branch). Never call
EnterWorktree. Commit with the repo-local identity, one causal delta per commit, pathspec commits only. Do NOT push
(the laptop fetches your branch). Use Bash and python3. **Never touch GEX44's live `~/.claude` or
`~/.claude/skills/claude-power-pack`** (agora-mission-sweep runs that tree). Gates that read `~/.claude/` settings or live
hooks judge GEX44's install, not the laptop's: prove hook behaviour by driving the repo's hook script directly
(stdin JSON -> stdout). If real Chromium is unavailable here (check `python3 -c "import playwright"` and a headless
launch), Phase 6 render steps go to `vault/programs/creative-cap/LAPTOP_STEPS.md`, numbered, copy-pasteable,
BLOCKED-ON-LAPTOP; then continue.

EXECUTION mode. Plan each phase inline. Do NOT dispatch gsd-planner or gsd-phase-researcher. At most 2 bounded subagents.
REUSE, never rebuild: `tools/design_index.py` (retrieval), `modules/cdicf/{source_intake,source_route,reference_intel,
component_meta,motion_select,component_install}.py` (licence/eligibility/composition; built by bcap-2, unwired),
`modules/cdio/design_route.py` + `tools/design_route_prompt.py` (automatic activation hook), `vault/knowledge_base/
visual-patterns/` (pattern corpus), `modules/cdio/taste.py`, `tools/design_review_record.py`, vendored playwright
(`skills/motion-promo/scripts/check_toolchain.py`). Evidence of Magic UI licence: `vault/programs/bcap-2/design-resources/
{LICENCE_PROBE,MAGICUI_REGISTRY_SCAN,LICENSE_PINS,SOURCES}.json`.
Each phase: one discriminating experiment first -> minimal change in the existing owner -> gate driven from both poles
(seeded failure caught, clean case passes) -> liveness (`python modules/liveness/reachability.py`; wire or declare every
new module) -> commit with evidence -> STATE.md section (gate command + exit, measured numbers with the command, spend or
UNMEASURED, 5-line meta-analysis). UNKNOWN/UNMEASURED is never PASS. Two materially identical failures = pivot the method.
Self-authored fixtures measure retrieval logic, NOT real-world taste: say so wherever a number is reported.
External fetches: read-only, pinned SHA, licence bytes hashed; never vendor restricted code (React Bits = gateway only,
Magic UI Pro is not the free repo, Motion Primitives has no LICENSE file -> UNVERIFIED).
Owner budget: ~220k net tokens guidance (orientative). Stop and name it in one line if it is clearly exceeded.

## Phases

- [ ] **Phase 1: M1 discovery benchmark first.** `tools/test_design_discovery.py`: 10 frozen scenarios A-J (premium dark
  software, warm local cafe, luxury real estate, minimal institutional, creative portfolio, mobile perf constraint, existing
  brand preservation, negative selection, library-name blindness, licensing constraint) as fixtures with expected
  relevant / forbidden / abstain sets. Measure recall@5, precision@5, abstention correctness, licence compliance against
  TODAY's `design_index --search`. Record the baseline numbers in STATE.md (expected red; the gate must be able to run
  in a baseline mode that reports without failing, and a target mode used from Phase 4 on).
- [ ] **Phase 2: M2 Magic UI capability catalog.** Read-only fetch of the upstream registry (registry.json or
  apps/www/registry*) at a pinned SHA. Generate `vault/knowledge_base/visual-patterns/catalog/magicui.json` by a script
  (`tools/catalog_magicui.py`), one record per component; examples are variants, not capabilities. Fields: id, title,
  upstream path, pin, licence pin, need tags, fits, contraindications, cost tier, motion level, a11y/reduced-motion,
  deps, annotation_status ANNOTATED|REGISTRY_ONLY. Hand-annotate the strongest ~30 (light rays, backlight, dither, progressive
  blur, noise texture, warp background, border beam, highlighter, hero video dialog, animated beam, magic card,
  flickering grid, particles, grid patterns, text motion, image treatments, CTA effects...). Gate: count == upstream at pin.
- [ ] **Phase 3: M3 index repair.** design_index ingests the catalog AND every visual-patterns file (today 15 of ~95);
  collapse the 150 duplicate generic rows (10 systems x same 15 patterns) to 15 rows with a multi-source list after
  grepping every consumer of design_index rows/tests. Gate: every VP file and catalog record indexed; /cpp-design timing
  bounds still pass.
- [ ] **Phase 4: M4 need-aware ranking + eligibility + abstention.** Need vocabulary (flat->depth/lighting/texture,
  more human/warm->warmth/editorial/paper, premium dark->ambient glow...), hard pre-filters (licence via
  source_intake.admit_code, motion budget from DESIGN.md experience, perf/mobile, trust-critical) and ABSTAIN. Extend
  existing modules. Gate: benchmark target mode beats Phase-1 baseline on recall@5 AND precision@5; D and H abstain or
  pick minimal; J refuses the restricted best match and offers a legitimate alternative.
- [ ] **Phase 5: M5 automatic activation.** design_route_prompt adds <=5 candidates (why + contraindication) or an explicit
  abstain line; byte bound; silent on non-visual prompts; kill switch CPP_DESIGN_CANDIDATES=off; latency measured under
  the 6 s hook timeout. Prove through the real hook entry (stdin JSON -> stdout), visual and non-visual poles; extend
  tools/test_design_route.py.
- [ ] **Phase 6: M6 Magic UI vertical proof.** Scenario A fixture page (static HTML under
  vault/programs/creative-cap/fixtures/) using ONE capability the old path did not surface, implemented from the MIT source
  with attribution. Real Chromium via vendored playwright: screenshot (look at it), console errors, prefers-reduced-motion,
  contrast of text over the effect, long tasks. Taste lint no critical; cdio-reviewer verdict recorded via
  design_review_record.py. Evidence in vault/programs/creative-cap/.
- [ ] **Phase 7: M7 best-of-each libraries.** In ROI order with pinned licence reads: Motion, tsParticles, Vanta, OGL,
  ShaderGradient, css-doodle, Paper Shaders (verify licence terms), grainy-gradients, gradient-backdrops, Pixerate flair,
  background-lab, animation-handbook (knowledge), UI Layouts, React Bits (gateway only), Motion Primitives (UNVERIFIED).
  Each gets a disposition (ADOPT/EXTEND/CONNECT/REFERENCE/REIMPLEMENT/BENCHMARK/QUARANTINE/REJECT) and catalog records
  only where retrieval value is shown. Specialty matrix in vault/programs/creative-cap/SPECIALTY_MATRIX.md.
- [ ] **Phase 8: M8 composition intelligence.** In the candidate path: at most one ambient-motion layer, attention and
  perf budget, redundancy, "no effect" can win. Gate: scenarios A, B, C, E get visibly different selections (pinned).
- [ ] **Phase 9: M9 hardening + ascension + handoff.** Mutation drills on retrieval/filters/activation (each caught);
  aggregate gate `tools/test_creative_capability.py` (all phase gates + liveness); UKDL traps/process rules via the
  existing UKDL file (search equivalents first); BASELINE_CANDIDATES.json entry if earned; fresh-agent proof (one
  subagent given only a brief, observe it retrieve and select); HANDOFF.md in vault/programs/creative-cap/ with the
  Owner's two-layer handoff; plan file status updated.

## Phase Details

### Phase 1: M1 discovery benchmark first
**Goal**: CC-03 baseline measured — tools/test_design_discovery.py runs 10 frozen scenarios A-J against today's index.

### Phase 2: M2 Magic UI capability catalog
**Goal**: CC-01 — catalog/magicui.json generated from the pinned upstream registry, count equals upstream.

### Phase 3: M3 index repair
**Goal**: CC-02 — every visual-patterns file and catalog record indexed; duplicate generic rows consolidated.

### Phase 4: M4 need-aware ranking + eligibility + abstention
**Goal**: CC-03/CC-04 — benchmark target mode beats the Phase-1 baseline on recall@5 and precision@5; D/H abstain; J refuses.

### Phase 5: M5 automatic activation
**Goal**: CC-05 — design route hook injects candidates or abstain on visual prompts only, proven through the real hook entry.

### Phase 6: M6 Magic UI vertical proof
**Goal**: CC-06 — one selected Magic UI capability rendered and verified in real Chromium with persisted evidence.

### Phase 7: M7 best-of-each libraries
**Goal**: CC-07 — every listed library dispositioned with a pinned licence read; SPECIALTY_MATRIX.md.

### Phase 8: M8 composition intelligence
**Goal**: CC-08 — composition budget in the candidate path; A, B, C, E get different pinned selections.

### Phase 9: M9 hardening + ascension + handoff
**Goal**: CC-09 — mutation drills caught, tools/test_creative_capability.py exit 0, UKDL, fresh-agent proof, HANDOFF.md.
