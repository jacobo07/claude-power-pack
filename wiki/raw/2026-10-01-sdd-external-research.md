# External benchmark: instructing AI coding agents (research started 2026-10-01)
Tiers: A = controlled/measured study; B = vendor/practitioner claim with detail; C = opinion.

## A1. GitHub Spec Kit (https://github.com/github/spec-kit/blob/main/spec-driven.md) [tier B]
- Pipeline: constitution -> /specify -> /clarify -> /plan -> /tasks -> /analyze -> /implement. Spec = WHAT/WHY not HOW.
- Mandatory [NEEDS CLARIFICATION: q] markers instead of guessing; completeness checklist ("requirements testable and unambiguous", "no remaining NEEDS CLARIFICATION").
- Constitution gates (simplicity, anti-abstraction, integration-first); test-first order: contracts -> tests -> impl; tests must be seen failing.
- Speculation prevention: every feature traces to a user story with measurable acceptance criteria.
- /analyze = cross-artifact consistency check vs constitution. No published outcome measurements (vendor claim).

## C2. AGENTS.md effect (Gloaguen et al., ETH SRI, arXiv 2602.11988, Feb 2026, https://arxiv.org/abs/2602.11988) [tier A]
- Across multiple agents/LLMs, context files give NO improvement in task success (LLM-generated: slightly worse) and raise inference cost >20%.
- Developer-written files modestly better than LLM-generated. Instructions are followed well; repo overviews NOT helpful. Useful for non-standard practices only (not inferable from repo).
- Implication: minimal, non-discoverable facts only; evaluate before deploying.

## A2. Kiro specs (https://kiro.dev/docs/specs/) [tier B]
- requirements.md (user stories + acceptance criteria, EARS), design.md (architecture, sequence diagrams), tasks.md (trackable, dependency-analysed into parallel waves).
- Requirements-first or Design-first workflows; Bugfix specs use current / expected / UNCHANGED behaviour (regression guard); Quick Spec skips approval gates.
- Per-phase approval gates are the control point.

## A3. Anthropic Claude Code best practices (https://code.claude.com/docs/en/best-practices, fetched 2026-10-01) [tier B]
- Core constraint: context fills, performance degrades. Verification first: "Give Claude a way to verify its work" (tests/build/screenshot); table: vague "validate email" -> example test cases + run tests. Ask for evidence not assertion. Hard gate options: /goal condition, Stop hook (deterministic), fresh-context verification subagent.
- Explore -> Plan -> Implement -> Commit; plan mode; "If you could describe the diff in one sentence, skip the plan." (planning is proportional).
- Specific prompts: scope file/scenario/test prefs, point to existing patterns, symptom+location+what "fixed" looks like (failing test first).
- Spec interview: have agent interview you (AskUserQuestion) about edge cases/tradeoffs, write SPEC.md, then execute in a FRESH session. "The most useful specs are self-contained: they name the files and interfaces involved, state what is out of scope, and end with an end-to-end verification step."
- CLAUDE.md: short; "Would removing this cause Claude to make mistakes? If not, cut it." Include non-guessable commands, deviating style, gotchas; exclude what is derivable from code, file-by-file descriptions. Bloat -> rules ignored. Advisory vs hooks: hooks deterministic.
- Adversarial review in fresh subagent against PLAN.md; warns reviewers over-report -> restrict to correctness/stated requirements (anti over-engineering).
- Writer/Reviewer split; tests by one agent, code by another. After 2 failed corrections /clear and rewrite prompt.

## A4. OpenSpec (https://github.com/Fission-AI/OpenSpec) [tier B]
- Lifecycle explore -> propose (change folder: proposal, spec deltas, design, tasks) -> apply -> archive (merge delta into living specs). Per-change delta folders = spec change control; artifacts updatable anytime, no rigid gates. Specs in repo markdown, reviewed like code. Positions itself as lightweight vs Spec Kit's phase gates ("agreement before building").

## A5. OpenAI Codex AGENTS.md (https://learn.chatgpt.com/docs/agent-configuration/agents-md) [tier B]
- Layered discovery: global ~/.codex/AGENTS.md, then git root -> cwd, closer files override; default combined cap 32 KiB (project_doc_max_bytes). Nested/per-directory overrides for scoped rules; "Code Review Rules" section; keep rules concise: behaviour to flag + safe alternative.

## A2b. Kiro EARS (search: kiro.dev/docs/specs/feature-specs/requirements-first/, mamezou-tech PBT blog Dec 2025) [tier B]
- Acceptance criteria in EARS: "WHEN <event> THE <System> SHALL <response>". Kiro derives property-based tests from EARS ("for any state where X occurs, Y holds") -> criteria map to executable properties. Example: ticket state machine criteria incl. "SHALL allow only Open->InProgress->Done".

## A6. Tessl / BMAD / Agent OS (web search summaries only; secondary) [tier B/C]
- Tessl: spec-as-source; specs hold requirements, behaviour, constraints, example cases that become tests; registry of library usage specs + evals (docs.tessl.io/introduction-to-tessl/concepts). Claim: specs are the mechanism by which change is applied so don't drift (claim, unmeasured).
- BMAD-METHOD: role-agents (analyst/PM/architect/SM/dev/QA), PRD + architecture + story files carry decisions across sessions to counter cross-session drift. Heavy ceremony.
- Agent OS (buildermethods.com/agent-os): discover/document codebase standards, inject into specs; standards-injection rather than per-task spec.

## C3. Tests as spec / TDD with LLMs
- TDAD (arXiv 2603.17973) [tier A, SWE-bench]: giving agent graph-derived "which tests to check" context cut regressions 6.08% -> 1.82% and raised resolution 24% -> 32%; generic PROCEDURAL TDD instructions without test context RAISED regressions to 9.94% (worse than nothing). "Surfacing context beats prescribing workflow."
- WebApp1K / Tests-as-Prompt (arXiv 2505.09027) [tier A]: tests + NL description as executable spec; pass@1 0.07-0.95 over 19 models; failures dominated by spec-obedience from test code; many failing tests are test/code non-conformance.
- Mathews & Nagappan, "TDD and LLM-based code generation" (2024) [tier A]: tests in prompt raise success on MBPP/HumanEval. TENET (repo-level test-driven gen) 69%/82% Pass@1 RepoCod/RepoEval.

## C4. Clarification / ambiguity
- Ambig-SWE (arXiv 2502.13069) [tier A]: underspecified SWE-bench Verified; interaction recovers performance (up to +74% vs non-interactive) but models default to non-interactive and detect underspecification poorly.
- Ask or Assume? (arXiv 2603.26233) [tier A]: uncertainty-aware multi-agent clarification scaffold gets 69.4% on underspecified SWE-bench Verified vs 70.8% with full spec -> clarifying before coding closes nearly all the gap.
- CLARITI (arXiv 2604.14624) [tier A]: trained clarifier matches GPT-5 with 41% fewer questions (3.0 vs 5.1) -> ask few, high-relevance, answerable questions.

## C1. Do specs/plans/acceptance criteria help?
- Structured Spec-Driven Engineering (arXiv 2605.02455) [tier A, 5 LLMs x 3 MVC apps x 10 reps, unit-test pass rate]: structured specs (Gherkin, domain model, API signatures) beat NL-only; API/function SIGNATURES were highest-impact (+7.82% avg TPR vs domain model alone); Gherkin+domain model best in 3/6 samples; >70% of failures detectable by static analysis (-> run linters/type-check as a gate).
- Constitutional SDD (arXiv 2602.02584) [tier B, single case study, no stats]: machine-readable security constitution => 73% fewer security defects vs unconstrained generation (weak: one banking app, baselines unspecified).
- Grounding AI Agents in Contracts (arXiv 2608.17177) [tier A-/B]: spec/contract-driven test-generation agent matched or beat developer tests (better in 56.7% of cases); gains attributed to contract guidance quality, not codegen skill.
- Spec-driven generation failure taxonomy: omitted methods, missing error handling, omitted data transformations are top spec-derived gaps (arXiv 2609.00568 WiseSpec search snippet) [tier B].
- "From Prompt to Process" (arXiv 2606.04967) compares SDD frameworks - PDF not machine-readable, not used.
- Note: I found NO controlled study showing Spec Kit/Kiro-style full workflows beat plain prompt+tests end-to-end; evidence is for components (signatures, tests, clarification), not the ceremony.

## C5. Decomposition granularity
- "Solving a Million-Step LLM Task with Zero Errors" (arXiv 2511.09030) [tier A, synthetic]: extreme decomposition into minimal steps + voting is what makes long tasks feasible; per-step error rate dominates.
- SWE-Bench Mobile (arXiv 2602.09540) [tier A]: success falls from ~18% (1-2 files) to ~2% (7+ files) -> cross-file span is a difficulty driver => scope tasks by files touched.
- Subtask-level success 89.7% vs task-level 51.9% in one agent benchmark (search snippet) [tier A/B, verify]. 

## A7. Practitioner critique: Böckeler / martinfowler.com (https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html, late 2025) [tier B, hands-on]
- Levels: spec-first (discarded after task) / spec-anchored (kept, evolved) / spec-as-source (humans never edit code).
- Failures observed: agents ignored instructions despite elaborate context; spec-kit agent treated existing classes as new spec and duplicated them; Kiro turned a small bug into 4 user stories + 16 acceptance criteria ("sledgehammer to crack a nut") => one workflow does not fit all sizes (supports TIERING); verbose repetitive artifacts -> "rather review code than markdown"; double review burden; MDD parallel (inflexibility + non-determinism); "false sense of control". "Spec" diluted into "detailed prompt".
- Marmelab "Spec-Driven Development: The Waterfall Strikes Back" (Nov 2025, via search) [tier B]: tested Spec Kit/Kiro/Tessl/BMAD; excessive docs, redundant process, double review.

## C6. Spec drift
- Spec Growth Engine (arXiv 2606.27045) [tier C/B: conceptual, NO measurements]: machine-readable spec graph, scoped context assembler, vertical-slice growth, DRIFT GATE making spec-code divergence a blocking merge condition.
- Practitioner pieces (augmentcode living specs, specstory spec drift, dev.to) [tier C]: drift invisible to linter/CI; agents regenerate code fast so stale spec compounds; remedy = write implementation decisions back into spec, spec changes in same PR as code.
- No controlled measurement of drift rates found.

## C2b. More context-file evidence
- Gloaguen detail (via dair.ai summary of arXiv 2602.11988) [tier A]: SWE-bench Lite (300 tasks, 11 repos) + AGENTbench (138 instances/12 repos, dev-written context files). LLM-generated files: -0.5% (Lite), -2% (AGENTbench); human-written: ~+4% avg; both add 14-22% more reasoning tokens and 2-4 extra steps.
- Instruction Adherence factorial study (arXiv 2605.10039, 1,650 Claude Code sessions, 16,050 function-level obs.) [tier A]: file size, instruction position, file architecture, adjacent-file contradictions: NO detectable effect on compliance. Strongest effect: within-session decay, each additional function generated = ~5.6% lower odds of compliance. => rules decay over a long run; re-check mechanically (hooks/gates), keep sessions/tasks short.
- Claude Code docs: bloat causes ignored rules (practitioner, B); hooks deterministic vs CLAUDE.md advisory.

## C1b. Requirement quality -> LLM output
- "What Should We Engineer in Prompts" (arXiv 2409.08775) per search summary [tier A/B]: omission errors (missing requirements) hurt more than commission errors (inaccurate): LLMs correct inaccuracies better than they fill gaps.
- "When Prompts Go Wrong" (arXiv 2507.20439) [tier A]: HumanEval/MBPP with ambiguous/contradictory/incomplete descriptions: contradiction most harmful, then ambiguity/incompleteness; minor wording flaws matter; bigger models more resilient.
- Prompt specificity / normativity vs security defects (arXiv 2510.22944 search summary) [tier A/B]: less clear/complete/consistent prompts -> higher vuln rate.
- Counterpoint: "When Prompt Under-Specification Improves Code Correctness" (arXiv 2604.24712) [tier A, exploratory]: reduced precision sometimes helps -> more spec is not monotonically better.
- METR RCT (metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study) [tier A]: 16 experienced devs, 246 tasks: AI use 19% SLOWER, believed 20-24% faster; overhead of reviewing/integrating output. Context: perception of speedup is unreliable; measure.

## B. Classic SE practice
- ISO/IEC/IEEE 29148:2018 (https://standards.ieee.org/standard/29148-2018.html; summary via search) [tier B, standard; the quality attributes are normative, effect on outcomes unmeasured here]: individual requirement = necessary, appropriate (right abstraction, no implementation detail), unambiguous, complete, singular (one requirement, no conjunction), feasible, verifiable/measurable, correct, conforming (template). Requirement SET = complete, consistent (no conflicts), traceable (upward to source/stakeholder need), feasible, verifiable. 
- EARS (Mavin, Rolls-Royce; https://en.wikipedia.org/wiki/Easy_Approach_to_Requirements_Syntax) [tier B; no quantified gains on that page]: ubiquitous "THE system SHALL"; event "WHEN trigger"; state "WHILE"; optional "WHERE"; unwanted "IF..THEN"; complex = combinations. Reduces ambiguity, improves testability.
- Google design docs (Malte Ubl, https://www.industrialempathy.com/posts/design-docs-at-google/) [tier B]: write only when design is ambiguous/contentious (skip if obvious or merely an implementation manual); sections: context & scope (facts only), goals & NON-GOALS (non-goals = things that could reasonably be goals but chosen not to be; not negated goals), design w/ trade-offs, ALTERNATIVES CONSIDERED ("one of the most important"), cross-cutting concerns (security, privacy, observability); review early when changes are cheap.
- ADRs (https://adr.github.io/) [tier B]: one decision per record: rationale, trade-offs, consequences; immutable, superseded by new record, forming decision log.
- Gherkin (https://cucumber.io/docs/bdd/better-gherkin/) [tier B]: declarative behaviour not implementation; "if wording would change when implementation changes, rework it"; concrete personas/examples; living documentation. Empirically Gherkin+domain model improved LLM test pass rate (arXiv 2605.02455, tier A).
- Not fetched (cited from general knowledge, tier B/C): Definition of Ready/Done (Scrum Guide: DoD is a formal commitment; DoR is a team practice, not in Scrum Guide - INVEST stories), contract-first (OpenAPI/types - supported empirically by signature finding), RFC process (IETF/Rust RFCs: motivation, drawbacks, alternatives, unresolved questions), traceability matrices (29148 traceable attribute), change control/versioning (OpenSpec delta + archive is the agent-era analogue).

## A8. Cursor (https://cursor.com/blog/agent-best-practices) [tier B]
- Plan Mode: research -> clarify questions -> plan with file paths -> approval; plans editable markdown saved to .cursor/plans/. Rules: build/test commands, style deviations, pointers to canonical examples; do NOT copy whole style guides or document every command/edge case; keep rules <500 lines, reference files rather than copy (staleness). TDD: write tests first, confirm fail, implement ("clear target to iterate against"). New conversation when switching tasks / agent confused. Cites U Chicago study: experienced devs plan before generating (secondary).

## A9. Devin (https://docs.devin.ai/essential-guidelines/instructing-devin-effectively) [tier B]
- Be as specific as with a human coworker; make design judgments for the agent; acceptance criteria concrete & measurable ("emit event when usage >80%", "endpoint returns 200 with all required fields") - NOT "make sure it works"; split into smaller checkpointed sub-tasks each with validation; reference existing files/patterns; run tests/build before PR.

## A10. GitHub analysis of 2,500+ agents.md (https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/) [tier B, observational]
- Six areas: commands (with flags, early), testing, project structure, code style via real snippet, git workflow, boundaries. Three-tier boundaries Always / Ask first / Never. One real snippet > prose. Note: observational of what exists, NOT shown to improve outcomes (cf. Gloaguen tier A: overviews don't help).

## A11. Aider (https://aider.chat/docs/usage/conventions.html) [tier B]: CONVENTIONS.md loaded read-only (--read), cacheable via prompt caching; style/library/testing preferences. Cross-tool convergence: AGENTS.md read by Codex, Cursor, Copilot, Gemini CLI, Aider, Devin, Factory, Jules etc.

## Engineer-grade spec checklist
Source keys: CCBP=Claude Code best practices; SK=Spec Kit; KIRO; BOCK=Boeckeler/fowler; G26=Gloaguen arXiv 2602.11988; TDAD=2603.17973; AMBIG=2502.13069; ASK=2603.26233; SSDE=2605.02455; OMIT=2409.08775; WPGW=2507.20439; IAF=2605.10039; SWEM=2602.09540; GDD=Google design docs; 29148; EARS; GHK=Gherkin docs; DEVIN; CUR=Cursor; GH2500; SGE=2606.27045.

1. Spec is sized to the task; a one-sentence diff gets no spec, ambiguous/multi-file work gets one. [B] CCBP, BOCK (Kiro 4 stories/16 AC for a bug), GDD "skip if obvious"
2. States intent as WHAT/WHY and observable behaviour, not implementation steps (except named interfaces). [B] SK, 29148 "appropriate", GHK
3. Each requirement is singular (one testable statement, no "and"). [B] 29148
4. Each requirement is unambiguous: one interpretation; no "fast", "robust", "make it better". [A/B] WPGW (ambiguity/contradiction degrade pass rate), DEVIN, 29148
5. No internal contradictions between requirements or with CLAUDE.md/AGENTS.md rules (checked before handoff). [A] WPGW (contradiction most harmful); 29148 consistent set
6. Completeness over precision: omissions are listed and filled (error paths, edge cases, data transformations) since models fix inaccuracies better than they invent missing info. [A/B] OMIT, WiseSpec failure taxonomy
7. Acceptance criteria are executable, or map 1:1 to named tests/commands with expected output. [A/B] CCBP, TDAD, WebApp1K 2505.09027, DEVIN, KIRO PBT
8. Acceptance criteria use a structured form (EARS WHEN/SHALL or Given-When-Then) with concrete values. [B; A for Gherkin gain] EARS, GHK, SSDE
9. Gherkin/examples are declarative (behaviour, not UI keystrokes) and use concrete example data. [B] GHK
10. Names the files, modules and interfaces/signatures to touch or create; gives actual function/type signatures where an API is involved. [A] SSDE (signatures +7.8% TPR), CCBP ("name the files and interfaces")
11. Points to an existing in-repo pattern/file to imitate. [B] CCBP, DEVIN, CUR
12. Explicit non-goals / out-of-scope list (things that could plausibly be in scope but are not). [B] GDD, CCBP
13. Alternatives considered and the reason for the chosen design recorded (for non-trivial design decisions); recorded as an ADR-style immutable decision. [B] GDD, ADR
14. Open questions are enumerated, marked (e.g. [NEEDS CLARIFICATION]) and resolved BEFORE coding; agent asks few, high-relevance, answerable questions. [A] AMBIG, ASK, CLARITI 2604.14624; [B] SK, CUR plan mode, CCBP interview
15. Agent is told when to stop and ask (ask-first boundaries) vs proceed. [B] GH2500 three-tier boundaries; [A] AMBIG (models default to not asking, so it must be instructed/gated)
16. Verification includes a regression guard: which existing tests must still pass / unchanged behaviour listed. [A] TDAD (targeted test context cut regressions 6.1%->1.8%); [B] KIRO bugfix "unchanged behaviour"
17. Prescribe WHICH tests/checks to run and how (exact commands), not a generic "do TDD". [A] TDAD (generic procedural TDD raised regressions to 9.9%); [B] CCBP
18. Includes a failing reproduction test first for bugs (symptom, location, "fixed" definition). [B] CCBP, CUR
19. Includes cheap static gates (typecheck/lint/build) in the done definition (most generated-code failures are statically detectable). [A] SSDE (>70% failures static-detectable)
20. Task is decomposed into small, independently verifiable checkpoints, each with its own validation. [A/B] 2511.09030, DEVIN, CCBP; spans of 1-2 files succeed far more than 7+ [A] SWEM
21. Dependencies between tasks and parallelisable ones identified. [B] KIRO waves, SK /tasks
22. Verification is independent of the author: fresh-context reviewer/subagent checks diff against the spec, scoped to correctness/stated requirements only. [B] CCBP
23. Spec is self-contained for a fresh session (execution happens in clean context; no reliance on chat history). [B] CCBP
24. Persistent instruction files contain only non-discoverable facts (commands, deviating conventions, gotchas), minimal, no repo overviews; reviewed/pruned. [A] G26, IAF-neutral on size; [B] CCBP, CUR
25. Critical rules enforced by deterministic gates (hooks/CI), not just prose, because compliance decays over a session (~5.6% lower odds per generated function). [A] IAF; [B] CCBP hooks
26. Requirements are traceable: each task/test/commit links to a requirement/story and no code is added without a requirement ("speculation prevention"). [B] 29148 traceable, SK
27. Spec records constraints/NFRs and cross-cutting concerns (security, privacy, observability, perf budgets) as measurable thresholds. [B] GDD, 29148 verifiable; [B/weak A] constitutional SDD 73% fewer security defects (single case study)
28. Spec lives in the repo, versioned, reviewed with code; changes proposed as deltas and archived (change control). [B] OpenSpec, ADR
29. Spec is updated in the same change when code diverges (decisions written back); a drift check can block merge. [B/C] SGE (no measurements), practitioner posts; no tier A evidence found
30. Done definition names evidence to show (test output, command + result, screenshot) rather than an assertion of success. [B] CCBP
31. Review burden is budgeted: spec/artifacts are short enough that a human actually reads them (prefer reviewing code or tests over long markdown). [B] BOCK, Marmelab
32. Tiering/ceremony level is declared up front and escalation criteria are explicit (what makes a task need a plan/spec). [B] CCBP "one-sentence diff", GDD "3+ yes answers", BOCK size-mismatch
33. Spec effectiveness is measured on your own tasks (A/B of with/without) rather than assumed. [A] G26 (intuitively helpful context files did not help), METR RCT 2025 (devs 19% slower while believing 20% faster)
