# Graphify — GK-01 — Knowledge Coordinate System (Global-Native Cognitive Address Space)

> The kernel's spine and its single genuinely-new substrate. Every resource in the ecosystem —
> a module, a dataset, a UKDL trap, a decision, a bug, a video engine, a session — is assigned a
> **stable cognitive coordinate**: an identity that survives a rename, a move, or a cross-repo
> mirror, because it is anchored to *what the resource is and how it relates*, not to where its
> bytes sit. "No busco rutas. Navego coordenadas." A path is a hypothesis about location; a
> coordinate is a durable address in a shared cognitive space.
>
> EXTEND, not from scratch: `kobi_graphify.py` already mints per-repo node identities (module /
> class / function nodes with wikilinks) and `audit_cache.py` already keys knowledge by content
> hash. GK-01 unifies these into one **global-native** address space — a coordinate is valid
> across every repo the PP touches, not scoped to one `_knowledge_graph/` folder — and adds the
> stable-identity layer neither has today. Honest (CO-10): a coordinate is a **record in an
> on-disk registry with a freshness anchor**, resolvable in one lookup; it is not a live pointer
> that auto-follows a moved file — a move is *detected* and the coordinate *rebound*, never
> silently trusted.

---

## Part I — The Coordinate

### I.1 What a coordinate carries

A cognitive coordinate is the structured identity of one resource, and it answers far more than
"where." It carries: the resource's **semantic identity** (its canonical name in the ontology,
resolved through GK-02 so ten aliases collapse to one), its **type** (repo / system / layer /
engine / dataset / decision / bug / trap / asset / …), its **owner system**, its **physical
locus** (repo + path, treated as *current binding*, not identity), its **relationships** (the
typed edges of GK-04), its **minimal context** (what must be loaded to act on it), its
**confidence and evidence** (why the graph believes this record), its **freshness anchor** (the
HEAD/hash it was true against), and its **usage history** (routes that reached it, assets it
produced, workflows that consume it). The path is one field among many, and the *least* durable —
which is the whole point: the coordinate remains addressable when the path changes.

### I.2 Identity is semantic, binding is physical

The load-bearing distinction: a coordinate's **identity** is stable and semantic; its **binding**
to a physical locus is mutable and re-derivable. "The video render engine" is a coordinate whose
identity persists across a refactor that renames its file, splits it into a module, or mirrors it
into a second repo. When the bytes move, GK-07 (freshness/integrity) detects the drift and
*rebinds* the coordinate to its new locus — the identity never changes, so every route, decision,
and edge that referenced it remains valid. This is the mechanism that makes "llévame al motor de
vídeo" answerable without a filename: the resolver (GK-05) navigates to the identity, and the
identity knows its current binding. A system that keyed on path would have to re-discover the
engine after every move; the coordinate system re-discovers it *once* and rebinds.

### I.3 Global-native by construction

kobi_graphify's `_knowledge_graph/` is per-repo; a coordinate here is **global by default**. The
address space spans every repo the PP touches, so a coordinate minted in KobiiCraft is navigable
from a TUA-X session, and a decision recorded once is a coordinate any repo can reference. Locality
is an *attribute* of a coordinate (its owning repo), not the *scope* of the address space. This is
what lets cross-repo reuse (GK-10) be a lookup rather than a re-discovery: learning in one repo
becomes a coordinate the whole ecosystem can reach. The global registry is the durable spine;
per-repo graphs (kobi_graphify output) become *views* into it, not separate universes.

---

## Part II — The Registry, Resolution, and Trust

### II.1 The Universal Coordinate Registry

The registry is the on-disk store of every coordinate, indexed for one-lookup resolution by
identity, by type, by owner, and by relationship. It composes the existing lookup surfaces — the
FTS5 indices, the `audit_cache` hash map, the kobi_graphify node files — into one query surface
that returns *coordinates*, not raw file hits. Retrieval returns a pointer (WARM, CO-04), paged to
full detail only on confirmed need, so consulting the registry is near-zero context cost. The
registry is the rung-1 CO-03 reaches first: before any model or any exploration, "is there a
coordinate for this?" is the cheapest possible resolution.

### II.2 Resolution: from intent to coordinate

Resolution turns a fuzzy intent ("the benchmark for Context VM," "the dataset governing Route
Packs") into a precise coordinate. It is semantic, not lexical: it matches on identity and
relationship, so it succeeds even when the caller does not know the filename — the failure mode of
grep. Resolution returns a coordinate *with its confidence*: an exact identity match is high
confidence; a relationship-inferred match ("the thing GK-06 documents") is medium and flagged for
verification. A resolution below threshold does not fabricate a coordinate — it falls through to
GK-05's query planner or, last, to genuine exploration, which then *writes back* a new coordinate
so the miss is paid once.

### II.3 Trust as a first-class field

Not every coordinate is equally believed, and the registry never pretends otherwise. Each carries
a trust class — **confirmed** (verified against source), **inferred** (derived from relationships,
not directly checked), **stale** (freshness anchor no longer matches), **host-limited** (points at
something the PP cannot fully see), or **superseded** (a newer coordinate replaced it). Resolution
surfaces the trust class with the coordinate, and consumers weigh it: a confirmed coordinate is
navigated directly; a stale or inferred one is a *lead* re-verified against the live binding
before action (HR-PREMISE-001). This is the primary-source-wins discipline of PM-01/CO-05 applied
to identity — a coordinate accelerates orientation; it never overrides verification on the
specific resource about to change.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **Stale binding trusted as current.** A coordinate points at a moved/deleted file and is acted
  on blind. Detection: resolution always returns the freshness verdict; a stale binding is a lead
  requiring rebind (GK-07), never a fact. Fail toward re-verify.
- **Identity collision / split.** Two distinct resources share a coordinate, or one resource
  fractures into two. Detection: GK-02's canonicalization audits identity uniqueness; a collision
  surfaces as an integrity finding (GK-07). Biased toward *split-then-merge-on-evidence* over a
  silent collapse that hides a distinct resource.
- **Orphan coordinate.** A coordinate whose binding no longer resolves to anything. Detection:
  GK-07 flags unresolvable bindings; the coordinate is marked stale/host-limited, not served as
  live.
- **Registry rot.** Coordinates accrete for resources that no longer exist. Detection: CO-06's GC
  policy prunes coordinates with dead bindings and zero recent resolutions, never dropping a
  hard-rule-class or recently-navigated identity.

### III.2 Rollback protocol

GK-01 is additive identity, so rollback is safe. (1) Demote coordinates from *authoritative* to
*advisory* — the resolver returns them as hints, but consumers cold-verify the binding, reverting
to path-based location. (2) Restrict the address space to per-repo (kobi_graphify's current
scope), disabling global resolution while the global registry is audited. (3) The registry's
*content* never rolls back — identities are institutional memory; only *active resolution* pauses.
The fail-safe direction is "resolve by path, verify against source" — no worse than pre-kernel —
never "trust a stale coordinate."

### III.3 Integration contract

- **kobi_graphify (parent)** — its per-repo node identities are promoted into global coordinates;
  its `_knowledge_graph/` output becomes a view into the registry.
- **audit_cache (parent)** — its content-hash keys become coordinate freshness anchors; its
  `depends_on` edges seed GK-04.
- **GK-02** — canonicalizes identity so aliases resolve to one coordinate; GK-01 is meaningless
  without it (ten names, one address).
- **GK-04 / GK-05 / GK-06** — edges hang off coordinates; the resolver and route compiler consume
  them as the addressable unit.
- **CO-03 / CO-04 / CO-05** — the registry is CO-03's rung-1, lives in CO-04's WARM tier, and is a
  CO-05 asset class with freshness.
- **GK-10** — cross-repo propagation moves coordinates, not files; the global-native space is what
  makes that a lookup.

### III.4 Anti-patterns (forbidden)

- **Keying identity on path.** The rename-fragility the coordinate system exists to end.
- **Serving a coordinate without its trust class + freshness.** The static-registry rot trap.
- **Fabricating a coordinate on a low-confidence resolution.** A miss falls through and writes
  back a *verified* coordinate, never a guess.
- **Per-repo-only thinking.** Treating the address space as folder-scoped defeats cross-repo reuse.
- **Trusting a stale binding over source.** Primary source always wins on the specific resource.

---

### GK-01 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Every mapped resource has a stable coordinate whose identity survives rename/move/mirror | Resource compiled into the graph (GK-03) | An identity for a resource never mapped (incremental coverage, GK-09) |
| Identity is semantic; a moved binding is detected and rebound, identity unchanged | Always | Auto-following a move without a freshness check (rebind is detected, not magic) |
| Resolution returns a coordinate with its trust class and confidence | Always | That a coordinate is always current — stale ones are leads |
| The address space is global; a coordinate is navigable cross-repo | Always | Coverage of a repo not yet compiled |
| Rollback reverts to path-based location without losing stored identities | On misbehavior | — |

**Guarantee level (honest):** GK-01 is a *knowledge-identity* layer (level-2 class, deterministic
one-lookup resolution) — it makes location *stable and reusable* when a coordinate exists; it
cannot guarantee a coordinate for an unmapped resource, and a stale binding is a lead re-verified
against source, never trusted blind. Parents: **kobi_graphify + audit_cache**, unified global.
*Sealed under SCS C71.*
