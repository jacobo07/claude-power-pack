# State-centric cognition — reality scan (2026-10-02, IN PROGRESS)

Mission: the Owner's `/ultra plan` "conversation-centric -> state-centric cognitive computing"
(durable Goal state authoritative, context compiled per invocation, workers disposable).
Status: REALITY SCAN, ownership sweep half done. **No plan presented, nothing approved, nothing
implemented.** Iteration file read (iteracion-avanzada-universal.txt). Evidence base:
`vault/plans/weekly-limit-burn-rca-2026-10-02.md`, backlog `vault/backlog/2026-10-02_weekly-limit-burn-followups.md`.

## Verified state at scan time

- Branch `feature/knowledge-acquisition`, HEAD `7982155`; ~690 dirty paths from other panes.
- Rollover: active since 09-28; economic trigger `139b19d` + Ralph exclusion `65bb95b` LIVE in the
  Stop-chain (repo file is executed by `~/.claude/hooks/hook-dispatcher.js:231`). Savings UNMEASURED.
- Floor (one-call probes, measured): 91.3k empty dir / 111.6k in this repo; skills 5.8k, MCP 3.0k
  measured; global CLAUDE.md+rules ~29k ESTIMATED; ~53k residual DERIVED (not decomposed).
  `--bare` cannot run on the subscription login ("Not logged in").

## D2A family run (deterministic, lexical)

`d2a_engine.py --family-file` over 15 decomposed systems: 1 FOLD (Durable Goal State -> repo_identity,
almost certainly a vocabulary false match), 14 DEFER = UNKNOWN. Not usable as an ownership verdict;
the manual sweep below is.

## Ownership sweep so far (read from module docstrings)

**The Goal spine already exists: `modules/gsd_x/goal/`** (plan in KobiiCraft
`vault/plans/kseip-goal-spine-v1-20260922.md`):
- `log.py` append-only goal event log = THE durable record (`~/.claude/state/gsd-x/goals/<repo>/<goal>/`)
- `contract.py` goal identity + revision · `brief.py` epoch brief compiled from durable state only
- `epoch.py` bounded epochs + provider contract + receipts · providers `claude`, `codex`, `gate`, `long_run`
- `reconcile.py` next step as a pure function of durable state (zero-LLM) · `sweep.py` unattended driver
- `judge.py` re-runs pinned gates before certifying · `git_state.py` evidence pinned to a tree
- `evidence.py` negative knowledge across executors · `intervention.py` operator events in the log
- `workspace.py` portable workspace capsule · `convergence.py` obligations/planes/closure
- `mission/` obligations, structured facts, coverage, closure, store.

**Reality: 3 goals ever** (g-001 100 events, g-002 4 events, ksr-p2w25 0 events); last activity
2026-09-25. `reachability.py` lists `gsd_x/goal/*` as ORPHAN. None of the 23,925 incident calls ran
through it. => Planes 1-4 (state, delta/epoch, event log, packet-from-state) are CONNECT/EXTEND,
not NEW. The gap is that live work (interactive panes, Ralph missions, subagents) does not route
through the spine.

Other owners found:
- `tools/gsd_mission.py` (mission outlives session) + `tools/gsd_epoch.py` (fresh-worker rotation;
  444/499 launches were turn-ends) + `tools/gsd_long_run.py` — the LIVE long-run path.
- `modules/capability_runtime/` — ACV: `agent_spec`, `agent_resolver`, `agent_bundle` (proof bundles),
  `applicability`, `invocation`, `retirement` => Agent Context Firewall is EXTEND.
- `modules/cognitive_os/` CO-00..CO-12: `memory` (Hot/Warm/Cold tiers), `gc` (eviction policy),
  `governor` (budgets), `scheduler` (CO-08 hot-session cap: decide LIVE, enforcement ABSENT),
  `router` (cheapest-first cascade = admission control), `registry` (zero-token asset reuse),
  `hibernation`, `loop_budget` (loop/subagent admission), `economics` (WU/MTok).
- `modules/contract_fabric/side_effect_ledger.py` (undeclared side effects) + `tools/test_side_effect_ledger.py`.
- `modules/session_delta/` (post-session learnings producer).
- `tools/rollover.py` + `tools/rollover_econ.py` (interactive fresh epochs).

**Concurrent owner alert:** `modules/cognitive_os/scheduler.py` cites
`vault/plans/cognitive-control-plane-2026-10-02.md` (verified today by ANOTHER pane). Read it before
proposing any scheduler/budget work — it may already own Planes 17/18/31.

## Sweep completed (session 969d8063, 2026-10-02, after RESUME_CERTIFIED)

**Cognitive Control Plane (CCP) is a peer program, Owner-APPROVED, executing in another pane**
(`vault/plans/cognitive-control-plane-2026-10-02.md` + `-RESUMPTION.md`; C0 `19a7bc5`, C1
`286ccbe`). It OWNS: burn monitor / usage index, fan-out ledger (C2), estate governor CO-08 shadow
(C3), agent floor + model policy (C4), in-agent growth (C5), rollover observation (C6), bounded
backpressure (C7). Its P0 measured that subagents do NOT inherit the parent transcript (0/219) —
the state-centric "context firewall" plane is therefore REJECTED, not deferred. This mission must
not edit any CCP surface, `tools/rollover.py`, `context-watchdog.py`, `tools/gsd_mission.py` or
`hooks/agent-solo-guard.js`.

Remaining owners (grep, 2026-10-02):
- singleflight: only local idioms (`context-watchdog.py`, `night_research_runner.py`); no shared
  primitive. Not a gap this mission needs.
- verification reuse: the goal spine already pins gate identity + tree hash (`git_state.py`,
  `judge.py`, plan GAP-5/GAP-7). EXTEND there, nothing new.
- event waits: no shared primitive (`monitoring/monitor.py`, `cpc_os` savers, harness Monitor).
  Out of scope.
- HCMH: ABSENT, doctrine only, Owner ruling open (`specs/agent-capability-virtualization.md:174`).
- Graphify: LIVE (GK-12 advisory fired on this session's PowerShell calls).

**Why the goal spine is orphaned (measured):** no hook, command or scheduled task calls
`modules/gsd_x/goal/*` or `tools/gsd_x_goal.py` (grep over hooks/, commands/, scripts/,
`tools/gsd_long_run*.py`, `tools/gsd_mission.py` = 0). Its own sweep (`goal/sweep.py`) needs a
precondition record; `~/.claude/state/gsd-x/autonomy_gates.json` exists (2026-09-22) but nothing
schedules the sweep. Other importers are research corpora (`keos_qwen`, `uwcp_*`), not live work.
Plan C12 (sweep hook) and K2/C15 (G-001, G-002 convergence) of the goal-spine plan never landed.

## Next

Present ONE inline ULTRA-PLAN (CONNECT-first, CCP-disjoint) with the six Q&A questions; wait.
