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

## Plan of record (Owner "y", six defaults, 2026-10-02)

S1 re-record autonomy gates · S2 schedule the goal sweep (gate epochs only) · S3 bind Ralph
missions observe-only · S4 finish G-001 · S5 G-002 transfer -> L3 · S6 proposal to the rollover
owner (no edit). Defaults: goal spine is the only state store; model-calling epochs wait for the
2026-10-07 17:00Z reset; Ralph read-only; done = L3, L5 excluded.

## Progress

- **S1 SEALED.** `c4c45b7`: the autonomy record is pinned to `engine_identity` (digest of the
  engine's discovered import closure, 49 files) instead of repo HEAD; HEAD moved every 7.6 min
  (median), the closure 43 times in 336 commits / 7 d. `7d5b3bd`: two mutation drills were
  INVALID before this work (stale anchors after `0ff7cf7`, `fe2be9c`), repaired, plus two engine
  mutants: 56/56. Record GREEN on engine `9114b69a`; `autonomy_verdict` = True.
- **S2 BUILT** (Owner "b"): `61914f9` (SPEC-GOAL-SWEEP-SCHEDULED) `autonomous --on --root`,
  `sweep-all` discovering goals from the store, heartbeat on every run, engine retry key;
  `tools/goal_sweep.ps1` + Windows task `PP-GoalSweep` (5 min, hidden, lease, bounded stage).
  Mutation drill 56/56; record re-earned at `61914f9`. G-001 marked autonomous with its root;
  first manual pass dispatched `ep-0954eedea9fe` (ob-evidence).
- **CORRECTION:** the claim below that "zero goals carry `goal.autonomous`" was a FAILED LOOK,
  not an absence: G-001 already held a root-less legacy autonomy event. The PowerShell probe
  printed two object shapes into one table and the second query's rows never rendered.
  `autonomous_goals()` found it and named it ("no root recorded").
- **S2 findings (original, superseded):** zero goals carry `goal.autonomous`, and the store records no
  root path, so a scheduled sweep has nothing to enumerate. G-001's seven obligations were all
  proven at KobiiCraft tree `b0dd193`; the worktree is now at `af38161` (no change inside its
  scope paths since 09-22), so G-001 needs only a RE-GATE, zero model quota. But `ob-reality`'s
  gate (`scripts/goal/gate_lobby_hotbar_live.py`) drives a bot through the PRODUCTION proxy
  (read-only). Marking G-001 autonomous = unattended production contact on every worktree move:
  Owner decision pending.

- **S2 LIVE (observed):** scheduled run 2026-10-02T19:15:47Z (`PP-GoalSweep`, rc 0) harvested
  `ep-0954eedea9fe`: ob-evidence SATISFIED at the current tree (`GOALRCPT_PASS=4/4`), with
  nobody attending. `ob-reality` had no gate class (accepted before the class rule), so the sweep
  would have refused it forever; re-accepted 19:2xZ as `in_game` (the script's own docstring:
  "the in-game gate", read-only), same text/gate/files, actor `claude` under Owner "b".

## Next

1. **S4 DONE.** The scheduler re-proved all G-001 obligations unattended 19:14Z-20:30Z
   (`ob-reality` `GOALLIVE_PASS=4/4`, real bot through the production proxy); READY_FOR_JUDGE at
   20:30Z; judge PASS recorded 20:44:47Z (34 s, every pinned gate re-run); status `may_close=True`,
   0 blocking at KobiiCraft tree `af38161`. Written up in `wiki/` (Owner: "use the research we did
   for the wiki"): [[goal-spine-connect-not-build]] and 5 more pages; next step proposed there:
   `wiki/improvements/spec-acceptance-as-goal-obligations.md` (spec acceptance -> goal
   obligations, done = judge PASS), drawn from the SDD-OS and CBR gap analyses.
2. **S3 BUILT** `738ed40` (SPEC-GOAL-OBSERVE-RALPH): `bind-mission` adopts a running Ralph
   mission observe-only (cancel refused, record bytes untouched, probe adopts via marker); the
   sweep observes/harvests/recovers every provider's epochs. Bind suite 10/10, mutation 58/58,
   record re-earned. Production proof PENDING an Owner goal: running missions are
   `m-9955845c3eaa` (KobiiCraft, `luckyarena-arena1`: same repo as G-001 but unrelated work,
   and binding would hold G-001's single epoch slot), `m-4c6125338df1` (CPP, `ucep`, no CPP
   goal), `m-129ddae5ccf3` (InfinityOps, no goal). A goal's intent is the Founder's words.
   Observed bonus: while engine files were dirty (my edits, the mutation drill) every scheduled
   pass REFUSED with a named reason -- the sweep cannot run unverified code or a mutant.
3. **S6 DELIVERED** (2026-10-03): `vault/proposals/2026-10-03_idle-return-rollover.md`. It corrects
   A1: a capsule older than 30 min fails SAFE_TO_FORGET (`rollover.py:403`), so `/kclear` after
   the gap is itself the cold rewrite. The $541 is only reachable by a UserPromptSubmit block
   plus a handoff-less capsule, which is a quality-authority change for the owner to decide.
4. **TOKEN-ECONOMY RESEARCH (Owner: "expand the research on token saving ... massive evolution",
   2026-10-02), IN PROGRESS.** Measured (7 d to 2026-10-02T20:48Z, `wiki/tools/token_economy_*.py`
   + `.out`): $8,312 API-equiv; cache read 54 %, cache WRITE 33 %, output 13 %; main thread 72 %
   (ctx p50 305k); Opus 85.7 %; cold first calls 13.2 %; 508 one-call sdk probes 4.9 %; mid-session
   prefix rebuilds 8.1 %. Upper bounds: floor -40k 12.6 %, 1h->5m TTL 9.6 % (97.8 % gaps <= 5 min;
   TTL is harness-chosen, not in settings), main ctx cap 150-200k 7-9 %, subagents->Sonnet 3.8 %
   (price table gives Opus/Sonnet equal cache_read: verify). USD != meter (CCP C1 G6).
   Two research agents write `wiki/raw/2026-10-02-token-economy-external-research.md` and
   `...-internal-inventory.md` (check they are complete; re-dispatch only the missing part).
   Then: wiki synthesis ranking levers (share x evidence tier x owner CCP vs this mission),
   improvement pages for unowned levers, source pages, index, log. Also inspect
   `vault/specs/parent-context-epoch-rotation.md` (unread owner).
   **SYNTHESIS WRITTEN** (2026-10-02, session ab73b303): `wiki/syntheses/token-economy-levers.md`,
   two source pages, four IDEA pages (tool-output-at-source, mid-session-prefix-rebuilds,
   sdk-probe-floor, rtk-powershell-gap), overview point 8. Price table verified against documented
   multipliers; sonnet-5-5 priced by family fallback. Next: Owner picks which IDEA to pursue;
   `mid-session-prefix-rebuilds` is zero-quota and read-only. Spec
   `parent-context-epoch-rotation.md` still unread.
   **WAVE 2 WRITTEN** (Owner: "next level research and massive brainstorming"):
   `wiki/syntheses/token-economy-brainstorm.md` + raw research-2 + six zero-quota instruments
   (`wiki/tools/token_economy_{deep,listings,coldstart,coldstart_bydir,prefix_stability,ttl_net}`).
   Key: session starts write 85-91 % fresh (<= 12.4 %); 73 % of rebuilds = idle > 1 h; 5 m TTL
   net +$1,262 (refutes wave-1 row); 280/319 skills never invoked. S6 proposal should carry
   idle-return rollover (A1). Next: Owner picks; A3 experiment needs quota.
