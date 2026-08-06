---
title: EFAIF Sprint 1 — D2A expansion and gap discovery
date: 2026-08-06
status: STOP #2 — BLOCKING, presented inline, no dataset written
verdict: 0 datasets derivable; 3 narrow EXTENDs survive, each on a named living owner
covers: [efaif, expansion, gap_discovery, stop2, oier, reframing]
sprint_0: SHIPPED — 42cd831 (R1 OIER producer) · 05a5aff (R2 reframing gate)
---

# EFAIF Sprint 1 — expansion attempt

## 0. Sprint 0 shipped before discovery began

Per `PR-AUDIT-RESIDUE-FIRST-001`, the two confirmed residues were built first —
they are gaps with a *verified absent owner*, so they do not depend on discovery
finding anything.

| Residue | Commit | Evidence |
|---|---|---|
| R1 — OIER producer (`modules/craif/oier.py`) | `42cd831` | `EFAIF_RESIDUES_PASS=11/11`, hermetic x3; live harvest of the real `OWNER_QUEUE.md` returned 4 observations, all AUTHORITY_BLOCK, rate correctly `UNMEASURED` |
| R2 — reframing predicate (`spec_gate.check_reframing_gate`) | `05a5aff` | same suite; `tools/test_craif.py` unaffected at `CRAIF_PASS=15/15` |

## 1. Three corrections to the inherited state

The brief carried a state that was two days stale. All three were re-measured
from disk, and all three change the sprint.

| Inherited | Measured 2026-08-06 | Effect |
|---|---|---|
| "Tres STOP #1 abiertos" | **8 OPEN**, of 18 STOP-bearing plans (`vault/plans/STOP_LEDGER.md`: OPEN 8 · CONTRADICTED 6 · RESOLVED 4) | The proposed `T-STOP1-BACKLOG-AS-GOVERNANCE-DEFECT-001` must not be sealed with the number three |
| EFAIF STOP #1 open | reads **CONTRADICTED** — a documented false positive: SEIP's base-rate table cites `EFAIF DO-NOT-BUILD` as prior art, and line-level matching cannot distinguish that from a disposition | The ledger's own "Known limits" section predicted this exact class |
| Discovery spaces are unswept | `uceimr-expansion-2026-08-04.md` **already swept ten**, finding G1–G5, all EXTENDs, 0 datasets | Spaces 1/4/8/11/12 overlap prior work; this sprint swept the remainder |

## 2. Discovery — probes run against `modules/**/*.py`

| Space | Probe | Hits | Disposition |
|---|---|---|---|
| S3 decision archaeology | `rejected_alternative\|alternatives_considered` | **0** | **real gap** |
| S6 evidence demand contract | `evidence_demand\|EvidenceDemand\|discriminative` | **0** | **real gap** |
| S11 STOP #1 prioritizer | `stop_ledger.py` defs: discover/build/render/write | **no ranking fn** | **real gap (half)** |
| S1 assumption registry | `assumption` | 13 | owned — `error_prevention/premise_verifier` + ACIS E0 |
| S2 reframing analytics | `reframe\|reframing` | 24 | owned as of `05a5aff`; analytics is a view, not a gap |
| S4 counterfactual reopen | `reopen\|counterfactual` | 51 | owned — `decision_review/epistemic_algebra.py` (verified present) |
| S5 debt taxonomy | `debt` | 26 | owned — DRK-05 + `retirement.py` + `token_irr` |
| S13 evidence staleness | `stale\|freshness\|verified_at\|expiry` | 206 | owned, densely |
| S14 rule-change provenance | `supersed\|amendment\|previous_version` | 25 | owned — `rule_compiler` + `stop1_queue` |
| S15 reuse ROI | `reuse\|reused` | 79 | owned — `recall_roi` (present) + D2A |
| S7 architecture half-life | — | — | struck vacuous 2026-07-29 (IGEF G9); no evidence has changed |
| S8 OIER consumer | — | — | producer shipped this session; consumer is CEPS recurrence |

`vault/decision_review/` still **does not exist** — UCEIMR G4 (`accountability.py`
has no producer) is unchanged and remains the estate's live orphan-field instance.

## 3. Novelty gate applied to the three survivors

All three were run against the 13 questions. **None answers Q4** ("why is
extending an existing owner insufficient") or **Q5** ("what new primitive does
it require").

- **C1 — rejected-alternative recording.** DRK produces verdicts; nothing records
  what was *not* chosen. Extends `decision_review/decision_record.py`, and shares
  a producer with UCEIMR G4. One dataclass field plus a writer.
- **C2 — evidence demand contract.** Zero hits on the identifiers, but DRK-03 owns
  evidence *burden* and `crawl_os_02` owns crawl-intent compilation. The unowned
  sliver is narrow: "which evidence would change this verdict", a field on an
  existing decision object. Extends DRK-03.
- **C3 — STOP #1 prioritizer.** `stop_ledger.py` enumerates and renders; nothing
  ranks by expected cost of remaining open. 8 OPEN items, oldest 11 days, no
  ordering. Extends `stop_ledger` + `backlog_autopilot`. One scoring function.

**Result: 0 of N slots filled with a dataset. 3 narrow EXTENDs, each on a named
living owner, each on the order of tens of lines.**

## 4. Why this is the expected result

Eleventh consecutive proposal set to measure majority-owned against a discovered
denominator. An expansion pass over an estate of 78 modules and 26 knowledge
families finds adjacency, not territory. The result is not a failure of the
sweep; it is the estate reporting that it is dense.

Anti-inflation honoured: no candidate was padded to reach a target count
(`no-silent-caps`), and every gap was re-tested against its nearest incumbent
before being called a gap (`T-OWNERSHIP-AUDIT-ABSORPTION-BIAS-001`).

## 5. Blocking condition

C1–C3 are not built. No further code is written until the Owner selects inline.
