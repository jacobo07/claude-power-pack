# C7 receipt
Status: DONE

Commits: worktree "cdc C7: cognitive CI gate..." ; live landing sha 3539228b673e (land_worktree; its own cognitive check GREEN, tests rc=0).
Files: tools/cognitive_ci.py, tools/test_cognitive_ci.py, tools/land_worktree.py (COGNITIVE_REGRESSION step after rebase), vault/programs/cdc/{C7-decision.md, cognitive-baseline.json, cognitive-budget-changes.json}.

- PROVEN: 25 deterministic metrics (floor sizes, capsule, admission floors, ctc on fixed graph, status model-call sites = 0, wait residents = 0, admission latency); baseline certified from 3 runs.
- PROVEN: metamorphic gates (+50 skills, +1000 history rows, +100 dormant goals, +500 tests -> fixed-work metrics unchanged; sensitivity control: skill listing does grow).
- PROVEN: planted +8K CLAUDE.md goes RED and land_worktree refuses COGNITIVE_REGRESSION with live untouched; budget entry (reason+owner+allowed_max) lets it land; ZERO metrics cannot be excused; CPP_COG_CI=off and instrument error fail OPEN (21 tests green).
- NOT_PROVEN: dynamic hook additionalContext (static literal scan only); status/wait are static call-site scans, not runtime traces; no live session measured.

Next unit must know: land_worktree now refuses on any always-on growth > 0.5 % (min 64 B) vs cognitive-baseline.json; a justified increase needs an entry in cognitive-budget-changes.json, then re-run `python tools/cognitive_ci.py --certify`. Calls used: ~22.
