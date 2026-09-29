---
name: destructive-state-authorization
description: Doctrine for any irreversible operation - deleting or overwriting files, discarding uncommitted work, git reset/clean/checkout/restore/force-push, dropping or truncating data, revoking, cancelling, bulk deletes, cleanup of worktrees/caches/sessions. Use BEFORE running or writing code that destroys state, and when designing a confirm dialog, a batch delete, a retry/idempotency path, or a peer protocol that can destroy. Answers - what exact state was authorized, is it still there (content identity, not mtime/size/ids), what can change between the check and the effect, per-item re-authorization in batches, truthful results, and mixed-version peers failing closed. A PreToolUse hook (destructive_doctrine_card.js) also shows its core once per session on the first destructive shell command.
---

# Destructive State Authorization

A user does not authorize "destroy whatever occupies this path when the request arrives". They
authorize destroying **the state they reviewed**. Every irreversible operation — deleting
uncommitted work, overwriting a draft, dropping a row, revoking a key, cancelling an order — owes an
answer to one question:

> **What exact state did the user authorize destroying, and is it still there?**

This is not stale-write protection in general. Optimistic concurrency protects a *value* from being
clobbered by a later writer, and the writer can retry. Here there is nothing to retry into: the bytes
are gone, and whether the guard was right is unfalsifiable afterwards. So the bar is higher than
"detect a conflict" — it is "never destroy something nobody looked at".

## Choose the identity from the EFFECT, never from what is easy to fetch

The tempting precondition is whatever version marker the system already hands you: a revision
number, an ETag, an object id, a generation counter, a modified timestamp, a diff summary. Each is
free, and each describes *some* state — rarely the one the operation destroys.

**The test is a falsification, and it is cheap:** construct one case where the destructive target
changes while the candidate identity stays constant. If you can, the identity is semantically
insufficient, whatever its pedigree.

Two worked failures, both from one investigation:

- A version-control status report offers the committed object id and the staged object id for free.
  The operation restores the working file from the committed state and leaves the staged entry alone
  — so what it destroys is exactly the bytes *neither* id describes. A file edited twice against an
  unchanged index passes as unchanged.
- A client-side row identity built from path, change-kind and added/removed line counts. Replace one
  line with a different line of the same length and all three are identical.

What survived was a hash of the bytes actually on disk, which also settles filter and encoding
questions for free: whatever transformation is configured, that is the form that disappears.

**Absence of an identity is never "unchanged".** A missing value means the caller could not say, and
the only safe reading is refusal. Make that explicit, because the convenient default is the wrong
one and nothing will remind you.

## State authorization is not operation identity

Two different contracts that look alike:

- **operation identity** answers *is this the same request?* — it collapses a retry.
- **state authorization** answers *is the state this request was authorized to mutate still the
  same?*

Neither substitutes for the other. A replayed request with a matching idempotency key and a moved
target must still be refused: the first attempt may have succeeded, the response may have been lost,
and the user may have done new work in between. Deduplication would silently destroy it.

## Locality does not mean freshness

The argument that a same-process client cannot act on stale state is about **transport**, and the
question is about **time**. Before exempting any local path, enumerate the windows between what the
user saw and what the code destroys. In one desktop application there were three, and the middle one
was a modal dialog waiting on a human — unbounded by construction.

Then ask who else can write. The producer of the newer state usually needs none of the application's
own machinery: an external editor, a formatter on save, a build step, an agent, a second window on
the same data. Measure the race; do not reason about the wire.

## Authorize at the point of observation, not at the point of execution

The identity must be captured when the user *saw* the state, and carried forward untouched. Reading
it again just before executing feels safer and is the defect: it authorizes destroying whatever
arrived in the meantime, which is the exact race, wearing the costume of a precondition.

This fails most often at a **confirmation boundary**. The surface holds the whole record when the
user clicks, then passes only an identifier onward, and the record — the only evidence of what was
observed — is dropped one frame before the destruction. Check what the confirm handler forwards.

Corollary: the authoritative side validates. A check on the client is worthless, because the stale
client is precisely the party that cannot know.

## The check is authoritative for the effect only if nothing can move in between

Everything above is about the past: the state the user saw has changed, so refuse. The irreversible
step needs a different property, and passing the first says nothing about the second:

> **A precondition covers the effect only if the state cannot go from authorized to unauthorized
> between the final check and the destruction.**

A stale-state test proves the past changed. A concurrency test proves the world can change while you
act. The second is the one that gets skipped, because the first one's green feels like it covers it.

So reconstruct the interval by following real async and process control, not by reading the function
top to bottom: the final read, every await after it, every subprocess spawn, every filesystem call,
then the destruction. Anything in there that is **not a write** belongs above the check — probes,
containment, cache invalidation — because none of it is the effect and all of it is time.

**Then measure what is left and put a number on it.** The irreducible part is usually one mechanism,
and its size decides what is worth fixing. Measured in one case: the destructive subprocess took a
median 95 ms against a 1.9 ms content check — a factor of 49. That ratio is the entire argument for
leaving the sub-millisecond calls above the check alone; shaving them while a 95 ms spawn remains is
noise dressed as safety, and it would have meant restructuring shared symlink-safety code to trade
one race for a smaller one.

Expect a genuine ordering tension and do not pretend it away. When two checks each want to be last —
path containment and state authorization, say — you cannot have both. Decide which failure is worse,
say so where the code is, and keep the other as close as you can.

**A batch cannot share one authorization moment.** Authorize every item in one pass and then destroy
in groups, and the last item's authorization is an entire destruction old when its turn arrives. That
is not a corner case; it is what a multi-select does every time. Re-authorize immediately before each
destructive call, at the granularity the destruction actually has — per chunk, per group, per
subprocess.

Note where this hides: the batch may **already** re-validate something else in exactly the right
place. One measured example re-checked *path safety* immediately before the deletion, for precisely
this reason, while state authorization still held the answer computed before the whole preceding phase
ran. The right place had been identified; only one of the two checks was in it. Wherever you find a
"recheck before the write" comment, read which check it guards.

The aggregate lies in the same breath: a member kept back late is exactly the one a result built from
the *requested* set reports as destroyed. Build it from what the destructions actually covered.

## What is achievable here, and what is not

Against a writer that honours nothing — an external editor, a formatter, another process — a
check-then-destroy on an ordinary filesystem cannot be made atomic. Say so plainly rather than
implying a guarantee:

- **Narrow** the window to the one mechanism that has to be in it.
- **Bound** it with a measurement.
- **Exclude** the writers you can. An editor's own delayed save is excludable by quiescing it before
  the request is even sent — worth doing precisely because it is the writer most likely to fire.
- **Do not** replace the destructive primitive to win milliseconds when the replacement loses
  semantics the primitive provided — content filters, line-ending conversion, hooks. A faster
  destruction that writes the wrong bytes is not an improvement.

Reflexive locking is not the answer either: a cooperative application lock is ignored by the external
writer that is the actual threat, and blocks the legitimate editors that are not.

**But first ask whether the competing writer is a peer you control.** Everything above is about a
writer that honours nothing. When the thing still admitting work is your own daemon, server or
service, the answer inverts: it can prove its own state and stop admitting **in the same turn**, and
you cannot do that from outside it. A residual your own software could close is **debt, not an
external limit** — and "external" is the word that makes everyone stop looking at it.

Two consequences, both measured:

- **Closing the window you measured exposes the next one.** Moving a revalidation to just before the
  effect is a real improvement, and it moves the boundary rather than removing it. After every such
  fix, name the NEW last-check-to-effect interval and challenge it on its own evidence. A shrunken
  race is still a race until harmful interleaving is impossible; probability is not safety, and the
  old race's test going green says nothing about the new one.
- **Look for the atomic primitive before designing one — and check its PRECONDITIONS, not its name.**
  The estate that needed this already had a "retire if idle" request that proved emptiness and fenced
  admissions in one event-loop turn. It still could not be reused: it also required the caller to be
  the peer's *only* client, which was right for the quit path it was built for and wrong for
  replacement. The shape was right and the contract was not. Reusing it on the strength of its name
  would have refused every legitimate replacement; concluding "no primitive exists" would have
  rebuilt one from scratch.

When you do extend the protocol, prefer a **new method name over a new optional field**: an old peer
rejects an unknown method and fails closed, while it silently ignores an unknown field and destroys
anyway. And keep "could not ask" distinct from "was refused" — only one of them is evidence about the
state, and collapsing them turns an unanswerable peer into a busy one, or a busy one into a licence.

## A change-detection comparator must see the field the guard depends on

If a cache, store or diff decides whether an update is "a change", and it does not compare the
identity, the identity freezes at whatever it held when some *other* field last moved. For a
rendered value that is a cosmetic lag. For an authorization it is a wall in one direction: the host
refuses against content the user replaced long ago, and no later refresh can clear it, because the
only thing that changed is the field the comparator does not look at.

Same shape for any identity carried through a transformation: **re-key the map after
canonicalization**. Keyed by the caller's spelling, every lookup misses and the guard refuses
everything for a reason nobody can see.

## Put the guard at the boundary, not beside the hole

Guard the narrowest choke point every caller passes through, not the caller you happen to be editing.
Otherwise the ordinary path is fenced and the degraded path is not — and the degraded paths are
reachable. Both real ones in the source investigation were mundane: a listing truncated past a size
cap emitted no identities at all, and its "too many items" state was a *banner* rather than a
replacement for the list, so every row still rendered a working destructive button.

## Refusal is not failure, and each refusal needs its own words

At least three outcomes, and collapsing any two tells the user something false about their own work:

| Outcome | What is true | What helps |
|---|---|---|
| the state moved | nothing was destroyed; the newer work is still there | look at it again |
| we could not tell | the state did **not** move; this side had no record | refresh |
| the peer cannot check | nothing about this item is wrong | update the peer |

Sharing one code between the first two once told someone their file had changed and their newer
edits were preserved — two false statements, and it hid the one sentence that said what to do.

And none of these messages names a hash, an object id or a token. The user authorized destroying
something they looked at; the machinery that recorded what that was is not their problem.

## Mixed versions must fail CLOSED

A safety-critical protocol change is compatible only if peers preserve the required **behaviour**. A
request that parses, executes and ignores the new field is not backward compatible — it is fail-open,
and it is the worst possible outcome: the new client believes the precondition is enforced, the old
peer destroys unconditionally, and success is reported.

So the additive-optional-field habit inverts here:

- **A new optional field is fail-OPEN.** An old peer ignores it.
- **A new method or endpoint name is fail-CLOSED by construction.** An old peer has no handler, so
  the call errors and nothing is destroyed. No capability table to keep in sync.

Prefer the second wherever the transport allows it. Where it does not — a field-shaped RPC with a
negotiated capability list — **assert the capability before dispatching**, never after. A response
cannot un-destroy anything, so "the peer confirmed it enforced the check" arrives too late to be a
safety mechanism.

Give each enforcement its **own** capability. A peer can enforce the single-item check and know
nothing about the batch one, and an already-deployed peer advertising the first is exactly that peer.
One flag for both reports a fence that is not there.

Losing the operation against an old peer is the correct outcome. Silently downgrading to the
unprotected one is not.

### A new method name fails closed at the peer, and open at the caller

The claim above — that a new method name is fail-closed by construction — is true of the *peer*
and says nothing about what the *caller* does with the rejection. An old peer answers an unknown
method exactly the way an unreachable one does, and a caller that reads "could not ask" as "no
evidence, proceed with the old algorithm" has restored the fail-open one layer up. Not
hypothetical: the estate's own replacement path asked for atomic retirement, received
`Unknown request type`, and fell through to the racy count the request existed to replace.

So separate the two questions the reply cannot separate:

- **Support is a property of the target incarnation, decided BEFORE the request.** Whatever
  authority states it — a protocol generation, an advertised capability, a handshake — consult it
  first. A reply arrives too late to be a safety mechanism, for the same reason a response cannot
  un-destroy anything.
- **Keep "the peer is too old" apart from "nothing answered."** Both are non-answers and neither
  may license destruction, but only one is fixed by updating a peer. Collapsing them made a daemon
  nobody could connect to read as an old daemon.

And when the caller's guard is a *negative* test — "treat it as a refusal unless the reason is one
of the non-answers" — the next non-answer added to that union silently becomes a refusal, which
turns an unreachable peer into an unkillable one. Write it as a positive test on the answers.

### An identity that two behaviours share is not an identity

The whole scheme rests on peers being *distinguishable*. Ship a safety-critical capability without
moving the version, and two builds advertise the same number while disagreeing about whether user
work may be destroyed — at which point no predicate can be written, by anybody, ever. The number
is not metadata; it is the key the precondition is looked up by.

The tell is cheap: **can I write the support predicate?** If the honest answer is "not from the
version, because both answer the same", the version must move before the capability ships.

Prefer fixing it by **relocation over repair**. Where the transport is addressed by version — a
versioned endpoint, socket, topic or route — moving the generation moves the whole ambiguous
population to a different address, and a destructive path scoped to "current" stops reaching it.
Nothing about the unsafe branch needs repairing; it needs to stop being reachable from a path that
claims to be safe.

Then check what the older population falls into, because "not destroyed" is not automatically
"fine": adopted and still serving its sessions is a good outcome, stranded behind an address
nobody reads is not. And prove the *newer* half too — an adoption rule that swallowed every
generation would satisfy every safety assertion while making a genuinely stale peer unreplaceable
forever.

**Get a real old peer; it is usually cheap.** A fixture built from current source supports
everything current source supports, so it cannot represent the population you are protecting, and
a version number passed to it is a label rather than a behaviour. One measured route: extract the
tree at the last commit before the capability landed, bundle its own test entry point, and run it.
That took about fifteen minutes and turned the entire argument into one observed string. Pin the
subject to that commit, and write the old version out by hand wherever the test names it — derive
it from the current constant and the next bump carries the boundary forward and erases the
evidence that this one ever existed.

## Batch operations: authorize per item, and tell the truth about the result

A multi-target destructive action authorizes the states of the items the user selected, so the
authorization is **per item**. One token for the whole snapshot makes an unrelated item's movement
refuse everything else — more annoying and no safer.

Decide the partial-failure contract explicitly, and prefer the one the product already has over a
new one. Safe-partial-completion with an explicit report usually beats all-or-nothing, which lets
one moved item block nineteen safe ones for no gain.

Then three things that are easy to get wrong:

- **Report what the authority said it did, not what you asked for.** Returning the requested set on
  success is a false aggregate the moment an item can be kept back: nineteen destroyed and one kept
  reads as twenty, so the survivor looks like a bug rather than the protection working.
- **A refusal must not fall through to an unprotected retry.** A batch path that catches *every*
  rejection and replays the items one at a time was written for a peer that lacks the batch call —
  a real case — and it cannot distinguish that from a peer refusing to destroy newer work. The
  moment refusal becomes possible, that catch converts "nothing was destroyed" into "destroy it one
  at a time". Narrow it to the case it was written for, and make the fallback itself protected.
- **Partial success needs its own notice**, separate from failure. Reporting a refusal as an error
  sends the user hunting for a fault; reporting nothing makes the survivors look like a defect.
- **Re-validation narrows; it never widens.** Iterate the set the user approved, re-checking each
  member, and never the current candidate list. A member that lost eligibility since approval
  (the user pinned it, a phone took it) drops out; a subject that *gained* eligibility since
  approval (the user un-pinned it) is not added — it belongs to the next plan. Drive both
  directions: a batch that re-plans from "whatever is eligible now" passes every narrowing test.
  (Orca X, 2026-09-17: a mutant that appended newly eligible panes after the approved loop was
  caught only by the un-pin-mid-batch case.)
- **Observation may widen the offer; it never authorizes.** A liveness sample taken to *show*
  a remote subject lets it be offered. The effect re-samples through the same reader, keys the
  answer to the host that gave it, and targets the identity the destructive API takes (a host
  PTY, not the client's handle) resolved from that fresh answer. (Orca X W7, 2026-09-17: plain-id
  fixtures hid that a paired client names panes by handle while exact stop takes host PTY ids.)

## Govern the aperture, not just today's callers

A destructive capability becoming reachable from a new client is a safety boundary change, whether
or not anything broke. Keep a classification of every destructive operation each client boundary can
reach, with a protection and a **reason someone can disagree with**, and fail when an unclassified
one appears.

Enumerate the population **structurally** — from the channel table, route table, or schema — never by
searching for the guard. Searching for a guard finds the operations that have one, which is the
opposite of the question.

An empty "unprotected" list is the dangerous state, because an empty expectation is satisfied by an
empty reality whether or not the check still works. Two controls make it mean something:

- a **floor on the population**, so a sweep that silently matched nothing cannot report a clean bill;
- a **stale-entry clause**, so the table cannot outlive its subjects — a matrix describing deleted
  operations reads exactly like one describing covered ones.

Drive the red branch with a **synthetic** entry, not whichever real one is broken today. A drill
pinned to a real defect has an interest in that defect surviving, and decays the moment it is fixed.

## DON'T

- **Don't treat every destructive action alike.** Deleting a branch with an expected head, and
  deleting uncommitted bytes, have different contracts. Reuse an existing canonical authority where
  the semantics match; do not force a content identity onto an operation already protected by a
  stronger one.
- **Don't call it protected because the tests pass.** Drive the red branch: revert the guard and
  confirm the drill fails. A green nobody has falsified could have every clause removed.
- **Don't let a test double be looser than the contract.** A stub returning nothing where the real
  authority returns an outcome made a batch path fall through on a type error — so two tests claimed
  to exercise the batch call while measuring the fallback.
- **Don't use real user data as a destructive fixture.** Create, own and delete the subject inside
  the test. This is the one rule where a mistake is not recoverable by reverting a commit.
- **Don't solve safety by disabling the feature.** Ship the negative control: with nothing moved, the
  operation still succeeds. Otherwise "refuses everything" passes every stale-case assertion.

## The completeness bar

A destructive feature is not done until it can answer: what state can this destroy · what did the
user observe · what exactly did they authorize destroying · is it recoverable elsewhere · can it
change between observation and execution · what identity represents it, and does the convenient one
actually cover the effect · who validates, and is that party authoritative · is validation close
enough to the irreversible step · can an external actor change the state · can the response be lost ·
can an old authorization be replayed after newer work exists · is operation identity separate from
state authorization · can an older peer enforce this, and does mixed-version operation fail closed ·
what happens when only some targets are still valid, and does the result say so · which clients can
reach it · what does the cost of the precondition actually measure · **who else can write to this
state · what sits between the final check and the effect · how long is that, in milliseconds · can the
race be positioned deliberately rather than hoped for · what happens when the competing write lands
before the check, inside the interval, and after the effect · does the newer state survive · and does
the batch re-authorize each member against its own destruction**.

## Source

Incident evidence moved to `~/.claude/knowledge_vault/rules-evidence/destructive-state-authorization.md` (2026-09-28) so it is not re-read on every call. The rule text above is unchanged.
