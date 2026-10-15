# Roadmap: CCR v5 Stage A — Execution-vehicle repair

Plan of record: `vault/plans/ccr-v5-vehicle-repair-2026-10-15.md` (Owner `approve p95`, packet
`ccr-v5-stageA-2026-10-15.json` sha 25b5bd9f86e2, applied 2026-10-15; programme `ccr` 213,000,000; lease **L14**
`ccr:v5-stageA` cap 12,000,000 incl. recovery reserve 1,000,000). The measured incident truth is in section 1 of the plan:
read it, do not re-derive it.

Principle: budget is authority, not guidance. A model may request a reforecast; it may never grant itself authority.

## Operating constraints (every phase) — BINDING

- **MAIN THREAD ONLY.** Do NOT spawn subagents (no gsd-planner, gsd-executor, gsd-plan-checker, gsd-verifier,
  general-purpose, Explore). Plan and execute each phase inline, overriding the GSD default. Measured cause of the
  80M incident: subagents = 79% of spend; one gsd-planner = 157 calls / 24.0M.
- One plan per phase, at most 2 if the phase truly splits. Each plan's tasks are small. Commit after each task.
- Work tree: `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\ccr-v5`, branch `ccr/v5`. Commit
  pathspec-scoped (`git commit -F <msgfile in $env:TEMP> -- <paths>`). The main tree is SHARED: never edit it.
- Git: `& 'C:\Program Files\Git\cmd\git.exe' -C <repo>`. Python: `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`,
  `$env:PYTHONIOENCODING='utf-8'`. PowerShell, not Bash.
- Never edit `~/.claude/settings.json`, `~/.claude/CLAUDE.md`, `~/.claude/rules/`, credentials. Hook changes only
  inside code already reached by the registered `hook-dispatcher.js` chain (`mission_wall.js` is registered). Anything
  needing a new registration = OWNER STEP written to EVIDENCE.
- The code under change lives in THIS worktree (`tools/`, `hooks/`). Its live copy in the main tree is NOT changed
  here: landing it is Stage B. Tests run against the worktree copy.
- Never run `goal-correct`. Ledger changes are append-only `goal-settle` rows.
- No push. No game servers. Do not touch mission m-a43d0aa7ce28 (held; its release is Stage B).
- Never ask the Owner: write blockers into the phase EVIDENCE.md, mark BLOCKED, continue with independent work.
- Every phase ends with EVIDENCE.md: commands, exit codes, observed output, verdict PROVEN/OBSERVED/UNJUDGED/BLOCKED.
  Apply `C:\Users\User\Downloads\Promptsss\Prompts pa iterar\Universal\iteracion-avanzada-universal.txt` at phase end.

## Phases

### Phase 1: Hard enforcement (route 4.5M) — DONE 2026-10-15 (5bfce1df, abbb9322, d8390521; phases/01-hard-enforcement/01-EVIDENCE.md)
- Per-phase lease in the mission record: `{phase, forecast, warn 1.2x, hard 1.5x, reserve}`. Writable only by `envelope`
  (CAS), never by the worker. Phase spend = processed since the phase's start (`gsd_epoch`/ledger cost marks keyed by the
  GSD phase read from STATE/ROADMAP). An unknown or ambiguous prior-phase accounting = BLOCKED, never permission.
- The sweep (`gsd_mission.py supervise`) trips at hard: owner hold + stop the worker. The successor gets a
  reforecast-only packet.
- In-turn hold: `hooks/mission_wall.js` (PostToolUse/PreToolUse path already registered) reads a hold flag file and
  denies further tool calls for the worker and its subagents. This closes the 5-minute sweep gap.
- Subagent cap: per agent type (default 30 calls / 3M processed; PGO overrides). Enforced in the same hook by denying
  the subagent's tool calls past the cap.
- Fault-injection tests: phase at hard while the model "wants to continue" -> stopped; ambiguous prior phase -> BLOCKED;
  subagent past cap -> denied; hold flag -> denied; control: under cap -> allowed.

### Phase 2: Accounting authority (route 2.0M)
- On reap/stop the supervisor settles every worker session (main + subagents, deduped by message id) with
  `goal_settle`, tagged with mission/epoch. Test: a breaker-stopped worker is booked exactly once.
- The coordinator d124ce03's v5 share: measure its transcript between 2026-10-14T21:00Z and Stage A arm, minus what L12/L13
  already hold for it. Book it to ccr if not booked. Record the method.
- Derived estimate: `arm`/`envelope` compute the token estimate from open roadmap routes. Authority above the lease
  remainder minus reserve is refused. Test both.
- No double charge: coordinator + worker on the same goal -> each session booked once (test).

### Phase 3: Type-safe completion, worktree MCP, compaction (route 2.0M)
- `gsd_mission.py:4274-4290`: a packet injected by recovery onto a workstream mission is a `unit`. Its receipt DONE
  relays to the roadmap; COMPLETED only when the composition contract (GSD all phases done) passes. Completion receipts
  carry `{type, id, parent, residual}`. Fault test: unit DONE with residual phases -> mission stays open; control: packet
  mission armed as unit -> completes.
- Worktree MCP at arm: detect inherited `.mcp.json` servers without approval for the cwd. Same git-common-dir as the
  approving repo -> write the worktree `.claude/settings.local.json` mirroring that repo's decision. Otherwise refuse arm
  with the remedy. Tests for both branches.
- Compaction: test that processed spend before a compact boundary stays counted by the breakers.

### Phase 4: Canary and reforecast (route 1.5M)
- A real `claude --bg` mission on a toy unit in a scratch worktree with phase cap 400K. It must be stopped within cap +
  one sweep. A deliberately spawned subagent must be denied at its cap. Record measured spend vs cap.
- Stage B reforecast from measured per-call cost: Phase 3 residual (03-02 summary, 03-03..03-06), A7 read-out, main merge.
  Write `vault/plans/ccr-v5-stageB-reforecast.md` with P50/P80/P95 and the capital packet draft. Do NOT apply it.

### Phase 5: Knowledge and close (route 1.0M)
- UKDL HR/PR/Traps (deduplicated) for the confirmed classes: PHASE_STOP_LOSS_MODEL_OVERRIDABLE,
  SUBAGENT_SPEND_UNGOVERNED, BREAKER_THRESHOLD_CHOSEN_NOT_DERIVED, BREAKER_STOPPED_SESSION_UNBOOKED, UNIT_DONE_CLOSES_MISSION,
  WORKTREE_MCP_APPROVAL_MISSING. Record also the falsified claims (no same-session runaway; 25.1M was real; DEFLATE not
  global). Write them in this worktree only.
- DEFLATE policy note: keep as-is; ablation moves to Stage C.
- Final EVIDENCE + HANDOFF.
