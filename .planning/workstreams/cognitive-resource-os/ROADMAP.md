# Roadmap: Cognitive Resource OS (GEX44 workstream)

Plan of record: `vault/plans/cognitive-resource-os-2026-09-27.md` (Owner APPROVED 2026-09-27).
Resume context: `vault/plans/cognitive-resource-os-RESUMPTION.md`. UKDL: `vault/knowledge_base/ukdl-cognitive-resource-os.md`.

Principle: waste less intelligence, never use less. Quality floors before token savings.
Every figure names its instrument and source (observed transcript vs estimate). UNKNOWN is never PASS.

## Operating constraints (every phase)

- This clone lives on GEX44 (`~/missions/cognitive-resource-os`, branch `mission/cognitive-resource-os`).
  Commit by explicit pathspec on this branch; the commits in this clone ARE the hand-back (the laptop fetches the
  branch from this directory over SSH). Do not push; if a push gate or hook refuses anything, record it and move
  on -- never route around a refusing gate. Never touch `/home/kobii/.claude/skills/claude-power-pack` (the live install) or any other
  mission's directory.
- Scope is THIS workstream only: observed usage, pricing, budget runway, prefix inventory, routing table, the P3
  protocol. Ralph/gsd_mission.py, gsd-x closure, and transcript-parser consolidation are peer-owned: read, never edit.
- Model calls are allowed ONLY on this host's subscription quota (claudeAiOauth, no API key). If
  `ANTHROPIC_API_KEY` is set in the environment of any run, STOP that phase and record BLOCKED.
- Never edit `~/.claude/settings.json`, `~/.claude/rules/`, `~/.claude/CLAUDE.md` or credentials. Never relocate rules.
- Never ask the Owner a question mid-run: when a phase cannot proceed honestly, write the blocker into its
  EVIDENCE file, mark the phase done with verdict BLOCKED/UNJUDGED, and continue.
- Measurements on this host describe GEX44 transcripts, not the laptop's. Say so beside every number.

## Phases

- [ ] **Phase 1: Gate verdict on the big host** - run the workstream's gates and the full pytest suite with a dirty-set bracket
- [x] **Phase 2: GEX44 observed baseline** - tis_observed over this host's own transcripts, split by entrypoint (completed 2026-09-28)
- [ ] **Phase 3: P3 pre-flight P0** - can an arm run without ~/.claude/rules without touching global config or credentials
- [ ] **Phase 4: Prefix cache-miss A/B** - does a second identical session reuse the first one's cached prefix, with and without MCP
- [ ] **Phase 5: Seal and hand back** - UKDL + RESUMPTION updated from phases 1-4, all committed on the branch

## Phase Details

### Phase 1: Gate verdict on the big host

**Goal**: Replace the laptop's INCONCLUSIVE V-BASELINE-INTACT (full pytest >180 s on a starved host) with a real verdict.
**Depends on**: Nothing
**Requirements**: CRO-01
**Success Criteria** (what must be TRUE):

  1. `tools/test_tis_observed.py`, `tools/test_pricing_source.py`, `tools/test_budget_monitor_observed.py`,
     `tools/test_prefix_inventory.py` each run and their pass lines are recorded verbatim.
  2. `python3 -m pytest tests/ -q` runs to completion with a bounded timeout (≤ 1800 s), bracketed by the sorted
     dirty-path SET before and after; result recorded as PASS / FAIL (with failing ids) / INCONCLUSIVE (with the moved paths).
  3. Any failure is classified: attributable to this workstream's files, pre-existing (reproduced at the base commit
     `784e446` in a scratch worktree), or environment (Linux vs Windows). No fix outside this workstream's scope.
  4. `.planning/workstreams/cognitive-resource-os/phases/01-*/EVIDENCE.md` holds commands, exit codes and verdicts.

**Plans**: 2/2 plans executed — phase BLOCKED (CRO-01 not satisfied; see EVIDENCE.md section 4). 01-02's Task 1
legitimacy checkpoint was answered rejected (no Owner reachable mid-run); rerun once the Owner answers it.

Plans:

- [x] 01-01-PLAN.md — pre-checks (API key, host, pytest probe) + the four workstream gates verbatim, owned-file set, gate verdict (autonomous, wave 1)
- [x] 01-02-PLAN.md — package-legitimacy checkpoint, pytest in a job-scratch venv, bracketed full suite (timeout 1800), failure classification at 784e446, CRO-01 phase verdict (wave 2, has a blocking-human checkpoint) — HALTED: Task 1 checkpoint rejected; Tasks 2-3 not run; suite_verdict BLOCKED, phase_verdict BLOCKED

### Phase 2: GEX44 observed baseline

**Goal**: A second, independently produced observed baseline, from a Linux host whose sessions are mostly mission workers.
**Depends on**: Phase 1
**Requirements**: CRO-02
**Success Criteria** (what must be TRUE):

  1. `python3 tools/tis_report.py --observed --all-projects` (and `tools/tis_observed.py` directly if needed) runs on
     this host; state is MEASURED, MEASURED_ZERO or UNMEASURED and is reported as such.
  2. Per entrypoint (cli / sdk-cli): sessions, calls, median first-call context, `startup_shared_share_median`,
     cache-write 1h share, API-rate-equivalent $ over 7 days with the pricing file named.
  3. The GEX44 figures are set beside the laptop's (1.9 % sdk-cli / 16.4 % cli first-call shared prefix; 79.9 % 1h
     cache writes) and the comparison states which differences the instrument can and cannot explain.
  4. Evidence file written; no code changes unless a tool defect is found, in which case it gets a failing test first.

**Plans**: 1/1 plans executed

Plans:

- [x] 02-01-PLAN.md — tracer: pre-checks + tis_report --observed --all-projects on GEX44 transcripts; by_entrypoint.py reproducer (selftest, reconciled vs tis_observed / tis_report / budget_monitor) for the per-entrypoint table; laptop comparison with can/cannot-explain; defect record; CRO-02 verdict (autonomous, wave 1)

### Phase 3: P3 pre-flight P0

**Goal**: Decide, without spending model calls, whether the predeclared ablation (`vault/plans/cognitive-resource-os-P3-ablation-protocol.md`) can run an arm WITHOUT ~/.claude/rules while touching neither global config nor credentials.
**Depends on**: Phase 1
**Requirements**: CRO-03
**Success Criteria** (what must be TRUE):

  1. Candidate mechanisms enumerated from `claude --help` / documented flags on the installed version
     (e.g. setting sources, config dir, append/replace system prompt) — each with what it changes and what it touches.
  2. Each candidate judged against the protocol's P0 clause; a mechanism that needs a copied credential or an edited
     global file is REJECTED, with the reason.
  3. Verdict is exactly one of PASS (named mechanism) or STOP (per protocol: do not improvise). No ablation run in this workstream.

**Plans**: TBD

### Phase 4: Prefix cache-miss A/B

**Goal**: Test the unmeasured hypothesis that a new session misses the previous session's cached prefix because the tool list varies with MCP.
**Depends on**: Phase 2
**Requirements**: CRO-04
**Success Criteria** (what must be TRUE):

  1. Pre-check recorded: no `ANTHROPIC_API_KEY`; credentials are claudeAiOauth. Otherwise BLOCKED.
  2. Arm A: two back-to-back `claude -p` runs in one scratch dir with an identical short prompt. Arm B: the same with
     `--strict-mcp-config` and an empty MCP config. Exactly 4 runs, cheapest model the protocol allows, output discarded.
  3. For each run, first-call `cache_read_input_tokens` and `cache_creation_input_tokens` read from its transcript via
     tis_observed (not from CLI stdout). The run-2 vs run-1 reuse is compared across arms.
  4. Verdict: hypothesis SUPPORTED / REFUTED / UNJUDGED (with why). n=2 per arm is stated as a limit, not hidden.

**Plans**: TBD

### Phase 5: Seal and hand back

**Goal**: The laptop session can pick up everything this run learned from the branch alone.
**Depends on**: Phase 3, Phase 4
**Requirements**: CRO-05
**Success Criteria** (what must be TRUE):

  1. `vault/plans/cognitive-resource-os-RESUMPTION.md` updated: sealed list, verdicts of phases 1-4, next three actions.
  2. `vault/knowledge_base/ukdl-cognitive-resource-os.md` gains entries only for findings with evidence (none invented).
  3. All work committed on `mission/cognitive-resource-os` in this clone; `git status` clean for this workstream's paths.

**Plans**: TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Gate verdict on the big host | 2/2 | Blocked (CRO-01: rerun 01-02 pending Owner) | - |
| 2. GEX44 observed baseline | 1/1 | Complete    | 2026-09-28 |
| 3. P3 pre-flight P0 | 0/? | Not started | - |
| 4. Prefix cache-miss A/B | 0/? | Not started | - |
| 5. Seal and hand back | 0/? | Not started | - |
