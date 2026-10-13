# Phase 5 Validation Map

Plane for every row below: laptop (Windows, PowerShell 5.1) unless a drill is UNRUN, then Linux plane (coordinator).

| Req | Behaviour | Gate (suite) | Plan | Red-first | Drill |
|---|---|---|---|---|---|
| D15 | VALIDATE only from re-derived premises; event is a claim | V-JV-CONTROL-VALIDATES, V-JV-FORGED-EVENT-REPLAYS (`GSDX_JUDGE_VALIDATE_PASS`) | 05-01 | yes | d1 |
| D15 | ineligible/fresh-required/unknown -> REPLAY | V-JV-FRESH-REQUIRED-REPLAYS, V-JV-UNKNOWN-REPLAYS | 05-01 | yes | d2 |
| D15 | gate weakening REFUSED on VALIDATE path | V-JV-WEAKENED-GATE-REFUSED | 05-01 | yes | d3 |
| D15 | epoch still UNJUDGEABLE; legacy receipt equal | V-JV-EPOCH-STILL-REFUSES, V-JV-LEGACY-RECEIPT-EQUAL | 05-01 | yes | -- |
| D16 | bound = min(posture, memory, env); default 1 | V-RP-SERIAL-IS-DEFAULT, V-RP-MEMORY-LOWERS (`GSDX_REPLAY_PARALLEL_PASS`) | 05-02 | yes | d5 |
| D16 | independence respected, all joined, order kept | V-RP-RESOURCE-SERIALISES, V-RP-ALL-JOINED, V-RP-RECEIPT-EQUALS-SERIAL | 05-02 | yes | d4 |
| R05 | A->B->A live read stale; snapshot read survives | V-ABA-LIVE-REWRITE-STALE, V-ABA-SNAPSHOT-READ-SURVIVES (`EVB_ABA_PASS`) | 05-03 | yes | d6, d7 |
| D17 | review event lands; stale only where moved; builder cannot review | V-REV-STALE-WHERE-MOVED, V-REV-BUILDER-CANNOT-REVIEW (`GSDX_REVIEW_PASS`) | 05-04 | yes | d8, d9 |
| D17 | concurrent reviewers all land once, bounded retry | V-REV-CONCURRENT-ALL-LAND, V-REV-RETRY-BOUNDED | 05-05 | yes | -- |

Regression (must not drop): `PCC_REPLAY_PASS` 28/28, `PCC_SEMANTICS_PASS` 48/48, frontier 40/40, invalidation 26/26,
judge 11/11, `EVB_PASS`. Liveness exit 0. Goal mutation suite: UNRUN on laptop (packet rule).

Parallel replay bound, stated once: `min(frontier.bound(state), memory_bound(free_ram_mb), GSDX_REPLAY_MAX)`;
memory < 1536 MB or unreadable -> 1, < 3072 MB -> 2; kill switch `GSDX_FRONTIER=off` -> 1.
