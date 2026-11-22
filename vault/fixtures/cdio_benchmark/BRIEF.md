# CDIO cross-sector benchmark — brief (tranche 2 item 3, Owner "sí" + "rec", 2026-11-22)

Worktree: `C:\Users\User\Apps\pp-cdio-bench` (branch `cdio/cross-sector-bench`). Everything below runs from there.
Python: `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe` (call it `$py`). Shell: PowerShell.

## Owner requirement: "que se vean muy clean siempre"
Clean is the done bar, stricter than the normal gate:
- cdio-reviewer verdict APPROVE (score >= 80) with **zero critical AND zero major** issues;
- **zero failing RENDER-\*** facts on desktop, tablet and phone;
- Taste lint (`$py -m modules.cdio.taste <page>`): zero critical findings.
Clean means: one clear focal point per screen, generous whitespace on a spacing scale, at most 2 typefaces,
a restrained palette (one accent), aligned grid, no decorative clutter, no template look.

## Surfaces (one folder each under vault/fixtures/cdio_benchmark/)
1. `b2b_dashboard/` — an operations dashboard for a B2B logistics SaaS (KPI row, one main chart, one table).
2. `pro_service/` — a high-trust professional service site (an independent tax-advisory practice): landing page.
3. `mobile_app/` — mobile app screens judged under CDIO-08 (onboarding, home, detail), phone-first HTML.
4. `brand_kit/` — a brand kit: wordmark + symbol SVG, palette and type page. Try CCF first
   (`$py -m modules.ccf.cli init/generate`); if no image provider is configured, author the SVGs by hand and say so.

## Honesty rules (non-negotiable)
- Each business is invented and named as a fixture in its folder's README.md. Never imitate a real company.
- No fabricated testimonials, reviews, client logos, awards or "trusted by" claims. Dashboard numbers carry a
  visible "Datos de ejemplo" label. No forms that collect real data.
- Static HTML/CSS (+ minimal JS), no external CDNs except Google Fonts. Respect prefers-reduced-motion.

## Protocol per surface
1. Build (builder agent). Self-check with Taste lint and `$py tools/design_review_record.py render <files>`
   (brand SVGs: `render <asset>` gives the framed light/dark 32/96/320 render). Fix every RENDER-* fail.
2. Independent review (cdio-reviewer, never the builder): read the render PNGs + facts, write verdicts JSON,
   `$py tools/design_review_record.py record --verdicts <v.json> --files <files>`. Report score, verdict, issues.
3. Not clean -> one repair by a builder, then a fresh independent review. At most 2 repairs.
4. Results row appended to `RESULTS.md`: surface | score | verdict | critical/major/minor | RENDER fails | repairs.
