# Graphify — GK-02 — Semantic Identity & Canonicalization Layer

> The kernel's disambiguator. The same concept is named ten different ways across a mature
> ecosystem — "Context VM," "CO-04," "context virtual memory," "the tiered memory," "hot/warm
> cold" — and each spelling is a coordinate the graph could mint separately, fracturing one
> resource into ten half-known ghosts. GK-02 resolves aliases to a single **canonical identity**
> so a coordinate (GK-01) addresses *one* thing, not one of its many surface names. Without this
> layer the coordinate system is a pile of near-duplicates; with it, it is a clean address space.
>
> EXTEND, not NEW principle: this is CO-05's "never reason the same thing twice" applied to
> *identity* rather than *conclusions* — the ecosystem must never *represent* the same thing
> twice. It reuses the dedup-by-identity discipline PM-03 built for findings (dedup on claim +
> artifact, not surface text) and the signal-threshold model of compound-learnings. Honest
> (CO-10): canonicalization is **evidence-gated merging** — two names collapse to one only when
> the evidence supports equivalence; an uncertain merge is *proposed*, not silently applied, so
> the layer can never erase a genuinely-distinct resource by over-collapsing.

---

## Part I — The Identity Problem

### I.1 Aliases, synonyms, and the fracture they cause

An alias is any surface form that denotes a resource other than its canonical name: an ID
("CO-04"), a prose label ("the context tiers"), a filename stem ("context_virtual_memory"), a
historical name from before a rename, a cross-repo equivalent. Left unresolved, each alias becomes
its own coordinate, and the graph fractures: a route asking about "the tiered memory" reaches a
thin coordinate that does not know the edges, decisions, and bugs recorded against "CO-04." The
resource is *known ten times, badly*, instead of *once, completely*. GK-02's job is to detect that
these ten surface forms denote one identity and bind them to a single canonical coordinate, so all
accumulated knowledge concentrates on one address.

### I.2 Canonical identity vs surface form

The layer maintains, for every resource, one **canonical identity** and a set of **known surface
forms** that resolve to it. The canonical identity is the ontology's preferred name (GK-01's
semantic-identity field); the surface forms are every alias the graph has observed, each with the
evidence that links it (co-location, shared edges, explicit "aka" in a dataset, a rename recorded
in git). Resolution (GK-05) accepts any surface form and returns the canonical coordinate, so the
caller need not know the "official" name. This is what makes navigation robust to how a human or
an agent *happens* to phrase the intent — the alias graph absorbs the phrasing variance that grep
cannot.

### I.3 Equivalence is evidence-gated, never assumed

The dangerous failure of any canonicalizer is over-collapsing — merging two resources that merely
*resemble* each other, erasing a real distinction. GK-02 mirrors PM-03's dedup discipline: it
merges on **identity evidence**, not surface similarity. "Route Compiler" and "Query Compiler" are
similar strings but distinct resources; they are not merged absent evidence (shared owner, shared
edges, an explicit equivalence assertion) that they are the same thing. The layer is tuned toward
*proposing* a merge for Owner/verification review over *silently applying* one — a false split
costs a little registry space and is cheaply merged later; a false merge destroys a distinction the
ecosystem paid to learn. Under-merge is recoverable; over-merge is data loss.

---

## Part II — Canonicalization Mechanics

### II.1 The alias registry and the namespace

GK-02 maintains an alias registry (surface form → canonical identity, with evidence and confidence)
and a cognitive namespace that prevents two canonical identities from claiming the same name. The
namespace is what keeps the address space unambiguous: within a scope (a repo, the global space),
one canonical name binds one identity. When a new surface form appears during compilation (GK-03)
or writeback (GK-08), the layer either matches it to an existing canonical identity (raising that
identity's completeness) or, if the evidence is insufficient, mints a *provisional* identity flagged
for later reconciliation — never a confident-but-wrong merge.

### II.2 Cross-repo equivalence

The highest-value canonicalization is cross-repo: recognizing that "the deploy healthcheck" in one
repo and "the release verifier" in another are the same *pattern*, so a decision or fix learned in
one is a coordinate reusable in the other (GK-10). This is inference, not confirmation, so
cross-repo equivalences are minted at **inferred** trust (GK-01's trust class) and surfaced as
reuse *candidates* requiring verification before an agent acts on the transported knowledge. The
layer never asserts two repos' resources are identical on name alone — it proposes the link with
its evidence and lets verification confirm.

### II.3 Supersession and lineage

Canonicalization also tracks *time*: when a resource is replaced (a decision superseded, an engine
rewritten), the old identity is not deleted — it is marked **superseded** and linked to its
successor, so a route that reaches the old coordinate is redirected to the current one with the
history intact. This preserves the "why was this decided" trail (the Decision-Librarian use case,
GK-11) while ensuring navigation lands on the live resource. Lineage is the canonicalizer's memory
that identity persists through replacement — the successor inherits the accumulated edges and the
predecessor becomes a navigable historical node, never a dangling ghost.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **Over-collapse (false merge).** Two distinct resources merged into one identity. Detection: an
  identity whose edges/owners are internally contradictory (it "does" two unrelated things) →
  audited by GK-07 integrity → split. Prevention: evidence-gated merge, biased toward under-merge.
- **Under-collapse (alias sprawl).** The same resource lives as many un-linked coordinates.
  Detection: GK-09 coverage/blind-spot analysis surfaces clusters of thin coordinates that share
  edges → merge candidates proposed. Recoverable and cheap.
- **Namespace collision.** Two canonical identities claim one name. Detection: the namespace
  invariant is checked on every mint; a collision blocks the mint and surfaces for disambiguation.
- **Stale supersession.** A superseded identity is still navigated as live. Detection: resolution
  follows the supersession link and returns the successor with a surfaced "this replaced X" note;
  a superseded coordinate served as current is the bug.

### III.2 Rollback protocol

GK-02 is additive resolution, so rollback degrades to raw identity. (1) Disable auto-merge — new
aliases are minted as separate provisional identities rather than collapsed, reverting to alias
sprawl (recoverable, no loss). (2) Disable cross-repo equivalence while it is audited, keeping
canonicalization repo-local. (3) The alias registry's *content* never rolls back — collapsing is
paused, existing merges persist unless a specific false-merge is found and split. The fail-safe
direction is "keep them separate" — under-merge — never "collapse them and hope."

### III.3 Integration contract

- **GK-01 (spine)** — canonicalization *is* GK-01's identity field made correct; a coordinate
  without canonicalization is a surface form masquerading as an identity.
- **CO-05** — "never represent the same thing twice" is CO-05's "never reason twice" for identity;
  canonical identities are CO-05 assets with freshness.
- **PM-03** — reuses the dedup-on-identity-not-text discipline; findings and identities share the
  over-publish-over-collapse bias.
- **GK-03 / GK-08** — compilation and writeback are where new surface forms enter; each routes
  through canonicalization before minting a coordinate.
- **GK-07 / GK-09** — integrity audits identity uniqueness; the observatory surfaces sprawl and
  merge candidates.
- **GK-10** — cross-repo equivalence is the substrate of cross-repo reuse; the propagation engine
  moves canonical identities, not surface forms.

### III.4 Anti-patterns (forbidden)

- **Merging on surface similarity.** The false-merge that erases distinctions; merge on evidence.
- **Silently applying an uncertain merge.** Propose it; let verification confirm.
- **Deleting a superseded identity.** It becomes a historical node with lineage, never a dangling
  ghost.
- **Letting alias sprawl stand unaudited.** Ten thin coordinates for one resource is the fracture
  the layer exists to heal.
- **Asserting cross-repo identity on name alone.** Cross-repo links are inferred candidates, not
  confirmed facts.

---

### GK-02 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Surface forms of one resource resolve to a single canonical identity | Evidence supports the equivalence | Merging two distinct resources — uncertain merges are proposed, not applied |
| Resolution accepts any known alias and returns the canonical coordinate | Alias observed and linked | Recognition of an alias never seen (incremental, GK-09) |
| Superseded identities are linked to successors with lineage intact | Always | Serving a superseded identity as current (resolution redirects) |
| Cross-repo equivalences are minted at inferred trust, surfaced for verification | Always | That an inferred equivalence is a confirmed fact |
| Rollback degrades to under-merge (alias sprawl) without losing merges or content | On misbehavior | — |

**Guarantee level (honest):** GK-02 is an *identity-resolution* layer (level-2 class) — it makes
one resource addressable by any of its names when the equivalence is evidenced; it cannot
guarantee it has seen every alias, and it errs toward under-merge because a false split is
recoverable while a false merge is data loss. Parents: **CO-05 dedup discipline + GK-01**.
*Sealed under SCS C71.*
