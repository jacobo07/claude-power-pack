# CDIO Backlog — Meta Astryx Complete Capability Absorption

**Created:** 2026-11-12  
**Owner request:** Ingest all usable Astryx design and component intelligence into the existing Claude Power Pack, with source-level completeness and no duplication.  
**Source:** https://github.com/meta/astryx and https://astryx.atmeta.com/components/  
**Observed upstream ref:** 08b751a6dfe84d3d3216745b3eb65194187299e9 (meta/astryx main, 2026-11-12).  
**Observed CPP baseline ref:** b4bba4f3957ccfbb68ebfe381664137d088bdd80 (main at initial audit).  
**Status:** OPEN / BACKLOG ONLY / NOT IMPLEMENTED. No installation, upstream cloning, third-party source-copy, tests, or runtime deployment performed in this conversation.  
**Related work:** [21 design resources](2026-10-30_cdio-21-design-resources-universal-absorption.md), [brand identity/logos](2026-10-21_cdio-brand-identity-logo-absorption.md), [Anime.js](2026-10-10_animejs-design-absorption.md), [CDICF owner audit](../audits/cdicf/CPP_DESIGN_OVERLAP_MAP.md). Extend; do not recreate.

## Mission

Absorb the **entire relevant source-capability surface** of Meta Astryx by complete source inventory, semantic extraction, owner mapping, selective legal code reuse, rigorous verification, and institutional promotion. Cover all documented components, public exports, hooks, variants, interaction states, samples, design tokens, themes, templates, agent tooling, CLI contracts, design conventions, accessibility behavior, experimental modules, source documentation, testing machinery and long-term update rules.

**100% means all discovered items and meaningful capabilities have evidence-backed dispositions**, not that CPP copies all source files, installs 180+ components, claims all experiments production-ready, or reproduces someone else's trademarks and visual identity.

## 1. Immediate reality and evidence boundary

- GitHub README: Astryx is open source, MIT root LICENSE (Meta Platforms, Inc. 2026), **Beta**, React 19+ and StyleX-authored. Consumers use prebuilt CSS and typed components; React, React DOM and StyleX remain peers. Root README says **150+** accessible components. That figure is a publisher statement, not a complete exact count.
- Official site https://astryx.atmeta.com/ advertises **180+ components**, 13,000+ apps and eight years of company usage. Publisher statements are not independent proof. 150+ vs 180+ might reflect scope/date: **derive a new immutable count from code and catalog** rather than pretending either is the canonical exported-component denominator.
- Inspected packages/core/package.json at pinned ref reports version **0.7.15** with **174 export keys**. This includes CSS, docs, tokens and utilities. **174 export keys != 174 UI components.** React and React DOM peer requirements are >=19; StyleX peer is ^0.19.
- Inspected packages/core/src root lists 148 entries, including components, source utilities, tests and internal modules. **148 root entries != component count.**
- packages/cli/assets/templates/pages currently has **58 template directories** (including blank, gallery and showcases). **Directory count != count of production-validated templates**.
- Seven published theme families per README: neutral, butter, chocolate, matcha, stone, gothic, y2k. packages/themes/probe is an internal directory, not a verified eighth public theme.
- Root repository MIT license does not automatically apply to all bundled media/fonts/icons, dependencies, third-party Figma art or separately licensed materials. Audit each.
- README and website describe core/CLI/themes as primary and distinguish **lab, charts, vega and native** as experimental or canary where indicated. Native README expressly says Android and React Native bindings are not yet built and the package is not production supported. Richtext is Lexical-based; upstream blog describes stable release, but installed tag must still be checked.
- Source inspection found agent CLI, structured JSON API, manifests/error codes, plugins for coding agents, spec authority records, accessibility contracts, vibe tests, Playwright, Storybook, demo apps, templates and a portable-native experiment. Their existence is not proof CPP integration or current passing tests.

## 2. Constitutional ownership (no new OS)

| Source capability | CPP owner | Decision |
|---|---|---|
| Quality judgments, user/system/agent states, hierarchy, responsive, color, motion, a11y | Existing CDIO-00..09 and modules/cdio/scorer.py, tools/design_gate.py | EXTEND rules only where observed residue exists |
| UI component catalog, rights, routing, installation, rollback and manifests | Existing modules/cdicf and lib/license_gate.js | EXTEND existing component registry/selector; no second installer |
| Theme compilation, project visual SSOT, tokens | Existing project DESIGN.md and modules/design-md | Compile approved values, no independent token source |
| Brand assets/logo generation | Existing modules/ccf | Reuse, do not turn Astryx themes into counterfeit brand DNA |
| Motion pattern applicability | Existing modules/cdio/motion_patterns.py and visual-patterns KB | Absorb rationale and tested patterns, not another engine |
| Knowledge/evidence/graph/trace/ratchet | Existing CrawlOS/knowledge vault/graphify/PM-03/CO-12/UKDL/capability runtime | Feed existing systems, not another memory vault |
| Enterprise, mobile and AI workstation consumer | CPP project runtime owner for target stack | React-only installs by opt-in; stack-neutral principles otherwise |

**Selection states:** ALREADY_OWNED, EXTEND, ADAPT_WITH_TESTS, METADATA_ONLY, REFERENCE_ONLY, UPSTREAM_GATEWAY, ABSTAIN, UNKNOWN, REJECT, RETIRED. Every entry needs one status, rationale, provenance and acceptance evidence. Reuse is a form of completed capability absorption. No title-tier novelty.

## 3. The full upstream surface: 16 mandatory audit domains

| ID | Source and scope | Complete census requirement |
|---|---|---|
| S01 | packages/core/src, exports, index.ts and package metadata | Every public component, hook, module, named export, props, events, states, style variants, utilities and version |
| S02 | https://astryx.atmeta.com/components/ | Every publicly visible category, example, page, variant, state and documentation pointer; site-only vs source-only differences |
| S03 | packages/cli and its API/clients/assets | Every command, subcommand, JSON schema, error code, manifest, search, init, doctor, swizzle, icon, upgrade, theme, build, template, render and host behavior |
| S04 | packages/cli/assets/templates/pages, blocks, themes; docsite templates | All 58 initial template directories plus each block and all current variants/states and published demo differences |
| S05 | packages/themes and packages/core/src/theme | Seven public themes, every palette, type, tokens, CSS and theme-specific exception; licenses of fonts and icons |
| S06 | docs/design and docs/families | All visual/interaction invariants, user/system/agentic states, component families, applicability and exclusions |
| S07 | docs/architecture, docs/contributing, docs/specs, docs/schemas/knowledge, docs/templates | Current/draft/archived owner contracts, schema versions, design/architecture decisions, source→spec→tests |
| S08 | packages/richtext, packages/charts, packages/vega, packages/lab | Package export, stable/canary status, rich-text/Markdown, charts/axes/scales, experimental components and promotion gates |
| S09 | packages/native | Experiments with Swift/SwiftUI, platforms, bridge and theme tokens; distinguish actual builds from aspirational Android/React Native |
| S10 | packages/build and internal/stylex-capabilities | Build/source compiler, style outputs, cascade layers, consumer styling compatibility |
| S11 | plugins/astryx, .agents, .claude-plugin, .claude | Agent plugin/skills, Claude/Codex discovery, per-project/global initialization effects, permissions |
| S12 | apps/docsite, storybook, sandbox, template-viewer, example Next/Vite apps | Rendered behavior, sample states, docs parity, CSS/SSR/Next/Tailwind/Vite compatibility |
| S13 | internal/a11y-spec, internal/vibe-tests, interaction-harness, eslint plugin, shadcn-registry | Accessibility behavior patterns, controlled LLM UI evaluations, quality and registry tests |
| S14 | .github/workflows, .changeset, release docs, pnpm lock, security policy | Build/CI, canary/stable, versioning, source drift, dependency and license constraints |
| S15 | Official Figma link, themes, templates, Storybook and blog | Human-designed visual artifacts, code↔Figma parity and source/usage rights, without copying Figma assets unauthorised |
| S16 | LICENSE, package source/data and imported assets | Root license, notices, third-party media/fonts/icon rights and trademark limitations |

**Discovery process:** freeze commit, enumerate entire relevant tree, enumerate public export map, component docs, website categories, templates, locales, theme assets, tests and specs. Join by canonical IDs and produce independent absolute denominators for source files, public components, hooks, docs, exported members, variants, fixtures, templates, themes and experimental packages. Do NOT make a green coverage percentage by shrinking what is counted or ignoring missing docs.

## 4. Official 11-category component catalog

The current page groups components into **11 families**. Names below are illustrative subsets; each actual named export, variant and state must be enumerated independently.

1. **Action:** Button, Button Group, Dropdown Menu, Icon Button, Link, More Menu, Segmented Control, Toggle Button/Group, Toolbar.
2. **Chat:** Chat Composer, Chat Layout, Chat Message and metadata, Chat System Message, Chat Tool Calls. Include streaming states, tool execution truth, tokenized composer, scroll, dictation and keyboard.
3. **Container:** Card, Carousel, Clickable/Selectable Card, Collapsible.
4. **Content:** Avatar/Group, Blockquote, Citation, Code/Code Block, Empty State, Heading, Icon, Kbd, Markdown, Text, Thumbnail, Timer, Timestamp, Token, Rich Text View.
5. **Feedback & Status:** Badge, Banner, Info Tip, Progress Bar, Skeleton, Spinner, Status Dot.
6. **Form Controls:** Calendar, Checkbox, Complex/Multi Selector, Date/Date Range/Date Time, Field/File Input, Number Input, Power Search, Radio List, Selector, Slider, Switch, Text Area/Input, Time Input, Tokenizer, Typeahead, Rich Text Editor.
7. **Layout:** App Shell, Aspect Ratio, Divider, Form Layout, Grid, Layout, Resize Handle, Scrollable Area, Section, Stack.
8. **Navigation:** Breadcrumbs, Outline, Pagination, Side Nav, Stepper, Tab List, Top Nav/Mega Menu.
9. **Overlay:** Bottom Sheet, Command Palette, Dialog, Drawer, Hover Card, Lightbox, Overlay, Popover, Toast, Tooltip; track deprecated variants.
10. **Table & List:** List, Metadata List, Overflow List, Table, Table Selection Toolbar, Tree List.
11. **Utility:** VisuallyHidden plus public utility exports discovered in code.

Every component can have a public docs record, source variant, sibling-family contract, visual example, private internal helper, test suite and web/mobile state. These are distinct records, not interchangeable proof.

## 5. P0 — Reality scan and complete provenance/legality

- [ ] **ASX-001** Fresh CPP HEAD, source tree, concurrent-writer, existing CDIO/CDICF and adjacent-backlog overlap scan.
- [ ] **ASX-002** Pin upstream commit, release, core/CLI/theme versions and stable/canary tags; collect exact source/file/website snapshot hashes and access statuses.
- [ ] **ASX-003** Generate complete public-component/export/hook/module/doc site denominators using source-derived IDs; no manually curated shortlist.
- [ ] **ASX-004** Generate template/block denominator from all page directories, variants, examples, docsite/sandbox preview and published vs draft status.
- [ ] **ASX-005** Inventory all schemas/specs/design/family/architecture knowledge, record authority and per-file source references.
- [ ] **ASX-006** Root, package, dependency, font, icon, image, Figma, example and data licensing audit with notices and actual redistribution rules.
- [ ] **ASX-007** Create complete existing-owner overlap ledger, assigning exactly one classification and reason per capability; no competing design registry.
- [ ] **ASX-008** Install/script security audit: npm lifecycle, global skill writes, CLI init, swizzle, codemods, remote links and executable templates. No runtime calls in read-only audit.
- [ ] **ASX-009** Detect site/README/export drift (150+ vs 180+ vs 174 export keys) without equating unlike counts; preserve unknowns and timestamped evidence.
- [ ] **ASX-010** Baseline initial implementation and quality metrics on reproducible CPP and Astryx reference fixtures before changes.

**P0 Gate:** all 16 source domains addressed, source-derived count for every available class, unverified items explicit, no unauthorized copying.

## 6. P1 — CDICF components, adapters, export and lifecycle

- [ ] **ASX-011** Build component manifest adapter into existing CDICF, preserving variant/prop/event/dependency license and version data.
- [ ] **ASX-012** Read-only lookup from CDICF selector to pinned Astryx API/docs; ranking by actual app context, compatibility and design fitness, with ABSTAIN.
- [ ] **ASX-013** React19/StyleX/Next/Vite/Tailwind/CSS module SSR/RSC/install compatibility matrix with tested failure paths.
- [ ] **ASX-014** Audit source export + source-only and web-only components; don't omit either; avoid duplicating sibling subcomponents.
- [ ] **ASX-015** Complete controlled/uncontrolled, ref/DOM ownership, callback composition, variants and a11y semantics in each tested adapter.
- [ ] **ASX-016** Provider-independent component chooser: native CPP, Astryx, shadcn/Magic/etc or no component. Hard license and maturity filters first.
- [ ] **ASX-017** Adopt only necessary and permitted primitives through CDICF, with explicit operator consent, staging, source hash, rollback, no global CSS spill.
- [ ] **ASX-018** Swizzle audit and isolated optional adapter: source ejection without overwriting edits, paired version and license, tested restore.
- [ ] **ASX-019** Deep chat suite: Chat Composer, streaming, tokenized text, metadata/tool calls, dictation, copy/export, scroll anchoring, error states.
- [ ] **ASX-020** Deep data suite: tables, tree, filters, virtualized list, pagination, selection, overflow, keyboard, hierarchy, responsive.
- [ ] **ASX-021** Deep input suite: calendar/locales/timezone, rich forms, selectors, IME, date errors, data persistence, touch and keyboard.
- [ ] **ASX-022** Deep overlays suite: bottom sheet, command palette, dialog/popover, focus management, nested dismissals, mobile keyboard, safe areas.
- [ ] **ASX-023** Import-by-component bundle, CSS, font, hydration, load-time and a11y performance benchmarks. No unbounded global runtime dependencies.

**P1 Gate:** representative eligible component in each of 11 categories demonstrably composes, renders, works and rolls back; prohibited/ineligible alternatives rejected.

## 7. P2 — CDIO visual intelligence, themes and design contracts

- [ ] **ASX-024** Adapt source-proven design taxonomy **User States / System States / Agentic States** to CDIO-07 and existing runtime state contracts. Distinguish measured and human-authored judgments.
- [ ] **ASX-025** Absorb design specs: spatial hierarchy, control rhythm, shapes, elevation, typography, iconography, color emphasis, animation, reduced motion, mobile typography, bidirectionality and composition.
- [ ] **ASX-026** Absorb family contracts: buttons, action groups, input fields, layout primitives/regions, navigation, overlays and dismissal.
- [ ] **ASX-027** Absorb system architecture lessons: component boundaries, cascading sizes, StyleX+CSS source builds, theming, layer runtime, interaction modality, internationalization, RTL, source/consumer split, list windowing.
- [ ] **ASX-028** Map seven ready themes into a **typed, opt-in** project DESIGN.md input; themes never replace approved brand identity or global design truth.
- [ ] **ASX-029** Derive semantic token/typography/contrast/CSS-variable changes through existing design-md; validate dark/light, forced colors, localized fonts and stable override order.
- [ ] **ASX-030** Cross-framework style proof: precompiled CSS and StyleX authoring vs downstream Tailwind/Next/Vite/CSS modules, reset and cascade layers, no CSS bleed.
- [ ] **ASX-031** Audit Figma/Storybook/site visual parity with code at same version, including themes, state matrices and accessibility; no unapproved Figma asset mirroring.
- [ ] **ASX-032** Promote design rules only if they improve existing CDIO-00..09 with evidence and counterexamples. Reuse prior motion and anti-slop knowledge.

**P2 Gate:** no conflicting project DESIGN.md tokens, broken RTL/high contrast/motion/focus or unsupported source provenance.

## 8. P3 — Agent-native CLI, docs API, discoverability and install safety

- [ ] **ASX-033** Enumerate every CLI command/argument/capability from machine-readable manifest and actual code, including search, docs, component, hook, template, build, theme, icon, init, doctor, integration, upgrade, swizzle, render and experimental.
- [ ] **ASX-034** Model typed JSON response/error codes, source version identity, selector semantics, project/local/global routing, and stable failure outputs as reusable CPP adapters.
- [ ] **ASX-035** Implement optional read-only Astryx discovery through existing CPP capability routing, bounded brief/compact/full/dense outputs and true source provenance.
- [ ] **ASX-036** Inspect AGENTS.md/CLAUDE.md and global ~/.agents/skills modification behavior; require explicit install authority, safe merge and rollback, never blind global mutation.
- [ ] **ASX-037** Reconcile Claude Code/Codex agent plugin skills and any MCP exposure with installed CPP tools; no rival plugin or skill distribution.
- [ ] **ASX-038** Evaluate CLI search/ranking, errors and source definitions for transferable query semantics; version/pin the source when selected.
- [ ] **ASX-039** Evaluate swizzle/upgrade/codemods and generated component source with atomic writes, non-destructive upgrades, source licensing and reversible diffs.
- [ ] **ASX-040** Prevent unscoped npm astryx collision, unpinned npx auto-execution, global CLI vs pinned project version drift, absent core and incompatible peers.
- [ ] **ASX-041** Capture token and latency economics of retrieving exact component docs vs dumping huge catalogs in context. Keep on-demand retrieval by default.

**P3 Gate:** one fresh agent finds exact correct source with version-aware docs, refuses mismatch, no global changes without consent.

## 9. P4 — Templates, AI workstations and reusable compositions

- [ ] **ASX-042** Recursively ingest all initial 58 template page directory facts, plus every block/example and public template entry with provenance and maturity; no “all done” from just listing names.
- [ ] **ASX-043** Classify AI chat conversation/landing, IDE/canvas, dashboard/cohort analytics, table/inbox, form/wizard, checkout, nav shells, galleries, docs, kanban, detail and settings patterns.
- [ ] **ASX-044** Extract full interaction contracts, layout slots, real data/state dependencies, responsive collapse, error/empty/loading states and keyboard semantics from those patterns.
- [ ] **ASX-045** Compare actual AI-chat templates with Orca X / Cognitive Workspace surface and agent-native mobile flows, without replacing their platform architecture.
- [ ] **ASX-046** Validate generated templates with long text, translations, RTL, mobile, keyboard, empty/error/loading/retry, dark/light themes and real form action state.
- [ ] **ASX-047** Route accepted compositions to existing CDICF + design-index + visual-patterns, not a competing template OS. Record “when NOT to use”.

**P4 Gate:** a verified composition improves at least one actual task category without losing brand fit or flow.

## 10. P5 — Higher leverage: QA, knowledge governance and experimental projects

- [ ] **ASX-048** Absorb shared WAI-ARIA and WCAG accessibility **pattern contracts** from internal/a11y-spec, not just count tests. Reuse CPP a11y owner.
- [ ] **ASX-049** Absorb method of upstream Vibe Tests: same prompt different design setups, frozen task denominator, measured output quality and token/time economics. Reproduce independently.
- [ ] **ASX-050** Evaluate knowledge-contract architecture: current/draft/archived ownership, source→component/family/system spec→test linkage, versioned schemas, review approval, drift checks. Extend CPP vault/UKDL owners, not another constitution.
- [ ] **ASX-051** Compare upstream Playwright, Storybook, Vitest, CSS/RTL audits, WebKit/performance/release lanes with actual CPP QA and add only meaningful missing tests.
- [ ] **ASX-052** Evaluate richtext separately: Lexical, Markdown round-trip, plugin extensions, server-safe serialization, editor focus/IME and untrusted content sanitation.
- [ ] **ASX-053** Keep charts, Vega wrappers and lab components **canary-only** unless exact stable evidence contradicts this; evaluate chart data/axis/shared scale design as a reference.
- [ ] **ASX-054** Keep native (SwiftUI/iOS/macOS/JSON logic host) **experimental only**; extract portable contract logic and measured native/web parity, label Android/RN bindings as not built in inspected version.
- [ ] **ASX-055** Audit supply chain, license of embedded fonts/icons, dependency graph, sandboxing and CI scripts before execution or redistribution.
- [ ] **ASX-056** Build independent a11y/interaction/security/RTL/perf regression tests for adopted components and rule promotion at correct evidence level.
- [ ] **ASX-057** Preserve upstream schema/owner/approval distinctions; never turn an unapproved proposed spec into a CPP hard rule.
- [ ] **ASX-058** Record source version changes, component deprecations, license drift and safe retirement through existing capability runtime.

**P5 Gate:** no canary mistaken for stable, no unverified “native-ready” claim, and measurable positive/negative quality assurance.

## 11. P6 — Full coverage, benchmark and institutional promotion

- [ ] **ASX-059** Freeze cross-sector benchmark: trust/legal portal, data dashboard, web checkout, mobile onboarding, chat/tool UIs, editor, tables, native-only, non-React, RTL and low-power clients.
- [ ] **ASX-060** Compare CPP baseline vs supported Astryx candidate: task success, first-valid output, expert review, a11y/focus, visual fidelity, responsiveness, bundle/CSS, hydration, code maintainability, tokens/latency/price and rollback.
- [ ] **ASX-061** Build selector adversarial tests for refusal, inaccessible candidate, React version mismatch, prohibited fonts and source drift.
- [ ] **ASX-062** Feed verified patterns, failures, decisions and trace to CDIO/CDICF and existing Knowledge Vault/graph/PM-03/CO-12/UKDL, with owner and source provenance.
- [ ] **ASX-063** Publish per-component and per-template disposition coverage from frozen source denominators: OWNED/EXTEND/REFERENCE/ADAPTER/TESTED/PROMOTED/BLOCKED/UNKNOWN/RETIRED.
- [ ] **ASX-064** Selective activation at decision time, never forced installation; source detail loaded on demand and possible ABSTAIN.
- [ ] **ASX-065** Independent audit and rollback proof per added production capability; no green based on README or upstream test source existing.
- [ ] **ASX-066** Institutional regression ratchet: test both passing and failing poles, promote only demonstrably better behavior; track source updates and retirement.
- [ ] **ASX-067** Complete all 16 source-domain inventories, catalog crosswalk and unresolved source access/license entries; maintain visible absolute denominator, no hidden gaps.
- [ ] **ASX-068** Final owner-approved quality decision: clearly label research completeness vs actual code integration vs tested production readiness. Only then update DONE.

**P6 Gate:** 100% of verified in-scope capabilities dispositioned with reproducible links; actual CPP improvement observed; no licensed/stack/risk escapes.

## 12. Forty proposed adversarial tests (not yet executed)

| ID | Falsification case | Required evidence/outcome |
|---|---|---|
| V-ASX-01 | 174 package export keys reported as 174 components | FAIL denominator |
| V-ASX-02 | 180+ marketing claim treated as exact count | FAIL evidence |
| V-ASX-03 | Source-only public component omitted from website | Explicit inclusion or UNKNOWN |
| V-ASX-04 | Deprecated/canary source called stable | Refuse production recommendation |
| V-ASX-05 | 58 template folders called 58 production-validated pages | Refuse completeness claim |
| V-ASX-06 | Unlicensed bundled artwork redistributed | License BLOCK |
| V-ASX-07 | Global skill file changed without approval | Block filesystem mutation |
| V-ASX-08 | Global CLI differs from local project pinned CLI | Respect local and record version |
| V-ASX-09 | Unscoped npm astryx executed unexpectedly | Warn/block package collision |
| V-ASX-10 | CLI JSON and typed API disagree | Contract drift FAIL |
| V-ASX-11 | Unknown component returns hallucinated successful match | ABSTAIN with error |
| V-ASX-12 | Swizzle overwrites local edits | Atomicity/rollback FAIL |
| V-ASX-13 | React18 project receives React19-only component | Selector ABSTAIN |
| V-ASX-14 | Python/Elixir app forced to add React | Selector ABSTAIN |
| V-ASX-15 | CSS layer order creates override regression | Render/style gate FAIL |
| V-ASX-16 | Theme overrides approved DESIGN.md | Visual SSOT consistency FAIL |
| V-ASX-17 | Theme font has missing rights/glyphs | Review required |
| V-ASX-18 | Dark/RTL/forced colors hides focus | CDIO BLOCK |
| V-ASX-19 | Dialog loses keyboard focus on Escape/unmount | Interaction FAIL |
| V-ASX-20 | Bottom sheet ignores virtual keyboard/safe-area | Mobile QA FAIL |
| V-ASX-21 | ChatToolCalls renders unsafe tool-output HTML | XSS security FAIL |
| V-ASX-22 | Streaming chat loses user input or scroll anchor | Runtime regression FAIL |
| V-ASX-23 | Agentic "thinking" shown as actual completed tool action | State truth FAIL |
| V-ASX-24 | Markdown roundtrip changes untouched content | Fidelity FAIL |
| V-ASX-25 | Giant table stalls keyboard or blocks UI | Performance gate FAIL |
| V-ASX-26 | Canary charts/native/lab installed as stable | Maturity gate BLOCK |
| V-ASX-27 | Experimental native APIs claimed to ship Android/RN | Claim REJECT |
| V-ASX-28 | Third-party Figma/Meta asset assumed MIT by repo | Rights gate BLOCK |
| V-ASX-29 | Dependency unexpectedly executes network installer | Security gate BLOCK |
| V-ASX-30 | Duplicate CDICF owner created | Ownership gate FAIL |
| V-ASX-31 | Huge Astryx corpus loaded into every prompt | Context budget FAIL |
| V-ASX-32 | Polished screenshot but nonfunctional form | CDIO completion FAIL |
| V-ASX-33 | Upstream tests read but not executed, yet marked green | Evidence BLOCK |
| V-ASX-34 | Draft design spec promoted as current standard | Authority FAIL |
| V-ASX-35 | Benchmark shrinks subjects to pass | Frozen denominator FAIL |
| V-ASX-36 | Component feature inferred from showcase but unimplemented | Mark UNKNOWN/ABSTAIN |
| V-ASX-37 | Locale/RTL state missing despite claim | Accessibility FAIL |
| V-ASX-38 | Style import breaks unrelated app surfaces | CSS isolation FAIL |
| V-ASX-39 | Package MIT but a source font/icon not cleared | Selective asset BLOCK |
| V-ASX-40 | Upstream release changes API after pin | Drift quarantine + rollback |

Every gate requires positive and negative fixtures where meaningful. No fake results from documentation, no unobserved test “passes”.

## 13. Implementation protocol and exit standard

1. **SOURCE** — pin upstream head, directory/export/test/docs inventory and licenses; measure absolute denominator.
2. **OWNER** — search current CPP reality; route to one existing canonical owner, not a new design subplatform.
3. **DIFFERENCE** — label existing capability, extension, legal adaptation, reference only, block or unknown with why.
4. **TEST FIRST** — source-specific negative case and acceptance test; never add a gate that cannot refuse.
5. **ADAPT** — minimal dependency/semantic adapter, opt-in installation only in suitable React project.
6. **VERIFY** — browser-real behavior, interactions, accessibility, performance, cross-theme and security receipts.
7. **PROMOTE** — knowledge indexes/graph and standards through existing ratchet; independent review/rollback.
8. **REPEAT** — track new upstream versions, deprecations and changes in license/security.

**Definition of DONE:** Source categories, code exports, specs, docs, themes, templates, examples, agent APIs, tests and experimental packages each have a reasoned disposition; all promoted production features have real green test and negative-case receipts; restricted assets and canary elements are not installed contrary to policy; no unobservable or duplicated subsystem is introduced. “Source comprehensively indexed” and “all adopted components production-verified” are different statuses; do not conflate them.

## 14. Pinned primary source pointers

- [Astryx root](https://github.com/meta/astryx), [MIT LICENSE](https://github.com/meta/astryx/blob/08b751a6dfe84d3d3216745b3eb65194187299e9/LICENSE), [README](https://github.com/meta/astryx/blob/08b751a6dfe84d3d3216745b3eb65194187299e9/README.md)
- [Core](https://github.com/meta/astryx/tree/08b751a6dfe84d3d3216745b3eb65194187299e9/packages/core), [CLI](https://github.com/meta/astryx/tree/08b751a6dfe84d3d3216745b3eb65194187299e9/packages/cli), [Themes](https://github.com/meta/astryx/tree/08b751a6dfe84d3d3216745b3eb65194187299e9/packages/themes)
- [Template pages](https://github.com/meta/astryx/tree/08b751a6dfe84d3d3216745b3eb65194187299e9/packages/cli/assets/templates/pages), [Design records](https://github.com/meta/astryx/tree/08b751a6dfe84d3d3216745b3eb65194187299e9/docs/design), [Knowledge contracts](https://github.com/meta/astryx/blob/08b751a6dfe84d3d3216745b3eb65194187299e9/docs/architecture/knowledge-contracts.md)
- [Vibe Tests](https://github.com/meta/astryx/tree/08b751a6dfe84d3d3216745b3eb65194187299e9/internal/vibe-tests), [A11y specs](https://github.com/meta/astryx/tree/08b751a6dfe84d3d3216745b3eb65194187299e9/internal/a11y-spec), [Agent plugin](https://github.com/meta/astryx/tree/08b751a6dfe84d3d3216745b3eb65194187299e9/plugins/astryx)
- [Richtext](https://github.com/meta/astryx/tree/08b751a6dfe84d3d3216745b3eb65194187299e9/packages/richtext), [Charts](https://github.com/meta/astryx/tree/08b751a6dfe84d3d3216745b3eb65194187299e9/packages/charts), [Native](https://github.com/meta/astryx/tree/08b751a6dfe84d3d3216745b3eb65194187299e9/packages/native), [Lab](https://github.com/meta/astryx/tree/08b751a6dfe84d3d3216745b3eb65194187299e9/packages/lab)
- [Official component site](https://astryx.atmeta.com/components/), [Templates](https://astryx.atmeta.com/templates), [Theme docs](https://astryx.atmeta.com/docs/theme), [Storybook](https://astryx.atmeta.com/storybook/), [Sandbox](https://astryx.atmeta.com/sandbox/).

**At creation:** source-tree and selected documentation reconnaissance only. 68 tasks and 40 adversarial cases are **pending**, not completed. This record makes the opportunity durable and assigns its correct ownership; the actual absorption must be demonstrated by later artifacts and tests.
