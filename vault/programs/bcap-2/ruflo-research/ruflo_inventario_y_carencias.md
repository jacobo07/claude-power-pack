# Ruflo (ruvnet/ruflo, formerly claude-flow): current capability inventory and gaps, as of 2026-11-19

Method: read-only. Started from the local audit `vault/backlog/2026-10-11_ruflo-security-absorption-sovereign-updates.md` (whose evidence ends at v3.57.0 / 2026-10-19), then updated it with GitHub releases, npm registry metadata, issues, discussions, advisories, changelog and independent reviews fetched on 2026-11-19. About 25 web fetches and searches. Nothing was installed or run.
Labels: **VERIFIED-IND** means confirmed by an independent party through code or a runtime test. **VERIFIED-SELF** means the project's own audit, test or release note says it works and no one outside has reproduced it. **CLAIMED** means it appears only in the README or marketing. **REFUTED** means an audit, the project's own or an independent one, found it false. **UNKNOWN** means no evidence either way.

## Q1. What is the latest version, what are its headline features, and which of them verifiably work?

### Takeaway
The latest release is **v3.78.0, published 2026-11-19**. It is the 10th release in 9 days, and the release index runs to 100 pages. The headline surface is very large: about 100 agents, 406 MCP tools, 48 plugins, swarms with consensus, AgentDB/HNSW memory, SONA learning and federation. Independent code-level evidence shows only a small working core: memory store/search, embeddings, terminal execution, session save, a persisted confidence-and-routing feedback loop, and a cron-style worker. Most of the multipliers and the "intelligence" claims have been refuted, including by the project's own audits, or remain unverified. No task-level outcome benchmark (SWE-bench or similar) exists.

### Cited Findings
**Version and release facts**
- Latest release v3.78.0, 19 Nov 2026, "security batch + dream-cycle neural/memory fixes". Earlier releases: v3.77.2 (17 Nov), 3.77.1 (13 Nov), 3.77.0 and 3.76.1 (12 Nov), 3.76.0 (11 Nov), and 3.75.0 to 3.75.3 (all on 10 Nov). The release index has 100 pages. — [Releases](https://github.com/ruvnet/ruflo/releases)
- The v3.78.0 tag commit is `337c8981e6196f74ea72abc990f0b76a686764d0` and carries a GitHub-verified signature. The release published `@claude-flow/cli`, `claude-flow` and `ruflo` 3.78.0, plus `@claude-flow/mcp` 3.1.8 and `@claude-flow/security` 3.0.8. The release notes list their own known issue: **`@claude-flow/swarm` was not republished, so the swarm consensus listener fix #4989 "has no effect in the installed CLI"**. They also say some leaf packages were published before their version pins merged. — [v3.78.0](https://github.com/ruvnet/ruflo/releases/tag/v3.78.0)
- npm `ruflo@3.78.0` is now a thin wrapper: 3 files, 47,148 bytes, one runtime dependency (`@claude-flow/cli` 3.78.0), Node >=20. It ships registry ECDSA signatures but **no provenance attestation**. Its `overrides` pin `better-sqlite3` 12.9.0, `agentdb` and `ruvector`. — [npm registry ruflo/latest](https://registry.npmjs.org/ruflo/latest). v3.75.2 (10 Nov) cut the package from 531 files to 3. — [Releases](https://github.com/ruvnet/ruflo/releases)
- Repo stats on 2026-11-19: 82.1k stars, 9.7k forks, 10,531 commits, MIT licence, 289 open issues, 270 open PRs, 1,938 closed issues. — [README](https://github.com/ruvnet/ruflo); [closed issues](https://github.com/ruvnet/ruflo/issues?q=is%3Aissue+is%3Aclosed+sort%3Aupdated-desc)
- CHANGELOG.md tops out at 3.71.0 (2026-11-01). Releases 3.72 to 3.78 have no changelog entries. — [CHANGELOG](https://raw.githubusercontent.com/ruvnet/ruflo/main/CHANGELOG.md)
- The repo moved from ruvnet/claude-flow to ruvnet/ruflo around v3.5 (February 2026). Both npm names are still published. — [rywalker.com](https://rywalker.com/research/claude-flow); [v3.78.0](https://github.com/ruvnet/ruflo/releases/tag/v3.78.0)

**Headline claims as they appear in the README (2026-11-19), with the evidence for each**

| Capability | README claim | Evidence status | Lifecycle stage |
|---|---|---|---|
| Agent catalogue | "100+ specialized agents", while the install table says "98 agents" | CLAIMED. The numbers are internally inconsistent. Agents are mostly Markdown definitions. #4087 (Oct) reported that SPARC references agents that do not ship. #607 "analyst agent never detected" is still open. — [README](https://github.com/ruvnet/ruflo); [#4775](https://github.com/ruvnet/ruflo/issues/4775) | coordination |
| MCP tools | 406 MCP tools and 61 CLI commands (314 tools and 26 commands on 2026-10-15) | Mostly REFUTED in April 2026: about 10 of 300+ tools were real (~3%) and ~290 were stubs, on v3.5.51. — [Discussion #1513](https://github.com/ruvnet/ruflo/discussions/1513). The project's own May 2026 audit put about 195 of 240 in the "real code" column (secondary report). — [search summary citing explainx/andrew.ooo](https://andrew.ooo/posts/ruflo-review-agent-harness-claude-code-codex/). v3.5.59 replaced hardcoded responses in 19 tools (maintainer). Tracker #4775 (Nov) lists untested autopilot_\*, transfer_\*, browser_\* and metaharness_\* tools. Current share of working tools: UNKNOWN. | all |
| `agent_spawn` / swarm execution | Swarms with hierarchical, mesh and adaptive topologies | REFUTED as execution: `agent_spawn` "only records state" (maintainer, Nov 2026). `agent_execute` makes a real model call (VERIFIED-SELF). — [#1513](https://github.com/ruvnet/ruflo/discussions/1513). #4726: swarm_shutdown leaves members running and swarm_status miscounts. #4727: hive-mind maxAgents is never enforced. — [#4775](https://github.com/ruvnet/ruflo/issues/4775) | coordination |
| Consensus | "Queen-led hierarchy (Raft, Byzantine, Gossip)" | REFUTED in April 2026: all five protocols routed to one JSON handler and `verifySignature()` always returned true. — [#1513](https://github.com/ruvnet/ruflo/discussions/1513). In Aug 2025 the maintainer admitted Byzantine consensus and signing were simulated. — [#640](https://github.com/ruvnet/ruflo/issues/640). Later Raft vote fixes shipped in 3.75.3, but the swarm package is not republished in 3.78.0. Status: UNKNOWN to partly inert. | coordination |
| HNSW / AgentDB memory | Now "~1.9x faster at N=20k, ~3.2-4.7x at N=5k vs brute force, recall@10 ~0.99; ties/loses at small N". Earlier claim: "150x-12,500x". | The old multiplier is REFUTED: the self-audit measured 1.48x at peak, slower below ~5k vectors. — [andrew.ooo](https://andrew.ooo/posts/ruflo-review-agent-harness-claude-code-codex/). The current README numbers are VERIFIED-SELF. The basic memory store/search works (VERIFIED-IND, Apr). — [#1513](https://github.com/ruvnet/ruflo/discussions/1513) | codebase context |
| SONA / ReasoningBank / neural learning | Self-learning neural patterns and trajectory learning, with no numbers | Partly VERIFIED-SELF: confidence moved 0.906 to 1.0 on success and down to 0.952 on failure, persisted, and routing feedback changed the next route. REFUTED parts: Flash Attention speedup "fabricated at runtime" with `Math.random()`; ONNX failure fell back silently to mock embeddings still labelled real; `route feedback -r -1.0` was parsed as +1.0. — [andrew.ooo](https://andrew.ooo/posts/ruflo-review-agent-harness-claude-code-codex/). In April, `neural_train` reported 93.6% on 5 samples while always predicting "coder". — [#1513](https://github.com/ruvnet/ruflo/discussions/1513). SONA persistence (#4080) and EWC wiring were closed 19 Nov 2026 via #5041. #5011 (open, 17 Nov): `ReasoningBank.distill()` discards failed trajectories. — [closed issues](https://github.com/ruvnet/ruflo/issues?q=is%3Aissue+is%3Aclosed+sort%3Aupdated-desc); [open issues](https://github.com/ruvnet/ruflo/issues?q=is%3Aissue+is%3Aopen+sort%3Acreated-desc) | cost/routing, maintenance |
| Routing | "Intelligent routing (89% accuracy)". 3.76.0 adds an opt-in nearest-centroid router; 3.77.0 adds opt-in model-judge routing. | CLAIMED, with no independent evaluation. — [explainx](https://explainx.ai/blog/ruflo-ruvnet-claude-flow-meta-harness-swarms-memory-federation-claims-vs-readme-2026); [Releases](https://github.com/ruvnet/ruflo/releases) | cost/tokens |
| Token savings | No longer a headline figure on the README | REFUTED in April: ReasoningBank "-32%" used a hardcoded baseline of 1000; Agent Booster "352x" was measured against `sleep(352)`; there was no token counting. The maintainer now calls those percentages "unverified". — [#1513](https://github.com/ruvnet/ruflo/discussions/1513). 3.71.0 `contextDelegation`: 6/6 correct, cost down 22.5%, described by the project as "samples, not a statistical result". 3.70.0 "deterministic protocol evidence, not a live cost or quality result". — [CHANGELOG](https://raw.githubusercontent.com/ruvnet/ruflo/main/CHANGELOG.md) | cost/tokens |
| Framework benchmark | v3.8.0 beats LangGraph, AutoGen and CrewAI "by 1.3x-1953x" | CLAIMED. It is an external gist that measures cold start, single turn and RSS only, not task success. Not reproduced. — [explainx](https://explainx.ai/blog/ruflo-ruvnet-claude-flow-meta-harness-swarms-memory-federation-claims-vs-readme-2026) | cost |
| Hooks | "27 Hooks" | Partly REFUTED: hooks print `[OK]` and do nothing (~130 ms per call), and a fresh init wired six hooks with no handler (#4200, Oct). — [andrew.ooo](https://andrew.ooo/posts/ruflo-review-agent-harness-claude-code-codex/). Core hooks return success on CLI or install failure. — [rywalker](https://rywalker.com/research/claude-flow). The pre-bash gate failed open on timeout, parse error or exception (#4743). — [#4775](https://github.com/ruvnet/ruflo/issues/4775) | security, verification |
| Background workers | "12 auto-triggered workers" | Workers run under ruflo-loop-workers with cron: "real and works" per one reviewer (secondary). In October, #4119 to #4123 and #4137 reported workers with hard-coded or fabricated security, coverage and benchmark output (local audit). — [search summary](https://andrew.ooo/posts/ruflo-review-agent-harness-claude-code-codex/) | ops |
| Plugins | "48 native Claude Code plugins + 14 in-tree npm plugins". The plugins page says "32". | Counts are inconsistent: 48 directories, 33 with descriptions. — [plugins dir](https://github.com/ruvnet/ruflo/tree/main/plugins). Plugins and mods run unsandboxed with the user's permissions. — [explainx](https://explainx.ai/blog/ruflo-ruvnet-claude-flow-meta-harness-swarms-memory-federation-claims-vs-readme-2026) | various |
| SPARC | "Guided 5-phase methodology with quality gates" (ruflo-sparc plugin) | Defects reported in October: agents and commands not resolvable (#4087, #4088); status read through approximate semantic search showed 8 of 133 entries (#4086). Fixes were announced in v3.56.8 (local audit). An independent re-test: UNKNOWN. | requirements/spec |
| GitHub integration | Not a headline any more. Skills `pr-manager`, `code-review-swarm` and `swarm-pr` exist as Markdown agent definitions that call `gh` and `mcp__claude-flow__github_*`. | CLAIMED, with no evidence they run. No dedicated GitHub plugin is among the 48. — [search: tessl/unpkg mirrors](https://tessl.io/registry/skills/github/ruvnet/ruflo/github-code-review); [plugins dir](https://github.com/ruvnet/ruflo/tree/main/plugins) | review, integration |
| testgen / coverage | ruflo-testgen: "test gap detection and TDD workflow" | In October the TDD skill hardcoded `success: true` (#4085). Coverage math was wrong: unweighted file averages, 83.8% vs Vitest's 88.36% (#4083); LF=0 counted as 0% (#4082). Fixes were announced in 3.56.8 (local audit). In Nov, #4718: `coverage-gaps --critical-only` does nothing. — [#4775](https://github.com/ruvnet/ruflo/issues/4775) | testing |
| Federation | "9 MCP tools + 10 CLI commands"; zero-trust mTLS plus ed25519 | Open issues: #5030 no ordered cursor; #5031 pulls can skip envelopes; #5029 invites default to 25 uses and cannot be revoked. Advisory GHSA-jwwq: a pinned peer can forge an envelope's origin. No production report exists. — [open issues](https://github.com/ruvnet/ruflo/issues?q=is%3Aissue+is%3Aopen+sort%3Acreated-desc); [advisories](https://github.com/ruvnet/ruflo/security/advisories) | coordination |
| Cost tracker / observability | ruflo-cost-tracker and ruflo-observability; the console has a cost dashboard | CLAIMED. PR #4078 (Oct) addressed cost writes that failed silently (local audit). | cost/ops |
| Migrations, ADR, DDD, docs plugins | Schema migrations, ADR lifecycle, DDD scaffolding, doc drift detection | CLAIMED only. No evidence found. — [plugins dir](https://github.com/ruvnet/ruflo/tree/main/plugins) | maintenance, design |
| Security tooling | AIDefence (prompt injection and PII, "14-type"), ruflo-security-audit (CVE scan), settings.json risk scanner | Partly VERIFIED-SELF. #4147 (Oct): a Hebrew injection was misclassified and the scanner learned zero patterns. The npm audit reported pnpm/Yarn projects as having 0 CVEs; it now reports "cannot scan" (#4124/#4154, local audit). Risk scanner on session restore added in 3.78.0 (#3835). — [v3.78.0](https://github.com/ruvnet/ruflo/releases/tag/v3.78.0) | security |

### Inferences
- The core that really works is narrow: memory, embeddings, terminal execution, session persistence, a confidence-feedback loop, real model calls through `agent_execute`, and cron-style workers. The "swarm/hive-mind/consensus/neural" layer is mostly bookkeeping and Markdown prompts on top of Claude Code's own subagents. Where "parallelism" happens, it is Claude Code doing it.
- The project's own language has shifted toward honesty. The changelog now says "samples, not a statistical result" and "no live provider call has succeeded yet", and the README concedes small-N losses. The README tool and agent counts still grow faster than the evidence does.
- Swarm-layer fixes may not reach users even after they are merged: 3.78.0 did not republish `@claude-flow/swarm`. "Released" does not equal "installed behaviour".

### Gaps
- No current (November 2026) independent runtime audit of v3.7x exists. The newest hands-on independent audit is April 2026 (v3.5.51). Since then the reviews are documentary.
- No task-outcome benchmark (SWE-bench, resolve rate, review accuracy) for Ruflo was found. — [search, 2026-11-19](https://www.vals.ai/benchmarks/swebench)
- The real-vs-stub ratio of the 406 MCP tools today is unknown.

## Q2. What do issues, discussions and the changelog report as missing, broken, flaky or most requested?

### Takeaway
The tracker is extremely active: 289 open issues, 1,938 closed, and many closures in batches. Much of it is generated by automation (scheduled "Dream Cycle" research issues, "[verification]" witness tasks, Claude-generated triage). The recurring clusters are:
1. False success and verification gaps.
2. Data integrity in the JSON/sql.js stores.
3. Flags and claims that do nothing.
4. Supply-chain and witness integrity.
5. Concurrency and locks.
6. Federation and MCP trust boundaries.
7. Usability and docs ("cannot get it to do work").
8. Windows.
9. Monolithic code size.

### Cited Findings
- Issue volume: 289 open and 1,938 closed on 2026-11-19. There were 690 open issues and 358 open PRs on 2026-10-15 ([explainx](https://explainx.ai/blog/ruflo-ruvnet-claude-flow-meta-harness-swarms-memory-federation-claims-vs-readme-2026)) and 665 on 2026-10-20 ([andrew.ooo](https://andrew.ooo/posts/ruflo-review-agent-harness-claude-code-codex/)). In the newest 25 closed issues, 16 were closed on 19 Nov, all fall within 17-19 Nov, several are labelled "already-fixed", and 9 carry the "[Dream Cycle]" prefix. — [closed issues](https://github.com/ruvnet/ruflo/issues?q=is%3Aissue+is%3Aclosed+sort%3Aupdated-desc)
- **Deep-review tracker #4775** (maintainer, 2026-11-05) lists 59 issues: CLI correctness 16, security hardening 15, tests 9, data integrity 8, docs/refactors 8, Windows 3. Examples:
  - Flags that are silently ignored (#4716 to #4722).
  - `||` turns a confidence of 0 into the default value (#4728).
  - A heartbeat for an unknown node reports success (#4731).
  - The sql.js store reports success after a refused save (#4733).
  - The daemon erases patterns by overwriting patterns.json (#4735).
  - Lost updates in the claims, tasks, agents and workflows JSON stores (#4736).
  - A corrupt store is reset to defaults and then saved over (#4737).
  - Lock stealing (#4738).
  - Stale README counts (#4756).
  
  The maintainer says all of these were folded into PR #4825, shipped in 3.72.0, and that "all eight advisories" were fixed. The tracker was "generated with RuFlo". — [#4775](https://github.com/ruvnet/ruflo/issues/4775)
- Several of those items were closed 17-19 Nov: #4736, #4738, #4742, #4746, #4747, #4749, #4751, #4752. — [closed issues](https://github.com/ruvnet/ruflo/issues?q=is%3Aissue+is%3Aclosed+sort%3Aupdated-desc). #4734 (read-only commands rewrite the whole sql.js DB) and #4750 (unsigned pattern-store downloads, with no size or timeout limits) are still open. — [open issues](https://github.com/ruvnet/ruflo/issues?q=is%3Aissue+is%3Aopen+sort%3Acreated-desc)
- **Most-commented open issues:**
  - #3189: witness signature verification fails and every manifest entry reads missing (104 comments, severity:high).
  - #2156: dream-cycle research (55 comments).
  - #3154 and #2969: the alpha CLI `--version` times out or never exits.
  - #958: "User cannot get v3 to do any actual work".
  - #4683 and #4997: witness drift.
  - #640: the verification and truth-enforcement failure in multi-agent setups (open since 2025-08-11).
  - #2885: neural training mutex crash on macOS arm64.
  - #574: Windows Git Bash setup fails and WSL is required.
  - #3157: critical and high vulnerabilities in the dependency tree.
  - #787: hive-mind docs are confusing.
  - #665: request to filter MCP tools with semantic search before they reach the LLM.
  
  — [open by comments](https://github.com/ruvnet/ruflo/issues?q=is%3Aissue+is%3Aopen+sort%3Acomments-desc)
- **Newest open issues (Nov 2026):**
  - Federation: #5030, #5031, #5029.
  - Managed-agent ledger: two waiters can both break the same stale lock (#5025).
  - `distill()` drops failed trajectories (#5011).
  - A verification check cannot run because an npm network install fails (#5035).
  - `openrouter-alts.json` resolves only from cwd, so npm installs never load it (#4957).
  - Flaky tampered-suite parity test (#4930).
  - The OpenAI provider ignores the saved endpoint, and `agent_execute` has no OpenAI-compatible branch (#4834).
  - Refactor requests for doctor.ts (3,055 lines, #4773) and neural.ts (4,704 lines, #4772).
  - Background-summary overhead (#4709), which has no measurements yet.
  
  — [open by date](https://github.com/ruvnet/ruflo/issues?q=is%3Aissue+is%3Aopen+sort%3Acreated-desc); [#4709](https://github.com/ruvnet/ruflo/issues/4709)
- **Performance:** policy anchor history still validates and rewrites the full chain on every append. At 100,000 anchors that costs 186-193 ms per assessment and 236-245 ms per append+fsync on 3.72.2, about 240 ms on 3.76.0. One live authorisation took 419 ms. The issue is open with no maintainer reply, and it continues #3164. — [#4883](https://github.com/ruvnet/ruflo/issues/4883)
- **#958 usability (open since 2026-01-17):**
  - The reporter could not get v3 to do real work.
  - The maintainer replied that the docs were "outdated" and that pending tasks are "by design".
  - Other users said "only 1 claude code 'agent' doing everything", that Claude "switched to its built-in planning mode and wrote code itself instead of using swarm tools", that they lost two days, and called it "AI slop".
  
  — [#958](https://github.com/ruvnet/ruflo/issues/958)
- **#640:** the "89%" false-success figure is not measured. In Aug 2025 the maintainer reported 72 verifications with a 16.7% pass rate. On 2026-07-29 the maintainer said v3.32.36 "advanced but did not complete" the work. The issue is still open as an umbrella. — [#640](https://github.com/ruvnet/ruflo/issues/640)
- **Feature requests (long-standing):**
  - #310: an orchestration layer for any coding CLI.
  - #578: non-interactive workflow modes.
  - #274: consolidate the MCP servers.
  - #665: semantic MCP-tool filtering.
  - #1315: message a running hive.
  - #794: multi-provider execution engine.
  
  — [open by comments](https://github.com/ruvnet/ruflo/issues?q=is%3Aissue+is%3Aopen+sort%3Acomments-desc)

### Inferences
- Top recurring complaint classes, ranked by how often they appear across the sources read:
  1. False green and fabricated output (hooks, workers, coverage, TDD, store saves, heartbeats).
  2. Store integrity and concurrency.
  3. Advertised commands, flags and agents that are not wired.
  4. Provenance and witness integrity.
  5. Onboarding confusion.
- The open-issue count fell from 665-690 to 289 in about a month. That fall is driven largely by batch fixes and automated triage. A close does not show that behaviour was re-verified.
- A large share of new issues are written by the project's own automation ("Dream Cycle", "[verification]"), so the tracker measures maintainer bandwidth and automation output as much as user pain.

### Gaps
- No exact per-theme counts across all 289 open issues. Only page 1 of each sort order was read.
- The closure reason (completed vs not planned) was not visible.

## Q3. What do independent reviews, Reddit/HN threads and benchmarks say about real-world effectiveness?

### Takeaway
No independent task-level effectiveness study exists. The two independent technical audits are roman-rr (April 2026, hands-on) and the project's own May self-audit as summarised by reviewers. They converge: there is a real core, a large decorative layer, and context and token overhead. Community sentiment in GitHub discussions is mostly negative or sceptical. Positive content is mostly promotional guides. No Hacker News thread was found.

### Cited Findings
- **roman-rr's independent audit** (Discussion #1513, 2026-04-04, v3.5.51) used eight research agents plus code review:
  - ~3% of MCP tools were real.
  - `agent_spawn` creates no subprocess and makes no LLM call.
  - The WASM agent echoes its input.
  - The AnthropicProvider is not on the execution path.
  - Intelligence data: 5,706 entries but only ~20 unique, producing a 100 MB graph. The same entry was injected 5 times per message, wasting ~15k tokens per session.
  - Estimated overhead: 15-25k tokens per session, including 91 agent definitions.
  
  — [#1513](https://github.com/ruvnet/ruflo/discussions/1513)
- **Discussion #1666** (Apr-May 2026). The accepted answer calls it "more empty promises than genuinely useful … didn't notice any significant improvements" and says the author removed it. Another user called it "not production-ready". Users cite an MCP naming mismatch (`mcp__claude-flow__*` vs `mcp__ruv-swarm__*`, #126) and synchronous better-sqlite3 blocking the event loop (#430). The only positive voice gives no data, and the maintainer did not reply. — [#1666](https://github.com/ruvnet/ruflo/discussions/1666)
- **andrew.ooo review** (2026-10-20, v3.58.1). The reviewer ran nothing because their CI lab was blocked by billing. Their verdict: "neither a scam nor the self-organizing system its tagline suggests". They judge it a poor fit for production repositories. Other points: 28 releases in October, effectively one human maintainer, and a warning that `@latest` in an MCP config means tools change overnight. — [andrew.ooo](https://andrew.ooo/posts/ruflo-review-agent-harness-claude-code-codex/)
- **rywalker.com** (verified 2026-09-15, v3.42.0):
  - MCP policy enforcement only happens with `RUFLO_MCP_ENFORCE_POLICY=1`; a policy file alone had no effect.
  - MetaHarness has a degraded mode in which a successful exit does not mean the audit ran.
  - Core hooks return success on failure.
  - Verdict: test a pinned version on a real task and verify governance by running an operation it should reject.
  
  — [rywalker](https://rywalker.com/research/claude-flow)
- **explainx.ai** (2026-10-15) reproduced none of the benchmarks. It notes that cold-start and RSS benchmarks "measure overhead, not whether agents solve tasks better". It also quotes the README's own admissions: demos use sample data or replayed frames, and "creating a mission does not mean the feature has been implemented". — [explainx](https://explainx.ai/blog/ruflo-ruvnet-claude-flow-meta-harness-swarms-memory-federation-claims-vs-readme-2026)
- A Reddit thread titled "Do not install Ruflo … 99% Fake / 1% Real" is referenced by secondary sources, but I could not locate or verify it. — [search 2026-11-19, no result](https://github.com/ruvnet/ruflo/discussions/1666)
- No Hacker News discussion was found. One profile said it found no substantive HN or Reddit threads with first-hand production reports. — [search summary / rywalker](https://rywalker.com/research/claude-flow)
- Promotional or anecdotal positives:
  - A DEV post titled "slashes API costs by 75%". — [dev.to](https://dev.to/arshkharbanda2010/ruflow-ruflo-the-multi-agent-claude-ai-orchestrator-that-slashes-api-costs-by-75-2nmc)
  - A blogger's personal claim of 35-45 min versus 3-4 h. Both are unverified.

### Inferences
- The claim that Ruflo makes Claude Code more effective at producing correct software has no independent support. The evidence that exists measures overhead, or internal mechanisms such as confidence values, not outcomes.
- The failure modes that recur across sources are:
  - Claude bypasses the swarm tooling and does the work itself.
  - Added context and token overhead.
  - Fabricated or default success values.
  - Configuration confusion: several MCP servers, the plugin path versus a full install, and mixed package names.

### Gaps
- No controlled A/B of plain Claude Code versus Claude Code with Ruflo on matched tasks, from anyone. Ruflo's own ADR-532 (#5000, #5036) only *proposes* MetaHarness evaluations against baselines. — [open issues](https://github.com/ruvnet/ruflo/issues?q=is%3Aissue+is%3Aopen+sort%3Acreated-desc)
- No current-version token-overhead measurement exists. The April figure of 15-25k tokens per session is the latest.

## Q4. Which development-lifecycle stages are weakly covered or absent?

### Takeaway
Ruflo's real investment is in **coordination, memory and context, and security of its own runtime**. Even there, the verified core is thin. The stages that matter most for software-delivery bottlenecks are weak or absent:
- Verification of agent output.
- Real test truth.
- Root-cause debugging.
- Review at scale.
- Legacy-codebase comprehension.
- Deployment and release safety.
- Operations.

Most of these exist only as Markdown agents or plugins with no evidence they run.

### Cited Findings (stage → what exists → evidence → gap)
- **Requirements/spec:** the SPARC plugin, ruflo-goals and ADR plugin, all CLAIMED. In Oct, SPARC agents and commands were not callable (#4087, #4088) and status listed 8 of 133 workflows (#4086); fixes were announced in v3.56.8 (local audit). → **Weak**: no evidence that SPARC improves spec quality.
- **Design/architecture:** ruflo-ddd and ruflo-adr scaffolding, CLAIMED only. — [plugins](https://github.com/ruvnet/ruflo/tree/main/plugins). → **Absent as evidence.**
- **Codebase understanding and context:** AgentDB/HNSW memory works (VERIFIED-IND), and there are knowledge-graph and graph-intelligence plugins. The speedups are modest and lose at small N. 3.71.0 `contextDelegation` reads large files with a cheaper model and returns cited passages; it was 6/6 on samples. — [CHANGELOG](https://raw.githubusercontent.com/ruvnet/ruflo/main/CHANGELOG.md). GHSA-rx87 showed the memory layer could be poisoned: repository files were injected into context as the user's own memory. — [advisories](https://github.com/ruvnet/ruflo/security/advisories). → **Partial.** No evidence of legacy-codebase comprehension at scale.
- **Code generation:** delegated entirely to Claude Code or Codex. Ruflo adds routing and agent personas. Users report Claude ignores the swarm tools. — [#958](https://github.com/ruvnet/ruflo/issues/958). → **No unique capability.**
- **Review:** `code-review-swarm`, `pr-manager` and `swarm-pr` exist as Markdown skills; ruflo-jujutsu does diff risk scoring. All are CLAIMED, and in Oct the analyze_diff and ownership tools reported guesses or fake success (#4119 to #4123, local audit). The analyze_diff-\* tools are untested (#4761). — [#4775](https://github.com/ruvnet/ruflo/issues/4775). → **Weak.**
- **Testing/verification:** ruflo-testgen and coverage-gaps. History of a hardcoded `success: true` (#4085) and wrong coverage math (#4082 to #4084). `--critical-only` was a no-op (#4718). #640, the truth-enforcement umbrella, has been open since 2025. → **Weak, and this is the largest gap.** Agent-output verification is still a roadmap item.
- **Debugging/root cause:** no dedicated capability found among the plugins. → **Absent.**
- **Integration/merge/CI:** GitHub skills are CLAIMED. Ruflo's own CI accepted segfault exit codes until #4099 (Oct), and its own witness verification has been red since September (#3189, #4683, #4997). — [open by comments](https://github.com/ruvnet/ruflo/issues?q=is%3Aissue+is%3Aopen+sort%3Acomments-desc). → **Weak.**
- **Deployment/release:** no deployment-safety capability, only a Docker compose for the MCP bridge, which had a critical unauthenticated RCE (GHSA-c4hm). The project's own release practice shows the problem: swarm fixes were not republished in 3.78.0, and leaf packages were published before their pins merged. — [v3.78.0](https://github.com/ruvnet/ruflo/releases/tag/v3.78.0). → **Absent.**
- **Operations/incidents:** loop-workers, ruflo-observability and ruflo-protector (a watchdog, off by default). Daemon TTL and orphan-timer issues (#4238, Oct, local audit). → **Weak.**
- **Security/supply chain:** the most actively worked area: AIDefence, a settings risk scanner, a pre-bash gate, CVE scan and signed helpers. Its own posture is still volatile; see Q5. → **Partial, heuristic.**
- **Maintenance/refactor/migration:** ruflo-migrations (DB schema) and docs drift detection, both CLAIMED. Ruflo's own code has 3,000-4,700-line command files. — [#4772, #4773](https://github.com/ruvnet/ruflo/issues?q=is%3Aissue+is%3Aopen+sort%3Acreated-desc). → **Absent as evidence.**
- **Coordination/multi-agent:** the core pitch. State bookkeeping works. Execution comes from Claude Code subagents or `agent_execute`. Consensus is unproven, and shutdown, maxAgents and lock bugs were found in Nov (#4726, #4727, #5025). → **Partial.**
- **Cost/tokens:** a cost-tracker plugin, opt-in routers and context delegation. Historical token-saving claims are refuted. There is +15-25k tokens per session of overhead (April), and current overhead is unmeasured (#4709 has no data). → **Weak; may be net negative.**

### Inferences
- Ruflo does not attack the main development bottleneck: trustworthy verification of AI-written changes. Its own history is a catalogue of false-green failures, including tests, coverage, hooks, CI, store saves and witness checks.
- The strongest transferable ideas are mechanisms rather than outcomes: governed context delegation with cited passages, a policy and receipt ledger (once bounded, see #4883), settings risk scanning, and memory provenance ("lessons only from files written by this machine", #5037).

### Gaps
- None of the stage verdicts rests on an independent runtime test of v3.78.0. They are built from tracker, code-review and changelog evidence.

## Q5. What is its security and supply-chain posture, and how does it compare with the local audit of 2026-10-19?

### Takeaway
The posture is improving fast but is still not trustworthy for a host with secrets. On 2026-11-05 the project published **8 new GHSAs** (1 critical, 4 high). The cross-client MCP principal issue #3294 is **still open**. Self-attested witness verification has been red for months. npm has registry signatures but no provenance attestation. Install-time scripts are gone from the `ruflo` wrapper. The local audit's HOLD stays justified, and several of its statements are now superseded.

### Cited Findings
- **Advisories:** 9 published. Eight are new on **2026-11-05**:
  - GHSA-5pxg-x8g8-fw4j, **Critical**: `browser_open` passes caller-supplied Chromium launch flags, allowing command execution.
  - GHSA-vqpp-qh58-2p7h, High: `memory_export` and `memory_import` write and read arbitrary paths.
  - GHSA-6rwv-52g2-vx7j, High: prototype pollution through `__proto__` ids in the agent, task and terminal stores.
  - GHSA-8jjw-xqg5-7pvx, High: the ruvocal mcp-bridge can be driven on loopback with no token (CORS \*, DNS rebinding).
  - GHSA-hgp6-gm2j-hx55, High: ruvocal SSRF through user-supplied MCP URLs.
  - GHSA-rx87-v2fr-76xf, Moderate: repository files are injected into context as the user's memory or learned patterns.
  - GHSA-hmmg-9p82-2m6q, Moderate: X-Forwarded-For bypasses the per-IP limits.
  - GHSA-jwwq-crgq-c4c7, Moderate: a federation peer can forge an envelope's origin.
  - Historical: GHSA-c4hm-4h84-2cf3, **Critical**, unauthenticated RCE in the MCP bridge docker-compose (2026-07-01).
  
  The advisory index shows no CVE IDs or version ranges. — [advisories](https://github.com/ruvnet/ruflo/security/advisories). The maintainer says these were fixed and published in 3.71.4 and 3.72.0. — [#4775](https://github.com/ruvnet/ruflo/issues/4775)
- **Other Nov security items:**
  - Managed-agent tools could act on **any session in the Anthropic org** (#4751, closed 17 Nov). 3.77.2 restricts sessions to those the project created.
  - The pre-bash gate failed open and missed `$(...)` (#4742, #4743).
  - The console auto-installed patches, and ruvocal Mongo bound all interfaces with no auth (#4755).
  - Helpers were unsigned and helper writes followed symlinks (#4746, closed 19 Nov).
  - Pattern-store downloads have no real signature or limits (#4750, **open**). 3.75.3 adds *optional* pinned-key verification.
  
  — [#4775](https://github.com/ruvnet/ruflo/issues/4775); [Releases](https://github.com/ruvnet/ruflo/releases)
- **v3.78.0 hardening:** authenticated `/ws` and constant-time tokens (#5032), transport and WebSocket limits (#4962), every `.claude-flow` write guarded and helpers signed (#5039), settings.json risk scanning on restore (#3835). — [v3.78.0](https://github.com/ruvnet/ruflo/releases/tag/v3.78.0)
- **#3294**, the MCP singleton session and cross-client principal aliasing: **open**. On 2026-09-11 the owner said "no merge or deployment until" gates pass. On 2026-11-04 a commenter reported that published `@claude-flow/mcp` 3.1.5 and 3.1.6 still lacked the request-scoped session boundary. — [#3294](https://github.com/ruvnet/ruflo/issues/3294)
- **Witness integrity:** #4997 (2026-11-15) reports drift=10 on all platforms in 3.77.1. The manifests are "self-attested", and `dist/` is never checked. The maintainer (2026-11-19) attributes this to an unbuilt-tree scheduled task, but the drift persisted across commits and the explanation is not demonstrated. #3189 (104 comments) is still open. #4201 (Oct): the witness seed is derived from the public commit hash; the maintainer says this does not affect npm signing. — [#4997](https://github.com/ruvnet/ruflo/issues/4997); [andrew.ooo](https://andrew.ooo/posts/ruflo-review-agent-harness-claude-code-codex/)
- **Install scripts:** `ruflo@3.78.0` has no preinstall, install, postinstall or prepare script. — [npm](https://registry.npmjs.org/ruflo/latest). History: 3.1.0-alpha.45 to .55 had a preinstall that walked npm `_npx/_cacache` and deleted files mentioning claude-flow or ruflo — [npm packument](https://registry.npmjs.org/ruflo). Reportedly shipped obfuscated through 3.5.2 and removed in v3.5.40. — [andrew.ooo](https://andrew.ooo/posts/ruflo-review-agent-harness-claude-code-codex/). The nested `@claude-flow/cli` 3.78.0 lifecycle scripts were NOT checked in this pass.
- **Permissions:** plugins and mods run unsandboxed with the user's permissions. — [explainx](https://explainx.ai/blog/ruflo-ruvnet-claude-flow-meta-harness-swarms-memory-federation-claims-vs-readme-2026). Hive-mind used to launch Claude Code with `--dangerously-skip-permissions`; this is now opt-in. — [andrew.ooo](https://andrew.ooo/posts/ruflo-review-agent-harness-claude-code-codex/). MCP policy enforcement is opt-in through an environment variable. — [rywalker](https://rywalker.com/research/claude-flow)
- **Telemetry and network:** the README badge counts "npm download events". The x.ruv.io gateway, federation, pattern-store downloads and 3.75.2's MCP-bridge guard against private-address URLs all show network surface. — [README](https://github.com/ruvnet/ruflo); [Releases](https://github.com/ruvnet/ruflo/releases)
- **Dependencies:** #3157 (critical and high transitive vulnerabilities on 3.38.20) is still open. 3.75.3 moved to zod 4 "to address audit findings". `overrides` pin better-sqlite3 12.9.0. — [open issues](https://github.com/ruvnet/ruflo/issues?q=is%3Aissue+is%3Aopen+sort%3Acomments-desc); [npm](https://registry.npmjs.org/ruflo/latest)

### Delta vs local audit (2026-10-11 → 2026-10-19 addenda)
- **SUPERSEDED:**
  - Latest version is v3.78.0 (2026-11-19), not v3.57.0. That is about 20 or more minor and patch releases in a month.
  - "The GHSA list shows only GHSA-c4hm" is now false: 8 more were published on 2026-11-05.
  - The v3.57.0 tag was unsigned; the v3.78.0 tag commit is GitHub-verified.
  - The `ruflo` npm package is now a 3-file wrapper with no install scripts. Registry signatures are present, but there is still no provenance attestation.
  - The "nested better-sqlite3 11.x" concern (#4055): the wrapper now pins better-sqlite3 12.9.0 via overrides. Whether the nested CLI tree resolves to it was not verified.
  - SONA persistence #4080 and the settings-scanner wiring #3834/#3835 are now closed and integrated in 3.78.0. That is a source fix, not artifact proof.
- **CONFIRMED and still open:**
  - #3294 cross-client principal aliasing.
  - #3189 witness verification, plus new drift reports #4683 and #4997.
  - #3164 ledger cost, continued as #4883 with measured O(history) growth on 3.76.0.
  - #640, the truth-enforcement umbrella.
  - The false-green pattern (new instances: #4731, #4733, #4743, `||` zero-to-default).
  - Release-to-installed gaps (#3306 then; `@claude-flow/swarm` not republished in 3.78.0 now).
- **NEW since the audit:**
  - The 59-item deep-review tracker #4775.
  - The managed-agents any-org-session exposure (#4751).
  - Repository files poisoning memory (GHSA-rx87).
  - Federation replay, ordering and revocation gaps (#5029 to #5031).
  - Unsigned pattern downloads (#4750, open).
  - Automated "Dream Cycle" research issues.
  - A tracker that has been opened and closed by automation in large volumes.

### Inferences
- The project now runs a real security process: GHSAs, a scheduled verification task and batch hardening. The attack surface grows at the same pace: browser, federation, x-gateway, ruvocal, managed agents, console auto-patching. Each release both closes and opens trust boundaries.
- For any host with secrets, the blocking items are still #3294 (open), unsandboxed plugins and mods, opt-in rather than default policy enforcement, unsigned pattern downloads, and the absence of npm provenance attestations.

### Gaps
- No CVE IDs or affected and patched ranges were visible for the 8 new GHSAs.
- The lifecycle scripts and transitive SBOM of `@claude-flow/cli@3.78.0` were not inspected.
- No independent malware or AV re-scan of current artifacts was found.
- The ten drifted files in #4997 were not identified.
