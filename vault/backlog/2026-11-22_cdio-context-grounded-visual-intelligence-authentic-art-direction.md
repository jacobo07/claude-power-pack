# CPP-CGVI-001 — Context-Grounded Visual Intelligence & Authentic Art Direction

**Created:** 2026-11-22 (Europe/Madrid).
**Status:** OPEN / BACKLOG RECORDED / NOT IMPLEMENTED / NOT PROMOTED.
**Priority:** P0 evidence and anti-false-ready correctness; P1 asset intelligence and art direction; P2 construction; P3 visual QA; P4 institution-wide ratchet.
**Canonical program owner:** existing CDIO + CCF + design-md + CDICF owners; no new competing design OS, image service, source-of-truth or automatic promotion authority.
**Requested outcome:** turn the qualitative critique of Bodeguita El Puerto Brand Kit V2 into a reusable, sector-aware CPP baseline that can build appetite-inducing, warm, distinctive and authentic brand/web experiences without automatically generating images, while retaining the option of selectively generating original conceptual assets.
**Pilot:** Bodeguita El Puerto (Sotogrande); references discussed by Owner are conceptual, **not evidence of the actual venue, food, decor or permission to use photographed material**.
**Evidence snapshot:** existing owner paths inspected in public CPP main on 2026-11-22 (initial HEAD 398216c6b3f281571a8fac8cfa650ea6f19357bc). GitHub repository identities below checked on 2026-11-22; **repository existence does not prove current versions, source licenses, model-weight licenses, third-party photo rights, runtime operation, compatibility or quality**. Reconcile main and deployed/global runtime at execution.
**Scope semantics:** this is a task and source-disposition register, not a claim that any named upstream was installed, absorbed, benchmarked, audited for licensing, or incorporated into the runtime.

## New source-derived CDIO specialization: chromatic art direction + US kitchen configurator (2026-11-22)

The Owner supplied two Instagram screenshots and seven video files showing palette-driven hero design (base/text/accent and an illustrative 60/30/10 heuristic), sector-specific art direction, and an interactive kitchen configuration demo. [CDIO-VRK-001 — Color Art Direction & US Kitchen Configurator Reverse Engineering](2026-11-22_cdio-color-art-direction-kitchen-web-configurator-reverse-engineering.md) is the authoritative **specialized** intake: 9/9 media identities with hashes and evidence limits, 22 scoped implementation tasks, 24 negative tests, US remodeler/cabinetmaker application classes and Production Reality proof boundaries. Four MP4s contain only one decodable frame. Preserve source/reference rights and distinguish UI mockups from verified backend functionality. Do not fork CGVI automation/brand/QA owners. **Backlog only: no implementation, tests or external media republishing.**

## 1. The actual problem: attractive template != authentic destination

Owner critique of the V2 (qualitative testimony, not a fresh independently inspected artifact): excessive empty space, flat geometric beer/fish/boat/house illustrations, little real food or human activity, repeated images/symbols, restrained typography, weak material/lighting atmosphere, and a "beautiful branding presentation" instead of an inviting bodeguita where someone wants to enter, eat and remain.

**False premise to challenge:** being in Sotogrande does not itself justify a maritime iconography. Identify the actual establishment's cuisine, interior, owners, service, clientele, artifacts, atmosphere and distinctive history first. A nautical approach is an option only if the real brief and observation substantiate it. Likewise "Spanish castizo", tiles, vermouth, barrels and traditional ornaments are **hypotheses or inspiration**, never automatic assertions about this specific business.

**Desired V3:** editorial discipline plus human warmth, appetizing authentic imagery, expressive but appropriate typography, licensed/constructed tactile motifs, rich material cues and differentiated, non-repeating compositions. Hero image must be a real cleared image of the venue/food or visibly labeled concept—not invented evidence. Every key page should serve a grounded visitor decision (menu, location, opening hours, table/contact/booking only when actually supported).

**Anti-overfit:** do NOT turn a niche hospitality direction into a universal default for legal firms, autism support, enterprise dashboards, SaaS, real estate, etc. "More texture", "more density", "more serif" and "more motion" are not unconditional quality improvements.

## 2. Existing authority, overlaps, and explicit non-duplication

| Responsibility | Existing authority / concrete observed path | This program's delta |
| --- | --- | --- |
| Aesthetic taxonomy, design evaluation and quality verdict | modules/cdio/scorer.py, CDIO-06/07, tools/design_gate.py, rules/web/design-quality.md | Add context-sensitive authenticity, appetite/atmosphere evidence and rendered-surface review signals; do not create second quality scorer |
| Project tokens and experience contract | modules/design-md/DESIGN.md.template and design-md | Enrich grounding and asset-role rationale via compatible extension or referenced brief; one project DESIGN.md SSOT |
| Creative brief, identity, asset generation, brand kit, release | modules/ccf and prior BI-00..35 | Reuse CCF Visual DNA, image persistence, provenance, release/format gates; don't duplicate logo/brand kit generation |
| External component/asset admission and licenses | modules/cdicf | Selective intake, current rights verification, sandbox pilots, no unverified installs |
| Inspiration, external research and pattern indexing | existing design_index, research/CrawlOS owners and visual-patterns KB | Venue-grounded photo/reference evidence and sector-aware relevance rather than a competing scrape/index service |
| Motion applicability | CDIO-07, modules/cdio/motion_patterns.py and prior animation programs | Reuse motion budgets, accessibility, routing; no forced scroll animation |
| Visual/browser testing, benchmark, telemetry and learning | existing QA/pp_eval + Knowledge Vault/UKDL/graphify/ratchet | Add frozen hospitality and counter-sector fixtures, missing consumers and evidence-based promotions |

**Mandatory prior backlog links (not new implementations):**
- [BI brand identity and logos, 2026-10-21](2026-10-21_cdio-brand-identity-logo-absorption.md): BI-08 brand truth; BI-11 cohesive identity; BI-12 Visual DNA; BI-13 optional image providers; BI-15 context preview; BI-18..20 vector/font/color; BI-23..26 package; BI-28..35 review and transfer.
- [D21 design resource absorption, 2026-10-30](2026-10-30_cdio-21-design-resources-universal-absorption.md): D21-B discovery; D21-C design-md; D21-E motion; D21-G artwork; D21-H ratchet. This program adds **authentic venue evidence + photographic art direction + explicit default no-generation route + calibrated sensory critique**, not a competing source catalog.
- [VP-019 cinematic brand-lit hero, 2026-11-17](2026-11-17_cdio-cinematic-brand-lit-hero-reconstruction.md): reuse hero photographic grading, responsive/fallback and benchmark; do not promise cinematic hero for every page.
- [Anime.js program, 2026-10-10](2026-10-10_animejs-design-absorption.md), [Synsation UX, 2026-10-13](2026-10-13_synsation-ux-patterns-absorption.md) and [Astryx, 2026-11-12](2026-11-12_meta-astryx-complete-cdio-absorption.md): motion, interaction and components remain in their respective owners.
- [CPP-AIA-001 institutional source intake, 2026-11-20](2026-11-20_cpp-atomic-github-intake.md): general source governance/security; record this as a scoped design intake, not duplicate generic dependency auditing.

### Existing implementation liabilities to measure rather than assume

- DESIGN.md template currently supplies **F3 Warm Editorial** with cream, terracotta, Instrument Serif and Lora as an editable example. The template itself warns not to leave F3 unexamined. Test whether automation treats the example as a default and produces repetitive identical identities.
- tools/atomic_branding.py selects a hue via named colors or otherwise via prompt hash, and emits default Inter typography. This is deterministic but **not grounded in the specific establishment**. Evaluate whether CCF already supersedes this for brand-facing deliverables, before proposing deprecation/override.
- tools/design_gate.py feeds selected declared design data to modules/cdio/scorer.py. Its documented fail-open SKIP on unreadable artifacts must not be misrepresented as passing visual quality; a technically passing contract does not establish actual photographic authenticity, hunger, atmosphere or CRO. Find the real release consumer before changing severity/availability semantics.
- The existing brand program has P0 truth hazards around generated asset persistence, false-ready kits, rights, provider spending past BLOCK, and release manifests. New generated assets must respect those fixes/dependencies before production use.

## 3. Acquisition and generation decision contract

Default order for a real establishment:
1. **REAL_AUTHORIZED:** owner-provided or explicitly licensed documentary photos/video of actual food, place, team, materials and atmosphere. Record claim applicability; no synthetic people/food or imagined interiors presented as venue facts.
2. **LICENSED_REFERENCE:** rights-cleared editorial/reference imagery where it does not impersonate the venue; visible labeling/attribution when required; never copy copyrighted/trademarked reference brands.
3. **PROGRAMMATIC:** source SVG, ornaments, stamps, patterns, lettering, ceramic-like texture, CSS compositing and layouts constructed from factual brand direction and reusable code.
4. **GENERATED_CONCEPT:** selectively generated original illustration, texture, exploratory poster or moodboard when the first three routes are insufficient and permission/cost/rights are understood. Mark as concept if depicting unverified real-world details.
5. **ABSTAIN / REQUEST_REAL_ASSET:** if the deliverable requires a real photograph of an actual product, venue or person and none is authorized; no model hallucination may satisfy the requirement.

For each requested asset declare: purpose, claim being made, source classification, source URL/file identity, owner, evidence/permission state, license/attribution, subject authenticity, crop, focal point, resolution, responsive safe zones, intended use, transformation permissions, generation cost if any, expiry/review date, SHA, rollback and derivative lineage. The **same object can be technically valid but semantically prohibited** for a claim about the venue.

A resource's repo MIT license never automatically licenses its sample photographs, fonts, model weights, artwork, user submissions, brand marks or image provider API outputs.

## 4. Complete GitHub source intake: 27 candidates, 27 distinct dispositions

**Inventory semantics:** all 27 repository identities checked via connected GitHub (Lost Pixel confirmed as archived). All 27 are **DISCOVERED ONLY**, not adopted or license-cleared. Initial dispositions are *proposals* to be revisited against exact source revision, docs, LICENSE, asset sub-licenses, maintenance and CPP owner overlap. No indiscriminate dependency installation.

| ID | Repository | Relevant mechanism | Proposed disposition / owner |
| --- | --- | --- | --- |
| CGS-01 | [anthropics/skills](https://github.com/anthropics/skills) (frontend-design) | Brand-specific frontend art direction, anti-generic design critique | REFERENCE / EXTEND CDIO-06; verify applicable source/skill license |
| CGS-02 | [vercel-labs/web-interface-guidelines](https://github.com/vercel-labs/web-interface-guidelines) | Interactions, UI semantics, accessibility, responsive and craft checks | REFERENCE / DIFF existing rules/web design-quality and CDIO; no duplicated rulebook |
| CGS-03 | [penpot/penpot](https://github.com/penpot/penpot) | Editable artboards, components, libraries, design tooling | OPTIONAL EXPORT/WORKFLOW PILOT after real need; no new default editor |
| CGS-04 | [google-labs-code/design.md](https://github.com/google-labs-code/design.md) | Design-system format, lint/diff/export | ALREADY PRESENT in modules/design-md; verify package/license, reuse |
| CGS-05 | [WordPress/openverse](https://github.com/WordPress/openverse) | Discovery of openly licensed visual material | OPTIONAL SEARCH INTEGRATION with per-asset license/attribution checks |
| CGS-06 | [apify/crawlee-python](https://github.com/apify/crawlee-python) | Bounded crawling and extraction of public authorized brand facts/assets | CONDITIONAL TOOL CANDIDATE in existing research/CrawlOS; robots/ToS/PII checks |
| CGS-07 | [mlfoundations/open_clip](https://github.com/mlfoundations/open_clip) | Text-to-image semantic retrieval for cleared local media collections | DEFER until retrieval benchmark shows ROI, model weight rights/cost checks |
| CGS-08 | [idealo/imagededup](https://github.com/idealo/imagededup) | Detect exact/near-duplicate imagery | PILOT if CPP lacks coverage; perceptual repetition still requires review |
| CGS-09 | [rough-stuff/rough](https://github.com/rough-stuff/rough) | Hand-drawn vector strokes | VECTOR/ORNAMENTAL PILOT in art/asset owner; not default rusticifier |
| CGS-10 | [riccardoscalco/textures](https://github.com/riccardoscalco/textures) | Repeatable SVG textures and patterns | REFERENCE/PILOT for authorized original patterns |
| CGS-11 | [svgdotjs/svg.js](https://github.com/svgdotjs/svg.js) | SVG composition and animation primitives | CONDITIONAL VECTOR LIBRARY vs existing SVG paths; CDICF decision |
| CGS-12 | [vercel/satori](https://github.com/vercel/satori) | Programmatic HTML/CSS-to-SVG typographic artwork | OPTIONAL programmatic poster/social/label pilot; font/runtime constraints |
| CGS-13 | [linebender/resvg](https://github.com/linebender/resvg) | Reproducible SVG raster rendering | CONDITIONAL renderer; compare existing exporters and fidelity |
| CGS-14 | [lovell/sharp](https://github.com/lovell/sharp) | Crop, responsive image, format conversion and image composition | P0/P1 TOOL CANDIDATE only if missing in current stack |
| CGS-15 | [google/fonts](https://github.com/google/fonts) | Font source and metadata | FONT DISCOVERY; per-family and build license verification |
| CGS-16 | [fontsource/fontsource](https://github.com/fontsource/fontsource) | Self-hosted font packages and subsets | CONDITIONAL FONT DELIVERY; verify glyphs/axes and licenses |
| CGS-17 | [danielgatis/rembg](https://github.com/danielgatis/rembg) | Optional background separation for owned photos | DEFER/CONDITIONAL; weights may have separate commercial restrictions |
| CGS-18 | [Codrops/TileScroll](https://github.com/Codrops/TileScroll) | Image grid and scroll direction technique | REFERENCE_ONLY until performance/a11y/rights benchmark |
| CGS-19 | [Codrops/ImageStackGrid](https://github.com/Codrops/ImageStackGrid) | Image stack-to-grid compositional grammar | REFERENCE_ONLY / adapt mechanism with cleared images |
| CGS-20 | [Codrops/TypographyMotion](https://github.com/Codrops/TypographyMotion) | Expressive headline motion techniques | REFERENCE_ONLY / CDIO-07 motion test with reduced-motion route |
| CGS-21 | [motiondivision/motion](https://github.com/motiondivision/motion) | Motion primitives and interaction implementation | EXISTING MOTION OWNER decision, compare CSS-first / installed runtime |
| CGS-22 | [greensock/GSAP](https://github.com/greensock/GSAP) | Advanced motion/scroll capabilities | CONDITIONAL LICENSE-REVIEW PILOT only where cheaper equivalent fails |
| CGS-23 | [microsoft/playwright](https://github.com/microsoft/playwright) | Real-browser screenshots and visual snapshots | QA OWNER; extend established stack, don't duplicate runner |
| CGS-24 | [argos-ci/argos](https://github.com/argos-ci/argos) | Visual-diff review per PR | OPTIONAL service/pilot with hosting, privacy, pricing and rights review |
| CGS-25 | [dequelabs/axe-core](https://github.com/dequelabs/axe-core) | Automated accessibility checks | QA OWNER; check existing integration before adding |
| CGS-26 | [GoogleChrome/lighthouse-ci](https://github.com/GoogleChrome/lighthouse-ci) | Performance/audits and budget regression | QA OWNER; check current CWV/Lighthouse coverage |
| CGS-27 | [lost-pixel/lost-pixel](https://github.com/lost-pixel/lost-pixel) | Historical visual regression implementation | ARCHIVED 2026-04-22; REFERENCE_ONLY / DO NOT ADOPT AS ACTIVE DEPENDENCY |

**Intake completion obligations:** exact upstream commit/tag; canonical project and product scope; latest declared license and nested font/photo/model assets; security/dependencies; maintenance and archived state; rights to scrape/access; API surface and real tests; runtime cost/footprint; CPP existing owner; useful primitive vs hype; disposition; positive/negative fixtures; update/retirement plan. Keep all 27 records, including rejected and already-owned ones. Every unknown stays UNKNOWN, never silently APPROVED.

## 4A. P0 — OWNER CORRECTION: autonomous design quality by default (2026-11-22)

**Owner directive:** No manual commands required to get maximum feasible visual quality. When the user asks to build or improve a site, design, identity, UI, brand kit or visually meaningful asset, relevant CDIO resources must be discovered, selected, executed, inspected and improved **automatically**. Commands such as /cpp-design, critique, polish, typeset and bolder remain optional overrides/diagnostics, never completion prerequisites. 100% autonomy means 100% of eligible tasks have a verifiable autonomous quality path, **not that 100% of resources execute on 100% of tasks**. Quality is constrained by brief, evidence, authenticity, legal rights, accessibility, function, provider spending, compute and diminishing returns; limitless iterations and all-tool execution are explicitly rejected.

### Evidence / architecture boundary

- On repository main, hooks/cdio_visual_advisory.js already checks qualifying PreToolUse Write/Edit frontend changes, requires DESIGN.md or a justified repository opt-out in certain cases and invokes tools/design_gate.py for canonical DESIGN.md. It does **not** prove that every live project/runtime has the hook installed, nor that after-render review automatically ran.
- hooks/hook-dispatcher.js has a PreToolUse-Edit-chain path referencing the CDIO hook. Check installed/live event reachability separately; source registration is not runtime proof. Some alternative file writes, tool families and rendered/exported assets are not covered by that PreToolUse check alone.
- The existing hook itself requests later cdio-reviewer inspection of the **rendered** UI and admits that token review is necessary but not sufficient. A statement asking the agent to run review is not evidence that review executed.
- commands/cpp-design.md invokes design_index lookup; commands/design-md.md invokes design-md init/lint/export. Turn them into automatically selected **providers** of design intelligence, not commands the Owner must remember.
- CDIO-00 explicitly describes CDIO as a cross-cutting quality intelligence layer **not the author**. Therefore CDIO owns design policy, art direction, critique and quality/done verdict; existing CPP execution/SDD/GSD/UWCP runtime owns workflow scheduling, CCF assets/identity, CDICF third-party admission/licensing and browser QA real execution. Do not create a rival CDIO orchestrator.
- This clarification elevates the automatic applicability mentioned in CGVI-31 from a later P4 concern to **P0**. Preserve CGVI-31 as knowledge/UKDL ratchet owner, no parallel engine.

### New P0/P1 execution backlog (open; no implementation claim)

- [ ] **CGVI-A00 — Visual intent coverage census.** Enumerate triggers for new site, redesign, single component, UI patch, visual asset, brand/logo/kit, motion, mobile, email templates and exported design; measure false negatives and false positives including Bash/script-created assets. Map the existing runtime owner.
- [ ] **CGVI-A01 — Autonomous activation.** Auto-enter a design-quality mission upon eligible user intent, load approved project/product context and DESIGN.md, route tools without slash commands, avoid unrelated-task activation.
- [ ] **CGVI-A02 — Typed capability selector.** Reuse existing CDICF/design_index and skill registries to describe candidates by capability, task/industry fit, source/rights, requirements, trust, cost, availability, priority, fallback and measurable benefit. Select just the relevant resources; record selected, skipped and missing reasons.
- [ ] **CGVI-A03 — Evidence-grounded art direction.** Research actual business/consumer goals, materials, product, photographic assets, comparable references and context-specific composition. Declare intended direction before implementation. Never turn a style category into a false real-business fact.
- [ ] **CGVI-A04 — Automatic source/asset routing.** Choose authorized real media, cleared references, programmatic vectors or selective generative concepts according to existing CGVI asset policy and cost/rights approvals; abstain when authentic claims cannot be supported.
- [ ] **CGVI-A05 — Render/Observe/Repair loop.** After visual work, render with real browser or artifact renderer at supported target breakpoints, capture screenshots plus version/hash, run CDIO and functional/performance/accessibility tests, propose specific fixes, apply and recheck. A token gate alone is not a completion gate.
- [ ] **CGVI-A06 — Independent context-aware critique.** Evaluate actual screenshot and relevant objective criteria, plus separately labeled subjective assessments of hierarchy, distinctiveness, photographic direction, premium perception, atmosphere and usability. Compare methods from Impeccable, Taste Skill and design-taste without duplicate reviewers or manufactured precision.
- [ ] **CGVI-A07 — Real done authority.** Existing scorer and completion owner consume proof of actual rendered review, not merely agent prose or a design-file APPROVE. Distinguish APPROVE, REVISE, BLOCK, SKIP and ABSTAIN. Missing browser/asset evidence, timeout or fail-open must never become a false green; preserve ability to continue work safely.
- [ ] **CGVI-A08 — Bounded quality optimization.** Prioritize defects with greatest effect, cap iterations/compute/provider calls, rollback regressions and stop when marginal improvement falls below cost or external human/rights decision is required; report unresolved defects without declaring full quality.
- [ ] **CGVI-A09 — Progressive context and workload tiers.** Lightweight guard for small edits; full rendered UX/art direction QA at relevant milestones; richer benchmark for major redesigns and brand kits. No repeated all-repository scans or downloading 27 repos on every UI edit.
- [ ] **CGVI-A10 — Real autonomous liveness receipts.** Trace eligible user intent -> selected resources -> actual calls -> rendered output/hash -> criterion verdict -> repair(s) -> done decision. Installed/source existence is never proof of activation; manual invocation counter should trend toward zero.
- [ ] **CGVI-A11 — Four-context transfer benchmark.** Test personal premium dark portfolio, restaurant/bodeguita, sensitive human/neuroinclusive service, and enterprise SaaS dashboard. Measure design quality/brand specificity, task usability, mobile proof, autonomous activation, missing reviews, time/cost, human prompts and tool bloat. No global cinematic/dark/ornament bias.
- [ ] **CGVI-A12 — Institutional promotion and maintenance.** Commit validated bug root cause + red/green replay + cross-sector counterexample to existing Knowledge Vault, CDIO standards and UKDL; require proven consumer, owner approval where needed and rollback/retirement.
- [ ] **CGVI-A13 — Human authority and opt-out.** Respect approved brand/identity, licensed assets, spend/security limits and explicit quiet/opt-out. Human intervenes for genuine subjective creative stakes, lack of permission or irreversible decisions—not to remember quality tools.

### 12 adversarial autonomy fixtures (NOT EXECUTED)

| ID | Input/problem | Pass condition |
| --- | --- | --- |
| V-CGVI-A01 | Owner asks only "build a restaurant website" | Auto quality activation and final rendered review without slash |
| V-CGVI-A02 | User changes one hero line | Selective lightweight checks; affected rendered surface reviewed |
| V-CGVI-A03 | Visual files change through Bash/codegen | Source-gate coverage gap detected and compensated at completion |
| V-CGVI-A04 | Hook source exists but installed runtime missing | Autonomy cannot claim active; liveness test fails |
| V-CGVI-A05 | DESIGN.md scores high, browser shows blank hero | No DONE until rendered-surface evidence/rework |
| V-CGVI-A06 | SKIP exit zero or renderer timeout | UNASSESSED, never APPROVE |
| V-CGVI-A07 | Law service website asks high trust | No auto hospitality art or forced motion |
| V-CGVI-A08 | All 27 tools proposed for 1px padding edit | Selector refuses irrelevant tools and logs decision |
| V-CGVI-A09 | Hero generation falsely depicts actual venue | Rights/authenticity refusal and labeled fallback |
| V-CGVI-A10 | Animation polish harms LCP/mobile/reduced motion | Measured regression rolled back or rejected |
| V-CGVI-A11 | Screenshot receipt predates changed hero image | Stale receipt rejected; review re-run |
| V-CGVI-A12 | Repair loop stalls/no gain or hits budget | Bounded stop with truthfully unresolved status |

### Acceptance sequencing

P0 first: demonstrate a genuine end-to-end path from **user intent without any manual commands** through selection, build, real render, independent critique, repair, release verdict and trace receipt, with the negative controls above. Only then increase reference/asset/model breadth: a tool with no actual consumer is inert inventory. CDIO must be reliably activated for eligible design tasks, avoid irrelevant activation, deliver demonstrable cross-sector improvement, respect budgets and never report DONE without the required observed evidence. **This section is backlog-only, not an autonomous system already running.**


## 5. P0: reality, ownership, evidence, and guardrails

- [ ] **CGVI-00 — Live reality scan and conflict audit.** Record fresh repo HEAD, active writers/worktrees, installed/runtime owner status, existing CCF/CDIO/CDICF/design-md/design_index/photo/motion/QA capability, versioned source inventory. Contrast against BI, D21, VP-019 and CPP-AIA; explicitly link to them rather than reopen their generic implementation tasks.
- [ ] **CGVI-01 — Owner brief evidence ledger.** Define real venue facts vs owner testimony vs inference vs inspiration vs synthetic concept vs license unknown. Capture menu, venue, audience, price, locally relevant cultural context, actual materials and approved creative constraints. No fabricated Bodeguita facts.
- [ ] **CGVI-02 — V2 failure record with visual evidence.** Acquire authorized V2 files/screenshots and grade actual screens, typography, assets and crops. Without those, preserve the Owner critique as qualitative testimony and mark independent visual verdict UNASSESSED.
- [ ] **CGVI-03 — Source/rights/PII intake matrix.** Verify each CGS-01..27 at pinned revisions, downstream licenses and sample art, robots/ToS, client consent, image model weights, third-party hosting. BLOCK copied/redistributed assets without rights and synthetic venue evidence.
- [ ] **CGVI-04 — F3/template-seeding falsification.** Instrument a sample of genuinely distinct brand briefs to measure if editable F3, terracotta/cream/serif and atomic_branding prompt-hash defaults are used without reason. Extend existing selection/validation, do not ban defensible F3 uses.
- [ ] **CGVI-05 — Completion-path truth map.** Prove which live consumer invokes tools/design_gate.py and CDIO scorer, distinguish PASS/APPROVE from SKIP/ABSTAIN, record release path and missing rendered-photo evidence; never claim quality approval from unread inputs.
- [ ] **CGVI-06 — Release safety dependencies.** Respect existing BI-01..07 CCF asset persistence, actual bytes, provider BLOCK, scan freshness, brand package manifest and no false SEALED before generated artifacts become eligible for release.
- [ ] **CGVI-07 — Small immutable pilot corpus and benchmark protocol.** Capture authorized Bodeguita reference assets or synthetic clearly labeled fixtures; include explicit no-photo/uncleared-photo/adversarial cases and at least 3 non-hospitality control sectors.

## 6. P1: authenticity, photography and asset intelligence

- [ ] **CGVI-08 — Asset-role taxonomy and visual brief.** For every image: exact business fact, subject, intended sensation, buyer/visitor job, source, crop, fallback and release permission. Define distinct PHOTO/EDITORIAL/PRODUCT/AMBIENCE/MATERIAL/HUMAN/ORNAMENTAL/ICON/CONCEPT roles.
- [ ] **CGVI-09 — REAL_AUTHORIZED acquisition.** Receive client-owned/authorized photos and metadata; implement explicit licensing/proof intake through existing CCF/CDICF, local secure storage and immutable hash/derivative lineage; do not scrape private media.
- [ ] **CGVI-10 — Openverse and bounded CrawlOS research adapter.** Compare already available search/extraction providers; optional Openverse licensed-reference search and permitted public-site image inventory only. Preserve attribution, rights state, source date, use limitation and no impersonation.
- [ ] **CGVI-11 — Asset suitability and duplicate screening.** Implement/extend exact hash and perceptual near-duplicate detection; enforce semantic role coverage across pages; avoid one jar/fish/boat repeating in multiple sections. Semantic similarity and "looks repetitive" are separate claims.
- [ ] **CGVI-12 — Responsive photo direction and performance.** Manual/approved focal point, safe crop, subject salience, responsive srcsets/formats/widths/alt semantics, reserve dimensions, verify low-power mobile. Sharp or existing asset tooling selected by CDICF after comparison.
- [ ] **CGVI-13 — Optional semantic search.** Benchmark OpenCLIP against simple labeled metadata on cleared venue asset library. Adopt ONLY if retrieval accuracy/diversity and time saved justify model weight/license, RAM/disk and inference cost; no unnecessary always-on service.
- [ ] **CGVI-14 — Media authenticity and transformations.** No replacement faces, invented restaurant interiors, fake food/service/personnel claims, false crowd/social proof or synthetic client testimonials. Label illustrative/conceptual media in deliverables and preserve image edit lineage.
- [ ] **CGVI-15 — Abstention where photographic truth is required.** If venue-specific hero/real dishes/team photo absent, refuse "real" photographic output, provide labeled concept or brief for a lawful photo session; do not fabricate a convincing venue image and call it documentary.

## 7. P1/P2: art direction as reproducible construction

- [ ] **CGVI-16 — Grounded Art Direction Contract.** Extend approved CCF Visual DNA / DESIGN.md with atmosphere, food appeal, human warmth, location story, texture/material hypotheses, font personality, spatial density, iconography relevance, distinctiveness, prohibited motifs, approved sources and expected visitor action. Keep one SSOT; use references rather than duplicating token values.
- [ ] **CGVI-17 — Differentiated creative routes.** Generate 2–3 genuinely distinct feasible art directions (with one-route exception when brief demands fidelity), including comparative photo direction, typography, layout, material and business truth. Reject superficial color swaps.
- [ ] **CGVI-18 — Vector-first craft grammar.** Compare Rough.js, Textures.js, SVG.js, Satori and resvg with CPP SVG/vector/brand owners. Reuse smallest safe mechanism for original stamps, paper, ink, engraving-like ornaments, frames, tiles and expressive labels only when grounded. Avoid reproducing protected art and trade dress.
- [ ] **CGVI-19 — Type craft and multilingual proof.** Pair display/body/UI fonts from verified licensed sources; test line-breaks, ES diacritics, glyphs, kerning, optical weight, headline size on mobile, readability and font subset performance. Expressiveness is deliberate, not an unconditional typography inflation.
- [ ] **CGVI-20 — Compositional anti-template grammar.** Hero with original authentic focal image or abstention, context-specific headline, differentiated section rhythm, layered compositions and real menu/visit CTAs; avoid empty space by reflex AND clutter by reflex. Test alternative visual hierarchy against the same brief.
- [ ] **CGVI-21 — Sector-specific experiential cues.** For hospitality: truthful food presentation, service atmosphere, human/communal experience, menu clarity, material warmth and venue access. For non-hospitality controls: explicitly forbid transferring "appetite" cues as mandatory brand requirements.
- [ ] **CGVI-22 — Motion selector, not motion quota.** Use existing CDIO-07 and motion resolver, CSS-first where suitable; review Codrops techniques as patterns, Motion/GSAP only if warranted, reduced-motion equivalent, fallback, no blocking CTA or compositing bloat.
- [ ] **CGVI-23 — Generation eligibility and economy.** Apply per-asset REAL / LICENSED / PROGRAMMATIC / GENERATED_CONCEPT / ABSTAIN decision contract with explicit costs, consent, release state and photo-truth policy. Default no image generation; enable bounded original art generation when value is demonstrated.
- [ ] **CGVI-24 — Multi-output art system.** Reuse CCF and BI package/export profile to derive web, print, menu, editorial cards, social and brand-kit assets from consistent approved Visual DNA. The real business claims must remain the same across outputs; no independent re-invention per format.
- [ ] **CGVI-25 — Bodeguita V3 pilot.** Build one authentic end-to-end vertical slice (landing hero + at least two distinctive sections + menu/visit path + mobile view + compact brand-kit spread). Use approved real or clearly labeled conceptual media; before/after evidence from V2 where available.

## 8. P3: verified aesthetics, real browser QA and anti-slop ratchet

- [ ] **CGVI-26 — Rendered-surface evaluation adapter.** Use existing CDIO scoring API and QA outputs to attach screenshots and observed facts. Technical checks deterministic; ambiguous visual/semantic critique independently assessed and labeled JUDGMENT with evidence. Never turn model preference alone into ground truth.
- [ ] **CGVI-27 — Operational visual check families.** Browser screenshots mobile/tablet/desktop; image decode and crop; repeated asset detections; overlay text contrast in real image region; interactive CTA; responsive overflow; reduced motion; accessibility (axe-core); performance (Lighthouse CI); visual regressions (Playwright). Argos optional if justified.
- [ ] **CGVI-28 — Human-calibrated experience benchmark.** Independent reviewers compare blind, counterbalanced V2/V3 and control variants on "looks specific to this business", "desire to visit", "desire to eat", "clarity/legibility", "authenticity" and false-claim risk. Record sample size, actual prompts, inter-rater disagreement and uncertainty; no invented uplift, leads or conversion.
- [ ] **CGVI-29 — Frozen negative fixtures.** Execute the cases in Section 9 with red/green evidence and unchanged adverse counterexamples; no benchmark gaming by removing difficult screens or requiring the model to prefer a target style.
- [ ] **CGVI-30 — Measured resource and economic budget.** Before/after time to usable brand kit, human revisions, image-gen calls/provider spend, asset licensing overhead, number of original/reused assets, JS weight, LCP/CLS/INP and visual QA defect rate; compare genuine business utility, not just screenshot preference.
- [ ] **CGVI-31 — Knowledge/UKDL ratchet, automatic applicability and retirement.** Ingest observed root causes, defects, fixes, counterexamples and source changes in existing vault/UKDL/graph indexes; promote only independently measured generalizable changes. Auto-select this program for visual business/brand/site work via existing triggers without loading giant corpus into hot context. Test expiry, rollback and style-specific applicability.

## 9. Required adversarial falsification matrix (20 initial scenarios; NOT executed)

| ID | Deliberately bad scenario | Expected refusal or observable outcome |
| --- | --- | --- |
| V-CGVI-01 | Brief says venue is near coast; agent invents fish/boat emblem despite no menu/identity evidence | Motif requires source; hypothesis explicitly challenged |
| V-CGVI-02 | Prompt mentions "warm editorial" for unrelated projects; every page becomes cream/terracotta/Instrument Serif | Family-selection audit detects unsupported repetition, valid F3 exception retained |
| V-CGVI-03 | User photo/permission absent; generated plausible restaurant interior labeled authentic | BLOCK real-world documentary claim or require clearly labeled concept |
| V-CGVI-04 | Stock photo of another restaurant represented as actual Bodeguita | BLOCK authenticity/attribution |
| V-CGVI-05 | Openverse result with ambiguous or incompatible license treated as cleared | BLOCK reuse; source remains UNKNOWN |
| V-CGVI-06 | GitHub library MIT assumed to license its demo images/fonts | BLOCK nested-asset rights |
| V-CGVI-07 | Model weights permit only limited use; background removal adopted commercially unchecked | DEFER/BLOCK pending rights verification |
| V-CGVI-08 | Same decorative icon appears in six sections with trivial color changes | Repetition/role review flags overuse; no indiscriminate icon ban |
| V-CGVI-09 | Great-looking illustration displaces all food photography on restaurant home page | Sector role review identifies missing food/experience when supported by brief |
| V-CGVI-10 | Hero photo crop cuts out principal dish on mobile | Responsive crop test fails against approved focal anchor |
| V-CGVI-11 | Text contrast checked against dark corner instead of actual text pixels | Rendered overlay text test fails |
| V-CGVI-12 | AI confidence "100% authentic" despite no venue evidence | UNASSESSED/REVIEW_REQUIRED; no false-ready status |
| V-CGVI-13 | Missing DESIGN.md or gate parse failure returns SKIP exit 0, downstream claims design APPROVE | Release consumer must not equate SKIP to APPROVE |
| V-CGVI-14 | Extra motion ignores reduced-motion or obscures main CTA | CDIO-07/a11y/runtime failure |
| V-CGVI-15 | Large photo and JS animation worsen CWV without measured benefit | Perf/reduced complexity gate proposes simpler implementation |
| V-CGVI-16 | All projects inherit hospitality visuals and ornate lettering | Cross-sector fixture demonstrates over-transfer and blocks global rule |
| V-CGVI-17 | Font lacks Spanish characters and silently substitutes generic face | Glyph/license/render test fails |
| V-CGVI-18 | Brand kit status READY but image assets missing or text-only PDF | Existing BI production truth/actual-byte gate fails |
| V-CGVI-19 | "V3 improved conversion 40%" without visitors/analytics or experiment | Reject unmeasured commercial claim; keep preference judgment separate |
| V-CGVI-20 | 27 GitHub links registered, no source/version/rights/owner or consumer proof; work marked DONE | Coverage/promotion gate refuses |

**Additional invariants:** positive controls must include coherent minimal restaurant brand, actual maritime brand, photo-poor but truthful small venue, a strongly non-editorial hospitality brief, neuroinclusive support service, legal/professional site and technical SaaS. Tests must not universally prefer decorative clutter.

## 10. Promotion gates, release sequence and evidence

**T0 (P0) RECONCILE:** exact HEAD, owner matrix, 27-source candidate ledger, dependencies BI/CCF, initial dataset and benchmark consent. No installer, global hook, provider spend or scraping without approval.
**T1 (P1) EVIDENCE:** venue-grounded brief and verified assets, source/rights manifest, counterfeit/claim safety, source-role coverage. No undocumented client asset release.
**T2 (P1/P2) CONSTRUCT:** approved contract/Visual DNA, real/vector/optional-generated asset routes, responsive proof, one coherent Bodeguita slice and labeled conceptual media.
**T3 (P3) VERIFY:** CDIO scorer integrated through real consumers, browser a11y/perf/renders, 20 failing/repair tests with receipts, independent calibrated comparative review.
**T4 (P4) PROMOTE:** Knowledge Vault/UKDL and existing triggers updated, transfer to several sectors proved, source-update/rollback plan, no duplication and measured ROI.

**For every atomic micro-commit when execution starts:** precise owner, before failure/evidence, source revision, minimum behavioral delta, passing and refusing tests, code + rendered artifact hash when relevant, runtime/instrumentation trace, review disposition, rollback and impact on future work. Group commits by verifiable semantic units, not arbitrary ticket count.

**Acceptance for BACKLOG RECORDED:** this document exists at canonical path in GitHub main, cross-linked from D21 or authoritative CDIO index, contains all 27 source candidates, P0–P4 work and negative cases. This is achievable now without implementation.
**Acceptance for EXECUTION DONE (future only):** 27/27 explicit source dispositions, no false provenance or generated-real venue claims, real V3 pilot with approved source assets and functioning menu/visit path, actual pixel evidence, executed positive and negative cases, human-calibrated comparison, no regression on non-hospitality controls, approved production artifacts and rollback, learning promoted through existing governance. Every unavailable asset/test remains OPEN/BLOCKED/UNASSESSED, not implicitly passed.

## 11. Future implementation handoff

At the next implementation mission: start with T0 Reality Scan; choose PLAN vs autonomous multi-phase execution by actual state/ROI; propose inline owner-approvable plan while backing it up in the existing plan system; leverage CPP/GSD/UWCP only when warranted. Use Claude Code to author code, with no code copied from unvetted GitHub examples. Respect existing permissions, Security/HR boundaries, explicit spending consent, independent proof, small commits and full report of PASS/FAIL/BLOCKED. User requested **backlog capture now**, not execution, external installation or automatic image generation.
