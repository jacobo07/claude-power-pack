# Graphify — GK-05 — Graph Query Runtime, Query Planner & Coordinate Resolver

> The kernel's ask-before-you-explore surface. Given an intent, GK-05 answers *from the graph* —
> "where is X," "what must I load to work on X," "what governs this," "what traps apply" — returning
> the minimum useful set of coordinates rather than a bulk read. Its resolver turns a fuzzy human
> intent ("llévame al motor de vídeo," "the benchmark for Context VM," "the dataset that governs
> Route Packs") into a precise coordinate *without a filename*. And its planner learns, over time,
> which queries are cheapest and most likely to succeed, so navigation gets faster the more the
> kernel is used.
>
> EXTEND, not NEW: `parts/sleepy/knowledge-graph.md` already defines the navigation protocol
> (read INDEX first, follow wikilinks, max 10 nodes, hot spots, stale-fallback); `jit_skill_loader`
> already decides *what to load by trigger relevance* at tiered depth with a circuit breaker; CO-03
> already sequences a cheapest-first cascade. GK-05 unifies these into one query runtime that
> returns coordinates. Honest (CO-10): the runtime returns *what the graph knows*; a miss falls
> through to exploration, which writes back (GK-08) so the miss is paid once — the runtime never
> fabricates a coordinate to avoid admitting it does not know.

---

## Part I — Querying the Graph

### I.1 The query surface

GK-05 answers a bounded set of navigation questions, each returning coordinates, not text: *locate*
(where is the resource matching this intent), *scope* (what is the minimum I must load to act on
it), *risk* (what traps / should-never-load-with / hot-spots apply), *govern* (what decisions and
contracts condition it), *validate* (what tests cover it), *reuse* (what asset already answers
this), and *relate* (what depends on it / what it depends on). Each answer is a small set of
coordinates with their summaries — the raw material the route compiler (GK-06) assembles into a
context pack. The runtime's contract is *minimality*: it returns the fewest coordinates that
satisfy the question, never a broad dump, because a query that returns too much has reintroduced
the exploration it replaces.

### I.2 The Coordinate Resolver

The resolver is the runtime's most distinctive capability: **navigation by identity, not filename.**
A caller need not know where the video engine lives or what its file is called — "llévame al motor
de vídeo" resolves through semantic identity (GK-01) and canonicalization (GK-02) to the engine's
coordinate, which knows its current binding, its edges, and its minimal context. This is what
"navego coordenadas, no rutas" means operationally: the resolver decouples *what you want* from
*where it happens to be*. It succeeds where grep fails — when the caller knows the concept but not
the string — and it returns the coordinate *with its trust class*, so an inferred match is flagged
for verification rather than acted on blind.

### I.3 The Query Planner

Not every path to an answer costs the same. The planner decides *how* to answer a query cheapest: a
direct identity match (rung-1, near-zero), a canonical-alias resolution, a relationship traversal, a
semantic-DNA match, or — last — a fall-through to genuine exploration. It orders these exactly as
CO-03 orders model rungs: cheapest first, stop at the first that satisfies the query to a confidence
threshold. The planner is the query-time expression of CO-03's cascade, specialized for *finding*
rather than *reasoning*: it never traverses an expensive path when a cheap one resolves, and it
never explores when the graph already holds the answer.

---

## Part II — Learning and Optimization

### II.1 Queries improve with use

The planner is not static — it learns which queries are cheap and which are reliable. When a query
class repeatedly resolves at rung-1, the planner *starts* there next time; when a class repeatedly
falls through to exploration, that is a signal the graph is missing a node or edge (surfaced to
GK-09 as a blind spot, and to GK-08 as a writeback target). Query success rate, tokens-to-answer,
and time-to-correct-coordinate are recorded per class, so the runtime's own performance is a
measured, improving quantity rather than a hope. This is CO-01's ROI discipline applied to
navigation: a query that reliably saves exploration earns its keep; one that reliably fails is a
gap to close.

### II.2 The minimality gate

Every query answer passes a minimality gate before it is returned: does it contain a coordinate the
task does not need? A query that returns ten coordinates when three suffice has inflated the eventual
context pack and is trimmed. The gate is the runtime's defense of the compression invariant (GK-00):
the graph exists to *reduce* what a task loads, so a query that returns too much is a failure even
if every coordinate it returns is correct. Minimality is measured (average query result size, average
resulting pack size) and trended down over time — the runtime is expected to return *less* as it
learns what tasks actually use.

### II.3 Confidence-aware answers

A query answer inherits the confidence of the coordinates and edges it traversed (GK-01/GK-04). A
high-confidence answer — exact identity match on fresh coordinates — is returned as authoritative. A
low-confidence answer — inferred match, or a traversal through a stale edge — is returned as a *lead
requiring verification*, explicitly labeled, so the caller re-checks against source before betting
work on it (HR-PREMISE-001). The runtime never collapses this distinction: it would rather return
"here is a probable coordinate, verify it" than a false-confident answer that sends a task down the
wrong path.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **Over-broad answer.** A query returns more coordinates than the task needs, inflating the pack.
  Detection: the minimality gate + GK-09's average-pack-size trend; a growing result size is
  investigated. Bias toward under-return-and-expand over over-return.
- **False-confident resolution.** The resolver returns an inferred match as authoritative and the
  task acts on the wrong resource. Detection: post-hoc, a route whose target failed verification →
  the resolver's confidence for that class is lowered; fail toward "verify" labeling.
- **Silent miss.** The runtime returns nothing and the task explores without recording the gap.
  Detection: every miss is logged as a blind-spot candidate (GK-09) and a writeback target (GK-08);
  a miss that produced no writeback is the bug (the sibling of the write-without-read lesson).
- **Planner over-fitting.** The planner starts a query class at a cheap rung that then repeatedly
  fails, thrashing. Detection: escalation-rate per class; a class that starts cheap but always
  escalates has its start-rung raised (the CO-03 re-grade discipline).

### III.2 Rollback protocol

GK-05 unifies existing surfaces, so rollback degrades to them. (1) Disable the learning planner and
use a fixed cheapest-first order (CO-03's static cascade) — the runtime stops improving but still
answers. (2) Disable the resolver's semantic matching and fall back to `jit_skill_loader` trigger
matching + FTS5 lexical search (today's baseline) — navigation by string, not identity. (3) Fully
disabled, the runtime reverts to the sleepy nav protocol as advisory doctrine. Fail-safe: "fall
through to exploration and write back," never "fabricate a coordinate to avoid the miss."

### III.3 Integration contract

- **sleepy nav doctrine / jit_skill_loader / CO-03 (parents)** — the navigation protocol, the
  trigger-relevance loader, and the cheapest-first cascade, unified into one coordinate-returning
  runtime.
- **GK-01 / GK-02** — the resolver navigates by canonical identity; a query returns coordinates.
- **GK-04** — queries traverse typed edges, weighting by confidence.
- **GK-06** — the route compiler consumes query answers as the raw coordinates it assembles into a
  pack; GK-05 finds, GK-06 assembles.
- **GK-08 / GK-09** — misses become writeback targets and blind-spot signals; query performance is
  observatory telemetry.
- **CO-04 / CO-05** — answers are WARM pointers; a resolved coordinate is a CO-05 asset; the planner's
  cheap rungs are CO-05 reads.

### III.4 Anti-patterns (forbidden)

- **Returning a bulk result.** A query that dumps coordinates has reintroduced exploration.
- **Fabricating a coordinate on a miss.** Fall through and write back; never guess to look complete.
- **Serving an inferred match as authoritative.** Label leads as leads; let verification confirm.
- **Exploring when the graph holds the answer.** The runtime is consulted first, by contract (GK-00).
- **A miss with no writeback.** An un-recorded gap is paid again next time.

---

### GK-05 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Answers navigation queries with the minimum useful set of coordinates | Query routed through the runtime | A minimal answer for a resource the graph has not mapped (falls through) |
| The resolver navigates by identity, not filename ("llévame al motor de vídeo") | Coordinate exists + canonicalized | Resolution of an intent with no matching coordinate (miss → writeback) |
| The planner answers cheapest-first and learns which queries are cheap/reliable | Always | Zero misses — a miss falls through to exploration and is recorded |
| Answers carry confidence; low-confidence answers are labeled leads to verify | Always | That a returned coordinate is always current/correct |
| Rollback degrades to lexical search + advisory nav protocol | On misbehavior | — |

**Guarantee level (honest):** GK-05 is a *navigation-resolution* layer (level-2 class,
cheapest-first) — it makes finding cheap and identity-based when the graph holds the answer; it
cannot guarantee a hit for an unmapped resource, and a miss falls through to exploration that writes
back so it is paid once. Parents: **sleepy nav doctrine + jit_skill_loader + CO-03**.
*Sealed under SCS C69.*
