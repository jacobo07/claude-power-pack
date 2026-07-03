# Graphify Intelligence Kernel — Knowledge Navigation Kernel — PLAN OF RECORD (REVISED)

> ULTRA-PLAN backup. Session: GraphifyKernel-Datasets-2026-07-03.
> Status: **STOP #1 REVISED — awaiting final go/no-go on the 13-dataset consolidated family.**
> Owner rulings applied: (1) EXTEND-first APPROVED + expanded to full Knowledge Navigation
> Kernel; (2) depth = inherit CO/PM ~560-1070w/Part; (3) NEW datasets designed now, live
> agents/stores deferred to EXECUTION-mode. Zero datasets written yet.

## Owner thesis (binding)
Graphify stops being an indexer. It becomes **THE Knowledge Navigation Kernel — the single
source of truth for locating knowledge**. Every agent/planner/loop/subagent/wrapper/Runtime/
Repo-Shared-Brain/Findings-Bus/Context-VM/Router consumes the SAME cognitive navigation system.
The paradigm shift: **stop thinking in files, think in cognitive coordinates** — every resource
has a stable identity independent of where it physically lives. "No busco rutas. Navego coordenadas."
EXTEND_EXISTING_PARENT is absolute; CO/PM become the substrate, never rebuilt.

## Consolidation law applied
The ~40 Owner-named candidates are folded into 13 responsibility boundaries. Sub-capabilities
become Parts/entities inside a dataset, NOT separate datasets — "una única fuente de verdad,
no sistemas paralelos" applied to the dataset family itself (anti-monolith).

## Revised family — `vault/knowledge_base/graphify/` — `graphify_NN_name.md`

### DOCTRINE
| ID | Dataset | Verdict | Parent | Absorbs |
|---|---|---|---|---|
| GK-00 | Knowledge Navigation Kernel — Paradigm & Single-Source-of-Truth Contract | NEW (doctrine) | sibling of CO-00 | the "coordinates-not-files" law; "one navigation system, no parallel systems" |

### SPINE — cognitive identity (the genuinely-new core)
| GK-01 | Knowledge Coordinate System (global-native) | **NEW** | EXTEND kobi_graphify node id + audit_cache keys | Cognitive Address Space, Semantic Coordinate Engine, Universal Coordinate Registry, Resource Coordinates |
| GK-02 | Semantic Identity & Canonicalization Layer | **NEW** | EXTEND CO-05 dedup + GK-01 | Alias Resolver, Concept Dedup, Knowledge Identity Engine, Cognitive Namespace, Canonicalization |

### GRAPH CORE — EXTEND the existing grapher
| GK-03 | Knowledge Graph Compiler (all node types) | EXTEND | `kobi_graphify.py` (code-only today) | Knowledge Asset Compiler, non-code nodes (dataset/PRD/UKDL/decision/bug/session/video-engine) |
| GK-04 | Typed Edge Registry + Evidence/Confidence/Lineage | EXTEND | `audit_cache.depends_on` (1 edge) | ~18 typed edges, Evidence Layer, Confidence Network, Lineage Runtime, Provenance, Dependency Graph |

### NAVIGATION — EXTEND CO-03 + sleepy doctrine
| GK-05 | Graph Query Runtime + Query Planner/Optimizer + Coordinate Resolver | EXTEND | CO-03 cascade + jit_skill_loader + `parts/sleepy/knowledge-graph.md` | Query Planner, Query Optimizer, Path Optimizer, Coordinate Resolver ("llévame al motor de vídeo") |
| GK-06 | Route Compiler + Minimal Context Pack + Route Cache/Confidence/Cost | EXTEND | CO-03 + CO-04 Hot/Warm | Route Cache, Route Confidence, Route Cost Estimator, Context Pack Builder, Route Provenance |

### HEALTH — EXTEND CO-05 freshness + CO-06 GC
| GK-07 | Graph Freshness, Integrity & Self-Evolution Engine | EXTEND | CO-05 anchors + CO-06 GC + graph_meta.json | Freshness Predictor, Integrity Auditor, Drift Detection, Self-Healing, Evolution Engine, Topology Optimizer, Compression, Quality Scoring |

### WRITEBACK — EXTEND PM-03
| GK-08 | Knowledge Writeback Engine (session → graph) | EXTEND | PM-03 Findings Bus + Cross-Pane Commit | continuous graph enrichment per session |

### OBSERVABILITY — EXTEND CO-01 WU/ROI + telemetry pattern
| GK-09 | Graph Navigation Observatory + Benchmark Suite | **NEW (one dataset)** | EXTEND CO-01 + `session_resilience/telemetry.py` pattern + `vault/benchmarks/ledger.json` | all 8 Observatories, Coverage/Blind-Spot/Hotspot/Heatmap/Usage Analytics, Navigation Telemetry, Route/Query Benchmark, Knowledge Benchmark Suite |

### CROSS-REPO — NEW, pre-scoped as deferred PM-06
| GK-10 | Cross-Repo Knowledge Propagation & Merge | **NEW** | EXTEND vault + CEPS + `cross_project_dedup` + `cross_signal_bus` | Global Knowledge Mesh, diff/merge/conflict-resolve, cross-repo reuse |

### AGENTS — NEW agent family (datasets now, live `.md` deferred)
| GK-11 | Librarian Swarm + Route Governor + Confidence/Compression Contract | **NEW** | Explore-agent pattern + CO-03 routing | Repo/Dataset/Decision/Bug/Asset/Workflow/UKDL/Video/Cross-Repo Librarians, Arbitration, locate-not-reason |

### GOVERNANCE — EXTEND CO-10
| GK-12 | Graph-First Enforcement & Honest Guarantee Ledger | EXTEND | CO-10 5-level ladder | the Hard Rule "consult graph before big exploration" (honestly **level-2 detect/warn**), single-source-of-truth architectural law |

## COVERED — do NOT build (fold references only)
Context Economy · Reasoning Elimination · Context ROI/Trust/Provenance/Waste/Inflation/Dedup
(Owner .txt Part V) = already **CO-01/03/04/05**. Duplicating them is the self-refutation the
kernel forbids. Knowledge Reuse Engine = CO-05. Repo Shared Brain = PM-01 (consumer, not rebuilt).

## Every ~40 candidate mapped (audit)
All 40 Owner-named systems fold into GK-00..GK-12 above; none spawns a parallel system.
(Full crosswalk retained in session context; each row's "Absorbs" column is the map.)

## Depth ruling
Inherit CO/PM ~560-1070w/Part (Owner-approved). V-DEPTH = accepted deviation, same as CO/PM.
A context-cutting kernel that ships 2500w essays is self-refuting.

## Done-gate
V-REALITY-SCAN · V-COORDINATE-SPINE (GK-01/02 stable identity ≠ path) · V-GRAPH-CORE ·
V-ROUTE-COMPILER · V-WRITEBACK · V-OBSERVATORY · V-GLOBAL-SCOPE · V-HONEST-GUARANTEES ·
V-NO-CODE · V-PARENT-REFS · V-BASELINE(pytest no-regression) · V-DEPTH(per ruling).
GRAPHIFY_INDEX.md master + SCS C71 seal + `REMOTE_DELTA = 0 0`.

## Deferred to EXECUTION-mode (not this session)
Live librarian agent `~/.claude/agents/graphify-*.md` (cold-load, needs /restart) ·
live global cross-repo store · live `kobi_graphify.py` node-type extension · Graph-First hook.
