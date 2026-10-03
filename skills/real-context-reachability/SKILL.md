---
name: real-context-reachability
description: Reachability and missing-data doctrine. Use when a capability must be invoked from the context the product really has (an imported account, a customer record, an external provider row) rather than from inside the engine; when estimating "N steps / one dependency away"; when parsing a provider or API response where a field can be absent; when a missing value could default to zero or to a neutral answer (absent vs measured zero vs unmeasured, abstention vs "continue"); when separating read / mutate / decide / spend authorities; when proving a path cannot mutate; and when recording decisions taken against live state. Core rule - absent is not zero, and a capability the real entry point cannot reach is not delivered.
metadata:
  opportunity_detector: none
  opportunity_detector_reason: coverage class none; no registered card hook and no CO-12 adapter names this skill
---

# Real-Context Reachability

A capability that exists, is correct, is tested, and **cannot be invoked from
the context the product actually has** is not a delivered capability. It is a
library the product does not own yet.

This failure is quiet by construction. Every unit test passes, because every
unit test starts *inside* the capability. Nothing is red, nothing is slow,
nothing looks wrong — and the feature is simply not there.

## How to find it before a customer does

Ask what identity the capability is keyed to, then ask what identity the real
entry point holds. When they differ, you have found it.

The tell is usually a **persisted prerequisite**: the engine reads a row, and
that row only exists for things the system itself created. Anything arriving
from outside — a customer's existing campaign, an imported account, a
third-party record — has no such row and never will.

    engine wants:  product_candidate_id -> a persisted result row
    customer has:  a campaign they have been running for three weeks

That gap is an adapter. It is worth saying so precisely, because the estimate
moves by an order of magnitude: **a missing capability is a product decision
measured in sprints; an unreachable one is a translation measured in days.** The
wrong reading is the expensive one, and it errs toward "bigger", which is the
direction that keeps work unstarted.

## The adapter translates. It must not decide.

Its legitimate jobs: resolve identity, bind context, normalise units, establish
freshness, validate prerequisites, construct the canonical input, invoke, and
preserve provenance. Not: thresholds, states, routing, policy.

**Extract the shared rule; never copy it.** If the mapping you need lives inside
a function you cannot call, pull it out into one both callers use. A copy is
correct on the day you write it and wrong on the day either side changes, and
nothing will tell you which day that was.

Then make the no-duplication claim checkable: have the result record **which
engine produced what**, and assert every name belongs to the canonical package.

## Beware the adapter that fabricates the prerequisite

The tempting shortcut is to satisfy the engine by writing the row it wants. Ask
what that row *means* to the rest of the system before you do. In one case the
persisted row was a **training label**: manufacturing one to make a read work
would have injected a customer's campaign into the system's own learning data.

The prerequisite is not a lock to be picked. If it cannot be honestly
constructed, the engine needs a second entrance, not a forged key.

## "One dependency away" is a claim, and it needs an instrument

The most expensive sentence a session can hand its successor is an unmeasured
estimate of what remains. Measured once: *"the gap is exactly one authorised
account, and no further engineering."* The next session measured it and found
no code that built the capability's input from a real read, a
gate with zero callers, and a provider request that omitted every fact the
decision required.

The reason this survives review is structural: **a join that does not exist has
nothing to hang a test on.** Every unit test passed, because each one started
inside a part. Parts are not a path.

So before writing "N away" in a report, run the sweep that would prove it:

- who CONSTRUCTS the capability's input type, in production, today;
- who CALLS the gated entry point, in production, today;
- does the external request actually ask for the fields the decision requires.

Each is an AST sweep costing minutes. Each can come back the opposite of what
the architecture diagram says. And note the direction of the error — an
underestimate of remaining work is not the safe one here: it converts a
buildable gap into a dependency nobody is chasing, and the work stays unstarted
because everyone believes it is done.

## The absence that arrives from a provider

The `absent ≠ zero` rule above is about your own model defaults. The same defect
re-enters one plane out, at the boundary where a provider's JSON is parsed, and
it is harder to see because the provider is the one omitting the field.

**A key a provider omits when the count is zero is indistinguishable from a key
it omits because nothing was ever configured.** Measured: an ad platform drops
its `actions` array entirely for a window with no actions — which is also
exactly what an account with no conversion tracking returns. Reading that as
zero resurrects the confident-HEALTHY defect at the integration layer.

The three-state model resolves it, and the middle state is reachable:

| provider returned | means |
|---|---|
| the array, with the event | measured, non-zero |
| **the array, without the event** | **measured zero** — the reporting pipe works and reported none |
| **no array at all** | unmeasured — refuse to guess |

And check whether the provider's own names OVERLAP before summing them. Three
action types that each describe the same purchase produce three sales from one.

## Unit scale is part of the quantity, and thresholds are quantities

A provider that reports one figure in major units and another in the currency's
minor unit — `spend: "420.00"` beside `daily_budget: "5000"`, both euros — hands
you a hundredfold error that lands precisely on the number a rule compares
against. Nothing downstream can detect it, because both values are plausible.

Convert explicitly from the currency's declared exponent, and let an unknown
currency produce *unmeasured* rather than an assumed two decimals. See
`monetary-quantity-integrity.md`; the point here is that the figure setting a
KILL threshold deserves the same treatment as the figure being measured.

## Test reachability from OUTSIDE, and make the test unfakeable

Start at the entry point the product calls — the route handler, the CLI command,
the job — not at the capability.

Then make it impossible to satisfy by accident. A provenance string, a registry
entry, and a plausible-looking number can all be produced by code that never
touched the engine. **Replace the engine with one that raises, and require the
exception to surface at the product boundary.** Either the call happened or it
did not.

Patch the name the *caller* bound, not the definition site — a module that did
`from x import f` holds its own reference and will not see a patch of `x.f`.

**Ship the positive control beside it.** A patch that silently failed to bind —
a renamed import, a moved call site — produces no exception, and
`pytest.raises` failing is indistinguishable from the engine simply never being
reached. Assert the *unpatched* path completes, so the raise is attributable to
the patch.

### When two providers produce the same outcome, the outcome is not the evidence

Testing from outside is necessary and it is not sufficient. If the old path and
the new one agree on what the caller *observes*, an end-to-end assertion on that
observation is satisfied by the world it exists to exclude — and the greenest
possible suite says nothing.

Measured: a destructive replacement was moved from a client-side count to an
atomic authority inside the peer. The real end-to-end gate asserted "nothing was
destroyed and the subject is still alive". Both guards produce exactly that.
Disconnecting the new authority entirely left **every pre-existing assertion
passing** — a fully composed, real-subject, real-second-client gate that could
not detect the fix being absent.

So when a change's whole value is *which component decides*, the regression must
name the **decider**, not the result:

- Return a discriminant that is **reachable only through the new authority**, and
  make the two vocabularies disjoint, so the legacy path cannot spell the new
  answer even by accident.
- Prefer a typed field over a log line. Prose is not a contract, and the
  distinction the safety property rests on should not live only in a string.
  Usually the product wants it too — the caller here could not say *why* it was
  entering degraded mode.
- **Mutate the link, not the endpoints.** Mutating the provider re-proves the
  provider; it says nothing about whether anything calls it. Sever the call and
  require the discriminating cases to go red *with the reason flipped to the old
  path*, while the liveness controls stay green.

The corollary for planning: "the primitive is proven" and "the product has the
property" are different claims, and the gap between them is invisible precisely
because every test on both sides is green.

## A hook-reachable capability is not a user-reachable one

The same gap exists inside one application. A capability that a test hook, a debug route or an
internal API can invoke is still unreachable until an ordinary navigation path calls it, and the
proof has to drive that path rather than the hook.

- **The surface orchestrates; the domain owner decides.** Preview through the canonical planner,
  act through the canonical effect, and render their answers. A surface that re-derives
  classification or ordering has become a second authority that will drift.
- **Resolve judging inputs from their live owner, and only once it has finished.** A capability set
  assembled from asynchronous probes is partial until every probe answers, and a partial set passed
  to a classifier turns "still asking" into "proven missing". A probe hook can look settled on its
  first render (`isLoading` false, nothing published): treat "no answer yet" as resolving. When a
  probe could not be asked at all, pass *unknown*, never the partial set.
- **Order the effect against the navigation's own side effects.** If entering an empty target seeds
  content, the effect that requires emptiness runs first.
- **Check the host is mounted where users are.** A menu inside a list that some window layouts yield
  to another panel is one step further away there; say so rather than claiming it is one click.
- **Build product evidence from an isolated tree.** A build from a shared working tree carries other
  writers' uncommitted changes; a worktree at your commit with dependencies linked does not.

Source: 2026-09-17, Orca X snapshots surface — see `presence-is-not-residency.md` and
`knowledge_vault/ukdl/product-reachable-restore-surface.md`.

## A stand-in proves the plumbing, never the external identity

A feature that claims continuity of a session owned by an external provider (resume,
reattach, hand-off) is complete only when a real provider run shows **the same external
identity before and after**. Check it at three points: the product's record, the argv the
real binary received, and the provider's own store. A stand-in that echoes argv verifies
the transport and nothing else.

A real run also measures things the stand-in cannot. Here the stand-in seeded its record on
a plain tab, while the real flow launches an agent tab, so the stand-in never walked the
agent-identity path. The real run showed the action becoming available in 16 s where the
stand-in took 0.4 s.

Make the real-provider gate safe to exist:

- **Opt-in**, and preflight each precondition by name (not installed · not authenticated ·
  no already-trusted folder · no memory headroom). Never manufacture one: a trust or login
  screen aborts the run and receives no key.
- Give the real account **only to the provider process**, and pin the provider to a
  **non-mutating mode** such as plan mode. Check that no product default re-adds a bypass
  flag after yours.
- **Bracket what must not move**: trust set, a credential hash, installed hooks, fixture
  files. The user's own global hooks run inside a real session and may write to the working
  directory. Attribute every write before calling it contamination, and make the
  exclusion list explicit.
- **Read the provider's own store before blaming the display.** A transcript with no user
  message means the input was never submitted, which is a different fix from a stale
  screen.

Source: 2026-09-17, Orca X W3.4. See `orca-agent-exit-leaves-a-working-live-record` in
project memory.

## Absent is not zero, and the two absences are not each other

Wherever a real context supplies facts, some will be missing. A model with
numeric defaults converts "nobody measured this" into "this was zero" at the
moment of construction, and from then on nothing downstream can tell.

The damage is not that a number is wrong. It is that a *rule* silently inverts:
a guard written as `if cost > threshold and count > 0` cannot fire when the
count defaults to zero, so **the absence of evidence is what makes the subject
look healthy**. In one measured case €420 of unexamined ad spend evaluated to
HEALTHY — the state meaning "keep spending" — and the same absence became LOSER
under a different budget, a number carrying no information about whether
anything had been measured.

So: every material fact optional, `None` meaning unmeasured, and no canonical
input constructed until all of them are present.

And keep three states, not two:

| | means | supports |
|---|---|---|
| measured, non-zero | a value | a decision |
| **measured zero** | evidence — often decisive | a decision |
| **unmeasured** | nothing | abstention only |

The middle row is the one that gets lost, and it is frequently the most
informative fact available. Both produce a null derived figure, so a nullable
number cannot distinguish them: carry a **state and a reason** alongside the
value, and write the test that asserts the two states differ *while their values
match* — that is the test a refactor back to one nullable float fails.

## Abstention is an answer. Keep it away from the neutral one.

At least four outcomes, and the failure mode is collapsing them into the
middle one:

- **the confident answers** — act, stop
- **the neutral decision** — continue, taken on COMPLETE evidence, and carrying
  the state that distinguishes one continue from another
- **abstention** — the evidence to choose does not exist
- **blocked / failed** — raise, never return; these are not about the subject

A neutral action that absorbs abstention is how a system with nothing to say
comes to look prudent.

And an abstention whose reasons are not rendered is indistinguishable from a
failure to answer. Name each missing fact individually: "insufficient data"
sends someone to check everything; "conversions were not measured for this
window" sends them to fix one thing.

## Separate the authorities. All of them.

- **may we observe the real world** — read
- **may we change it** — mutate
- **may we decide** — machine or human
- **may we commit resources** — spend, quota, capital

An action must satisfy each independently, and each needs its own refusal
message because each needs a different fix.

**Observe and mutate are the pair most often welded together**, because one
config switch historically turned "talk to the real API" on. Once welded, you
cannot show a customer their own live data without also being able to change it,
and a non-mutating observation mode becomes unrepresentable. Splitting them is
usually additive and usually small.

When you split a safety property, **re-assert its neighbour in the same commit**.
Widening one is exactly when the one beside it widens unnoticed.

## Prove non-mutation by TYPE, not by flag

A badge is not a control, and a check is only as good as the paths that remember
to make it. Searching for the check finds the call sites that have it, which is
the opposite of the question.

The stronger property: **the path holds no object that can mutate.** Where a
read-only client and a mutating client are different classes, a path that
imports only the first cannot mutate however much it forgets.

Prove it structurally:

1. enumerate mutating operations from the AST **by what they do** — verb
   prefixes, HTTP methods, decorators — never by whether they are gated;
2. enumerate the modules defining the classes that carry them;
3. compute the transitive import closure of the path under test;
4. assert the intersection is empty, from **every** entrance — proving one clean
   says nothing about the other.

Then three positive controls, because an empty intersection is also what a
broken sweep produces:

- the parser read a plausible number of modules;
- the enumerator found real operations, anchored on a few **by name** so a
  rename goes red instead of finding nothing;
- and the closure **finds a forbidden module** when run from a path that
  genuinely reaches one. Without that last one, a traversal with a bug reports
  every package clean forever, and nothing else in the file notices.

A runtime trap is worth adding beside the static proof — patch the real
constructors to raise, and **count the firings** so "it never fired" is a
measurement rather than an absence nobody looked for. Two instruments for one
claim; their disagreement would be worth more than their agreement.

## A recommendation is evidence, not a token to act on

Make it structurally incapable of authorising anything: no field a caller could
set, and a future execution path that must independently re-resolve authority,
resources, freshness and current state. Render that boundary in the product —
a verdict beside a "sealed" badge reads like an instruction about to be carried
out, and the user should never have to infer which authority they are looking
at.

Give the verdict a rationale, too. A one-word answer about someone's money is an
assertion; the inputs, the threshold compared against, and the evidence quality
are what make it arguable.

## Decisions taken against live state

- **Seal the decision together with the evidence it was made from.** A seal over
  the verdict alone leaves the inputs editable, and the inputs are exactly what
  an interested party would revise.
- **Supersede; never overwrite.** Yesterday's stop and today's continue are both
  true, of different moments, and the pair is the record. Keeping only the
  latest makes it impossible to ask afterwards whether the system was right and
  changed its mind, or wrong and corrected — the entire question the exercise
  exists to answer. Constrain a revision to the same subject and the same
  tenant, or the chain reads as one history while being two.
- **Order history by observation time, not insertion time.** Two readings
  processed out of order otherwise render as a reversal that never happened.
- **The latest decision is not automatically the current one.** Return the row
  AND whether it may be shown as current; conflating them presents a stale
  recommendation as live. Still return the stale one — hiding it is its own lie.
- **Judge freshness against the source's own cadence**, and clamp a negative age
  to zero: a clock skew reading as fresher than fresh is the one direction this
  must not fail in.

## DON'T

- **Don't widen a shared contract to serve one caller.** If a mode value already
  means something to a scheduled job, three test files and a nightly worker,
  changing it for a new feature changes their behaviour too. Prefer the
  per-call seam that already exists.
- **Don't reuse a table because it is nearly right.** Required columns that
  carry no meaning for the new case, and an enum that admits only labels that
  are wrong for it, are the schema telling you these are different things. Share
  the *mechanism* — sealing, provenance, supersession — not the shape.
- **Don't accept a convenience default for a number that sets a threshold.** An
  estimator that fills in a missing cost is reasonable for something the system
  is about to try and a fabrication for something belonging to a customer: that
  one guess sets the threshold, which is the decision, and nothing in the output
  shows a number was invented.
- **Don't let a ratio be formed from unlike quantities.** A sum of mismatched
  units yields a suspicious magnitude; a quotient yields an entirely ordinary
  number with no unit left to contradict it.
- **Don't pad a pass count with a tautology.** A check asserting `True` with a
  comment explaining why it is true is a green that measures nothing, and it
  will be counted in the total you report.
- **Don't let a new path inherit a repository's "no scope means no filter"
  convenience.** A per-tenant store that derives its scope from the session and
  falls back to UNFILTERED when the session carries none is correct for the
  internal callers it was written for, and is a cross-tenant leak the moment a
  new path hands it a raw session. Assert the scope you expect; do not rely on
  the caller having opened the right unit of work.
- **Don't let a structural proof keep its old entrances.** A closure test that
  names the modules it starts from proves nothing about the module you just
  added — and the module you just added is usually the one that reaches the
  outside world. After adding an entrance, measure that it CHANGED the closure:
  an entrance that fails to resolve yields an empty closure and a trivially
  empty intersection, which reads exactly like a clean bill.
- **Don't let a verifier of environments die in one.** A preflight exists to
  describe a partial environment, which makes it the tool most likely to meet
  one. An uncaught failure in its third check abandons the remaining two while
  still presenting as a verdict. Isolate each check, and let a check that could
  not run say so — that is different evidence from a dependency being absent,
  and only one of the two is about the subject.
- **Don't report a refusal whose cause is a host setting as a property of the
  subject.** A process-global ceiling that lowers every scope produces a refusal
  worded as if the scope were at fault, sending an operator to change the wrong
  thing. Name the ceiling separately wherever the refusal is surfaced.

## Source

Incident evidence moved to `~/.claude/knowledge_vault/rules-evidence/real-context-reachability.md` (2026-09-28) so it is not re-read on every call. The rule text above is unchanged.
