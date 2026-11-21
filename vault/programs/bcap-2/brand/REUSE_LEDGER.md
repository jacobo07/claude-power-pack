# BCAP-2 Phase 7 — CDIO Brand Identity & Logos: Reuse Ledger (PARTIALLY_PROVEN) — 2026-11-19

Owner of the work: `modules/ccf` (EXTEND, no new owner). Gate: `python3 tools/test_bcap2_brand.py` (BR-01..BR-16, 71 PASS).
**Campaign A fetched no upstream; campaign B Phase 1 did (2026-11-21): see `UPSTREAM_READ.md`** (source read at the pinned SHA, file:line per row).
Rows below marked `READ` were read there; rows marked `HYPOTHESIS` are the two whose page-level content is Phase 3 (DesignHub, Impeccable).

## Upstream repos (10)
| Repo | Pin (from backlog) | Disposition | Evidence status | Note |
|---|---|---|---|---|
| fatihaydost/brand-identity-skill | 532742d7 | EXTRACT/ADAPT method (small-size, glyph, contrast, licence checks) | READ (UPSTREAM_READ.md) | CPP-side equivalents built: `small_size_check`, `check_font`; MIT claimed, third-party notices unaudited |
| moayadMoatamed/Marker-AI | d14340c3 | EXTRACT_METHOD ONLY | READ (UPSTREAM_READ.md) + **LICENSE_CONFLICT** | Backlog: LICENSE text Apache-2.0 vs README MIT. `license_conflict()` blocks code ingestion on any disagreement (BR-14). 12-technique taxonomy (BI-10) not started |
| velinussage/brand-gen | 3fff970a | AUDIT FOR DELTAS, never copy orchestrator/memory | READ (UPSTREAM_READ.md) | not started |
| xianshi3/sigilgen | c3f605b7 | PILOT ADAPTER (P2) | READ (UPSTREAM_READ.md) | not started; typeface outline rights unaudited |
| Leonxlnx/imagegen-skills | beb16b0d | EXTRACT_METHOD | READ (UPSTREAM_READ.md) | not started |
| mcpware/logoloom | 9e5de3e9 | OUTPUT SPEC ONLY, never install | READ (UPSTREAM_READ.md) | Backlog flags shell-interpolated path, PNG-as-.ico, regex SVG, silent Inter fallback. CPP pins the *negatives*: BR-08 (hostile id), BR-09 (PNG named .ico), BR-07 (SVG), BR-10 (no silent font substitution) |
| yakew7/DesignHub | 148e8c3f | COMPARE & BENCHMARK | HYPOTHESIS | not started |
| Forge-Space/branding-mcp | 5128f2ea | ARCHIVED REFERENCE | READ (UPSTREAM_READ.md) | archived at inspection |
| pbakaus/impeccable | dad8dbb3 | REVIEW-GATE REFERENCE | HYPOTHESIS | not a logo generator |
| op7418/logo-generator-skill | bf4e9ac4 | REFERENCE | READ (UPSTREAM_READ.md) | not started |

## Specialist libraries
| Library | Disposition | Status |
|---|---|---|
| resvg | would give deterministic multi-size render | NOT USED: validators are pure-Python structural parsers; real render is laptop/paid plane |
| fontTools | glyph coverage from a real font file | NOT USED: `check_font` consults a declared registry, not a font file |
| SVGO, VTracer, color.js, Style Dictionary, DTCG, favicons, FAISS, Simple Icons | per backlog | DECLINE (campaign B Phase 1): sha + licence pinned in `SPECIALIST_PINS.json`; content not read; no BI gate needs a Node/Rust/C++ dependency; DTCG = spec text (principles only), Simple Icons = trademarks (never as brand assets) |

## Built in-repo (verified by the gate)
BI-01/02 persisted real bytes + CONCEPT_REPORT vs BRAND_KIT split (PDF embeds the mark: BR-01/03); BI-03 BLOCK before provider (BR-04);
BI-04 missing/stale scan = UNASSESSED (BR-05, real defect fixed); WARN needs ack, BLOCK not overridable even by `--by llm` (BR-06/16);
SVG/ICO/PNG validators (BR-02/07/09); unsafe concept ids (BR-08, real path-traversal defect fixed); determinism (BR-11);
blob logo never BRAND_KIT_READY via CLI (BR-12); concept edited after generate refused by provenance (BR-13);
licence-conflict poles (BR-14); partial provider failure state (BR-15); scanner recall 8/8 BLOCK on a frozen paraphrase set (BR-16).

## Residuals (not hidden)
- Scanner is a first-pass filter, not legal clearance; clean-set false-BLOCK is 0 on 5 frozen items but 3 of 5 get WARN (high WARN rate by design).
- No real render, no mono/light/dark variant check, no real font file parse; fixtures avoid words like "ring"/"curve" that trip WARNs.
- BI-00 denominator and BI-08..35 (Marker taxonomy, sigilgen adapter, export profiles, etc.) mostly not started.
- Upstream sources unfetched; evidence_level stays `research`.
