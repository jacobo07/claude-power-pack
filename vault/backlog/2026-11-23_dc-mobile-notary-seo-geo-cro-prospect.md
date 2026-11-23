# CPP-PROSPECT-20261123-001 — DC Mobile Notary: SEO / GEO / AEO / CRO opportunity

**Recorded:** 2026-11-23 (Europe/Madrid).
**Type:** EXTERNAL COMMERCIAL PROSPECT / CASE-STUDY CANDIDATE. This is **not** a Claude Power Pack runtime bug, an implementation approval, or a new architectural owner.
**Status:** OPEN / INITIAL TRIAGE ONLY / NO CONTACT / NO CLIENT RELATIONSHIP CONFIRMED / NO WORK AUTHORIZED.
**Priority:** B (qualify before outreach); potential higher priority only after independently validated opportunity and authorized outreach.
**Website:** https://www.dcmobilenotary.com/
**Market:** Washington, DC metropolitan area (including Northern Virginia and Maryland), with nationwide U.S. document-processing services.
**Suggested services:** evidence-first technical and local SEO, multilingual quality, AI-answer visibility (GEO/AEO), conversion-rate optimization (CRO), and selectively UX improvements.
**Site redesign:** NOT PRESCRIBED. Prefer measurable fixes to existing conversion paths over speculative full rebuilds.

## 1. Opportunity thesis — explicitly a hypothesis

A documented-services business handling apostilles, document authentication, embassy legalization, translation, mobile notary work and fingerprinting may benefit from clearer service messaging, improved discoverability for high-intent queries, and easier quote conversion. It already has a meaningful service-page footprint and public trust content; do **not** represent it as a business with zero SEO or an obviously failed website.

No Search Console, Analytics, CRM, conversion, backlink, SERP-ranking, live Core Web Vitals, revenue or AI-referral data was accessed. Traffic loss, missed revenue, ranking position and expected uplift are **UNKNOWN**. Do not invent any of these.

## 2. Evidence and investigation register

All evidence is from public pages; retrieved HTML/search snapshots can be stale and do not prove behavior in a current rendered browser.

| ID | Observation / hypothesis | Evidence | Epistemic state | Required verification |
| --- | --- | --- | --- | --- |
| DMN-01 | The homepage's *Fingerprinting Services* card describes mobile notarization / estate-planning documents rather than fingerprinting, despite later fingerprinting-specific bullets. | https://www.dcmobilenotary.com/ — services section, public HTML snapshot inspected 2026-11-23 | OBSERVED_IN_RETRIEVED_CONTENT | Reproduce at live URL; screenshot DOM and check production version before proposing fix |
| DMN-02 | The *Translation Services* and *Embassy Legalization* cards reuse a generic apostille pickup/delivery sentence rather than a distinct, service-specific introduction. | https://www.dcmobilenotary.com/ — services section | OBSERVED_IN_RETRIEVED_CONTENT | Verify in current mobile/desktop rendering; rewrite only against actual business facts |
| DMN-03 | An earlier exploratory audit reported a missing review widget, but the subsequent fetched homepage did **not** contain the error phrase. This is not an established current defect. | https://www.dcmobilenotary.com/ | CONFLICTING_SNAPSHOTS / UNVERIFIED | Test live embedded widgets in browser on supported viewport(s), inspect console/network errors and preserve timestamped screenshot |
| DMN-04 | The Spanish-language FAQ and service pages may contain untranslated English blocks. | Spanish site routes: discover and confirm exact URLs before filing a defect | UNVERIFIED_LEAD | Manually compare EN/ES page pairs, language switcher, canonical/hreflang and translated CTAs |
| DMN-05 | Payment/deposit language may conflict across pricing and individual services. | Pricing/Payments and Apostille pages: identify canonical URLs during audit | UNVERIFIED_LEAD | Capture exact passages and date, distinguish service-specific policies, request business clarification |
| DMN-06 | Service geography, FAQ answers, markup, internal linking and local-vs-nationwide intent may be improvable. | Homepage positioning: nationwide apostilles; DC/MD/VA mobile services | HYPOTHESIS | Crawl links, review structured data, map local entity and service intent, check real search results |
| DMN-07 | Google/AI recommendation and lead conversion opportunity may exist. | Not measured; no analytics access | UNMEASURED | Establish reproducible, neutral query set and conversion baseline before any impact claim |

**Important:** Do not treat earlier speculative observations as verified SEO, UX, Google ranking or AI visibility failures. A dated copy issue does not justify a total redesign.

## 3. Qualification plan — highest information gain first

1. **Site reality capture:** inspect production homepage, service pages, pricing, contact/quote funnel and ES routes in an actual browser. Capture timestamp, viewport, effective language, URLs, screenshots and console/network issues.
2. **Technical SEO baseline:** verify crawl/indexability, robots/sitemap, canonicals, hreflang, title/H1 intent mapping, duplicate service content, structured-data accuracy, internal linking, accessibility and real Lighthouse/Core Web Vitals results.
3. **Intent and local baseline:** map distinct intents for apostille, federal/FBI apostille, embassy legalization, translations and mobile notary across nationwide vs DC/MD/VA. Independently check Google local and organic coverage rather than assuming a ranking problem.
4. **AI visibility/GEO baseline:** test a fixed, documented set of neutral service queries across available engines; distinguish brand mention, citation, referral and actual business outcome; preserve dates, engines, locale and raw answers.
5. **CRO/measurement:** review the quote journey, speed to contact, service differentiation, mobile readability, form friction, trust evidence and pricing clarity. Request analytics or CRM access only with permission.
6. **Opportunity scoring:** assign severity, confidence, impact hypothesis, evidence link, effort, reversibility and proposed proof gate to each candidate fix. Prioritize low-risk, measurable fixes over full rebuild.
7. **Proposal:** offer a small, evidence-backed audit or demonstration with a clear validation plan; no unverified performance guarantees. Any outreach, access to nonpublic systems, changes or deployments require separate authorization.

## 4. Done gates — for *prospect qualification*, not implementation

- [ ] At least three distinct problems or opportunities are reproduced and linked to exact URLs, dated screenshots or repeatable measurements; otherwise mark **NO EVIDENCE / DO NOT PITCH AS DEFECT**.
- [ ] An evidence ledger separates VERIFIED, HYPOTHESIS, UNVERIFIED, NOT_REPRODUCED and RESOLVED; contradictory snapshots are reconciled.
- [ ] A 3-tier opportunity assessment distinguishes quick wins, testable experiments and non-priorities; proposed business impact remains hypothesis without instrumentation.
- [ ] A one-page commercial brief is suitable for the actual business, not a generic web-redesign pitch.
- [ ] No unauthorized contact, Google profile claim, website alteration, synthetic testimonials, sensitive document capture or client-status assertion.
- [ ] Any proposal to generalize a finding into CPP is routed to existing CDIO / SEO overlay / revenue-forensics / quality-gate owners. Do not create parallel prospecting runtime, score engine or knowledge base for one lead.

## 5. Reusable Claude Power Pack pattern

**Evidence-led prospect intake:** discovery -> live reproducibility -> confidence grading -> search/user-intent mapping -> business-impact *hypothesis* -> small reversible intervention -> measured outcome -> optional institutional pattern promotion. Use stable observation IDs and explicit revalidation dates so historical website issues cannot be sold after they have been fixed.

**Privacy/public-repo boundary:** this repository is public. Record only publicly observable website facts and non-sensitive methodological notes here. Keep private introductions, commercial terms, contact plans, private messages and relationship context outside this file and outside public GitHub history.

**Next action:** independent live-browser verification of DMN-01/DMN-02 and investigation of DMN-03/DMN-05; then decide whether the lead merits a tailored proposal.
