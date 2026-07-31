---
title: OSR — Instrument Registry
date: 2026-07-31
governed_by: CLAE Part XIII (The Instrument Taxonomy) — seven kinds and their native
  levels, selection by required level, perturbation under envelope, chain coverage as
  intersection, three-valued output
note: CLAE's own registry files (CLAE_EVALS.md, CLAE_PRODUCTION_GATES.md, and the rest)
  are listed `pending` in CLAE_INDEX.md and do not exist yet. These rows live here, in
  the family that produced them, rather than being appended to a SEALED Part. When
  CLAE materializes its registries these fold in; until then this file cites Part XIII
  as the governing taxonomy and claims no authority over it.
---

# OSR Instrument Registry

Three instruments, one law. Every one is three-valued by construction — `MATCH`,
`DIFF`, `UNMEASURED` — which is CLAE Part XIII's own requirement, not a local choice.

| ID | Instrument | Native level | Input | Emits | Never emits |
|---|---|---|---|---|---|
| **OSR-I1** | raster comparison (`compare_rasters`) | direct observation of a rendered artifact | two 8-bit PNGs | differing-pixel count, max channel delta, differing regions as block coordinates, dimension mismatch | a percentage, a score, a fidelity level |
| **OSR-I2** | geometry comparison (`compare_geometry`) | direct observation of a structured surface | two element-box inventories keyed by a stable element id | missing, extra, moved, resized — each element named | a similarity measure |
| **OSR-I3** | temporal comparison (`compare_timelines`) | direct observation of an ordered execution | two named-phase timelines | per-phase duration drift, order change, missing and extra phases | a smoothness or quality judgment |
| **OSR-L1** | ordering gate (`verify_ordering`) | contract-level, not observational | a **declared** prerequisite sequence + an observed trace | `SATISFIED` / `MISSING_PREREQUISITE` / `AFTER_TERMINAL` / `OUT_OF_ORDER` / `TERMINAL_NOT_REACHED` / `UNMEASURED` | a derived sequence — see the counter-rule |

## Selection guidance

Pick by the level of the claim being made, per Part XIII's selection rule.

- A claim about **appearance** needs OSR-I1, and OSR-I1 alone cannot support any claim
  above it. Two rasters that match prove nothing about whether a control has a handler.
- A claim about **structure** needs OSR-I2. It is the instrument that catches the
  divergence class OSR-I1 cannot name: an element that moved, vanished, or appeared.
  It is also the only one of the three that can be run without a rendering surface.
- A claim about **sequence** needs OSR-I3 for observed durations and order, and OSR-L1
  for *declared* contract order. These are different questions and the second one is
  not answerable from the first.
- A claim about **fidelity** needs none of them alone. Chain coverage is an
  intersection: the strongest claim these three jointly support is bounded by the
  weakest link, and the fidelity verdict itself belongs to DAIF-03.

## Perturbation envelope

Each instrument carries a declared tolerance, and a tolerance is part of the claim:

| Instrument | Tolerance | Why it exists |
|---|---|---|
| OSR-I1 | `channel_tolerance`, default 2 | antialiasing, font hinting and renderer differences move channels by small amounts; without a tolerance the instrument reports DIFF on every capture and is discarded, which is worse than a tuned one |
| OSR-I2 | `tolerance_px`, default 2 | sub-pixel layout rounding |
| OSR-I3 | `tolerance_ms`, default 25 | scheduler jitter; also the source document's own proposed animation tolerance |
| OSR-L1 | none | ordering is binary. A tolerance on order would be a tolerance on causality |

A result reported without its tolerance is not reportable. Every instrument echoes its
tolerance in its own observations block for exactly this reason.

## Aggregation

`instrument_report()` is a **conjunction, never an average**. Any `DIFF` makes the
report `DIFF`; any `UNMEASURED` with no `DIFF` makes it `UNMEASURED`. This mirrors
DAIF-03 §1.2 — *"fidelity is not a weighted mean of ten scores; it is a conjunction
over ten dimensions"* — rather than restating it as a rival rule.

## What is deliberately not registered

- **A perceptual instrument.** A perceptual difference metric is a real instrument
  class and OSR does not have one; OSR-I1 is a channel-delta comparison with a
  tolerance, which is a weaker and more honest thing. Recorded as absent rather than
  implied, because an instrument's declared level is the whole basis for trusting it.
- **A semantic-tree instrument.** It needs an accessibility tree, and acquiring one
  from a running application is crawl_os DS05's territory, not OSR's.
- **A design-quality instrument.** `cdio` owns that. A replica can be faithful and
  ugly because the original was, and a registry that blurred the two would give the
  estate two answers to one question.

## Verification

`python tools/test_osr.py` — 30 V-OSR-* gates, hermetic across three consecutive runs
(30/30 each). The raster instrument is proven end to end: the gate encodes PNG
fixtures and the module under test decodes them, so the decoder is exercised rather
than described.
