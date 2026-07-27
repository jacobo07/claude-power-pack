# Cognitive OS — CO-14 — Residency Jurisdiction and the Dependent Register

> Three systems in this estate describe where a cognitive asset lives and what degrades
> first under pressure: the Cognitive OS memory family (CO-00/03/04/05/06), the DAIF-08
> Context Runtime, and the Parallel Mesh pressure and prefetch pair (PM-04/PM-05). The
> founding suspicion was that they were three uncoordinated authorities with no rule for
> which one governs on conflict.
>
> **That suspicion is rejected by the evidence, and its refutation is this dataset's most
> useful content.** Jurisdiction is already declared, explicitly, by both dependents. What
> is missing is the other half of the handshake.
>
> **Non-duplication contract (binding).** CO-14 defines no tier, no eviction rule, no
> budget and no pressure mode. CO-04 owns residency, CO-00 owns the ceiling, CO-05 owns
> assets, CO-06 owns eviction, CO-10 owns enforcement-strength classification. CO-14 owns
> exactly one thing none of them does: the **owner-side register of who depends on them**,
> and the change rule that register makes possible.

---

## Part I — The hierarchy is already declared

### I.1 What the dependents say

Both systems that consume residency name their owner in their own text, without hedging.

**DAIF-08 Context Runtime**, Part I: *"It does not own the memory tiers; CO-04 owns
residency, and DAIF-08's ascent and descent are requests against it, never a parallel
tiering. It does not own the budget; CO-00 owns it."* Elsewhere in the same Part it states
that its budget *"composes CO-00 rather than declaring a second ceiling"*, and that the
estate already owns a context-pack builder in which *"CO-04 tiers what is resident, CO-00
caps the spend."*

**Parallel Mesh PM-05**, integration contract: CO-04 and CO-05 are listed as **parents**.
Prefetched artifacts are *"speculative occupants of CO-04's Warm tier and provisional CO-05
assets; PM-05 adds only the when and the what-to-guess."*

There is no ambiguity to resolve. Two dependents, two unprompted declarations, one owner.
The estate's Duplicate-to-Advantage doctrine worked exactly as intended in both cases.

### I.2 What the owner says

Nothing. A search across every Cognitive OS dataset returns **zero references to DAIF-08
and zero to PM-04 or PM-05**. CO-04's own integration contract enumerates CO-00, CO-03,
CO-05, CO-06, CO-07, the reset commands and the vault — and stops there.

So the dependency graph is real, correct, and **recorded on one side only**.

### I.3 Why a one-directional contract is not a contract

A declared dependency the owner does not know about buys the dependent nothing that
survives contact with change. Three concrete consequences, none hypothetical:

- **Change impact is invisible at the point of change.** An author revising CO-04's tier
  semantics, its promotion gate, or the trust status of the External tier has no way to
  discover from CO-04 that two other systems have built on those exact guarantees. The
  information exists; it is filed under the wrong name, in the wrong direction.
- **Deprecation cannot be performed safely.** An owner may only retire a guarantee it can
  enumerate the users of. CO-04 cannot enumerate its users, so every one of its guarantees
  is effectively permanent by ignorance rather than by decision.
- **The dependent's compliance is unverifiable.** PM-05 promises its speculative artifacts
  are untrusted until anchored — a promise about CO-04's Warm tier. Nothing on the CO-04
  side records that this promise was made, so nothing can check that it is still kept.

**The rule this dataset exists to state: a dependency declared only by the dependent is a
courtesy, not a contract. It becomes a contract when the owner records it.**

---

## Part II — The Dependent Register

### II.1 Shape

The register is owner-side and minimal. For each dependency it records the dependent, the
specific guarantee relied upon, the direction of the relationship, and what breaks if the
guarantee changes. It is not a design document and carries no mechanism; its whole purpose
is that an author editing an owner can see, in that owner's own text, who is standing on
the thing being edited.

### II.2 Contents as measured 2026-07-27

| Owner | Dependent | Guarantee relied upon | Breaks if changed |
|---|---|---|---|
| CO-04 | DAIF-08 Context Runtime | tier membership and residency decisions; ascent and descent are requests, not a parallel tiering | DAIF-08's progressive-disclosure ladder loses its substrate; its page-fault event has no tier to fault against |
| CO-00 | DAIF-08 Context Runtime | the single ceiling; DAIF-08 composes it rather than declaring a second | a second ceiling appears, and over-spend attribution becomes ambiguous between two budgets |
| CO-04 | PM-05 Speculative Prefetch | the Warm tier accepts a speculative, freshness-anchored occupant that is untrusted until validated at point of use | prefetch either promotes unverified content or loses its placement target; the harmless-failure property is what depends on this |
| CO-05 | PM-05 Speculative Prefetch | a validated prefetch may promote to an asset; historical access records inform prediction | prediction loses its strongest non-declared signal |
| CO-06 | PM-05 Speculative Prefetch | unused speculative artifacts are evicted on a short timer as the lowest-priority occupant | speculative residue accumulates and prefetch stops being self-limiting |
| CO-03 | PM-05 Speculative Prefetch | prefetch is pinned to the deterministic and cheap rungs | the cheap-only constraint loses its enforcement point, and a wrong guess stops being cheap |
| CO-04, CO-06 | CO-13 adapter (pending) | the field mapping from the live telemetry stream | the adapter is written against a vocabulary that has moved |

Seven relationships. All seven were discoverable only by reading the dependents.

### II.3 The change rule

An edit to a registered guarantee requires the register to be read first, and every named
dependent to be either confirmed unaffected or updated in the same change. This is a
process rule, not a gate: there is no mechanism here that can enforce it, and CO-10's
honesty ladder places it at the weakest rung — doctrine, enforced by reading. Claiming
otherwise would be exactly the enforcement theatre CO-10 exists to prevent.

The rule is still worth stating at that rung, because its failure mode is silent and its
cost is a subsequent multi-day investigation into why a dependent stopped behaving.

---

## Part III — Failure modes, rollback, integration, anti-patterns

### III.1 Failure modes of the register itself

- **Drift.** The register is hand-written and therefore measures what someone remembered —
  the defect pattern this estate has recorded seven times. It is defensible here only
  because the dependency statements it mirrors are themselves textual: the register can be
  regenerated by searching dependents for owner names, and it should be, not maintained by
  hand. That producer is not built by this dataset and its absence is named, not hidden.
- **False completeness.** A register with seven rows reads as though seven is all there
  are. It is all that were **found**, by searching two known dependents. Any system that
  depends on residency without naming CO-04 is invisible to this method and is not counted.
- **Ceremony.** A register consulted by nobody is a file. Its only real enforcement is that
  it sits inside the owner's own dataset, where an author editing that owner will see it.
- **Staleness on the dependent side.** A dependent may change its mind silently; the
  register records the claim as of a date and does not track it.

### III.2 Rollback protocol

CO-14 introduces no runtime behaviour, so there is nothing to roll back. Deleting it
returns the estate to a correctly-declared, one-directionally-recorded dependency graph —
the state of 2026-07-26. The fail-safe direction is the prior one.

### III.3 Integration contract

- **CO-04, CO-00, CO-05, CO-06, CO-03** — the owners. Each receives the rows naming it;
  none changes behaviour.
- **CO-10** — classifies this rule honestly at the doctrine rung. CO-14 does not claim a
  gate it does not have.
- **CO-13** — supplies the last row: the pending adapter is itself a registered dependent
  before it is written, which is the first use of the register in its intended direction.
- **DAIF-08, PM-04, PM-05** — the dependents. Their own declarations are the source; this
  dataset copies them rather than restating or reinterpreting them.
- **`modules/liveness/reachability.py`** — the nearest existing instrument in spirit: it
  replaced a hand-declared registry with a discovered one. The regeneration producer named
  in III.1 should follow that precedent rather than this dataset's hand-built table.

### III.4 Anti-patterns (forbidden)

- **Unifying authorities that are already subordinated.** The founding proposal for this
  dataset was a unification. There was nothing to unify; two dependents had already named
  their owner. Building the unification would have created the second authority its own
  premise objected to.
- **Reading a missing back-reference as a missing hierarchy.** Absence of the owner's
  acknowledgement is not absence of jurisdiction, and the two demand different repairs.
- **Maintaining the register by hand once a producer is possible.** Stated in III.1 and
  repeated here because the estate's recorded failure rate on this exact substitution is
  seven for seven.
- **Escalating a doctrine-rung rule to a claimed gate.** No mechanism enforces the change
  rule. Saying otherwise would inflate the guarantee, which CO-10 exists to catch.

---

### CO-14 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Every register row quotes a dependency the dependent itself declared, in its own text | As of 2026-07-27 | That the dependent still holds that position later |
| The owner-side record exists where an author editing the owner will encounter it | Always | That the author reads it — this is a doctrine rung, not a gate |
| The founding premise is stated and refuted, with the evidence that refutes it | Always | That no third residency authority exists — only that two were found and both are subordinated |
| Seven relationships enumerated, none previously recorded on the owner side | Measured | Completeness — this is what the method found, not what exists |

**Guarantee level (honest):** rung-0, doctrine. CO-14 enforces nothing and detects nothing.
Its entire value is that a dependency graph which existed in one direction now exists in
both, and that a proposed unification was replaced by a back-reference roughly two orders
of magnitude cheaper. The register is hand-built, which is the weakness it names about
itself; regenerating it from the dependents' own text is the next honest step and is not
taken here.
