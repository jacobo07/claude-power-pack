# CPCSC — MISSION STATE

**Phase:** STOP #2 APPROVED · A1 SEALED · A2 SEALED · run_family FIXED · **Tier B PENDING (only remaining work).**
**Updated:** 2026-07-21

## STOP #2 ruling (Owner, approved)
- **Tier A: APPROVED** — build A1 + A2.
- **Tier B: APPROVED** — 9 Parts/modules into named owners.
- **Tier C: DEFERRED** — World Model Federation (needs usage evidence) + Cognitive
  Diplomacy (needs constitutional amendment to IAS-F1 §3.4). Do NOT build here.
- **Tier D: belongs to the open CPP-ACI STOP #1** — do NOT touch here.

## Sealed
- STOP #1 (`3af2665`), Task 1 repatriation (`6b83358`), Task 1b D2A registry (`314ad9a`),
  UKDL rules (`417ec51`), Tribunal content-tier 12/12 (`bc3e70d`/`7721031`), STOP #2
  boundary (`4f7b27e`).
- **A1 Cognitive Education SEALED (`fd3bcb1`)** — 25/25 Parts, avg 1396 w/Part (0 under
  the 1200 floor; verified vs estate ref ias_c1=1565 avg), 25 FINAL LAWs, END-OF-DATASET
  marker, contamination 0 hits, citation-only. File:
  `vault/knowledge_base/cpcsc/cpcsc_a1_cognitive_education.txt` (+ DATASET_A1_CONTRACT.md,
  PART_MAP_A1.md). Pushed, REMOTE_DELTA 0 0.
- **A2 Theory Generator / Law Extraction SEALED (`065d2bf`)** — 25/25 Parts, avg 1287
  w/Part (0 under floor), 25 FINAL LAWs, END-OF-DATASET marker, contamination 0 hits,
  citation-only. Object: the estate's legislature — induce candidate laws from evidence,
  PROPOSE-NEVER-APPLY (enforced by construction). Honest B1/B2 build dependency recorded
  in-dataset. File: `cpcsc_a2_theory_generator.txt` (+ DATASET_A2_CONTRACT.md,
  PART_MAP_A2.md). Pushed, REMOTE_DELTA 0 0.
- **run_family DEFER fix SEALED (`ccb025b`)** — the STOP #2 §5 defect: a 45%-capped
  candidate (parent vocabulary matched, precision too low) was reported as KEEP "genuinely
  new". Added `DupeVerdict.deferred` (set when pre-floor coverage >= 50 but not plausible)
  + a third DEFER verdict in run_family (not counted in recommended_count). Gate
  V-D2A-FAMILY-DEFER-NOT-KEEP proves World Model Federation now DEFERs not KEEPs
  (recommended 2→1). D2A 27/27, DFP 17/17, hermetic ×2. Pushed, REMOTE_DELTA 0 0.

## Pending — Tier B ONLY (all else done)
**Tier B — 9 Parts/modules into named owners** (STOP_2 §3). Each: read the owner dataset
fully, write the extension IN PLACE (a new Part in the owner's file, or a module for the
non-dataset ones), close ONLY the named gap (don't widen scope), contamination audit,
add an existence gate to the owner's test suite, micro-commit per owner.
- **B1** unknown-unknown generation → **FIOS** (carries it as 🟡 EXTEND, not built) — module/Part
- **B2** epistemic algebra unification → **new registry + Part** (join DRK-00 / DAIF-01 / ACIS)
- **B3** reasoning execution axis → **CO-03 + one_shot** — wiring
- **B4** corpus→executable transduction → seam **DFP FREEZE → IAS-C1 FUNDED** — module
- **B5** undeclared side-effect ledger → **daif_04 PART VII** — Part + module
- **B6** mission constitution → **ias_a1 PART VII** — one Part
- **B7** adversarial pathogen class → **ias_d2** (taxonomy closed at 6 self-inflicted) — Part
- **B8** semantic memory abstraction ladder → **daif_08** — Part
- **B9** DR simulator · model-exit simulator · SPOF/maturity/debt register → **ias_f3** — Parts

Note B1/B2 are also A2's build dependencies — building them advances both A2's liveness and
the Tier-B ledger. Dataset-Part extensions (B5/B6/B7/B8/B9) obey the >=1200 w/Part floor;
the wiring/module ones (B1/B3/B4) obey the module contract + a V-gate.

## Standing rules for the remaining build
- Floor >= 1200 w/Part (verified; the estate genuinely exceeds it). Citation-only, no
  verbatim restatement. Contamination scan 0 hits before every SEAL. Each Part a FINAL LAW.
- NEVER `git add -A`; every commit pathspec-scoped; verify `git log -1 --format='%s'`.
- Do NOT commit sibling-pane files (`__init__.py`, `graphify_knowledge.py`,
  `test_corpus_roi.py`, `test_redteam_protocol.py`).
- Content-tier verdicts absolute over title-tier. STOP #2 already drawn — build within it.

## Next 3 actions (Tier B)
1. Start with **B6 (ias_a1 PART VII, one Part)** and **B5 (daif_04 PART VII)** — smallest,
   clearest gaps; read each owner fully first, extend in place, floor >=1200, add a gate.
2. Then B7 (ias_d2), B8 (daif_08), B9 (ias_f3) — dataset-Part extensions, same discipline.
3. Then B1/B2/B3/B4 — the module/wiring ones (B1/B2 double as A2's build dependencies);
   module contract + V-gate each. Micro-commit per owner; final REMOTE_DELTA 0 0.

## Floor-first authoring lesson (confirmed A1 + A2)
A1 first-pass landed ~950 w/Part (under floor) → full expansion pass. A2 written
floor-first at ~9 subsections/Part landed ~1200-1420 first-pass (a few needed a small
nudge). For Tier-B dataset Parts: 9+ dense subsections per Part, measure per-Part before
sealing, nudge any under 1200. The estate reference is ias_c1 = 1565 avg/Part.
