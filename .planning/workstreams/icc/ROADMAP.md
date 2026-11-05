# Roadmap -- icc (v1): state-centric cognitive runtime, continuation of GPF / Cognitive Economy / CCR

Authority: `vault/plans/icc-state-centric-2026-11-05.md` (Owner `y go ICC`, 2026-11-05; plan commit da0edf96). Its Reality
Scan section is settled: do NOT re-scan owners it already states. EXTEND existing owners only; no new subsystem.
PLANE: laptop DESKTOP-PMT5BS8, main tree `C:\Users\User\.claude\skills\claude-power-pack`, branch feature/knowledge-acquisition.
SHARED TREE: ~1,270 dirty paths belong to other panes. Commit ONLY your own paths:
`git commit --only -F <msg> -- <files>`, then verify `git log -1 --format=%s`. Never push. Never stage `CLAUDE.md` (foreign edit).
git = `C:\Program Files\Git\cmd\git.exe`; python = `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`.
Use PowerShell (Bash may 127 in panes opened before 2026-11-05). PS 5.1: write scripts to files, never `bash -c` quoting.
EXECUTION mode, small scopes. Plan each phase inline. Do NOT dispatch gsd-planner / gsd-phase-researcher subagents.
At most 2 bounded subagents in parallel, each with files, question, bound, output path.
HR-001: no write under `~/.claude` outside this repo (settings, ~/.claude.json, rules, hooks) without a separate Owner go:
write the exact command into `vault/programs/icc/OWNER_STEPS.md`, mark the phase BLOCKED-ON-OWNER in STATE.md, continue others.
HR-2: a CCR release without a green smoke from the same commit is rolled back (`python tools/ccr_release.py rollback`).
Before any CCR release: `python tools/hardrule_compile.py --class DEPLOY`. 3+ files changed -> pp-code-reviewer before commit.
Every new gate gets a mutation drill that must go red. UNKNOWN / UNMEASURED are never PASS. CACHED is not ELIMINATED.
Recorded-plane chars (transcript attachments) are NOT request-plane tokens: label every figure with its plane.
Measure spend after each phase: `python tools/mission_spend.py session-tree --session <your sid>` -> STATE.md.
Breaker: two consecutive 5M intervals with no causal commit -> write METHOD_PIVOT_REQUIRED in STATE.md and stop.
Harness rules for live probes (GPF): pin `--session-id`, reader thread on the pty, never plan mode, `/exit` only after end_turn,
`--allowedTools=X` form (the space form swallows the prompt). Driver precedent: `vault/programs/ctx-rent-x/phase5_smoke.py`.

## Phases

- [x] **Phase 1: W0 Request-plane floor truth (early-value checkpoint)**
- [ ] **Phase 2: W1 Capability virtualization of deferred tool names (CCR canary)**
- [ ] **Phase 3: W2 Instruction elimination in repo CLAUDE.md (conditional)**
- [ ] **Phase 4: W3 Model-call accounting + Zero-Model Fraction + zero-model closeout**
- [ ] **Phase 5: W4 Agent semantic-delta return (agent_bundle on one real path)**
- [ ] **Phase 6: W5 Context Policy Regret + floor CI on the request plane**
- [ ] **Phase 7: Closeout: UKDL, Error->Immunity, Baseline Ratchet, fresh-agent test, final handoff**

## Phase Details

### Phase 1: W0 Request-plane floor truth
**Depends on**: nothing. P50 4M, ceiling 6M.
- A1: single-variable probes, `claude -p --model haiku` one short prompt, n=3 per arm, pinned session ids: control;
  `CCR_MAIN_CANARY=0`; `--strict-mcp-config --mcp-config <empty json in scratch>` (no MCP servers). Read call-1 usage from
  each transcript. Output `vault/programs/icc/floor-request-plane.json` + a table: marginal tokens per layer (canary-stripped
  listings, MCP names+instructions), the residual hard floor (system prompt + built-in tool schemas). Label planes.
- wake_check / floor gate: the caller that picks "newest transcript by mtime" pins a session id instead (or refuses when two
  candidate sessions are live); regression test red on HEAD, green after.
- COMPAT miss surfaced: when the CCR start receipt says `compatible:false`, SessionStart prints one line naming the host
  version and the reprobe command (in-repo code only; find the existing SessionStart owner, do not add a new hook file
  outside the repo). Test both poles.
- GEX44 (ssh `~/.ssh/kobicraft_gex44`, read first): list dangling doctrine pointers in GEX44 `~/.claude/CLAUDE.md`; write a
  GEX44 resident budget file in this repo; attribute the -13,786 by layer from GEX44 transcripts (floor_regression_gate there).
  Any write to GEX44 `~/.claude` = OWNER_STEPS entry, not done by you.
- **Acceptance (early-value):** request-plane table committed within 6M cumulative, else METHOD_PIVOT_REQUIRED.

### Phase 2: W1 Capability virtualization of deferred tool names
**Depends on**: Phase 1. P50 7M, ceiling 10M.
- `mods/cpp-cognitive-runtime/hooks/policy.ts` + `register.ts`: extend the main-lean canary to `deferred_tools_delta`:
  collapse `mcp__<server>__*` names to one line per server with its count + a ToolSearch hint ("query by keyword or
  select:<name>"); built-in deferred names stay listed. Kill switch `CCR_DEFERRED_NAMES=0`. Shadow first (receipt carries
  before/after chars), then enforce. Test poles in policy.test.ts; mutation drill.
- Quality task (must stay correct): the model is asked to use a named deferred MCP tool (read-only, e.g. a github get_me or
  vercel list_teams) and must find it via ToolSearch. n=10 per arm ON/OFF interactive haiku; correctness + call-1 + processed.
- Elasticity bench: synthetic +10x / +100x skills/agents/MCP-name estate in a scratch HOME or --plugin-dir; call-1 delta per arm.
- Release via `tools/ccr_release.py`, HR-2 smoke, keep or roll back.
- Acceptance: request-plane call-1 reduction measured, quality non-inferior, elasticity table.

### Phase 3: W2 Instruction elimination (conditional)
**Depends on**: Phase 1. P50 3M, ceiling 5M.
- Only if `git status -- CLAUDE.md` is clean (the foreign edit landed). Else mark DEFERRED-FOREIGN-WRITER and skip.
- Move the per-skill "Activation Criteria" blocks of the repo CLAUDE.md into their skills' SKILL.md / a routed page, keep a
  one-line pointer each. Measure call-1 (n=4/arm, counterbalanced) and quality 6/6 (GPF-L2 quality driver).

### Phase 4: W3 Model-call accounting
**Depends on**: Phase 1. P50 5M, ceiling 8M.
- Extend `tools/cognitive_admission.py` / `tools/mission_spend.py` (do not create a new meter): per-obligation model-call
  receipt derived from transcripts + mission ledgers; report calls per obligation and Zero-Model Fraction by Work Class.
- One zero-model closeout path: a mission whose done-gate command passes is closed by the supervisor without a model turn
  (find the existing COMPLETED path in gsd_mission.py first; extend it). Live evidence on one real mission record.

### Phase 5: W4 Agent semantic-delta return
**Depends on**: Phase 1. P50 5M, ceiling 8M.
- Wire `modules/capability_runtime/agent_bundle.py` (proof-bundle-v1) into one real reviewer return path; measure parent
  context growth (tokens added to the parent per review) vs prose return on >= 3 real reviews each.

### Phase 6: W5 Context Policy Regret + floor CI
**Depends on**: Phases 1-2. P50 4M, ceiling 7M.
- Regret = actual carriage - offline Belady bound (`tools/ctx_rent.py`), per Work Class, on >= 3 real transcripts.
- `vault/programs/global-prefix-floor/resident_budget.json` gains request-plane listing layers; the floor gate fails on growth.

### Phase 7: Closeout
**Depends on**: all. P50 3M, ceiling 4M.
- UKDL entries (recorded-vs-request plane trap; silent shadow on host update; others proven). Error->Immunity rows.
- Baseline Ratchet assessment; fresh-agent recovery test; master done-gate mapping (plan section) with each deferred item's NPV.
- Final handoff per the Owner contract; update `vault/programs/global-prefix-floor/RESUMPTION_FILE.md` Start line.
