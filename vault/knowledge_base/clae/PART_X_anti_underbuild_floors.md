---
title: "CLAE Part X — Anti-Underbuild Floors"
family: clae
part: X
depends_on: [IX]
feeds: [XI, XVIII, XIX, XX, XXV]
status: SEALED
date: 2026-07-26
---

# Part X — Anti-Underbuild Floors

## 1. Purpose

Parts II through IX built the measuring half of this family. Part II §9 was explicit that the
measuring half does not enforce: distance informs, floors enforce, and conflating them destroys
both. This Part is the enforcing half.

It addresses a failure distance discipline cannot reach. An artifact can be measured honestly,
carry a large and correctly-recorded residual, and still ship — because shipping is an
admissibility decision, and a large residual is not an inadmissibility. That is correct behaviour.
It also means that if nothing else intervenes, **a system can ship a real-looking implementation of
something it did not actually build**, with a perfectly honest ledger recording how far short it
fell.

A floor is what intervenes. It is a domain-derived minimum below which the work is not admissible
at all, and it exists to catch the specific case that every other mechanism in this stack misses:
work that is genuinely real and genuinely shallow.

## 2. The underbuild problem

This stack already forbids incompleteness through the Reality Contract, enforced by a detector that
matches an incomplete-work lexicon — the marker tokens by which unfinished code announces itself.
That mechanism works and this Part does not disturb it.

Its coverage has a precise boundary:

> **Incompleteness that announces itself is detectable by a matcher. Incompleteness that does not
> announce itself is not.**

Underbuilt work does not announce itself. It compiles. It runs. It contains no marker tokens
because nothing was deferred in a way anyone wrote down. It passes its tests, because the tests
were written alongside it by the same author with the same conception of what the feature is. It
handles the case that was demonstrated. It is, by every mechanical check available, complete.

Detecting it requires knowing what *should* have been there — which sounds like a reference
question and would make it as expensive as Part IV. It is not, and the difference is the whole
economy of this Part. The question is not *how does this compare to the best instance*, which
requires a reference. It is *does this clear the minimum this kind of thing requires to be real*,
which requires only the domain. Minima are far cheaper to establish than bars, and they are
checkable without any external object at all.

## 3. A floor is not a low bar

Part III §6 fixed the vocabulary. Operationally the distinction is sharper than the definitions
suggest, and collapsing it is the most common error in this Part.

| | Floor | Bar |
|---|---|---|
| Question answered | Is this a real implementation of this thing? | How good is it? |
| Derived from | The domain and the consequence class | An external reference |
| Output | Admissible or not | A graded residual |
| Effect of crossing | Changes what may ship | Changes a recorded number |
| Movement | Rises only on evidence of a new failure class | Moves whenever the reference moves |

**A floor is not a bar set low.** They are different kinds of object answering different questions,
and a system that treats its floor as a weak bar will drift the floor upward whenever the reference
moves — at which point nothing ships and the floors get bypassed wholesale, per §6. A system that
treats its bar as a high floor blocks all work that is not at the frontier, which is the mirror
failure Part III §6 named.

## 4. The six shapes of underbuild

The practical core of this Part. Each shape passes compilation, execution, the marker-token
detector, and its own tests. Each is a distinct floor family.

**Happy-path-only.** The demonstrated case works; error paths are absent rather than deferred. No
marker token appears because nothing was marked — the branches simply were not written. Floor: every
declared failure mode of the artifact has an observable handling path.

**Single-instance.** Works for one input, one configuration, one consumer. Generalization was never
attempted, so nothing records that it is untested. Floor: the artifact is exercised across the
declared range of its inputs, not one member of it.

**Unobservable.** Works, and emits nothing. When it fails in production the failure is silent, and
the first signal is a downstream symptom with no connection to its cause. Floor: every failure path
emits a signal that identifies itself. This shape is the most consequential, because it is what
converts every *other* shape from a detectable problem into an undiagnosable one.

**Unrecoverable.** Works, but a partial failure leaves state requiring manual repair. The success
path was designed; the interrupted path was not. Floor: an interrupted operation leaves state a
subsequent run can proceed from.

**Unbounded.** Works, with no limit on time, memory, retries, recursion or iteration. Correct on
every input tried, and one unusual input consumes the host. Floor: every loop, retry and recursion
carries a declared bound and a defined behaviour at that bound.

**Undeclared-dependency.** Works because of an environmental accident — a tool on the path, a file
that happens to exist, an ordering that happens to hold. Nothing records the dependency because
nobody knew it was one. Floor: the artifact's environmental requirements are declared and checked,
and it fails legibly when they are absent rather than behaving unpredictably.

The shapes are not independent. Unobservable underbuild hides the other five; unbounded and
unrecoverable frequently co-occur, since the same missing consideration produces both. Where one is
found, the others are worth checking directly rather than waiting for them to surface.

## 5. What makes a floor legitimate

Five properties. A minimum failing any of them is a preference, and preferences enforced as floors
are how enforcement loses its authority.

1. **Derived, not imported.** The minimum comes from this domain and this consequence class, not
   from a figure borrowed from elsewhere. Part XI is devoted to why imported floors fail.
2. **Checkable.** Someone or something can evaluate it, repeatably, at a cost the process bears. A
   floor nobody can evaluate is an aspiration that will be assumed satisfied.
3. **Binary at the boundary.** Even where the underlying quantity is continuous, the floor's verdict
   is admissible or not. A floor reported as a score has become a bar and stops enforcing.
4. **Justified by a named consequence.** Every floor states the failure it prevents. A floor with no
   named failure cannot be argued with, cannot be retired, and cannot be traded off — which makes it
   permanent by construction rather than by merit.
5. **Escapable by a declared route.** There must be a recorded way to ship below it: a deviation
   with a proven constraint, preserved intent and measured loss, per Part XVIII.

Property five is counterintuitive and it is the one that determines whether a floor set survives.

> **A floor with no escape route will be defeated, not obeyed.**

Real work encounters legitimate exceptions. If the only options are satisfy the floor or violate it
silently, the exceptions become silent violations, and once silent violation is normal the floor no
longer constrains anything — it only adds ceremony to the cases that were going to comply anyway. A
declared escape converts what would have been an invisible breach into a recorded deviation with an
owner and a measured loss, which is strictly more information than a floor that is merely bypassed.

## 6. The floor accumulation problem

Floors accrue. Each incident produces one, each is justified, and none is ever removed. After enough
incidents the floor set is large, mostly untriggered, expensive to satisfy, and satisfied
ritualistically.

At that point the floor set has become **a self-authored criterion set that reports compliance and
discards magnitude** — which is precisely Part I's trap, reconstructed by this family's own
enforcement mechanism. The recursion is not hypothetical; it is the ordinary end state of quality
checklists, and this family's own §5 machinery is what produces it if left unbounded.

Two controls.

**Every floor carries a retirement condition at creation.** The condition states what would have to
become true for this floor to be unnecessary — usually that the failure class it prevents has been
structurally eliminated, so that violating the floor is no longer possible rather than merely
forbidden. A floor whose retirement condition cannot be stated at creation is a signal that the
consequence was never clearly identified, per property four.

**Floors are reviewed against their trigger history.** A floor never violated across a large number
of artifacts is in one of two states, and they require opposite responses: the failure class is
structurally impossible now, in which case retire it; or the check is not actually running, in which
case the floor has been decorative for however long that has been true. Distinguishing them requires
looking at the check, not the record — a floor with zero violations and no evidence its check
executed is the unfalsifiable zero of Part II §P8, arriving in the enforcement layer.

## 7. Floors and distance are bidirectional

The two halves of this family inform each other, and the traffic runs both ways.

**Distance discovers floors — the promotion rule.** When a residual recurs on the same dimension
across many artifacts, it is no longer an artifact-specific gap; it is a systematic shortfall in
what the domain's work routinely omits. That is a floor candidate. Promotion converts a
per-artifact measurement into a per-domain minimum, which is far cheaper to enforce than measuring
each artifact against a reference forever.

**Floors bound measurement cost — the demotion rule.** A dimension held above a floor no longer
needs the same measurement intensity, because the failure it guarded against cannot occur. Floors
retire measurement, which is how this family avoids the fate of measuring everything forever.

The relationship is why floors are not a lesser mechanism than distance. Distance is how you find
out what the minima should be; floors are how you stop paying to rediscover it.

## 8. Boundary

Floors are wrong in four situations.

**Exploratory work**, where the artifact is explicitly a probe of feasibility. Applying production
floors to exploration makes exploration unaffordable and drives it out of view, which is worse than
unfloored exploration. The requirement is that exploratory status is *declared* and that the
artifact cannot silently graduate into production while retaining the exemption.

**Where the floor would be imported.** A borrowed minimum with no local derivation is a preference
with a citation. Part XI treats this in full.

**Where the floor duplicates a prohibition.** Prohibitions are absolute and already enforced.
Restating one as a floor adds a second, weaker enforcement path with an escape route the prohibition
correctly lacks.

**Where the floor costs more than the consequence it prevents.** A floor is an economic object. One
whose satisfaction cost exceeds the expected cost of the failure it prevents is a net loss, however
sound its reasoning. Recording that judgment is what keeps the floor set from growing purely by the
accumulation of individually-reasonable additions.

## 9. Evidence — this stack's existing floors

| Floor | What it enforces | Shape coverage |
|---|---|---|
| Reality Contract, marker-token detector | No declared incompleteness in shipped code | None of the six — it catches announced incompleteness only |
| Output quality threshold | A composite score must clear a fixed value | Partial; a criterion-score floor, and a shallow artifact can score above it |
| Done means observed evidence, not exit code | A verdict must be backed by an observation | Indirectly aids unobservable, if the observation reaches the failure paths |
| Completion gates | Compile, lint, build, test, schema, audit, evidence | Happy-path-only partially, if tests exercise error paths — usually they do not |
| Secret firewall | A prohibition, correctly absolute | Not a floor; out of scope by §8 |
| Reachability gate | A new module must be reachable or declared | Undeclared-dependency, in one narrow sense |

The finding: this stack has a substantial floor set and **none of its floors targets the six shapes
of §4 directly**. Every shape passes every row of this table. The completion gates come closest and
depend entirely on whether the tests exercise the paths in question, which is exactly the property
happy-path-only work does not have — the tests were written by the same author with the same
conception of the feature, so they exercise what was built rather than what was required.

This is the gap this family was chartered to close, and it is a gap in enforcement rather than in
measurement, which is why it survived a stack with this many quality mechanisms. — Floor behaviours
OBSERVED from the enforcement surfaces during the Phase 0 audit; shape-coverage assessments INFERRED
against §4.

## 10. Failure modes

| Failure | Mechanism |
|---|---|
| **Floor as low bar** | The minimum drifts upward with the reference; eventually nothing ships |
| **Bar as high floor** | Frontier-level quality demanded for admissibility; all non-frontier work blocked |
| **Silent violation** | No declared escape, so legitimate exceptions become invisible breaches and the floor stops constraining |
| **Ritual accumulation** | The floor set grows without retirement until it is a compliance checklist — Part I's trap rebuilt by this family |
| **Decorative floor** | The check does not execute; zero violations read as structural safety |
| **Imported minimum** | A borrowed figure enforced without local derivation |
| **Unstated consequence** | A floor with no named failure, therefore unretirable and unarguable |
| **Exploration capture** | Exploratory exemption retained as the artifact graduates into production |

## 11. Detection signatures

1. **The tests that mirror the implementation.** Test cases enumerating exactly the paths that were
   built. Strong indicator of happy-path-only underbuild, since the tests inherit the author's
   conception of the feature.
2. **The silent failure.** A production incident whose first signal is a downstream symptom with no
   log, metric or trace at the origin. Unobservable underbuild, and it will have hidden others.
3. **The zero-violation floor.** A floor with no violations and no evidence its check ran.
4. **The growing checklist.** A floor set that only ever gains entries. No retirement condition was
   ever stated, so none can be applied.
5. **The undocumented exception.** Work that shipped below a floor with no deviation record. The
   escape route was absent or unusable, so the violation went underground.

## 12. Trap seeds — for Part XXII

- **T-CLAE-UNANNOUNCED-INCOMPLETENESS** — work that is real, shallow and free of marker tokens,
  passing every mechanical check because nothing was deferred in a way anyone recorded.
- **T-CLAE-FLOOR-AS-BAR** — a floor treated as a low bar, drifting upward with the reference until
  nothing is admissible.
- **T-CLAE-SILENT-VIOLATION** — a floor with no declared escape, defeated rather than obeyed, with
  the exceptions invisible.
- **T-CLAE-RITUAL-FLOOR-SET** — floors accumulated without retirement conditions until the set is a
  compliance checklist, reconstructing Part I's trap inside this family's enforcement half.
- **T-CLAE-DECORATIVE-FLOOR** — a floor whose check does not execute, whose zero violations read as
  structural safety.

## 13. Rule seeds — for Part XXIII

- **PR-CLAE-FLOORS-ARE-DERIVED** — a floor states the domain reasoning that produced its minimum.
  An imported figure is a preference and is labelled as one.
- **PR-CLAE-NAME-THE-CONSEQUENCE** — every floor names the failure class it prevents. A floor
  without one is not admitted to the set.
- **PR-CLAE-RETIREMENT-AT-CREATION** — every floor states, when created, what would make it
  unnecessary. A floor whose retirement condition cannot be stated indicates an unidentified
  consequence.
- **PR-CLAE-DECLARED-ESCAPE** — every floor has a recorded route to ship below it via a deviation
  with a proven constraint and measured loss. Floors without one produce silent violations.
- **PR-CLAE-VERIFY-THE-CHECK** — a floor's zero-violation record is evidence only alongside proof
  its check executed.
- **PR-CLAE-PROMOTE-RECURRING-RESIDUALS** — a residual recurring on one dimension across many
  artifacts is reviewed as a floor candidate; per-domain minima are cheaper than per-artifact
  measurement.

## 14. Eval seeds — for Part XXIV

- **Six-shape probe.** For a sample of shipped artifacts, check each of §4's shapes directly. This
  is the family's most direct test of the gap in §9 and needs no reference at all.
- **Test-mirror probe.** Compare each artifact's test cases against its implemented branches. Near-
  exact correspondence indicates tests that inherited the author's conception rather than the
  domain's requirements.
- **Check-execution probe.** For every floor, confirm its check actually ran on the last several
  artifacts. Zero violations without execution evidence is a decorative floor.
- **Escape-usage probe.** Count deviations recorded against each floor. A floor with many
  violations and no deviations has an unusable escape route and is being bypassed silently.
- **Retirement-condition probe.** Verify every floor states one. Those without are the seeds of the
  ritual accumulation in §6.
- **Floor economics probe.** For each floor, compare satisfaction cost against the expected cost of
  the failure it prevents. Net-negative floors are candidates for retirement independent of their
  soundness.

## 15. Production Reality Gate seed — for Part XXV

**Underbuild Floor Gate.** An artifact may be admitted only when each of the six shapes has been
checked and either cleared or covered by a recorded deviation. The gate additionally requires that
every floor applied names its consequence, carries a retirement condition, and has execution
evidence for its check on this artifact. A floor without execution evidence does not count toward
admission, since an unexecuted check and a passed check are indistinguishable in the record.

## 16. Pseudoflow — establishing and applying a floor

To establish one: name the failure class first, before any threshold. Determine the consequence — 
what the failure costs and who bears it. Derive the minimum from that consequence and this domain,
writing the derivation down; a figure with no derivation is a preference regardless of how sound it
sounds. State the retirement condition: what would make this floor unnecessary. State the escape
route: what constraint would justify shipping below it and what loss would have to be measured.
Confirm the check is evaluable at a cost the process bears, and confirm the floor's cost does not
exceed the consequence it prevents.

To apply one: run the check and record that it ran, not only its verdict. Where the artifact clears
the floor, record the execution alongside the pass. Where it does not, the artifact is inadmissible
unless a deviation is recorded with its constraint proven, its intent preserved and its loss
measured. Do not lower the floor to admit the artifact; lowering a floor to fit the work is the
mechanism by which floors become descriptions of what was built.

Periodically, review the floor set against its trigger history. Where a floor's retirement condition
has been met, retire it. Where a floor has zero violations, determine whether the check executed
before concluding anything from the zero. Where a floor has many violations and no deviations, its
escape route is unusable and it is being defeated rather than obeyed.

When a residual recurs on one dimension across many artifacts, review it as a floor candidate.
Promotion is how measurement cost is converted into enforcement, permanently.

## 17. Integration

Part XI derives floors properly and explains why imported minima fail. Part XVIII owns the escape
route: a deviation is the only legitimate way below a floor, and §5's property five is what makes
that route necessary rather than optional. Part XIX's evidence-gated autonomy uses floor clearance
as a precondition, since autonomous work below a floor is unbounded in exactly the way §4's shapes
describe. Part XXIII carries retirement conditions as a required rule field, and Part IX's ledger
receives promoted residuals as the evidence trail behind each derived floor.

Outside the family, the marker-token detector is endorsed unchanged for the incompleteness it does
catch, and the six shapes are offered as the complement it structurally cannot reach. The completion
gates are the natural host for the six-shape check, since they already run at the same moment.

## 18. Open questions

1. Are the six shapes exhaustive? They were derived from failure classes observable in this stack's
   own history plus the corpus, and a seventh may exist that neither surfaced. — HYPOTHESIS; the
   honest expectation is that the list grows.
2. Can the shapes be checked mechanically, or does each require judgment? Unbounded and
   undeclared-dependency look mechanically checkable; happy-path-only and single-instance may
   require knowing the declared failure modes and input range, which is a specification question
   rather than an inspection one. — UNKNOWN, and it determines whether this Part is affordable.
3. What is the correct review cadence for the floor set? §6 requires review against trigger history,
   and reviewing too rarely permits ritual accumulation while reviewing too often destabilizes
   admissibility. — UNKNOWN.

## 19. Institutional writeback

Five trap seeds, six process-rule seeds, six eval seeds and one production gate.

Three portable results. **The six shapes** — a checklist for real-but-shallow work that requires no
reference, no ledger and no machinery, and that every mechanical completeness check in an ordinary
stack will miss. **A floor with no escape route will be defeated, not obeyed** — the declared
deviation is what converts an invisible breach into a recorded one, and floor sets without it decay
into ceremony for the cases that were going to comply anyway. And **every floor carries a retirement
condition at creation**, because an enforcement set that only grows becomes the self-authored
compliance criterion this family exists to attack, arrived at by this family's own machinery.
