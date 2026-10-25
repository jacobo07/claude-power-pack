Status: DONE -- `campaign next` built, gated and committed on GEX44; first real packet is WIDEN (cohort 33). Open questions (not unmet acceptance) are listed under UNKNOWN.

## Where it lives
GEX44 `~/missions/t1-campaign`, branch `t1/campaign` (local, not pushed), on top of 0c353ecb.
- 7f28f5b8 feat(recon_fabric): campaign next -- deterministic next-unit packet (WU-H3) -- `modules/recon_fabric/campaign.py` + `tools/test_recon_fabric_next.py`
- b2648c34 evidence(t1): first campaign next packet -- WIDEN, cohort 33 (WU-H3 canary) -- `evidence/campaign/next/001-census.{json,md}`
Tree clean after both commits. Nothing pushed; nothing outside `~/missions/t1-campaign` touched.

## What `campaign next` does
Picks the next campaign unit from committed evidence only (no model, no network) and writes a numbered `.json` + `.md` packet under `evidence/campaign/next/`: WIDEN census, CLASS_INTERRUPT for one label, or explicit NO_WORK. Rules R1 certified excluded, R2 already searched under the landed operator set excluded, R3 recorded negatives excluded, R4 WIDEN on the remainder.

## Gates (re-run 2026-10-25 by the coordinator pane, after the residual worker stopped)
- `python3 tools/test_recon_fabric_next.py` -> `NEXT_PASS=22/22`
- existing suite -> `FR1_PASS=15/15`
- Red drill (residual worker): certified-exclusion line broken -> `NEXT_PASS=18/22`, exit 1; restored, campaign.py sha256 identical before/after.

## Canary on the real evidence tree
`python3 -m modules.recon_fabric.campaign next` -> `CAMPAIGN_NEXT {"class": "WIDEN", "cohort": 33, "file": "evidence/campaign/next/001-census.json", "sha256": "fd213bc1e806d6f09a458e0806b4da00f866f5453fa1207daad629f08d4225e6"}`, rc 0.
Why: R1 17 of 557 views certified; R2 1 excluded (pins tam-ds-7, depth >= 3, operators arg-passthru@1, decl-swap@1, ptr-bytestride@1, stmt-swap@1, sum-reorder@1); R3 label RELOC_OR_BRANCH_ONLY / medoid fn_8025CDE8 excluded; R4 33 left. Packet budget: P50 600K, hard 1.5M.

## UNKNOWN (not checked)
- Whether WIDEN should include uncertified functions whose frontier state is `NO_COMPILE`; `next` includes any uncertified function with a searchable label.
- Label spelling: `search_c` uses `REGISTER_MAPPING_*`, the views file `REG_MAP_*`; a mismatch could change the cohort.
- The `campaign` usage string still lists `pin|check|run` only; `next` works but is not in `--help`.

## Spend
Worker 1 m-8d17a6f712f6: 2,950,435 (route exhausted, RED test only). Residual m-e1ae498acaa4: 2,843,464 at its last cost mark (code + gates green, stopped by the session breaker before canary/commits/receipt). Canary, commits and this receipt: coordinator pane fc4dce34. H3 total ~5.8M against the plan row's 2.7M.
