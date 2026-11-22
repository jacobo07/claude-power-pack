---
id: CDIO-12
name: Heritage, Archive and Heraldic Identity — the Provenance Axis
type: dataset
domain: cdio
status: sealed
governs: [cdio-reviewer, cdio-core, design-md]
governed_by: CDIO-00
amends: CDIO-03 (archive exception, sec. 4) and CDIO-06 (family F11 Heritage Maritime, sec. 6)
source: CDIO-GAP-INSTITUTIONAL screen of 961 candidates against CDIO-00..09 (2026-11-22, Owner-approved proposal, units A07, A11, A13) + Owner decision of 2026-11-22 on the archive exception + DRX research report vault/research/2026-11-22_223544_mapa-exhaustivo-objetivo-1000-candidatos-de-patron.md
evidence: observed practice on heritage institution sites and published standards (level C); one credibility study reported through a degraded research run (level B); the archive exception itself is an Owner decision resting on that study and on CDIO-03's own rule (sec. 4)
---

# CDIO-12 — Heritage, Archive and Heraldic Identity (the Provenance Axis)

An old institution's strongest asset is that it is old, and its website is where that asset is
most easily counterfeited. The founding year, the photograph of the first regatta, the
burgee, the royal title: each is a claim about the past, and each tempts a designer to improve
it. The date is rounded, the blurred photograph is swapped for a crisp stock yacht, the crest
is redrawn so that it scales, the red of the burgee becomes the red of every warning on the
site. None of those changes looks like a lie. Each of them is one.

CDIO-03 judges imagery for crispness and calls a low-resolution image a trust leak, which is
correct for a product screenshot and wrong for a photograph from 1912. CDIO-06 has no family
whose authority comes from age and a supplied emblem. CDIO-12 resolves the first collision by
a narrowly bounded exception, approved by the Owner on 2026-11-22, and supplies the second as
family F11 Heritage Maritime, registered in CDIO-06 by amendment. Its governing question is
provenance: **can every historical claim and every inherited mark on this surface be traced to
the institution that owns it, and is it shown as what it is?**

CDIO-12 adds criteria; it never relaxes a CDIO-00 floor. The archive exception narrows one
CDIO-03 finding; it does not touch the honesty, contrast or accessibility floors, and sec. 4
states exactly where its edge lies.

## 1. Scope

CDIO-12 applies to any surface that presents an institution's history, archive, emblem or
titles: yacht and rowing clubs, historic sports clubs, learned societies, museums, schools,
regiments' associations, family firms that trade on their founding year. It governs history
pages, timelines, archive galleries, the use of historical photographs anywhere on a site, the
crest, burgee or coat of arms in every placement, and the institution's formal titles. It does
not govern the archive's cataloguing practice, which is a curatorial matter, nor the legal
right to use an image, which CDIO-14 routes.

## 2. Evidence levels used in this dataset

- **A** — a measured study of the behaviour in question. None specific to heritage sites.
- **B** — secondary research reported through the DRX run of 2026-11-22, carried with that
  run's confidence tags. The run was degraded (20 of 150 searches), so its findings are never
  treated as measured.
- **C** — a published standard or observed practice on real institutional sites, with a URL
  that answered when checked.
- **H** — hypothesis. A criterion resting only on H is **advisory** and never produces a
  failing verdict or moves the CDIO-05 score.

Some criteria below rest on neither external evidence nor hypothesis but on a sealed floor:
an invented date, title or emblem variant is a fabricated claim, and CDIO-03 and CDIO-05
already class that as critical. Those criteria say so instead of citing a level. Severity
follows CDIO-05 sec. 3; verdicts report under the existing four dimensions.

## 3. Founding date and the verified timeline

**`founding-date-verified`** (dimension `trust`, severity critical). The founding date shown
(in the header lockup, the footer, the history page or a seal) is the date the institution
supplied or published, at the precision it supplied it: a year if only the year is known, a
full date if the full date is documented. A full date invented to make a year look exact, or a
year moved to make an anniversary fall in a convenient season, fails. Observed value: each
founding date shown and its source. When NOT: where the founding date is genuinely disputed
(a club founded informally in one year and constituted in another), both dates are shown with
what each one marks, and that passes. Severity is critical because an invented date is a
fabricated claim under the CDIO-03 honesty floor. Evidence: C for the practice of a prominent,
exact founding date, observed on the New York Yacht Club site (https://www.nyyc.org/),
catalogue A07-003.

**`timeline-sourced`** (dimension `trust`, severity minor). A historical timeline lists only
milestones the institution can document, each with its year, a short statement and, where the
institution holds one, its source (minutes, a press cutting, a register entry). Observed value:
milestones shown and how many carry a source. When NOT: a three-line history summary on the
home links to the full timeline and need not carry sources itself. Evidence: C, observed on
the Royal Yacht Squadron site (https://www.rys.org.uk/), catalogue A07-001.

**`timeline-no-filler-milestones`** (dimension `trust`, severity critical). No milestone exists
on the timeline because the layout needed one more: no "the club grows" entry in a decade
with nothing documented, no estimated year presented as known. Gaps in a timeline are
history; filling them is fiction. Observed value: milestones with no supplied source and no
precision note. When NOT: an entry explicitly marked as tradition ("by club tradition, the
first race was sailed in 1897; no record survives") is honest and passes. Severity follows
the fabricated-claim floor.

**`milestone-verification-grade`** (dimension `trust`, advisory). Each milestone says whether
it is documented, held by tradition, or awaiting verification. Observed value: whether grades
are shown. When NOT: a timeline in which every entry is documented needs no grades. Evidence: H
(catalogue A07-002).

## 4. Archive photography and the archive exception

**The rule CDIO-03 applies.** CDIO-03 sec. 1 and sec. 3 record a visibly low-resolution or
stretched image as a trust leak, and require imagery to be crisp at its rendered size. For
current photography that rule stands unchanged: a blurred photograph of today's clubhouse says
that nobody cared enough to take a proper one.

**The archive exception (Owner decision, 2026-11-22).** A genuine historical or club
photograph shown at low resolution is **not** a CDIO-03 trust leak when it is presented as an
archive object, which means **all** of the following hold:

1. **It is genuine.** It is a photograph of the institution, its people, its boats or its
   place, from the institution's archive or a documented source; not a stock image, not a
   generated image, not a photograph of somewhere else.
2. **It carries an informative caption**: what it shows, who appears where known, where it was
   taken, and when, to the precision known ("c. 1925" is a precision).
3. **It carries a visible credit or provenance**: the photographer, the archive, the collection
   or "club archive".
4. **It is shown at or below its native scale, or given a deliberate treatment.** Either it is
   rendered no larger than its source pixels allow, or it is placed in a deliberate archive
   treatment that makes its age part of the design: the VP-008 duotone, a frame or mount, a
   contact-sheet or album composition.

When those hold, the softness of the image is information about its age, and the Stanford Web
Credibility research reported through the DRX run supports the direction of the exception: real
photography of the institution and its facility builds credibility better than stock imagery
[OBSERVED][MEDIUM]. Evidence: B, Stanford Web Credibility Project (2002) via the DRX report;
the exception is the Owner's decision on that evidence.

**Where the exception ends.** Two uses of an archive image remain defects, and so does one
substitution:

- **Upscaling past native size.** An archive photograph enlarged beyond its source resolution
  so that it shows interpolation, blocking or halos is still a CDIO-03 trust leak. The
  treatment exempts age, not enlargement.
- **The full-bleed sharp-hero use.** An archive photograph used as a full-width hero that is
  expected to read as sharp, with text laid across it as though it were a modern photograph,
  is not an archive presentation and gets no exception.
- **Stock substituted for the institution's own photographs.** Replacing the club's real but
  imperfect photographs with generic stock imagery is a defect in its own right (below).

**`archive-exception-conditions`** (dimension `trust`, severity major). A low-resolution image
that is not exempt by the four conditions above is judged under CDIO-03 as before; one that
meets them is not reported as a CDIO-03 imagery finding. This criterion records which case
applies. Observed value: for each low-resolution image, the conditions met and missed, for
example "1931 regatta photo: genuine, captioned, credited; rendered at 1600px from a 640px
source with no treatment: condition 4 fails". When NOT: an image at full modern resolution is
outside the exception and outside this criterion.

**`archive-native-scale`** (dimension `visual`, severity major). No archive image is rendered
above its native pixel size unless it sits in a deliberate treatment that absorbs the
enlargement (a duotone, a halftone, a mount at small scale on a large ground). Observed value:
rendered size against source size per archive image. When NOT: vector reproductions of
documents, which have no native scale. Evidence: the CDIO-03 sealed imagery rule, applied
here; catalogue A11-021 (H on its own).

**`archive-caption-informative`** (dimension `ux`, severity minor). Archive images carry a
caption that answers what, who, where and when, and does not repeat the section heading.
Observed value: the caption text, or its absence. When NOT: a purely decorative image takes no
caption; but an archive image is never decorative, because its value is what it records.
Evidence: C, NN/g photos as web content
(https://www.nngroup.com/articles/photos-as-web-content/), catalogue A11-008.

**`photo-credit-visible`** (dimension `trust`, severity minor). Every photograph carries a
visible credit (photographer and year, or the archive and collection), per image or once per
gallery. Observed value: images with and without credit. When NOT: the institution's own
icons, illustrations and diagrams. Evidence: C, observed on the Royal Yacht Squadron site
(https://www.rys.org.uk/), catalogue A11-003.

**`real-over-stock`** (dimension `trust`, severity major). Photographs on the site show the
institution: its people, its boats, its place, its events. Generic stock photographs of
anonymous yachts, models or other marinas presented in their stead fail, and fail hardest in
the hero, where the reader assumes the image is the place. Observed value: images identified
as stock and where they appear. When NOT: an illustrative image explicitly presented as such
(a generic diagram of points of sail in a school page) is not a claim about the place.
Evidence: C, NN/g photos as web content
(https://www.nngroup.com/articles/photos-as-web-content/), catalogue A11-010; B, Stanford Web
Credibility Project via the DRX report [OBSERVED][MEDIUM].

**`archive-not-fabricated`** (dimension `trust`, severity critical). No generated, composited
or staged image is presented as a historical photograph. Observed value: images presented as
archive whose provenance is generated or unknown. When NOT: a generated illustration labelled
as an illustration, in a style that does not imitate a photograph, is not presented as archive.
Severity follows the fabricated-signal floor.

**`restoration-declared`** (dimension `trust`, advisory). A restored, retouched or colourised
archive photograph says so in its caption. Observed value: restored images and whether the
restoration is declared. When NOT: routine cleaning of dust and scratches that adds nothing.
Evidence: H (catalogue A11-014).

**`photo-gap-honest`** (dimension `trust`, advisory). Where the institution has no photograph
for a section, the layout omits the image or uses a typographic or heraldic composition; it
does not fill the slot with stock. Observed value: image slots filled with non-institution
imagery. When NOT: never excused in spirit, but the failure case is already scored by
`real-over-stock`. Evidence: H (catalogue A11-033).

Photographs of minors, in archive or current use, raise consent questions that are legal
rather than visual; CDIO-14 routes them.

## 5. Heraldry and titles

The crest, burgee or coat of arms is not a logo the designer owns. It is a mark the
institution inherited, often regulated, sometimes registered, and its exact form is part of
what it means.

**`crest-as-supplied`** (dimension `trust`, severity major). The crest and burgee are used in
the form the institution supplied, from its master artwork: not redrawn, simplified,
re-proportioned, recoloured or "modernised" into an invented variant. Where only a raster
exists, it is used at a size it supports, and the lack of a vector master is recorded as a gap
to be closed by the institution, not closed by tracing. Observed value: each placement of the
mark and whether it matches the supplied master, for example "header crest redrawn as flat
vector; anchor removed; red shifted from the burgee's value". When NOT: a derived variant the
institution has approved and documented (below) is as supplied. Evidence: the CDIO-03 honesty
floor (an invented variant presented as the official mark is a claim the institution did not
make); severity is major rather than critical because the mark is still the institution's,
only altered, and becomes critical when an invented mark is presented as official.

**`derived-variants-documented`** (dimension `trust`, advisory). Each derived form of the mark
(single-colour white for dark grounds, one-colour for embroidery, a vector redraw, a favicon
reduction) is listed in the design system with its source artwork, who derived it, and the
institution's approval or its absence. A concept variant not yet approved is labelled as a
concept in every file that carries it. Observed value: derived variants present and their
documentation. When NOT: a site using only the supplied master needs no register. Evidence: H.

**`title-verified`** (dimension `trust`, severity critical). Formal titles and honours (a
royal prefix such as "Real" or "Royal", a patronage, royal arms or a crown in the mark, a
federation membership, a protected designation) appear only when the institution holds them
and can show the grant or the register entry. Observed value: each title or honour shown and
its source. When NOT: never excused. An unverified royal title is a fabricated claim, and in
several jurisdictions a regulated one. Severity follows the fabricated-signal floor.

**`alert-red-separate`** (dimension `visual`, severity major). Where the institution's colours
include a red, the danger and alert colour of the interface is a separate token, distinct in
hue or lightness from the heraldic red, and no decorative element uses the danger token.
Every alert carries an icon and text, so its meaning never depends on its colour. Observed
value: the two tokens and their values, and any element using one for the other's purpose, for
example "cancellation badge and burgee share #B3122A; error text uses the same". When NOT: a
brand without red uses the standard danger token and nothing more is needed. Severity rises to
critical when an alert relies on colour alone, which is an accessibility-floor failure under
WCAG use of colour. Evidence: C, WCAG 2.2 use of colour
(https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html), catalogue A13-005.

**`palette-from-emblem`** (dimension `visual`, advisory). The institution's primary colours
are sampled from the rendered pixels of its official emblem master and fixed as tokens, rather
than chosen by eye or taken from an earlier website. Observed value: the token values and
their sampling source. When NOT: an institution with a published colour specification uses the
specification. Evidence: H (catalogue A13-001), consistent with the global rule that a visual
token's source of truth is rendered pixels.

## 6. F11 Heritage Maritime (family proposal, registered in CDIO-06 by amendment)

CDIO-06 has ten families and none of them is built on inherited authority. F3 Warm Editorial is
humane and serif, but its warmth is a prosumer warmth. F9 Cult / Indie borrows the archive as
an aesthetic of differentiation. Neither describes an institution whose surface must look as
though it has always been there and must carry a mark it did not design. F11 is that family. It
is registered in CDIO-06 sec. 1 by an amendment of 2026-11-22, which points here for detail.

- **Palette:** a deep, desaturated navy as the dark neutral in place of black; a paper or
  bone ground in place of pure white; the burgee's own colours as the only saturated hues,
  sampled from the master (see `palette-from-emblem`); a separate alert red (see
  `alert-red-separate`).
- **Typography:** a text serif with real italics and old-style figures for reading, paired
  with a restrained humanist or grotesque sans for interface, navigation, labels and data;
  tabular lining figures in every table. Small capitals for titles and dates where the face
  provides true small capitals. Display sizes are modest: authority is not loud.
- **Use when:** institutions whose authority comes from age and from a supplied emblem — royal
  and historic yacht clubs, rowing clubs, learned societies, museums, schools with a long
  register — on reading-heavy public surfaces.
- **Sanctions default-tier fonts:** no. The type pairing is the commitment.

**Invariants — break one and it is not this family.**
- The supplied mark is used as supplied (sec. 5).
- Saturated colour comes only from the emblem, and is scarce.
- Archive imagery is presented as archive: captioned, credited, at native scale or in a
  deliberate treatment (sec. 4).
- Surfaces are opaque and flat; contrast is computable from tokens.

**Strong preferences.** A generous measure for reading; rules and hairlines rather than cards
for grouping; a restrained duotone (VP-008) for archive imagery; texture limited to the paper
ground and engraved-style illustration, never noise over text.

**Motion restraint.** F11 moves very little. No parallax, no scroll-driven sequences, no
animated crest. Transitions are short opacity changes, and under reduced motion there are none.
Everything else is governed by CDIO-07; F11 adds only that motion must never animate the mark.

**Anti-patterns.** The nautical cliché kit: rope borders, anchor dingbats, compass roses used
as decoration, a wheel icon for settings. Gold gradients standing in for a real heritage.
A redrawn "modern" crest. Stock yachts in the hero. A timeline padded to look full. A
founding year in a display size larger than the institution's name.

**Floor collisions.**
- **Navy on navy, and bone under text.** A desaturated navy ground with a lighter navy text,
  or mid-grey text on a bone ground, sits close to the 4.5:1 line while looking dignified.
  Check the ratio; do not trust the eye.
- **Heraldic colours as text.** Burgee reds and golds are chosen for cloth at a distance, not
  for small text on screen; gold on bone routinely fails. Use them for fields and marks, set
  text in ink.
- **Text over archive photographs.** Archive images are uneven in tone. Text laid over one
  needs the scrim token and must clear the floor at the image's lightest point; better, set the
  text beside it.
- **Small capitals and italics at small sizes.** Both lose legibility below the body size; keep
  them for display and labels at a readable size.

**Proof set.** Nominated for verification against rendered pixels, not yet verified as
exemplars: the Royal Yacht Squadron (https://www.rys.org.uk/), the New York Yacht Club
(https://www.nyyc.org/), the Real Club Náutico de Barcelona (https://www.rcnb.com/) and the Yacht
Club de Monaco (https://www.yacht-club-monaco.mc/). Each answered when checked; none has yet
been measured trait by trait. Until at least two are, F11's proof rung is "nominated", and a
reviewer cites F11's invariants, never its proof set, as the basis of a finding.

**Picker.** CDIO-06's picker reaches F11 on a read-heavy surface for a public audience when
the brand's authority is inherited rather than claimed. Where the institution wants to read as
contemporary and its mark is new, F1 or F3 remain the honest choices.

## 7. Where CDIO-12 collides with the CDIO-00 floors

- **The exception is not a contrast exception.** A captioned, credited archive photograph is
  exempt from the low-resolution finding only. Its caption must clear the text floor, and any
  text over it must clear the contrast floor at the worst point.
- **Alt text still applies.** An archive image's caption does not replace its text
  alternative; the alternative describes the image, the caption documents it.
- **Honesty outranks completeness.** A history page with four documented milestones is
  finished; one with twelve, eight of them invented, is not.

## 8. Common false positives (what CDIO-12 does not flag)

- **A soft, grainy 1920s photograph at native size with caption and credit.** That is the
  archive exception passing. Reporting it as a CDIO-03 imagery leak is the error this dataset
  exists to prevent.
- **A short timeline.** Few milestones is not an unfinished history.
- **A crest that looks old-fashioned.** Its age is the point; "dated logo" is not a finding
  against an inherited mark.
- **No royal title.** Most institutions have none.
- **A disputed founding date shown twice.** That is `founding-date-verified` passing by its own
  "when NOT".

## 9. Evidence, scope and contract

Scope claimed: history, archive, emblem and title surfaces of any institution, judged by
`cdio-reviewer` under CDIO-05 Lens 1 (first impression), Lens 3 (hierarchy) and Lens 4 (trust),
with verdicts in the existing four dimensions; the score formula is unchanged. F11 is
read by `design-md` as a declarable `aesthetic_family` once CDIO-06's amendment registers it;
because it does not sanction default-tier fonts, `check_font_stack` treats it like F3 and F9.

The evidence ceiling is stated plainly: no measured study of heritage websites was found. The
archive exception rests on one credibility study carried through a degraded research run and on
the Owner's decision; its four conditions are written so that a reviewer can check each one on
the rendered page. CDIO-03 carries a short pointer to sec. 4 so the low-resolution rule no
longer fires on an exempt archive image. `cdio-core` routes a request that mentions a history
page, an archive, an old photograph, a crest, a burgee, a coat of arms, a royal title or a
founding date here first.
