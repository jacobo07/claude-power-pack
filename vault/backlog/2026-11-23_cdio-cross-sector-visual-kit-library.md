# CDIO-CVK-001 — Cross-Sector Visual Kit Library and Autonomous Retrieval

**Date:** 2026-11-23 (Europe/Madrid). **Status:** SEED DATASET CREATED / AUTOMATED INTEGRATION NOT IMPLEMENTED / REFERENCE_ONLY.
**Owner request:** source more visual kits akin to the November 22 Instagram brand-palette/hero/kitchen configurator examples, then build a cross-sector library that CPP/CDIO can use autonomously for visual/brand/site projects.
**Initial seed:** [46 provenance-first references](../knowledge_base/visual-patterns/datasets/CDIO_CROSS_SECTOR_VISUAL_KITS_SEED_2026-11-23.jsonl) — 31 specific case studies and 15 research/source directories. These are URL/descriptor entries only, **not** downloaded images, brand assets, licensed kits, validated design systems or runnable product patterns. All license states default to REFERENCE_ONLY_LICENSE_NOT_VERIFIED_FOR_COPY; all review states DISCOVERY_ONLY.
**Institutional owner:** existing CDIO-06 visual direction, visual-patterns KB, existing `tools/design_index.py` FTS5/registry, CCF/Visual DNA and DESIGN.md (approved project tokens), CDICF (assets and licensed code), actual browser QA and UKDL/Constitutive Baseline Ratchet. Do not duplicate index/database, second CDIO evaluator or UI design OS.
**Dependencies:** [CGVI-001](2026-11-22_cdio-context-grounded-visual-intelligence-authentic-art-direction.md), [VRK-001](2026-11-22_cdio-color-art-direction-kitchen-web-configurator-reverse-engineering.md), [D21 21-source intake](2026-10-30_cdio-21-design-resources-universal-absorption.md) and existing brand identity backlog.
**Evidence scope:** source links and case-study descriptions were retrieved through public web results on 2026-11-23. Individual authors' descriptions of their work are self-reported, and there are no claims that those designs were tested for accessibility, conversion, mobile performance or shipped code. Dynamic source size and available access can change.

## North Star

User: "Build a website for a US kitchen remodeling company."
CPP: recognizes sector + job, inspects actual business facts and brand constraints, retrieves diversified case studies and compatible visual patterns, produces **original** evidence-grounded art direction, respects real client photos and rights, builds the site, runs a rendered QA/functional review, repairs observed problems and captures a reusable technique.
User does **not** need to remember any search, critique, palette, layout, or QA command.

## Distinguish four different library objects

1. **SOURCE:** Directory/source API or gallery; not itself a design kit.
2. **REFERENCE:** A designer's published case study; can inspire analysis but grants no reuse license.
3. **PATTERN:** Original abstracted and independently reproducible recipe with source provenance, applicability, when-not-to-use, and original fixtures.
4. **DEPLOYABLE KIT:** Approved original/cleared assets plus coherent DESIGN.md-compatible design system, components, implementation and rendered evidence, with clear rights and licensing.

Never promote SOURCE/REFERENCE directly to DEPLOYABLE KIT. A URL is not proof of access to a source asset, and a screenshot is not proof of an operational website.

## Multi-axis classification — sectors are not styles

**Sector axes (initial):** kitchen/cabinetry/remodeling, construction/roofing, solar/energy, real estate/hospitality properties, restaurant/food/cafe, beauty/wellness, legal/professional, healthcare, education, SaaS/enterprise, homewares/retail. The 31 case-study records currently contain granular sector strings; normalize to umbrellas and subsegments when building the consumer.

**Independent style axes:** photo-led, expressive typographic, editorial, architectural minimal, warm artisanal, playful, technical, cinematic, high contrast, restrained, environmental, product visualizer. Avoid suggesting that any sector has one required palette/theme. The specific palette roles from VRK-001 can be considered, but 60/30/10 is a heuristic not an enforced percentage.

**Experience/job axes:** attract leads, book consultation, display real work, compare finishes, explore configurator, request quote, place an order, explain services, build trust, navigate an operational app. An art direction is judged by its fit to the actual job, brand and evidence.

## Existing owners observed in repository

- `tools/design_index.py`: existing SQLite FTS5 design-pattern index with 10 systems × 15 categories; extend its existing schema/consumer or its documented authority, no unrelated parallel search service.
- `vault/knowledge_base/visual-patterns/README.md`: pattern entries require explicit "Cuando NO usar"; higher evidence/proof status than a source URL is needed for promotion.
- `modules/cdio/rendered_checks.py`: source currently documents warning-only candidate checks for motif repetition, pictograms, section monotony, art provenance; do not claim a production-blocking visual gate.
- Existing `CGVI-A00..A13` contains the autonomous source-selection and render/review/repair architecture; this subprogram is a curated reference dataset and proof of source-to-consumer usage, not another autonomous runtime.

## P0 — Build a real reusable index before increasing volume

- [ ] **CVK-00:** Reality Scan exact HEAD/workspaces/installed hooks/index ownership, current source intake and overlap with D21/CGVI.
- [ ] **CVK-01:** Verify the 46 seed URLs, authorship, update dates, subtype tags, source availability, robot/ToS and any explicit licensing. Preserve UNKNOWN.
- [ ] **CVK-02:** Define the versioned reference schema: identity, permalink, source, real-vs-concept status, sector+subsector, target job, visual composition, typography, palette roles with evidence, real media usage, motion, interaction, negative applicability, legal rights, access/update time and reviewer proof. Keep observed vs inferred distinct.
- [ ] **CVK-03:** Map references to the existing visual-patterns KB and CDIO/design-index consumers, dedupe same projects across aggregators/creators, and route metadata through the existing query API (prefer FTS5 as baseline; embeddings optional with measurable retrieval ROI).
- [ ] **CVK-04:** Implement conservative source acquisition: permitted APIs (e.g. Are.na with authenticated permissions and premium search limitation), owner-approved/manual URLs and link-only curated discovery. Do not bulk mirror Behance, Pinterest, reels, brand logos or unlicensed videos.
- [ ] **CVK-05:** Manual and/or independently supported art-direction annotations for a small high-quality subset; per entry require one transferable mechanism, one counterexample, clear evidence and a target user decision.
- [ ] **CVK-06:** Implement sector-aware diversified retrieval, explicit reasons for including or skipping sources and proof of retrieving relevant references automatically from an ordinary design mission. Avoid overfit to one style or globally picking cinematic/dark.
- [ ] **CVK-07:** Compile selected patterns into a **proposal** that respects existing approved CCF Visual DNA/DESIGN.md, not an overwrite. Generate only original or cleared assets and explain any abstention.
- [ ] **CVK-08:** Build original demonstration fixtures across 6+ sectors, render desktop/mobile and assess identity fit, accessibility, functionality and visual specificity without importing protected third-party artwork.
- [ ] **CVK-09:** Compare automatic retrieval vs no-retrieval baselines in a blinded test: first useful result accuracy, sector relevance, source diversity, brand specificity, iteration count, tool cost and actual user-task success.
- [ ] **CVK-10:** Promote original verified patterns and lessons to visual-patterns KB/UKDL using established criteria and actual consumer receipts, with rollback, expiry and cross-sector counterexamples.
- [ ] **CVK-11:** Establish curated renewal: source check, moved/removed URLs, new design eras, source-license drift, broken links, maintenance frequency and explicit retirement.

## Adversarial tests — not executed

| ID | Case | Correct response |
| --- | --- | --- |
| CVK-T01 | Gallery page listed as a downloadable visual kit | Preserve SOURCE vs KIT distinction |
| CVK-T02 | Behance screenshot treated as reusable licensed website asset | Reject copy; retain reference-only |
| CVK-T03 | Kitchen company automatically receives espresso/oat/sage regardless of existing brand | Enforce real brand constraints and justify any palette |
| CVK-T04 | Different sectors all receive the same 3 reference designs | Retrieval diversity and sector fit check fails |
| CVK-T05 | User asks for a kitchen configurator, retrieved reference is photo-only landing | Recommend interaction patterns separately; no fake functional claim |
| CVK-T06 | Source claims high-conversion but offers no data | Keep conversion unverified |
| CVK-T07 | Login/paywall or premium API search unavailable | Respect access terms, report UNKNOWN, use other lawful source |
| CVK-T08 | Source 404 or renamed, cached description still used as live evidence | Freshness check and degraded status |
| CVK-T09 | Agent generates fake client installation photos from moodboard references | Authenticity blocker |
| CVK-T10 | Huge catalog indexed but no CDIO consumer calls retrieval | Liveness test fails; not done |
| CVK-T11 | Three colors/60-30-10 forced even if brand has four roles | Heuristic does not override business truth |
| CVK-T12 | Popular screenshots selected with no fit to visitor job | Relevance/quality check fails |
| CVK-T13 | Source study reveals technique but no "when not to use" | Pattern not promoted |
| CVK-T14 | Existing design-index implementation replaced by new vector DB without benchmark | Duplicate owner/infra cost check rejects |
| CVK-T15 | Page uses a flashy hero but inaccessible mobile navigation | Rendered QA/release gate rejects |
| CVK-T16 | Human approves design but no legal image rights | Do not redistribute unlicensed assets |

## Done vs backlog truth

**SEED DONE now** only when the 46 entries are durably stored and syntactically valid, with source URL and rights status, and this program explicitly records the missing runtime integration.

**LIBRARY OPERATIONAL DONE later** only after the real CPP/Claude Code flow retrieves this library without the user issuing manual design commands, produces an original context-grounded output, observes a real rendered result, refuses seeded illegal/irrelevant examples and proves it improves outcomes in multiple unrelated sectors.

**Do not equate** committed JSONL, visible GitHub link, impressive reference count or automatically collected images with usable/approved institutional intelligence.
