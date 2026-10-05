# Stage 0 evidence -- TOK-18 pre-rearm (sealed 2026-10-05, pane 87601e81)

Unit everywhere: **processed tokens = input + cache_write + cache_read + output**, deduplicated by message id.
Scripts are zero-model (they read transcripts only). Copied from session scratchpads so they survive `/clear`.

## Measured (status SEALED / REUSE)
| workload | processed | calls | per-plan | first-call floor (median) | floor share | per-call median | script |
|---|---|---|---|---|---|---|---|
| KSR recon-factory m-caadc51ab81e | 273,912,110 | 1,141 | 24-28M (ph1 48.8M/2, ph01.1 170.2M/6) | 93,364 (workers ~122k) | 46.8% | 228,955 | `ksr_floor.py`, `mission_tokens.py` |
| KME SkyParty m-2648e6c25747 (workers 67ca9fa1, 41e4bea7, 2f9049a0) | 107,407,089 ctx + 351,353 out | 393 | 11.9M (9 plans 01-01..04-02) | 103,978 | 49.6% | 275,959 | `kme_sky.py`, `kme_find.py` |

KSR context classes (`mission_prefix.py` = KME `recon_cost_miner` unchanged; control delta +0): instructions 14.7%,
system_prompt 13.1%, listings 6.9%, file_text 12.2%, assistant_output 5.8%, tool_text 5.2%, hook_context 1.8%,
unattributed 39.5% (first-call unexplained median 59,881 on main sessions). Output: `prefix_out.txt`.

Fresh-worker ceiling on KSR (same call count, `ksr_floor.py`): N=10/S=10k 43.3% ... N=40/S=30k 23.0%. Ceiling, not saving.

Instrument note: `kme_sky.py` first returned 0 workers (a 400 KB head filter); session 2f9049a0 was the positive
control (157 hits), and `kme_find.py` located the card on line 1 of the three workers.

## Owner map (`owner_map.md`, agent output, REUSE WITH CORRECTIONS)
It cites `gen2/SPEND.md`; the real file is `vault/programs/skill-capability/gen2/SPEND.md`. Its "gen1 488.6M processed /
78M weighted" is the skill-capability programme, not Cognitive Economy. Items 14, 18, 19 UNKNOWN. That agent cost
7.84M processed = 45% of Stage 0.

## External baseline (Owner file, not copied)
`Downloads\Dataset CPP CW Ops Optimization Mission 1, 1.md` lines 5-30: InfinityOps odr-device-trust phases 1-3 =
374.5M processed / 1,531 messages, 17.8-25.5M per plan; Phase 4 so far 41.6M. Its "Phase 4 = 54-100M, ~70M" is
plans x average (old-architecture reference only). Floor split 35K/45K/13K/12K/9K and role split planner 14.6M /
researcher 8.9M / verifier 7.4M / executor 1.6M: **not found on disk -> UNVERIFIED**, measured in Gen2.1 A0.

## Spend
Stage 0 + plan writing, this pane: 17.4M processed (92 calls, 39 of them subagent) at the Gen2.1 approval.
That is sunk campaign cost; Gen2.1 incremental spend is counted from the anchor in the RESUMPTION file.
