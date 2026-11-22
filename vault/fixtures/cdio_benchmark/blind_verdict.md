# Independent visual verdict (CDIO bench, 2026-11-22)

All 12 images loaded. Phone first screen = top 844 px, desktop = top 900 px.

## Task 1a -- dashboard (Ledgerline "today" view)

Preferred: **B**. Confidence: **high**.

Reasons:
1. OBSERVED -- A (desktop and phone) never says the data is demo data; B has a top banner "Demo data. Every figure and shipment on this page is sample data..." and "5 sample shipments". The brief requires the demo label.
2. OBSERVED -- A's status column is a coloured dot only (green/red/yellow), no text; B shows "Late" (triangle), "On hold" (pause bars), "On time" (dot) as text pills plus a coloured left row border. B does not rely on colour alone.
3. OBSERVED -- B orders rows Late, Late, On hold, then On time and states the rule ("Late and on-hold shipments come first, each group in ETA order"); A lists rows by shipment id, so the two red rows are rows 2 and 5.
4. OBSERVED -- A phone render is about 1128 px wide in a 390 px viewport: the table and KPI row overflow sideways, the gradient header stops at 390 px. B phone reflows into a 2x2 KPI grid and one card per shipment with no horizontal overflow.
5. OBSERVED -- B adds filter tabs with counts (Needs action 3 / Late 2 / On hold 1) and a search box; the Exceptions KPI is the only one in red with a red edge. A has a "View full report" link and marketing copy ("Unlock the power of seamless logistics"), a broken avatar image icon in the header, and an emoji greeting. JUDGEMENT: A's purple gradient + glow cards read as generic template, B as a work tool.

Still weak in B:
- Phone: the first actionable row (LL-20419, Late) starts around y=670 and ends around y=857; only part of it is in the first screen, and the second Late row is below the fold. The demo banner, header, 4 KPIs, filters and search take most of the first screen.
- Desktop: the page ends around y=660 with a large empty grey area below; the KPI cards are not linked to the filters (OBSERVED only as no visible affordance; behaviour not testable from a still).
- Phone: each shipment card is about 188 px tall, so 5 rows need about 940 px; with more than 5 real shipments the late ones would need a scroll to compare. JUDGEMENT.
- No "act on it" control is visible on a row (no assign/contact/open button); the job is to "act on them fast". OBSERVED absence in the render.

## Task 1b -- despacho (Herrera Gil Abogados)

Preferred: **B**. Confidence: **high**.

Reasons:
1. OBSERVED -- A shows figures the brief says do not exist: "+10.000 clientes satisfechos", "99% casos ganados", "25 años de experiencia" (the firm opened in 2019; the senior lawyer was admitted in 2009), plus two testimonials ("Laura M.", "Carlos R.") although the brief says there are no real testimonials. For a visitor who "distrusts lawyers who promise a lot", this is the exact thing the brief warns against. B shows none of these.
2. OBSERVED -- B states the price and format above the fold: heading "Herencias y testamentos en Sevilla", body "La primera consulta dura 45 minutos y cuesta 60 €", and a card with Precio 60 € (deducted if you hire them), Duración 45 min, Dónde (office or video call), Teléfono 955 00 00 00. A never shows the price, duration, address, hours or phone anywhere on the page.
3. OBSERVED -- B answers "what papers to bring" with a three-column checklist (De la persona fallecida / De lo que dejó / De los herederos) and a note on the six-month inheritance tax deadline; A has no such content. A's service cards say "Soluciones a tu medida", "Protegemos lo que más importa", and all three use the same upload-arrow icon.
4. OBSERVED -- B's footer says "Herrera Gil Abogados es un despacho ficticio. Esta web es una demostración..." as the brief requires; A's footer reads only "© Herrera Gil Abogados. Todos los derechos reservados." B also has "Lo que no llevamos: asuntos penales y laborales" and names both lawyers with their admission years.
5. OBSERVED -- A has a broken image ("Nuestro equipo" alt text with a broken-image icon) and its phone render is about 513 px wide in a 390 px viewport: the "+10.000" figure is clipped at the left edge and the third service card runs off the right. B phone reflows into one column with no overflow. JUDGEMENT: A's hero "Soluciones legales innovadoras / enfoque disruptivo" is generic startup copy that does not fit an inheritance practice.

Still weak in B:
- Desktop: the FAQ shows questions with "+" only; whether the answers expand cannot be checked from a still, and the first question ("¿Cuánto cuesta tramitar una herencia completa?") is the one most likely to be asked. If it is answered vaguely, the trust gain is lost. Unverifiable here.
- Desktop: the "Quiénes somos" section is text only with no portrait (correct per the brief: no photos exist), and the right column stays empty under "Lo que no llevamos". JUDGEMENT: the layout is thin in places.
- Phone: the full page is about 4,667 px tall. The phone number appears near the top only inside the consultation card; there is no sticky call button (OBSERVED: none visible in the render, beyond the "Pedir cita" button in the header).
- The mark next to the name in the header is very small (around 16 px on phone); JUDGEMENT: it adds little.

## Task 2a -- nurseapp (Relevo)

Coverage: both renders show ONLY onboarding screen 1 of 3. Onboarding screens 2-3 and the mid-shift home screen (half of what the brief asks for) are in no image, so they are not judged. On desktop the screen sits in a phone mock-up beside a "Prototype controls (not part of the app)" panel; on phone those controls stack below the app (y~860-1135).

Strengths:
1. OBSERVED -- "This is a fictional app. Relevo is a design prototype, not a real product..." appears in an outlined box under the name on screen 1, as the brief requires.
2. OBSERVED -- the no-health-claim line is there: "Relevo reminds and records. It doesn't treat tiredness or change how you sleep."
3. OBSERVED -- the three routines from the brief, each with a one-line description ("One tap per glass", "Three quick taps", wind-down "ticked off one by one").
4. OBSERVED -- full-width pill buttons about 55 px tall ("Set up in 2 steps", "Skip and use a night shift") at y~700-820, in the thumb zone; the skip path suits an interrupted nurse.
5. OBSERVED -- the "1 of 3" progress label keeps onboarding within the 3-screen limit.

Defects:
1. OBSERVED -- light theme only: pale mint-grey background, dark text, bright orange button. No dark or low-light variant is rendered. JUDGEMENT: glaring on a dark night ward.
2. OBSERVED -- the mid-shift home screen is not rendered, so the core one-handed task (log a glass) cannot be judged.
3. OBSERVED -- the descriptions and the disclaimer are small grey text (~14-15 px) at lower contrast than the headings. JUDGEMENT: harder to read for a tired nurse in low light.
4. OBSERVED -- the routine markers (filled teal dot, empty ring, half-orange dot) have no label or key. Minor.
5. OBSERVED -- on phone, the prototype-control rows sit right under the app buttons and look like app UI. They are labelled "(not part of the app)". JUDGEMENT: a minor risk in a demo.

One-handed / low light: one-handed is plausible for this screen (large bottom-half buttons, nothing needed in the top corners; glove-sized). Low light is NOT shown: only a light theme is rendered, and I judge it too bright for a night ward.

## Task 2b -- brandkit (Radio Taller)

Resolution caveat: the desktop render (1440x8564) reached me scaled to 336 px wide and the phone render (390x17263) to 45 px wide. I can read the structure, colour blocks and large type, but not body copy or fine detail.

Strengths:
1. OBSERVED -- the mark is a radio dial: a round knob with concentric waves and a tilted orange needle, annotated as tyre/waves/needle/hub. It ties to the brief's real story (the old "RADIO" sign), not to eco imagery.
2. OBSERVED -- "Where it goes" shows all three uses the brief names: a navy apron mock-up with the stacked wordmark, a wall mock-up under a "RADIO" sign, and a favicon block, plus "minimum sizes" and "breathing room" diagrams.
3. OBSERVED -- six named colours (cream, near-black, orange "Naranja Válvula", blue "Azul Mahón", yellow "Amarillo Dial", grey) with a contrast table giving each pair's ratio and allowed use. No green in the palette.
4. OBSERVED -- the type pairing is shown in use: the "PINCHAZO? LO ARREGLAMOS." poster and the "TALLER ABIERTO 19:00" banner, which carry the practical, humorous tone.
5. OBSERVED -- a Do/Don't section with drawn examples, a Files list of SVGs with their uses, and a top banner saying the co-op is fictional.

Defects:
1. Favicon legibility -- NOT VERIFIED at pixel level. The block shows the mark at 32 and 16 px, but at my scale I can see only a ring with thin inner rings and a thin needle. JUDGEMENT: at 32 px it likely reads as a dial; at 16 px the inner wave rings very likely merge, and only the ring and needle survive. A full-resolution crop of that block is needed to settle it.
2. Eco cliché check -- OBSERVED: the only green on the page is the Do/Don't tile "NO ECO GRADIENTS", a clearly labelled forbidden example. The identity itself has no leaves, no green and no gradients. JUDGEMENT: this passes, though that tile is the most saturated thing in its row.
3. OBSERVED -- the page is very long: 8,564 px on desktop and 17,263 px on phone (about 20 phone screens). JUDGEMENT: heavy for a kit people need to scan.
4. OBSERVED -- on phone the swatches and the contrast table become long single-column strips; I cannot judge their readability at the supplied scale.
5. Desktop body copy looks small next to the huge section headings. This is resolution-limited and not confirmed.

## Task 3 -- hero protagonist test (phone, top 844 px)

| Render | (a) Protagonist | (b) In first screen | (c) Evidence |
|---|---|---|---|
| dashboard A | Data screen, no marketing hero; key info = late/on-hold shipments | partly | The table is at y~340-570, but the page is ~1128 px wide, so Carrier/ETA/Owner sit off-screen right; status is a colour dot only; late rows are mixed in by id. |
| dashboard B | Data screen, no marketing hero; key info = late/on-hold shipments | partly | The red "Exceptions 37" and "Late 2 / On hold 1" counts are in; the first Late card (LL-20419) spans y~670-857, so it is cut at the fold; the second Late card is below. |
| despacho A | The offer (practice + first-consultation terms) | no | The screen shows "Soluciones legales innovadoras" + "Pide cita" + invented stats; the price and the services never appear in the first screen, and the price is not on the page at all. |
| despacho B | The offer: inheritances/wills in Sevilla, 60 € / 45 min consultation | yes | The heading, the "45 minutos y cuesta 60 €" sentence, "Pedir cita" and the consultation card (price, duration, place, phone) all end by y~640. |
| nurseapp | Onboarding 1: fictional notice + three routines + start button | yes | Notice y~145-265, routines y~290-610, buttons y~698-820. |
| brandkit | The radio-dial mark + wordmark | yes (resolution-limited) | In the 45 px preview the "RADIO TALLER" wordmark and the large dial sit at about y~170-520 in the original. |

## Summary

| surface | preference / verdict | confidence | protagonist | in first phone screen |
|---|---|---|---|---|
| dashboard | B | high | late/on-hold shipments (data screen) | A partly (sideways overflow, colour-only status); B partly (first Late card cut at fold) |
| despacho | B | high | the offer: 60 € / 45 min first consultation | A no; B yes |
| nurseapp | onboarding 1 meets brief; home + screens 2-3 not rendered; light-only theme is a low-light risk | medium | fictional notice + routines + start | yes |
| brandkit | covers apron/wall/favicon/palette/type; no eco cliché in identity; 16 px favicon legibility unverified | low-medium (downscaled renders) | radio-dial mark + wordmark | yes (resolution-limited) |

