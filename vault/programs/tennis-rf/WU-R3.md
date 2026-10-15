# WU-R3 -- gsdx_chain: strategy exhaustion -> transition packet, and unbooked-coordinator guard (PP global, additive)

Plan: `vault/plans/recon-factory-locality-routing-2026-10-15.md` sections 6, 11 (Owner approved 2026-10-15 "y", charged
to tennis-rf as its canary). Budget: <= 2.0M; stop and write the receipt at 1.7M.

CAUTION: `tools/gsdx_chain.py` is LIVE for other chains (gsdx-fabric ticks every 10 min in this tree). Every change is
additive, default-preserving for a chain without the new keys, behind kill switch `CPP_CHAIN_STRATEGY=off`, and the full
existing test file must stay green before commit. Commit by pathspec only; the PP tree has >1000 dirty paths of others.

Facts (do not re-derive): `decide()` returns `{"action": "complete"}` (:416) when all units are done and
`residual_exhausted` "Owner decides" (:91); both are SILENT (:503). No next-strategy code exists. Coordinator spend was
off-ledger 19.25M for pane 85b7c296 until settled into L40 on 2026-10-15: goal_settle without `--measured` caps a session
with a mark at mark+holds (`tools/mission_spend.py:536-544`), so later coordinator spend can never be booked by default.

Steps:
1. Strategy exhaustion. Optional chain key `strategy` -> path of `strategy.json` {strategies: [{id, class, status
   ACTIVE|EXHAUSTED|RETIRED, evidence, next: [candidate ids]}], candidates: [{id, packet, route, expected_evc,
   info_gain, capital, termination}]}. When decide() would return `complete` or `residual_exhausted` and `strategy`
   is set: mark the current strategy EXHAUSTED (with the triggering receipt), write
   `<programme>/strategy-transition-<ts>.json` (exhausted strategy, proof, residual, candidates ranked by expected_evc
   then info_gain, capital need vs envelope remaining). If the top candidate has a packet, positive info_gain and fits
   the envelope: append it as a unit (after = last unit) and return `arm` on the next tick. Else return
   `strategy_exhausted` (SILENT) carrying the packet path. Bound: at most 3 appended units per strategy file; never an
   appended unit whose packet path already ran.
2. Coordinator guard. Optional chain key `coordinators` (session ids bound to the goal). Before an `arm`, measure each
   coordinator transcript (`session_tokens`) against its ledger mark; if unbooked > 2,000,000 return `coord_unbooked`
   {sid, unbooked} instead of arming (SILENT). Kill switch shared.
3. Accounting fix: `goal_settle` gains `--coordinator` meaning: settle the full transcript delta above the mark (no
   ceiling cap), refused unless the current lease's succession id is `<goal>:coord-<sid8>` (prevents booking onto a
   unit lease, memory feedback_goal_correct_does_not_unbook_lease).
4. Tests (`tools/test_gsdx_chain_strategy.py`, V-CHAIN-STRAT-*): complete+positive candidate -> unit appended and armed;
   complete+no positive candidate -> strategy_exhausted with packet; residual_exhausted path same; cap of 3 holds;
   chain without `strategy` key -> identical old output; kill switch; coord guard both poles (unbooked 2.5M refuses,
   0.5M arms); --coordinator refused on a unit lease, accepted on a coord lease. Mutation drills: remove the append ->
   red; remove the guard -> red. Run the existing gsdx_chain test file too.
5. Wire tennis-rf chain.json: `strategy` -> `vault/programs/tennis-rf/strategy.json` (strategies: S-BULK-TRANSFER
   EXHAUSTED evidence D12c; S-LOCAL-ROUTING ACTIVE), `coordinators: ["85b7c296-0977-4d61-a87c-546b6c052ec8"]`.
   `gsdx_chain.py tick --dry-run` must still return the next unit for tennis-rf and unchanged output for gsdx-fabric.

Done-check: new + existing tests exit 0, both mutation drills red, both dry-runs as stated.
Receipt `WU-R3-receipt.md`: test lines, drill results, dry-run outputs, commits.
