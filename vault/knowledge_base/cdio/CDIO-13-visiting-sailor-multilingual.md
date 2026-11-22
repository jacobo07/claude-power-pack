---
id: CDIO-13
name: Visiting Sailor and Multilingual Surface — the Arrival Axis
type: dataset
domain: cdio
status: sealed
governs: [cdio-reviewer, cdio-core]
governed_by: CDIO-00
source: CDIO-GAP-INSTITUCIONAL screened catalogue (961 candidates, axes 3, 10, 18 and 19; Owner approval 2026-11-22)
evidence: observed practice and published standards (level C); no measured study specific to clubs or marinas (see sec. 9)
---

# CDIO-13 — Visiting Sailor and Multilingual Surface (the Arrival Axis)

CDIO-02 asks whether a user can complete a task without friction, and CDIO-03 asks whether the
surface earns trust. Neither was written for a user who is arriving from the sea, reads the site on a
phone in a cockpit, may not read the site's main language, and will act on what the page says about
depths, radio channels and opening hours. That user exists on every royal yacht club, marina, port
authority page and coastal sports club that accepts visitors, and the failure modes are specific: a
draught figure nobody verified, a working channel shown as a pictogram, a date written 11/12 that
means two different days to two readers, a language selector built from flags, an English page that
silently falls back to the Spanish home.

CDIO-13 is that axis. It was distilled from the screened gap catalogue of 2026-11-22, which found no
existing CDIO criterion for any of the rows below, and from the published practice of the clubs and
standards bodies cited inline. Its organising rule is the one CDIO already applies to generated
content, made specific to the sea:

> **A figure a sailor will navigate by needs a verified source. Absence stays absent, and says so.**

CDIO-13 adds criteria; it never relaxes a CDIO-00 floor. Where it and an older dataset appear to
disagree, CDIO-00 decides.

## 1. Scope and the three conditions

The arrival axis applies when **all three** of these hold. A club site with no visitor berths and a
single-language local membership is assessed by CDIO-10 and CDIO-14, not here.

1. **The institution receives people who are not members.** Visiting yachts, regatta crews, parents
   of sailing-school pupils, tourists who use the restaurant or the slipway.
2. **Some of those people act on the page.** They plan an approach, call the harbour office, turn up
   at a time, or decide not to sail because of a notice.
3. **At least one audience does not read the main language natively**, or the site already offers
   more than one language. A site that publishes only one language for one local audience is not
   failed by the language criteria in sec. 4; it is unassessed on them.

The exclusions were observed in the catalogue rather than reasoned:

- **Navigation is not the website's job.** The site never replaces an official chart, a notice to
  mariners or the harbour office. Every criterion below that touches approach data asks for a source
  and a link, never for the site to become a pilot book.
- **A members-only area is out of scope.** Internal forms, minutes and member rosters follow CDIO-10.
- **Event pages follow CDIO-11.** A regatta's notice of race, amendments and results have their own
  honesty rules; this dataset judges only the arrival and language layer around them.

## 2. Evidence levels and the honesty rule

Every criterion cites its evidence level inline, using the scale of the gap report: **A** measured or
peer-reviewed research, **B** published practitioner research, **C** observed practice at a named
institution or a published standard with a working link, **H** hypothesis. No row in this dataset
reaches A or B for the club and marina domain; most are C. A criterion that rests only on H is marked
**advisory**: the reviewer records the observation and the recommendation, and the scorer never turns
it into a failing verdict.

The honesty rule governs every figure on this axis. The catalogue flagged a large share of its
candidates with an honesty veto because they would push a builder to show data nobody could verify.
The resolution is not to drop the row but to give it an honest state. A port sheet with a verified
length and an unverified depth shows the length, and in the depth slot says "Depth: ask the harbour
office on VHF channel NN" or omits the row with a recorded reason. It never shows a plausible number.
An invented depth is a fabricated claim under CDIO-05 sec. 3 and is critical, however small it is
printed.

## 3. Criteria — arrival and the port

Each criterion names the dimension it reports under, so the scorer in CDIO-05 sec. 4 weighs it with
no change to the formula. Catalogue ids are given for traceability.

**`port-technical-sheet`** (dimension `ux`, severity major). A site that accepts visiting boats
publishes a port technical sheet as a table or definition list: number of berths, maximum length,
maximum beam, maximum draught or depth at the visitor pontoon, and the reference used for depth, each
with its unit. Observed-value form: "visitor page lists services in prose; no maximum length, beam or
draught anywhere on the site". Evidence C: observed at the Yacht Club de Monaco
(https://www.yacht-club-monaco.mc/) (G-A03-001). When NOT: a club with no visitor berths; a sheet that
would need figures the harbour office has not confirmed, in which case only the confirmed rows appear.

**`port-figures-sourced`** (dimension `trust`, severity critical). Every depth, length and beam on the
sheet comes from a named, verifiable source (the harbour office, the port authority, a dated survey),
and the source and its date are visible next to the table. Observed-value form: "draught 3.5 m shown,
no source, no date; harbour office states 2.8 m at low water". Evidence C: catalogue honesty veto on
G-A03-001 and the CDIO generated-content rule. When NOT: descriptive facts that are not navigational,
such as the number of showers, which need no survey; they still must be true.

**`radio-arrival-block`** (dimension `ux`, severity major). The arrival page carries one prominent block
with the VHF working channel, the station's call name as spoken on the radio, and the harbour-office
hours, with what to do outside those hours. Observed-value form: "VHF channel mentioned once inside a
PDF; not on the arrival page; no hours". Evidence C: observed at the Royal Yacht Squadron
(https://www.rys.org.uk/) (G-A03-006, G-A19-008). When NOT: a channel the marina staff do not monitor
must not be published; a club with no harbour office publishes the phone and says there is no radio
watch.

**`port-status-notice`** (dimension `trust`, severity major). Works, closures and restrictions in the
port appear as one dated notice near the top of the arrival and contact pages, with a start date, an
expected end date and the date it was last confirmed. The notice is removed when the incident ends.
Observed-value form: "fuel dock closed per harbour office; site says open"; or "notice of works dated
March still shown in November". Evidence C: GOV.UK notification banner
(https://design-system.service.gov.uk/components/notification-banner/) (G-A03-027). When NOT: routine
seasonal hours belong in the hours table, not in a notice; a notice for every minor change trains
readers to ignore the one that matters.

**`official-conditions-first`** (dimension `trust`, severity major). Sea state, sea level and tide are
taken from the official provider before any figure of the club's own: in Spain the Puertos del Estado
Portus widgets (https://portus.puertos.es/Portus/docs/widgets.pdf), with AEMET
(https://www.aemet.es/) for the marine forecast. The widget carries its provider's attribution, and
any figure from the club's own anemometer is labelled as such with its time. Observed-value form:
"homepage shows 'wind 12 kn' with no provider and no time". Evidence C (G-A10-001). When NOT: when the
official widget does not cover the port, link the nearest official station and name it as the nearest,
rather than presenting it as the port's own reading.

**`activity-suspension-notice`** (dimension `ux`, severity major). When outings, classes or races are
suspended for weather, the sailing-school and event pages show a dated notice with the time of the
decision, what is suspended, and when the next decision will be made. Observed-value form: "school
lesson cancelled by phone to parents; site shows the lesson as running". Evidence C: GOV.UK notification
banner, as above (G-A10-016). When NOT: the notice is removed once the suspension ends; a stale
suspension is itself a failure of this criterion.

**`values-in-text`** (dimension `visual`, severity critical). Every weather, tide, sea-state or service
icon that carries information is accompanied by its value and description in text, so that the
information survives without the image and is read by assistive technology. Observed-value form:
"wind shown as an arrow glyph and a colour; no number, no direction in text". Evidence C: WCAG 2.2
Understanding 1.1.1 Non-text Content
(https://www.w3.org/WAI/WCAG22/Understanding/non-text-content.html) (G-A10-026). Critical because it
is an accessibility-floor failure. When NOT: a purely decorative icon beside a value already in text
needs no second description; mark it decorative instead.

**`dual-units`** (dimension `ux`, severity minor). Length, beam and draught are shown in metres and
feet on sheets and tariffs ("12 m / 39 ft"), with the conversion correct to the stated rounding
(1 m = 3.281 ft). Observed-value form: "tariff bands in metres only; English page identical". Evidence
C: the SI definitions published by the BIPM (https://www.bipm.org/en/measurement-units) (G-A19-007).
When NOT: an official document whose units are fixed by regulation is quoted in its official unit and
not converted; a tariff priced by metre band shows feet as guidance only and says which governs.

**`how-to-get-here-link`** (dimension `ux`, severity minor). "How to get here" opens the device's map
application on the coordinates of the correct entrance (the club gate, the visitor pontoon, the
slipway), not on the centroid of the port and not on a name search. Observed-value form: "map link
searches 'club náutico' and resolves to a different club 4 km away". Evidence C: Google Maps URLs
(https://developers.google.com/maps/documentation/urls/get-started) (G-A18-010). When NOT: a site
whose only access is by sea links the approach notes instead.

**`arrival-by-land`** (dimension `ux`, **advisory**). A short block for crews arriving by air, rail and
road. Evidence H only (G-A19-022); recorded as an observation, never as a failing verdict. When NOT:
clubs that do not receive visitors.

## 4. Criteria — language

**`language-selector-endonyms`** (dimension `ux`, severity major). Languages are listed by their own
name (Español, English, Français, Català, Valencià), with the language code available to assistive
technology, and no flag is used as the label or the only signal. A flag names a country, not a
language: English is not the United Kingdom, Catalan is not Spain. Observed-value form: "selector of
three flags with no text; Valencian shown as the Spanish flag". Evidence C: USWDS language selector
(https://designsystem.digital.gov/components/language-selector/) (G-A19-001). When NOT: a site with a
single language has no selector to judge.

**`language-selector-placement`** (dimension `ux`, severity minor). On desktop the selector is visible
in the header corner without opening a menu; on mobile it is inside the menu and repeated in the
footer. A globe icon alone, with no text, does not satisfy the criterion. Observed-value form: "selector
only in mobile footer; desktop header has none". Evidence C: NN/g on language switching
(https://www.nngroup.com/articles/language-switching-ecommerce/) (G-A19-002). When NOT: a two-language
site may use a single text link ("English") in the same positions.

**`language-switch-equivalent`** (dimension `ux`, severity major, critical when the target is a dead
end). Changing language lands on the same page in the other language, not on the home. Observed-value
form: "switch on /es/puerto/tarifas goes to /en/; tested on five deep routes, five fail". Evidence C:
USWDS select-a-language pattern (https://designsystem.digital.gov/patterns/select-a-language/)
(G-A19-003). When NOT: a page that does not exist in the target language is handled by the next
criterion, not by a silent redirect.

**`translation-parity-notice`** (dimension `trust`, severity major). When a page exists in only one
language, the other version shows a notice ("This page is only available in Spanish"), a short summary
of the essentials in the reader's language, and a link to the original. Machine translation, if used,
is declared. Observed-value form: "/en/ facility rules returns the Spanish text with an English
heading and no notice". Evidence C: USWDS select-a-language (G-A19-005, G-A19-015). When NOT: normative
texts are not machine-translated without review; the notice and summary are the honest form.

**`lang-declared`** (dimension `ux`, severity critical for the page language, minor for parts). The
document language attribute matches the language of each page, and passages in another language are
marked. Observed-value form: "every /en/ page declares lang es". Evidence C: WCAG 2.2 Language of Page
(https://www.w3.org/WAI/WCAG22/Understanding/language-of-page.html) and Language of Parts
(https://www.w3.org/WAI/WCAG22/Understanding/language-of-parts.html) (G-A19-004). When NOT: loanwords
already absorbed by the language ("regatta", "yacht") are not marked as foreign.

**`no-forced-language-redirect`** (dimension `ux`, severity major). The site may suggest the language it
detects in a dismissible notice; it never redirects by IP or browser setting in a way that blocks the
other versions. Observed-value form: "Accept-Language en redirects /es/ to /en/ with no way back".
Evidence C: Google's guidance on multi-regional sites
(https://developers.google.com/search/docs/specialty/international/managing-multi-regional-sites)
(G-A19-006). When NOT: a remembered choice the user made explicitly is not a forced redirect.

**`text-expansion-tolerated`** (dimension `visual`, severity minor). Buttons, tabs and table headers
hold a 30 to 35 per cent longer string without clipping or overflow. Observed-value form: "French
'Demander un amarre' clips inside a fixed-width button". Evidence C: W3C Internationalization on text
size (https://www.w3.org/International/articles/article-text-size) (G-A19-018). When NOT: a single
language site.

**`nautical-terminology-glossary`** (dimension `ux`, **advisory**). Nautical terms are translated by
equivalence from a controlled glossary (amarre = berth, capitanía = harbour office, pantalán = pontoon)
and used consistently. Evidence H only (G-A19-014). When NOT: single-language sites.

## 5. Criteria — international formats and contact

**`unambiguous-dates`** (dimension `ux`, severity major). Dates in content read by an international
audience show the month in words for the page's locale ("22 Nov 2026", "22 nov 2026"), never a purely
numeric form such as 11/12 that two readers resolve to different days. Observed-value form: "arrival
window '03/04' on the English page". Evidence C: W3C Internationalization on date formats
(https://www.w3.org/International/questions/qa-date-format), produced per locale with Intl.DateTimeFormat
(https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/DateTimeFormat)
(G-A19-011). When NOT: machine-readable date attributes, which must stay ISO 8601.

**`event-time-zone`** (dimension `ux`, severity minor). Start times for races, briefings and arrivals
carry their zone ("11:00 CEST"), optionally with UTC. Observed-value form: "first warning signal 11:00,
no zone, event open to foreign entries". Evidence C: W3C Working With Time Zones
(https://www.w3.org/International/wiki/WorkingWithTimeZones) (G-A19-012). When NOT: local events with
no international audience.

**`international-phone`** (dimension `ux`, severity minor). Phone numbers are written with the country
prefix, grouped for reading ("+34 963 00 00 00"), and linked as telephone links. Observed-value form:
"harbour office '963000000' as plain text, no prefix, not tappable". Evidence C: GOV.UK telephone
numbers pattern (https://design-system.service.gov.uk/patterns/telephone-numbers/) (G-A18-004). When
NOT: numbers that do not accept calls, such as a fax line, are not linked.

**`international-forms`** (dimension `ux`, severity major, critical when submission becomes impossible).
Forms accept compound surnames, apostrophes, diacritics, non-Spanish postcodes and addresses with no
province, and ask for the country as a field. Observed-value form: "berth request rejects 'O'Neill'
and postcode 'SW1A 1AA'; the form cannot be sent". Evidence C: GOV.UK names pattern
(https://design-system.service.gov.uk/patterns/names/) (G-A19-021). When NOT: fields that legally
require a national identifier for residents may validate it, as long as foreign visitors have a path.

**`service-languages-declared`** (dimension `trust`, severity minor). Each contact point states the
languages in which it actually answers. Observed-value form: "flag icons beside the phone; staff answer
in Spanish only". Evidence C: schema.org availableLanguage (https://schema.org/availableLanguage)
(G-A19-019). When NOT: never list a language the staff do not speak; absence is the honest form.

## 6. Floor collisions with CDIO-00

Three of the criteria above meet a CDIO-00 floor head on, and the floor decides each time.

**(a) Density of the port sheet against the hierarchy ceiling.** A complete technical sheet is a dense
table, and on a phone it tempts the builder to shrink type below the 16 px mobile body floor or to drop
columns. Neither is permitted. The sheet reflows into labelled rows, keeps body size, and keeps every
unit; the CDIO-01 extension on responsive tables governs how.

**(b) The status notice against "one dominant element".** A dated port notice competes with the hero
for attention. That competition is the point: on the day the fuel dock is closed, the notice is the
most important element on the page. The notice may take the dominant role while it is live; when the
incident ends, it is removed rather than restyled to recede.

**(c) Weather colour against colour-only signalling.** Weather and sea-state widgets love a green,
amber and red scale. CDIO-01 already forbids state conveyed by hue alone, and `values-in-text` makes
the number and the word mandatory. A colour scale may stay as a redundant cue; it never carries the
information alone, and its text must clear 4.5:1 wherever it sits.

## 7. Common false positives (what CDIO-13 does not flag)

- **A site with one language.** The language criteria are unassessed, not failed.
- **A missing depth row with a recorded reason.** That is `port-figures-sourced` passing.
- **Metric only on an official document.** That is `dual-units` passing by its own exception.
- **A suggestion banner for the detected language.** Dismissible suggestion is the recommended form.
- **A third-party marina booking platform.** The handoff is judged by CDIO-10's continuity criteria;
  this dataset judges only that the arrival information exists before the handoff.

## 8. Deferred: search visibility

The catalogue's axis 25 rows that touch this surface are **not** criteria here. They are unscreened
against the Owner's SEO/GEO corpus, which the global rules require before any search-visibility
decision, so they stay as candidate ids only until that screening is done: G-A25-001, G-A25-003,
G-A25-006, G-A25-007, G-A25-009 and G-A25-033. Reciprocal hreflang annotations between language
versions (G-A25-009) are noted because the language criteria above produce the parallel URLs they would
annotate; the decision itself is deferred.

## 9. Evidence, scope and the ladder

Scope claimed: **arrival and language doctrine for institutional sites that receive non-members**,
judged by `cdio-reviewer`. Not claimed: that the site may stand in for official navigational sources,
or that any figure becomes true by being displayed.

| rung | status | evidence |
|---|---|---|
| local success | not reached | no CDIO-reviewed site has yet shipped all of sec. 3 to 5 |
| repeated success | not reached | — |
| production reality | not reached | criteria are distilled from named practice, not from a measured build |
| adversarial survival | not reached | no drill has yet shown `port-figures-sourced` can go red |
| transfer | partial | rows drawn from several institutions and standards bodies across countries |
| enforcement | judged, not gated | reviewer criteria above; no deterministic gate |

The first consumer will be a club site reviewed under CDIO-05. Until a drill shows a seeded unsourced
depth going red, `port-figures-sourced` is judged by the reviewer with an observed value, exactly as
CDIO-09's criteria were before their first drill.

## 10. Contract with the review pipeline

`cdio-reviewer` applies sec. 3 to 5 under CDIO-05 Lens 2 and Lens 6 whenever the surface is an arrival,
port, contact, sailing-school or event page of an institution that meets sec. 1; the verdicts report
under the existing `ux`, `visual` and `trust` dimensions, so the score formula is unchanged. Advisory
criteria are listed in the report and never scored. `cdio-core` routes a request that mentions visiting
yachts, berths, harbour office, VHF, tides, a language selector or translation here first, to CDIO-14
for the legal and emergency layer, and to CDIO-11 for anything about a race.

## Evidence update 2026-11-23 (second deep-research run)

Source run: vault/research/2026-11-23_000309_evidencia-medida-o-acad-mica-estudios-ux-baymard-n.md. No severity changes.

- `dual-units`: the run records publication in both metric and imperial units as standard practice in international navigation and racing communication [OBSERVED][MEDIUM as practice, evidence C]; it found no measurement of how many visitors use each unit. The criterion keeps its evidence level C.
- `language-selector-endonyms`: the run's claim that a flag-based selector is itself a WCAG violation is REJECTED as an overclaim: no WCAG success criterion names flags. The criterion keeps its basis in the USWDS language selector guidance and NN/g language-switching research, plus WCAG 1.1.1 and 3.1.2 where a flag carries no text alternative or language attribute.