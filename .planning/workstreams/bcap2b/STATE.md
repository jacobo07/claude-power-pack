# State: bcap2b

Armed from laptop HEAD after 8af361d1 (2026-11-21). Campaign A state: `.planning/workstreams/bcap2/STATE.md` (read-only
input). At the start: done_gate BCAP2_DONE_GATE PASS, every item PARTIALLY_PROVEN, none ACTIVATED.

## Phase log

### Phase 1 (COMPLETE except two rows carried to Phase 3 by design; epoch 2)
done: brand upstream read (8/10 repos READ at pinned SHA, `vault/programs/bcap-2/brand/UPSTREAM_READ.md`; ledger rows flipped; brand gate PASS). DesignHub + Impeccable rows stay HYPOTHESIS -> Phase 3.
done: AGSK batch B (17 rows) -> `vault/programs/bcap-2/upstream-read-b/AGSK_B_rows.tsv` (3 UNVERIFIED resolved to EXTEND, 6 wrong owner paths found). NOT yet merged into DISPOSITIONS.md; gate `tools/test_bcap2_agsk.py` V-AGSK-LEDGER-ONLY-PILOT-READ must be relaxed (READ rows need evidence) when merging.
done: D21 page reads, 21 sources / 22 URLs all HTTP 200 with a generic UA (designmd.ai now 200): `design-resources/LIVE_READ.json` (title, observed numbers, licence words). SOURCES.json NOT yet updated (live_verified still false; gate lines test_bcap2_d21.py:26,116 pin that and need new poles: live_verified only with LIVE_READ evidence). Observed denominators noted: Kinetics page 162 effects (README said 162, site index 144), 3dicons ~1400+ renders, Component Gallery 2,671/60/95.
AGSK batch A finished after the wall: 17 rows in `upstream-read-b/AGSK_A_rows.tsv` (complete, committed); merge with batch B into DISPOSITIONS.md.
Spend: not measured this epoch.

Epoch 2 closed the rest of Phase 1 (each step committed, gate re-run, done_gate PASS after all):
- AGSK: all 34 HYPOTHESIS rows merged into `agsk/DISPOSITIONS.md` as READ (7 UNVERIFIED resolved: 5 EXTEND, 2 CONDITIONAL); gate `V-AGSK-LEDGER-READ-HAS-EVIDENCE` + pole `...WITHOUT-EVIDENCE-REJECTED`; test_bcap2_agsk 57/0.
- D21: SOURCES.json `live_verified` true for 21/21, backed by LIVE_READ.json (web URLs 200 + title; GitHub repos via REPO_META); gate `V-D21-LIVE-VERIFIED` with two poles (claim without read, non-200 read).
- Anime.js: 3 UNVERIFIED rows read at pin 01b81be1 (animatable, motionpath, examples); noted upstream has zero reduced-motion handling; gate no-UNVERIFIED + real-predicate pole; 37/0.
- Brand: 8 specialist libs pinned (sha + LICENSE sha256, `brand/SPECIALIST_PINS.json`), DECLINED for adoption (content not read; stated plainly); DTCG principles-only, Simple Icons never a brand asset; gate BR-PIN with poles.
- Synsation: UX-14/15/18 UNVERIFIED -> REJECT as universal (single sponsored source); DBG R1 / TDD R3 stale residuals marked closed (already read in `dbg/MATTPOCOCK_READ.md`).
- LAPTOP_STEPS B1 added (SaaS style 3 reference bank, 403 from GEX44).
- DECISION: DesignHub + Impeccable rows stay HYPOTHESIS and are read in Phase 3 (the roadmap gives them there); BCAP2B-01 therefore closes at the end of Phase 3. Safe: internal, reversible.
- DECISION: nothing in Phase 1 needed the Owner (no outward action, no spend beyond reads).
Spend: UNMEASURED this epoch (supervisor measured 7.96M processed at start of epoch 2).
Meta: (1) a gate that pinned "live_verified false" and "only pilot READ" had to be inverted into evidence-backed predicates, not just edited; each now has a seeded-bad pole. (2) Ledger owner cells held multi-path prose, so a primary verified path was extracted and the full list kept in the tsv. (3) GitHub API unauthenticated was enough for licence+sha. (4) Phase 1 ended without a clone for the 8 libs: licence+pin only is a DECLINE, not a READ. (5) Next: Phase 2 (D21 remaining workstreams), then Phase 3.

### Phase 2 (epoch 3, PARTIAL: laptop/page-read residuals named)
done: D21-A03 capability denominators (8 OBSERVED from page text with labeled counts + quotes in LIVE_READ.json; 13 UNKNOWN with a reason; gate + 2 poles). 36/36 V-D21 scenarios now named in a driving test (22 added: existing owners driven, new `modules/cdicf/scenario_guards.py` for 19-23/26/27/30/34; mutant drill turned V-D21-23 red). done_gate already carried d21_bc (roadmap line was stale); scenario_guards added to NEW_MODULES. Backlog Status + deferred-backlog row updated.
open (need registry/page reads or a real browser, none cheap on GEX44): C01/C02 live prompt-source audit, D01/D02/D04 registry semantics, E01-E04, F01-F05, G, H03-H09. Phase 8 stays PARTIALLY_PROVEN.
DECISION: stop probing here (diminishing return; cheap probes exhausted in campaign A); Phase 3 next. Safe: internal.
Spend: UNMEASURED (supervisor 13.8M at epoch start).
Meta: (1) the "UNKNOWN (not derived)" pin had to become an evidence-backed predicate, again. (2) LIVE_READ numbers were unlabeled, so a count needed a re-read for context before it could be a denominator. (3) Many scenarios were already enforced by owners but untagged: naming is not driving, so each got a pole. (4) Tests with an unmeasured input must supply it or the unmeasured branch fires first (glass_plan). (5) Next: Phase 3 DesignHub + Impeccable reads.

### Phase 3 (epoch 4, CLOSED: BCAP2B-01 and BCAP2B-03 done; BI-27 COMPARE only, BI-30 principles only)
read (pinned 148e8c3f, raw files, tree 823 blobs): lib/mockups/registry.ts (19 templates: business-card, letterhead, envelope, sticker, poster, billboard, merch, coffee-cup, shopping-bag, id-badge, laptop-landing, desktop-dashboard, mobile-app, app-store, smartwatch, lock-screen, tablet, browser-tab, email-signature) and lib/guidelines/registry.ts (22 book pages: cover, introduction, mission, logo-usage, clear-space, minimum-size, incorrect-usage, co-branding, color-palette, color-usage, data-visualization, typography, typography-usage, iconography, imagery, spacing-layout, components, accessibility, voice, social-media, color-tokens, scale-tokens); lib/guidelines/outline.ts adds PDF bookmarks + contents links via pdf-lib low-level objects. Technique candidates (MIT, principles-only until header scan): the 22-page book order for BI-24, bookmark/link outline for the PDF, the 19-template catalogue vs modules/ccf/brand_release.py 9 contexts. NOT yet written to DESIGNHUB_PROBE.md, REUSE_LEDGER row still HYPOTHESIS.
next: write the DesignHub READ section + flip ledger row; then Impeccable detector: list is in $CLAUDE_JOB_DIR scratch only (impeccable.tree.json lost with the session); re-fetch tree at b49177d3 (`git/trees/<sha>?recursive=1`), find detect*/antipattern* paths, read, decide port (Apache-2.0, keep NOTICE) vs principle. Gate: tools/test_bcap2_brand.py. Then Phase 4.
Spend: UNMEASURED.

Epoch 4 closed Phase 3: DESIGNHUB_PROBE.md READ section (catalogue 19 vs 9 contexts, 22-page book order, outline technique; no code admitted, bodies unread); IMPECCABLE_AUDIT.md detector READ (62 rules, 31 slop / 31 quality, Rust workspace -> PRINCIPLES ONLY, no port, no NOTICE needed); ledger rows both READ. brand gate PASS, done_gate PASS. DECISION: no port of Impeccable (Rust+CDP, unreviewable size, a third already owned by taste.py). Safe: internal, reversible. Next: Phase 4 (BI-24 illustrated PDF), then GSD phase dirs for 1-3.

### Phase 4 (epoch 4, CLOSED: BCAP2B-04)
done: `modules/ccf/brand_book.py` (pure Python, no render toolchain needed): 7-page book (contents, logo usage, clear space, minimum size, incorrect usage, colour palette, typography), mark embedded once as the PNG's own IDAT Image XObject, bookmarks + contents links; `package` CLI writes `brandbook.pdf` beside the kit PDF (skips with a printed reason when the concept declares no #RRGGBB or no font). Gate: 15 BI-24 checks in tools/test_bcap2_brand.py, poles for wrong mark, kit-PDF-as-book, truncation, stripped outline, link to non-page, mark never drawn, broken/RGBA PNG, bad hex, no fonts, empty palette; each pole fails for its own reason. Independent read with pypdf 7.1.1 + PyMuPDF (scratch venv outside the repo): 7 pages, 7 bookmarks, 6 links, a rendered page looked at. done_gate PASS, ccf/brand_book in NEW_MODULES.
Limits stated: base-14 fonts only (brand fonts are named, not rendered); typography page names the declared font; palette from literal hex only; a real brand-font render and legal/visual review are laptop plane.
DECISION: no scratch-venv toolchain in the product path (only used to verify). Safe: internal. Next: Phase 5.

Epoch 4 end: GSD phase dirs 01-04 written (PLAN/SUMMARY/VERIFICATION), roadmap boxes 1-4 ticked. Next: Phase 5 (BI-15..35 on the CLI path).

### Phase 5 (epoch 5, CLOSED as scoped: BCAP2B-05; BI items stay PARTIALLY_PROVEN)
done: `package` stage in `modules/ccf/creative_checks.py` (12 checks: BI-15,17,18,19,20,22/23,25,26,28,29,31,35), called from `cli.cmd_package` before any file is written, same report/enforce/UNASSESSED rule as slice A; file inputs project-relative only (traversal and missing files are FAIL). Gate `tools/test_bcap2_cli15.py` in done_gate (56+ checks, each check driven pass/fail/absent through the real CLI, 2 mutants). AC1 held: test_ccf 16, test_asc_ccf, test_bcap2_brand, test_bcap2_activation all PASS. Registry LIBRARY entries for brand_color/brand_release/brand_review/trace_lane removed (now reachable).
open: BI-16 CCF adapter + cross-platform hash (LAPTOP_STEPS B2); BI-34 `applicable` is an agent-prompt router, not a project-config check, left LIBRARY-style; no real font/render/benchmark run exists, so every check reports on declared inputs only. Nothing is ACTIVATED (law 4 needs execution evidence on a real project, none exists).
DECISION: no adapter for sigilgen without the cross-platform result and a Node dependency decision. Safe: internal, reversible.
Spend: UNMEASURED. Meta: (1) a stage with many checks needs the check name threaded through the test runner, not parsed from the project dir name. (2) Declared-path inputs need a traversal refusal from day one. (3) Wiring let four registry LIBRARY notes go stale; removed. (4) Pole matrix per check (pass/fail/absent) was cheap once data-driven. (5) Next: Phase 6 SaaS style 3.
