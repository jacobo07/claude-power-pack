# Backlog — Absorb Synsation UX interaction patterns into Claude Power Pack Design

**Created:** 2026-10-13  
**Priority:** P0/P1 — high leverage for every interactive frontend  
**Source basis:** four owner-supplied Synsation videos inspected as frame sequences from the uploaded files in the 2026-10-13 session.  
**Goal:** turn the useful UX concepts into durable CPP design intelligence, tests, patterns and routing — without duplicating concepts already owned by CDIO.

## Evidence manifest

| Source | Duration | SHA-256 | Primary observed topic |
|---|---:|---|---|
| synsation__fe97b0a1cc1f4b859b3ac06376157663.mp4 | 73.375 s | 815e3b438be35b50c4ee7fdc879d96bcb803c725c3b7941085a32ac1cd26bbe2 | Disabled submit controls, form validation discoverability, accessibility/recovery |
| synsation__14a28c4cd47c4d8cbbe6aa4ae62039bd.mp4 | 71.843 s | 36872a211c656540f7e6c7115b28ae3f0b4ebf6f6aa870fbdcd6338ba3df72b5 | Target size, proximity, invisible hit-area expansion, accidental activation |
| synsation__7de80ae39f6a4eda91397eb7e4018b32.mp4 | 70.356 s | 89b62735fc4369a237f2275ee03b2a8ecbbb31034f75491129b0492e28339737 | Loading feedback: skeletons, inline spinners, optimistic UI, perceived latency |
| synsation__86392f83f44a414a8453078b02913111.mp4 | 91.997 s | 864dfef7f9ed50c0f4da5c5e667de2d756472093f1bfa2d065736fb266c6e2dc | Enterprise/compliance readiness UX: context-dependent frameworks, evidence status, continuous compliance |

**Evidence limitation:** these notes are grounded in visible frames and burned-in captions observed from the supplied videos. No full audio transcript was available. Claims that depend on wording not visible in the frames remain INFERRED until the source is transcribed or replayed with audio in the implementation session.

---

# Mission

Absorb every transferable UX principle demonstrated by these sources into Claude Power Pack Design so future agents do not need to rediscover them.

The outcome must not be a giant prose checklist. Useful material should become, where justified:

- CDIO criteria or conventions;
- DESIGN.md / experience-contract semantics;
- reusable interaction patterns;
- state-space scenarios;
- deterministic or browser-real tests;
- accessibility gates;
- negative examples / traps;
- routing logic;
- Knowledge Vault lessons;
- UKDL Hard Rules / Process Rules / Traps;
- baseline candidates only after evidence supports promotion.

Reuse existing ownership first.

---

# Reality Scan — known overlap before implementation

The current CPP already owns part of this territory:

- **CDIO-05 / CDIO-08** already enforce a 44×44 minimum tap target; CDIO-08 records 48dp as the Android platform target.
- **CDIO-02** already requires specific error recovery and says inline validation beats full-page rejection after submit.
- **CDIO-02** already requires visible action acknowledgement and progress for operations that exceed the response threshold.
- **CDIO-03** already treats loading/error/empty states as trust surfaces.
- **CDIO-07** already models waiting as skeleton, spinner, progress, optimistic or none; it has a progress threshold and explicitly requires reconciliation for optimistic updates.
- **CDIO-07** already warns that an 80ms spinner flash is itself a defect.
- **frontend lieutenant** already carries the 44×44 touch floor and disabled-while-async rule.

Therefore the correct work is mostly **EXTEND + CONNECT + TEST**, not a new parallel UX OS.

---

# UX-01 — Discoverable validation: do not hide why an action is unavailable

## Source observation

The first video repeatedly shows a long form, a disabled-looking Submit control, a missing required Work Address field, a red inline error state, keyboard/accessibility references, and later contrasts the pattern with shorter/simple controls.

## Transferable principle

A disabled action can prevent the user from discovering why they cannot proceed.

For forms, especially long or partially off-screen forms, pre-emptively disabling Submit can create a false dead end:

- the user cannot trigger validation;
- the missing requirement may be outside the viewport;
- the reason for disabled state may not be perceivable;
- keyboard/screen-reader users may receive weaker causal feedback;
- the UI communicates impossibility without recovery.

## Candidate rule

**Blocked-by-validation is not the same semantic state as unavailable.**

When the system can accept an activation attempt and use it to explain what must be fixed, prefer:

activate → validate → expose errors → move/announce focus to the first actionable error → preserve entered data.

A disabled control is appropriate when the action is genuinely unavailable and the reason/recovery is already obvious or explicitly exposed.

## Important distinctions to institutionalize

Do not collapse these states:

- unavailable because permission/capability does not exist;
- blocked because required data is incomplete;
- invalid after validation;
- pending because a request is in flight;
- rate-limited;
- temporarily unavailable;
- completed.

They have different UX, accessibility and system semantics.

## Form recovery contract candidate

For a failed submit:

- identify every invalid required field;
- show a specific inline error adjacent to the field;
- expose an error summary when the form is long or multiple errors exist;
- programmatically associate error text with the control;
- focus or scroll to the first actionable invalid field according to accessibility guidance;
- announce the failure where assistive technology requires it;
- never erase already valid input;
- keep the submit action discoverable unless disabling is semantically required.

## False-positive guard

Do not convert this into “disabled buttons are always bad.”

A short, fully visible interaction where the enabling requirement is obvious may legitimately disable an action. The defect is **hidden causality / no recovery**, not the CSS state itself.

## Existing owner hypothesis

Extend CDIO-02 error prevention/recovery + accessibility flow criteria. Add CDIO-07 state semantics only if needed. Do not create a new dataset solely for this rule.

---

# UX-02 — Actionability causality: every disabled state must answer “why?” and “how?”

Create a reusable disabled-state contract.

For every visible disabled interactive control, a reviewer/test should be able to determine:

1. Why is it disabled?
2. Can the user change that condition?
3. If yes, how do they discover the required action?
4. Is the reason perceivable without relying on color alone?
5. Is the state exposed correctly to assistive technology?
6. Does the control become enabled deterministically when the requirement is satisfied?
7. Can stale state leave it disabled after the requirement becomes valid?

Candidate defect classes:

- opaque-disabled-action
- disabled-with-hidden-prerequisite
- stale-disabled-state
- disabled-but-clickable
- enabled-but-inert
- validation-block-with-no-error-path

---

# UX-03 — Long-form validation must be spatially discoverable

A long form changes the correct recovery strategy.

Candidate convention/criterion:

- errors outside the viewport need a navigation/recovery mechanism;
- validation should not require the user to manually hunt through a long form;
- error summary → field link/focus can be useful when multiple failures exist;
- preserve scroll/focus semantics;
- sticky footer submit bars must not hide the field they scroll to;
- dynamically inserted errors must not cause destructive layout jumps.

Adversarial scenarios:

- first invalid field above viewport;
- first invalid field below viewport;
- multiple invalid fields;
- field inside collapsed/conditional section;
- field mounted after async data;
- validation after keyboard-only submit;
- screen reader announcement;
- mobile keyboard covering focused invalid field;
- error appears while sticky footer is present.

---

# UX-04 — Fitts-style target engineering: interaction geometry is larger than visual geometry

## Source observation

The second video contrasts small social-action icons, discusses larger targets and targets being easier/faster, shows a heart icon with a larger dotted hit region, a checkbox whose surrounding label/container becomes interactive, and a large event/card interaction where overly broad targeting may create another problem.

## Transferable principle

**Visible glyph size and interactive hit area are separate design variables.**

A control can remain visually restrained while its hit target expands through padding or a larger semantic container.

This should be explicitly understood by CPP rather than equating 44×44 with “draw a 44px icon.”

## Existing floor

Retain CDIO's 44×44 critical floor and Android's 48dp target convention.

## New candidate checks / patterns

- visual-size-vs-hit-area — a small icon may pass if its actual hit region clears the floor;
- label-expands-control — checkbox/radio labels and their intended row/container can expand the target when semantics remain clear;
- target-population-floor — automated tests inspect actual hitboxes, not icon dimensions;
- pointer-region-truth — the measured clickable region must match the region the design implies.

---

# UX-05 — Target proximity and accidental activation are a tradeoff

Larger/closer controls improve acquisition speed, but oversized or overlapping hit regions can create accidental activation.

The target system should consider:

- target size;
- distance to likely pointer/thumb origin;
- spacing between competing targets;
- overlap of invisible hit regions;
- scroll/drag gesture territory;
- destructive-vs-safe action cost;
- one-handed reach;
- edge proximity;
- density of adjacent controls.

Candidate defect classes:

- undersized-hit-target
- overlapping-hit-targets
- hit-area-steals-neighbour
- hit-area-intercepts-scroll
- accidental-destructive-hit
- surprising-semantic-hit-region

A larger invisible target is good only while its semantic boundary remains predictable.

---

# UX-06 — Make the semantic row clickable when the row is the action

For checkbox/radio/list-row patterns, if the visual language implies the entire row describes one control, the target can be the row/label rather than the tiny glyph alone.

Do not turn containers with nested independent controls into one giant click target.

Adversarial cases:

- checkbox + inline help link;
- row + overflow menu;
- card + secondary CTA;
- label containing hyperlink;
- nested button inside clickable card;
- touch scroll starting inside card.

The implementation must prevent parent activation when the user intended a nested action.

---

# UX-07 — Loading feedback must be selected by scope, latency and truth

## Source observation

The third video explicitly shows:

- skeleton screens;
- page/section structure represented during loading;
- inline spinners for small/local operations;
- a Submit control with local loading;
- optimistic UI;
- an Instagram-like “like photo” example;
- “it feels instant” messaging.

## Transferable principle

There is no single loading state.

The waiting pattern should be derived from:

- scope — whole page, section, component, control;
- expected latency;
- whether final geometry is known;
- operation certainty;
- reversibility;
- error cost;
- whether work has measurable progress;
- whether stale content can remain visible safely.

This should strengthen CDIO-07's existing waiting enum with an explicit decision procedure.

---

# UX-08 — Skeletons are structural promises

Use skeletons when enough of the final structure is known that preserving geometry helps the user understand what is coming.

A good skeleton should:

- approximate the final layout hierarchy;
- reserve final space and reduce CLS;
- avoid decorative shimmer that becomes the experience;
- not imply content/fields that may not exist;
- not run for operations too short to justify it;
- transition without a large geometry jump.

Candidate defects:

- skeleton-shape-mismatch
- skeleton-causes-layout-shift
- skeleton-for-unknown-structure
- skeleton-flash
- perpetual-skeleton
- skeleton-looks-like-disabled-real-content

---

# UX-09 — Inline spinners belong to local work

A local action should not unnecessarily block or visually reset the whole page.

Use inline/local progress for operations such as a single control or bounded region when the rest of the page remains valid.

Candidate invariants:

- spinner/progress location identifies what is waiting;
- pending state prevents duplicate activation where duplication is unsafe;
- control width remains stable while label/spinner changes;
- pending does not erase the action label if the user then cannot remember what is happening;
- completion/error reconciles to a real system result;
- local pending work does not freeze unrelated controls without reason.

---

# UX-10 — Avoid loading feedback that flashes

CDIO-07 already owns this principle. Strengthen it with executable coverage.

Very fast operations should not produce a spinner flash that increases perceived instability.

The system should support a show-delay + minimum-visible-duration policy where appropriate:

- delay the indicator until latency crosses a threshold;
- once shown, keep it long enough to be perceptible without faking progress;
- never delay completion just to perform decorative animation on critical flows.

Exact thresholds remain product/context dependent unless independently evidenced.

---

# UX-11 — Optimistic UI is a truth contract, not merely a speed trick

Optimistic updates can make an interaction feel instant when success probability is high and the action is safely reversible.

Required semantics:

- immediate local feedback;
- server reconciliation;
- rollback or explicit correction on failure;
- duplicate-event prevention;
- conflict handling;
- stale-response protection;
- eventual consistency state when the server result is delayed;
- no optimistic claim for irreversible/high-risk actions without evidence that this is safe.

CDIO-07 already states that optimistic waiting without reconciliation is a trust defect. Extend this into reusable browser-real scenarios.

Candidate defect classes:

- optimistic-without-rollback
- optimistic-duplicate
- optimistic-stale-overwrite
- optimistic-success-on-failed-server
- optimistic-order-conflict
- optimistic-high-risk-claim

---

# UX-12 — Perceived performance must remain subordinate to state truth

The video demonstrates the psychological value of feeling instant. CPP should preserve the principle but not let perceived performance become fake performance.

Hard boundary:

- never invent numeric progress;
- never claim completion before the system reaches a truthful state;
- never hide a meaningful server failure behind an optimistic animation;
- never use animation to disguise indefinite work.

The best perceived-performance pattern reduces uncertainty without changing the truth.

---

# UX-13 — Waiting-pattern decision matrix

Build or document one canonical decision procedure, without duplicating CDIO-07.

Candidate dimensions:

| Situation | Likely pattern |
|---|---|
| instant / below threshold | none |
| local bounded action | inline spinner/progress or pending control |
| page/section with known geometry | skeleton |
| measurable long operation | real progress |
| small reversible high-success action | optimistic + reconciliation |
| unknown-duration task | indeterminate/staged status |
| stale data remains trustworthy | keep content + subtle refresh state |
| critical irreversible action | explicit pending/settlement state, not optimistic completion |

This matrix is a hypothesis to refine against CPP doctrine and external accessibility/performance evidence before becoming canonical.

---

# UX-14 — Enterprise compliance UX is contextual, not a static badge

## Source observation

The fourth video is partly promotional/product-oriented rather than a pure UX lesson. It visibly connects compliance needs to **Product / Customers / Data / Location**, shows HIPAA, SOC 2 / ISO 27001, GDPR, an enterprise customer asking for a SOC 2 report, then demonstrates a workflow that connects systems, chooses a framework, shows what is on track / needs attention, and supports staying compliant as the company evolves.

Treat this as an **adjacent enterprise-product UX pattern**, not universal law.

## Transferable candidate

For products where compliance is a user task, do not reduce compliance UX to a decorative trust badge.

Model it as an operational workflow:

context → applicable requirements → evidence sources → current readiness → gaps → remediation → report/export → continuous monitoring.

---

# UX-15 — Contextual requirements compiler for compliance/trust onboarding

The visible Product / Customers / Data / Location model suggests a reusable onboarding pattern:

ask only the context necessary to determine which obligations are applicable.

Potential context dimensions:

- product/domain;
- customer type / enterprise requirements;
- data classes handled;
- user/customer location and jurisdictions;
- deployment environment;
- requested assurance framework;
- existing certifications/evidence.

Do not present every possible framework as one giant checklist when applicability can be derived.

Candidate general principle:

**requirements should be generated from context, not exposed as undifferentiated bureaucracy.**

This may generalize beyond compliance to setup/configuration products, but promotion requires transfer evidence.

---

# UX-16 — Readiness should expose “on track” versus “needs attention”

Operational trust UX should make current posture legible.

A user should be able to distinguish:

- satisfied;
- in progress;
- missing;
- stale;
- failing;
- awaiting external evidence;
- awaiting human review;
- not applicable;
- unknown.

Do not collapse compliance to a binary green/red status where provenance or freshness matters.

This aligns with CPP's broader epistemic doctrine and should reuse existing status vocabularies where possible.

---

# UX-17 — Evidence acquisition should reduce user toil

Where a trust/compliance workflow can connect to systems and derive evidence, the UX should prefer:

connect source → observe evidence → show provenance/freshness → request only what cannot be obtained.

Do not make users manually re-enter facts already available from authoritative connected systems.

This is a candidate Process Rule, not yet a universal Hard Rule.

---

# UX-18 — Compliance is continuous state, not one-time onboarding completion

The “stay compliant as you evolve” framing suggests that user experience must model drift.

Candidate state machine:

ready → changed dependency/configuration → evidence stale → attention required → remediated → ready.

If adopted, testing should include:

- evidence expiring;
- integration disconnecting;
- framework requirement changing;
- new location/jurisdiction;
- new data class;
- new customer requirement;
- auditor request arriving after earlier completion.

A one-time green onboarding screen must not create a permanently false sense of readiness.

---

# UX-19 — Trust claims must distinguish readiness, evidence, review and certification

Never use one generic “compliant” badge for semantically different states.

Potential distinctions:

- evidence collected;
- control passing;
- framework readiness;
- audit in progress;
- independently audited;
- certified/attested where that term legally applies;
- report available;
- stale evidence;
- exception accepted.

The exact taxonomy must come from the product/domain; CPP should enforce semantic honesty, not invent legal status.

---

# UX-20 — Enterprise trust UX removes blockers; it does not promise demand

The source visibly states that compliance will not automatically win the customer, while preparedness can prevent it from becoming the reason a deal fails.

Useful conversion/trust distinction:

- a compliance asset can be a permission-to-progress / friction-removal mechanism;
- it must not be marketed as proof of product value or guaranteed sales.

Potential owner: CDIO-03 trust + CDIO-04 conversion honesty.

---

# Cross-cutting state-space to add to the Universal UI Defect Ontology

The four sources together point to a useful testing product:

**Control/Flow × State × Input mode × Viewport × Latency × Validity × Risk × Evidence freshness**

Representative scenarios:

### Forms
- enabled/disabled/pending/invalid;
- mouse/keyboard/screen reader/touch;
- first error visible/offscreen/collapsed;
- short/long form;
- async validation;
- stale validity.

### Targets
- 44px floor;
- visual glyph smaller than target;
- adjacent target collision;
- nested interactive elements;
- touch scroll;
- destructive nearby action.

### Waiting
- instant;
- medium delay;
- long delay;
- success/failure;
- optimistic rollback;
- navigation/unmount during wait;
- duplicate click;
- stale response.

### Compliance/trust
- evidence fresh/stale/missing;
- applicable/not-applicable/unknown;
- integration connected/disconnected;
- framework selected/changed;
- report requested before readiness;
- human review pending.

The compiler should select relevant combinations rather than run the full Cartesian product.

---

# Negative corpus candidates

Register these as candidate reusable traps if the implementation audit confirms they are not already owned:

1. Disabled Submit with no visible causal explanation.
2. Long form where the user must hunt for the missing required field.
3. Tiny icon measured instead of the actual hit region.
4. Invisible hitbox expanded until it overlaps another action.
5. Clickable-card parent stealing nested-control taps.
6. Full-page spinner for one local action.
7. Skeleton unrelated to final geometry.
8. Spinner flash for an instant operation.
9. Optimistic success with no reconciliation/rollback.
10. Fake numeric progress.
11. Compliance reduced to one green badge with no provenance/freshness.
12. Static compliance checklist ignoring product/customer/data/location applicability.
13. One-time compliance completion that never models drift.
14. Trust badge implying certification/review the system cannot prove.

---

# Proposed ownership map

Reality Scan decides final placement.

| Concept | Likely owner |
|---|---|
| disabled-validation causality | CDIO-02 |
| long-form recovery | CDIO-02 + accessibility |
| target size | CDIO-05 / CDIO-08 existing owner |
| hitbox geometry / overlap | CDIO-08 or universal interaction criterion |
| loading-pattern routing | CDIO-07 |
| skeleton / inline spinner / optimistic patterns | visual-patterns + CDIO-07 |
| perceived-performance truth | CDIO-07 + CDIO-03 |
| compliance trust semantics | CDIO-03 |
| compliance conversion honesty | CDIO-04 |
| contextual requirements onboarding | CDIO-02 / product-surface doctrine |
| continuous readiness / evidence freshness | interaction/state doctrine + relevant domain owner |
| browser-real state testing | Universal UI Defect Ontology / testing infrastructure |

Do not create a new CDIO dataset unless extension cannot preserve one canonical owner.

---

# Required implementation campaign when activated

## Phase 0 — Reality Scan

Audit the current CPP HEAD, including:

- CDIO-00..09;
- DESIGN.md schema;
- visual-patterns;
- frontend lieutenant;
- accessibility/test infrastructure;
- Universal UI Defect Ontology if it exists by then;
- any new design/template/asset systems created after this backlog entry.

For every concept above, classify:

- ALREADY OWNED;
- EXTEND OWNER;
- NEW PATTERN;
- CONVENTION;
- FIRST-PRINCIPLE CRITERION;
- DOMAIN-SPECIFIC;
- UNVERIFIED;
- REJECTED.

## Phase 1 — Distill semantics

Convert only genuinely missing concepts into the narrowest durable representation.

## Phase 2 — Make applicable concepts executable

Prefer tests/gates where behavior is mechanically observable.

Examples:

- actual browser bounding boxes for target size and overlap;
- keyboard activation;
- validation focus;
- live-region/error association;
- loading-delay behavior;
- duplicate-submit prevention;
- optimistic rollback;
- stale-response race;
- zero-population red controls.

## Phase 3 — Visual/browser reality

Screenshots alone are insufficient for:

- clickable hit regions;
- focus transfer;
- disabled semantics;
- scroll interception;
- live-region announcements;
- pending state;
- optimistic reconciliation.

Use real browser interaction.

## Phase 4 — Learning

Capture:

- failures in Knowledge Vault;
- transferable Hard Rules / Process Rules / Traps in UKDL;
- baseline candidates only after scope-appropriate transfer evidence.

---

# Done-gate

This backlog item is complete only when:

1. all four supplied videos have an evidence record and every transferable concept has a disposition;
2. existing CDIO ownership is reused rather than duplicated;
3. disabled-vs-validation semantics are explicitly modeled;
4. long-form error recovery is testable;
5. target-size testing measures the real hitbox rather than visible icon dimensions;
6. hitbox overlap / nested interaction / scroll interception are covered;
7. CDIO-07 has a falsifiable loading-pattern decision procedure or equivalent owner;
8. skeleton, inline-spinner and optimistic patterns have applicability and “when NOT to use” contracts;
9. optimistic UI has reconciliation/rollback/race coverage;
10. false progress and spinner-flash failure modes are covered;
11. the compliance/trust video's useful product patterns are either absorbed at the narrowest justified scope or explicitly rejected as domain-specific/promotional;
12. trust/compliance states distinguish evidence, freshness and review semantics where applicable;
13. browser-real tests demonstrate red capability through adversarial or mutation drills;
14. negative-corpus traps are discoverable automatically during relevant frontend work;
15. a fresh agent can apply these lessons without seeing the source videos;
16. UKDL / Knowledge Vault / Constitutive Baseline Ratchet are updated at the correct evidence scope;
17. no source-specific implementation accident is universalized merely because it appeared in one video.

## First action when activated

Reinspect the original source videos if still available, obtain/transcribe audio if possible, and verify the frame-derived inferences above before promoting any wording-dependent claim. Then produce a reuse/extend/build decision ledger before mutation.
