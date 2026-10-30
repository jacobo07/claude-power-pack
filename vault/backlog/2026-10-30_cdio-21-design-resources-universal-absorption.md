# CDIO Backlog — Universal Absorption of the 21 Design Resources (six screenshots)

**Created:** 2026-10-30  
**Status:** BACKLOG RECORDED; RESEARCH PARTIALLY VERIFIED; NO EXTERNAL CODE OR ASSETS ABSORBED; NO TESTS EXECUTED  
**Owner instruction:** "añade todo esto al backlog de CDIO para absorberlo absolutamente todo" — all six user-supplied @nocodealex slides, including every named resource, its useful capability categories, cross-resource composition, new failure classes and long-term institutional learning.  
**Source evidence:** six screenshots uploaded in conversation on 2026-10-30; screenshot inventory below. Website and GitHub checks 2026-10-30. Site counters are volatile.  
**Purpose:** actionable intake and completeness register, not a new CDIO constitution or blanket authorization to copy other people's sites, prompts, components or art.  
**Canonical repo:** https://github.com/jacobo07/claude-power-pack  
**Related prior backlogs:**
- [2026-10-21 CDIO brand identity & logos](2026-10-21_cdio-brand-identity-logo-absorption.md) — already covers 10 logo/brand repositories + specialist tooling, 36 BI tasks and 16 BR falsification scenarios. Do not duplicate those workstreams.
- [2026-10-10 Anime.js](2026-10-10_animejs-design-absorption.md) — owns the detailed Anime.js absorption; this backlog adds a cross-source animation census, comparison and routing only.
- [2026-10-13 Synsation UX](2026-10-13_synsation-ux-patterns-absorption.md) — owns UX interaction principles already captured there. Extend its evidence where appropriate, not its doctrine.
- [CDICF ownership audit](../audits/cdicf/CPP_DESIGN_OVERLAP_MAP.md) — SEARCH → REUSE → EXTEND → CONNECT, new only for verified unowned gaps.

## 0. What "absolutely everything" means here

The **coverage obligation** is 21/21 upstream resource identities, all useful observable **capability families** and — for machine-discoverable catalogs when access and rights permit — every relevant catalog entry assigned a disposition. The goal is semantic and operational completeness, **not** blindly vendoring thousands of third-party source files, reproducing sites pixel-for-pixel, redistributing premium/proprietary work, or claiming that inspiration grants intellectual-property rights.

Every source/category entry must eventually have: identity and canonical URL, provenance and observed date, legal/robots/ToS posture, original owner, applicability/exclusions, usable source representation, quality evidence, integration mode, test fixture(s), status and upgrade policy. Missing site access, missing license or unreviewed ownership must produce **UNKNOWN / BLOCKED_FROM_COPY**, never a fabricated APPROVED.

Selection dispositions: EXISTING_OWNER / EXTEND_OWNER / PATTERN_WITH_CONTEXT / LEGALLY_ADAPTABLE_PRIMITIVE / REFERENCE_ONLY / UPSTREAM_GATEWAY / DEFER / REJECT / UNKNOWN. Each entry gets one explicit disposition and a reason. A website with 12,000 examples cannot be claimed 100% absorbed because only 5 screenshots were inspected. An absolute denominator is discovered from the source (when lawful and technically accessible), versioned, and unknown inaccessible entries remain outstanding.

When prior CPP contracts already solve a class of problem, that is **real absorption by reuse**. Do not score it as missing and build another subsystem.

## 1. Exact 21-resource inventory (preserve source-slide grouping)

### Slide 01 / 06 — DESIGN INSPIRATION: "Copy real designs" (4 resources)

| ID | Source / canonical reference | Screenshot claim (historical, not a license) | Capability to absorb | Initial disposition |
|---|---|---|---|---|
| D21-01 | [Minimal Gallery](https://minimal.gallery/) | Hand-picked sites and visual taste | Editorial selection, sector/category tagging, desktop/mobile comparison, composition/typography/branding signals, references to actual site evidence | REFERENCE_ONLY → CDIO-06 and design-index |
| D21-02 | [Kage](https://kage.design/) | Pick a design and copy it as a prompt | Site/section → structured design intent/prompt, product-context alignment, prompt-vs-render fidelity, design selection and applicability | REFERENCE_ONLY → design-md / prompt compiler; not a license to clone |
| D21-03 | [AppShot Gallery](https://appshot.gallery/) | "821 hand-picked real apps" | Mobile-app discovery, navigation/state/typographic UI references, platform-specific patterns, screenshots tied to real product and timestamp | UNVERIFIED_LIVE_ACCESS → CDIO-08; source URL corroborated by independent 21-site guide but site access was not confirmed in this session |
| D21-04 | [The Component Gallery](https://component.gallery/) | "60 components, 95 design systems, 2,671 examples" | Cross-design-system component taxonomy, alternate names, suitability criteria, evidence/UX rationale, patterns in different stacks | REFERENCE_ONLY/EXTEND → CDICF registry + design_index + CDIO-02 |

### Slide 02 / 06 — STYLE FILES FOR AI: "DESIGN.md files" (4 resources)

| ID | Source / canonical reference | Screenshot claim | Capability to absorb | Initial disposition |
|---|---|---|---|---|
| D21-05 | [DESIGN.md library](https://designmd.ai/) / [upstream format](https://github.com/google-labs-code/design.md) | "2,000+ ready-made DESIGN.md" | Example discovery, design tokens, human-readable visual rationale, schema lint/export/diff, style → project contract | **ALREADY OWNED** via modules/design-md and DESIGN.md; only augment validated catalog intake |
| D21-06 | [Refero Styles](https://styles.refero.design/) | 2,000+ real site styles as files | Observed-site→design.md derivation, type/color/spacing/components, measured vs assumed tokens, comparison, provenance and change detection | EXTEND EXISTING design-md brand-to-design-md |
| D21-07 | [Jiro](https://jiro.build/) | Browse a design, copy the prompt | Gallery→implementation intent, section-level prompt recipes, live previews, constraint-rich generative UI briefs, prompt-to-render evaluation | REFERENCE_ONLY/EXTEND prompt compiler |
| D21-08 | [VibePrompt](https://vibeprompts.dev/) | Ready prompts for pricing, heroes, dashboards | Prompt patterns by surface, marketing intent, interactions, responsive requirements and reusable prompt taxonomies | UNVERIFIED_LIVE_ACCESS; URL corroborated by 21-site guide but page not fetched; verify exact brand and legal terms before copying |

**Critical correction:** modules/design-md/README.md in CPP describes the upstream license as "Proprietary (Google Labs Code)", whereas the verified GitHub upstream https://github.com/google-labs-code/design.md/LICENSE currently contains **Apache-2.0**. Record this as LICENSE_DOCUMENTATION_DRIFT requiring reconciled current package/source terms; do not silently assume either repo text or README is sufficient for the actual installed npm artifacts.  
**Important:** Refero's extracted DESIGN.md files are **not official brand specifications** by default. Distinguish measured site styles, design inference, vendor-owned marks and transferable general design concepts.

### Slide 03 / 06 — BUILD A PAGE FAST: "Landing page parts" (4 resources)

| ID | Source / canonical reference | Screenshot claim | Capability to absorb | Initial disposition |
|---|---|---|---|---|
| D21-09 | [21st.dev](https://21st.dev/) / [GitHub org](https://github.com/21st-dev) | 12,000+ hero sections and buttons | Searchable community component registry, installation metadata, section composition, provenance/licensing at **individual contribution** level, shadcn registry workflows | EXTEND CDICF registry/selector; NEVER bulk-copy by default |
| D21-10 | [shadcn/ui](https://ui.shadcn.com/) / [repo](https://github.com/shadcn-ui/ui) | Clean source-owned components | Foundation primitives, component registry contract, accessibility, design system portability, CLI install/upgrade, UI theming | **ALREADY OWNED in CDICF**; audit deltas, do not create a second shadcn distribution |
| D21-11 | [Aceternity UI](https://ui.aceternity.com/) / [license](https://ui.aceternity.com/licence) | 200+ animated landing parts | Hero layouts, complex backgrounds, card depth, bento grids, storytelling, visual polish and motion composition | REFERENCE_ONLY / LICENSE-GATED gateway; Pro license forbids redistribution of source/items and certain templates |
| D21-12 | [Magic UI](https://magicui.design/) / [GitHub](https://github.com/magicuidesign/magicui) | 150+ animated components | Animated marketing blocks, marquee/globe/beam/text compositions, custom effects, layout and registry interoperability | CANDIDATE_ADAPT_WITH_TESTS for MIT main repo; Pro/premium separate |

### Slide 04 / 06 — MOTION + EFFECTS: "UI animations" (4 resources)

| ID | Source / canonical reference | Screenshot claim | Capability to absorb | Initial disposition |
|---|---|---|---|---|
| D21-13 | [Anime.js](https://animejs.com/) | One lightweight animation library | Timeline, staggering, keyframes, animation scopes, WAAPI/JS decisions, scroll, SVG path/morph, interruption and cleanup | **ALREADY BACKLOGGED** on 2026-10-10; reference, do not reimplement |
| D21-14 | [Motion Primitives](https://motion-primitives.com/) / [repo](https://github.com/ibelick/motion-primitives) | Copy-paste animated parts | Shared element movement, text transitions, gesture/hover, animated layouts, lifecycle and framework-specific motion semantics | PATTERN or licensed component through existing CDIO-07 / CDICF |
| D21-15 | [Kinetics](https://kinetics.colorion.co/) / [repo](https://github.com/ckissi/kinetics) | 153 spring effects (screenshot) | Spring-parameter reasoning (stiffness/damping/mass), CSS and React representations, AI prompts, input/feedback/reveal patterns | **REFERENCE_ONLY UNTIL LICENSE VERIFIED**. No LICENSE found in GitHub root at audit; README counts 162 while a cached site index says 144. Do not silently copy effect code or freeze a single count |
| D21-16 | [MicroKit UI](https://microkit.co/) / [repo](https://github.com/henriquegpb/microkit) | 49 microinteractions (screenshot) | Hover/click/focus/drag feedback, tabs, navigation, button state, micro-feedback without unnecessary motion/runtime cost | MIT candidate through CDICF; official site currently says **54**, so source census must be live and versioned |

### Slide 05 / 06 — LOOKS EXPENSIVE: "Premium UI effects" (3 resources)

| ID | Source / canonical reference | Screenshot claim | Capability to absorb | Initial disposition |
|---|---|---|---|---|
| D21-17 | [mapcn](https://mapcn.dev/) / [repo](https://github.com/AnmolSaini16/mapcn) | Maps with markers and routes | MapLibre map UI components, markers, popups, routes, controls, theme-aware map surfaces, map interaction quality | MIT component candidate; **map basemap/tile commercial terms separate**: repository README warns CARTO basemaps require a commercial arrangement for commercial usage |
| D21-18 | [Uiverse](https://uiverse.io/) / [repo](https://github.com/uiverse-io/galaxy) | Community-made UI elements | CSS/Tailwind visual interaction primitives, controls, loaders, effects, creativity patterns, originality filter | Community and per-item provenance/licensing required; code registry as candidates, not wholesale mirror |
| D21-19 | [Liquid Glass by samasante](https://glass.samasante.com/) / [repo](https://github.com/samasante/liquid-glass) | Apple-style liquid glass on web | SVG/WebGL displacement/refraction, glass lens, reusable React rendering, tunable optical parameters, fallback and accessibility/performance design | Reference + sandboxed candidate; MIT claim by project docs, verify exact code/asset versions. **Not** liquidglass.dev/websiteglass.com; screenshot's named source is samasante |

### Slide 06 / 06 — ART + ICONS: "Art + 3D icons" (2 resources)

| ID | Source / canonical reference | Screenshot claim | Capability to absorb | Initial disposition |
|---|---|---|---|---|
| D21-20 | [Kitbitz](https://kitbitz.art/) | 2,000+ hand-drawn illustrations, SVG/PNG, Figma and MCP | Illustration style families, illustration composition, art selection, SVG/PNG quality, Figma asset kit and AI-tool adapter discovery | Site claims CC0 for illustrated kits; **validate per-asset and third-party rights** before local ingestion/redistribution. Keep art ≠ original logo |
| D21-21 | [3dicons](https://3dicons.co/) | 1,440+ 3D icons | 3D icon visual vocabulary, Blender/format variants, lighting/shadows/camera consistency, raster output, asset selection and style adapters | Site says initial V1 CC0; current collection mixes **open-source and premium** content. Import only explicitly licensed items and log version/asset scope |

**Source totals:** 4 inspiration + 4 AI style files + 4 components + 4 motion + 3 premium UI + 2 artwork = **21** named resources. No additions or omissions; counts in screenshots are historical marketing copy, not verification of available source entries.

### Screenshot evidence manifest (private conversation attachments, hashes only; do not upload screenshots into repo)

All six attached JPEGs were 709×1536 pixels; SHA-256 calculated from uploaded bytes in this session:

| Slide | Attachment name | SHA-256 | Source group |
|---|---|---|---|
| 01/06 | 1000527125.jpg | 22f46f9700efc211d63bb00e6fe9b5ee032535b1eb9d57ec4260e95e0ff79fa2 | Inspiration |
| 02/06 | 1000527123.jpg | 09072be2b669d021fd39ae0958bc3e9b79ce5b6350319ff49525484538f21036 | DESIGN.md / style files |
| 03/06 | 1000527127.jpg | 157c85df6faa45e8bf78f4a82d1892043b24c8e634efcb4721eafc534bf20f2b | Landing-page parts |
| 04/06 | 1000527129.jpg | e46b66e5b896306f51a402fbe9ef907e3f4d94883e1d6813d702c4fadd76570b | Motion |
| 05/06 | 1000527131.jpg | 7869036973904ce00a6dad966f1c84e41685fc6d20d14dd6729998599ec3659a | Premium UI effects |
| 06/06 | 1000527135.jpg | 28f9378d0dd20967bbf8afbd8ad54c84d12cd39774197d35b7ba2688d62d2716 | Art + 3D icons |

The order 01–06 is the orange slide label order, not the Instagram 2/8–7/8 carousel badge order. Claims in slides may differ from live values.

## 2. Source rights, availability and trust boundaries

The live lookup here is **targeted validation**, not a complete code/security audit of all 21 sites. Source-count drift is observed for MicroKit and Kinetics. For AppShot Gallery and vibeprompts.dev, source identity is corroborated by [this contemporaneous 21-resource guide](https://chen.media/guides/21-sites-for-every-serious-vibe-coder), but direct webpage access was not established in this session; do not synthesize their terms or entries.

**COPY/INSTALL STOP rules:**

1. Public website visibility ≠ open-source license. If source is a curated gallery of **other brands' designs**, use as evidence and inspiration only; never clone a third party's whole visual identity, copyrighted screenshots, layouts, marks or private assets under a false license assumption.
2. **Component-level license is authoritative**, especially community-built 21st.dev/Uiverse or premium/free tiers. Run existing CDICF license gate against exact retrieved item + version. Unknown/ambiguous/restricted licenses must not be copied or redistributed.
3. **Aceternity Pro**: official license allows end-products but prohibits redistributing the item/source as stock and selling derivative template libraries. Never mirror its premium code into CPP. Free component terms require separate inspection, not a blanket MIT conclusion from an unrelated npm package.
4. **Kinetics**: GitHub root license could not be verified. No LICENSE does not imply permissive rights. Keep code as reference until explicit grant or independent clean-room implementation from legitimate general principles.
5. **mapcn**: MapLibre component-code license and tile/basemap service terms are independent. The mapcn README specifically notes CARTO enterprise conditions for commercial basemaps. Verify tile provider and attribution, quotas, map data privacy, geolocation access, online/offline behavior and key handling.
6. **3dicons**: initial V1 CC0 is **not** blanket rights for premium/current items. **Kitbitz** claims CC0 for its kits; still check asset provenance, trademarked depictions and third-party resources before export.
7. **Liquid Glass**: verify samasante implementation's package license and transitive dependencies, GPU/performance limits, accessible native control semantics, reduced transparency/motion and non-Chromium fallbacks. Brand look-and-feel need not imitate Apple's trade dress.
8. **DESIGN.md format**: CPP already integrates it. Upstream google-labs-code/design.md LICENSE file contains Apache-2.0 but CPP modules/design-md/README.md says Proprietary. Reconcile installed version and documentation rather than assert a global license correction blindly.
9. Never execute external installers or arbitrary pasted component commands as an auto-discovery side effect: inspect installation script, lockfile, transitive dependencies, network, secrets, telemetry, unsigned lifecycle hooks and generated files first.
10. No unbounded scraping, hidden copyright-violating mirroring, assumed robots/ToS permission or storing users' private product screenshots in the public CPP repo. Use URLs and minimal lawful structured facts when needed; retain attribution and provenance.

## 3. CPP architecture and canonical owners: no parallel systems

### Existing infrastructure observed in repository main

- CDIO: vault/knowledge_base/cdio/CDIO-00..09, modules/cdio/scorer.py, modules/cdio/motion_patterns.py, tools/design_gate.py, CDIO reviewers.
- CDICF: modules/cdicf/component_manifest.schema.json, registry_emitter.js, selector.js, installer.js and tools/design_index.py.
- Experience design: CDIO-07 experience contract in DESIGN.md; visual-patterns KB and the existing motion pattern resolver; no need for another "motion engine" solely to hold 153/162 spring demos.
- Design source of truth: modules/design-md/DESIGN.md.template and its Google-format wrapper; design-md lint/export/diff; governance/DESIGN_GOVERNANCE.md.
- Creative brand identity: modules/ccf, previously audited in 2026-10-21 identity backlog; not replaced by any new site catalog.
- Reuse/knowledge/evidence: existing CrawlOS, Knowledge Vault, graph, CDICF selector, CO-12/PM-03, release governance and scoped skill invocation.
- Current live visual pattern KB already indexes approximately 18 named patterns and an automatic motion resolver; verify actual denominator before declaring coverage after implementation.
- Existing Anime.js backlog and Synsation UX backlog already own detailed portions of motion/interaction quality.

### Responsibility routing by class

| New source class | Truth/owner | What to EXTEND, only after reality proof |
|---|---|---|
| Curated website/mobile galleries | CDIO-06/08 + existing design_index + CrawlOS provenance | Reference type taxonomy, constrained reference records, visual comparison/evidence; no website clone database |
| AI prompts and style files | modules/design-md + CCF prompt compiler where brand-specific | Verified reference → DESIGN.md compiler, intent metadata, reference attribution, output-vs-prompt fidelity |
| Copy/paste UI component registries | CDICF manifest/selector/installer | Catalog adapter and registered component evidence; hard license/security filters; no second registry |
| Motion/effects | CDIO-07 + modules/cdio/motion_patterns.py + visual-patterns | Pattern applicability, motion budgets, fallback/cleanup, alternative runtimes; prior Anime backlog retained |
| Map UI | CDICF + platform/map/geo owner (to be discovered) | Map component selection and licensed tile-provider adapter; avoid inventing a standalone map OS |
| Glass/material | visual-patterns + CDIO-01/03/07 + performance | Optical effect pattern with verified fallback; prohibit contrast/perf regressions |
| Illustration/3D art | CDICF assets/provenance + CCF identity asset consumer | Licensed asset selection, art style metadata, quality controls, context for use; not fake logo originality |
| Benchmarks and ratchet | Existing testing/QA + CCF/CDIO telemetry + UKDL | Counterexample gates, scorecards, writeback and promotion only on measured evidence |

## 4. Workstream A — Evidence discovery and complete corpus denominator (P0)

- [ ] **D21-A01** Reality Scan live CPP main, active branches/writers, existing source index, CCF/CDIO/CDICF/design-md/motion ownership, and previous three backlogs. Record overlap, not duplicated tasks.
- [ ] **D21-A02** Create 21 source records from screenshot evidence with exact canonical URLs, screenshot claim vs live verified fact, provenance, last checked date, access status and name disambiguation (Kinetics vs Kinetik, samasante vs other glass projects, VibePrompt vs other VibePrompts sites).
- [ ] **D21-A03** Build a source-derived **capability denominator for each of 21 sources**: actual named categories, page/component IDs and available interfaces from legally accessible discovery. Keep UNREADABLE/UNKNOWN count explicit. Distinguish "available on website" from "legally reusable in CPP".
- [ ] **D21-A04** For each catalog entry, assign owner, source ID, category, intent, tech stack, license, evidence confidence, applicability/exclusions and disposition. Avoid full source code capture in metadata-only records.
- [ ] **D21-A05** Capture exact Git tags/commit SHAs for GitHub-backed implementations once an adapter is selected; archive license evidence/fingerprint, origin attribution and release date. Snapshot updates only on new proof; never use marketing counts as gate denominators.
- [ ] **D21-A06** Record source-specific known conflicts: DESGIN.md upstream licensing doc drift; Kinetics missing license and count drift; MicroKit count drift; 3dicons V1/premium split; Aceternity Pro source resale limits; CARTO basemap terms; AppShot/VibePrompt inaccessible live checks.
- [ ] **D21-A07** Create an absolute coverage matrix with counts source-level (21/21), capability-level, entry-level, resolved vs unresolved and owned-vs-new. A pass cannot be manufactured by reducing scanned catalogs.
- [ ] **D21-A08** Test source unavailability, partial catalog, unlicensed material and changed URL; allow REFERENCE_ONLY/UNKNOWN without fabricating content. Network and crawling budgets are bounded.

**Gate A:** all 21 registered, 21/21 legal/scope dispositions present (some may remain explicit UNKNOWN), no mislabeled source URL, and source inventory denominator derived from reality when accessible.

## 5. Workstream B — Inspiration and reference intelligence (P1)

- [ ] **D21-B01** Minimal Gallery: classify visual references by audience, sector, density, typography, editorial hierarchy, photography, mobile/desktop structure, motion intensity, conversion layout, brand differentiation and design era; exclude trademark/template cloning.
- [ ] **D21-B02** Kage: extract *structure of design-to-prompt decisions*, connect to actual render evaluations, write traceable reference-to-brief transform with stop conditions against exact copying.
- [ ] **D21-B03** AppShot: after access and license verification, catalog cross-platform mobile patterns, app families, navigation, onboarding, empty/success/error states, touch ergonomics and gesture affordances; feed CDIO-08, not generic desktop design rules.
- [ ] **D21-B04** Component Gallery: ingest taxonomy of component names/synonyms, primary jobs, accessibility variants, state matrices and references to other design systems; route to CDICF selector and CDIO-02. Do not interpret gallery editorial choices as official standard mandates.
- [ ] **D21-B05** Implement visual reference retrieval ranking: match user's purpose, platform, conversion/trust context, existing DESIGN.md constraints and language; diversity/novelty guard, license filter and ABSTAIN when mismatched.
- [ ] **D21-B06** Require a design-decision brief before synthesis: WHAT source motivated a pattern, WHICH decisions are transferable, WHICH copied choices are forbidden, HOW result will differ and HOW it will be tested.
- [ ] **D21-B07** Capture a small legally reusable test corpus of reference descriptions, URLs and user-created test assets to verify discovery precision/diversity. Reject automatic harvesting of third-party site screenshots without authority.

**Gate B:** cross-sector and mobile-specific retrieval quality beats keyword-only baseline on frozen queries; no off-brand or unauthorised identity clones.

## 6. Workstream C — DESIGN.md, style transfer, AI prompt compilation (P1)

- [ ] **D21-C01** DESIGN.md library: audit only genuine deltas against existing modules/design-md; already owns Google-format lint/diff/export, DESIGN.md as project SSOT. Fix stale license documentation based on currently installed package facts.
- [ ] **D21-C02** Refero: stage URL/screenshot reference evidence → observed tokens (colors, font names, roles, components, sizes) → inference/unknown labels → new project design requirements → vetted DESIGN.md. Explicitly not an official vendor brandbook.
- [ ] **D21-C03** Jiro: classify section/page prompts into target job, audience, data dependencies, accessibility, motion budget, visual family and complete acceptance criteria; no verbatim proprietary prompt corpus copying.
- [ ] **D21-C04** VibePrompt: verify site's identity/content rights first; map compatible prompt categories (hero, pricing, benefits/bento, dashboards, navigation, product walkthrough); import method only if authorized.
- [ ] **D21-C05** Build DESIGN.md cross-source schema compatibility matrix: Google format, Refero examples, designmd.ai records, Jiro/VibePrompt prompt instructions, CPP existing template. One canonical project truth, transformations are derivative and reversible when feasible.
- [ ] **D21-C06** Strict source-evidence policy: real-site extracted tokens vs inferred creative recommendations; no invented font name/hex/radius/spacing; when not observable label UNKNOWN.
- [ ] **D21-C07** Prompt-vs-render QA: no unobserved "1:1" fidelity claims; test generated page, text, interaction states, responsive behavior, typography/font availability and accessibility. Creative adaptation should preserve product identity, not blindly recreate a reference.
- [ ] **D21-C08** Measure context/token cost and prompt effectiveness against CPP's existing DESIGN.md workflow; prefer compact reusable knowledge and retrieval over stuffing thousands of prompts into agent context.

**Gate C:** same DESIGN.md produces coherent cross-route tokens/layout/behavior without drift; controlled reference adaptation never silently overwrites an approved project identity.

## 7. Workstream D — UI component and landing page fabric (P1/P2)

- [ ] **D21-D01** 21st.dev: discover categories and components through supported registry API when authorized; source-level license not enough — validate each contributed component's actual license, dependencies, ownership, maintenance and last update.
- [ ] **D21-D02** shadcn/ui: compare with CDICF's existing shadcn integration; absorb only new registry features, safe upgrade/install, primitive accessibility and relevant patterns; never fork another component runtime.
- [ ] **D21-D03** Aceternity UI: build a **REFERENCE_ONLY/UPSTREAM_GATEWAY** catalog for restricted/pro material. Permit source-copy into CPP only for a separately licensed, permitted item after inspecting terms. Learn compositional patterns in a clean, non-cloning design manner.
- [ ] **D21-D04** Magic UI: audit MIT free source and its dependency/registry contract, select useful blocks and effects via CDICF; never silently conflate Pro assets with free repo.
- [ ] **D21-D05** Create normalized component metadata for: hero, navbar, CTA, pricing, testimonials, FAQ, benefits, bento, cards, tables, dashboard, forms, modals, icons, charts, backgrounds, typography/text effects and empty/error states.
- [ ] **D21-D06** Resolve component stacks and accessibility: React/Next/Vue/HTML, Tailwind versions, SSR/RSC hydration, semantic HTML, keyboard/focus, ARIA, responsive, RTL/i18n, styles collision, dark/light, reduced motion.
- [ ] **D21-D07** Require *selection before installation* and use existing CDICF filters: license/attribution, malware/supply chain, compatibility, cost, design identity fit, component state coverage, registry source version, rollback.
- [ ] **D21-D08** Add composition QA across multi-source parts: shared spacing/type/colors, no mismatched dependencies, no z-index collisions, no duplicate button variants, no excessive card soup, and one project DESIGN.md source of truth.
- [ ] **D21-D09** Build end-to-end install/rollback mutations: malicious registry, missing peer dependency, renamed component, license drift, stale source snapshot, failed install partway, components with same name from two registries.

**Gate D:** one legitimate component from each approved source can be discovered, license-evaluated, selected, installed, rendered, tested and rolled back; restricted/unknown options are refused with explanation.

## 8. Workstream E — Motion, springs and microinteractions (P1/P2)

- [ ] **D21-E01** Reuse [Anime.js existing backlog](2026-10-10_animejs-design-absorption.md) for complete API/scroll/SVG/timeline behavior and source licensing; no redundant Anime work queue.
- [ ] **D21-E02** Motion Primitives: map primitive types and layout animation semantics to CDIO-07, reduced motion alternatives, responsive behavior, cleanup and state truth; capture valid reusable patterns with evidence levels.
- [ ] **D21-E03** Kinetics: discover real source denominator and license first; study spring-like dynamics, parameterization, bounded overshoot, damping, interaction response and input constraints. No unauthorised direct copy from an unlicensed repository.
- [ ] **D21-E04** MicroKit UI: inspect all current component/trigger classes (hover, click, focus, drag, tabs, input, icon, navigation). Adapt code only through license-verified CDICF component manifests, testing focus and touch parity.
- [ ] **D21-E05** Create a motion selection decision record: CSS transitions/WAAPI vs Motion Primitives/Motion vs Anime.js vs bespoke JS vs no animation. Determine by functional purpose, platform, input model, interruptibility, latency, frame budget and size, not trendiness.
- [ ] **D21-E06** Enforce motion semantics from existing CDIO-07: motion budget ceilings, reduced-motion functional equivalence, no fake loading, no progress illusion, no non-deterministic state transitions; expressiveness NONE remains valid.
- [ ] **D21-E07** Runtime verification: interrupted animations, rapid toggles, unmount while active, navigating away, resize/orientation/zoom, memory/listener cleanup, concurrency, nested scrolling, touch/keyboard/reduced motion and FPS/long tasks.
- [ ] **D21-E08** Add negative examples to visual-patterns: spring overrun on destructive controls, an unnecessary animation in a payments console, hover-only content, a drag action without keyboard alternative, broken focus after transition, animated text that is inaccessible.

**Gate E:** motion patterns selected by purpose and DESIGN.md contract, benchmarked vs no-motion baseline, no WCAG/CPU/CLS/regression loss, and no “new animation family” that is only a duplicate of existing motion grammar.

## 9. Workstream F — Premium effects, maps, materials (P2)

- [ ] **D21-F01** mapcn: audit MapLibre components (markers, popups, routes, tooltips, zoom/compass/location/fullscreen, controlled state), tile provider terms, attributions, rate limits, commercial permission, geolocation authorization, SSR and fallback when tiles unavailable.
- [ ] **D21-F02** Uiverse: build a design-quality and security-aware component reference taxonomy (buttons, loaders, inputs, toggles, state feedback); separate github galaxy MIT from provenance of individually submitted community examples. Copy only permitted source with attribution as required.
- [ ] **D21-F03** samasante Liquid Glass: analyze lens optical controls (depth, curvature, dispersion, bend, frost, sheen, glow), SVG feDisplacementMap/possible WebGL, performance and fallback. Compare to CPP's existing glass/material rules; do not presume any glass effect suits a trust-critical interface.
- [ ] **D21-F04** Cross-browser matrix Chrome/Edge, Firefox and Safari including older/mobile hardware, forced-colors, reduced-transparency and reduced-motion settings; opacity/contrast worst-case, backdrop images vs arbitrary DOM, text readability, pointer events and focus visibility.
- [ ] **D21-F05** GPU and map resource budgets: memory, frame time, event listeners, tile/network requests, key use, cost/caching, reduced quality/no-effect fallback with identical core functionality.
- [ ] **D21-F06** Build material/gimmick arbitration in CDIO-03/06: choose glass, depth, gradient, micro-motion only when information hierarchy, trust, brand differentiation and accessibility improve. Simpler opaque UI often wins.

**Gate F:** glass/material/map improvements must survive baseline quality and interaction requirements and have a safe no-feature fallback. Use licensed map data and authentic geographic assertions only.

## 10. Workstream G — Artwork, illustration families and 3D icons (P2/P3)

- [ ] **D21-G01** Kitbitz catalog: discover kits/themes, SVG/PNG/Figma/MCP surfaces, structured asset names, composition slots, scaling, style family, outline/colored assets and visual consistency; record CC0 or other license per item and author notices where applicable.
- [ ] **D21-G02** 3dicons catalog: separate original CC0 V1 from current premium/free contents; map source Blender objects vs ready renders, angles, color variants, lighting, shadows, packaging and render dimensions; never assume all 1,440/1,500+ assets are freely redistributable.
- [ ] **D21-G03** Art selector: choose asset appropriate to brand visual DNA, UI meaning and culturally relevant context; avoid visual noise, category clichés, deceptive illustration, duplication and trademark lookalikes.
- [ ] **D21-G04** Safe asset ingest: validate SVG sanitization, raster dimensions/compression, transparent background, Blender/gltf security/performance if native 3D imported, anti-virus/transitive file scan and licensing provenance; no uncontrolled external Figma/MCP plugin execution.
- [ ] **D21-G05** Preserve semantics in interfaces: decorative images hidden appropriately from assistive tech, meaningful illustrations get real alternative descriptions, icons paired with non-color-only labels, small-size and contrast tests, responsive export.
- [ ] **D21-G06** Define illustration assets as **supporting brand visuals**, not a replacement for CCF's original logo generation. Only a licensed, sufficiently distinct, explicitly approved symbol can become a brand logo; otherwise retain as decoration/reference.
- [ ] **D21-G07** Create an output-profile adapter mapping art/icon choices to CCF and CDICF manifests and project DESIGN.md asset rules; do not maintain an independent asset memory of visual DNA.

**Gate G:** output shows genuine authorized source/derivatives, safe file formats, correct accessibility and consistency, with mixed free/premium items never silently copied.

## 11. Workstream H — Unified routing, benchmarking and institutional learning (P3)

- [ ] **D21-H01** Build a compact source-discovery decision surface: ask for a design goal, infer layer (reference / design contract / ready-made component / motion / map / material / art), query existing CDICF/design-index/KB owners and show grounded evidence with abstentions.
- [ ] **D21-H02** Make resource selection explainable, deterministic for equal versioned inputs, licensing-first, identity-sensitive, measurable and budget-aware. Prior popularity must never outrank compatibility or a prohibition.
- [ ] **D21-H03** Create freeze-frame multi-sector eval denominator: premium/luxury, law, finance/trust, creative portfolio, mobile productivity, SaaS dashboard, ecommerce, learning, landing conversion, map/dashboard, performance-constrained mobile, multimodal/art-heavy.
- [ ] **D21-H04** Compare baseline CPP against new sourcing on retrieval precision, source diversity, independent design preference, time to first valid prototype, component failures, runtime failures, accessibility, motion budget, bundle size, user iteration count, token usage and external asset license risk. No fabricated conversion/CTR uplift.
- [ ] **D21-H05** Publish verified entry manifests to existing retrieval index/graph/knowledge vault; gate on **absolute counts**: 21 source records, every lawfully visible catalog category/entry disposition, reported UNKNOWN remainder. No denominator shrinkage.
- [ ] **D21-H06** Establish update/diff and retirement policy: source 404, license drift, new component versions, removed design, broken behavior, incompatible framework, stale SEO/marketing figures and superseded UI patterns. Retire bad patterns instead of allowing indefinite accumulation.
- [ ] **D21-H07** Writeback of evaluated choices, counterexamples and user feedback to existing CCF/CDIO PM-03/CO-12/UKDL learning mechanisms with source lineage, not a second database or self-rewarding “taste score”.
- [ ] **D21-H08** Independent cross-browser and QA review of the actual artifact produced, not only a static screenshot or an AI opinion. One state-specific failure blocks only the affected capability and gives a recovery plan.
- [ ] **D21-H09** Integrate the route into current CLI/CDIO advisory when justified, so a fresh agent discovers the right external source and applicable rules without rereading all 21 sites or loading thousands of tokens.

**Gate H:** validated, on-demand CPP knowledge that makes future UI builds better without full-corpus context bloat, silent license escapes, duplicate owners or unjustified dependencies.

## 12. Executable falsification scenarios / DON’T FAKE DONE

The following are **proposed tests, not executed**. They must be driven at both passing and refusing poles once implemented. Add real source fixtures and discovered cases rather than substituting model-generated expected outputs.

| ID | Red scenario | Expected refusal / proof |
|---|---|---|
| V-D21-01 | 20/21 registered, missing one screenshot resource | Coverage FAIL, names missing resource |
| V-D21-02 | screenshot 49 microinteractions treated as immutable current count | Source/version drift surfaced; not silently asserted |
| V-D21-03 | Kinetics 153 screenshot vs changing 144/162 catalog counts | Versioned denominator, no false 100% |
| V-D21-04 | appshot.gallery/vibeprompts.dev fetch fails | UNKNOWN_ACCESS, no invented license/content |
| V-D21-05 | 21st community component unknown license | CDICF declines install and copy |
| V-D21-06 | Aceternity Pro source offered for vendoring | BLOCK redistribution, pointer/reference permitted as legally appropriate |
| V-D21-07 | Uiverse community snippet missing origin/permission | No copied code into CPP registry |
| V-D21-08 | Source gallery screenshot recreated 1:1 as unrelated brand | Identity clone warning and human review |
| V-D21-09 | Restricted source enters search index as license-free executable | Manifest rejection |
| V-D21-10 | Source README says permissive but LICENSE/terms disagree | LICENSE_CONFLICT; fail-closed for code redistribution |
| V-D21-11 | Google DESIGN.md source licensed Apache-2.0 but stale CPP doc says proprietary | Explicit drift reconciliation task, neither silently overwritten |
| V-D21-12 | Site reference missing observed font/color token | UNKNOWN, not invented design token |
| V-D21-13 | Imported design conflicts with current project DESIGN.md | Existing project design contract wins; no silent override |
| V-D21-14 | Installer auto-runs external registry code or network hooks | Safe install blocked until audited and explicitly selected |
| V-D21-15 | Component loads but inaccessible by keyboard/focus | CDIO/QA failure |
| V-D21-16 | Animated source has no reduced-motion functional equivalent | Motion gate refuses |
| V-D21-17 | Animation leaks listener after unmount / double trigger | Lifecycle regression FAIL |
| V-D21-18 | Motion budget NONE but Kinetics/Motion Primitives suggested | ABSTAIN, no effect proposed |
| V-D21-19 | Same motion feature duplicated as new local engine despite Anime backlog | Ownership overlap FAIL |
| V-D21-20 | mapcn rendered with unauthorized commercial CARTO basemap | Tile-license gate BLOCK, alternate provider considered |
| V-D21-21 | Map controls expose location without permission | Privacy and authorization FAIL |
| V-D21-22 | WebGL/glass unavailable or high-cost on mobile | Safe no-glass fallback; core UI still functions |
| V-D21-23 | Glass effect makes text unreadable on complex background | Contrast/readability gate blocks |
| V-D21-24 | Kitbitz third-party asset without checked rights enters brand kit | Asset license gate BLOCK |
| V-D21-25 | 3dicons premium item mislabelled "all CC0" | Version-aware asset license BLOCK |
| V-D21-26 | Heavy 3D icons cause poor LCP/CLS/frame time | Performance budget failure + simpler fallback |
| V-D21-27 | Model says “premium” without measurable evidence | No automatic CDIO quality promotion |
| V-D21-28 | Marketing library has proprietary text or photo reused in user product | Provenance/rights refusal or reference-only route |
| V-D21-29 | Registry contains identical components from multiple sources | Dedup/canonical owner resolution |
| V-D21-30 | Better visual screenshot but broken forms/mobile/RTL | CDIO cross-state/breakpoint FAIL |
| V-D21-31 | Source corpus shrinks to pass coverage | Absolute denominator non-shrinking gate |
| V-D21-32 | Upstream invalidates previously permitted item | Drift audit marks affected manifest stale/uninstallable |
| V-D21-33 | Recommender ranks popular UI over higher fitness/safer low-dependency alternative | Hard-filtered selector and grounded rejection |
| V-D21-34 | Reference-pattern improvement logged as proven based only on social post | Evidence tier remains hypothesis/research until real tests |
| V-D21-35 | Competitor logo/brand identity treated as open design template | Distinctiveness/rights reviewer refuses |
| V-D21-36 | Workstream reports DONE with just 21 source URLs and zero vetted entries | Production coverage gate fails |

## 13. Delivery sequence and integration stops

**P0 / SOURCE-TRUTH GATE:** A01..A08, 21/21 inventory, exact source IDs, legal boundaries, overlap audit. No component copying or model-driven site reconstruction before this stage.  
**P1 / HIGH LEVERAGE:** B01..B07 and C01..C08 (reference/experience-to-design transformations); D01..D09 (registry selection and safe component install) after license preconditions. E (motion) can start only where it doesn't duplicate the already open Anime backlog.  
**P2 / SPECIALISTS:** E02..E08, F01..F06, G01..G07 with browser, licensing and performance evidence.  
**P3 / UNIFIED SYSTEM:** H01..H09, benchmarks, automatic routing, durable knowledge, selective upgrade. No new platform modules unless a concrete owner insufficiency is proved.

**Earliest cross-workstream dependencies:**
- Resolve CDICF license/posture before D01/D03/D04/E04/F02/G01/G02 code/assets are copied.
- Respect the prior P0 CCF artifact-persistence false-SEALED work before publishing generated brand identity packages containing new images/icons.
- Resolve motion contract CDIO-07 before allowing spring effects, hover motion, glass motion or advanced interactions.
- Resolve map provider license/privacy before claiming a map demo is production-ready.
- Resolve DESIGN.md project SSOT before automatically deriving any theme from scraped reference tokens.

### Mandatory evidence bundle per promoted capability

1. Upstream URL and pinned version/commit (where applicable); legal license text + dependencies and third-party assets.
2. Original source entry identifier and title, captured facts, capabilities, limits, applicability and exclusion surfaces.
3. Existing CPP canonical owner and exact reuse/extension/new-build decision.
4. Implemented runnable primitive **or** reusable structured knowledge (reference-only); explicit scope, no invented asset.
5. Passing and refusing tests including browser-real rendering when appropriate; source/version diff test.
6. Before/after benchmark with denominator, status and unknowns, provenance and human inspection.
7. Rollback, retirement and future update condition; note any upstream-only details deliberately not reproduced.

### Definition of DONE

Do not mark this backlog complete until:
- all **21** source identities have verified or explicitly unverified classifications, and every discovered legally inspectable capability class has exactly one disposition;
- the 21 provenance records include accountable rights/terms status; restricted references have not leaked into distributable code;
- each canonical CPP owner has retained authority (CDIO, CDICF, design-md, CCF, motion, QA and existing knowledge/runtime);
- benchmark includes real before/after observations and verifies at least one useful result in each of the six source groups, with failures and unknowns explicitly counted;
- 36 red/green falsification cases are implemented as applicable or documented as non-applicable with evidence; no silent drop;
- independent QA has inspected real component/render output; no false universal "absorption" claim;
- progress is recorded in existing backlog/knowledge systems and CODE/INSTALL/APPLY changes are documented with commits and rollback.

**Current status of this document:** source intake and backlog only. No new source code installed, third-party site copied, component copied, file mass-downloaded, design pattern promoted, benchmark run, release tested or main production runtime modified.

## 14. Evidence pointers and audit constraints

Public sources inspected:
- [The same 21-site grouping, independently listed](https://chen.media/guides/21-sites-for-every-serious-vibe-coder)
- [Minimal Gallery](https://minimal.gallery/), [Kage](https://kage.design/), [Component Gallery](https://component.gallery/)
- [DESIGN.md library](https://designmd.ai/), [Refero Styles](https://styles.refero.design/), [Jiro](https://jiro.build/)
- [shadcn official](https://ui.shadcn.com/docs/official), [Aceternity terms](https://ui.aceternity.com/licence), [Magic UI source](https://github.com/magicuidesign/magicui)
- [Motion Primitives](https://motion-primitives.com/), [Kinetics source](https://github.com/ckissi/kinetics), [MicroKit actual catalog](https://microkit.co/)
- [mapcn README / basemap limitations](https://github.com/AnmolSaini16/mapcn), [Uiverse](https://github.com/uiverse-io/galaxy), [samasante Liquid Glass docs](https://glass.samasante.com/?view=docs)
- [Kitbitz](https://kitbitz.art/), [3dicons](https://3dicons.co/) and [CC0 initial release statement](https://3dicons.co/about)

All external facts are **time-bounded**; marketing figures, access, code license and website labels may change. Reconfirm in the implementing session. A link in this document is a research reference and never authorization for automatic fetching, installation, mirroring or redistribution.
