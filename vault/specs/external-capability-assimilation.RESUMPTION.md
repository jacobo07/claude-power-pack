# External Capability Assimilation — resumption contract

**Read this first; it is self-contained.** Spec: `vault/specs/external-capability-assimilation.md`.
Worktree `C:\Users\User\Apps\pp-assim`, branch `feat/external-assimilation` (off
`feature/knowledge-acquisition@2b6f183`, pushed to origin). Source: `Downloads\for cpp-gsd-long.zip`.

## Thesis
Every capability (Genesis 21 modules + runner, Context Budget, loop kit, self-continuation) gets ONE
CPP owner/disposition in `vault/assimilation/genesis-2026-09/ASSIMILATION_MANIFEST.json`. Hot path
native Python; cold path vendored MIT Node via `modules/external_assimilation/node_bridge.py`.

## Owner decisions (2026-09-28)
Worktree, full scope, hybrid runtime, autonomy gate LIVE, night research VPS-only (VPS Node v22.22.2
< ^22.23.2: install user-level Node 24 first), experiments hybrid, push everything.

## Sealed
T1 `f9a8391` `6ab1b06` vendor+provenance+bridge+manifest · T2a `0efa0ba` Context Budget as epoch
evidence + Fresh Context Tax (median 185,930 tokens fixed bootstrap; 389/445 sessions were quota
refusals) · T3a `6fedb1d` provider circuit breaker · T3b (this commit) autonomy gate extending DRK +
rubric/wake-order in the Ralph Stop hook + decision receipts.
Gates: test_genesis_bridge 9/9 · test_assimilation_manifest 9/9 · test_vendor_provenance 5/5 ·
test_context_budget 8/8 · test_gsd_epoch_context_budget 6/6 · test_fresh_context_tax 3/3 ·
test_provider_breaker 15/15 · test_gsd_mission 191/191 · test_gsd_epoch pass · test_autonomy_gate
22/22 · node tools/test_gsd_stop_continuation.js 17/17.

## NOT YET LIVE
Nothing is merged into `feature/knowledge-acquisition` (the checkout hooks load from). Going live =
re-read that branch's HEAD, merge `feat/external-assimilation`, rerun the gates above there.

## Next 3 actions
1. Manifest: flip self-continuation-rubric / -stop-directive / -decision-log to LIVE (proofs:
   test_autonomy_gate.py, test_gsd_stop_continuation.js); add rubric + WAKE_ORDER to
   `render_card` in tools/gsd_mission.py (wakeup-continuation-order).
2. Merge to `feature/knowledge-acquisition` (go-live), push.
3. T4–T12 per spec: source_packet.py, plan-graph wave check, review/evidence intake, regression
   memory, change impact on audit_cache, routing metrics, verified reuse, paired experiment,
   task adaptation, charter lab, night research on VPS, live smoke mission, red team, KV/UKDL.

## Start instruction
`git -C C:\Users\User\Apps\pp-assim log --oneline -8`, run the gates, then action 1.
