# REF-BRAND-LIGHT-001 — Brand-colour propagation into cinematic hero environments

**Evidence class:** owner-supplied portrait social video; observed frames only.  
**Date inspected:** 2026-11-17.  
**Source filename:** mattxwebb_e4f36a50bf5e477286788284a34e7d1c.mp4.  
**Video SHA-256:** eed17326e7f43d5c6d3f21e4fadaf7233b6fd37cec19713c668c84d4a387594a.  
**Technical metadata:** H.264 1280x720 with rotation -90 degrees (portrait visual display 720x1280); 30 fps; 563 frames, approximately 18.90 seconds.  
**Rights:** user provided video as a reference for analysis. Do NOT check video frames/crops or copyrighted original art into public CPP repo, do not assume redistribution rights.  
**Derived pattern:** [[../../cinematic-brand-lit-hero]] (VP-019).  
**Evidence level:** one video, research only. No generated asset, component or pixel-perfect reconstruction validated.

## OBSERVED

- Around 1.50–4.50 seconds: a website mockup labeled **Mossgrove**, with garden architecture, dense landscaping and a horizon/terrace composition. Palette cards read Emerald #0F5C45 and White #FFFFFF, and then Tangerine #F28C28. When the orange card appears, both CTA and localized visible scene lighting become warmer: horizon, steps, foreground foliage and terrace.
- Around 5.25–11.25 seconds: a second mockup labeled **Tidewell**, dark navy background, left-aligned text, right-aligned glossy suspended water-like droplet and a bright floor reflection. Palette cards read Ink Navy #141B2D, Pearl White #F4F1EA, and Electric Coral #FF5A4E. The coral state changes CTA and the perceived rim/floor illumination, not the overall dark scene layout.
- Around 12.00–18.00 seconds: a third mockup labeled **Blackridge**, stormy/dark house photo with left-aligned headline and right-aligned architectural roof. Palette cards read Jet Black #0B0B0C, Smoke Grey #8A8D93, Cherry Red #C8102E. In the accent version the CTA and a thin aligned roof-gable edge appear red.
- All three show similar composition across neutral/accent variants, with restrained accent use, real-looking image depth, large light-weight sans typography, two CTA treatments, top navigation and subdued credibility metadata.
- The images are **overlaid within a social video**. The video does not show site behavior, navigation clicks, accessibility semantics, source layers, production source paths or browser interactions. Frame-level movement by the presenter and video compression cannot be attributed to the actual site.
- Visible color swatch values are displayed by the video; sampling screenshot pixels yields different values because of compression, display lighting and grading. Store hex strings only as **reference labels**, not measured environment RGB or brand defaults.

## MEASURED (reproducible from supplied video)

Comparison of fixed site-card region in portrait-decoded frames (coordinates x91..627, y730..1091; grayscale Pearson correlation; not registration-corrected):
- Mossgrove 3.00 vs 3.75 s: approximately **0.953**.
- Tidewell 7.50 vs 9.75 s: approximately **0.950**.
- Blackridge 12.75 vs 15.00 s: approximately **0.952**.

**Interpretation:** appearance/composition is highly similar with strong chromatic relighting; this is NOT evidence of exact same source image or particular CSS/Blender/AI implementation. Presenter movements and compression cause some mismatches.

## INFERRED (plausible, NOT observed implementation)

- Mossgrove is consistent with an authored photographic or generated scene plus localized warm sky and landscape-light relighting (or two carefully matched exported image variants).
- Tidewell is consistent with physically inspired 3D/refraction rendering or a high-quality precomposed droplet with accent-specific reflection passes.
- Blackridge is consistent with a masked or baked emissive line anchored to roof geometry, with faint glow around a sharp line.
- It is more robust to bake physically dependent reflections into image variants than to rely on one global CSS hue rotation.

## UNKNOWN

- Whether the three mockups are real deployed websites or conceptual artwork.
- Whether the same base plate was algorithmically recolored, regenerated or manually composited.
- Whether JavaScript or WebGL was used at all.
- Whether visible transition corresponds to a functioning theme toggle or social video editing.
- Licensing of the depicted original imagery and fonts.
- Responsive assets, performance, reduced-motion behavior, real CTA links, contrast verification, SEO and CMS.
- Exact camera, HDRI light settings, depth masks and image-generation prompts.

## HYPOTHESES TO FALSIFY IN CPP

H1: A scene-specific layered lighting process outperforms a flat duotone tint in perceived material cohesion, at equal brief/asset quality.

H2: A static optimized image with pre-rendered light is sufficient for most of these hero designs, avoiding unnecessary WebGL.

H3: Recolored variants derived from the same geometry maintain semantic/visual consistency better than independent image regeneration; verify especially roofs/architecture.

H4: The quality of the effect depends on *where* brand color appears in environment lighting and material, not simply on how much accent color fills the screenshot.

## Experiments required

Freeze a licensed or original scene for each of three variants, apply two recipes (flat tinted overlay vs scene-directed lighting), preserve text, crop and brand tokens, and compare blind human design preference plus measurable geometry/cropping/contrast/mobile/size performance. Run with real web rendering; differentiate the expected quality delta from panel dimensions, hero composition, typography and source image quality.

Do not promote VP-019 to a generic production baseline without independent examples and failures.

## Technical sources for candidate mechanisms (not provenance of original implementation)

- MDN multiple backgrounds: https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Backgrounds_and_borders/Using_multiple_backgrounds
- MDN background blend: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/background-blend-mode
- MDN mask image: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/mask-image
- Blender Render Passes: https://docs.blender.org/manual/en/latest/render/layers/passes.html
