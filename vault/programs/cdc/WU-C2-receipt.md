# C2 receipt
Status: DONE

Commits: worktree 512af829; live landing sha 512af829 (land_worktree LANDED, tests before/after rc=0).
- PROVEN: one enum (ZERO/DETERMINISTIC/BOUNDED/NOVEL/OWNER_COGNITION) + legacy aliases in tools/cognitive_effects.py; plan in C2-decision.md.
- PROVEN: route_admission.admit -> REFUSED_EFFECT for ZERO/DETERMINISTIC route with workers and no deopt; with deopt ADMISSIBLE; absent effect = BOUNDED (defaulted flag). Kill switch CDC_EFFECT_GATE=off; missing module fails open.
- PROVEN: mutation drill (CE_DRILL_DIR, gate disabled) turns V-CE-03/04/05/06/08 red.
- PROVEN: tier_for accepts enum names; existing tier tests 15/15, cost_to_completion 24/24.
- NOT_PROVEN: the effects gate registered in test_matcher_liveness (it is a pure function in admit, not a hook).
- INCONCLUSIVE/pre-existing: test_route_admission 19/21 (V-RADM-SLIM-T2-ADMITTED, V-RADM-SLIM-REPO-FILE-EXISTS) fails identically at HEAD before C2.
- Calls used: ~14.
Next unit: route.json/packets may now carry effect/deopt/invalidators/expected_boundaries; cost_to_completion still uses its own class names (aliased, not rewritten). The cdc route.json has no effect (defaults BOUNDED).
