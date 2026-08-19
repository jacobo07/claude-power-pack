# Graphify — GK-13 — Change Impact & Compatibility Compilation

> The kernel's forward-looking edge. GK-07 answers *what has gone stale* — it observes that a node
> changed and marks the routes through it untrusted. GK-13 answers the question asked one moment
> earlier: **given a change that has not been made yet, who is affected, and is the change safe for
> them?** The two look adjacent and are opposite in time. Stale-hard tells a consumer to recompile
> before use; it never tells an author that the edit about to be made breaks a contract someone
> depends on. Freshness governs whether knowledge is still *valid*. Compatibility governs whether a
> change is still *safe*. A kernel that holds every edge in the estate and cannot answer the second
> question is holding the data and declining the use.
>
> EXTEND, not NEW: this is a **compilation over inputs that already exist** — the dependent sets from
> `architecture_horizon`, reference resolution from `refcheck`, observed drift from `drift_registry`,
> scope deviation from `one_shot/lock.py`, and the typed edges of GK-04. GK-13 builds none of them.
> It owns the compile step and the compatibility classification, and it is honest about its
> enforcement level in the CO-10 sense: **level-2 detect and warn**, because no in-process mechanism
> stops an author from making an edit.
>
> **Origin:** UPAC ownership audit 2026-08-18, system 11 (CICC), verdict
> `EXISTS_PARTIALLY → EXTEND_EXISTING_OWNER`, resolution COMPOSE. Owner selected option D.

---

## Part I — The Impact Set

### I.1 Prospective, not retrospective

GK-07's three verdicts are computed *after* a resource moves: fresh, stale-soft, stale-hard. That is
the right shape for navigation, where the question is always whether what the graph holds is still
true. It is the wrong shape for a change, where the question is asked before the edit exists and no
anchor has moved yet.

The distinction is not academic, because the two failure modes are different. A missed staleness
produces a route that carries an outdated summary — recoverable, and GK-07 declares the region
unreliable rather than hiding it. A missed impact produces a change that ships and breaks a consumer
nobody consulted, and the first observation of it is the consumer failing.

### I.2 Propagation is a property of the edge type, not of the graph

The naive impact set is the transitive closure of the dependency relation. In a connected estate that
returns nearly everything, and an answer of *everything* is operationally identical to no answer at
all — it cannot be acted on, so it is ignored, and the mechanism that produces it is soon switched
off.

GK-04's typed edge registry is what makes the set usable: **each edge type declares whether and how a
change propagates across it.** A structural dependency propagates a narrowing change and does not
propagate an additive one. A supersession edge propagates meaning in one direction only. An evidence
edge propagates invalidation but not breakage — the conclusion becomes unsupported without becoming
wrong. An advisory or ordering edge propagates nothing at all.

The compile is therefore a typed traversal: start at the changed coordinate, follow only the edge
types that carry *this* change's class (Part II), and stop where propagation ends. The result is a
bounded set, which is the only kind anyone reads.

### I.3 The frontier, and the estate's measured limit

The output has three regions, and the third is the one that must not be silently dropped.

| Region | Meaning | Obligation |
|---|---|---|
| **Direct** | consumers one typed edge away | verify against the new contract |
| **Transitive** | reached through propagating types only | verify where the type carries breakage |
| **Frontier** | reached, but the next edge's propagation is undeclared | **report as undetermined**, never as clean |

The frontier exists because edge-type coverage is never total, and an undeclared type is an unknown,
not a stop. Rendering it as a stop is the same defect this family has already recorded twice: an
absence of evidence read as a favourable verdict.

**Measured limit, stated rather than hidden.** The estate's own dependency graph contains an
eleven-unit mutually-dependent core in which every member transitively reaches every other. Inside
that group the transitive region *is* the group, for any change, and this compiler's output there is
correct and useless. That is not a defect in the compile — it is the untyped-closure problem showing
up as real data, and its only real fix is architectural: the cycle must be broken. GK-13 reports the
condition explicitly rather than emitting a set that appears actionable.

---

## Part II — Compatibility Classification

### II.1 Four classes

A change is classified before its impact is traversed, because the class decides which edge types
propagate it.

| Class | The change | Breaks |
|---|---|---|
| **Additive** | something new exists; nothing existing changes meaning | nobody |
| **Widening** | an existing surface accepts more than it did | consumers that exhaustively handle the old range |
| **Narrowing** | an existing surface accepts or provides less | every producer relying on what was removed |
| **Replacing** | the same name now means something different | every consumer, silently |

### II.2 The silent class

Replacing is the class this compiler exists for, because every other mechanism in the estate misses
it by construction.

Reference integrity checking asks whether a name resolves — after a replacement it still does.
Freshness asks whether a node changed since its anchor — the node is freshly updated, so it is
*fresh*, which is the most favourable verdict available. Drift detection compares deployed against
source — both moved together, so there is no drift. The three healthiest possible signals are
produced by the most dangerous class of change.

**Recorded instance.** A duplication registry in this estate grew from 58 entries to 131 in one
commit. No name changed, no reference broke, nothing went stale. But one threshold downstream was
scaled to the registry's size, so its meaning moved with the count, and a verdict that had read
`DEFER` for one family began reading `KEEP` — a behavioural change nobody requested and no gate
reported. That is a replacing change at a stable identity, and it is exactly the case the four
signals above call healthy.

### II.3 The verification obligation

Each class carries a different obligation, and the point of classifying is to avoid paying the
maximum every time.

| Class | Obligation |
|---|---|
| **Additive** | none; record the addition |
| **Widening** | re-check consumers that branch exhaustively over the old range |
| **Narrowing** | every producer of what was removed, before the change lands |
| **Replacing** | every consumer re-verified against the new meaning, **and the change announced** — a replacement that is merely correct and unannounced is indistinguishable to a consumer from a defect |

A scale-derived value — a threshold, a ratio, a budget computed from a population — is classified
**replacing** whenever its population changes, even though its own definition did not. This is the
single rule that would have caught the recorded instance, and it generalizes: **a value whose meaning
depends on a population changes meaning when the population does.**

---

## Part III — Composition, Failure Modes, Contract

### III.1 Composed, never rebuilt

GK-13 builds no scanner. It reads what already exists and compiles.

| Input | Owner | Used for |
|---|---|---|
| dependent and transitive-dependent sets | `architecture_horizon` | the traversal substrate |
| typed edges and their propagation | GK-04 | which edges carry which class |
| reference resolution | `refcheck` | whether a name still resolves after the change |
| source-versus-deployed drift | `drift_registry` | whether the change already partly landed |
| scope deviation | `one_shot/lock.py` | whether the change exceeds its contract |
| freshness verdicts | GK-07 | whether the graph being traversed is itself trustworthy |

The last row is a precondition rather than an input: **an impact set compiled over a region GK-07
has declared unreliable inherits that unreliability and says so.** A confident impact set over a
corrupt subgraph is worse than no impact set, and this is the same rule GK-07 applies to routes.

### III.2 Honest enforcement level

Level-2, detect and warn, plus a level-3 redirect where a route can offer the verification obligation
before the edit. No in-process mechanism physically prevents an author from making a narrowing change,
and any downstream document upgrading this to *compatibility-enforced* is inflating the claim in
exactly the way GK-12's audit flags. The strongest honest guarantee is: **the obligation is computed
and surfaced before the change, and it is counted when ignored.**

### III.3 Failure modes and detection

| Failure | Detection signature |
|---|---|
| Untyped closure returned as the impact set | the set size approximates the graph size |
| Frontier reported as clean | an impact report with no undetermined region, on a graph with undeclared edge types |
| Replacing classified as additive | a name whose meaning moved with no consumer verification recorded |
| Scale-derived value not reclassified | a threshold defined against a population that changed in the same commit |
| Impact compiled over an unreliable region | a report with high confidence and a GK-07 unreliable verdict on the same subtree |
| Obligation computed after the change | the report's timestamp follows the edit's |
| Announcement skipped for a correct replacement | consumers report a defect that is the intended new behaviour |

### III.4 Anti-patterns (forbidden)

Compiling an impact set without edge types. Rendering the frontier as a stop. Treating a fresh
verdict as evidence of compatibility — it is evidence of the opposite for the replacing class.
Claiming enforcement above level-2. Rebuilding any input in the Part III.1 table inside this dataset.
Emitting an impact set for a change inside a known dependency cycle without reporting the cycle.

### GK-13 verifiable contract (summary)

- Every impact report names the **change class** before the set, and the class determines the
  traversal.
- Every impact report carries three regions — direct, transitive, **frontier** — and the frontier is
  never empty by omission.
- A **scale-derived value is replacing whenever its population changes**, regardless of whether its
  own definition moved.
- A **replacing change carries an announcement obligation**, not merely a verification one.
- An impact set over a region GK-07 declares unreliable is **reported as inheriting that verdict**.
- The enforcement level is stated as **level-2 detect and warn**; no document may upgrade it.
- Inside a known dependency cycle the report states that the transitive region is the cycle, rather
  than presenting the cycle as an actionable set.
