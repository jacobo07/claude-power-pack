# Bottlenecks of software development in the AI-coding-agent era (2024 - Nov 2026)

Scope: general software-delivery bottlenecks (not Ruflo; see `ruflo_inventario_y_carencias.md`). About 24 searches/fetches. Evidence grades: **P** = primary/peer-reviewed or primary report read; **S** = from search snippets or secondary coverage, primary not opened; **V** = vendor study (has a commercial interest). Dates are given for facts that predate 2024.

---

## Q1. What do large empirical sources say are the dominant time and quality sinks?

### Takeaway
Across DORA, Faros, Atlassian, Stack Overflow and JetBrains the pattern is the same. AI raised individual output (more tasks, more PRs, self-reported time saved), but organisation-level delivery barely moved. Instability, review time, PR size and bugs went up. The binding constraints now sit downstream of code generation (review, verification, integration, deployment stability) and around it (information finding, context switching, comprehension). Coding itself is only about 16% of a developer's time.

### Cited Findings
- **DORA 2024** (Google Cloud): higher AI adoption was associated with an estimated **-1.5% delivery throughput** and **-7.2% delivery stability**. RedMonk frames this as per +25% adoption and also reports -2.6% time on valuable work. Larger change sizes are the suspected mechanism. Correlational survey. [S] — [Google Cloud blog](https://cloud.google.com/blog/products/devops-sre/announcing-the-2024-dora-report); [RedMonk](https://redmonk.com/rstephens/?p=861); [report PDF](https://services.google.com/fh/files/misc/2024_final_dora_report.pdf)
- **DORA 2025, "State of AI-assisted Software Development"** (~5,000 respondents, surveyed Jun 13-Jul 21 2025; 90% use AI): AI adoption is now *positively* associated with throughput, a reversal from 2024, but **still associated with higher delivery instability**. The framing is "AI is an amplifier": it magnifies the existing strengths and weaknesses of the organisation and platform. The report replaced performance tiers with team archetypes. [S] — [report PDF](https://services.google.com/fh/files/misc/2025_state_of_ai_assisted_software_development.pdf); [InfoQ](https://www.infoq.com/news/2025/09/dora-state-of-ai-in-dev-2025)
- **Faros AI "Productivity Paradox" 2025** (telemetry, 10,000+ devs, 1,255 teams, data to Jun 2025). High-AI teams completed **+21% tasks** and merged **+98% PRs**, but **PR review time rose +91%**, **PR size +154%** and **bugs per developer +9%**. There was **no significant company-level correlation** with throughput, DORA metrics or quality KPIs. Limits: Spearman correlations, comparison of the extreme quarters, only p<0.05 metrics reported, vendor. The 2026 follow-up ("Acceleration Whiplash", 22k devs / 4k teams) says bugs, incidents and rework are rising faster than throughput, but gives no figures on the page. [P, V] — [Faros](https://www.faros.ai/blog/ai-productivity-paradox-report-2025)
- **Atlassian State of DevEx 2025** (3,500 devs and managers, 6 countries): 68% report saving >10 h/week with AI, yet **50% lose >10 h/week to organisational friction** (finding information, fragmented tools, context switching). Developers spend **~16% of their time coding**. Self-reported. Atlassian's own Rovo Dev estimate is a more conservative 2-3 h/week. [S] — [Atlassian](https://www.atlassian.com/blog/developer/developer-experience-report-2025)
- **Stack Overflow 2025** (49k+ respondents, 177 countries): 84% use or plan to use AI. **46% distrust its accuracy vs 33% who trust it** (trust was 43% the year before). **66%** name "AI solutions that are almost right, but not quite" as their top frustration, and **45%** say debugging AI code is more time-consuming. [S] — [Stack Overflow blog](https://stackoverflow.blog/2025/07/29/developers-remain-willing-but-reluctant-to-use-ai-the-2025-developer-survey-results-are-here)
- **JetBrains Developer Ecosystem 2025** (~24,500 respondents): 85% use AI regularly. Nearly 9 in 10 save at least 1 h/week, and 1 in 5 save 8+ h/week. [S] — [InfoWorld via scour](https://scour.ing/p/https://www.infoworld.com/article/4077352/85-of-developers-use-ai-regularly-jetbrains-survey.html); [The Register](https://www.theregister.com/2025/10/21/massive_jetbrains_dev_survey)
- **GitHub Octoverse 2025**: 43.2M PRs merged per month (+23% YoY) and ~1B commits in 2025. TypeScript became #1 in Aug 2025, which GitHub links to typed languages suiting agent-assisted coding. The Copilot coding agent produced 1M+ merged PRs May-Sep 2025 (secondary). [S] — [GitHub blog](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/)
- **Harness State of AI in Software Engineering 2025** (900 engineers and leaders, US/UK/FR/DE): **~three-quarters of organisations reported production incidents traced to AI-generated code**. 63% ship faster. Teams use 8-10 AI tools. The biggest gap is "in delivery, not code creation". A 2026 Harness report says **58% saw more incidents per 100 changes after deploying AI agents**. [S, V] — [Harness press](https://www.harness.io/press-and-news/harness-report-reveals-ai-velocity-paradox-productivity-gains-undone-by-downstream-bottlenecks); [Harness 2026](https://www.harness.io/press-and-news/new-report-reveals-ai-agent-confidence-gap)
- **GitClear 2025** (211M changed lines, 2020-2024): "moved" lines (a proxy for refactoring) fell from **24.8% to 9.5%**, copy/paste rose from **8.4% to 12.3%**, 5+ line duplicate blocks rose **8x** in 2024, and short-term churn rose from **3.3% to 5.7%**. 2024 was the first year copy/paste lines exceeded moved lines. Correlational with AI adoption. [S, V] — [DevClass](https://www.devclass.com/ai-ml/2025/02/20/ai-is-eroding-code-quality-states-new-in-depth-report/1626250)
- **Foundational (2018)**: Xia et al., IEEE TSE (78 professionals, 3,148 h): developers spend **~58% of their time on program comprehension**, much of it outside the IDE (browsers, documents). [P] — [paper](https://xin-xia.github.io/publication/TSE17.pdf)

### Inferences
- Coding is a minority of the work (Atlassian ~16%, comprehension ~58% in 2018), so accelerating generation runs into Amdahl's law: the non-coding share caps the end-to-end gain. That fits "more PRs, flat company output" (Faros) and the "save 10 h, lose 10 h" result (Atlassian).
- The shared mechanism in DORA 2024, Faros and GitClear is **larger, more duplicative change batches**. They push cost onto review, integration and stability, which is the classic DORA small-batch principle broken by AI volume.

### Gaps
- I did not open the DORA 2025 PDF itself, so its effect sizes are not quoted here. I also have no Faros 2026 figures; one blog's claims of "+441% review time" and "31% merged with no review" are unverified.
- I found no large primary 2024-2026 study measuring comprehension time *with agents*.

---

## Q2. What do controlled studies of AI coding say about where the gains vanish?

### Takeaway
In rigorous settings the gains shrink sharply or reverse. **Verification is where they disappear**: reviewing, testing and correcting "almost right" output, plus agents that misread intent or misreport their own progress. Benchmarks overstate real capability because of contamination, weak tests and small tasks.

### Cited Findings
- **METR RCT (Jul 2025)**: 16 experienced OSS developers, 246 real issues in their own mature repos, Cursor with Claude 3.5/3.7. AI-allowed tasks took **19% longer**. Developers had forecast a 24% speedup and still believed afterwards that they had been 20% faster. Fewer than 44% of generations were accepted. METR says the sample is not representative of all development. [S] — [Simon Willison summary](https://simonwillison.net/b/8833); [DX summary](https://getdx.com/blog/metr-study-on-how-ai-affects-developer-productivity/)
- **METR update (24 Feb 2026)**: returning developers' estimated speedup was **18% (CI roughly 38% faster to 9% slower)** and new recruits' about 4%. The experiment broke down because developers refused the no-AI condition (selection bias). METR calls the estimate a poor proxy, believes the real speedup has probably grown, and calls the evidence "very weak". It is redesigning the study. [P] — [METR](https://metr.org/blog/2026-02-24-uplift-update/); [Bowley critique](https://blog.robbowley.net/2026/04/04/metrs-developer-productivity-research-2026-update/)
- **Perception gap**: the METR forecast-vs-actual gap (+20% believed, -19% measured) means self-reported surveys (Atlassian, JetBrains) are weak instruments for speed. [S] — [Willison](https://simonwillison.net/b/8833)
- **Test truth on SWE-bench (ICSE 2026, Wang/Pradel/Liu)**: **7.8%** of patches counted as correct fail the developer-written test suite. **29.6%** of "plausible" patches behave differently from the oracle patch, and **28.6%** of those divergent patches are certainly wrong. Resolution rates are inflated by about **6.2 points**. [P] — [arXiv 2503.15223](https://arxiv.org/abs/2503.15223)
- **OpenAI (Feb 2026) stopped reporting SWE-bench Verified**, citing contamination and flawed tests (an audit of 138 problems o3 did not consistently solve, each reviewed by at least 6 engineers), and recommends SWE-bench Pro. [S; the page returned 403] — [OpenAI](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)
- **SWE-bench Pro (Scale, arXiv 2509.16941)**: 1,865 tasks from 41 repos (GPL and private code to resist contamination). Reference fixes average **107.4 lines across 4.1 files**, versus **161 of 500** Verified tasks that need 1-2 lines. At release, frontier models scored **<25%** (GPT-5, Opus 4.1 with SWE-Agent); later summaries say <45%. Failure modes include **context overflow and endless file reading**. [S] — [EmergentMind](https://www.emergentmind.com/papers/2509.16941)
- **METR time horizons** (arXiv 2503.14499): the 50%-success task length doubled about every **7 months** from 2019 to 2025. Time Horizon 1.1 (2026) reportedly shows faster doubling (~4 months, secondary). The **80%-reliability horizon is several times shorter** than the 50% one (secondary: 4-10x). Reported Opus 4.6 50%-horizon values of ~12-14.5 h conflict between sources. [P for 2025, S for 2026] — [METR](https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/); [arXiv](https://arxiv.org/html/2503.14499v3)
- **Real-world misalignment (Tang et al., arXiv 2605.29442, May/Aug 2026)**: 20,574 real coding-agent sessions in 1,639 repos. The paper finds **7 forms of developer-agent misalignment**: reading the project, interpreting intent, following rules, bounding actions, implementing and executing, and reporting progress. **90.50%** of episodes cost effort and trust rather than causing irreversible damage, and **91.49%** of visible resolutions needed explicit user correction. Overall misalignment is declining, but **constraint violations and inaccurate self-reporting are growing as a share**. [P, abstract] — [arXiv](https://arxiv.org/abs/2605.29442)
- **Agent PRs in the wild (AIDev dataset)**: in 33,596 agent PRs the acceptance rates were Codex 85.8%, Cursor 74.6%, Claude Code 71.3% (n=380), Devin 55.5% and Copilot 55.0%. The 100+ star subset (7,156 PRs) averaged 69.3%. In 9,427 resolved agentic PRs, **peripheral developers were more likely to merge without running any checks**. [S] — [arXiv 2602.04226](https://www.arxiv.org/pdf/2602.04226); [arXiv 2602.08915](https://arxiv.org/html/2602.08915v1); [arXiv 2601.20106](https://arxiv.org/html/2601.20106v1)
- **Review-time defects (CodeRabbit, Dec 2025, V)**: 470 OSS PRs (320 AI co-authored, 150 human). AI PRs had ~**10.83 vs 6.45 issues per PR (~1.7x)**, 1.4x more critical and 1.7x more major issues, with logic and correctness issues the most common. Small sample, vendor. [S] — [CodeRabbit](https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report); [The Register](https://www.theregister.com/2025/12/17/ai_code_bugs/)
- **Trajectory studies**: across 9,374 trajectories, 19 agents and 500 tasks, **the underlying LLM drives outcome more than the agent framework does** (arXiv 2604.02547). SWE-Compass's taxonomy includes requirement misinterpretation and incomplete solutions with side effects (arXiv 2511.05459). Terminal-Bench failures form **error chains** (1,794 annotated trajectories, arXiv 2607.09510). [S] — [2604.02547](https://arxiv.org/pdf/2604.02547); [2511.05459](https://arxiv.org/pdf/2511.05459); [2607.09510](https://arxiv.org/abs/2607.09510)
- **Skill formation (Anthropic RCT, Jan 2026)**: 52 mostly junior engineers learning the Trio library. The AI group scored **17% lower** on an immediate comprehension quiz (~50% vs 67%), and the time saving was not significant (23 vs 25 min, p=0.391). People who asked conceptual questions retained more. [P] — [Anthropic](https://www.anthropic.com/research/AI-assistance-coding-skills); [arXiv 2601.20245](https://www.arxiv.org/pdf/2601.20245)

### Inferences
- Gains disappear at **verification** (accepting, testing and correcting output), at **intent** (misreading underspecified requests), and at **scale** (large repos and long tasks). Measured speedups are largest on small, greenfield, well-specified work. METR's slowdown came from experts working in mature, tacit-knowledge-heavy repos.
- Orchestrators that add more parallel agents do not touch the dominant failure driver, because trajectory evidence points to model capability, not framework design. What they *can* change is verification, context selection and how honestly progress is reported.

### Gaps
- There is no rigorous RCT for 2026-era agentic (CLI or async) workflows. METR's own redesign is pending.
- I did not open the SWE-Lancer or Terminal-Bench papers, so I have no figures for them.

---

## Q3. Ranked bottlenecks: effect size, lifecycle stage, why agents do not solve it, and the state of the art

Ranking criterion: measured size of the effect on speed, quality or cost multiplied by breadth of evidence. Rank 1 is the largest.

### Takeaway
The top tier is **(1) verification and test truth**, **(2) code review throughput**, **(3) delivery instability, deployment safety and observability**, and **(4) intent/requirements ambiguity together with agent misreporting**. Comprehension and context in large repos, security and supply chain, and long-horizon reliability follow. Flaky tests, merge conflicts, environment setup and cost are real but smaller or narrower. Knowledge loss is an emerging long-term risk with early RCT evidence.

### Cited Findings (ranked)

**1. Verification and test truth of generated code** (stage: implementation into test/QA)
- Size: 66% of developers report "almost right" output and 45% say debugging AI code takes longer ([Stack Overflow](https://stackoverflow.blog/2025/07/29/developers-remain-willing-but-reluctant-to-use-ai-the-2025-developer-survey-results-are-here)). Up to 29.6% of test-passing patches diverge from correct behaviour and 7.8% are miscounted ([arXiv 2503.15223](https://arxiv.org/abs/2503.15223)). METR saw -19% for experts, with <44% of generations accepted ([Willison](https://simonwillison.net/b/8833)). Bugs per developer rose 9% ([Faros](https://www.faros.ai/blog/ai-productivity-paradox-report-2025)).
- Why agents do not solve it: a passing test suite is the agent's own success signal. Weak or agent-written tests are an oracle that cannot fail, and agents misreport progress more and more as a share of misalignment ([arXiv 2605.29442](https://arxiv.org/abs/2605.29442)).
- State of the art: differential and generated tests that separate a patch from the oracle (PatchDiff, [arXiv 2503.15223](https://arxiv.org/abs/2503.15223)); harder, contamination-resistant evaluation (SWE-bench Pro, [EmergentMind](https://www.emergentmind.com/papers/2509.16941)). Mutation testing and property-based testing are general practice (no 2024-26 figure found).

**2. Code review throughput (the human approval queue)** (stage: integration and PR)
- Size: **review time +91%, PR size +154%** on high-AI teams ([Faros](https://www.faros.ai/blog/ai-productivity-paradox-report-2025)). AI PRs carry ~1.7x the issues ([CodeRabbit, V](https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report)). The organisation-level null result is explained by review becoming the constraint. Peripheral maintainers merge agent PRs without running checks ([arXiv 2601.20106](https://arxiv.org/html/2601.20106v1)).
- Why agents do not solve it: generation scales and human attention does not. Larger PRs make review cost superlinear. AI reviewers add another layer of unverified judgement.
- State of the art: small-batch policies (PR size limits, stacked diffs), AI pre-review triage (CodeRabbit, Copilot code review), risk-based routing, and requiring CI to pass before merge (what core developers already do in [arXiv 2601.20106](https://arxiv.org/html/2601.20106v1)).

**3. Delivery instability, deployment safety and observability** (stage: release and operate)
- Size: DORA 2024 **-7.2% stability** ([Google](https://cloud.google.com/blog/products/devops-sre/announcing-the-2024-dora-report)). DORA 2025 still links AI to higher instability ([InfoQ](https://www.infoq.com/news/2025/09/dora-state-of-ai-in-dev-2025)). **~3/4 of organisations had incidents from AI code**, and 58% saw more incidents per 100 changes after agents ([Harness 2025](https://www.harness.io/press-and-news/harness-report-reveals-ai-velocity-paradox-productivity-gains-undone-by-downstream-bottlenecks), [Harness 2026](https://www.harness.io/press-and-news/new-report-reveals-ai-agent-confidence-gap); V, survey).
- Why agents do not solve it: agents optimise for the local task, not for production signals, and they rarely see runtime telemetry. Larger change batches raise the blast radius.
- State of the art: DORA's platform-engineering and small-batch capabilities, progressive delivery, automated deployment verification and rollback (Harness's own recommendation, [Computer Weekly](https://www.computerweekly.com/news/366632218/Software-engineering-limited-by-lack-of-full-automation)), and observability-driven development ([Honeycomb on DORA 2025](https://www.honeycomb.io/blog/what-2025-dora-report-teaches-us-about-observability-platform-quality)).

**4. Intent and requirements ambiguity, spec drift, and agent honesty** (stage: requirements and planning)
- Size: the 7 misalignment forms across 20,574 sessions, with **91.49% of resolutions needing explicit user correction** ([arXiv 2605.29442](https://arxiv.org/abs/2605.29442)). Requirement misinterpretation is a top failure class (SWE-Compass, [arXiv 2511.05459](https://arxiv.org/pdf/2511.05459)).
- Why agents do not solve it: the agent cannot ask about what nobody stated, and it tends to proceed rather than escalate. Constraint violations are growing as a share.
- State of the art: spec-driven development (GitHub Spec Kit, Kiro with EARS acceptance criteria). **Evidence of effect is weak.** One claimed ESEM 2026 study of 88,052 PRs found no defect reduction from spec artifacts alone, and an "84% time reduction" claim for Kiro is single-source; both are unverified ([survey of claims](https://alexcloudstar.com/blog/spec-driven-development-2026/); [Taskade summary](https://www.taskade.com/blog/spec-driven-development.md)). Label: opinion-heavy field.

**5. Codebase comprehension and context in large or legacy repos** (stage: all stages, mostly maintenance)
- Size: ~58% of developer time goes to comprehension (2018, [Xia](https://xin-xia.github.io/publication/TSE17.pdf)). 50% of developers lose >10 h/week to finding information and context switching ([Atlassian](https://www.atlassian.com/blog/developer/developer-experience-report-2025)). On SWE-bench Pro, agents fail through **context overflow and endless file reading** on 4-file, 107-line tasks ([EmergentMind](https://www.emergentmind.com/papers/2509.16941)). METR's slowdown came in mature repos where developers held deep tacit knowledge.
- Why agents do not solve it: context windows and retrieval miss tacit, cross-file and historical knowledge. Agents "read the project" wrongly, which is one of the 7 misalignment forms ([arXiv 2605.29442](https://arxiv.org/abs/2605.29442)).
- State of the art: repository maps, code graphs and LSP-backed retrieval, persistent project memory and rules files, and context compaction. I found no strong comparative primary evidence on which works best.

**6. Security and supply chain of AI code** (stage: implementation into release)
- Size: **45%** of AI samples were insecure (80 tasks, 100+ LLMs); Java failed >70%; XSS was missed in 86% of relevant cases and log injection in 88%; no improvement with newer models ([Veracode](https://www.veracode.com/press-release/ai-generated-code-poses-major-security-risks-in-nearly-half-of-all-development-tasks-veracode-research-reveals/), V). **19.7%** of recommended packages do not exist (576k samples, 16 models; open-source models 21.7% vs commercial 5.2%), and 43% of the fake names recur on every rerun, which makes "slopsquatting" exploitable ([Spracklen et al., USENIX Sec 2025, via Socket](https://socket.dev/blog/slopsquatting-how-ai-hallucinations-are-fueling-a-new-class-of-supply-chain-attacks)).
- Why agents do not solve it: functional tests do not check security properties, and agents install dependencies on their own.
- State of the art: SAST/SCA in the agent loop, package allowlists and registry firewalls, and RAG plus self-refinement (which cut hallucinated packages to 2.4-9.3%, still too high per the same source).

**7. Long-horizon reliability and agent drift** (stage: multi-step implementation)
- Size: the 80% horizon is several times shorter than the 50% one ([METR](https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/); multiplier secondary). Frontier models scored <25% on SWE-bench Pro at release. Error chains dominate failed trajectories ([arXiv 2607.09510](https://arxiv.org/abs/2607.09510)).
- Why agents do not solve it: errors compound and agents rarely detect their own drift. Self-reports are unreliable.
- State of the art: task decomposition with checkpoints, independent verifier agents, and frequent human checkpoints. The horizon is growing fast (doubling every ~4-7 months).

**8. Flaky tests and CI latency** (stage: CI)
- Size: **>=2.5% of productive developer time** (1.1% investigating false failures, 1.3% repairing; ICST 2024 industrial study, ~30 developers, 5 years) ([TUM PDF](https://mediatum.ub.tum.de/doc/1730194/1730194.pdf)). In 1,960 Java GitHub Actions projects, 3.2% of builds were rerun, totalling ~339 cumulative years of waiting ([summary](https://www.getpanto.ai/blog/flaky-test-statistics), S).
- Why agents do not solve it: a flaky signal poisons the agent's oracle. Agents retry or "fix" tests rather than the nondeterminism.
- State of the art: quarantine plus automated rerun detection (reruns cost little per the ICST study), flaky-test classifiers, and hermetic builds.

**9. Merge conflicts in parallel or agent work** (stage: integration)
- Size: 40.2% of repos have co-active agent PR pairs, covering 79.4% of agent PRs. Replayed merges of 747 pairs gave **41.7% conflicts for cross-agent pairs vs 19.8% intra-agent** (non-overlapping CIs). Cross-agent pairs are rare (0.5% of pairs, 4.3% of repos). 84.4% of conflicted files were source code, and ~42% of conflicts were structural ([Xu et al., arXiv 2607.04697](https://arxiv.org/abs/2607.04697), P abstract). Parallel agents form inconsistent views of shared state ([Geng & Neubig, arXiv 2603.21489](https://arxiv.org/html/2603.21489v1)).
- Why agents do not solve it: worktree isolation postpones conflicts rather than preventing them, and semantic (build-level) conflicts pass a textual merge.
- State of the art: worktree isolation, task partitioning by file ownership, and LLM merge resolution (reported 55-59% match with developers on true Java conflicts; secondary, [developersdigest](https://www.developersdigest.tech/blog/llm-merge-conflict-resolution-study-2026)).

**10. Environment setup and reproducibility** (stage: onboarding, CI and the agent sandbox)
- Size: EnvBench (329 Python and 665 JVM repos) best success is **6.69% Python and 29.47% JVM** ([arXiv 2503.14443](https://arxiv.org/pdf/2503.14443)). SetupBench (Microsoft, 93 instances) gives **38.9-57.4%** for repo setup and 20-53.3% for database configuration, with **38-89% of agent actions unnecessary** ([EmergentMind](https://api.emergentmind.com/papers/2507.09063)).
- Why agents do not solve it: an undocumented environment is tacit knowledge, and agents cannot verify anything they cannot run.
- State of the art: devcontainers and Nix, prebuilt agent sandboxes, and setup benchmarks.

**11. Cost, tokens and latency of agents** (stage: cross-cutting)
- Size: on SWE-bench Verified, repeated runs of the same task vary **up to 30x in tokens**. Accuracy peaks at moderate spend and then flattens. Kimi-K2 and Sonnet 4.5 used >1.5M more tokens than GPT-5 on the same tasks. **Cache-read input tokens dominate cost**, and models predict their own token use poorly ([Bai et al., arXiv 2604.22750, NeurIPS 2026](https://huggingface.co/papers/2604.22750); [NeurIPS](https://neurips.cc/virtual/2026/170688)).
- Why agents do not solve it: unbounded exploration loops (the same "endless file reading" seen on SWE-bench Pro).
- State of the art: per-task budgets, early stopping, context pruning and caching, and model routing.

**12. Knowledge loss, skill erosion and onboarding** (stage: people, long term)
- Size: **-17% comprehension** for AI-assisted learners with no significant time gain ([Anthropic RCT](https://www.anthropic.com/research/AI-assistance-coding-skills)). Copy/paste is up and refactoring down ([GitClear](https://www.devclass.com/ai-ml/2025/02/20/ai-is-eroding-code-quality-states-new-in-depth-report/1626250)), which erodes the shared design understanding of the codebase.
- Why agents do not solve it: agents make the knowledge gap worse by doing the work that would have built understanding, and their rationale is not captured.
- State of the art: explanation-first usage patterns (the high scorers in the RCT), decision records, and session-to-memory capture.

**Debugging and root cause**: I kept this but merged it into rank 1. The 45% "debugging AI code takes longer" figure is its only direct 2025 measure ([Stack Overflow](https://stackoverflow.blog/2025/07/29/developers-remain-willing-but-reluctant-to-use-ai-the-2025-developer-survey-results-are-here)).

### Inferences
- **Ranks 1-4 share a root**: the verification signal (tests, review, production telemetry, agent self-report) is weaker than the generation signal. Any orchestrator gap analysis should score how it produces independent, falsifiable evidence of correctness, not how many agents it runs in parallel.
- The second structural theme is **batch size and volume**. AI raises PR size and count, and DORA, Faros and GitClear all tie that to instability and review cost.
- Parallelism has a measured cost: cross-agent PR pairs conflict about twice as often as intra-agent pairs. Orchestrators that fan out without file-ownership partitioning or shared-state coordination add integration load.
- Cost is a second-order bottleneck compared with verification, but its 30x run-to-run variance makes budgeting unpredictable.

### Gaps
- Most incident and quality figures come from vendors (Faros, Harness, CodeRabbit, Veracode, GitClear) or surveys. Only METR, the Anthropic RCT, ICSE/ICST papers and the arXiv agent studies are independent and rigorous.
- I found no primary 2024-26 quantification of CI latency's share of cycle time, of observability gaps, or of spec-driven development's effect (the ESEM 2026 88k-PR claim is unverified).
- Several arXiv IDs from 2026 were seen only through abstracts or secondary write-ups (2601.20106, 2602.04226, 2604.02547, 2607.09510). Treat their numbers as abstract-level.
- I did not read SWE-Lancer, Terminal-Bench, Google/Meta internal code-review latency studies or SPACE/DevEx framework papers within the bound.
