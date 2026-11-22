---
id: CDIO-14
name: Institutional Trust and Compliance — the Accountability Axis
type: dataset
domain: cdio
status: sealed
governs: [cdio-reviewer, cdio-core]
governed_by: CDIO-00
source: CDIO-GAP-INSTITUCIONAL screened catalogue (961 candidates, axes 14, 16, 17, 18, 20 and 21; Owner approval 2026-11-22)
evidence: published law (BOE, EUR-Lex), published standards and observed practice at named clubs (level C); no measured study specific to clubs (see sec. 9)
---

# CDIO-14 — Institutional Trust and Compliance (the Accountability Axis)

CDIO-03 owns trust as a property of a product page: signals above the fold, proof that is specific,
finish that is consistent. An institution is trusted for a different reason. A royal yacht club, a
municipal sports club, a federation, a heritage foundation or a residents' association is trusted
because it is **accountable**: a reader can find out who it legally is, who answers for the children
in its sailing school, what its rules say and since when, what happens to money paid for a cancelled
course, which door to knock on for which question, and where not to write in an emergency. None of
that is decoration, and much of it is required by law. When it is missing, the site looks finished and
the institution looks evasive.

CDIO-14 is that axis. It was distilled from the screened gap catalogue of 2026-11-22, which found no
CDIO criterion for any row below, from Spanish and European law cited by its official text, and from
observed practice at named clubs. It is written Europe and Spain first, because that is where the law
was read, and generalises by replacing each named statute with the local equivalent; the criteria are
about what a reader must be able to find, not about one country's article numbers.

Its organising rule:

> **Accountability is something a reader can reach in one step from the place they need it.
> A legal duty met only in a buried PDF is met on paper and missed on the page.**

CDIO-14 adds criteria; it never relaxes a CDIO-00 floor. Where it and an older dataset appear to
disagree, CDIO-00 decides. Nothing in this dataset is legal advice; the reviewer checks what is shown
on the surface and records whether the obligation applies as an observed fact or as unknown.

## 1. Scope and conditions

The axis applies to any site that represents an **institution** rather than a product: a club, an
association, a foundation, a federation, a public or semi-public body, a heritage institution. It
applies in full when the institution does at least one of: takes payments or registrations, runs
activities with minors, collects personal data through forms, or receives public money.

The exclusions:

- **The criteria never require inventing a fact.** A registry number, an officer's name or a
  transparency figure that the institution has not supplied is absent, and the surface says what to do
  instead ("Contact the secretary's office for our registry details"). Showing a plausible value is a
  fabricated trust signal under CDIO-05 sec. 3 and is critical.
- **Applicability is a fact, not a guess.** Several duties below depend on thresholds (public aid
  received, number of workers, whether minors take part). The reviewer records applicability as
  observed or unknown and never fails a criterion whose trigger is unknown; an unknown trigger is a
  question for the Owner.
- **Members-only governance documents follow CDIO-10.** Minutes and internal records stay in the
  private area; this dataset judges only what must be public.

## 2. Evidence levels

The scale is the gap report's: **A** measured or peer-reviewed research, **B** published practitioner
research, **C** published law or standard with a working link, or observed practice at a named
institution, **H** hypothesis. Most rows here are C, and the legal ones are C of an unusually strong
kind, since the source is the official gazette. A criterion that rests only on H is **advisory**: the
reviewer records it and the scorer never turns it into a failing verdict.

## 3. Criteria — identity and accountability

Each criterion names the dimension it reports under, so the scorer in CDIO-05 sec. 4 weighs it with no
change to the formula. Catalogue ids are given for traceability.

**`legal-identity-footer`** (dimension `trust`, severity major). The footer of every page, or a legal
notice linked from every footer, states the legal name, the tax identifier, the full registered address
and, for a sports entity, its number in the registry of sports entities. Observed-value form: "footer
shows the club's trading name and a PO box; no tax ID, no registry number; no legal notice link".
Evidence C: the information duty of Spain's Ley 34/2002 (LSSI), art. 10
(https://www.boe.es/buscar/act.php?id=BOE-A-2002-13758); the full footer is cited in the screened
catalogue as observed practice at the Real Club Náutico de Barcelona (https://www.rcnb.com/)
(G-A17-002). When NOT: never replace the address with a PO box, never omit the tax ID; outside Spain,
the local registry and identifier replace these fields; a registry number the institution has not
supplied is left absent with a stated way to obtain it.

**`child-protection-reachable`** (dimension `trust`, severity major). Where minors take part in
activities, the sailing-school page and every activity page for minors link in one step to a page that
states the protection protocol, names the role of the designated protection officer and gives a
corporate contact for that role, and explains how to raise a concern. Observed-value form: "school page
has no link; protocol exists only as an unlinked PDF in the documents section". Evidence C: Spain's Ley
Orgánica 8/2021 (LOPIVI), which requires a protection officer in entities that run sport or leisure
activities with minors (https://www.boe.es/buscar/act.php?id=BOE-A-2021-9347); observed as linked from
the school area at the Real Club Náutico de Valencia (https://www.rcnv.es/) (G-A17-009). When NOT: an
institution with no activities involving minors; never publish the officer's personal mobile, only a
corporate channel for the role.

**`facility-rules-summary`** (dimension `ux`, severity major). Rules for each facility (pool, courts,
boatyard, pontoons, slipway) appear as a short HTML summary of the five to seven points a user needs,
followed by the official document with its year and approval date. Observed-value form: "boatyard rules
only as a 14-page scanned PDF without date". Evidence C: observed at the Real Club Náutico de Valencia
(https://www.rcnv.es/) and GDS on publishing in HTML rather than PDF
(https://gds.blog.gov.uk/2018/07/16/why-gov-uk-content-should-be-published-in-html-and-not-pdf/)
(G-A16-002). When NOT: superseded rules are never shown without a "no longer in force" mark; the
summary never contradicts the document and names the document as the authority.

**`last-reviewed-date`** (dimension `trust`, severity minor). Factual pages (facilities, prices, hours,
contact, rules) show "Last reviewed: month year", and the date changes only when the content was
actually checked. Observed-value form: "hours page shows no date; hours changed in October per
secretary"; or "footer date updates on every build with no content change". Evidence C: GOV.UK content
design guidance (https://www.gov.uk/guidance/content-design/writing-for-gov-uk) (G-A16-039,
G-A21-009). When NOT: a page nobody will maintain shows no date rather than a date that will go stale
unattended; news items carry their publication date under CDIO-02 instead.

**`certifications-dated`** (dimension `trust`, severity major, critical when the distinction has lapsed).
Each distinction (Blue Flag, quality marks, environmental certificates) carries its year and links to
the awarding body's register; it is removed when it expires. Observed-value form: "Blue Flag badge in
the header; the marina is not in the current year's list". Evidence C: the Blue Flag criteria
(https://www.blueflag.global/criteria) (G-A17-010). A badge shown after withdrawal is a fabricated
trust signal, hence critical. When NOT: a historic distinction may appear in a dated history section,
labelled with its year, never as current.

**`team-by-area`** (dimension `ux`, severity minor). The professional team is presented by area
(management, secretary's office, harbour office, sailing school, events) with each area's corporate
contact. Observed-value form: "one generic address for everything; harbour office not listed".
Evidence C: observed at the Royal Ocean Racing Club (https://www.rorc.org/) (G-A17-014). When NOT:
never publish personal mobiles; photographs of staff only with consent.

## 4. Criteria — contact and the urgent channel

**`contact-by-department`** (dimension `ux`, severity major). The contact page is organised by what the
reader needs (berths, school, events, membership, restaurant, press), each with its own channel, rather
than one form for everything. Observed-value form: "single contact form; berth requests and restaurant
bookings land in the same inbox with no subject choice". Evidence C: GOV.UK pattern for contacting a
department (https://design-system.service.gov.uk/patterns/contact-a-department-or-service-team/). When
NOT: a very small institution with one person answering may keep one channel, as long as it says so.

**`hours-beside-phone`** (dimension `ux`, severity minor). Every published phone number states the days
and hours it is answered, next to the number. Observed-value form: "harbour office phone with no hours;
nobody answers after 14:00". Evidence C: GOV.UK telephone numbers
(https://design-system.service.gov.uk/patterns/telephone-numbers/) (G-A18-003). When NOT: a number
answered around the clock says so instead of listing hours.

**`urgent-channel-separate`** (dimension `trust`, severity critical when the surface invites an
emergency through email or a form, major when the emergency block is absent on a site that sends people
to sea). Emergencies at sea are kept visually and structurally apart from ordinary contact: 112, the
maritime rescue service and VHF channel 16, in a block of their own, with a sentence that the club's
email and forms are not monitored for emergencies. Observed-value form: "contact form subject list
includes 'Emergency'". Evidence C: Spain's maritime rescue service
(https://www.salvamentomaritimo.es/) (G-A18-031). Critical because a form that accepts an emergency is
a dead end at the worst possible moment. When NOT: an institution with no activity on or near water
keeps only 112, in the same separate form.

**`response-time-declared`** (dimension `ux`, **advisory**). The expected reply time for each channel
is stated before sending. Evidence H only (G-A18-026). When NOT: never promise a time the office does
not keep.

## 5. Criteria — money, data and documents

**`cancellation-terms-linked`** (dimension `trust`, severity major). Cancellation and refund conditions
for courses, events and bookings are published and linked from each registration and payment step, in
the same language as the step. Observed-value form: "regatta entry takes payment; no cancellation terms
anywhere on the site". Evidence C: the consumer protection consolidated text, Real Decreto Legislativo
1/2007 (https://www.boe.es/buscar/act.php?id=BOE-A-2007-20555) (G-A17-031). When NOT: conditions not
yet approved by the institution are not published; the registration says terms are available from the
secretary's office until they are.

**`layered-privacy-notice`** (dimension `trust`, severity major, critical when a consent box is
pre-ticked). Every form carries a short first layer next to the submit button (who is responsible, the
purpose, the legal basis, how to exercise rights and, where one exists, the data protection officer's
contact), linked to the full policy. No box is pre-ticked and no consent is requested for what does not
need it. Observed-value form: "form ends with a pre-ticked 'I accept the privacy policy and marketing'
box; no first layer". Evidence C: GDPR art. 13 (https://eur-lex.europa.eu/eli/reg/2016/679/oj)
(G-A18-013, G-A17-033). A pre-ticked consent is a dark pattern under CDIO-02 sec. 4, hence critical.
When NOT: a form that sends nothing personal (a search box) needs no notice.

**`cookie-banner-accessible`** (dimension `ux`, severity critical when it traps focus or hides the
focused element, major otherwise). The cookie banner is operable by keyboard, announced to assistive
technology, does not trap focus when it is not modal, and does not cover the focused element; accept and
reject carry equal prominence. Observed-value form: "banner fixed over the bottom 40 % of the viewport;
tabbing reaches links hidden beneath it". Evidence C: GOV.UK cookie banner
(https://design-system.service.gov.uk/components/cookie-banner/), WCAG 2.2 Focus Not Obscured
(https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html) and the AEPD cookie guide
(https://www.aepd.es/guias/guia-cookies.pdf) (G-A20-023, G-A17-016). When NOT: a site that sets only
strictly necessary cookies shows no consent banner at all, which is the better outcome.

**`transparency-when-obliged`** (dimension `trust`, severity major, assessed only when the obligation is
observed). An entity that receives public aid above the threshold of Ley 19/2013, art. 3.b (more than
100,000 euros a year, or at least 40 per cent of its annual income when that reaches 5,000 euros)
publishes the active-publicity information the law requires (contracts, agreements, grants, accounts,
pay of senior officers) in a findable transparency page. Observed-value form: "club reports 180,000
euros of municipal grants in its annual report; no transparency page". Evidence C:
https://www.boe.es/buscar/act.php?id=BOE-A-2013-12887 (G-A17-006). When NOT: an entity below the
threshold is not obliged and does not build an empty portal; a short page of grants received, dated,
is the honest form if it wishes to publish anything.

**`whistleblower-channel`** (dimension `trust`, severity minor, assessed only when the obligation is
observed). Where Spain's Ley 2/2023 applies to the institution, the internal reporting channel is linked
from the footer or the transparency page, and it is the confidential system the law describes, not a
general mailbox. Observed-value form: "footer link 'Ethics channel' opens a mailto to the general
office". Evidence C: https://www.boe.es/buscar/act.php?id=BOE-A-2023-4513 (G-A17-008). When NOT:
institutions outside the law's scope.

**`downloads-labelled`** (dimension `ux`, severity minor). Every link to a document states its format,
size and, for long documents, number of pages ("Boatyard rules 2026, PDF, 300 KB, 4 pages"). Observed-
value form: "link 'Download' opens a 24 MB PDF on a phone with no warning". Evidence C: GDS on HTML and
PDF, as above (G-A14-043). When NOT: links to HTML pages.

## 6. Floor collisions with CDIO-00

**(a) The footer against the hierarchy ceiling.** A complete legal footer adds a block of small text.
Small is allowed: it is metadata and may sit below body size under CDIO-01 sec. 9. Its contrast may not
drop: the footer text must clear 4.5:1 against its background, and a pale-grey legal block on a dark
navy footer is the commonest failure on institutional sites.

**(b) The emergency block against colour meaning.** It is tempting to mark the emergency block in the
institution's heraldic red. CDIO-01 reserves danger hues for their status, and CDIO-12 keeps the
heraldic palette apart from alert colour. The emergency block is identified by its heading, its icon
with text and its position, and any colour it uses is redundant with those.

**(c) The cookie banner against the conversion floor.** A banner that covers the primary action breaks
CDIO-04's floor before the user has seen the value. The banner may not obscure the primary action or
the focused element; when it must sit over content, it sits at the edge and the page reserves space for
it so that it causes no layout shift.

**(d) The privacy first layer against field bloat.** Four lines of privacy text near the submit button
are not field bloat under CDIO-02; they are information the law requires at the moment of collection.
Their length is counted against the legal minimum, not against zero.

## 7. Common false positives (what CDIO-14 does not flag)

- **No transparency portal on a small private club.** Below the threshold it is not owed.
- **No protection officer on a site with no activities for minors.** The criterion is unassessed.
- **A registry number shown only in the legal notice.** Linked from every footer, that satisfies
  `legal-identity-footer`.
- **No cookie banner.** If only strictly necessary cookies are set, the absence is correct.
- **One contact channel at a two-person institution that says so.** That is the stated exception.

## 8. What was deliberately not universalised

- **The exact statutes.** Spanish article numbers are the evidence, not the criterion. Another country
  replaces each law with its own, and the criterion survives unchanged because it is about what a reader
  can reach.
- **The 100,000 and 40 per cent figures.** They belong to Ley 19/2013 and to Spain. The transferable
  rule is "publish what your transparency law requires, and nothing pretending to be it".
- **Club names.** The observed-practice citations name the institutions where the catalogue saw the
  pattern; they are not endorsements and not templates to copy.

## 9. Evidence, scope and the ladder

Scope claimed: **accountability doctrine for institutional sites**, judged by `cdio-reviewer`. Not
claimed: legal compliance. A pass on this axis means the reader can reach the information; whether the
information is legally sufficient is for counsel.

| rung | status | evidence |
|---|---|---|
| local success | not reached | no CDIO-reviewed site has yet shipped all of sec. 3 to 5 |
| repeated success | not reached | — |
| production reality | not reached | criteria distilled from law and named practice, not from a measured build |
| adversarial survival | not reached | no drill yet seeds a pre-ticked consent or a lapsed badge |
| transfer | partial | law from Spain and the EU, practice from Spanish and British clubs |
| enforcement | judged, not gated | reviewer criteria above; no deterministic gate |

## 10. Contract with the review pipeline

`cdio-reviewer` applies sec. 3 to 5 under CDIO-05 Lens 4 (trust signals) and Lens 5 (conversion path)
whenever the surface represents an institution that meets sec. 1; the verdicts report under the
existing `ux` and `trust` dimensions, so the score formula is unchanged. Criteria whose trigger is
unknown are listed as questions for the Owner, and advisory criteria are listed but never scored.
`cdio-core` routes a request that mentions a legal notice, footer, privacy, cookies, child protection,
transparency, rules, cancellations or emergency contact here first, to CDIO-13 for arrival and language,
and to CDIO-10 for membership and access.
