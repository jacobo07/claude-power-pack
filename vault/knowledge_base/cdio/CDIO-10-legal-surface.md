---
id: CDIO-10
name: Legal Surface — the Pages Every Website Owes Its Visitors
type: dataset
domain: cdio
status: sealed
governs: [cdio-reviewer, cdio-core]
governed_by: CDIO-00
source: General-Legal/legal-templates (CC0 1.0, commit 6d6805425eabd41bed86fc1e2ec51612760f716c, vendored at legal-templates/), absorbed 2026-10-08 on Owner instruction "usarlos siempre que hagamos webs"
evidence: executable checker run read-only against four real Owner websites on 2026-10-08 (see sec. 8)
---

# CDIO-10 — Legal Surface (the pages every website owes its visitors)

CDIO-00 through CDIO-09 judge how a surface looks, how it behaves, and whether it earns trust.
None of them asks whether the website has the pages a visitor is entitled to: who is behind the
site, what it does with their data, what it stores in their browser, and on what terms they use
it. A landing page can score 95 under CDIO-05 and still have no privacy policy, a cookie banner
that only offers "Accept", or a terms page that still reads "[CompanyName]". Each of those is a
trust failure of the most literal kind, because each is a promise the site makes or omits to the
person reading it, and each can carry a regulatory consequence for the Owner's client.

CDIO-10 closes that gap. It absorbs the twelve attorney-drafted templates General Legal released
under CC0 (vendored verbatim in `legal-templates/`, see its `NOTICE.md`), decides which of them a
website needs and when, records what they do not cover for a business in Spain or the EU, and
makes their presence, completeness and reachability part of the CDIO done-gate. The Owner's
instruction was that these templates are used every time a website is built; this dataset is
what turns that instruction into a check rather than a habit.

CDIO-10 adds criteria; it never relaxes a CDIO-00 floor. Where it and an older dataset appear to
disagree, CDIO-00 decides. It is not legal advice and it never says a page is legally sufficient.
It says whether the page exists, whether it was filled from facts, whether a visitor can reach
it, and whether it matches the jurisdiction it claims.

## 1. Scope and the Owner's policy

**Every website built under the Power Pack carries a privacy page and a terms page.** This is the
Owner's policy, set on 2026-10-08, and it is stricter than the law in some places on purpose. A
brochure site with no form and no analytics still processes personal data in its server logs
(IP addresses, user agents), still sets the terms under which its content is used, and still
benefits from saying so. The policy removes the judgement call "does this small site need one?",
which is exactly the call that leaves the small sites without one.

The other documents are conditional, and each condition is observable:

- **Cookie notice** — required when the site uses any cookie-setting third-party tracker or
  embed (analytics with cookies, advertising pixels, session-recording tools, video embeds that
  set cookies). In the EU and Spain the notice is not enough on its own; a consent mechanism must
  block those trackers until the visitor accepts (sec. 4).
- **Aviso Legal (legal notice)** — required for every website operated by a business established
  in Spain, whatever it sells, under LSSI-CE art. 10. No template exists for it in the vendored
  set; sec. 4 lists its contents.
- **Consumer sale terms** — required when the site sells to consumers in the EU or Spain
  (pre-contract information, price with taxes, delivery, the 14-day withdrawal right with its
  model form, guarantees). No template exists for it either. A site that sells only to
  businesses declares so (`--b2b` on the checker), because a scan cannot tell who the buyer is.
- **Data Processing Addendum** — required when the product is a SaaS that processes personal data
  on behalf of business customers. It is a contract, not a marketing page, but it must be
  reachable (commonly at a legal or trust route) so a customer's privacy team can review it.

The remaining vendored templates are not website pages and CDIO does not route to them for a web
build: the master services agreement (offered alongside a DPA for B2B SaaS), the two NDAs, the
California offer letter, the advisor agreement, and the HIPAA business associate agreement
(relevant only to a U.S. product that handles protected health information). They are vendored
because the Owner asked for all twelve and because one verbatim copy is easier to keep honest
than a partial one.

What CDIO-10 does not cover, and must not be read as covering: sector regulation (financial
services, health, gambling, alcohol, children's services), accessibility statements required of
public bodies, terms for marketplaces where third parties sell, and any contract negotiated with
a specific counterparty.

## 2. The template catalogue and the routing table

The vendored templates are written in markdown with two marks for what must be completed:
highlighted fields wrapped in `<mark>` tags, and bracketed instructions such as `[INSERT …]`,
`[ADD]`, `[DATE]` or `[CompanyName]`. Two of them also open with a header row addressed to the
drafter ("TEMPLATE PRIVACY POLICY AND COOKIE NOTICE (GDPR compliant for U.S. Company with no
establishment in the EEA or UK)"), and the terms template contains a bracketed drafting note
about state-specific provisions. All of these must be resolved before publication; none of them
is content.

Routing by jurisdiction (the checker's `plan` subcommand prints the same table with paths):

| page | us | eu | es |
|---|---|---|---|
| privacy | privacy-policy-us | privacy-policy-gdpr, restructured (sec. 4) | as eu, in Spanish, with the form first layer |
| terms | terms-of-use | terms-of-use without arbitration and waivers | as eu, consumer forum preserved |
| cookies | cookie-notice | cookie-notice plus a blocking consent banner | as eu, per the AEPD cookie guide |
| legal notice | not required | judged per member state (sec. 4) | required, no template |
| consumer sale terms | advisable, not gated | required when selling to consumers, no template | as eu, TRLGDCU |
| DPA (SaaS only) | dpa-us | dpa-global | dpa-global |

Three rules govern how a template becomes a page:

1. **The template is a structure, not a text to paste.** Sections that do not apply to the site
   are removed, not left in with a note. A privacy policy that describes a mobile app the client
   does not have, or chat features the site does not offer, misstates what the site does, which
   is the opposite of what the page is for.
2. **The General Legal credit footnote stays.** CC0 does not require it; the authors ask for it,
   and keeping it costs a single line.
3. **The upstream copy is never edited.** Filling happens inside the website being built. When
   upstream publishes a new version, it is re-vendored at the new commit and the `NOTICE.md`
   commit line changes in the same change.

## 3. The criteria (what CDIO-10 can fail)

Each criterion names the dimension it reports under, so the deterministic scorer in CDIO-05 sec. 4
weighs it with no change to the formula. Severity follows CDIO-05 sec. 3, which names a missing
or unfilled legal page as a legal-floor failure and therefore critical. Criteria marked
mechanical are emitted by `modules/cdio/legal_surface.py`; the rest are judged by
`cdio-reviewer`, each with an observed value.

**`legal-page-present`** (dimension `trust`, severity critical). Every page required by sec. 1
for this site and jurisdiction exists at a route a visitor can load. Mechanical: a path segment
of the site must match the page's slug set (privacy, privacidad, politica-de-privacidad; terms,
terminos, condiciones-de-uso; cookies, politica-de-cookies; aviso-legal, legal-notice; and so
on). Observed-value form: "no legal_notice page: no path segment matches aviso-legal or
legal-notice". A policy that exists only as a PDF link or inside a modal with no route is judged
by the reviewer; the checker will report it missing, and the reviewer may record a pass with the
observed location.

**`legal-fields-filled`** (dimension `trust`, severity critical). No legal page contains an
unfilled template field: a `<mark>` element, a bracketed instruction, a bracketed field name taken
from the vendored templates' own vocabulary, a run of blank underscores, the template's sample
telephone number, or a drafting note addressed to the person filling it. Mechanical, and the
vocabulary is read from the vendored templates at run time rather than written by hand, so a
field the checker's author never thought of is still caught. Observed-value form:
"app/privacy/page.tsx: 7 unfilled fields, first [CompanyName], [DATE], [INSERT Chatbot provider]".
An unfilled field on a published legal page is a fabricated statement in the most literal sense:
it is the authoring prompt presented to a visitor as the company's commitment.

**`legal-facts-from-owner`** (dimension `trust`, severity critical). Every fact filled into a
legal page — company name, legal form, tax identifier, registered address, contact email, data
protection contact, registry data, effective date, the list of processors and cookies, retention
periods — came from the Owner or the client, not from inference. Judged. Observed-value form:
"NIF B12345678 on the aviso legal does not appear in any brief, message or file supplied by the
client". A field that nobody supplied stays visibly unfilled, so `legal-fields-filled` blocks the
site, which is the intended outcome: a blocked site is a question to the Owner, an invented NIF
is a false statement published under the client's name.

**`legal-page-linked`** (dimension `trust`, severity critical). Each legal page is linked from
the site's persistent chrome, normally the footer of every page, so it is reachable "easily,
directly and permanently" (the LSSI-CE wording, and a good test anywhere). Mechanical, by
heuristic: some file other than the page must reference its route. Observed-value form: "terms:
no file outside the page references /terminos". Critical, because a page no visitor can reach
discharges none of the obligation it exists for; it is the legal surface's dead end. The
heuristic cannot see a link assembled at run time, so when the reviewer observes the link in the
rendered footer it records a pass carrying that observation, and the checker's verdict is
superseded by the rendered one rather than deleted.

**`consent-before-tracking`** (dimension `trust`, severity critical). In the EU and Spain, no
cookie-setting tracker loads before the visitor has accepted it. Mechanical in one direction
only: a known tracker signature with no consent mechanism anywhere in the site is a FAIL. When a
consent mechanism is present, the checker reports UNVERIFIED, never PASS, because only a real
browser can show the tracker's request is held until acceptance. Observed-value form: "Google tag
and Meta Pixel present, no consent mechanism found", or, from a browser run, "gtag request fired
240 ms after load with no interaction".

**`reject-as-easy-as-accept`** (dimension `ux`, severity critical). The consent banner offers a
reject action on its first layer, at the same level and with comparable prominence to accept; no
cookie is pre-ticked; scrolling or continuing to browse is not treated as consent; and withdrawing
consent later is as easy as giving it (a persistent link or control). Judged on the rendered
banner. Observed-value form: "first layer shows a filled 'Aceptar' and a text link 'Configurar';
reject is only on the second layer". This is a dark pattern under CDIO-05 sec. 3 and is critical
for that reason as much as for the regulator's.

**`jurisdiction-fit`** (dimension `trust`, severity major). The page matches the jurisdiction the
site operates in. Judged. Typical failures: the U.S. privacy template on a Spanish site (CCPA
rights, no lawful bases, no supervisory authority); the GDPR template left in its "U.S. company
with a Notice to European Users" framing for a company established in Spain; the terms template's
arbitration clause, class-action waiver or Delaware or California forum left in for consumers in
the EU. Observed-value form: "terminos page retains 'binding individual arbitration' and a
class-action waiver; site sells to consumers in Spain".

**`form-first-layer`** (dimension `trust`, severity major). In Spain, every form that collects
personal data shows the first information layer beside it — controller, purpose, legal basis,
recipients, rights, and a link to the full policy — and any marketing consent is a separate,
unticked checkbox. Judged. Observed-value form: "contact form at /contacto has a single 'Enviar'
with no controller or purpose stated and a pre-ticked newsletter box".

**`cookie-notice-matches-trackers`** (dimension `trust`, severity major). The cookie notice
names the cookies and vendors the site actually sets, with purpose and duration, and names no
vendor the site does not use. Judged against the rendered site's storage and network activity.
Observed-value form: "notice lists Google Analytics; site loads Hotjar and Meta Pixel, neither
listed". The vendored template's table ships with "[ADD]" in every vendor cell, which is caught
mechanically; this criterion catches the table filled with the wrong vendors.

**`legal-language-matches-site`** (dimension `trust`, severity major). The legal pages are
written in the language the site addresses its visitors in. A Spanish-language site with English
legal pages fails, because a policy the visitor cannot read informs no one. Translating the
vendored English templates is drafting, not formatting, and a translated page is recorded as
"translated, pending review" until a qualified person has read it.

**`not-claimed-as-reviewed`** (dimension `trust`, severity critical). No page, badge or copy
states or implies that the site's legal texts were drafted or reviewed by a lawyer, unless the
Owner supplies evidence that one did. The templates were drafted by attorneys; the filled pages
were not reviewed by anyone because of that. Observed-value form: "footer reads 'Legal texts
reviewed by our legal team'; no review exists". This is a fabricated trust signal under CDIO-05
sec. 3, and is critical for that reason.

**`us-opt-out-link`** (dimension `trust`, severity major). For a U.S. site that shares personal
data for cross-context behavioural advertising (advertising pixels are the common case) and whose
operator meets the California thresholds, a "Do Not Sell or Share My Personal Information" or
"Your Privacy Choices" link is present and the site honours the Global Privacy Control signal.
Judged, because the thresholds are facts about the business that a scan cannot see. Observed-value
form: "Meta Pixel present, operator confirmed above CCPA threshold, no opt-out link in footer".

**`last-updated-stated`** (dimension `trust`, severity minor). Each legal page states its
effective or last-updated date, and that date is real. Observed-value form: "privacidad page has
no date". An invented date is a `legal-facts-from-owner` failure, not this one.

**`legal-page-readable`** (dimension `visual`, severity major). A long legal page is still a page
a person must be able to read: real headings that match the index, an index with working
anchors when the document runs past a few screens, body text that clears the CDIO-01 contrast and
size floors, and a line measure inside the CDIO-01 range. Observed-value form: "privacy page is
9,400 words in a single block with no headings; body 13px at 4.1:1". A legal page is where
designers most often stop applying the system, because it feels outside the product.

## 4. Jurisdiction: what the U.S.-drafted templates do not cover

The vendored templates were drafted for U.S. technology companies. The GDPR-enhanced privacy
policy is explicit about its own scope in its first line: a U.S. company with no establishment in
the EEA or UK. Most of the Owner's clients are businesses established in Spain. For them the
templates are a strong structure and an incomplete text. This section records what must be added
or changed; it lists sources so the person filling the page can check them, and it is not legal
advice.

**Privacy policy (GDPR art. 13; for Spain also LOPDGDD, Organic Law 3/2018).** For a controller
established in the EU, GDPR is the main body of the policy, not an annex for European visitors.
It must state the controller's identity and contact details, the data protection officer's
contact where one is appointed, each purpose with its legal basis, the legitimate interests
relied on where that is the basis, the recipients or categories of recipients, any transfer
outside the EEA and its safeguard, the retention period or the criteria for it, the rights of
access, rectification, erasure, restriction, portability and objection, the right to withdraw
consent, the right to complain to the supervisory authority (in Spain, the AEPD), whether
providing the data is a legal or contractual requirement, and any automated decision-making. The
template's California and U.S. state sections are removed for a site with no U.S. audience, not
left in. LOPDGDD art. 11 allows layered information, which is why forms carry a first layer
(`form-first-layer`) linking to the full policy.

**Cookies (ePrivacy Directive art. 5(3); for Spain LSSI-CE art. 22.2 and the AEPD cookie
guide).** Storing or reading non-essential information on the visitor's device requires prior,
informed consent. The vendored cookie notice is the information half. The consent half is a
banner that blocks the trackers until acceptance, offers reject on the first layer with the same
prominence as accept, treats neither scrolling nor continued browsing as consent, and lets the
visitor withdraw as easily as they accepted. Strictly necessary cookies (session, load balancing,
the consent record itself) are exempt from consent but still disclosed. The template's paragraphs
on Flash local shared objects describe a technology browsers no longer run and are removed.

**Legal notice (LSSI-CE art. 10).** Every website of a business established in Spain must make
available, easily, directly, permanently and free of charge: the legal name, the tax identifier
(NIF), the registered address, an email address or other means of direct contact, the
commercial-registry data (register, volume, folio, sheet) or other public registry where the
business is registered, the administrative authorisation and supervising body where the activity
requires one, the professional body, title and state of issue for a regulated profession, and
prices with taxes and delivery costs where prices are shown. No vendored template covers it. In
Germany and Austria an Impressum plays the same role under national law; other member states vary,
so outside Spain the reviewer judges it rather than the checker requiring it.

**Terms of use (Unfair Terms Directive 93/13/EEC; Rome I art. 6; for Spain TRLGDCU, Royal
Legislative Decree 1/2007).** The vendored terms bind users to individual arbitration, waive the
right to class actions and jury trial, and choose a U.S. forum. Against consumers in the EU these clauses
are unenforceable and their presence is itself a defect: they are removed, and the consumer's own
courts and law are preserved. Business users can be bound by a chosen forum; the reviewer checks
which audience the site addresses.

**Consumer sale terms (Consumer Rights Directive 2011/83/EU; for Spain TRLGDCU arts. 97-98 and
the withdrawal provisions).** A site that sells to consumers must give the pre-contract
information (identity, main characteristics, total price with taxes, delivery costs and
timing, payment, the 14-day right of withdrawal with its conditions and the model withdrawal
form, the legal guarantee, after-sales service) before the order is placed. No vendored template
covers it. The EU online dispute resolution platform link that older sites carry should not be
added: the platform was discontinued in July 2025.

**United States.** The vendored U.S. templates are fit for purpose with their fields filled. The
two judged additions are the opt-out link and Global Privacy Control handling (`us-opt-out-link`)
for operators that meet the California thresholds, and the removal of any section describing
data practices the site does not have.

## 5. Filling discipline

Filling a legal template is the same act as generating any other text a person will read, and
it fails in the same three ways (the generated-content evidence gate in the Owner's rules names
them): copying fields without judging them, letting a plausible default stand in for a fact,
and rendering an absent value as content. The discipline that follows:

- **Facts come from the Owner or the client, never from inference.** A company name may be on the
  site already; its legal name, NIF and registered address usually are not. Ask once, in one list,
  at the start of the build: legal name, legal form, NIF, registered address, contact email, data
  protection contact, registry data, processors used (hosting, email, analytics, payments),
  trackers used, retention periods, and whether the site sells to consumers.
- **An unanswered field stays unfilled and blocks the site.** That is what the checker is for. It
  converts a missing fact into a visible question instead of a published guess.
- **Remove what does not apply.** Optional clauses in brackets are decisions, not decoration. A
  clause about a mobile app, an AI chatbot or training models on user data stays only if the site
  really does that, and its presence is then a commitment the client must keep.
- **Record the vendors the site actually loads.** The cookie and processor lists are read from the
  built site, not from what the Owner remembers installing, because a forgotten embed is the most
  common inaccuracy in a cookie notice.
- **Date the page with the date it was published,** and change the date when the content changes.

## 6. What was deliberately not universalised

The test applied to every candidate rule was the one CDIO-06 sec. 9 and CDIO-09 sec. 6 use: does
it survive a change of brand, platform or jurisdiction? These did not, and are recorded so
nobody imports them as doctrine:

- **The U.S. dispute-resolution framework.** Binding arbitration, the class-action and jury-trial
  waivers, the Delaware or California forum. Valid choices for some U.S. businesses; defects for
  EU consumers.
- **The California-specific notices and the offer letter.** State law, one state.
- **The HIPAA business associate agreement.** One U.S. sector.
- **The Flash local shared object paragraphs.** A technology that no longer runs.
- **Any particular consent management platform.** The criteria judge behaviour (blocking, reject
  parity, withdrawal), not a vendor. The checker recognises several vendors' signatures only to
  know that a mechanism exists.
- **The slug lists.** They are the routes this checker recognises today. A site with a legal page
  at an unrecognised route is reported missing, and the reviewer records the real location as a
  pass; the slug list is extended when that happens twice.

## 7. Traps that transfer

- **A highlight stripped is not a field filled.** Converting the template's markdown to a page
  often drops the `<mark>` tags and keeps the brackets, so "[CompanyName]" survives as plain text.
  The checker looks for both forms, and for the bracketed field names the templates themselves
  define.
- **The drafting header is not a title.** The privacy templates open with a table row addressed to
  the drafter. Rendered as the first line of the page, it tells every visitor the policy is a
  template for a U.S. company.
- **A cookie banner that loads after the trackers is decoration.** Banner code added to a layout
  that already loads a tag manager in the document head looks complete in a screenshot and
  consents to nothing. Only a browser run with an empty profile, watching the network before any
  click, shows the order.
- **A route that renders is not a page that is linked.** Building the page at the right route and
  forgetting the footer link passes a route check and fails the visitor.
- **A localised site has more than one legal page per kind.** A bilingual site needs the privacy
  page in each language, each filled, each linked from its own locale's footer. The checker scans
  every matching route, so an untranslated or unfilled second locale is caught.
- **Absence of a detected tracker is not absence of tracking.** Detection is by signature over
  the site's own files. A tracker injected by a tag manager container at run time, or by a vendor
  outside the signature list, is invisible to a static scan; the report says so in its notes
  rather than passing silently.

## 8. Evidence, scope and what is still planned

Scope claimed: **presence, completeness, reachability and jurisdiction fit of a website's legal
pages**, judged by `cdio-reviewer` and gated mechanically where a static scan can decide. Not
claimed: legal sufficiency of any page, correctness of the filled facts, or runtime behaviour of
a consent banner.

On 2026-10-08 the checker was run read-only against four of the Owner's websites with
jurisdiction es:

- Club Náutico (web), Mytilus Belgian Restaurant and Regina Margherita: no privacy page, no terms
  page and no aviso legal in any of them; a text search of each repository for legal wording
  confirmed no legal content under another name. Verdict BLOCK, score 25, three criticals each.
- TUA-X (frontend, 523 files): privacy and terms present in both locales, filled, and linked;
  aviso legal missing; a checkout was detected, so consumer sale terms are required unless the
  Owner declares the product business-only. Verdict BLOCK, score 50.

| rung | status | evidence |
|---|---|---|
| local success | reached | checker found real, confirmed gaps on four real sites |
| repeated success | not reached | no site has yet been built from the vendored templates |
| production reality | not reached | no rendered banner has been checked in a browser under these criteria |
| adversarial survival | partial | the gate's drills go red on an unfilled field, a missing page, a tracker with no consent mechanism and an unlinked page |
| transfer | not reached | one Owner, one checker |
| enforcement | gated | `legal_surface check` exits non-zero on BLOCK; `cdio-reviewer` folds its verdicts in |

A browser-based consent check (empty profile, record requests before any interaction, fail if a
known tracker fires) is **PLANNED**. It needs a real browser and a site that has a banner to judge;
it becomes worth building with the first site built under this dataset. Until then a present
consent mechanism is reported UNVERIFIED, which is the honest reading.

## 9. Common false positives (what CDIO-10 does not flag)

- **A bracketed cross-reference kept as text.** The privacy template refers to its own sections
  in brackets. Copied verbatim it is flagged as unfilled; the fix is to turn it into a link,
  which is also the better page.
- **Business-only sales without consumer terms.** Declared with `--b2b`, not a defect.
- **No cookie notice on a site with no cookie-setting tracker.** Not required; strictly necessary
  cookies are disclosed in the privacy page.
- **Cookieless analytics without a banner.** Analytics the vendor documents as cookieless
  (Plausible, Vercel Analytics, Fathom) need disclosure in the privacy page, not consent.
- **Legal pages styled more plainly than the marketing pages.** Plain is fine; unreadable is not.
  `legal-page-readable` judges headings, contrast, size and measure, never decoration.
- **The General Legal footnote.** Kept on purpose; it is not a third-party trust leak.

## 10. Contract with the review pipeline

`cdio-reviewer` applies sec. 3 under CDIO-05 Lens 4 (trust signals) whenever the surface under
review is a website or a web app reachable by the public. It runs
`python -m modules.cdio.legal_surface check <site_root> --jurisdiction us|eu|es` (with `--saas`
and `--b2b` as the Owner has declared) and folds the emitted verdicts into its own before the
score is computed, then judges the criteria the checker cannot decide. The verdicts report under
the existing `trust`, `ux` and `visual` dimensions, so the score formula is unchanged, and a
critical from this dataset forces BLOCK like any other. `cdio-core` routes any request to build,
launch or ship a website here first, runs `legal_surface plan` to list the pages and their source
templates, and asks the Owner for the facts in sec. 5 before the pages are written. The criteria
grammar, the checker's red drills and every wiring point named in this section are pinned by
`tools/test_cdio_legal.py`.
