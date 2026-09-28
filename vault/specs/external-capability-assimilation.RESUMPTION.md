# External Capability Assimilation — resumption contract

**Read this first; it is self-contained.** Spec: `vault/specs/external-capability-assimilation.md`.
Worktree `C:\Users\User\Apps\pp-assim`, branch `feat/external-assimilation` (off
`feature/knowledge-acquisition@2b6f183`). Source package: `Downloads\for cpp-gsd-long.zip`.

## Thesis
Every capability of Genesis Suite (21 modules + runner), Context Budget, the event-driven loop
kit and the self-continuation protocol gets ONE CPP owner and disposition, recorded in
`vault/assimilation/genesis-2026-09/ASSIMILATION_MANIFEST.json`. Hot path native Python; cold
path vendored MIT Node through `modules/external_assimilation/node_bridge.py`. Unlicensed inputs:
ideas only, no bytes.

## Owner decisions (2026-09-28)
Worktree, full scope, hybrid runtime, autonomy gate LIVE (not shadow), night research on the
Sovereign VPS only (Node there is v22.22.2 < ^22.23.2 — install user-level Node 24 first),
experiments hybrid dry-run/quota, push everything.

## Sealed
`f9a8391` T1 vendor + provenance + bridge + manifest · `6ab1b06` adapter moved out of ignored
`/lib/`, git resolved off-PATH, tamper drills.
Gates: `python tools/test_genesis_bridge.py` 9/9 · `python tools/test_assimilation_manifest.py`
9/9 (runs LIVE proofs) · `python tools/test_vendor_provenance.py` 5/5 ·
`python tools/vendor_provenance.py verify --fresh-checkout` VALID 341+12.

## Do not touch
Live mission `m-916e905e23d4` (S10 proof) runs from the MAIN checkout; `gsd_mission.py` /
`gsd_epoch.py` there are owned by panes c2/e9. Edits here are additive and merged only after
re-reading the target branch HEAD. The Ralph hook is loaded straight from the main checkout
(`~/.claude/hooks/hook-dispatcher.js:172`): merging = going live.

## Next 3 actions
1. T2: `modules/context_budget/` native port (UNMEASURED state) + `tools/fresh_context_tax.py` run on
   the S10 mission's real epochs; then the pressure reading as evidence in epoch receipts.
2. T2: `tools/source_packet.py` (bridge → taskContext/sourcePackets) consumed by `render_card`.
3. T3: autonomy gate extending `modules/decision_review/decision_kernel.py`; provider breaker
   beside `quota_hold` (`tools/gsd_mission.py:1272`).
Flip each manifest entry to LIVE with a proof command as it lands.

## Start instruction
`git -C C:\Users\User\Apps\pp-assim log --oneline -5`, run the four gates above, then T2.
Trust git and the gates, not this file.
