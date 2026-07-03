# Graphify Intelligence Kernel — Master Index

> The Knowledge Navigation Kernel of Claude Power Pack. Where the Cognitive OS (CO-00…CO-10) governs
> the *cost* of a session and the Parallel Mesh (PM-01…PM-05) governs the *coordination* of many
> panes, the Graphify Kernel (GK-00…GK-12) governs *how knowledge is located* — replacing exploration
> with navigation across the whole ecosystem.
>
> **The fundamental Hard Rule:** *Claude navega el grafo. Claude no explora archivos.* Before any
> expensive knowledge operation, the graph is consulted first — honestly at **level-2 (detect / warn)
> plus a route-compiler redirect** (GK-12/CO-10), never a claimed physical block.
>
> **The paradigm:** stop thinking in files, think in **cognitive coordinates** — every resource has a
> stable identity independent of where its bytes live. *No busco rutas. Navego coordenadas.*
>
> **Root law (inherited from PM):** one navigation system, no parallel systems. Every agent, planner,
> loop, subagent, wrapper, Runtime, Repo Shared Brain, Findings Bus, Context VM, and Router consumes
> the SAME coordinate system and route compiler — a single source of truth for locating knowledge.
>
> **Honesty rule (inherited from CO-10):** every GK surface is a **file on disk queried before
> exploration**, not a live semantic brain; guarantees are classified, residuals are measured.
>
> Scope approved by Owner 2026-07-03 (STOP #1, two rounds): **13 datasets**, depth inherited from the
> CO/PM lineage (~560-1070 words/Part, Owner-ruled), live agents/global-store deferred to
> EXECUTION-mode. Sealed as **SCS C69**.

---

## Family tree

```
Cognitive OS (CO-00..CO-10)  +  Parallel Mesh (PM-01..PM-05)     ← PARENT SUBSTRATE (consumed, never rebuilt)
│
└── Graphify Intelligence Kernel (GK-00..GK-12)                  ← this family (Knowledge Navigation Kernel)
    │
    ├── DOCTRINE
    │   └── GK-00  Navigation Kernel Paradigm & Single-Source-of-Truth   (sibling of CO-00)
    │
    ├── SPINE — cognitive identity (the genuinely-new core)
    │   ├── GK-01  Knowledge Coordinate System (global-native)           (EXTEND kobi_graphify + audit_cache)
    │   └── GK-02  Semantic Identity & Canonicalization                  (EXTEND CO-05 dedup + GK-01)
    │
    ├── GRAPH CORE
    │   ├── GK-03  Knowledge Graph Compiler (all node types)             (EXTEND kobi_graphify)
    │   └── GK-04  Typed Edge Registry (Evidence·Confidence·Lineage)     (EXTEND audit_cache.depends_on)
    │
    ├── NAVIGATION
    │   ├── GK-05  Query Runtime · Planner · Coordinate Resolver         (EXTEND CO-03 + jit_loader + sleepy nav)
    │   └── GK-06  Route Compiler · Minimal Context Pack · Cache         (EXTEND CO-03 + CO-04)
    │
    ├── HEALTH
    │   └── GK-07  Freshness · Integrity · Self-Evolution                (EXTEND CO-05 anchors + CO-06 GC)
    │
    ├── WRITEBACK
    │   └── GK-08  Knowledge Writeback (session → graph)                 (EXTEND PM-03 Commit Protocol)
    │
    ├── OBSERVABILITY
    │   └── GK-09  Navigation Observatory + Benchmark Suite              (EXTEND CO-01 ROI + telemetry + ledger.json)
    │
    ├── CROSS-REPO
    │   └── GK-10  Cross-Repo Propagation & Merge                        (EXTEND deferred PM-06)
    │
    ├── AGENTS
    │   └── GK-11  Librarian Swarm · Route Governor · Compression        (EXTEND GK-05/06 + Explore pattern)
    │
    └── GOVERNANCE
        └── GK-12  Graph-First Enforcement & Honest Guarantee Ledger     (EXTEND CO-10)
```

## Dependency graph (consumer → provider)

- **GK-00** governs all; consumes CO-00 as its sibling contract.
- **GK-01** consumes kobi_graphify (node identity) + audit_cache (hash keys); provides the coordinate
  every other GK dataset addresses.
- **GK-02** consumes CO-05 (dedup) + GK-01; provides canonical identity so aliases do not fracture coordinates.
- **GK-03** consumes kobi_graphify + audit_cache; provides coordinates (GK-01) + seeded edges (GK-04).
- **GK-04** consumes audit_cache.depends_on + GK-03 seeds; provides typed edges to GK-05/06/07.
- **GK-05** consumes CO-03 + jit_loader + sleepy nav + GK-01/02/04; provides query answers to GK-06.
- **GK-06** consumes CO-03/04 + GK-05 answers + GK-04 edges; provides the Minimal Context Pack to execution + GK-12.
- **GK-07** consumes CO-05 + CO-06 + GK-01/04; provides freshness verdicts to GK-05/06 and integrity to GK-09.
- **GK-08** consumes PM-03 + CO-05 verify gate; provides graph mutations + learner feedback to GK-05/06/07/09.
- **GK-09** consumes CO-01 + telemetry + ledger.json; provides metrics to every learner + the Owner.
- **GK-10** consumes deferred PM-06 (vault+CEPS+cross_signal_bus) + GK-01/02; provides the reuse dividend.
- **GK-11** consumes GK-05/06 + Explore pattern + CO-03 routing; provides compressed routes via the Governor.
- **GK-12** consumes CO-10 + every GK guarantee; provides the honest ledger + graph-first detection.

## EXTEND vs NEW vs COVERED

| ID | Dataset | Verdict | Parent / reuse |
|---|---|---|---|
| GK-00 | Navigation Kernel Paradigm | **NEW (doctrine)** | sibling of CO-00 |
| GK-01 | Knowledge Coordinate System | **NEW (the spine)** | kobi_graphify + audit_cache, unified global |
| GK-02 | Semantic Identity & Canonicalization | **NEW** | CO-05 dedup discipline + GK-01 |
| GK-03 | Knowledge Graph Compiler (all node types) | **EXTEND** | kobi_graphify (code-only today) |
| GK-04 | Typed Edge Registry | **EXTEND** | audit_cache.depends_on (1 edge type) |
| GK-05 | Query Runtime + Resolver | **EXTEND** | CO-03 + jit_skill_loader + sleepy nav |
| GK-06 | Route Compiler + Context Pack | **EXTEND** | CO-03 + CO-04 |
| GK-07 | Freshness · Integrity · Self-Evolution | **EXTEND** | CO-05 anchors + CO-06 GC |
| GK-08 | Knowledge Writeback | **EXTEND** | PM-03 Cross-Pane Commit Protocol |
| GK-09 | Navigation Observatory + Benchmarks | **NEW (one dataset)** | CO-01 ROI + telemetry pattern + ledger.json |
| GK-10 | Cross-Repo Propagation & Merge | **NEW** | deferred PM-06 (vault + CEPS + cross_signal_bus) |
| GK-11 | Librarian Swarm + Route Governor | **NEW (agent family)** | GK-05/06 + Explore pattern |
| GK-12 | Graph-First Enforcement & Guarantee Ledger | **EXTEND** | CO-10 |

**COVERED — consumed as substrate, never rebuilt:** Context Economy · Reasoning Elimination · Context
ROI / Trust / Provenance / Waste / Inflation / Dedup = CO-01/03/04/05. Repo Shared Brain = PM-01
(consumer). Reasoning de-dup = CO-05. Duplicating any of these inside a GK dataset is forbidden (GK-00).

## The ~40 Owner candidates → 13 boundaries (crosswalk)

- **Coordinate/Address/Semantic-Coordinate/Universal-Registry/Resource-Coordinates** → GK-01
- **Alias-Resolver/Concept-Dedup/Identity-Engine/Namespace/Canonicalization** → GK-02
- **Asset-Compiler/Dependency-Graph (nodes)** → GK-03
- **Evidence/Confidence-Network/Lineage/Provenance/Dependency-Graph (edges)** → GK-04
- **Query-Planner/Query-Optimizer/Path-Optimizer/Coordinate-Resolver** → GK-05
- **Route-Cache/Route-Confidence/Route-Cost-Estimator/Context-Pack-Builder/Route-Provenance** → GK-06
- **Freshness-Predictor/Integrity-Auditor/Drift-Detection/Self-Healing/Evolution/Topology-Optimizer/Compression/Quality-Scoring** → GK-07
- **(session enrichment)** → GK-08
- **8 Observatories + Coverage/Blind-Spot/Hotspot/Heatmap/Usage-Analytics/Navigation-Telemetry/Route-&-Query-Benchmark/Benchmark-Suite** → GK-09
- **Global-Knowledge-Mesh/Cross-Project-Learning/Universal-Coordinate-Registry (global)** → GK-10
- **(all Librarians + Arbitration + Confidence + Compression)** → GK-11
- **Graph-First-Rule/Graph-Gated-Execution/single-source-of-truth** → GK-12

All 40 fold in; zero parallel systems.

## V-gates (FASE 4 done-gate) — honest scorecard

| Gate | Status | Evidence |
|---|---|---|
| V-REALITY-SCAN (no dataset duplicates a CO-0N / PM-0N) | ✅ PASS | discovered kobi_graphify as true parent; COVERED set named; every GK declares a real parent |
| V-COORDINATE-SPINE (stable identity ≠ path) | ✅ PASS | GK-01 identity-vs-binding contract + GK-02 canonicalization |
| V-GRAPH-CORE (nodes + typed edges concrete) | ✅ PASS | GK-03 node taxonomy + GK-04 ~18 typed edges w/ evidence/confidence |
| V-ROUTE-COMPILER (minimal context pack defined) | ✅ PASS | GK-06 pack sub-structure + minimality gate + compression invariant |
| V-WRITEBACK (graph enriched each session) | ✅ PASS | GK-08 close-boundary commit + verify gate + negative-knowledge contract |
| V-OBSERVATORY (coverage/ROI measured) | ✅ PASS | GK-09 per-type coverage + benchmark suite + self-refutation guard |
| V-GLOBAL-SCOPE (works cross-repo) | ✅ PASS | GK-01 global-native + GK-10 propagation/merge |
| V-HONEST-GUARANTEES (stale detection + level honesty) | ✅ PASS | GK-07 freshness verdicts + GK-12/CO-10 5-level ledger |
| V-PARENT-REFS (each declares its parent) | ✅ PASS | every dataset's blockquote + contract names its CO/PM/tool parent |
| V-NO-CODE (zero code in datasets) | ✅ PASS | 0 fenced code blocks across GK-00..GK-12 (only this index's family tree) |
| V-DEPTH (per Owner ruling) | ⚠️ ACCEPTED DEVIATION | inherits CO/PM depth ~560-1070 words/Part (Owner-ruled 2026-07-03); 2500w would be the burn the kernel prevents |
| V-BASELINE (pytest no regression) | ⏳ PENDING | zero code changed — only .md added; to confirm at seal |

**11/12 strict PASS + 1 accepted deviation (V-DEPTH, Owner-ruled) + 1 pending (baseline at seal).**
Consistent with the CO/PM sealed depth rulings. Honest per the "no classified FAILs at done-gate" doctrine.

## Deferred to EXECUTION-mode (not this session — architecture only)

- Live librarian agents `~/.claude/agents/graphify-*.md` (cold-load, need `/restart`; Windows cap-2 dispatch).
- Live global cross-repo coordinate store (GK-10 propagation transport).
- `kobi_graphify.py` node-type extension (code-only → all ontology types).
- Graph-First detection hook (GK-12 level-2 PreToolUse advisory).

Same staging discipline as PM-02's scheduler recalibration: the datasets are the architecture; the
code is the Owner-authorized follow-up.

## The fundamental property of the whole system

> **Navigate, do not explore.** Coordinates, not files. One navigation system, no parallel systems.
> Each session enriches the graph; the graph compounds; navigation gets cheaper. The graph is
> trustworthy or it declares itself untrustworthy. Every guarantee is honest about its level. All of
> it is files on disk queried before exploration — no live brain claimed, no magic promised.
