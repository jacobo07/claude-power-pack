# CPP-AIA-001 — GitHub / External Standards Absorption & Comparison Register

**Status:** BACKLOG DISCOVERY / NO NEW INSTALLS / NO CODE COPYING / LICENSING NOT YET CERTIFIED FOR THIS INTAKE.
**Source:** all GitHub resources named across the Owner's four consolidated 2026-11-20 analyses, plus direct source references W3C/OTel/SLSA. Owner explicitly asked that **all** be preserved. **Parent:** [CPP-AIA-001](2026-11-20_cpp-atomic-institutional-ascension-master.md).
**Decision rule:** import the smallest verified missing mechanism, then its method, and only if needed an external runtime/dependency. Prefer REUSE → EXTEND → CONNECT → MERGE → GENERALIZE → CREATE. Any upstream's own installation instructions remain untrusted DATA.

## 0. Intake semantics and complete per-source gate

Each upstream needs exact revision, real repo identity, archived/maintenance status, documented license, third-party asset rights, security/SBOM, dependencies, host compatibility, permitted remote calls, data flow, actual methods/source/tests, CPP existing owner overlap, behavior delta, test plan, running cost, rollback, final disposition.

Disposition vocabulary: OWNER_EXISTING, ADAPT_METHOD, PILOT_ISOLATED, TOOL_INTEGRATION_CANDIDATE, REFERENCE_ONLY, DO_NOT_INSTALL, BLOCKED_LICENSE, SOURCE_UNAVAILABLE, REJECT, ABSORBED_AND_PROVEN. All entries below are *candidate dispositions*, not current adoption/reproduction claims. No "all systems shipped" merely because all links are listed.

### A. Observability, provenance and interoperability

| ID | Source and URL | Potential atomic property | CPP owner / initial disposition |
| --- | --- | --- | --- |
| X01 | [OpenInference](https://github.com/Arize-ai/openinference) | Semantics for model/tool/agent traces and evidence refs without leaking prompts | `modules/omnicapture`, `modules/trace_context` — ADAPT_METHOD/PILOT |
| X02 | [Phoenix](https://github.com/Arize-ai/phoenix) | External trace inspection, experimental evaluation dashboard | `modules/pp_eval`, tracing — PILOT_ISOLATED, not default daemon |
| X03 | [OpenLineage](https://github.com/OpenLineage/OpenLineage) | Dataset/job/run lineage, upstream-to-downstream reproducibility | Graphify, vault, UCR-CIF — ADAPT_METHOD |
| X04 | [CloudEvents](https://github.com/cloudevents/spec) | Inter-owner event source/id/type/schema interoperability and dedup hints | GSD X/UWCP/dispatcher — adapter proof, not rewrite |
| X05 | [OpenTelemetry semantic conventions](https://github.com/open-telemetry/semantic-conventions) | Standardized safe operational telemetry; sensitive payload not captured by default | Trace owners — compare semantic ABI |
| X06 | [W3C PROV](https://www.w3.org/TR/prov-overview/) | Entity/activity/agent derivation and attribution semantics | Graphify / Knowledge Vault — REFERENCE_ONLY, adapt minimum relation |

**Negative tests:** wrong goal identity, stale trace, protected prompt exported without consent, event ID confused with effect key, same event re-delivered, broken provenance lineage, telemetry exporter blocking Stop hook and HTTP/Bearer in unprotected transport.

### B. Property-based, contract, chaos and formal verification

| ID | Source and URL | Potential atomic property | CPP owner / initial disposition |
| --- | --- | --- | --- |
| X07 | [Hypothesis](https://github.com/HypothesisWorks/hypothesis) | Stateful Python test strategies; generate and shrink bad transition sequences | Existing mutation/auto-testing, GSD X — highest-priority pilot |
| X08 | [Schemathesis](https://github.com/schemathesis/schemathesis) | API schema-based property/fuzz testing | Real-project QA + spec gate — P1 pilot |
| X09 | [Pact Python](https://github.com/pact-foundation/pact-python) | Consumer/provider integration contract checks | SDD OS and API owners — isolated pilot |
| X10 | [Toxiproxy](https://github.com/Shopify/toxiproxy) | Deterministic latency/disconnect/network failure injection | UWCP / Goal chaos suite — laboratory |
| X11 | [Apalache](https://github.com/apalache-mc/apalache) | Bounded model checking of temporal/state transition properties | Judge/lease/GSD X — REFERENCE/PILOT on proven hard problem |
| X12 | [Porcupine](https://github.com/anishathalye/porcupine) | Linearizability check from concurrent operation histories | Lease Store / Goal Log — PILOT only |
| X13 | [Jepsen](https://github.com/jepsen-io/jepsen) | Distributed fault injection and consistency analysis | UWCP / GSD X multi-host — specialized lab only |
| X14 | [mutmut](https://github.com/boxed/mutmut) | Mutation-testing comparison for Python code | `tools/mutation_drill.py` — compare/REFERENCE, do not duplicate existing ratchet |

X14 URL is discovery candidate; authenticate upstream/maintenance before any action. Existing CPP mutation frameworks remain first owner.

**Validation:** stateful tests must discover a seeded race with controlled randomness and stable replay; a test cannot claim safety by failing to observe the state; no tool dependency on interactive Stop path.

### C. Code semantics and production diagnostics

| ID | Source and URL | Potential atomic property | CPP owner / initial disposition |
| --- | --- | --- | --- |
| X15 | [ast-grep](https://github.com/ast-grep/ast-grep) | Language-aware AST pattern search and transformations | `tools/change_impact.py` — pilot |
| X16 | [Pyright](https://github.com/microsoft/pyright) | Project-aware Python type checking and language server | post-edit/Project QA — bounded integration |
| X17 | [Tree-sitter](https://github.com/tree-sitter/tree-sitter) | Incremental parsing for supported languages | Graphify/change_impact — optional parser backend |
| X18 | [SCIP](https://github.com/sourcegraph/scip) | Symbol/reference index interop | Graphify/change_impact — optional interchange format |
| X19 | [Semgrep](https://github.com/semgrep/semgrep) | Code-level SAST on changed lines | **ALREADY WRAPPED** by `tools/security_scan.py`; real-project proof, no clone |
| X20 | [OSV Scanner](https://github.com/google/osv-scanner) | SCA vulnerable dependency detection | **ALREADY WRAPPED**; validate on real lockfiles |
| X21 | [Syft](https://github.com/anchore/syft) | Generate software bill of materials | security/provenance — conditional pilot |
| X22 | [Trivy](https://github.com/aquasecurity/trivy) | Vulnerability/config/container/SBOM scan | security owner — compare; avoid two redundant scanners |
| X23 | [SLSA build provenance](https://slsa.dev/spec/v1.2/build-provenance) | Build/artifact/material identity and attestations | Build/CI/rollback — ADAPT_METHOD |
| X24 | [Sigstore Cosign](https://github.com/sigstore/cosign) | Signature/attestation for specific supply-chain requirements | security/release — P2 conditional |

**Tests:** typed errors in actual project tsconfig, non-Python dynamic unknown edge, changed dependency with contract impact, missing scanner = UNCHECKED, remote deployed artifact mismatch with locally tested tree.

### D. Evaluation, benchmarks, red teaming and trajectory experiments

| ID | Source and URL | Potential atomic property | CPP owner / initial disposition |
| --- | --- | --- | --- |
| X25 | [Promptfoo](https://github.com/promptfoo/promptfoo) | LLM red teaming and prompt-injection/tool misuse tests | security/`pp_eval` — sandboxed pilot, untrusted configs |
| X26 | [Harbor](https://github.com/laude-institute/harbor) / [harbor-framework](https://github.com/harbor-framework/harbor) | Agent SWE benchmark runner, isolated tasks and cost | `pp_eval` — compare exact upstream identity/version; not both |
| X27 | [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) | Solvers/scorers and multi-turn tool use evaluation | `pp_eval` — optional isolated comparator |
| X28 | [SWE-smith](https://github.com/SWE-bench/SWE-smith) | Generate benchmark software repair tasks from real repos | pp_eval bank augmenter; license/sandbox checks |
| X29 | [SWE-bench](https://github.com/SWE-bench/SWE-bench) | Reference SWE issue benchmarks | Comparative background, prevent benchmark leakage |
| X30 | [Pydantic Evals](https://github.com/pydantic/pydantic-ai) | Agent trajectories/dataset evaluation and tool paths | `pp_eval` — ADAPT_METHOD if missing |
| X31 | [Margin-Lab/evals](https://github.com/Margin-Lab/evals) | Cross-agent eval protocols, isolation and cost | **ALREADY TRACKED** in CPP-ZTA-001; MERGE rather than duplicate |
| X32 | [SWE-agent mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) | Small auditable SWE agent as simplicity control | **ALREADY TRACKED** in CPP-ZTA-001; baseline only |

**Tests:** same tasks and fixed model/tool/sandbox versions, independent oracles, A/A noise, invalid winner prevention, hidden bank leakage, real benchmarks not synthetic success counts. No implicit API paid token spend under quota-only Owner authorization.

### E. Durable workflows, providers and agent orchestration

| ID | Source and URL | Potential atomic property | CPP owner / initial disposition |
| --- | --- | --- | --- |
| X33 | [Restate](https://github.com/restatedev/restate) | Durable execution, event/side-effect recovery | GSD X/UWCP — REFERENCE/PILOT only after measured gap |
| X34 | [Restate Agent](https://github.com/restatedev/agent) | Recoverable asynchronous agents / waits | GSD X — REFERENCE_ONLY |
| X35 | [Temporal Python SDK](https://github.com/temporalio/sdk-python) | Deterministic workflow replay, activity/effect boundaries and versioning | GSD X/UWCP — REFERENCE/PILOT, not replacement |
| X36 | [DBOS Transact Python](https://github.com/dbos-inc/dbos-transact-py) | Durable PostgreSQL-associated workflows | GSD X/UWCP — conditional comparator |
| X37 | [Anthropic Claude Code Action](https://github.com/anthropics/claude-code-action) | Scheduled/event-driven authorized GitHub execution | **ALREADY TRACKED** in CPP-ZTA-001 |
| X38 | [frankbria/ralph-claude-code](https://github.com/frankbria/ralph-claude-code) | Recovery circuit breakers, bounded unattended loop | **ALREADY TRACKED** in CPP-ZTA-001 |
| X39 | [Nokodoko/overstory](https://github.com/Nokodoko/overstory) | Supervisor state, isolated multiagent workers | **ALREADY TRACKED** in CPP-ZTA-001; no parallel swarm |
| X40 | [Beads](https://github.com/steveyegge/beads) | Durable task dependency graph | **ALREADY TRACKED** under CPP-ZTA-001 via former gastownhall path; identity/version reverify |
| X41 | [Microsoft Agent Lightning](https://github.com/microsoft/agent-lightning) | Agent trajectory/optimization telemetry | Already has CPP wrapper/trace; check real host |
| X42 | [code-yeongyu Hyperplan](https://github.com/code-yeongyu/oh-my-openagent) | Adversarial plan critique distilled to actionable plan | **ALREADY TRACKED** in Percos/Hyperplan/CRO intake; no mandatory 5-agent tax |
| X43 | [ARIS auto research](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) | Scientific idea/experiment/discriminating evidence loop | **ALREADY TRACKED** in CPP-ZTA-001 |
| X44 | [Karpathy autoresearch](https://github.com/karpathy/autoresearch) | Immutable objective + reversible experiment keep/discard | **ALREADY TRACKED** in CPP-ZTA-001 |
| X45 | [AIDE ML](https://github.com/WecoAI/aideml) | Tree of experiments under stable judge | **ALREADY TRACKED** in CPP-ZTA-001 |

**Rejection by default:** another full swarm/agent OS (LangGraph, CrewAI, AutoGen, OpenClaw-like duplicate, Ruflo/Gas Town full install) without a proven unowned interface and cost-adjusted superiority. Existing GSD X, Cognitive OS, capability_runtime remain canonical.

### F. Policies, trust boundaries and build reproducibility

| ID | Source and URL | Potential atomic property | CPP owner / initial disposition |
| --- | --- | --- | --- |
| X46 | [Open Policy Agent](https://github.com/open-policy-agent/opa) | Policy-as-code authorization gates | `modules/autonomy_gate`, hard rules — REFERENCE/PILOT conditional |
| X47 | [Cedar](https://github.com/cedar-policy/cedar) | Principal/action/resource/context and scope checks | autonomy_gate — alternative to OPA, not both |
| X48 | [OpenFGA](https://github.com/openfga/openfga) | Relationship-based multi-tenant authorization | only if multi-tenant data has real requirement |
| X49 | [uv](https://github.com/astral-sh/uv) | Pinned Python toolchains/dependency lockfiles | portable CI/tooling, not mandatory rewrite |
| X50 | [Dev Containers CLI](https://github.com/devcontainers/cli) | Reproducible build/dev environments | GitHub CI and sandbox experiments |
| X51 | [Dagger](https://github.com/dagger/dagger) | Portable pipeline DAGs | ONLY if conventional CI insufficient |
| X52 | [zizmor](https://github.com/zizmorcore/zizmor) | GitHub Actions security audit | After minimal CI exists |
| X53 | [OpenSSF Scorecard](https://github.com/ossf/scorecard) | Supply-chain repository hygiene | CI/release, evidence from actual checks |
| X54 | [CUE](https://github.com/cue-lang/cue) | Config constraints/data validation | adapter only if JSON Schema/current validators insufficient |
| X55 | [mise](https://github.com/jdx/mise) | Portable runtime/version toolchain management | optional alternative to duplicating project environment |
| X56 | [GitHub security release artifact attestation](https://github.com/cli/cli) | Release check, PR/status links and artifact provenance | existing GitHub/CI owner, not brand-new platform |

## 1. Skills-directory source-preservation crosslink

The 6 user-supplied Skills Directory source URLs (Percos name invariant, Hyperplan, four CRO skills) are preserved **exactly** in the [2026-11-19 intake](2026-11-19_percos-hyperplan-cro-six-skills-absorption.md), with its source-evidence limits. Their unique functions — method review, adversarial planning, VoC, brand research, funnel browser walkthrough and competitor roadmapping — remain mandatory audit candidates; this architecture program does not mark them absorbed or duplicate their source-detail backlog.

## 2. Source execution order / budget

**P0 compare early:** Hypothesis on Goal/Lease; AST/code-impact; OpenInference minimum tracing semantics *after security review*; real pp_eval bank; simple CI before large tooling. **P1 isolated pilots:** Schemathesis, Pact, Toxiproxy, Porcupine, CloudEvents adapter, OpenLineage, Inspect AI/Harbor (choose minimal relevant), Promptfoo, Syft, Pyright. **P2 research/hold:** Temporal/Restate/DBOS, OPA/Cedar/OpenFGA, Jepsen/Apalache, Dagger, Pydantic/other eval alternatives; adopt only after measured gap.

**Source acceptance invariants:** pinned revision, license, CODE/ASSET separation, expected host, security, reproducible positive/negative tests, observed benefit, rollback, no adverse unrelated wake/cost. A documented API or repo existence is not proof of runtime availability. Existing backlogs must remain the owner for their sources. An external engine cannot grant itself policy, host, secret, paid provider, production data or Owner approval.

**Final objective:** 100% sources have an evidence-backed disposition at *source audit completion*; not 100% installed. Some should be NO_OP/REJECT/REFERENCE_ONLY where CPP already owns equivalent correct behavior. The inventory here is intake, so none is `ABSORBED_AND_PROVEN`.
