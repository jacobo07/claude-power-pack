---
covers: [agent-virtualization, agent-spec, agent-estate-audit, carrier-agents, agent-resolver, proof-bundle, role-paging, agent-foundry, agent-discovery-cost, agent-solo-guard-conflict, agent-telemetry, symbol-lexicon, resolver-negative-cache, carrier-guard-settings]
date: 2026-09-30
updated: 2026-10-03
tier: T3
status: ready
scope: [modules/capability_runtime/, modules/cognitive_os/co_12_telemetry.py, tools/agent_carrier_run.py, tools/agent_patch_apply.py, tools/agent_estate_audit.py, hooks/carrier_bash_guard.js, agents/carriers/, tools/test_agent_telemetry.py, tools/test_capability_runtime.py, tools/test_agent_resolver.py, tools/test_agent_carrier_run.py, tools/test_agent_patch_apply.py]
open_questions:
  - Q1 | RESOLVED | symbol names are fixed inside the shared applicability._hits (D1), not resolver-local
  - Q2 | RESOLVED | telemetry extends CO-12 record_signal through a new agent_telemetry.py adapter (D3)
  - Q3 | RESOLVED | required guards ship as repo-owned per-run --settings; /root host settings untouched (D6)
  - Q4 | ASSUMED | S5f runs after the weekly reset or an explicit Owner go; S5a-S5e do not wait (D8)
  - Q5 | RESOLVED | S6 starts recorder-only; challenger needs recurring gaps and n>=3 per arm (S6 gate)
  - Q6 | RESOLVED | creation gate is REPORT now, SHADOW later, BLOCK only after certification (S7 gate)
  - Q7 | RESOLVED | agent_resolver is a parent entrypoint, wired via carrier descriptions; PLANNED+OWNER_QUEUE until installed (D7)
acceptance:
  - AC-1 symbol names route and ordinary phrases keep identical hits | verify: python tools/test_capability_runtime.py
  - AC-2 resolver routes C++ to cpp-reviewer; a code change invalidates a cached miss | verify: python tools/test_agent_resolver.py
  - AC-3 resolution/run/outcome rows reach CO-12 through an injectable sink | verify: python tools/test_agent_telemetry.py
  - AC-4 run accounting, guard states and pinned CLI recorded per run | verify: python tools/test_agent_carrier_run.py
  - AC-5 a repair counts only when plain apply fails and recount succeeds | verify: python tools/test_agent_patch_apply.py
must_still_pass:
  - python tools/test_agent_spec.py
  - python tools/test_agent_bundle.py
  - python tools/test_agent_s4.py
  - python tools/test_agent_bench.py
  - python tools/test_tower_o4.py
  - python tools/test_gsd_x_reconstruction.py
  - python tools/test_gsd_x_mutation.py
  - python tools/test_usea_cross_domain_benchmark.py
  - python tools/test_surface_architecture.py
checkpoints:
  - CP-1 | C1 identity property test passes over phrases discovered from contracts, specs and tower families, and its symbol-edged positive control changes hits
  - CP-2 | C2 stale-miss regression is red before the policy hash and green after
  - CP-3 | C3 mutation drills kill the boundary, lexicon and policy-key mutants on an isolated copy
  - CP-4 | C5 a full test run leaves the live ~/.claude/state/co12_readiness/signals.jsonl unchanged
  - CP-5 | C7 a local hermetic carrier run records FIRED from the run-settings source only
  - CP-6 | C8 GEX44 PRG record names user, repo sha, CLI path+version, spec and settings digests, heartbeat, CO-12 rows
---

# Agent Capability Virtualization — ULTRA plan (phase 5, audit fixes injected)

Capability availability must not require capability residency. Durable copy of the
inline approval plan. Every capability is PLANNED until its slice gate runs.

## Measured baseline (2026-09-30, HEAD 4ead645, branch feature/knowledge-acquisition)

- Repo `agents/`: 16 files, 107,753 B; 9 not installed anywhere (undispatchable).
- `~/.claude/agents`: 92 files, 91 named, 62 unique names, 1,218,761 B.
- 29 name collisions: upstream GSD installer ships `gsd-X.compact.md` with the same
  `name:` as `gsd-X.md` (`~/.claude/gsd-file-manifest.json`). Dispatch winner UNKNOWN.
- Parent-resident per agent: name + description + tool list (observed in the
  parent's own Agent listing); bodies not resident. 62 descriptions = 19,338 B, linear.
- Skills: 237 SKILL.md, 197 unique names, 69,358 description bytes (upper bound; the
  parent listing shows many skills name-only, so the runtime truncates).
- `~/.claude/agents/INDEX.md` hand-curated and stale.
- Bug: `hooks/agent-solo-guard.js:338-373` (contract check) and `:375+` (bound check)
  are mutually exclusive for a long read-only agent: the first refuses a
  durable-output clause without Write, the second refuses a long prompt without one
  and never consults declared tools. Repo `hooks/` and live `~/.claude/hooks/` copy
  are byte-identical (sha256 D5FE7CCEDE78).

## S0 results (measured 2026-09-30, Claude Code 2.1.286)

- Guard deadlock fixed (aa1b8e9): 18/18, the new case fails on the old guard.
- Collision probe (`claude -p`, haiku, project agents `collide-probe.md` +
  `collide-probe.compact.md`, same `name:`): listing shows the name ONCE; the
  dispatched body was `collide-probe.md`. The 29 GSD `.compact.md` twins therefore
  cost no listing and are never dispatched. Filename-match vs sort order: UNDETERMINED
  (one probe).
- `tools/agent_estate_audit.py` (V-AGE 10/10): 10 dormant repo agents (the 9 above
  plus python-reviewer; the earlier "9" was a handoff number the auditor repeated).
  Resident listing bytes: global 23,010; revenue-forensics pack 11,887 (project
  scoped). Body duplication: 3,288 shared 8-word shingles; largest pair
  gsd-phase-researcher / gsd-project-researcher (1,220), upstream-owned.
- `tools/agent_discovery_curve.py`, real parent usage, synthetic listed agents with
  310 B descriptions: N=0 68,288 · 100 77,082 · 400 97,195 · 1000 135,563 context
  tokens. 64-88 tokens per listed agent, no ceiling observed: a flat 1,000-agent
  estate doubles the parent's startup context. S2 must beat this on the same tool.

## Owner decisions (phase 2)

Collisions first (detect/report, never delete third-party files) · dormant agents
become virtual specs · carrier model accepted · benchmark on subscription quota,
cheapest working design · full scope · commits pushed.

## Audit (phase 4) -> resolution

| # | sev | gap | resolution |
|---|---|---|---|
| 1 | HIGH | "extend capability_runtime" undefined | AgentSpec = CapabilityContract (`contract.py:79`) identity/applicability/retirement + an agent section (permission_class, pages, primitives, model_policy, output_contract). Field map written into this spec in S1 before code. |
| 2 | HIGH | agent_pack_sync is a copier, not a generator | New projection writer; pack_sync untouched, only distributes generated packs. |
| 3 | HIGH | read-only carrier cannot write the bundle | Bundle returned inline (fenced JSON); parent validates and persists. |
| 4 | HIGH | Bash escapes class | investigator = Read/Grep/Glob (no Bash); verifier = + Bash under a PreToolUse mutation-verb guard; writer = + Edit/Write. Gate: carrier `tools:` equals class allowlist. |
| 5 | HIGH | class chosen by caller | class is a spec property, hashed in the catalog; resolver and foundry may only downgrade; mutation drill: spec claiming writer under investigator refused. |
| 6 | HIGH | benchmark cannot return REGRESSION | pre-declared n, margin, crippled positive control, fixtures frozen by hash before the spec split; INCONCLUSIVE blocks migration. |
| 7 | MED | resident claim omits resolver + skills | claim includes carriers + resolver skill bytes; skills measured above. |
| 8 | MED | collision winner unknown | S0 runtime probe decides it (hard precondition). |
| 9 | MED | unnamed deps, PLANNED half of teams | bus = `~/.claude/state/parallel_mesh/` (PM-03), cited in S2; leases/TTL stay PLANNED in the status table, not a deliverable. |
| 10 | MED | no real end-to-end dispatch gate | real `claude -p` dispatch through a carrier, page Reads asserted in transcript, bundle validated. |
| 11 | LOW | shared-tree risk | new files only until S4; pathspec commits; HEAD re-read before each commit. |

## Architecture

- Carriers: three resident agents (investigator / verifier / writer), short
  descriptions, runtime-enforced tools. Resident cost O(classes).
- Virtual specialists: AgentSpecs outside the parent, resolved deterministically,
  compiled into a carrier prompt at dispatch. HOT archetypes may be AOT-projected to
  real agent files; spec is authority.
- Paging: identity + contract inline; procedure and deep playbook as file paths the
  specialist Reads on demand.
- Proof bundle: claims, evidence, counterevidence, epistemic status, unknowns,
  recommendation, refs, state version read (HEAD sha). Merge refuses stale.

## Slices (micro-commits, V-gates, pushed)

- S0 Reality: guard-conflict fix + test both branches; collision dispatch probe;
  estate audit tool (surfaces, collisions, dormant, bytes, body duplication with
  positive controls, generated index); discovery-cost curve N=16/100/500/1000;
  benchmark fixtures authored and hash-frozen.
- S1 AgentSpec + primitives + compiler + carriers + paging of
  oneshot-architect-auditor; reconstruction gate; class-allowlist gate; escalation drill.
- S2 Resolver (tags + BM25, typed NO_CERTIFIED_SPECIALIST, cache on fingerprint +
  catalog hash) + bundle schema/validator + version stamp + real-boundary gate.
- S3 Benchmark: 3 frozen fixtures x 8 seeded defects; arms monolithic / virtual /
  crippled, same model (sonnet), 1 run each = 9 dispatches. Non-inferior iff virtual
  recall >= monolithic - 1 per fixture and false positives <= monolithic + 1;
  crippled arm must yield REGRESSION or the benchmark is void.
- S4 Migrate the 9 dormant agents to specs (gated on S3 NON_INFERIOR).
- S5 Resolution + outcome log, negative cache.
- S6 Minimal foundry: ephemeral spec from certified primitives on no-match;
  downgrade-only; never writes the registry; recurrence records a candidate only.
- S7 Closure: UKDL HR/PR/Trap, agent-creation gate, liveness registration,
  RESUMPTION file, meta-analysis.

## Claim boundary

Resident parent bytes (carriers + resolver skill) are constant in the number of
virtual specs, measured on synthetic catalogs. Runtime serialization is measured only
through what the parent observes.

## Status

| capability | status |
|---|---|
| S0-S4 (carriers, AgentSpec, paging, resolver, bundle, benchmark v2 NON_INFERIOR, 11 specs) | LIVE -- evidence in RESUMPTION + vault/audits/agent_estate/real_boundary/; suites re-measured green @ fa0babac (2026-10-03): spec 26/26, resolver 14/14, bundle 14/14, s4 44/44, bench 16/16, ACR 19/19, patch 9/9. Benchmark v2 is n=1 per arm: a non-inferiority signal, not equivalence |
| scoped writer grant (hermetic dontAsk run) | LIVE, proven on a synthetic spec only; no catalog spec is writer class |
| S5a symbol lexicon (C1), cache policy key (C2), drills (C3), typed misses (C4) | LIVE 2026-10-03 -- C1 cec43401, C2 83efad9f, C3 ee4461ac, C4 b34dbeec/016a5b6a/7faf70be/16976909; resolver 29/29, 13 mutation drills KILLED (vault/audits/agent_estate/mutation_drills/). C4 subsumes the 10-01 S5d "typed negative cache + invalidation"; S5d's replay and gap-recurrence records move to the S6 recorder |
| S5 telemetry (C5), run accounting (C6), portable guards (C7) | APPROVED 2026-10-03, READY FOR EXECUTION -- see "S5-S7 decisions" below |
| S5f real GEX44 PRG | APPROVED, gated on S5a-e green AND (weekly reset passed OR Owner go) |
| S6 foundry (recorder -> challenger -> active), S7 closure | PLANNED, entry gates below |
| instance leases / TTL beyond runtime subagent lifetime | PLANNED, no slice |
| MVCC beyond version-stamped stale refusal | PLANNED, no slice |
| learned router, cross-runtime adapters | ABSENT by decision |

## S5-S7 decisions (Owner Q&A answered 2026-10-03, approved "y"; HEAD fa0babac -> 31e1e25c)

Supersedes the 2026-10-01 phase-1 text below wherever they disagree; that text is kept as
history. Audited by oneshot-architect-auditor (READY-WITH-FIXES, 10 gaps, all accepted;
gaps 1/7/9 re-checked against the code by the parent).

Re-measured 2026-10-03 (red baseline for S5a, real catalog of 11 specs / 13 contracts):
`_hits` returns [] for `c++`, `c#`, `f#`, `.net`; hits for `node.js`, `go code`. Resolver
tokens for "C++"/"C#"/"F#" are empty; "review this C++ code for memory bugs" ->
NO_CERTIFIED_SPECIALIST while the same request with "cpp" -> cpp-reviewer; C++/C#/F# share one
cache key; a second identical lookup returns the cached miss. GEX44 (read-only ssh): user kobii,
/root drwx------, node v18.19.1, PATH `claude` = /usr/local/bin/claude 2.1.113 (STALE), current
~/.local/bin/claude 2.1.287, bench clone at 131180ec. Quota: 90 % of the weekly limit in 40 h on
2026-10-02 (`vault/plans/weekly-limit-burn-rca-2026-10-02.md`); current level UNKNOWN.
Correction to the 10-01 addendum: `tools/agent_carrier_run.py` imports agent_bundle and
agent_spec, not agent_resolver; agent_resolver has test callers only.

- **D1 symbols, shared owner.** `applicability._hits`: `\b..\b` -> `(?<!\w)..(?!\w)` (identical
  for word-edged phrases). One lexicon (c++ cpp, c# csharp, f# fsharp, .net dotnet), each entry
  a case-insensitive edge regex, idempotent, applied INSIDE `_hits` to text and phrase while
  returning the original phrase; `evaluate()` stays byte-identical (the gsd_x mutation drill
  anchors on applicability.py:138). The resolver tokenizer imports the same lexicon. Fixtures:
  "example.network", "asp.net", "c++11", "C++". No resolver-local exception.
- **D2 cache identity.** Key adds a sha256 over every `modules/capability_runtime/*.py`
  (class order, contract defaults and scales feed the answer), computed once per process.
  Empty-token queries are never cached. Cache stays an optimisation: any read error recomputes.
- **D3 telemetry.** EXTEND CO-12 `record_signal` via NEW `modules/capability_runtime/
  agent_telemetry.py`; co_12 gains one lazy-import line in `readiness_report` (cdio pattern).
  Kinds agent_resolution / agent_run / agent_outcome, schema `agent-telemetry/1`; dispatch_id,
  spec id + digest, carrier, model, host, repo sha, CLI path + version; goal_id only if supplied.
  Adapter refuses payload keys kind/ts. Emits on cache HIT too. Injectable sink; tests assert the
  live signals.jsonl did not grow. Read-only `agent_metrics()`. Never enters model context.
- **D4 run economics.** Tokens from the run's own stream `result.modelUsage`, else UNMEASURED.
  A repair counts only when plain `git apply --check` fails and the `--recount` check passes
  (agent_patch_apply.py:68 always recounts), or on a re-dispatch under the same dispatch_id.
  first_pass = validated with 0 repairs. One agent_run row per dispatch. consumed = UNKNOWN.
- **D5 typed misses** (lands before resolver emission): NO_MATCH, BELOW_GATE, CLASS_EXCLUDED,
  CATALOG_UNREADABLE; precedence CATALOG_UNREADABLE > BELOW_GATE > CLASS_EXCLUDED > NO_MATCH.
  **Amended by C4 (Owner-approved 2026-10-03):** precedence CATALOG_UNREADABLE > CLASS_EXCLUDED >
  BELOW_GATE > NO_MATCH -- an above-grant spec that WOULD pass the same gate is the exact
  counterfactual cause and must not hide behind an in-grant block. Definitions, as built:
  CLASS_EXCLUDED needs would_activate; BELOW_GATE needs a trigger hit AND a BLOCKING verdict; an
  anti-trigger veto is NO_MATCH (`vetoed_by`); a partial catalog is CATALOG_UNREADABLE and never
  cached; an unsearchable task is EMPTY_TASK. Contract: vault/plans/acv-c4-typed-misses-2026-10-03.md.
- **D6 portable guards.** Repo template -> per-run settings via `--settings` on every carrier run;
  required set {carrier_bash_guard}; heartbeat tagged with its registration source (only
  run-settings lines count); shell = Bash|PowerShell; states FIRED / NOT_EXERCISED / UNPROTECTED /
  STREAM_BLIND / BLOCKED (settings, guard file or node missing). Runner pins and records the CLI
  binary path + version. /root untouched. Re-measure `--settings` under `--setting-sources
  project,local` before relying on it.
- **D7 module roles.** agent_resolver = parent entrypoint the parent cannot reach; agent_bundle
  = parent acceptance step. Wire both through the repo carrier descriptions; reachability seeds
  only installed `~/.claude/agents/*.md` (`reachability.py:63,70`, non-recursive), so both are
  PLANNED+OWNER_QUEUE in the registry until the Owner installs (HR-001). Estate audit gains a
  repo-vs-installed carrier byte check. No fake invocations.
- **D8 GEX44 PRG (S5f)** after S5a-e green AND (weekly reset passed OR Owner go); one run per
  carrier class; else S5 = LOCALLY COMPLETE / REMOTE PRG BLOCKED.
- **S6 gate.** Recorder only (aggregate agent_capability_gap rows, no generation, no routing)
  until gaps recur; challenger vs general-purpose agent with production tools, best existing
  specialist and parent-direct, n>=3 per arm, ephemeral specs only; promotion only via CBR.
- **S7 gate.** `agent_estate_audit --check` typed findings against a shrink-only baseline:
  REPORT now, SHADOW later, BLOCK only after false positives are characterised. CBR family
  agent_systems at B0, all EXPERIMENTAL. UKDL candidates stay candidates.

Commits: C0 this text; C1 lexicon + boundaries; C2 policy key; C3 mutation drills; C4 typed
misses; C5 telemetry; C6 run accounting; C7 guards; C8 GEX44 PRG; C9 docs.

## S5-S7 plan (ULTRA phase 1, 2026-10-01, HEAD 8e7f30d) -- history; Q&A answered in "S5-S7 decisions" above

Reality: 535d691 is an ancestor of 8e7f30d; 4 later commits (other panes) touch no
agent-virtualization path; 706 dirty paths, none ours. S0-S4 suites green at HEAD.

Owners (EXTEND/CONNECT, measured): event sink = CO-12 `record_signal`
(`modules/cognitive_os/co_12_telemetry.py:66`, liveness already watches it); mechanics
vocabulary = `invocation.Status`; recurring root-caused failures = CEPS only; tokens = stream
`result.modelUsage` per model (measured in real streams), else UNMEASURED; PRG =
`tools/prg_assess.py`; CBR = `modules/tower` + `vault/tower/families/` (no agent family yet);
UBC = no module found, CBR family injection is the canonical equivalent. FIOS: reference only.

Findings that change the plan:
- C++ miss is general: resolver tokenizer drops symbol-bearing names (C++, C#, F# -> nothing)
  AND `applicability._hits` uses `\b`, so a phrase ending in a symbol never matches (shared
  module, all contracts). CLASE 2. Fix: canonicalise symbol-bearing technical names before
  tokenising (query and spec side) + lookaround boundaries in `_hits`.
- Resolver cache already is a negative cache and is stale-prone: key lacks resolver/gate code
  version; symbol-only queries collide on an empty token key.
- GEX44: all 6 registered PreToolUse hooks point into /root (drwx------); run user kobii
  reaches none. Every GEX44 run so far had no working PreToolUse hooks. CLASE 2.
- Probe (GEX44): a `--settings` file's hooks DO fire in a hermetic dontAsk run. So guard hooks
  can travel with the run (repo-owned file), fixing both GEX44 and hermetic-hook debt
  without editing host settings.
- Only 3 certified primitives exist (prompt-defense, proof-bundle-v1, patch-proposal-v1).

S5 slices: S5a lexicon + `_hits` boundary fix + cache key versioning; S5b telemetry schema
`agent-telemetry/1` (resolution / execution / outcome kinds, dispatch_id correlation,
append-only outcome, three axes: mechanics / outcome / attribution, only AGENT|CONTEXT move
competence); S5c run + patch-apply instrumentation (modelUsage, deterministic_repairs,
plain-vs-recount); S5d typed negative cache + invalidation + would-have-suppressed replay +
gap recurrence records; S5e guard hooks travel with every carrier run; S5f real GEX44
dispatch + PRG. Telemetry never enters model context; compact projections by CLI only.
S6 (gated on S5 PRG): ephemeral spec on typed no-match, primitives + borrowed certified
pages, downgrade-only, never writes the catalog, recurrence record only; benchmark incl.
known-match control, escalation attempt, generalist comparison; ships only if it beats
generalist fallback, else recorder-only.
S7: UKDL HR/PR/Trap, agent-creation/update gate, liveness contract for dispatch events, CBR
family for agent systems, RESUMPTION, meta-analysis.

Addendum (second investigator, same day):
- UBC owner = `modules/capability_runtime/applicability.py` + `vault/capability_runtime/
  contracts/` (D2A audit; a second UBC is forbidden by design). S7 baseline = a capability
  contract there AND a CBR family (`vault/tower/families/` + `B0.json`; `ratchet.promote` has
  no admission control and no caller -- do not rely on it).
- Liveness: `agent_resolver` and `agent_bundle` are ORPHANED and undeclared in
  `vault/liveness/reachability_registry.json`. S5 must wire or declare them and every new
  module (lexicon, telemetry) in the same commit, or the reachability gate fails.
- Agent-creation gate: ABSENT. Extension point = `tools/agent_estate_audit.py` (always exits
  0 today) -> nonzero on a new undeclared agent file / collision / duplicated doctrine.
- UKDL canonical = `vault/knowledge_base/ukdl-universal.md` (writer `tools/ceps.py`). The
  global CLAUDE.md pointer `knowledge-vault/UKDL/universal-knowledge.md` does not exist --
  reported to the Owner, not edited here (HR-001).
- Agent memory / HCMH: ABSENT (doctrine only, Owner ruling open). Out of S5-S7 scope.
- Dispatch heartbeat: nearest owner `modules/cpc_os/registry.py`; no dispatch heartbeat exists.
- rolloverFocus: collision confirmed (`hooks/session_start_hub.js:260-351` matches capsules on
  cwd only). Both hub and autotype files are dirty from another writer: recorded debt, not
  touched by this plan.
