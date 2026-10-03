# Handoff to the cognitive-economy owner: CE done-gate is unpassable (selftest stale)

Owner: `tools/test_cognitive_economy_program.py` (CE program, mission m-fdefb0fca0c0). Not edited by this program.

## Defect
`V-CEP-REAL-HANDOFF` (selftest, lines ~491-503 at HEAD 6d3113b8) assumes "the plan file's only commit is C0
1cabd117". The plan was edited again by the freeze commit fa9ae2ed and by 8b62b6ce, so `handoff_landed` frozen
at 1cabd117 now returns True (a later commit touches the file). Both poles read True, the selftest FAILS, and
`--final` always appends `S0 selftest failed`: the CE done-gate cannot pass even with all 20 pillars closed.

## Reproduction
command: python tools/test_cognitive_economy_program.py --selftest
observed 2026-10-03: `FAIL V-CEP-REAL-HANDOFF (frozen at C0 -> True, frozen before C0 -> True)`, rc 1.
Why unseen: the 30/30 selftest in the CE execution log ran before fa9ae2ed was committed.

## Proven fix (applied in wrappers, not in the CE file)
Read the poles from the probe file's history instead of hardcoding them: frozen at its newest commit ->
False; frozen at the parent of its first commit -> True. Implemented as `real_handoff_control` in
`tools/test_skill_capability_program.py` and `tools/test_incremental_cognition_program.py`. Mutation drill
(handoff_landed forced True, then False): the control goes red both times; unmutated it is green.

## Reopen / close condition
Closed when the CE file computes the poles from history (or the CE ledger records why its own `--final` is
judged through a wrapper). Until then, CE `--final` rc 1 is this defect, not a pillar failure.
