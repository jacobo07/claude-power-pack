---
title: CCFL-PDPF STOP #1 — Dataset Corpus Boundary
date: 2026-07-31
---

# Dataset Corpus Boundary

Where any approved work may write, and where it may not. Violating a boundary here is a
duplication defect, not a style preference.

## Write-permitted

| Path | Contents |
|---|---|
| `vault/audits/ccfl_pdpf/` | this STOP #1 audit set (already written) |
| `vault/plans/ccfl-pdpf-corpus-2026-07-31.md` | the plan backup |
| `modules/cdp/` | CDP-01…04 executables, **only after approval** |
| `vault/knowledge_base/cdp/` | the CDP doctrine index (option A) or dataset family (option B), **only after approval** |
| `tools/test_cdp.py` | the family done-gate |

## Write-forbidden without the owning family's own approval

| Path | Owner | Why |
|---|---|---|
| `vault/knowledge_base/cpp_ias/**` | CPP-IAS | 478,208 words; IAS-D2 holds the immunity object outright |
| `vault/knowledge_base/crawl_os/**` | Crawl OS | active build, live resumption, DS04 is its named next action; a second writer forks it |
| `vault/knowledge_base/d2a_fabric/**` | DAIF | 8/8 SEALED — a sealed family is not amended by a sibling |
| `vault/knowledge_base/clae/**` | CLAE | 26/26 SEALED |
| `vault/knowledge_base/acis/**` | ACIS | the epistemic ladder is the estate's single confidence scale |
| `vault/knowledge_base/fable_distillation/**` | FD | FD-03 already owns insight routing |
| `vault/hard_rules/**` | `rule_compiler` | rules enter through admission, never by hand |
| `~/.claude/settings.json`, `~/.claude/hooks/**` | Owner | HR-001: agent ships the repo-side half and documents the registration step |

## Amendment path for a forbidden path

Any change CDP needs inside a sealed family is written as a **proposal** into
`vault/OWNER_QUEUE.md` with the target family, the target Part, the delta, and the
evidence — never applied directly. This mirrors `T-FIOS-EVOLUTION-LOCK-001`
(`evolution_engine` proposes and never applies) and the cdio-standards-librarian contract.

## Corpus-format boundary

- No executable code inside a dataset artifact. Conceptual schemas, pseudoflows, state
  machines, decision trees, tables and abstract event formats are permitted.
- No second confidence scale, no second telemetry accountant, no second rule registry, no
  second knowledge graph, no second duplication engine, no second completion authority.
- A concept with a canonical owner is defined once and referenced everywhere else **with
  the referencing context stated**. A verbatim restatement of another family's schema is a
  drift defect — Crawl OS DS10's own Part XXV §25.4 audits for exactly this and is the
  precedent to copy.

## The reachability boundary

Every CDP module must clear `python modules/liveness/reachability.py` before it is called
done, or be declared in `vault/liveness/reachability_registry.json` with an honest class.
A module that imports cleanly and passes its own tests while nothing invokes it is the
estate's single most-recurring error (`root_cause_taxonomy.md` CLASE 0). CDP-01's writer
without a caller would be that error committed by the system built to detect it.
