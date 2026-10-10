# WU-W8 -- C3 recompiled: Tennis Scope A and Scope B reforecast from measured capability

Common brief: `PROGRAMME.md`. Plan section 5 (W8). Needs W7 DONE. Iterate after the Scope A forecast and again after
Scope B.

Inputs: measure/records.jsonl, claims.jsonl, causal-ledger.json, families.json, W3 toolchain note, W4 disposition,
the old hypothesis file PP `vault/plans/d21-tennis-token-budget-2026-10-10.md` (47/215/755M; 434/1,927/4,640M).
1. Two forecasts per scope:
   - CURRENT-TOPOLOGY: measured cost per verified function under W5 as it ran x the scope's function count, plus fixed
     lines. This is the honest "do nothing more" number.
   - COMPILED-LEARNING: CAPEX (toolchain, transform, families, proof) once + per-family first-member cost + per-member
     marginal cost from the W5b curve + frontier long tail at the model-needed share + relink + WMOS + validation.
     If the curve did not fall, this forecast equals CURRENT-TOPOLOGY and says why.
2. For each: semantic lower bound, LOWER, P50, P80, P95, recommended hard authority, confidence, dominant drivers.
3. CAPEX (reusable: transform, certificate, lint, claim ledger, toolchain note) vs Tennis OPEX, with expected other
   beneficiaries (Resort CP50, other DOLs) and the share charged to Tennis.
4. Scope-B admission: ADMIT / NOT YET with the evidence (curve slope, recurrence, model-needed share, proof
   automation, context duplication). NOT YET is a valid answer; the scope stays.
5. Compare with the old hypothesis: what changed, why, what is measured vs inferred vs unproven savings.
Write `vault/plans/d21-tennis-token-budget-2026-10-11.md` (new file; keep the old one) with every figure tagged
M / D / H and its source. Receipt: the two scope tables and the admission line.
