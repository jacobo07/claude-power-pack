---
id: SPEC-CDIO-KITCHEN
title: Absorb the dqnamo Kitchen components into CDIO visual-patterns (REF-KITCHEN-001)
tier: T2
status: approved
covers: [ref-kitchen-001, dqnamo-kitchen, visual-patterns-axis-e, vp-019, vp-020, vp-021, vp-022, vp-023, vp-024, vp-025, vp-026, vp-027, test_visual_patterns_kitchen]
owner_go: "absorbe dentro de CDIO todos estos componentes: https://www.dqnamo.com/kitchen" (2026-10-08), plan approved as "Si, ejecuta"
---

# SPEC — Kitchen absorption into CDIO visual-patterns

## Objective

The Owner pointed at fifteen published interaction studies (https://www.dqnamo.com/kitchen) and
asked for all of them inside CDIO. CDIO already has the owner for "how to implement a concrete
effect": `vault/knowledge_base/visual-patterns/`, whose movement entries are discovered by
`modules/cdio/motion_patterns.py` and served on every visual write by `hooks/cdio_visual_advisory.js`.
This spec extends that owner. It does not create a CDIO-NN dataset (HR-NOVELTY-001: a second
authority over the same patterns).

## Source disposition

No page states a license or copyright. The code is visible but not licensed for reuse, so the
absorption carries **principles only**: behaviour, timings, states, accessibility contracts and
failure modes, restated in our own words. No source code is copied into the repo. Every claim is
labelled OBSERVED / INFERRED / UNKNOWN in `evidence/REF-KITCHEN-001/OBSERVATION.md`.

## Scope

1. `visual-patterns/evidence/REF-KITCHEN-001/OBSERVATION.md`: per-component extraction, license
   disposition, the rejected component and why, the cross-cutting doctrine.
2. Nine new entries VP-019..VP-027 (new axis E, interaction primitives, plus axes B and D), each
   with a real "Cuando NO usar" (HR-VP-01) and browser support (HR-VP-02); movement entries carry a
   `motion:` block at `evidence_level: research`.
3. VP-007 extended with the pointer/scroll variant (a second source; no duplicate entry).
4. `visual-patterns/README.md` index rows + axis E.
5. `tools/test_visual_patterns_kitchen.py` (V-VPK-*).

## Mapping

| VP | component(s) |
|---|---|
| VP-019 | Hold to Confirm |
| VP-020 | Magnetic Drop Zone |
| VP-021 | Dynamic Button |
| VP-022 | Scramble Text |
| VP-023 | Receipt Printer |
| VP-024 | Animated Signature + Logo Trace Loader |
| VP-025 | Scroll Fade List |
| VP-026 | Ticket + Stamp |
| VP-027 | Tactile Button + Cassette Audio Player + Playing Cards |
| VP-007 (extended) | Iridescent Foil |
| rejected | Advanced Model Selector |

## Out of scope

- Copying, vendoring or depending on the source's code.
- Raising any entry above `research`: none of these has been built in an Owner project.
- Changing `test_motion_grammar.py` predicates. New entries must keep them green by their own
  `applies_to` and thresholds.

## Acceptance

- `python tools/test_visual_patterns_kitchen.py` exit 0 (schema, HR-VP-01, no code fences,
  provenance resolves, nothing above `research`, real routing with a red drill).
- `python tools/test_motion_grammar.py` exit 0 (no regression of the pinned predicates).

## Rollback

Delete VP-019..027, the REF-KITCHEN-001 folder, the gate and this spec; revert the VP-007 and README
hunks. Nothing else reads them.
