# CPP-ACI — BUILD STATUS

> One row per planned dataset. Only `SEALED` counts as done.
> State machine: DISCOVERED → MAPPED → CONTRACTED → OUTLINED → IN_PROGRESS → CONTENT_COMPLETE → INTEGRATED → EVALUATED → HARDENED → SEALED.

**Global phase:** Phase -1 COMPLETE · **STOP #1 — AWAITING OWNER APPROVAL** · nothing built.

## Architecture decision
- [ ] STOP #1 approved by Owner (architecture locked)
- Recommended architecture: **circulatory delta** (~6–8 datasets), NOT full 12-science spec. See `MASTER_BUILD_PLAN.md` §3.
- Alternative on the table: full conceptual compendium (~15–25 datasets). See §4.

## Planned datasets (recommended architecture — all PENDING until STOP #1)

| ID | Dataset | Tier | Verdict | State |
|---|---|---|---|---|
| LEDGER | NON_DUPLICATION_LEDGER + SYSTEM_REGISTRY | — | NEW (Tribunal on disk) | DISCOVERED |
| F1 | Canonical Glossary (cross-estate) | 0 | NEW-thin | DISCOVERED |
| F2 | Universal Institutional Object Registry | 0 | NEW-thin | DISCOVERED |
| F3 | Dataset Interoperability & Provenance Standard | 0 | NEW-thin | DISCOVERED |
| C1 | Institutional Circulatory Fabric | 1 | NEW (the real delta) | DISCOVERED |
| C2 | Cross-Project Incident Federation & Canonical Identity | 1 | NEW | DISCOVERED |
| M1 | Meta-Institutional Control Plane + Governance Yield | 2 | NEW/EXTEND | DISCOVERED |

## ABSORB→REFERENCE (do NOT build — routed in the ledger)
Sciences I, II, III, IV, VI, VII, VIII, IX, XII · MACRO_AUDIT P1–P4 (already built modules) · 23 pp_dataset Sovereign systems.

## EXTEND (thin genuine delta, folded into C1/M1)
Science V (mission topology) · Science X (measured governance yield) · Science XI (evolution — thin).

## Verification counters (populate as built)
- Datasets SEALED: 0 / TBD
- Total words: 0
- Domain Contamination hits (CW Ops): not yet run
- REMOTE_DELTA: n/a (no PP repo writes this mission)
