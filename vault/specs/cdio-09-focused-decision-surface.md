---
id: SPEC-CDIO-09
title: CDIO-09 Focused Decision Surface (absorption of the InfinityOps Focused Monochrome UI)
tier: T2
status: approved
covers: [cdio-09, focused-decision-surface, focused-monochrome, one-dominant-decision, test_cdio_focus]
owner_go: "finish off with this inside Claude Power Pack" (2026-10-01), continuing the Owner-approved /ultra-plan of session 8b2c7516
---

# SPEC — CDIO-09 Focused Decision Surface

## Objective

InfinityOps proved a focused-decision surface in its own product (STANDARD-113, PR #467,
two consumers, production build verified in a real browser). Claude Power Pack has no knowledge
of it: `cdio-reviewer` cannot judge one, `cdio-core` cannot route to it, and CDIO-06 has no
zero-accent monochrome entry. A fresh agent in any other repo inherits nothing. This spec
closes that gap at the narrowest justified scope.

## Scope

1. `vault/knowledge_base/cdio/CDIO-09-focused-decision-surface.md` — sealed dataset: applicability
   (four conditions + exclusions), scorable criteria in the CDIO-08 grammar
   (`**\`name\`** (dimension \`d\`, severity s)`), the monochrome variant's collisions, what was not
   universalised, evidence ladder.
2. Wiring: CDIO-00 `governs`, CDIO-05 Lens 5 pointer, CDIO-06 F1 zero-accent note + collision,
   the three CDIO agents (repo + live mirrors).
3. `tools/test_cdio_focus.py` — V-CDIO-FOCUS-* done-gate; `tools/test_cdio.py` dataset count 9 -> 10.

## Out of scope

- No change to `modules/cdio/scorer.py` formula: criteria report under existing dimensions.
- No `design_gate` check: evidence is one product (two consumers). A mechanical gate is PLANNED
  until a second product adopts the pattern (recorded in the dataset, sec. 8).
- No edits to the InfinityOps repo. The measured contrast findings on its tokens are reported
  to the Owner, not fixed here.

## Acceptance

- `python tools/test_cdio_focus.py` exit 0, with red drills (malformed criterion, mirror drift,
  missing wiring) that can fail.
- `python tools/test_cdio.py` exit 0 with 10 datasets.
- `python tools/test_cdio_mobile.py` still exit 0 (shared agents changed).

## Rollback

Revert the commit. Nothing reads CDIO-09 except the agents and tests listed above.
