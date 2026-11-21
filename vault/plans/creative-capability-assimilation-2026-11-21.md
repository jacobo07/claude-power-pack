---
covers: [creative-capability, magicui, design-discovery, design_index, design_route, cdicf-selection, visual-materials]
tier: T2
status: AWAITING_OWNER_APPROVAL
created: 2026-11-21
---
# Creative Capability Assimilation & Magic UI Coverage — plan (durable backup of the inline plan)

## Reality Scan (HEAD 734bde95, branch feature/knowledge-acquisition, dirty tree owned by other sessions)
- Reference commit ddde1a22 does NOT exist in this repo: historical figures unverifiable against it.
- Magic UI in CPP = licence evidence only: LICENCE_PROBE (MIT), MAGICUI_REGISTRY_SCAN (80 registry files @ b0b2e497, 0 per-file markers). ZERO capability records, ZERO index rows, no installed magicui skill in ~/.claude/skills, no MCP.
- design_index (/cpp-design): 165 rows = 10 systems x the SAME 15 generic patterns (150, near-duplicates) + 15 "Power Pack" rows. visual-patterns holds ~95 pattern files (57 componentry-*), so ~80 are invisible to retrieval.
- CDICF component index: `--components-status` -> NO_INDEX (exit 30). Selector has nothing to select. Manifests: 2 examples (shadcn button, react-bits split-text as SOURCE_AVAILABLE_RESTRICTED gateway).
- Automatic activation (hooks/hook-dispatcher -> tools/design_route_prompt.py) injects skill names + Stop-gate checks only; it never retrieves candidates. /cpp-design runs only when invoked.
- Measured miss: query "hero looks flat, needs ambient light and depth" -> #1 Text Bevel, #3 Adaptive Favicon (BM25 matched "light" in "light and dark mode"). Magic UI Light Rays/Backlight/Dither not reachable.
- bcap-2 Phase 8 built 12 pure modules (source_intake, reference_intel, source_route, component_meta, motion_select, component_install...) all "not wired" — reuse them, do not rebuild.

## Confirmed causes (each reproduced above)
1. Catalog absent (Magic UI never inventoried as capabilities). 2. Index incomplete (80+ VP patterns unindexed) and noisy (150 duplicate generic rows). 3. Retrieval is lexical, no need vocabulary. 4. Activation never retrieves. 5. CDICF index never built. 6. Selection modules unwired.
Refuted/unknown: licence is NOT a blocker for Magic UI free repo (MIT, pinned). Skill-superficiality: N/A (no skill installed).

## Owners (no new subsystem)
inventory = visual-patterns catalog + CDICF manifests; retrieval = tools/design_index.py; eligibility/licence = modules/cdicf/source_intake.admit_code + source_route.select; composition = component_meta.composition_qa; art direction/abstention = CDIO (design_route + experience contract); activation = design_route_prompt.py; verification = playwright (vendored) + modules.cdio.taste + cdio-reviewer.

## Microcommits
M1 benchmark-first: tools/test_design_discovery.py, 10 frozen scenarios A-J, recall@5 / precision@5 / abstention / licence; record baseline (expected red).
M2 Magic UI catalog from registry.json @ pinned SHA: one record per component, examples as variants; need tags, fits, contraindications, cost/motion/a11y, deps, licence pin; annotation status honest (ANNOTATED vs REGISTRY_ONLY).
M3 design_index: ingest catalog + ALL VP files; collapse 150 duplicate generic rows to 15 with multi-source list (consumers checked first).
M4 need-aware ranking + eligibility filters (licence, motion budget, perf, trust-critical) + ABSTAIN; extend source_route/reference_intel.
M5 activation: design_route_prompt emits <=5 candidates with why/contraindication or an explicit abstain line, bounded bytes; silent off-visual.
M6 vertical proof: Scenario A fixture page with one selected Magic UI capability, rendered in Chromium (screenshot, console errors, reduced-motion, contrast, long tasks), Taste lint, cdio-reviewer.
M7 other libraries in ROI order with pinned licence reads (React Bits stays gateway; Paper Shaders licence to verify).
M8 composition QA in the candidates path (one ambient-motion layer, attention budget, perf).
M9 mutation drills + aggregate gate tools/test_creative_capability.py; liveness; UKDL traps; baseline candidate; fresh-agent proof; handoff.

## Rollback
Each microcommit reverts alone; activation behind CPP_DESIGN_ROUTE / new CPP_DESIGN_CANDIDATES=off kill switch.
