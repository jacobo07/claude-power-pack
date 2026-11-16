# STATE: ascension

status: ARMED 2026-11-16 on GEX44 (Owner "hazlo en la GEX44")
current_phase: 2
authority: 120M processed tokens + 3 x 40M auto top-ups (granted only with commits outside .planning/ since the last grant)
spend: laptop planning pane 72497d57 before arm: UNMEASURED
RAM at arm: laptop 726 MB free / 32,061 MB; GEX44 39 GB available
base: 2f9386f6 (laptop feature/knowledge-acquisition, committed state only)

## Phase log
### Phase 1: Obligation inventory -- DONE (GEX44, 2026-11-16)
- Tool: `modules/backlog_autopilot/inventory.py` (extends backlog_autopilot; discovers, never curates). Artifact: `vault/programs/ascension/phase1/obligation_inventory.json` (620 raw records, 471 obligation identities, 0 unreadable).
- Gate: `python3 tools/test_asc_inventory.py` exit 0 (V-ASC-INV, 14 checks): seeded omission FAILS, post-inventory new source FAILS, semantic duplicate collapses to one identity, distinct item stays separate, unreadable source fails, clean fixture passes. Real-tree verify PASS against an independent os.walk census.
- Spend: UNMEASURED (mission_spend session id not available in this session).
- Meta: (1) wrong assumption: real tree has duplicates to collapse. Measured 0 at Jaccard 0.85; near-pairs 0.60-0.71 are distinct, so no collapse is claimed on real data. (2) The independent census caught a real discover() omission (nested RESUMPTION files), fixed. (3) Unreachable knowledge: Taste Skill is only a name in keep-lists (REFERENCED_ELSEWHERE, laptop step 1); ASTRYX NOT_OBSERVED on GEX44 (laptop step 2); Design Index referenced in code, no obligation source. (4) UNKNOWN: every state is source-claimed only, no implementation status yet. (5) Next: Phase 2 ledger on top of these identities + `gsd_mission status` parked label RED->GREEN.
