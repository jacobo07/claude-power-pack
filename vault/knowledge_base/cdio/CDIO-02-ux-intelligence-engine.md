---
id: CDIO-02
name: UX Intelligence Engine
type: dataset
domain: cdio
status: sealed
parent: CDIO-00
---

# CDIO-02 — UX Intelligence Engine

Owns the measurable evaluation of cognitive load, information architecture, and
task flows. Where CDIO-01 asks "can the user see and read this," CDIO-02 asks
"can the user think through this and complete the task without friction or
error." It inherits CDIO-00's value hierarchy: flow serves conversion, and no
flow optimization may drop the surface below the accessibility floor.

## 1. Cognitive load

Cognitive load is the mental effort a surface demands. Excess load is the
silent killer of completion because it does not produce an error message — the
user simply gives up. CDIO-02 makes it measurable.

**Decision points per screen.** Each screen should present a small number of
meaningful choices. Measurement: count the distinct decisions the user must make
to proceed (which plan, which option, which path). A screen with more than a
handful of simultaneous decisions forces comparison-paralysis; the primary path
should reduce to one obvious next action, with alternatives subordinate. The
worst case is a screen where every option looks equally weighted — the user has
no default and must evaluate all of them.

**Choices in a set.** When presenting a set of options (plans, menu items,
filters), the set should be bounded. Measurement: option sets far above roughly
seven items with no grouping or search overload working memory; large sets
should be chunked into labeled groups or made searchable. A pricing page with
three tiers is well-formed; one with nine flat, ungrouped tiers is a finding.

**Information density.** A screen should show what the current task needs and
defer the rest (progressive disclosure). Measurement: content that is not
relevant to the current step and not deferrable is load; a settings screen that
exposes every advanced option at the same level as the common ones buries the
common path. Advanced options belong behind a disclosure, not inline.

**Reading load.** Instructional and value copy should be scannable, not dense
paragraphs. Measurement: a block of more than roughly four lines of unbroken
body copy in a task flow is a scanning failure; it should be chunked, bulleted,
or shortened. The user reads flows in an F-pattern and skips prose.

## 2. Information architecture

Information architecture is how content and functions are organized and labeled
so users can find and understand them.

**Match the mental model.** Categories and labels should reflect how the user
thinks, not how the system is built. Measurement: navigation labeled by internal
system names ("Modules," "Entities") rather than user tasks ("Projects,"
"Billing") is a mental-model mismatch finding. Labels should be the words the
user would use.

**Findability.** A user should reach any key destination within a bounded number
of steps. Measurement: a primary destination that requires more than about three
clicks from the entry point, or that is reachable only through a non-obvious
path, is a findability finding. Depth beyond three levels of nesting for common
tasks signals an over-deep hierarchy.

**Consistent navigation.** The primary navigation should be present and
consistent across screens; the user should always know where they are.
Measurement: a navigation structure that changes between sections, or the
absence of a current-location indicator (active state, breadcrumb), is a finding.
Users who lose their place abandon.

**Labeling clarity.** Every label, button, and link should say what it does.
Measurement: vague labels ("Click here," "Submit," "Learn more" with no object)
force the user to infer; action labels should name the action and object ("Create
project," "Download invoice"). This is both a UX and a conversion criterion.

## 3. Task flows

A flow is the sequence of steps to complete a goal. CDIO-02 evaluates the flow
for length, friction, and recoverability.

**Steps to completion.** The primary task should complete in the fewest
necessary steps. Measurement: count the steps and clicks from intent to done;
each additional step loses a fraction of users. A checkout that spreads five
fields across four pages when one page would serve is a friction finding. Steps
that exist only for the system's convenience (not the user's) should be removed.

**Form field count.** Forms should ask for the minimum required to complete the
task now. Measurement: count the fields against the minimum the task truly needs;
every non-essential field is a drop-off risk. A signup that asks for company
size, role, and phone number before the user has seen value is a
friction-before-value finding (CDIO-00). Optional fields should be marked or
deferred.

**Friction before value.** The surface should deliver value before it demands
commitment. Measurement: a mandatory signup, paywall, or long form that appears
before the user has experienced any value is a finding; the well-formed pattern
lets the user reach a first success, then asks. This directly serves conversion.

**Error prevention and recovery.** Every failure state must have a recovery
path, and the surface should prevent errors where it can. Measurement: (a) a
form that rejects input without saying what is wrong or how to fix it is a
recovery finding; (b) inline validation that catches an error at the field
beats a full-page rejection after submit; (c) a destructive action with no
confirmation or undo is an error-prevention finding; (d) any dead-end state (an
error with no way forward) is critical. Error messages must be specific,
human, and actionable — never a raw code or a blank.

**Feedback and system status.** The surface must tell the user what is
happening. Measurement: an action that produces no visible response (no loading
state, no success confirmation) leaves the user uncertain and prone to
double-submit; every action needs acknowledgement within a fraction of a second,
and any operation over about one second needs a progress indicator.

## 4. Dark patterns (a hard prohibition)

CDIO-02 treats manipulative patterns as findings regardless of their conversion
lift, because they violate CDIO-00's "trust over originality" and the integrity
floor. Measurable instances:

- **Forced continuity** — a free trial that requires a card and auto-charges
  with no reminder. Finding.
- **Confirmshaming** — an opt-out worded to shame the user ("No, I don't want to
  save money"). Finding.
- **Misdirection** — the dismiss/cancel action visually hidden while the
  conversion action is emphasized to the point of hiding the alternative.
  Finding.
- **Hidden costs** — fees revealed only at the final step. Finding.
- **Roach motel** — easy to sign up, deliberately hard to cancel. Finding.
- **Preselected upsells** — add-ons checked by default that the user must
  notice and uncheck. Finding.

A dark pattern is never traded for conversion; it is a trust defect that
compounds into churn and reputational cost.

## 5. The CDIO-02 anti-pattern catalog (with detection rules)

- **Decision overload** — too many equally weighted choices; no default path.
- **Mental-model mismatch** — navigation named by system, not by user task.
- **Deep burial** — a key destination beyond ~three clicks / three nesting levels.
- **Field bloat** — a form asking more than the task minimally requires.
- **Friction-before-value** — commitment demanded before value delivered.
- **Dead-end error** — a failure state with no recovery path. Critical.
- **Silent action** — an action with no feedback or status.
- **Dark pattern** — any manipulative pattern from §4. Trust defect.

## 6. How CDIO-02 feeds the score

Countable checks — decision points, option-set size, step count, form-field
count, click depth — are computed directly from the described flow and are not
opinion. Judgment checks — mental-model fit, label clarity — are supplied by the
reviewer but must cite the specific label or step at fault. Dark patterns and
dead-end errors are classified as critical and, per CDIO-00, block a "done"
verdict on their own. As everywhere in CDIO, the output is a criterion plus an
observed value, so the same flow yields the same verdict for any reviewer.

## 7. Accessibility of the flow (measurable, not optional)

CDIO-01 owns the visual accessibility floor (contrast, target size); CDIO-02
owns the interaction accessibility floor, which is equally measurable and equally
non-tradeable.

**Keyboard operability.** Every action reachable by mouse must be reachable by
keyboard. Measurement: a control that cannot be focused and activated with Tab
and Enter/Space is a critical finding; a modal that traps focus with no Escape
and no way back is a keyboard-trap, critical. Focus order must follow reading
order — a Tab sequence that jumps around the page unpredictably is a finding.

**Labels and names.** Every input and control must have a programmatic name.
Measurement: an icon-only button with no accessible label, an input with only
in-field hint text and no persistent label, or a form field whose label is not
associated with it are findings — a screen-reader user cannot operate what has no
name. In-field hint text is not a label; it disappears on input and fails
low-vision users.

**Motion and timing.** Content that moves, auto-advances, or times out must be
controllable. Measurement: a carousel that auto-rotates with no pause control, or
a session that times out with no warning and no extension, is a finding.
Animation that cannot be reduced for users who request reduced motion is a
finding.

## 8. Worked examples (criterion, observed value, verdict, fix)

**Field bloat.** A newsletter signup asks for first name, last name, company,
role, company size, and email — six fields to send an email. Observed: 6 fields;
task minimum: 1 (email). Verdict: fail, major. Fix: ask for email only; collect
the rest later if ever needed.

**Friction before value.** A design-tool site requires account creation and a
credit card before the user can try a single feature. Observed: commitment (card)
demanded before any value shown. Verdict: fail, major (and the card-for-trial is
a forced-continuity dark-pattern risk). Fix: offer an in-browser trial that
produces a first result, then prompt to save it behind signup.

**Dead-end error.** A checkout rejects a card with the message "Error 402" and no
further guidance. Observed: failure state, no recovery path, non-human message.
Verdict: fail, critical. Fix: state what went wrong ("Your card was declined")
and the next step ("Try another card or contact your bank"), and keep the
already-entered data.

**Decision overload.** A settings page presents 22 toggles at equal weight on one
screen with no grouping. Observed: >7 ungrouped choices, no default path.
Verdict: fail, major. Fix: group into labeled sections, surface the 3 common
settings, and place the rest behind an "Advanced" disclosure.

**Silent action.** Clicking "Save" changes nothing visible; the save succeeded
but the UI gave no confirmation. Observed: action with no feedback. Verdict:
fail, minor (major if it induces double-submits on a costly action). Fix: show an
inline "Saved" confirmation and a disabled-while-pending button state.

These examples are the CDIO-02 template: name the criterion, count or observe the
value, assign severity by rule, and give the concrete fix. An interaction concern
that cannot be stated as a count or an observed state is an impression, and CDIO
does not record impressions.

## 9. Common false positives (what CDIO-02 does NOT flag)

Over-flagging a flow trains teams to remove necessary steps and to distrust the
review. These interaction patterns look like friction but are correct:

- **A necessary field is not field bloat.** A checkout that asks for a shipping
  address is not bloated — the task genuinely needs it. Field bloat is fields the
  task does not need *now*, not every field. Count against the true task minimum,
  not against zero.
- **A required confirmation is not friction.** An "Are you sure?" before deleting
  an account is error prevention, not a friction defect. Confirmation on a
  destructive or irreversible action is the correct pattern; flagging it as a step
  to remove is a false positive.
- **A deliberate multi-step wizard is not a dead-end.** Breaking a genuinely
  complex task into labeled steps with a progress indicator reduces cognitive
  load; it is not the same as spreading a simple task across needless pages. Judge
  step count against task complexity, not against "one page always wins."
- **An anchor tier is not a dark pattern.** Marking one pricing plan "most
  popular" is a legitimate decision aid as long as it is honest. Only a false or
  manipulative anchor is a dark pattern; a truthful recommendation is not.
- **A gated feature that has already shown value is not friction-before-value.**
  Asking for signup *after* the user has produced a first result is the correct
  value-then-ask sequence, not a friction finding. The defect is the gate *before*
  value, not every gate.
- **Progressive disclosure is not deep burial.** Advanced options placed behind a
  clearly labeled disclosure are correct information architecture, not a
  findability failure. Burial is a *common* destination made hard to reach, not a
  rare advanced setting deliberately tucked away.

Before recording a CDIO-02 finding, confirm the step or field genuinely fails the
task rather than serving it. A flow finding must show that the step costs the user
without serving the task; a step that serves the task is not friction, however
much a naive "fewer steps" heuristic would cut it.
