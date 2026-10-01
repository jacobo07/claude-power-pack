# External benchmark: Constitutive Baseline Ratchet (CBR) -- making family baselines work (research started 2026-10-01)
Tiers: A = peer-reviewed / controlled measurement; B = documented large-scale industry practice (named org, published account); C = practitioner opinion / blog.
Access marks: [opened] = page fetched and read; [snippet] = seen only in a search result summary.
Subject: family-classified, immutable generations of requirements, auto-promoted lessons, ratchet (no downgrade), APPLIED / NOT-APPLICABLE done-gate, delivered by context injection into a coding agent, judged by measured "lift".

## 1. Ratchet patterns in code quality

### 1a. Betterer (https://phenomnomnominal.github.io/betterer/docs/introduction) [tier C/B tool docs] [opened]
- Stores a value over time in `.betterer.results`; better -> file updated, worse -> test fails, same -> held. "keeps track of a value as it changes over time."
- Mechanism is per-test snapshot, auto-tightening on improvement. Lowering = editing/regenerating the results file (a human-visible diff, not a blocked action).

### 1b. SonarQube Clean as You Code (https://www.sonarsource.com/blog/clean-as-you-code/ ; docs.sonarsource.com/.../clean-as-you-code) [tier B vendor] [snippet]
- Quality gate judged on NEW code only (new-code period = previous version / N days / specific analysis / reference branch); legacy left alone; claim that overall quality rises incrementally. No published controlled measurement found (vendor claim).
- CBR relevance: a generation raise should judge projects started/changed AFTER it, not retro-fail the estate ("new code period" for baselines).

### 1c. Google deprecation (SWE at Google ch.15, https://abseil.io/resources/swe-book/html/ch15.html) [tier B] [opened]
- Advisory deprecation fails: "hope is not a strategy"; old systems keep a "conceptual (or technical) pull".
- Build-system visibility allowlists stop NEW dependents; entries auto-pruned as teams migrate (ratchet = allowlist that only shrinks).
- Compulsory deprecation needs an owner, a deadline with enforcement, and staffed migration help; unfunded mandates "come across ... as mean spirited".

### 1d. Google static analysis (SWE at Google ch.20, https://abseil.io/resources/swe-book/html/ch20.html; Sadowski et al. CACM 2018) [tier B] [opened ch.20; CACM paper snippet only]
- Check admission criteria: understandable, actionable (fix guidance), <10% effective false positives, significant impact; platform ~5% effective FP across 100+ analyzers.
- "developers ignore compiler warnings" -> each check is either build-breaking or off; no middle "warning" tier.
- "Not useful" button per finding; analyzers with high not-useful rates get fixed or DISABLED. = a demotion path driven by recipient feedback.
- Earlier FindBugs dashboard / batch attempts failed; results delivered at code review ("change mindset") succeeded.

### 1e. Facebook Infer (Distefano et al., "Scaling Static Analyses at Facebook", CACM 2019, https://cacm.acm.org/research/scaling-static-analyses-at-facebook/) [tier A-/B, field measurement] [snippet]
- Same analysis, same FP rate: batch/offline reports ~0% fix rate; diff-time comments in review >70% fix rate. Timing/placement of the requirement dominates its content.
- CBR relevance: injecting a baseline at plan time / at the diff is the analogue of diff-time; a done-time checklist is closer to batch.

### 1f. Ratchet rot in the wild (GitHub issues, 2025-2026; search results) [tier C] [snippet]
- Recurring failure titles: "exemptions never expire: the allow list only grows, and one entry can cover a whole file"; "ratchet is disabled and its baseline has drifted on 54 of 82 entries"; "baseline drifts on any line move, failing unrelated PRs"; "allowlist entry's own explanatory comment can go stale and get copied forward as fact".
- Pattern: a ratchet only detects growth; it does not detect that an entry's justification became false, nor that it has been disabled.

### What makes a ratchet hold vs rot (synthesis)
- Holds: automatic tightening on improvement (betterer), enforcement in the blocking path (build error, not warning), delivery at change time, a named owner, FP rate kept low with a recipient-facing "not useful" channel.
- Rots: exemptions with no expiry; coarse-grained entries (whole file); location-keyed entries that churn; nobody checks that the gate still runs; lowering requires no reason; "improvement" achieved by deleting the measured code (count ratchets reward deletion).

## 2. Golden paths / paved roads / scorecards

### 2a. Spotify Soundcheck / Golden State (https://backstage.spotify.com/discover/blog/how-soundcheck-improves-tech-health-pt-1) [tier B, observational] [opened]
- Structure: Track (long-term initiative, e.g. "Golden State for Web", "Test Certified for Backend") -> Levels (1-3) -> Checks -> Certification. Tracks are per component KIND (web, backend, mobile) = family-scoped standards.
- Governance: checks per level owned by Advisory Boards + Technology Architecture Group (human ownership, not auto-promotion).
- Reported: "Up to 7 more deployments per percentage point gained"; "~25% decrease in high-urgency incidents" at 85% pass; "~1.5 hour faster resolution" per 10-pt pass-rate gain. Caveat: correlational, no control; healthier teams may simply pass more checks (confounding). Vendor-of-own-product.
- Golden Path = onboarding tutorial; Golden Technologies = blessed stack; Golden State = target state. Separates "how to start" from "what done looks like".

### 2b. Google PRR -> frameworks (SRE book ch.32, https://sre.google/sre-book/evolving-sre-engagement-model/) [tier B] [opened]
- Per-service PRR checklist did not scale: "Onboarding each service required two or three SREs and typically lasted two or three quarters"; work reimplemented per service; knowledge stayed local.
- Fix: embed the standard INTO frameworks so new services inherit it by default ("the framework already takes care of correct infrastructure use"). Checklist -> code.
- CBR relevance: the strongest delivery form of a baseline entry is a scaffold/library that makes compliance the default, not a context line asking the agent to remember.

### 2c. Netflix paved road (Netflix tech blog; InfoQ 2018 https://www.infoq.com/news/2018/06/netflix-full-cycle-developers/) [tier B] [snippet]
- Not mandated: "We don't mandate adoption ... but encourage adoption" by making the paved road a far better experience. Security paved road adoption measured by automated control detection across the app inventory (https://netflixtechblog.medium.com/scaling-appsec-at-netflix-6a13d7ab6043).
- CBR relevance: an opt-out-with-reason (NOT-APPLICABLE) model is consistent with this; measurement is of adoption, not outcome.

### 2d. OpsLevel / Cortex scorecards (docs.opslevel.com/docs/checks-and-filters ; docs.cortex.io/improve/initiatives) [tier B vendor docs] [snippet]
- Checks bucketed by Category x Level x Filter; filters by tier/owner/type decide which components a check applies to = applicability is data, not prose.
- Cortex: Levels = ladder (entity reaches level only after passing every rule at and below); "Initiatives" add deadline + owner + notifications because scorecards alone did not move entities ("When scorecards need a deadline").
- CBR relevance: generation = level; applicability = filter; a raise needs an initiative (deadline/owner) to propagate to existing projects, otherwise it only binds new ones.

### 2e. OpenSSF Scorecard outcome evidence (Zahan, Shohan, Harris, Williams, arXiv 2210.14884; IEEE S&P 2023 arXiv 2208.03412) [tier A] [opened abstract]
- Over npm/PyPI packages, "the number of reported vulnerabilities increased rather than reduced as the aggregate security score ... increased"; models explained only R² 9-12%.
- Lesson: a compliance score built from practice checks can be uncorrelated or inversely correlated with the outcome it targets (detection bias, popularity confounding). A CBR "lift" metric must not be the baseline's own compliance rate.

### 2f. AWS Well-Architected / SLSA (aws.amazon.com/architecture/well-architected; slsa.dev) [tier B] [not opened - known from general practice, low weight]
- Well-Architected: pillar questions + "lenses" per workload type (serverless, SaaS, games...) = family overlays over a common core. Reviews are periodic, human-run.
- SLSA: numbered levels, versioned spec (v0.1 -> v1.0 split into tracks); levels are cumulative and checkable via provenance attestations. Example of an externally versioned, immutable-per-version requirement set.

### Synthesis
- Classification is by component kind + tier + owner, expressed as filters. Standards are human-governed. Propagation to existing components needs an explicit initiative with deadline/owner; "raise the bar" alone binds only new components. Outcome evidence is correlational at best, inverse at worst (OpenSSF).

## 3. Templates that propagate updates

### 3a. Copier update (https://copier.readthedocs.io/en/stable/updating/) [tier B tool docs] [opened]
- Stores `.copier-answers.yml` (template version + answers). Update = regenerate old version, diff vs project, apply new version, re-apply diff (3-way), pre/post migrations; versions = git tags compared by PEP 440.
- Conflicts surface as inline markers or `.rej`; "you should review those manually". "Never update `.copier-answers.yml` manually" (provenance file must be truthful or updates go wrong).
- CBR relevance: each project should record WHICH generation it was built/attested against (answers-file analogue), so an upgrade is a diff B_n -> B_n+1, not a full re-audit.

### 3b. Cruft for cookiecutter (https://pypi.org/project/cruft/) [tier C tool docs] [snippet]
- Cookiecutter alone leaves "copy-and-pasted code to manage through the life of your project"; cruft records template commit and offers `cruft check` in CI to fail when a project lags the template.

### 3c. Backstage Software Templates (backstage.io docs; Red Hat 2025 "10 tips" https://developers.redhat.com/articles/2025/03/17/10-tips-better-backstage-software-templates) [tier B/C] [snippet]
- Scaffolder covers CREATE only; no day-2 update path; templates not versioned so "breaking changes can happen without warning"; templates need long-term maintenance or "will undermine their value". Day-1 standard, day-2 drift by design.

### 3d. Renovate shared presets (https://docs.renovatebot.com/config-presets/) [tier B tool docs] [snippet]
- Repos `extends` an org preset (optionally pinned by tag `github>org/repo#v2.0.0`); unpinned -> changes propagate on next run; pinned -> explicit opt-in upgrade. Two propagation modes = "floating" vs "pinned generation".
- CBR relevance: decide per entry whether existing projects float to the new generation (auto-applies) or stay pinned until an explicit upgrade.

### 3e. Clone-and-own (Dubinsky, Rubin, Berger et al., CSMR 2013, https://gsd.uwaterloo.ca/publications/view/512.html) [tier A, exploratory industrial study] [snippet]
- Industrial product lines built by cloning variants; change propagation between clones is manual and becomes a primary maintenance cost. Foundational evidence that "copy at creation" without a link back diverges.

### Evidence gap
- I found NO quantitative empirical study of template drift rates after day 1 (cookiecutter/copier/Backstage). Evidence is tool design + practitioner accounts + clone-and-own literature.

## 4. Fitness functions & ADRs

### 4a. Fitness functions (Ford, Parsons, Kua, Sadalage, "Building Evolutionary Architectures", 2nd ed. 2022, subtitle "Automated Software Governance") [tier B/C book] [snippet via summaries e.g. https://lethain.com/building-evolutionary-architectures/]
- "An architectural fitness function provides an objective integrity assessment of some architectural characteristic(s)."
- Taxonomy: atomic vs holistic; triggered (test, pipeline, lint) vs continual (monitoring); static vs dynamic; automated vs manual; intentional vs emergent. Tools: ArchUnit-style dependency rules.
- Thesis of the 2nd edition = governance by executable checks, not review checklists. A baseline entry with a machine check is a fitness function; one without is a manual fitness function and should be labelled as such.

### 4b. ADR adoption (search result for an MSR study of ~900 GitHub repos; attribution NOT verified) [tier A? unverified] [snippet]
- Claim: ~50% of repos that start ADRs hold fewer than five records -> abandonment after pilot; cost paid now by author, benefit later by maintainers (incentive misalignment). I could not locate the primary paper; treat as unverified.

### 4c. ADR templates compared (arXiv 2604.27333, 2026) [tier A, controlled comparison] [opened]
- Nygard template beat MADR on overall score (p=0.002); "template choice is context-dependent"; more structure = more completeness but more effort.
- CBR relevance: entry schema (id/requirement/why/origin/check) is ADR-like; keep it short or authors stop writing.

### 4d. LLMs checking ADR compliance (arXiv 2602.07609, 980 ADRs / 109 repos) [tier A] [opened abstract]
- LLM judges show "substantial agreement and strong accuracy for explicit, code-inferable decisions"; weak on implicit/deployment decisions needing organizational knowledge.
- CBR relevance: an LLM can serve as the "machine check" only for code-inferable entries; process/deployment entries need a deterministic probe or human attestation.

### 4e. Checks over checklists (Google SRE PRR -> frameworks, see 2b; Google "build error or nothing", see 1d) [tier B]
- Converging industry pattern: move a requirement from (a) review checklist -> (b) automated check in the change path -> (c) default in framework/scaffold. Each step reduces reliance on memory.

## 5. Checklists and their evidence

### 5a. WHO Surgical Safety Checklist pilot (Haynes et al., NEJM 2009, https://www.ncbi.nlm.nih.gov/books/NBK143241/) [tier A, pre/post, 8 hospitals, no concurrent control] [snippet]
- 19-item checklist: complications 11.0% -> 7.0%, in-hospital death 1.5% -> 0.8%. Design = before/after with a study team present (Hawthorne + co-interventions possible).

### 5b. Ontario mandated rollout (Urbach et al., NEJM 2014, https://www.nejm.org/doi/full/10.1056/NEJMsa1308261) [tier A, population-based, 101 hospitals] [snippet]
- After a REGULATOR-MANDATED rollout: adjusted operative mortality 0.71% -> 0.65%, not significant; no reduction in complications, ED visits, readmissions.
- Interpretation in the literature: same instrument, different implementation -> effect vanished. Mandated adoption measured completion, not fidelity.

### 5c. Fidelity vs completion (process evaluations, e.g. PMC5388350; orthopaedic narrative review PMC12801170; reimplementation study PMC10652215) [tier A-/B] [snippet]
- Checklist "may encourage box-ticking without true fidelity"; "often inaccurately documented as complete"; success "depends more on how it is implemented than on the checklist itself"; reimplementation focused on team process restored fidelity.
- CBR relevance: an APPLIED/NOT-APPLICABLE gate is a completion record. Without evidence per APPLIED (a check result, a file, a test) it will converge on box-ticking.

### 5d. Aviation normal checklists (Degani & Wiener, NASA CR-177549, 1990; Human Factors 1993 https://journals.sagepub.com/doi/10.1177/001872089303500209) [tier A field study] [snippet]
- Repetition makes checking "automatic, fast and fluid"; crews reported seeing an item in the wrong state but perceiving the expected state (expectation bias). Design weaknesses (no pointer to current item) matter.
- Read-do vs do-confirm (Gawande, "The Checklist Manifesto", 2009) [tier C]: do-confirm suits experts doing the work from memory, then pausing to confirm a short list of killer items; recommended 5-9 items per pause point. Long lists get skipped.
- CBR relevance: a baseline injected at START is read-do; the done-gate is do-confirm. Do-confirm lists must be short and limited to items that are both easy to miss and costly.

### Synthesis
- Checklists work when short, owned by the team using them, aimed at known killer items, and their completion is verified by an independent signal. They fail when mandated top-down and scored by completion rate (Ontario). Expect the APPLIED rate to approach 100% irrespective of real effect.

## 6. Organizational learning / lessons-learned systems

### 6a. NASA LLIS audit (NASA OIG IG-12-012, 2012, https://oig.nasa.gov/wp-content/uploads/2024/02/IG-12-012.pdf) [tier B, government audit] [snippet + secondary summary opened]
- "NASA program and project managers rarely consult or contribute to LLIS even though they are directed to by NASA requirements."
- Causes: input policy weakened over time; inconsistent policy direction; uneven funding; "Lack of Monitoring". 2005-2010 only JPL contributed consistently (~12/yr; other centers ~1/yr, per Knoco summary http://www.nickmilton.com/2012/07/why-arent-lessons-learned-working-at.html [tier C, opened]).
- Milton: "a lesson is not learned when it is documented, it is learned when something has changed as a result." A pull-based lesson store decays; lessons must be pushed into process/standards.
- CBR relevance: CBR's push-injection directly addresses LLIS's pull failure. The LLIS failure modes it still inherits: monitoring absent, contributions concentrated in one source, nobody checks use.

### 6b. Project lessons survey (Williams, IEEE TEM 55(2) 2008, https://hull-repository.worktribe.com/output/417989/) [tier A survey] [snippet]
- Temporary project organizations and project complexity inhibit learning; surveyed practice shows lessons are captured more than they are transferred. (Details not opened.)

### 6c. Postmortem follow-through (incident.io / practitioner blogs, e.g. https://www.benjamincharity.com/articles/post-mortem-action-accountability/) [tier C] [snippet]
- Commonly repeated claim "fewer than 40% of postmortem action items are completed within 90 days" - NO primary source found; treat as unverified. Consistent qualitative point: "Items that live only in a document almost never see completion"; tracking with owner + deadline is what closes them.
- Google SRE book ch.15 "Postmortem Culture" [tier B, known, not opened this session]: blameless, reviewed, action items tracked as bugs with owners; unreviewed postmortems "might as well never have existed".

### 6d. Auto-promotion without review - agent-memory evidence (Xiong et al., "How Memory Management Impacts LLM Agents", arXiv 2505.16067, 2025) [tier A, controlled] [opened abstract]
- "Experience-following": high input similarity to a stored record -> highly similar outputs. So stored errors propagate ("error propagation"); some successful past runs are still harmful as memories ("misaligned experience replay").
- Quality-gated addition + deletion beats accumulate-everything; "future task evaluations can serve as free quality labels for stored memory".
- CBR relevance (direct): auto-promoting lessons without a quality signal is the measured failure case. Safer: auto-promote as PROVISIONAL, let downstream task outcomes confirm or evict, with Owner review as a second filter.

### Synthesis
- Lesson stores fail by (1) pull-only access, (2) no monitoring of use, (3) no owner, (4) growth without pruning. Auto-promotion fixes capture volume (rarely the bottleneck) and worsens quality control (the actual bottleneck in agent memory studies).

## 7. LLM-agent context injection

### 7a. Context files: success effect (Gloaguen et al., ETH SRI, arXiv 2602.11988, 2026) [tier A] [opened in sibling research [[2026-10-01-sdd-external-research]] C2]
- Context files gave NO improvement in task success (LLM-generated slightly worse), cost >20% more inference; instructions in them ARE followed; repo overviews not helpful. Useful only for non-inferable facts.
- CBR relevance: a baseline entry the agent would do anyway (inferable from family conventions) is cost without lift. Only inject entries that are non-obvious.

### 7b. Context files: efficiency (arXiv 2601.20404, 10 repos / 124 PRs, with vs without AGENTS.md) [tier A-, small] [snippet]
- AGENTS.md associated with median runtime -28.64% and output tokens -16.58%, "comparable task completion". Efficiency gain, not quality gain.

### 7c. Rule evolution in AI IDEs (arXiv 2606.12231; 7,310 rules / 83 projects; 1,540 evolution events; survey n=99) [tier A] [opened abstract]
- Rule updates raised artifact compliance 49.14% -> 72.13% (on 160 assessed events). 77.78% of devs modify rules to correct AI errors; devs "add new negative constraints rather than editing existing ones" -> rule files grow by accretion.
- Devs rate architectural constraints important but files are dominated by low-level workflow/formatting rules.
- CBR relevance: (a) per-lesson rules do raise compliance on the targeted behaviour; (b) accretion is the default dynamic, so a size budget + consolidation step is needed.

### 7d. Proactive rule retrieval (arXiv 2607.26819; 4 frontier models, 106 issues, 49 repos) [tier A] [opened abstract]
- Agents "almost never proactively retrieve the contribution rules"; compliance improved with reminder prompts, rule quotes, verifier feedback; "never refuse to contribute in AI-banned repositories under any condition".
- CBR relevance: pull-based baselines (agent must look them up) fail; push (inject) + verifier feedback works for checkable rules; prohibitions/escalations remain unsolved by prompting.

### 7e. Instruction count vs compliance (IFScale, Jaroslawicz et al., arXiv 2507.11538) [tier A] [opened abstract]
- 20 models, up to 500 simultaneous instructions: best frontier models "only achieve 68% accuracy at the max density of 500"; three degradation patterns; "bias towards earlier instructions" (primacy).
- Lost in the Middle (Liu et al., TACL 2024) [tier A] [known, not opened]: retrieval accuracy U-shaped by position; middle of long contexts under-used.
- CBR relevance: a growing generation degrades per-entry compliance; order entries by severity; cap count.

### 7f. Agent memory and transfer
- Agent Workflow Memory (Wang et al., arXiv 2409.07429) [tier A] [opened abstract]: induced reusable workflows +24.6% relative (Mind2Web), +51.1% (WebArena); cross-task/website/domain gains 8.9-14.0 abs points over baselines. Positive transfer of ABSTRACTED procedures.
- "When Continual Learning Moves to Memory" (arXiv 2604.27003) [tier A] [snippet]: "abstract procedural memories transfer more reliably than detailed trajectories"; negative transfer "disproportionately harms" cases the agent cannot yet solve alone; old/new experiences compete for context at retrieval.
- "How Memory Management Impacts LLM Agents" (arXiv 2505.16067) [tier A] [opened abstract]: experience-following + error propagation; quality-gated add/delete beats accumulation (see 6d).
- Reflexion (Shinn et al., NeurIPS 2023) / Voyager skill library (Wang et al., 2023) [tier A] [known, not opened]: verbal self-reflection and executable skill libraries help within an environment; Voyager stores skills as CODE verified by environment feedback before admission.
- Memory poisoning (MemoryGraft arXiv 2512.16962; arXiv 2601.05504) [tier A] [snippet]: a reuse channel that admits entries automatically is an attack/corruption channel; admission control is the defence.

### Synthesis
- Injection reliably changes behaviour on the targeted rule (7c, 7d) but does not by itself raise overall task success (7a) and costs tokens. Compliance falls with list length and position (7e). Transfer works for abstract, verified procedures and harms hard cases when mismatched (7f). So: few entries, abstract + checkable, ordered by consequence, scoped tightly to the family, and admitted only with a quality signal.

## 8. Classification into families

### 8a. Industry practice: classification as filters, multi-valued (OpsLevel checks-and-filters; Cortex; Backstage catalog `spec.type` + `lifecycle` + tags) [tier B] [snippet]
- Applicability is expressed as filters combining type, tier, owner, lifecycle, language; a component matches every filter it satisfies -> many checks from many "families" apply at once. No exclusive family membership in any tool surveyed.
- AWS Well-Architected lenses (serverless, SaaS, games, IoT...) are overlays applied ON TOP of the common framework; a workload can take several lenses. Spotify tracks are per technology (web/backend/mobile) and a component can be in several.

### 8b. Learned repository classification (Izadi et al., "Topic Recommendation for Software Repositories using Multi-label Classification", arXiv 2010.09116; ~152K repos, 228 topics) [tier A] [snippet]
- Multi-label from README/description/file names: Recall@5 0.890, LRAP 0.805. Shows (a) labels are inherently multi-valued, (b) text-based learned classifiers are good at top-5 ranking, not at a single exact label.
- AutoFL (arXiv 2408.02557) [tier B, tool] [snippet]: multi-granular labelling (file/package/project) - a single repo is heterogeneous internally.

### 8c. Rule-based vs learned - evidence gap
- No study found comparing rule-based (manifest/marker files: `package.json`+framework, `server.properties`, devkitPPC Makefile) vs learned classification for selecting engineering standards. Interpretation: deterministic markers are auditable and give "UNKNOWN" honestly; learned/LLM classifiers give better coverage but need an abstain threshold. Existing tooling universally uses explicit declared metadata (catalog-info.yaml type, tags), i.e. the owner DECLARES the family, tooling validates.

### Synthesis
- Treat family as a SET of labels with per-entry applicability predicates, not a single class. Conflicts between families need an explicit precedence or a "both apply" rule. Declared-and-validated beats inferred-only.

## 9. Measurement of "lift"

### 9a. Perceived vs measured (METR RCT 2025, 16 devs / 246 issues; https://metr.org/research/) [tier A] [snippet]
- Developers forecast +24%, self-reported +20%, measured -19% time (slower) with AI tools; "substantial and persistent gap between perceived and actual performance". METR now labels it historical.
- Lesson: Owner/agent impressions of lift are not evidence; only a controlled measurement is.

### 9b. Enterprise RCT (Google, arXiv 2410.12944, n=96) [tier A] [snippet]
- AI features ~21% faster on an enterprise task, "although the confidence interval is large". Shows RCTs on internal dev tooling are feasible, but n~100 gives wide CIs.

### 9c. Counterfactual designs for platform effects (OneUptime 2026 "attribute DORA metric changes"; platformengineering.org) [tier C] [snippet]
- Difference-in-differences: (after - before for adopters) - (after - before for comparable non-adopters). Confounders listed: service type, team size, change volume, repo migration, concurrent CI/observability work, freezes, workload growth.
- "After" is not "because".

### 9d. DORA (dora.dev, State of DevOps reports) [tier B, survey-based, large n] [known, not opened]
- Four keys (deploy frequency, lead time, change failure rate, time to restore) + reliability; survey + cluster analysis, cross-sectional -> associations, not causal. 2024 report notably found AI adoption associated with slightly lower throughput and stability [recall, not re-verified this session].
- Spotify Soundcheck "lift" numbers (2a) are of this correlational kind.

### 9e. Compliance is not outcome (OpenSSF, 2e; Ontario checklist, 5b) [tier A]
- Two large datasets where higher compliance did not track the outcome. The baseline's own APPLIED rate cannot be the lift metric.

### Synthesis - a feasible lift design for a single-Owner portfolio
- Unit = project (or task). Outcome = defects found after "done" (reopens, hotfix commits, failed done-gates, Owner corrections) per entry's target failure class. Counterfactual = held-out entries (randomly withheld from injection for a fraction of projects in the family) or step-wedge rollout of a new generation. Small n -> report per-entry hit evidence (did the targeted failure recur?) rather than a portfolio-wide percentage.

## 10. Checklist for a CBR-like mechanism
Tier = strongest evidence behind the item. Refs = section ids above.

1. **Versioned, immutable generations; projects record the generation they attest against** (answers-file analogue). [B] 3a, 3d, 2f
2. **Upgrade = diff B_n -> B_n+1**, presented as the delta only, never a full re-audit. [B] 3a
3. **Two propagation modes, chosen per entry: floating (applies to existing projects on next touch) vs pinned (new projects only until explicit upgrade).** [B] 3d, 1b
4. **"New code period" for raises: a new entry judges work started/changed after it lands, not the legacy estate.** [B] 1b
5. **Raising the bar for EXISTING projects needs an initiative: owner + deadline + tracking**; a raise alone binds only new projects. [B] 2d, 1c
6. **Prefer delivery as default (scaffold/library/framework) over delivery as instruction.** Checklist -> check -> default. [B] 2b, 4e
7. **Machine-checkable entries preferred; each entry labelled CHECKED / LLM-JUDGED / MANUAL.** LLM judging only for code-inferable entries. [A/B] 4a, 4d
8. **Enforcement is binary: blocking or off. No advisory tier that accumulates ignored warnings.** [B] 1d
9. **Deliver at plan/diff time, not only at done time** (diff-time fix rate >70% vs ~0% batch). [A-/B] 1e
10. **Context budget: hard cap on injected entries per task; order by consequence (primacy bias); prune before adding.** [A] 7e, 7c
11. **Inject only non-inferable entries**; what the agent does anyway is cost without lift. [A] 7a
12. **Entries are abstract procedures + a check, not raw trajectories or anecdotes.** [A] 7f
13. **Auto-promoted lessons enter as PROVISIONAL with a quality signal** (later task outcomes confirm or evict); never auto-promote straight to binding. [A] 6d, 7f
14. **Admission control on the promotion channel** (provenance verified, not just present) - an auto-admit memory is a corruption/poisoning channel. [A] 7f
15. **Per-entry provenance: repo + commit + incident + date**, and the provenance must be truthful (never hand-edited). [B] 3a, 6c
16. **Per-entry falsifiable "why"; stale-justification detection** (does the origin incident's failure class still exist?). [C] 1f
17. **Expiry / review-by date on every NOT-APPLICABLE waiver and every exemption**; waivers that never expire are the documented rot mode. [C] 1f
18. **Demotion path driven by recipients: a "not useful"/false-positive signal per entry, with a threshold that triggers fix-or-disable.** [B] 1d
19. **Ratchet forbids silent downgrade but permits reasoned demotion** recorded as a new generation with reason + actor. [B] 1d, 1c
20. **Anti-gaming: count ratchets must not reward deletion of the measured subject; key entries by stable identity, not line/location.** [C] 1f
21. **APPLIED requires evidence (check output, file, test id), not a tick.** Completion rates converge to 100% regardless of effect. [A] 5b, 5c
22. **Done-gate list is short (do-confirm, ~5-9 killer items per pause point); the long list belongs to read-do at start or to automation.** [A/C] 5d
23. **Family = set of labels + per-entry applicability predicate**, multi-label by default (SaaS + website both apply). [A/B] 8a, 8b
24. **Explicit conflict rule between families** (precedence or "both apply, stricter wins" - and state when stricter-wins is wrong). [B] 8a (unsourced for the precedence rule itself)
25. **Family is declared and validated, with UNKNOWN as a reachable outcome**, not silently inferred. [B] 8c
26. **Human ownership of each family's standard (advisory board analogue) and a review cadence**; ownerless lesson programs decay (NASA LLIS). [B] 2a, 6a
27. **Use telemetry: record per entry how often it was injected, applied, waived, and failed later** - monitoring absence was a named LLIS failure cause. [B] 6a
28. **Lift is measured against a counterfactual** (withheld entries, step-wedge rollout, or diff-in-diff vs non-adopting projects), never against the baseline's own compliance score. [A] 9a, 9e, 2e
29. **Per-entry outcome metric tied to the failure class the entry targets** (recurrence of the origin failure), because portfolio n is small. [A/C] 9b, 9c
30. **Perception is not lift: neither the Owner's nor the agent's impression counts as evidence of improvement.** [A] 9a
31. **Size growth is monitored; accretion of negative constraints is the default dynamic, so consolidation is a scheduled task.** [A] 7c
32. **Push, not pull: the agent must not be expected to retrieve the baseline itself.** [A/B] 7d, 6a

## 11. Open questions (literature does not answer)
1. No controlled study of "baseline injection into a coding agent" measured across PROJECTS of a family (cross-project transfer of rules, as opposed to cross-task memory within benchmarks).
2. Optimal injected-rule count for coding agents specifically; IFScale measures keyword instructions in report writing, not code constraints with tools/tests in the loop.
3. Whether auto-promotion with LATE human review (CBR's design) beats review-before-promotion; agent-memory papers compare quality-gated vs ungated, not review timing.
4. No quantitative template-drift data (copier/cookiecutter/Backstage) after day 1.
5. How to measure lift at n = a handful of projects per family; RCT designs need n~100 and still give wide CIs.
6. Conflict resolution between overlapping standards (multi-family) - tools apply all matching checks; no published evidence on when "stricter wins" causes harm.
7. Whether NOT-APPLICABLE waivers with reasons drift into rubber-stamping over time in agent-run gates (surgical evidence suggests yes for humans; untested for agents judging themselves).
8. Interaction of baseline generations with model upgrades: an entry that compensates for one model's weakness may be pure cost for the next (7a suggests inferable entries become cost) - no study tracks rule obsolescence across model versions.
9. The ADR "~50% of repos have <5 records" abandonment figure could not be traced to its primary paper.
10. Postmortem "<40% action items completed in 90 days" is widely repeated with no primary source found.

## Source count
~33 sources consulted; opened: betterer docs, SWE@Google ch.15 and ch.20, SRE book ch.32, Soundcheck blog, copier docs, arXiv abs 2210.14884, 2602.07609, 2604.27333, 2606.12231, 2607.26819, 2507.11538, 2409.07429, 2505.16067, Knoco/NASA summary. Rest = search snippets (marked).
