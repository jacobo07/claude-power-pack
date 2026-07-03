# Graphify — GK-06 — Route Compiler, Minimal Context Pack & Route Cache

> The kernel's payoff engine. Query (GK-05) *finds* the relevant coordinates; GK-06 *compiles*
> them into a route — an ordered, minimal, actionable plan — and materializes that route as a
> **Minimal Context Pack**: the smallest set of nodes, decisions, contracts, traps, assets, and
> validations a task needs to execute without exploring. A route is not a list of files; it is a
> cognitive path that says where to start, what to load first, what to ignore, what to reuse, and
> what to verify. It is the artifact that turns "read 50 files" into "load 5 coordinates."
>
> EXTEND, not NEW: CO-03's cascade already sequences cheapest-first *model* selection; CO-04's
> Hot/Warm tiers already hold the content a pack would draw from; the sleepy nav protocol already
> caps at "max 10 nodes." GK-06 is those disciplines fused into a *compiler* that emits a pack as a
> first-class object, with a cache so frequent routes are not recompiled. Honest (CO-10): a route
> is *compiled from the graph's current state*; it carries a confidence and a freshness verdict, and
> a stale route is re-validated (GK-07) before reuse — it is never replayed blind.

---

## Part I — The Route and the Pack

### I.1 A route is a cognitive path, not a file list

The defining property: a route encodes *order and sufficiency*, not just membership. It answers
where to begin (the entry coordinate), what to load first vs defer, what to deliberately not load
(the should-never-load-with edges, the irrelevant neighbors), what prior knowledge to reuse instead
of re-deriving (CO-05 assets), which decisions and contracts constrain the work, which traps to
avoid, and which validations gate "done." A file list leaves all of that reasoning to the executing
agent; a route has already done it. This is the difference between handing someone a pile of
documents and handing them a briefing — the briefing is smaller *and* more actionable, which is the
whole thesis of the kernel.

### I.2 The Minimal Context Pack

The pack is the route's materialization — the actual content loaded HOT (CO-04) for execution. Its
governing law is *minimality with sufficiency*: the smallest pack that still lets the task complete
to its done-gate. It is assembled from coordinate *summaries* (not full resources) plus the specific
decisions, contracts, traps, and assets the route names — so a task that would have cost a 50-file
read costs a handful of summaries and a few precise excerpts. The pack is structured into the sub-
packs the Owner named — node, scope, decision, risk, asset, validation, done-gate — so an executing
agent (or a Graph-Gated execution, GK-12) has each dimension explicitly, not buried in prose. The
pack's size is measured and trended down; a pack that grows toward a bulk read has failed.

### I.3 Route confidence and cost

Every compiled route carries two honest numbers. **Confidence** propagates from the coordinates and
edges it traversed (GK-01/GK-04): a route built on fresh, observed, high-confidence links is
authoritative; one that had to traverse an inferred or stale edge inherits that weakness and is
labeled "verify before betting on this." **Cost** is the estimated token/latency price of loading
the pack, computed before assembly so the compiler can prefer a cheaper route among equivalent ones.
A route that is cheap *and* high-confidence is preferred; a route that is cheap but low-confidence is
returned with its caveat, never laundered into false certainty. These numbers are what let the
executing layer decide whether to trust the route or verify first.

---

## Part II — Compilation, Caching, Optimization

### II.1 Compilation: from coordinates to a minimal path

The compiler takes GK-05's query answer (a set of relevant coordinates) and reduces it to a path:
it orders the coordinates by dependency and load-priority, drops those the task will not use, folds
in the governing decisions/contracts/traps from their edges, attaches the reusable assets that
answer sub-problems (so the task reuses rather than re-derives), and names the validations that gate
completion. Reduction is the active verb: the compiler's success is measured by how much it *removes*
from the query answer while keeping the task completable. It is CO-03's cheapest-first cascade
applied to *pack assembly* — the cheapest sufficient pack wins.

### II.2 The Route Cache

Frequent routes should not be recompiled every time. GK-06 caches compiled routes as reusable assets
(CO-05), keyed by the intent-class and the graph state they were compiled against. A cached route is
a near-instant answer for a recurring task — "set up a deploy," "add a KobiiCraft command," "find and
load the video pipeline." The cache's discipline is freshness-by-anchor (the CO-05 / audit_cache
model): a cached route is valid only while the coordinates and edges it references are unchanged; on
any drift, GK-07 invalidates it and the next request recompiles. The cache decides *when* to cache (a
route used repeatedly), *when* to invalidate (referenced-node drift), *when* to merge (near-identical
routes), and *when* to evict (a route unused over a long window, via CO-06 GC).

### II.3 Route learning

Routes improve because execution reports back (GK-08). After a task runs, the writeback records which
pack coordinates were *actually used*, which were dead weight, which were *missing* (the task had to
explore for them anyway), and which traps appeared that the route did not warn about. The compiler
folds this in: unused coordinates are dropped from that route class's next compilation, missing ones
are added, and the pack shrinks toward exactly what tasks of that class need. This is the mechanism
by which average pack size falls over time — the compiler learns the true working set of each task
class from observed execution, not from a guess.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **Inflated pack.** The compiler includes coordinates the task never uses. Detection: writeback
  reports unused pack members; a route class with persistent dead weight is trimmed. Measured by
  average-pack-size (GK-09), trended down.
- **Under-packed route.** The pack omits something the task needs, forcing mid-task exploration.
  Detection: writeback reports "had to explore for X"; X is added to the route class. Fail toward
  a slightly-larger pack over a task-blocking omission — but both are trended.
- **Stale route replayed.** A cached route is reused after its coordinates drifted. Detection: GK-07
  invalidates cache entries on referenced-node drift; a route served without a freshness verdict is
  the bug. Fail toward recompile.
- **Low-confidence route trusted.** A route traversing stale/inferred edges is acted on as certain.
  Detection: route confidence is attached and surfaced; a failed high-stakes route on a
  low-confidence path lowers that path's confidence and forces verify-first next time.

### III.2 Rollback protocol

GK-06 fuses existing disciplines, so rollback degrades to them. (1) Disable the route cache — every
request recompiles fresh (slower, never stale). (2) Disable route learning — the compiler uses a
fixed inclusion policy rather than an execution-tuned one (larger packs, but correct). (3) Fully
disabled, execution reverts to GK-05 query answers loaded directly, or to the sleepy "max 10 nodes"
advisory. The compiler's *outputs* (cached routes) are never destroyed by rollback — only active
caching/learning pauses. Fail-safe: "recompile fresh, or load the raw query answer," never "replay a
stale route."

### III.3 Integration contract

- **GK-05 (upstream)** — supplies the coordinates; GK-06 reduces them to a minimal path. GK-05
  finds, GK-06 assembles.
- **CO-03 / CO-04 (parents)** — cheapest-first assembly is CO-03's cascade; the pack lives in CO-04's
  Hot tier and is bounded by CO-00's ceiling.
- **CO-05** — cached routes and reused assets are CO-05 institutional memory with freshness.
- **GK-04** — should-never-load-with and governed-by edges directly shape pack inclusion/exclusion.
- **GK-07** — invalidates stale routes; supplies the freshness verdict a route carries.
- **GK-08 / GK-09** — execution writeback tunes routes; pack size and route reuse are observatory
  metrics.
- **GK-12** — Graph-Gated execution consumes the sub-packs (node/scope/decision/risk/asset/
  validation/done-gate) as its admission checklist.

### III.4 Anti-patterns (forbidden)

- **A pack that approaches a bulk read.** Violates the compression invariant; the route failed.
- **Replaying a cached route without a freshness check.** The stale-route trap.
- **Laundering a low-confidence path into a confident route.** Confidence propagates honestly.
- **Ignoring writeback.** A compiler that does not learn from what tasks actually used cannot shrink.
- **Emitting a file list instead of a path.** A list defers the reasoning the route is meant to do.

---

### GK-06 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Compiles query coordinates into an ordered, minimal, actionable route | Query answer available (GK-05) | A route for an intent the graph cannot resolve (falls through to exploration) |
| Materializes a Minimal Context Pack (node/scope/decision/risk/asset/validation/done-gate) | Always | A pack smaller than the task's true working set — sufficiency is preserved |
| Every route carries confidence + cost; low-confidence routes are labeled verify-first | Always | That a route is always current — stale routes are re-validated (GK-07) |
| Frequent routes are cached and invalidated on referenced-node drift | Route recurs; anchors hold | Serving a stale cached route (invalidated on drift) |
| Rollback degrades to fresh recompilation or raw query answers | On misbehavior | — |

**Guarantee level (honest):** GK-06 is a *route-assembly* layer (level-2 class, cheapest-first) —
it turns found coordinates into the minimal pack that completes a task, learns the true working set
from execution, and carries honest confidence/cost; a stale route is re-validated, never replayed
blind. Parents: **CO-03 cascade + CO-04 tiers + sleepy nav**. *Sealed under SCS C71.*
