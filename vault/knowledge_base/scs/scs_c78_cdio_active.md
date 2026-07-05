# SCS C78 — CDIO-Active: Chief Design Intelligence Officer integrated into the PP

**Sealed:** 2026-07-05
**Type:** new capability (a cross-cutting design-intelligence layer) + integration
**Slot check:** C75 Process-Hibernation, C76 CO-08 Intent-Gate, C77 CO-08 scope-autoexport → this is **C78**. Next free: C79.
**Siblings:** `[[graphify_live_scs_c72]]` (Graphify nodes CDIO rides), `[[parallel_mesh_scs_c65]]` (PM-03 bus CDIO publishes to), `[[scs_c74_co_nextgen]]` (CO-12 telemetry CDIO records to).

---

## What CDIO is

CDIO (Chief Design Intelligence Officer) is a cross-cutting design-intelligence
layer, not a design prompt. It intervenes whenever any PP agent produces or
proposes a visual experience (landing, dashboard, component, onboarding, rendered
marketing copy) and holds every judgment to one law: **a finding names a
measurable criterion and an observed value — never an opinion**
(`[[T-DESIGN-OPINION-VS-CRITERIA-001]]`). It is a citizen of existing PP
infrastructure — it creates no parallel knowledge store.

## Reality Scan corrections that shaped the build (honest, not the prompt verbatim)

Two premises in the build prompt were corrected against source before building:

- **The graph ontology is closed.** `tools/graphify_knowledge.py` fixes
  `NODE_TYPES`/`EDGE_TYPES`; there is no `design_standard` node type or
  `violates`/`implements` edge, and adding them would edit the grapher that
  indexes 722 coordinates for every repo. **Decision (Owner-approved): ride the
  existing types.** CDIO datasets are markdown → auto-classified as `dataset`
  nodes by GK-08 session_writeback → already navigable. To promote them
  cross-repo, one token `CDIO-\d` was added to `_GOV_ID` in `global_store.py`
  (one line, zero blast radius). This is the whole graph integration (I1).
- **A "Design Quality Score" from an agent's gestalt is the opinion the doctrine
  forbids.** **Decision (Owner-approved): a deterministic scorer.**
  `modules/cdio/scorer.py` computes the mechanical checks (WCAG contrast,
  tap-target, type-levels, measure, spacing conformance) and aggregates the
  reviewer's per-criterion verdicts into a reproducible 0–100. Same verdicts →
  same score, proven by test.

## What shipped

- **6 datasets** `vault/knowledge_base/cdio/CDIO-00..05` (kernel, visual, UX,
  trust, conversion, review pipeline). Each > 2000 words, measurable criteria,
  **zero code**, tagged `CDIO-0N` for cross-repo promotion.
- **`modules/cdio/`** deterministic core: `scorer.py` (the CDIO-05 formula
  verbatim + mechanical checks), `bus_bridge.py` (PM-03 publish/consult),
  `telemetry.py` (CO-12 signals + readiness reader), `__init__.py`.
- **3 agent files** `vault/agents/cdio-core.md`, `cdio-reviewer.md`,
  `cdio-standards-librarian.md` (canonical in repo, copied live to
  `~/.claude/agents/` per `[[PR-AGENT-FILES-IN-REPO-001]]`; cold-load needs `/restart`).
- **Integrations:** `_GOV_ID += CDIO-\d` (graph promotion); CO-12
  `readiness_report` now carries a live `cdio` block; PM-03 topic convention
  `design:<criterion>`.
- **Advisory hook** `hooks/cdio_visual_advisory.js` (I4): PreToolUse on a
  visual-surface Write/Edit → additionalContext reminder to run cdio-reviewer.
  Level-2, never blocks, fail-open, throttled, BOM-tolerant.

## Done-gate (observed)

`tools/test_cdio.py` **8/8 ×3 hermetic** (exit 0 each run):
- `V-AGENT-FILES-COMPLETE`, `V-DATASETS-DEPTH` (all 6 > 2000 words),
  `V-GRAPH-NODES` (promotable token), `V-BUS-PUBLISHES`, `V-TELEMETRY-WIRED`,
  `V-REVIEW-PIPELINE` (score=65/BLOCK deterministic; contrast 21.0 exact),
  `V-NO-CODE-IN-DATASETS`, `V-BASELINE-INTACT`.

No regression from the two touched modules: `test_co12_telemetry` 8/8,
`test_co12_readiness_telemetry` 8/8, `test_parallel_mesh` 34/34.

## Honest boundary — Owner-side final hop

The advisory hook is canonical in `hooks/`; activating it is the Owner-side step
(HR-001): `Copy-Item hooks/cdio_visual_advisory.js` to `~/.claude/hooks/`, register
as a PreToolUse `Write|Edit` hook (settings.json or the PP hook-dispatcher
EVENT_MAP), `/restart` to cold-load. The 3 agent files are already copied live;
they too need `/restart` before dispatch. Until wired, the review gate
(`[[PR-CDIO-REVIEW-GATE-001]]`) is invoked by convention: any agent about to
declare a visual surface done runs cdio-reviewer first.

## Cross-references

- Code: `modules/cdio/*`, `modules/graphify/global_store.py` (`_GOV_ID`),
  `modules/cognitive_os/co_12_telemetry.py` (`readiness_report`),
  `hooks/cdio_visual_advisory.js`
- Datasets: `vault/knowledge_base/cdio/CDIO-00..05`
- Agents: `vault/agents/cdio-{core,reviewer,standards-librarian}.md`
- Tests: `tools/test_cdio.py` (8/8 ×3)
- Doctrine: `[[PR-CDIO-REVIEW-GATE-001]]`, `[[T-DESIGN-OPINION-VS-CRITERIA-001]]`,
  `[[PR-AGENT-FILES-IN-REPO-001]]`
- Plan: `vault/plans/cdio-build-2026-07-05.md`
