# Parallel full-suite runs under a timeout cap fabricate reds; a baseline must be serial and awaited (CDC C5/C5b)
- Symptom: C5 proof run of 463 suites (10x parallel, 90 s cap) showed 125 red; closure-vs-full agreement could not be read. C5b: even serially, "full minus baseline" was 3/7/5 on leaf landings.
- Trigger: contention timeouts counted as red; flaky suites (test_motion_grammar red, green, red); suite count differs per commit.
- Root cause: verdict taken from one parallel run with no parent control and timeouts folded into reds.
- Fix: tools/c5b_baseline.py (serial, every subprocess awaited, timeouts a separate list); verdict = serial rerun + same suite at parent commit; land_worktree --baseline-red.
- Prevention: a suite is "caused" only if green at parent and red after, on a serial rerun; timeout is not red.
- Regression proof: evidence/C5b-baseline.json, C5b-step2.json; tools/test_land_worktree.py 24/24 (V-LAND-12..15).
