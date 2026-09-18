---
covers: [cdio-08, mobile-app-surface, mobile-app-ui-design, cdio-mobile, test_cdio_mobile]
date: 2026-09-18
tier: T2
extends: vault/knowledge_base/cdio/CDIO-00-design-intelligence-kernel.md
---

# CDIO-08 -- absorbing ceorkm/mobile-app-ui-design

## Objective
Make CDIO and the Power Pack carry the useful content of
github.com/ceorkm/mobile-app-ui-design (SKILL.md + references/industry-conventions.md,
fetched 2026-09-18) without importing the parts that contradict sealed CDIO doctrine.

## Inventory and destinations (every source claim lands on exactly one)
- ALREADY OWNED (not duplicated): 8-point grid (CDIO-01), 44pt tap targets and 16px body
  on mobile (CDIO-05 Lens 6), empty/loading/error states (CDIO-03 sec.7), contrast floors.
- NEW, measurable -> CDIO-08 criteria: thumb-zone primary action, value-over-label,
  zero-state search, selection-over-typing, status-as-timeline, user-stage adaptation,
  bottom navigation count, tinted shadow on coloured surface, 60/30/10 as a convention.
- NEW, convention -> CDIO-08 sec. industry conventions (CDIO-06 is dirty with another
  writer's uncommitted F10 hunks, so it is NOT edited; CDIO-08 points at it instead).
- NEW, behavioural -> CDIO-07 sec. Peak-End: a way to CHOOSE `celebration_policy`,
  never a licence to celebrate.
- REJECTED, with reason, recorded in CDIO-08: celebrate every small win; glow and
  backdrop-blur as polish; 80-96px section padding on a phone; the 2-vs-3 weights
  self-contradiction; monospace for numbers (tabular figures instead).
- UNVERIFIED, never criteria: Duolingo DAU figure, Disney 70% figure.

## Changes
1. vault/knowledge_base/cdio/CDIO-08-mobile-app-surface.md (new dataset, source: front matter).
2. CDIO-07: one appended section. CDIO-00 `governs`, CDIO-05 Lens 6 pointer.
3. vault/agents/cdio-core.md + cdio-reviewer.md: route mobile app surfaces to CDIO-08.
4. skills/mobile-app-ui-design/SKILL.md: PP skill rewritten CDIO-aligned, mirrored to
   ~/.claude/skills/mobile-app-ui-design/. Activation row in PP CLAUDE.md.
5. tools/test_cdio.py EXPECTED_DATASETS 8 -> 9; tools/test_cdio_mobile.py (V-CDIO-MOBILE-*).

## Acceptance
- `python tools/test_cdio.py` 9/9 datasets and exit 0.
- `python tools/test_cdio_mobile.py` exit 0, including a red drill on a synthetic
  criterion with no threshold and on a mirror drift.
- modules.cdio.scorer untouched (another writer owns its uncommitted hunks).

## Rollback
Delete CDIO-08, the skill dir and its mirror, test_cdio_mobile.py; revert the appended
sections and EXPECTED_DATASETS.
