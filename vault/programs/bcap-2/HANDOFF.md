# BCAP-2 HANDOFF (branch mission/bcap-2-run, 2026-11-19)

Closeout gate: `python3 vault/programs/bcap-2/done_gate.py` -> exit 0 = consistent and honest (all 8 item gates green, no orphan BCAP-2 module,
ledgers parse, nothing claims ACTIVATED). It does NOT mean any backlog is closed: **no item is ACTIVATED; every item is PARTIALLY_PROVEN**
under plan law 4. Source of truth per item: `.planning/workstreams/bcap2/STATE.md` (residuals) + `vault/plans/deferred-backlog.md` rows.

| Item | Gate | Verdict | Main residual |
|---|---|---|---|
| 01 DBG | test_bcap2_dbg 37 | PARTIALLY_PROVEN | upstream scan; floor_guard not emitted live by done_gate |
| 02 TDD | test_bcap2_tdd 65 (needs pytest+coverage interpreter, done_gate finds one) | PARTIALLY_PROVEN | upstream unfetched; mutation oracle measured only in venv |
| 03 AGSK | test_bcap2_agsk 55 | PARTIALLY_PROVEN | 34 rows HYPOTHESIS, 7 UNVERIFIED |
| 04 Anime.js | test_bcap2_animejs 35 | PARTIALLY_PROVEN | real-browser checks (laptop) |
| 05 Synsation | test_bcap2_synsation 35 | PARTIALLY_PROVEN | videos not on GEX44; browser-real (laptop) |
| 06 SaaS styles | none (scan only) | PARTIALLY_PROVEN | **Owner decision**: style 3 family F11 vs structural axis (pick b recorded) |
| 07 Brand | test_bcap2_brand 71 | PARTIALLY_PROVEN | no real render; upstream unfetched; BI-08..35 mostly open |
| 08 21 resources | test_bcap2_d21 28 | PARTIALLY_PROVEN | 23/36 scenarios undriven; Workstreams B-H not started; no network |
| 09 Ruflo | test_bcap2_ruflo 69 | PARTIALLY_PROVEN | activation refused; no provenance attestation; advisory fixes unverified at runtime |

Known pre-existing failure, not from this work: `test_cdio_componentry` V-CMP-WIRING (EXPECTED_DATASETS = 12 vs live mirror).
Nothing pushed, no PR, no UKDL/HR promotion (nothing met the evidence bar; deltas stay in vault/programs/bcap-2/).

## Next, in order
1. One batched read-only upstream fetch pass for Phases 1, 2, 3, 7, 8 (all rows still HYPOTHESIS / live_verified false). Network works on GEX44.
2. Phase 8 Workstreams B-H (23 scenarios), Phase 7 BI-08..35.
3. Laptop: `vault/programs/bcap-2/LAPTOP_STEPS.md` (browser-real, videos, Ruflo canary drill).
4. Owner: style-3 decision; approval before anything leaves the Ruflo sandbox (`/home/kobii/ruflo-sandbox-bcap2`, 1.2 GB, `rm -rf` to undo).
