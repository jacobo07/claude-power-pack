---
title: "CLAE Part XV — Incident-to-Probe Conversion"
family: clae
part: XV
depends_on: [XIII, XIV]
feeds: [XIX, XXI, XXII, XXIV]
status: SEALED
date: 2026-07-26
---

# Part XV — Incident-to-Probe Conversion

## 1. Purpose

Part XIV built instruments in response to blockers. This Part builds them from failures, and the
economics are entirely different.

A blocker requires an instrument to be designed: someone must decide what to observe and construct
a case that exercises it. **An incident arrives with its case already attached.** The failing input
exists, the environment that produced it exists, and the true answer — that this fails — is
established independently of any instrument. That is the definition of the known-answer case Part
XIII §8 requires for calibration, delivered free.

It also expires quickly, which is why this Part exists as doctrine rather than as advice.

## 2. The perishability of an incident

At the moment of an incident, five things are available together and briefly:

- The **failing input** — the exact arguments or state that produced it.
- The **environment** — versions, configuration, ordering, concurrent activity.
- The **observed state** — what the system looked like when it went wrong.
- The **symptom** — how the failure presented, before it was interpreted.
- The **motivation** — someone is looking at this, now, and wants to understand it.

Within days all five are gone. The fix is in, so the input no longer fails. The environment has
moved. The state was not captured. The symptom has been replaced in memory by the explanation. And
the motivation is spent, because the problem is solved.

> **An incident is the cheapest known-answer case a system will ever get, and it has a short
> expiry.**

The conversion must therefore happen **inside the incident**, alongside the diagnosis, not
afterwards as a follow-up item. A follow-up item to write a probe is a promise to reconstruct
something that no longer exists.

## 3. Probe, fix and test are three different artifacts

One incident yields three, and they are routinely collapsed into one or two.

| Artifact | Asserts | Rewritten when |
|---|---|---|
| **Fix** | The system no longer behaves this way | The design changes |
| **Test** | The system behaves as intended | The intent changes |
| **Probe** | This specific historical failure does not reproduce | **Never** |

The fix without a probe means recurrence is undetectable until it reaches production again. The
test without a probe asserts what was *intended* — and the incident was never intended, so no test
written from intent will express it.

The distinction that matters operationally is the last column. **A test is rewritten when intent
changes; a probe is not, because it is a historical record rather than a specification.** When a
feature is redesigned, its tests are legitimately replaced. Its probes stay, because the question
they ask — does this old failure come back — remains meaningful across redesigns and is *most*
meaningful during them. Probes deleted alongside the tests of a redesigned feature are the most
common way a probe suite silently loses its accumulated value.

## 4. The conversion threshold

Not every incident deserves a probe. Converting all of them reproduces the accumulation problem
Part X §6 named, and a probe suite that only grows becomes ceremony.

Four criteria, any one sufficient:

1. **It was expensive** — the cost of the incident itself justifies the cost of detecting a
   recurrence early.
2. **It was surprising** — it falsified a model of how the system behaves. This is Part VIII §5's
   null outcome in incident form, and surprising failures are the highest-value conversions because
   the model that failed is still in use elsewhere.
3. **It is structurally likely to recur** — the conditions that produced it remain possible.
4. **It was hard to diagnose** — the probe pays for the diagnosis the next time, per §6.

Explicitly **not** a criterion: severity alone. A catastrophic failure whose cause has been
structurally eliminated needs no probe; there is nothing left to detect. Severity drives urgency of
the fix, not the value of the probe, and conflating them fills the suite with probes for
impossibilities.

## 5. The probe contract

A probe carries:

- **Incident identity and date** — what created it. Part III §5 requires this; a probe without a
  lineage is an instrument, not a probe.
- **Reproduction** — the exact input and the environmental preconditions.
- **The distinguishing observable** — what separates failure from success, specifically enough that
  a near-miss is not read as a pass.
- **Three-valued output**, per Part XIII §7. This matters more for probes than for any other
  instrument: a probe whose preconditions are absent must report *could not run*, never *passed*. A
  two-valued probe silently becomes decorative the moment its environment drifts, and the suite
  reports green while covering nothing.
- **Expected result and the meaning of a change** — what it means if this starts failing, and
  separately what it means if it starts passing for a reason nobody arranged.
- **Retirement condition** — what would make this probe unnecessary, per §7.

## 6. The value is diagnosis, not prevention

The instinctive justification for probes is preventing recurrence. That is the fix's job, and if the
fix is sound the probe will never fire.

The actual value is different and larger:

> **A probe converts a future undiagnosable incident into a diagnosed one.**

If the failure class does recur — through a regression, a refactor, an environmental change, a
different path reaching the same defect — the probe localizes it immediately. Without it, the
recurrence presents as a fresh symptom and the entire diagnosis is performed again, from nothing,
by someone who may not know it happened before.

This is Part XII §2's reactive-instrumentation cost, paid once per failure class rather than once
per occurrence. It reframes the economics: a probe that never fires has not been wasted, in the same
way that a smoke detector that never sounds has not been wasted. The expected value is the diagnosis
cost avoided, multiplied by the probability of recurrence — and criterion four in §4 exists because
hard-to-diagnose incidents have the largest term.

## 7. The probe suite is a floor set

Probes accumulate exactly as floors do, and they need the same three controls Part X §6 established,
for the same reason: an accumulating check-set that is never pruned becomes a self-authored
compliance ritual, which is the trap this family exists to attack.

**Retirement conditions at creation.** What would make this probe unnecessary — normally that the
failure class has become structurally impossible rather than merely fixed. When that happens, retire
the probe and record the elimination, because the record is what prevents someone reintroducing the
possibility later without knowing it was closed deliberately.

**Execution verification.** A probe suite reporting all-green proves nothing unless the probes ran.
Three-valued output makes this automatic rather than requiring an audit — an unrun probe says so.

**Economics.** A probe whose execution cost exceeds the diagnosis cost it saves, discounted by
recurrence probability, is a net loss regardless of the incident that produced it.

## 8. When the incident cannot be reproduced

Sometimes the conditions cannot be reconstructed: a race that depended on timing, an environmental
state that is gone, a failure observed once and never since.

The honest path is to record what *is* known — the symptom, the partial state, the environment as
observed — as an **observation attached to the incident**, not as a probe. It is evidence for a
future diagnosis and it is not a check.

The rule that matters here is sharper than it appears:

> **A probe that does not reliably reproduce is worse than no probe.**

An intermittently-failing probe gets muted. Muting one probe teaches that probes are mutable, and
the suite's authority erodes across every probe in it, including the sound ones. The damage is to
the institution rather than to the individual check.

A probe failing intermittently is in one of exactly two states. It is measuring a quantity whose
variation envelope was never characterized — Part VI §7 and Part XII §5 — in which case the fix is
to characterize the envelope and set the distinguishing observable outside it. Or it is not a probe
at all, because it does not reproduce a specific failure. **Fix it or delete it. Never mute it.**

## 9. The probe is an agent's memory of failure

For autonomous work this Part is not an efficiency measure. It is the memory substrate.

A human carries an informal recollection — *that broke last time, check it first* — which survives
between sessions and shapes attention without any artifact existing. An agent has no such channel.
Its context does not persist, and the next session begins with no knowledge that the failure ever
occurred.

> **For an agent, the probe is the only durable form of "this broke before".**

Everything else — the diagnosis, the reasoning, the near-miss that was noticed and not written down
— is gone at session end. This makes conversion more urgent for agentic work than for human work,
and it makes §2's expiry window effectively one session rather than several days.

It also explains why agentic systems repeat failures that a human team would remember: not because
the agent is less careful, but because the substrate that carries the memory does not exist unless
someone builds it deliberately, one incident at a time.

## 10. Boundary

Do not convert incidents in genuinely throwaway work, incidents whose failure class is now
structurally impossible, or one-off environmental events with no recurrence path — a machine that
was out of disk once is not a probe candidate.

Do not convert an incident into a probe when what it actually needs is a **floor**. A recurring
class of incident across many artifacts is Part X §7's promotion signal: the right response is a
domain minimum, not a probe per occurrence. Probes address specific historical failures; floors
address classes. Converting a class into fifty probes is the accumulation failure arriving by the
most sympathetic route available.

## 11. Evidence — incident conversion in this stack

This stack has an unusually complete incident-conversion pipeline, and examining where it terminates
is the finding.

| Surface | What an incident becomes | Re-runnable? |
|---|---|---|
| Sealed hard rules, each carrying an origin incident | A constraint on the agent | **No** — a rule, read at decision time |
| Recurring-error log | A recognized recurrence with a count | Partially — it detects repeats, does not reproduce them |
| Bug-to-rule protocol | A new rule in the archive | **No** |
| Known false positives register | A recognition that stops re-investigation | **No** — and correctly so; these are non-failures |
| Secret firewall | A rule *and* an enforcing hook | **Yes** — the exception that proves the pattern is achievable |
| This session's own record of the third-write block | A documented response applied when it recurred | **No** — it worked, and it worked because a human-readable register was consulted |

**The finding: this stack converts incidents into rules, and almost never into probes.** The
pipeline is real, disciplined and well-populated — nearly every hard rule cites the empirical
incident that produced it, which is more than most systems manage. But a rule and a probe do
different work. A rule constrains the agent at decision time and depends on the agent reading and
applying it. A probe detects the failure at check time and depends on nothing.

The consequence is that this stack's accumulated failure knowledge is **advisory rather than
detective**. It works when the agent consults it — as happened this session with the third-write
block, correctly and quickly — and it does nothing when the agent does not, or when the failure
arrives by a path the rule's trigger does not describe.

The secret firewall is the counterexample and the model: one incident class that produced both a
rule and an enforcing check. That combination is what §3 argues every significant incident should
yield. — Conversion surfaces OBSERVED from the governance archive and this session's own record;
the rule-versus-probe assessment is INFERRED against §3.

## 12. Failure modes

| Failure | Mechanism |
|---|---|
| **Deferred conversion** | The probe becomes a follow-up item; by then the input, state and environment are gone |
| **Fix without probe** | Recurrence is undetectable until it reaches production again |
| **Test substituted for probe** | Intent asserted where a historical failure needed reproducing; the incident was never intended |
| **Probe deleted with the tests** | A redesign removes probes alongside legitimately-replaced tests, discarding accumulated history |
| **Two-valued probe** | Drifted preconditions report as passes; the suite reports green while covering nothing |
| **Muted flaky probe** | One mute teaches that probes are mutable; the suite's authority erodes across all of them |
| **Severity-driven conversion** | Probes accumulated for failure classes that can no longer occur |
| **Class converted per-occurrence** | A recurring class turned into many probes where one floor was needed |
| **Rules without checks** | Failure knowledge that is advisory rather than detective, effective only when consulted |

## 13. Detection signatures

1. **The reconstructed probe.** A probe whose reproduction was written days after the incident. It
   encodes what was remembered, not what happened.
2. **The green suite in a drifted environment.** Probes passing under conditions where their
   preconditions cannot hold. Two-valued output.
3. **The muted entry.** Any probe disabled rather than fixed or deleted. Its presence is a standing
   statement that the suite is optional.
4. **The redesign gap.** A feature with a rich incident history and no probes older than its last
   rewrite.
5. **The advisory archive.** A large body of recorded failure knowledge with no corresponding
   executable checks — the §11 finding, in general form.

## 14. Trap seeds — for Part XXII

- **T-CLAE-DEFERRED-CONVERSION** — the probe deferred past the incident, to be written from memory
  after the input, state and environment are gone.
- **T-CLAE-TEST-FOR-PROBE** — a test written from intent substituted for a probe reproducing a
  failure that was never intended.
- **T-CLAE-PROBE-SWEPT-BY-REDESIGN** — probes deleted alongside the legitimately-replaced tests of a
  rewritten feature, discarding the history most valuable during a rewrite.
- **T-CLAE-MUTED-PROBE** — an intermittent probe muted rather than fixed or deleted, eroding the
  authority of every probe beside it.
- **T-CLAE-ADVISORY-ONLY-KNOWLEDGE** — failure knowledge captured entirely as rules read at decision
  time, with no executable check, effective only when consulted.

## 15. Rule seeds — for Part XXIII

- **PR-CLAE-CONVERT-INSIDE-THE-INCIDENT** — the probe is written during the diagnosis, not after the
  fix. Conversion deferred past the incident is recorded as an unconverted incident, not as pending
  work.
- **PR-CLAE-THREE-ARTIFACTS** — a significant incident yields a fix, a test where intent needs
  asserting, and a probe. The probe is not satisfied by either of the others.
- **PR-CLAE-PROBES-SURVIVE-REDESIGN** — probes are not rewritten when intent changes and are not
  removed with the tests of a redesigned feature. They are historical records.
- **PR-CLAE-PROBE-THREE-VALUED** — a probe with absent preconditions reports could-not-run, never
  passed.
- **PR-CLAE-FIX-OR-DELETE-NEVER-MUTE** — an intermittent probe is either measuring an
  uncharacterized envelope, in which case characterize it, or is not a probe, in which case delete
  it. Muting is not available.
- **PR-CLAE-CLASS-BECOMES-FLOOR** — a recurring incident class across many artifacts is promoted to
  a floor rather than converted into a probe per occurrence.

## 16. Eval seeds — for Part XXIV

- **Conversion-latency probe.** For each significant incident, measure the interval between the
  incident and its probe. Intervals beyond the incident's own working session indicate reconstruction
  from memory.
- **Rule-without-check probe.** For each recorded rule with an origin incident, determine whether an
  executable check exists. The ratio quantifies §11's finding and is directly actionable.
- **Precondition-drift probe.** Run the probe suite under deliberately absent preconditions. Any
  probe reporting pass is two-valued and its green history is uninterpretable.
- **Mute-census probe.** Count disabled probes. Any non-zero count is a standing erosion of the
  suite's authority and each is a fix-or-delete decision that was never made.
- **Survival probe.** For features rewritten in the last period, check whether their probes survived
  the rewrite.

## 17. Production Reality Gate seed — for Part XXV

**Incident Conversion Gate.** A significant incident may be recorded as closed only when its
diagnosis produced a fix and either a probe or an explicit recorded decision not to convert, with
the reason drawn from §4 or §10. The probe must carry its incident lineage, reproduction,
distinguishing observable, three-valued output and retirement condition. An incident closed with
neither a probe nor a recorded decision is registered as an unconverted incident — a visible state,
so that the stock of them is countable rather than invisible.

## 18. Pseudoflow — converting an incident

While the incident is open and before the fix lands, capture the reproduction: the exact input, the
environmental preconditions, and the state as observed. This is the step that cannot be recovered
later, and it is the step that competes with the urgency of fixing.

Decide whether this incident meets the conversion threshold — expensive, surprising, structurally
recurrent, or hard to diagnose. Severity alone is not sufficient. If it does not meet the threshold,
record the decision and the reason, so the incident is closed deliberately rather than by omission.

Determine whether the right artifact is a probe or a floor. A specific historical failure yields a
probe. A class recurring across many artifacts yields a floor, and converting it per-occurrence is
the accumulation failure by its most sympathetic route.

Write the probe: incident lineage, reproduction, and a distinguishing observable specific enough
that a near-miss is not read as a pass. Give it three-valued output, so that absent preconditions
report could-not-run rather than passed. State its retirement condition — normally that the failure
class has become structurally impossible.

Run it before the fix, and confirm it fails. A probe that does not fail on the unfixed system is not
reproducing the incident, and this is the only moment that check is available for free.

Apply the fix. Run the probe again and confirm it passes. This is the loop-validation of Part VIII
§9 at the scale of a single failure.

If the probe cannot be made to reproduce reliably, do not add it. Record the symptom and partial
state as an observation attached to the incident, and leave the suite unpolluted.

Thereafter, never mute it. An intermittent probe is characterized or deleted.

## 19. Integration

Part XIII receives probes as its narrowest instrument kind and applies its full declaration contract
to them. Part XIV's register-or-delete rule applies unchanged; a probe is an instrument built in
response to a blocker of a particular kind. Part XIX's evidence-gated autonomy consumes probe results
as evidence, and §8's mute prohibition is what keeps that evidence meaningful. Part X §7's promotion
rule is the boundary in §10: classes become floors, instances become probes. Part XXII's trap
registry is the natural companion of the probe suite, since a trap describes what to watch for and a
probe detects it.

Outside the family, the secret firewall is the model — one incident class yielding both a rule and an
enforcing check — and the hard-rule archive is identified as a well-populated conversion pipeline
that terminates one step short of a detective mechanism.

## 20. Open questions

1. Can conversion be made cheap enough to happen inside every significant incident? §2's argument is
   that the window is the incident itself, and the incident is exactly when attention is scarcest.
   If conversion is not near-free, the rule will lose to urgency every time. — UNKNOWN, and the
   determining factor for whether this Part is practiced or merely stated.
2. What is the correct action when an old probe starts passing for a reason nobody arranged? The
   contract requires interpreting this, and it may mean the failure class was eliminated
   incidentally, or that the probe stopped reaching the condition. These require opposite responses
   and may be indistinguishable from the probe's output. — UNKNOWN.
3. Does the rule-plus-probe pairing scale to a large rule archive? §11 implies every origin-bearing
   rule wants a check, and for a large archive that is a substantial construction programme whose
   economics have not been assessed. — HYPOTHESIS: only the subset meeting §4's threshold warrants
   it, which is far smaller than the archive.

## 21. Institutional writeback

Five trap seeds, six process-rule seeds, five eval seeds and one production gate.

Three portable results. **An incident is the cheapest known-answer case a system will ever get, and
it expires within days** — which makes conversion an in-incident obligation rather than a follow-up
item, because a follow-up item is a promise to reconstruct something that no longer exists. **Fix or
delete, never mute** — muting one intermittent probe erodes the authority of every probe beside it,
so the damage is institutional rather than local. And **for an agent, the probe is the only durable
form of "this broke before"** — the informal recollection that shapes a human team's attention has
no equivalent across sessions, which is why agentic systems repeat failures a human team would
remember, and why the substrate must be built one incident at a time.

The finding worth carrying beyond this stack: an organization can have a disciplined, well-populated
incident-to-rule pipeline and still hold its failure knowledge in a purely advisory form. Rules work
when consulted. Probes work regardless.
