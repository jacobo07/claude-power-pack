---
id: UACF-01
name: Surface Architecture
type: dataset
domain: uacf
status: sealed
owner: modules/surface_architecture
date: 2026-09-21
---

# UACF-01 — Surface Architecture

> **Owns:** which entry-surface topology a product's measured constraints justify, and
> where its boundaries fall.
> **Does not own:** the ordering *principle* (CDIO-02), visual or interaction quality
> (CDIO-00..07), which component realises a semantic (CDICF), authentication mechanics.

This is **one part, not a family**. `T-D2A-ANTIINFLATION-VIOLATION-001`: a dataset where
a Part would suffice is a violation, and a new dataset must first beat four cheaper
alternatives. It did not, so it is a part.

## 1. What is borrowed, and from whom

The ordering principle is **not stated here**. CDIO-02 owns it, as a judgement rule:

- CDIO-02 §"Friction before value" — *"a mandatory signup, paywall, or long form that
  appears before the user has experienced any value is a finding; the well-formed
  pattern lets the user reach a first success, then asks."*
- CDIO-02 §"Steps to completion", §"Form field count".
- CDIO-02:237 — *"Asking for signup after the user has produced a first result is the
  correct pattern."*

Restating that here would create two places it can be written and one place it can
drift. UACF-01 cites it and confines its own claim to **where the boundary falls**.

The division is exact and worth keeping: **CDIO judges a surface that exists; UACF-01
decides the shape of one that does not.** CDIO-00:22-24 disclaims authoring outright —
*"a cross-cutting design-intelligence layer, not an author. It never originates a
product."* That sentence is why this part exists at all.

## 2. Archetypes

Eleven, and the ids are stable — `modules/surface_architecture/archetypes.py` holds the
executable registry and `V-SA-DATASET-DRIFT` asserts these two lists agree, so a
rename in one that is not made in the other fails a gate rather than rotting quietly.

| id | the topology |
|---|---|
| `IDENTITY_FIRST` | a known party is established before anything else happens |
| `INTENT_FIRST` | what the party wants is captured before anything is asked of them |
| `WORK_FIRST` | useful work begins before a durable owner exists |
| `VALUE_FIRST` | a result is demonstrated or delivered before anything is requested |
| `ARTIFACT_FIRST` | something the party already holds seeds the work and resolves facts |
| `INTEGRATION_FIRST` | an authorised external source resolves many facts at once |
| `INVITATION_FIRST` | entry is predicated on an invitation that already carries context |
| `NARRATIVE_BOOTSTRAP` | free description bootstraps the work; structure is derived |
| `STRUCTURED_CONFIGURATOR` | bounded choices assemble the work — **the residual** |
| `RETURNING_PARTY_RESOLUTION` | an already-known party is recognised, not re-enrolled |
| `EPHEMERAL_TO_DURABLE` | work begins without a durable owner and is later bound to one |

**They are not mutually exclusive, and there is no global ranking.** Both statements were
established by measurement, not preference. A first version picked one winner by a
scalar score and the contrasting-fixture set falsified it twice: counting exclusions let
a topology win by listing ways it could lose, and counting only requirements made six
tie. The premise was the defect. A document-heavy flow genuinely *is* artifact-first and
work-first at once.

`STRUCTURED_CONFIGURATOR` is the **residual**: zero requirements, so it is always
justified. That is what makes "no topology is selected" expressible — when only the
residual survives, the facts are complete and they select nothing.

## 3. Boundaries

Seven, each placed on a path of phases (`entry · intent · work · value · effect ·
commitment`) rather than at a step number: value, identity, persistence, assurance,
consent, commitment, activation.

Identity is computed twice, from different facts:

- **earliest justified** — the first phase at which a known party is required by a
  *need*. Not the first phase at which it is *possible*; that is always `entry`, and
  treating possibility as justification is how identity becomes the default first step.
- **latest safe** — the last phase after which postponing *loses* something.

**The valuable output is when they cross.** A product whose earliest justified position
falls after its latest safe one has no valid position, and saying so beats choosing one
of the two and hiding the tension. That is `CONFLICT`, and it escalates to a human.

**Persistence is not identity.** Where work can exist before a durable owner, durable
storage is required before that owner exists, and the two boundaries land at different
phases.

## 4. Four outcomes, and why three was wrong

`RECOMMEND` 0 · `ABSTAIN` 20 · `REQUIRE_APPROVAL` 21 reuse `modules/cdicf/selector.js`
so two gates stay comparable. `UNDETERMINED` 22 is added.

| | the facts | what to fix |
|---|---|---|
| `ABSTAIN` | complete; they select nothing | the product |
| `UNDETERMINED` | incomplete, or outside the vocabulary | the measurement |

Collapsing these is a failure this estate has paid for four times:
`done_gate/strength_ladder` (*"three outcomes, because two is the bug"*),
`cdio/scorer` (`score=None`, *"the absence of a judgment"*),
`capability_runtime/applicability` gate 1.5 (*"dormant, not blocked"*), and here.

**A `RECOMMEND` is evidence, not authority.** It carries no permission to build, and
nothing downstream may read it as approval.

## 5. Evidence: one clip, and what it does and does not support

Source: `coltonholland.ai_fc7fbac9….mp4`, 5.72 s, 720×1280, sampled at 9 points, plus
two 10 fps windows. Instrument named because the claim depends on it.

**OBSERVED.** A phone recording of a laptop showing a preview deployment (tab title
carries a hotfix hash — not a shipped surface). Composition: a device frame; the
headline *"The first fitness coach in your pocket"*; a gradient CTA **"Build my
plan →"**; the line *"Already have an account? Log in"*. Across every sample the
headline, CTA and login line hold text and position **while the device content
changes** — which rules out a page scroll, since a scroll would carry the headline with
it. At 4.6–4.7 s two product screens are visible overlapping in one frame: a
cross-dissolve, hence a programmatic animation rather than a navigation. Transitions
located at ≈1.15 s and ≈4.65 s.

**STRONG INFERENCE.** A pre-signup acquisition surface, not a signup sequence. An
autoplaying cross-dissolving proof carousel. *Persistent promise × dynamic proof* as a
composition.

**NOT PROVEN, and not rounded up.** Two transitions 3.5 s apart fit a ~1.17 s period and
equally fit 1.75 s or 3.5 s — **two points cannot establish a period**, and no third
measurement was taken because no decision depends on it. No input event was ever
observed. Nothing after the CTA is visible, so identity-boundary placement, work
preservation and activation are **not observed** and may not be cited from this clip.

**What survives as a pattern, and at what confidence.** Three extractions, each with
this single clip as its only source:

1. an invariant promise may coexist with varying evidence;
2. a primary action may be named for the party's **outcome** rather than the system's
   mechanic (*"Build my plan"*, not *"Sign up"*) — this one is **observed**, not inferred;
3. a returning-party path belongs at the value boundary, beside the primary action.

Under **LAW 10 — applicability before universalization**, one product's success does not
make a rule universal. None of these is promoted to a baseline obligation. They are
recorded with their source, their confidence, and the fact that a second independent
observation is what would move them.

## 6. Failure modes

Registered per archetype in `archetypes.py` as `failure_modes`, so they are data a gate
can read rather than prose a reader must remember. The recurring ones this part names:
premature account wall · surprise account wall · work loss at the identity boundary ·
invisible inference · wizard theater · schema-driven friction · duplicate questioning ·
one-happy-path completion.

These are **not** a new taxonomy. DS23 of the binding
`vault/audits/apir/NON_DUPLICATION_LEDGER.md` routes failure genomes to CEPS, CRAIF,
CLAE and `anti-antipatterns.md`; a second store would be the duplication that ledger
exists to prevent.

## 7. What this part does not make true

Registering a capability makes it **discoverable**, not **callable**.
`capability_runtime/applicability.compile_stack` returns capability ids and never
invokes a capability, so nothing dispatches `resolve()`. That dispatch is DS08, reserved
by the same binding ledger to `hooks/hook-dispatcher.js`. The kernel contract's
`non_scope` says so and the signup derivative inherits it verbatim.

No signup surface has been built from this. The decision engine has been exercised
against seven scenarios and zero products.
