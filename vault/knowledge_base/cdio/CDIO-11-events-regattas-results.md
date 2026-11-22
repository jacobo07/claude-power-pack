---
id: CDIO-11
name: Events, Regattas and Honest Results — the Programme Axis
type: dataset
domain: cdio
status: sealed
governs: [cdio-reviewer, cdio-core]
governed_by: CDIO-00
source: CDIO-GAP-INSTITUTIONAL screen of 961 candidates against CDIO-00..09 (2026-11-22, Owner-approved proposal, units A05, A06, A20, A21) + World Sailing Racing Rules of Sailing Appendix J + schema.org EventStatusType + IETF RFC 5545
evidence: published racing-rules structure and web standards (level C); observed practice on club sites (level C); no measured study of regatta websites (sec. 10)
---

# CDIO-11 — Events, Regattas and Honest Results (the Programme Axis)

An institution's programme is the part of its website that changes every week and that the
most people depend on at once. A regatta page is read by competitors who must know which
version of the sailing instructions is in force, by parents checking when the boats come back
in, by the race committee posting a postponement, and by journalists who need the provisional
leader at five in the afternoon. A social calendar is read by members deciding whether to
come on Saturday. None of these users wants to be impressed; all of them need to know what is
true, since when, and what to do next.

The evaluative datasets cover some of this in general terms. CDIO-03 says an empty state must
explain itself and an error must not dead-end. CDIO-08 asks for tabular figures in numeric
lists. Neither knows that a regatta has a canonical document order fixed by the racing rules,
that a sailing instruction can be amended four times in a weekend and each version matters,
that a result is provisional until the protest time has expired, or that a cancelled event
must stay where people will look for it. CDIO-11 is that axis.

CDIO-11 adds criteria; it never relaxes a CDIO-00 floor. Where it and an older dataset appear
to disagree, CDIO-00 decides.

## 1. Scope

CDIO-11 applies to every public surface of an institution's programme: the season calendar,
the event list, the event detail page, the regatta page and its documents, entry lists and
results tables, and the home blocks that surface any of them. It applies equally to sailing,
rowing, tennis, golf or chess competitions; the regatta is the worked case because it has the
most formal structure. It does not apply to the competition management platforms themselves
(scoring software, entry systems), which are applications under CDIO-02; it does apply to the
moment the institution's own site hands a user over to one.

## 2. Evidence levels used in this dataset

- **A** — a measured study of the behaviour in question. None exists for programme pages.
- **B** — secondary research or an out-of-sector study. Not used here.
- **C** — a published rule or standard, or observed practice on real institutional sites,
  with a source URL that answered when checked.
- **H** — hypothesis. A criterion resting only on H is **advisory**: it is reported with an
  observed value and a recommendation, never produces a failing verdict and never moves the
  CDIO-05 score.

Severity follows CDIO-05 sec. 3. Verdicts report under the existing `visual`, `ux`, `trust`
and `conversion` dimensions.

## 3. The regatta page and its canonical sections

Competitors read a regatta in the order the racing rules organise it. World Sailing's Racing
Rules of Sailing, Appendix J, defines what a notice of race and the sailing instructions
contain, and organising authorities publish around them the same small set of documents.
Following that order on the page means a competitor who has sailed anywhere finds things
where they expect them.

**`regatta-canonical-sections`** (dimension `ux`, severity major). Every regatta page carries
its documents in the canonical order, as a sub-navigation or tabs repeated on each section:
notice of race; sailing instructions; entry (how to enter, fees, deadline); entries (the
list of entered boats); notices and amendments (the official notice board); results. A section
that does not exist yet is shown with its state ("Sailing instructions: to be published by
the race committee before the first warning signal"), never silently omitted, because its
absence is information. Observed value: the sections present, their order and the missing
ones, for example "NoR and results present; SIs, notices and entries absent; no state shown".
When NOT: an informal social race without a notice of race needs an ordinary event page
(sec. 6), and forcing six empty sections onto it would be noise. Evidence: C, World Sailing
Racing Rules of Sailing Appendix J
(https://www.racingrulesofsailing.org/rules?part_id=62), catalogue A05-001.

**`notice-board-online`** (dimension `ux`, severity minor). Official notices to competitors are
published on the page with a number, the date and the time of posting, newest first, and the
page says whether the online board is the official board or a copy of a physical one.
Observed value: notices present and whether each carries number, date and time. When NOT: an
event with no notices yet shows an empty board that says "No notices posted; notices appear
here and on the official board at the race office". Evidence: C, Racing Rules of Sailing
Appendix J (https://www.racingrulesofsailing.org/rules?part_id=62), catalogue A05-002.

**`amendments-numbered-dated`** (dimension `trust`, severity major). Every change to the notice
of race or the sailing instructions is published as a numbered, dated amendment ("Amendment
2 to the SIs, 14 May, 18:30"), the version in force is visibly distinguished, and earlier
versions stay accessible. Overwriting the PDF at the same address with no trace is the
failure: a competitor who downloaded it on Friday cannot know that Saturday's course changed.
Observed value: documents with amendments, whether each is numbered and dated, and whether
the current version is marked. When NOT: a document that has never been amended needs no
amendment register, only its own publication date. Evidence: C, US Sailing notice of race
and sailing instruction guides and templates
(https://ussailing.org/competition/rules-officiating/racing-rules/appendices-kg-and-lg-notice-of-race-and-sailing-instructions-guides-and-templates),
catalogue A05-003.

**`entry-platform-announced`** (dimension `ux`, severity minor). When entry is handled on an
external platform, the entry control names the platform and says the user is leaving the
site before they leave ("Enter on Manage2Sail, opens an external site"), and the regatta page
still states the deadline and the fee in its own text. Observed value: the entry control's
label and destination, and whether deadline and fee are on the institution's page. When NOT:
entry handled on the institution's own site needs no announcement. Evidence: C, observed on
the Royal Ocean Racing Club site (https://www.rorc.org/), catalogue A05-012. The same
hand-off rule for member platforms is CDIO-10 `external-platform-handoff`.

**`entry-close-visible`** (dimension `ux`, advisory). The closing date and time of entry is
shown on the event page and in the event list, with its time zone where competitors travel.
Observed value: whether the closing time is shown and where. When NOT: open entry on the day
needs only that statement. Evidence: H (catalogue A06-031).

**`programme-by-day`** (dimension `ux`, severity minor). The schedule is a list grouped by day,
with times: registration, skippers' briefing, first warning signal, last possible warning
signal, prize giving. Observed value: whether the programme is grouped by day and each item
has a time. When NOT: where the programme is not final, the confirmed items are shown and the
rest are marked as unconfirmed, never filled with plausible times. Evidence: C, US Sailing
templates
(https://ussailing.org/competition/rules-officiating/racing-rules/appendices-kg-and-lg-notice-of-race-and-sailing-instructions-guides-and-templates),
catalogue A05-016.

## 4. Event status: visible, structured, never deleted

An event that is postponed or cancelled is the event most people will look up, because they
heard a rumour and want to know. Deleting its page sends them to a not-found page at the
moment they most need an answer, and the not-found page then reports the wrong failure class,
which CDIO-03 already names as `error-status-collapse`.

**`event-status-visible`** (dimension `trust`, severity major). Every event carries one of a
small set of states in text on its card and its detail page: scheduled, postponed,
cancelled, rescheduled (with the new date), moved online where that applies. The state is
also present in the page's structured data as schema.org `eventStatus`, and the two agree.
Observed value: the visible state, the structured-data state, and any disagreement, for
example "page shows 'Postponed'; structured data still EventScheduled". When NOT: a site
that publishes no structured data is judged on the visible state alone; the structured data
is then a recommendation, not a fail. Evidence: C, schema.org EventStatusType
(https://schema.org/EventStatusType), catalogue A05-027.

**`cancelled-not-deleted`** (dimension `trust`, severity major). A cancelled or postponed event
keeps its address and its page, with the state, the reason when the institution gives one and
the new date when there is one. In lists, it remains in place with its state, visually
subordinate (struck through or muted, with the state word in text so meaning does not rest
on styling). Observed value: the address of a cancelled event and what it returns. When NOT:
after the original date has passed, a cancelled event may leave the upcoming list; its page
stays, linked from the season archive. Evidence: C, schema.org eventStatus
(https://schema.org/eventStatus), catalogue A21-014 and A06-015.

A cancellation must also reach calendars. When an event exported as a calendar file is
cancelled, the institution publishes the same event identifier with the cancelled status and a
higher sequence number, as RFC 5545 provides, so that subscribed calendars update instead of
keeping a ghost event. This is recorded as guidance under `event-ics` below.

## 5. Results: provisional, official, and when

A results table is a trust surface with a legal shape. Under the racing rules a result can
change until protests are heard and the protest time limit has expired, and requests for
redress can change it after that. Publishing a provisional table as if it were final is a
statement about the world that may be false by the evening.

**`results-status-timestamp`** (dimension `trust`, severity major). Every results table states
its status in text (provisional, provisional subject to protests, official or final) and the
date and time it was published or last updated, above the table. Observed value: the status
and timestamp present, for example "no status; no time; table labelled 'Results'". When NOT:
an archive table for a season long closed may show "Final" and the event date only. Evidence:
C, Racing Rules of Sailing (https://www.racingrulesofsailing.org/), catalogue A21-002 and
A05-007.

**`results-table-structure`** (dimension `ux`, severity minor). A series results table shows,
per class, the rank, sail number, boat, helm or owner and club, the points per race, discarded
scores distinguished (conventionally in parentheses, with a legend), scoring codes explained
(DNF, DSQ, OCS) and the net total. Observed value: the columns present and whether discards
and codes are explained. When NOT: a single-race social event may show rank, boat and time
only. Evidence: C, Racing Rules of Sailing Appendix A scoring as published at
https://www.racingrulesofsailing.org/, catalogue A05-005.

**`results-tabular-figures`** (dimension `visual`, severity minor). Points, times and totals
are set in tabular (fixed-width) figures and right-aligned or decimal-aligned, so columns can
be compared down the page. Proportional figures in a results column make 111 and 888 different
widths, and the eye reads alignment as meaning. Observed value: the numeric font feature in
use on the table and the alignment of numeric columns. When NOT: a results summary in prose
("won by two points") is text, not a table. Evidence: C, MDN font-variant-numeric
(https://developer.mozilla.org/en-US/docs/Web/CSS/font-variant-numeric); consistent with
CDIO-08's tabular-figures criterion and the CDIO-01 extension proposed in the same screen
(A12-003).

**`results-table-responsive`** (dimension `ux`, severity minor). On a narrow screen the table
keeps rank, sail number and boat fixed while race columns scroll horizontally inside the
table, with the table's own headers associated to its cells so assistive technology reads
each score with its race. Collapsing a results table into stacked cards loses the comparison
the table exists for. Observed value: the behaviour at 390px width and whether header
association is present. When NOT: a table of three columns fits and needs no strategy.
Evidence: C, W3C WAI tables tutorial (https://www.w3.org/WAI/tutorials/tables/), catalogue
A05-018.

**`results-pending-state`** (dimension `ux`, severity minor). Before the first race is scored,
the results section says so and says when results are expected ("Results pending; first
warning signal 11:00 Saturday; provisional results usually within an hour of the last finish"),
and links the notice board. A blank table, a table of zeros, or a sample table fails. Observed
value: what the results section shows before scoring. When NOT: never excused; a sample table
is additionally a CDIO-03 unfinished-content leak. Evidence: C, NN/g empty-state design
(https://www.nngroup.com/articles/empty-state-interface-design/) and CDIO-03 sec. 7; catalogue
A05-042 (H on its own).

**`results-update-time`** (dimension `ux`, advisory). During a live event, the time of the last
update is visible above the table and the page does not pretend to be live when it is updated
by hand. Observed value: the update time shown. When NOT: a final table. Evidence: H
(catalogue A05-038); the status-and-time requirement that is not advisory is
`results-status-timestamp`.

## 6. The calendar and the event page

**`event-access-badge`** (dimension `ux`, severity minor). Every event in a list and on its
page says whether it is open to the public, open to members and guests, or members only, as a
text badge. Observed value: events checked and those with an access badge. When NOT: a
calendar in which every event has the same access may say so once above the list. Evidence:
C, observed on the Yacht Club de Monaco site (https://www.yacht-club-monaco.mc/), catalogue
A06-011. The facility-level counterpart is CDIO-10 `facility-access-declared`.

**`event-ics`** (dimension `ux`, severity minor). Every event with a confirmed date offers a
per-event calendar file that a personal calendar can import. The file carries a stable unique
identifier, a time stamp and valid start and end (with time zone, or as an all-day date), and
when the event changes or is cancelled the same identifier is reissued with a higher sequence
number and, for a cancellation, the cancelled status. Observed value: whether a calendar file
is offered, whether it validates, and whether an update reuses its identifier. When NOT: an
event whose date is not confirmed offers no calendar file; a file with an invented date
fails `programme-by-day` and the honesty floor together. Evidence: C, IETF RFC 5545
(https://datatracker.ietf.org/doc/html/rfc5545), catalogue A06-004.

**`poster-as-text`** (dimension `ux`, severity major; critical when the poster has no text
alternative). The facts on an event poster (what, when, where, how to enter, price, contact)
are also on the page as HTML text. The poster is an illustration of the page, never the only
carrier of its content. Observed value: the facts that exist only inside the image, for
example "date, venue and entry deadline only in poster.jpg; alt text 'poster'". When NOT: a
purely decorative image, or a poster reproduced in a news archive as a historical object with
a caption (CDIO-12 governs that case). Evidence: C, WCAG 2.2 images of text
(https://www.w3.org/WAI/WCAG22/Understanding/images-of-text.html), catalogue A20-011. Severity
rises to critical because an image carrying the only copy of the information with no text
alternative fails the non-text content requirement, which is an accessibility-floor failure
under CDIO-05.

**`event-card-fixed-fields`** (dimension `ux`, advisory). Event cards and pages present their
facts in a fixed order (what, when, where, access, price, entry, contact), so a reader who has
seen one can scan the rest. Observed value: the field order across three event pages. When
NOT: a one-off ceremony with no entry or price omits those fields rather than showing them
empty. Evidence: H (catalogue A06-012).

**`agenda-list-default`** (dimension `ux`, advisory). The default calendar view is a
chronological list grouped by month; a month grid is optional. Grids hide event titles behind
truncation on phones and present empty days as content. Observed value: the default view at
390px. When NOT: a facility booking calendar, where the empty days are the information, is a
grid by nature. Evidence: H (catalogue A06-001).

**`agenda-type-filter`** (dimension `ux`, severity minor). A calendar with more than one kind
of event (racing, social, school, open to the public) can be filtered by kind, and the filter
state is visible and reachable from the address so it can be shared. Observed value: the
filters offered. When NOT: a calendar with one kind of event or fewer than a handful a month.
Evidence: C, observed on the Yacht Club de Monaco site (https://www.yacht-club-monaco.mc/),
catalogue A06-003.

## 7. Honest empty states and claims about availability

**`agenda-empty-next-step`** (dimension `ux`, severity major). When no upcoming events are
published, the calendar says so plainly and gives a real next step: the last event held, the
season calendar if one is published, and a way to be notified. "No events in August. Next:
Autumn Series, 6 September" passes; an empty grid fails, and an empty grid filled with
sample events fails twice. Observed value: what the calendar shows with no upcoming events.
When NOT: never excused. A dead-end empty state with no navigation is critical under the
CDIO-02 and CDIO-03 rules. Evidence: C, NN/g empty-state design
(https://www.nngroup.com/articles/empty-state-interface-design/), catalogue A21-001 and A06-009.

**`scarcity-needs-record`** (dimension `trust`, severity critical). "Full", "few places left",
"waiting list" and similar states appear only when the institution has a registration record
that supports them. Without that record the page says "Contact the secretariat for
availability". Observed value: each scarcity claim and its source. When NOT: never excused.
A scarcity claim without data is a fabricated signal and an urgency dark pattern, both critical
under CDIO-05 sec. 3. Catalogue A21-015 records it as a hypothesis about club practice; the
criterion does not depend on that, because it is the CDIO-03 honesty floor applied to
availability.

**`home-next-events-real`** (dimension `trust`, advisory). A home block of upcoming events shows
between one and three real events with dates, drawn from the same source as the calendar, and
disappears when there are none rather than showing an empty frame. Observed value: the events
shown and whether they match the calendar. When NOT: an institution with no public programme
has no such block. Evidence: H (catalogue A06-017). If the block shows invented events, that
is not an advisory finding: it is a fabricated signal, critical under CDIO-03.

## 8. Where CDIO-11 collides with the CDIO-00 floors

- **Strike-through as the only state.** Marking a cancelled event by striking it through, or
  by greying it, carries meaning by styling alone. The state word must be present in text,
  and a greyed card must still clear the text contrast floor; a cancelled event is still
  content someone needs to read.
- **Status badges in colour.** Provisional and official, open and members only, scheduled and
  postponed are often colour-coded. Colour may reinforce; the word carries the meaning
  (WCAG use of colour). The CDIO-12 rule that keeps alert red apart from heraldic red applies
  to a cancellation badge as well.
- **Dense tables on touch.** Results tables collide with the 44px target floor when each cell
  is a link to a boat's scorecard. Link the boat name, not every score.
- **Live-update motion.** A results table that animates rows into new positions on update
  must respect reduced motion; under CDIO-07 the update is shown, not performed.

## 9. Common false positives (what CDIO-11 does not flag)

- **A small event with no regatta structure.** A social race with a notice and a start time is
  correctly an ordinary event page; `regatta-canonical-sections` has its own "when NOT".
- **Results shown in the scoring platform's own page.** Linking to an external, official
  results service is acceptable when the institution's page states the status and the update
  time and announces the hand-off; reproducing the table is not required.
- **A past cancelled event missing from the upcoming list.** Leaving the list after the
  original date is correct; the finding is a deleted page, not a filtered list.
- **No calendar file for an unconfirmed date.** That is `event-ics` passing by its own rule.
- **A long notice board.** Twenty numbered notices on a championship weekend is the record
  competitors need, not clutter.

## 10. Evidence, scope and contract

Scope claimed: the public programme surface of an institution, judged by `cdio-reviewer`
under CDIO-05 Lens 4 (trust) and Lens 5 (conversion path), and Lens 6 (mobile) for results
tables. Verdicts use the existing four dimensions; the score formula is unchanged. Not claimed:
the content of racing documents, the correctness of a score, or the behaviour of entry and
scoring platforms.

The evidence base is mostly structural and therefore unusually firm for a design dataset: the
document order comes from the racing rules and their published templates, the status
vocabulary from schema.org, the calendar mechanics from an IETF standard and the text
alternatives from WCAG. What is not firm is everything about presentation preference (list
versus grid, field order, live update time), and each of those criteria is advisory until a
second institution's build or a primary study lifts it. No measured study of regatta or club
calendar pages was found in the screen behind this dataset.

`cdio-core` routes a request that mentions a regatta, race, event calendar, results, entries,
notice of race, sailing instructions, cancellation or postponement here first; to CDIO-10 when
the question is who may attend; to CDIO-12 when an old poster or result is shown as heritage;
and to CDIO-13 when the reader is a visiting competitor arriving by sea.
