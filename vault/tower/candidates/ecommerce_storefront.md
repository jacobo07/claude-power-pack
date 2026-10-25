# Candidates — ecommerce storefront (NOT promoted)

Recorded 2026-10-25 by TUA-X sge-10 P8 (plan `dreamy-mixing-wirth` §6). These are rules a storefront
generator met once. They stay candidates: there is no `ecommerce_storefront` family yet, and each has
evidence from ONE domain (SGE / CW Shrine on Shopify). Promotion needs the same rule observed in a
second, independent storefront (another repo or platform), then a family with B0 written through
`modules/tower` (`ratchet.promote`) with a verified `origin.quote`.

| id | candidate rule | evidence (single domain) |
|---|---|---|
| ecom-single-sku-no-categories | A store selling one SKU emits no collection template and no category navigation. | TUA-X sge-10 P4 `engines/sge/sections.py` (PLP only for multi_collection); Dawn still ships its own `templates/collection.json` — open question whether to overwrite it. |
| ecom-filters-on-real-attributes | Filters, swatches and option controls render only from attributes the products actually have; a colour without a platform swatch colour is a labelled chip, never a guessed paint. | sge-10 P4 PLP (`collection.filters`), P5 swatch defect: option names ("Rojo") are not CSS colours, 8/8 swatches painted the same grey. |
| ecom-essential-media-blocks-completeness | A product whose primary image is missing cannot be called visually complete; a missing gallery or variant image degrades and is listed. | sge-10 P3 `engines/sge/media_manifest.py` + P5 ladder check `media_manifest` (manifest must describe the RENDERED product). |
| ecom-price-format-is-the-shops | A price rewritten client-side uses the shop's money format for the shop currency, never the browser locale. | sge-10 P5: "€44,95" became "69,95 €" on a size change. |

Related B4 entries (promoted, universal): `web_surface-controls-proven-by-driving-them`,
`web_surface-render-check-seen-failing`, `web_surface-generated-claim-needs-a-fact`.
