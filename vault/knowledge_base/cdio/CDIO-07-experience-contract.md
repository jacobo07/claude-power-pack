---
id: CDIO-07
name: Experience Contract — the Behavioural Axis
type: dataset
domain: cdio
status: sealed
governs: [design-md, design_gate, cdio-reviewer]
governed_by: CDIO-00
source: internal — CDIO-00 §10 boundary, CDIO-02 §3/§7 and CDIO-03 §7 thresholds made refusable (sealed 2026-08-24)
---

# CDIO-07 — Experience Contract (the Behavioural Axis)

CDIO-01 through CDIO-05 judge a surface **at rest**: what it shows, how it reads,
where the eye lands, whether the path completes. CDIO-06 chooses the family the
surface will inhabit **before** a token is written. Neither axis answers the
question a user actually experiences, which is not *what does this look like* but
**what does this do when I touch it, and what does it do while I wait.**

That question has been deliberately out of scope. CDIO-00 §10 draws the line
explicitly: CDIO owns the measurable, and "brand character, emotional tone, the
rightness of a specific creative direction" belong to the human authority. The
line is correct and this dataset does not move it. What it corrects is a
mis-sorting on the CDIO side of it: **a large part of what teams call "feel" is
not taste at all — it is behaviour that was never declared.** Whether a click
acknowledges within a perceptible moment, whether an operation past a second
shows progress, whether motion carries meaning or decorates, whether a success is
celebrated or merely confirmed, whether the interface has a character that speaks
— every one of those is a decision somebody makes, and almost none of them are
written down anywhere. Undeclared, they are settled by whoever writes the
component last, and the product acquires a feel nobody chose.

The inversion this dataset enforces, stated in the form CDIO-06 established:

> A default is not slop. A default without a declared intent is slop.
> **Expression is not delight. Expression without a declared experience objective
> is noise.**

Both halves are load-bearing. A surface with no feedback at all fails this axis.
A surface that celebrates a saved draft with a full-screen animation fails the
**same** check, for the same reason: the behaviour was not the one the product
declared it wanted. An axis that can only ever ask for *more* animation is not
engineering; it is a preference with a schema, and it is exactly the cargo-cult
this dataset exists to refuse.

## 1. The experience contract (the declared vocabulary)

A project declares its experience contract once, in `DESIGN.md` front-matter,
under `experience:`. The contract is **optional**. A project that declares
nothing is not in violation — it is unassessed, and the gate says so rather than
inventing a verdict. Only a *declared* contract can be enforced, and only a
declared contract can be broken.

Twelve fields, each chosen because it changes a decision an implementer would
otherwise make silently:

| Field | What it settles | Values |
|---|---|---|
| `expressiveness` | The ceiling on all expressive behaviour on this surface | `none` · `restrained` · `moderate` · `high` |
| `motion_budget` | How much animation a component may carry | `none` · `low` · `medium` · `high` |
| `reduced_motion` | What a reduced-motion user gets instead | `equivalent` · `absent` |
| `feedback_latency_ms` | The acknowledgement ceiling for a user action | integer, milliseconds |
| `progress_threshold_ms` | Past this, an operation must show progress | integer, milliseconds |
| `waiting` | What the interface does while it works | `skeleton` · `spinner` · `progress` · `optimistic` · `none` |
| `progress_language` | How advancement is expressed | `numeric` · `staged` · `indeterminate` · `none` |
| `success_posture` | What completion feels like | `silent` · `confirm` · `acknowledge` · `celebrate` |
| `error_posture` | What failure feels like | `terse` · `explain` · `explain_and_recover` |
| `celebration_policy` | Which events may be celebrated at all | `never` · `milestones_only` · `first_success` · `unrestricted` |
| `character_policy` | Whether the product has a voice or a figure | `none` · `voice_only` · `illustrated` · `persistent_character` |
| `trust_posture` | How much the surface must feel predictable | `standard` · `elevated` · `critical` |

`premium_posture` is deliberately **absent from this list**. Perceived premium is
already owned, measurably, by CDIO-03 §3 — consistency, restraint, finish,
imagery — and a second field asserting it here would create two authorities over
one property. A project that wants a premium feel declares `expressiveness:
restrained` and clears CDIO-03; that is the whole mechanism, and it already
exists.

## 2. The picker (three questions, one contract)

Answer in order. The first question sets the ceiling and the other two can only
narrow it, never raise it — which is what keeps the picker from being a ratchet
toward more expression.

1. **What is the cost of a mistake on this surface?**
   Irreversible or financial → `trust_posture: critical`, `expressiveness:
   restrained` or `none`, `celebration_policy: never`.
   Recoverable → continue.
2. **Does the user return to this surface by habit, or arrive at it with a task?**
   Habit, repeated over days → progress and small acknowledgement earn their
   cost; `success_posture: acknowledge`, `celebration_policy: milestones_only`.
   Task, then leave → `success_posture: confirm`, `expressiveness: restrained`.
3. **Is the task itself intimidating, or is the interface the whole product?**
   Intimidating → the budget is spent on calm: `waiting: skeleton`,
   `error_posture: explain_and_recover`, `progress_language: staged`.
   The interface *is* the product (a creative tool, a consumer app) → expression
   is part of the value; `expressiveness: moderate` is defensible and must still
   clear every floor in §5.

A contract reached by this tree is a **hypothesis**, exactly as CDIO-06 §2 says a
family is. The picker chooses the intent; the review decides whether the
execution honoured it.

## 3. Abstention is a first-class outcome

`expressiveness: none` is a complete, passing, correct contract. An internal
admin table, a batch-operations console, a compliance export screen — these are
surfaces where the right amount of expressive behaviour is zero, and a system
that cannot record that answer will keep proposing animation to interfaces whose
users want speed and nothing else.

This mirrors the CDICF selector's design (`modules/cdicf/selector.js`), where
abstention carries a remedy code rather than an empty result, because "nothing
matched" and "nothing should be installed here" have opposite remedies. The same
distinction holds here: **a surface with no declared contract** and **a surface
that declared it wants no expression** are different states, and collapsing them
would make the second unreachable.

Two consequences follow, and both are enforced rather than recommended:

- A gate may never treat `none` as a lower score than `high`. The contract sets
  the target; conformance to it is the only thing measured.
- A recommendation engine may never propose raising `expressiveness`. Raising it
  is a product decision made by a human at the picker, never a finding produced
  by a review.

## 4. Refusal runs in both directions

This is the mechanism that separates the axis from taste. A declared contract
makes four things refusable that were previously unrefusable in either direction:

**Under-delivery.** An action with no acknowledgement inside
`feedback_latency_ms`; an operation past `progress_threshold_ms` with no progress
cue; an error rendered as a raw code where the contract declared
`explain_and_recover`. CDIO-02 §3 and CDIO-03 §7 already call each of these a
finding — in prose, with no executable check anywhere. The contract supplies the
threshold the check needs.

**Over-delivery.** A component whose motion exceeds `motion_budget`; a
celebration on an event the `celebration_policy` excludes; a persistent character
on a surface that declared `character_policy: none`. Before the contract, none of
these could be refused at all, because there was no declared value to exceed.

**Incoherence.** A contract can be wrong on its own terms, and that is checkable
without seeing a single rendered pixel: `expressiveness: high` alongside
`reduced_motion: absent`; `celebration_policy: unrestricted` alongside
`trust_posture: critical`; a `motion_budget` above what the declared
`expressiveness` permits. An incoherent contract is refused at declaration time,
before any surface is built against it.

**Manipulation.** `celebration_policy` and `character_policy` are the two fields
that can be turned against the user — a streak that shames, a character that
pressures, a celebration engineered to make a purchase feel like an achievement.
CDIO-02 §4 already prohibits dark patterns and does not trade them for
conversion. CDIO-07 adds no new prohibition and creates no exemption: an
expressive behaviour that satisfies this contract and violates CDIO-02 §4 is a
critical finding, and the contract is not a defence.

## 5. Where each posture collides with the CDIO-00 floors

CDIO-06 §5 names each family's characteristic failure so nobody discovers it as a
BLOCK at the end. The same service, for postures:

- **`expressiveness: high`** collides with the accessibility floor first, and
  almost always through `reduced_motion`. High expression that has no reduced
  equivalent is not an expressive surface — it is a surface that stops working
  for a class of users. `equivalent` means the *information and the state
  transition still arrive*, by a non-motion channel; it does not mean the
  animation is merely shortened.
- **`success_posture: celebrate`** collides with the trust floor. A celebration
  asserts that something good happened. When the underlying operation is queued,
  optimistic, or reversible, the celebration is a claim the system cannot yet
  back — feedback that contradicts real state is a trust defect (CDIO-03 §4),
  not a delight.
- **`waiting: optimistic`** collides with the same floor from the other side. An
  optimistic update that is never reconciled leaves the user holding a false
  belief. Optimistic waiting requires a declared reconciliation path, or it is
  a fabricated state.
- **`character_policy: persistent_character`** collides with the Flow dimension
  (CDIO-00 §2.5). A figure that occupies attention during a serious or timed task
  competes with the task. Character belongs where attention is abundant, not
  where it is the scarce resource.
- **`motion_budget: medium` or `high`** collides with performance. Motion is paid
  for in main-thread time, battery, and low-end hardware. A perceived-premium
  gain bought with interaction latency is a net loss, and the trade is not
  arbitrable: perceived quality that makes the product slower has failed on the
  dimension it was purchased to improve.
- **`progress_language: numeric`** collides with honesty. A percentage that
  jumps, stalls at a round number, or is synthesised from nothing is worse than
  `indeterminate`. Declare numeric progress only where a real fraction exists.

Rule 5 of CDIO-06 §3 governs here unchanged and is restated because this axis is
where it will be tested most: **accessibility floors are not arbitrable.** No
posture, however deliberately chosen, buys a reduced-motion exemption, a
keyboard-operability exemption, or motion as the sole channel for essential
information.

## 6. Contract with the gate (what is actually machine-read)

This dataset is not advisory prose. Four of its structures are read by code, and
each is refusable:

- **The `experience:` block** in `DESIGN.md` front-matter is parsed by
  `tools/design_gate.py`. Absent → the surface is reported `unassessed`, never
  failed. Present and internally incoherent (§4) → refused at declaration time.
- **`reduced_motion`, `motion_budget`, `feedback_latency_ms`,
  `progress_threshold_ms`** are consumed as thresholds by the mechanical checks
  in `modules/cdio/scorer.py`. A floor breach is `critical` by CDIO-00 §4, in the
  same way a contrast failure is — not because this axis is important, but
  because an accessibility floor is a floor wherever it is measured.
- **The whole contract** feeds the compliance filter, which reports
  `resolved` / `unresolved` / `unassessed` and rides the hard-filter path in
  `review_gate`. It **never** contributes a score deduction. A criterion that
  silently re-scores surfaces reviewed last month is a regression wearing a
  gate's clothes, and the ≥80 threshold must mean the same thing after this
  dataset as before it.
- **`motion_budget` and the open usability findings** are emitted as the CDICF
  selector's project context, so a declared budget actually filters which
  components may be adopted rather than sitting in a document nobody reads.

A rule no gate can refuse is a preference. These four are refusable.

## 7. Common false positives (what CDIO-07 does NOT flag)

This axis is the most vulnerable in CDIO to over-flagging, because a reviewer can
always imagine a livelier interface. Guard against these:

- **Absence of animation is not a finding.** On a surface declaring `none` or
  `restrained`, a still interface is conformance. Never record "lacks
  micro-interactions" as a defect; there is no criterion it fails.
- **An instant operation needs no progress cue.** `progress_threshold_ms` is a
  threshold, not a mandate. An operation that completes below it correctly shows
  nothing, and a spinner that flashes for 80ms is itself a defect.
- **A terse error is not automatically a poor error.** Under `error_posture:
  terse` on an expert tool, a short precise message is the contract. The defect
  is a *raw code or a dead end* (CDIO-02 §3), which fails at every posture.
- **A quiet success is not a missing success.** `silent` is legitimate where the
  result is self-evident — the row appeared, the value changed. Confirmation of
  a visible outcome is redundancy, not reassurance.
- **A character is not amateurism.** CDIO-03 §9 already holds this line for
  visual style; it holds here for voice. A declared, coherent character is a
  choice. Inconsistency is the defect, not informality.
- **A reduced-motion fallback that differs is not a failure.** `equivalent`
  requires the same information and state change to arrive, not the same
  animation at lower amplitude. A cross-fade replacing a slide is conformance.
- **A missing contract is not a failing contract.** Report `unassessed`.
  An unmeasured property treated as a failure inerts the gate on day one; treated
  as a pass, it launders an unknown into a yes. It is neither.

Before recording a CDIO-07 finding, confirm the behaviour departs from what the
project **declared**, not from what the reviewer would have declared. If the only
support is "I would have made it livelier", it is not a finding — it is a request
to change the contract, and that request goes to the picker.

## 8. What this axis cannot see (honest limits)

Stated plainly, because a gate that oversells its coverage is a rubber stamp and
a rubber stamp is worse than no gate (CDIO-06 §7).

1. **The gate reads a declaration, never a render.** It knows what a project
   committed to and nothing about what shipped. Timing, motion, and perceived
   responsiveness are properties of a running surface; only the render-verified
   path (VQ-8, `DESIGN_GOVERNANCE.md` §7) can observe them. A conformant contract
   is a necessary condition, never a sufficient one.
2. **Conformance is not effect.** That a surface honoured its declared feedback
   ceiling says nothing about whether users completed more tasks. Effect requires
   outcome data this repository does not hold for consuming products. §9 defines
   the fields such a loop would attach to; the loop itself is not claimed.
3. **This axis does not measure taste and does not try.** Whether a character is
   charming, whether a transition is elegant — CDIO-00 §10 assigns those to the
   human authority, and this dataset leaves them there. What moved across the
   line is only what was always behaviour: thresholds, budgets, postures,
   policies. The unmeasurable half stayed exactly where it was.

## 9. Evidence fields (the schema, not the loop)

A behaviour declared for a reason should eventually be checkable against that
reason. The fields below exist so a future outcome loop has a schema to attach
to, and so that a hypothesis is recorded at the moment it is cheap to record —
at declaration — rather than reconstructed later from memory.

Each declared posture may optionally carry: the **user moment** it addresses, the
**current state** it assumes, the **intended state**, the **observable** that
would show it worked, and the **counter-observable** that would show it backfired.
The counter-observable is the field that matters most and the one most often
omitted: a hypothesis with no failure condition is a belief, and beliefs
accumulate rather than resolve.

No claim of causality is made or permitted from these fields alone. A posture
that correlates with an improved outcome is a candidate for wider use, never a
proven mechanism, and it becomes a baseline default only through the promotion
gate — never because it worked once on one product.

## 10. Worked examples (contract, observed, verdict, fix)

**Under-delivery.** A dashboard declares `feedback_latency_ms: 100`. Clicking
"Run report" produces no visible change until the response returns 1.8s later.
Observed: action with no acknowledgement inside 100ms; operation past the
progress threshold with no cue. Verdict: fail, critical (dead-feeling action, and
the double-submit risk CDIO-02 §3 names). Fix: disable-and-label the control on
click, show the declared `skeleton` past the threshold.

**Over-delivery.** A payments console declares `expressiveness: restrained`,
`celebration_policy: never`, `trust_posture: critical`. A refund completion
triggers a confetti burst. Observed: celebration on a surface whose policy
excludes it, on an irreversible financial action. Verdict: fail, major — and
critical if the refund is queued rather than settled, because the celebration
then asserts a state the system has not reached. Fix: replace with a confirmation
naming the amount, the recipient, and the reversal path.

**Incoherence, refused before build.** A contract declares `expressiveness: high`
with `reduced_motion: absent`. Observed: an expressive ceiling with no declared
equivalent for users who request reduced motion. Verdict: refused at declaration
— the contract cannot be conformed to without breaching an accessibility floor,
so no surface should be built against it. Fix: declare `equivalent` and state the
non-motion channel, or lower the ceiling.

**Correct abstention.** An internal batch-operations console declares
`expressiveness: none`, `success_posture: silent`, `waiting: spinner`. The
interface has no animation anywhere. Observed: full conformance. Verdict: pass,
zero findings. A reviewer proposing micro-interactions here has produced a
preference, and the review records none.

These are the CDIO-07 template: name the declared value, state the observed
behaviour, assign severity by the CDIO-05 §3 rules, and give the concrete fix. A
concern that cannot be stated as a departure from a declared value is an
impression, and CDIO does not record impressions — on this axis least of all,
because this is the axis where impressions are most persuasive.
