# CostaLuz — Ronda 139 (Pane 4): CLS + Image Dimensions + WebP — Research Report

## Executive Summary

This report consolidates the research underpinning R139's Pane-4 workstream: eliminating **Cumulative Layout Shift (CLS)** through explicit image dimensioning, and reducing image payload via **WebP/AVIF** delivery — both in service of the site-wide mobile-LCP crisis flagged in R116. The single most important structural finding for this round is that **CLS and image-format optimization are orthogonal problems solved by different mechanisms**: CLS is fixed by reserving layout space (width/height attributes or CSS `aspect-ratio`), while WebP/AVIF only shrink bytes and improve LCP. Conflating them is the most common implementation error and would waste the round.

A second decisive finding: the classic "fix" of adding `width`/`height` attributes is silently defeated by a single CSS line — `width: auto` — and this failure is **invisible on a developer's cached machine**, which is exactly the conditions under which prior rounds verified work. R139 must reproduce on cold cache.

Third: on a WordPress install with REST-only content access (the CostaLuz access boundary sealed in R142), `<picture>`/`<source>`/`srcset` will be **stripped by `wp_kses_post`** unless the allowlist is extended — meaning the cache-safe, zero-JS format-selection path is not freely available through the content API and the realistic plugin-free path is server-side negotiation (`.htaccess`/Nginx), which is operator-gated.

---

## Part I — Core Web Vitals Context (2026 Baseline)

### Thresholds and Measurement Model

| Metric | Good | Needs Improvement | Poor | Notes |
|---|---|---|---|---|
| **CLS** | ≤ 0.10 | 0.10–0.25 | > 0.25 | Unitless; built from impact fraction × distance fraction |
| **LCP** | ≤ 2.5 s | 2.5–4.0 s | > 4.0 s | ~77% of LCP elements are images |
| **INP** | ≤ 200 ms | 200–500 ms | > 500 ms | Replaced FID on 2024-03-12 |

Key measurement facts that constrain how R139 success can be claimed:

- **All three are assessed at the 75th percentile (p75)** of real-user **CrUX** sessions over a **rolling 28-day window**. A page must pass **all three** to earn "Good" in Search Console.
- **CWV are measured EXCLUSIVELY by field data (CrUX/RUM).** Lab tools — Lighthouse, WebPageTest, Chrome DevTools — do **not** measure CWV. A perfect Lighthouse 100 does **not** guarantee passing. **PageSpeed Insights uniquely combines both**: CrUX field data (the ranking signal) plus Lighthouse lab diagnostics.
- **CrUX lags 1–2 days** and uses the 28-day window, so any R139 fix takes **~4–6 weeks** to fully reflect in GSC. Verdict claims this round must be lab-evidence-qualified ("PSI Lighthouse diagnostic improved; field confirmation pending ~4–6 wks").
- **CrUX falls back URL → URL-group → origin** when URL-level data is insufficient.
- **CLS analytics must sum `metric.delta`, not `metric.value`** — CLS accumulates across the session.

### The CLS Scoring Mechanism (Precise)

CLS is **not** a simple sum of shifts. It uses **session windows** with a **1 s gap** and a **5 s cap**, and the reported score is the **MAXIMUM window score**, not the total. Shifts within **500 ms of discrete user input** are excluded via `hadRecentInput`. This matters for R139: the facade/lazy-iframe swap pattern is CLS-exempt precisely because the swap occurs within the 500 ms input window.

### Where CLS Sits in the 2026 Landscape (Web Almanac 2025)

| Metric (mobile) | % "Good" | YoY |
|---|---|---|
| **CLS** | **81%** | +9pp (largest improvement of any metric) |
| INP | 77% | — |
| LCP | 62% | hardest to pass |
| **All three** | **48% mobile / 56% desktop** | — |

- CLS desktop "good" origins: 72% (up from 62% in 2021). CLS is now the **best-performing CWV on mobile**.
- Despite this, **unsized media remains the #1 cause of CLS.**

---

## Part II — CLS Root Cause #1: Unsized Images

### The Scale of the Problem (Web Almanac 2025)

| Metric | Mobile | Desktop |
|---|---|---|
| Pages shipping ≥1 image with no width/height | **62%** (was 66% in 2024) | **65%** (was 69%) |
| Unsized images at p75 | 8 | 9 |
| Median unsized-image height | 98 px | 111 px |

Only **11% of pages preload web fonts** — relevant to the secondary CLS cause (font swap).

### Why Unsized Images Shift Layout

When an `<img>` (especially lazy-loaded) carries no `width`/`height` and no CSS `aspect-ratio`, the browser **reserves zero space** until the image downloads, then **shifts all following content down** when it arrives. Lazy loading amplifies this because the reservation is deferred even further.

### The Correct Fix — and Its Hidden Killer

Browsers since **2019–2020** compute an intrinsic **aspect-ratio from the `width`/`height` attributes BEFORE the image downloads**, internally generating `aspect-ratio: auto W / H` at the lowest CSS priority. This is what reserves the box.

**The fix-killer is `width: auto` in CSS.** It overrides the browser's internal width, leaving both dimensions unknown, so the image renders **0×0 until download** — re-introducing the shift the attributes were meant to prevent.

| Approach | Result |
|---|---|
| HTML `width`/`height` attributes (px) + CSS `img { width: 100%; height: auto; max-width: 100% }` | ✅ Correct — box reserved |
| HTML attributes + CSS `width: auto` | ❌ Defeated — 0×0 until load |
| CSS `aspect-ratio: 16/9` (or `1/1`) directly | ✅ Correct alternative |

**Two reproduction traps R139 must defend against:**

1. **The bug hides on dev/cached machines** because browser cache supplies dimensions instantly. Reproduce via DevTools **"Disable cache"** or **incognito** / cold load. (Aligns with the project's pixel-validation-on-primary-source doctrine — a declared value is a hypothesis until validated under real conditions.)
2. **Lighthouse misses it** because it checks **HTML attributes, not computed CSS.** A green Lighthouse audit can coexist with live CLS. Field/cold-cache verification is mandatory.

Additional correctness note: setting **wrong attribute values** (e.g., 4:3 on a 16:9 image) causes a **correction shift** when the real image loads — wrong dimensions are not "better than none."

### WordPress-Specific Behavior

- WordPress **5.5+** auto-adds `loading="lazy"`; **6.3+** adds `fetchpriority="high"` to the first content image.
- Shopify's Liquid `image_tag` auto-sets the height attribute (cross-reference, not applicable to CostaLuz's WP stack).
- **CLS is fixed by width/height attributes, NOT by WebP conversion.** This must be stated explicitly in the R139 verdict to prevent scope-confusion.

---

## Part III — CLS Root Causes #2–4 and Their Fixes

| Cause | Fix |
|---|---|
| **Iframes** (do NOT derive aspect-ratio from attributes; default to **300×150**) | Wrapper with `aspect-ratio: 16/9; width: 100%`, OR the **facade pattern** (static placeholder swapped to real iframe on visibility — swap shift excluded from CLS as it's within 500 ms of user input) |
| **Web-font swap** | Prefer `font-display: optional` (waits ~100 ms, commits once, no mid-session swap) over `swap`; pair with metric overrides `size-adjust`/`ascent-override`/`descent-override`/`line-gap-override` (auto-generated by **Fontaine** or **Next.js @next/font**) + `<link rel=preload as=font crossorigin>` |
| **Dynamically injected ads/cookie banners** | Reserve `min-height` (smallest likely size) + `contain: layout style` to isolate internal reflows |
| **Non-compositor animations** | Animate **only** `transform` and `opacity`; never `top/left/width/height/margin/padding` |
| **Repeat shifts on back/forward nav** | Ensure **bfcache eligibility** — no `unload` listeners, no `Cache-Control: no-store` |

---

## Part IV — WebP / AVIF (Payload & LCP, NOT CLS)

### Compression and Support

| Format | vs JPEG | vs PNG | Browser support | Encode cost |
|---|---|---|---|---|
| **WebP** | 25–35% smaller | up to 26% smaller | **97%+ global** | baseline |
| **AVIF** | 30–50% smaller | — | **92%+** (Safari 16.4+) | **5–10× slower** than WebP |

Real-world (tweakswp.com):

| Source | WebP | AVIF |
|---|---|---|
| 2560×1440 hero JPEG, 1,842 KB | 896 KB (−26%) | 612 KB (−50%) |
| 1200×800 PNG screenshot, 487 KB | 178 KB (−57%) | 142 KB (−66%) |

A full **WebP+AVIF+lazy-load** pipeline cut total image page weight **4.2 MB → 1.8 MB (−57%)** and **LCP 50%** (desktop 2.8 s → 1.4 s; mobile 4G 5.2 s → 2.6 s) — at the cost of **+133% disk** (originals + variants).

> **Direct relevance to R116:** site-wide mobile LCP ~5.7 s with 10/10 pages CRITICAL, attributed to theme/plugin CSS-JS bloat. WebP addresses the **image-byte** fraction of LCP, not the CSS/JS render-blocking fraction — so WebP alone will not clear R116. It is necessary, not sufficient.

### Two Delivery Paths and Their Constraints

**Path A — `<picture>` + `<source>` (zero JS, cache-safe).** The browser picks the source; no per-Accept-header CDN caching needed. **Blocked on CostaLuz content path:** `wp_kses_post()` strips `<picture>`, `<source>`, and `srcset` unless explicitly added to the allowed-HTML array (see Part V). Injecting these via REST content is therefore not freely available.

**Path B — Server-side content negotiation (plugin-free, no HTML rewrite).**
- **Apache `.htaccess`:** `RewriteCond %{HTTP_ACCEPT} image/webp` + `RewriteCond %{REQUEST_FILENAME}.webp -f`, internally rewriting `image.jpg → image.jpg.webp` with `[T=image/webp,L]`. **Internal rewrite, no 301 — original URLs stay valid.**
- **The `Vary: Accept` header is CRITICAL** — without it a CDN/browser cache may serve a WebP body to a JPEG-only client.
- **Nginx equivalent:** `map $http_accept → $webp_suffix` + `try_files` (more efficient than `if` blocks).
- WordPress conversion hook: `wp_handle_upload` filter (PHP **GD `imagewebp()` @ quality 82**, or **Imagick @ quality 75**). WP **5.8** added native `.webp` upload; **6.1+** can output WebP for intermediate sizes via GD/Imagick.

> **R142 boundary collision:** Path B edits server config (`.htaccess`/Nginx) — that is a SiteGround/WP-Admin operator-gated action, NOT reachable via REST content access (App Password ≠ wp-login GUI). Per the R142 perf-deploy boundary, R139 can **audit + prepare + runbook** the WebP negotiation but **cannot deploy it**; it hands off to the operator. Hard-rule triggers (writes to load-bearing config) apply — read UKDL §HARD-RULES before any such write.

---

## Part V — WordPress kses Filtering (Why `<picture>` Doesn't Survive REST)

- WordPress uses the **kses** family (`wp_kses`, `wp_kses_post`, `wp_kses_data`, `wp_filter_post_kses` in `wp-includes/kses.php`) — strips any tag/attribute **not in an explicit allowlist**. `wp_kses_post()` allows post-content tags (headings, lists, links, images, blockquotes) and strips scripts. **`<picture>`, `<source>`, and `srcset` are stripped** unless added to the allowed-HTML array.
- Doctrine: **"sanitize on input, escape on output."** `content_save_pre` auto-applies `wp_kses_post` on save for users **lacking `unfiltered_html`** capability.
- `wp_kses()` checks `style` properties against an allowed-properties list and **strips the entire `style` attribute** if no contained property is safe; it **strips camelCase/uppercase attributes** (args must be lowercase — e.g., `viewBox` must be declared lowercase). An **empty array OR boolean `true`** as an attribute value means the attribute is allowed. ("kses" = recursive acronym from XSS + access, "kses strips evil scripts.")
- On large content blocks, `wp_kses` runs a **recursive HTML parser** with measurable processing cost — profile with **Query Monitor** before high-frequency paths.

**REST API specifics:**
- Sanitization belongs in the schema's **`sanitize_callback`** (runs before the endpoint callback), **NOT** inside the callback. Output goes through `rest_ensure_response()`; manually-built HTML still needs escaping.
- **Capability checks** (`current_user_can`, e.g. `unfiltered_html`), **nonces** (`wp_verify_nonce`/`check_admin_referer`), and **escaping** are **three independent layers**. A user without `unfiltered_html` has post content auto-filtered through `wp_kses_post` on save.

> **Implication for R139:** if any picture-element approach is desired through content, it requires either (a) extending the kses allowlist (a code/plugin change, operator-gated) or (b) a user with `unfiltered_html`. Neither is the default REST content path. The realistic R139 levers are: **width/height attributes** (these survive kses — `<img>` and its dimension attributes are allowlisted) for **CLS**, and a **prepared-but-handoff** server-negotiation runbook for **WebP**.

---

## Part VI — Lazy-Loading & LCP Interactions (Adjacent, Must Not Regress)

- **Never lazy-load the LCP/hero/featured image.** Shopify's perf team: stores lazy-loading their LCP image have **median LCP 1.0 s slower**. HTTP Archive (~8M pages): ~17% of LCP images are lazy-loaded overall but **59% on Shopify**, where LCP runs ~3 s slower. **~77% of LCP elements are images.** Fix: eager-load with `loading="eager"` + `fetchpriority="high"`. **A `loading="lazy"` blanket pass on CostaLuz must exclude the hero/featured image.**
- **Native `loading="lazy"`** (spec 2019, **92–96%+** support, Safari 15.4+) is preferred over JS libraries like **lazysizes** (5–10 KB overhead, now legacy). Native limits: no threshold control, no placeholder, **cannot lazy-load CSS background images** (only `<img>`/`<iframe>`). Proper lazy-loading cuts initial page weight **40–80%** on image-heavy pages.
- Manual `<link rel="preload">` for the LCP/featured image can shave **100–300 ms** off LCP.

### LCP Subpart Model (for diagnosing where mobile 5.7 s goes)

LCP decomposes into **exactly four additive, non-overlapping subparts**:

1. **TTFB**
2. **Resource Load Delay** (TTFB → LCP resource starts loading)
3. **Resource Load Duration** (downloading the LCP resource)
4. **Element Render Delay** (resource finishes → element renders)

- For **text/system-font** LCP elements, Load Delay and Load Duration are **always 0 ms** — everything not in TTFB is render delay.
- Target: keep the **two delay subparts ≤ 20% of total LCP**, leaving ~40% each for TTFB and Load Duration (the two near-unavoidable network components for image LCP). Optimization order by impact: **(1) eliminate resource load delay → (2) eliminate render delay → (3) reduce load duration → (4) reduce TTFB.** WebP attacks **(3)**; preload + not-lazy-loading attack **(1)**.
- Google added **LCP subpart data + LCP resource type (image vs text)** to **CrUX in Feb 2025**. CrUX reports subparts **only for image LCP elements**, **only for high-traffic pages**, and takes **≥4 weeks** to update. **Not yet in PageSpeed Insights** — viewable in **Chrome DevTools "LCP by phase"** panel and tools like **DebugBear**.

---

## Part VII — R139 Pane-4 Recommendations (Synthesis)

### Do This Round (within REST content access)

1. **CLS fix via width/height attributes** on `<img>` tags (survives `wp_kses_post`), paired with verifying CSS does **not** carry `width: auto` (the fix-killer). Use `height: auto; max-width: 100%` only.
2. **Verify on COLD CACHE** (incognito / DevTools Disable cache) — not a dev-cached machine, and **not Lighthouse-only** (it checks attributes, not computed CSS). This is the done-gate.
3. **Audit lazy-load coverage** to confirm the hero/featured image is **eager** + `fetchpriority="high"`, never lazy.
4. **Validate attribute values** match true intrinsic aspect ratios (wrong ratio = correction shift, not a fix).

### Prepare-and-Handoff (operator-gated, per R142)

5. **WebP server negotiation runbook**: `.htaccess` (Apache) or `map`+`try_files` (Nginx) with the **mandatory `Vary: Accept`** header, GD `imagewebp()` @82 / Imagick @75 conversion via `wp_handle_upload`. Audit + backup + runbook + fresh PSI baseline, then hand to the operator. **Read UKDL §HARD-RULES before any config write.**
6. Flag that `<picture>`/`srcset` is **not** a content-path option without a kses-allowlist code change.

### Verdict-Language Discipline

7. Any "done/improved" claim this round is **lab-qualified** (PSI Lighthouse diagnostic), with **field confirmation pending ~4–6 weeks** (CrUX 28-day window). Do **not** assert a CWV pass from Lighthouse.
8. State explicitly in the verdict: **CLS fixed by dimensions; WebP only reduces bytes/LCP — they are separate workstreams.**

### What Would Be Out of Scope / Wrong

- Treating WebP conversion as a CLS fix (it isn't).
- Claiming a CWV "pass" from a green Lighthouse run.
- Verifying the dimension fix on a cached dev machine.
- Attempting `<picture>`/`<source>` injection through REST content (kses strips it).
- Deploying `.htaccess`/Nginx WebP negotiation directly (operator-gated, R142 boundary; hard-rule trigger).

---

## Appendix — Quick-Reference Fact Table

| Fact | Value / Rule |
|---|---|
| CLS good / NI / poor | ≤0.10 / 0.10–0.25 / >0.25 (p75, 28-day CrUX) |
| CLS scoring | max session window (1s gap, 5s cap); not a sum; >500ms-post-input shifts excluded |
| Pages with ≥1 unsized image | 62% mobile / 65% desktop (2025) |
| CLS "good" mobile | 81% (+9pp YoY, best CVW improvement) |
| Pass all three CWV | 48% mobile / 56% desktop |
| Fix-killer CSS | `width: auto` → renders 0×0 until load |
| Correct CSS | `height: auto; max-width: 100%` only |
| Lighthouse blind spot | checks HTML attrs, not computed CSS |
| Iframe default size | 300×150 (no aspect from attributes) |
| Font fix | `font-display: optional` + metric overrides + preload |
| WebP vs JPEG | 25–35% smaller; 97%+ support |
| AVIF vs JPEG | 30–50% smaller; 92%+ support; 5–10× slower encode |
| WebP nego header | `Vary: Accept` mandatory |
| GD / Imagick WebP quality | 82 / 75 |
| kses strips | `<picture>`, `<source>`, `srcset` unless allowlisted |
| LCP good | ≤2.5s; ~77% LCP elements are images |
| Never lazy-load | the LCP/hero image (Shopify: +1.0s median LCP) |
| Native lazy support | 92–96%+; Safari 15.4+; can't lazy CSS backgrounds |
| CrUX field lag | 1–2 days; 28-day window; ~4–6 wks to reflect fixes |
| LCP subparts in CrUX | since Feb 2025; image-LCP + high-traffic only; not in PSI |

---

**Bottom line for R139 Pane 4:** ship the **image-dimension CLS fix through REST** (the one lever fully inside content access), gate it on **cold-cache + non-Lighthouse** verification, keep the **hero image eager**, and **prepare-but-hand-off** the WebP server-negotiation as an operator-gated perf change per the R142 boundary — with all completion claims lab-qualified and field-confirmation flagged as pending.

## Sources

- <https://web.dev/articles/optimize-cls>
- <https://logoswebdesigns.com/blog/how-to-fix-cumulative-layout-shift-2026/>
- <https://www.wicked-seo.com/2026/04/07/how-to-fix-cumulative-layout-shift-cls-issues-on-your-website/>
- <https://testdom.io/webvitals/performance/unsized-images>
- <https://www.corewebvitals.io/core-web-vitals/cumulative-layout-shift/images-and-media>
- <https://elementor.com/help/lazy-loading/>
- <https://easyappsecom.com/guides/shopify-lazy-loading-guide>
- <https://www.thunderpagespeed.com/blog/shopify-lazy-loading/>
- <https://performance.shopify.com/blogs/blog/optimizing-images-for-performance-on-shopify>
- <https://baltic-lab.com/2025/01/webp-images-without-plugin/>
- <https://tweakswp.com/optimize-wordpress-images-cli-server-methods-2/>
- <https://www.wavewrite.com/convert-images-to-webp-in-wordpress-without-a-single-plugin/>
- <https://helloadmin.com/serve-images-in-webp-format-in-wordpress-without-a-plugin/>
- <https://blog.sailed.io/imgproxy-wordpress-optimize-images-webp/>
- <https://developer.wordpress.org/apis/security/escaping/>
- <https://developer.wordpress.org/reference/functions/wp_kses/>
- <https://codeboxr.com/sanitize-wordpress-xss-prevention/>
- <https://tweakswp.com/how-to-prevent-xss-in-wordpress-sanitization-and-escaping-functions-guide/>
- <https://www.corewebvitals.io/core-web-vitals>
- <https://accs-net.com/glossary/core-web-vitals/>
- <https://support.google.com/webmasters/answer/9205520?hl=en>
- <https://sujeet.pro/articles/core-web-vitals-measurement>
- <https://www.w3era.com/blog/seo/core-web-vitals-guide/>
- <https://web.dev/articles/optimize-lcp>
- <https://developer.chrome.com/docs/performance/insights/lcp-breakdown>
- <https://developer.chrome.com/docs/lighthouse/performance/lighthouse-largest-contentful-paint>
- <https://www.smashingmagazine.com/2025/03/how-to-fix-largest-contentful-issues-with-subpart-analysis/>
- <https://www.debugbear.com/blog/lcp-subparts>

## Run metadata

- **Prompt:** SESIÓN: CostaLuz — Ronda 139 (PANE 4): CLS + IMG DIMS + WEBP
- **Depth / breadth:** 2 / 3
- **Queries used:** 6 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 467.6 s
- **Errors during run:** 2
- **Started at:** 2026-06-21T11:09:35Z
- **Module version:** deep_research 0.1.0

<details>
<summary>Error log</summary>

- `fetch_page 'https://copyelement.com/blog/lazy-loading-images-in-elemento...': page-fetch: https://copyelement.com/blog/lazy-loading-images-in-elementor-a-step-by-step-guide-no-plugins: HTTP Error 429: Too Many Requests`
- `fetch_page 'https://medium.com/@python-javascript-php-html-css/solving-w...': page-fetch: https://medium.com/@python-javascript-php-html-css/solving-wordpress-rest-api-content-stripping-issues-44c72abd01b4: HTTP Error 403: Forbidden`

</details>
