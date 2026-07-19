# Crawl OS — Consumer Declarations

Approved 2026-07-19 (Fase 0, plan `wiggly-sparking-dolphin`). Read this before writing or
sealing any Crawl OS dataset — it is the liveness contract every dataset's front matter
must point back to.

## Invocation model (decided, not aspirational)

Two-tier, both mechanisms already live in this repo, zero new infrastructure required:

**Tier 1 — permanent, all 19 datasets.** Graphify (GK-01/08/10) auto-indexes any file
landing under `vault/knowledge_base/crawl_os/` the next time `modules/graphify/indexer.py
--repo claude-power-pack` runs. Verified non-curated: querying for a file never manually
registered (`cognitive_os_01_operating_economics`) returned it as a real `node_type:
dataset` coordinate. A `PreToolUse:Grep` hook already tells every future session working
in this repo to query the graph before filesystem exploration.

**Correction found and fixed during this build (2026-07-19):** `tools/graphify_knowledge.py`
originally scanned only `.md` files, which silently excluded every dataset written in the
SQI/DAIF/Crawl OS heavy-corpus `.txt` convention — including the already-sealed SQI
constitution, which returned zero graph hits before the fix. Extended the scanner to also
index `.txt` under `vault/knowledge_base/` or `vault/datasets/`. Re-indexed and verified:
node count 979 -> 1004, `sqi_00_constitution_v1` and
`crawl_os_01_constitutional_architecture` both now return as real `dataset` nodes. This
fix benefits SQI and DAIF too, not only Crawl OS — a pre-existing gap, not one this family
introduced. **Query syntax note:** `--query --name <term>` matches a substring against the
node's filename-derived `name`/`node_id` field, not full-text search across the file's
prose — query with the underscored stem or a fragment of it (`"crawl_os_01"`,
`"sqi_00"`), not a spaced phrase (`"crawl os constitutional"` returns nothing even after
the fix, because that phrase never appears literally in the stem).

**Tier 2 — transient, build-time only.** While a specific dataset is actively being
written, a short pointer spec (front matter + a compact summary, not the dataset body)
lives at `vault/specs/crawl-os-<NN>-<slug>.md`. `tools/jit_skill_loader.py`'s
`_active_spec()` picks the most-recently-modified file under `vault/specs/` and injects
it as `ACTIVE PROJECT SPEC` on every `UserPromptSubmit` (24 KB cap, 5-min cache) — this
is the exact mechanism that injected `deep-research-agent.md` twice earlier in this same
engagement, confirmed live, not theoretical. The pointer spec is deleted once its dataset
seals, since the slot is shared repo-wide with every other in-flight spec in this
ecosystem (Crawl OS does not get a permanent claim on it).

**Downstream execution state: PLANNED, stated honestly.** `modules/liveness/
reachability.py`, the repo's formal REACHABLE/ORPHAN gate, scopes only `modules/*.py` —
it does not enumerate prose datasets at all, so it cannot certify these as REACHABLE and
it would be false to claim that status. No code under a future `modules/crawl_os/`
exists yet; that was the Owner's own explicit STOP #1 choice (prose corpus before code).
Each row below names the future module path execution will eventually route through, in
the `PLANNED` vocabulary `reachability.py` already uses for exactly this situation, so
the gap is declared rather than hidden.

## Per-dataset declarations

Format: dataset — primary consumer (graphify, permanent, automatic) — downstream
execution consumer (PLANNED future module) — evidence of consumption.

**01 Crawl OS Constitutional Architecture.** Graphify, permanent. Downstream: every other
Crawl OS dataset and eventually `modules/crawl_os/__init__.py`'s docstring, which by
convention in this repo restates the owning family's constitutional boundary (see
`modules/duplicate_to_advantage/__init__.py`'s docstring for the pattern). Evidence:
`indexer.py --query --name "crawl os constitutional"` returns the node; every sibling
dataset's front matter cites it by name (grep-checkable).

**02 Crawl Intent and Mission Compilation.** Graphify, permanent. Downstream: PLANNED
`modules/crawl_os/mission_compiler.py`. Evidence: graph query; once the module lands, its
docstring names this dataset as source, matching the `d2a_engine.py` header convention
of naming the SCS/dataset it implements.

**03 Adaptive Acquisition Strategy Routing.** Graphify, permanent. Downstream: PLANNED
`modules/crawl_os/strategy_router.py`. Evidence: graph query; the router's cost-ladder
table (dataset §3.2) becomes the module's routing table verbatim, so a diff between the
two is itself a drift check once the module exists.

**04 HTTP Fetch and Transport Intelligence.** Graphify, permanent. Downstream: PLANNED
`modules/crawl_os/adapters/http_fetch.py`. Evidence: graph query.

**05 Browser Interaction and Session Governance.** Graphify, permanent. Downstream:
PLANNED `modules/crawl_os/adapters/browser_session.py`. Evidence: graph query.

**06 Large-Scale Crawl Frontier Engineering.** Graphify, permanent. Downstream: PLANNED
`modules/crawl_os/frontier.py`. Evidence: graph query.

**07 Semantic Extraction and Content Understanding.** Graphify, permanent. Downstream:
PLANNED `modules/crawl_os/extraction/semantic.py`. Evidence: graph query.

**08 Adaptive Selector and Extractor Recovery.** Graphify, permanent. Downstream: PLANNED
`modules/crawl_os/extraction/selector_recovery.py`. Evidence: graph query.

**09 Universal Document Normalization.** Graphify, permanent. Downstream: PLANNED
`modules/crawl_os/normalize.py`. Evidence: graph query.

**10 Evidence Provenance and Integrity Fabric.** Graphify, permanent. Downstream: PLANNED
`modules/crawl_os/evidence.py`. Secondary interface (not fold): once an Evidence Object
is institutionalized it is written back as a typed GK-04 edge — that write-back call is
the one place this dataset's downstream consumer is a REAL existing module
(`modules/graphify/` edge writer), not only a planned one. Evidence: graph query today;
a GK-04 edge with `origin=crawl_os` once the writer exists.

**11 Temporal Web and Change Intelligence.** Graphify, permanent. Downstream: PLANNED
`modules/crawl_os/change_intelligence.py`. Evidence: graph query.

**12 Crawl Memory and Institutional Learning.** Graphify, permanent. Downstream: PLANNED
`modules/crawl_os/memory/`. Evidence: graph query.

**13 Crawl Cortex Supervision and Autonomous QA.** Graphify, permanent. Downstream:
PLANNED `modules/crawl_os/cortex.py`. Evidence: graph query.

**14 Web-to-Dataset Compilation.** Graphify, permanent. Downstream: PLANNED
`modules/crawl_os/compiler.py`. Evidence: graph query.

**16 Authorization, Compliance and Safety.** Graphify, permanent. Downstream: PLANNED
`modules/crawl_os/authz.py`. Evidence: graph query. Built early in the dependency order
(position 4 of 18, ahead of the acquisition engines it bounds) precisely because a
governance dataset with no consumer until position 16 of 20 would itself be a liveness
smell — authorization has to bound the engines from their first Part, not audit them
after the fact.

**17 Evaluation, Benchmarks and Reality Gates.** Graphify, permanent. Downstream: PLANNED
`modules/crawl_os/reality_gates.py`, explicitly built as an extension of DRK-03's
evidence-burden vocabulary (see composition point below) rather than a parallel one.
Evidence: graph query; once built, `reality_gates.py` imports from
`modules.decision_review` rather than reimplementing confidence/sufficiency logic —
that import is the real test of the composition point holding.

**18 Claude Code Skills, MCP and Agent Interfaces.** Graphify, permanent. Downstream:
PLANNED skill definitions under `.claude/skills/` invoking the other 18 datasets'
capabilities as tools — deliberately last in the build order since it can't be written
honestly until the capabilities it exposes exist to be described.

**19 Production Operations and Failure Recovery.** Graphify, permanent. Downstream:
PLANNED `modules/crawl_os/ops/`. Evidence: graph query.

**20 Crawl OS Evolution and Ecosystem Governance.** Graphify, permanent. Downstream: this
dataset's own consumer is partly reflexive — it is read whenever a future Crawl OS
proposal runs through the D2A engine's `FAMILY_REGISTRY`, once Crawl OS itself is added
as a registered family there (mirroring how CO/PM/GK/FD were added). Evidence: graph
query; a future `FAMILY_REGISTRY["CRAWL-OS"]` entry citing this dataset by name.

## Composition points (binding on every dataset's front matter)

15 Cost, Performance and Resource Governance folds into CO-01
(`cognitive_os_01_operating_economics.md`) as a new Part — no dataset 15 exists in this
family, and no Crawl OS dataset may reintroduce general budget/cost/token accounting
language that duplicates CO-01's territory. 10 Evidence Provenance interfaces with GK-04
(typed edge write-back) without being subsumed by it. 17 Evaluation/Reality Gates cites
DRK-03's evidence-burden vocabulary (CONNECT) rather than inventing a parallel one. 02
Crawl Intent and Mission Compilation has no real composition point with DRK-03 — the
original D2A family-sizing FOLD verdict was a false positive on the shared word
"evidence," verified at STOP #1.

## What "sealed" requires here

A Crawl OS dataset may be marked SEALED only when: its front matter names this file, its
Tier 1 graphify consumption is verified by a real `--query` return (not asserted), its
Tier 2 build-time spec pointer has been deleted, and its downstream PLANNED module path
is recorded in this file (already true for all 19 above). A dataset with content but no
entry in this file is not sealed regardless of word count or Part count.
