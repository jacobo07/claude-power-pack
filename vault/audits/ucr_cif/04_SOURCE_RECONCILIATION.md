---
title: UCR-CIF — O1 Source Reconciliation
date: 2026-09-23
status: MEASURED
instrument: scratchpad/reconcile_sources.py — md5 of every stripped non-blank line, first-occurrence position map, 10k-line coverage buckets
supersedes: nothing. Re-anchors the denominator of Phase 1.
---

# O1 — the two source files, reconciled

## 1. What was measured, and why it mattered

Two files sit in `C:\Users\User\Downloads` with near-identical names:

| | file | bytes | lines | non-blank | written |
|---|---|---:|---:|---:|---|
| **A** | `…Fabric 1.txt` | 1,521,366 | 75,350 | 37,947 | 2026-08-25 |
| **B** | `…Fabric 1 (1).txt` | 3,086,894 | 167,842 | 81,754 | 2026-09-19 |

**A** is the corpus the Phase 1 inventory and the Phase 3 D2A audit were built on.
**B** is the file the Owner named canonical on 2026-09-23.

Membership was tested by content hash of the stripped line, so reflow or reordering
cannot hide a match. Position mapping answers the sharper question — *does A land inside
B monotonically, and where does it stop?*

## 2. Result

**B is a strict superset of A. 37,947 of 37,947 non-blank lines of A are present in B —
100.0%.**

A maps into B monotonically and terminates at B's line 75,350:

| decile of A | median position in B |
|---|---|
| 0–10% | ~3,056 |
| 50–60% | ~39,877 |
| 90–100% | ~70,294 |

(Raw monotone-step count is 83.2%; the 17% that step backwards are repeated boilerplate
lines that hash identically wherever they occur. The decile map is strictly increasing,
which is the signal that matters.)

So **B = A + roughly 92,500 appended lines.** The Owner kept extending one export.

## 3. The consequence — the Phase 1 denominator covers 46% of the canonical corpus

Coverage of B's non-blank lines by A, per 10,000-line bucket:

| B lines | covered |
|---|---|
| 0 – 69,999 | 77–92% |
| 70,000 – 79,999 | **40.9%** |
| **80,000 – 167,842** | **0.0%** |

Aggregate: **37,947 / 81,754 = 46.4%.**

**~44,500 non-blank lines of the canonical corpus were never inventoried by anyone.**

Therefore:

- The Phase 1 inventory — **1,394 concepts, 336 laws, 71 top-level systems** — is an
  inventory of the first 46%. Every one of its counts is a **floor**, not a measurement.
- The Phase 3 D2A verdicts (10 OWNED · 8 EXTEND · 6 CREATE candidate · 4 UNRESOLVED)
  remain valid **for the 28 spine systems they judged**. What is not valid is the belief
  that 28 is the population. Spine systems may exist in the uncovered half and would
  currently read as absent.
- `CREATE rate: 6 of 28 = 21%` is a rate over a partial denominator.

## 4. The part that bears on the Universal Tower mission directly

The uncovered region is not filler. Anchors already identified inside it:

| B line | content |
|---|---|
| 76,677 | table of candidate macrosystems |
| **89,813 – 90,636** | CodeRabbit absorption · **the eight *Lifts* of the Torre Universal** · "Mi decisión" |
| 113,888 | table — "Capacidad universal UCR-CIF / qué absorbe de las 100" |

**The Universal Tower appears to be defined in the half nobody inventoried.** The Phase 1
pass stopped at A's end (B 75,350). The 2026-09-23 reading pass stopped at B 40,200. B
89,813 has been read by neither.

Any claim about what the Tower *is*, sourced from either pass, is a claim about a document
that does not contain its definition.

## 5. Corroboration of the prior contamination measurement

`UCR_CIF_RESUMPTION.md` records contamination as *nine discontinuous runs, ~3,900 lines,
spanning 60,200–70,299*. The 2026-09-23 reading pass independently found pasted third-party
Codex / PDF / DOCX documentation at B 60,381–63,920, with no knowledge of that record.

Two instruments built differently, agreeing on the same range. The contamination
measurement stands.

## 6. What this does not claim

- It does **not** claim the uncovered half contains new spine systems. It claims nobody has
  looked, and that absence-of-inventory has been reading as absence-of-system.
- It does **not** invalidate any individual D2A verdict. Each was measured against the
  estate, and the estate did not change.
- It does **not** measure how much of the uncovered half is further contamination. The
  contamination audit covered A's range only.
