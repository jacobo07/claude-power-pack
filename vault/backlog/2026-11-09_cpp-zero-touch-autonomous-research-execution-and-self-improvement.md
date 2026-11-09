# CPP-ZTA-001 — Zero-Touch Autonomous Research, Execution, Verification & Self-Improvement

**Created:** 2026-11-09 · **Owner intent:** "añádelo absolutamente todo al backlog" after deep GitHub reconnaissance for Claude Code that works, researches, tests hypotheses, corrects bugs, learns and improves without requiring the owner to make routine decisions.
**Status:** BACKLOG / NOT IMPLEMENTED. **Priorities:** P0 unattended execution and proof integrity; P1 autonomous scientific experiments; P2 self-evolution and transfer.
**Owner:** Claude Power Pack existing Goal/Mission Runtime, Cognitive OS, autonomy gate, pp_eval, capability/knowledge runtime, CEPS/UKDL, Constitutive Baseline Ratchet — exact write/read owners must be confirmed at execution time.
**Source basis:** 2026-11-09 conversational research (GitHub-oriented). Repository EXISTENCE of the 17 primary candidates was checked via connected GitHub at capture time. Capabilities and specific compatibility are REPORTED BY UPSTREAM or INSPECTED SELECTIVELY; none were installed or end-to-end tested in this CPP runtime by this backlog operation.
**Authority:** archival backlog entry ONLY. No permission to spend money, run Claude headless, expand token budgets, modify global security/permission policy, deploy or merge/release changes. Existing limits and Owner approvals apply.
**Related CPP backlogs:** 2026-10-11_diagnosing-bugs-causal-proof-ratchet.md; 2026-10-11_tdd-evidence-first-vertical-slice-ratchet.md; 2026-10-11_ruflo-security-absorption-sovereign-updates.md; 2026-07-06_cognitive-os-vdepth-expansion.md. **Related private GSD X epic:** GSDX-ARSI-001 (Atomic Reconstruction & Recursive Scientific Intelligence). Do not copy private Wii/game evidence into this public backlog.

## 0. Mission, non-goals and constitutional constraints

**North star:** Under an explicit durable goal, permission scope, budget and stop policy, Claude Code should autonomously: inspect real state, recover and resume interrupted work, choose ready obligations, investigate knowledge gaps, formulate competing hypotheses, run discriminating experiments, implement reversible solutions, independently verify the real outcome, record causally supported new knowledge, improve its own methods when ROI-positive, and continue to the next admissible task without re-prompting the Owner.

Target **zero routine intervention within preauthorized limits**, NOT impossible unconditional 100% autonomy over credentials, funds, unbounded compute, protected heldouts, security policy, production deployment, irreversible actions, or changes to success criteria. When authorization genuinely ends, preserve progress and continue independent authorized obligations; report the exact blocked boundary without fabricating autonomy.

Existing CPP components already own many responsibilities. The objective is **close observed producer→consumer gaps**, not install multiple full autonomous OS frameworks or generate many unused agents. New implementation starts with REUSE → EXTEND → MERGE → CONNECT → GENERALIZE → CREATE.

Hard non-negotiables:
- One source of mission truth; never introduce parallel schedulers/ledgers that silently diverge.
- Independent test and certification authority; no self-acquittal; no change to the judge just to pass.
- Event-driven wait/restart and progress-based stop; NO infinite self-prompt loop.
- Bounded cost, context, concurrency, retries, paid-provider and wall-time limits.
- Proven permission boundary that cannot be bypassed by modifying a prompt.
- Genuine production-reality demonstration before DONE.
- Experimental metrics must be valid; cost saved and autonomous success are measured, never promised.
- Owner can inspect, interrupt, revoke, or override authorized automation at any time.
- Knowledge is versioned, provenance-bound, scoped, revocable, and consumed by future real work.

## 1. Existing CPP ownership — confirm reachability, not existence only

Observed module owners in CPP main at 2026-11-09:
1. **modules/gsd_x/mission/contract.py / obligation.py / closure.py / store.py** — mission intent, derived obligations and evidence-governed closure; GSD planning remains phase owner.
2. **modules/cognitive_os/loop_budget.py / scheduler.py / process_governor.py / hibernation.py / rehydration.py** — bounded loops, concurrency, processes, context budgets and recovery. The loop-budget code requires max iterations, checkpoints, stop gates, kill switch and resume plan. Its documented admission is not proof every runtime path actually enforces it.
3. **modules/autonomy_gate/gate.py** — agent-vs-Owner decision boundary; defaults to fail-closed for authority. Must be exercised at the ACTUAL action boundary.
4. **modules/pp_eval/runner.py / nightly.py / verdict.py / floor.py** — independent runs in worktrees, hidden tests, nighttime scheduling, compare and admission.
5. **modules/decision_review/proactive_scanner.py / decision_kernel.py** — evidence-backed proactive decision suggestions and reversibility.
6. **modules/one_shot/compiler.py** — frozen per-task scope, budget and done gate.
7. **modules/capability_runtime/** — applicability, agent resolution, invocation, telemetry and retirement.
8. **modules/agent-lightning/query_lightning.py** — client querying existing optimization/tracing results; DO NOT infer installed training infrastructure from its presence.
9. **modules/autoresearch/** — existing autoresearch/media acquisition capability; DO NOT conflate it with Karpathy's separate ML experiment program.
10. **modules/universal-meta-systems/runtime**, **modules/pp_agents**, existing Knowledge Vault, UKDL, CEPS, UCR-CIF and Constitutive Baseline Ratchet — assess actual consumers and institutional owners before extension.

Critical rule: check read/write authority, source identity, runtime entry point, tests, host activation and real consumer. An existing source file is not necessarily an activated capability.

## 2. External resource inventory — all candidates preserved for selective disposition

All 17 repo roots below were checked as existing at capture time. Upstream functionality claims are **discovery evidence**, not measured CPP compatibility. Classify each as REUSE IDEA / EXPERIMENTAL ADAPTER / NO-INSTALL / CONFLICT / LICENSE_REVIEW / REJECTED after follow-up investigation.

| ID | GitHub source | Useful capability / idea | Proposed CPP disposition |
|---|---|---|---|
| EXT-01 | https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep | ARIS: idea discovery, literature/novelty checks, experiment planning/bridge/queue/monitoring, ablation, paper claims, cross-model adversarial review, use-log-guided meta-optimization | **P0/P1 selective research workflow absorption**; never install entire harness blindly |
| EXT-02 | https://github.com/karpathy/autoresearch | Fixed-time experiments; unmodifiable objective evaluator; keep/discard; experimental branch and result ledger; simplicity tradeoffs | **P0 experimental protocol pattern**; not an assertion CPP must train a neural network |
| EXT-03 | https://github.com/anthropics/claude-code-action | Scheduled/event-driven GitHub-triggered Claude Code execution | **P0 autonomous external trigger pilot** with permissions, secrets, PR boundaries and bill limits |
| EXT-04 | https://github.com/WecoAI/aideml | AIDE ML: tree search through implementations/experiments, execution feedback, branches and scoring | **P1 measured strategy-tree prototype**, not a second scheduler |
| EXT-05 | https://github.com/Margin-Lab/evals | Cross-agent task isolation, reproducible traces, runtime and token/cost comparisons | **P1 compare with pp_eval**, absorb only missing instrumentation/evaluator contracts |
| EXT-06 | https://github.com/frankbria/ralph-claude-code | Loop continuation, persisted state, circuit breaker for stagnation/errors/permission denials, budgets, cooldowns | **P0 circuit-breaker audit** against cognitive_os/liveness; do not duplicate mission loop |
| EXT-07 | https://github.com/Nokodoko/overstory | Multi-agent coordinator, workers, isolation, liveness/watchdog and integration | **P1 inspect supervisor recovery patterns**; avoid replacing GSD runtime |
| EXT-08 | https://github.com/obra/superpowers | Systematic debugging, test-first discipline, verification-before-completion | **P1 selective methods** via existing QA/CPP debugging owners |
| EXT-09 | https://github.com/gastownhall/beads | Durable task graphs, dependencies, ready-work selection, progress persisted across sessions | **P2 adapt only if missing mission obligation capabilities**, no dual task source-of-truth |
| EXT-10 | https://github.com/microsoft/agent-lightning | Agent trajectories, rollouts, optimization/training infrastructure | **P2 training/optimization feasibility**, not ability to mutate hosted Claude weights |
| EXT-11 | https://github.com/SakanaAI/AI-Scientist-v2 | Agentic idea/hypothesis generation and experiment trees, research review/workflow | **P2 scientific methods**; license, infrastructure and scope review before code reuse |
| EXT-12 | https://github.com/SWE-agent/mini-swe-agent | Small, auditable SWE agent implementation and strong simplicity baseline | **P1 benchmark baseline**, not another main runtime |
| EXT-13 | https://github.com/dsifry/metaswarm | Parallel research, planning, review, learning and implementation coordination | **P2 reference mechanisms**; no full-stack import without proven gap |
| EXT-14 | https://github.com/gastownhall/gastown | Durable multi-agent workspaces, supervisor/processes, queue, role and coordination patterns | **NO INSTALL by default** due high overlapping orchestration authority; study isolated ownership/recovery ideas |
| EXT-15 | https://github.com/ruvnet/ruflo | Broad swarm/memory/tool-routing and agent automation surface | **NO INSTALL by default**; existing CPP dedicated Ruflo security absorption backlog governs any intake |
| EXT-16 | https://github.com/midego1/claude-orchestrate | Complexity-based delegation, verification, bounded retries and agent composition | **P2 selective agent-team routing** against current CPP routing |
| EXT-17 | https://github.com/OpenHands/openhands | Agent runtime and local/remote/sandbox operation patterns | **NO INSTALL by default**; selectively assess remote persistence and audit |
| EXT-18 | https://github.com/anthropics/claude-code | Official Claude Code reference and Ralph-Wiggum-style Stop hook / code review plugin concepts | **P0 confirm current official paths/availability before direct integration**, do not depend on stale plugin paths |
| EXT-19 | https://github.com/anthropics/claude-code-security-review | Security review workflows; upstream itself has prompt-injection caveats for untrusted contributions | **P1 complementary security test**, sandbox and trusted-input assessment required |

EXT-18/19 were discussed in the research even though the 17-primary-repo verification set focused on the others; verify paths, current version and license separately. All integration proposals must document licensed code adaptation vs pattern-only absorption.

### ARIS internal components worth inspecting as INDIVIDUAL contracts

- idea-discovery, idea-creator, novelty-check, arxiv/openalex/literature search: evidence discovery.
- experiment-plan, experiment-bridge, experiment-queue, monitor-experiment, experiment-audit: pre-registered plans → implementation → actual runs → falsification.
- ablation-planner, analyze-results, integrity-forensics, claims-drafting, citation-audit: causal attribution and no phantom/normalized-to-self results.
- auto-review-loop, reviewer independence and cross-model review: independent critique and bounded fix loops.
- meta-optimize, meta-apply, trigger_eval.py: use-log-driven improvement of skills and scientific harness.
- context compression and durable experiment tracker: recovery without full transcript reload.

**Important verified privilege boundary:** ARIS meta-optimize is a read-only proposal producer. Meta-apply is a SEPARATE human-invoked privileged landing command with fresh external review, and ARIS explicitly notes gaps in a blacklist-only corpus-write guard. This is NOT zero-human self-modification today; preserve it as a design lesson. ARIS auto-review-loop explicitly forbids wrapping itself with external periodic verdict loops; schedule the external condition (experiment completion), not periodic re-judging of the same evidence.

## 3. Atomic backlog — P0 external activation and continuity [ZTA-L]

- **ZTA-L00 / Reality scan.** Reconcile live host, active worktrees/writers, permissions, tokens, scheduler, actual Claude Code CLI version and connectors. Map complete entrypoint→process→receipt ownership. Do not infer running capability from README.
- **ZTA-L01 / Durable preauthorized mission contract.** Explicit goal, constraints, allowed action classes, max paid spend, tokens, concurrency, wall time, stop conditions, required reviewer and owner-granted permissions. Reuse Mission Contract/OneShot; do not create a second ledger.
- **ZTA-L02 / External trigger.** Test GitHub-Action-driven event/scheduled execution versus existing daemon/scheduler for desired platforms. Avoid storing high-privilege keys in prompt or making untrusted PR instructions authoritative.
- **ZTA-L03 / External liveness supervisor.** Verify genuine process-death detection, restart/re-entry, lease ownership, heartbeat, sentinel/PID logic, no orphan descendants and no duplicate writers; external process required, a Stop hook alone cannot recover a dead process.
- **ZTA-L04 / Task DAG and ready selection.** Select next approved obligation only when predecessor postconditions are independently proven; implement blocked/unknown/rejected handling without mechanically advancing a phase. Avoid adding Beads as second source of truth.
- **ZTA-L05 / Crash/context recovery.** Replay persistent mission identity and no-user-prompt resumption after hard kill, host restart, context compaction and provider interruptions. Fresh worker must recover at most once and not duplicate side effects.
- **ZTA-L06 / Circuit breaker.** Compare Ralph's repeated-error, no-progress, permission-denial, exhausted-budget, cooldown and half-open recovery to CPP CO-09; extend enforcement where real gaps exist; mutation-test termination.
- **ZTA-L07 / Loop economics.** Enforce real maximum iterations, token/time/CPU/memory/API cost and stop gates at actual launch boundaries; no unbounded loops or token-free CPU burn.
- **ZTA-L08 / Session and repo writer leases.** Single active writer per overlapping owner; worktree isolation, no resurrection of disposed work, stale lease recovery, idempotent jobs.
- **ZTA-L09 / Blocked-work rerouting.** If Owner-only permission is required, record exact boundary, keep researching unrelated authorized obligations and notify once with concise evidence; no authority escalation.
- **ZTA-L10 / Provider and network resilience.** Distinguish 401, 403, provider quota, transient network, crash, malformed output and true methodological failure; instrument retries/abstention and never hide cost.
- **ZTA-L11 / Autonomy boundary red-team.** Try unauthorized external push/deploy/spend, secret read/exfil, destructive change, self-approval and prompt-injection from issues/PRs; must refuse despite the agent's own interpretation of mission priority.

## 4. Atomic backlog — P0/P1 autonomous scientific method [ZTA-R]

- **ZTA-R01 / Evidence research.** Discover web/repo/docs sources on demand with provenance, dates, repository identity, copyright/licensing checks, alternate evidence and source freshness. No hallucinated results.
- **ZTA-R02 / Missing-knowledge detection.** Convert task failure, unexplained residual, method plateau, compiler mismatch or tooling gap into bounded, falsifiable hypotheses and an information-request contract.
- **ZTA-R03 / Competing hypothesis protocol.** Record predicted outcomes under each explanation, discriminating experiment, cost, instrumentation risk and clear ABSTAIN conditions.
- **ZTA-R04 / Pre-registered experiment planning.** Freeze goal, metrics, controls, cohort, heldout leakage rules, baseline and stop rules before trying variants. Use scientific workflow proven by actual executions.
- **ZTA-R05 / Experiment bridge.** From approved research contract: implement experiment, isolate environment, sanity first, run real tools, gather results, append durable receipt, classify instrument failure separately.
- **ZTA-R06 / Result integrity audit.** Falsify fake ground truth, self-normalized scores, phantom outputs, inapplicable benchmarks, tiny pilots presented as global claims and incorrect evaluation scripts. Independent reviewer cannot change evaluator.
- **ZTA-R07 / Ablation and causal attribution.** Test whether improvement is attributable to actual new component versus baseline, changed cohort, different model, hidden data, toolchain or stochastic variation.
- **ZTA-R08 / Strategy-tree research.** Evaluate AIDE-like branching on hypothesis/method/representation with stateful negative results. Baseline comparison against a single-worker deterministic workflow; no unbounded agent explosion.
- **ZTA-R09 / Active experiment choice.** Select cheapest sufficiently discriminating experiment, not most elaborate research report; track question-value realized.
- **ZTA-R10 / Reviewer independence.** Compare cross-model critique, fresh contexts, objective unit/integration tests and independent oracles. An external LLM opinion is not a substitute for tests.
- **ZTA-R11 / Research wait events.** Await experiment completion, model response or external state via dedicated observer; audit only upon new evidence. No periodic re-review that adds zero information.
- **ZTA-R12 / Research reproduction.** Replay experiment after context loss and on a fresh worktree; record env, SHA, cost, inputs and tools.
- **ZTA-R13 / Original-path verification.** An implemented hypothesis must reach actual runtime/product/CLI boundary; mock- or report-only results cannot mark the mission complete.

## 5. Atomic backlog — P1 independent evaluation and comparison [ZTA-Q]

- **ZTA-Q01 / pp_eval vs Margin Eval gap study.** Compare isolation, task corpus, hidden tests, model/arm identities, trace exports, stable reproduction, full cost and regression proof. Integrate missing capability via existing pp_eval.
- **ZTA-Q02 / Minimal-agent control.** Run mini-SWE-agent or equivalent low-complexity baseline versus CPP on same frozen task set. If complexity doesn't improve result, remove/avoid it.
- **ZTA-Q03 / Champion-challenger experiments.** Use autoresearch discipline: fixed method/evaluator, bounded variants, keep/discard, full cost, complexity penalty and immutable baseline; never tune the judge to achieve progress.
- **ZTA-Q04 / Multi-seed and selection bias.** Repeat comparisons where stochastic variance is material, isolate task leakage, preserve all negative samples and report confidence appropriately.
- **ZTA-Q05 / Security/integrity verification.** Include code review, SAST or domain-appropriate oracle where applicable; benchmark security-review tools on actual vulnerabilities and adversarial PR text.
- **ZTA-Q06 / Completion boundary.** Integrate GSD Mission closure, V-gate, Production Reality, cross-surface tests and durable side effects. No completed summary without executed evidence.
- **ZTA-Q07 / Evaluation independence.** Proposed optimization cannot edit evaluation corpus, hidden tests, verifier binaries, identity pins or rubric; judge changes use separately authorized review.

## 6. Atomic backlog — P1/P2 agent and method self-improvement [ZTA-M]

- **ZTA-M01 / Use telemetry.** Track actual invocation of skills, reasoner route, tools, errors, capabilities, costs, outcome and downstream consumers. Safe redact and avoid blanket transcript duplication.
- **ZTA-M02 / Trigger evaluation.** Use ARIS trigger_eval methodology: paraphrased positive/negative prompts in neutral CWD, confusion/miss matrices and no-side-effect probe; don't score a skill as used because file exists.
- **ZTA-M03 / Harness meta-optimization.** Propose improvements to skill descriptions, prompts, model routing, default params, tools, team policy and experiments based on observed bottlenecks. Preserve before/after tests and rollout plan.
- **ZTA-M04 / Separate proposal and landing.** Independent staging, review and privileged apply. Never let proposer write a forged PASS that the applier trusts. Start human-gated for sensitive changes.
- **ZTA-M05 / Safe automatic promotion tier.** Investigate Owner-authorized automatic landing ONLY for reversible, low-blast-radius changes with independent evaluator, branch isolation, scoped tests, rollback and maximum cost. Certifiers, security policies, permissions, payouts, production release and benchmarks stay Owner/separate-authority gated.
- **ZTA-M06 / Strategy Genome & method archive.** Reuse CPP Strategy Genome, MethodGraph and capability lifecycle; retain per-task specialist variants instead of one constantly mutating best algorithm.
- **ZTA-M07 / Agent Lightning feasibility.** Capture trajectories with valid rewards and independent labels; evaluate candidate policy/model training only when actual trainable model, data, infrastructure and full economics exist. Hosted Claude model weights are not implicitly trainable.
- **ZTA-M08 / Meta-method evaluation.** Measure whether the way the system discovers improvements itself is better (more valid improvements, fewer false winners, lower total cost), not just that it writes more meta-analysis.
- **ZTA-M09 / Capability retirement.** Detect redundant or economically inferior tools; archive evidence and narrow/retire applicability without losing older proven results.
- **ZTA-M10 / Cross-project transfer.** Reuse only validated generic workflows across Wii reconstruction, regular SWE, infrastructure, frontend/CLI integration or other authorized tasks; never promote an instance-specific workaround as universal.
- **ZTA-M11 / Escalation and emergency stop.** Preserve a human override and explicit, revocable authorities. Agents cannot expand their own autonomy or budgets.
- **ZTA-M12 / Institutional ratchet.** Candidate method → independent outcome evidence → legitimate applicability → fresh-agent consumer → Knowledge Vault/UKDL (Hard Rules, Process Rules, Traps) → CEPS/UCR-CIF/Constitutive Baseline Ratchet promotion with regression and invalidation.

## 7. Atomic backlog — real proof experiments / first value [ZTA-X]

**X00. Preflight ownership and permissions.** Tool and resource availability, CWD/branch and current contract; no side effects. Proof: owner map and gap list.

**X01. External-survival proof (P0):** A durable task starts under approved automation, worker process is deliberately killed, real supervisor detects exit, recovers a new session, reads persisted task state and finishes once, without duplicate effects or user instructions. Negative mutants: no heartbeat, stale pid, orphan stdout, double worker, expired token, revoked permission. Passing only a Stop hook is FAIL.

**X02. Headless dependency graph proof (P0):** Task B is blocked by proof obligation A, agent may work task C while A is blocked but never claim B done or change the goal. Simulate provider/auth failures, exhausted budget and owner intervention.

**X03. Scientific autonomy proof (P0/P1):** Given competing hypotheses with a real oracle, agent selects a discriminating test, updates evidence and changes method. Compare same frozen task with CPP current policy and a baseline, recording full resource spend and false conclusions.

**X04. Autoresearch champion/challenger proof (P0/P1):** A fixed objective and immutable evaluator compare reversible candidate changes; keep/discard must correspond to real measurement. Mutation tests attempt score normalization fraud and evaluator edits.

**X05. Research review independence proof (P1):** One executor proposes result, independent verifier finds purposely planted fake truth / phantom result / undersized scope; evaluator refuses the report. Re-review only when artifact changes.

**X06. Strategy-tree comparative proof (P1):** AIDE-like branching vs linear current workflow on same frozen hypotheses and budget; measure successful discrimination/certificates/bug fixes and total cost.

**X07. Meta-optimize proof (P1/P2):** Real observed skill misses trigger proposed changes; stage change, independent evaluation, separate authority for landing; in authorized low-risk tier show retained future task success. No full skill rewrite without proof.

**X08. Multi-agent cost proof (P1/P2):** Single agent vs bounded team vs external supervisor coordination. Compare time, tokens, quality, interference, overlaps and recovery; reduce swarm where it loses.

**X09. Fresh-agent continuation proof (P0/P1):** Cold agent consumes only mission/knowledge artifacts, chooses correct next work and avoids a known bad method without prompts or chat history.

**X10. Institutional transfer proof (P2):** A method learned on one repo causes independently verified improvement on a different applicable repo without exposing private evidence; negative transfer narrows applicability.

**X11. Authorization red-team (P0):** Agent tries to trick gates into issuing new permissions, altering rubric, deploying, paying, unlocking secrets, changing hidden tests or exceeding budget. Must fail closed at real boundary.

**X12. Failure economics (P1):** Compare full observed cost of unattended operation including supervision, retries, context, CI, model, CPU, machine idling and human interventions to baseline. Do not count only API prices or only successful runs.

## 8. Prioritized release tranches and dependency gates

**Tranche A — P0, autonomy that really survives:** ZTA-L00–L11 + X01/X02/X11. Existing mission authority, global control, liveness, process resurrection, budget law, interruption and blocked-work continuation. Do not add AIDE/ARIS on top of unreliable recovery.

**Tranche B — P0/P1, science that checks hypotheses:** ZTA-R01–R07, R09–R13; ZTA-Q01–Q07 and X03–X05. Reuse pp_eval; integrate ARIS experiment contracts and autoresearch immutable evaluator. Require one real independent scientific decision advantage before scale.

**Tranche C — P1, strategic experimentation:** ZTA-R08, ZTA-M06, X06/X08. Only if branching beats simple linear/pure baseline on measured cost and success.

**Tranche D — P1/P2, improve own methods:** ZTA-M01–M05, M08–M12; X07/X09/X10. First propose/stage/review, then limited authorized autonomous promotion for low-risk classes; never unreviewed judge/security evolution.

**Tranche E — P2, model training:** ZTA-M07 and optional Agent Lightning trial. Only when infrastructure, trainability and reward oracle are independently demonstrated.

No tranche implies automatic authority for the next; use explicit goal, approved budgets and real done gates. Execution mode for clear fixes, plan for coupled work, ultra-plan only for fundamental architecture/authority decisions; /cpp-gsd-long/UWCP only if existing mechanism is activated and needed.

## 9. Anti-duplication and integration-decision matrix

- **Gas Town / Overstory / OpenHands / MetaSwarm / Ruflo:** do not adopt as new command center. Study atomic liveness, worktree, supervisor, operator and communication patterns; compare under isolated benchmark before replacing any owner.
- **Beads:** mission obligations already support durable structured state. Prefer an adapter or no action; reject a second canonical task DAG.
- **Ralph / Ralph Wiggum:** loop is helpful but NOT a resilient external monitor. Compare with current CO-09 and existing GSD continuation. Never authorize infinite stop-hook prompts.
- **ARIS:** strongest hypothesis/audit workflow opportunity; meta-apply remains human-gated upstream. No false claim of autonomous self-update, no relaxing proposed/landing separation.
- **Karpathy autoresearch:** best minimalist controlled experiment principle, not a general agent OS and not necessarily relevant to every task.
- **AIDE / AI Scientist v2:** optional experiment/strategy search; keep a minimal single-agent and deterministic baseline. Inspect licenses/compute requirements first.
- **Margin Eval:** improve pp_eval rather than duplicating isolated-run/evidence stores.
- **Agent Lightning:** only candidate training/policy optimization with real trainable models and data; do not promise automatic Claude weight updates.
- **Superpowers / security review:** absorb only test/verification routines not already covered by CPP's verified completion and diagnostic standards.
- **Claude Code Action:** deployment/event activation sits outside CPP's mission truth. GitHub permissions must remain explicit; untrusted issue text is data, not privileged instructions.

## 10. Completion and ongoing governance

Each atomic task must have a proven producer/consumer seam, actual host or runtime boundary, independent evidence and cost. NO feature marked done because a file/skill/hook/plugin exists. Production Reality Gate mandatory per applicable completed unit. All errors found in work, whether specified or discovered, require root cause + regression proof + Knowledge Vault + UKDL scope-level assessment. Constitutive Baseline Ratchet promotion ONLY after verified use and transfer, with independent rollback/invalidation.

**Handoff** on actual execution must include: PANE, HOST, SESSION, MISSION, MODE, branch and HEAD, active owners, current task, actual executable test and verdict, resource/token budgets and used amounts, commit receipts, DONE/BLOCKED, next pane and next action. Backlog state alone must never be represented as running unattended work.

**Primary success measures:** percentage of approved tasks completed without routine Owner turns; correct recovery from process failure; false-DONE/false-PASS incidence; independent valid-result rate; research hypothesis discriminations per full cost; ROI of auto-improvement; transfer to novel tasks; violations of authority (must remain zero). Measure distribution by task class, not ungrounded universal "100% autonomy."

**Final law:** An autonomous agent that works endlessly is not useful. An agent that works without supervision, knows when to test or pivot, reports when it is blocked by genuine authority, preserves the truth of its evidence, and makes future work measurably cheaper is the goal.
