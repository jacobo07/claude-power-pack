# mattpocock/skills read (epoch 10) - DBG R1 and TDD R3 reading
Pin: mattpocock/skills @ abeeaf95660ba9e8b7c753eb38f441ca707a8823 (MIT). Files read in full: skills/engineering/diagnosing-bugs/SKILL.md (sha256 849198df88cdb65f...), skills/engineering/tdd/SKILL.md (5505d25bbaa8fc14...). Not read: referenced sub-files tests.md, mocking.md, scripts/hitl-loop.template.sh, the codebase-design skill. No text copied; concept-level dispositions only.

## diagnosing-bugs vs CPP-DBG-001 (modules/dbg + test_bcap2_dbg)
Upstream phases: 1 feedback loop (red-capable, deterministic, fast, agent-runnable), 2 reproduce+minimise (every remaining element load-bearing), 3 3-5 falsifiable ranked hypotheses shown to user, 4 instrument (one variable at a time, tagged debug logs, perf: baseline then bisect), 5 regression test before fix only at a correct seam (no seam = a finding; prove forced mutations landed by diff), 6 cleanup (tagged logs removed, winning hypothesis in commit message), plus a Redact rule.
- ALREADY OWNED (backlog six-phase summary matched in code): loop red-capable/deterministic, minimise, falsifiable hypotheses, regression-before-fix, flake maths.
- CANDIDATE GAPS to check against the 20 fixtures (not yet checked): tagged-debug-log cleanup check; "no correct seam is itself a finding" state; mutation-landed-by-diff proof; redaction of captured artifacts; "3-5 hypotheses, not one" count rule; perf branch (baseline before fix).
- DECLINE: asking the user mid-run (unattended mission posture); hitl script.
R1 is closed for pin + licence + reading; implementation delta above is open.

## tdd vs Phase 2 (tools/test_bcap2_tdd.py)
Upstream: behaviour-through-public-seams tests; seams agreed before any test; anti-patterns implementation-coupled, TAUTOLOGICAL (expected value recomputed like the code), horizontal slicing (all tests first); loop rules red-before-green, one slice, refactor is not in the loop.
- CANDIDATE GAPS: tautological-assertion detector (poles: expect(add(a,b))==a+b refused, literal accepted); horizontal-slicing signal (many new tests, zero implementation per cycle).
- DECLINE: confirm seams with the user (unattended); refactor-excluded rule (conflicts with CPP mutation/gate flow, unevaluated).
R3 is closed for pin + licence + reading; implementation delta above is open.
