# BCAP-2 Phase 5 — Synsation UX Reality Scan (IN PROGRESS, scan only, no implementation) — base 029bdac2

Spec: vault/backlog/2026-10-13_synsation-ux-patterns-absorption.md (UX-01..UX-20; sources are 4 owner videos that are NOT on GEX44 — claims depending on audio/wording stay INFERRED; re-inspection of the videos is a LAPTOP step).

Owners found (grep): CDIO-05 L60/L91 and CDIO-08 L68-70 own the 44x44 floor (48dp Android note); CDIO-02 L224 owns disabled-while-pending + inline "Saved";
CDIO-03 L204 owns the >1 s no-feedback measurement; CDIO-07 L64 owns the `waiting` enum (skeleton/spinner/progress/optimistic), L172-177 optimistic needs reconciliation, L233 spinner-flash defect, L301 skeleton past threshold.
Corpus: modules/cdio/motion_patterns.py discovers `motion:` blocks in vault/knowledge_base/visual-patterns/ (3 VP-AJS entries from Phase 4 are the template).
GOTCHA: tools/test_cdio.py pins exactly 13 datasets in vault/knowledge_base/cdio/ — do NOT add a CDIO-13 file (Phase 4 hit this); extend CDIO-02/03/07 in place or add under visual-patterns/.

## Provisional dispositions (HYPOTHESIS, owners verified to exist, overlap not yet analysed)
- UX-04/05/06 hit-area geometry: floor ALREADY OWNED (CDIO-05/08); real-hitbox measurement + overlap/nested-target = EXTEND/new executable check (browser-real part is LAPTOP/browser plane).
- UX-07..13 waiting: enum ALREADY OWNED (CDIO-07); missing = falsifiable decision procedure (UX-13 matrix) -> candidate deterministic function + skeleton/inline-spinner/optimistic pattern entries with "Cuando NO usar".
- UX-01..03 disabled/validation causality: EXTEND CDIO-02 (disabled-state contract, 7 questions, defect classes); long-form recovery testable only in a browser.
- UX-14..20 compliance UX: DOMAIN-SPECIFIC/promotional video; absorb narrowest into CDIO-03 (evidence/freshness/review distinct states, no single "compliant" badge) + CDIO-04 (removes blocker, not demand); rest REJECT/UNVERIFIED.

## Next exact steps
1. Write vault/programs/bcap-2/synsation/DISPOSITIONS.md (UX-01..20, one closed-vocab row each, owner path exists).
2. Implement minimal: a pure-python waiting-pattern decision function + disabled-state/hit-target record checkers (modules/cdio/, wire from design_route.py so liveness passes), 2-3 patterns in visual-patterns/, small in-place extensions to CDIO-02/03/07.
3. Gate tools/test_bcap2_synsation.py (both poles, seeded-red mutants; edit in small steps, no giant Write with weakening fixtures), run test_cdio 8/8, test_motion_grammar 46/46, Phase 1-4 gates, liveness 56.
4. STATE.md section, backlog Status + deferred-backlog row, commit.
