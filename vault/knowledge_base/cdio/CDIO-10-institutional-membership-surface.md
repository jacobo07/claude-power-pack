---
id: CDIO-10
name: Institutional Membership Surface — the Audience and Admission Axis
type: dataset
domain: cdio
status: sealed
governs: [cdio-reviewer, cdio-core]
governed_by: CDIO-00
amends: CDIO-04 (page type "institutional multi-audience home", sec. 8)
source: CDIO-GAP-INSTITUTIONAL screen of 961 candidates against CDIO-00..09 (2026-11-22, Owner-approved proposal, units A01, A02, A15, A18, A24) + DRX research report vault/research/2026-11-22_223544_mapa-exhaustivo-objetivo-1000-candidatos-de-patron.md
evidence: observed practice on club sites and published design standards (level C); survey and out-of-sector research from a degraded research run (level B); no measured, club-specific study exists (sec. 11)
---

# CDIO-10 — Institutional Membership Surface (the Audience and Admission Axis)

CDIO-04 was written for surfaces that sell: a landing page with one conversion goal, a
product page, a pricing table. It has no answer for a website whose owner is not trying to
sell anything to most of the people who arrive. A royal yacht club, a marina, a rowing or
tennis club, a professional association or a heritage foundation serves at least four
audiences on the same domain: the public who want to know what the institution is, the
members who come every week to do something specific, the visiting sailor or guest who needs
practical facts once, and the press who need a name, a date and a photograph. Only one of
those four is a conversion audience, and even for that one the conversion is rarely a
purchase: admission usually needs a sponsor, a committee and a waiting period.

Treating such a site as a landing page produces two opposite defects, both observed in the
screen behind this dataset. The first is the club home that shouts "Join now" at members
who are already members, and promises an immediate purchase that the statutes do not allow.
The second is the club home with no goal at all, a wall of equal-weight tiles where the
member cannot find the login and the curious visitor cannot find what membership involves.
CDIO-10 is the axis that sits between them: it names the audiences, gives each a route,
separates acquisition from service, and makes admission and fees honest.

CDIO-10 adds criteria; it never relaxes a CDIO-00 floor. Where it and an older dataset
appear to disagree, CDIO-00 decides. The one older rule this dataset reinterprets rather
than merely extends, CDIO-04's "one page, one goal", is amended explicitly in sec. 8 so that
the reinterpretation has an address.

## 1. Scope

CDIO-10 applies to the public website of any institution that has members and admits new
ones by a process: yacht and sailing clubs, marinas with a member tier, sports clubs,
professional and cultural associations, alumni bodies, heritage institutions with friends'
schemes. It applies to the public pages and to the boundary with the member area, never to
the inside of a member platform, which is an application and is judged under CDIO-02 and
CDIO-08.

It does not apply to a commercial gym or a subscription service where joining is an
ordinary purchase completed online. For those, CDIO-04 already holds unchanged, and several
of the criteria below say so in their "when NOT" line.

## 2. Evidence levels used in this dataset

Every criterion cites the level of evidence it rests on, inline, with its source.

- **A** — a measured study of the behaviour in question. None exists for club websites.
- **B** — secondary research: a published survey or study, or an out-of-sector result,
  reported through the DRX research run of 2026-11-22. That run was degraded (20 of 150
  searches, regex extraction), so its figures are carried with the run's own confidence
  tags and never treated as measured.
- **C** — observed practice on real institutional sites, or a published design standard,
  with a source URL that answered when checked.
- **H** — hypothesis: a plausible pattern without either of the above.

A criterion that rests only on level H is **advisory**: it is reported with an observed value
and a recommendation, and it never produces a failing verdict or moves the CDIO-05 score.
Severity follows CDIO-05 sec. 3. Dimensions are the existing four, so the scorer formula is
unchanged.

## 3. Audience-split information architecture

The commonest failure is building the main navigation out of audiences: "Members",
"Visitors", "Press", "Sailors". People do not reliably know which bucket they are in (a
member who is also a visiting sailor at another club, a parent enrolling a child in the
school), and audience menus duplicate content across buckets until each copy drifts.
Nielsen Norman Group's guidance on audience-based navigation is precisely this, and it is why
the primary navigation stays organised by topic and task: Racing, Harbour, School, The Club.

Audiences still exist, and they get **doors**, not menus: a small set of entry routes on the
home and in the utility bar, each landing on a page that already exists in the task
structure.

**`audience-routes-by-task`** (dimension `ux`, severity major). The primary navigation is
organised by topic or task; audience labels appear only as secondary entry points. Observed
value to record: the primary navigation items in order and the count that are audience
labels, for example "primary nav: Members, Visitors, Press, Contact; 3 of 4 are audiences".
When NOT: an institution whose audiences genuinely use disjoint content with no overlap (a
trade fair with separate exhibitor and visitor sites) may route by audience; record the
absence of overlap as the justification. Evidence: C, NN/g audience-based navigation
(https://www.nngroup.com/articles/audience-based-navigation/).

**`audience-doors`** (dimension `ux`, advisory). The home offers between three and five
audience doors (for example: become a member, member access, arriving by sea, press and
media), each a link to an existing task page, never to a duplicate audience copy. Observed
value: the doors present and their destinations. When NOT: a site with one dominant
audience, such as a members-only club with no public programme, needs no doors; a press door
is unnecessary where the institution publishes no news. Evidence: H (catalogue A01-011); a
pattern seen on several club homes but never measured, so it is advisory.

The visiting sailor's door is defined here only as an entry point. What it must contain
(VHF channel, position, transit berths, harbour office hours) belongs to CDIO-13 and is not
repeated.

## 4. Member access as a persistent utility

For a member the site is a tool used weekly: book a court, see the race notice, read the
newsletter. Member access is therefore **service, not acquisition**, and it lives where
services live, in the utility bar, on every page, labelled in words.

**`member-access-utility`** (dimension `ux`, severity major). A text link labelled as member
access ("Member area", "Members' login") is present in the header utility area of every
page at desktop width, inside the mobile menu at its top level, and repeated in the footer.
Observed value: pages checked, pages where the link was found, and its label, for example
"present on 14 of 18 routes; absent on event detail pages; label is a person icon with no
text". When NOT: an institution with no private area must not show one, and a site that is
entirely private has nothing to separate. Evidence: C, observed on the Royal Ocean Racing
Club (https://www.rorc.org/) and Real Club Náutico de Barcelona (https://www.rcnb.com/)
sites, catalogue A01-002 and A24-001.

**`member-link-resolves`** (dimension `ux`, severity critical). The member access link
reaches a real login or member platform. A login control that opens a form which cannot
authenticate anyone, or a page that says the area is unavailable, is a dead end and a
fabricated affordance. Observed value: the destination URL and what it renders. When NOT:
nothing excuses it; a demo without a real member system describes the member area in prose
and links nowhere, which is honest (catalogue A24-021). Severity is critical by the CDIO-05
sec. 3 rule for broken and dead-end states, not by this dataset's preference.

**`join-login-distinct`** (dimension `conversion`, severity major). Joining and logging in are
two separate controls with different emphasis: the acquisition action ("Become a member",
"Request membership information") may be the primary action of its band, the service
action ("Member area") is a quiet utility link. A single "Join / Log in" control, or a
filled "Members" button that leads to the login, merges two intents and sends prospective
members to a password field. Observed value: the controls found, their labels and their
destinations. When NOT: an invitation-only club that admits nobody by application shows no
join control at all, and "Join" there promises something that does not exist. Evidence: C,
https://www.rorc.org/ (catalogue A01-003).

**`members-only-link-marked`** (dimension `ux`, severity minor). A link whose destination
requires a login says so in its accessible name, with a text suffix ("(members)") or an icon
that carries a text alternative. A lock icon with no text fails, and so does a list of
documents where half open a login wall without warning. Observed value: count of
login-gated links and how many are marked, for example "6 gated links in the regatta page, 0
marked". When NOT: on a page inside the member area every link is gated and marking each
says nothing. Evidence: C, WCAG 2.2 link purpose in context
(https://www.w3.org/WAI/WCAG22/Understanding/link-purpose-in-context.html), catalogue
A01-026.

**`external-platform-handoff`** (dimension `trust`, severity major). When the member area or
any member service lives on another domain or on a third-party platform, the link announces
the destination before the user leaves ("Member access on members.example.org"), and the
destination's login page carries the institution's name and crest so the user can tell it is
the right place. A silent jump to an unbranded third-party login is exactly the shape of a
phishing page, and members are being trained to accept it. Observed value: link text,
destination domain, whether the destination shows the institution's identity. When NOT: a
member area on the same domain and in the same identity needs no announcement. Evidence: C,
https://www.rcnb.com/ (catalogue A24-002, A01-005).

**`access-help-at-login`** (dimension `ux`, severity minor). The login page names a human
route for access problems, the secretariat's telephone or email and its hours, next to the
form, and does so in the same place on every authentication page. "Contact the
administrator" with no contact fails. Observed value: the help text present, or its absence.
When NOT: a platform the institution does not control may not allow the text; record that
the help then sits on the institution's own page immediately before the hand-off. Evidence:
C, WCAG 2.2 consistent help (https://www.w3.org/WAI/WCAG22/Understanding/consistent-help.html),
catalogue A24-010.

**`practical-info-public`** (dimension `ux`, advisory). Information that a visitor, parent or
journalist also needs (opening hours, regulations, contact, the event calendar) is not locked
behind the member login merely because members use it most. Observed value: the public
facts found only behind the login. When NOT: content that is private by right, such as minutes
of the general assembly or the member directory, belongs behind the login. Evidence: H
(catalogue A24-016).

## 5. Admission: from interest to welcome

Admission to a club is a process with a sponsor, a committee and a wait, and the website's
job is to describe that process truthfully before it asks for anything. The research behind
this dataset found the institutional pattern that makes the website's role smaller than a
marketer would assume: in the International Council of Yacht Clubs survey reported by the
DRX run, friends and family were by far the most effective source of new members, the
sailing community second, and only three clubs reported using paid marketing at all
[DERIVED][MEDIUM]. Over two thirds offered no monetary referral incentive
[DERIVED][MEDIUM]. The website, then, is mostly read by someone who already knows a member
and wants to know what happens next. Evidence: B, ICOYC survey via the DRX report.

**The contradiction, reported unresolved.** The same research run carries a second reading
of the survey: that about two thirds of clubs acknowledge referrers publicly, in newsletters,
socially or with dining vouchers [DERIVED][LOW]. Whether public acknowledgement counts as an
incentive is not settled by the source. If it does, the claim "most clubs offer no referral
incentive" is false; if it does not, both readings stand. CDIO-10 therefore defines **no
criterion** about sponsor recognition or referral rewards, and a reviewer must not cite
either reading as support for a finding until the primary survey has been read.

**`admission-numbered-steps`** (dimension `ux`, severity major). The membership page sets out
the admission process as an ordered list of three to six steps, each with a verb and its
typical duration: for example, request information, meet the secretariat, submit the
application with the sponsors' signatures, committee review (meets monthly), payment of the
entrance fee, welcome. Observed value: the steps listed and whether each carries a duration,
or "process described only as 'contact us'". When NOT: where admission is immediate and
online there is no process to number, and inventing steps to look selective is a defect of
its own; where the institution has not confirmed its steps, show the ones it has confirmed
and say the rest are explained by the secretariat. Evidence: C, GOV.UK start-using-a-service
pattern (https://design-system.service.gov.uk/patterns/start-using-a-service/), catalogue
A02-004.

**`sponsor-step-visible`** (dimension `ux`, severity minor). Where the statutes require one or
more existing members to sponsor or endorse an application (aval, proposer and seconder), the
requirement is stated on the membership page before the form, together with what the
applicant should do if they know no member. Observed value: whether the requirement is
stated, and where. When NOT: an institution without a sponsorship requirement says nothing
about one. Evidence: B, ICOYC survey (recommendation by existing members is near-universal
among international yacht clubs, [DERIVED][LOW] for the requirement itself) and C for the
statutes of the club under review when they are published.

**`admission-cta-matches-process`** (dimension `conversion`, severity major). The call to
action names the real next step. When admission needs approval, the action is "Request
membership information" or "Arrange a meeting", not "Join now" or "Become a member today",
which promise an immediate result the institution cannot deliver. This is CDIO-04's
action-and-object label applied to a process with a gate in it. Observed value: the CTA label
and the first thing that happens when it is pressed. When NOT: if joining genuinely completes
online, "Join" is accurate and CDIO-04 governs unchanged. Evidence: C, https://www.rorc.org/
(catalogue A18-037, A02-024); B, the out-of-sector finding in sec. 6 that guidance at the
point of decision is what makes information usable.

**`interest-form-short`** (dimension `ux`, severity minor). The first form asks only what the
secretariat needs to reply: name, email, the category of interest and a message. Address,
date of birth, boat details and sponsor names belong to the formal application, which is a
separate step. Observed value: field count of the first form and which fields belong to a
later step. When NOT: an institution whose only form is the formal application, with no
information step, is judged by CDIO-02 field-bloat rules instead. Evidence: C, GOV.UK
question pages (https://design-system.service.gov.uk/patterns/question-pages/), catalogue
A02-011.

**`confirmation-says-what-next`** (dimension `ux`, severity minor). After the form is sent the
page says what happens next, who will make contact and in roughly what time. "Thank you" on
its own fails. Observed value: the confirmation text. When NOT: never excused; when the
timing is unknown, say who will reply and how to follow up. Evidence: C, GOV.UK confirmation
pages (https://design-system.service.gov.uk/patterns/confirmation-pages/), catalogue A02-013.

**`no-payment-before-approval`** (dimension `trust`, advisory). Where admission is decided by a
committee, the web flow ends in a request and never in an online payment. Observed value:
whether a payment step precedes the decision. When NOT: a deposit that the statutes require
with the application and that is refunded on refusal may be taken, provided the refund is
stated at the point of payment. Evidence: H (catalogue A02-036).

**`membership-faq-real`** (dimension `ux`, severity minor). A membership FAQ answers the
questions applicants actually ask (do I need a boat, can I bring guests, is there an entrance
fee, how long is the wait, can my children use the school) in short answers, in an accessible
disclosure pattern or on one page. Observed value: the questions present and whether each has
a substantive answer. When NOT: invented questions that nobody asks, written to carry
marketing copy, fail the criterion they pretend to satisfy; an institution that has not
supplied answers gets no FAQ, not a FAQ of guesses. Evidence: C, GOV.UK accordion
(https://design-system.service.gov.uk/components/accordion/), catalogue A02-017.

**`benefits-as-facts`** (dimension `conversion`, advisory). Each membership benefit is a
concrete fact (access to the pool, the member rate for a berth, reciprocal access at named
clubs), never an adjective ("an exclusive lifestyle"). Observed value: benefits listed and
how many are verifiable facts. When NOT: a heritage institution whose benefit is genuinely
belonging may say so once, plainly. Evidence: H (catalogue A02-008).

## 6. Fees and the honest consult state

Fees are where an institutional site is most tempted to invent and most damaged by it. A
plausible entrance fee written into a design because the slot looked empty is a fabricated
statement about the world, and CDIO-03 already classes a fabricated signal as an
integrity-floor violation. The rule is short: **a fee appears only when it comes from a
verified source; otherwise the page says honestly that fees are given on request, and guides
the reader to the request.**

The research is also clear that publishing a number is not, by itself, what helps. In the
DRX run's out-of-sector evidence, price transparency alone was barely used (about 2 % of
health-plan members used transparency tools) and behaviour changed only when transparency
came with simplified presentation and guidance at the point of decision [OBSERVED][HIGH,
out-of-sector]. Evidence: B. The transferable lesson for a club is that a well-guided
"consult" state is not a failure of transparency, and a bare price table with no explanation
is not a success of it.

**`fee-from-verified-source`** (dimension `trust`, severity critical). Every fee, quota, price
or discount shown can be traced to a source the institution supplied or published (its fee
schedule, its general assembly resolution, a price list with a date). Observed value: each
fee shown and its source, or "entrance fee 3,000 EUR; no source in the content supplied".
When NOT: never excused. A fee with no source is removed, and the consult state below takes
its place. Severity is critical by the CDIO-05 rule for fabricated trust signals and the
CDIO-03 honesty floor.

**`fee-consult-state-guided`** (dimension `conversion`, severity minor). Where fees are not
published, the page says so and says why in one sentence (they depend on category, age or
boat length; they are set yearly by the assembly), names the channel that gives them and,
where possible, what the reader should have ready (category of interest, boat length). A
bare "price on request" with no channel fails. Observed value: the consult text and channel.
When NOT: where verified fees are published, the consult state is unnecessary. Evidence: B,
out-of-sector price transparency research above; catalogue A02-003, A21-004 (H on their own).

**`fee-components-separated`** (dimension `trust`, advisory). Where fees are published, the
entrance fee and the periodic fee are shown separately, with their period and whether tax is
included, so that the reader can compute the real first-year cost. Observed value: the fee
components shown. When NOT: a single all-inclusive fee needs no breakdown. Evidence: H
(catalogue A02-002); the general rule that the full price must be computable before
commitment is already sealed in CDIO-04 sec. 4 and applies with its own severity.

**`member-and-public-price`** (dimension `conversion`, severity minor). Services sold to
members and to the public at different rates (berths, courses, the restaurant, facility
hire) show both rates side by side rather than on separate pages, so neither audience has to
guess which rate applies. Observed value: the services with dual rates and how they are
shown. When NOT: a service with one rate for everyone. Evidence: C, observed on the Real Club
Náutico de Valencia site (https://www.rcnv.es/), catalogue A24-017.

## 7. Declared access per facility

Institutional sites routinely describe a restaurant, a pool, a gym or a terrace without
saying who may use it. The visitor who arrives to find a members-only door, and the member
who never learns that guests are allowed, are both products of that silence.

**`facility-access-declared`** (dimension `ux`, severity major). Every facility or service
page states in its first block who may use it, in one of a small number of declared
categories: open to the public, members and their guests, members only, or by booking for
anyone. The category is text, not colour alone and not an icon alone. Observed value: the
facility pages checked and those that state access, for example "restaurant page: no access
statement; pool page: 'members and guests' in second paragraph". When NOT: an institution in
which every facility has the same rule may state it once, site-wide, near the facilities
index. Evidence: C, observed on the Yacht Club de Monaco site
(https://www.yacht-club-monaco.mc/en/), catalogue A15-008.

## 8. CDIO-04 extension: the institutional multi-audience home

This section amends CDIO-04 sec. 3 with a new page type. It is recorded here, with the
criteria it governs, so that CDIO-04's sealed text stays as written and the amendment has a
single address.

**Page type: institutional multi-audience home.** The home page of an institution whose
visitors arrive with several legitimate goals of which only one is conversion. Typical
signals: a member area exists; admission is by process; the institution publishes a public
programme (regattas, events, a school); and the site also serves visiting users and the press.

**How "one page, one goal" applies to it.** CDIO-04 says a landing page pursues a single
conversion goal. On this page type the rule is applied per **audience band**, not per page:

1. The home is composed of bands, each a horizontal section with one audience and one goal
   (the public band explains what the institution is; the programme band shows the next real
   events; the membership band explains admission; the visiting band routes to arrival
   information).
2. **One goal per band.** A band that asks the member to log in and the visitor to request
   admission at equal weight has split intent, exactly as CDIO-04 describes for a whole page.
3. **One primary action per screen**, unchanged from CDIO-04 sec. 1. Where two bands share a
   viewport, only one of their actions is filled; the other is subordinate.
4. **The first viewport states the institution, not an offer.** Its question set is CDIO-03's
   three-second test reworded for an institution: what is this, is it the right one, where do
   I go next.

**`home-band-one-goal`** (dimension `conversion`, severity major). Each band of an
institutional home serves one audience and one goal, and no viewport carries more than one
filled primary action. Observed value: bands in order with their goal, and any viewport with
two primary actions. When NOT: a page that is not an institutional multi-audience home
(a regatta landing page, a school enrolment page) is a single-goal page under CDIO-04
unchanged. Evidence: the one-primary-action rule is sealed in CDIO-04 sec. 1 and carries its
own evidence; the band composition itself is H (catalogue A01-011), which is why the failure
this criterion scores is the double primary action, never the absence of a particular band.

**`home-no-sales-pressure-on-members`** (dimension `conversion`, severity minor). The home
does not present an acquisition action as the dominant element of the first viewport when the
institution's admission needs approval. Observed value: the dominant action of viewport one.
When NOT: an institution in an active, published recruitment campaign may lead with
membership for its duration. Evidence: C, consequence of `admission-cta-matches-process`.

A reviewer applying CDIO-04 to such a home records the page type in the review header, so
that "no single conversion goal" is not reported as a finding against a page that is
correctly built to serve four audiences.

## 9. Where CDIO-10 collides with the CDIO-00 floors

- **Honesty before completeness.** The design instinct to fill every slot (a fee, a member
  count, a founding year, a waiting time) collides with CDIO-03's honesty floor. An empty fee
  is a consult state; an empty count is no count. The integrity floor wins every such
  collision and the criteria above are written so that the honest state passes.
- **The utility link over a photograph.** Member access lives in the header, and
  institutional homes often lay that header transparently over a hero photograph. The link's
  text must clear 4.5:1 against the worst point of the image behind it, which in practice
  needs a scrim token. A beautiful, illegible member link is an accessibility-floor failure
  and therefore critical under CDIO-05, whatever this dataset's own severity for the link.
- **Lock icons and colour badges.** Marking members-only links and access categories with an
  icon or a colour alone collides with the use-of-colour and non-text content rules. The text
  carries the meaning; the icon decorates it.
- **Two audiences, one target.** Utility links are small by convention. On touch they still
  need the 44px target floor, which a dense utility bar often misses.

## 10. Common false positives (what CDIO-10 does not flag)

- **No visible join control on an invitation-only club.** That is `join-login-distinct`
  passing by its own "when NOT", not missing conversion.
- **No published fees.** A guided consult state is correct, not hidden pricing. CDIO-04's
  hidden-cost finding is about fees revealed late, not about fees given on request before
  any commitment.
- **A quiet member link.** Service actions are supposed to be subordinate. The finding is a
  member link that is absent or unlabelled, never one that is not the primary action.
- **Audience doors absent.** They are advisory; a well-organised task navigation that lets
  each audience find its route is not a finding.
- **A long admission page.** Six steps with durations, sponsor rules and an FAQ is the
  content the reader came for, not choice overload.

## 11. Evidence, scope and contract

Scope claimed: the public surface of membership institutions, judged by `cdio-reviewer`
under CDIO-05 Lens 5 (conversion path) and Lens 4 (trust), with verdicts reported under the
existing `ux`, `trust` and `conversion` dimensions so the score formula is unchanged. Not
claimed: the inside of member platforms, statutes, or the merits of any admission policy.

The evidence is honest about its ceiling. No candidate in the screen behind this dataset had
measured or academic evidence specific to clubs. Level C criteria rest on observed practice on
named club sites and on public-sector design standards that solve the same problem (starting
a service with a process, contacting a department, confirming what happens next). Level B
rests on one survey and one out-of-sector study, carried through a degraded research run, and
one contradiction in that survey is reported unresolved in sec. 5. Level H criteria are
advisory and stay so until a second institution's build or a primary source lifts them.

`cdio-core` routes a request that mentions a club, an association, members, admission,
sponsorship, a member area or fees on request here first, then to CDIO-11 for events and
results, CDIO-12 for history and heraldry, and CDIO-13 and CDIO-14 for visiting users and
institutional compliance.

## Evidence update 2026-11-23 (second deep-research run)

Source run: vault/research/2026-11-23_000309_evidencia-medida-o-acad-mica-estudios-ux-baymard-n.md (25 queries, full HTML extraction, 9 OBSERVED and 17 DERIVED learnings, 1 unresolved contradiction). Nothing in this run is sector-specific measurement for yacht clubs; every measured figure below is cross-sector and is cited as such. No criterion changes severity and no advisory criterion is promoted, because none gained in-sector A or B evidence.

- `interest-form-short` and `admission-numbered-steps`: cross-sector form data reported via userpilot.com/blog/saas-signup-flow (secondary report of HubSpot figures: about 25 percent completion at 3 fields against about 12 percent at 8 fields) [OBSERVED][MEDIUM, cross-sector, secondary]. It supports keeping the first contact to the minimum a club needs to reply and moving everything else after the first reply. It does not support any particular field count for a club admission form.
- `join-login-distinct`: progressive enrolment as documented by Okta (help.okta.com, Identity Engine progressive enrolment) collects the minimum at first sign-in and the rest later [D, vendor documentation, corroborates only].
- Membership retention baselines: one source reports first-year renewal near 75 percent and overall renewal of 85 to 87 percent for membership organisations (campai.com member retention rate), another reports repeat-purchase rates of 28 to 30 percent as normal for membership organisations (hightperformance.com). CONTRADICTION, unresolved: the two figures probably measure different things (renewal against ancillary purchases). No criterion rests on either figure.
- New advisory criterion `berth-allocation-rules-published` (advisory, evidence C): a club that allocates berths or keeps a waiting list publishes how allocation works (for example seniority, membership category, vessel length) as a dated document; observed practice: the Aeolian Yacht Club berth rules and procedures PDF (aeolianyc.org). Observed value to record: present with date, present undated, absent. Severity when reported: minor. When NOT: a club that does not allocate berths, or whose allocation is run entirely by a port authority that publishes its own rules, which should be linked instead. Never render a waiting-list position, occupancy figure or allocation outcome that does not come from a verified record (`fee-from-verified-source` and the CDIO-03 honesty floor govern). The run's claim that written tiered policies cut disputes and raise retention comes from vendor material and is recorded as a hypothesis only.