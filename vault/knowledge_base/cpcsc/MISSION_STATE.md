# CPCSC — MISSION STATE

**Phase:** Task 1 + 1b SEALED · Task 2 IN FLIGHT (wave 1 of 3) · STOP #2 not drawn.
**Updated:** 2026-07-20

## Sealed
- **STOP #1 audit** (`3af2665`) — 20 domains. Source read to EOF (4,779 lines); line 1
  carries a bearer token, never transcribed. 6 verdicts content-verified: all 6 moved
  toward less-owned. Final: 9 ABSORB · 8 EXTEND · 3 KEEP-AS-NEW · 0 REJECT.
- **Task 1 — repatriation** (`6b83358`) — CPP-IAS (14 datasets, 478,208 w) →
  `vault/knowledge_base/cpp_ias/`; CPP-ACI governance → `cpp_aci/`. Byte-identical,
  0 mismatches. `CPP_IAS_INDEX.md` authored.
- **Task 1b — D2A registry derived** (`314ad9a`) — registry 32 → 55 families,
  `registry_gaps()` empty. All 4 measured false FOLDs now DEFER; Counterfactual
  Intelligence now binds KB-DECISION-REVIEW (engine can finally see drk_04).
  Canonical duplicate unchanged at 95%. D2A 26/26, DFP 17/17 (was a pre-existing
  16/17), DRK 18/18, FD 12/12 — hermetic ×3.
- **UKDL** — `PR-CORPUS-AUDIT-CONTENT-TIER-001` + `T-D2A-REGISTRY-BLIND-SPOT-001`.
- Pushed: REMOTE_DELTA `0 0` at `314ad9a`.

## In flight — Task 2, Tribunal content-tier re-run
The 2026-07-12 Tribunal's 12 Sciences. Its §2.2 table lists **9** ABSORB rows
(I, II, III, IV, VI, VII, VIII, IX, XII) while its tally line says "8 of 12 ABSORB,
3 EXTEND, 0 NEW" — summing to 11. Use the TABLE; record the discrepancy.

- **Wave 1 (dispatched):** Sciences I, II, XII · Sciences III, IX
- **Wave 2 (next):** Sciences IV, VIII · Sciences VI, VII
- **Wave 3:** V, X, XI — spot-check only (already EXTEND; bias could only make them
  MORE new, never less)

Deliverable: `CPP_ACI_TRIBUNAL_CONTENT_TIER.md`, 12 rows.

## Known residual limitations (do not paper over)
- **Digital Twin under-called.** Content tier put IAS-F3 at 65% ownership; the fixed
  engine returns 45%/DEFER (func=13, floor is 15). Under-detection that names the
  right adjacent parent is safer than over-detection naming a wrong one, but it IS a
  miss. Do not tune the floor to make one case pass — that is overfitting.
- **Sub-threshold verdicts all pin to exactly 45%**, collapsing ranking among deferred
  cases. Acceptable: 45 means one thing, "insufficient precision to name a parent".
- `corpus_roi.py CORPUS_REGISTRY` is a fourth hand-curated registry with the same
  defect. Recorded in UKDL, deliberately out of scope.

## Next 3 actions
1. Collect wave 1, dispatch wave 2.
2. Write `CPP_ACI_TRIBUNAL_CONTENT_TIER.md`; commit.
3. Draw STOP #2 across CPCSC + Tribunal + CPP-IAS-in-denominator; present inline.

## Do not
- Do not seal any ABSORB/REJECT at title tier (`PR-CORPUS-AUDIT-CONTENT-TIER-001`).
- Do not draw STOP #2 before Task 2 completes.
- Do not commit `modules/duplicate_to_advantage/__init__.py`, `tools/graphify_knowledge.py`,
  or the untracked `tools/test_corpus_roi.py` / `test_redteam_protocol.py` — all belong
  to concurrent panes. Every commit stays pathspec-scoped.
