# CDIO cross-sector benchmark: seeded defects (kept out of the builders' reach)

Baselines live in `C:\Users\User\Apps\cdio-bench\<case>\` (each its own git repo, outside this repo so the Power
Pack's project hooks cannot help). The builder session sees only its case directory. This file is the answer key.

## dashboard (B2B, desktop + phone)
- D1 broken image: `avatar.png` does not exist.
- D2 horizontal overflow on phone: table `min-width:1100px` with no scroll container.
- D3 tap targets 24x24 px (search, alerts, settings).
- D4 infinite `pulse` animation on every KPI card, no `prefers-reduced-motion` (red-team 13: enterprise screen that
  needs no animation).
- D5 status shown by colour only (dots, no text).
- D6 low contrast: #a0a0b0 on #fff (2.5:1) for labels and headers.
- D7 dead link: `reports.html` does not exist.
- D8 slop: purple-pink gradient, emoji icons, "Welcome back", "Unlock the power of seamless logistics".
- D9 missing fact: the brief requires the page to say it shows demo data; it does not.

## despacho (high-trust professional service, Spanish prompt)
- P1 hero with no protagonist: gradient + generic headline (red-team 3).
- P2 invented claims: "+10.000 clientes", "99% casos ganados", "25 años", two named testimonials. The brief has none
  of these and says the firm opened in 2019 (red-team 10).
- P3 CTA that does nothing: `<button>Pide cita</button>`, no handler, no phone/mail (red-team 6).
- P4 broken image: `equipo.jpg` does not exist (and the brief says no photos exist).
- P5 low contrast and small text: #999 on #fff, 13 px body, 11 px footer.
- P6 duplicate image: `icono.svg` used three times.
- P7 dead links: servicios.html, equipo.html, contacto.html do not exist.
- P8 missing facts: price of first consultation, hours, address, phone, the "demo / ficticio" notice.

## nurseapp, brandkit
From scratch, no baseline. Judged on the brief's own constraints (nurseapp: low light, one hand, gloves, interrupted,
no health claims, fictional notice; brandkit: 32 px favicon legibility, apron stamp in one colour, no eco cliché,
free fonts, fictional notice).
