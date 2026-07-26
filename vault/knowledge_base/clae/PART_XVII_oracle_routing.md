---
title: "CLAE Part XVII — Oracle Routing"
family: clae
part: XVII
depends_on: [XVI]
feeds: [XIX, XX, XXI, XXV]
status: SEALED
date: 2026-07-26
---

# Part XVII — Oracle Routing

## 1. Purpose

Part XVI established which questions must go outward and who has standing to answer them. This Part
is the mechanics: **when** to ask, **how** to present the question, and how an answer becomes durable
evidence rather than a remark that must be purchased again.

The framing that organizes it: a routed question has three independent failure points, and a
question can be correctly identified as an oracle question, sent to the correctly-standing oracle,
and still produce a worthless answer at any one of them.

- **Timing** — asked outside the window in which the answer can be both informed and consequential.
- **Presentation** — the oracle cannot reach the question, or reaches a different one.
- **Recording** — the answer decays into a remark and the question returns.

Part XVI's warning that the channel is scarce and non-replenishable makes each of these expensive.
An ask spent badly is not merely wasted; it withdraws attention that the next question needed.

## 2. Timing — the answerable window

**Asked too early**, there is nothing concrete to judge. An oracle presented with an intention
answers about the intention, and intentions are cheap to endorse — they contain none of the
compromises that make the real artifact worth judging. The answer will not survive contact with what
gets built, and the question returns later having consumed an ask.

**Asked too late**, the decision is already sunk. The question has become a request for
ratification, and the oracle usually knows it. The cost of answering *no* has been raised by the
asker's own investment, which means the answer is shaped by that investment rather than by the
judgment. This is the more damaging error and the harder one to see, because it produces an answer
that looks entirely valid.

> **Asking too early wastes an ask. Asking too late corrupts one.**

The window opens when a concrete instance exists that carries the properties in question — Part IV's
instantiation condition, applied to what is put in front of the oracle. It closes when the cost of
acting on an unfavourable answer exceeds the value of having asked.

The practical consequence is that the window is often narrower than the schedule that surrounds it,
and that a question worth asking should be asked before it is comfortable to ask it. A team that
asks when the work feels ready is asking at the moment the answer can least afford to be negative.

## 3. Presentation — what the oracle needs

Six things. The first three are usually supplied and the last three are usually not, and the last
three are what determine whether the answer is calibrated.

1. **The artifact itself**, not a description of it. Part IV §C2's argument applies unchanged: a
   description conveys only what its author knew to include, and an oracle asked to judge a
   description is judging the author's model.
2. **The specific question**, not an invitation to react. *What do you think* returns whatever the
   oracle noticed first, which is a function of legibility rather than importance.
3. **The alternatives actually available.** An oracle shown one option can express approval or
   unspecified dissatisfaction, and neither is a judgment between things.
4. **What the system already knows** — the measurements taken, the residuals recorded. Without it,
   the oracle may spend their answer on an instrument question the system could have answered, which
   is exhaustion arriving through the presentation rather than through the routing.
5. **The consequence of each answer** — what actually changes. An oracle who does not know what
   their answer causes cannot calibrate it, and will tend toward the answer that seems safest.
6. **What it costs to change later.** This is the field most often omitted and the one that most
   changes answers. A judgment about something cheap to revise and a judgment about something
   effectively permanent are different judgments, and an oracle not told which one they are making
   will make the first.

## 4. Presentation anti-patterns

**The wall.** Everything relevant supplied at once. The oracle answers whatever they could parse,
which is whatever was most legible — and legibility and importance are unrelated.

**The leading frame.** Alternatives presented with one fully developed and the others sketched. The
asymmetry in preparation is read as an asymmetry in merit, and the answer ratifies the preparation.

**The disguised instrument question.** A question a procedure should answer, wrapped in judgment
language so that it feels like a legitimate ask. It consumes the channel and returns a worse answer
than the procedure would have.

**The single option.** *Is this acceptable?* The available answers are yes, or a demand for
unspecified work. Neither is a judgment, and the second is usually declined out of politeness.

**The abstraction.** A summary substituted for the artifact, because the artifact is large or
inconvenient to present. What is judged is the summary, and the answer is evidence about the summary
— per §6, precisely and only that.

## 5. Answer types, and the escalation ladder

Answers differ in reusability, and this difference is the strongest available lever against oracle
exhaustion.

| Type | Form | Reusability |
|---|---|---|
| **Verdict** | Acceptable or not | Single-use — this artifact, this version |
| **Ordering** | This before that | Reusable within the comparison class |
| **Threshold** | Acceptable at this level | Reusable as a floor candidate, per Part X §7 |
| **Criterion** | What matters here is this property | **Reusable across a whole class of future questions** |

> **Ask for a criterion where a verdict would do.**

A verdict answers one question and is consumed. A criterion resolves every future question of that
shape, and turns what would have been a stream of oracle traffic into an instrument question the
system can answer for itself — which moves Part XVI's boundary in the direction that Part XVI §6
established nobody moves it.

The extra cost is small. An oracle giving a verdict has already formed the criterion; asking them to
state it converts a single answer into a durable rule. The reason it is rarely done is that verdicts
are what get asked for, and the asker is optimizing for the immediate decision rather than for the
channel.

A threshold answer is the second-best outcome and has a specific onward path: it becomes a floor
candidate under Part XI's derivation, with the oracle's reasoning as the recorded consequence — which
is exactly the derivation an imported number lacks.

## 6. An answer is evidence about what was shown

The subtlety that makes oracle records honest:

> **An oracle answer is evidence about the presentation, not about the artifact in general.**

If the artifact was presented partially, along one dimension, at one moment, then the answer is valid
for that presentation and no further. An answer to *is this acceptable* given a summary is evidence
that the summary was acceptable. Extending it to the artifact is exactly the projection failure of
Part VI §6, arriving in the evidence record.

Every oracle record therefore carries **what was shown** alongside what was answered. Without that
field, the answer's scope is unbounded in practice and will be stretched to cover whatever later
needs covering — usually in good faith, by someone who was not present and cannot know what the
oracle actually saw.

Combined with Part XVI §8's validity scope, an answer is bounded in two dimensions: by time, and by
presentation. Both are needed. An answer that has not lapsed but is being applied to something the
oracle never saw is as invalid as an expired one, and considerably harder to notice.

## 7. Re-asking

Legitimate grounds are three: the artifact changed materially along the judged dimension; the scope
of validity lapsed; the constituency changed.

Not a ground: the answer was inconvenient. Re-asking until a preferred answer arrives is the oracle
equivalent of Part XI's floor being lowered to admit the work, and it destroys the channel faster
than over-asking, because it teaches the oracle their answers are provisional.

The useful instrument here is a **re-ask ledger** — how often each question class returns. A high
re-ask rate is diagnostic rather than merely wasteful:

- The **scope** was set too narrowly, so answers expire before their usefulness does.
- The question was really an **instrument question** all along, and the repeated asking is the signal
  that something should be built.
- Or the presentation is failing, and each answer is about a different partial view.

All three are actionable, and none is visible without counting.

## 8. Economics

The channel is the scarce resource and is budgeted like correction capacity, per Part VIII §3.

**Prefer criteria over verdicts**, per §5 — the primary lever, because it reduces future demand
rather than rationing current demand.

**Batch by constituency, not by artifact.** Five questions to one oracle cost far less than one
question to each of five, and the batched questions share context that would otherwise be rebuilt
each time. Batching by artifact does the opposite: it fragments across constituencies and rebuilds
context repeatedly.

**Spend the ask on what cannot be instrumented.** An ask consumed by something a procedure could
answer is not merely inefficient; it is a withdrawal from the account that funds the questions with
no alternative.

## 9. Boundary

These mechanics apply to oracle questions. Questions that fail Part XVI's four marks should not be
routed at all, and improving their presentation is optimizing a mistake.

Nor do they apply to approvals, which are authority over an action rather than judgment about a
property. An approval has its own timing and its own record, and dressing an approval as an oracle
question produces a record that captures permission and loses the judgment — Part XVI §4's
conflation, arriving through the routing layer.

## 10. Evidence — routing in this compendium's own construction

The clearest available example is this build, and it is instructive in both directions.

**Timing — correct.** The architecture question was routed after Phase 0 had measured the overlap
and before any family was constructed. A concrete instance existed to judge — a measured
duplication finding and four costed options — and the cost of acting on any answer was still
bounded, since nothing had been built. That is §2's window, entered deliberately.

**Presentation — mostly correct.** Four alternatives were shown rather than one, each with its
consequence, and what the system already knew was supplied: the measured surface, the ownership
table, the ten verified gaps. The recommendation was marked as such rather than concealed. What was
*not* supplied was §3's sixth item — what it would cost to change the decision later — and that
omission matters more here than usual, since the choice determined a construction order that
subsequent Parts have been built on.

**Recording — partially correct.** The answer was recorded in the resumption file as an active
decision with its consequences, which is durable. But it was recorded as a **verdict** — three new
families and five extension passes — and no **criterion** was extracted.

That last point is the honest finding, and §5 is what makes it visible. The Owner's answer plainly
rested on a criterion: something like *build only where measurement showed a genuine gap, and extend
rather than duplicate where an owner already exists*. Had that criterion been asked for and recorded,
it would govern the family decisions still to come for the remaining two families without another
ask. As recorded, it governs one decision, and the same question will return.

This is not a failure of the ask; it is the ordinary shape of asking, and it is why §5's ladder is
stated as a standing preference rather than as advice. — OBSERVED from this session's own record.

The stack's other routing surfaces are consistent with this pattern: reserved decisions are captured
as permissions with their outcomes, and none of them records a criterion that would let the system
answer the next instance itself. — Reserved-decision behaviour OBSERVED; the criterion assessment
INFERRED against §5.

## 11. Failure modes

| Failure | Mechanism |
|---|---|
| **Asked too early** | An intention judged rather than an artifact; the endorsement does not survive construction |
| **Asked too late** | Ratification sought after the decision is sunk; the answer is shaped by the asker's investment |
| **The wall** | Everything supplied; the most legible thing is answered, not the most important |
| **Leading frame** | Preparation asymmetry read as merit asymmetry |
| **Single option** | Only yes or unspecified dissatisfaction available; neither is a judgment |
| **Description for artifact** | The summary is judged, and the answer is evidence about the summary |
| **Verdict where a criterion was available** | A single-use answer purchased where a reusable one cost the same |
| **Unbounded presentation scope** | What was shown is unrecorded, so the answer is stretched to cover what the oracle never saw |
| **Re-ask until favourable** | Answers treated as provisional; the channel learns its judgments do not bind |
| **Batched by artifact** | Context rebuilt per constituency instead of shared per oracle |

## 12. Detection signatures

1. **The comfortable ask.** Questions routed at the point the work feels ready, which is the point at
   which a negative answer is most expensive. §2's late error, visible in the schedule.
2. **The unanimous approval history.** An oracle channel that has never returned an unfavourable
   answer. Either the questions are ratifications, or the framing is leading.
3. **The verdict-only record.** Every recorded answer is acceptable-or-not. No criterion was ever
   extracted, so the channel's load cannot fall.
4. **The recurring question class.** The same shape of question returning repeatedly — §7's ledger
   signal, and each of its three causes is fixable.
5. **The absent what-was-shown field.** Records with answers and no presentation. Their scope is
   unbounded in practice.

## 13. Trap seeds — for Part XXII

- **T-CLAE-RATIFICATION-ASK** — a question routed after the decision is sunk, returning an answer
  shaped by the asker's investment and indistinguishable from a valid judgment.
- **T-CLAE-LEADING-ALTERNATIVES** — options presented with unequal preparation, so the answer
  ratifies the effort rather than the merit.
- **T-CLAE-VERDICT-ONLY** — verdicts purchased where criteria were available at the same cost, so
  oracle load never falls and the boundary never moves outward.
- **T-CLAE-UNBOUNDED-ANSWER-SCOPE** — what was shown is unrecorded, so the answer is later applied to
  an artifact the oracle never saw.
- **T-CLAE-REASK-UNTIL-FAVOURABLE** — repeated asking after an inconvenient answer, teaching the
  channel that its judgments are provisional.

## 14. Rule seeds — for Part XXIII

- **PR-CLAE-ASK-IN-THE-WINDOW** — questions are routed once a concrete instance exists and while the
  cost of acting on an unfavourable answer is still bounded. A question routed after that point is
  recorded as a ratification, not as a judgment.
- **PR-CLAE-SHOW-THE-ARTIFACT** — the artifact is presented, not a description. Where only a summary
  can be shown, the answer's scope is bounded to the summary in the record.
- **PR-CLAE-PRESENT-ALTERNATIVES-EVENLY** — options are presented with comparable preparation, each
  with its consequence and its cost to reverse.
- **PR-CLAE-ASK-FOR-THE-CRITERION** — where a verdict would serve, ask for the criterion behind it.
  A criterion resolves the class; a verdict resolves the instance.
- **PR-CLAE-RECORD-WHAT-WAS-SHOWN** — every oracle record carries the presentation alongside the
  answer. An answer without it has unbounded scope in practice.
- **PR-CLAE-REASK-ON-GROUNDS-ONLY** — re-asking requires material change, lapsed scope or changed
  constituency. Inconvenience is not a ground, and the re-ask rate per question class is tracked.

## 15. Eval seeds — for Part XXIV

- **Window probe.** For each routed question, compare its date against the point the decision became
  expensive to reverse. Questions routed after it were ratifications.
- **Answer-type census.** Classify recorded answers by type. An all-verdict distribution means the
  channel's load can only grow.
- **Presentation-completeness probe.** Check each record for §3's six items, especially the cost to
  change later. Its absence is the most consequential omission.
- **Re-ask-rate probe.** Count returns per question class and diagnose each against §7's three
  causes.
- **Scope-stretch probe.** For each answer in current use, compare what it is being applied to
  against what was shown when it was given.
- **Unfavourable-rate probe.** Compute the proportion of unfavourable answers. A rate near zero
  indicates ratification or leading framing rather than good work.

## 16. Production Reality Gate seed — for Part XXV

**Oracle Routing Gate.** An oracle answer may be used as evidence only when its record carries the
question as asked, what was shown, the alternatives presented, the answerer and standing, the date,
the validity scope, and the answer type. Answers whose presentation is absent are bounded to the
narrowest artifact the record can establish. Answers obtained after the decision became expensive to
reverse are recorded as ratifications and do not satisfy a judgment requirement anywhere in the
family.

## 17. Pseudoflow — routing a question

Confirm first that this is an oracle question by Part XVI's four marks. If it is not, do not improve
its presentation; build the instrument.

Identify the window. The earliest defensible moment is when a concrete instance exists carrying the
properties in question. The latest is before the cost of acting on an unfavourable answer exceeds the
value of asking. Ask nearer the opening than the closing, and accept that this will feel premature.

Assemble the presentation: the artifact itself; the specific question; the alternatives actually
available, prepared comparably; what the system already knows and has already measured; what each
answer causes; and what it will cost to change the decision later. Omitting the last is the most
common way an answer is miscalibrated.

Before sending, check whether a criterion would serve where a verdict is being requested. If it
would, ask for the criterion — the oracle has already formed it, and stating it costs them little
and resolves the class.

Record the answer with the question as asked, what was shown, the alternatives presented, the
answerer and their standing, the date, the validity scope and the answer type. The what-was-shown
field is what bounds the answer's scope in practice.

Where the answer was a threshold, carry it to Part XI's derivation as a floor candidate with the
oracle's reasoning as the recorded consequence — that reasoning is exactly what an imported number
lacks.

Do not re-ask without material change, lapsed scope or changed constituency. Track the re-ask rate
per class, and when one is high, determine which of the three causes applies rather than continuing
to pay for it.

## 18. Integration

Part XVI supplies the routing decision and the standing requirement this Part implements. Part VII
§6's value-laden frontier decisions are the largest source of traffic here, and §5's ladder is what
prevents that traffic from growing without bound — a criterion extracted from one frontier decision
orders many future frontiers. Part X §7 and Part XI receive threshold answers as derived floor
candidates. Part XIX's evidence-gated autonomy consumes oracle records as evidence and inherits §6's
presentation bound: an autonomous agent may rely on an answer only within what the oracle was shown.
Part XX's phase closure treats an unanswered in-window question as an open closure obligation.

Outside the family, the owner-facing queue is the transport, and the reserved-decision surfaces are
noted as capturing permissions with their outcomes but no criteria.

## 19. Open questions

1. Can the window's closing edge be identified before it passes? §2 defines it by the cost of acting
   on an unfavourable answer, and that cost is usually estimated by the party whose investment
   creates it. — UNKNOWN, and the weakest point in the Part.
2. Do criteria obtained from an oracle remain valid as the artifact class evolves, or do they drift
   like references? §5 treats a criterion as durable across a class; Part V established that
   externally-sourced objects go stale, and there is no reason a criterion would be exempt. —
   HYPOTHESIS: criteria need horizons too, which is not currently required anywhere.
3. Is the unfavourable-rate signature reliable? A near-zero rate may indicate ratification, or a team
   that asks well and prepares thoroughly. Distinguishing them from the rate alone may not be
   possible. — UNKNOWN.

## 20. Institutional writeback

Five trap seeds, six process-rule seeds, six eval seeds and one production gate.

Three portable results. **Asking too early wastes an ask; asking too late corrupts one** — and since
the late error produces an answer that looks valid, the window should be entered while it still feels
premature. **Ask for the criterion where a verdict would do** — the oracle has already formed it,
stating it costs almost nothing, and it converts a stream of future questions into something the
system can answer itself, which is the one lever that moves Part XVI's boundary in the direction
nothing else moves it. And **an answer is evidence about what was shown** — recording the
presentation alongside the answer is what stops a bounded judgment from being stretched, in good
faith, to cover an artifact the oracle never saw.

The self-example in §10 is the Part's own demonstration: this build routed its architecture question
at the right moment, presented it evenly, recorded it durably — and took a verdict where a criterion
was there for the asking, so the same question will return for the two families still to come.
