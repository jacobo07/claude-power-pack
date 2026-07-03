# Graphify — GK-00 — Knowledge Navigation Kernel: Paradigm & Single-Source-of-Truth Contract

> The kernel's founding law. Claude Power Pack stops *exploring* files and starts *navigating*
> knowledge. Today an intention triggers read → glob → grep → reason-about-relationships →
> resolve; every one of those steps re-derives structure the ecosystem already holds. GK-00
> declares the inversion: an intention resolves to a **coordinate**, a coordinate compiles to a
> **route**, a route yields a **minimal context pack**, execution runs, and a **writeback**
> enriches the graph. Navigation replaces exploration wherever a navigable answer exists.
>
> EXTEND, not NEW substrate: GK-00 is the sibling of CO-00 (the Hard Context Budget Contract).
> Where CO-00 governs *how much context a session may hold*, GK-00 governs *how a session finds
> what to load in the first place*. It owns no store and no engine — it is the contract every
> other GK dataset, and every consumer across the PP, is measured against. Honest from line one
> (CO-10): the kernel is **files on disk queried before exploration**, not a live semantic brain;
> its guarantee is *detect-and-redirect* (level-2), never a physical block on a model that
> chooses to grep anyway.

---

## Part I — The Paradigm Inversion

### I.1 Files are an implementation detail; coordinates are the unit of work

The governing shift is stated once and inherited by every dataset below it: **the addressable
unit of the ecosystem is a cognitive coordinate, not a filesystem path.** A path answers "where do
the bytes live"; a coordinate answers "what is this, what owns it, what depends on it, what
governs it, what breaks it, and what is the minimum I must load to act on it." A path breaks when
a file moves, is renamed, or is mirrored across repos; a coordinate is stable across all three
because its identity is semantic, not locational. The PP already pays for this gap daily — the
same module re-globbed, the same UKDL trap re-derived, the same "which file actually implements
this" question re-answered across sessions and panes. GK-00 declares that question answerable
*once*, by the graph, and thereafter navigated rather than re-explored.

### I.2 The mandatory sequence

Every non-trivial task inherits one control flow: **Intent → Coordinate → Route → Minimal Context
Pack → Execution → Writeback.** Intent is resolved to the coordinates it concerns (GK-01/GK-05).
Those coordinates compile to a route — the ordered, minimal set of nodes, decisions, contracts,
traps, and assets the task needs (GK-06). The route materializes as a context pack that is loaded
HOT (CO-04). Execution proceeds against that pack, not against an open-ended read of the repo. On
close, the writeback (GK-08) records what was learned so the next intent resolves faster. The
sequence is not a suggestion about tidiness; it is the definition of a *governed* task. A task
that opens with an arbitrary bulk read has skipped the first three steps and is, by GK-00's
contract, ungoverned — measured and surfaced (GK-12), never silently accepted.

### I.3 One navigation system, no parallel systems

The Owner's binding constraint: **there is exactly one source of truth for locating knowledge.**
Every agent, planner, loop, subagent, wrapper, Runtime, Repo Shared Brain (PM-01), Findings Bus
(PM-03), Context Virtual Memory (CO-04), and Router (CO-03) consumes the *same* coordinate system
and the *same* route compiler. GK-00 forbids a second locator growing beside the first — a private
index in one tool, a bespoke grep-wrapper in another — because two locators drift, disagree, and
reintroduce the duplicate cognition the kernel exists to kill. This is the root-law of the
Parallel Mesh ("duplicate cognition forbidden") lifted from *panes on a repo* to *systems in the
PP*: the coordinate system is shared infrastructure, and anything that locates knowledge does so
through it or is a defect.

---

## Part II — What the Kernel Owns, and What It Refuses

### II.1 Owns: the contract; refuses: the mechanism

GK-00 owns the *contract* — the sequence, the coordinates-not-files law, the single-source rule,
and the honesty framing — and deliberately owns no *mechanism*. The coordinate store is GK-01; the
compiler is GK-03; the query runtime is GK-05; the route compiler is GK-06. This separation is the
anti-monolith discipline made structural: GK-00 can be amended (a new step in the sequence, a
tightened rule) without touching a single engine, and an engine can be rebuilt without renegotiating
the paradigm. A kernel that owned both contract and mechanism would be the monolith the family is
architected to avoid.

### II.2 The COVERED boundary — substrate, never rebuilt

GK-00's second refusal is the explicit list of systems the kernel *consumes* rather than
reimplements. Context Economy, Reasoning Elimination, Context ROI / Trust / Provenance are
**CO-01/03/04/05** and are used as substrate. Repo situational awareness is **PM-01** and is
consumed, not rebuilt. Cross-session reasoning de-duplication is **CO-05** and is the rung the
route compiler reaches first. The kernel's contribution is *navigation* — turning that substrate
into stable coordinates and minimal routes. Any GK dataset that re-derives a COVERED capability
violates GK-00 and is rejected at its own done-gate. The boundary is not a courtesy; it is the
difference between a kernel that compounds the PP and one that forks it.

### II.3 The honesty framing (inherited from CO-10)

The kernel's central claim — "consult the graph before exploring" — is classified honestly the
moment it is made. It is **level-2 (detect / project / warn) plus a route-compiler redirect**, not
a level-1 physical switch. No in-process mechanism can stop a model mid-turn from choosing to
grep; the strongest honest guarantee is that the *cheaper path is offered first and the expensive
one is measured when taken*. GK-00 exists in part to prevent this framing from ever inflating into
a false "graph-enforced" absolute in a downstream doc. The residual — a task that explores anyway —
is named, counted (GK-09), and surfaced (GK-12), never papered over.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **Paradigm bypass.** A task opens with a bulk read, skipping Intent→Coordinate→Route. Detection:
  GK-12 flags an expensive exploration with no preceding query record. The task is not blocked
  (honest level-2), but its burn is attributed and trended, so bypass is visible pressure.
- **Shadow locator.** A tool grows a private index beside the coordinate system. Detection: a
  knowledge-locating code path that does not consult GK-01/GK-05 is a shadow system; it is the
  single-source-of-truth violation and is surfaced for consolidation.
- **Coverage illusion.** The kernel is trusted as complete when it is incrementally built.
  Detection: GK-09's coverage metric names the represented fraction and the blind zones out loud;
  the kernel never claims to know what it has not mapped.
- **Guarantee inflation.** "Graph-first" drifts to "graph-enforced." Detection: GK-12/CO-10 audit
  the claim against its real level; the over-claim is flagged (the theater path).

### III.2 Rollback protocol

GK-00 is a contract, so its rollback is pure de-scope with zero loss. (1) Demote the mandatory
sequence to advisory — tasks *may* navigate but are not measured on it, reverting to today's
explore-first baseline. (2) Relax the single-source rule to permit a fallback locator while the
coordinate system is audited. (3) Fully disabled, GK-00 persists as documentation of the intended
paradigm. The fail-safe direction is always "explore more, navigate less" — the pre-kernel
behavior — never "trust a stale coordinate." Nothing the kernel stores is destroyed by rolling
back the contract; only the *discipline* pauses.

### III.3 Integration contract

- **CO-00** — the sibling contract: CO-00 caps what a session holds, GK-00 governs how it finds
  what to load. A minimal route (GK-06) is the strongest proactive defense of CO-00's ceiling.
- **CO-03 / CO-04 / CO-05** — consumed as substrate: the route compiler's cheapest rungs *are* the
  Vault/asset reads CO-03 already sequences; the context pack lives in CO-04's Hot/Warm tiers;
  reuse-not-rederive is CO-05.
- **PM-01 / PM-03** — the Repo Shared Brain is a coordinate consumer; the Findings Bus is the
  writeback channel (GK-08). The mesh's "duplicate cognition forbidden" is GK-00's rule at pane
  scope.
- **CO-10 / GK-12** — every kernel guarantee is registered and classified; GK-00 holds the honest
  framing of the flagship "graph-first" claim against drift.
- **`/loop` `/kclaude` `/compact` `/kclear`** — a loop resolves its route once at entry, not per
  iteration; kclaude injects the opening coordinate briefing; the graph is external memory that
  *survives* compaction and repo-scoped clears.

### III.4 Anti-patterns (forbidden)

- **Exploring when a route exists.** The canonical inefficiency the kernel is built to end.
- **A second locator.** Any private index/grep-wrapper that bypasses the coordinate system.
- **Rebuilding a COVERED system.** Re-deriving CO/PM capability inside a GK dataset.
- **Claiming enforcement above level-2.** "Graph-enforced" for a detect-and-redirect mechanism.
- **Trusting coverage as complete.** Treating an incremental graph as omniscient.

---

### GK-00 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Every governed task follows Intent→Coordinate→Route→Pack→Execution→Writeback | Task routed through the kernel | Coverage of a task that bulk-reads outside the kernel (flagged, not blocked) |
| Exactly one navigation source of truth; shadow locators are defects | Always | Prevention of a private grep a tool issues directly (level-5 residual) |
| COVERED systems (CO-01/03/04/05, PM-01) are consumed, never rebuilt | Always | — |
| The "graph-first" claim is held at its honest level (2 + redirect) | Always | A physical block on mid-turn exploration |
| Rollback de-scopes to explore-first with zero stored-knowledge loss | On misbehavior | — |

**Guarantee level (honest):** GK-00 is a *contract/classification* layer (level-2 class) — it
enforces nothing itself; it defines the paradigm every GK engine implements and every PP consumer
obeys, and it names the residual (a task that explores anyway) rather than pretending to prevent
it. Parent: **sibling of CO-00**. *Sealed under SCS C71.*
