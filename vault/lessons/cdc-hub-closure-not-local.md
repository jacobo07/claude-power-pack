# Affected-test closure of a hub tool is not local (CDC C5)
- Symptom: `land_worktree --affected` for tier_routing / land_worktree selected ~272 of 463 suites; hooks/*.js and vault/* mapped to no test.
- Trigger: import-graph closure over hub modules; JS and vault files are outside the python graph.
- Root cause: closure size was never bounded and unmapped paths silently counted as covered.
- Fix: hub = closure > 25 % of suites -> REFUSED AFFECTED_HUB_NEEDS_EXPLICIT_TEST; unmapped path -> REFUSED AFFECTED_NO_MAPPED_TEST unless --exempt (listed in receipt); hooks/<n>.js -> tools/test_<n>.py by name.
- Prevention: unjudged or unmapped is never green.
- Regression proof: tools/test_land_worktree.py V-LAND-16..21 (24/24), test_change_impact 9/9.
