# WU-C7 -- Cognitive CI: release-blocking regression gate + metamorphic tests

Common brief: `vault/programs/cdc/PROGRAMME.md`. Plan section: 3 (C7).

Goal: an unjustified cognitive regression cannot land.
1. PLAN (`vault/programs/cdc/C7-decision.md`, <= 1 page): benchmark bank, metric list, noise model, thresholds.
2. `tools/cognitive_ci.py`: deterministic benchmarks (no live model): fresh-floor census (CLAUDE.md, rules, hook
   additionalContext, skill/agent listings sizes -- reuse ctx S1 census if landed), capsule size, route_admission
   floor per profile, cost_to_completion on a fixed claim graph, status path model calls (must be 0), wait path
   residents (must be 0), admission/breaker latency. Metamorphic V-gates: add 50 unrelated skills / 1,000 history rows /
   100 dormant goals / 500 unrelated tests to a fixture -> fixed-work metrics stay within noise.
3. Certified baseline `vault/programs/cdc/cognitive-baseline.json`; regression budget file
   `cognitive-budget-changes.json` (justified increases only, each with reason + owner).
4. `land_worktree.py` runs `cognitive_ci.py --check` before ff-only; material unjustified regression -> refuse
   (kill `CPP_COG_CI=off`). Thresholds from measured noise (3 runs), confidence by blast radius.
5. Proof: a planted +8K always-on injection goes RED and the landing is refused; a justified entry lets it through.
Land via land_worktree (this landing is itself checked).
