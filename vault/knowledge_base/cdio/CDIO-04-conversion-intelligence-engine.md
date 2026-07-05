---
id: CDIO-04
name: Conversion Intelligence Engine
type: dataset
domain: cdio
status: sealed
parent: CDIO-00
---

# CDIO-04 — Conversion Intelligence Engine

Owns the measurable evaluation of whether a surface moves a user toward its goal:
call-to-action strength, page structure, pricing presentation, and the
value-before-friction sequence. It inherits CDIO-00's "conversion over
creativity" ordering — but never at the cost of the trust floor (CDIO-03) or the
accessibility floor. A surface that converts by manipulation is a defect, not a
success. CDIO-04 evaluates conversion by structure and evidence, not by
guaranteeing a number no static review can promise.

## 1. The call to action (CTA)

The CTA is the hinge of conversion. CDIO-04 evaluates it on presence, clarity,
prominence, and singularity.

**One primary action.** Each screen should have exactly one primary action — the
thing the surface most wants the user to do. Measurement: count the primary
(high-emphasis) CTAs in a viewport; more than one primary action per region
splits intent and is a finding. Secondary actions are allowed but must be
visually subordinate (outline vs. filled, lower contrast).

**Above-the-fold presence.** The primary CTA should be reachable without
scrolling on the entry viewport. Measurement: a landing page whose only CTA is
below the fold is a finding; the undecided user should never have to hunt for
the next step.

**Action-and-object label.** The CTA text should name the action and, ideally,
the value. Measurement: "Submit," "Click here," or "Continue" with no object is
weak; "Start free trial," "Get my report," "Create account" is strong. A label
that restates the value at the moment of commitment lifts intent. Vague labels
are a finding shared with CDIO-02.

**Visual prominence.** The primary CTA must be the (or a) visually dominant
interactive element — sufficient size, the accent color, adequate contrast (≥
4.5:1 for its text; ≥ 3:1 for its boundary), and enough surrounding whitespace to
stand out. Measurement: a primary CTA styled the same as body links, or one with
failing contrast, is a finding that is simultaneously a CDIO-01 accessibility
issue.

## 2. Landing page structure

A landing page has a well-understood measurable skeleton. CDIO-04 checks that the
skeleton is present and ordered.

**The canonical sequence.** A strong landing page generally moves: (1) hero with
value proposition + primary CTA; (2) social proof / trust signals; (3) the
problem and the outcome; (4) how it works / key capabilities framed as benefits;
(5) more proof (testimonials, results); (6) objection handling / FAQ; (7) a final
CTA. Measurement: a page that jumps into feature lists before establishing value,
that carries no proof section, or that ends without a closing CTA has structural
findings. The order is not rigid, but value-before-features and proof-present are.

**Benefit framing over feature listing.** Capabilities should be framed as user
outcomes. Measurement: a section that lists features ("OAuth2, webhooks, RBAC")
with no statement of what they do for the user is a framing finding; each feature
should carry its benefit ("Sign in with the accounts your team already uses").

**One page, one goal.** A landing page should pursue a single conversion goal.
Measurement: a page asking the user to simultaneously sign up, book a demo,
read the blog, and follow social channels with equal emphasis dilutes the goal;
the primary goal should dominate and the rest recede.

## 3. Page-type criteria

Conversion criteria differ by surface type; CDIO-04 applies the right rubric.

**SaaS / product landing.** Value proposition above the fold; free-trial or
demo CTA with minimal friction; social proof; a benefits-framed capability
section; pricing reachable in one click; a closing CTA. Measurement: missing
any of value-clarity, proof, or a low-friction primary CTA is a finding.

**E-commerce (product page).** Clear product imagery (multiple angles); price
and availability visible without scrolling; a prominent add-to-cart; concise
benefit-led description; reviews/ratings; shipping and return clarity;
trust/security cues at checkout. Measurement: price below the fold, no reviews,
or a weak add-to-cart is a finding. Hidden costs revealed late is a dark-pattern
finding (CDIO-02).

**Portfolio.** The strongest work first; each piece with context (role, outcome);
a clear contact path; fast load. Measurement: burying the best work, cases with
no outcome, or no obvious contact route are findings.

**Dashboard / app.** The most important metric or action first; a clear default
state and a designed empty state; drill-down without losing context; the primary
action reachable from the main view. Measurement: an undifferentiated wall of
equal-weight widgets, or an empty state with no guidance, is a finding. (Dashboard
legibility and density are shared with CDIO-01/02.)

## 4. Pricing presentation

Pricing is where conversion and trust meet, and it is highly measurable.

**Transparency.** The full price and what it includes must be clear before the
commitment step. Measurement: fees or required add-ons revealed only at checkout
is a hidden-cost finding (dark pattern). The user should be able to compute their
real cost from the pricing surface.

**Bounded, comparable tiers.** Pricing tiers should be a small, comparable set
(commonly two to four) with a recommended option indicated. Measurement: too many
flat tiers (CDIO-02 choice overload), or tiers whose differences are not
scannable in a comparison, are findings. A highlighted "most popular" tier is an
anchor that aids decision, not a dark pattern, as long as it is honest.

**Value framing.** Price should sit next to value, not alone. Measurement: a
price with no statement of what it delivers, or annual/monthly toggles that
obscure the real cost, are findings.

## 5. Value before friction

The sequence of value and friction is the highest-leverage conversion lever and
restates CDIO-00's friction-before-value anti-pattern from the conversion side.

**Deliver, then ask.** The surface should let the user perceive or experience
value before it demands commitment. Measurement: a mandatory account, card, or
long form before any value is shown is a finding; the strong pattern shows the
value (a live demo, a first result, a clear preview) and then asks. Every field
and every step before the first taste of value is measured drop-off risk.

## 6. The CDIO-04 anti-pattern catalog (with detection rules)

- **CTA weakness** — vague label, failing contrast, or no visual prominence.
- **Multiple primaries** — more than one high-emphasis CTA competing per region.
- **CTA below fold** — no primary action reachable in the entry viewport.
- **Value burial** — features before value; value not stated above the fold.
- **No proof** — landing page with no trust/proof section (links to CDIO-03).
- **Feature-listing** — capabilities with no benefit framing.
- **Hidden cost** — fees or add-ons revealed only at the final step. Dark pattern.
- **Tier overload** — too many flat, non-comparable pricing options.
- **Friction-before-value** — commitment demanded before value delivered.

## 7. How CDIO-04 feeds the score, and its honesty boundary

Structural and countable checks — CTA count and placement, presence of proof and
closing CTA, tier count, field count before value — are computed from the
described surface and are not opinion. Label and framing checks are supplied by
the reviewer citing the specific text. CDIO-04 states its own limit honestly: a
static review measures the *structure* known to drive conversion; it does not
promise a conversion rate, which only live testing establishes. A finding is
"this structure diverges from the conversion-supporting pattern at these points,"
never "this will convert at X%." As with every CDIO dataset, the output is a
criterion plus an observed value, never an unfalsifiable prediction.

## 8. Microcopy at the point of commitment

The words at the exact moment of commitment carry disproportionate conversion
weight and are fully reviewable.

**Button microcopy.** The CTA label should reduce perceived cost and restate
value. Measurement: a label that emphasizes the user's effort ("Sign up," "Fill
out form") is weaker than one that emphasizes their gain ("Get my free report").
First-person framing ("Start my trial") often outperforms second-person, and is
worth flagging as a convention-level improvement, not a hard rule (CDIO-00 §5).

**Risk-reducers next to the CTA.** A small reassurance beside the button lowers
hesitation. Measurement: a trial CTA with no adjacent risk-reducer ("No credit
card required," "Cancel anytime," "30-day guarantee") is a missed-reassurance
finding where the commitment is non-trivial. The reassurance must be true — a
false one is a trust defect (CDIO-03).

**Form microcopy.** Fields should explain themselves where needed and never
punish the user for a format the system could accept. Measurement: a field that
rejects a phone number for containing spaces, rather than normalizing it, is a
friction finding; a required field with no indication of why it is needed is a
trust-and-friction finding.

## 9. Worked examples (criterion, observed value, verdict, fix)

**CTA weakness.** A hero's primary action is a text link "Continue" in the body
color at 3.0:1 contrast. Observed: vague label, no visual prominence, contrast
below 4.5:1. Verdict: fail — the contrast alone is critical (accessibility
floor), the weakness is major. Fix: make it a filled accent button labeled "Start
free trial" at ≥4.5:1.

**Multiple primaries.** A pricing hero shows "Buy now," "Book a demo," and "Chat
with sales" all as filled buttons of equal weight. Observed: 3 competing primary
CTAs in one region. Verdict: fail, major. Fix: pick one primary ("Start free
trial"), demote the others to outline/secondary.

**Value burial.** A product page opens with a feature grid ("SSO, webhooks, audit
logs") before stating what the product is for. Observed: features precede value;
value not above the fold. Verdict: fail, major. Fix: lead with the outcome, then
frame each feature as a benefit.

**Hidden cost.** A checkout shows a $29 price throughout, then adds a $9
"processing fee" only on the final confirmation. Observed: fee revealed at the
last step. Verdict: fail, critical (dark pattern, CDIO-02 §4). Fix: show the
all-in price from the first pricing surface.

**Tier overload.** A pricing page lists nine flat plans with no recommended
option and overlapping feature sets. Observed: 9 non-comparable tiers, no anchor.
Verdict: fail, major. Fix: reduce to three or four clearly differentiated tiers
with one marked "most popular."

These examples are the CDIO-04 template: name the conversion criterion, observe
the structural value, assign severity by rule (hidden cost and floor-failing CTAs
are critical), and give the concrete fix. CDIO-04 measures the structure that
supports conversion; it never predicts the number, which only a live test can
establish.

## 10. Common false positives (what CDIO-04 does NOT flag)

Conversion is where a review most tempts a reviewer into cargo-cult pattern
matching — flagging anything that differs from a generic template. Guard against
these false positives:

- **A second CTA is not "multiple primaries."** A hero can hold one primary
  (filled) and one secondary (outline or text) action without violating the
  single-primary rule. The defect is *competing equals*, not the existence of a
  secondary path.
- **A long page is not value burial.** A thorough landing page with many sections
  is fine as long as the value is stated above the fold. Length is not the defect;
  *value below the fold* is. Do not flag a long page that leads with its value.
- **A demo-request CTA is not weak just because it is not "Buy now."** For a
  high-consideration B2B product, "Book a demo" is the correct primary action.
  Judge the CTA against the product's real conversion goal, not against a
  transactional default.
- **Requiring an account for an inherently account-based product is not
  friction-before-value.** A banking app cannot show a live account before login;
  the value *is* the authenticated experience. The rule targets gates before value
  that could have been deferred, not gates the product fundamentally requires.
- **A premium price is not a conversion defect.** High price with clear value
  framing is a positioning choice, not a finding. CDIO flags *hidden* or
  *unframed* cost, never the magnitude of an honest, well-presented price.
- **A single, honest anchor tier is not manipulation.** Highlighting a recommended
  plan aids the decision. Only a false anchor or a preselected hidden upsell is a
  dark pattern.

Before recording a CDIO-04 finding, confirm it diverges from the
conversion-supporting structure in a way that costs the user or hides the truth —
not merely from a generic template. A structure that fits the product's real goal
is not a defect because it differs from a SaaS-landing cliché.
