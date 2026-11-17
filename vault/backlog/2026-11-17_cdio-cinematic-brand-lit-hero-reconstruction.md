# Backlog — CDIO Cinematic Brand-Lit Heroes (VP-019)

**Created:** 2026-11-17.  
**Status:** RESEARCH EVIDENCE RECORDED; ENGINEERING AND BROWSER VALIDATION NOT IMPLEMENTED.  
**Source:** user-supplied 18.9 s portrait reference; see [REF-BRAND-LIGHT-001](../knowledge_base/visual-patterns/evidence/REF-BRAND-LIGHT-001/OBSERVATION.md).  
**Reusable pattern:** [VP-019](../knowledge_base/visual-patterns/cinematic-brand-lit-hero.md).  
**Owner boundary:** CDIO-06 chooses aesthetic direction; visual-patterns KB specifies technique; DESIGN.md owns palette/experience; CCF obtains/provisions original assets where necessary; CDICF selects licensed implementation dependencies; frontend/runtime owner implements; CDIO reviewer judges actual output.  
**Related:** [21-resource design absorption](2026-10-30_cdio-21-design-resources-universal-absorption.md), [brand identity](2026-10-21_cdio-brand-identity-logo-absorption.md), [ASTRYX](2026-11-12_meta-astryx-complete-cdio-absorption.md). No new cinematic design OS or global shader engine.

## Objective

Make CDIO capable of *selecting and producing through existing implementers* premium photographic or rendered heroes where a brand accent physically informs plausible scene lighting, while real UI remains accessible, performant, editable and verifiably functioning.

The three required source variants:

- **Photographic environment:** dark garden architecture with sunrise/sunset-like local illumination; mask/grade sky and foliage separately, preserve scene geometry.
- **Refractive object:** glossy suspended droplet with specular rim, internal refraction-like highlight and matching ground halo, ideally pre-rendered, not fake CSS-only refractive physics.
- **Geometric emissive accent:** dark architectural roof with a line accurately registered to a roof edge plus controlled glow; maintain crop alignment across responsive variants.

The methods are reusable **grammars**, not copies of Mossgrove/Tidewell/Blackridge trade dress, names or their original site assets.

## Atomic work items

- [ ] **VPL-01 — Reality Scan.** Verify current CDIO-06, VP-008, VP-015, CDIO-07, CCF, CDICF, DESIGN.md and available renderer ownership; reject duplications and discover prior similar patterns.
- [ ] **VPL-02 — Authorized scene corpus.** Source or create three original/cleared test subjects with provenance, explicit rights, source resolution, optional masks/depth/reflectance, and responsive safe areas; do not vendor video screenshots.
- [ ] **VPL-03 — Brand-lit scene contract.** Bind a typed scene specification to approved DESIGN.md color roles, accent zone, light source, depth/subject mask, focal point, photo vs 3D source, image source metadata, contrast scrim, bounds, responsive asset variants and failure states. Reuse owner schemas.
- [ ] **VPL-04 — Garden lane.** Build neutral/accent export pair with localized horizon/step/foliage light. Compare against globally tinted control. Avoid geometry changes disguised as a simple theme variant.
- [ ] **VPL-05 — Droplet lane.** Build original/licensed high-fidelity refractive visual (offline 3D or compositing), control rim/reflection/floor light and eliminate unnecessary real-time shaders if image-only is sufficient. Verify same droplet geometry across colors.
- [ ] **VPL-06 — Roof lane.** Build camera-registered emissions along specified gable/roof geometry with sharp core, restrained halo and plausible bounce. Separate path alignment from cosmetic color and test crop transformations.
- [ ] **VPL-07 — DOM and responsiveness.** Implement a complete functional landing hero with semantic real text, navigation, CTA destinations, proof labels requiring real evidence, keyboard/focus, tablet/mobile art direction, contrast and screen reader behavior. No baked-in lettering.
- [ ] **VPL-08 — Performance and accessibility.** Measure encoded responsive assets, LCP/CLS/INP, page load, CPU/GPU, flash risk, high contrast and reduced motion. Choose least-expensive adequate rendering method and a static fallback.
- [ ] **VPL-09 — Evidence-based selector.** Route qualified requests for hero photographic atmospheres to VP-019 using existing design-index / CDIO-06, with no auto-adoption on dashboards/checkout/forms, and no forced dependencies or hallucinated provenance.
- [ ] **VPL-10 — Evaluation and ratchet.** Freeze 3 subjects × 2 techniques and test on actual target viewports. Blind compare fidelity and relevance, verify output and source-to-consumer path, document negative cases, then consider promotion only after independent observations and existing baseline governance.

## Initial negative tests — NOT EXECUTED

1. **V-VPL-01:** A plain red/orange rectangle over every pixel is misidentified as locally plausible illumination → selector/reviewer detects unsupported physical claim or fidelity failure.
2. **V-VPL-02:** Roof emission shifts off the roofline at mobile crop → responsive alignment FAIL.
3. **V-VPL-03:** Text readability evaluated only on the darkest part of an image instead of actual text region → contrast FAIL.
4. **V-VPL-04:** CSS filter alters the real product color in a context where accuracy matters → appropriateness BLOCK.
5. **V-VPL-05:** Full-screen WebGL used despite static-equivalent imagery and low-power constraints → cost/performance decision must be justified or prefer static.
6. **V-VPL-06:** Claim of 3D source or live animated palette based only on original social-video frames → evidence UNKNOWN, not PASS.
7. **V-VPL-07:** Hero buttons exist but have no real destinations/actions → Production Reality BLOCK.
8. **V-VPL-08:** Unauthorized external reference image or protected wordmark shipped in test/site → rights BLOCK.
9. **V-VPL-09:** Two independently generated “same building” states move structural geometry while presented as pure recoloring → identity/fidelity FAIL.
10. **V-VPL-10:** New design pattern is merely noted in a doc with no agent retrieval path, then claimed operational → reachability FAIL.

## Done-gate

- Real examples for all three techniques built from approved assets and real text, with source manifest.
- Actual browser screenshots at 360/390, 768 and 1440+; compare both palette states against frozen geometry and controls.
- Functional links/buttons and keyboard/focus proven; accessible static fallbacks; no unsupported hover-only content.
- Tests of asset size/decoding and current CPP CWV floor; no false production-ready claims from social mockups.
- Evidence that a *fresh CDIO-assisted agent* can retrieve this VP-019 pattern and select/refuse it based on a task.
- Independent quality comparison against flat-tint controls, failure tests and concrete review receipts.
- Knowledge Vault and UKDL candidates only for transferable **proven** faults; avoid promoting one reference into a constitutive baseline.

**State at backlog creation:** VP-019 and observational evidence are documented; no new hero renderer, source art, website, browser verification or activation baseline is claimed.
