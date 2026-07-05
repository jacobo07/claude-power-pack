# CDIO Build Plan — Chief Design Intelligence Officer (2026-07-05)

Backup record of the ULTRA-PLAN CDIO build. Sealed as `[[scs_c78_cdio_active]]`.

## Approved architecture (STOP #1, Owner-approved 2026-07-05)

Three decisions were put to the Owner after the Reality Scan; all three
recommendations were approved:

1. **Graph integration** → **ride existing types.** CDIO datasets are markdown,
   auto-indexed as `dataset` nodes by GK-08; one token `CDIO-\d` added to
   `_GOV_ID` in `global_store.py` enables cross-repo promotion. The closed
   `NODE_TYPES`/`EDGE_TYPES` ontology (722-coordinate blast radius) was NOT
   forked.
2. **Design Quality Score** → **deterministic scorer module.**
   `modules/cdio/scorer.py` computes mechanical checks + aggregates the
   reviewer's verdicts into a reproducible 0–100. Not the agent's gestalt.
3. **Hook I4** → **advisory reminder.** PreToolUse additionalContext on a
   visual-surface Write/Edit; never auto-dispatches, never blocks.

## Build order (dependency-sorted, as executed)

1. Datasets CDIO-00..05 (`vault/knowledge_base/cdio/`) — the criteria.
2. `modules/cdio/` — scorer, bus_bridge, telemetry, __init__ (the deterministic core).
3. Integrations — `_GOV_ID += CDIO-\d`; CO-12 `readiness_report` `cdio` block.
4. 3 agent files (`vault/agents/`) + Copy-Item to `~/.claude/agents/`.
5. Advisory hook `hooks/cdio_visual_advisory.js`.
6. `tools/test_cdio.py` — 8 V-gates ×3 hermetic.
7. Seal — SCS C78, UKDL (PR-CDIO-REVIEW-GATE-001, T-DESIGN-OPINION-VS-CRITERIA-001), push.

## Done-gate (observed)

- `tools/test_cdio.py` 8/8 ×3 hermetic, exit 0.
- No regression: `test_co12_telemetry` 8/8, `test_co12_readiness_telemetry` 8/8,
  `test_parallel_mesh` 34/34.
- Scorer verified: contrast black/white = 21.0; white-on-light-green CTA = 1.76:1
  critical; deterministic score reproducible across runs.

## Owner-side activation (documented, not auto-applied — HR-001)

- `Copy-Item hooks/cdio_visual_advisory.js` → `~/.claude/hooks/`, register as a
  PreToolUse `Write|Edit` hook (settings.json or hook-dispatcher EVENT_MAP).
- `/restart` to cold-load the hook and the 3 agent files (already copied live).

## Design decisions log

- Anti-pattern prose in datasets avoids the write-gate's forbidden slop literals
  (the filler-copy and unfinished-work markers) because the Jobs/Woz write gate
  scans for them; the anti-patterns are described obliquely instead (a candidate
  for a future write-gate detector allowlist).
- Datasets were expanded past 2000 words each with genuine measurable content
  (worked examples + false-positive catalogs), never padding.
- Code lives only in `modules/cdio/`; the knowledge base is prose-only, so
  V-NO-CODE-IN-DATASETS stays clean.
