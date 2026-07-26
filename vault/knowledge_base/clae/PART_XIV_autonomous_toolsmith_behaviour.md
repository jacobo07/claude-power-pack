---
title: "CLAE Part XIV — Autonomous Toolsmith Behaviour"
family: clae
part: XIV
depends_on: [XIII]
feeds: [XV, XIX, XXI, XXV]
status: SEALED
date: 2026-07-26
---

# Part XIV — Autonomous Toolsmith Behaviour

## 1. Purpose

Part XIII established how to select an instrument. This Part addresses the case where selection
fails: no existing instrument reaches the dimension, and one must be built mid-work by the agent
doing the work.

This is not a tooling convenience. It is a decision point with a specific structure — a moment when
the correct action is to stop producing and start building the means to see — and it is the decision
autonomous systems get wrong most reliably, for a reason that is structural rather than careless.

The Part states when toolsmithing is mandatory, why every local incentive argues against it, the
four conditions that must all hold before building, the rule that terminates the instruments-to-
measure-instruments recursion, and the accounting change without which toolsmithing will always look
like a failed cycle.

## 2. When toolsmithing is mandatory

Three triggers, each arriving from an earlier Part.

1. **The null pivot.** Part VIII §7: consecutive null outcomes on a dimension mean the problem is no
   longer the correction. Continuing to correct is retrying a failed shape; the thing to change is
   the instrument.
2. **The level shortfall.** Part XIII §3: the downstream operation requires L3 to rank or L4 to
   correct efficiently, and no available instrument reaches it. Proceeding means ranking on unknown
   magnitudes or correcting by guess.
3. **The missing capability.** Part XII: a dimension now needed has no complete Phase Zero chain,
   and the measurement debt declared at the outset has come due.

Underneath all three is one question:

> **Is the blocker the work, or the ability to see the work?**

If the work is blocked, work harder. If the *seeing* is blocked, building the instrument **is** the
work — and everything produced without it is unfalsifiable, accumulating at whatever rate production
runs at.

## 3. Why every local incentive argues against it

The bias toward proceeding is not carelessness. It is an asymmetry in when the two costs become
visible.

**The cost of the detour is immediate, visible and attributable.** Time spent building an instrument
is time not spent producing, and it is obvious to everyone including the builder.

**The cost of proceeding blind is deferred, invisible and unattributable.** Work continues, output
accumulates, nothing appears wrong. The cost materializes later as corrections that cannot be
verified, residuals that cannot be interpreted, and a body of output nobody can evaluate — by which
point it is no longer connected to the decision that caused it.

Every local decision therefore favours proceeding, and a series of individually reasonable local
decisions produces a system that has never been observed to work.

For an autonomous agent the asymmetry is sharper still, for two reasons Part XII §7 established. The
agent can produce plausible work indefinitely without observation, and nothing in its immediate
feedback distinguishes verified output from unverified output — both look like completed tasks.
And the informal model a human carries between sessions, which partially compensates for missing
instrumentation, does not persist. **What is not observable is not merely unmeasured; for an agent
it is unavailable.**

The practical consequence: toolsmithing must be triggered by a *rule* rather than by judgment,
because judgment at the decision point is systematically biased by an asymmetry the decider cannot
see from inside.

## 4. The four conditions

All four, before building anything.

1. **The dimension is required**, not merely interesting. Required means a downstream operation —
   a ranking, a correction, a floor check, an admissibility decision — cannot proceed correctly
   without it.
2. **No existing instrument reaches it**, established by actually walking Part XIII §3's selection
   rather than by assuming. This condition fails more often than expected: the needed observation is
   frequently available from a capture that already exists and is unused.
3. **The instrument costs less than the unfalsifiable work it prevents.** An instrument is an
   economic object exactly as a floor is (Part X §8). Where the dimension affects little and the
   instrument is expensive, the honest output is *undefined* with the reason.
4. **It will be used more than once.** A single-use instrument is usually a manual observation
   wearing engineering. Where the question is asked once, answer it once and record the answer.

Condition two deserves the most attention because it is the cheapest to check and the most
frequently skipped. Building is engaging; searching is not.

## 5. Terminating the recursion

An instrument is an artifact and is subject to this entire family: it needs coverage, an envelope,
three-valued output, and a known-answer case (Part XIII §4, §8). Which raises the obvious problem —
establishing those may itself require an instrument.

The recursion is real. It must terminate, and it must not terminate by building a third level.

> **An instrument that requires its own new instrument to validate is over-scoped. Shrink it until
> its known-answer case can be established by direct inspection.**

This is the operative rule and it is a scope constraint, not a permission to skip validation. If the
thing being built is so elaborate that confirming its correctness needs machinery, the correct
response is a narrower instrument whose output a person can check against a case they can verify by
looking.

Three legitimate terminations, in order of preference: **direct inspection** of a known-answer case;
a **formal bound** the instrument's output can be checked against, which cannot itself be wrong; and
an **oracle**, per Parts XVI and XVII, where neither is available.

## 6. The minimum viable instrument

The characteristic failure of agentic toolsmithing is not building too little. It is building too
much: a general framework where a specific probe was needed, with configuration, extension points
and coverage of cases nobody has encountered.

> **Build the narrowest instrument that answers the question that blocked you.**

Part XIII's probe — one specific question at one point — is usually the right kind, and it is the
cheapest to validate by direct inspection, which keeps §5's termination available.

Generalize on the **second** use, never in anticipation. An instrument generalized before its second
use has been generalized against an imagined second case, and the imagined case is authored by the
same party whose model is in question — Part XII §2's retrofit blindness, arriving in the toolsmith's
own work.

This also preserves the option to discover that the second use never comes, which is common and is
information: an instrument used once was a manual observation, and condition four was not actually
satisfied.

## 7. Abuse boundaries

Toolsmithing can become avoidance, and it is well-camouflaged because it produces artifacts and
feels rigorous. Four signatures.

**The yak-shave.** The instrument's scope expands while the original question recedes. Each
expansion is justified by the last.

**The substitution.** Toolsmithing chosen because building an instrument is more tractable, better
understood and more pleasant than the actual problem. The tell is that the instrument is being built
before the blocking question was written down.

**The recursion.** Instruments to measure instruments, per §5.

**The orphan.** Instruments built, used once, and left. This is the same failure this stack has
already sealed for modules — something that imports cleanly, works when invoked, and is invoked by
nothing.

Three controls, all cheap:

1. **Write the blocking question before building.** One sentence, recorded. It bounds the instrument
   and makes the yak-shave visible when the built thing answers something else.
2. **Box the scope in advance.** Exceeding the box is a signal to reconsider whether the instrument
   was the right response, not a reason to continue.
3. **Re-run the blocking question immediately.** The instrument's first use is answering the question
   that justified it. An instrument that does not immediately answer it was not the right instrument.

## 8. Ownership after the fact

An instrument built mid-work is an artifact with an owner, or it rots into the orphan case above.

> **At the end of the cycle, a built instrument enters the instrument register or is deleted. There
> is no third state.**

The register carries what Part XIII §4 requires — coverage, envelope, perturbation, extraction level,
cost, failure behaviour — plus the known-answer case and its last validation date. Registration is
what makes the instrument findable by the next agent, which is the entire reason it was worth
building rather than observing manually.

Deletion is a legitimate and underused outcome. An instrument that answered its question and has no
second use costs nothing to delete and costs ongoing attention to keep. The failure is neither
registering nor deleting — leaving it present, unregistered, and slowly diverging from an
environment nobody is checking it against.

## 9. Cost accounting

Toolsmithing consumes correction capacity, which means it reduces k for the cycle it happens in
(Part VIII §3). Recorded naively, that cycle closes zero distance and reports as unproductive.

This is the mechanism by which organizations stop building instruments: not a decision to stop, but
an accounting in which building one always looks like a wasted cycle.

The correction is to record it as what it is:

> **A cycle spent building an instrument closes zero quality debt and repays instrument debt.**

Part IX §5 established the three debts precisely so that this distinction is expressible. A cycle
reporting *instrument debt repaid* alongside *zero quality debt closed* is legible as productive
work; the same cycle reporting only zero distance closed is legible as failure. The numbers are
identical. The difference is entirely whether the accounting has three debts or one — which is the
clearest demonstration in the family that Part IX's split is operational rather than taxonomic.

## 10. Boundary

Do not toolsmith where the question is asked once — answer it manually and record the answer. Where
the dimension is an oracle question, per Part III's boundary test, no instrument can answer it and
building one fabricates a result. Where a formal bound exists, use it; it needs no construction and
cannot drift. And where the instrument's cost exceeds the consequence of leaving the dimension
unmeasured, record *undefined* with the reason and move on — that is a complete and honest outcome,
not a deferral.

## 11. Evidence — instruments built in response to blockers in this stack

| Instrument | Trigger | Registered? | Assessment |
|---|---|---|---|
| Reachability audit | A blocking question that could not be asked: which modules are reached | Yes — with a named baseline | The model case. Narrow, answers exactly its question, output is a named set |
| Source map with content hashes | Read cost blocking bulk audit | Partially — consumed by a hook | A capture built for one purpose, under-used for others per Part XIII §11 |
| Coordinate graph over the repository | Navigation cost | Yes | Broad; generalized early, which §6 argues against, and it has found second uses |
| This compendium's gate script | Built in Phase Zero, before the work it gates | No — it is inline in the construction, not registered | Correct timing, unregistered; the orphan risk §8 names |
| Recurring-error log | Repeated failures with no cross-session memory | Yes | Narrow, durable, and it is what makes Part VIII's null pivot detectable at all |

Two findings.

**The reachability audit is this stack's exemplary toolsmith artifact.** It exists because a question
could not be asked — not because a general capability was desired — it is narrow, it answers exactly
that question, it reports a named set rather than a count, and it is registered with a baseline.
Anything built under this Part should be modelled on it.

**This family's own gate script is unregistered.** It was built at the right moment and in the right
scope, it has been used thirteen times, and it exists nowhere as a declared instrument with coverage
and a known-answer case. By §8 it is currently in the third state that is supposed not to exist. —
Instrument histories OBSERVED from the surfaces and this session's own construction; assessments
INFERRED against §6 and §8.

The second finding is recorded rather than resolved, because resolving it inside the artifact it
concerns would be circular. It belongs in the family's completion report as declared instrument debt.

## 12. Failure modes

| Failure | Mechanism |
|---|---|
| **Proceeding blind** | The visible detour cost beats the invisible blind cost at every local decision |
| **Unsearched build** | Condition two skipped; an instrument built where a capture already held the observation |
| **Recursive validation** | An instrument elaborate enough to need its own instrument to check |
| **Premature generality** | Generalized before a second use, against an imagined case the builder authored |
| **Yak-shave** | Scope expands, the blocking question recedes, each expansion justified by the last |
| **Substitution** | Instrument-building chosen because it is more tractable than the actual problem |
| **Orphan instrument** | Built, used once, neither registered nor deleted, diverging quietly |
| **Toolsmithing as failed cycle** | Recorded as zero distance closed; the accounting teaches the organization to stop |

## 13. Detection signatures

1. **The unwritten question.** No record of the blocking question predating the instrument. Either
   substitution or yak-shave; both, usually.
2. **The instrument that outgrew its answer.** The built thing does more than the blocking question
   required and has not been re-run against it.
3. **The unregistered veteran.** An instrument in repeated use with no register entry, no declared
   coverage and no known-answer case.
4. **The zero-distance cycle.** A cycle reporting no progress that in fact repaid instrument debt.
   Its presence in the record is what the accounting in §9 exists to prevent.
5. **The capture nobody searched.** A new instrument observing something an existing capture already
   holds.

## 14. Trap seeds — for Part XXII

- **T-CLAE-PROCEED-BLIND** — production continues past a seeing-blocker because the detour cost is
  visible and the blind cost is not, accumulating unfalsifiable output at production rate.
- **T-CLAE-RECURSIVE-INSTRUMENT** — an instrument requiring its own new instrument to validate,
  producing an unterminating tower instead of a narrower tool.
- **T-CLAE-PREMATURE-GENERALITY** — an instrument generalized before its second use against a case
  the builder imagined, which is retrofit blindness inside the toolsmith's own work.
- **T-CLAE-ORPHAN-INSTRUMENT** — built, used once, neither registered nor deleted, drifting against
  an environment nobody checks it against.
- **T-CLAE-TOOLSMITH-AS-FAILURE** — instrument-building recorded as a zero-distance cycle, teaching
  the organization to stop building instruments without anyone deciding to.

## 15. Rule seeds — for Part XXIII

- **PR-CLAE-SEEING-BLOCKER-STOPS-WORK** — where the blocker is the ability to observe rather than
  the work itself, building the instrument is the work. Production past a seeing-blocker is recorded
  as unfalsifiable output.
- **PR-CLAE-FOUR-CONDITIONS** — required dimension, no existing instrument found by actual search,
  cost below the unfalsifiable work prevented, and more than one use. All four before building.
- **PR-CLAE-SHRINK-DONT-STACK** — an instrument needing its own instrument to validate is
  over-scoped and is narrowed until direct inspection of a known-answer case suffices.
- **PR-CLAE-NARROWEST-FIRST** — build the narrowest instrument answering the blocking question.
  Generalize on the second use, never in anticipation.
- **PR-CLAE-WRITE-THE-BLOCKER-FIRST** — the blocking question is recorded before construction
  begins, and the instrument's first use is answering it.
- **PR-CLAE-REGISTER-OR-DELETE** — at cycle end a built instrument is registered with its Part XIII
  declarations and known-answer case, or deleted. Leaving it unregistered is not an outcome.
- **PR-CLAE-BOOK-TO-INSTRUMENT-DEBT** — a cycle spent building an instrument reports instrument debt
  repaid, never zero quality debt closed alone.

## 16. Eval seeds — for Part XXIV

- **Blocker-provenance probe.** For each instrument built in the last period, look for the blocking
  question recorded before construction. Absence indicates substitution or yak-shave.
- **Search-first probe.** For each new instrument, determine whether an existing capture already
  held the observation. This probe is cheap and is expected to find several.
- **Second-use probe.** Count instruments used exactly once. Each was a manual observation that
  became an artifact, and each is a register-or-delete decision that was never made.
- **Register-completeness probe.** Compare instruments in active use against the instrument register.
  Unregistered veterans have no coverage declaration, so every zero they have ever reported is
  uninterpretable.
- **Accounting probe.** Examine cycles reporting zero distance closed and determine how many repaid
  instrument debt. A high proportion means the accounting is teaching the wrong lesson.

## 17. Production Reality Gate seed — for Part XXV

**Toolsmith Gate.** An instrument built during work may be used in accounting only when its blocking
question was recorded before construction, all four conditions of §4 were established, its
known-answer case is verifiable by direct inspection, and it is registered with its Part XIII
declarations at cycle end. A cycle containing instrument construction publishes instrument debt
repaid alongside its distance figures. Instruments failing registration at cycle end are recorded as
orphans, which is a visible state rather than a silent one.

## 18. Pseudoflow — encountering a seeing-blocker

When progress stops, first classify the blocker: is the work blocked, or is the ability to observe
the work blocked? If the latter, write the blocking question down in one sentence before doing
anything else. That sentence bounds everything that follows and is the only defence against the
scope expanding past it.

Search before building. Walk the existing instruments and captures against Part XIII's selection
questions, and check specifically whether a capture already holds the observation under a different
name. This step fails to find something less often than expected.

If nothing exists, check the four conditions explicitly. A dimension that is interesting rather than
required, or a question asked once, does not justify an instrument — answer it manually and record
the answer.

Build the narrowest thing that answers the written question. Resist configuration, extension points
and coverage of cases nobody has met. If the design has grown elaborate enough that checking its
correctness would need machinery, it is over-scoped: narrow it until a known-answer case can be
verified by looking.

Establish the instrument's declarations before first use: coverage, envelope, perturbation,
extraction level, cost, and three-valued output. Establish the known-answer case and run it.

Re-run the blocking question. If the instrument does not answer it, it was the wrong instrument, and
that is discovered now rather than after it has been depended on.

At cycle end, register it with its declarations and validation date, or delete it. Record the cycle
as instrument debt repaid, so that the effort reads as what it was rather than as a cycle that
closed nothing.

## 19. Integration

Part XV takes instruments built in response to specific incidents and makes them durable probes,
which is the highest-value subclass of what this Part produces. Part XIX's evidence-gated autonomy
inherits §2's rule as a stopping condition: an autonomous agent encountering a seeing-blocker halts
production rather than continuing, because continuing is precisely the unbounded case. Part XIII's
instrument register is the destination §8 requires. Part IX's three debts make §9's accounting
expressible.

Outside the family, the reachability audit is the model artifact and the pattern new instruments
should follow. The recurring-error log is noted as the instrument that makes Part VIII's null pivot
detectable at all — without it, consecutive nulls are not visible as a pattern, and this Part's first
trigger never fires.

## 20. Open questions

1. Can the seeing-blocker classification be made mechanical? §2's question is the trigger for
   everything here, and if it requires judgment at exactly the moment §3 shows judgment to be biased,
   the rule may not fire when it is most needed. — UNKNOWN, and the most serious open item in this
   Part.
2. Is the register-or-delete rule affordable for very small instruments? A one-line check built in
   passing may cost more to register than to rebuild, which would make deletion the standing answer
   and lose the findability that justified building. — HYPOTHESIS.
3. How is the cost of unfalsifiable work estimated for condition three? It requires pricing output
   that has not yet been shown wrong, which is the same estimation problem Part XI §5's likelihood
   threshold faces. — UNKNOWN.

## 21. Institutional writeback

Five trap seeds, seven process-rule seeds, five eval seeds and one production gate.

Three portable results. **The asymmetry**: the cost of building an instrument is immediate, visible
and attributable, while the cost of proceeding without one is deferred, invisible and unattributable
— so every local decision favours proceeding, and toolsmithing must be triggered by a rule rather
than by judgment made at the biased moment. **Shrink, do not stack**: an instrument that needs its
own instrument to validate is over-scoped, and narrowing until direct inspection suffices is what
terminates the recursion without abandoning validation. And **book it to instrument debt** — a cycle
that builds an instrument closes zero quality debt and repays instrument debt, and reporting only
the first is the accounting by which organizations stop building instruments without ever deciding
to.
