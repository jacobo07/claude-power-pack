# Backlog — CDIO Brand Identity & Logos: evidence-gated GitHub absorption

**Created:** 2026-10-21  
**Owner intent:** Absorb the useful brand-identity and logo-design capabilities identified in the owner-provided "Dataset CDIO Brand Identity & Logos 1.md", including all ten GitHub projects, the specialist libraries, and the follow-up CPP reality audit, into the existing Claude Power Pack CDIO ecosystem.  
**Priority:** P0 correctness / P1 creative capability / P2 production integration; schedule only after existing owners and tests are verified.  
**Status:** BACKLOG OPEN — source research and static CPP audit exist; absorption, code changes, runtime tests, external installations, and product release are NOT DONE.  
**Audit companion:** [Draft PR #8](https://github.com/jacobo07/claude-power-pack/pull/8), [detailed audit on its isolated branch](https://github.com/jacobo07/claude-power-pack/blob/audit/cdio-ccf-brand-absorption-2026-10-21/vault/audits/ccf/CDIO_CCF_GITHUB_BRAND_ABSORPTION_AUDIT_2026-10-21.md). Draft PR is evidence, not a shipped implementation.  
**Document role:** Actionable canonical backlog entry, not a new design constitution, duplicate engine, completed migration, or permission to copy unvetted code.

## Mission and non-negotiable outcome

Turn brand and logo generation into a reusable, evidence-based, vector-capable, production-verifiable institutional capability of Claude Power Pack. A future agent should be able to go from a valid brand brief to well-differentiated identity proposals, approved visual DNA, source SVG and derivatives, accessible and legally screened identity assets, production-ready brand guidelines, and durable learning **without inventing a new parallel owner**.

A logo alone is not an identity. A rendered image alone is not a vector asset. A positive model response is not proof of a persisted image. A valid PDF containing only textual descriptions is not a completed brand kit. A low similarity score is not trademark clearance. An AI aesthetic judgment is not an objective measurement.

**Minimum invariant:** Brand package status SEALED/READY must mean that all contractually required *real* visual assets exist, are valid, represent the selected identity, survive the relevant fitness tests, and have retained provenance and human decisions.

## Constitutional ownership: REUSE before CREATE

| Responsibility | Existing canonical owner | Required relation |
|---|---|---|
| Creative brief, concept routes, provider execution, assets, packaging, release, creative learning | [modules/ccf](https://github.com/jacobo07/claude-power-pack/tree/main/modules/ccf) (Creative Compilation Framework / brand-identity specialization) | **EXTEND**, never fork |
| Visual criteria, aesthetic direction, typography/color/accessibility, independent design review and scorer | [modules/cdio](https://github.com/jacobo07/claude-power-pack/tree/main/modules/cdio) + [CDIO-00..09](https://github.com/jacobo07/claude-power-pack/tree/main/vault/knowledge_base/cdio) | **EXTEND / CONNECT**, no new scorer authority |
| Component applicability/manifest, reusable primitives, provenance, upstream licensing | [modules/cdicf](https://github.com/jacobo07/claude-power-pack/tree/main/modules/cdicf), [license_gate.js](https://github.com/jacobo07/claude-power-pack/blob/main/lib/license_gate.js) | **REUSE / HARDEN** |
| Project-approved design truth | Project DESIGN.md, [design-md](https://github.com/jacobo07/claude-power-pack/tree/main/modules/design-md), [DESIGN_GOVERNANCE](https://github.com/jacobo07/claude-power-pack/blob/main/governance/DESIGN_GOVERNANCE.md) | CCF identity object compiles to this contract; do not maintain conflicting palette/token masters |
| Deterministic theme and motion tokens | [tools/atomic_branding.py](https://github.com/jacobo07/claude-power-pack/blob/main/tools/atomic_branding.py) + design token rules | Extend and/or replace internals through deliberate compatibility migration |
| Retrieval, evidence, historical learning and baseline ratchet | Existing design_index / CrawlOS / Knowledge Vault / Graphify / PM-03 / CO-12 / UKDL / capability_runtime owners | **PRODUCE EVIDENCE to existing systems** rather than duplicate them |
| Default activation | [CLAUDE.md CCF activation criteria](https://github.com/jacobo07/claude-power-pack/blob/main/CLAUDE.md) | Strengthen existing triggers; CDIO need not be mentioned explicitly by users |

**Canonical policy:** CCF constructs; CDIO judges; CDICF governs reuse/licensing; DESIGN.md distributes approved identity; CPP captures outcome evidence.

**Pre-existing CDICF precedent:** [CPP_DESIGN_OVERLAP_MAP](https://github.com/jacobo07/claude-power-pack/blob/main/vault/audits/cdicf/CPP_DESIGN_OVERLAP_MAP.md) already rejected redundant design owners. Do not create a new "CDIO Brand OS", redundant institutional memory, duplicate trademark scanner, competing image service, or second token source.

## Evidence snapshot and source-status semantics

The four core repos below were source-inspected during the 2026-10-21 audit; findings are **static inspection, not a passing integration test**. The six secondary projects below had their repository existence and head commits checked; functional capabilities remain **candidates to audit**. No licenses, dependencies, font assets, model access, or CI outcomes should be inferred from a README without independent confirmation.

Proposed classifications: OWNED; EXTEND_EXISTING; ADAPT_WITH_TESTS; EXTRACT_METHOD; REFERENCE_ONLY; DEFER; REJECT; UNKNOWN_NEEDS_EVIDENCE. Each source capability needs exactly one evidence-backed disposition in an absorption ledger with path, version, owner, risk, regression gate, and promotion status.

### A. Ten source projects — complete candidate denominator

| Candidate | Snapshot as inspected 2026-10-21 | Hypothesized benefit / work item | Current disposition |
|---|---|---|---|
| [fatihaydost/brand-identity-skill](https://github.com/fatihaydost/brand-identity-skill) | 532742d7477dba3b744433adf92845642953dc28 | Unified logo + typography + color, independent routes, identity comparison cards, small-size render, glyph, contrast and licensing checks, full brand guide | **P1 EXTRACT/ADAPT**; MIT repo, third-party rights/notice audit still needed |
| [moayadMoatamed/Marker-AI](https://github.com/moayadMoatamed/Marker-AI) | d14340c372730899950419dd9c0dd34b31116d6c | Deconstruct semantic/letterform raw material; 12 technique hypotheses; Gestalt/negative space; brand-specific construction recipe and self-critique | **P1 EXTRACT_METHOD ONLY until licensing conflict resolved** |
| [velinussage/brand-gen](https://github.com/velinussage/brand-gen) | 3fff970ac7e44fb2609b0f4047438a2a59346509 | Research → plan → validate → execute → review → evolve; typed tool and outcome protocol | **P1 AUDIT FOR DELTAS**, never copy its orchestrator/memory |
| [xianshi3/sigilgen](https://github.com/xianshi3/sigilgen) | c3f605b7864b41a3319fc25dacca6174b0aa897b | Offline, deterministic, parametric flat SVG; geometry, symbol, palette, typeface, explainable source and input bounds | **P2 PILOT ADAPTER**, MIT code; typeface outline and glyph rights audit required |
| [Leonxlnx/imagegen-skills](https://github.com/Leonxlnx/imagegen-skills) | beb16b0d0f4dae9a6f5cb04ea41e97b93a54ab8e | Brandkit exploration of marks, compositions, palettes and real-world applications | **P1 EXTRACT_METHOD** after actual skill/license inspection |
| [mcpware/logoloom](https://github.com/mcpware/logoloom) | 9e5de3e95d24fd86ea9af3cbe77749df088ad176 | SVG → complete export profile: light/dark/mono variants, social images, favicon, PNG/WebP, identity guide | **P3 OUTPUT SPEC ONLY**; never install code directly without security fixes |
| [yakew7/DesignHub](https://github.com/yakew7/DesignHub) | 148e8c3ffa8ea82801b3cfb16ef91b4ca515d285 | Brand Studio / brand book / mockups / design-token application, once audited | **P3 COMPARE & BENCHMARK**, no duplicate editor |
| [Forge-Space/branding-mcp](https://github.com/Forge-Space/branding-mcp) | 5128f2ea59d19976e6670c791fea2b72bba336e5 | Color/type/token algorithms and reusable boundaries | **P2 ARCHIVED REFERENCE**: repository archived at inspection; do not treat as maintained dependency |
| [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | dad8dbb3aac21ad1fa236c110315ef4abece23e8 | UI design critique, anti-generic patterns, application fidelity | **P4 REVIEW-GATE REFERENCE**; not a logo generator |
| [op7418/logo-generator-skill](https://github.com/op7418/logo-generator-skill) | bf4e9ac4d4428bda261afcfe981871ceb92d94e6 | Logo construction ideas, prompt and design methodology | **P2 REFERENCE** after inspection |

**Critical source traps:**
- Marker-AI has **LICENSE file with Apache-2.0 text but README indicating MIT**; GitHub auto metadata was non-assertive. Treat code adoption as LICENSE_CONFLICT until analyzed and explicitly resolved, even though its *general ideas* may be studied.
- LogoLoom's image-to-svg implementation interpolates a supplied path into a shell command; its ICO export writes PNG bytes with an .ico extension; its SVG extraction relies on regex over markup; text-to-path can silently choose bundled Inter. Do not vendor these behaviors. Require positive/negative security and format tests.
- brand-identity-skill reports 474 upstream unit tests and roughly 40.5 turns / 0.86M billed-input-equivalent tokens for a complete three-set run. These are **upstream-authored claims**, not CPP benchmark results or cost targets. Borrow its quality mechanics without copying a costly interaction schedule.
- Sigilgen's deterministic output is a useful baseline, not proof of brand distinctiveness. Audit its bundled outline/icon sources, non-ASCII names, commercial rights, international glyph coverage, and generated-content constraints.
- Simple Icons and competitor identities may be compared as references; never assume rights to recycle a trademark merely because SVG code is available.

### B. Specialist libraries — candidate implementation denominator

These are **not automatically selected dependencies**. Audit version, license, supply chain, API, alternatives and total cost before using.

| Library / standard | Intended CPP role |
|---|---|
| [SVGO](https://github.com/svg/svgo) | SVG reduction, with before/after rendered-difference gate |
| [VTracer](https://github.com/visioncortex/vtracer) | Optional raster→vector first pass; requires cleanup/quality assessment, not automatic finish |
| [resvg](https://github.com/linebender/resvg) | Deterministic SVG render and multi-size visual verification |
| [fontTools](https://github.com/fonttools/fonttools) | Typeface metadata, Unicode/glyph coverage, font-axis/license evidence |
| [color.js](https://github.com/color-js/color.js) | Perceptual color and palette computations |
| [Style Dictionary](https://github.com/style-dictionary/style-dictionary) | Cross-platform token export from canonical identity |
| [Design Tokens Community Group](https://github.com/design-tokens/community-group) | Interoperability/format contract; use current adopted specification, not invented fields |
| [favicons](https://github.com/itgalaxy/favicons) | Correct favicon/platform formats with actual file validation |
| [FAISS](https://github.com/facebookresearch/faiss) | Optional indexed *screening* against a grounded visual corpus, not legal clearance |
| [Simple Icons](https://github.com/simple-icons/simple-icons) | Potential comparative reference set; marks belong to their owners, never template inventory |

## P0 — CCF production truth and release safety (must precede P1–P4 shipment)

Owner: **modules/ccf/**. Review: **CDIO quality reviewer + existing license/security owners**.

- [ ] **BI-00 · Fresh Reality Scan, denominator and ownership.** Recheck current main HEAD, active branches/writers, CCF paths, CDIO-00..09 contracts, CDICF and source license/version fingerprints. Build the source-capability ledger (all 10 repos + specialist tools). Record OWNED/EXTEND/REFERENCE/REJECT/UNKNOWN for every meaningful candidate. No duplicate owner. Verify previous findings before acting on them.
- [ ] **BI-01 · Persist actual provider assets.** [CCF current CLI](https://github.com/jacobo07/claude-power-pack/blob/main/modules/ccf/cli.py) serializes ImageArtifact metadata but drops bytes and rehydrates just status. Persist validated image bytes atomically to safe project-contained paths, track SHA-256, dimensions, mime/magic, generator version, cost and prompts, read persisted asset at later stages. A status flag is never image evidence.
- [ ] **BI-02 · Split CONCEPT_REPORT from BRAND_KIT.** Current [artifact_compiler](https://github.com/jacobo07/claude-power-pack/blob/main/modules/ccf/artifact_compiler.py) creates text-only PDF/HTML; distinguish these useful drafts from visually complete kits. Embed actual logo art into production PDF and require real source assets and rendered preview; no false SEALED on empty/fake image data.
- [ ] **BI-03 · Enforce BLOCK before provider spend.** [cmd_generate](https://github.com/jacobo07/claude-power-pack/blob/main/modules/ccf/cli.py) currently records trademark BLOCK but still reaches provider generation in the inspected call path. Blocked concept ⇒ zero paid/provider calls, zero deliverables, explicit reason.
- [ ] **BI-04 · Require positive, fresh scan evidence at release.** [release_manager](https://github.com/jacobo07/claude-power-pack/blob/main/modules/ccf/release_manager.py) rejects explicit BLOCK/WARN-unacknowledged but not a missing report. Absent/invalid/stale version → UNASSESSED/NOT_READY, not implied PASS. Audit risk policy when a WARN is acknowledged. Do not claim legal clearance.
- [ ] **BI-05 · Gate package/manifest integrity.** Enumerate required files per deliverable profile; hash/check actual SVG/PNG/PDF/ICO bytes, renderability, version, trusted paths, selected-concept identity and content completeness. Two or more independent false-green test families; preserve rollback and draft artifacts.
- [ ] **BI-06 · Close source/supply-chain policy.** Existing CDICF/license-gate owns code redistribution. Check upstream README vs LICENSE, bundled glyphs, illustrations, sample marks, notices, restrictions, generated assets, transitive deps, network behavior, install scripts and license drift. No unchecked remote script/npx auto-download in critical paths.
- [ ] **BI-07 · Reconcile tests/spec/runtime.** Revise source contracts and tests so the positive route proves a genuine rendered and persisted mark, not ImageArtifact(status=OK) with no bytes. Run existing CCF/CDIO/CDICF/governance regression suites and independent review in an isolated worktree.

**P0 completion:** CCF cannot emit SEALED/READY without proof that the brand kit's visual deliverables exist and are valid, and a deterministically BLOCKed concept never incurs generation cost. No regression of other CCF/CDIO consumers.

## P1 — Strategy, symbolic reasoning and coherent identity generation

Owner: **CCF contract/config/prompt compilation**; governing CDIO **CDIO-00/01/06**.

- [ ] **BI-08 · Brand Truth evidence intake.** Typed/traceable brand purpose, audience, sector, category codes, geography/languages, competitive identity space, positioning, personality, price/experience signals, claims/constraints and existing protected assets. Route external evidence through existing CrawlOS/research owners, without fabricating source observations or automatic brand-name trademark clearance.
- [ ] **BI-09 · Multi-territory generator.** Produce at least three meaningfully different conceptual directions by default, with explicit narrow-brief exception; compare distinct brand facts, mechanism, audience fit and rejection reasons, not simply colors of the same icon. Preserve a typography-only or monogram route when appropriate.
- [ ] **BI-10 · Marker technique taxonomy.** Absorb 12 mechanism categories as typed hypotheses: negative space, letterform mutation, semantic fusion, Gestalt, geometry, etymology, cultural association, and others verified from pinned source. Require a concrete brand-specific observation and a geometrically actionable construction recipe. Do not elevate LLM self-ratings to measured originality.
- [ ] **BI-11 · Cohesive identity sets.** Adapt brand-identity-skill's single decision system spanning logo, font and palette, with explicit 2–4 comparison axes, conceptual rationale, contrast/typography testing, and category-default challenge. Preserve original logo/palette/font in KEEP or REFRESH modes and avoid unwanted redesign.
- [ ] **BI-12 · Typed Visual DNA.** Define a versioned CCF data contract for identity: brand_id and approved brief, conceptual territory, symbol strategy, geometric constraints, shape language, relative proportion, palette roles, typography/font metadata, spacing, variants, photography/icon/motion policy, forbidden patterns, avatar rules, small-size rules, applications and selection/review evidence. Compile it into DESIGN.md and tokens; never fork project SSOT.
- [ ] **BI-13 · Structured creative provider policy.** Evaluate brand-gen and imagegen-skills/brandkit for transferable prompt recipes, bounded tool use, generative composition and scenario design; do not import parallel orchestration, memories or unverified claims. Explicitly track token/cost/latency and model fallback. Generate image concepts only when deterministic/vector construction cannot meet intent.
- [ ] **BI-14 · Independent concept critique.** Evidence vs judgment separated; test meaningfulness, silhouette, category fit, genericity, spelling, constructability, emotion fit and user intent. A human selects from genuinely distinct qualifying directions; automatic critique suggests refinements but cannot silently approve.
- [ ] **BI-15 · Brand-context application preview.** Test the same identity against site masthead, avatar, favicon, real photography, packaging label, print, ad overlay, mobile screen and social canvas. Mark mock context as mock; use consistent selected Visual DNA, never independently reinvent the identity in every channel.

**P1 completion:** given a testable brief, CCF produces explicit differentiated, repeatable concept records and human-reviewable identity sets whose technical statements can be checked and whose uncertain judgments remain marked as such.

## P2 — Vector-first, type-safe and deterministic construction

Owner: **CCF construction adapter**, with **CDICF/license gate** and **CDIO-01**.

- [ ] **BI-16 · Sigilgen sandbox pilot.** Pin exact upstream ref, inventory 5 engines, palette/type/icon brain and test coverage; construct a CCF adapter exposing seed/inputs/outputs without injecting a rival workflow. Prove byte-identical output on cross-process and cross-platform relevant fixtures where practical.
- [ ] **BI-17 · Safe SVG source authority.** Use an allowlisted SVG serializer/parser and strict URL/attribute policies. No scripts, event handlers, executable foreignObject or external remote references in untrusted logo sources. Separate icon, wordmark and combined graphic as typed parts, not regex extraction from arbitrary markup.
- [ ] **BI-18 · Vector/raster dual lane.** Native parametric SVG where suitable; optional GPT/image raster concept followed by traced SVG (VTracer) only with explicit inspect/repair/reject. Quantify path complexity, tiny gaps, negative space, print legibility and render differences; trace != production-quality vector.
- [ ] **BI-19 · Font/Unicode fidelity.** Inspect licensed fonts, actual glyph coverage in ES/EN/PT/FR/DE and source brand languages, diacritics/kerning/variable axes; never silently substitute bundled Inter for a selected commercial wordmark. Verify text-to-path when shipping outlined marks and preserve font/provenance metadata.
- [ ] **BI-20 · Color science and accessibility.** Prefer role-based colors, perceptual ramps, real contrast checks (context-specific), mono/dark/light profiles and perceptual color-difference tests. Avoid invented color-conversion heuristics and unproven associations with conversions or trust.
- [ ] **BI-21 · Extra sources triage.** Inspect branding-mcp (archived) and logo-generator-skill as historical knowledge only unless production evidence supports a bounded component. Record accepted and rejected concepts in CDIO/visual patterns with applicability, caveats and counterexamples.

**P2 completion:** one selected brand concept produces safe, versioned, editable SVG assets plus raster derivatives with tested language, color, glyph and rendering behaviors; no hidden code execution or unlicensed font substitution.

## P3 — Complete portable identity kit and cross-platform applications

Owner: **CCF artifact_compiler + release_manager**, consuming **DESIGN.md / DTCG tokens**.

- [ ] **BI-22 · Safe LogoLoom-style exporter.** Extract desired asset categories (icon, wordmark, combination, monochrome, reversed, dark/light) and sizes/contexts into a versioned export profile; DO NOT reuse unquoted shell execution, regex SVG splitting, PNG-as-ICO or silent font fallback. Verify formats by parsers.
- [ ] **BI-23 · One source, multiple derivatives.** Generate exactly the requested and contractually mandatory PNG/WEBP/SVG/ICO/PDF/social assets from one approved vector/Visual DNA source, not independent generative reruns. Proper ICO container; explicit output sizing, optical/safe-area layouts, clipping and background choices.
- [ ] **BI-24 · Accessible visual brand guidelines.** Produce an actual illustrated brand book: primary/secondary mark, symbol/wordmark variants, spacing and minimum sizes, color/contrast roles, fonts and licenses, wrong-use examples, avatars, storefront/header/social/print examples and legal evidence state. The PDF must show marks, not just text instructions.
- [ ] **BI-25 · Interoperable tokens.** Adopt current DTCG-compliant canonical token model and Style Dictionary where appropriate; generate CSS/Tailwind, design-system and other platform derivatives without hand-maintained conflicting brand values. Existing atomic_branding outputs remain compatible or receive a deliberate migration plan.
- [ ] **BI-26 · Release artifact proof.** Manifest per version with hashes, owner approval, generator refs, licenses/notices, actual dimensions, linked brief/route/Visual DNA and every derivative's source. Atomic export, retry/rollback, zero contaminated files on refusal. Use a versioned immutable release, not a mutable summary of what supposedly exists.
- [ ] **BI-27 · DesignHub application review.** Compare Brand Studio, brand-book and mockup techniques; port only irreducible design/UX value. Do not fork CCF or create a competing logo studio.

**P3 completion:** prove at least one complete production-eligible kit by parsing, rendering and visual inspection of every required artifact and by reproducing derivative hashes from the approved identity.

## P4 — CDIO gates, similarity screening, benchmarks and institutional ratchet

Owner: **existing CDIO reviewer/scorer**, CCF knowledge_feed and normal CPP evidence owners.

- [ ] **BI-28 · Logo-specific quality lens.** Add a scoped review contract for correct spelling, 16/24/32 px (and larger application) small-size readiness, silhouette, negative space, monochrome, dark/light, print/web, correct file format, type/font/glyph, exact brand-token consumption, provenance and human sign-off. Reuse CDIO-01/05 mechanics; do not reweight all UI Design Quality Scores just to make logo scores pass.
- [ ] **BI-29 · Similarity risk with honest status.** Compare against a provenance-logged reference corpus (including competitors and lawfully usable index of known marks). A perceptual/embedding index such as FAISS is *screening*, not trademark clearance. Report corpus coverage, nearest examples, limitations and human/legal review obligations; PASS must not mean universal uniqueness.
- [ ] **BI-30 · Anti-generic transfer.** Audit Impeccable's critique/rules and the existing CDIO-06 anti-slop and VQ-6 swap test; strengthen identity-neutral pattern detection without banning valid category conventions. Separate symbol distinctiveness from UI logo-swap behavior.
- [ ] **BI-31 · Frozen cross-sector benchmark.** At least 12 briefs with brand creation vs refresh/keep, icon-only vs wordmark, multilingual text, fashion/luxury, software, hospitality, law/professional services, consumer products and adversarial imitation cases. Before/after baseline measures: complete release rate, independent blind preference and concept diversity, letter/symbol failures, small-size pass, legal risk triage, human iteration count, runtime, billed input/output tokens, provider spend, retries and reproducibility. Publish absolute denominator and uncertainty.
- [ ] **BI-32 · Make 16 red/green falsification scenarios executable.** See matrix below. Include live CLI path, file parsers and actual bytes. Run both passing and failing poles; forbid tests that turn green by shrinking tested scope.
- [ ] **BI-33 · Institutional writeback.** Feed observed defects, corpus misses, selected-vs-rejected concept reasons, provider failure economics, corrected vector/font bugs and reusable patterns to existing CCF feeds, PM-03, CO-12, UKDL and graph/knowledge owner APIs. Deduplicate and promote only evidence-supported changes; preserve rollback/retirement semantics and avoid reward-hacking a single style.
- [ ] **BI-34 · Automatic applicability.** Existing CLAUDE.md CCF triggers must activate for new logo/brand/identity work without the owner naming CCF or CDIO. Use progressive context disclosure; only load relevant skills and corpus, with budget/cost gate and abstention. Preserve human approval for chosen identity.
- [ ] **BI-35 · Independent review and rollback.** Reviewer distinct from implementer; prove gates refuse deliberately broken cases; record phase commit refs, changed files, real test counts, dependency posture, rendered evidence, provenance, revert path, and clear DONE/NOT_DONE status.

**P4 completion:** CDIO-quality evaluation and CCF-release policy agree, failures are measured, and a fresh agent can retrieve the accepted rules/fixtures without having to reread ten upstream repositories.

## Required falsification matrix (initial 16 tests)

The BR IDs and failure classes come from the [2026-10-21 audit](https://github.com/jacobo07/claude-power-pack/pull/8). These are **proposed tests; not executed yet**.

| Gate | Deliberate red condition | Required observable result |
|---|---|---|
| BR-01 | ImageArtifact.status=OK but zero image bytes / no source file | BRAND_KIT BLOCK; no SEALED |
| BR-02 | Corrupt/truncated or false-format raster/base64 | Explicit artifact validation failure |
| BR-03 | Valid text-only HTML/PDF without actual rendered mark | CONCEPT_REPORT possible; BRAND_KIT BLOCK |
| BR-04 | Scanner BLOCK before generate | Provider call count zero, zero spend |
| BR-05 | Missing, UNKNOWN or stale scan report on selected concept | Release UNASSESSED/BLOCK |
| BR-06 | WARN with no accountable human acceptance | Release BLOCK |
| BR-07 | Untrusted SVG containing script/event/foreignObject/external URI | Safe rejection, no fetch/execute |
| BR-08 | Malicious brand/path containing shell metacharacters or traversal | No shell execution / no outside writes |
| BR-09 | PNG file bytes saved as favicon.ico | Output parser FAIL |
| BR-10 | Unknown/unlicensed font, wrong glyphs or unsupported Unicode | No silent substitution; reject or document human-approved replacement |
| BR-11 | Two compilations from identical pinned deterministic inputs | Same exact export checksums; render equivalent |
| BR-12 | Blob at 16px or missing mono/small variant | No READY |
| BR-13 | Selected concept version differs from palette/asset source | Provenance consistency BLOCK |
| BR-14 | Source README asserts MIT while actual LICENSE contains Apache 2.0 | License conflict; source-code ingestion blocked |
| BR-15 | Provider failure mid-multi-concept generation | Partial state inspectable, never falsely complete |
| BR-16 | Generic/imitation candidate receives confident LLM praise | Independent comparison/human review vetoes unsupported promotion |

## Release readiness: state machine and evaluation truth

Possible outcomes, kept distinct:

- **UNASSESSED**: inputs or review evidence absent; no quality claim.
- **DRAFT_CONCEPT**: concept and/or preview for assessment; not a licensed, release-ready asset.
- **REVISE**: measurable technical failures, weak differentiation, or justified revision requests.
- **BLOCKED**: prohibited source, security issue, hard technical failure, explicit trademark blocker or broken output contract; no misleading exports.
- **REVIEW_REQUIRED**: subjective/sign-off, unresolved brand character, unreviewed similarity or rights clearance needs a qualified human.
- **BRAND_KIT_READY**: required assets validated and human decisions captured. This does **not** assert globally registrable trademark rights.
- **SEALED**: immutable release manifest with actual file hashes and reproducible source/version linkage; never assigned on metadata-only evidence.

Do not overload the historical CCF enum before a compatibility audit. These are *target semantics* to be mapped to the existing release contracts, not an instruction to break callers by renaming fields.

## Absorption protocol and acceptance ledger

For each of the ten upstream projects and each specialist implementation candidate, a future workstream must produce:

1. Source tree and exact pinned commit/asset versions; explicit repo status and upstream change watch only if justified.
2. Capability denominator constructed from relevant code, docs, tests and examples, not from title-tier assertions.
3. Applicable source rights: code license, data/font/icon/asset notices, patents/trademarks and distribution obligations, with contradictions surfaced.
4. Mapping from each capability to CPP's current owner and proposed OWNED/EXTEND/ADAPT/REFERENCE/REJECT/UNKNOWN decision.
5. Minimum runnable experiment and a **red test** for the failure it prevents; falsification is not a decorative checkbox.
6. Independent quality review; benchmark vs baseline including tokens, spend and human corrections.
7. Promotion only after real passing verification and documented rollback; otherwise keep as unverified proposal.

**No magic "100%":** completeness means every in-scope source capability has a justified disposition and proof link. It never means copying every source file or declaring third-party methods compatible without execution.

## Priority summary and release sequence

- **P0:** BI-00..07 — stop metadata-only/fake-ready kits, provider spend past BLOCK, missing scans and unsafe ingestion first.
- **P1:** BI-08..15 — strategic brand intelligence, multi-territory creative reasoning, cohesive identity sets and typed Visual DNA.
- **P2:** BI-16..21 — deterministic SVG, safety, multilingual type, color and optional vector tracing.
- **P3:** BI-22..27 — safe multi-format outputs, illustrated brand book, DTCG design tokens and reproducible releases.
- **P4:** BI-28..35 — CDIO-scoped review, similarity-screening honesty, 16 negative tests, cross-sector benchmark, automatic routing and institutional promotion.

All BI items start **OPEN / NOT IMPLEMENTED**. Prior research is recorded, but no P0–P4 item becomes DONE from this backlog file, the user-provided dataset, or the draft audit PR alone. Inspect real HEAD, state and test evidence before promoting status.

## Stop conditions / warnings

- Missing source assets, unreadable output or a claimed PDF that doesn't depict selected mark.
- Provider calls after a deterministic risk BLOCK.
- Conflicting README/LICENSE or unknown license for copied code, source icons or font outlines.
- Untrusted paths passed to a shell, remote npx fallback executed without consent, SVG with active markup.
- CCF and CDIO double-counting a metric or maintaining divergent brand truth.
- Fabricated claims of improved originality, revenue/conversion or legal clearance.
- Only one narrow aesthetic family succeeding while the benchmark denominator secretly shrinks.
- Excessive multi-agent/token costs not justified by measured output quality; obtain real CPP budget data.
- Unobserved tests reported as green; source README's benchmark reported as local result.

## Execution handoff

**Execution mode:** reality scan → red tests of observed P0 defects → minimal fixes in existing CCF → reverify old CCF/CDIO/CDICF owners → integrate creative/value sources in small, independently reviewed increments → measured promotion.

**Working tree policy:** don't edit concurrently-owned paths on the same worktree, don't overwrite active changes; use an isolated branch/worktree and inspect current HEAD before each phase. Avoid changing sealed CDIO-00..09 doctrine without an owner-approved, evidence-backed amendment.

**Artifacts expected per phase:** source/owner matrix, source capability denominator, pinned license/NOTICE ledger, phase patch with tests, actual rendered and parsed asset proof, before/after scorecard, rollback proof and phase verdict with unresolved unknowns.

**Related documents:**
- [Audit PR #8](https://github.com/jacobo07/claude-power-pack/pull/8) — inspected core-source evidence, existing CCF truth gaps and 16 BR cases.
- [CDIO-00 kernel](https://github.com/jacobo07/claude-power-pack/blob/main/vault/knowledge_base/cdio/CDIO-00-design-intelligence-kernel.md) and [CDIO-05 review](https://github.com/jacobo07/claude-power-pack/blob/main/vault/knowledge_base/cdio/CDIO-05-design-review-pipeline.md).
- [CCF architecture](https://github.com/jacobo07/claude-power-pack/blob/main/vault/plans/CCF_ARCHITECTURE.md), [CCF quality gates](https://github.com/jacobo07/claude-power-pack/blob/main/vault/plans/CCF_QUALITY_GATES.md), [CCF learning](https://github.com/jacobo07/claude-power-pack/blob/main/vault/plans/CCF_KNOWLEDGE_SYSTEMS.md).
- [CDICF ownership audit](https://github.com/jacobo07/claude-power-pack/blob/main/vault/audits/cdicf/CPP_DESIGN_OVERLAP_MAP.md).
