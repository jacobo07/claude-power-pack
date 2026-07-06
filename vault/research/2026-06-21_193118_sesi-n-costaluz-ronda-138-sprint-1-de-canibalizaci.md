# CostaLuz — Ronda 138 (Sprint 1): De-Cannibalization
## Research Report — Keyword & Intent Cannibalization in the SEO + GEO Era (2026)

---

## 1. Executive Summary

Keyword cannibalization — two or more of a site's own URLs competing for the **same search intent** — has moved from a second-order hygiene problem to a **first-order ranking and citation risk** in 2026. Three forces converged:

1. **Google penalizes internal ranking conflict ~3× more aggressively** since the March 2026 core update (compounded by the February 2026 Discover update). Cannibalization-affected sites are seeing visibility drops at roughly 3× the average.
2. **AI search engines exclude cannibalized pages entirely.** Where classic SEO merely splits position (#3 → #7), LLM-backed answer engines cluster near-duplicate URLs, pick **one representative page**, and drop the rest from citations — there is no "page two" in an AI Overview. For a GEO-first project like CostaLuz, this is the dominant cost.
3. The **economics of fixing it are exceptional**: documented consolidation sprints lift organic traffic 22–34% within 4–8 weeks with **zero new content** — pure architectural cleanup.

This report consolidates the full research corpus into an operational doctrine for the CostaLuz R138 de-cannibalization sprint: definitions, detection, winner-selection, the fix hierarchy, the intent test that prevents over-merging, the internal-anchor-text discipline, and a quantified evidence base. It also introduces a **concentration-metric framing (HHI-derived)** for prioritizing which cannibalization clusters to fix first.

> **Speculative flag (clearly marked):** Section 9's HHI-for-cannibalization severity index is a novel synthesis I am proposing from the antitrust-concentration learnings; it is not an industry-standard metric. Treat it as a prioritization heuristic, not a validated scoring system.

---

## 2. What Cannibalization Is — and Is Not (2026 Definition)

The single most important reframing: **cannibalization is defined by shared SEARCH INTENT, not by shared keywords.**

| Condition | Verdict |
|---|---|
| Same intent **+** same format | **Conflict** (cannibalization) |
| Same intent **+** different format (guide vs. checklist) | Usually **fine** |
| Same keyword **+** different intent (informational vs. transactional) | **Not** cannibalization |
| Same keyword **+** different location target | **Not** cannibalization |
| Two pages holding **stable, distinct top-10 positions** (e.g., #3 and #7) | **Not** a problem — leave alone |

### 2.1 The diagnostic test (three-part, all must be true)

A multi-URL ranking is genuine cannibalization **only if**:

1. **Same query class**, AND
2. **Same user need**, AND
3. **Same next action / page role**.

Similar wording alone does not prove cannibalization. Ahrefs explicitly argues that many dashboard-flagged cases are non-issues because the second URL's traffic is **genuinely incremental, not stolen**.

### 2.2 Legitimate multi-URL coverage (do NOT merge)

Canonical examples of strategic, intentional multi-URL ranking that merging would **destroy**:

- **Health** ranking multiple "protein powder" pages
- **Nuclino** ranking multiple "project management software" pages
- **Allbirds** ranking three distinct "running shoes" pages
- **Apple** ranking "MacBook Pro" three times
- Product page vs. blog explainer; glossary vs. how-to; pillar-cluster architecture; branded queries

The recurring failure mode is **over-correction** — merging valid intent-split pages and collapsing legitimate coverage.

---

## 3. The AI-Search Amplification (Why This Matters Most for CostaLuz)

CostaLuz is run as a **GEO/AIO** project, not a classic SEO project — which makes the AI-search penalty the headline risk.

- **Microsoft confirmation (Fabrice Canel & Krishna Madhavan, Bing Webmaster Blog, December 2025):** LLMs group near-duplicate URLs into a **single cluster** and select **ONE representative page** — which may be the **outdated or unintended** one. Duplicate content carries **no penalty per se**, but it **dilutes authority and slows update propagation**.
- **Complete exclusion, not demotion:** In AI search, cannibalization causes **total loss of the citation** (0 traffic), not a position drop. Answer engines (ChatGPT Search, Perplexity, Claude, Google AI Overviews) cite **one URL per claim** with no second-page fallback.

### 3.1 The click-economics backdrop (why every citation counts)

| Metric | Finding | Source |
|---|---|---|
| Organic CTR with AI Overview present | Fell **1.76% → 0.61% (−61%)** | Seer Interactive (3,119 informational queries, 42 orgs, 25.1M impressions, Jun 2024–Sep 2025) |
| Reward for being **cited inside** the AI Overview | **+35% organic**, **+91% paid** clicks | Seer Interactive |
| Click-through on a traditional result when AI summary present | **8%** of visits (vs. 15% without) | Pew Research (900 US adults, March 2025) |
| AI-response visibility lift from citation/statistical/fluency optimization | **up to +40%** | Aggarwal et al., "GEO: Generative Engine Optimization," KDD '24 (DOI 10.1145/3637528.3671900) |

**Implication for CostaLuz:** with classic CTR collapsing ~61% under AI Overviews, the **only** reliable traffic path is being the cited representative page. Cannibalization is the fastest way to forfeit that single citation slot.

---

## 4. Detection Methodology (Free-First, Multi-Signal)

**A single-signal diagnosis is the most common false positive.** Cross-validate with at least two of the methods below before acting.

### 4.1 The canonical GSC method

1. Google Search Console → **Performance** report.
2. Filter by **Query AND Page dimensions simultaneously** (window: last **28 days–6 months** to smooth volatility).
3. The cannibalization signal is **2+ of your own URLs splitting IMPRESSIONS** for one query (split *impressions*, not clicks).
4. Position behavior confirms it:
   - **Position 20–80 instability band** ("seesaw" / "X-curve") = Google rotating candidates, OR
   - Pages **clustered at positions 8–15 / 3–10** ("cannibalization zone") where none break the top 5.

### 4.2 Fast cross-checks

| Method | Time | Note |
|---|---|---|
| `site:domain.com "keyword"` | 30 sec | Returns only a **sample** — an r/SEO case showed only 800 of 19,000 GSC-indexed pages surfacing |
| Screaming Frog (free ≤500 URLs) | minutes | Flags duplicate titles / H1s |
| **SERP Overlap analysis** | minutes | **>60–70% top-10 overlap = same-intent cannibalization; <30% = false positive; 30–60% = gray zone** |
| Full audit | longer | Export queries+pages to Sheets, pivot on **distinct-URL-count**, sort by impressions |

### 4.3 Prevention beats detection

Most cannibalization is an **editorial-process failure, not a technical one**. The structural fix is a **site-level keyword map: 1 Primary + 3 Secondary keywords per page**, checked at **content-brief time**. CostaLuz should adopt this map as a gating artifact before any new content brief (it dovetails with the existing NLV cluster-cannibalization work from R147–R148).

---

## 5. Winner Selection & Fix Hierarchy

### 5.1 Selecting the keeper (the "winner")

Rank candidates by:

1. **Ranking position**
2. **Last-90-day clicks**
3. **Backlink count**
4. **Content quality / best crawl history**
5. **Tie-break:** keep the page with **fewer inbound internal links** (cheaper to redirect/re-point).

### 5.2 The five canonical fixes, in impact order

| # | Fix | When | Equity behavior | Notes |
|---|---|---|---|---|
| 1 | **Merge + 301 redirect** the loser | **Identical intent** | **Fully transfers link equity** | Highest impact; applies to **60–70%** of real cases. Pick the URL with most backlinks/best crawl history, absorb unique content, 301 the loser, update internal links, request re-indexing |
| 2 | **rel=canonical** | Genuine duplicates / e-commerce filter variants that must stay live | Does **NOT** consolidate equity efficiently | Google calls it a **"strong signal"** (~90%+ stick rate) but it's a **HINT, not a directive** — Google may ignore it if pages differ too much. Explicitly a **"soft fix / last resort"** |
| 3 | **Internal-link disambiguation** | Distinct but overlapping intent | Signals hierarchy | See Section 6 |
| 4 | **Rewrite / de-optimize titles, H1, meta** | Blog vs. service page overlap | Re-targets the lesser page | Rename toward education (e.g., "→ Strategy & Examples"), strip the commercial term, rewrite intro |
| 5 | **410 Gone** | Valueless pages, **no backlinks** | n/a | For genuine deadweight |

**AVOID noindex** for same-site canonicalization — Google's docs explicitly recommend against it because it **blocks the page entirely**. (`301 / canonical / noindex` are all last-resort relative to merge + intent differentiation.)

### 5.3 The intent-driven decision (not threshold-driven)

- **301 merge+redirect** = gold standard **ONLY when pages serve identical intent**. Recovery: **2–4 weeks** (rankings) / **1–3 months** (full).
- **PIVOT / differentiation protocol** = when a **blog post and a service/product page** have genuine but overlapping intent: de-optimize the blog (remove the commercial term from headers/meta/H1, rename, add an internal link to the service page with exact-match anchor, rewrite intro toward education).
- **Canonical** = reserved for technical/near-duplicates that must stay live.
- **410** = valueless, no backlinks.

### 5.4 Severity scoring formula

```
Severity = (Total Impressions × Competing URL Count) / Average Position
```
**> 1,000 = critical.** Use this to triage the cluster backlog.

### 5.5 Post-fix timeline (set expectations)

| Phase | Timing | What happens |
|---|---|---|
| Recrawl / reclassify | **2–8 weeks** | Google re-evaluates |
| Canonical / redirect effect | **2–6 weeks** | Signal propagates |
| **Temporary traffic dip** | **weeks 2–4** | Expect **10–30%** dip — do NOT panic-revert |
| Full stabilization | **weeks 7–12** | Gains consolidate |

---

## 6. Internal Anchor Text Doctrine

Internal anchor text is a **direct ranking signal** Google uses to decide what a page should rank for. This is the lever for the **R138 intent-disambiguation approach** (per the git log, R138 was executed precisely as "de-cannibalization via intent-disambiguation links").

### 6.1 Core rules

- **Reusing the same anchor across multiple pages dilutes the signal and splits authority** → the wrong page ranks, or rankings stall near page 2.
- Assign **ONE primary page per core topic**; use the strongest/most consistent anchor **only for that page**.
- Support secondary pages with **varied contextual anchors**.
- **REMOVE** existing internal links to other pages that use similar anchor text.
- Audit anchors (Screaming Frog) **starting with pages ranking at positions 2–3** — that's where clarity unlocks movement.
- The **15–25 words surrounding the link** often carry more relevance weight than the anchor itself.

### 6.2 Keyword-cluster consolidation

Multiple pages receiving similar exact-match anchors **split the relevance signal**. Identify which single page should **own** each keyword cluster, consolidate internal linking toward it, and **vary phrasing** across placements:

> e.g., `"keyword research"` / `"how to do keyword research"` / `"keyword research for SEO"` — never repeat one exact anchor to one page (that repetition is itself a pattern flag).

### 6.3 Anchor distribution ceilings (2026 consensus)

**Internal links** follow *different* rules from external — Google expects you to control your own architecture:

| Anchor type | Internal distribution | External distribution |
|---|---|---|
| Keyword-rich (exact + partial) | **40–60%** | partial match **15–25%** |
| Descriptive / LSI | 25–35% | — |
| Generic | 10–20% | 10–20% |
| Branded | — | **30–50%** |
| Naked URL | — | 5–15% |
| **Exact match** | (within the 40–60% keyword-rich band) | **only 1–5%** (some allow 3–8%) |

**External exact-match above 10–15% for a single keyword = Penguin penalty territory.**

### 6.4 Page-type exact-match ceilings

| Page type | Exact-match ceiling |
|---|---|
| Homepage | **<3%** |
| Service / money pages | **<5%** |
| Blog / informational | **<8%** |
| Local landing pages | **<5%** (location-modified partials like "W3Era Dallas" function as branded) |

**Evidence:** a study of **23 million internal links** found URLs with **greater anchor variation consistently attract more search traffic** than repetitive exact-match anchors. Google **Penguin** (launched 2012, folded into core 2016) targets these patterns; recovery = halt new exact-match links, build **3–5 offset (branded/generic/naked) links/month**, disavow only **Spam Score 40%+** as last resort, with recovery in **6–12 weeks**.

### 6.5 Internal-link consolidation case proof

- **Backlinko:** **+466% YoY clicks** from one 301 consolidation.
- **Planable:** **+176% organic traffic in 6 months** after merging pages ranking between positions 15–45 and redirecting weaker URLs.

---

## 7. Quantified Evidence Base (Case Studies)

| Case | Action | Result | Window |
|---|---|---|---|
| **Cicéro (legal site)** | 87 articles → 14 multi-URL queries; fixed only **4 high-volume commercial cases** | **+22% organic traffic**, zero new content | next month |
| Cicéro fix-mix benchmark | — | content merge used in **~60%** of cases | — |
| **B2B SaaS** | 120 articles / 23 cases → **12 merges, 7 redirects, 4 de-opts** | **+34% traffic** | 8 weeks |
| **E-commerce** | merge | position **18 → 6** | 3 weeks |
| **Email-marketing** | 3-post merge | position **15 → 5**, **+300% clicks** | 4 weeks |
| **E-commerce (AEO)** | merged 12 posts → 4 differentiated 2,000-word guides | **AEO Site Rank 42 → 51** (+9) | — |
| **Consolidation sprints (general)** | merge | **AEO Site Rank +5–8 points** | — |

**AEO weighting note:** AEOContent.ai weights cannibalization at only **2% raw**, but **caps the score at 6/10 when Topic Coherence ≤ 4** — i.e., cannibalization is a *latent* penalty that becomes a hard ceiling once topical clarity degrades. This is the GEO-equivalent of the AI-exclusion mechanism in Section 3.

**Schema-gap opportunity (Lumina audit of top-10 EN+DE "keyword cannibalization" guides):** only **1/10 ships FAQPage schema**; one DE article ranks **#4 on Google.de with zero JSON-LD**; SEMrush's EN guide had a **`dateModified` 1,141 days stale** (last bumped March 2023). → A competitor field where freshness + FAQPage schema is an open lever.

---

## 8. When NOT to Act (False-Positive Guardrails)

Drop the case if any of these hold:

- The two pages serve **different intents** (informational vs. transactional vs. commercial/navigational) or **different locations**.
- The pages hold **stable, distinct top-10 positions** (#3 and #7) — no instability.
- SERP overlap is **<30%** (false positive) — and treat 30–60% as a gray zone requiring a third signal.
- The second URL's traffic is **incremental, not cannibalized** (Ahrefs caution).
- A **canonical alone won't fix it** if titles, headings, links, and body copy still send mixed signals — canonical is repeatedly warned against as an overused shortcut.

---

## 9. Proposed Prioritization Lens — HHI-Derived Cluster Concentration Index

> **Speculation flag:** This section is a novel synthesis I am proposing from the antitrust-concentration learnings. It is **not** an established SEO metric. Use it as a triage heuristic alongside the validated severity formula in §5.4.

### 9.1 The borrowed instrument

The **Herfindahl-Hirschman Index (HHI)** — conceived by Albert O. Hirschman (1945, *National Power and the Structure of Foreign Trade*) and independently by Orris C. Herfindahl (1950 Columbia Ph.D. dissertation, *Concentration in the U.S. Steel Industry*) — is the **sum of squared market shares** of all firms, scaling **0 to 10,000** (a 100% monopoly = 10,000). It **weights larger firms more heavily** than concentration ratios (CR4/CR8), capturing size-distribution inequality the CRs miss.

Reference thresholds (DOJ/FTC **2023** Merger Guidelines):
- "Highly concentrated" lowered to **HHI > 1,800** (from 2,500 in 2010).
- Structural-presumption delta-HHI trigger lowered to **+100 points** (from +200).
- Separate presumption: merged share **>30%** with delta-HHI **>100**.
- Merger-driven HHI change for two firms = **2 × s₁ × s₂** (e.g., a 15% + 10% merger = **300 points**).
- Empirical support (Bhattacharya, Illanes & Stillerman, 2006–2017 US retail): delta-HHI 100–200 raised prices **2.9pp** more than sub-100; **>200 raised them 5.1pp** more.

**Caveats inherited:** HHI ties to the Cournot model (HHI ÷ price-elasticity ∝ market-share-weighted Lerner Index); it **breaks down** with differentiated products, high fixed-to-variable cost ratios, and **winner-take-all / two-sided platform markets**, and is **critically dependent on market definition**. Alternatives: GUPPI, the Lerner Index, and Ahern/Kong/Yan's "effective firms" statistic (NBER w32057).

### 9.2 The analogy (why it maps to cannibalization)

Treat **each query as a "market"** and **each of your competing URLs as a "firm,"** with **impression share** as market share. Then:

- A query where **one URL holds ~all impressions** → HHI ≈ 10,000 → **healthy** (one clear representative — exactly what an LLM wants to pick).
- A query split evenly across, say, four of your URLs → HHI ≈ 2,500 → **fragmented** → high cannibalization, high AI-exclusion risk.
- The **delta-HHI of merging two of your URLs = 2 × s₁ × s₂** — a direct estimate of how much *internal consolidation* you'd gain by merging that specific pair.

**Crucially, the winner-take-all caveat is a feature here, not a bug:** AI answer engines *are* winner-take-all (one cited URL). So you actually **want** maximum concentration (HHI → 10,000) on the keeper page. The antitrust framing inverts cleanly: in markets, high HHI is bad (monopoly); in **your own site's competition for a query, high HHI is the goal**.

### 9.3 Practical triage

1. For each cannibalized query, compute impression-share HHI across your competing URLs.
2. **Low HHI (most fragmented) + high impressions = fix first** (combine with §5.4: `(Impressions × URL count) / Avg position > 1,000 = critical`).
3. Use **delta-HHI = 2 × s₁ × s₂** to rank *which pair* to merge for the biggest single-move consolidation.
4. Post-merge, re-measure HHI — a jump toward 10,000 on the keeper is your leading indicator of success, weeks before rankings stabilize.

This is a **prioritization overlay**, not a replacement for the intent test (§2.1) — never merge on concentration math alone if the URLs serve distinct intents.

---

## 10. Application to CostaLuz — R138 Sprint 1

**Context from the repo state:** R138 was already executed as *"de-cannibalization via intent-disambiguation links (canonical impossible + wrong here)"*, building on R147 (NLV cluster, 7 internal links, canonical pairs `#29175→#29150`, `#23108→#9794`) and R148 (canonical consolidation live, NLV 17-page cluster census). This research validates and extends that direction.

### 10.1 Why "canonical impossible + wrong here" is correct doctrine

The R138 decision aligns exactly with the research:

- **Canonical does NOT consolidate link equity** and is a **HINT Google may ignore** if pages differ — useless for genuine intent-overlap cases.
- For CostaLuz's NLV cluster (sibling pages with **distinct but overlapping** intent), the correct lever is **internal-link disambiguation + de-optimization** (§5.2 fix #3–#4, §6), not canonical (#2).
- Two known constraints reinforce this: **`_yoast_wpseo_canonical` is silently dropped on POST** (canonical isn't even REST-writable on this install — see memory `feedback_yoast_canonical_not_rest.md`), and **canonical is a soft fix anyway**. Internal anchor disambiguation is both *writable via REST* and *the doctrinally superior fix*.

### 10.2 The CostaLuz-specific risk profile

| Factor | CostaLuz reality | Consequence |
|---|---|---|
| Project type | GEO/AIO-first (AI visibility is the goal) | **AI-exclusion** (§3) is the headline risk, not position-splitting |
| Site shape | Bilingual EN/ES, ~423 WP pages, NLV split across **≥5 sibling pages** | Classic editorial-process cannibalization (§4.3) |
| Canonical write path | **Blocked** (Yoast canonical not REST-writable) | Forces the **internal-link / de-optimization** path — which is the better fix anyway |
| Position lever | Confirmed = links + canonical, but **audit cannibalization FIRST** (memory R147) | Sequence discipline already encoded |

### 10.3 Recommended R138+ execution sequence

1. **Build the keyword map artifact** (1 Primary + 3 Secondary per page) for the NLV cluster — this is the prevention layer (§4.3) and the gate for all future briefs.
2. **Run the GSC Query×Page detection** (§4.1) over a 6-month window on the NLV cluster; cross-validate with `site:` + SERP-overlap (§4.2). Reject single-signal calls.
3. **Compute severity** (§5.4) and **HHI overlay** (§9.3) per query → triage backlog.
4. For each confirmed same-intent pair: **merge + 301** the loser into the keeper (winner-selection §5.1). Where the canonical pairs from R147 (`#29175→#29150`, `#23108→#9794`) are genuinely same-intent, prefer 301 over the (non-writable, soft) canonical.
5. For distinct-but-overlapping intent (the R138 case): **de-optimize the lesser page** (strip head keyword from title/H1/meta, retarget to long-tail) **+ add one varied-anchor internal link** to the keeper (§6). Audit existing anchors and **remove competing-anchor internal links** to non-owner pages.
6. **Schema lever:** ship **FAQPage JSON-LD** on the keeper pages — the Lumina audit shows only 1/10 competitors do this (§7). (Note: align with existing FAQPage work flagged in memory R51.)
7. **Set expectations** with María: **10–30% temporary dip in weeks 2–4** is normal (§5.5); do not revert. Measurement at the existing 06-28 gate.
8. **Re-measure HHI / impression concentration** as the leading success indicator before rankings stabilize (weeks 7–12).

### 10.4 Hard-rule guardrails for this sprint

- **Do NOT over-merge** legitimate EN/ES or intent-split pages (§8) — the bilingual mirror pages are *not* cannibals of each other.
- **Respect the hard bans** in selection: exclude **Golden Visa** and any hard-ban slugs *before* any bulk operation (memory `feedback_hardban_bulk_op_guard.md`).
- **No invented data**; **backup before any PATCH, verify after**; **content.raw + context=edit** for all WP writes (project CLAUDE.md).
- **Internal anchors** stay within ceilings (§6.4): service/money pages **<5%** exact-match, blog **<8%**.

---

## 11. Key Takeaways

1. **Intent, not keywords, defines cannibalization** — and the three-part test (same query class + same need + same next action) is the gate before any action.
2. **AI search makes it binary**: cannibalized pages aren't demoted, they're **excluded from citations entirely** — the central stake for a GEO project.
3. **Merge + 301 is the gold standard** (60–70% of real cases); **canonical is a soft, equity-leaky last resort** — and on CostaLuz it isn't even REST-writable, which conveniently forces the better path.
4. **Internal-anchor disambiguation** (the R138 lever) is doctrinally correct for distinct-but-overlapping intent: one owner per cluster, varied anchors, remove competing links.
5. **Detection must be multi-signal** (GSC Query×Page + `site:` + SERP overlap); single-signal is the #1 false positive.
6. **Expect a 10–30% week-2–4 dip; gains land weeks 7–12.** Consolidation routinely returns +22–34% with zero new content.
7. **Prioritize with the severity formula** `(Impressions × URL count) / Avg position > 1,000 = critical`, optionally overlaid with the **HHI concentration heuristic** (§9, speculative) — where, uniquely, **higher concentration on the keeper is the win**.

---

*Report compiled for CostaLuz R138 Sprint 1 (De-Cannibalization). Validates the already-executed intent-disambiguation approach and extends it with detection methodology, fix hierarchy, anchor-text discipline, a quantified evidence base, and a proposed HHI-derived prioritization lens.*

## Sources

- <https://cicero.studio/en/blog/keyword-cannibalization-seo/>
- <https://morningscore.io/how-to-resolve-issues-of-keyword-cannibalization/>
- <https://www.wicked-seo.com/2026/04/07/keyword-cannibalization-how-to-find-and-fix-it-in-2026/>
- <https://searchenginerealm.com/seo-strategy-and-growth/keyword-cannibalization/>
- <https://www.linkedin.com/pulse/canonicalization-vs-keyword-cannibalization-key-seo-fixes-agrawal-txfwf>
- <https://www.traficxo.com/blog/content-cannibalization>
- <https://intercore.net/education/content-cannibalization-guide/>
- <https://wellows.com/blog/what-is-content-cannibalization/>
- <https://heydaymarketing.com/blog/how-to-avoid-keyword-cannibalization>
- <https://www.aeocontent.ai/knowledge/content-cannibalization/>
- <https://marketingagent.blog/2026/04/23/tutorial-fix-keyword-cannibalization-in-search-console/>
- <https://redbit.wtf/guides/how-to-find-keyword-cannibalization-in-search-console>
- <https://polytraffic.com/articles/search-console-cannibalization-detection>
- <https://seocluster.ai/blog/keyword-cannibalization-how-to-detect-fix>
- <https://lumina-seo.com/blog/keyword-cannibalization-guide/>
- <https://www.investopedia.com/terms/h/hhi.asp>
- <https://ryanoconnellfinance.com/market-concentration-hhi/>
- <https://www.promarket.org/2024/06/24/an-explainer-on-how-market-concentration-is-measured/>
- <https://fairlaneo.com/market-concentration-and-herfindahl-hirschman-index/>
- <https://backlinko.com/keyword-cannibalization>
- <https://diffusedigitalmarketing.com/identifying-keyword-cannibalization/>
- <https://webtrek.io/blog/how-to-fix-content-cannibalization-properly>
- <https://www.linkedin.com/posts/md-julfikar-ali-58886b309_seo-internallinking-technicalseo-activity-7421954222826512384-Dp-7>
- <https://3way.social/blog/exact-match-vs-partial-match-anchor-text/>
- <https://www.w3era.com/blog/seo/anchor-text-optimization-guide/>
- <https://anchortool.dev/blog/exact-match-vs-partial-match-anchor>
- <https://anchorape.com/blog/right-anchor-text-strategy>
- <https://linkscope.io/blog/anchor-text-guide/>

## Run metadata

- **Prompt:** SESIÓN: CostaLuz — Ronda 138 (SPRINT 1): DE-CANIBALIZACIÓN
- **Depth / breadth:** 2 / 3
- **Queries used:** 6 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 521.7 s
- **Errors during run:** 1
- **Started at:** 2026-06-21T17:31:18Z
- **Module version:** deep_research 0.1.0

<details>
<summary>Error log</summary>

- `fetch_page 'https://anzlaw.thomsonreuters.com/0-107-4556?transitionType=...': page-fetch: https://anzlaw.thomsonreuters.com/0-107-4556?transitionType=Default&contextData=(sc.Default): HTTP Error 403: Forbidden`

</details>
