---
title: "CLAE Part V — Reference Acquisition, Versioning and Provenance"
family: clae
part: V
depends_on: [IV]
feeds: [VI, IX, XV, XXI]
status: SEALED
date: 2026-07-26
---

# Part V — Reference Acquisition, Versioning and Provenance

## 1. Purpose

Part IV said what qualifies as a reference. This Part says how one is obtained, how it is held
so that residuals measured a year apart mean the same thing, how its decay is detected, and how
it is retired.

The framing that makes the rest follow: **a reference is not a fact, it is an acquired artifact
with a lifecycle.** Treating it as a fact — something true that can simply be cited — produces
every failure in this Part. Facts do not go stale, do not drift, do not need custody, and cannot
be captured. References do all four.

This Part also closes an open question left by Part II: whether references should be pinned or
live. The answer is neither, and §5 gives the construction that dissolves the dilemma.

## 2. The four lifecycle stages

| Stage | Question | Consequence of skipping it |
|---|---|---|
| **Acquisition** | How was this obtained, and what was known at the time? | The reasoning is unrecoverable within days |
| **Pinning** | Which exact version do residuals refer to? | Residuals across time are incomparable and nobody notices |
| **Use** | Is it still valid, and along which dimensions? | Silent measurement against an expired bar |
| **Retirement** | Has it been superseded, captured, or lost standing? | A dead reference keeps producing confident numbers |

Most surfaces that adopt distance discipline implement acquisition and use, and skip pinning and
retirement. That combination produces numbers that look rigorous and cannot be compared to each
other, which is worse than the compliance reporting it replaced, because the numbers invite
trending and the trend is meaningless.

## 3. Acquisition — the perishability principle

The information required to justify a reference is **perishable**. Which candidates were
considered, why this one won, what its standing argument was, how much the acquisition cost, what
the observability profile looked like — all of it is vivid at the moment of acquisition and gone
within days. It cannot be reconstructed later, because reconstruction is performed by the same
party the externality condition exists to constrain, and a reconstructed justification is an
internally-authored justification.

> **Provenance is written at acquisition or it is written by the wrong author.**

The acquisition record therefore captures, in one act:

- **Identity** — what the object is, unambiguously enough to be re-obtained.
- **Version** — the exact revision, edition, build or content hash.
- **Date and method** — when and how it was obtained.
- **Fidelity** — per §4.
- **Class and direction** — from Part IV §3 and §5; historical-self references carry the
  regression-only label here.
- **Standing argument** — why this object is defensibly ahead along this dimension, in the
  acquirer's own words.
- **Candidates considered and rejected** — with the reason, closing the selection-laundering hole
  Part IV §6 named.
- **Observability profile and cost** — which properties can be observed, at what effort.
- **Capture risk** — where the object now lives, who can modify it, and what would make the
  capture detectable.
- **Horizon** — declared now, per §6, not when staleness is suspected.

A record missing the standing argument cannot be defended. One missing the rejected candidates
hides an internal choice inside an external object. One missing the horizon guarantees silent
staleness, because nothing will ever prompt the question.

## 4. Acquisition methods and fidelity

Fidelity is a property of *how the reference was obtained*, and it propagates: every residual
measured against a reference inherits that reference's fidelity, and no residual can be more
trustworthy than the acquisition beneath it.

| Method | What is held | Fidelity | Principal risk |
|---|---|---|---|
| **Direct observation** | The instance itself, inspectable on demand | Highest | Acquisition cost; availability may lapse |
| **Captured artifact** | A snapshot, recording or export of the instance | High | The capture may omit the dimension later needed |
| **Derived measurement** | Measured values, not the instance | Medium | Only the dimensions measured at capture are ever available |
| **Third-party report** | Another party's assertions about the instance | Lowest | Sits at the boundary of Part IV's unobserved-claim degenerate |

The asymmetry between rows two and three matters more than it appears. A captured artifact can be
re-examined along a dimension nobody thought of at acquisition time; a derived measurement cannot.
**Capturing the object is almost always worth more than capturing the numbers**, and costs little
more at the moment of acquisition — which is the only moment the choice is available.

The third-party report is admissible only when its own provenance is recorded and the residual is
labelled with that fidelity. Where a report is the sole available access, the honest position is
usually that the dimension is undefined rather than measured at low fidelity, because a low-
fidelity number and an absent number are treated identically by every downstream consumer except
the one that should have been warned.

## 5. Pinning — dissolving the pinned-versus-live dilemma

The apparent dilemma: a pinned reference resists bar inflation and accumulates staleness; a live
reference tracks the world and makes the residual ledger unstable, since the bar moves under the
measurements.

Both horns assume the choice is between one pinned value and one moving value. The construction
that dissolves it:

1. **The reference is always pinned.** Every residual cites a specific pin, never a moving object.
2. **The pin is versioned.** Pins form an ordered sequence: generation one, generation two.
3. **A pin update is an explicit event**, never a silent refresh, and it produces a record.
4. **Residual trends are valid only within a pin generation.** Across generations, a trend is
   published only alongside the re-baseline delta.

The reference is therefore stable for measurement and current for governance, and the tension
moves from an unresolvable design choice to a scheduled, visible act.

**Answering Part II's open question.** The horizon question is not answered globally by choosing
pinned or live; it is answered per reference class by choosing the *pin update cadence*, which is
the subject of §6.

## 6. Horizon by class

The horizon is declared at acquisition and driven by what actually makes that class of reference
decay.

| Class | Horizon driver | Expiry means |
|---|---|---|
| **Formal bound** | None; a limit does not decay | Never expires; only its applicability to the dimension can be disproved |
| **External specification** | The issuing body's revision cadence | A new revision exists; the pin is a generation behind |
| **Exemplar instance** | The rate at which the domain's practice changes | Instances now exist that this one no longer represents |
| **Prior-art corpus** | Corpus admission rate | The corpus no longer reflects the population |
| **Historical self** | One generation | Superseded on the next release by construction |
| **Judgment aggregate** | Shortest of all; judgment shifts continuously | The aggregated view no longer holds |

A horizon is a *prompt to re-examine*, not an automatic invalidation. At expiry the reference is
re-argued: it may be re-pinned unchanged with a fresh standing argument, updated to a new
generation, or retired. What must not happen is expiry passing unobserved, which is what a
declared horizon exists to prevent.

## 7. Three decays, three signatures, three remedies

These are routinely collapsed into "the reference is old". They are different failures.

**Staleness.** The reference is unchanged; the world moved past it. The reference is now behind
the achievable state. *Residuals are understated* — the artifact looks closer to the bar than it
is, which is the most flattering and therefore least-questioned error. Signature: residuals
trending to zero while the domain visibly advances. Remedy: re-acquire at a new generation.

**Drift.** The reference itself changed upstream. Residuals measured before and after are
incomparable, in an unknown direction. Signature: a step change in residual across many
dimensions at once, with no corresponding change in the artifact. Remedy: pin discipline, §5 —
drift is impossible against a pin, which is the main argument for pinning at all.

**Relevance decay.** The artifact's purpose moved and the reference no longer has standing along
the dimension. The residual is not wrong; it is *irrelevant*, which is harder to notice because
the number is still correct. Signature: residuals accurate, stable, and no longer consumed by
anyone. Remedy: retirement, §8 — re-acquisition would not help, because the problem is standing
rather than currency.

Distinguishing them matters because the remedies are mutually unhelpful: re-acquiring a reference
whose standing decayed produces a fresh, precise, still-irrelevant number, and retiring a
reference that was merely stale discards a working relationship.

## 8. Bar inflation and residual change decomposition

Bar inflation is the governance failure that ends distance disciplines. The reference is refreshed
faster than work closes the gap, the residual never falls, effort appears futile, and the ledger
is abandoned as demoralizing noise. Critically, **every individual act in that sequence is
correct** — each refresh was justified, each measurement honest.

The mechanism that prevents it is not slower refreshing. It is attribution.

**Any change in a residual between two reports decomposes into two parts:** the portion
attributable to the artifact changing, and the portion attributable to the reference changing. A
report giving only the net figure conflates them, and conflation is the whole failure. A team that
closed a real gap while the bar rose further sees a flat number and concludes the work was
worthless.

The rule follows directly: **a pin update publishes the re-baseline delta** — the residual
measured against both the old and the new pin, for the unchanged artifact. That single extra
measurement, taken once per pin update rather than per assessment, separates the two causes
permanently and cheaply.

With decomposition available, bar inflation stops being invisible. A reference whose bar-
attributable movement consistently exceeds the work-attributable movement is either advancing
faster than the effort allocated to it — a resourcing fact worth knowing — or is being refreshed
without justification, which the acquisition records will show.

The cost is one extra measurement per pin update. The failure it prevents is the abandonment of
the entire discipline, which is the observed end state of most measurement programmes.

## 9. Retirement

A reference is retired when it is superseded by a better-qualified candidate, when its standing is
disproved, when its relevance decays, when observability is lost, or when it is captured per Part
IV §6 and cannot be re-externalized.

Retirement is an event with a record: what retired it, when, and which residuals were measured
against it.

**Residuals measured against a retired reference are marked, never deleted.** Deleting them
destroys the history that makes trends interpretable and quietly improves the ledger's appearance
— an ideal target for the mechanism this family exists to prevent. A marked residual is
interpretable: it says what was true, against what, until when.

## 10. Custody — where the provenance record lives

Part IV left this open: if the provenance record is editable by the assessing party, condition C4
protects nothing, because capture can be performed on the record as easily as on the reference.

The partial answer is that **tamper-evidence is achievable with substrate this stack already
has**, and tamper-proofing is not.

An acquisition record committed to version control acquires an append-only history, a content
hash, a timestamp and an author. Editing it later is possible and is no longer *silent* — it
leaves a diff, in a log, attributable. Since the failure this family fears is silent substitution
rather than open revision, tamper-evidence is the property that actually matters.

The honest limit: a party with authority to rewrite history can still erase the trail. This does
not become secure by adding process; it becomes secure only by moving custody outside the party's
authority, which is a substrate decision beyond this family's scope. What this Part requires is
that acquisition records live in an append-only store with attribution, and that any store failing
that is declared, so consumers know the provenance is assertion rather than evidence.

## 11. Evidence — a compliant acquisition, from this compendium's own construction

This family need not look far for a worked example. The corpus underlying this compendium was
acquired under exactly the record this Part specifies, before any design work began.

| Field | What was recorded |
|---|---|
| Identity | Nine reverse-engineering rounds, named individually |
| Version | Archive content hash, plus a per-file hash, byte length, line count and word count |
| Date and method | Acquisition date; extraction to a controlled read-only working directory |
| Fidelity | Direct observation — each file read to end-of-file, with that fact recorded per file |
| Integrity | Per-file corrupt, truncated and empty checks, all recorded as observed values |
| Candidates | Two pillars found to exist only inside the archive and nowhere else; the archive declared authoritative on that basis, with the reasoning recorded |

That record makes every later claim in this compendium re-checkable by a party who was not
present. It is also the reason the two archive-only pillars did not silently vanish: the
enumeration was performed against what the archive contained rather than against what was
remembered, which is Part IV §7's discovery mechanism applied to the corpus itself. — OBSERVED;
the evidence ledger is the artifact.

The contrast with the rest of the stack is the finding. The two surfaces Part IV endorsed carry no
acquisition record at all: the index-direction monitor compares against a prior value with no pin
generation and no horizon, and the reachability audit rediscovers its set each run with no record
of what the set was last time. Both are correct in their comparisons and both are unable to
answer, after the fact, what they were comparing against. — INFERRED from their described
behaviour; recorded as a gap rather than a defect, since neither claimed the property.

## 12. Boundary

Acquisition discipline applies to references and to nothing else. Criteria, rubrics and internal
thresholds need version control and review; they do not need standing arguments or horizons,
because they make no claim about the outside world.

Nor does it apply to observations. An observation is dated and attributed by nature and does not
require a horizon: it does not decay, it simply describes a past state. Applying reference
machinery to observations produces ceremony without protection.

Finally, retirement discipline does not apply to formal bounds. A limit cannot be superseded; only
the claim that it applies to a given dimension can be disproved, and that disproof is a change to
the standing argument rather than a retirement.

## 13. Failure modes

| Failure | Mechanism |
|---|---|
| **Reconstructed provenance** | Justification written after the fact by the party the record exists to constrain |
| **Silent refresh** | The pin advances without an event, and pre-refresh residuals are compared to post-refresh ones |
| **Conflated attribution** | Net residual change reported without decomposition; real progress reads as futility |
| **Numbers instead of the object** | Derived measurement captured where the artifact could have been, foreclosing every later dimension |
| **Expired-in-place** | The horizon passes unobserved; measurement continues against a bar that is behind |
| **Retirement by deletion** | Residuals against a retired reference removed rather than marked, improving the ledger's appearance |
| **Custody assumed** | The provenance record treated as evidence while living somewhere freely editable |

## 14. Detection signatures

1. **The undated citation.** A reference cited with a name and no version. Every residual beneath
   it is uninterpretable, and the absence is invisible in the reports.
2. **The asymptotic residual.** Residuals trending smoothly toward zero across every dimension.
   Genuine improvement is uneven; smooth convergence to zero more often indicates staleness, per
   §7.
3. **The synchronized step.** Many residuals changing at once with no artifact change — drift, and
   evidence that the reference was live rather than pinned.
4. **The unattributed flat line.** Residual constant across reports with no decomposition
   published. Either nothing was done or the bar moved equally; the report cannot distinguish
   them, which is the state that ends measurement programmes.

## 15. Trap seeds — for Part XXII

- **T-CLAE-RECONSTRUCTED-PROVENANCE** — the standing argument and rejected candidates are written
  after the fact by the assessing party, laundering an internal choice.
- **T-CLAE-SILENT-PIN-REFRESH** — the reference advances without an event; residuals across the
  boundary are compared as though commensurable.
- **T-CLAE-CONFLATED-ATTRIBUTION** — net residual change published without the work-versus-bar
  decomposition, making real progress indistinguishable from none.
- **T-CLAE-EXPIRED-IN-PLACE** — a declared horizon passes with no re-examination, and measurement
  continues against a bar the world has passed.

## 16. Rule seeds — for Part XXIII

- **PR-CLAE-ACQUIRE-WITH-RECORD** — a reference is usable only from the moment its acquisition
  record exists, complete with standing argument, rejected candidates and horizon. Records written
  later are labelled reconstructed and the dependent claims re-read.
- **PR-CLAE-ALWAYS-PINNED** — residuals cite a pin generation, never a moving object. Pin updates
  are events with records.
- **PR-CLAE-PUBLISH-THE-REBASELINE** — a pin update publishes the unchanged artifact's residual
  against both old and new pins, so subsequent changes decompose into work and bar.
- **PR-CLAE-TREND-WITHIN-GENERATION** — a residual trend crossing a pin boundary is published only
  alongside the re-baseline delta.
- **PR-CLAE-CAPTURE-THE-OBJECT** — where both are affordable, hold the artifact rather than the
  derived measurements, so unforeseen dimensions remain available.
- **PR-CLAE-MARK-DONT-DELETE** — residuals against a retired reference are marked with the
  retirement, never removed.

## 17. Eval seeds — for Part XXIV

- **Record-completeness probe.** For each reference in use, verify all ten acquisition fields.
  Missing standing arguments and missing horizons are the two that predict later failure.
- **Pin-citation probe.** Sample residuals and verify each cites a pin generation. Uncited
  residuals are uninterpretable and are relabelled as such.
- **Decomposition probe.** For each pin update, verify a re-baseline delta was published. Its
  absence means every subsequent trend conflates work with bar movement.
- **Horizon-expiry probe.** List references past their declared horizon with no re-examination
  event. This probe is cheap, runs unattended, and catches the §7 staleness failure before it
  flatters a report.
- **Fidelity-propagation probe.** Verify residuals inherit the fidelity of the reference beneath
  them, and that no residual is reported at higher fidelity than its acquisition supports.

## 18. Production Reality Gate seed — for Part XXV

**Provenance Integrity Gate.** A distance claim may be published only when its reference cites a
pin generation, an acquisition record with date, method and fidelity, and a horizon that has not
expired without re-examination. A pin updated since the last published claim additionally requires
the re-baseline delta. Failure downgrades the claim to an uninterpretable measurement rather than
blocking the work, consistent with Part II §9: distance informs and never enforces.

## 19. Pseudoflow — acquiring and holding a reference

At the moment a candidate is selected, and before any measurement is taken, write the acquisition
record in full: identity, version, date, method, fidelity, class, direction, standing argument,
the candidates rejected and why, the observability profile and its cost, the capture risk, and the
horizon. Nothing here is recoverable later by anyone whose reconstruction would count.

Prefer holding the object over holding measurements derived from it, whenever both are affordable
at acquisition. Only the object supports a dimension nobody has thought of yet.

Assign the pin generation. From this moment, every residual cites that generation and never the
underlying object, so that upstream change cannot silently alter what past measurements meant.

Store the record where history is append-only and attributed. Where the store does not have that
property, say so in the record, so consumers read the provenance as assertion rather than
evidence.

At the declared horizon, re-examine rather than automatically replace. The reference may be
re-pinned unchanged with a refreshed standing argument, advanced to a new generation, or retired.
Whichever occurs, record it as an event.

On advancing a generation, measure the unchanged artifact against both pins and publish the
difference. Thereafter every residual change decomposes into work and bar.

On retirement, record what retired it and mark every residual measured against it. Do not remove
them; the ledger's history is the only thing that makes its trends readable.

## 20. Integration

Part VI takes the observability profile recorded here and turns it into extraction procedure. Part
IX consumes pin generations, since residuals from different generations may not be aggregated
without the re-baseline delta. Part XV's incident-derived probes are acquisitions in their own
right and inherit this record contract. Part XXI treats bar inflation as a failure lineage, with
§8's decomposition as its principal control.

Outside the family, version control is used as the append-only provenance store rather than
building one, and the compendium's own corpus evidence ledger stands as the worked example a new
acquisition can be modelled on.

## 21. Open questions

1. What is the correct pin update cadence when the horizon driver is itself unobservable? An
   exemplar's horizon is driven by the rate the domain changes, and measuring that rate requires
   the surveying the reference was adopted to avoid. — UNKNOWN.
2. Can the re-baseline delta be computed when the old pin is no longer observable? §8 assumes both
   pins can be measured against at the moment of update; a reference that lapsed before the update
   makes decomposition impossible, and the correct handling of that gap is unresolved. — UNKNOWN.
3. Does fidelity compose across a chain? Where a residual is derived from another residual, it is
   unclear whether fidelity takes the minimum of the chain or degrades further at each step. — 
   HYPOTHESIS: it takes the minimum, unmeasured.

## 22. Institutional writeback

Four trap seeds, six process-rule seeds, five eval seeds and one production gate. Part II's open
question on pinning is closed by §5's construction; Part IV's custody question is partially closed
by §10, with the residue stated rather than papered over.

The portable result is §8's residual change decomposition. Most measurement programmes are
abandoned rather than disproved, and they are abandoned because effort stops appearing to matter.
Separating work-attributable from bar-attributable movement costs one additional measurement per
pin update and removes the specific ambiguity that causes the abandonment.
