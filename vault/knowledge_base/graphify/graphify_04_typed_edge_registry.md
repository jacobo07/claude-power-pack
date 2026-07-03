# Graphify — GK-04 — Typed Relationship Edge Registry (Evidence · Confidence · Lineage)

> The kernel's relationships as first-class citizens. A graph is only as valuable as its edges: a
> pile of nodes with no typed relations is a directory with extra steps. GK-04 makes every
> relationship a governed record — not just "A relates to B," but *which* relation (governed-by,
> extends, broke-because-of, should-never-load-with…), *why* the graph believes it, *how much* it
> believes it, and *whether it may have gone stale*. Edges are what turn location into navigation:
> they are the roads a route (GK-06) travels.
>
> EXTEND, not NEW: `audit_cache.py` already extracts exactly one typed edge — `depends_on`, by
> resolving imports and wikilinks to project-relative paths — and already carries a freshness hash.
> GK-04 is that single edge type generalized into a registry of ~18, each carrying the evidence and
> confidence `depends_on` currently omits. It reuses PM-03's finding model (a claim + its evidence
> + a freshness anchor + the source that published it) at edge granularity. Honest (CO-10): an edge
> is a **stored assertion with an evidence pointer and a confidence class**, re-verified against
> source when stale — it is never a guaranteed live truth, and an inferred edge is explicitly weaker
> than an observed one.

---

## Part I — Edges as Governed Records

### I.1 The edge vocabulary

GK-04 governs the relationship types the Owner ontology names, grouped by what they let a route
reason about: **structural** (depends-on, imports, owns, requires), **architectural** (extends,
supersedes, implements, governed-by), **provenance** (generated-by, validated-by), **causal**
(broke-because-of, fixed-by), **advisory** (conflicts-with, related-to, used-by), and
**operational co-load** (should-load-before, should-never-load-with). The last pair is the
highest-leverage novelty: an edge that says "loading X without Y is a known trap" or "these two
must never share a context pack" encodes hard-won operational knowledge directly into the graph, so
a route inherits it automatically rather than a session re-learning it. The vocabulary is
extensible — GK-04 mints a new edge type only when a relationship recurs and no existing type fits.

### I.2 Every edge carries evidence

The discipline that separates GK-04 from a wikilink dump: **no edge without evidence.** Each edge
records *why* it exists — the file:line of the import, the dataset line declaring a parent, the
commit that links a fix to a bug, the UKDL entry asserting a should-never-load-with. Evidence is a
pointer, not a copy, so the edge stays WARM-cheap; but it means any consumer can audit the claim.
An edge whose evidence no longer resolves (the import was deleted, the asserting line removed) is a
*broken* edge, detected by GK-07 and demoted, not silently carried. This is the primary-source-wins
rule at edge granularity: the relationship is a hypothesis until its evidence is checked.

### I.3 Confidence as a first-class field

Not all edges are equally trustworthy, and GK-04 grades them. An **observed** edge (a resolved
import, an explicit declaration) is high confidence — the graph saw it directly. An **inferred**
edge (a cross-repo equivalence, a "these probably relate" from shared semantic DNA) is medium and
flagged. A **stale** edge (evidence anchor no longer matches) is a lead, not a fact. A route (GK-06)
weighs edge confidence when it plans: it travels high-confidence edges freely and treats
low-confidence ones as *candidates to verify* before betting a context pack on them. Confidence is
what lets the graph be aggressive where it is sure and cautious where it is guessing — the honest
alternative to treating every edge as equally true.

---

## Part II — The Registry and Its Guarantees

### II.1 Bidirectional, queryable, minimal

The registry stores edges so both directions are cheap: "what does X depend on" and "what depends on
X" are one lookup each, because navigation needs both (a route forward to load, a blast-radius query
backward to assess risk). Edges return as pointers between coordinates, so traversing the graph is
near-zero context cost until a node is paged to full detail. The registry composes the existing
edge sources — `audit_cache.depends_on`, kobi_graphify's `DEPENDENCY_GRAPH.md` and
`CLASS_HIERARCHY.md` views, the wikilinks — into one typed surface, rather than the disjoint
representations that exist today.

### II.2 Lineage and provenance

GK-04 owns the *history* of relationships, not just their present. A **lineage** chain records how
a resource evolved — this decision superseded that one, this engine extends that predecessor — so a
route can answer "why is it this way" by walking the chain rather than re-deriving the rationale
(the Decision-Librarian use case, GK-11). **Provenance** records where a resource *came from* — the
prompt that generated it, the workflow that produced it, the session that introduced it — so an
asset is traceable to its origin. Lineage and provenance are what make the graph a *memory* rather
than a snapshot: they preserve the "how we got here" that raw structure discards, at the cost of a
few extra edges rather than a re-investigation.

### II.3 Confidence networks and propagation

Confidence is not isolated per edge; it composes. A route built entirely on observed, fresh edges
carries high route confidence (GK-06); a route that must traverse an inferred or stale edge inherits
that weakness. GK-04 exposes this so the route compiler and the observatory (GK-09) can reason about
*chains* of trust, not just individual links — a single stale edge in a critical path is a visible
risk, not a hidden one. Confidence propagates conservatively: a chain is only as strong as its
weakest edge, so the graph never launders a low-confidence inference into a high-confidence route by
burying it among strong links.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **Phantom edge.** An edge whose evidence no longer exists (deleted import, removed declaration).
  Detection: GK-07 re-checks evidence anchors on scan; an unresolvable evidence pointer demotes the
  edge to broken. Fail toward drop-the-edge, never carry-it-blind.
- **Confidence inflation.** An inferred edge treated as observed. Detection: the registry records
  edge provenance (observed vs inferred); a route that acted on an inferred edge as if certain, and
  failed, flags the inflation → the inference threshold tightens.
- **Contradictory edges.** X supersedes Y and Y supersedes X; A should-load-before B and B before
  A. Detection: GK-07 integrity audits for contradiction cycles → surfaced, not silently resolved.
- **Edge bloat.** Every faint relation minted as an edge, drowning the strong ones. Detection: edges
  with zero route traversals over a long window are GC'd (CO-06); minting is gated on recurrence.

### III.2 Rollback protocol

GK-04 generalizes one working edge type, so rollback is safe. (1) Disable the widened edge
vocabulary and revert to `audit_cache.depends_on` alone (today's baseline) — the graph loses typed
relationships but keeps import-dependency. (2) Disable confidence grading and treat all edges as
advisory, verifying against source before any action (the pre-kernel discipline). (3) Disable
lineage/provenance, flattening the graph to present-state. Edge *content* never rolls back — stored
relationships persist; only the typing and grading pause. Fail-safe: "verify every relationship
against source," never "trust a stale edge."

### III.3 Integration contract

- **audit_cache (parent)** — `depends_on` is the seed edge type; its hash becomes the edge freshness
  anchor.
- **GK-01 / GK-02** — edges connect coordinates; canonicalization ensures an edge points at one
  identity, not one of its aliases.
- **GK-03** — the compiler seeds edges from what it observes; GK-04 governs their evidence and
  confidence.
- **GK-06** — the route compiler travels edges, weighting by confidence; should-never-load-with
  edges directly constrain pack assembly.
- **GK-07** — audits edge evidence, contradiction, and freshness; broken/contradictory edges are its
  findings.
- **PM-03 / CO-10** — reuses the finding model (claim + evidence + anchor); confidence classes are
  CO-10's honesty applied to relationships.

### III.4 Anti-patterns (forbidden)

- **An edge without evidence.** A relationship the graph cannot justify is a guess, not a road.
- **Treating inferred and observed edges alike.** Confidence must be graded and must propagate.
- **Laundering a weak edge into a strong route.** A chain is only as strong as its weakest link.
- **Carrying a phantom edge.** An edge whose evidence is gone is demoted, not served.
- **Minting an edge for every faint resemblance.** Edge bloat drowns the relationships that matter.

---

### GK-04 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Every edge is typed and carries an evidence pointer to why it exists | Edge minted by compiler or writeback | An edge whose evidence was never captured (dropped, not guessed) |
| Edges are graded observed / inferred / stale; a route weights by confidence | Always | That an inferred edge is as true as an observed one |
| Bidirectional lookup — dependencies and blast-radius are each one query | Always | — |
| Lineage/provenance preserve "why it is this way" and "where it came from" | When the history was captured | Reconstructing history the graph never recorded |
| Rollback reverts to import-dependency-only without losing stored edges | On misbehavior | — |

**Guarantee level (honest):** GK-04 is a *relationship-governance* layer (level-2 class,
deterministic lookup) — it makes relations navigable, auditable, and confidence-graded; an edge is
a stored assertion re-verified against source when stale, and an inferred edge is honestly weaker
than an observed one. Parent: **audit_cache.depends_on**, generalized. *Sealed under SCS C69.*
