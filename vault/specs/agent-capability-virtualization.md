---
covers: [agent-virtualization, agent-spec, agent-estate-audit, carrier-agents, agent-resolver, proof-bundle, role-paging, agent-foundry, agent-discovery-cost, agent-solo-guard-conflict]
date: 2026-09-30
tier: T3
status: PLANNED (phase 5 revised after audit; awaiting Owner approval)
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
| everything above | PLANNED |
| instance leases / TTL beyond runtime subagent lifetime | PLANNED, no slice |
| MVCC beyond version-stamped stale refusal | PLANNED, no slice |
| learned router, cross-runtime adapters | ABSENT by decision |
