# Claude Power Pack Backlog — PERCOS, Hyperplan and Four CRO Intelligence Skills

**ID:** CPP-SKILL-INTAKE-2026-11-19-06
**Created:** 2026-11-19
**Status:** OPEN — BACKLOG INTAKE ONLY; ZERO SKILLS IMPLEMENTED OR DEPLOYED; ZERO CPP RUNTIME TESTS EXECUTED
**Priority:** P1 evidence/ownership audit; P1 targeted CRO and planning pilots if evidence supports them; P2 Percos specialization pending source inspection
**Owner request:** Absorb all six user-supplied Skills Directory references into Claude Power Pack, keeping the useful transferable capabilities and making them reusable engineering infrastructure. **Name the first CPP-facing capability "Percos", NOT "Percom"** (intentional owner naming joke).
**Canonical repository:** https://github.com/jacobo07/claude-power-pack
**Document role:** Intake ledger, bounded research mission, ownership and acceptance contract. NOT a claim of upstream functionality, legal reuse approval, software delivery, or automatic installation.

## 0. Source-of-truth and evidence ceiling

Six exact inputs, six required final source-level dispositions. All are in scope; none may disappear silently because its website is inaccessible.

| Intake ID | CPP-facing name | Exact user-provided source | Source-body evidence as of intake | Candidate destination / status |
| --- | --- | --- | --- | --- |
| CPP-S06-01 | **Percos** | https://www.skillsdirectory.com/skills/brycewang-stanford-percom-review-process | Directory page did not yield inspectable content in this session. Name and implied topic from URL only; NO claim about its actual method or original author repository. | Evidence-based critical review / research-review adapters, owner TBD after audit. **UNVERIFIED SOURCE** |
| CPP-S06-02 | **Hyperplan** | https://www.skillsdirectory.com/skills/code-yeongyu-hyperplan | Directory listing read; matching source SKILL.md directly inspected in GitHub at pinned revision below. | Existing planning/decision review/GSD X; **SOURCE-INSPECTED PARTIALLY, NOT ABSORBED** |
| CPP-S06-03 | **CRO Customer Voice** | https://www.skillsdirectory.com/skills/daltonai-cro-customer-voice | Page did not yield inspectable content; behavior inferred ONLY from title as research hypothesis. | Customer insight, provenance, CRO evidence; **UNVERIFIED SOURCE** |
| CPP-S06-04 | **CRO Brand Research** | https://www.skillsdirectory.com/skills/daltonai-cro-brand-research | Page did not yield inspectable content; behavior inferred ONLY from title as research hypothesis. | Brand/positioning research + CDIO/CCF/Founder OS; **UNVERIFIED SOURCE** |
| CPP-S06-05 | **Funnel Walkthrough** | https://www.skillsdirectory.com/skills/daltonai-funnel-walkthrough | Page did not yield inspectable content; behavior inferred ONLY from title as research hypothesis. | Real-browser CRO journey / CDIO/OSA/PP eval; **UNVERIFIED SOURCE** |
| CPP-S06-06 | **Competitor Roadmap** | https://www.skillsdirectory.com/skills/daltonai-competitor-roadmap | Page did not yield inspectable content; behavior inferred ONLY from title as research hypothesis. | Competitor intelligence → product prioritization / Founder OS; **UNVERIFIED SOURCE** |

**Hyperplan primary-source pointer:** https://github.com/code-yeongyu/oh-my-openagent/blob/b036a83c622e637bb483c423733449af8f7f3923/.agents/skills/hyperplan/SKILL.md — upstream dev commit **b036a83c622e637bb483c423733449af8f7f3923**, observed on 2026-11-19; file blob **c3492f46f04b7ff8050753cb74862ed49eb4e02e**. This is a snapshot for the audit, not a declaration that this version is stable or suitable for CPP. Confirm LICENSE.md and any transitive attribution before code/prompt reuse.

**Important drift observed:** the Skills Directory Hyperplan snapshot describes a five-member adversarial process with a required final handoff to a dedicated plan agent, but its role/category/model examples differ from those in the inspected GitHub dev branch. This is already an example of why the source/commit/host contract must be pinned. Do NOT hardwire either listing's model IDs, role categories, team-mode preconditions, or host-specific agents into CPP.

**Hard evidence rule:** Source page title/URL ≠ actual SKILL.md contract ≠ tested behavior ≠ CPP integration ≠ shipped benefit. For the five uninspected bodies, all method descriptions below are explicitly CANDIDATE REQUIREMENTS, not observations about their implementations. If an original repository cannot be authenticated, register UNKNOWN / SOURCE_UNAVAILABLE and do not fabricate contents.

## 1. Mission: complete absorption without framework multiplication

Produce a full, versioned capability census across all six sources; map every useful principle, workflow, rubric, template, example, script, dependency, security boundary, test and failure mode to its existing CPP canonical owner; then **reuse → extend → merge → connect → generalize → create only with proven gap**.

"Absorb everything" means **100% of the verified source inventory receives an explicit evidence-backed disposition**, including compatible improvements, overlapping functionality, risks, non-transferable host assumptions, excluded or non-licensable content, and unverified items. It never means copy six skills wholesale, install an additional orchestration OS, run a second always-on router, or claim every proposed pattern is good.

Required dispositions per source capability:
- ALREADY_OWNED (with evidence), EXTEND, CONNECT, ADAPT_WITH_TESTS, EXTRACT_METHOD, REFERENCE_ONLY, UPSTREAM_ONLY, REJECT, BLOCKED_BY_LICENSE, SOURCE_UNAVAILABLE, UNDERDETERMINED.
- Only **verified, tested behavior change** can be classified ABSORBED_AND_PROVEN. The intake itself cannot earn that status.
- Track a negative result as knowledge, too: what was rejected, why, against which evidence, and what would change the conclusion.

## 2. Canonical ownership and system boundaries — hypotheses to reality-check

| Workstream | Inspect / prefer existing CPP owners | Non-duplication rule |
| --- | --- | --- |
| Adversarial planning / Hyperplan | modules/gsd_x, commands/ultra.md, commands/arch-decision.md, modules/arch-decision, modules/decision_review, modules/pp_eval, modules/skill_router | No separate compulsory five-agent planner, plan router, daemon or competing approval authority |
| Percos review capability | modules/code-review, modules/code_review, modules/decision_review, modules/deep-research, modules/pp_eval, current research and knowledge standards | Do not invent a second reviewer or claim conference-quality peer review without evidence |
| CRO customer voice | modules/founder_os, modules/knowledge_acquisition, modules/pp_eval, modules/cdio and relevant marketing/ads owners | Customer evidence is a reusable dataset/provenance input, not an unverified synthetic persona generator |
| CRO brand research | modules/ccf, modules/cdio, modules/design-md, modules/founder_os, product/brand research owners | Reuse existing design/brand authority; do not create a second brand DNA or DESIGN.md truth source |
| Funnel walkthrough | modules/cdio, modules/osa, modules/product_demo, existing real-browser/QA capabilities and verification contracts | Use executable user journeys; no fake browser evidence or screenshot-only "walkthrough passed" |
| Competitor roadmap | modules/founder_os, modules/deep-research, modules/decision_review, modules/knowledge_acquisition | No competing opportunity OS, stale competitor truth cache or independent speculative roadmap authority |
| Cross-cutting skill routing/evals | modules/skill_router, modules/pp_eval, knowledge vault, UKDL, quality/baseline ratchet owners | No new global hot prompt, parallel evaluator, duplicate knowledge graph or recurring forced multi-agent spend |

These are **candidate owners grounded in existing repository paths**, not proven active call-path mappings. Verify code reachability, host registration, current HEAD, workload triggers, overlap and maintenance responsibility before patching.

Related canonical backlog: [CPP-AGSK-001: Agent Skills absorption](2026-10-11_addyosmani-agent-skills-selective-absorption.md); [21 design-resource absorption](2026-10-30_cdio-21-design-resources-universal-absorption.md); [CDIO brand identity](2026-10-21_cdio-brand-identity-logo-absorption.md); [Synsation UX](2026-10-13_synsation-ux-patterns-absorption.md). Merge overlapping test patterns and ownership; do not restart their work.

## 3. PERCOS — evidence-based multi-pass review (SOURCE HYPOTHESIS)

**Naming invariant:** CPP-facing display name, command/skill candidate, documentation, activation vocabulary, test IDs and program identity MUST use **Percos**. Preserve "PerCom" only where historically necessary inside an exact external URL, citation, upstream title, attribution, or provenance field. Do not silently rewrite third-party intellectual property or URLs.

The URL suggests a review-process skill but does NOT establish its actual methodology. First retrieve and read full upstream SKILL.md and all dependencies, identify if "PerCom" refers to a conference, internal workflow or something else, and evaluate its actual scope. Only then decide whether it brings value beyond current code review, architecture review, research review and quality gates.

**Candidate transferable outcomes to test, not assume:**
- Evidence-grounded review rubric: claims, supporting observations, uncertainty, contradictions and failure-to-reproduce.
- Independent first pass before seeing the author's preferred conclusion; review of assumptions, design, method, statistical/risk validity where relevant.
- Explicit weaknesses, actionable revision requests, competing hypotheses and reconciliation (not performative disagreement).
- Review record with source version, evidence pointers, confidence limits, unresolved questions and disposition.
- Graduated application to research papers, plans, engineering design reviews or product claims ONLY where source and ROI support generalization.

**Falsification:** can Percos find consequential seeded flaws that existing CPP review misses without high false-positive rate, reviewer bias, redundant model calls or unnecessary friction? If not, REFERENCE_ONLY or REJECT.

## 4. HYPERPLAN — risk-gated adversarial plan strengthening (PARTIALLY VERIFIED)

**Observed upstream mechanism at pinned source:** five distinct critique perspectives (simplicity skeptic, cross-component validator, evidence researcher, architecture critic, creative alternative challenger), multi-round challenge/defense/distillation, then mandatory conversion of surviving insights into an executable plan by a dedicated planning agent. Source requires host-specific team orchestration and predefined agent categories. Do not mistake elaborate debates for empirical planning quality.

**Candidate CPP integration:** add an **optional risk/uncertainty-triggered adversarial plan review path** inside the existing planner and decision review, with:
- Independently challenged assumptions and explicit evidence, objective success conditions and competing minimal alternatives.
- Reviewer separation: contract/artifact first, author rationale only after unbiased critique when feasible.
- Defend/refine/concede decisions, versioned dissent, risk mitigation, stop/abstain decisions and an accountable final planner.
- Dynamic minimum-sufficient debate depth (single skeptic for low-risk, multi-perspective review only at high blast radius); bounded cognitive spend and deterministic fallbacks if no multi-agent team exists.
- Existing **inline-in-chat approval** semantics and plan-file backup where CPP policy requires; never impose the upstream dedicated plan-agent identity or its specific model roster.
- Strong fit with /ultra only if routing and A/B evidence show actual improvement; /cpp-gsd-long remains for genuinely multi-context unattended execution, **not** automatically for every plan.

**Reject upfront:** unconditional five-agent + three-round tax, mandatory model-brand identities, copied aggressive persona prompts, team-mode hard failure for ordinary CPP operation, hallucinated consensus, a plan detached from live repo reality.

**Test:** seeded architecture/concurrency/security/ROI flaws; compare same tasks with CPP baseline, 1-review and adversarial variants. Record serious defects caught, false positives, plan validity, owner decisions, latency, tokens, model costs, pass/fail at implementation, and repeated-task transfer.

## 5. CRO cluster — one evidence-to-experiment loop, four source inventories

These are **workload requirements to validate against source**, not descriptions of the four SKILL.md implementations. A complete useful CRO loop is:

**Observed user/market evidence → customer voice and jobs-to-be-done → brand/positioning hypotheses → real funnel journeys → competitor-backed alternatives → prioritized experiments → production measurement → verified improvement → institutional reuse.**

### CPP-S06-03 — CRO Customer Voice

Investigate whether upstream provides: evidence acquisition from interviews, reviews, support, search terms and consented qualitative records; language-of-customer extraction; objections, motivations, triggers, anxieties, purchase criteria, segments, JTBD and journey stages; traceable quote IDs and verbatim-vs-paraphrase distinctions.

Candidate CPP outcome: **structured, source-linked Voice-of-Customer records** that can inform copy, services, UX and experiments without claiming synthetic outputs are real interviews. Prohibit invented testimonials, invented counts, demographic inference without support, unsupported customer quotes and leakage of personally identifying records.

Validation: each customer assertion has a verifiable source or is clearly a hypothesis; consent/usage rights and minimization policy; blinded spot-check of quote fidelity and segment relevance; ES/EN multilingual cases.

### CPP-S06-04 — CRO Brand Research

Investigate source treatment of brand positioning, promise, differentiators, evidence-based claims, competitive language, emotional drivers, identity tone, trust, objections, offer hierarchy and message-market consistency.

Candidate CPP outcome: **provenance-backed positioning/claim evidence** shared with CCF/CDIO/Founder OS; distinguish company assertions from independent proof. Claims absent from the source stay UNVERIFIED. No fabricated competitive superiority, awards, credentials, years in business, reviews or client results.

Validation: reviewers can trace each proposed positioning statement to evidence or an explicitly labeled hypothesis; brand consistency and tone constraints survive UI/email/landing-page transformations.

### CPP-S06-05 — Funnel Walkthrough

Investigate source protocol for acquisition → entry point → landing → service/product discovery → pricing/offer → form/cart → payment/booking/lead → success/error/follow-up.

Candidate CPP outcome: **reproducible, real-browser journey audits** with route, viewport, locale, device, consent state, screenshots/DOM/event evidence where available, keyboard/mobile/accessibility checks, network/performance defects, CTA visibility, friction severity and exact reproduction steps. Treat unavailable authentication/tools as unverified, not as passing paths.

Validation: scripted walkthrough finds seeded missing CTA, invalid disabled forms, broken mobile interaction, unexpected redirect, failed thank-you/analytics event and checkout error; negative controls avoid fabricating failure. Consent and privacy guardrails apply to recording journeys.

### CPP-S06-06 — Competitor Roadmap

Investigate whether source provides competitive collection, update cadence, segmentation, alternative positioning, differentiator scoring and product roadmap comparison.

Candidate CPP outcome: **date-stamped competitor evidence and opportunity-to-experiment ranking**, separating verified observations, estimates and hypotheses. No unsupported pricing/revenue/traffic/customer-count forecasts; no copying proprietary user content, unauthorized crawling, competitor impersonation, circumvention or ToS-incompatible acquisition.

Validation: time-staleness invalidation, sources traced by observation date and page/version, comparability across same market/segment, no automatic feature cloning; falsifiable ranking based on impact, confidence, effort, reversibility and strategic differentiation.

## 6. Cross-source composability without a new "CRO OS"

Build on existing owners using shared **evidence contracts** rather than a new orchestrator:

- Source identity: source URL/repo, original project/author, commit/version/date, licence, acquisition method and content hash.
- Observation identity: inspected artifact, observed fact, screenshot/transcript/evidence pointer, timestamp/locale, confidence and contradictions.
- Hypothesis identity: proposed insight, audience/context, expected causal mechanism, severity/opportunity, competing alternatives, uncertainty and invalidators.
- Decision identity: owner, alternatives, chosen action, expected cost/risk/value, explicit approvals and rollback conditions.
- Experiment identity: baseline, changes, guardrail metrics, event definition, minimum viable instrumentation and measurement horizon.
- Outcome identity: actual vs expected result, denominators, segment, uncertainty, win/loss/no-result verdict, regression impact and transferable pattern.
- Institutionalization: Knowledge Vault/UKDL record, applicable owner, red-capable regression/eval proof, promotion decision and traceability.

A "customer voice insight" with no source is a hypothesis. A "funnel conversion gain" with no comparable post-launch events is **not measured**. "Absorbed" means the relevant future CPP work genuinely routes to the proven pattern and improves outcomes, not simply that six markdown skills exist.

## 7. Execution packages (existing ownership first)

- **S06-00 — Repository Reality Scan (P1):** inspect latest HEAD, active branches, canonical owners, existing backlogs, capability routing, harnesses, version drift and runtime/installed parity; preserve live concurrent work. Record no-op/overlap before any code.
- **S06-01 — Upstream Retrieval and Identity (P0 prerequisite):** resolve every Skills Directory URL to its authentic source repo, exact SKILL.md, references, scripts, assets, readmes, examples and tests. Pin commit/version and content hashes. Identify upstream collisions, redirects, missing resources and read-vs-install differences. NEVER infer source contents from path labels.
- **S06-02 — Licencing/Security/Host Audit (P0 prerequisite):** verify each upstream license and third-party attribution, repository authority, dependencies, external calls, executable hooks, secrets/data flows, prompt-injection surfaces, browser/session side effects, team-mode assumptions and irreversibility. Record REFERENCE_ONLY/BLOCKED where appropriate. Reading public docs is not permission to install or execute.
- **S06-03 — Complete Six-Source Census and Delta Matrix (P1):** inventory 100% of inspected source capabilities and all dependencies; every item gets source pointer, CPP existing owner/call-path, overlap, transferable invariant, test plan, cost/ROI, applicability and disposition. Unavailable material retains explicit UNKNOWN, never disappears.
- **S06-04 — Percos Pilot (P2 pending S06-01):** once the original method is actually verified, test smallest defensible review rubric against existing CPP review, deep research and decision-review; do not add a command by default.
- **S06-05 — Hyperplan Risk-Gated Pilot (P1):** benchmark minimal adversarial review versus existing plan path on real and seeded tasks; isolate the genuinely valuable critiques; formalize into existing planner, preserving live-state/inline-approval and budget policies.
- **S06-06 — Customer Voice Evidence Adapter (P1 conditional):** if source warrants, add only missing VoC capture/qualification/traceability and multilingual evals to existing knowledge/Founder OS owners.
- **S06-07 — Brand Research Reconciliation (P1 conditional):** compare with CCF/CDIO/design-md/Founder OS; add provenance and message/claim consistency only at identified gaps.
- **S06-08 — Real Funnel QA (P1 conditional):** design user-path fixtures with baseline screenshots/DOM/behavior/analytics proof; reuse browser adapters and existing CDIO/OSA/QA.
- **S06-09 — Competitor Research Roadmap (P2 conditional):** versioned evidence, staleness detection, controlled scoring and decision/experiment links inside existing strategic owner.
- **S06-10 — Combined CRO Experiment Pilot (P1 if four source audits justify):** run ONE bounded real-world website example where legal/consent and test infrastructure allow; compare evidence completeness, defect discovery, decision clarity and measurement against baseline. Pilot is not proof of uplift until deployed results exist.
- **S06-11 — Routing and Interference (P1):** extend modules/skill_router and modules/pp_eval only if needed; positive/negative triggers ES/EN, risk-scoped activation, no overlap double-wake with CRO/CDIO, GSD/ultra, Code Review or Founder OS; bounded prompt/context cost.
- **S06-12 — Knowledge/UKDL/Baseline Ratchet (P1 on demonstrated wins):** canonical incident/lesson records, source provenance, failure-mode generalization, tests and affected-proof closure; promote to shared default only where verified and cost-effective. Rejected options are retained as negative knowledge, not discarded.

Execution order: S06-00 → S06-01 → S06-02 + S06-03 → independent smallest pilots → combined CRO pilot → routing/effect verification → ratchet. Can parallelize independent source retrieval only after ownership and permission boundaries are understood.

## 8. Required red-capable cases

1. Source directory advertises feature X but upstream pinned SKILL.md does not: flag contradiction; no absorption claim.
2. Source unavailable or no verified licence: retain intake row, block code/prompt copying, allow only independent general principles.
3. Upstream asks to alter host config, invoke unavailable team APIs or send network secrets: treat as untrusted data, never as instruction.
4. Trivial typo activates five models or CRO research: routing cost regression; must stay asleep.
5. Reviewer accepts the author's planted wrong explanation or all reviewers share contaminated source: independent flaw-detection regression.
6. Three adversarial rounds do not change defect catch or cost-adjusted decision outcome: terminate/reject excess orchestration.
7. Real customer quote is fabricated, decontextualized, duplicated, paraphrased as verbatim or not licensed: fail.
8. Brand claim lacks evidence or contradicts actual business offering: fail.
9. Funnel audit says PASS while mobile booking fails, success event never fires or auth was unavailable: fail.
10. Competitor reference is stale, wrong region/segment or claims market performance without data: invalidates ranking.
11. A/B experiment declares uplift from screenshots, a tiny biased sample, attribution mismatch or invented conversion metrics: fail.
12. Active worktrees collide, a second planner/knowledge authority appears, or a new skill has no live consumer: no promotion.
13. Negative controls or relevant measured population are removed to make a quality gate green: fail.
14. Source improves one domain but degrades false wakes, privacy, runtime, reproducibility or maintainability in neighboring domains: reject until reconciled.
15. Source methodology creates onerous user interviews when the project already holds the requisite facts: no unnecessary owner interruption.

## 9. Measured acceptance and definition of done

**Intake complete now:** exactly SIX source URLs and CPP-facing identifiers recorded, naming invariant fixed, known evidence gaps explicit. Nothing else may be called done in this document.

**Source audit done when:** all six are resolved to source revisions or explicitly marked SOURCE_UNAVAILABLE with retrieval evidence, complete per-source inventories where accessible, full licence/security and host dependency assessment, 100% of discovered meaningful capabilities dispositioned with exactly one CPP owner or justified absence.

**Integration done when:** real consumer/routing path verified; isolated + integration + negative-control/evidence-gate tests pass on the appropriate host; seeded faults detected; rollback and permission rules honored; reproducible before/after benchmarks report correctness, false positives, time, token/context and engineering effort with no invented ROI.

**Institutionalization done when:** a validated behavior or method is reachable by future relevant workflows without rediscovery, recorded in existing Knowledge Vault and UKDL where applicable, protected by a named baseline/negative-case check, and demonstrably does not lower existing floors or silently add model residency.

Track at minimum: source-audit coverage (0–6 and capability subdenominator), verifiable claim/quote provenance, reviewer true-positive vs false-positive rate, plan defects escaping implementation, browser journey reachability, funnel finding precision, measurable conversion experiment sample and guardrails, competitor evidence staleness, routing false-wake rate, cost per verified decision, and rework avoided. Explicitly separate NOT_RUN, SOURCE_UNAVAILABLE, FAILED and PASS.

**No global host hooks/config edits, new auto-installing skills, undisclosed autonomous spend, brand copying, unlicensed third-party code or automatic published marketing claims.** Every new reusable capability must earn its activation under the CPP Context-First prompting contract: precise outcomes/invariants/evidence, implementation decisions delegated to repo reality, small bounded proofs, explicit owner gates.

## 10. Closing record

- **Recorded:** 6/6 source requests, including **Percos** as the sole CPP-facing name for source 1.
- **Verified at source level:** Hyperplan single pinned SKILL.md excerpt and directory listing; source revisions disagree in host/model categories.
- **Not verified:** full Percos and four DaltonAI source bodies, current source licences, six-source behavioral efficacy, CPP integration behavior.
- **Not performed:** installations, upstream code copying, CPP module changes, runtime tests, automated learning, deployment, new commands/hooks, skill activation.
- **Next autonomous agent action:** S06-00 + S06-01 reality/source audit, then issue evidence-backed dispositions and targeted execution plan; no invented completion.
