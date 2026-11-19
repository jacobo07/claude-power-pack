# BCAP-2 Phase 3 CPP-AGSK-001 — Dispositions

Upstream: https://github.com/addyosmani/agent-skills @ 8c99fa36d90068c82d547f7c12a9d67a3e95f4ee (MIT, (c) 2025 Addy Osmani).
Observed: 26 skill directories (backlog said 25: `accessibility-engineering` is the extra) and 10 command TOMLs (backlog said nine; it lists a11y, build, code-simplify, constraints, planning, review, ship, spec, test, webperf = ten).

Honesty column `basis`: `READ` = upstream content AND CPP owner were read this phase; `HYPOTHESIS` = the backlog's initial
disposition mapped to the closed vocabulary, with the owner path verified to EXIST but the overlap NOT yet analysed.
Only the pilot (constraint-driven-development, AGSK-C) is READ. A HYPOTHESIS row is not an absorption claim.
Vocabulary: ALREADY OWNED, EXTEND, CONNECT, MERGE, CONDITIONAL, UPSTREAM-ONLY, REJECT, UNVERIFIED.
Machine-checked by `tools/test_bcap2_agsk.py` (one row per upstream name, owner path exists, vocabulary closed).

| kind | upstream | disposition | cpp owner | basis | note |
|---|---|---|---|---|---|
| skill | using-agent-skills | ALREADY OWNED | modules/skill_router | HYPOTHESIS | one router only; never a second global router |
| skill | idea-refine | ALREADY OWNED | modules/decision_review | HYPOTHESIS | decision/intent capability |
| skill | interview-me | CONDITIONAL | modules/intent_verified | HYPOTHESIS | no interview when facts exist |
| skill | spec-driven-development | ALREADY OWNED | modules/spec_gate | HYPOTHESIS | SDD OS + spec_gate |
| skill | planning-and-task-breakdown | ALREADY OWNED | modules/gsd_x | HYPOTHESIS | GSD plan verification; no extra planner |
| skill | constraint-driven-development | EXTEND | modules/sqi | READ | PILOT AGSK-C: diff-scoped floor guard added beside sqi weakening census (modules/sqi/floor_guard.py) |
| skill | context-engineering | ALREADY OWNED | modules/context_budget | HYPOTHESIS | context_budget/JIT already own it |
| skill | source-driven-development | UNVERIFIED | modules/knowledge_acquisition | HYPOTHESIS | AGSK-D: version/provenance retrieval gap not yet measured |
| skill | doubt-driven-development | UNVERIFIED | modules/code-review | HYPOTHESIS | AGSK-B: risk-gated in-flight review not yet scanned |
| skill | incremental-implementation | CONNECT | modules/uqf/principles/tdd_workflow.py | HYPOTHESIS | vertical slice lives in CPP-TDD-001 |
| skill | test-driven-development | MERGE | modules/uqf/principles/tdd_workflow.py | HYPOTHESIS | merged into CPP-TDD-001 (Phase 2); no second TDD owner |
| skill | debugging-and-error-recovery | MERGE | modules/craif | HYPOTHESIS | merged into CPP-DBG-001 (Phase 1); no second causal engine |
| skill | api-and-interface-design | CONDITIONAL | modules/contract_fabric | HYPOTHESIS | extend only on measured gaps |
| skill | browser-testing-with-devtools | UNVERIFIED | modules/osa | HYPOTHESIS | AGSK-E: gap-test needs real browser; likely LAPTOP plane |
| skill | code-review-and-quality | ALREADY OWNED | modules/code-review | HYPOTHESIS | pp-code-reviewer pipeline |
| skill | code-simplification | CONDITIONAL | modules/code-review | HYPOTHESIS | behavior-preserving scope-bounded only |
| skill | frontend-ui-engineering | ALREADY OWNED | modules/cdio | HYPOTHESIS | CDIO owns UI quality |
| skill | performance-optimization | UNVERIFIED | modules/pp_eval | HYPOTHESIS | AGSK-F keep/revert ledger not yet scanned |
| skill | observability-and-instrumentation | UNVERIFIED | modules/monitoring | HYPOTHESIS | AGSK-F not yet scanned |
| skill | security-and-hardening | CONDITIONAL | modules/secret_firewall | HYPOTHESIS | extend on verified gaps only |
| skill | ci-cd-and-automation | ALREADY OWNED | modules/deployment | HYPOTHESIS | deploy gates + rollback |
| skill | deprecation-and-migration | CONDITIONAL | modules/rollback | HYPOTHESIS | AGSK-F selective |
| skill | git-workflow-and-versioning | ALREADY OWNED | modules/repo_identity | HYPOTHESIS | worktree/concurrency governance |
| skill | documentation-and-adrs | ALREADY OWNED | modules/decision_review | HYPOTHESIS | decision records |
| skill | shipping-and-launch | ALREADY OWNED | modules/deployment | HYPOTHESIS | Production Reality + healthcheck |
| skill | accessibility-engineering | ALREADY OWNED | modules/cdio | HYPOTHESIS | absent from the backlog table (26th skill); CDIO owns a11y |
| command | a11y | ALREADY OWNED | modules/cdio | HYPOTHESIS | cdio-reviewer |
| command | build | CONNECT | modules/gsd_x | HYPOTHESIS | GSD execute |
| command | code-simplify | CONDITIONAL | modules/code-review | HYPOTHESIS | see code-simplification |
| command | constraints | EXTEND | modules/sqi | READ | PILOT: guard subcommand maps to floor_guard; check/ratchet map to existing sqi ratchet (dormant by Owner decision 4) |
| command | planning | ALREADY OWNED | modules/gsd_x | HYPOTHESIS | GSD plan |
| command | review | ALREADY OWNED | commands/code-review.md | HYPOTHESIS | /code-review |
| command | ship | ALREADY OWNED | commands/deploy.md | HYPOTHESIS | /deploy + DEPLOY HRs |
| command | spec | ALREADY OWNED | commands/sdd-os.md | HYPOTHESIS | /sdd-os |
| command | test | MERGE | commands/test-gaps.md | HYPOTHESIS | test-gaps/mutation owner (CPP-TDD-001) |
| command | webperf | UNVERIFIED | modules/pp_eval | HYPOTHESIS | AGSK-F not yet scanned |
