# CostaLuz — Ronda 132 (PANE 3): CTR Per-Page Diagnosis + LCP Authorization

**Research synthesis report — 2026-06-30**
**Client:** CostaLuz Lawyers (conveyancing / property litigation, Spain — YMYL legal vertical)
**Scope:** Two parallel levers for Round 132 — (1) per-page Click-Through-Rate diagnosis in Google Search Console, and (2) the Largest Contentful Paint (LCP) fix and its authorization/deploy boundary.

---

## Executive Summary

| Lever | Core finding | Lever ceiling | Constraint |
|---|---|---|---|
| **CTR per-page** | AI Overviews (AIO) have collapsed classic CTR curves; for a YMYL legal site, ~78% of legal queries trigger an AIO, so most of the impression base is now AIO-mediated. The dominant lever is no longer keyword density — it is **being cited inside the AIO** (entity E-E-A-T + schema), which *inverts* the penalty into a gain. | Title/meta/schema rewrites lift CTR ~15–35% with **no rank change**, but the AIO citation lever is the larger structural play. | Effects need 14–21 days to re-crawl; measure with matched pre/post windows. |
| **LCP auth** | Mobile LCP ~5.7s site-wide (R116) is the #1 conversion lever. The bottleneck is almost certainly **render-blocking JS/CSS + main-thread blocking**, NOT the hero image — diagnose the waterfall first. | A documented WP audit cut 5.3s→1.8s mostly via JS deferral + caching, no image format change. | Site-wide `<head>`/theme changes are **WP-Admin/SiteGround operator-gated** (R142); the autonomous REST lever is the **Code Snippets v1 plugin** (R144), which can mutate theme-injected output via `functions.php`-style hooks. |

**Net recommendation:** Run the CTR per-page diagnosis as a *read-only* audit this turn (no thrash — pre-diff any meta proposals per the meta-script guard), and treat the LCP fix as the higher-impact lever but route it through the Code Snippets REST path with the operator-gate explicitly acknowledged. Do not optimize the hero image until the waterfall confirms it is the bottleneck.

---

## Part 1 — The AI Overview Regime (Why CTR Math Changed)

### 1.1 Rollout and prevalence

AI Overviews rolled out broadly in 2024 and have grown explosively:

- **Keyword footprint:** 10,000 keywords (Aug 2024) → **172,855 by May 2025** (GrowthSRC).
- **SERP coverage:** AIOs now appear on **~31% of SERPs** generally; by **February 2026, ~6 of 10 Google searches** surface an AIO.
- **Europe (Sistrix, March 2026):** 47% of **informational** queries trigger an AIO vs 23% transactional and 8% navigational — growing **+5 points/quarter**. Spanish is among the 7 covered European languages, which is directly material to CostaLuz's ES-mirror corpus.

### 1.2 The legal/YMYL multiplier

CostaLuz sits in the **single highest-triggering vertical**:

- **77.67% of YMYL legal queries** trigger an AIO (SE Ranking, 2024); legal ~**78%**, ahead of healthcare/finance/retail.
- **Question-format queries** trigger AIOs **57.9%** of the time; **long-tail 7+ word queries** account for **46%** of AIO appearances (Ahrefs, Nov 2025) — i.e. exactly the conveyancing how/what/can-I queries that drive CostaLuz's informational traffic.

**Implication:** For CostaLuz, the majority of the impression base is AIO-mediated. A per-page CTR audit that treats AIO presence as noise will misread the data.

### 1.3 The CTR collapse — and the inversion

Classic position-based CTR curves have buckled:

| Position | Pre-AIO CTR | Post-AIO CTR | Change |
|---|---|---|---|
| 1 | 28% | 19% | **−32% YoY** |
| 2 | 20.83% | 12.60% | **−39% YoY** |
| 6–10 | (low) | rose ~30% | **+30%** (users scroll past AIO to verify) |

- **MailOnline:** CTR drops of **56.1% desktop / 48.2% mobile** when an AIO appears.
- **Seer Interactive (Sept 2025, 25.1M impressions):** organic CTR falls **61%** when an AIO is present (1.76% → 0.61%).
- **Pew (2025, 68,879 queries):** **8% click-through with an AIO vs 15% without** (47% relative decline); **~25% of AIO sessions end zero-click**.

**The critical inversion — citation flips penalty into gain:**

| Source | Non-cited | Cited |
|---|---|---|
| Seer (Sept 2025) | (baseline drop) | **+35% organic clicks, +91% paid clicks** |
| Sistrix (Europe, Mar 2026) | positions 1–3 lose **−18% CTR** | **+22% CTR, +340% impressions** |

- **Featured snippets** achieve **42.9% CTR** (First Page Sage) — higher than a clean position 1.
- **AI-referred traffic converts at ~2–3× organic** (professional services **+100%** lift) — high relevance for a legal lead-gen site.

**Strategic conclusion:** The CTR lever for CostaLuz is not "rewrite titles to claw back position-1 clicks." It is **earn AIO citation**, because cited > non-cited by a wide margin and the cited cohort *grows* impressions and converts at 2–3×.

---

## Part 2 — CTR Per-Page Diagnosis Workflow (Pane 3 / Lever 1)

### 2.1 The GSC audit recipe

1. **Performance → Search results**, set **90-day range**.
2. Toggle on all four metrics: **Clicks / Impressions / CTR / Average Position**.
3. Filter **Impressions > 1,000** (kills noise).
4. Find **page-1 pages (position 1–10)** whose CTR is **below the position benchmark** — flag if **below ~3% on page 1**.

### 2.2 GSC data-integrity caveats (avoid mis-reads)

- **Aggregation asymmetry:** GSC aggregates **Queries / Countries / Devices / Dates by property**, but **Pages / Search-appearance by page** → chart-vs-table discrepancies are *expected*, not a bug.
- **Lag:** data has a **2–3 day lag**; newest data is **preliminary (dotted line)** — never diagnose on the last 3 days.
- **New GSC features to exploit:**
  - **AI natural-language filter** (global, Feb 2026)
  - **Branded Queries filter** (Nov 2025)
  - **Query Groups** (Dec 2025)

The Branded-Queries filter is especially useful for CostaLuz: separating brand search (where CTR should be high) from non-brand conveyancing queries (where AIO suppression bites) prevents a healthy brand CTR from masking a collapsed informational CTR.

### 2.3 Fixes that lift CTR without rank changes

| Fix | Spec | Expected lift |
|---|---|---|
| **Title tag rewrite** | 40–60 chars / 6–9 words, front-load keyword, add year `2026`/numbers/brackets, **brand at end** | part of 15–35% |
| **Meta description** | <160 chars, micro-CTA matching intent | part of 15–35% |
| **Structured data** | FAQ / Review / Product / HowTo schema | **15–35%** (agency reports) |

- **Latency:** changes take effect in **14–21 days** (re-crawl needed).
- **Measurement:** compare a **14–21 day post-change window vs the prior equal period** — not raw day-over-day.

> **Guard (per project memory `feedback_pre_apply_diff_guard` / `feedback_sovereign_doubt_from_dryrun`):** any auto title/meta batch MUST pre-diff against live state and quality-gate the proposal (block 3+ adjacent random nouns); snapshot post-apply. A meta-pass previously overwrote 8/10 vetted titles. For R132, the per-page CTR work should be **diagnosis-only** unless a specific, pre-diffed, single-page rewrite is approved. Also recall **`feedback_yoast_canonical_not_rest`**: on this install only title + meta are REST-writable; `_yoast_wpseo_canonical` is silently dropped.

### 2.4 The citation lever for legal pages (the real play)

For conveyancing/legal pages the AIO-citation lever is **entity-layer E-E-A-T + structured schema, not keyword density**:

- AI systems **cross-reference author JD credentials / bar admissions** against databases and **verify specific statute citations** (e.g. "California Code of Civil Procedure Section 335.1") over vague phrasing. For CostaLuz the analog is precise Spanish statute citation (Ley de Enjuiciamiento Civil articles, Ley 57/1968 for off-plan deposits, etc.) attributed to **María Luisa de Castro** with **ICA Cádiz 2745** bar admission.
- **Recommended schema stack:**
  - **FAQPage** (Q&A) — already live on CostaLuz
  - **LegalService** (practice areas)
  - **Article** with author/**Person** credentials
  - **LocalBusiness / NAP consistency**
- **AIO source density:** French AIOs average **3.2 sources cited** per overview — citation slots are scarce; entity authority is the tiebreaker.

> **Compliance overlay (project memory):** authorship is **corporate-only** ("Reviewed by María Luisa de Castro, Expert in Off-plan Property Investment"), never an individual byline; the **"not definitive legal advice" disclaimer is mandatory**; **never publish tariffs**; **Golden Visa is hard-banned**. Any schema author/credential work must respect these.

---

## Part 3 — LCP Diagnosis & Fix (Pane 3 / Lever 2: "LCP AUTH")

### 3.1 The target and the 4-phase model

LCP target: **under 2.5s for ≥75% of real-user (field) visits**. Google decomposes LCP into 4 sub-parts with empirical weights:

| Phase | Weight | Driver | Fix family |
|---|---|---|---|
| **TTFB** | ~40% | hosting/CDN + full-page caching | caching, hosting upgrade, CDN |
| **Resource Load Delay** | <10% | above-fold content swept into optimizations | exclude above-fold from lazy/optim; resource hints |
| **Resource Load Time** | ~40% | image/CSS/JS **size** | image compression, critical CSS, CDN, cache expiration |
| **Element Render Delay** | <10% | render-blocking CSS/JS, main-thread | eliminate render-blocking, smaller JS, `font-display: optional` |

**Key insight — Element Render Delay is a main-thread (not network) problem**, adding **200ms+ after downloads complete**.

### 3.2 The hero-image red herring

The reported LCP element (often a hero image) is **frequently NOT the bottleneck**:

- JS execution + render-blocking CSS commonly block the main thread **for seconds** after the image already downloaded in ~500–700ms.
- **Documented WordPress audit:** mobile LCP **5.3s → 1.8s** (TTFB 1.2s → 320ms, mobile score 58 → 95) achieved **mostly via delaying non-essential JS, full-page caching, and a hosting upgrade — NOT image format changes**.
- **When TTFB is already fast (~200ms, e.g. Cloudflare):** the bottleneck is phases 2–4 — most commonly a too-large hero (800KB–4MB; a 2.4MB PNG at 4000×2667 → 148KB WebP at 1800px q80 cut LCP 1.8s) **or** render-blocking CSS.

**Mandate:** Diagnose the **critical rendering path / waterfall first** (Chrome DevTools **Coverage Report** shows which plugins/third-party domains add the most CSS/JS bytes) **before** optimizing images. For CostaLuz (R116: theme/plugin CSS-JS bloat across 10/10 pages), the evidence already points to bloat, not images.

### 3.3 Fixes available WITHOUT WP-Admin core changes

**Already-automatic WordPress behaviors:**
- WP **5.9+** enhanced lazy-loading **already skips the first 3 images**.
- WP **6.3+** auto-adds `fetchpriority="high"` to the likely LCP image (**~5–10% LCP improvement**).
- WP **6.3** added `wp_script_attributes` filter; WP **6.4** added the native `strategy` param (`defer`/`async`) to `wp_enqueue_script` with dependency-chain handling.

**`functions.php`-class fixes (deliverable via the Code Snippets REST lever — see §3.5):**

1. **`fetchpriority="high"`** via `wp_get_attachment_image_attributes` filter with a **static `$done` flag** so **only ONE image** gets high priority per page (multiple cancel each other out).
2. **Preload hero** via `wp_head` hook at **priority 1** (runs before other `wp_head` hooks): `<link fetchpriority="high" rel="preload" as="image">` (WebP/AVIF).
3. **Inline critical CSS** via `wp_head` + **defer main stylesheet** via `style_loader_tag` filter using `rel="preload" as="style" onload` swap, or the `media="print" onload="this.media='all'"` trick with `<noscript>` fallback.
   - *Combined (1)+(2)+(3): documented **5.1s → 1.8s**, zero plugins, ~20 min.*
4. **Render-blocking JS** via `script_loader_tag` filter:
   - `async` for **DOM-independent** scripts (analytics/pixels/chat)
   - `defer` for **DOM-dependent non-critical** scripts
   - **NEVER defer jQuery** (breaks inline `jQuery()` calls)
5. **Conditional dequeuing** (highest-impact lever): dequeue e.g. WooCommerce `wc-cart-fragments` AJAX (fires on every page), `woocommerce-general` CSS on pages that don't need them.
6. **Self-host fonts** with **`font-display: optional`** (Google-recommended over `swap`; only **WP FOFT Loader** supports `optional`).
7. **Lazy-render HTML** (`#comments`/`#footer`) via FlyingPress or LiteSpeed Cache.

**Quantified expectations:**
- Eliminating render-blocking typically improves LCP **0.5–1.5s**.
- CSS sweet spot **~10–15kB compressed**; **unused CSS is often 70%+** of the stylesheet.

**Plugin tooling ranking (if a plugin route were available):** FlyingPress / LiteSpeed Cache > WP Rocket / SiteGround Optimizer for `fetchpriority` + mobile image resizing; Perfmatters / Asset CleanUp for per-page CSS/JS unloading.

### 3.4 "LCP AUTH" — the deploy boundary (R142)

The session label "LCP AUTH" maps to the **authorization/access boundary** documented in project memory:

- **Perf / site-wide `<head>` changes are WP-Admin/SiteGround operator-gated.** REST content-only access (App Password) **cannot** deploy them: App Password ≠ wp-login GUI; **GTM is theme-injected**; there is **no delay-JS plugin** installed.
- The correct autonomous path is therefore **not** "PATCH the theme" — it's the **Code Snippets v1 REST lever**.

### 3.5 The autonomous lever — Code Snippets v1 REST (R144)

- `code-snippets/v1/snippets` REST is **app-password-writable (full CRUD)**.
- This is the lever for changing **theme-injected inline output** (the GTM `ob_start` + `preg_replace_callback` pattern).
- It can host all the `functions.php`-class fixes in §3.3 (fetchpriority, hero preload, critical-CSS inline, `script_loader_tag` defer/async, conditional dequeue).
- **After deploy: purge SiteGround cache** (otherwise the change won't surface).

> **Operational guards (project memory):**
> - **`reference_costaluz_sgcaptcha_blocker`:** SiteGround WAF flags the local IP after >15 req/min bursts (30-min cooldown). Throttle; warmed-Chromium write path (T-206) may be required and needs Owner authorization each session (`feedback_costaluz_wp_write_path`).
> - **HR-004 / UKDL §HARD-RULES:** any `files/write` to a load-bearing production substrate (a live Code Snippet **is** production) **triggers a mandatory full read of `vault/knowledge_base/ukdl-universal.md` §HARD-RULES BEFORE the write**, plus backup-before-PATCH / verify-after-PATCH. Do not deploy the LCP snippet without that gate.
> - **No visual CSS changes** unless explicitly requested (INC-001 / Mistake #52) — the critical-CSS inline must preserve rendered appearance; screenshot-validate against the live page.

---

## Part 4 — Round 132 Sequencing & Recommendations

### 4.1 Recommended order of operations

1. **CTR diagnosis (read-only, this turn):** Run the §2.1 GSC recipe with the Branded-Queries filter to separate brand from informational CTR. Flag page-1 pages <3% CTR with Impressions >1,000. **Do not** auto-rewrite meta — produce a pre-diffed shortlist only.
2. **AIO-citation audit (strategic):** For the flagged informational pages, check whether CostaLuz is *cited* in the AIO. Non-cited high-impression page-1 pages are the priority schema/E-E-A-T targets (LegalService + Article/Person + precise statute citation), because cited > non-cited is the dominant lever.
3. **LCP waterfall diagnosis (before any image work):** Run DevTools Coverage on the worst R116 pages to rank plugins/third-party domains by CSS/JS bytes. Confirm whether the bottleneck is render-blocking (likely) vs hero image.
4. **LCP fix via Code Snippets REST (HR-004-gated):** Deploy the §3.3 stack (fetchpriority single-flag + hero preload + critical-CSS inline + `script_loader_tag` defer/async + conditional dequeue), throttled, backup-first, purge SG cache, screenshot-validate, then re-measure field LCP.

### 4.2 Why LCP outranks CTR rewrites in priority

CTR title/meta rewrites cap at ~15–35% and need 14–21 days; the AIO-citation lever is structural and slower. **Mobile LCP at 5.7s is a hard conversion ceiling** (R116/R52 invisible-conversion): no CTR gain matters if mobile users abandon before render. LCP is the **#1 lever**; fix it before manufacturing more content or chasing marginal meta gains.

### 4.3 Speculative / forward-looking notes (flagged)

- **[Speculation]** As European AIO informational triggering climbs +5 pts/quarter, the ES-mirror corpus will increasingly be AIO-mediated *before* it ranks conventionally — front-loading LegalService + Person schema on the ES mirrors now is likely a higher-ROI bet than waiting for classic rankings.
- **[Speculation]** The +340% impression lift for cited sites (Sistrix) suggests AIO citation behaves like a *distribution* channel, not just a CTR modifier — meaning the conversion math (AI-referred converts 2–3×) compounds. For a lead-gen legal site this could dwarf the classic-SERP CTR question entirely within 2–3 quarters.

---

## Appendix — Consolidated Metrics Table

| Metric | Value | Source |
|---|---|---|
| AIO SERP coverage (general) | ~31% (→6/10 by Feb 2026) | industry / 2026 |
| Legal/YMYL AIO trigger rate | 77.67% (~78%, highest vertical) | SE Ranking 2024 |
| EU informational AIO trigger | 47% (+5 pts/qtr) | Sistrix Mar 2026 |
| Position 1 CTR drop | −32% YoY (28%→19%) | — |
| Position 2 CTR drop | −39% YoY (20.83%→12.60%) | — |
| MailOnline CTR drop w/ AIO | −56.1% desktop / −48.2% mobile | MailOnline |
| Organic CTR drop w/ AIO | −61% (1.76%→0.61%, 25.1M impr) | Seer Sept 2025 |
| Cited-brand gain | +35% organic / +91% paid clicks | Seer Sept 2025 |
| Cited-site gain (EU) | +22% CTR, +340% impressions | Sistrix Mar 2026 |
| Featured snippet CTR | 42.9% | First Page Sage |
| Zero-click w/ AIO | ~25% of sessions; 8% vs 15% CTR | Pew 2025 |
| AI-referred conversion | 2–3× organic (+100% prof. svcs) | — |
| Title tag spec | 40–60 chars / 6–9 words | — |
| Meta description | <160 chars + micro-CTA | — |
| Schema CTR lift | 15–35% | agency reports |
| CTR change latency | 14–21 days | — |
| LCP target | <2.5s for ≥75% field visits | Google CWV |
| LCP phase weights | TTFB ~40%, RLD <10%, RLT ~40%, ERD <10% | Google |
| Documented WP LCP win | 5.3s→1.8s (JS defer + cache + hosting) | case audit |
| functions.php combined win | 5.1s→1.8s, 0 plugins, ~20 min | case audit |
| Render-blocking removal | +0.5–1.5s LCP | — |
| CSS sweet spot | 10–15kB compressed; 70%+ often unused | — |
| WP 6.3 fetchpriority auto | ~5–10% LCP improvement | WP core |

---

*Report covers all 12 research learnings. CTR lever = diagnosis-only this turn (meta-rewrite guarded); AIO-citation via schema/E-E-A-T is the dominant structural play. LCP lever = higher priority, deployed via the Code Snippets v1 REST path under the HR-004 hard-rule gate, waterfall-diagnosed before any image work.*

## Sources

- <https://support.google.com/webmasters/answer/7576553?hl=en>
- <https://www.panaclicks.com/gsc-ctr-audit-fixes/>
- <https://wor-pro.com/en/google-search-console-7-tactics-boost-ctr/>
- <https://trydecoding.com/blog/googles-organic-click-through-rate-by-search-position/>
- <https://wireframesdigital.com/seo/clicks-impressions-ctr-search-console-metrics/>
- <https://taqtics.com/blog/ai-overviews-legal-queries-citation-playbook/>
- <https://www.stackmatix.com/blog/ai-overview-impact-analysis>
- <https://www.lexiconlegalcontent.com/aio-for-lawyers-how-law-firms-can-dominate-ai-overviews-with-aio-optimization/>
- <https://www.aisosystem.com/en/blog/ai-overviews-statistics-and-trends-2026>
- <https://creativethemes.com/blocksy/blog/largest-contentful-paint-wordpress/>
- <https://next3offload.com/blog/how-to-fix-largest-contentful-paint/>
- <https://belovdigital.agency/blog/optimizing-lcp-in-wordpress/>
- <https://wpoptimizers.com/improved-largest-contentful-paint-on-wordpress/>
- <https://onlinemediamasters.com/largest-contentful-paint-wordpress/>
- <https://devmamun.com/fix-render-blocking-resources-in-wordpress/>
- <https://www.linkedin.com/pulse/your-cloudflare-configured-lcp-still-5-seconds-heres-what-dwivedi-9mzbc>
- <https://www.corewebvitals.io/core-web-vitals/largest-contentful-paint/element-render-delay>
- <https://tweakswp.com/wordpress-remove-render-blocking-css-js/>

## Run metadata

- **Prompt:** SESIÓN: CostaLuz — Ronda 132 (PANE 3: CTR PER-PAGE + LCP AUTH)
- **Depth / breadth:** 2 / 3
- **Queries used:** 5 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: regex-fallback, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 457.7 s
- **Errors during run:** 1
- **Started at:** 2026-06-30T11:11:08Z
- **Module version:** deep_research 0.1.0

<details>
<summary>Error log</summary>

- `web_search 'title tag meta description rewrite SEO b...': ddg: 0 hits parsed (possible block or empty SERP); brave: BRAVE_API_KEY not set; apify: APIFY_TOKEN / APIFU_API_KEY not set`

</details>
