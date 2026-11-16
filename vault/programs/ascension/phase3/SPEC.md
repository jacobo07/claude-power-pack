---
covers: [web-slice, asc-03, ascension-phase3, bcap-web-vertical-slice]
tier: 2
status: ready
scope: [modules/backlog_autopilot/webslice.py, tools/test_asc_webslice.py, vault/programs/ascension/phase3/]
open_questions:
  - Q1 | RESOLVED | Home is modules/backlog_autopilot (extend the owner); no new system, no PLAN-mode needed
  - Q2 | RESOLVED | Browser is the system Chromium binary driven directly with --headless=new --dump-dom; system python3 has no Playwright
  - Q3 | ASSUMED | Candidate pool = real CDIO componentry catalog + legal_surface + motion corpus, plus seeded negatives; license policy is allow-list, UNKNOWN is refused
acceptance:
  - AC-1 | verify: python3 tools/test_asc_webslice.py
  - AC-2 | verify: python3 tools/test_asc_ledger.py
  - AC-3 | verify: python3 tools/test_asc_inventory.py
must_still_pass:
  - python3 tools/test_asc_ledger.py
  - python3 tools/test_cdio.py
---

# Phase 3 spec: web vertical slice (ASC-03)

## Why
Phases 1-2 measured obligations statically. OPERATIONAL coverage is 0/373 because nothing has executed. Phase 3 builds one
small REAL web surface and drives the full flow, producing the first execution evidence, and proves 12 mandatory decisions
from both poles (a seeded positive the gate catches, a clean case it passes).

## Flow
intent -> product type -> existing identity (DESIGN.md) -> applicability selection -> componentry / motion / legal ->
license + dependency check -> build -> real Chromium render -> in-page interaction check -> CDIO scorer verdict ->
Production Reality check.

## Mandatory cases (each with an observed verdict)
1 useful resource selected; 2 unsuitable rejected; 3 backlog-only not announced available; 4 installed-but-unreachable skill
detected; 5 incompatible license refused; 6 technically incompatible dependency refused; 7 expressiveness none honoured;
8 existing design system not overwritten; 9 too-close brand reference refused; 10 tool success without artifact caught;
11 green test over broken behaviour caught; 12 undiscoverable feature flagged.

## Rollback
Delete modules/backlog_autopilot/webslice.py, tools/test_asc_webslice.py, vault/programs/ascension/phase3/. No other file changes
except phase2/execution_evidence.json (additive).

## Out of scope
Baseline promotion and inheritance (Phase 5), CCF integrity (Phase 4).
