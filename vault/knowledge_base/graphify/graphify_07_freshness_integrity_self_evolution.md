# Graphify — GK-07 — Graph Freshness, Integrity & Self-Evolution Engine

> The kernel's conscience about its own map. A graph that silently rots is worse than no graph —
> it serves confident answers about a workspace that has moved on. GK-07 is the engine that keeps
> the graph *trustworthy or honestly-untrustworthy*: it detects when nodes and edges have gone
> stale, audits the graph for structural defects (orphans, contradictions, broken bindings,
> dangerous cycles), and — beyond mere hygiene — *evolves* the graph by proposing missing relations,
> merging duplicates, and flagging blind zones. The graph must be reliable, or it must declare
> itself unreliable. There is no third option.
>
> EXTEND, not NEW: CO-05 already makes freshness a first-class property (every asset carries a
> hash/mtime anchor, stale is re-verified or demoted); CO-06 is the Cognitive Garbage Collector
> whose recency/relevance eviction policy this engine reuses; `audit_cache` already tracks content
> hashes and `graph_meta.json` already stamps `generated_at`. GK-07 is those freshness and hygiene
> disciplines generalized to the whole graph, plus the self-evolution layer none of them has.
> Honest (CO-10): staleness detection is a **scan-time verdict against git/hash state** — the engine
> knows a node *may* have changed, not that it *has* in real time; it fails toward "re-verify,"
> never toward "trust."

---

## Part I — Freshness

### I.1 Anchored, never assumed

Every coordinate and edge carries a freshness anchor (the HEAD/hash it was true against), exactly as
CO-05 assets do. GK-07 compares those anchors to live state and issues one of three verdicts, the
PM-01 model generalized: **fresh** (anchor matches → navigate directly, zero re-derivation),
**stale-soft** (the repo advanced but the specific resource is untouched → navigate with a surfaced
advisory), **stale-hard** (the resource itself changed → its summary/edges are not trusted; recompile
before use). There is no silent consumption of an unvalidated node — the verdict is always computed
and always surfaced. This is what lets a route (GK-06) carry an honest confidence: it knows the
freshness of every coordinate it traversed.

### I.2 The volatile-vs-stable distinction

Not all knowledge decays at the same rate, and GK-07 grades it. A **stable** node — a sealed
decision, a Hard Rule, a historical bug — rarely goes stale; its anchor can be checked cheaply and
infrequently. A **volatile** node — an actively-edited module, a config under change — must be
checked aggressively. The engine tracks each node's volatility from its edit history, so it spends
its freshness-checking budget where drift is likely rather than uniformly. This is the freshness
analogue of CO-04's working-set principle: check hard where change is probable, trust longer where it
is not — never a blanket re-scan (which would be the burn) and never a blanket trust (which would be
rot).

### I.3 Freshness prediction

Beyond detecting staleness, GK-07 *predicts* it: a node in a hot-spot (frequently-changed area,
GK-09) is flagged as likely-to-drift before its next scan, so a route touching it is pre-warned to
verify. Prediction is explicitly probabilistic and labeled as such — it is a heuristic that raises
verification priority, never an assertion that a node *has* changed. It lets the engine front-run rot
in the areas most prone to it, while remaining honest that a prediction is a lead, not a fact.

---

## Part II — Integrity

### II.1 The structural audit

A graph degrades not only by staleness but by structural defect, and GK-07 audits for the failure
set the Owner named: **orphan nodes** (a coordinate no route or edge reaches), **broken bindings** (a
coordinate whose physical locus no longer resolves), **contradictory edges** (X supersedes Y and Y
supersedes X; conflicting should-load-before), **phantom edges** (evidence no longer resolves),
**ownership ambiguity** (a resource two systems both claim to own), **duplicate identities** (the
canonicalization gap, GK-02), **dangerous cycles** (a dependency loop that would trap a route), and
**superseded-but-live** nodes (a replaced resource still navigated as current). Each defect is a
surfaced finding with a diagnosis, not a silent condition.

### II.2 Reliable, or declared unreliable

The engine's central promise: the graph is either reliable *or it says so*. An integrity audit
produces a health verdict per region — a subtree whose nodes are fresh and whose edges are
evidence-backed and non-contradictory is reliable; a subtree riddled with stale nodes, broken
bindings, or contradictions is *declared unreliable*, and routes through it are flagged low-confidence
or refused. This is CO-10's honesty applied to the graph itself: the kernel never presents a corrupt
region as trustworthy. A declared-unreliable region is a visible pressure to repair, not a hidden
hazard a route stumbles into.

### II.3 Self-healing

Where a defect is mechanically fixable, GK-07 repairs it — but proposes rather than silently
mutates where judgment is required. It *rebinds* a coordinate whose file moved (mechanical, safe,
auto-applied). It *demotes* a phantom edge whose evidence is gone (safe). It *proposes* a merge for
duplicate identities (GK-02, evidence-gated, review-surfaced). It *flags* a contradiction for
resolution rather than picking a side. The healing discipline mirrors the whole family's bias: safe,
reversible repairs are automatic; ambiguous ones are proposals with evidence. The engine never
"fixes" the graph by guessing, because a confident wrong repair is worse than an honest flag.

---

## Part III — Self-Evolution, Failure Modes, Rollback, Integration

### III.1 Self-evolution

Beyond keeping the graph correct, GK-07 makes it *grow better*. It detects **missing relations** (two
nodes that share evidence but have no edge → propose one), **isolated nodes** (a coordinate with no
edges → investigate why), **emerging families** (a cluster of related new nodes that wants a parent
system → surface to the Owner as an architectural signal), and **reorganization opportunities** (a
region whose edges suggest a cleaner topology). These are *proposals*, fed to GK-09 (observability)
and the Owner, never auto-applied structural rewrites — the engine improves the map's completeness
and shape over time, at the pace evidence and review allow. This is what keeps the graph from
freezing into its initial, partial form.

### III.2 Failure modes and detection

- **Stale served as fresh.** An anchor check skipped. Detection: every navigation logs a freshness
  verdict; a consume with no verdict is the bug. Block until the check runs; fail toward re-verify.
- **False-positive staleness.** A cosmetic change flags a node stale-hard, forcing needless
  recompiles. Detection: recompiles that produce an identical summary → the volatility/anchor
  granularity is too coarse → tune.
- **Integrity audit misses a defect.** A contradiction or orphan survives. Detection: a route that
  fails on a defect the audit did not catch → the audit's rule set is extended (the defect becomes a
  checked class).
- **Over-eager self-heal.** An auto-rebind points a coordinate at the wrong new locus. Detection:
  post-rebind resolution failure → rebind is reverted and demoted to a proposal. Only unambiguous
  rebinds auto-apply.

### III.3 Rollback protocol

GK-07 generalizes proven freshness/hygiene mechanisms, so rollback is graceful. (1) Disable
self-evolution and self-healing → the engine only *detects and reports*, applying nothing (pure
visibility). (2) Disable prediction → fall back to scan-time verdicts only. (3) Disable the integrity
audit → revert to CO-05 per-asset freshness + `graph_meta.json` timestamp (today's baseline). The
graph's content is never altered by rolling GK-07 back — only its active repair pauses. Fail-safe:
"detect and declare, never auto-mutate on doubt."

### III.4 Integration contract

- **CO-05 (parent)** — freshness anchors and the re-verify-or-demote discipline; GK-07 is that
  generalized graph-wide.
- **CO-06 (parent)** — the eviction policy GK-07 invokes to prune dead nodes/edges/routes.
- **GK-01 / GK-02 / GK-04** — rebinds coordinates, drives canonicalization merges, demotes phantom
  edges; integrity is defined over their records.
- **GK-06** — supplies route freshness verdicts and invalidates stale cached routes.
- **GK-09** — self-evolution proposals and integrity findings are observatory signals (blind spots,
  missing relations, hot-spot volatility).
- **CO-10** — the reliable/unreliable declaration is CO-10's honesty applied to the graph; the engine
  never presents rot as trustworthy.

### III.5 Anti-patterns (forbidden)

- **Serving a node without a freshness verdict.** The static-vault rot trap at graph scale.
- **Auto-mutating the graph on ambiguous evidence.** Safe repairs auto-apply; ambiguous ones are
  proposals.
- **Presenting a corrupt region as reliable.** Declare unreliable; never launder rot.
- **Blanket re-scan or blanket trust.** Check hard where drift is likely, trust longer where stable.
- **Freezing the graph at its initial shape.** Self-evolution keeps completeness and topology growing.

---

### GK-07 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Every node/edge carries a freshness anchor; navigation gets a fresh/stale-soft/stale-hard verdict | Always | Real-time change detection — verdicts are scan-time against git/hash |
| The graph is audited for orphans/contradictions/broken-bindings/cycles; regions are declared reliable or not | On scan | That every defect class is already known — misses extend the rule set |
| Safe repairs (rebind, phantom-demote) auto-apply; ambiguous ones are evidence-backed proposals | Always | An auto-repair on ambiguous evidence (proposed, not applied) |
| Self-evolution proposes missing relations, merges, emerging families | Continuously | Auto-applied structural rewrites (Owner/review-gated) |
| Rollback de-scopes to detect-and-report, then to CO-05 per-asset freshness | On misbehavior | — |

**Guarantee level (honest):** GK-07 is a *freshness/integrity/evolution* layer (level-2 class,
scan-time) — it keeps the graph trustworthy or honestly declares it untrustworthy, auto-applies only
unambiguous repairs, and proposes the rest; it detects that a node *may* have drifted, never claims
live omniscience. Parents: **CO-05 freshness + CO-06 GC**. *Sealed under SCS C71.*
