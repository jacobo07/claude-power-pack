---
id: SPEC-CDIO-10
title: CDIO-10 Legal Surface (absorption of General-Legal/legal-templates)
tier: T2
status: approved
covers: [cdio-10, legal-surface, legal-templates, general-legal, legal_surface, test_cdio_legal]
owner_go: "tambien absorbe esto https://github.com/General-Legal/legal-templates dentro de CDIO para usarlos siempre que hagamos webs" (2026-10-08); scope answers - all 12 templates, blocks done, template + ES/EU gaps
---

# SPEC — CDIO-10 Legal Surface

## Objective

Every website the Owner builds needs legal pages (privacy, cookies, terms, and in Spain the
Aviso Legal). Today CDIO judges a site's look and behaviour and says nothing about whether those
pages exist, are filled in, are reachable, or match the jurisdiction. General Legal published 12
attorney-drafted templates under CC0. This spec absorbs them into CDIO and makes their use a
done-gate for websites, not a reminder.

## Scope

1. `vault/knowledge_base/cdio/legal-templates/` — the upstream `templates/`, `LICENSE` and
   `README.md` verbatim at commit `6d6805425eabd41bed86fc1e2ec51612760f716c`, plus `NOTICE.md`.
   The `.docx` originals and the upstream fetch/convert scripts are not vendored.
2. `vault/knowledge_base/cdio/CDIO-10-legal-surface.md` — sealed dataset: when each document is
   required, template routing per jurisdiction (us / eu / es), the ES/EU gaps the US-drafted
   templates do not cover, criteria in the CDIO-08 grammar, filling discipline, limits.
3. `modules/cdio/legal_surface.py` — executable checker. `plan` prints the required pages and
   their source templates; `check <site>` scans a site's source or build and emits CDIO verdicts
   (missing page, unfilled template field, unreachable page, tracking without a consent
   mechanism) scored by the real `modules/cdio/scorer.py`. Exit 1 on BLOCK.
4. Wiring: CDIO-00 `governs`, CDIO-05 Lens 4 pointer + sec.3 legal-floor severity line, the
   three CDIO agents (repo + live mirrors), `tools/test_cdio.py` dataset count 10 -> 11.
5. `tools/test_cdio_legal.py` — V-CDIO-LEGAL-* done-gate.

## Out of scope

- No scorer formula change: criteria report under the existing `trust` / `ux` / `visual`.
- No legal advice. The dataset and the checker never state that a filled page is legally
  sufficient; they state what is present, filled and reachable.
- No Spanish translation of the templates. Translating legal text is drafting; the dataset
  requires it and marks it as needing review.
- No runtime proof of consent ordering. Static analysis can find a tracker with no consent
  mechanism (FAIL); it cannot prove the mechanism blocks the tracker, so that is reported
  UNVERIFIED, never PASS.

## Acceptance

- `python tools/test_cdio_legal.py` exit 0, with red drills (unfilled field found, missing page
  found, tracker without consent found, control site passes, malformed criterion, mirror drift,
  missing wiring).
- `python tools/test_cdio.py`, `tools/test_cdio_mobile.py`, `tools/test_cdio_focus.py` exit 0.
- `python modules/liveness/reachability.py` names no new unreachable module.
- `check` run against at least one real Owner website repo, read-only, result recorded.

## Rollback

Revert the commit. Nothing outside the CDIO agents, the CDIO tests and this checker reads
CDIO-10 or the vendored templates.
