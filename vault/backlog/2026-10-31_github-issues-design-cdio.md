# GitHub issues -- design / CDIO backlog (2026-10-31)

Source: `gh issue view` on 2026-10-31 (the GitHub MCP returned 401 this session; `gh` was authenticated). Bodies are copied verbatim; their headings are demoted three levels so they nest under each issue. GitHub stays the source of truth: re-read the issue before acting.

CDIO is named in TUA-X #4 (owner of the visual 10/10 standard, render QA, >=3 distinct PDP presentations), #6 (canonical visual system), #8 (reuse CDIO, no second brand engine) and #10 (no new CDIO/theme engine; #4 owns visual). #5, #7 and #9 touch UX without naming CDIO. claude-power-pack #5 is the repo's only issue and is not a design item.

## Index

- [ ] TUA-X#4 [OPEN] 2026-10-25 -- SGE — Standard visual 10/10: experience intent, visual merchandising/PLP y render QA (https://github.com/jacobo07/TUA-X/issues/4)
- [ ] TUA-X#5 [OPEN] 2026-10-25 -- SGE — Preference-Based Offer Architecture: elección auténtica, valor y pricing transparente (https://github.com/jacobo07/TUA-X/issues/5)
- [ ] TUA-X#6 [OPEN] 2026-10-25 -- SGE 10/10 — Popup Experience Intelligence: captación, gamificación verificable y Quality Gate real (https://github.com/jacobo07/TUA-X/issues/6)
- [ ] TUA-X#7 [OPEN] 2026-10-26 -- SGE — Subscription Commerce & Retention Intelligence: 6 prácticas, selling plans reales y lifecycle verificado (https://github.com/jacobo07/TUA-X/issues/7)
- [ ] TUA-X#8 [OPEN] 2026-10-26 -- SGE — Identity-Led Positioning & Transformation Intelligence (Georgie Lewis) (https://github.com/jacobo07/TUA-X/issues/8)
- [ ] TUA-X#9 [OPEN] 2026-10-26 -- SGE — Store Credit Rewards & Repeat-Purchase Intelligence (Ty Chapman) (https://github.com/jacobo07/TUA-X/issues/9)
- [ ] TUA-X#10 [OPEN] 2026-10-27 -- SGE — Commerce Site Architecture Intelligence: catálogo condicional de 20 experiencias (Maxtymosh) (https://github.com/jacobo07/TUA-X/issues/10)
- [ ] claude-power-pack#5 [OPEN] 2026-10-10 -- Epic: Global Goal Fabric & Actorless Zero-Resident Autonomy (https://github.com/jacobo07/claude-power-pack/issues/5)

## TUA-X#4 -- SGE — Standard visual 10/10: experience intent, visual merchandising/PLP y render QA

State OPEN, created 2026-10-25, https://github.com/jacobo07/TUA-X/issues/4

##### Objetivo y referencia

Elevar **SGE (Site Generation Engine)** desde generación correcta de copy/secciones hasta una **experiencia comercial premium, editorial, interactiva y verificable en navegador**. Referencia de mecanismos (NO de identidad visual): el ejemplo **10/10 de Aritzia** mostrado en el vídeo aportado por el usuario de Shovel Studio, especialmente ~00:42–01:03: navegación visual por subcategorías, filtros contextualizados, PLP con imágenes consistentes, vistas/vídeo de producto, densidad y ritmo editorial.

**«10/10» es el estándar aspiracional de experiencia, no un score validado ni una promesa de conversión.** El vídeo inserta una afirmación «−50% abandonment»: **NO usar como verdad/resultado esperado sin fuente y experimentos propios.**

##### Evidencia técnica del repositorio (main revisado 2026-10-25)

- `tuax_core/engines/sge/quality_gate.py`: `QUALITY_FLOOR=70`; dimensión `taste` verifica estructura/copy, **no la apariencia real renderizada**. `_content_context()` declara `has_images=False` («no image pipeline»).
- `tuax_core/engines/sge/models.py`: `StoreGenerationResult` tiene `homepage_sections` y `pdp_sections`, pero no `collection_sections` ni manifiesto visual/render evidence.
- `tuax_core/engines/sge/sections.py`: `render_os2_templates` solo emite `templates/index.json` y `templates/product.json`; PDP prevé imágenes pendientes. El orden de secciones de conversión tiene invariantes que deben preservarse.
- `tuax_core/theme/cw-shrine/README.md`: CW Shrine es **overlay sobre Dawn**, con `templates/index.json`, `product.json` y secciones de home/PDP, sin compilador específico de PLP; conservar despliegue no destructivo en un tema unpublished.
- `tuax_core/engines/sge/store_quality.py`: evalúa alineación estructural con patrones del vault y mantiene referencia visual **informativa**, no obliga a copiar.
- `AGENTS.md`: **Code Freeze/Post-Code Sarcophagus**; ideas nuevas van en issues. No codificar ni abrir PR de features sin requisitos de telemetría, gobernanza y gates aplicables.

##### Ley arquitectónica

SGE **compone**; Chief Design Intelligence valida; CW Shrine **renderiza**; Product/Offer/Economic Truth y Asset Registry suministran hechos; Creative OS suministra activos autorizados; el sistema de medición produce evidencia. **SGE ≠ WRRE**: transferir *mecanismos de diseño*, no replicar marca, imágenes, copy, assets ni composición protegida de Aritzia. Evitar motores/scorers paralelos o reconstrucciones de módulos existentes; buscar en el repo el productor canónico y conectar mediante contratos compatibles.

##### Alcance propuesto (auditar reutilización antes de implementar)

1. **Experience Intent / Design Contract:** ampliar el contrato existente de `design_intent` (sin crear SoT duplicado) con objetivos por tipo de catálogo, posicionamiento, personalidad de marca, profundidad de descubrimiento, densidad visual, composición, guía fotográfica, motion policy, requisitos de pruebas/variantes y evidencia de origen. Categorías y colecciones solo cuando tienen sentido comercial.
2. **Visual Merchandising / PLP:** hacer primera clase la página de colecciones en CW Shrine (Dawn OS 2.0): navegación visual por familias *si catálogo y assets lo justifican*; breadcrumbs, filtros reales (no botones falsos), sort, tamaños/variantes/precio/stock, rejilla responsiva, badges basados en datos y comportamiento de imágenes/vídeo condicionado a recursos disponibles. Mantener descubrimiento y merchandising coherentes con SKU, atributos y disponibilidad. **Single-product stores NO reciben categorías artificiales**: aplicar lenguaje editorial y merchandising a home/PDP.
3. **Product Media Contract:** reutilizar los registries de Product Truth y activos existentes; manifiesto por SKU/variante: foto principal, alternate, detalle, vídeo opcional, derechos/licencia, estado, aspect ratio, procedencia y cobertura. No marcar como completa una experiencia con fotos pendientes, assets ficticios o incoherentes. Sin vídeo válido → fallback estático funcional. Sin producto real → preview honesto, no publish-ready.
4. **Premium composition & interactions:** gramática adaptable al nicho (tipografía, grid, espacios, escala editorial, consistencia fotográfica, tamaños táctiles, estados hover/touch/focus, loading, empty/filter-zero, reduced-motion); componentes Shopify editables y reutilizables, no hardcode de Aritzia. Evitar sobrecargar diseño o aumentar fricción para exhibir efectos.
5. **Chief Design × Browser-render QA:** conservar el `store_score` actual para contenido/completitud y añadir **evidencia de experiencia renderizada**, con clasificación independiente y verificable: `NOT_RENDERED`, `RENDERED_UNVERIFIED`, `VISUALLY_COMPLETE`, `COMMERCIALLY_COHERENT`, `PUBLISH_READY` (nombres definitivos tras auditar enums actuales). Capturas reales 390/768/1440 (o tamaños ya canónicos), DOM/interacción, accesibilidad, errores y honestidad de claims; iteración acotada a causa raíz y prueba de regresión. Nunca elevar `taste` por cumplimiento estructural y llamarlo validación visual.
6. **Truth/safety/performance:** suprimir/reformular claims de `Trusted by customers`, dinero garantizado, envío rápido o badges donde falten evidencias. No urgencia falsa ni comparativas no contrastadas. Revisar WCAG AA, teclado, foco, mobile/touch, LCP/CLS/INP con métricas reales, carga diferida y formatos eficientes. Shopify Theme Check y theme render real, no solo JSON estático.
7. **Learning loop:** instrumentar impresiones de colección, CTR de categorías, aplicación de filtros, product-list clicks, PDP views, ATC, checkout, purchase, conversion/contribution margin. Definir hipótesis y comparación controlada; atribución sin afirmar causalidad por intuición.

##### Gates de aceptación (must pass)

- [ ] `SGE` conserva los contratos existentes y los tests de SGE, CW Shrine y onboarding; sin duplicar modelos/gates de verdad.
- [ ] En catálogo multíproducto real: home + PLP + PDP visualmente compuestos, con subcategorías útiles, filtros funcionales y medios con procedencia. En single-SKU: sin carruseles/categorías inútiles.
- [ ] Shopify genera/renderiza `collection` (cuando aplique) dentro de **CW Shrine overlay** y respeta la base Dawn, incluyendo preview draft/unpublished.
- [ ] Capturas visuales reproducibles de desktop/mobile + evidencia funcional de navegación, filtros, variantes, media y ATC; sin paneles vacíos ni recortes graves.
- [ ] Todos los hard blockers de visual/media/accessibility/claim-truth se aplican a `PUBLISH_READY`; previsualización puede mantenerse con estado explícito de incompleto.
- [ ] Hero/PLP/PDP mantienen jerarquía reconocible, tipografía coherente, sistema de espaciado y fotografía homogénea **según la marca**.
- [ ] Media opcional ausente degrada de forma elegante; media obligatoria ausente impide sello de «visualmente completo».
- [ ] No contiene el nombre/logos/fotografías/copy de Aritzia, ni «−50% abandono» como claim de SGE.
- [ ] Pruebas unitarias del compiler/contract, snapshots de theme, integración Shopify, E2E de navegador, regresión por nicho, movimiento reducido, accesibilidad y performance; informes con pruebas y límites explícitos.
- [ ] Evidencia de publicación en tema no productivo antes de cambiar rol live; ningún side effect irreversible sin gate.
- [ ] Cambios persistidos mediante registry/evidence/lessons/experiments donde el repo tenga autoridad, no documentación aislada.

##### Orden de trabajo

**M0 — Discovery/read-only:** mapear SGE, Shopify adapter, CW Shrine, Chief Design, Product Truth, Asset Registry, Creative OS, experimentación, gobernanza, tests y el backlog. Medir el baseline actual con dos casos (single SKU y catálogo multíproducto). Identificar interfaces canónicas y coste marginal. No implementar sin aprobación de los gates del repo.

**M1 — Contract + media truth:** habilitar intent de experiencia, modelos/coverage y bloqueo de publicación incompleta con diffs mínimos.

**M2 — PLP compiler + Shrine primitives:** navegación visual condicionada, colección realmente Shopify, filtros y media funcional.

**M3 — Real-render evaluator + bounded repair:** capturas, fallos accionables, regresión y evidencia de readiness diferenciada del scorer textual.

**M4 — Controlled experiments & compounding:** métricas reales y aprendizaje reusable de qué mecanismos aumentan comprensión, conversión y beneficio, sin atribuirlas al vídeo.

##### Restricciones

- No tocar el runtime/live theme ni rediseñar CW Shrine desde cero.
- No cambiar políticas de marketing/garantía sin fuente.
- No inventar objetivos de uplift; la prioridad es diseñar la instrumentación.
- Respetar el **feature code freeze** de `AGENTS.md`: este issue es propuesta/lista de aceptación; cualquier implementación requiere evidencia y el proceso autorizado.
- La grabación aportada por el usuario está **en el chat**, no almacenada como archivo en este repo. Esta especificación describe las mecánicas observadas, no pretende adjuntar el vídeo al issue.

**Definición de éxito:** SGE deja de confundir `STRUCTURALLY_VALID` con `VISUALLY_COMPLETE` y produce tiendas visualmente distintivas, funcionales, verificables y comercialmente coherentes — no solo tiendas con buen texto.

---

##### Addendum — PDP Second-Version 10/10 (Molly Loves Ecom, 2026-10-26)

###### Source evidence and interpretation

Owner-provided video: `mollylovesecom_a32668f2efe044d29bc237f603e139ea.mp4` (12.05 s), SHA-256 `d3dd04e5972543821b43ea76b39e0387db9c90d27d6e2ac1ea8260d5dd06fe08`. The file is supplied in the conversation, **not** checked into this repository.

The Owner explicitly selects the **second, enhanced variant** in the video's before/after demonstrations as the design reference, **not** necessarily the second brand or a fixed page to copy:

- ~00:00–00:02: bare single-product headphone PDP → richer headphone configurator: visual style choices, color swatches, material choices, prominent media and purchase action.
- ~00:02–00:05: basic one-time purchase card → tiered offer selection panel: multi-day supply, highlighted offer, per-day price, verified included kit/benefit, alternative purchase paths.
- ~00:05–00:07: simplified drink-mix PDP → more complete product choice interface: flavor, 1/2/3-pack selections, one-time vs subscription, price context, clearer image/detail structure.
- ~00:07–00:09: wellness product PDP with persistent bottom buy CTA and the more comprehensive purchasing panel.

**These frames establish a design pattern only.** They do not prove that the second option converts better, has better contribution margin, is legally compliant, or that the displayed price/discount/gift is true. No cloning of others' photos, brand marks, wording, product imagery or proprietary page assets.

###### Architectural decision: PDP Decision Architecture, not a new store builder

Make the **enhanced, choice-capable PDP** an SGE *experience archetype*, composed by existing owners:

- **SGE** decides the appropriate degree of purchase-panel complexity from real SKU/variant/offer/customer intent; may choose a simpler PDP where it is demonstrably more usable.
- **Existing StoreSection / CW Shrine** render the purchase interface; retain `Atención → Deseo → Justificación → Confianza → Urgencia → Captura` invariant unless governance explicitly approves a change. Enhance within/alongside the current layers, not replace them with a competing theme.
- **Product Truth / Shopify variants** are authoritative for variant IDs, color/media, stock and price. No invented variants or inaccessible combinations.
- **Offer Builder / Pricing** are authoritative for economics, but *offer recommendations are not automatically purchasable Shopify variants, bundles or subscriptions*. Show only inventory/terms that actually exist and can be purchased. Cross-reference #5 for real choice and pricing transparency.
- **CDIO and render-QA** validate actual rendered states, not screenshot-only or generated section count. Cross-reference #4 core gates and #6 to avoid popup competing with this purchase UI.

###### Existing code to reuse / inspect (as observed 2026-10-26)

- `tuax_core/theme/cw-shrine/sections/shrine-captura.liquid` already includes variant controls, quantity stepper and Add-to-Cart.
- `tuax_core/theme/cw-shrine/snippets/sticky-atc.liquid` and `assets/cw-shrine.js` already include a sticky purchase affordance; **do not create a second one**.
- `tuax_core/engines/sge/sections.py` already emits offer, guarantee, comparisons, trust and FAQ sections.
- Gaps for verification: screenshots do not establish an SGE-generated *buyable* pack/subscription; current `OfferStructure` can contain calculated recommendations without Shopify inventory. Existing sticky price appears seeded from the first Liquid variant, while variant JS updates the main price; test synchronization rather than asserting it works. Verify sold-out variant disabling and media/price/checkout alignment with actual browser interaction. A static Liquid swatch color based on a color name may not match product photography; prefer real variant-linked media/valid swatch data.

###### Desired behavior (conditional, product-truth-first)

1. **Rich variant configurator:** descriptive option names, visual swatches/thumbnails when data exists, compatible option combinations, immediate linked images/price/stock/selected SKU and Add-to-Cart updates. Keyboard/touch/screen-reader parity.
2. **Truthful price-choice panel:** coherent one-time purchase, multiple real quantities/packs and optionally authentic subscription plans. Show total price, unit price, correct duration/per-day basis (only when verifiable), billing interval, renewal/cancellation terms and actual discount. No dark-pattern defaults or forced subscriptions.
3. **Offer differentiation:** optional «best value» or «most popular» ONLY with declared objective basis and evidence: computed lowest real unit cost for «best value», measured popularity for «most popular». Free kits, bonuses, guarantees, discounts and limited stock require inventory/eligibility/terms; never just a line of copy.
4. **Concentrated decision surface:** product media, product title, key evidence-based benefits, variant/offer selectors, availability, pricing, shipping/tax information and primary CTA arranged to reduce decision friction, not merely add widgets. Editability in Shopify theme remains intact.
5. **Synchronized persistent CTA:** sticky bar mirrors selected variant/offer, real price, availability and purchase action at all times; mobile-safe, non-obstructive, not duplicated unnecessarily, and disabled correctly for out-of-stock options. Never add a different SKU than the selected offer.
6. **Progressive disclosure:** advanced options only where relevant. Small catalogs and single-SKU products without real alternatives retain elegant simple buy boxes; no fabricated multipacks/subscriptions or preference questions.
7. **Real economics:** optimize conversion *and* contribution profit per eligible session, subscription churn/refunds, AOV, discount/bonus costs and return/cancellation, not visual richness or badges alone.
8. **Claims safety:** supplements/health claims and outcomes require specific evidence; no promise of faster results based on a higher price or pack size.

###### Production Reality acceptance gates

- [ ] Read-only discovery first: find canonical pricing/product/variants/bundles/subscriptions owners and Shopify/consent dependencies, commit history and current governance before planning changes. No duplicate engine.
- [ ] Demonstrate a real multivariant product and a genuine multi-offer/pack product; where subscription unavailable, show verified fallback and **no fake subscription**.
- [ ] Change variant → actual selected SKU, hero/media, price, availability, cart line and sticky CTA stay synchronized across desktop/mobile; deep link/back/reload preserve intended state when supported.
- [ ] Invalid or sold-out variants cannot be added; fallback and errors are understandable, accessible and do not leave contradictory prices.
- [ ] Plan, bundle, gifts and subscription options map to real purchasable objects and real checkout charges, not just templates or prose. No false «best value», comparisons or automatic inflated anchors.
- [ ] Sticky CTA, primary CTA and express checkout use the same chosen item/plan; no dead buttons, duplicate orders or unexpected 401/connection breaks.
- [ ] Keyboard/touch, focus management, reduced motion, screen reader and mobile viewport are tested; no obscured checkout/cookie interfaces or serious LCP/CLS/INP regressions.
- [ ] Real browser captures and action logs show each state and the full product→cart path on a permitted Shopify preview/staging surface; mocks do not count as production-real verification.
- [ ] Run controlled comparison of simple vs enhanced PDP when sample and economics allow; avoid declaring the second visually attractive variant the universal winner without evidence.
- [ ] UKDL Hard Rules / Process Rules / Traps record actual new failures with root-cause evidence; ratchet reusable principles such as **«all product selection surfaces must remain synchronized with transaction truth»** and **«recommendation is not purchasable inventory»** in a domain-appropriate, enforced completion standard. Prove fresh-agent inheritance.
- [ ] Honor the repo's feature Code Freeze and telemetry/approval requirements; this is a tracked specification, **not an implementation or deployment claim**.

###### Delivery strategy / ROI

**P0** Audit and test existing variant/sticky purchase flow (possible immediate correctness opportunities); **P1** guarantee transactional consistency and media linkage; **P2** compose rich purchase panels for only real offers; **P3** render/browser QA; **P4** experiment with decision friction and contribution profit, then promote proven lessons to canonical baseline. Execute as bounded, reviewable micro-commits after authorized inline plan. Production Reality Gate at each done-gate.

**Success:** the second-option *principles* become a reusable, context-dependent standard of PDP completeness, not a compulsory screenshot clone or an unverified conversion claim.

###### Continuidad de las referencias SGE 10/10 — 2026-10-26

- **Molly Loves Ecom (segunda opción del vídeo):** la ampliación **PDP Second-Version 10/10** de este issue es la especificación canónica de configurador, panel de compra premium, ofertas reales y sticky purchase.
- **Wellcopymax (suscripciones y retención):** [#7 — Subscription Commerce & Retention Intelligence](https://github.com/jacobo07/TUA-X/issues/7) define selling plans comprables, coherencia de descuentos entre PDP y popup, educación postcompra, recordatorios de cobro, medición de contribución y Production Reality Gates. La parte del buybox se consume aquí; el runtime de suscripciones/lifecycle pertenece a sus propietarios, no a un segundo SGE.
- **Invariante:** riqueza visual e interacción no son evidencia de suscripción activa, consentimiento del cliente, precio recurrente correcto ni uplift económico. Ningún cierre de este issue puede dar por cumplidos los gates B2C de #7 sin trazas reales.

---

##### Addendum — Trust-at-Decision, UGC & CRO ROI Priority (Jos + Jssie, 2026-10-26)

###### Evidence source A: Jos Poulakis — decision-local trust and PDP composition
Owner video: `jospoulakis_f557e2c824eb481c88ebf7afdb1c6841.mp4` (~61.4 s, SHA-256 `79846afbb6d908385abfe1ecc732916426e9541c6939e15a2e28fad186383929`). Source is attached to the conversation, **not** to GitHub.

Observed:
- ~00–08: Shopify product page GLIDE Anti-Chafe Shorts; presenter calls for more trust on a product page, **especially named customer reviews**, visibly next to product title/price/offer. Source video display is an example, not independent verification of authenticity.
- ~09–13: **UGC videos inside the buy box** plus a separate picture/review section, drawing the visitor into more than a sterile image gallery. Product/media rights and grounded endorsements remain mandatory.
- ~14–32: make visitors feel understood by describing their persona and acknowledging **real objections**, sourced from customer questions and places where they discuss the category (e.g. groups/social comments). Rewrite into brand-owned content, **do not copy user testimonials without rights/consent**; keep question/claim provenance.
- ~34–44: show real quantities/offer packs, then a relevant **post-add-to-cart upsell**. Video says «you would be surprised how many ...» without measured data; do not assume uptake/profit.
- ~47–60: shows **prebuilt Shopify PDP templates** inside an app/dashboard and recommends using them; app installation is a vendor/economic decision, **not** evidence that templating automatically constitutes a production quality gate.

**System design / SGE reuse**:
- Extend **SGE's existing PDP composition**, `store_quality`, verified social proof and media contracts, and **CW Shrine**. No separate trust engine or parallel slideshow system.
- Near-decision evidence types: verified ratings, a small number of attributable testimonials where publication is authorized, delivered-size/fit evidence, UGC/video with provenance, warranty, payment/fulfilment, and clear purchase options.
- Real objections become structured questions linked to **verified answers**, shown near the decision point or deeper via FAQ as needed. Persona should be grounded in research and must not imply evidence of customer sentiment where none exists.
- **Optional contextual upsell** connected to actual inventory and pricing, matching current selected variant and respecting margin/price/stock. Never present it as already added or hide total cost.
- Existing `shrine-captura.liquid`, `shrine-deseo.liquid`, `shrine-confianza.liquid`, `sections.py` and `quality_gate.py` contain relevant seams. Audit current literal placeholders such as «Verified reviews appear here as customers leave them», «Trusted by customers», guessed shipping or money-back copy before claiming fidelity.
- Source video is not authorization to clone GLIDE's branding/photos/copy or install an unidentified commercial app.

###### Evidence source B: Jssiehcktt — CRO intervention triage, not a universal tier ranking
Owner video: `jssiehcktt_cb23a27eb40a4a8aa7953a0231fcb7da.mp4` (~47.2 s, SHA-256 `ea50e2143c966950102196d037a9e10e59c8cab332b1186031804440d26336dd`). Video shown as a creator's subjective S/A/B/C/D/E/F tier list, **not experiment results**.

Visible comparisons from source:
- ~03–07: **new homepage** placed in a low tier (D). Claim: most visitors do not see it when direct traffic arrives on PDP.
- ~09–13: **spin-to-win popup** placed above homepage redesign but still lower priority (C); not a guaranteed first optimization. Relates to #6, where `no-popup` remains a valid option.
- ~15–18: **mobile page speed** ranked B and called a real fix.
- ~19–27: **reviews immediately next to Add-to-Cart** ranked A, trust should be where the decision happens, not buried on a review page nobody visits.
- ~29–37: **shipping time, returns and fit** explained in one accurate, legible line **above the fold on the PDP** ranked A, with the presenter claiming support tickets may drop (unverified).
- ~39–46: **second-purchase conversion rate** ranked S; the creator expects increased word-of-mouth and repeat business, but this ranking and outcome are **subjective**. Track real cohort repeat purchase before declaring uplift. Connect to #7 (retention) and #9 (store-credit experiments).

**SGE 10/10 completion implication**:
- CRO choice is an **ROI-ranked intervention**, not an always-on feature checklist. Rank fixes using bottleneck, evidence confidence, expected incremental contribution, blast radius, reversibility, cost, traffic landing path and product context. A home-focused brand may legitimately prioritize its homepage; mobile speed and second-purchase uplift can dominate if actual data supports it.
- Generate clear **decision-proximal verified evidence** and truthful shipping/returns/fit; do not fabricate shipping windows, refund rights, stock/fit claims, review identities or star counts.
- Product media/popup/upsell must not increase LCP/CLS/INP/friction enough to erase gains. Trust placement must remain accessible, legible and consistent on mobile.
- Separate **operator recommendations** (what to optimize first) from **store generation** (what can be implemented now). Reuse existing revenue bottleneck/next-best-action, experiments, CXE lifecycle and `quality_gate` when ownership supports them, without building a second universal CRO sorter in SGE.

###### Production Reality / acceptance extensions
- [ ] Evidence map: creators' observations vs claims vs verified runtime constraints; no supposed conversion uplift smuggled into stable constants.
- [ ] True name/photo/UGC/review license and substantiation required before public display. Empty reviews → clean absence or explicit neutral state, **not fake verified testimonials**.
- [ ] Source-backed shipping, delivery, returns and fit displayed near purchase with mobile accessibility, matching checkout and fulfilment provider.
- [ ] The UGC carousel/videos display media only when assets are licensed, video controls work, and reduced-motion/slow-data fallback is available; measure LCP/CLS/INP.
- [ ] The primary buy box, variants, add-to-cart, review anchors and upsell operate on the actual selected SKU/price/stock and purchase event; verify end-to-end in a real browser/Shopify non-live preview where possible.
- [ ] Tests on direct-to-PDP traffic and homepage-entry traffic; recommendation changes according to measured landing-page mix, not a universal «homepage D».
- [ ] Prioritize conversion and **second-purchase contribution economics** with real cohort/experiment data, including returns, shipping fees, loyalty liability and repeat frequency, not AOV alone.
- [ ] Comparisons with simpler layout/control: a richer PDP does not automatically mean a more profitable PDP. `UNDETERMINED` when data insufficient.
- [ ] Error cases, broken media, unknown delivery, no customer reviews, unsupported product options, no email consent and no upsell inventory produce honest states and no dead controls.
- [ ] UKDL Hard Rules / Process Rules / Traps and Constitutive Baseline Ratchet promotion **only after real failures and enforceable evidence**: «decision-local claims are grounded», «observable purchase effects match selected offer», «optimizations are prioritized by measured bottlenecks and contribution». Scope rules to relevant interfaces/business domains.
- [ ] TUAX Feature Code Freeze `AGENTS.md` / telemetric approval, inline plan, bounded micro-commits, Production Reality Gate on each done-gate. This addendum is **not** a code delivery.

###### Connected upstream / downstream work
- [#8 Identity-Led Positioning & Transformation Intelligence](https://github.com/jacobo07/TUA-X/issues/8): grounded persona and ideal self, usable for credible customer-voiced PDP copy.
- [#9 Store Credit Rewards & Repeat Purchase](https://github.com/jacobo07/TUA-X/issues/9): optional second-purchase incentive after real profit and redemption analysis.
- [#7 Subscription Commerce & Retention](https://github.com/jacobo07/TUA-X/issues/7): lifecycle/cohort repeat conversion, not a duplicate retention service.
- [#6 Popup Experience](https://github.com/jacobo07/TUA-X/issues/6): optional, not automatically above decision-proximal trust in every store.

**ROI order:** inspect existing claims/variant/cart correctness and mobile performance first, then add verified UGC/objections, then test contextual upsell and cross-lifecycle repeat purchase. All gates require real evidence; screenshots alone are insufficient.

---

##### Addendum 2026-10-27 — Jeffrey M. Park + Jos Poulakis: PDP Reference Grammar & Offer-Proof Composition

###### Scope and provenance

Two **different** owner-supplied videos, reviewed frame by frame, are additional evidence for this existing SGE 10/10 programme. Their source files exist in the conversation, **not in the repository**, and are design/copy references only — neither is a performance audit or a licence to clone assets:

- **Jeffrey M. Park:** `jeffreympark_ddc0e20578274423937a510139dff2e0.mp4`, duration ~6.92 seconds, SHA-256 `bdb99261555a9fe8199df5e02dd972f14d46486a0c5a8c8f267dd70d359eda13`. Caption «10/10 Shopify product pages». Includes screenshots of four visually different supplement/health PDPs: Metabolace Ceylon Cinnamon (warm orange/brown); Kitty Supps Taurine (blue/white); Resilia Aged Odorless Garlic (deep red/burgundy); Lymphoria Lymphatic Drainage Drops (botanical green). At ~03–06s the creator asks viewers to comment «PDP» for links; **actual links are not in the supplied video**. No conversion, page speed, checkout or merchant permissions independently verified.
- **Jos Poulakis (NEW clip, not the earlier GLIDE shorts video already captured in this issue):** `jospoulakis_a94f204ad6e748e19ad0d4d29163df52.mp4`, duration ~87.45 seconds, SHA-256 `1d2c7a30e5e00c0a84814f587d90188a96487ab6ebdf0dc996908a169fdc9882`. Observed MOVA Sculpt Set product-page walkthrough. The video claims a **6% conversion** near 00:00, but offers no verified analytics, definition, period, denominator or causal experiment. Store-specific banners, reviews, stocks, shipping timing, rewards and bundles in footage are **observed page content, not independently validated facts**.

###### NEW perspective A — PDP visual grammar must be brand-specific even within one niche

Jeffrey's four screenshots illustrate **distinct styles for related product categories**, not a single universally optimal page. Extract abstract and transferable structure rather than page assets or fixed colors:

- Product photography dominant but adapted to brand's tone, background and evidence needs.
- Brand-specific design tokens, typographic contrast, editorial vs clinical vs botanical styling, whitespace and accent allocation.
- Cohesive visual relation between product media, hero, key benefits, trust, price and purchase panel.
- Intentional, readable card density and truthful status/offer labels.
- A library of **sourced PDP visual patterns** feeding existing CDIO/SGE design-intent and CW Shrine *without cloning or adding a parallel designer*.
- **Diversity without randomness**: even stores in one niche should not all collapse to the same Shopify/Dawn layout or palette; expressive differentiation must remain compatible with accessibility, performance and the underlying brand/product truth.
- The caption «10/10» is a **creator opinion**, never SGE's measured score; static screenshots show appearance only, not live interactions or operational completion.

###### NEW perspective B — MOVA-style conversion composition is an evidence-grounded journey

The Jos footage includes these *specific* observed mechanisms, each of which can map to existing SGE/CW Shrine primitives only when real product and commerce data make it valid:

1. **~00:03–00:13, first-order offer at decision point.** PDP header advertises **15% off first set/order** with a code. Test whether a discount with specific customer/product eligibility truly applies in Shopify checkout and agrees with cart/other offers; it is a *promotional claim*, not universal advice to discount by 15%.
2. **~00:18–00:22, actual bonus proposition.** Header says **«Free matching scrunchie with every set»**. If replicated as a mechanism, the gift must be a genuine eligible SKU/service with inventory, fulfilment cost, eligibility, redemption/auto-add behavior and Shopify receipt. No gift promise solely through copy.
3. **~00:10–00:25 and ~00:45–00:60, rich purchase choice.** MOVA buy box shows **Single / Duo / Trio** and claimed price savings (e.g. Duo 15%, Trio 25% shown in footage). Must map each selection to real stock/variant or bundle objects, correct component inventory, actual unit economics, transparent totals, correct SKU/checkout and reversible user choice. Synchronize selected choice with sticky ATC and drawer. Do not invent bundles or assume advertised percentage verified.
4. **~00:24–00:46, objection-led proof.** Section titled approximately **«Another set that goes see-through in month two?»** addresses visible-pilling/opacity concerns with detailed product assertions and a customer-quote-looking review. Creator recommends inspecting negative customer reviews to uncover objections. Only use legitimately sourced customer/competitor research; factual material/performance assertions and testimonials must be proven/authorized. Do not invent names, ratings, testimonials or guaranteed durability.
5. **~00:44–00:51, feature→benefit hierarchy.** Presenter calls attention to **three strong benefits at the top of the product page**, with creative/product explanation. Compile claims via existing product truth/copy engine and show only when verified; do not hide vital specifications or tradeoffs.
6. **~00:57–00:60, scarcity cue.** Text **«Almost out of Stock»** appears close to Add to Cart. Permit only with current provider-backed inventory, defined threshold, correct variant/warehouse scope, expiration and cache invalidation. Unknown stock → no scarcity claim. **Existing CW Shrine HR-URGENCIA-REAL remains binding**.
7. **~00:61–00:66, operational countdown/arrival promise.** «If you order within ... you'll get it by ...» and ordered/shipped/delivered milestones. Gate on actual merchant cutoffs, warehouse hours, timezone, shipping method, destination, holidays, fulfilment capacity and provider ETA; a free-running JS timer or unverifiable delivery day is a BLOCKER to the promise. After missed cutoff, update/withdraw the claim.
8. **~00:66–00:71, customer footage and contextual drawer.** Short UGC videos near the purchase journey plus a cart drawer shown later. Every media asset needs usage rights/provenance, accessible control and low-data fallback; drawer must show exact selected items/variants/promo/gift and real totals.
9. **~00:74–00:85, ready-made Shopify page sections.** Creator shows an app/library of PDP presets and mentions a free trial. **Do not infer the app is installed, priced appropriately or operational**; evaluate against current CW Shrine renderer, licensing, recurring TCO, vendor lock-in and the existing source of truth before considering adoption. A screenshot of an app section catalog is not a completed feature.

###### Implementation boundary / reuse map

- **SGE** composes desired experience and product-specific claim positions from existing research, `StoreSection`, `build_pdp_sections`, Offer Builder and awareness-copy; avoid new pricing, merchandising or persuasion authorities.
- **CDIO/Design Intelligence + existing design-intent** own aesthetic decisions; **CW Shrine over Dawn** owns merchant-editable render. Preserve sealed six-layer PDP conversion order unless the constitutional owner approves its revision.
- **Shopify and merchant inventory/promo/shipping sources** own applicability, money, item identifiers, inventory, cutoffs and outcomes. `OfferStructure` may contain *recommendations* and speculative projections; recommendations are **not** live discounts, gifts or buyable inventory.
- **#5** authentic offer choices and pricing owns first-order promo/gift/bundle truth and stacking; **#6** popup cannot advertise a conflicting discount; **#7** subscriptions remain distinct from one-time multibuy bundles.
- **Quality Gate** must not label a store «PUBLISH_READY» based on copy structure or appearance when discount/gift/shipping/stock semantics are not verified in an actual checkout. Preserve evidence class `UNDETERMINED` where missing.

###### Extra completion tests (Production Reality Gate on each DONE)

- [ ] Provenance entry for both videos: URL when genuinely known, transcript/subtitle limitations, visual patterns, timestamps, source claim vs verified conclusion; no derivative product imagery or copy copied from screenshots.
- [ ] CDIO demonstrates **at least three brand-consistent but visually distinct** PDP presentations for grounded catalog items, including low-asset/no-proof fallback; diversity is not achieved by randomly recoloring a fixed page.
- [ ] A first-order promo is **actually redeemable** by eligible buyers at checkout and is rejected/withdrawn for ineligible customers; test promo interactions with automatically applied discounts and bundle pricing.
- [ ] «Free gift» appears only when a real eligible item is added/redeemable and fulfilment/stock/cost conditions are satisfied; hidden/effectless free-gift banner fails.
- [ ] Real Single/Duo/Trio purchase choices preserve correct variant/component IDs, unit prices, total, discounts, inventory, cart drawer and checkout under change/reload/mobile/stock depletion.
- [ ] Objection-led blocks, verified reviews, «top 3 benefits», photo/video and strong USP include provenance and respect health/supplement claims requirements when relevant.
- [ ] Low-stock message requires a provider-backed measured stock threshold; simulate unknown stock or 0 stock; no fake countdown/volume signals.
- [ ] Delivery cutoff + estimated delivery are grounded in a real fulfilment calendar and buyer destination; test crossing cutoff, holidays, network errors, unsupported carrier and timezone.
- [ ] No dead button, unexpected 401, disconnected frontend/CLI/provider, misleading cart totals or duplicate item adds; keyboard/touch accessibility and Web Vitals measured using real browser evidence.
- [ ] Main CTA, sticky CTA, cart drawer, all rewards and final checkout describe the **same** purchase, not competing snapshots.
- [ ] Controlled simple-vs-rich PDP experiment before asserting a conversion uplift. Track incremental contribution margin/session including promotion/gift/fulfilment costs, not visual «10/10» score or unverified «6% conversion».
- [ ] Incidents → canonical Knowledge Vault, UKDL Hard Rules/Process Rules/Traps and credible regression tests. **Constitutive Baseline Ratchet candidate**: *Every visual or transactional customer promise has a measurable source, a live consumer and a verified downstream effect; unverified promises cannot obtain Production Reality PASS*. Promotion requires actual enforcement and fresh-agent read-path.
- [ ] TUAX `AGENTS.md` feature Code Freeze/telemetry/approval honored. This addendum is a spec/backlog update, **not evidence of new runtime implementation**.

###### ROI execution order

**M0:** snapshot current store, inventory, Shopify authorization, CDN/media and shipping sources; classify what is already implemented and misrepresented. **M1:** fix any real purchase/claim integrity holes in existing CW Shrine/SGE before visual flourish. **M2:** enrich grounded visual grammar and contextual benefits/objections. **M3:** first-order offer + gift + multibuy **only when provider-backed**, with actual cart/checkout verification. **M4:** delivery/stock logic and live-browser QA. **M5:** controlled experiment, institutional learning and ratchet of verified invariants. Use bounded micro-commits and plan-inline approval as mandated.

**Final aim:** SGE can render different brands with high-quality visual grammar and a truthful, fully-functional offer/proof journey; it does **not** acquire a licence to copy screenshots, promise fabricated scarcity or claim +6% conversion.

---

##### Extension 2026-10-27 — Whole-Site Coverage / 20 Commerce Experiences

Owner-supplied Maxtymosh video «20 pages for your e-commerce website» is tracked in **[#10 — Commerce Site Architecture Intelligence](https://github.com/jacobo07/TUA-X/issues/10)**. This issue (#4) remains the **PDP/PLP visual design, merchandising and browser-render QA owner**. #10 owns the larger architectural decision: which *other* commerce experiences merit a true page, a reusable section, a provider-owned customer surface, or an explicit NOT_APPLICABLE verdict.

Do not attempt to satisfy the «20 pages» reference by building 20 static Shopify pages. The source names 20 customer intents, not 20 required Shopify template types. #10 requires a complete site-coverage decision (including justified absence) and real links/actions for the relevant surfaces.

**Important new live-system risk for #4 and #10:** current ShopifyAdapter targets API 2024-01, and _maybe_write_theme creates an unpublished theme but then calls publish_theme, setting its role to main. This is a change to the live theme even when the prior theme's files were untouched. Real Shopify-version/scope audits, owner authorization and an unpublished-theme preview gate are required before any non-test deployment. See #10 for details, Shopify documentation and additional gates.


## TUA-X#5 -- SGE — Preference-Based Offer Architecture: elección auténtica, valor y pricing transparente

State OPEN, created 2026-10-25, https://github.com/jacobo07/TUA-X/issues/5

##### Objetivo

Integrar en **SGE** una capacidad de **Preference-Based Offer Architecture / Truthful Choice Architecture**: preguntar opcionalmente al comprador qué prioriza, traducir la preferencia a ofertas REALES, disponibles y claramente diferenciadas, y comprobar si la experiencia mejora el **beneficio de contribución por sesión** sin deteriorar confianza, cumplimiento, devoluciones ni calidad de decisión del cliente.

Motivación: guion aportado por el Owner en la conversación del 2026-10-25. Un creador relata que, tras subir precios un 30 %, añadió una pregunta al PDP: elegir entre «faster results» y «lowest price», afirma que sus ventas subieron y denomina al mecanismo «fake choice». **La historia es anecdótica y causalmente NO verificada.** No incorporar ni la promesa de +30 % ni «charge whatever you want» como doctrina institucional.

##### Decisión doctrinal

**ADOPTAR**: explicit preference elicitation, self-selection, value framing basado en hechos, comparador de ofertas, mejoras de valor percibido que se correspondan con beneficios reales, diseño y medición de experimentos.

**RECHAZAR**: ilusión de elección, opciones que no alteren la experiencia/oferta, esconder el precio para explotar una selección forzada, fake discounts, afirmaciones comparativas sin datos, segmentación opaca de disposición a pagar, resultados de salud exagerados o falsos.

La frase/pregunta solo se muestra cuando cada opción provoca una consecuencia verificablemente distinta que el comprador puede inspeccionar y cambiar; si no, no hay cuestionario.

##### Reutilización obligatoria (inspección main 2026-10-25)

- `tuax_core/engines/sge/offer_builder.py`: propietario existente de arquitectura de ofertas; reutilizar el contrato `OfferStructure` en vez de crear una segunda fuente de verdad.
- `tuax_core/engines/sge/pricing.py`: propietario de pricing económico; auditar supuestos 4x-COGS / límites / evidencia antes de extensiones de elasticidad de precio.
- `tuax_core/engines/sge/awareness_copy.py`: copy y CTA según awareness; no duplicar sistema de copy.
- `tuax_core/engines/sge/models.py`: `OfferComponent`, `OfferStructure`, `StoreGenerationResult`, `StoreSection`: evaluar la extensión mínima compatible.
- `tuax_core/engines/sge/sections.py` y `tuax_core/theme/cw-shrine/`: renderizador de PDP; conectar solo componentes reales y editables en Shopify.
- `tuax_core/engines/sge/quality_gate.py` + evaluadores canónicos: añadir validación de selección auténtica, sin score paralelo.
- Auditar capacidades de experimentación, analítica, consentimiento, Product Truth, profit/P&L y gobernanza reales antes de definir nuevos módulos.
- **Relacionada:** #4 (SGE Visual Standard 10/10). #4 gobierna la excelencia renderizada; esta issue gobierna la coherencia de oferta y decisión del cliente. Ambas deben converger en un done-gate de experiencia completa.

##### Experiencia de comprador prevista

Ejemplo genérico, adaptable por producto:
«¿Qué prefieres priorizar en esta compra?»
- «Más comodidad / solución más completa» → pack o servicio diferenciado con mayor contenido/servicio verificable.
- «Menor desembolso inicial» → unidad/base disponible realmente más barata en coste total inicial.

No utilizar «resultados más rápidos» en suplementos, cosmética o salud sin evidencias específicas y claims autorizados. **Más caro ≠ resultados más rápidos.**

La comparación puede presentarse directamente sin cuestionario si eso ofrece mejor UX/conversión. Control, variante con elección y comparación directa deben tratarse como hipótesis, no como una receta obligatoria.

Contratos UX:
- Pregunta opcional/no bloqueante, accesible por teclado/touch, reversible, sin manipulación visual.
- Mostrar precios reales, impuestos/costes requeridos, cantidad, recurrencia, variaciones en entrega/servicio y condiciones con suficiente claridad antes de decidir la compra; acceso fácil a todas las opciones. Nada de ocultar la alternativa relevante.
- No asignar dos precios secretos al MISMO SKU por inferencia de poder adquisitivo. Si existe personalización de precio basada en decisiones automatizadas, activar gobernanza legal y avisos exigidos; preferencia de pack estándar diferente no equivale por sí misma a discriminación de precio individual.
- Si el inventario/oferta no soporta diferencias significativas → renderizar comparación honesta o PDP habitual; jamás una elección ficticia.

##### Price & Economic Truth

No incrementar el precio global automáticamente porque un cliente prefirió calidad/resultados.

Medir rentabilidad incremental, no solamente facturación:
- Exposición al tratamiento y tasa de participación.
- Distribución de respuestas y opción mostrada.
- Conversión de PDP→ATC→checkout→purchase.
- Valor medio del pedido y unidades.
- Margen de contribución por visitante/sesión, neto de COGS, descuentos, fulfilment, fees y gastos incrementales relevantes.
- Devoluciones/cancelaciones, reclamaciones y señales de confianza.
- Impacto móvil y tiempos de carga.
- Consistencia de precios y ofertas en otros canales.

Instrumentar ensayos controlados usando el experimento canónico del repositorio, con asignación estable, detección de interferencia, tamaños de muestra/intervalos e interpretación causal honesta. No afirmar que el vídeo prueba uplift. Comparar el tratamiento con un control sin pregunta y, cuando haya volumen, una alternativa de comparación directa y transparente.

##### Gate de cumplimiento / protección del comprador

Fuentes oficiales de referencia que deben revalidarse en ejecución para cada mercado:
- España (Ministerio de Consumo), transparencia de precios personalizados: https://www.dsca.gob.es/es/consumo/preguntas-frecuentes/puede-tienda-online-usar-mis-datos-mostrarme-precios-personalizados
- Comisión Europea, ejemplos de prácticas comerciales engañosas y ocultación de costes: https://commission.europa.eu/news-and-media/news/eu-check-reveals-misleading-sales-practices-online-2026-03-26_en
- UE, precios personalizados y deberes de información: https://europa.eu/youreurope/citizens/consumers/unfair-treatment/unfair-pricing/index_en.htm
- UE, regulación de declaraciones nutricionales y saludables: https://food.ec.europa.eu/food-safety/labelling-and-nutrition/nutrition-and-health-claims_en

Jurisdicción y producto determinan aplicabilidad. No afirmar que cualquier pregunta previa al precio es ilegal ni que cualquier precio personalizado está prohibido: el cumplimiento es más específico. Revisar los requisitos del marketplace/ads cuando aplique.

##### Done-gates (implementación futura condicionada por gobernanza)

- [ ] Discovery read-only de propietarios, dependencias, diseños, medidas y reglas del repositorio; sin duplicar motores.
- [ ] Dos opciones diferentes producen al menos dos consecuencias COMPROBABLES y activables (SKU, pack, términos o servicio); prueba que falla si ambas rutas coinciden sin diferencia real.
- [ ] Precio total y términos sin sorpresas; selector reversible y opcional; accesibilidad y estados negativos probados.
- [ ] Pruebas Shopify/reales de disponibilidad, checkout, cambio de opción, manejo de stock y error de conexión, según los recursos y permisos disponibles.
- [ ] Sin dark patterns ni claims de resultados clínicos no sustentados. Prueba adversarial para no prometer «faster results» sin respaldo o «lowest price» sin verificación.
- [ ] El comprador puede ver y comparar todas las alternativas relevantes; no se le oculta información para inducir una decisión.
- [ ] Métricas instrumentadas en el sistema canónico; cualquier uplift requiere experimento, datos y desglose de costes.
- [ ] Mantener compatibilidad con single-SKU sin crear packs ficticios; comportamiento de fallback explícito.
- [ ] Production Reality Gate antes de cualquier PASS; no basta con Pydantic/test/mocks o screenshot.
- [ ] Incidentes → Knowledge Vault + patrón UKDL Hard Rules / Process Rules / Traps, con evidencia y promoción controlada.
- [ ] Constitutive Baseline Ratchet: promover **solo el principio universal de elección auténtica y coste/efecto visibles**, no un componente de marketing específico para software ajeno a ecommerce; demostrar consumo/enforcement mediante fresh-agent/negative test.
- [ ] Respetar `AGENTS.md`: Feature Code Freeze exige mecanismo/gates de aceptación aplicables; una idea va a issue, no PR arbitrario.

##### Secuencia ROI

M0: audit/diagnóstico de contratos y ofertas actualmente representables.
M1: mínimo contrato de preferencia→oferta real, con gates de veracidad; si no hay alternativas reales, NO UI.
M2: experiencia reversible en CW Shrine y pruebas de navegador/Shopify.
M3: instrumento experimental y análisis de beneficio de contribución.
M4: UKDL/Ratchet y pruebas de herencia institucional.

**Estado**: propuesta para planificación. Ningún despliegue, cambio de precio, prueba estadística o modificación de código realizada con este issue.

**Regla final**: vender una alternativa más cara solo es aceptable como recomendación más adecuada cuando las diferencias son reales, claras y justificables; el comprador conserva el control efectivo de la elección.
---

##### Positioning cross-reference — aspiration is not price evidence (2026-10-26)

Georgie Lewis's identity-led positioning video has been captured in [#8 — Identity-Led Positioning & Transformation Intelligence](https://github.com/jacobo07/TUA-X/issues/8). An aspirational product story may influence *perceived value*, but is **not** proof of price elasticity or a justification to raise prices without testing contribution profit and customer trust. Preserve #5's authentic-choice and price-truth contracts. Use #8's source-grounded positioning only as input to the canonical SGE Offer Builder/brand/copy machinery, never a second pricing source.


---

##### Addendum 2026-10-27 — First-Order Code + Free Gift + Single/Duo/Trio Offer Truth (MOVA)

Cross-reference: [#4 10/10 PDP — Jeffrey M. Park and the new Jos Poulakis MOVA clip](https://github.com/jacobo07/TUA-X/issues/4). The new Jos clip (~87.45 s; SHA-256 `1d2c7a30e5e00c0a84814f587d90188a96487ab6ebdf0dc996908a169fdc9882`) displays a **15% first-order/first-set promo banner**, **free matching scrunchie with every set**, and **Single/Duo/Trio** purchase options (with advertised tier savings). These visual claims must become legitimate *provider-backed offers* before SGE may generate them in an active store. The creator's claim of **6% conversion** is not verified and must not be used for economic forecasts.

###### Offer Builder enhancement — composition, not parallel pricing

- Reuse existing SGE `OfferStructure`, Offer Builder, Shopify discounts and inventory; first-order codes, automatic discounts, gifts and bundle tiers are not interchangeable representations.
- A *promo banner* needs a valid discount code or actual automatic discount; verify first-order eligibility, applicable variants, exclusions, date window, number of uses, currency, combinability and checkout applicability. Hide or downgrade the claim if any contract is unverifiable.
- A *free matching gift* must have a real SKU, available stock, real addition/redemption path, fulfilment cost, handling of returns and removal when eligibility changes; Shopify's built-in buy-X-get-Y logic may require both cart items to be present rather than automatically adding the gift. **Do not advertise gift fulfilment unless it is actually enabled.**
- A *Single/Duo/Trio* tier requires real product or bundle identifiers and quantities, calculated unit economics and exact compare-at/discount math. Re-select/reload/change availability must update every cart/checkout-facing selection consistently.
- **Promo stack** across #4 PDP, #6 popup, #7 subscription and #9 credit must not promise incompatible or double-applied savings. Prioritize correct total contribution profit over a higher reported discount percentage.
- Prefer Shopify-native features where they work; evaluate third-party theme/offer apps only if a verified feature gap and  total cost of ownership warrant them. The video shows an app template catalog but not a working integration in TUAX.

###### Validation / kill-switch tests

- [ ] Real eligible first-time order receives exactly the advertised benefit; ineligible customer, invalid code, date expiry, incompatible stack, different market or wrong variant sees accurate offer/CTA.
- [ ] When checkout requires entering a code, disclose it and provide a functional path; never treat 'banner displayed' as 'discount applied'.
- [ ] Gift truly shows as an eligible checkout item and is fulfilled with sufficient stock, without unexpected charges; if absent, no «free gift» promise.
- [ ] Single/Duo/Trio values, bonus units, percentage saved and price per unit reconcile to actual checkout under quantity/variant changes and inventory exceptions.
- [ ] No arbitrary first-order discount default of 15%, no fake limited offer, no purported 6% conversion benefit.
- [ ] End-to-end real merchant/staging browser confirmation with screenshots, checkout transaction/discount receipts and negative-path tests. Mocks alone = `PRODUCTION_REALITY_UNVERIFIED`.
- [ ] Actual defects and generalizable traps flow via Knowledge Vault and the UKDL three layers; any Constitutive Baseline Ratchet promotion requires enforced invariant, real negative test and proof of fresh-agent inheritance.
- [ ] Respect `AGENTS.md` Code Freeze + owner authorization and telemetry gates. **Specification only; neither an active coupon nor an issued gift is implied.**

Shopify's current official discount help documents details on code eligibility, combinations, and automatic discount behavior:
- https://help.shopify.com/es/manual/discounts/discounts-faq
- https://help.shopify.com/es/manual/discounts/discount-combinations
- https://help.shopify.com/es/manual/discounts/discount-methods/automatic-discounts

**Success** means the shopper can really purchase the exact proposed bundle, receive the eligible and accurately described gift/discount, and see matching final charges — not simply that an aesthetically persuasive offer was generated.


## TUA-X#6 -- SGE 10/10 — Popup Experience Intelligence: captación, gamificación verificable y Quality Gate real

State OPEN, created 2026-10-25, https://github.com/jacobo07/TUA-X/issues/6

##### Qué solicita el Owner

Incorporar al **SGE (Store Generation Engine)** el estándar de **popup 10/10** observado en vídeo de Nonso (`nonso.ecom_0e95cf4cf5c04f2eb7d726916e3bd146.mp4`, aportado en la conversación; **no está adjuntado al repositorio**). Objetivo: **experiencias de captación, interacción e incentivo coherentes con cada marca, realmente funcionales y económicamente justificadas**.

###### Evidencia visual directa del vídeo (33,88 s; inspección de fotogramas)

- **~00–04 s:** AG1; oferta de bienvenida con imágenes del kit, campo de nombre y CTA de incentivo («Save £68 on your AG1 Welcome Kit» visible como claim del ejemplo, NO garantía de nuestra oferta).
- **~05–09 s:** SKIMS; formulario «Never miss a drop», captura de email, preferencias seleccionables y alternativa «No thanks».
- **~09–13 s:** IM8; selector gamificado de tarjetas «Try your luck» → pantalla que anuncia un descuento y regalos, seguida por email.
- **~13–16 s:** composición editorial «Join the Club» con fotografía, beneficio, formulario SMS y cierre.
- **~16–20 s:** «Try Your Luck» de un comercio de relojes; minijuego Plinko/caída de bola con casillas de descuentos «20% off» y «Mystery Discount» y CTA **«Drop Ball»**, superpuesto al catálogo.
- **~21–29 s:** demostración de creación/adaptación de un popup en un editor visual a partir de captura de referencia, mostrando el mecanismo sobre una web de maletas y luego una presentación de relojes. La grabación **no demuestra** que se haya conectado un backend real de premios, consentimientos, códigos o analytics, ni que mejore conversión.

No copiar marcas/fotografías/composición exacta/propiedad intelectual de ejemplos. No inferir resultados económicos ni prácticas de consentimiento correctas por verse en el vídeo.

##### Arquitectura: extensión, no motor duplicado

**SGE decide/orquesta** formato e intención comercial → **CW Shrine renderiza** componentes Shopify OS 2.0 → **Offer Builder / Pricing / Product Truth** determinan ofertas válidas → propietario real de **captación/consentimiento** almacena suscripciones autorizadas → propietario de **discounts** asigna recompensas verificables → **Analytics/Experimentation** mide → **Design/Quality/Reality Gates** validan. Auditar los propietarios existentes y no crearlos de nuevo sin pruebas de ausencia.

Referencia: **#4 SGE 10/10 experiencia visual** y **#5 SGE elección de oferta auténtica**. El componente popup debe consumir las decisiones de diseño y los contratos de valor ya canónicos, no establecer un segundo branding/pricing/CRM.

###### Estado actual inspeccionado, a revalidar en HEAD

- `tuax_core/theme/cw-shrine/README.md`: overlay Shopify Dawn con homepage/PDP y acciones de carrito; no documenta un componente popup.
- `tuax_core/theme/cw-shrine/assets/cw-shrine.js`: JS del overlay revisado sin referencias a `popup`/`modal`/`subscribe`/`sms`.
- `tuax_core/engines/sge/sections.py` y `quality_gate.py`: contratos de secciones y scorer actuales; no demuestran un popup interactivo renderizado.
- **No asumir ausencia global** de captación o de sistema de promociones: revisar APIs, Shopify Forms, apps conectadas, Shopify Discounts, consentimiento, segmentación y analítica del repo antes de construir nada.
- `AGENTS.md` contiene restricciones de **Code Freeze**: esta issue es propuesta, no autorización para escribir código de feature sin telemetría, gates y aprobación aplicables.

##### Resultado esperado: Popup Experience Intelligence, no «un pop-up bonito»

SGE debe determinar **si conviene mostrarlo** y **qué variante aporta mayor utilidad esperada** por nicho, tipo de catálogo, oferta real, intención/etapa de compra y canal/dispositivo:

1. **Welcome benefit / incentivo verificable**: mensaje y descuento ligados a un offer real, sin descuentos inventados.
2. **Editorial opt-in**: captura de email/SMS con beneficio/expectativa explícitos, estado de consentimiento y control de cierre.
3. **Preference capture**: preguntas/segmentación auténticas y opcionales, conectables al Issue #5; sin decisiones ficticias.
4. **Gamified reveal**: tarjetas, elección de cofre, caída de bola/Plinko u otra mecánica de juego **solo cuando** existe un motor seguro y autorizado de premios y condiciones, y el costo incremental del incentivo lo justifica.
5. **No-popup**: primera clase y potencialmente óptima si la UX, SEO, calidad de tráfico, cumplimiento o economía lo exigen.

El formato puede ser barra no invasiva, trigger contextual, pequeña modal, página opcional o diálogo de interacción; escoger la superficie según contexto. Single-SKU y multi-SKU deben recibir variantes apropiadas.

###### Contrato visual/funcional

- Arquetipo de marca y sistema visual canónico (CDIO/SGE): tipografía, fotografía original o licenciada, gradiente/contraste, composición, espaciado, responsividad. Los juegos deben ser reconocibles pero NO imitar interfaces ajenas.
- El popup no debe bloquear el contenido tras el primer paint por defecto. Trigger por intención o engagement **medible**, ajustado a móvil y desktop; respetar dismiss, opt-out, visitantes ya suscritos, frecuencia/cooldown y reentrada. No forzar exit-intent no soportado en móvil.
- Cierre siempre accesible; teclado/foco correcto, Escape, scroll-lock restaurado, lector de pantalla, `prefers-reduced-motion`, touch target, no layout shift/animación obstructiva.
- Ausencia de popup en checkout y otras rutas o condiciones donde genere interferencia inapropiada.
- No competir con banners de cookies, confirmaciones de autenticación, menú móvil o selección de variantes.
- Formularios con errores de red/validación, estados loading/success/failure/retry/dismiss reales; ninguna captura «fantasma».
- Ofertas, stock, fechas, términos y restricción por región del comercio verificables. El mismo premio no puede ser generado dos veces por refresh/retry; backend / código promocional como autoridad, animación como representación, sin manipulación de resultado.
- Si falta una capacidad esencial (app/permission/API/códigos/consentimiento), usar alternativa funcional más simple o desactivar el formato; **no declarar DONE** con animación frontend mock.

###### Promotions Truth / anti-dark-patterns

- Los premios anunciados existen y son canjeables. El descuento realmente funciona en el checkout; reglas de máximo uso, stock, elegibilidad, combinabilidad, expiración y coste se verifican.
- No fabricar ganadores, cuenta atrás, escasez, «mystery prize» de valor engañoso ni probabilidades secretas que creen falsas expectativas.
- Investigar si la mecánica aleatoria está sujeta a reglas sobre promociones/sorteos, premios y fiscalidad en los mercados aplicables; si no se autoriza o no puede verificarse, usar recompensa determinada y transparente o formato sin juego.
- Separar participación/recompensa de consentimiento para marketing según la normativa aplicable; no dar por consentido el email/SMS por jugar o cerrar. Consentimiento registrable, canal, marca, marca temporal, base/fuente, finalidad, revocación y preferencias; privacidad y minimización de datos.
- Nunca cambiar precios del mismo producto según perfil inferido sin transparencia y gobernanza correspondiente.
- No afirmar que «10/10» o «gamificado» demuestra mejora de conversión.

###### Reutilización de Shopify antes de custom implementation

Investigar la capacidad real de **Shopify Forms**, sus integraciones de marketing y descuentos, y el estado de las apps/API ya configuradas. La ayuda oficial describe formularios popup/inline con captura de consentimiento por canal y descuentos en pantalla de éxito:
https://help.shopify.com/es/manual/promoting-marketing/create-marketing/forms-app/settings/all-forms

Aplicar el proveedor nativo cuando resuelva el caso con menor TCO. El juego avanzado probablemente exija una extensión propia o integración autorizada, pero **no inventar funciones de Shopify Forms**. Mantener la capacidad SGE de orquestar otras superficies de captación sin vendor lock-in artificial.

Google desaconseja intersticiales invasivos por su efecto sobre la accesibilidad del contenido/SEO:
https://developers.google.com/search/docs/appearance/avoid-intrusive-interstitials?hl=es

###### Experimentación y verdad económica

Comparación no-popup/control vs newsletter/simple benefit vs juego, con asignación persistente, sesgo/atribución controlada y muestras suficientes. Métricas reales:

- Elegible, popup mostrado, cerrado, interacción iniciada, recompensa asignada y validada.
- Form submit vs consentimiento de marketing válido vs entrega real (sin confundir direcciones captadas con audiencia contactable).
- Tasa de canje, conversiones de PDP/checkout/purchase, AOV.
- **Beneficio de contribución incremental por sesión** neto de descuentos, COGS, fees, fulfilment, costes de envío y herramientas, junto con repetición de compra y coste de oportunidad.
- Fricción/abandono, señal de spam/unsubscribe, incidencias, Web Vitals y accesibilidad.
- No usar resultados anecdóticos del vídeo como prior causal.

##### Definition of Done & Production Reality Gate

- [ ] Discovery read-only de responsables reales: popup/CRM/Shopify Forms, theme renderer, discount system, analytics, experiments, consent/privacy, visual grammar y gobernanza.
- [ ] SGE puede proponer **no popup**; no produce un juego o incentivo ficticio por defecto.
- [ ] Para al menos dos arquetipos de tienda distintos se demuestra selección coherentede formato (no hardcode), incluidos escenarios single-SKU/no-asset/no-offer.
- [ ] Ejemplo de email capture funcional con consentimiento y supresión de visitantes ya suscritos; integración canónica real o bloqueo declarado.
- [ ] Modal no invasiva/cerrable, responsive, accesible y compatible con teclado, lectores de pantalla, touch, reduced motion y privacidad.
- [ ] Si se aprueba minijuego: lógica de premios real y resistente a recargas, concurso con términos/odds/requisitos verificados y descuento aplicable en checkout real. **Si no existe infraestructura/promoción permitida, no exigir implementación de juego como condición para entregar el resto del trabajo: declararlo bloqueado de forma explícita.**
- [ ] Sin 401 inesperado/CTA sin efecto/código inventado/doble premio/evento duplicado/pérdida de datos tras submit.
- [ ] Pruebas E2E en navegador y ambiente Shopify autorizado; inspección de experiencia móvil/escritorio con capturas, logs, assets y evidencia reproducible.
- [ ] Sin bloqueo SEO mediante intersticial al cargar en móvil, salvo razón legítima/excepción comprobada.
- [ ] Eventos de control, interacción y redención conectados al sistema de analítica; hipótesis, criterios económicos y guardrails documentados.
- [ ] Quality Gate de SGE distingue contrato renderizable de funcionalidad realmente observada. No da PASS 10/10 solamente porque existe una sección/modal.
- [ ] Fallos reales → Knowledge Vault y UKDL Hard Rules / Process Rules / Traps, con regla justificada y detector/fresh-agent test cuando corresponda.
- [ ] **Constitutive Baseline Ratchet:** promoción UNIVERSAL de principio comprobable «elementos interactivos prometidos deben estar conectados a efectos reales, los incentivos son verificables, el usuario puede rechazar»; gates específicos de popup solo para interfaces pertinentes. Demostrar enforcement/reproducción en un nuevo contexto.
- [ ] Cumplir Code Freeze, presupuesto, micro-commits, aprobación del plan inline y Production Reality Gate por done-gate conforme a protocolo del repositorio.

##### Ruta ROI

**M0 Discovery:** auditoría del stack, coste de proveedor vs desarrollo, selección de arquetipos y hipótesis económicas; distinguir referencia visual de funcionalidad demostrada.

**M1 Light Capture:** implementación más pequeña que produzca formulario real integrado, consent y experiencia coherente; demostrar con Shopify/entorno autorizado.

**M2 Interaction & Offers:** conectar variantes por preferencia e incentivos efectivos; si hay caso comercial sólido y condiciones viables, activar minijuego real sin fabricar aleatoriedad.

**M3 Visual/QA:** render snapshots, móvil+desktop, comportamiento de cierre, liveness, accesibilidad, control de errores, rendimiento.

**M4 Learning:** experimento controlado, dataset de resultados, conocimiento UKDL y gates heredables.

**Estado**: propuesta registrada, no producto desplegado. **Pregunta institucional**: ¿cuándo NO mostrar popup? Debe ser una salida válida del sistema, no un fallo.
---

##### CRO triage cross-reference — popup is not an automatic win (2026-10-26)

Jssiehcktt's video (~09–13s) subjectively ranks a **spin-to-win popup** below foundational conversion improvements (mobile speed, near-decision customer trust, shipping/returns clarity, second purchase). This is **not scientific ranking evidence**, but directly reinforces this issue's existing first-class **NO-POPUP** option and cost-benefit selection rule. SGE must evaluate real impact on engagement, interruption, mobile performance, contribution economics and conversion using its existing instrumentation.

Do not make gamification mandatory just because an external creator shows a visually polished popup. Relative priorities are handled by #4's CRO triage extension; credible second-purchase reward alternatives are tracked by [#9 Store Credit](https://github.com/jacobo07/TUA-X/issues/9). Keep this issue scoped to popup experience and legitimate consent/promo execution.


## TUA-X#7 -- SGE — Subscription Commerce & Retention Intelligence: 6 prácticas, selling plans reales y lifecycle verificado

State OPEN, created 2026-10-26, https://github.com/jacobo07/TUA-X/issues/7

#### SGE — Subscription Commerce & Retention Intelligence

##### Intención

Convertir las **seis prácticas de ecommerce por suscripción** demostradas en el vídeo del Owner (Wellcopymax) en una capacidad **reutilizable y coherente con la economía del negocio** de CommonWealth Ops. **SGE genera y orquesta la experiencia y su contrato de activación; no se convierte en un segundo proveedor de cobros, descuentos, emails ni contratos recurrentes.** Integrar la arquitectura existente de PDP, Offer Builder, CW Shrine, CXE, Shopify y P&L mediante los propietarios canónicos verificados.

Relacionados: #4 (estándar visual 10/10 + segunda versión PDP del vídeo de Molly), #5 (elección de ofertas auténticas y pricing transparente), #6 (popup 10/10 y ofertas coherentes). **El vídeo de Molly ya fue registrado en #4: no duplicar implementación ni otra especificación.**

###### Fuente y alcance de evidencia

Vídeo aportado por el Owner en conversación 2026-10-26: `wellcopymax_9cbedbe13ccf4b3386f7a7a72cb689cd.mp4`, 72,3 segundos (SHA-256 `aec6faf72d358a3cce99a480b193d99410b136b61c3b12166ef73e733f19d20b`). La grabación **no está adjuntada ni almacenada en el repositorio**. Referencias de pantalla extraídas durante revisión del vídeo, no de un sistema de checkout real accesible en el repo.

La fuente menciona «non-negotiables for ecommerce subscription brands» y presenta estas seis recomendaciones, que deben tratarse **como hipótesis comerciales hasta contrastar con datos propios**:

1. **~00:03–00:15 — Push subscription on the first order.** Presenta cohortes y afirma +50 % de LTV a seis meses y 2–3× a doce meses para quienes se suscriben en la primera compra. **No validado:** comprobar definición de cohorte, autoselección, CAC, margen, repeticiones reales, cohortes nuevas, rentabilidad y sesgos. No convertir las cifras del vídeo en constantes del motor.
2. **~00:15–00:26 — Front-load your discount.** Muestra contraste entre un descuento plano en cada envío y 30 % primer envío + 10 % siguientes; ejemplo de ARMRA con 30 % primer pedido y 5 % de recurrencia. Estos porcentajes son referencias visuales, NO una regla óptima universal. Modelar costes y elasticidad para decidir o rechazar descuentos.
3. **~00:27–00:30 — Auto-select subscription on the PDP and show the value.** Ejemplo de tarjeta «30-day supply» y «90-day supply» junto a «one-time purchase». **Desacuerdo deliberado con la recomendación literal:** no activar compromisos recurrentes subrepticiamente. Hacer la suscripción visible/destacada solo cuando sea coherente, con importe, frecuencia, descuento, condiciones y consentimiento explícitos y reversibles; por defecto evitar preselección que haga pasar desapercibido el cobro futuro. Verificar requisitos del país y proveedor.
4. **~00:30–00:43 — Align popup form with your best subscription offer.** Ejemplo de popup de greens con descuento de bienvenida, selector de necesidad y oferta de «autoship». Detecta conflicto de mensajes (10 % vs 40 %, por ejemplo). Crear una única fuente de verdad para promoción, elegibilidad y caducidad entre popup, PDP, checkout y lifecycle. Coordinar con #6. No es necesario popup si perjudica la UX.
5. **~00:43–00:51 — Educational email onboarding sequence.** Ejemplos de secuencias de bienvenida/educación para mejorar el uso real del producto antes de la próxima entrega. Integrar **solo** comunicaciones autorizadas, productos entregados y claims verificables. Diferenciar correo transaccional necesario de marketing, consentimiento y bajas.
6. **~00:51–00:69 — Customized billing reminder and order confirmation.** Ejemplos de recordatorio del pedido próximo, opciones de modificar/añadir/saltar y emails de confirmación más claros. La intención es reducir sorpresa y cancelación, NO **ocultar** el cargo. Mostrar explícitamente importe, fecha, recurrencia, productos, enlace genuino de gestión, cambio de pago, pausa/cancelación, estado del pedido y acción de soporte. No confundir aviso previo con confirmación de un cargo completado.

Últimos segundos (~00:70–00:72): promoción de un «$100M subscription brand playbook» del autor, no evidencia independiente de ninguna cifra.

##### Hallazgos canónicos del repositorio (read-only, main revisado 2026-10-26; revalidar antes de codificar)

- `tuax_core/engines/sge/offer_builder.py` ya produce una `subscription_offer` **para ciertos nichos**, pero es una **recomendación económica modelada**, no prueba de contrato de suscripción comprable ni activado en Shopify.
- `tuax_core/engines/sge/models.py`: `OfferStructure` y `StoreGenerationResult` existentes son los contratos a inspeccionar/extender, no duplicar.
- `tuax_core/theme/cw-shrine/sections/shrine-captura.liquid`: contiene variantes, cantidad, precio y ATC; **no se verificó vínculo real con selling plan** en esa sección. `CW Shrine` es overlay Dawn.
- `tuax_core/engines/cxe/flows.py`: propietario existente de algunos flows postcompra (review, cross-sell, soporte), pero no demuestra por sí solo un lifecycle de suscripción activado.
- `tuax_core/engines/cxe/ltv.py`: calculadora de LTV con retención estimada por heurística, **no observación de cohortes por suscripción a 6/12 meses**. No justificar descuentos con ese dato como si fuera un resultado causal.
- `tuax_core/engines/billing/dunning.py` y `tuax_core/api/welcome_email.py`: corresponden a **suscripciones del operador/tenant a CommonWealth Ops mediante Stripe**, no deben reutilizarse para enviar cargos o emails de los clientes ecommerce sin comprobar identidad y ownership. Evitar mezclar billing B2B del OS y subscriptions B2C de tiendas.
- `tuax_core/engines/experimentation/` existe: auditar si soporta experimentos de PDP/retención antes de ampliarlo.
- `AGENTS.md`: repositorio bajo **feature Code Freeze**, con requisito de telemetría/gates; esta issue es propuesta y no autorización a desplegar features.

##### Compatibilidad real con Shopify

La fuente de verdad de planes es el sistema real de **Shopify purchase options/selling plans o la app autorizada**. Shopify Subscriptions ofrece planes periódicos, descuentos, widget, notificaciones, y gestión de salto/pausa/cancelación y métodos de pago; verificar capacidades exactas de la versión/configuración del merchant:
- https://help.shopify.com/es/manual/products/purchase-options/subscriptions
- https://help.shopify.com/es/manual/products/purchase-options/subscriptions/shopify-subscriptions
- https://help.shopify.com/es/manual/products/purchase-options/subscriptions/shopify-subscriptions/setup

No crear contratos recurrentes solo mediante datos estáticos de theme ni falsificar descuentos. Determinar requisitos de permisos, elegibilidad de cada tienda, jurisdicción, checkout y apps de terceros **antes** de publicar un selector.

##### Arquitectura objetivo y límites

**SGE (compiler de tienda):** decidir si la recurrencia tiene sentido según necesidades reales de reposición/consumo, producto, fulfilment, capital, riesgos y márgenes. Compilar mensajes, diferencias de ofertas, diseño PDP, coherencia popup, requisitos de activos, manifest de activación, estados `NOT_CONFIGURED` / `READY` / `VERIFIED` y evidencia de Shopify sin duplicar el modelo canónico existente.

**Offer Builder / Pricing / P&L:** comparar primera compra y recompra por frecuencia, contribución neta, COGS, fees, shipping, descuentos, devoluciones, fallos de cobro, churn, cancelaciones, CAC y LTV observado. Aceptar `no subscription` si la economía o el uso del producto no la justifican.

**CW Shrine:** representar compra única vs planes **existentes** con importe primera compra, importe recurrente, frecuencia, variantes, stock, condiciones, próximas fechas cuando se conozcan y control claro de selección. Sin doble compra ni precios inconsistentes entre PDP, sticky-ATC, cart y checkout. Cumplir regla #4 de PDP premium contextual.

**Promotions/Popup (#6):** beneficio promocional consistente y canjeable en todas las superficies, sin apilar descuentos incompatibles ni supuestas rebajas sin verificación.

**CXE / Lifecycle owner:** orquestar onboarding educativo y comunicaciones por eventos reales (checkout contratado, fulfillment, próximo cobro, cobro completado, cambio de plan, pausa, cancelación). Idempotencia; tracking; opt-outs y consentimiento por finalidad, diferenciando mensajes transaccionales. No meter secuencias de email marketing en `StoreOrchestrator`.

**Shopify Subscriptions / commerce provider:** autoridad para suscripción, precio futuro, charge, renewal, payment method, cancel, skip, pause, selling plan y cliente. Shopify-provided capabilities tienen preferencia de TCO sobre reconstruir un subscription management engine.

**Evidence/Analytics/Experimentation:** cohorts reales con timestamps de first order/subscribe/cancel/renew, discount cohort, product usage signals autorizadas, ticket/churn/refund y profit per acquisition cohort. Todo uplift debe ser medido, no heredado del vídeo.

##### Guardrails comerciales, consentimiento y honestidad

- Selección de recurrencia **inequívoca**, términos visibles antes del cobro, compromiso no escondido, fácil cambio entre compra única/suscripción. No false-select ni trampas que den lugar a suscripciones inadvertidas.
- El precio futuro debe mostrarse antes de comprometer la compra (incluido cualquier aumento respecto del descuento de entrada). Renovaciones y cancelación accesibles sin técnicas de retención coercitiva.
- Emisión de emails/SMS bajo base de comunicación correcta y preferencias. No disfrazar mensajes promocionales de transaccionales ni eludir bajas.
- Las referencias de suplementos «uso/beneficio» exigen claims y hechos respaldados. El onboarding no puede prometer beneficios médicos inexistentes.
- No sobreoptimizar tasas de suscripción inicial sacrificando profit, devoluciones, confianza y retención.
- En mercados regulados, someter elecciones automáticas, promociones, términos de recurrencia y reminders a revisión de normativa y plataforma; no hacer afirmaciones legales universales sin evidencia jurisdiccional.

##### Acceptance / Production Reality Gates

- [ ] M0 Ownership/ROI audit: checkout billing B2B vs comprador B2C separados y probados; catálogo/test fixtures y capacidades existentes revisados.
- [ ] Caso positivo de subscription **real** mediante un selling plan autorizado, con SKU, cantidad, plan, precio inicial, precio recurrente, frecuencia, impuestos y recurrencia coherentes desde PDP→ATC→cart→checkout; casos negativos con no app, no API, no plan, stock inválido y cancelación.
- [ ] Si no existe un plan Shopify real, **no renderizar** tarjeta de suscripción como opción comprable; preview puede exhibir requisito no activado claramente.
- [ ] Usuario puede cambiar a compra única, revisar costes futuros y términos, y administrar/cancelar la suscripción en una ruta funcional. No inferir autorización por preselección visual.
- [ ] Si hay descuento escalonado, todas las iteraciones representan exactamente lo configurado en provider, incluyendo renovaciones, impuestos y códigos; los descuentos son financieramente viables antes de activarse.
- [ ] PDP, modal, email y checkout son coherentes: mismo plan, términos, descuento y elegibilidad. Popup nunca enseña una oferta que checkout rechaza.
- [ ] Tests de lifecycle educativo con primera entrega confirmada, reglas de consentimiento y supresión, manejo de rebotes, reenvíos, fallos de API y duplicados.
- [ ] Billing reminders antes de la renovación cuando corresponda y confirmaciones solo después del evento real; importes, fechas y enlaces verificados; baja/cancel/skip/pause sin rutas muertas.
- [ ] Test negativo de suspensión/cancelación: ninguna comunicación de «próximo envío» falsa ni cargos/CTA inexistentes después de cancelación.
- [ ] Métricas instrumentadas: adoption rate, retention 30/60/90d y cohortes 6/12mo cuando haya datos, AOV, contribution-LTV, CAC payback, churn voluntario/involuntario, refunds, cancel reason, true repeat purchase, coupon cost y deliverability. Si n insuficiente, verdict UNDETERMINED.
- [ ] Browser E2E en desktop/mobile y merchant dev Shopify autorizado, hooks/events reales o evidencias claras de qué no está accesible; mocks solo unitarios.
- [ ] Production Reality Gate en cada done-gate, con evidence/capturas/trace de orden transaccional; cero botones huérfanos, 401 inesperados ni cambios de precio silenciosos.
- [ ] Errores reales → Knowledge Vault + UKDL Hard Rules / Process Rules / Traps, pruebas de regresión y detección con consumo demostrable.
- [ ] **Constitutive Baseline Ratchet:** elevar como estándares universales/en dominio correcto: «una compra recurrente nunca se activa sin un consentimiento y coste futuro entendibles», «cada oferta mostrada debe ser comprable al precio anunciado», «un email transaccional afirma solo eventos realmente ocurridos», «los descuentos de entrada se evalúan con toda la economía del ciclo». Probar herencia fresh-agent y detectar una violación, no solo escribir documentación.
- [ ] Code Freeze, gates, telemetría, aprobación plan inline y micro-commits autorizados antes de merge/deploy.

##### Ruta de ejecución propuesta — ROI

**P0: Read-only architectural ownership and merchant capability audit**, con decisiones de adopción por ROI.
**P1: True subscription offer / purchase selection** para un caso real y uno `no subscription`, preservando consistencia ATC/cart/checkout.
**P2: Coordinated promotional offers** con #5 y #6; solamente descuentos realmente autorizados.
**P3: Post-purchase education and honest renewal communications**, integrados en CXE y proveedor real, no en un sistema de emails duplicado.
**P4: Browser/live-path proof, cohort measurement and experiments**, con gates de realidad.
**P5: UKDL & Constitutive Baseline Ratchet**, transferibilidad probada por un agente/contexto fresco.

**Estado inicial:** idea y especificación únicamente. El vídeo explica prácticas de marketing, no acredita resultados replicables ni demuestra infraestructura existente. Esta issue no modifica código, precios, campañas, planes, cobros ni emails.

**Regla de aceptación final:** SGE debe generar **negocios preparados para recurrencia**, no solo una etiqueta «Subscribe & Save» estéticamente convincente.
---

##### Retention extension — second-purchase priority & genuine store credit (2026-10-26)

In the user's fourth-video evidence batch, Jssiehcktt (~39–46 seconds; SHA-256 `ea50e2143c966950102196d037a9e10e59c8cab332b1186031804440d26336dd`) subjectively ranks **improving second-purchase conversion rate** in tier **S**. The ranking is an opinion, not a causal study, but adds a useful research hypothesis to the retention system already specified here.

Ty Chapman's ~28.6-second video (SHA-256 `05cba2ef45e386a37ff55ded13412f2b0d650a9e5f89c5565eb1713ea604e7e2`) demonstrates post-purchase promotional **store credit** examples, one requiring a real ledger/issuer. The complete dedicated contract lives at [#9](https://github.com/jacobo07/TUA-X/issues/9) and applies to non-subscription as well as subscription brands; **do not duplicate Store Credit logic here**.

Integration principles:
- CXE owns event-triggered second-purchase experiences; SGE compiles truthful storefront/offer prompts and setup, provider owns account credit, analytics/P&L owns measurable contribution. Preserve separation of **B2C customer rewards** from TUAX's **B2B platform Stripe billing**.
- Treat second purchase probability, reorder time, contribution margin by cohort, CAC payback, refunds, unspent reward liability and retention as economic metrics. A subscription is only one of several valid repeat-purchase mechanisms, not the universal answer.
- Compare **control / genuine subscription / non-recurring credit / discount** only when eligibility and sample justify it. Do not infer an S-grade ROI for every merchant from the video.
- Shopify's native Store Credit requires supported customer accounts, currency and scope. Do not infer credit automatically works for future recurring renewals; check the subscription app's capability and the customer's explicit authorization.
- No invented expiry/redeemability, hidden subscription auto-enrolment, or messaging after credit cancellation/spend. Track issue #9 Production Reality Gate as a separate conditional domain completion gate.

This extension strengthens the **second-purchase learning objective** without changing existing #7 owners or declaring lifecycle implementation done.

---

##### Cross-link 2026-10-27 — Site architecture and subscription surface (#10)

Maxtymosh's «20 pages for your e-commerce website» names subscriptions as one of 20 commerce experiences; the full intent-specific surface coverage is specified in [#10 — Commerce Site Architecture Intelligence](https://github.com/jacobo07/TUA-X/issues/10). **This issue (#7) remains authoritative** for recurring purchase/Shopify selling-plan truth, onboarding, renewal and lifecycle mechanics.

SGE's #10 should render subscription-specific content only for an eligible catalog/product with a provider-backed selling plan and visible recurrence terms; do not count an informational Shopify page as evidence of a live subscription contract. SGE site-coverage reporting distinguishes NOT_APPLICABLE from BLOCKED_EXTERNAL_DEPENDENCY and UNVERIFIED.


## TUA-X#8 -- SGE — Identity-Led Positioning & Transformation Intelligence (Georgie Lewis)

State OPEN, created 2026-10-26, https://github.com/jacobo07/TUA-X/issues/8

##### Goal / decision
Incorporate the **Georgie Lewis** video into SGE as **Identity-Led Positioning & Transformation Intelligence**. Treat the video as an *inspiration and testable theory*, **not** evidence that aspiration always yields pricing power or that every niche should switch from functional to identity-based marketing.

**No second brand engine.** Reuse existing Brand/Consumer/Positioning Intelligence, CIE/psychographics, SGE awareness-copy and CDIO, extending only missing contracts with clear ownership and source provenance.

###### Source inspected in this conversation
Owner-supplied `georgie_lewis___25e51641bfb346ed80a5add5acaf61e0.mp4` (~43.8 sec; SHA-256 `0ceeb0149c9a7d69e6e330e9c460d71f57310e2dba67b10b43c6d8f9a70694d2`). The source video is in the chat, **not attached to or hosted in this GitHub repo**.

**Video-evidenced ideas:**
- ~00–04s: creator asks why consumers accept some higher prices; contrasts different aspirational product categories. This is a hypothesis, not a controlled experiment.
- ~09–19s: brand contrast (Lululemon as status/identity example): discount-led «gym leggings 30% off this weekend» versus identity-led message «for the women who want to be the strongest version of themselves». The second is her preferred positioning; **not a factual guarantee**.
- ~30s screenshot: explicit **three-step source framework**:
  1. *Work out what you're actually selling* — function-first utility/wallet vs identity-first aspiration/ego; identify which purchase motivation dominates.
  2. *Map your customer's ideal self* — what they aim to become, admired identities/creators/language/brands and the gap between current/desired identity.
  3. *Position your product as the transformation* — move from features to belonging, belief and transformation when relevant; use identity-aware visuals/copy, rather than claiming any price is warranted.
- ~35–43s: author's contention that simple products can command more because of the future self being promised, not price-led competition. **Outcome unverified and conditional.**

###### Existing repo seams (main read-only audit, 2026-10-26; recheck live HEAD)
- `tuax_core/engines/sge/awareness_copy.py`: awareness archetypes, stable variant selection, optional `mechanism` and `ideal_customer`/avatar, and an existing **identity-first cross-angle**. This is the FIRST owner to inspect, not a reason to invent another copy engine.
- `tuax_core/knowledge/vault/copy_frameworks.yaml` and `awareness_pyramid.yaml`: candidate reusable canon. Verify provenance and live consumers.
- `tuax_core/engines/cie/` includes consumer/creative intelligence; `tuax_core/engines/bce/` is **not automatically a brand positioning system** merely because its acronym is BCE — inspect actual ownership.
- `tuax_core/engines/sge/sections.py`: design_intent and Shopify/CW Shrine section compiler.
- Parent **#4** governs premium visual experience; sibling **#5** governs authentic offer choice and price truth.

###### Acceptance intent
SGE must choose between function-first, identity-first, or blended positioning **based on evidence and context**:

1. **Customer identity research contract**: source-supported current and desired states, authentic language, communities and admired reference contexts with confidence/provenance; separate quotes/observations from marketer inference.
2. **Value bridge**: map an actual product attribute/service to a defensible customer benefit and only then to an aspirational association; never imply a product guarantees a transformed identity/mental state/fitness or social status.
3. **Brand expression**: consistent hero, PDP, imagery briefs, offer framing, creative angles and microcopy rooted in the same positioning; diversity tests avoid everyone looking like the same «aspirational» generic boutique.
4. **Function-first fallback**: low-evidence/utility/regulated/high-stakes contexts stay product-truth-first; preserve accurate specifications, price, warranties, fit, ingredients, limitations and comparisons.
5. **Claims/compliance**: aspirational marketing cannot conceal product limitations, use stigmatizing insecurities as an implicit promise, invent testimonials or imply health outcomes unsupported by the product. Avoid copying visual trademarks and source assets.
6. **Economic validation**: compare functional vs identity vs blended only with adequate randomized tests/credible data; primary incremental **contribution profit per eligible session**, plus conversion, returns, complaints, trust and repeat purchases. Pricing power is **not presumed** merely because the narrative sounds better.
7. **Commercial proof**: visual mock/demo without grounded product assets or a customer-facing render is **not** a completed brand/store.
8. **Provenance/compounding**: save creative hypothesis + context + rejected versions + results to existing registries/knowledge graph, promoting only supported general principles.
9. **Storefront/visual QA**: inspect real mobile/desktop render of image, headline, benefits and offer; no conflict between identity promise and checkout reality.

###### DONE / Production Reality Gates
- [ ] Map actual owner chain brand/consumer→SGE copy→CW Shrine→real rendered store, with no parallel sources of truth.
- [ ] Demonstrate 2 contrasting product cases: aspirational/identity-fitting and purely utilitarian. Both pass product-truth, and the second is not forced into «self transformation».
- [ ] Store hero, PDP, creative instructions and offer agree semantically and accurately with supplied product/customer evidence.
- [ ] No invented customer research, uplift, celebrity endorsement or transformation outcome.
- [ ] Observe real browser flow and assets, not only templates/JSON/unit tests; respect 10/10 rendering #4.
- [ ] A/B evidence claims bounded by sample/assignment/analysis. If no outcome data → `UNDETERMINED`, not revenue uplift.
- [ ] Actual failures are captured with RCA, regression proof, Knowledge Vault → UKDL Hard Rules/Process Rules/Traps through canonical promotion; Constitutive Baseline Ratchet gets only **domain-appropriate** reusable invariant: claims and design messages trace to real customer/product evidence.
- [ ] Respect TUAX `AGENTS.md` Code Freeze/telemetry approval. **Issue only; no feature implementation has been authorized by this issue.**

###### ROI plan
P0 map existing identity/consumer/copy ownership and baseline; P1 minimal source-backed positioning contract; P2 compose through current SGE & CDIO (no redundant modules); P3 browser/claims QA; P4 controlled economic experiment and reusable validated learning.

**Decision rule:** premium position is a competitive strategy, **not** permission to charge arbitrary prices.

## TUA-X#9 -- SGE — Store Credit Rewards & Repeat-Purchase Intelligence (Ty Chapman)

State OPEN, created 2026-10-26, https://github.com/jacobo07/TUA-X/issues/9

##### Goal
Add to SGE a **Store Credit Rewards & Repeat-Purchase Journey** capability based on Ty Chapman’s video. The job is to make a *genuine, spendable customer credit* part of a profitable, trustworthy post-purchase journey — **not** a static «you earned £45» badge, an invented voucher, a disguised discount or a second ledger.

**Architectural boundary:** SGE can recommend/compose offer and customer experience; Shopify-native Store Credit/authorized provider owns credit balances and redemption; CXE owns event-driven lifecycle; financial ledger/P&L owns the liability, reward cost and margin; experiment system owns causal claims. First discover actual runtime owners, store/tenant capabilities and app contracts.

###### Video evidence, not proof of effectiveness
Source: owner-uploaded `tychapman_sell_more_ecom_6fc346aabe264b2a91c0e09c7fa915db.mp4` (~28.6 s), SHA-256 `05cba2ef45e386a37ff55ded13412f2b0d650a9e5f89c5565eb1713ea604e7e2`. **Chat attachment only, not committed to GitHub.**

- ~00–07: example post-order confirmation «You’ve earned £45 credits for your next order», using a customer example (no real merchant authentication/transaction established by the video).
- ~08–13: example email announces a monetary-looking «Squish Cash» reward and a deadline; business recommendation is a reminder before expiry.
- ~14–20: creator invokes loss aversion and re-spending rationale; these are *persuasive claims, not an A/B measured causal effect*.
- ~20–28: shows the Shopify App Store listing **Redeemly Store Credit Rewards** as one possible vendor. The video **does not prove** integration is working, feature availability, app cost, Merchant eligibility, or incremental profit.

###### Up-to-date Shopify contracts to verify at implementation
Official source (reviewed 2026-10-26): https://help.shopify.com/es/manual/customers/store-credit
Admin API example: https://shopify.dev/docs/api/admin-graphql/2026-01/mutations/storeCreditAccountCredit

Shopify supports store credit as a native payment method for signed-in **new customer accounts** (not legacy customer accounts) or Shop Pay. Store credit is currency-specific. Expiry can be assigned per issuance; local consumer-law checks are required. Redemption, legacy-account/channel restrictions, inability to select a partial amount, fee implications for some shops, subscription-renewal limitations, permission scopes and issuer idempotency must be revalidated for the merchant's live API/version/plan. `storeCreditAccountCredit` requires `write_store_credit_account_transactions` scope; do not invoke without granted permissions.

Native functionality may be sufficient; only use a third-party app if its real cost/capability gap is justified. **Do not implement a private money ledger as a replacement for Shopify's customer credit balance.**

###### Scope and connected issues
- **#7:** Subscription Commerce & Retention Intelligence; this issue provides the separate opt-in credit/reward capability and tracks *second purchase* economics. Store credit on recurring invoices only if the subscription app supports and customer authorizes it.
- **#6:** Popup campaign offer consistency; never promise credit in a popup that post-purchase/checkout cannot honor.
- **#5:** authentic choices and pricing; credit and nominal discount must be distinguished and visible.
- **#4:** premium PDP: show relevant credit balance/earnings only when real, without banners that misrepresent cash equivalence or block checkout.
- **#8:** identity/value message is optional and cannot overrule liability/terms truth.

###### Behavioral contract (minimum viable positive scope)
1. **Eligibility/campaign**: only target markets/brands with supported customer accounts, actual granted scope, currency, authorized reward budget, viable redemption conditions, legal/merchant review, and positive expected contribution. **No-credit** is a first-class outcome.
2. **Earn:** on eligible verified order event, apply reward according to published terms and *issuer idempotency*; durable audit/provenance linked to order, customer, currency, policy version and issue transaction. Reject duplicate webhook/retries. Consider returns/cancellations/reversals and liability accounting; no promise until credit actually issued.
3. **Experience:** real post-checkout confirmation and/or customer-account balance (not an invented number). Clearly indicate «store credit for a future eligible purchase», exact currency/amount, restrictions, expiration or none, and how to redeem. Do not call it cash. If issued later after eligibility check, distinguish `PENDING` from `ISSUED`.
4. **Communication:** event-triggered email/SMS only under the appropriate legal/consent basis; show real balance and expiry, link to existing customer account and products. Suppress after redemption, cancellation or opt-out; transactional vs marketing messages separated. No artificial urgency, misleading «today only», silent suppression of rights.
5. **Redeem:** verify customer can actually log in and apply native credit to a checkout; reconcile remaining balance and transaction records. Respect Shopify's application limitations, subscription incompatibilities and multi-currency handling.
6. **Commercial model:** first-time discount vs store-credit reward vs no incentive; compare *incremental* contribution per acquired cohort and 2nd-purchase probability, repeat AOV, redemption, promotion liability outstanding, breakage, acquired customer payback, returns, support tickets, and provider/processing fees. **Unredeemed credit is not automatically free profit**; avoid encouraging deceptively short expiry.
7. **Provider strategy:** prefer Shopify first-party native credit. Consider Redeemly **only after** merchant permission/feature/cost comparison, privacy/contract/API due diligence and lifetime TCO case.
8. **Segmentation:** account state and redemption eligibility, not surveillance or hidden pricing. Surface only with actual evidence.

###### Real-world failure cases / must-pass gates
- [ ] Case with native credit *enabled and authorized* and valid merchant customer account; provider and permission preflight.
- [ ] Unsupported legacy account / absent API scope / unsupported channel/currency → deterministic non-credit experience and explicit setup requirement, **not a fake earning event**.
- [ ] Same order event delivered twice → exactly one credit transaction; audit trail reconciles with provider, with retry/resume behavior after partial failure.
- [ ] Order cancelled/refunded/returned → campaign-specific reversal and safe reconciliation; ensure consumer statutory cash refund rights are not silently converted to credit.
- [ ] Actual balance before/after credit issue and redemption visible and consistent across native customer account and checkout; no double spend and no fabricated spendability.
- [ ] Expiry calculation is timezone/legal/eligibility correct and message dates are synchronized with actual issuer record. Never auto-apply expired or unsupported credit.
- [ ] Email suppression on spent balance and preference change, no unconsented marketing messages; links work and do not leak customer balance.
- [ ] Capture genuine checkout/browser evidence on authorized test merchant, or mark `PRODUCTION_REALITY_UNVERIFIED` with precise external blocker rather than declaring end-to-end DONE.
- [ ] Experiment comparison has randomization and metrics; no unverified «massive LTV increase» or claims of monetary cash equivalence.
- [ ] Existing customer/financial systems used without B2B operator-billing contamination; no new parallel ledger.
- [ ] Code Freeze/telemetry gate from TUAX `AGENTS.md` followed. No code changes in issue intake.
- [ ] Failures receive RCA, regression tests and Knowledge Vault → UKDL Hard Rules / Process Rules / Traps where genuinely generalizable. Constitutive Baseline Ratchet candidate: **«A promised financial incentive must have a genuine, reconcilable economic source and a redeemable customer path»**. Apply as a domain-specific rule (financial incentive) with a negative test and fresh-agent consumer, not as blanket requirement for unrelated software.

###### ROI sequence
**P0 read-only:** identify Shopify/store-credit/CXE/P&L/offer-provider ownership, policy and available test merchant.
**P1 simplest actual earn→account→redeem proof** using native Shopify where possible, with idempotency + reconciliation.
**P2 communication + responsible expiries** only when product economics and consent justify it.
**P3 UX integration** into SGE-generated PDP/confirmation and tests; avoid noisy popups.
**P4 experiment/financial truth** (control, discount, store-credit reward) measuring realized contribution and retention.
**P5 governance ratchet** with verified counterexamples, knowledge distillation and read-path.

**State:** SPEC PROPOSAL, NO LIVE CREDIT ISSUED, NO APP INSTALLED, NO FINANCIAL BENEFIT MEASURED.

##### Explicit Production Reality Gate and Baseline promotion boundary

**Every done-gate requires Production Reality Gate evidence**, not only static code, unit tests, claimed app settings or an email screenshot. The minimum meaningful end-to-end proof is: *a real eligible purchase event → exactly one authorized native/provider credit issuance → reconciled customer account balance → actual customer sign-in → eligible subsequent checkout applying valid credit → ledger/liability and actual remaining balance reconciled*. Reproduce idempotency on webhook retry, a returned purchase, multi-currency mismatch, expired credit, loss of permissions, unsupported legacy account and opt-out. If a merchant substrate is unavailable, mark the relevant step `BLOCKED_EXTERNAL_DEPENDENCY` or `PRODUCTION_REALITY_UNVERIFIED`, never `COMPLETE`.

Only real observed failures produce hard-rule/trap promotion to the canonical UKDL. A proposed new Constitutive Baseline must prove it is *read and enforced* by a fresh agent and a failing test against a deliberately broken incentive, with scope limited to reward/financial-incentive software. Respect the TUAX Feature Code Freeze and authorized plan/micro-commit workflow.


## TUA-X#10 -- SGE — Commerce Site Architecture Intelligence: catálogo condicional de 20 experiencias (Maxtymosh)

State OPEN, created 2026-10-27, https://github.com/jacobo07/TUA-X/issues/10

#### SGE — Commerce Site Architecture & Page Coverage Intelligence

##### Decisión del Owner

Incorporar al SGE los **20 tipos de experiencia ecommerce** enumerados en el vídeo de Maxtymosh. La capacidad nueva NO es «crear 20 páginas siempre», sino **compilar una arquitectura comercial completa, pertinente, navegable y verificable**, justificando por qué cada experiencia es REQUERIDA, CONDICIONAL, NO APLICABLE o BLOQUEADA POR DATOS/PROVEEDOR.

**Regla:** negocios > tiendas; sistema de decisión sobre arquitectura de información > colección de 20 plantillas; económica y operativamente viable > aparente completitud por volumen.

**Frontera de ownership:** SGE planea y compone las experiencias; CW Shrine/Dawn renderiza las páginas/secciones Shopify editables; las fuentes existentes de productos, marcas, SKU, inventario, envío, garantías, documentos, reseñas, medios, geolocalizaciones y customer accounts aportan hechos; CXE gestiona posventa; Shopify/proveedores autorizados gestionan pedidos, contratos de venta, cobros, tracking y redención. Buscar propietarios efectivos antes de implementar. No construir un segundo CMS, otro order-tracking backend, otro subscription processor ni un segundo quality scorer.

###### Fuente inspeccionada

- Archivo aportado por el Owner en la conversación: maxtymosh_3e6a7ed3972943d190589714cfc3d342.mp4.
- Duración: **33,44 s**. Resolución 1280×720 (vídeo vertical embebido en frame). SHA-256: **2e47d600c95d1dad72a563cf80c69d581c50fc5d23c6848d33b216a8e9cfff43**.
- El vídeo **no está incorporado al repositorio**; texto legible y ejemplos se inspeccionaron en fotogramas del archivo adjunto en esta conversación.
- Título observado del vídeo: «20 pages for your e-commerce website».
- El vídeo muestra capturas ilustrativas de tiendas y enumera los 20 elementos. **No demuestra** la funcionalidad real de cada web, ni que 20 páginas sean imprescindibles, ni cifras de tráfico, conversiones o ROI. No copiar sitios, marcas, textos ni imágenes de sus ejemplos sin licencia.

##### Inventario exacto de la fuente y decisión de activación

**Grupo A — Catálogo, selección y aprendizaje**

| # | Rótulo textual del vídeo | Representación posible (solo cuando aplica) | Evidencia / condición de activación |
|---|---|---|---|
| 1 | Product detail pages | PDP/plantilla product, variantes y CTA | Producto real, medios autorizados, precio, SKU, stock y ruta de checkout |
| 2 | Product categories | Collection/list-collections, PLP y navegación | Taxonomía real de catálogo; no colecciones ficticias en single-SKU |
| 3 | Shop by use | Colecciones filtradas, landing por caso de uso, facetas | Casos de uso observables y asignación producto→uso respaldada |
| 4 | Shop by brand | Índice de fabricantes/marcas y colecciones por marca | Catálogo realmente multimarca; NO aplicable por defecto en DTC monomarca |
| 5 | Product comparisons | Comparador PDP/colección/guía con diferencias reales | Productos comparables, atributos normalizados, datos verificables, actualización |
| 6 | Buying guides | Artículo/página de guía editorial, navegación contextual | Decisión compleja e información contrastada, no SEO thin content |
| 7 | Size & fit guides | Guía de tallas y prueba de ajuste por producto/categoría | Datos de tamaño/fit específicos, unidad/corte/versiones; no talla inventada |
| 8 | Compatibility guides | Tabla/buscador de compatibilidad e instrucciones | Catálogo de dispositivos/modelos, reglas de compatibilidad verificables y versionadas |
| 9 | Bundle pages | PDP/landing de pack o colección de kits | Bundle REAL con inventario de componentes, precio y checkout consistente |
| 10 | Subscriptions | Elección de plan y guía de compra recurrente | Shopify selling plans/comercio recurrente autorizado; ver #7, nunca pseudo-suscripción |

**Grupo B — Confianza, soporte y ciclo de vida**

| # | Rótulo textual del vídeo | Representación posible (solo cuando aplica) | Evidencia / condición de activación |
|---|---|---|---|
| 11 | Customer photos | Galería UGC en PDP/reviews/landing | Consentimiento/derechos de las imágenes y relación real con producto |
| 12 | Verified reviews | Módulo de reseñas verificadas, filtros, página de reseñas opcional | Procedencia de opinión, verificación de compra cuando se afirme, moderación honesta |
| 13 | Shipping & delivery | Página/FAQ de envíos y promesas contextualizadas en PDP | Políticas reales por país/carrier, costes, cutoff, ETA/holiday handling |
| 14 | Returns & exchanges | Página/flujo real de devoluciones/cambios | Política mercantil vigente y derechos legales, dirección/portal/acciones reales |
| 15 | Warranty coverage | Página de garantía, consulta por SKU, registro si procede | Cobertura, duración, exclusiones, flujo de reclamación y derechos legales verdaderos |
| 16 | Order tracking | Portal/estado del pedido, preferentemente proveedor nativo | Shopify order status/customer accounts/fulfilment autorizados, acceso protegido y estado veraz |
| 17 | Product setup guides | Artículo/manual/vídeo de instalación/puesta en marcha | Producto necesita montaje/uso; manual correcto por versión y medios licenciados |
| 18 | Replacement parts | Colección/PDP de recambios y compatibilidades | Recambios reales en stock o solicitables; no enlaces a piezas inexistentes |
| 19 | Gift finder | Selector guiado, gift collections, recomendaciones | Inventario disponible, criterio transparente, preferencias opcionales y recomendaciones comprables |
| 20 | Store locator | Localizador/landing de puntos físicos | Establecimientos físicos reales con direcciones verificadas, horarios/cobertura e información geográfica pertinente |

**Observación crucial:** 20 conceptos comerciales ≠ 20 tipos distintos de plantilla técnica. En Shopify, parte corresponde a product/collection/page/article/blog y otras funcionalidades corresponden a secciones, metaobjects, native account/checkout, páginas de política o aplicaciones/servicios externos. El SGE debe escoger la implementación soportada con menor coste total, no fabricar rutas por cumplir el número.

###### Ejemplos de pantalla de la fuente (visual only)

- ~02–04s: categorías y «Shop by Activity» con imágenes por uso.
- ~06s: índice «Shop by Brand» en formato de directorio.
- ~08–10s: comparador de productos y contenido de guía.
- ~12–14s: Size Chart y compatibilidad por modelo.
- ~16s: productos/paquetes agrupados.
- ~18s: lista de reseñas.
- ~20–24s: Shipping, Returns y Warranty.
- ~26s: Track your order con entrada de número + identificador.
- ~28s: Video Guides / Getting started.
- ~30s: piezas/repuestos.
- ~32s: Store locator con campo de ciudad/código postal y mapa.

No se declara funcionamiento de estos ejemplos; son capturas.

##### Evidence / Estado actual de TUAX (inspección read-only 2026-10-27)

- tuax_core/engines/sge/models.py: StoreGenerationResult contiene homepage_sections y pdp_sections, **no un plan de cobertura de otras superficies**.
- tuax_core/engines/sge/sections.py: render_os2_templates y render_shrine_templates solo generan templates/index.json y templates/product.json. No concluyas que Dawn carece de otras plantillas: sí puede traerlas de base; el gap es que **SGE no compila ni verifica su personalización/actividad end-to-end**.
- tuax_core/theme/cw-shrine/README.md: overlay sobre Dawn; componentes propios para Home y PDP, no un compilador completo de navegación/soporte/educación/lifecycle.
- tuax_core/api/onboarding_exec_router.py: camino _maybe_write_theme requiere write_themes y el ZIP; crea tema unpublished, escribe overlay y finalmente invoca publish_theme. **Publicar tema nuevo CAMBIA cuál es el tema live**, aunque no mutara los archivos del tema anterior. NUNCA tratar la frase «clobber-safe» como autorización de activación automática; separar build/preview/approval/live activation.
- tuax_core/integrations/shopify.py: cliente usa la ruta de versión Admin API 2024-01 y REST Theme/Asset. Shopify publica versiones trimestrales y la 2024-01 está fuera de su ventana habitual de soporte en 2026; comprobar los headers y la versión real de respuesta, compatibilidad y permisos antes de ampliar el deploy. REST es legacy y themeFilesUpsert en GraphQL requiere, además del scope, **exención para modificar theme files**. No migrar a ciegas ni asumir que write_themes basta.
- AGENTS.md establece Feature Code Freeze, telemetría y validaciones de cambio: idea/especificación va a issue, no a PR/merge de funcionalidades sin procedimiento autorizado.

**Fuentes oficiales verificables en plan de implementación** (revalidar versión vigente antes del cambio):
- Shopify theme template types: https://shopify.dev/docs/storefronts/themes/architecture/templates
- Theme composition: https://shopify.dev/docs/storefronts/themes/architecture
- Shopify order status: https://help.shopify.com/es/manual/fulfillment/setup/order-status-page
- Shopify API versioning: https://shopify.dev/docs/api/usage/versioning
- Theme files permissions: https://shopify.dev/docs/api/admin-graphql/latest/mutations/themeFilesUpsert
- Legacy Theme/Asset: https://shopify.dev/docs/api/admin-rest/latest/resources/asset

##### Propuesta: Site Experience Coverage Contract (extensión, no nuevo duplicado)

SGE debe emitir, a través de los modelos/registries canónicos que ya existan, un **plan auditable de cobertura de experiencias** por tienda, con una fila por cada una de las 20 capacidades y por los elementos esenciales que el vídeo omite (accesibilidad, navegación, carrito, contacto, búsqueda, políticas legales y estados vacíos/error).

**Por cada capacidad:**
- ID/taxonomía, objetivo del visitante, impacto económico esperado y clase de página/sección/servicio.
- Estado requerido: REQUIRED / RECOMMENDED / NOT_APPLICABLE / BLOCKED_EXTERNAL_DEPENDENCY / PRODUCTION_REALITY_UNVERIFIED / VERIFIED (adaptar enums al vocabulario canónico actual; no duplicarlos).
- Evidencia de aplicabilidad: catálogo real, atributos, SKU, marcas, medios, políticas del operador, fulfilment, ubicación física, compatibilidad, rights, proveedor.
- Fuente de verdad + propietario + consumidor real.
- Ruta/canonical/jerarquía de navegación y enlaces de ida/vuelta, SEO/GEO y estrategia de indexación.
- Activos y copy sólo cuando tengan fundamento (no generar tiendas fantasmas).
- Dependencias, permisos y acciones manuales específicas del operador.
- Coste de creación/mantenimiento y razón comercial de inclusión/exclusión.
- Done-gate y prueba de recorrido real.

El plan puede generar 1 PDP y 2 superficies adicionales o docenas de rutas dependiendo del catálogo, **pero todas las 20 capacidades deben quedar decididas, no ignoradas silenciosamente**. Cubrir un concepto mediante una sección válida evita forzar una página separada o duplicar contenido.

##### Reutilización y dependencias inter-issue

- **#4: Premium Visual 10/10, PLP y render QA** es el propietario de experiencia visual y de las secciones de catálogo; este issue amplía la **cobertura de superficies y navegación**. No crear otro CDIO/theme/design engine.
- **#5: Preference-Based Offer Architecture y Transaction Truth** es propietario de bundles/choice/price truth; en #10 sólo compilar navegación/pages que consuman ofertas existentes.
- **#6: Popup Experience** es opcional: que haya 20 superficies no obliga a introducir popups.
- **#7: Subscription Commerce & Retention** gobierna selling plans y posventa recurrente; no reinventar cobro en SGE.
- **#8: Identity-Led Positioning** alinea el lenguaje y navegación por uso con marcas/consumidores cuando hay evidencia.
- **#9: Store Credit** gobierna créditos de recompra; no meter saldo financiero en navegación/páginas por defecto.
- **CXE/Support/Shopify customer accounts** son dueños de estados transaccionales privados, envío, tracking, RMA/returns, soporte y notificaciones. Si alguno no está construido, declarar dependencia y no aparentar completitud.
- **Product/Media Truth, UGC/Creative, Knowledge Vault, registries, GEO/AEO/SEO, Analytics/Experimentation** suministran los datos y evaluación; auditar existencia real y liveness, no asumir.

##### Activación por arquetipo de operador / negocio

El compilador debe probar, al menos, cinco casos semánticamente distintos:

1. **Single-SKU DTC sin ubicaciones físicas**: PDP y políticas/contacto/transporte razonables; no Shop by Brand, recambios, locator o directorios vacíos.
2. **Multibrand retailer**: Brand Index, categorías, búsquedas/filtrado reales y comparadores cuando hay atributos comparables.
3. **Ropa/tallas**: guías Size & Fit basadas en dimensiones y variantes, returns clarificados y producto con fotos licenciadas.
4. **Electrónica/equipos**: compatibilidad y replacement parts condicionados a modelo real; setup guide correctamente versionada; warranty veraz.
5. **Producto recurrente / tienda híbrida online-offline**: selling plan real si existe, y store locator sólo si hay puntos físicos. Un producto no recurrente sin plan permanece no-subscription.

El sistema debe distinguir «no aplicable» de «relevante pero faltan datos», y no intentar ocultar un bloqueo como N/A para elevar score.

##### Quality Gates — la cobertura real de la tienda

###### Gate C1 — Applicability & truth
- [ ] Las 20 capacidades están clasificadas con razón específica y evidencias de disponibilidad y necesidad.
- [ ] No quedan páginas sin producto/datos, testimonios inventados, comparación falsa, guía genérica de bajo valor, instrucciones de instalación incorrectas o uso ficticio.
- [ ] Reglas por país, moneda, idioma, tipos de cliente, accesibilidad y derechos de consumidor se aplican donde corresponda; no generar condiciones legales no aprobadas.
- [ ] Un cambio de inventario, precio, compatibilidad, política, horario o selling plan invalida/regenera las superficies afectadas (sin datos obsoletos).

###### Gate C2 — Publication & architecture
- [ ] Cada ruta activa existe, responde y está accesible desde navegación/contexto que la necesita; no dead links, 404, redirecciones cíclicas ni rutas sin consumidor.
- [ ] Shopify OS 2.0 templates/sections/page resources y editor están correctamente conectados y son editables por el operador cuando aplica.
- [ ] Preview en tema unpublished validado; cambio a tema main **requiere autorización real**, con rollback y comparación, nunca asumir que no cambia producción.
- [ ] Compatibilidad probada con API vigente/permiso real y sin reintentos side-effecting duplicados. API antigua y protected theme write se auditan antes de feature rollout.

###### Gate C3 — Customer action/reality
- [ ] Categorías, compra por uso/marca, comparador, recomendaciones y búsquedas muestran resultados correctos y actualizados.
- [ ] PDP/bundle/subscription dirigen al producto/variante/plan realmente comprables al precio mostrado.
- [ ] Customer reviews/photos son verificadas o se omiten; la ausencia de reseñas no es un error en sí.
- [ ] Shipping, returns, warranty y delivery settings tienen propietario aprobado y no prometen términos que el comercio no cumple.
- [ ] Order tracking usa servicio real, controla acceso a datos de cliente y reproduce estados correctos (no lookup inseguro que revela dirección/email/pedido).
- [ ] Setup guides, recambios y compatibilidad usan SKU/modelo/versiones reales.
- [ ] Gift Finder sólo propone regalos en stock y adecuados al criterio declarado; store locator sólo muestra establecimientos reales.

###### Gate C4 — Experience quality
- [ ] Browser E2E recorre la topología completa, incluyendo navegación y enlaces contextuales, tanto móvil como escritorio.
- [ ] Accesibilidad, teclado/touch, velocidad, SEO/GEO (canonical/indexado correcto, ausencia de páginas thin, duplicadas o huérfanas), privacidad, errores y ausencia de botones muertos verificados.
- [ ] Métricas de operación relevantes según superficie: product discovery, comparación→PDP, CTA, soporte deflection, RMA, tracking self-service, 2nd purchase, profit per session, mantenimiento y coste de cambio. **Ninguna mejora causal sin experimento válido**.

###### Gate C5 — Institutional compounding
- [ ] Production Reality Gate en CADA done-gate; éxito sólo con evidencia real de la ruta, consumidor, efecto y datos correctos; mocks unitarios son insuficientes para producción.
- [ ] Errores reales: RCA + evidence + regression test + Knowledge Vault + patrón UKDL Hard Rules / Process Rules / Traps mediante los propietarios canónicos y su proceso de promoción.
- [ ] Constitutive Baseline Ratchet: considerar un principio general **«cada capacidad declarada en la experiencia del usuario debe tener ruta alcanzable, datos suficientes, consumidor y resultado observable; la ausencia pertinente nunca se oculta»**, con enforcement/fresh-agent test; la taxonomía específica de 20 experiencias pertenece al estándar ecommerce, **NO** a todo software del mundo.
- [ ] Las capacidades se mantienen coherentes ante datos tardíos, error de proveedor, cambio de versión Shopify, nuevos marketplaces, variantes de catálogo y locales.
- [ ] Respeta el Feature Code Freeze de AGENTS.md: para implementación, evidencia, telemetría, autorización, plan inline, micro-commits y aprobación de condiciones de gobernanza.

##### Plan por ROI: delivery sin feature explosion

**P0 — Discovery/read-only y Reality Scan.** Verificar rutas reales, arquitectura y fuentes; medir qué capacidades están vivas, simuladas o no implementadas. Preflight API Shopify 2024-01 y mecanismo de publicación; proteger producción.

**P1 — Site Coverage Decision, sin crear 20 páginas vacías.** Extender el contrato canónico con aplicabilidad, propietarios, enlaces y reasons; reportar lo que ya funciona y lo que requiere datos/permiso. Probar casos single-SKU y multi-SKU.

**P2 — Navegación/PLP/guías de mayor valor.** Elegir primeras superficies por demanda real, intentos de búsqueda, dudas de clientes, fricción y coste marginal; partir de Dawn+CW Shrine y #4 en lugar de clonar.

**P3 — Soporte transaccional real.** Activar envío/devoluciones/garantías/tracking y flujos de ayuda en el proveedor/cuentas que corresponda; si faltan permisos, no inventar portal.

**P4 — Funcionalidades condicionadas.** Comparador, tallas, compatibilidad, recambios, finder o localizador si hay datos y ROI suficientes. Bundles y suscripciones via #5/#7.

**P5 — Browser full-site crawl / adversarial QA / observabilidad.** Verificar cada ruta ofrecida y casos negativos; detectar 404, contenido desactualizado, rutas inaccesibles, llamadas de proveedor erróneas o leak de datos.

**P6 — UKDL y Constitutive Baseline Ratchet.** Promocionar sólo invariantes demostrados; verificar que el próximo agente/proyecto puede leer y aplicar el estándar con pruebas negativas.

**Resultado exigido:** «una tienda completa» ya no significa sólo homepage + PDP ni «exactamente 20 URLs». Significa que SGE puede justificar y materializar **todas las superficies que el negocio necesita**, y demostrar su funcionamiento, relevancia, integridad y mantenimiento.

**STATUS: SPECIFICATION ONLY / NO RUNTIME CODE / NO DEPLOY.** Este issue registra requisitos y gates. No altera productos, datos privados, cuentas, Shopify, temas live ni garantías del merchant.


## claude-power-pack#5 -- Epic: Global Goal Fabric & Actorless Zero-Resident Autonomy

State OPEN, created 2026-10-10, https://github.com/jacobo07/claude-power-pack/issues/5

##### Intent

Make unattended autonomy scale with **durable semantic goals, not resident model processes**. The terminal architecture is an event-driven institutional runtime where mastered work executes deterministically and models are sparse, disposable cognitive coprocessors invoked only for irreducible novelty or necessary assurance.

This epic is deliberately global. It must extend/merge canonical CPP owners rather than create another parallel OS.

##### Constitutional laws

- Autonomy scales with durable goals, not resident model processes.
- Mission cost scales with irreducible semantic change, not wall-clock duration.
- A live goal does not require a live model.
- Waiting must be cognitively free.
- Known control, routing, continuation, proof and recovery belong below the model.
- Mission history may grow without active context growing with it.
- Goal count may grow without model-worker count growing proportionally.
- Every recurring unattended Work Class must exhibit cognitive deflation or be treated as non-institutionalized.
- Model workers are disposable compute; durable semantic state is the mission.
- Cognitive load should scale with current irreducible uncertainty, not institution size, age, history, goal count or ambition.
- Minimum Necessary Intelligence: use the least intelligence class that can safely produce the verified transition.
- No scope/quality/assurance reduction is allowed as a token-saving mechanism.

##### Workstream A — Global Goal Fabric

- Evolve independent missions toward views/subgraphs over a shared institutional Goal Fabric.
- Represent postconditions, dependencies, constraints, evidence, authority, proofs, events, unknowns and effects.
- Introduce unresolved institutional obligation as the economic/scheduling primitive where useful.
- Support mission merge/split, automatic supersession, dead-branch elimination, constant folding and cross-mission common-subexpression elimination.
- Incremental view maintenance: reality deltas reevaluate only affected goals.
- Dependency-indexed subscriptions/wakeups; avoid broad global polling.

##### Workstream B — Actorless / zero-resident autonomy

- A mission may remain active with zero workers, zero Agents, zero context windows and zero model spend.
- Compile Owner intent into an Autonomous Mission Executable / operational IR rather than a long-running conversation.
- Runtime executes certified transitions directly; Agent/model is an execution strategy only when no lower-intelligence path suffices.
- Scale cognition to zero when no unresolved cognitive work exists.
- Track Cognitive Duty Cycle, Model Residency Ratio, Wake Precision and False Wake Rate.

##### Workstream C — Event and temporal runtime

- External waits become events, callbacks, timers, watchers or cheap deterministic pollers.
- Temporal conditions compile into scheduler state; no model waits for dates, quotas or provider jobs.
- Zero-hot waiting is mandatory.
- Goal dormancy/hibernation and bounded-cost resurrection.
- Event-driven wakeups with idempotent effects and recovery for duplicate/out-of-order/lost events.

##### Workstream D — Cognitive Interrupt Runtime

- Represent sparse Cognitive Interrupt Slots in compiled missions.
- Every material model wake has explicit semantic cause/provenance.
- Add Cognitive Necessity checks before model invocation.
- Interrupt firewall checks current state, theorems, known transforms, in-flight derivations, cached derivations, deterministic tools, solvers and proof implication first.
- Shared global cognitive compute pool instead of one Agent per mission.
- Autoscale worker count from live irreducible parallelism, not Goal count.
- Track Frontier Cognition Purity and Avoidable Institutional Cache Misses.

##### Workstream E — Mission compiler and semantic superoptimizer

- Prefer declarative postconditions/constraints to procedural step lists where compatible.
- Deterministic planning/constraint solving first; models handle architectural ambiguity.
- Add Minimum-Cognition Certificate for expensive execution.
- Semantic branch-and-bound and dominance pruning for alternative strategies.
- Optimize Expected Total Verified Cost, reversibility, proof cost, latency, authority and future reuse.
- Receding-horizon execution: long-horizon intent, short verified horizons.
- Mission topology optimizer: split/fuse/hoist/reuse/delete/compile nodes dynamically.
- Peephole optimization and sequence mining over recurring execution motifs.

##### Workstream F — Cross-mission reuse and global demand optimization

- Semantic singleflight/CSE across projects and missions.
- Share proofs, reality observations, failures, owner resolutions and derivations when dependency fingerprints match.
- Cognitive batching and mission batching only when EVCC improves.
- Information-Leverage / Resolution-Leverage scheduling: prioritize cognition that extinguishes the most downstream work.
- Cognitive critical path separate from ordinary project critical path.
- Knowledge fan-out scheduling and economically justified semantic precomputation.
- Demand netting across overlapping/contradictory goals.

##### Workstream G — Context and memory virtualization

- Model context is an L1 working-set cache, not institutional storage.
- Hierarchy from exact interrupt packet to raw historical evidence.
- Continuation/resumption cost must be O(live semantic delta), not O(history).
- Semantic paging, prefetch, weighted caching, context GC and thrashing detection.
- Context compression is below deletion/eviction/projection in priority.
- Detect Cognitive Memory Leaks: idle workers, stale context objects, raw outputs, repeated reads, stale handoffs, status loops.
- Measure Archaeology Tax, Rediscovery Tax and lifetime Token Rent.
- Keep active context bounded as institutional history/capabilities grow.

##### Workstream H — Proof, effects and recovery below the model

- Proof-carrying state transitions and proof-carrying knowledge/capabilities.
- Affected-proof closure only; cross-mission proof sharing/subsumption.
- Proof batching and proof extinction when architecture makes invalid states impossible.
- Green-proof cognitive tax trends toward zero.
- Known failure classes compile into deterministic recovery transactions and eventually prevention.
- Recovery escalation: retry → known transaction → alternate resource → focused cognitive interrupt → Owner.
- Transactional irreversible effects with idempotency/outbox/fencing where appropriate.
- First-class effect receipts and deterministic reconciliation.
- Zero-ambiguity success states; no null/probable success.

##### Workstream I — Authority, safety and preemption

- Mission Effect System declares read/mutate/spend/send/deploy/delete/Owner-required effects.
- Capability-based, scoped, revocable authority with budget/count/expiry.
- Blast-radius-aware autonomy and proof strength.
- Economic preemption at safe semantic boundaries; revoke spend and rotate expensive workers safely.
- Irreversible-effect firewall remains separate from ordinary autonomous execution.
- Liveness and safety properties must hold under crash, retry, duplicate events, stale workers and provider delay.

##### Workstream J — Global scheduler and multidimensional economics

- Global scheduler across many goals; optimize portfolio, not isolated workers.
- Budget is a vector: cognition, processed tokens, money/API-equivalent, quota, CPU, RAM, browser/GPU, latency, human attention and semantic risk.
- Quota-aware backpressure: deterministic work continues while cognitive interrupts queue.
- Fairness based on urgency, critical path, leverage, Owner priority and risk.
- Semantic/data/runtime locality scheduling across laptop/GEX44/other machines.
- Capital substitution between deterministic compute and model cognition.
- Opportunity-cost scheduling and just-in-time cognition/proof/context/Owner attention.
- Mission Digital Twin/counterfactual simulation for high-cost plans where ROI is positive.
- Regret accounting updates scheduling/worker/model/context/proof policy.

##### Workstream K — JIT/AOT institutionalization

- Repeated model-interpreted workflows specialize, compile and deopt safely on exceptions.
- AOT compile mature high-frequency Work Classes.
- Automatic candidate synthesis from repeated sequences, decisions, repairs, proofs and context combinations.
- Sequence → primitive; repeated decision → policy/constraint/type/schema/API; repeated repair → guard; repeated proof → validator.
- Work-Class recurrence cost must slope downward absent new novelty/assurance.
- Track Cognitive Capitalization Ratio: reusable theorem/primitive/proof/index/transform/failure immunity created per cognitive spend.

##### Workstream L — Knowledge, Constitution and semantic defragmentation

- Proof-carrying knowledge with applicability, evidence, strength and invalidators.
- Institutional theorem propagation without loading project histories.
- Semantic memory dedup and current-truth defragmentation.
- Measure Institutional Entropy / truth-resolution cost.
- Constitutional garbage collection: mechanized rules leave hot CLAUDE.md while remaining documented cold.
- Prompt extinction and self-deflating MEMORY/knowledge surfaces.
- Capability growth must not imply hot-prompt/context growth.

##### Workstream M — Observability as cognitive infrastructure

Every autonomous component should answer deterministically: current state, why, last transition, next eligible transition, blocker, owner and proof.

Add/extend:
- semantic state interrogation API;
- failure-boundary localization;
- minimal counterexample output;
- repair-scope compiler;
- verification-scope compiler;
- Goal cost ledger separating novelty/known execution/proof/control/recovery/waiting/Owner cost;
- automatic mission autopsy on semantic-cost anomalies.

##### Workstream N — Adaptive specialization without fragmentation

- Shared semantic ABI for state/proof/authority/economics.
- Domain optimizer registry selects compiler passes by workload phenotype.
- Visual, distributed-systems, research, SEO, etc. may specialize without becoming separate mini-OSes.
- Cognitive Roofline classifies cognition/context/proof/reality/control/resource/Owner/transport/wait bottlenecks and only optimizes the actual limiter.

##### Required scaling invariants / benchmarks

For fixed semantic novelty:
- doubling wall-clock duration adds approximately zero cognition;
- doubling Goal count does not double model spend;
- doubling mission history does not materially increase resumption cost;
- adding unrelated capabilities does not grow a Work Unit's active semantic surface;
- adding unrelated tests does not grow local proof cost;
- growing institutional knowledge does not grow active context for a mature fixed Work Class;
- known recovery, coordination, waiting and green-proof cognition trend toward zero.

Build an Autonomous Mission Gym with historical incidents and adversarial cases: worker death, quota exhaustion, stale state, context explosion, lost/duplicate/out-of-order events, proof failure, zombie worker, delayed usage, crash during effects, lost receipt and provider outage.

##### Core metrics

Track where measurable:
- Autonomous Mission Density;
- Goal-hours per model token;
- Cognitive Duty Cycle;
- Model Residency Ratio;
- Cognitive Concurrency Ratio;
- Cognitive Sparsity;
- Deterministic Coverage;
- Event Coverage;
- Wake Precision / False Wake Rate;
- Resume Efficiency;
- Recovery Efficiency;
- Coordination Efficiency;
- Proof Efficiency;
- Context / Autonomy / Knowledge Elasticity;
- Frontier Cognition Purity;
- Archaeology / Rediscovery / Coordination / Waiting / Green-Proof / Known-Recovery taxes;
- Semantic Entropy Burn Rate;
- Resolution Leverage;
- Cognitive Capitalization Ratio;
- Human Attention Rent;
- recurrence deflation curves.

##### Completion-standard ratchet

For recurring/autonomous software, "done" increasingly requires:
- known transitions can run below the model where evidence supports it;
- queryable durable state;
- bounded reasoning/context locality;
- local/affected proof;
- deterministic known recovery;
- event-driven waiting;
- safe resumability independent of transcript/process/provider/machine;
- minimal recurring Owner mechanics;
- observability sufficient to avoid log archaeology;
- no unnecessary global-resident cognitive tax;
- future equivalent executions are measurably cheaper when institutionalization is applicable.

Promote verified universal mechanisms through UKDL + Constitutive Baseline Ratchet. Reuse/extend/merge existing CPP owners before creating new components.

##### Terminal target

CPP becomes a persistent autonomous institutional runtime in which:
- missions are views over durable semantic obligations;
- most mastered state transitions are actorless/deterministic;
- workers are disposable cognitive compute;
- models are sparse interrupt processors;
- cognition scales with current irreducible uncertainty rather than institution size, age, history, duration or Goal count;
- increasing autonomy produces decreasing marginal cognitive cost.

