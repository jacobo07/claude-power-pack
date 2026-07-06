# CostaLuz Lawyers — Ronda 17: GEO/AIO Visibility Strategy & Citation-Engineering Report

**Prepared:** 2026-06-04 · **Client:** CostaLuz Lawyers (costaluzlawyers.com) · **Owner:** María Luisa de Castro (CEO) · **Round:** R17 (AEO Readiness)
**Scope:** Synthesis of the 2026 Generative-Engine-Optimization (GEO) / AI-Overview (AIO) / Answer-Engine-Optimization (AEO) research corpus, mapped against CostaLuz's current footprint, the active competitive threat, and a prioritized action plan for Spanish property-law AI visibility.

---

## 1. Executive Summary

The center of gravity in search has moved from *ranking* to *being cited*. Three structural facts now govern CostaLuz's pipeline and frame everything in Ronda 17:

1. **AI Overviews are now the default surface, not the exception.** They appear in **>50% of searches** (up from ~18% in early 2025; BrightEdge puts the tracked-query trigger at **48%, +58% YoY**), and on **>30% of legal queries** specifically. For YMYL legal queries — exactly CostaLuz's territory — the overview *is* the answer the prospect reads first.

2. **The organic-to-AI bridge is collapsing, but SEO remains the price of entry.** Overlap between the Google top-10 and AI citations fell from **~75% (mid-2025) to 17–38% (early 2026)**; only **4.5% of AIO URLs** match a Page-1 organic URL. Yet **93.67%** of AI Overview citations still link to *at least one* top-10 result, and **87%** of ChatGPT citations match Bing's top-10. Translation: strong rankings no longer *guarantee* citation, but their absence nearly guarantees invisibility.

3. **The revenue threat is zero-click.** Organic CTR drops **61%** when an AI Overview appears (Seer, 3,119 queries), and **80–83%** of those searches become zero-click. For a flat-fee firm whose entire funnel depends on an email-first consultation booking, *the citation is now the click* — if CostaLuz is not inside the overview, the prospect never reaches the Calendly CTA.

**The single highest-leverage gap:** CostaLuz publishes strong Quick-Answer content but has **no observed FAQPage / Speakable / LegalService schema** — the precise technical lever the direct competitor (Hispanic Legal Marketing Experts) markets as its "HLME GEO Framework™." Schema-equipped legal sites are cited **2.5×–3.2× more often**; FAQPage content shows a **71% AIO citation rate**. This is a 7–30 day re-index fix with a 30–60 day compounding payoff — the cheapest, fastest win available in R17.

---

## 2. Client Baseline — What CostaLuz Already Has

| Dimension | Current State | GEO Implication |
|---|---|---|
| **Authority / E-E-A-T** | Founded 2006; María Luisa de Castro qualified 1998 (ICA Cádiz); **620+ off-plan cases won, €31M+ refunded** under Ley 57/1968 since 2012; allied with DeCastro Gabinete Jurídico since 2008 | Quantified, verifiable track record = ideal "Statistics Addition" + "Cite Sources" raw material. **96% of AIO citations come from strong-E-E-A-T sources.** |
| **Named expert team** | María Luisa de Castro, Keith Rule (client service, 2013), Jorge Medialdea (off-plan claims), Antonio Barba (abogado Cádiz), María del Carmen Romero (litigation coord.) | Person-entity + `hasCredential` schema fuel; entity-knowledge-graph density correlates with citation at **r=0.76**. |
| **Content format** | Dated "Quick Answer" / direct-answer articles (e.g. 03-Jun-2026 Spanish will-coordination guide); AI-disclosure footers; reviewed-by-María-Luisa attribution | Already aligned with answer-engine extraction; needs schema wrapper to be machine-readable. |
| **Productization** | QuickLease rental-compliance pre-purchase check (**1.000€ + IVA**); fixed personalized quote regardless of property value | Differentiator vs rivals' 1–1.5% percentage fees — a citable, comparison-table-friendly fact. |
| **Conversion path** | Calendly CTA (`marialuisa-b4a`); email-first (not call-first) | Citation must carry the brand + booking intent, since the click may never happen. |
| **Schema markup** | **None observed** (no FAQPage, Speakable, LegalService, Person/hasCredential) | **The core technical gap.** Competitor's entire pitch. |
| **llms.txt** | Not observed at `/llms.txt` | Named "highest-leverage GEO config file" (Bowen BAI-2026-002). |

---

## 3. The 2026 GEO Landscape — The Data That Reframes Everything

### 3.1 Surface ubiquity & channel shift

- AI Overviews: **>50% of searches** (Search Engine Land, Mar 2026); **48% of tracked queries, +58% YoY** (BrightEdge); **>30% of legal queries**.
- Organic CTR **−61%** when AIO present; **80–83% zero-click** (Seer, Sept 2025).
- Average AIO: **10.2 links from 4 unique domains**; typically **cites 2–4 sources** per overview.
- **Only 14% of marketers track AI search performance** (Conductor 2026) — a first-mover monitoring advantage for CostaLuz.

### 3.2 What actually correlates with being cited

Two research camps, both actionable:

**Behavioral / brand signals:**
| Correlate | Strength | Source |
|---|---|---|
| Brand search volume | **r = 0.334** (strongest in this study) | Ahrefs, Mar 2026 (863K SERPs, 4M URLs) |
| Branded mentions | 0.392 | Bowen 2026 |
| Backlinks | *Not* a top correlate | Ahrefs |

**Structural / semantic signals (Bowen "Authority Ladder," ranked higher):**
| Correlate | Strength |
|---|---|
| **Vector-embedding alignment** | **Pearson r = 0.84** |
| **Entity Knowledge-Graph density** | **r = 0.76** |
| Branded mentions | 0.392 |
| Brand search volume | 0.334 |

> **Strategic read:** The Authority Ladder places *semantic/embedding alignment and entity density above brand signals.* For CostaLuz this means: comprehensively answer the query's decomposed sub-questions (embedding alignment) and densely interlink named entities (María Luisa, Ley 20/2015, Modelo 210, Seguro Decenal) — these outrank chasing raw brand volume in the short term.

### 3.3 On-page citation mechanics

- **Ski-ramp effect:** **55% of citations** come from the **first 30% of page content** (CXL / Kevin Indig); corroborated at **44.2%** by Zyppy. → Front-load answers.
- **Comparison tables** yield **47% higher citation rates**; added trusted citations gave a **132% visibility lift** (CXL).
- **Structured data: +43% AI visibility uplift** (SearchX); **+43%** corroborated across sources.
- Optimal answer length: **40–250 words** per FAQ answer.

### 3.4 The foundational GEO tactics (Princeton/Georgia Tech/AI2/IIT-Delhi, KDD '24, GEO-bench/10K queries)

The three highest-lift tactics — directly buildable into CostaLuz's legal content:
1. **Statistics Addition** (e.g., "620+ cases, €31M refunded, 24% vs 19% tax rates")
2. **Cite Sources** (Ley 20/2015, Art. 1271 Civil Code, Modelo 210)
3. **Quotation Addition** (attributed expert quotes from María Luisa de Castro)

Headline lifts: up to **+40% visibility**; **+115.1% relative lift** for a 5th-ranked site that added source citations; averages of **+41% Position-Adjusted Word Count** and **+28% Subjective Impression**.

### 3.5 Query fan-out (the retrieval mechanic to exploit)

Each search is decomposed into **3–7 sub-queries** (Ethan Lazuk; reverse-engineered by Mike King's iPullRank "Qforia"), matched to passages via **cosine-similarity RAG**. Pages that comprehensively answer *multiple related sub-queries on one URL* win disproportionate citation share. → Build **comprehensive hub pages**, not thin single-answer posts.

---

## 4. Platform-Specific Citation Behavior (Citation ≠ Citation)

Citations diverge sharply by engine — **only ~11% of domains are cited by both ChatGPT and Perplexity** (Semrush & Lantern, independently). A single optimization will *not* serve all engines equally.

| Engine | Share / Traffic | Index | Behavioral quirk | CostaLuz tactic |
|---|---|---|---|---|
| **ChatGPT** | ~60–73% share; **87.4% of AI referral traffic** (Conductor) | **Bing** | Over-cites **product pages** (20.1% vs Perplexity 0.4%); sites with **>32,000 referring domains 3.5× more likely** cited | Ensure **Bing** indexation; treat QuickLease/service pages as citable products |
| **Perplexity** | Converts **~11× organic**; **18–22% citation CTR** | Own + web | Rewards depth | Comprehensive hubs; one of the few engines where the click survives |
| **Gemini** | Referral traffic **+388% YoY** (77.9% mobile) | Google | Powers AIO (Gemini 3) | Mobile-first; core Google SEO |
| **Claude** | Converts up to **16.8%** | — | Rarely shows inline links | Brand/entity recall over link-chasing |

**Earned-media / entity dominance (the deeper lever):**
- **86% of AI citations come from brand-managed sources** (Yext, 6.8M citations): **44% first-party + 42% listings/reviews**.
- **~90% of AI citations come from earned media** (Bowen).
- Review profiles (G2/Capterra/Trustpilot — for legal, read **Google Business / Trustpilot / legal directories**) give **3× higher citation odds** (SE Ranking, Nov 2025).
- YMYL skew: citations tilt toward **.org/.gov** (.org share jumps to **~20%+**); overall **.com ~80%, .org ~11%**. → Earn citations *from* .org/.gov-adjacent legal/government references and cite them prominently.

---

## 5. The Schema Gap — The Single Most Exploitable Lever

This is where the competitor is winning and CostaLuz is exposed.

### 5.1 The evidence base
- Law firms with structured **FAQPage** markup report **2.5× higher** citation rates vs traditional optimization.
- A full schema ecosystem (**FAQPage + LegalService + Person + Article + Organisation**) drove a **130%+ increase in SGE citations** for practice-area queries within **6 months** (Omni Marketing).
- Schema-equipped sites cited **3.2× more often**; FAQPage appears in **67%** of relevant AI answers; adding FAQ blocks gave a **44% citation jump** (Subscribe PR).
- Google AI Overviews show a **71% citation rate** for FAQ-schema content.

### 5.2 Critical implementation correctness (avoid the deprecated trap)
- **Attorney schema is deprecated (2024)** — still validates, but **no rich results, no citation lift**. **Do not use it.**
- **Correct current pattern:** `Person` + `hasCredential` (bar admission via `EducationalOccupationalCredential`) → linked to a `LegalService` entity via `worksFor`, with **stable `@id` cross-references** binding the entity graph.
- **FAQ rich results were rolled back (Aug 2023)** to government/health sites only — *but FAQPage schema retains full value for AI citation* (this is the key nuance: no blue-link rich result, but yes AI citation).
- **Timing:** schema effects appear within a **7–30 day re-index cycle**, compounding over **30–60 days**.

### 5.3 Competitor threat — Hispanic Legal Marketing Experts (HLME)
- Markets the **"HLME GEO Framework™"** (1-866-846-1929; 27+ years) for Spanish-language legal AI Overviews.
- Explicit tactics: **FAQPage JSON-LD + Speakable schema, E-E-A-T building, Spanish content hubs, monthly citation monitoring** across Google AIO, ChatGPT, Perplexity, Gemini.
- Claims: AIO on **>30% of legal queries**, **60% of clicks**; **first citations 60–90 days, broad citation 3–6 months**.
- **This is precisely the technical surface CostaLuz currently lacks.** Closing it neutralizes the competitor's entire differentiation in the Spanish legal niche.

---

## 6. Content Opportunity — The Legal Subject Matter as a Citation Asset

CostaLuz's substantive expertise maps cleanly onto a high-intent, quantifiable FAQ corpus. Each cluster below is a candidate hub page (front-loaded answer + comparison table + FAQPage schema + stat/cite/quote tactics).

### 6.1 Off-plan buyer protection (the flagship cluster)
- **Legal anchor:** **Ley 20/2015 (14 July 2015)** replaced the historically-ignored **Ley 57/68**; developers MUST secure all buyer payments via **individual bank guarantees/insurance + interest**, ring-fence funds in a separate development-only account, and name the guaranteeing bank in the contract.
- **Legal basis for selling future property:** **Article 1271, Civil Code.**
- **The repeated CRITICAL FAQ pivot (high-citation candidate):** *Bank guarantees are INVALID without a valid Building Licence (Licencia de Obra) — verify both before paying any deposit.*
- **Other protections:** 10-year structural warranty (**Seguro Decenal**); **Licencia de Primera Ocupación (LFO)** at completion; **Andalusia's DIA fact-sheet** requirement; **delays >6 months** typically = fundamental breach → full refund + interest.

### 6.2 Off-plan mechanics & costs (quantifiable = "Statistics Addition" gold)
| Item | Figure |
|---|---|
| Discount vs completed homes | 15–30% |
| Construction timeline | 2–3 years |
| Reservation deposit | €3,000–€6,000 (~30-day exclusivity) |
| On PPC signing | ~10% |
| Staged construction payments | 30–35% total |
| Balance at notary | 55–65% (foreign buyers ~30–50% cash; e.g. 42% before mortgage activates) |
| New-build VAT (IVA) | 10% (21% for separately-titled parking/storage) |
| Stamp Duty (AJD) | 0.5–1.5% (Madrid 0.75%, Catalonia 1.5%, **Andalusia 1.2%**, Valencia 1.0%) |
| Notary / Registry / Legal | 0.5–1% / 0.5–1% / 1–1.5%+VAT |
| Total fees over price | **10–13%** |
| Mortgage LTV | Non-residents max 70%; residents up to 80% (only after First Occupation Licence) |
| NIE timing | 1–2 weeks via lawyer vs up to 8 weeks via consulate |

### 6.3 Post-Brexit tax & visa cluster (high-intent UK buyers as "third-country nationals")
- **Rental income tax:** non-EU/EEA residents pay **24% with NO expense deductions** vs **19% for EU/EEA** (deductible); filed quarterly via **Modelo 210**.
- **90-days-in-180 Schengen rule** applies; UK-Spain **driving-licence exchange** in force 2023 (within 6 months of residency).
- **Golden Visa / Investor Visa eliminated/suspended April 2025** — no longer available in any modality → pushes UK buyers toward **Non-Lucrative, Digital Nomad, or Entrepreneur** visas.
  - ⚠️ **HARD BAN reminder (project memory):** *Never create, touch, mention, or recommend Golden Visa content.* The fact above is **research context for understanding buyer migration** — it must **not** become published Golden Visa guidance. Frame any content purely around the *available* alternative visas.

### 6.4 Competitive positioning to embed in content
- Fixed personalized quote **regardless of property value** vs rivals' **1–1.5% percentage fees**.
- Rival off-plan firms in this SERP: **Legal Nest Group, Lawants** (and HLME on the marketing-services side).

---

## 7. Strategic Recommendations — Ronda 17 Build Plan

Prioritized by **leverage ÷ effort**, mapped to the evidence above.

### Tier 0 — Immediate technical (7–30 day re-index payoff)
1. **Deploy the legal schema ecosystem** across all practice-area + Quick-Answer pages:
   - `FAQPage` (answers 40–250 words) — the 2.5×–3.2× lever.
   - `LegalService` (firm entity, stable `@id`).
   - `Person` + `hasCredential` for María Luisa (ICA Cádiz / 1998 admission) and team — **NOT** deprecated `Attorney`.
   - `Article` + `Organisation` with cross-referenced `@id`s for entity-graph density (r=0.76).
   - `Speakable` on Quick-Answer blocks.
   - **This is the R17 centerpiece** — it directly neutralizes HLME and is the fastest compounding win. (Note: the repo's `r17_aeo_readiness.py` / `aeo-readiness-R17.json` artifacts suggest this scoring is already in motion — wire schema output into that readiness gate.)
2. **Publish `/llms.txt`** — named highest-leverage GEO config file.
3. **Verify Bing indexation** (ChatGPit = 60–73% share, Bing index, 87.4% of AI referral traffic). Don't optimize for Google alone.

### Tier 1 — Content restructure (30–60 day payoff)
4. **Front-load every answer** into the first 30% of the page (the 55%/44.2% ski-ramp).
5. **Add comparison tables** to every cost/tax/visa cluster (+47% citation rate). The §6.2 and §6.3 tables are ready-made.
6. **Build comprehensive hub pages** answering 3–7 fan-out sub-queries per topic (off-plan protection hub, post-Brexit tax hub, visa-alternatives hub) — exploit cosine-similarity RAG matching.
7. **Inject the three GEO-bench tactics** into existing content: **Statistics** (the §6 figures), **Cite Sources** (Ley 20/2015, Art. 1271, Modelo 210), **Quotation** (attributed María Luisa quotes). The **+132% trusted-citation lift** is the target.

### Tier 2 — Entity & earned-media (60–180 day payoff)
8. **Build entity authority over backlinks** — 86% of citations from brand-managed sources; densify the knowledge graph (consistent NAP, Google Business, legal directories, Trustpilot → 3× citation odds).
9. **Pursue .org/.gov-adjacent citations** for YMYL trust skew (cite and get cited by bar associations, government legal-info portals).
10. **Grow brand search volume** (r=0.334) via the productized QuickLease offering and case-win PR.

### Tier 3 — Measurement (close the 14%-of-marketers gap)
11. **Stand up monthly multi-engine citation monitoring** (Google AIO, ChatGPT, Perplexity, Gemini, Claude) — match HLME's monitoring claim. Only 14% of competitors do this; it's a durable advantage and the only way to prove the 60–90 day citation-onset thesis for CostaLuz's own pages.

---

## 8. Realistic Timeline & KPIs

| Milestone | Mechanism | Expected window |
|---|---|---|
| Schema re-indexed | 7–30 day re-index cycle | Weeks 1–4 |
| First AI citations | Matches HLME's 60–90 day claim; schema compounds 30–60 days | Months 2–3 |
| Broad citation across clusters | Omni Marketing's 130%+ SGE-citation pattern at 6 months | Months 3–6 |

**KPIs to track in the R17 readiness gate:** (a) % of pages with valid FAQPage/LegalService/Person schema; (b) AIO citation count per cluster per engine (monthly); (c) Bing index coverage; (d) brand search volume trend; (e) entity-graph completeness (named entities with stable `@id`).

---

## 9. Risks, Caveats & Speculation Flags

- **🔴 Speculative correlation strength:** The r=0.84 vector-embedding figure (Bowen BAI-2026-002) and the 132%/130% lift figures come from vendor/marketing studies, not peer-reviewed work (only the Princeton/KDD '24 GEO-bench is academic). Treat the *direction* as reliable, the *magnitude* as optimistic. **Flagged as moderate-confidence.**
- **🟡 Platform divergence risk:** Optimizing for ChatGPT (Bing) and Google AIO (Gemini) requires *different* indexation hygiene; an 11%-overlap world means no single fix covers all engines. Budget for both.
- **🟢 Hard compliance guardrails (project law, non-negotiable):** Golden Visa **HARD BAN** (research context only, never published); **English & Spanish only — never imply Arabic service**; **no invented data** (every stat above is research-sourced and must be client-confirmed before publishing as CostaLuz's own claim); **mandatory "not definitive legal advice" disclaimer**; **off-plan authority = María Luisa, never María del Carmen** (recurring drift); **articles carry no individual byline — only "Reviewed by María Luisa de Castro."**
- **⚠️ WP write-path reminder:** any deployment of schema/content to costaluzlawyers.com uses `content.raw` + `context=edit` (never `content.rendered`), backup-before-PATCH, and the warmed-Chromium path (SiteGround WAF burst-throttles bare requests).

---

## 10. Bottom Line for Ronda 17

CostaLuz already owns the two hardest assets in GEO: **genuine E-E-A-T** (620+ wins, €31M, a credentialed named expert since 1998) and **answer-formatted content**. It is losing on the *cheapest* one: **machine-readable structure.** The competitor's entire "HLME GEO Framework™" is a schema-and-monitoring play that CostaLuz can replicate and surpass because CostaLuz has the *substantive authority* the schema is meant to advertise.

**Ronda 17's mandate:** ship the FAQPage + LegalService + Person/hasCredential schema ecosystem and `/llms.txt`, restructure the top clusters to front-loaded comparison-table hubs with stats/cites/quotes, verify Bing indexation, and stand up monthly multi-engine citation monitoring. That sequence converts CostaLuz's earned authority into the citation share that — in a 61%-CTR-drop, 80% zero-click world — *is* the funnel.

---

*Sources synthesized: Ahrefs (Mar 2026), Seer Interactive (Sept 2025), CXL/Kevin Indig, Zyppy 2025, Yext (6.8M citations), Semrush, Lantern, SE Ranking (Nov 2025), Conductor 2026, BrightEdge/Demand Local, Bowen AI Strategy Group (BAI-2026-002, CC BY 4.0), Omni Marketing, Subscribe PR, Wellows, Aggarwal et al. (Princeton/GT/AI2/IIT-Delhi, KDD '24 GEO-bench), Ethan Lazuk / Mike King (iPullRank Qforia), plus Spanish property-law statutory sources (Ley 20/2015, Ley 57/68, Art. 1271 CC, Modelo 210) and competitive intelligence on Hispanic Legal Marketing Experts, Legal Nest Group, and Lawants.*

---

Report complete. Two concrete next actions I can take this turn if you want to move R17 from strategy to build:

1. **Generate the actual JSON-LD schema blocks** (FAQPage + LegalService + Person/hasCredential with stable `@id` graph) for the off-plan flagship cluster — ready to wire into `r17_aeo_readiness.py`.
2. **Draft `/llms.txt`** for costaluzlawyers.com.

Which do you want first — or should I save this report to `clients/costaluz/` / the Obsidian vault as the R17 strategy doc?

## Sources

- <https://www.costaluzlawyers.com/>
- <https://www.costaluzlawyers.com/welcome/>
- <https://hispaniclegalmarketingexperts.com/geo-generative-engine-optimization-law-firms/>
- <https://www.legaltica.com/abogados/costaluz-lawyers/>
- <https://www.thinkspain.com/spain-listings/o5561>
- <https://scholar.google.com/>
- <https://www.stackmatix.com/blog/ai-overview-citation-analysis>
- <https://www.eyeonspain.com/blogs/costaluz/24115/legal-tip-1519-spains-supreme-court-doubles-down-on-off-plan-buyer-protection.aspx>
- <https://aithinkerlab.com/generative-engine-optimization-2026/>
- <https://en.ai-pedias.com/blog/geo-generative-engine-optimization-guide-2026>
- <https://www.oltre.ai/blog/generative-engine-optimization/>
- <https://dr3amsystems.com/resources/geo-generative-engine-optimization/>
- <https://geoptie.com/blog/generative-engine-optimization>
- <https://omnimarketing.agency/what-specific-schema-markup-do-sge-citations-prioritise-for-legal-sites/>
- <https://torontoseo.com/learn/schema-markup-for-llm-citation-for-lawyers/>
- <https://www.bowenaistrategygroup.com/geo-benchmarks-2026.html>
- <https://subscribepr.com/blog/legal-schema-markup-guide/>
- <https://presenceai.app/blog/llm-citation-optimization-12-strategies-ai-search-visibility-2026>
- <https://www.costaluzlawyers.com/buying-property-in-spain-complete-legal-guide-2026/>
- <https://www.legalnestgroup.com/en/blog/buying-property-off-plan-in-spain>
- <https://www.lawants.com/en/buying-property-under-construction-spain/>
- <https://www.nockolds.es/buying-off-plan-property-spain/>
- <https://www.idealista.com/en/news/property-for-sale-in-spain/2025/09/09/857154-buying-off-plan-in-spain-a-complete-guide-for-foreign-buyers>

## Run metadata

- **Prompt:** SESIÓN: CostaLuz — Ronda 17
- **Depth / breadth:** 2 / 3
- **Queries used:** 6 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: bs4-strip, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 497.3 s
- **Errors during run:** 1
- **Started at:** 2026-06-04T14:07:27Z
- **Module version:** deep_research 0.1.0

<details>
<summary>Error log</summary>

- `extract_learnings: llm-parse: no valid JSON in 3039 chars; head: '{"learnings":["Spanish Supreme Court doctrine under Ley 57/1968 (now Ley 20/2015) holds the DEPOSITARY bank that received off-plan stage-payments stri'; anthropic-sdk: ANTHROPIC_API_KEY not set`

</details>
