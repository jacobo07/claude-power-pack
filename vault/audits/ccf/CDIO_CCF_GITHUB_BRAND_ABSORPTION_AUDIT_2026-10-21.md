# CDIO × CCF — GitHub Brand Identity Absorption Audit

**Date:** 2026-10-21  
**Status:** EVIDENCE-BASED PROPOSAL / NOT IMPLEMENTED  
**Scope:** four upstream repositories, current CPP ownership and highest-risk integration seams.  
**Method:** GitHub source-tree and file-content inspection at pinned refs. No clone, dependency install, actual model call or test execution was performed. Repository documentation and CI configuration are evidence of claims and intended tests, **not** proof that those tests passed in this audit.  
**Target outcome:** raise CPP's brand/logo construction baseline without adding a second design authority, CCF or memory layer.

## 0. Decision

**Disposition: EXTEND EXISTING OWNERS + SELECTIVE CODE/KNOWLEDGE ABSORPTION.**

Do not build a parallel "Brand Identity OS" or a new CDIO owner.

1. **CCF (modules/ccf)** is the only owner of brief → conceptual routes → generation/vector construction → artifactual identity kit → release.
2. **CDIO (modules/cdio; CDIO-00..09)** owns design quality standards, evaluation and abstention; extend existing review mechanics, not competing scorers.
3. **CDICF (modules/cdicf) / lib/license_gate.js** owns third-party components, provenance, redistribution posture and applicability selection.
4. **Project DESIGN.md**, governed by governance/DESIGN_GOVERNANCE.md and modules/design-md, is the local approved visual contract; a CCF Visual DNA may be its typed upstream input, not a conflicting second project SSOT.
5. **Existing Knowledge Vault/CCF knowledge feeds, PM-03, CO-12, provenance and ratchet owners** own lessons and metrics; add events and verified patterns through existing owners, never a second institutional memory store.

**Priority reversal:** before making new logos, fix the production false-positive in CCF: it may SEALED a brandkit while retaining no real generated image in its persisted artifact record and embedding no logo into the PDF.

## 1. CPP observed inventory

- [CLAUDE.md](https://github.com/jacobo07/claude-power-pack/blob/main/CLAUDE.md) explicitly activates `cpp creative` on new brand/logo/visual-identity requests. This is already the canonical execution route.
- [CDIO-00](https://github.com/jacobo07/claude-power-pack/blob/main/vault/knowledge_base/cdio/CDIO-00-design-intelligence-kernel.md) describes CDIO as a cross-cutting design-intelligence layer, **not the author** of a product. Valid review findings require observable criteria.
- [CDIO-01](https://github.com/jacobo07/claude-power-pack/blob/main/vault/knowledge_base/cdio/CDIO-01-visual-intelligence-engine.md) governs typography, color, spacing, hierarchy.
- [CDIO-05](https://github.com/jacobo07/claude-power-pack/blob/main/vault/knowledge_base/cdio/CDIO-05-design-review-pipeline.md) + [scorer.py](https://github.com/jacobo07/claude-power-pack/blob/main/modules/cdio/scorer.py) own deterministic UI design quality and the ≥80, zero-critical approval gate. Existing surface score must **not** substitute for a specific logo/artifact release contract.
- [CDIO-06](https://github.com/jacobo07/claude-power-pack/blob/main/vault/knowledge_base/cdio/CDIO-06-aesthetic-families.md) owns generative aesthetic families, not a full symbolic brand research or SVG editor.
- [CCF](https://github.com/jacobo07/claude-power-pack/tree/main/modules/ccf) already implements contract_engine, config_schema, prompt_compiler, model_adapter, evaluation_engine, artifact_compiler, trademark_scanner, release_manager, knowledge_feed and CLI.
- [atomic_branding.py](https://github.com/jacobo07/claude-power-pack/blob/main/tools/atomic_branding.py) creates deterministic CSS/Tailwind and motion tokens from text; it is **not** a vector logo construction engine.
- [CDICF](https://github.com/jacobo07/claude-power-pack/tree/main/modules/cdicf), [design_index.py](https://github.com/jacobo07/claude-power-pack/blob/main/tools/design_index.py) and [license_gate.js](https://github.com/jacobo07/claude-power-pack/blob/main/lib/license_gate.js) already own component retrieval/manifests and license filtering.
- [Prior CDICF overlap audit](https://github.com/jacobo07/claude-power-pack/blob/main/vault/audits/cdicf/CPP_DESIGN_OVERLAP_MAP.md) measured strong existing coverage and explicitly listed CCF as a creative owner. Respect its reuse-before-create precedent.

## 2. P0 observed correctness gaps in CCF

### CCF-GAP-01 — Generated visual bytes are discarded before downstream compilation (HIGH, source-confirmed)

[model_adapter.py](https://github.com/jacobo07/claude-power-pack/blob/main/modules/ccf/model_adapter.py) makes ImageArtifact.bytes_ available (base64-encoded content per adapter comment). In [cli.py](https://github.com/jacobo07/claude-power-pack/blob/main/modules/ccf/cli.py), `_artifact_to_record` writes status/provider/model/format/resolution etc **without bytes or a durable asset path**; `_ArtifactRecordView` restores only status. The package flow compiles from these metadata-only records. Thus no production-ready logo source is available to the artifact compiler from that path.

**Fix contract:** after provider return, verify and decode according to declared encoding; validate actual magic/dimensions and bounded size; persist bytes atomically under project-contained safe paths; record checksum, format, dimensions, generator/version, prompt/spec ID and provenance; reload these persisted bytes when compiling. A status string alone is never evidence of an image.

### CCF-GAP-02 — Text-only kit may receive SEALED (HIGH, source-confirmed; runtime reproduction pending)

[artifact_compiler.py](https://github.com/jacobo07/claude-power-pack/blob/main/modules/ccf/artifact_compiler.py) creates a textual HTML and handwritten text-only PDF, explicitly notes image XObjects are deferred, and sets `built=True` solely when an ImageArtifact has status OK. [evaluation_engine.py](https://github.com/jacobo07/claude-power-pack/blob/main/modules/ccf/evaluation_engine.py) passes a bundle if it was marked built. [release_manager.py](https://github.com/jacobo07/claude-power-pack/blob/main/modules/ccf/release_manager.py) may SEALED that bundle after selection/trademark checks. [test_ccf.py](https://github.com/jacobo07/claude-power-pack/blob/main/modules/ccf/test_ccf.py) uses ImageArtifact(status=OK) with no bytes and asserts successful PDF/release.

This conflicts with the visual brand-kit expectations in [CCF_QUALITY_GATES.md](https://github.com/jacobo07/claude-power-pack/blob/main/vault/plans/CCF_QUALITY_GATES.md).

**Fix contract:** distinguish CONCEPT_REPORT (textual) from BRAND_KIT (actual rendered/vector assets). BRAND_KIT release requires all manifest-required files to exist, pass format parsing, be visualized/rendered successfully, and match the approved concept/version. PDF preview must actually depict the logo and use licensed/verified typography. Missing assets ⇒ INCOMPLETE/BLOCK, never SEALED.

### CCF-GAP-03 — Blocking trademark scan does not stop provider call (HIGH cost/control seam, source-confirmed)

In [cli.py cmd_generate](https://github.com/jacobo07/claude-power-pack/blob/main/modules/ccf/cli.py), a scanner BLOCK sets `any_block=True`, but no continue/early return prevents `adapter.generate` for that concept. The CLI returns blocked **after** provider work. Policy and spend are not actually stopped before execution.

**Fix contract:** BLOCK is a precondition that prevents any provider invocation, file creation or export for the blocked concept, with a negative provider-call assertion and actual cost accounting. WARN must have documented policy for preview vs paid generation and release.

### CCF-GAP-04 — Absent scan can bypass positive-evidence requirement (HIGH confidence seam, source-confirmed)

In [release_manager.py](https://github.com/jacobo07/claude-power-pack/blob/main/modules/ccf/release_manager.py), missing `scan_verdicts[selected_id]` yields `verdict=None`; code refuses BLOCK and unacknowledged WARN but does not require explicit PASS or acknowledged WARN. With otherwise passing inputs this permits SEALED without scan evidence.

**Fix contract:** release requires an explicit, fresh, versioned PASS or reviewed WARN; unknown/absent/stale/error = UNASSESSED and cannot be marked brand-ready. Human acknowledgment of a *risk* is not legal clearance.

### CCF-GAP-05 — Creative/evaluation vocabulary is too shallow for differentiated identity (FUNCTIONAL GAP)

[CreativeSpecification](https://github.com/jacobo07/claude-power-pack/blob/main/modules/ccf/contract_engine.py) captures brand_name, industry, audience, values, constraints, references, optional mood_axis and deadline. It does not require competitor territory analysis, differentiated symbolic mechanisms, multilingual glyph needs, small-size variants, protected wordmark, or approval/license evidence. [evaluation_engine.py](https://github.com/jacobo07/claude-power-pack/blob/main/modules/ccf/evaluation_engine.py) explicitly does **not** perform pixel/OCR verification, and current checks evaluate prompt text/config and scanner status. [trademark_scanner.py](https://github.com/jacobo07/claude-power-pack/blob/main/modules/ccf/trademark_scanner.py) includes only three seed marks (Airbnb, Nike, Apple), compares icon descriptions via SequenceMatcher, and expressly disclaims visual similarity and legal clearance.

**Fix contract:** add only missing typed fields, evidence-backed candidate research and differentiated-route metadata to CCF, and a distinct logo-quality lens through existing CDIO scorer/reviewer. Maintain two epistemically separate outcomes: internal visual-similarity **screening** and independent legal clearance when necessary. No automatic declaration of trademark safety.

## 3. Four upstream dispositions and exact snapshot

Source snapshots inspected via GitHub API (commit ref; code paths from the same selected default branch at retrieval time):

| Source | Ref | License evidence | Disposition | Reason |
|---|---|---|---|---|
| [fatihaydost/brand-identity-skill](https://github.com/fatihaydost/brand-identity-skill) | 532742d7477dba3b744433adf92845642953dc28 | LICENSE MIT; substantial THIRD_PARTY_NOTICES; font/trademark caveats | EXTEND CCF/CDIO; selectively port proven tests/tools after ledger | Strong cohesive concept/type/color method; 16/32px and glyph/color checks; claims 474 tests and CI; self-reported workflow around 40.5 turns/0.86M billed-input-equivalent tokens is not an acceptable default runtime budget. |
| [moayadMoatamed/Marker-AI](https://github.com/moayadMoatamed/Marker-AI) | d14340c372730899950419dd9c0dd34b31116d6c | LICENSE text Apache-2.0, README says MIT; GitHub API reports NOASSERTION | KNOWLEDGE REFERENCE ONLY until provenance discrepancy resolved; no copied source | Rich conceptual taxonomy (12 techniques) and semantic specificity/swap tests, but LLM self-critique is not objective rendered-image measurement. |
| [xianshi3/sigilgen](https://github.com/xianshi3/sigilgen) | c3f605b7864b41a3319fc25dacca6174b0aa897b | LICENSE MIT | PILOT isolated deterministic logo engine adapter | SVG allowlisted serializer, offline/no runtime deps, 5 engines, 33 palettes, 18 font families/468 outlines, 70 icons, 34 moods, deterministic-output hash verification. Inspect rights/provenance of compiled font glyphs and supported language coverage before distribution. Determinism ≠ originality. |
| [mcpware/logoloom](https://github.com/mcpware/logoloom) | 9e5de3e95d24fd86ea9af3cbe77749df088ad176 | LICENSE MIT | EXTRACT EXPORT PROFILE / DESIGN IDEAS ONLY; DO NOT RUN AS DEFAULT DEPENDENCY | File export concept useful, but raw PNG is written to favicon.ico; XML/SVG splitting via regex; supplied imagePath concatenated into shell execSync; fallback downloads/runs CLI via npx -y; text-to-path silently falls back to bundled Inter. Rebuild dangerous functions with safe primitives, do not blindly vendor. |

References:
- brand-identity: [SKILL.md](https://github.com/fatihaydost/brand-identity-skill/blob/532742d7477dba3b744433adf92845642953dc28/skills/brand-identity/SKILL.md), [testing](https://github.com/fatihaydost/brand-identity-skill/blob/532742d7477dba3b744433adf92845642953dc28/docs/testing.md), [licenses/notices](https://github.com/fatihaydost/brand-identity-skill/blob/532742d7477dba3b744433adf92845642953dc28/THIRD_PARTY_NOTICES.md).
- Marker: [12-technique search](https://github.com/moayadMoatamed/Marker-AI/blob/d14340c372730899950419dd9c0dd34b31116d6c/backend/src/pipeline/nodes/technique_search.py), [synthesis](https://github.com/moayadMoatamed/Marker-AI/blob/d14340c372730899950419dd9c0dd34b31116d6c/backend/src/pipeline/nodes/synthesize.py), [critique](https://github.com/moayadMoatamed/Marker-AI/blob/d14340c372730899950419dd9c0dd34b31116d6c/backend/src/pipeline/nodes/critique.py), [LICENSE](https://github.com/moayadMoatamed/Marker-AI/blob/d14340c372730899950419dd9c0dd34b31116d6c/LICENSE) vs [README](https://github.com/moayadMoatamed/Marker-AI/blob/d14340c372730899950419dd9c0dd34b31116d6c/README.md).
- Sigilgen: [generate.ts](https://github.com/xianshi3/sigilgen/blob/c3f605b7864b41a3319fc25dacca6174b0aa897b/src/generate.ts), [serializer.ts](https://github.com/xianshi3/sigilgen/blob/c3f605b7864b41a3319fc25dacca6174b0aa897b/src/serializer.ts), [check-determinism](https://github.com/xianshi3/sigilgen/blob/c3f605b7864b41a3319fc25dacca6174b0aa897b/scripts/check-determinism.mjs).
- LogoLoom: [export-brand-kit](https://github.com/mcpware/logoloom/blob/9e5de3e95d24fd86ea9af3cbe77749df088ad176/src/tools/export-brand-kit.mjs), [image-to-svg](https://github.com/mcpware/logoloom/blob/9e5de3e95d24fd86ea9af3cbe77749df088ad176/src/tools/image-to-svg.mjs), [text-to-path](https://github.com/mcpware/logoloom/blob/9e5de3e95d24fd86ea9af3cbe77749df088ad176/src/tools/text-to-path.mjs), [MCP exposure](https://github.com/mcpware/logoloom/blob/9e5de3e95d24fd86ea9af3cbe77749df088ad176/src/server.mjs).

**Legal and security policy:** permissive repo license never transfers trademark rights or automatically authorizes bundled fonts, assets, icon data, training data or generated third-party material. All copy/vendor decisions require pinned upstream license evidence and verified dependency/asset notices. Marker-AI's LICENSE/README contradiction is a STOP for literal code adoption until reconciled.

## 4. Proposed semantic extension: Brand Concept → Visual DNA → Verified Assets

CCF must own a versioned typed identity object (implementation/schema decided after Reality Scan), with fields needed for:

- Brand truth: audience, category, positioning, values, geographic/language scope, competitor references with provenance, avoid-cliches, exclusions.
- Concept identity: territory ID, specific evidence-backed *brand fact*, symbolic mechanism, one-sentence insight, typographic strategy, basic geometry, concept comparison axes and reject reasons.
- Visual DNA: typography roles and font license refs, color roles, silhouette/shape rules, monogram/small-size rules, wordmark/protected spelling, light/dark/mono semantics, image and motion policy, accessibility floors.
- Artifacts: source/vector authority, asset types, explicit viewBox, rendered PNGs, print and social derivatives, hash, dimension, real parser result, source-generator ref, selected concept version.
- Evaluation: human judgment vs measured checks, abstention on missing evidence, similarity-screening candidates, trademark review state, approval role/timestamp, source provenance.
- Delivery: one sealed release manifest with required artifacts explicitly enumerated, no fictional "31 files" guarantee and no mutable latest pointer without versioned immutable evidence.

**Boundary:** project DESIGN.md remains the project consumption authority; compile its approved palette/type/tokens from the brand object. Avoid storing independent hand-edited parallel palettes in CCF, atomic_branding.py and DESIGN.md.

**Research dependency:** CrawlOS/evidence owners can provide competitor/category evidence; CCF records its references, not a second crawler.

## 5. Implementable sequence, each phase evidence-gated

**P0 — Repair existing CCF quality truth before adding features.** Red tests for GAPS 01–04, then minimal correction of durable visual asset persistence, tested package fidelity, scan veto before provider calls, scan positive-evidence at release. Keep old text reports clearly named. Explicitly test the real CLI path, not only helper tests with invented success metadata. Preserve existing working UI/CDIO behavior.

**P1 — Add creative intelligence, not a new agent.** Build a concept-route extension from Marker-AI's technique taxonomy (provenance-resolved if code copied) and brand-identity-skill's cohesion/decision-axis protocol. Require 3 distinguishable directions except when explicitly constrained; concepts tied to distinct brand facts, with own reject reason and a no-symbol / typography-only alternative when suitable. Integrate via existing CCF brief/config/prompt interfaces. Human selects; model judgment never masquerades as automated evidence.

**P2 — Isolated vector-first deterministic baseline.** Pilot Sigilgen behind CCF's model/generator adapter boundary, as optional generator (not global default). Pin code and licenses, test malicious SVG input, full Unicode/font behavior and transparent/mono/small-size handling. Compare with selective image generation on the same briefs. Keep SVG as versioned source authority when possible; raster-to-vector is a fallible path requiring QA.

**P3 — Release-grade brand package.** Implement a safe, deterministic identity asset exporter under CCF. Derive useful LogoLoom *output profiles*, not its unsafe implementation. Use SVG tree/DOM parsing; safe file writes inside worktree; spawn subprocesses without invoking a shell; proper ICO format parsing, actual rendering and hash validation; constrain dimensions/file sizes; license gate fonts/icons. Ensure the logo appears on the PDF and image previews and exports match the approved brand tokens. Record outputs in a machine-verifiable release manifest.

**P4 — CDIO verification + institutional ratchet.** Reuse CDIO-01/05 measurable floors and CDIO-06 anti-default conventions. New logo-specific measurements must include 16/24/32px render readability, monochrome, text integrity, glyph coverage, basic silhouette/safe-area, render parity and accessibility applications. Symbol distinctiveness/emotional fit is a calibrated human/independent critique backed by references, not a fabricated deterministic number. Connect known failure modes to CCF knowledge_feed, CO-12/PM-03/UKDL only where owner APIs already exist. Promote baseline improvements only with measured benefit over prior CPP baseline.

## 6. Red/green acceptance matrix — proposed, NOT run

| ID | Negative test required | Expected refusal/result |
|---|---|---|
| BR-01 | ImageArtifact status OK, bytes absent and no persisted source asset | BRAND_KIT BLOCK; no SEALED |
| BR-02 | Corrupt/truncated/wrong-magic PNG or base64 | Artifact validation FAIL |
| BR-03 | HTML/PDF is technically valid but contains no visual mark | BRAND_KIT BLOCK; CONCEPT_REPORT may remain valid |
| BR-04 | Trademark scanner returns BLOCK | Provider call count **zero** for the concept |
| BR-05 | Selected concept's scanner report missing/UNKNOWN/stale | Release BLOCK/UNASSESSED |
| BR-06 | WARN without signed, versioned human acknowledgement | Release BLOCK |
| BR-07 | Valid SVG containing script, external ref, or unsupported tags | Sanitizer refuses; no execution/fetch |
| BR-08 | Brand name or source file path contains shell metacharacters or path traversal | Contained safely; no shell spawn or outside writes |
| BR-09 | Favicon.ico carries PNG magic bytes without ICO container | Export gate FAIL |
| BR-10 | Requested font missing or unlicensed | Explicit unsupported or fallback requiring approval, no silent wordmark mutation |
| BR-11 | Same pinned contract/seed/model-independent inputs compiled twice | Byte-identical deterministic export hashes; rendered equivalence |
| BR-12 | Visual mark illegible at small sizes or absent mono version | Not release eligible until fixed/approved exemption |
| BR-13 | Export built from stale concept selection or diverging palette tokens | Fail provenance/integrity check |
| BR-14 | Upstream README says MIT but license file says Apache 2.0 | LICENSE_CONFLICT; no code absorption |
| BR-15 | Image-generation provider fails after one success | No fabricated complete kit; partial artifacts remain inspectable |
| BR-16 | Adversarial "popular generic" logo receives high LLM self-rating | Independent comparison/human evaluation prevents automatic promotion |

**Benchmark denominator:** one frozen cross-sector set (at least 12 briefs) with category and languages intentionally varied; include existing-logo-keep, typography-only, icon-only, new brand, refresh, premium, legal services, hospitality, consumer goods and software. Compare before/after CCF on measured release completeness, rule refusals, expert blind preference, concept diversity, human correction cycles, token usage, runtime, actual provider spend and operational failure rate. Do not set a commercial efficacy claim (e.g. increased CTR) without a real field study and controls.

## 7. Hard rules

- Never SEALED on metadata-only evidence; artifact presence and visual decode are release preconditions.
- Never spend a provider call after a deterministic BLOCK for that concept.
- Never treat a pass against a three-mark corpus as trademark clearance.
- Never let LLM quality scores equal measured rendered quality.
- Never copy code when LICENSE and README conflict without a legal provenance decision.
- Never execute downloaded scripts, shell strings or remote npx fallbacks from untrusted user brand assets.
- Never expand the global CDIO score formula solely to make brandkit approval look compliant; create a scoped brand-artifact lens wired to existing CDIO owners.
- Never confuse VQ-6's UI logo-swap identity review with a real trademark/distinctiveness search.
- Never manufacture a "100% absorbed" claim: build a source-capability denominator, each entry annotated OWNED / EXTEND / COPY-ADAPTER / REFERENCE / REJECT / UNKNOWN, with tests and evidence for each promotion.
- Never claim benchmark results from README/test files as though CPP ran them.

## 8. Remaining evidence and implementation boundaries

Not yet verified in this audit: actual unit/integration test passes on Windows/Linux; provider model availability/API latency/cost; current runtime setup or agent CLI activation across projects; third-party font/icon dataset redistribution rights; real legally relevant marks database coverage; vulnerability scan of transitive dependencies; accessibility quality of rendered candidate output; browser/print export parity.

All code and changes belong to a **new isolated worktree/branch** with existing writers respected. Before implementing: fresh Reality Scan, inspect uncommitted changes and existing active plans, establish exact test denominator, freeze failure evidence; do not overwrite concurrent work.

## 9. Proposed delivery proof

A future implementation is complete only with: a named single source owner for each new capability; four upstream per-capability disposition manifests with hashes and licenses; red tests that demonstrate the previously failing behaviors; green CI and real artifact render checks; at least one actual brandkit package whose SVG/PDF/PNG/ICO are valid and visually inspected; independent review; rollback proof; before/after benchmark with absolute denominators; and a documented CCF→CDIO→DESIGN.md→knowledge-feed trace.

**Final status of this artifact:** AUDIT RECORDED, 0 external repositories installed, 0 production code changes, 0 tests executed, 0 brandkits generated, 0 capability promotions. Proposal only; no production-readiness claim.
