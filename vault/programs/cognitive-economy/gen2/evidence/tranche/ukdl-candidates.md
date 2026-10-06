# UKDL candidates (WU4). Not written to ukdl-universal.md: that file holds 661 lines of another writer's uncommitted hunks.
Duplicate grep on ukdl-universal.md (match counts, loose patterns): call-allowance=0, contract-test/key-set=0, control-on-red-pole=15, like-for-like=0. Counts >0 may be unrelated hits; verify by reading hits before promoting. Earlier broad grep (first 25 hits) showed no entry for these four rules.
## Process Rule: PR-PACKET-CALL-ALLOWANCE-001 (project-scoped: cognitive-economy tranche)
A packet's call allowance = token budget / measured per-call prefix, stated in the packet; never an independent call count. Evidence: WU1 0.6M cap + 25 calls at ~100-125k/call spent ~1.5M; planning pane 33 calls, 5,856,325 (commit b67f5d8f context in WU1/WU4 receipts). Universal once a second tranche confirms.
## Trap: T-JSON-CONTRACT-KEY-WITHOUT-TEST-001 (universal, 1 incident)
Adding a key to a JSON output contract without updating the contract test commits a red suite (V-FLOOR-JSON 60/61, fixed b67f5d8f 61/61).
## Trap: T-DRILL-CONTROL-ON-RED-POLE-001 (universal, 1 incident)
A mutation drill whose unmutated control already sits on the red pole proves nothing; assert the control is green first. WU1: unmutated floor check already exit 1.
## Trap: T-CROSS-PROJECT-FLOOR-COMPARE-001 (project-scoped)
Admitting a cwd difference makes project-scope rows (memory_project +34,478 of +37,683) a different-project comparison, not a regression. Label them non-comparable or record a per-cwd reference.