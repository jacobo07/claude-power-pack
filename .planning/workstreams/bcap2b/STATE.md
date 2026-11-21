# State: bcap2b

Armed from laptop HEAD after 8af361d1 (2026-11-21). Campaign A state: `.planning/workstreams/bcap2/STATE.md` (read-only
input). At the start: done_gate BCAP2_DONE_GATE PASS, every item PARTIALLY_PROVEN, none ACTIVATED.

## Phase log

### Phase 1 (IN PROGRESS, epoch 1 ended at context wall)
done: brand upstream read (8/10 repos READ at pinned SHA, `vault/programs/bcap-2/brand/UPSTREAM_READ.md`; ledger rows flipped; brand gate PASS). DesignHub + Impeccable rows stay HYPOTHESIS -> Phase 3.
done: AGSK batch B (17 rows) -> `vault/programs/bcap-2/upstream-read-b/AGSK_B_rows.tsv` (3 UNVERIFIED resolved to EXTEND, 6 wrong owner paths found). NOT yet merged into DISPOSITIONS.md; gate `tools/test_bcap2_agsk.py` V-AGSK-LEDGER-ONLY-PILOT-READ must be relaxed (READ rows need evidence) when merging.
done: D21 page reads, 21 sources / 22 URLs all HTTP 200 with a generic UA (designmd.ai now 200): `design-resources/LIVE_READ.json` (title, observed numbers, licence words). SOURCES.json NOT yet updated (live_verified still false; gate lines test_bcap2_d21.py:26,116 pin that and need new poles: live_verified only with LIVE_READ evidence). Observed denominators noted: Kinetics page 162 effects (README said 162, site index 144), 3dicons ~1400+ renders, Component Gallery 2,671/60/95.
AGSK batch A finished after the wall: 17 rows in `upstream-read-b/AGSK_A_rows.tsv` (complete, committed); merge with batch B into DISPOSITIONS.md.
Spend: not measured this epoch.
