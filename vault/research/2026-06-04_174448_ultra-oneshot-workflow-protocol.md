# /ultra — ONESHOT Workflow Protocol: A Research-Grounded Design Report

## Executive Summary

The `/ultra plan <target>` command activates a **7-phase ONESHOT workflow** — Ultra Plan → Q&A Pass → Revised Plan → Audit → Fix Injection → Auto Mode Execution → Real-input Verification — in which Phase 2 (a mandatory 6-question stop) is non-skippable. This report grounds each phase of that protocol in the current (early-2026) research literature on prompt engineering, automated prompt optimization, structured/constrained decoding, multi-agent review architectures, and machine-readable verification.

The central thesis the research supports is this: **ONESHOT quality is bounded by prompt quality, and prompt quality is a function of (a) structured decomposition, (b) elicited human intent, (c) reflective optimization over execution traces, and (d) adversarial, machine-readable verification — not raw model scale.** Every one of the seven phases maps to an empirically validated technique. The protocol is, in effect, a hand-assembled instantiation of the same reasoning-amplification stack that DSPy, GEPA, Self-Refine, and multi-lens review agents automate.

---

## 1. The Core Premise: Why Phase Structure Beats One Big Prompt

A recurring theme across the research is that **prompt engineering can improve task performance 40–70% without changing model weights**. This is the single most important justification for `/ultra` existing at all: the marginal return on *structuring how you ask* dominates the marginal return on *which model you use*. The 7-phase decomposition is the structuring mechanism.

The supporting evidence on reasoning elicitation is unambiguous:

| Technique | Source | Measured Gain |
|---|---|---|
| Chain-of-Thought (CoT) | Wei et al., NeurIPS 2022 | PaLM 540B GSM8K **17.7% → 58.1%** |
| Zero-shot CoT ("Let's think step by step") | Kojima et al., 2022 | Triggers reasoning with no exemplars |
| Self-Consistency (multi-path voting) | Wang et al., ICLR 2023 | **+12–18%** on top of CoT |
| Tree-of-Thought | Yao et al., NeurIPS 2023 | Game of 24 **4% → 74%** |
| Graph-of-Thought | — | Extends reasoning to arbitrary directed graphs |

The implication for `/ultra`: the **Ultra Plan (Phase 1)** is structurally a CoT/ToT expansion — it forces the model to externalize a reasoning trajectory *before* committing to code, exactly the move that lifted Game of 24 from 4% to 74%. A monolithic "just build it" prompt is the standard-few-shot baseline; the phased plan is the CoT condition.

This also dovetails with **Claude Code's own recommended core workflow: Explore → Plan → Code**, using plan mode to separate exploration from execution. Anthropic advises *skipping* the plan only for trivial one-sentence diffs (a typo, a log line, a rename) and *planning* when the approach is uncertain, multiple files change, or the code is unfamiliar. `/ultra` is the maximal expression of "plan when the approach is uncertain."

---

## 2. Phase-by-Phase Mapping to the Research

### Phase 1 — Ultra Plan
**Function:** Decompose `<target>` into a reasoned, externalized plan before any edit.

**Research grounding:** This is the Explore→Plan stage of the Claude Code workflow and a CoT/ToT externalization. The practitioner ecosystem converges hard here: Superpowers, Spec Kit, BMAD-METHOD, GSD, and feature-dev's 7-phase flow **all** implement the same skeleton — *Research/Spec → Plan → Execute → Review → Ship* — with a deliberate **fresh-context reset between planning and execution** to avoid context-window degradation. Phase 1's job is to produce an artifact good enough to survive that reset.

**Design note:** Anthropic exposes `Ctrl+G` to open the plan in a text editor for direct human editing before execution. The Ultra Plan should be a *durable, editable artifact* (markdown), not ephemeral chat text — consistent with how slash commands themselves live as `.claude/commands/<name>.md`.

### Phase 2 — Q&A Pass (6 questions, MANDATORY stop)
**Function:** Elicit human intent through six honest questions; non-skippable. The protocol's stated rationale: *"six honest answers > one vague paragraph; plan-quality is bounded by prompt-quality."*

**Research grounding:** This is the highest-leverage and most defensible phase. Two independent lines of evidence support a mandatory clarification gate:

1. **The dominant LLM failure mode is unverified/under-specified success.** The single most common failure mode documented is Claude asserting "tests pass" / "bug fixed" without fresh verification. Phase 2's upstream analogue is asserting *understanding* without confirming it. The Q&A pass forecloses the "I'll just infer intent" path.

2. **Sample-efficiency of intent-rich signal.** The GEPA result is striking precisely because *natural-language signal is dramatically more sample-efficient than scalar signal*. GEPA reads full execution traces as **"Actionable Side Information" (ASI)** and beats the GRPO reinforcement-learning baseline by **6–10% on average (up to 20%) using up to 35× fewer rollouts (100–500 evals vs ~24,000)**. The lesson generalizes to the human-in-the-loop: six pieces of rich natural-language intent are worth more than thousands of trial-and-error iterations against an underspecified goal. The MANDATORY stop is the workflow refusing to spend rollouts before it has the intent.

**Why "skipping phase 2 is REJECTED":** The protocol treats the Q&A as fail-closed because the alternative — proceeding on assumption — reintroduces the exact "asserting success without verification" pathology one phase earlier in the pipeline.

### Phase 3 — Revised Plan
**Function:** Fold the six answers back into the plan.

**Research grounding:** This is one iteration of **Self-Refine (Madaan et al., NeurIPS 2023)** — a generate→critique→refine loop that improves output quality **5–25%**. Here the "critique" is the human answers rather than a model self-critique, which is strictly stronger signal. It is also the workflow's first **APE-style instruction rewrite** (Zhou et al., ICLR 2023, *"LLMs are human-level prompt engineers"*): the revised plan is a better-specified instruction than the original target.

### Phase 4 — Audit (spawn `oneshot-architect-auditor` sub-agent)
**Function:** A fresh-context sub-agent audits the revised plan for gaps in auth, env-vars, file paths, edge cases, and integration points; returns a numbered gap list; does **not** rewrite the plan.

**Research grounding:** This is the richest phase to justify, because the multi-agent-review literature is the most developed:

- **Fresh-context adversarial verification.** Anthropic's four verification mechanisms include *"an adversarial verification subagent/dynamic workflow that refutes findings in a fresh context."* Phase 4 is exactly this — a sub-agent with **isolated context and scoped tools** (per the `.claude/agents/<name>.md` config model) that the planning context cannot bias.

- **Subagent isolation is the correct coordination model here.** The research contrasts **subagents (hub-and-spoke: own context, results summarized back, lower token cost)** against **agent teams (mesh: peer-to-peer mailbox, ~3–4× tokens for 3 teammates, up to ~7× in Plan mode)**. For a single auditor returning a gap list, the hub-and-spoke subagent is the cost-correct choice — agent teams are reserved for parallel collaborative work (split lenses, separate file ownership, competing-hypothesis debugging).

- **Multi-perspective beats single generic review.** kurkowski93's LangGraph agent runs **five parallel lenses (Architectural, Business Domain, Code Quality, Security, Modernization)**; an OpenCode variant scoped permissions per domain (frontend agent blind to Terraform, DevOps agent blind to React) for sharper output. The `oneshot-architect-auditor`'s explicit checklist (auth, env-vars, file paths, edge cases, integration points) is a compressed multi-lens audit. **A scaling path:** for high-stakes `<target>`s, fan Phase 4 into parallel lensed auditors rather than one generalist — the research says this sharpens output.

- **Audit-before-execute reduces downstream defects.** Baz's Spec Review agent (Amazon Bedrock + AgentCore) decomposes specs into discrete requirements and spawns isolated per-requirement subagents, reporting **bugs reduced up to 50% and time-to-merge down 30–70%**. Phase 4's "decompose plan → numbered gaps" is the planning-stage analogue of Baz's "decompose spec → per-requirement subagents."

**Important design constraint the research validates:** the auditor *returns a gap list, does not rewrite the plan*. This separation of *finding* from *fixing* mirrors the ZeroFalse / multi-agent-security discipline where adjudication is a distinct stage from remediation — and avoids the auditor smuggling in unreviewed changes.

### Phase 5 — Fix Injection
**Function:** Feed the numbered gap list back into the plan, resolving each gap.

**Research grounding:** A second Self-Refine iteration, now driven by the auditor's machine-structured findings. The two-stage *Revised Plan (human intent) → Fix Injection (auditor gaps)* sequence is a deliberate **double critique-refine loop**, which the Self-Refine and APE results predict will compound the 5–25% per-iteration quality gain.

### Phase 6 — Auto Mode Execution
**Function:** Execute the now-audited, gap-closed plan.

**Research grounding:** This is the Code stage of Explore→Plan→Code, executed *after* the fresh-context reset that all practitioner repos (Superpowers/Spec Kit/BMAD/GSD) prescribe. The plan artifact carries the reasoning across the reset so execution doesn't degrade. Execution is where **structured outputs** earn their keep (see §3): typed, schema-constrained tool calls turn the build from a text-generation problem into a function-call problem with eliminated parse/retry failure classes.

### Phase 7 — Real-input Verification
**Function:** Verify against real input, not assertions.

**Research grounding:** This phase is the protocol's answer to *the single most common failure mode — asserting success without fresh verification.* The research insists verification be **machine-readable and run by Claude itself ("evidence before claims")**: tests, build exit codes, linters, fixture diffs, browser screenshots. Anthropic's four mechanisms are directly usable as Phase-7 substrate:

| Mechanism | Behavior | Phase-7 Use |
|---|---|---|
| In-prompt iteration | Model re-checks within the turn | Lightweight self-check |
| `/goal <condition>` | A separate fast evaluator re-checks after **every turn** | Continuous gate on the success condition |
| Stop hook | Deterministic gate; Claude Code overrides and ends the turn after **8 consecutive blocks** | Hard fail-closed gate |
| Adversarial verification subagent | Refutes findings in a fresh context | Confirms the build actually meets `<target>` |

Baz's runtime verification (AgentCore Browser Tool: DOM inspection, event simulation, visual testing in live preview, triggered by GitHub PR webhook) is the gold standard for "real input" — it confirms behavior at runtime, not just that code compiles. Phase 7 should prefer runtime/fixture evidence over static checks wherever the target produces observable behavior.

---

## 3. Cross-Cutting Substrate: Structured Outputs

By early 2026, **structured outputs (constrained decoding to a JSON schema) became the foundational production prompt-engineering advance.** This is infrastructure, not a phase — it underpins Phases 4–7:

- **OpenAI Responses API** guarantees **100% schema compliance with `strict: True`**.
- **Anthropic** released structured outputs for Claude as a **public beta on the Messages API via `response_format` json_schema**.
- Effect: LLM calls become **typed function calls**, eliminating parsing/retry failure classes.

For `/ultra`, this means the **Phase 4 gap list should be a schema-constrained JSON object** (e.g., `[{id, category, location, severity, fix}]`), not free text. That makes Phase 5 (Fix Injection) deterministic to consume and Phase 7 (Verification) able to assert per-gap closure. Anthropic's **Opus 4.6 "adaptive thinking"** (dynamically sets reasoning budget; extended thinking allocates `budget_tokens`, e.g. 10000) is the natural model for the reasoning-heavy Phases 1 and 4, while routine execution (Phase 6) can run on Sonnet — matching the cost guidance that reserves Opus for the lead/architecture role and assigns Sonnet to workers.

---

## 4. Where `/ultra` Could Be Automated: DSPy / GEPA

`/ultra` is a *hand-assembled* optimization loop. The research shows this loop is now **production-grade automatable** — relevant if the protocol is ever meta-optimized.

**DSPy** (Stanford; matured in its 3.x series by early 2026) reframes prompting as programming via **Signatures / Modules / Optimizers**. Its optimizers map onto `/ultra`'s phases:

| Optimizer | Mechanism | Sample Needs | Typical Gain |
|---|---|---|---|
| **MIPROv2** | Bayesian search over **instructions + demonstrations** | 200+ examples, 40+ trials | **15–40%** on domain metrics |
| **GEPA** (Genetic-Pareto) | Reflective; reads full traces as ASI; **instruction-only, no few-shot demos** | **3–10 examples, 20–100 evals** | **+10–13% over MIPROv2**; +12% AIME-2025 |
| **SIMBA** | Failure-focused; stochastic mini-batch finds high-variability examples, LLM introspection generates fix rules | Targeted | Targeted hard-case fixes |

**GEPA (Agrawal et al., arXiv:2507.19457, submitted 25 Jul 2025, ICLR 2026 oral)** is the most directly analogous to `/ultra`'s philosophy, because it optimizes by *reflecting on full execution trajectories in natural language* — the same thing Phase 2 (human Q&A) and Phase 4 (auditor trace) do manually. Concrete GEPA gains:

- MATH ChainOfThought **67% → 93% (+26 points)**
- AIME 2025 (GPT-4.1 Mini) **46.6% → 56.6% (+10pp)**
- Facility-support structured extraction **2.93/3 (97.8%)**
- Financial entity extraction **+14 over DSPy / +22 over raw OpenAI baseline**
- Across six tasks on Qwen3 8B: **beats GRPO by 6–10% avg (up to 20%) with up to 35× fewer rollouts**

GEPA ships standalone (`pip install gepa`, `optimize_anything` API) and is integrated into **DSPy (`dspy.GEPA`), MLflow, Google ADK/Gemini Enterprise, and Databricks** — which reported building enterprise agents **"90× cheaper," beating Claude Opus 4.1.**

**`/ultra`-relevant takeaway:** if the protocol's prompts (the Ultra Plan template, the six Q&A questions, the auditor checklist) were treated as DSPy modules, **GEPA is the right optimizer** — it needs only 3–10 examples, optimizes instructions without demos (matching `/ultra`'s instruction-driven design), and reflects on traces exactly as `/ultra` does manually. MIPROv2's 200+-example appetite makes it ill-suited to a workflow run a handful of times per target. SIMBA would be the tool for fixing a *specific recurring `/ultra` failure mode* (e.g., it always misses env-var gaps).

---

## 5. The Verification Hardening Lessons (Phase 4 + Phase 7 Depth)

The SAST/false-positive literature offers the deepest guidance on making the audit and verification phases *trustworthy* rather than noisy — the failure mode being an auditor that floods Phase 5 with false gaps.

**Context beats raw diffs.** Feeding raw git diffs to an AI is insufficient because diffs lack surrounding context. Baz layers **Difftastic** (grammar-aware syntax diffing that ignores whitespace/formatting noise to conserve tokens) and **Tree-Sitter** (incremental AST parser assigning persistent unique IDs to functions/variables across versions) to enable impact reasoning and root-cause analysis. *`/ultra` implication: the Phase-4 auditor should receive AST-aware/structured context about the plan's touch points, not a bare diff or file dump.*

**Structured contracts + specialized rubrics cut false positives.** **ZeroFalse (arXiv:2510.02534v1, 2026, JACM)** treats CodeQL SARIF alerts as **structured contracts enriched with flow-sensitive source-to-sink taint traces, surrounding code snippets, and CWE-specific micro-rubrics/boundary checklists** before LLM adjudication. Across 10 LLMs it hit **F1 0.912 on OWASP Java Benchmark (grok-4)** and **0.955 on OpenVuln (gpt-5, recall 0.9142)**, holding recall *and* precision above 90%. *`/ultra` implication: Phase 4's checklist (auth, env-vars, file paths, edge cases, integration points) is exactly a "CWE-specific micro-rubric" applied to architecture — the research validates checklist-driven over generic auditing.*

**Specialized prompting > scale; reasoning models > big context.** **CWE-specialized prompting consistently outperforms generic "one-size-fits-all" prompts, and reasoning-oriented LLMs deliver the most reliable precision-recall balance — raw model scale and extended context windows alone do not guarantee generalization.** The robustness gap is stark on noisy real-world data: on OpenVuln, **gemini-2.5-pro collapsed to F1 0.372** despite F1 0.910 on OWASP, while **smaller gpt-oss-20b held F1 0.904.** *`/ultra` implication: (a) use a reasoning model (adaptive-thinking Opus) for the auditor, not merely the largest context window; (b) the specialized, scoped auditor prompt is doing real work — don't replace it with "audit this generally."*

**Reliability varies by language.** LLM review is **Excellent for Python/JS/TS, Less Reliable for C/C++/Rust.** Phase-7 verification confidence should be calibrated to the target language; for C/C++/Rust targets, lean harder on runtime evidence (tests, exit codes) and less on the auditor's static read.

**Pipeline lineage (for completeness):** predecessor hybrids **LLM4SA (Wen et al. 2024, the first such approach)** and **LLM4FPM (Chen et al. 2024, used code slicing for concise complete context)** were limited to a small CWE set and never benchmarked multiple LLMs systematically. A complementary direction (Arjun Gopalakrishna) injects LLM semantic metadata *throughout* the pipeline — SAL annotations for C/C++, AST node tagging (`taint_status`, `domain_role`, `security_level`), CFG edge risk labeling, call-graph refinement — rather than only post-hoc adjudication. The architectural lesson for `/ultra`: enrich context *upstream* (at Phase 1/4 planning) rather than only adjudicating downstream.

---

## 6. Synthesis: `/ultra` as a Manual Reasoning-Amplification Stack

| `/ultra` Phase | Research Analogue | Validated Effect |
|---|---|---|
| 1. Ultra Plan | CoT / ToT externalization; Explore→Plan | Reasoning gains up to ToT's 4%→74% regime |
| 2. Q&A Pass (mandatory) | ASI / rich-signal intent (GEPA); pre-empts unverified-assumption failure mode | Sample-efficient intent; 35× fewer downstream rollouts |
| 3. Revised Plan | Self-Refine iter 1; APE instruction rewrite | +5–25% per refine loop |
| 4. Audit subagent | Adversarial fresh-context verification; multi-lens review; checklist/micro-rubric | Up to −50% bugs (Baz); F1 >0.90 with rubrics (ZeroFalse) |
| 5. Fix Injection | Self-Refine iter 2 (structured critique) | Compounding refine gain |
| 6. Auto Execution | Code stage; structured outputs as typed calls | Eliminated parse/retry failure classes |
| 7. Real-input Verification | Evidence-before-claims; `/goal`, Stop hook, adversarial subagent; runtime testing | Defeats the #1 failure mode |

The protocol's core claim — *"plan-quality is bounded by prompt-quality"* — is precisely the thesis the prompt-engineering literature has spent three years validating: **40–70% achievable gains from structuring the ask, with the largest returns from reasoning externalization (Phases 1, 4), rich natural-language intent signal (Phase 2), iterative critique-refine (Phases 3, 5), and machine-readable adversarial verification (Phases 4, 7).** `/ultra` is a hand-built GEPA-shaped loop: it reflects on trajectories (human Q&A + auditor traces), refines instructions over demonstrations-free signal, and gates on evidence.

---

## 7. Recommendations (Speculative — flagged)

These extend the protocol along directions the research supports but that go beyond the cited material; treat as design speculation:

1. **Schema-constrain the Phase-4 gap list** (json_schema `response_format`) so Phase 5 consumption and Phase 7 per-gap closure-checks are deterministic. *Directly supported by the structured-outputs learning.*
2. **Fan Phase 4 into parallel lensed auditors** (architecture / security / integration / data-flow) for high-stakes targets, using subagents (not agent teams) to stay cost-correct. *Supported by multi-lens-beats-generic + subagent-cost learnings.*
3. **Calibrate Phase-7 evidence weight by target language** — runtime-heavy verification for C/C++/Rust, static-read-acceptable for Python/JS/TS. *Supported by the language-reliability learning.*
4. **If `/ultra`'s own templates are ever tuned, use `dspy.GEPA`, not MIPROv2** — `/ultra` runs too few times per target to feed MIPROv2's 200+-example budget, and GEPA's instruction-only, trace-reflective design matches `/ultra`'s architecture exactly. *Supported by the optimizer sample-requirement learnings.*
5. **Reserve adaptive-thinking Opus for Phases 1 and 4** (reasoning-bound), Sonnet for Phase 6 (execution-bound). *Supported by adaptive-thinking + cost-routing learnings.*

The throughline: `/ultra` already encodes, by hand, the techniques the 2022–2026 literature proved most effective. Its non-negotiable Phase-2 stop and its evidence-gated Phase 7 are not bureaucratic friction — they are the two interventions the research most strongly associates with avoiding the dominant LLM failure mode (confident, unverified, under-specified success).

## Sources

- <https://github.com/Tanmay1112004/prompt-engineering>
- <https://aiworkflowlab.dev/article/production-prompt-engineering-2026-structured-outputs-prompt-chaining-dspy>
- <https://www.colabcodes.com/post/advanced-prompt-engineering-building-multi-step-context-aware-ai-workflows>
- <https://www.meta-intelligence.tech/en/insight-prompt-engineering>
- <https://arxiv.org/abs/2507.19457>
- <https://www.morphllm.com/gepa-prompt-optimization>
- <https://dspy.ai/tutorials/gepa_ai_program/>
- <https://github.com/gepa-ai/gepa>
- <https://deepwiki.com/gepa-ai/gepa-artifact/3.3-comparison-with-baselines>
- <https://code.claude.com/docs/en/best-practices>
- <https://github.com/shanraisshan/claude-code-best-practice>
- <https://community.sap.com/t5/artificial-intelligence-blogs-posts/claude-code-best-practices-for-developers/ba-p/14394164>
- <https://sidbharath.com/blog/claude-code-the-complete-guide/>
- <https://claudefa.st/blog/guide/development/agentic-engineering-best-practices>
- <https://code.claude.com/docs/en/agent-teams>
- <https://claudefa.st/blog/guide/agents/agent-teams>
- <https://github.com/ThamJiaHe/claude-code-handbook/blob/main/docs/agent-teams-guide.md>
- <https://ice-ice-bear.github.io/posts/2026-03-03-claude-code-agent-teams/>
- <https://kurkowski.substack.com/p/ai-that-audits-your-code-building>
- <https://aws.amazon.com/blogs/machine-learning/how-baz-improved-its-ai-agent-code-review-accuracy-using-amazon-bedrock-agentcore/>
- <https://yashdhirajoza.github.io/Agentic-AI-Code-Review-System/agent.html>
- <https://baz.co/resources/building-an-ai-code-review-agent-advanced-diffing-parsing-and-agentic-workflows>
- <https://arxiv.org/html/2510.02534>
- <https://link.springer.com/article/10.1007/s10664-026-10842-2>
- <https://github.com/247arjun/ai-static-analysis-pipeline/blob/main/Elevating%20Code%20Security%20and%20Reliability%20via%20LLM-Augmented%20Static%20Analysis.md>
- <https://papers.cool/arxiv/2510.02534>

## Run metadata

- **Prompt:** # /ultra — ONESHOT Workflow Protocol
- **Depth / breadth:** 2 / 3
- **Queries used:** 6 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: empty-input, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 445.2 s
- **Errors during run:** 3
- **Started at:** 2026-06-04T15:44:48Z
- **Module version:** deep_research 0.1.0

<details>
<summary>Error log</summary>

- `fetch_page 'https://medium.com/@connect.hashblock/10-prompt-engineering-...': page-fetch: https://medium.com/@connect.hashblock/10-prompt-engineering-patterns-that-automate-multi-step-workflows-a8a18ecdfbf4: HTTP Error 403: Forbidden`
- `fetch_page 'https://medium.com/@shankaravi6/claude-code-subagents-vs-age...': page-fetch: https://medium.com/@shankaravi6/claude-code-subagents-vs-agent-teams-complete-practical-guide-edceb6a0043a: HTTP Error 403: Forbidden`
- `fetch_page 'https://medium.com/@Micheal-Lanham/building-an-ai-code-revie...': page-fetch: https://medium.com/@Micheal-Lanham/building-an-ai-code-reviewer-that-actually-understands-your-github-repos-b76d35a32d93: HTTP Error 403: Forbidden`

</details>
