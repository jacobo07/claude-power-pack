# Graphify — GK-08 — Knowledge Writeback Engine (Session → Graph)

> The kernel's compounding loop. A navigation kernel that only *reads* the graph is a static map;
> the graph gets better only if every session *writes back* what it discovered. GK-08 is the
> write-half of the Intent→…→Writeback sequence: at close, a session records the coordinates it
> found, the relations it discovered, the decisions it made, the assets it produced, the bugs and
> traps it hit, and — critically — the knowledge that *must not be re-investigated*. Every session
> enriches the graph; the graph compounds; future navigation gets cheaper. Without this engine the
> graph decays toward its initial snapshot and the kernel stops improving.
>
> EXTEND, not NEW: PM-03 (Shared Findings Bus) already publishes findings and runs the Cross-Pane
> Commit Protocol ("publish what changed, what you learned, what must not be repeated"); the
> compound-learnings and NEVER_AGAIN pipelines already distill durable lessons. GK-08 is the Commit
> Protocol repointed from *the pane's Bus* to *the graph's coordinate/edge registry*: a published
> finding becomes a node or edge, not just a message. Honest (CO-10): writeback happens at the
> **close boundary** (or explicit checkpoints), writing files on disk — it is not a live stream that
> mutates the graph mid-turn, and what it writes is verified before it becomes an authoritative
> coordinate.

---

## Part I — What Gets Written Back

### I.1 The discovery ledger

At close, a session has learned things the graph did not hold, and GK-08 captures them as graph
mutations: **new coordinates** (a resource the session located that was unmapped), **new edges** (a
relation it discovered — this governs that, this broke because of that), **rebinds** (a coordinate
whose true locus it corrected), **decisions** (an Owner-locked ruling, so no future session
re-litigates it — the sibling of "check sibling commits before refactor"), **assets** (a reusable
output — a template, a schema, a script — registered for CO-05 reuse), **bugs and traps** (a failure
and its root cause, so the next route through that area is pre-warned), and **negative knowledge**
(the explicit "this was investigated, here is the answer, do not re-investigate"). The last is the
highest-value class: it is what stops the ecosystem from re-paying for a conclusion it already
reached.

### I.2 Writeback is verified, not raw

A session's raw impressions are not authoritative — the Reality Contract forbids storing a
hypothesis as a fact. GK-08 applies the CO-05 verify gate: a discovery becomes an *authoritative*
coordinate/edge only after it clears verification (observed to work, confirmed against source, or
recurred past the compound-learnings signal threshold). Unverified discoveries are written at
**provisional/inferred** trust (GK-01/GK-04), navigable as leads but flagged for confirmation. This
is what keeps writeback from poisoning the graph: an eager session cannot promote a wrong conclusion
to a confident coordinate that CO-03's cheap rungs then serve to everyone. The gate is the
difference between a graph that compounds *knowledge* and one that compounds *noise*.

### I.3 The negative-knowledge contract

The single most economically important thing a session can write back is *what not to do again*: the
dead-end explored, the file that turned out to be wrong, the premise that proved false, the trap that
cost tokens. GK-08 structures these as first-class negative-knowledge nodes and should-never /
broke-because-of edges, so a future route *inherits the warning* rather than re-discovering the
hazard. This is the compound-learnings / NEVER_AGAIN discipline made navigable: the lesson is not
buried in a session log; it is an edge on the coordinate the next task will touch. A trap recorded
once should never be paid for twice.

---

## Part II — The Writeback Mechanics

### II.1 The close-boundary commit

GK-08 fires at the honest coordination point PM-03 already uses: the session close (and explicit
checkpoints like `/kclear`). A session that made discoveries but closed without a writeback is
flagged — a silent close is the bug, the sibling of the write-without-read lesson: a discovery not
committed is documentation of nothing, paid for again next time. The commit is append-structured for
volatile knowledge (findings, decisions accrue) and anchor-idempotent for coordinate updates (a
rebind tagged with its HEAD; a racing writeback detects the newer anchor and yields rather than
clobbering), reusing PM-01's concurrent-writer discipline exactly.

### II.2 From finding to graph mutation

PM-03 publishes a finding as a message on the Bus; GK-08 additionally *structures* it into the
graph. "Function X is dead" becomes a node annotation + a should-not-call edge; "the real signature
is Y not the assumed Z" becomes a rebind + a corrected contract edge; "this test covers that module"
becomes a validated-by edge. The Bus remains the *hot* pane-to-pane layer (fast, recent); the graph
is the *durable, navigable* layer the writeback populates. GK-08 is the bridge: it turns the Bus's
stream of findings into the graph's permanent structure, so a finding published today is a coordinate
navigable next month.

### II.3 Feeding the learners

Writeback is also the signal source for the engines that improve navigation. It tells GK-06 which
route coordinates were *actually used* vs dead weight (so routes shrink), GK-05 which queries *missed*
(so blind spots are found), GK-07 which nodes *drifted* during the session (so freshness stays
current), and GK-09 which assets got *reused* (so ROI is measured). A session's writeback is
therefore not just data storage — it is the feedback that makes every downstream engine learn. A
kernel whose sessions do not write back is a kernel that cannot improve; GK-08 is the loop that makes
"each session enriches the graph" literally true.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **Silent close.** A session makes edits/discoveries and closes without writeback. Detection: the
  close-boundary gate compares session activity to committed deltas; edits with no writeback are
  flagged. Fail toward "prompt the writeback," never toward silent loss.
- **Poisoned writeback.** An unverified conclusion promoted to an authoritative coordinate.
  Detection: the verify gate blocks promotion; a coordinate whose later retrievals fail is
  quarantined and its writeback source flagged (CO-05 poisoned-asset discipline).
- **Duplicate writeback.** The same finding written every checkpoint, bloating the graph. Detection:
  dedup on claim+artifact identity (PM-03 model), not text; a finding already a coordinate is updated,
  not re-minted.
- **Concurrent-writer clobber.** Two panes write back against the same coordinate. Detection: anchor-
  idempotent commit — the older writeback yields; append sections never clobber by construction
  (PM-01 discipline).

### III.2 Rollback protocol

GK-08 extends the proven Commit Protocol, so rollback degrades to it with zero loss. (1) Disable
graph-structuring and revert to PM-03's message-only Bus + compound-learnings distillation (today's
baseline) — findings still persist, they just are not structured into coordinates/edges. (2) Make
writeback provisional-only (no auto-promotion to authoritative) while the verify gate is audited. (3)
Fully disabled, sessions record to the Bus/vault as they do now; the graph stops compounding but
loses nothing already stored. Fail-safe: "record to the durable Bus/vault," never "promote an
unverified conclusion."

### III.3 Integration contract

- **PM-03 (parent)** — the Cross-Pane Commit Protocol and finding model, repointed to write graph
  structure; the Bus is the hot layer, the graph the durable one.
- **GK-01 / GK-04** — writeback mints coordinates and edges; canonicalized (GK-02) and verified before
  authoritative.
- **CO-05** — the verify gate and asset registration; a written-back asset is CO-05 institutional
  memory.
- **GK-05 / GK-06 / GK-07 / GK-09** — writeback is the feedback that tunes queries, shrinks routes,
  refreshes freshness, and measures ROI.
- **compound-learnings / NEVER_AGAIN** — the durable session-end pipelines; negative knowledge feeds
  both and the graph.
- **`/kclaude` `/compact` `/kclear` `/loop`** — writeback at close/checkpoint; a loop writes back new
  findings once, not re-publishing per iteration (the Bus-spam anti-pattern).

### III.4 Anti-patterns (forbidden)

- **Closing with discoveries uncommitted.** A finding not written back is paid for again.
- **Promoting an unverified conclusion to an authoritative coordinate.** The graph-poisoning path.
- **Re-writing the same finding every checkpoint.** Dedup on identity; the graph is not a log.
- **Discarding negative knowledge.** "What not to do again" is the highest-value writeback.
- **Clobbering a concurrent writeback.** Anchor-idempotent commit; the older write yields.

---

### GK-08 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| A session's discoveries (coordinates, edges, decisions, assets, negative knowledge) are written to the graph at close | Close-boundary commit runs | Capture from a session that closes silently (flagged, not silently covered) |
| Discoveries are verified before becoming authoritative; unverified ones are provisional leads | Always | That every impression is stored as fact — the verify gate gates promotion |
| Negative knowledge ("do not re-investigate") becomes a navigable warning on the coordinate | Always | — |
| Writeback feeds the learners (routes shrink, blind spots surface, freshness updates, ROI measures) | Always | Improvement without writeback — a non-writing session cannot compound |
| Rollback degrades to message-only Bus + distillation without losing stored knowledge | On misbehavior | — |

**Guarantee level (honest):** GK-08 is a *knowledge-compounding* layer (level-2 class,
close-boundary) — it turns each session's verified discoveries into durable graph structure so
navigation compounds; it writes at boundaries on disk, not live mid-turn, and gates promotion on
verification so writeback compounds knowledge, not noise. Parent: **PM-03 Commit Protocol**.
*Sealed under SCS C71.*
