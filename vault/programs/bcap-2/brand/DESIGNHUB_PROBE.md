# BI-27 DesignHub probe (inventory + READ of registries, epoch 4)

Source: github.com/yakew7/DesignHub @ 148e8c3ffa8ea82801b3cfb16ef91b4ca515d285 (the pin in the backlog). GitHub SPDX MIT, not archived. Git tree read 2026-11-20: 907 paths, not truncated.

## Inventory (paths only; no source file was read)
Next.js local-first studio. Relevant modules by blob count: lib/social 58, lib/svg 36, lib/mockups 24, lib/guidelines 24, lib/color 24, lib/brand 17, lib/brand-dna 12, lib/logo 9, packages/cli 12. Pages cover brand, brand-dna, logo, mockups, guidelines, export, accessibility.

## Decision (reasoned, not measured)
- Overlap with CCF: brand-dna, logo, mockups, guidelines and export map onto CCF Visual DNA, concept generation, BI-23 preview contexts and BI-26 release manifest. DesignHub is an application, so forking it would create the competing logo studio the backlog forbids.
- Candidates for technique comparison only: lib/mockups (context catalogue for BI-23) and lib/guidelines (brand-book structure for BI-24). Nothing was read, so no technique is claimed or ported.
- Licence is repo-level MIT; per-file headers, vendored assets and font/image licences in mockups were not checked, so code admission stays refused until that scan.

## Not done (BI-27 stays open)
No source read, no technique comparison, no measured benefit. Next unit: read lib/mockups and lib/guidelines index files, scan headers, compare against modules/ccf/brand_release.py context list.

## READ (epoch 4, 2026-11-21, raw files at pin 148e8c3f)
Read in full: `lib/mockups/registry.ts`, `lib/guidelines/registry.ts`, `lib/guidelines/outline.ts`. Header scan: these three carry no per-file licence header (imports and code only); the repo LICENSE is MIT, "Copyright (c) 2026 DesignHub contributors". Template and page bodies (`lib/mockups/templates/*`, `lib/guidelines/pages/*`) and any vendored font/image were NOT read, so no code is admitted: principles only.

### Catalogue vs CCF (`modules/ccf/brand_release.py` CONTEXTS, 9)
DesignHub registers 19 mockup templates. Mapping to our 9 contexts (judgement from template names, not from template bodies):
- masthead: browser-tab, laptop-landing, desktop-dashboard
- favicon: browser-tab
- avatar: id-badge (weak), email-signature (weak)
- packaging: shopping-bag, coffee-cup, sticker, merch
- print: business-card, letterhead, envelope, poster
- ad_overlay: billboard, poster
- mobile_screen: mobile-app, app-store, lock-screen, smartwatch, tablet
- photography, social_canvas: no template (social lives in `lib/social`, 58 blobs, not read)
Not covered by any of our 9: email-signature, id-badge, smartwatch, lock-screen as surfaces of their own. They are CANDIDATE contexts only; adding one needs a real render and the BR-07 SVG rules, so none is added.

### Brand book (BI-24)
22 pages in order: cover, introduction, mission, logo-usage, clear-space, minimum-size, incorrect-usage, co-branding, color-palette, color-usage, data-visualization, typography, typography-usage, iconography, imagery, spacing-layout, components, accessibility, voice, social-media, color-tokens, scale-tokens. Principles taken for Phase 4: (1) a fixed page order with logo rules (clear-space, minimum-size, incorrect-usage) before colour and type; (2) PDF bookmarks plus contents rows that link to pages, built with low-level PDF objects because the PDF library has no outline API (outline.ts says so itself); (3) switched-off pages are left out of the contents, not blanked.

## Verdict
READ, principles only, no code ported, no measured benefit claimed. BI-27 closes as COMPARE (catalogue and book order compared), not BENCHMARK: no metric was run against DesignHub output, and that is stated, not hidden.
