---
id: VP-019
name: Cinematic Brand-Lit Hero — Environmental Accent Propagation
type: pattern
domain: visual-patterns
status: active
evidence_level: research
provenance: REF-BRAND-LIGHT-001
---

# VP-019 — Cinematic Brand-Lit Hero (Environmental Accent Propagation)

## Distinction and ownership

**CDIO-06** judges whether the visual family fits the product; this entry governs the **reproducible art-direction/compositing method** for an image-backed hero. **DESIGN.md** owns the project's actual approved colors and experience contract. **CCF** owns brand assets if the project requires original art. This entry does **not** create an alternate theme compiler, an image generator, an animation engine, or a new aesthetic family.

Unlike [[duotone-image-overlay]] (VP-008), this technique **does not recolor every shadow/highlight**. It preserves a readable, physically coherent scene and directs the brand accent only to plausible light sources, reflections or designed emissive edges. Unlike [[grainy-gradient-background]] (VP-015), the ground is a photographic or rendered scene rather than a CSS gradient with noise.

## Eje

E — Hero photographic/3D art direction; environment lighting, controlled accent and image composition. First reference: REF-BRAND-LIGHT-001.

## Observed origin

User-supplied 18.9-second portrait video inspected 2026-11-17. Three static-like website mockups cycle from a neutral/base palette to an accent-lit state. The visible scenes do **not** expose source HTML, CSS, images, original production pipeline, functioning controls, responsive behavior, or proof of interactive animation. Their static content has closely corresponding geometry across the compared color states. Observations, hex colors, timecodes and inference boundaries: [[evidence/REF-BRAND-LIGHT-001/OBSERVATION]].

## Core mechanism

1. **Define the role of the image.** Choose subject, desired emotion and physical context; do not select a dramatic photo before knowing whether the audience needs quiet trust, urgency, luxury or direct information. Preserve the identity already approved in DESIGN.md.
2. **Freeze composition.** Plan horizon, main subject, eye path, readable negative space, camera height, focal point, safe crops and layout anchors **before** generating color variants. The hero headline and navigation remain real accessible HTML rather than text baked into the photograph.
3. **Obtain an authorized base scene.** Photograph, commission/produce an original render, license an image, or generate new visual assets where allowed. Record source, rights and transformation history. Do not copy the reference mockups as commercial art.
4. **Separate scene controls.** Treat background plate, subject/object, depth or semantic masks, ambient exposure, localized light sources, specular/reflection channels, emissive edges, vignette/scrim and texture as conceptually separate layers, even if the final web asset is pre-rendered and flattened.
5. **Propagate brand color into plausible illumination.** Keep accent localized to where light would exist: the dusk horizon and illuminated steps, reflections and caustic-like ground glow beneath glass/water, or a designed glowing architectural edge. Accent hue in physical light is allowed to shift locally with exposure/material: do not force every pixel to the UI hex.
6. **Balance against UI.** Reserve the highest-contrast interface accent for the primary action, brand glyph or a very small number of details. Maintain clear typographic hierarchy and large negative space; distinguish foreground from an atmospheric but subdued background.
7. **Render/ship the cheapest adequate representation.** Default to optimised static photography/3D render plus simple CSS gradients/scrim. Use image variants with a cross-fade only when the product needs a live palette transition. Use SVG masks, Canvas/WebGL or real-time 3D only when interaction, responsiveness or independent recoloring warrants their higher cost and complexity.
8. **Check the real rendering.** Validate screenshot across viewport, color mode, DPI and content/locale, with genuine web text and working CTAs. Do not infer that a social video of a mockup proves a functioning site.

## Three source-grounded recipes

### E1 — Landscape: dusk/ambient relighting

Reference style: Mossgrove gardens, dark emerald scene, warm orange horizon and steps. Preserve garden silhouettes, depth and natural shadow order. Localized color should plausibly emanate from sunset and low architectural lights; avoid uniform orange filters over all foliage. Preferred path: original/licensed scene, authored spatial lighting/masks, baked alternate grade when a toggle is desired. CSS can add subtle localized transparent gradients and text scrims but cannot independently reconstruct light bounced onto occluded plants from a single flat photo.

### E2 — Hero object: refractive specular accent

Reference style: Tidewell plumbing, transparent suspended droplet over dark navy field. The coral appearance is on object edges, internal reflection/refraction zones and the floor halo, rather than a filled flat orange silhouette. Preferred path: physically based offline rendering or controlled image compositing, with plausible transparent material, multiple rim lights and floor illumination, then export a licensed, optimized static image. Blender render passes (environment, specular, emission, shadow/ambient occlusion) can be composited separately when needed. CSS-only filters cannot replace geometry/material-dependent refraction.

### E3 — Architecture: designed emissive contour

Reference style: Blackridge roofing, dark house and overcast sky, thin red highlight along one roof gable. Preserve building edges and masonry/shingle textures. Put emission on a correctly registered geometric contour, with a narrower sharp core and a faint surrounding glow; avoid tinting the entire roof red. The contour must align after responsive crop (bake into each source crop or reproject from normalized image-space geometry). A pseudo-neon line misaligned by a resize is a defect, not “creative motion”.

## Source-specific sample colors (reference, NOT CPP defaults)

- Mossgrove: emerald #0F5C45 / white #FFFFFF / tangerine #F28C28.
- Tidewell: ink navy #141B2D / pearl white #F4F1EA / electric coral #FF5A4E.
- Blackridge: jet black #0B0B0C / smoke grey #8A8D93 / cherry red #C8102E.

These are text values displayed in the user's video and are sample-only. Do not copy brands, their wordmarks, original page graphics or protected imagery; derive any new project colors from its own identity.

## Selection and source authority

Use when: premium service/real estate/hospitality/landscape/architecture/product hero where visual emotion supports a genuine commercial or informational objective, and authorized scene assets and responsive composition are available.

**Cuando NO usar**:
- Dense operational dashboards, data-entry, checkout, authentication, trust-critical or accessibility-sensitive surfaces in which artwork impairs comprehension or speed.
- Backgrounds that compete with vital text, navigation or form controls, or whose worst-case contrast cannot be tested.
- Photos where accurate real-world color, product condition or medical/technical appearance is essential.
- When the design brief calls for calm, minimal energy, small bundle budgets or strict low-power/mobile constraints; a plain image or solid surface may be better.
- When the image/brand/trademark/license provenance is unverified.
- When matching the example demands copying another studio's art, brand name or composition 1:1.
- When a proposed animation is pure decoration and the declared CDIO-07 budget disallows it.
- When it would require an interactive WebGL scene merely to display a static photographic hero.

## Tokens / semantic design parameters

Reuse approved colors and typography in DESIGN.md. Proposed scene parameters only, **not** a second source of color truth: scene kind, focal subject and source, base asset/rights, accent role, light-zone geometry or masks, reflected light role, environment exposure and scrim strength, object/roof depth alignment, safe-crop regions, motion allowance, mobile fallback, render provenance and version.

No numeric default opacity, glow radius or render engine is prescribed universally; tune through side-by-side rendered evidence and specific context.

## Web implementation classes

- **Static, low cost (default):** responsive encoded image, dark/transparent gradient scrim for text, optional pre-rendered accent image; semantic DOM and CSS tokens.
- **Controlled compositing:** image layers, masked localized color gradients and blend modes, preserving object/foreground occlusion; test Safari/Firefox/Chrome and device GPUs. MDN documents multiple CSS backgrounds, blend modes and mask-image but these do not inherently generate physical reflections.
- **Offline production-grade:** original/licensed photography plus color grade/depth masks, or Blender lighting and render passes; export assets for browser rather than imposing a real-time renderer on a static landing.
- **Interactive/animated (opt-in):** video, Canvas, WebGL or animated scene layers only with demonstrated user need; functional reduced-motion/static alternative and bounded CPU/GPU/network usage.

## Quality gates

**VP19-Q01 — Source/rights:** source asset/texture/font/brand permission known and recorded; UNKNOWN blocks commercial publication.

**VP19-Q02 — Scene consistency:** accents connect to plausible light zones, do not indiscriminately change product reality, and do not contaminate text layers. Base and accent variants keep geometry/focal alignment when presented as recoloring one identity.

**VP19-Q03 — Text and controls:** real HTML text, keyboard-usable live CTAs, recognizable focus states; check actual minimum text contrast on the **worst relevant crop and bright region**, not overall image average.

**VP19-Q04 — Responsive crop:** realistic 360/390, 768 and 1440+ viewport tests; subject visible, headline not obscured, masks/roof contours aligned, no UI-over-image clipping.

**VP19-Q05 — Performance:** verify actual transferred bytes, LCP, layout shift, image decoding and GPU use in target devices. Avoid shipping video/3D when the visual is effectively static. Existing CPP performance floors still govern.

**VP19-Q06 — Motion budget:** no unrequested breathing/particles/hover/glow loops; respect CDIO-07 reduced-motion and still-frame equivalence.

**VP19-Q07 — Negative control:** a uniform tint over an unsegmented image and a misaligned glow edge must be distinguishable as inferior or blocked for fidelity; visually attractive screenshots with dead buttons cannot pass Production Reality.

**VP19-Q08 — Portability:** inspect real build, load, variants and asset references under the actual framework; do not claim Photoshop/Blender workflow from observing a video.

## Evidence and status

**Observed reference (one video), research-level pattern — not implemented or production-verified inside CPP.** Derived from original frame samples and qualitative comparison; no source design files. A new implementation and real browser evaluation are required before promotion to local/repeated/proven/baseline.

MDN source documentation:
- https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Backgrounds_and_borders/Using_multiple_backgrounds
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/background-blend-mode
- https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/mask-image
- https://docs.blender.org/manual/en/latest/render/layers/passes.html

## Creative combination bank and ledger (2026-11-17)

A subordinate **160-recipe ideation catalog** complements the three directly observed video examples. It is [stored as a dataset](datasets/VP019_BRAND_LIT_COMBINATIONS.md) grouped by 20 sectors and material/illumination scenarios. [Its aligned JSONL evidence ledger](ledgers/VP019_COMBINATION_LEDGER.jsonl) contains one `HYPOTHESIS_UNTESTED` record per candidate with explicit missing build/render/rights/QA/baseline receipts. Nothing in that catalog upgrades VP-019's evidence rank; none of its invented scenes can be attributed to the source video. The patterns' access remains through VP-019 and existing design-index workflows until a new, tested discovery adapter exists.
