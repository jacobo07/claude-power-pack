# Graphify — GK-03 — Knowledge Graph Compiler (All Node Types)

> The kernel's ingestion engine. It turns dispersed workspace knowledge into navigable structure —
> minting a coordinate (GK-01) for every resource worth navigating and seeding the typed edges
> (GK-04) between them. Today's grapher sees only *code*; GK-03 generalizes it to the whole
> ecosystem: datasets, PRDs, prompts, UKDL entries, decisions, bugs, sessions, assets, workflows,
> commands, tests, and domain engines (the video pipeline being the reference case) all become
> first-class nodes. The result is that Claude can *ask the graph* what exists before loading a
> byte of it.
>
> EXTEND, not NEW: `kobi_graphify.py` already compiles source into an Obsidian vault
> (`_knowledge_graph/INDEX.md` + node files + architecture views) with an incremental `--sync`;
> `audit_cache.py` already extracts `neural_summary`, `semantic_dna`, and `depends_on` per file.
> GK-03 is those two engines widened from a code-only `LANGUAGE_MAP` to the full ontology, and
> repointed from per-repo output to the global coordinate registry. Honest (CO-10): compilation is
> a **scan that runs at boundaries** (repo-add, large structural change, post-commit incremental);
> the graph is as fresh as its last scan, and GK-07 owns the staleness verdict — the compiler
> never claims live omniscience.

---

## Part I — What Gets Compiled

### I.1 Beyond code: the full node taxonomy

The compiler's defining extension is scope. `kobi_graphify` maps modules, classes, and functions;
GK-03 additionally mints coordinates for **textual architecture** (datasets and their Parts, PRDs,
prompts), **governance knowledge** (UKDL Hard Rules / Process Rules / Traps, SCS seals, contracts,
done-gates, decisions), **failure knowledge** (bugs, root causes, fixes, regressions), **operational
knowledge** (commands, workflows, checklists, deploy paths), **reusable knowledge** (assets,
templates, schemas, benchmarks, prior outputs), and **domain engines** (the video pipeline, image
systems, and their configs/dependencies). Each becomes a coordinate whose type is drawn from the
GK-01/ontology vocabulary, so the graph is a map of *knowledge*, not just of source files.

### I.2 Extraction: signature, summary, semantic DNA

For every node, the compiler extracts the same three-part fingerprint `audit_cache` already
produces, generalized past code: a **structural signature** (for code: the API surface; for a
dataset: its Parts and contracts; for a decision: its ruling and rationale), a **neural summary**
(the ~one-paragraph "what and why" that lets a route read the node at ~150-300 tokens instead of
its full text), and a **semantic DNA** (the keyword/concept vector that feeds canonicalization and
query matching). This fingerprint is the node's WARM representation (CO-04): a route loads the
summary, not the resource, and pages to full content only on confirmed need. The compiler's output
is therefore *compressive by construction* — the graph is smaller than the corpus it maps, which
is the precondition for it reducing context rather than adding it.

### I.3 Edge seeding

Compilation does not just mint nodes; it seeds the relationships between them. `audit_cache`'s
`depends_on` (import/wikilink resolution) is the first edge type; GK-03 additionally infers
**governed-by** (a module referencing a Hard Rule, a dataset declaring a parent), **generated-by**
(an asset naming the prompt/workflow that produced it), **validated-by** (a resource and its
tests), **broke-because-of** / **fixed-by** (a bug's links to code and commits), and **extends /
supersedes** (a dataset's declared parent, a decision's replacement). These seeds are handed to
GK-04, which owns the typed-edge registry and its evidence/confidence. The compiler's job is to
*propose* edges from what it can observe in the text; GK-04 governs their trust.

---

## Part II — Compilation Mechanics

### II.1 The incremental contract

A full ecosystem scan is expensive, so GK-03 inherits and generalizes kobi_graphify's `--sync`:
the initial compile of a repo is a one-time cost; thereafter only *changed* resources are
recompiled, keyed by the content hash `audit_cache` already tracks. A post-commit incremental
touches only the files the commit changed, rebinds their coordinates, and re-seeds their edges —
seconds, not a full rescan. This is the mechanism that keeps the graph affordable to maintain: the
build cost amortizes to near-zero per session because the vast majority of the ecosystem is
unchanged between scans. Compilation that re-scanned everything each run would itself be the burn
the kernel prevents.

### II.2 When compilation runs

The compiler fires at honest boundaries, never mid-turn: on **repo-add** (a new repo joins the PP →
full initial compile), on **large structural change** (a refactor an Owner flags → targeted
recompile of the affected subtree), and **incrementally after each commit** (the changed-files
delta). Between boundaries the graph is static and its freshness is *known* (GK-07): a coordinate
carries the HEAD it was compiled against, so a consumer can see exactly how current it is. The
compiler makes no claim to track edits it has not scanned — it makes the *last-scanned* state
precise and lets freshness detection surface the gap.

### II.3 The compression invariant

GK-03 operates under a hard invariant inherited from GK-00: **the compiled graph must be smaller,
in tokens, than the corpus it represents, and navigating it must load less than exploring would.**
A node's summary is bounded (~150-300 tokens); INDEX-level views are bounded (~1.5k tokens, per the
existing kobi_graphify INDEX). If a compiled representation grows toward the size of the source it
maps, compilation has failed its purpose and the node is re-summarized more aggressively. The graph
is a *reduction* of the corpus; a graph that inflated context would be a defect, not a feature.

---

## Part III — Failure Modes, Rollback, Integration, Anti-patterns

### III.1 Failure modes and detection

- **Stale node compiled-once, never refreshed.** A resource changes but its coordinate still
  carries the old summary. Detection: the content-hash anchor mismatches on next scan → GK-07
  marks it stale-hard → recompile. The primary source (the resource) always wins over the node.
- **Over-noding.** The compiler mints coordinates for trivia (every log line, every one-off),
  bloating the registry. Detection: the compound-learnings signal thresholds gate what becomes a
  node; low-value nodes with zero resolutions are GC'd (CO-06). Bias toward *fewer, richer* nodes.
- **Mis-typed node.** A resource assigned the wrong ontology type. Detection: type-inconsistent
  edges (a "test" that is imported as a library) surface in GK-07 integrity → re-type.
- **Summary drift.** The neural summary no longer reflects the resource. Detection: hash-mismatch
  forces re-summarization; a summary served without a freshness check is the bug (GK-07).

### III.2 Rollback protocol

GK-03 extends a proven engine, so rollback is graceful. (1) Disable the widened node types and
revert to kobi_graphify's code-only compilation (today's baseline) — the graph loses non-code nodes
but keeps the working code grapher. (2) Disable edge seeding, leaving nodes without inferred
relationships (a flatter graph, still navigable by identity). (3) Disable global registry output and
revert to per-repo `_knowledge_graph/` folders. The compiler's *output* is never destroyed by
rollback — coordinates persist; only the *widening* pauses. Fail-safe: "compile less, explore more,"
never "serve a stale node as fresh."

### III.3 Integration contract

- **kobi_graphify (parent)** — the code-compilation core, widened; its INDEX/node/architecture
  output becomes a view into the coordinate registry.
- **audit_cache (parent)** — its `neural_summary` / `semantic_dna` / `depends_on` extractors are
  the per-node fingerprint, generalized past code.
- **GK-01 / GK-02** — every compiled resource becomes a coordinate, canonicalized on mint so
  aliases do not fracture it.
- **GK-04** — receives the seeded edges and governs their typing/evidence/confidence.
- **GK-07** — owns the freshness verdict on every compiled node and the integrity audit over the
  graph the compiler produces.
- **CO-04 / CO-05** — node summaries are WARM content; verified nodes are CO-05 assets; the
  incremental hash-cache is the CO-05 Cognitive Cache.
- **`/kclaude` `/loop`** — compilation runs at launch/commit boundaries, never per loop iteration.

### III.4 Anti-patterns (forbidden)

- **Full rescan every run.** The build cost must amortize; re-scanning unchanged resources is the
  burn.
- **Noding trivia.** Minting coordinates below the signal threshold drowns real nodes.
- **A node summary larger than a cheap read of the resource.** Violates the compression invariant.
- **Serving a stale node without a freshness check.** The static-vault rot trap at node scope.
- **Code-only thinking.** Compiling source but not the datasets/decisions/bugs that govern it
  leaves the graph half-blind.

---

### GK-03 verifiable contract (summary)

| Promise | Condition | Never guarantees |
|---|---|---|
| Mints a coordinate + fingerprint (signature/summary/DNA) for every ontology node type | Resource scanned at a compile boundary | Coverage of a resource created after the last scan (freshness-flagged, GK-07) |
| Compilation is incremental — only changed resources recompile, keyed by hash | Post-initial | A full-scan-free initial compile (the first pass pays once) |
| The compiled graph is smaller than the corpus; navigating loads less than exploring | Always | — |
| Seeds typed edges for GK-04 to govern; proposes, does not assert, their trust | Always | Confirmed edges without GK-04's evidence/confidence |
| Rollback reverts to code-only per-repo compilation without losing coordinates | On misbehavior | — |

**Guarantee level (honest):** GK-03 is an *ingestion/compression* layer (level-2 class,
boundary-triggered) — it makes the ecosystem navigable and smaller than its corpus; it is as fresh
as its last scan and defers the staleness verdict to GK-07, never claiming live omniscience.
Parents: **kobi_graphify + audit_cache**, widened to the full ontology. *Sealed under SCS C69.*
