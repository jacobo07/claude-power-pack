# CDIO-VRK-001 — Chromatic Art Direction, Visual Hero Grammar & US Kitchen Website Configurator Reverse Engineering

**Date:** 2026-11-22 (Europe/Madrid). **Status:** BACKLOG OPEN / SOURCE ANALYSIS ONLY / NO CODE, LIVE IMPLEMENTATION OR TESTS EXECUTED.  
**Requested by Owner:** reverse engineer the techniques shown in two Instagram screenshots and seven accompanying MP4 uploads; institutionalize reusable CDIO visual and interactive patterns, especially for future US kitchen design, cabinetry and kitchen remodeling businesses.  
**Priority:** P0 truthful source interpretation and existing-owner reconciliation; P1 reusable chromatic/art-direction patterns; P1 commercial kitchen configurator vertical slice; P2 benchmark, adaptive routing and cross-sector promotion.  
**Canonical owners:** CDIO for art direction, visual quality and applicability; existing CCF for brand identity and licensed assets; DESIGN.md for project design authority; CDICF for component/media/dependency intake; current frontend/runtime for interactive implementation; existing QA and UKDL/Knowledge Vault for proofs and ratchet. Do NOT create another design OS or copy the demonstrated websites.
**Parent initiatives:** [CPP-CGVI-001 — Context-Grounded Visual Intelligence](2026-11-22_cdio-context-grounded-visual-intelligence-authentic-art-direction.md); [CDIO-06 aesthetic families](../knowledge_base/cdio/CDIO-06-aesthetic-families.md); [CDIO-07 experience contract](../knowledge_base/cdio/CDIO-07-experience-contract.md); [BI brand identity](2026-10-21_cdio-brand-identity-logo-absorption.md); [21-resource design intake](2026-10-30_cdio-21-design-resources-universal-absorption.md). Extend these; no duplicated ownership.

## 1. Uploaded evidence manifest — only observations, no unlicensed media check-in

Media was inspected locally in this 2026-11-22 conversation. Filenames, bytes and SHA-256 refer to user-provided captures and videos. **Do not upload/rehost their raw bytes, screenshots, frames, identifiable people, audio or original third-party designs to the public CPP repository.** These are references for technique extraction, not licensed assets. Evidence hashes let the Owner reattach and verify the originals privately.

| ID | Uploaded filename | SHA-256 | Observation coverage |
| --- | --- | --- | --- |
| VRK-S01 | Screenshot_20261122_231511_Instagram.jpg | 3a2bc436e2635356d494495217055a61d7f6b44a0e367528854712033c938c86 | Reel UI: Deep Teal / Bone / Magenta swatches with dramatic flamenco dance event hero |
| VRK-S02 | Screenshot_20261122_231507_Instagram.jpg | 408f16c3aa6f6df3929cf00cdc31aa1c0348e95579232986cbfdc7ac2148416e | Reel UI: Lake Blue / Navy / Sun Yellow swatches with large sail/photo/type sailing-course hero |
| VRK-V01 | charles.unemployed_2b9ce52303e249a6b09fa43e91df7ec9.mp4 | 21c7d7590ff3be5d671c023e8b0fe9c56bc9ac485f0fa69c85161d2b5dee3908 | Approximately 20.4 seconds; sequence of 3-role palette proposals, graphic mockups and a spoken-caption 60/30/10 rule |
| VRK-V02 | alfiewoelfe_e41629a8746a4c298aa506b9a17286ba.mp4 | 90018d448ce8c0bfbdbabd05f65cbcc56bb2dbb7bc038af81b51188e19888ff3 | **One decodable frame only**: partial headline about a brand comparison, portrait and Google identity; no timing/motion inference possible |
| VRK-V03 | alfiewoelfe_f597e1d6e5f14bd5b95a23bb3de073b1.mp4 | a213607f49eecd15ed178f960d8022d07d1f44579892d9ea10303b2814aac999 | **One decodable frame only**: typography '3 colour rule', three swatches (dark, white, warm accent) and dramatic digital hero |
| VRK-V04 | alfiewoelfe_ce4c210976f740fab86c50b5e2f8b053.mp4 | f07c90d6e3376b9314a8f362369738b246576e8a5d7fc1bfdf360fcf30cd6190 | **One decodable frame only**: typography 'Feel trusted', headline/button/proof labels, insurance example with people photograph |
| VRK-V05 | alfiewoelfe_debc586fde574a6f8d040b431f7ec8ed.mp4 | 9fd7e4446d466a6c62ce5e406193aee202692300c6d99950c6a7428e1eff6bf9 | **One decodable frame only**: alternative '3 colour rule' with plum-black, white and orange/warm accent, cinematic visual hero |
| VRK-V06 | mattxwebb_a2bd9980acc84c6d97a6b1175b1cc157.mp4 | 33c70a403a5fc8a1a35014cc313b161b9f229e7084b14a0e676e8e5da54713f5 | Approximately 25.1 seconds; photographed laptop presenting a kitchen design configurator with mutable finishes/options and displayed indicative total |
| VRK-V07 | mattxwebb_f79893aeb5ea4ee298dae9bfa8f573de.mp4 | 9648bda3a44d9ddc6cde2818d61c0879ff2689279ff376daac900e0b7e230195 | Approximately 24.0 seconds; kitchen, roofing and solar/energy hero concepts paired with sector-specific three-swatch palettes |

**Media constraints:** the four alfiewoelfe files are actual MP4 containers but each yielded only one decodable frame through local inspection. Do not claim they contain full video motion, a continuous demonstration, or corroboration of their source assertions. The other three clips provide visible time-sequence evidence; no independent transcript of all spoken words or source-code/backend evidence was inspected. Screenshot Instagram UI overlays, reel accounts and view/like counts are irrelevant to the design technique and do not substantiate business outcomes.

## 2. Observed visual techniques: reverse engineer the grammar, not the original work

### VRK-P01 — Intentional base/text/accent color roles

Charles demonstrates a sequence: neutral or muted pair alone versus the same palette gaining a high-contrast accent; examples include Cream Paper + Riso Teal + Fluorescent Pink, Raw Clay + Iron Brown and Petrol Blue + Ivory + Saffron Gold. The owner-supplied screenshots show Deep Teal/Bone/Magenta for a flamenco-themed hero and Lake Blue/Navy/Sun Yellow for a sailing-oriented composition. The video displays a **60% background / 30% secondary / 10% accent** heuristic late in the clip; preserve it as an illustrative starting hypothesis, **not** a numerical universal rule or a pixel-measured fact about every shown design.

Reverse-engineering focus: semantic palette roles; distribution by salience rather than just area; neutral temperature; chroma contrast; visual hierarchy; CTA isolation; accent integration with the subject; contrast/readability; color-blindness, dark/light and print contexts; brand-preservation exception. The objective is not to force three visible colors, neon accents or a default palette on every project.

### VRK-P02 — Subject-driven, art-directed hero

The flamenco and sailing mockups show bold display typography combined with a dominant photograph and a strong colored subject. The words, photograph, negative space, color contrast and focal direction together create identity. The original captures are small reel overlays, not complete responsive website implementations. The implied overlap/masking, font/subject hierarchy and crop mechanics remain **engineering hypotheses until reproduced in an original controlled fixture**. Extract layout relationships and visual treatments, never copy photos, trademarks, headline lettering or original page composition 1:1.

### VRK-P03 — Industry-adaptive visual territory, not global formula

The mattxwebb palette reel pairs different styles with kitchens, roofing and a dark energy-oriented product UI. The kitchen example uses espresso/oat/sage green earthy neutrals and an interior product photo; roofing uses a cool slate/white pairing; energy uses jet-black/silver/electric-yellow emphasis. These are examples of context-responsive choices, not evidence that a sector has one obligatory palette. Source code and original production sites are not provided; treat the visuals as examples, not finished customer implementations.

### VRK-P04 — Real photographic/product proof and trust

The single-frame 'Feel trusted' reference contrasts clear headline, singular action and a proof block alongside a people photograph. For kitchens, replace generic claims with verified installed-project photography, real material samples, genuine reviews/permissions and clear contact/appointment actions. A pretty screenshot is not proof of a real testimonial, guarantee, accreditation, installation or operating company.

## 3. Kitchen configurator: what the uploaded video does and does not prove

In VRK-V06, a large kitchen photo/render occupies the left of a desktop layout, with an option form on the right. Observed options include cabinet color swatches, worktop finish cards, design/offer packages and fitting dates; on-screen photos and displayed price figures change while the presenter interacts. The visible demo has British pound amounts. Some visible phrasing suggests a kitchen design-and-booking workflow. **Not observed:** underlying state model, price calculation, inventory/SKUs, real 3D geometry, server calls, actual quote accuracy, CRM integration, persistence, checkout or production readiness.

### Reusable US kitchen-business pattern — Visual Configuration → Qualified Lead

- **Audience and subtype discovery:** distinguish bespoke cabinetmakers, full kitchen-remodeling contractors, kitchen design studios/showrooms, countertop specialists, cabinet refacing, appliance suppliers and commercial kitchen fabricators. Do not impose a high-cost configurator when a project portfolio + simple consultation form is the better sale.
- **Real offerings and available options:** only offer actual cabinet doors, finishes, hardware, worktops, layouts and services supported by the client; combinations need compatibility and availability data. Owner-authorized source photography or controlled original renders, not another business's images.
- **Visualization:** product-state synchronization across swatches/options and preview. Choose static photo-composite, layered 2D, pre-rendered variants or optional 3D according to project evidence, fidelity and ROI. Do not assert that the reference uses 3D.
- **Money and geography:** US-dollar display where appropriate, feet/inches if necessary, ZIP/service-area eligibility, US-style dates, sales tax/disposal/installation/permit disclaimers according to verified business policy. UK £ figures from the reference must never be imported as US pricing.
- **Indicative estimate:** client-approved price model and assumptions, server-side rules where financially material, range and inclusions/exclusions, no authoritative fixed quote without valid source data. Missing prices or incompatible options must stop/label estimation rather than show fictional totals.
- **Conversion journey:** save or share configuration when supported, request appointment or quote, persist a reliable normalized selection snapshot and consent, deliver the captured configuration to a real lead/CRM consumer. No empty CTA, inert submit, fake booking, silent 401 or disconnected frontend/CLI.
- **UX/accessibility:** labeled color names beyond swatches, keyboard/touch interaction, visible selection, undo/recovery, mobile stacked preview + controls, focus management, reduced motion, accessible pricing updates, valid form state and safe persistence.
- **Commercial proof:** measure completed configurations, qualified-lead rate, submitted design briefs, appointment requests and actual quotation conversion when analytics/consent permit. Never infer uplift from a reel.

### Deliverable archetypes (select contextually)

A. Premium kitchen design/remodel landing + real project portfolio + financing/consultation path (no configurator unless justified).  
B. Cabinet finish explorer with verified options and illustrative before/after comparison.  
C. Kitchen design configurator with validated material combinations and indicative range/lead handoff.  
D. Customer project/design portal when there is an actual operational backend and privacy contract.

Use the smallest useful archetype; *not every kitchen company needs all four*.

## 4. Integration with autonomous CDIO baseline

**Selection, not command dependency:** user asks "build a website for a US kitchen company"; existing CPP intent routing should identify hospitality vs residential renovation, target locality, product taxonomy, verified differentiators and assets; CDIO selects appropriate color/composition/photo grammar, CCF assets where needed, design-md tokens and component/visualization path, then the frontend runtime builds it, browser QA inspects it, CDIO critiques and repair loops run within budget. No requirement for the Owner to invoke design commands by name.

**Existing canonical authority:** CDIO-06 aesthetic choice; CCF Visual DNA/approved brand; CDICF licensed dependencies; DESIGN.md project identity; CGVI-A00..A13 autonomous activation, resource selection and render-review; CGVI-26..31 evaluation and ratchet; existing QA/Production Reality Gate. This backlog owns the **new specific source-derived pattern and the industry-qualified kitchen interaction contract**, not duplicate registries/gates.

**Implementation authorization boundary:** backlog capture does not authorize client asset scraping, new paid image/video models, installation of external apps, deployment, publishing third-party photos/brand assets, or promising real-price estimates.

## 5. Ordered actionable backlog — P0 ownership and P1/P2 functional proof

- [ ] **VRK-00 — Fresh reality + overlap audit:** reconcile current repo main, CGVI, CCF, CDICF, DESIGN.md, CDIO-06/07, video/motion corpus and any existing kitchen estimator/configurator engine before writing new code.
- [ ] **VRK-01 — Source-anchored visual observations:** preserve this 9-file hashed manifest, index exact timecoded observations for the 3 full clips, separate four one-frame clips and mark hypotheses/unknowns.
- [ ] **VRK-02 — Visual mechanism ontology:** define base/text/accent roles, tonal hierarchy, chroma contrast, subject/accent coupling, typographic/photo layering, visual focal priority, sector fit and mobile crop as source-grounded pattern candidates with applicability limits.
- [ ] **VRK-03 — Color grammar falsification:** experimentally test 2-, 3-, 4+ role palettes; 60/30/10 vs other distributions, brand-safe variants, AA contrast and brightness/print variants. Never freeze the reel heuristic as a constitutional law.
- [ ] **VRK-04 — Reproducible original visual test scenes:** recreate only the *techniques* using original/cleared kitchen photos or authored geometric fixtures; never rehost or copy reel mockups or originals.
- [ ] **VRK-05 — Responsive typographic/photo art direction:** validate subject, type scale, masking, overlay, focus, hero crop, CTA visibility and readability on desktop/tablet/mobile without relying on reel framing.
- [ ] **VRK-06 — Palette-to-material coherence:** choose brand palette separately from cabinetry/worktop/product finish palette; materials affect configurable product, not arbitrarily the entire site chrome.
- [ ] **VRK-07 — Market/ICP segmentation:** distinguish kitchen company archetypes and when an immersive design preview improves qualification rather than merely adding friction.
- [ ] **VRK-08 — US-market proof requirements:** derive company-provided service area, accepted ZIPs, units, available finishes, pricing source, exclusions, quote/legal wording, available appointments, client approvals and image rights. Record UNKNOWN rather than invent facts.
- [ ] **VRK-09 — Configuration state and compatibility:** derive from actual product catalog; deterministic cross-option behavior; same selection displayed, estimated and submitted; invalid combinations rejected or explained.
- [ ] **VRK-10 — Visual preview implementation comparison:** benchmark authorized pre-rendered variants, compositing and optional 3D against fidelity, asset size, performance, mobile and maintenance cost. Default to the simplest technique meeting the requirement.
- [ ] **VRK-11 — Pricing/estimate contract:** client-grounded calculator with US-dollar formatting and transparent range/assumptions; explain taxes, labor, dimensions, region/installation only when verified; no invented quotes.
- [ ] **VRK-12 — Lead/appointment integration:** a real consumer of the selected configuration, consent, error recovery, verified delivery and analytics boundaries. No decorative CTA/pretend backend.
- [ ] **VRK-13 — Original design alternatives:** at least two meaningfully distinct kitchen brand treatments for the same verified brief, e.g. earthy craftsmanship vs architectural premium, retaining approved brand DNA and avoiding generic cream/terracotta by inertia.
- [ ] **VRK-14 — Device and accessibility proof:** actual viewport screenshot, contrast, swatches readable without color discrimination, touch targets, keyboard, reduced motion, state preservation, pricing announcements and form usability.
- [ ] **VRK-15 — Financial and production QA:** validate price/state persistence against tampering and stale data, currency and service-area rules, error/empty states, loading UX, performance and security within the true deployment environment.
- [ ] **VRK-16 — Automatic CDIO applicability:** when user requests web for US kitchen/cabinetmaker/remodeler, consider pattern without command; select/reference only if business evidence and ROI support it; never force on all sites or sectors.
- [ ] **VRK-17 — Source and license intake:** rights for fonts, visual examples, sample media, models, diagram generators and any external component/tool; no automatic copying of third-party creator work.
- [ ] **VRK-18 — US kitchen benchmark:** original test fixture + one authorized real company pilot if available; compare static brochure vs simple finish selector vs full configurator on qualified UX, lead task completion, accessibility, performance and build/operating cost.
- [ ] **VRK-19 — CDIO rendered-review and repair:** actual browser/render screenshots and interaction recording; independent reviewer flags visual blandness, focal errors, UI fake elements, unsupported imagery, state/price mismatch; builder corrects and reruns.
- [ ] **VRK-20 — Universal Knowledge Distillation and Constitutive Baseline Ratchet:** promote only verified and applicable art-direction/color/interaction principles through existing visual-patterns KB, UKDL Hard Rules/Process Rules/Traps, benchmark and real future-project consumers; counterexamples prevent visual homogenization.
- [ ] **VRK-21 — Source-coverage ledger and retirement:** every observed pattern/source gets owner, status (REFERENCE, IMPLEMENTED, REJECTED, UNKNOWN), test, rights, applicable business type, proof and change/retirement conditions; 9/9 source files inventoried != "reverse engineering complete".

## 6. Adversarial acceptance matrix (not executed)

| Test | Injected error | Required result |
| --- | --- | --- |
| V-VRK-01 | Three exact colors enforced on every brand | Context selector refuses universal rule |
| V-VRK-02 | 60/30/10 ratio treated as measured fact | Reviewer marks heuristic not verified proportion |
| V-VRK-03 | Fluorescent accent hides CTA or text | Contrast/focal review fails |
| V-VRK-04 | Dramatic photo/type overlap clips on mobile | Responsive/real rendered check fails |
| V-VRK-05 | Reference Instagram image shipped on client site | Rights gate blocks |
| V-VRK-06 | Imaginary kitchen presented as an installed client project | Authenticity block |
| V-VRK-07 | Decorative color chips do not change preview | Functional interaction fails |
| V-VRK-08 | Preview changes but quote/lead uses stale selection | State/evidence parity fails |
| V-VRK-09 | Unsupported finish combination remains selectable | Product compatibility constraint fails |
| V-VRK-10 | Fake fixed quote derived from visual swatch alone | Money/truth gate refuses |
| V-VRK-11 | Demo £ prices copied to US-facing $ quote | Locale/currency gate fails |
| V-VRK-12 | Client unavailable in entered ZIP | Eligibility explains outcome; no false booking |
| V-VRK-13 | Price updates cannot be perceived by screen reader | A11y fails |
| V-VRK-14 | Color-only selection excludes color-blind users | Accessible naming/selection fails |
| V-VRK-15 | Lead CTA submits but backend returns silent 401 | Production Reality fails, recovery required |
| V-VRK-16 | Quote creates record with wrong selected materials | Consumer parity fails |
| V-VRK-17 | 3D/WebGL added when a lightweight static proof suffices | Cost/perf comparison selects simpler lane |
| V-VRK-18 | Finished-looking design without actual real product catalog | Concept clearly labeled; no production claim |
| V-VRK-19 | Kitchen configurator forced onto every renovation site | ROI/applicability declines where not useful |
| V-VRK-20 | Visual variant improves beauty but worsens lead usability | Contextual QA rejects regression |
| V-VRK-21 | Four one-frame MP4s represented as complete reels with timing | Evidence integrity rejects |
| V-VRK-22 | Source file hashes listed but no actual visual technique consumer exists | Ratchet remains BACKLOG / NOT_DONE |
| V-VRK-23 | Auto CDIO activation requires the user to type a design command | Autonomy acceptance fails |
| V-VRK-24 | Screenshot-only prototype claims production-ready configurator | Backend/price/lead Production Reality gate fails |

## 7. Release sequence and completion

**P0:** source-truth and existing-owner audit; accessible/responsive color/hero grammar experiment; one original kitchen brief and licensed fixture.  
**P1:** working kitchen visualization control with real catalog-grounded state, safe indicative estimate or no quote, real lead flow in permitted test environment, independently rendered visual review and repair.  
**P2:** cross-sector benchmark (kitchen vs non-kitchen and low vs high visual intensity), performance/cost verification and automatic invocation.  
**P3:** UKDL, Knowledge Vault, visual-patterns and relevant existing design-selector/done-gate promotion, if—and only if—transfer proof supports it.

**Backlog-capture DONE:** this document exists, is linked by CPP-CGVI-001, contains 9/9 source identities, findings and evidence limitations, US kitchen archetypes, actual engineering jobs, negative tests and ownership.  
**Engineering DONE (NOT CLAIMED):** original legally cleared demo; real functioning preview/option/estimate/lead path (or honest exclusion where unavailable); real browser and Production Reality receipts; red/green tests; independent visual critique, mobile/a11y, output provenance; autonomous CDIO selection and demonstrable future-project baseline inheritance.  
**Never claim:** source code recovered from the reels, replicated commercial websites, original images licensed, verified US market prices, actual customer conversion lift, full four alfiewoelfe videos inspected, or production software shipped from this backlog entry.
