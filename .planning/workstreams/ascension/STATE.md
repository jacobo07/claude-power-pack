# STATE: ascension

status: ARMED 2026-11-16 on GEX44 (Owner "hazlo en la GEX44")
current_phase: 3
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

### Phase 2: Reconciliation ledger -- DONE (GEX44, 2026-11-16)
- Tool: `modules/backlog_autopilot/ledger.py` (extends backlog_autopilot, consumes inventory identities; fields map to CapabilityContract owner/entrypoint/consumers/tests/retirement). Artifact: `vault/programs/ascension/phase2/reconciliation_ledger.json`. Home decision: extend backlog_autopilot (no PLAN-mode needed, no new system).
- Gates: `python3 tools/test_asc_ledger.py` exit 0 (V-ASC-LED, 17 checks): seeded false absorption -> CLAIM_REJECTED; dropped BLOCKED row, forged states, hand-inflated ratio all FAIL verify; recorded exit-0 evidence is the only way OPERATIONAL numerator rises. `python3 tools/test_gsd_mission_parked_label.py` exit 0 (V-PARK): RED first (4 FAIL) then GREEN; owner_hold 49/49, surface 6/6, test_gsd_mission 248/248 unchanged. Fix: `display_state` added to `gsd_mission status` rows; raw `state` untouched.
- Measured (static, real tree): RECONCILIATION 372/471 = 0.79 (rows with proven state+owner+destination); OPERATIONAL 0/373 (no execution evidence recorded yet, by construction). By state: BACKLOG_ONLY 98, SOURCE_FOUND 127, IMPLEMENTED 39, ACTIVATED 206 (static wiring only), CLAIM_REJECTED 1, UNKNOWN 0; BLOCKED rows in denominator: 3.
- Spend: UNMEASURED.
- Meta: (1) First run read 471/471 and 211 ACTIVATED: instrument too generous (BACKLOG_ONLY counted as reconciled; docs/JSON counted as consumers). Tightened both; numbers fell to 0.79 and 206. (2) ACTIVATED is still static wiring; a spot-check found plans citing a path in passing. Never promote it without execution evidence. (3) CLAIM_REJECTED=1 on real data is low recall: most sources do not declare Status or cite paths, so false-absorption detection is proven on fixtures, not yet on real breadth. (4) UNKNOWN: license is UNKNOWN for every row (no license probe yet; Phase 3 license check must supply it); execution evidence NOT_OBSERVED for all. (5) Next: Phase 3 web slice; it will produce the first execution evidence.
