---
covers: [cdio-edge-states, dead-affordance, edge-state-host-ownership, error-status-collapse, unobserved-layout-state, test_cdio_edge_states]
date: 2026-10-08
tier: T2
extends: vault/knowledge_base/cdio/CDIO-00-design-intelligence-kernel.md
---

# CDIO edge states -- a recovery page passes on links that resolve, in its own brand

## Objective
CDIO already owned "error states are trust surfaces" (CDIO-03 sec.7) and "dead-end error"
(CDIO-02 sec.5). One sentence in CDIO-03 sec.7 passed any 404 that "offers search or a link
home". A production campaign showed four ways a 404 satisfies that sentence and is still
wrong. This spec closes them inside the sections that already own the topic: no new dataset,
no renumbering, no product detail.

## Provenance (evidence, not doctrine)
Source: InfinityOps repo, branch `feat/ql-not-found`, plan
`17_Businesses/QuickLease/docs/plans/ql-not-found/PLAN.md`, 2026-10-08. Owner approved
amending CDIO with citations ("CDIO datasets may be amended with citations").

| Observation (where, how measured) | Becomes |
|---|---|
| Production: an unknown path on one product's host returned the right 404 status rendered as ANOTHER product's page (curl, before-state red 3/3). | `edge-state-host-ownership` |
| Local production build `8296e7bc`: the page was fixed but og:title / twitter:title still named the other product. The framework merges metadata per field; only the title had been replaced (Playwright 19/26). | same criterion, metadata clause |
| Mutants on the build: a recovery link pointing to a missing page (M2) and a relative link rewritten by the host proxy (M3). Only following each link on its own host saw them. | `dead-affordance` |
| Plan audit G4 + adversarial probes: a signed-out request must reach sign-in, not the 404; a forbidden resource may answer not-found only as a written anti-enumeration decision. | `error-status-collapse` |
| A raw-HTML check "found" the 404 headline on every healthy page: the framework embeds the root not-found tree in each page's payload. | CDIO-05 sec.8 observation rule |
| 768px: cards three across while the hero was still stacked (~110px of text per card). Neither the 390 nor the 1280 capture could show it. | `unobserved-layout-state` |
| The owner-approved reference image drew a mock nav, a "sample report" card and a dashboard button; the product could keep none of them as drawn. | CDIO-05 sec.8 reference rule |

## Destinations
- CDIO-02 sec.5: catalog line + `dead-affordance` (ux, critical: a broken/dead-end state per
  CDIO-05 sec.3; major off a recovery surface).
- CDIO-03 sec.7: the 404 sentence now requires links that resolve; "Edge states belong to the
  host that serves them" + `edge-state-host-ownership` (trust, major); "An edge state keeps its
  status" + `error-status-collapse` (trust, critical).
- CDIO-05 sec.8 (honesty boundary): "A reference is evidence of intent, not of production
  truth"; "An observation must be able to see what it claims" + `unobserved-layout-state`
  (visual, major).
- NOT in CDIO (product-specific, kept in that product's DESIGN.md and plan): the brand, the
  illustration and its people, colours, copy, the per-host link lists.

## Acceptance
`python tools/test_cdio_edge_states.py` 6/6: criteria in their owning sections, severities per
CDIO-05 sec.3, each accepted by the real scorer and lowering it, the two criticals block "done",
no product trivia (drilled), the old sentence gone. Red on the pre-amendment datasets (1/6,
measured 2026-10-08). `test_cdio.py`, `test_cdio_mobile.py`, `test_cdio_focus.py`,
`test_experience_contract.py` unchanged and green.

## Retrieval
Agents read CDIO from `~/.claude/skills/claude-power-pack/vault/knowledge_base/cdio`, the live
checkout. It carries these amendments only once that checkout contains this commit; merging to
main is necessary, not sufficient. Measure it (grep the live dataset for `dead-affordance`)
before claiming an agent can retrieve it.

## Rollback
Revert the commit: three dataset hunks and one new test; no consumer depends on the new ids.
