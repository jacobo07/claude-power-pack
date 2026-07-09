# FD-06 — Permanent Advantage Writeback

> The executor of the suite. FD-03 decides *what* a delta becomes and *where* it belongs; FD-06 performs
> the durable write to that location and propagates the deposit's effect across every system that should
> be able to reach it. It is the station where a distilled delta stops being a decision and becomes a
> permanent artifact on disk that future sessions consult. It absorbs three candidate systems the Reality
> Scan proved are one write surface: the Cross-System Reinforcement Layer (propagate a delta so it is
> reachable by CO-03, CO-05, GK, UKDL, PM-03, and CO-12 at once), the standalone Permanent Advantage
> Writeback Layer, and the Dataset Mutation Engine (stronger deltas *mutate* existing assets rather than
> spawn duplicates). Parents: **GK-08** (the graph-writeback transport, extended from generic
> session-node writeback to typed FD-deposit writeback with cross-system reinforcement) and **UKDL** (the
> append-only rule/lesson ledger, whose append it executes without deciding what becomes a rule). Sealed
> under **SCS C82**. Guarantee level (CO-10): **rung-3 execution with a rung-2 verification** — it
> performs the write with genuine durability mechanics (idempotency, mirror-sync, append-only supersede),
> and it verifies that the write reached the live consulted location, but it makes no routing or
> classification judgment of its own.

---

## Part I — Mission, the Execution Problem, and the Write-Destination Taxonomy

### I.1 Mission

FD-06 exists to make a routing decision physically real. FD-03 hands it a fully-routed, fully-transmuted
deposit — a destination, a form, a trigger, a completeness assertion, an optional supersede pointer, and
a rationale — but that record is still a *plan* to write, not a write. The gap between a plan and a
durable artifact is not clerical; it is the gap across which most distillation systems silently fail. A
delta that FD-01 classified correctly, that FD-03 routed to exactly the right home in exactly the right
form, produces zero dependence reduction if the write lands in the canonical repo copy but never reaches
the live `~/.claude` copy the running session actually consults; produces zero reduction if it lands in
UKDL but is never made reachable by CO-03's router or GK's navigator; produces active harm if it
overwrites a sibling pane's concurrent supersede or if a re-run double-writes it into a duplicate. FD-06's
mission is to close that gap with real durability mechanics — to perform the write to the exact location
FD-03 named, to propagate the deposit's effect to every downstream consumer that should be able to reach
it, and to verify empirically that the deposit took effect where it will actually be consulted, not merely
where the repository stores it.

The mission is deliberately scoped to *execution and propagation only*. FD-06 does not classify a delta
(FD-01's right), does not decide its destination or reshape its form (FD-03's right), does not test whether
it is portable (FD-04's right), and does not compute the dependence metric (CO-12's right). It performs the
one operation that must happen after all of those and before the deposit can compound: the durable,
idempotent, verified write plus the cross-system reinforcement that makes the write *take effect across the
stack*. This narrowness is what makes the executor auditable. Its inputs are fixed (FD-03's deposit
record), its output is a set of confirmed writes with a verification record, and its correctness is
checkable by a single question that admits no interpretation — *is the deposit now present, exactly once,
at every location a downstream consumer will look for it, including the live consulted copy?* A station
that tried to route and write in one step would be unable to answer that question cleanly, because a failed
write and a wrong route would be indistinguishable in its output. FD-06 is the last link, and the suite's
promise — capture the delta, reduce future dependence — is delivered or squandered at the moment its write
either reaches every consulted location or does not.

### I.2 The execution problem (why the write is not a `save()`)

Writing a distilled delta is not writing a row to a database, and treating it as one is the origin of the
station's characteristic failures. Three properties of the Power Pack's substrate make the write genuinely
hard, and each maps to a discipline FD-06 must enforce rather than assume.

The first property is *the canonical/live split*. Every rule, hook, command, and asset in the Power Pack
exists in two places that can drift apart: the canonical copy under the git-tracked repository
(`skills/claude-power-pack/...`) and the live copy under `~/.claude/...` that a running session actually
loads and consults. This is not a theoretical hazard; it is a documented, recurring Power Pack bug — the
hook-dispatcher split-brain, where a hook was edited and committed in the canonical tree and changed
nothing at all because the live tree was never updated, so the running session kept loading the stale
version. A distillation write that lands canonical-only is *inert in exactly the way FD-03's inert deposit
is inert*, one layer down: the deposit exists, the vault grew, the git history shows the write, and yet the
capability is never surfaced because the session consults the live copy, which never received it. FD-06
must therefore treat "the write reached the live consulted location" — not "the write reached the
repository" — as its definition of a successful write, and it must *verify* that, because the canonical
write succeeding proves nothing about the live copy.

The second property is *append-only durability with never-silent-delete*. The two systems FD-06 writes into
most — UKDL and the graph via GK-08 — are append-only by law, and for a reason the suite depends on: a
superseded deposit is not wrong, it is *history*, and the chain from a current rule back to the incident
that birthed it is load-bearing knowledge. When FD-03 routes a STRONGER delta as a supersede of an
existing deposit, FD-06 must append the new revision *and* link it back to the one it supersedes, never
overwrite or delete the old one. This is the same discipline the Session Safety Contract's Sacred Invariant
imposes on `.jsonl` transcripts (no automation destroys a transcript) and the same discipline UKDL imposes
on rules (a rule is superseded with a back-reference, never edited in place). A silent delete does not just
lose the old deposit; it breaks every back-reference that pointed at it and severs the provenance chain that
lets a future session understand *why* the current rule exists.

The third property is *concurrency on a shared substrate*. The Owner runs six to ten panes on one repo, and
several may reach FD-06 at once — two panes routing supersedes of the same deposit, two panes appending to
the same UKDL section, two panes writing graph nodes that reference each other. A naive write serializes
nothing and one pane's write silently clobbers another's, which on a shared `.git/index` is the exact
pathspec-scoped-commit hazard the Power Pack already documents (an unscoped commit from one pane packages
another pane's staged files). FD-06 must serialize supersedes as back-reference chains and scope its writes
so that concurrent panes' deposits compose rather than collide. It does not invent a lock manager; it
leans on the append-only chain discipline and pathspec-scoped writes the stack already uses, because a
bespoke coordination layer would fracture the shared floor into per-pane floors and destroy the very
un-replicability that makes the vault a moat.

These three properties are why the write is a *contract with mechanics*, not a `save()`. Storage is what a
naive writeback does — it puts bytes on disk and declares victory. Execution is what FD-06 does — it puts
bytes at every consulted location, exactly once, verifiably, without destroying history or clobbering a
sibling, and it confirms the deposit is reachable by every mechanism that should reach it before it reports
the write done.

### I.3 Difference from existing systems

**Versus GK-08 (Session Writeback).** GK-08 is FD-06's transport parent, and the relationship is
extension, not duplication. GK-08 writes session discoveries to the knowledge graph as coordinates and
edges at session close (the automatic Stop-hook re-index), and it does so for *generic* session nodes with
uniform fidelity. FD-06 extends GK-08 in two directions GK-08 does not cover. First, it writes *typed FD
deposits* — a deposit is not a generic session node but a delta with a class, a destination, a transmuted
form, and a supersede relationship, and the write must honor the destination's form (a Hard Rule's
four-field contract, a CO-05 asset's runnable recipe) rather than dropping a uniform node. Second, and this
is the genuine delta, FD-06 adds *cross-system reinforcement*: GK-08 writes one node to one graph, whereas
FD-06 writes the deposit *and* ensures every other downstream consumer sees it — a new CO-05 asset becomes a
rung CO-03 can route to and a node GK can navigate; a new Hard Rule is mirrored to the live location and
published to the bus. GK-08 answers "is it in the graph?"; FD-06 answers "is it reachable from everywhere it
should be reachable, including the live consulted copy?" FD-06 rides GK-08's graph-write mechanics for the
graph-node half of its job and never re-implements them.

**Versus UKDL.** UKDL is the append-only ledger that *stores* Hard Rules, Process Rules, and Traps. FD-06
executes the append into UKDL, but it makes no judgment about what *becomes* a rule — that judgment was
FD-03's (destination = Hard Rule) and FD-01's before it (class = NEW/STRONGER). FD-06 is the hand that
writes the ledger line; UKDL is the ledger and its append-only, supersede-with-back-reference discipline.
FD-06 inherits that discipline for *all* its destinations, not just UKDL — the never-silent-delete rule is
a UKDL law FD-06 generalizes across CO-05, the graph, and datasets — but it does not duplicate UKDL's
storage or its cross-reference machinery. When FD-06 appends a Hard Rule, it also honors the router's inline
mirror: the canonical `HARD_RULES.md` archive and the CLAUDE.md inline block are two consulted locations,
and a Hard Rule that lands in the archive but not the inline block (or the live copy of either) is a
partial write.

**Versus FD-03.** The split is planner/executor and it is absolute. FD-03 decides destination and form and
never touches disk; FD-06 executes to that destination and never makes a routing decision. FD-06 receives
FD-03's `{destination, transmuted_form, trigger, form_completeness, supersedes?, routing_rationale}` and
treats the destination as given — it does *not* re-route, re-rank homes, or second-guess the form. If FD-06
finds the deposit malformed (an unnamed trigger, a false completeness that was not flagged for follow-up),
it rejects the deposit back to FD-03 rather than repairing the route itself, because repairing the route
would be making the routing decision FD-03 owns. The one adjacent judgment FD-06 *does* make is a purely
mechanical one: given a STRONGER delta with a supersede pointer, *which physical revision-chain operation*
realizes the supersede (append-and-back-reference) — but the decision that it *is* a supersede, and of
*which* deposit, was FD-03's.

**Versus CO-05 (Asset Registry).** CO-05 is one of FD-06's write destinations, not a competitor. When
FD-03 routes a `deterministic` delta to a CO-05 asset, FD-06 performs the asset write — and, for a STRONGER
delta, the asset *mutation* (the Dataset Mutation Engine folded in): rather than spawning a second,
near-duplicate asset, FD-06 mutates the existing asset in place under the append-only-history discipline, so
CO-05 holds one improved asset with a revision trail rather than two competing ones. CO-05 answers "what
assets exist?"; FD-06 answers "make this asset exist, or make the existing one better, exactly once,
reachable by CO-03." The reinforcement half then ensures the new or mutated asset becomes a rung CO-03's
router can actually reach, because an asset CO-03 cannot route to is inert exactly as a canonical-only write
is inert.

### I.4 What FD-06 does NOT duplicate (explicit)

FD-06 does **not** classify a delta (FD-01 owns NEW/STRONGER/DUP/DISCARD), does **not** decide its
destination or transmute its form (FD-03 owns both), does **not** test portability (FD-04), does **not**
compile questions (FD-02), does **not** compute the dependence metric (CO-12), and does **not** own the
storage systems it writes into (UKDL, CO-05, the graph, the datasets are destinations FD-06 writes *to*, not
systems FD-06 re-implements). It performs one compound execution — durable write plus cross-system
reinforcement plus verification — and emits one confirmed-write record. If an edit to FD-06 begins to decide
*whether* a delta should be a Hard Rule rather than a Process Rule, it has crossed into FD-03's lane; if it
begins to judge *whether* the capability is genuinely above the floor, it has crossed into FD-01's; if it
begins to prove the capability runs on a cheaper substrate, it has crossed into FD-04's. The executor's
value is precisely its refusal to make those judgments — it takes a decided, transmuted deposit and makes
it permanently, verifiably real everywhere it must be real, and nothing more. This refusal is not modesty;
it is what keeps the write auditable, because an executor that also routed could always excuse a bad write
as a re-route, and the suite would lose the sharp boundary that lets a mis-write be localized to the write
step rather than smeared across routing and execution.

### I.5 The write-destination execution taxonomy

FD-06 executes into a closed set of destinations, mirroring FD-03's destination taxonomy but from the
execution side: each destination has a *physical write operation*, an *append-only/mutate discipline*, a
*mirror surface* (whether it has a live copy that can drift from canonical), and a *reinforcement set* (the
other consumers that must be made able to reach the deposit). The taxonomy is closed because it is FD-03's
taxonomy seen from the disk side; adding a destination here without adding it in FD-03 would create a write
target no router routes to, and removing one would leave a routed deposit with no executor.

| Destination | Physical write operation | Discipline | Mirror surface (drift risk) | Reinforcement set (must also reach) |
|---|---|---|---|---|
| **Hard Rule** (UKDL §HARD-RULES) | append the four-field contract to `HARD_RULES.md` + the CLAUDE.md inline mirror | append-only; supersede via back-reference chain, never edit-in-place | canonical archive + inline block + **live `~/.claude` copy** — high drift risk | PM-03 (publish), CO-12 (trigger registered), GK node `type: fd_dataset` |
| **Process Rule** (UKDL) | append the when-X→do-Y rule with rationale | append-only; supersede with back-reference | canonical + live copy — moderate | PM-03, CO-12, GK node |
| **Trap** (UKDL traps) | append the symptom→cause→do-not-re-investigate note | append-only | canonical + live — low (rarely inline-mirrored) | GK node (negative-knowledge edge), PM-03 |
| **CO-05 asset** (deterministic/template/cache) | write a new asset **or mutate** an existing one (Dataset Mutation Engine) | mutate-in-place under revision history for STRONGER; new record for NEW | asset registry canonical + live — moderate | **CO-03 (make it a routable rung)**, GK node, PM-03 |
| **Dataset Part** (knowledge_base) | write/extend the structured section in the dataset file | extend, never truncate a sibling section; append-only within the file | canonical dataset (rarely live-mirrored) — low | GK node `type: fd_dataset` (the primary trigger), FD-04 reference if benchmark-adjacent |
| **Benchmark** (reference value) | write the metric + reference value into the benchmark store | append/supersede a superseded reference with back-link | canonical — low | FD-04 (decay-test reference), CO-12, GK node |
| **Prompt fragment** | write the compact snippet into the prompt-fragment store | append; supersede a replaced fragment with back-link | canonical + any live prompt-assembly cache — moderate | FD-02 (compilation input), the consuming skill's assembly, GK node |

The columns that do not exist in FD-03's taxonomy are the whole point of FD-06. The *mirror surface* column
encodes which destinations carry a live-copy drift risk and therefore demand the mirror-sync verification
(II.5) — Hard Rules are the highest risk because they live in three places (archive, inline block, live
copy) and a Hard Rule that fires only in the canonical copy fires nowhere. The *reinforcement set* column
encodes the cross-system delta over GK-08: every destination's write is incomplete until the listed
consumers can also reach the deposit, and the near-universal presence of the GK node in that column is why
FD-06 rides GK-08 for one specific sub-operation (the node write) even when the primary destination is UKDL
or CO-05 — the graph node is what makes the deposit *navigable* regardless of where its content physically
lives.

### I.6 Core principles

- **The write is not done until the live consulted copy has it.** Canonical success proves nothing; the
  definition of a successful write is presence at the location the running session actually loads. This is
  the mirror-sync discipline elevated to the station's first law, because the canonical/live split is a
  documented recurring PP bug, not a hypothetical.
- **A deposit reachable from one place but not the others is a partial write.** The cross-system
  reinforcement is not an optional propagation step; an un-reinforced deposit is inert one layer below
  FD-03's inert deposit, and the write is incomplete until every consumer in the reinforcement set can
  reach it.
- **Never silent-delete; supersede with a back-reference.** A superseded deposit is history, and the chain
  from a current rule to its origin is load-bearing knowledge. This is UKDL's law and the Session Safety
  Contract's Sacred Invariant, generalized across every FD-06 destination.
- **Idempotent by content hash.** A re-run of the same deposit must not double-write. The SHA-256
  content-hash dedup key (CWOPS §2.2, idempotency-in-every-tool-contract) is the mechanism: the same
  deposit content produces the same key, and a key already present is a no-op, not a duplicate.
- **Mutate, don't duplicate, for STRONGER deltas.** A STRONGER delta improves an existing asset; FD-06
  mutates that asset under revision history rather than spawning a near-duplicate, because two competing
  assets for one capability dilute CO-03's routing and the vault's precision.
- **Serialize concurrent supersedes; scope concurrent writes.** On the shared multi-pane substrate,
  supersedes become back-reference chains (no clobber) and writes are pathspec-scoped (no sibling capture),
  leaning on stack machinery rather than a bespoke lock manager.
- **Verify, then report.** The station's guarantee is rung-3 execution *with a rung-2 verification*: it does
  not report a write done until it has confirmed presence at every consulted location, because an unverified
  write is a hypothesis, and CO-10/CO-12 forbid claiming a result that was not observed.

### I.7 Why cross-system reinforcement is the genuine delta over plain writeback

It is worth stating at length why FD-06 is a distinct station absorbing three candidates rather than a thin
wrapper over GK-08's `save()`, because the temptation to collapse it into "just write the file" is exactly
the temptation that produces the inert deposit one layer down. The argument is the same one CWOPS makes for
why the loop, not the artifact, is the moat, applied to the *last* link of the loop rather than the first.
CWOPS observes that a data flywheel degrades into a "log file" precisely when its captured signal does not
close back into changed behavior — when the loop is not, in its terms, *closed*. FD-01 guards the loop's
entry (extract the real delta, not a restatement); FD-03 guards the loop's routing (send the delta to a home
whose trigger fires at the decision point); but neither guard matters if the write that realizes the route
lands somewhere the running behavior never reads. Cross-system reinforcement is the mechanism that closes
the loop *physically*: it is the guarantee that the deposit is not merely stored but *installed* — present
and reachable at every point where the stack's behavior might consult it, so that the next time the relevant
decision point recurs, the distilled capability is actually surfaced and the stack does not escalate to the
frontier for a capability it already owns.

The reason a single write is insufficient is that the Power Pack is not one store but a mesh of consulted
systems, each with its own retrieval path. A capability distilled into a CO-05 asset is retrieved by CO-03's
router when it reaches the asset rung; the *same* capability might be needed by a session that navigates the
knowledge graph rather than invoking the router, and if the deposit is not also a GK node, that session
re-explores what the asset already holds. A Hard Rule is fired by a PreToolUse-class trigger, but a session
that reads the CLAUDE.md inline block rather than triggering the hook must also find it there, and a session
whose live copy drifted from canonical finds it nowhere. The mesh has multiple entry points, and a deposit
present at one entry point but absent at the others is *conditionally* inert — it works for the retrieval
path that happens to hit its one location and fails silently for every other path. This conditional
inertness is more insidious than total absence, because it produces intermittent, hard-to-diagnose
dependence: the capability sometimes surfaces (when the consulting path matches the deposit's one location)
and sometimes does not (when it does not), so the dependence metric shows a partial, noisy reduction that
looks like a weak but real effect rather than a broken write. FD-06's reinforcement set exists to eliminate
this failure class by making the deposit reachable from *every* entry point the mesh offers, so that the
dependence reduction is deterministic — the capability surfaces regardless of which retrieval path the
consulting session takes.

This reframes what the three absorbed candidates actually were. The "Cross-System Reinforcement Layer" was
never a separate system; it was the recognition that a write to one store is a *partial* write to a mesh,
and that completeness requires propagation to the mesh's other entry points. The "Dataset Mutation Engine"
was never a separate system either; it was the recognition that a STRONGER delta's correct physical
realization is a *mutation* of the existing asset under revision history rather than a new record, because
two records for one capability fracture the retrieval — CO-03 does not know which of two competing dedup
assets to route to, and the vault's precision (FD-00's ≥0.8 deposit-precision floor) erodes with every
duplicate. And the standalone "Permanent Advantage Writeback Layer" was the recognition that the *permanence*
is not the file existing but the deposit being reachable at every consulted location, verified, forever —
which is the durability half (append-only, never-delete, mirror-synced) married to the reachability half
(reinforcement). The three candidates are one station because they are three faces of a single operation:
make the routed delta permanently, verifiably, universally reachable across the mesh, exactly once, without
destroying history. That single operation is genuinely more than GK-08's node write, and it is genuinely
less than FD-03's routing decision, which is why it is its own station with its own contract, its own
failure modes, and its own verification discipline — the last, load-bearing link that turns a good routing
decision into a durable, compounding reduction in what the stack must ask the frontier to do.

A final consequence of this framing is that FD-06 is the station where the suite's honesty about its own
guarantee level is most severely tested, because it is the only station whose success is *physically
checkable* and therefore the only one that can be caught lying by a filesystem probe rather than by a
judgment. FD-01 can over-classify NEW and the lie is subtle (it takes a fresh-baseline re-check to expose);
FD-03 can mis-route and the lie takes a consultation-rate join to surface. But FD-06 either wrote the
deposit to the live consulted copy or it did not, and a single `Test-Path` against the live location settles
it. This checkability is a gift, and FD-06's design leans into it: rather than trusting that a write
succeeded because the write call returned, the station *verifies* presence at every consulted location and
reports the write done only when the verification passes. This is the CO-12 Telemetry-Before-Claims Contract
made physical — the write is not a result until it is observed to have reached where it will be consulted,
and because that observation is a cheap filesystem check, there is no excuse for the station to ever report a
write it did not confirm. The station that results is one whose central claim ("the advantage is now
permanent and reachable") is the one claim in the whole suite that can be, and therefore must be, backed by
a direct observation rather than a chain of inference — which is exactly why the executor, not the
classifier or the router, is where the suite's permanence guarantee actually lives.

---

## Part II — The Write-and-Reinforcement Contract

### II.1 Operating contract (inputs and outputs)

FD-06's **input** is FD-03's routed, transmuted deposit: `{destination, transmuted_form, trigger,
form_completeness, supersedes?, routing_rationale}`, wrapped by FD-00 with the session's `co12_signals` and
the originating `canonical_trace` from FD-01. FD-06 treats this record as authoritative and immutable on the
routing dimension — it reads the destination and executes to it; it does not re-decide. Its **output** is a
confirmed-write record: `{write_id, content_hash, destination, physical_locations_written[],
live_copy_verified, reinforcement_set_confirmed[], supersede_chain?, bus_published, co12_signal_emitted,
verification_status ∈ {confirmed, partial, failed}}`. The record is the deposit's permanence receipt: it
names the SHA-256 content hash that makes the write idempotent, the exact physical locations written
(canonical *and* live), an explicit boolean that the live consulted copy was verified present, the list of
reinforcement-set consumers confirmed able to reach the deposit, the supersede back-reference chain if any,
and the terminal verification status. The contract's hard postcondition: **no write is reported `confirmed`
unless the live consulted copy is verified present and every consumer in the destination's reinforcement set
is confirmed reachable** — a write that reached canonical but not live, or one store but not the mesh, is at
best `partial` and is surfaced as such, never dressed as done.

Three output fields carry the station's genuine weight. `content_hash` is the idempotency key: it is
computed over the deposit's transmuted content (UTF-8-byte-normalized, so trivial whitespace or line-ending
differences do not defeat dedup), and a re-run whose hash already appears in the destination is a no-op, not
a second write. `live_copy_verified` is the mirror-sync postcondition made a first-class field: it is not
set by the write call returning, but by a positive read-back of the deposit from the live `~/.claude`
location after the write. `reinforcement_set_confirmed` is the cross-system delta made structural: it lists,
per the taxonomy's reinforcement column, each consumer verified able to reach the deposit (CO-03 rung
registered, GK node present, PM-03 published, CO-12 signal emitted), and a write with an incomplete
reinforcement set is `partial`.

### II.2 The write-and-reinforcement procedure

The write runs in six ordered steps, each with a defined output, so a failed or partial write localizes to a
step rather than presenting as an opaque failure.

**Step 1 — validate the deposit.** Confirm the input record is well-formed for execution: destination is in
the closed taxonomy, `trigger` is named, `form_completeness` is true (or explicitly flagged-for-follow-up by
FD-03). A malformed deposit is rejected *back to FD-03*, not repaired — repairing the route would be making
FD-03's decision. This step is the boundary that keeps a routing error from being masked by the write
succeeding.

**Step 2 — compute the idempotency key and check for a prior write.** Compute the SHA-256 content hash over
the normalized transmuted form. Query the destination for an existing deposit with the same hash. If present,
the write is a no-op — the deposit already exists exactly once — and the station short-circuits to a
`confirmed` record referencing the existing write. This is the CWOPS §2.2 idempotency-in-every-tool-contract
discipline: the write operation is safe to retry because its effect depends only on the content, not on how
many times it runs.

**Step 3 — resolve the physical operation (new vs mutate vs supersede).** If the deposit carries no
supersede pointer and is NEW, the operation is an append/new-record write. If it carries a supersede pointer
(a STRONGER delta improving an existing deposit), the operation is a *mutation under revision history* for a
CO-05 asset (mutate in place, retain the prior revision in the chain) or an *append-with-back-reference* for
UKDL/graph/benchmark (append the new revision, link it back to the superseded one, never delete the old).
The Dataset Mutation Engine is this step's mutate-branch: a STRONGER delta becomes a better version of the
existing asset, not a second asset.

**Step 4 — write to canonical *and* live.** Perform the physical write to the canonical repository location
and, for any destination whose mirror surface includes a live copy, to the live `~/.claude` location. The
two writes are treated as one atomic obligation: a canonical write without its live counterpart is an
incomplete Step 4, not a completed write. For Hard Rules, "canonical" is itself plural (the `HARD_RULES.md`
archive *and* the CLAUDE.md inline mirror), and all of them plus the live copy must receive the deposit.

**Step 5 — cross-system reinforcement.** Propagate the deposit to every consumer in the destination's
reinforcement set: register a CO-05 asset as a CO-03-routable rung; write the GK node (`type: fd_dataset`)
with typed edges to the deposit's CO/PM/GK parents so the deposit is navigable; publish to the PM-03 bus so
concurrent panes see it; emit the CO-12 `delta_deposited` signal so the dependence metric and the
consultation-tracking machinery register the new deposit. Each propagation's success is recorded in
`reinforcement_set_confirmed`.

**Step 6 — verify and report.** Read back the deposit from the live consulted copy (setting
`live_copy_verified`) and confirm each reinforcement-set consumer can reach it. Only if the live copy is
verified present *and* the reinforcement set is complete is the write reported `confirmed`; otherwise it is
`partial` (some but not all locations) or `failed` (the primary write did not land), and the gap is surfaced
explicitly with the exact missing location so it can be repaired.

The procedure is deliberately explicit because the station's failures cluster at specific steps. A skipped
Step 2 double-writes on a re-run (the idempotency failure). A Step 4 that writes canonical but not live is
the mirror-sync split-brain — the deposit exists in git and is inert in the running session. A skipped Step
5 produces the conditionally-inert deposit reachable from one entry point but not the mesh. A skipped Step 6
reports a write done that was never confirmed — the exact CO-12 Telemetry-Before-Claims violation. Making
each step a named, inspectable output means an audit can localize a bad write to the step that caused it,
which is how the station's reliability is improved over time rather than treated as a black box.

### II.3 Interfaces with existing PP systems

- **GK-08** — FD-06's transport parent for the graph-node half of every write; FD-06 calls GK-08's node-write
  mechanics to create the `type: fd_dataset` node with typed edges and never re-implements graph writing. The
  extension is that FD-06 wraps GK-08's generic node write inside the typed-deposit + reinforcement contract.
- **UKDL** — the destination for Hard Rule / Process Rule / Trap appends; FD-06 executes the append under
  UKDL's append-only, supersede-with-back-reference law, and honors the Hard Rule inline-mirror surface.
- **CO-05** — the destination for asset writes and, for STRONGER deltas, asset *mutations* under revision
  history; FD-06 writes the asset and (Step 5) registers it as a CO-03-routable rung.
- **CO-03** — reinforcement target, not a write destination: a new CO-05 asset is made a rung CO-03 can
  reach, which is the mechanism by which a written deposit reduces future frontier calls.
- **PM-03** — every confirmed deposit is published to the findings bus so concurrent panes consume it before
  re-reasoning and do not re-deposit it; this is also the concurrency-safety mechanism (II.5, III.12).
- **CO-12** — receives the `delta_deposited` signal per write and the consultation-tracking hooks that let
  FD-03's consultation-rate metric and the family's dependence metric register the deposit; FD-06 *feeds*
  CO-12, never stands up a parallel accounting layer.
- **FD-03** — supplies the routed, transmuted deposit; receives a malformed-deposit rejection when Step 1
  fails. **FD-01** — its `canonical_trace` rides along for provenance. **FD-04** — benchmark deposits are
  written as FD-04's decay-test references; a `frontier-only` deposit is written flagged as an FD-05
  conversion candidate.

### II.4 Decision rights and non-decision rights

FD-06 **may decide**: the idempotency key computation and the dedup verdict (is this content already
present?); the physical operation that realizes a supersede (mutate-in-place vs append-with-back-reference,
a mechanical choice dictated by the destination type); the write order across canonical and live; the
reinforcement propagation order; and the terminal verification status. FD-06 **may not decide**: the delta's
class (FD-01); its destination or transmuted form (FD-03); whether the capability is portable in fact
(FD-04); whether a delta *should* supersede another (FD-03 sets the supersede pointer; FD-06 only executes
it); or the dependence metric's values (CO-12 computes; FD-06 emits the raw signal). The subtle boundary is
with FD-03 on supersedes: FD-03 decides *that* delta A supersedes deposit B and sets the pointer; FD-06
decides only *how* to physically realize that (which revision-chain operation), and if the target deposit B
turns out to no longer exist (it was deprecated), FD-06 does not silently create a new deposit — it surfaces
the broken supersede pointer back to FD-03, because deciding to route A as NEW instead of a supersede is a
routing decision. FD-06's autonomy is entirely on the *mechanics* of the write, never on *what* is written or
*where*.

### II.5 Idempotency and mirror-sync rules

Two disciplines are load-bearing enough to be specified as their own contract, because each corresponds to a
documented, recurring failure the station exists to prevent.

**Idempotency (the SHA-256 content-hash dedup key).** Every write is keyed by a SHA-256 hash computed over
the deposit's normalized transmuted content — UTF-8 bytes, normalized line endings, stable field ordering —
so that the same deposit produces the same key regardless of trivial formatting differences or how many
times the write is attempted. Before writing (Step 2), the destination is queried for the key; a present key
short-circuits to a no-op. This makes the write *safe to retry*, which matters enormously on the Power Pack's
substrate where a session may re-run a distillation, a Stop hook may fire twice, or a pane may re-attempt a
write after an ambiguous failure. Without the key, each retry appends a duplicate, and the vault fills with
near-identical deposits that dilute CO-03's routing and erode deposit precision — the duplicate-write failure.
The key is the concrete realization of CWOPS §2.2's idempotency-in-every-tool-contract principle: a durable
write is not durable if it cannot be safely repeated, and the content hash is the cheapest mechanism that
makes repetition safe. The normalization matters: a naive hash over raw bytes would treat a CRLF-vs-LF
difference or a reordered field as new content and defeat the dedup, so the hash is computed over a canonical
serialization, the same discipline the Power Pack applies to its integrity-map MD5s and audit-cache SHA-256s.

**Mirror-sync-direction (verify the write reached the live consulted location).** This is the station's most
important rule because it corresponds to the most damaging documented PP bug: the canonical/live split-brain,
where a hook or rule edited and committed in the canonical tree changes nothing because the live `~/.claude`
tree — the one the running session loads — was never updated. FD-06 treats a write as reaching *two*
obligated locations for any mirror-surface destination: the canonical repository copy and the live
`~/.claude` copy. Step 4 writes both; Step 6 *verifies* the live copy by reading the deposit back from it,
setting `live_copy_verified` only on a positive read-back. A write that lands canonical but not live is
reported `partial` with the live location named as the gap, never `confirmed`. The rule's teeth are in the
verification, not the write: it is not enough to *attempt* the live write, because the live write can fail
silently (a permissions deny on `~/.claude/hooks`, a sync-direction rule that only propagates canonical→live
on certain paths), and an attempted-but-unverified live write is exactly the split-brain wearing a
success costume. The mirror-sync rule also encodes *direction*: for a Hard Rule the canonical archive is the
source of truth and the live copy is the mirror, so the propagation is canonical→live, and FD-06 must not
invert it (writing live-only would leave the durable git-tracked copy stale and the deposit would vanish on
the next canonical-driven sync). The rule is: write canonical (source of truth), propagate to live (consulted
mirror), verify live present, and report `confirmed` only when the read-back from the live copy succeeds.

### II.6 Token-ROI rules

FD-06 is itself a cost, and the doctrine forbids an executor that costs more than it saves. The write and its
verification are cheap by construction — a content hash, a handful of file writes, a read-back, and a few
reinforcement registrations — and this cheapness is essential, because the station runs on *every* deposit,
so any per-write expense multiplies across the vault. The ROI rule is that the executor's per-write cost must
be a negligible fraction of the frontier call that produced the delta it is writing; a writeback that
reasoned as long as the model did would have no ROI, the same CWOPS guardrail-economics principle FD-01 and
FD-03 inherit. The one place FD-06 could accidentally become expensive is the verification and reinforcement
steps, if they were done by re-reasoning rather than by cheap mechanical checks — so the verification is a
filesystem read-back (not an LLM judgment) and the reinforcement registrations are structural writes (not
re-derivations). The station's entire value is that it makes a decided deposit permanent and reachable with
near-zero marginal cost, and the moment it starts spending real tokens to do so, it has become the CWOPS
anti-pattern of a guardrail that costs more than the loss it prevents.

### II.7 Portability's effect on the write, and no-bloat

The delta's portability estimate, carried through from FD-01 and honored by FD-03's destination choice,
shapes FD-06's reinforcement emphasis. A `deterministic` deposit routed to a CO-05 asset gets its *strongest*
reinforcement toward CO-03 — the whole point of a deterministic asset is that CO-03 can route to it and
avoid a model call entirely, so making it a routable rung is the reinforcement that most directly reduces
dependence, and FD-06 verifies the rung registration with particular care. A `frontier-only` deposit routed
to a dataset Part gets written with an explicit not-yet-portable flag and a reinforcement edge that marks it
an FD-05 conversion candidate, so the conversion machinery can find it. FD-06's no-bloat rule is the
idempotency key plus the mutate-don't-duplicate discipline: a re-run does not bloat (the key dedups), and a
STRONGER delta does not bloat (it mutates the existing asset rather than spawning a duplicate). The station
never files a deposit it was not handed — there is no FD-06 path that writes without an FD-03 deposit — so
the only bloat it could introduce is duplication, and both duplication vectors (retry and near-duplicate
supersede) are closed by construction. This makes FD-06 the station where the suite's deposit-precision floor
(FD-00's ≥0.8) is physically enforced: every duplicate the executor prevents is a vault entry that never has
to be garbage-collected later.

### II.8 A worked writeback: one deposit, full propagation

The contract is clearest when a single deposit is walked through the six steps with its full cross-system
propagation, because the reinforcement is invisible until you trace where the one deposit must land. Take
the deposit FD-03 hands over from the FD-03 worked example: the pane-admission scope-disjointness invariant,
routed to a **Hard Rule** with TRIGGER (scheduler admits a new pane), STOP (verify scope disjointness against
all admitted panes; refuse on overlap), EXCEPTION (an Owner phrase authorizing an overlapping admission for
one turn), ORIGIN (the observed silent-double-processing incident), `form_completeness` true, no supersede
pointer (it is NEW), portability `deterministic`.

**Step 1 — validate.** Destination is Hard Rule (in taxonomy); trigger is named (pane admission);
completeness is true. The deposit is well-formed for execution.

**Step 2 — idempotency.** FD-06 computes the SHA-256 over the normalized four-field contract and queries
UKDL §HARD-RULES for that key. Not present — this is a genuinely new Hard Rule. Proceed.

**Step 3 — physical operation.** No supersede pointer, class NEW → the operation is an append of a new Hard
Rule record (assign the next HR-NN id).

**Step 4 — write canonical *and* live.** The Hard Rule's mirror surface is plural: FD-06 appends the
four-field contract to the canonical `vault/hard_rules/HARD_RULES.md` archive, appends the inline mirror
block to the canonical CLAUDE.md, *and* propagates both to the live `~/.claude` copies. All four physical
locations (archive canonical, inline canonical, archive live, inline live) receive the deposit; a write that
updated the archive but not the inline block, or canonical but not live, is an incomplete Step 4.

**Step 5 — cross-system reinforcement.** The Hard Rule's reinforcement set is {PM-03, CO-12, GK node}. FD-06
publishes the new Hard Rule to the PM-03 bus (so a concurrent pane admitting a pane sees the invariant is now
enforced and does not re-derive it); emits the CO-12 `delta_deposited` signal with the deposit's class and
destination (so the dependence metric registers a new frontier-only-avoidance rule and the consultation
tracker begins watching whether the trigger fires); and writes the GK node `type: fd_dataset` with typed
edges to its parents (the concurrency-architecture coordinate, the PM-02 collision-detection node) so a
future session navigating concurrency knowledge reaches the rule instead of re-deriving it.

**Step 6 — verify and report.** FD-06 reads the Hard Rule back from the *live* CLAUDE.md and the *live*
archive (setting `live_copy_verified = true` only on positive read-back), confirms the PM-03 publish, the
CO-12 signal, and the GK node are all reachable, and reports `verification_status = confirmed`. The
confirmed-write record names all four physical locations, the content hash, the verified live copy, and the
complete reinforcement set.

The propagation is the whole lesson. A naive writeback would have appended the Hard Rule to `HARD_RULES.md`
and stopped — and the rule would have been *conditionally inert*: it would fire only if the running session's
Hard Rule mechanism loaded the archive, and if the live copy drifted from canonical it would fire nowhere,
and a session navigating the graph rather than triggering the hook would never find it. FD-06's six steps
make the rule reachable from every entry point: the hook fires it (live copy verified), a reader finds it in
the inline block, a graph navigator reaches the node, a concurrent pane sees it on the bus, and CO-12 tracks
whether it is consulted. The idempotency check (Step 2) means that if this exact distillation re-runs — a
Stop hook firing twice, a session re-processing — the Hard Rule is not appended a second time under a new
HR-NN id, which would produce two identical rules and dilute the archive. And because the write is NEW with
no supersede, the mutate branch (Step 3) does not engage; had it been a STRONGER improvement to an existing
Hard Rule, FD-06 would have appended the improved revision with a back-reference to the superseded HR-NN
rather than editing it in place, preserving the provenance chain to the original incident.

### II.9 The reinforcement-completeness invariant

The deepest property FD-06 must maintain, and the one that distinguishes it most sharply from a file write,
is what can be called the *reinforcement-completeness invariant*: at the moment FD-06 reports a write
`confirmed`, the deposit is reachable from every entry point in the mesh that a consulting session might use
to look for it, and this reachability has been verified rather than assumed. The invariant is subtle because
its violation is silent and intermittent. A deposit that violates it — present in UKDL but not the graph, or
canonical but not live — does not throw an error; it simply fails to surface on the retrieval paths that miss
its one location, and the resulting dependence reduction is partial and noisy in a way that is nearly
impossible to attribute to a specific broken write after the fact. This is why the invariant must be enforced
at write time, by verification, rather than discovered later by a dependence-metric anomaly: the cost of a
violated invariant is not a loud failure but a quiet, un-diagnosable erosion of the very metric the whole
suite is built to move.

The invariant also explains why FD-06's verification is a *read-back*, not a *write-return-check*. A write
call returning success proves the write API accepted the bytes; it does not prove the bytes are present at
the consulted location, because the consulted location may be a different copy (the live/canonical split),
the write may have been silently redirected or denied (a permissions deny on `~/.claude/hooks`, which the PP
substrate documents as a real occurrence), or a concurrent pane may have clobbered it between the write and
the report. Only reading the deposit *back* from the exact location a consulting session will read from
proves the invariant holds. This is more expensive than trusting the write-return — a read-back per location
— but the expense is a cheap filesystem read, and the alternative is the conditionally-inert deposit whose
cost is un-diagnosable dependence erosion. The trade is decisively in favor of verification, and it is the
concrete form the CO-12 Telemetry-Before-Claims Contract takes at this station: the write is not a result
until it is observed present where it will be consulted.

There is a second, structural reason the invariant is enforced by FD-06 rather than left to the individual
destination systems. Each destination system (UKDL, CO-05, the graph) knows how to store *its own* deposit,
but none of them knows about the *others*, so none can enforce that a deposit present in it is also present
in the mesh's other entry points. UKDL cannot check that a Hard Rule it holds is also a GK node; CO-05 cannot
check that an asset it holds is also a CO-03 rung. The cross-system view belongs to no single store, which is
precisely why it needs a station — FD-06 — that sits above all of them and holds the reinforcement set as its
own contract. This is the same argument FD-01 makes for why extraction needs a station above PM-03's
transport, and FD-03 for why routing needs a station above the destinations: the cross-cutting judgment
belongs to no single component, so it gets its own. FD-06's cross-cutting judgment is reachability across the
mesh, and the reinforcement-completeness invariant is the property that judgment exists to maintain. A suite
whose writeback enforced only per-store presence would be a suite whose deposits were each individually
stored and collectively unreachable — gold in seven separate vaults with no single map that leads to all of
them — which is why the invariant, and the station that holds it, are not optional polish but the mechanism
by which a decided delta becomes a durable, universally-reachable, compounding advantage rather than a
scattering of conditionally-inert writes.

---

## Part III — Failure Modes, Gates, Benchmarks, and Evolution

### III.1 Failure modes with diagnosis protocol

| Failure mode | Symptom | Diagnosis | Root cause |
|---|---|---|---|
| **Canonical/live split-brain** | deposit exists in git; running session behaves as if it were never written; Hard Rule never fires | `Test-Path` / read-back the deposit from the *live* `~/.claude` copy; compare to canonical | Step 4 wrote canonical but not live, or Step 6 verification skipped; the documented hook-dispatcher split-brain |
| **Conditionally-inert deposit** | dependence reduction partial and noisy; capability surfaces on some retrieval paths, not others | check `reinforcement_set_confirmed`; find which mesh entry points lack the deposit | Step 5 reinforcement incomplete — deposit in one store, not the mesh |
| **Duplicate write** | vault holds two near-identical deposits; CO-03 routing ambiguous between them | join deposits by content hash; find two records with the same normalized content | Step 2 idempotency check skipped; a retry/double-fire appended a second copy |
| **Silent clobber (concurrency)** | a sibling pane's supersede vanished; provenance chain broken | compare the supersede chain to the two panes' write records; find a lost revision | Step 3 supersede not serialized as a back-reference chain; two panes wrote naively |
| **Broken supersede pointer** | a STRONGER delta's target deposit no longer exists; supersede lands nowhere or spawns a stray | check whether the `supersedes?` target is present | FD-03's target was deprecated between routing and execution; FD-06 should have rejected to FD-03 |
| **Provenance severed (silent delete)** | a superseded deposit is gone, not chained; back-references dangle | audit for deposits referenced by a back-link but absent | Step 3 edited/deleted in place instead of append-with-back-reference; violates UKDL/SSC law |
| **Unverified-report** | write reported `confirmed`, later found absent at a consulted location | re-verify every location in the confirmed-write record against disk | Step 6 reported without a read-back; the Telemetry-Before-Claims violation |

The station's characteristic failure is the **canonical/live split-brain**, because it is the failure that
*looks* like success in the place people check. The git history shows the write, the canonical file holds the
deposit, a code review of the repository passes — and the running session, which loads the live copy, behaves
as if nothing was written. This is the exact one-layer-down analogue of FD-03's inert deposit (correctly
decided, physically written, operationally dead) and it is dangerous for the same reason: every metric of
*writing* is green and only the metric of *consultation* — did the live session ever surface this? — reveals
the deposit is inert. The diagnosis is cheap and decisive (read the deposit back from the live copy), which
is exactly why Step 6's live read-back is non-negotiable: the failure is invisible to every check except the
one FD-06 is required to run before reporting done.

### III.2 Anti-patterns with evidence

- **Write-and-trust.** Reporting a write done because the write call returned, without a read-back from the
  live consulted location. Evidence: the documented hook-dispatcher split-brain, where committed changes
  changed nothing because the live tree was stale; and the CO-12 Telemetry-Before-Claims Contract, which
  forbids claiming an unobserved result. Forbidden by Step 6's mandatory live read-back.
- **Canonical-only writeback.** Writing the git-tracked copy and stopping, on the assumption a sync will
  propagate to live. Evidence: mirror sync is direction-scoped and can silently skip `~/.claude/hooks` on a
  permissions deny; a write that is not verified live is the split-brain. Forbidden by the mirror-sync rule
  (II.5).
- **Duplicate-on-retry.** Appending a fresh deposit every time a distillation re-runs, with no content-hash
  dedup. Evidence: CWOPS §2.2 idempotency-in-every-tool-contract; a durable write must be safe to repeat.
  Forbidden by the Step 2 SHA-256 key.
- **Duplicate-not-mutate.** Spawning a second CO-05 asset for a STRONGER delta instead of mutating the
  existing one, fracturing CO-03's routing between two competing assets. Evidence: FD-00's ≥0.8
  deposit-precision floor; two records for one capability erode precision. Forbidden by the Step 3 mutate
  branch (the Dataset Mutation Engine).
- **Silent-delete-on-supersede.** Overwriting or deleting a superseded deposit instead of appending a
  back-referenced revision. Evidence: UKDL's append-only law and the Session Safety Contract's Sacred
  Invariant (no automation destroys a `.jsonl`); provenance is load-bearing knowledge. Forbidden by the
  never-silent-delete principle.
- **Store-completeness masquerading as mesh-completeness.** Reporting a write done because the primary store
  holds it, without confirming the reinforcement set. Evidence: the conditionally-inert deposit's
  un-diagnosable dependence erosion. Forbidden by the reinforcement-completeness invariant (II.9) and the
  `reinforcement_set_confirmed` postcondition.

### III.3 Quality gates (binary)

- **G1 — Idempotent.** Does every write carry a SHA-256 content-hash key, and does a same-key write
  short-circuit to a no-op? Binary.
- **G2 — Live-verified.** Is `live_copy_verified` set by a positive read-back from the live consulted copy
  for every mirror-surface destination? Binary (the mirror-sync postcondition).
- **G3 — Reinforcement complete.** Is every consumer in the destination's reinforcement set confirmed
  reachable before the write is reported `confirmed`? Binary (the reinforcement-completeness invariant).
- **G4 — Append-only / never-delete.** Does every supersede append a back-referenced revision and leave the
  superseded deposit intact? Binary.
- **G5 — No-route-decision.** Does the write execute FD-03's destination without re-routing, and reject a
  malformed deposit back to FD-03 rather than repairing it? Binary (the executor boundary).
- **G6 — Verified-before-reported.** Is no write reported `confirmed` without the Step 6 verification passing?
  Binary (Telemetry-Before-Claims).

### III.4 Evaluation rubric (measurable)

| Dimension | Metric | Source | Target |
|---|---|---|---|
| Live-write fidelity | fraction of writes whose live copy is verified present at report time | confirmed-write records vs live-disk read-back | 1.0 (any miss is a split-brain) |
| Idempotency | fraction of re-run deposits that no-op instead of duplicating | content-hash collision audit | 1.0 |
| Reinforcement completeness | fraction of writes with a fully-confirmed reinforcement set | `reinforcement_set_confirmed` audit | ≥ 0.98 |
| Provenance integrity | fraction of supersedes that preserved the back-reference chain (no silent delete) | supersede-chain audit | 1.0 |
| Duplicate rate | fraction of deposits that are content-hash duplicates of an existing deposit | vault dedup scan | → 0 |
| Write-to-consultation | fraction of confirmed deposits later observed consulted at their trigger | CO-12 consultation join | rising (feeds FD-03's metric) |

### III.5 Benchmarks with reference values

The station's benchmarks anchor to durability and reachability, not throughput. **Live-write floor: 1.0** —
every confirmed write must be verified present at the live consulted copy; this is the one metric that admits
no shortfall, because a single canonical-only write is a split-brain, and the split-brain is the station's
defining failure. **Idempotency floor: 1.0** — a re-run must never duplicate; below 1.0 the vault inflates on
every retry and deposit precision cannot hold. **Provenance floor: 1.0** — no supersede may silently delete;
the back-reference chain from a current rule to its origin is load-bearing and its loss is irreversible.
**Reinforcement floor: ≥ 0.98** — near-total mesh reachability; the small tolerance exists only for
destinations whose ideal reinforcement target is not yet implemented (an honest CO-10-level flag, per II.4),
never for a target that exists and was skipped. **Cost ceiling:** the per-write cost (hash + writes +
read-back + reinforcement registrations) must be a negligible fraction of the frontier call that produced the
delta — the CWOPS guardrail-economics principle; an executor that spent real reasoning to write would have no
ROI. **Duplicate rate: → 0** — the vault should trend toward zero content-hash duplicates as the idempotency
key and mutate-don't-duplicate discipline hold across the vault's lifetime.

### III.6 Example operational traces

**Trace A — NEW Hard Rule, full propagation.** As II.8: validate → hash-not-present → append new HR-NN to
archive + inline, canonical + live → publish PM-03, emit CO-12, write GK node → read-back live confirms →
`confirmed`, four locations named.

**Trace B — STRONGER CO-05 asset, mutation.** FD-03 routes a STRONGER dedup-recipe improvement to CO-05 with
a supersede pointer to the existing recipe asset. Step 3 resolves to *mutate-in-place under revision history*:
FD-06 updates the asset to the improved recipe, retaining the prior revision in the asset's chain (not a
second asset). Step 5 re-registers the mutated asset as the CO-03 rung (so the router now reaches the improved
version) and updates the GK node. Step 6 verifies the mutated asset is live and CO-03-routable. `confirmed`;
`supersede_chain` records the prior revision.

**Trace C — idempotent re-run (no-op).** A Stop hook fires twice and re-submits the same benchmark deposit.
Step 2 computes the hash and finds it already present in the benchmark store. The write short-circuits to a
`confirmed` record referencing the existing write — no second benchmark, no duplicate. The re-run cost is a
single hash-and-query.

**Trace D — canonical-live gap caught.** A Process Rule write lands canonical but the live `~/.claude` write
is silently denied (a permissions deny on the live path). Step 6's read-back from the live copy fails;
`live_copy_verified = false`; `verification_status = partial`, with the live location named as the gap and a
concrete next action (re-propagate canonical→live, or surface the permissions deny to the Owner). The write is
*not* reported `confirmed` — the split-brain is caught at write time rather than discovered as inert weeks
later.

**Trace E — broken supersede pointer, rejected to FD-03.** A STRONGER delta carries a supersede pointer to a
CO-05 asset that was deprecated between routing and execution. Step 3 finds the target absent. FD-06 does not
silently create a new asset (that would be re-routing); it rejects the deposit back to FD-03 with "supersede
target absent — re-route as NEW or to the replacement asset," honoring the executor boundary.

**Trace F — concurrent supersede, serialized.** Two panes route improvements to the same Hard Rule at once.
FD-06 serializes them as a back-reference chain: pane A's revision appends with a back-link to the original;
pane B's revision appends with a back-link to A's, not a clobber. Both improvements survive; the chain stays
legible; the PM-03 bus shows both routes so neither pane re-derives the other's increment.

### III.7 Edge cases

- **Deposit whose content hash collides with a genuinely different deposit.** Astronomically unlikely with
  SHA-256, but on a detected collision FD-06 treats the deposits as distinct by falling back to a
  location-plus-content comparison rather than trusting the key alone — a defensive check, not an expected
  path.
- **Mirror-surface destination whose live path is denied.** As Trace D: reported `partial` with the denied
  live path named; never `confirmed`; the deny is surfaced (the `~/.claude/hooks` write-deny is a documented
  PP occurrence).
- **STRONGER delta superseding a deposit under active read by a reviewer pane.** Per the G2-reviewer-rebase
  race discipline, FD-06 does not mutate a deposit while a reviewer pane is reading it; it serializes behind
  the review verdict, because a mid-read mutation is a file-state race that can invalidate the review.
- **Reinforcement target not yet implemented.** If the ideal reinforcement (e.g., a CO-03 rung type that does
  not exist yet) is absent, FD-06 writes the deposit, reinforces every *existing* target, and flags the
  absent one as a follow-up — the CO-10 honest-guarantee discipline, never pretending an absent target was
  reinforced.
- **Deposit that is a Dataset Part extending a file another pane is concurrently editing.** FD-06 uses
  pathspec-scoped writes and the append-only-within-file discipline so the two panes' section additions
  compose rather than one clobbering the other (the sibling-commit-absorbs-untracked-files hazard).
- **DUP/DISCARD arriving at FD-06.** These should never reach the executor (FD-01/FD-03 stop them), but if a
  do-not-store-flagged record arrives, FD-06 honors the flag and writes nothing, recording the no-op for the
  audit trail.

### III.8 Writeback verification rules

The verification is the station's guarantee made physical, and it has four rules. **First: verify at the
consulted location, not the written location.** The read-back is from the live `~/.claude` copy (or the exact
canonical location a consulting path uses), because that is where a session will look; verifying the location
FD-06 just wrote to proves only that the write API accepted bytes. **Second: verify the reinforcement set,
not just the primary store.** Each consumer in the destination's reinforcement set is confirmed able to reach
the deposit (the GK node is present and navigable, the CO-03 rung is registered, the PM-03 publish landed, the
CO-12 signal was accepted); the reinforcement-completeness invariant is checked, not assumed. **Third: a
partial verification is reported as partial, never rounded up to confirmed.** If the primary store has the
deposit but one reinforcement target does not, the status is `partial` with the gap named — the honest state,
because a partial write is a conditionally-inert deposit and must be visible as such. **Fourth: the
verification is a cheap mechanical read, never an LLM re-judgment** — a filesystem read-back and a
registry-presence check, so the verification cannot become the expense that voids the station's ROI. These
four rules together are why FD-06's guarantee level is "rung-3 execution *with a rung-2 verification*": the
write is a real, mechanical execution, and the verification is a real, measured observation, so the station's
central claim — the advantage is now permanent and reachable — is the one claim in the suite backed by direct
observation rather than inference.

### III.9 Conceptual regression tests

- **R1 — Idempotent re-run.** Submit the same deposit twice; assert the second is a no-op referencing the
  first, not a duplicate.
- **R2 — Live-verified write.** Write a mirror-surface deposit; assert `live_copy_verified` is set only after
  a positive read-back from the live copy, and that a simulated live-write-deny yields `partial`, not
  `confirmed`.
- **R3 — Mutate-not-duplicate.** Submit a STRONGER delta with a supersede pointer to a CO-05 asset; assert the
  asset is mutated under revision history, not duplicated.
- **R4 — Never-silent-delete.** Submit a supersede; assert the superseded deposit remains present and is
  back-referenced by the new revision.
- **R5 — Reinforcement completeness.** Write a CO-05 asset; assert it is confirmed reachable as a CO-03 rung
  *and* a GK node before the write is `confirmed`; a missing rung yields `partial`.
- **R6 — Executor boundary.** Submit a malformed deposit (unnamed trigger); assert FD-06 rejects it back to
  FD-03 rather than repairing the route.
- **R7 — Broken supersede.** Submit a STRONGER delta whose supersede target was deprecated; assert rejection
  to FD-03, not a silent new write.
- **R8 — Verified-before-reported.** Simulate a write that lands canonical but not live; assert the status is
  never `confirmed`.

Per SCS C41, these are gate assertions for the EXECUTION-mode harness, not auto-generated unit tests; the
live-write-fidelity and reinforcement-completeness metrics are measured against real disk read-backs and
registry-presence checks, which is the honest observation the anti-test-theater rule requires.

### III.10 Done criteria (verifiable)

FD-06 is done when: the dataset exists on disk, un-truncated, >2500 real words/Part; the write-destination
taxonomy is closed and mirrors FD-03's destinations with a physical operation, discipline, mirror surface,
and reinforcement set per destination; the six-step procedure localizes each failure to a step; idempotency
is a SHA-256 content-hash key with a same-key no-op; the mirror-sync rule requires a live-copy read-back
before any `confirmed` report; the reinforcement-completeness invariant is a binary gate; the never-silent-
delete / append-with-back-reference discipline is enforced across every destination; the executor boundary
(no routing decisions; reject malformed deposits to FD-03) is a binary gate; the dataset declares GK-08 and
UKDL as parents (extended, not duplicated) and CO-05/CO-03/PM-03/CO-12 as reinforcement targets; and
V-FD-NO-CODE finds zero code fences.

### III.11 Upgrade path

- **v1 (this dataset):** the write-and-reinforcement executor as a rung-3-with-rung-2-verification layer,
  consuming FD-03 deposits and propagating across the mesh with a live-copy read-back.
- **v2 (EXECUTION-mode):** the live-write-fidelity and reinforcement-completeness metrics are computed on
  each write from real disk read-backs and registry checks, so a split-brain or an incomplete reinforcement is
  caught at write time rather than discovered as inert; the idempotency key and mutate-don't-duplicate
  discipline are enforced in code with a vault-wide dedup scan.
- **v3:** the mirror-sync verification is served by a canonical→live parity checker that FD-06 invokes
  structurally, so the live read-back is a call into the existing mirror-parity machinery rather than a
  bespoke read; the reinforcement registrations are driven off the destination taxonomy's reinforcement column
  so a new destination automatically inherits its reinforcement obligations.
- **Deprecation trigger:** if a destination's deposits are durably never consulted after correct writes (a
  home whose trigger, per FD-03's own deprecation trigger, proves useless), FD-06 stops reinforcing that
  destination's deposits into the mesh once FD-03 retires the destination — the executor's reinforcement work
  narrows with the router's taxonomy, so the station never spends propagation effort on a home the router no
  longer offers.

### III.12 Concurrency and the shared-substrate write

FD-06 inherits the same multi-pane reality as FD-01 and FD-03, and it is the station where that reality bites
hardest, because it is the station that actually touches disk on a shared `.git/index` and a shared
`~/.claude` tree. Three hazards arise that a single-pane design would miss, and each is resolved by leaning on
stack machinery rather than a bespoke coordinator. The first is the *concurrent-supersede clobber*: two panes
route improvements to the same deposit and, if both writes land naively, one silently overwrites the other,
losing an improvement and severing a back-reference. FD-06 resolves this by serializing supersedes as a
back-reference chain (III.6 Trace F): each revision appends with a back-link to the revision it supersedes, so
concurrent improvements stack into a legible chain rather than clobbering, exactly the append-only,
never-silent-delete discipline UKDL itself uses. The second is the *unscoped-commit capture*: on a shared
index, an unscoped `git commit` from one pane packages another pane's staged deposit under the wrong message,
the documented pathspec-scoped-commit hazard. FD-06's writes are always pathspec-scoped — a commit that
persists a deposit names exactly the deposit's files in a trailing pathspec clause — so a concurrent pane's
staged files are never swept into this pane's write. The third is the *sibling-absorption race*: a deposit
FD-06 just wrote to a file may already have been committed by a concurrent pane's unscoped add, so a naive
"my file is missing from git status" reaction would wrongly re-write it; FD-06 verifies the deposit's content
at HEAD before assuming a clobber, distinguishing "a sibling committed my content" (fine, exclude from my
pathspec) from "my content was lost" (re-write).

The deeper point is that FD-06 does *not* build a lock manager or a merge engine for any of this. Every
resolution consumes machinery the stack already provides: the append-only back-reference chain (UKDL's law),
pathspec-scoped commits (the commit doctrine), the PM-03 bus for cross-pane visibility (so a pane sees a
sibling's in-flight write and does not duplicate it), and the G2-reviewer-rebase-race discipline (do not
mutate a deposit a reviewer pane is reading). This is the "one system, no parallel systems" discipline the
suite inherits, applied at the write surface: a bespoke FD-06 coordinator would fracture the shared substrate
into per-pane write regimes and destroy the very shared floor whose un-replicability makes the vault a moat.
The only FD-06-specific addition to the shared machinery is that a write's PM-03 publish (Step 5) carries the
deposit's content hash, so a concurrent pane about to write the same content sees the hash on the bus and
short-circuits to the idempotent no-op *before* touching disk, rather than both panes writing and relying on
the destination's dedup to catch it after the fact. This turns the bus into a pre-write dedup channel across
panes, extending the single-pane idempotency key (II.5) into a cross-pane one, so that six to ten panes
distilling against the same rising floor deposit into a single coherent vault rather than a scattering of
per-pane near-duplicates — which is the concurrency form of the reinforcement-completeness invariant, ensuring
the mesh stays coherent not just across *stores* but across *panes*.

### III.13 Why the executor carries the suite's permanence guarantee

A closing synthesis makes explicit why FD-06, quiet and mechanical as it is, is the station where the suite's
core promise is either kept or broken. The suite's promise is *permanent, portable, model-independent
advantage* — a delta captured once and consulted forever, reducing future dependence on the frontier model
that produced it. Every upstream station contributes to that promise but none of them realizes it: FD-02
compiles a good question, FD-00 admits the frontier token, the model answers, FD-01 extracts and classifies
the delta, FD-03 routes and transmutes it — and at the end of all that investment the delta is still only a
*decision to write*, a plan that has reduced no dependence and will reduce none until it is physically,
durably, universally installed. FD-06 is the station that converts the entire upstream investment into a
standing artifact, and it is the *only* station that can void that investment with a silent failure: a
split-brain write voids it (the deposit is inert in the running session), an incomplete reinforcement voids
it (the deposit is conditionally inert across the mesh), a duplicate erodes it (deposit precision falls), a
silent delete severs it (provenance is lost), an unverified report hides all of these behind a false
`confirmed`. The permanence guarantee is not made by the classifier or the router; it is made — or broken —
by whether the executor's write reached every consulted location, exactly once, verifiably, without
destroying history.

This is why FD-06's discipline is the most physical and the least interpretive in the suite. FD-01's
correctness is a measured accuracy against a hand-labelled set; FD-03's is a consultation rate that arrives
later; both are judgments graded against outcomes. FD-06's correctness is a filesystem fact: the deposit is
present at the live consulted location and reachable across the reinforcement set, or it is not, and a
read-back settles it now. The suite is fortunate that its last, load-bearing link is the one whose success is
directly observable, and FD-06's design spends that fortune deliberately — it verifies rather than trusts,
reads back rather than assumes, and reports `confirmed` only on observation. In doing so it makes the suite's
grandest claim (the advantage is now permanent) the suite's most honest one, because it is the claim backed by
a direct measurement rather than a chain of inference. A distillation suite whose extraction and routing were
flawless but whose writeback trusted its own success would be a suite that quietly leaked its advantage into
canonical-only, mesh-partial, unverified writes — finding gold, deciding exactly where to keep it, and then
setting it down without checking that it landed in the vault. FD-06 is the discipline of checking that it
landed, everywhere it must land, forever — which is the whole difference between a vault that compounds and a
vault that merely records the intention to compound.
