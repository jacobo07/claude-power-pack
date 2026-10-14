# WU-P52a receipt (mission m-53847a002b65)
Status: DONE
Commits: 07aa3908 (05-2-PLAN-CHECK.md + findings a-g applied to plans 01/02/04/05), test RED commit (see git log, "05-2-01 trust suite RED 0/7"), 8e7f09d4 (05-2-01 implementation + SUMMARY).
Gate GSDX_TRUST_PASS=7/7  threshold=7/7  (plane: Windows laptop); RED was 0/7 for the right reason (features absent).
Regress (Windows laptop): GSDX_JUDGE_VALIDATE_PASS=11/11; GSDX_INVALIDATION_PASS=26/26; GSDX_CERTIFICATE_PASS=7/7; GSDX_PCC_SEMANTICS_PASS=48/48.
Liveness (Windows laptop): reachability.py exit 0, gate offenders: 0 (gsd_x/goal/trust declared PLANNED in the registry).
DENOMINATOR rows moved: none yet (N01 N02 N05 N23 get their evidence line in 05-2-05; N16 N17 N19 D11 stay open).
Deviations: authority id is `gsdx-sweep` (dotted ids are read as event types by V-PCC-VOCAB-DECLARED). Phase 2 pins edited for the deliberate `authority.revoked` landing: spec S7 row, a sample payload and len==7 in test_gsd_x_goal_pcc_semantics.py.
Drills t1..t7: UNRUN (05-2-05). replay/frontier/hermetic regress: not run this unit (05-2-05).
Open points / next: (1) 05-2-02 forgery: trust.verify_certificate + inherited_event_ok registry check (AUTHORITIES membership, F6), contract_hash legacy = sha256 of first declared contract. (2) 05-2-03, 05-2-04 (verification_set through combine_states), 05-2-05 (done-gate registry, V-DONE-COUNT>=40, MIGRATION-ONCE, drills).
(3) is_trusted only checks authority+lineage presence; registry/ancestry validation is 05-2-02.
Untracked noise left unstaged as instructed (packets/*.partial.json, WU-P52-receipt.md, LEARNINGS_PENDING.md, vault/specs/salvage/).
HANDOFF NOTE: WU-P52a done