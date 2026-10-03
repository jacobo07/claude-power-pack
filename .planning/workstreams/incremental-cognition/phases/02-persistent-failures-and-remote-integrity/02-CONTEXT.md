# Phase 2: Persistent failures and remote integrity - Context

**Gathered:** 2026-10-03 (GEX44, orchestrator pre-research; discuss skipped via workflow.skip_discuss)
**Status:** Ready for planning
**Mode:** Auto-generated from ROADMAP + measured evidence below. Pillars C then B (ledger ids).

<domain>
## Phase Boundary

Goal: an authorization-class failure parks a mission instead of relaunching; a GEX44 launch proves its
environment first.

Success criteria (ROADMAP):
1. Red test of the 137-relaunch shape (worker dies on `Login expired` before any API call) -> fix -> green.
2. GEX44 a5/a7: rules version, hook health and interpreters checked by a repeatable preflight; broken hooks and
   stale rules repaired by a deploy script; re-login recorded in the owner bundle, never bypassed.

Frozen pillar rules (ledger `vault/programs/incremental-cognition/ledger.json`, immutable):
- **C** (owner `tools/gsd_mission.py`): "A worker that dies on an authorization-class failure (Login expired)
  parks the mission in a non-relaunching state until a qualifying precondition change; red test reproduces the
  137-relaunch shape." Predicted IMPLEMENTED_AND_VERIFIED.
- **B** (owners `tools/gsd_mission.py`, `tools/gsd_x_runtime_preflight.js`): "Preflight before a remote launch
  proves auth readiness, rules version, hook health and interpreters, or refuses with a typed reason; stale rules
  and broken hooks are repaired by a repeatable deploy, never hand copying; re-login itself is an Owner action."
  Predicted IMPLEMENTED_AND_VERIFIED.
</domain>

<evidence>
## Measured on GEX44, 2026-10-03 (read-only; reproduce with the commands named)

### The 137-relaunch shape (pillar C)
- a7 env: `~/a7-env/` (HOME=`~/a7-env/home`, own node/npm, sweep `~/a7-env/mission_sweep.sh` every 5 min via
  crontab, runs `$HOME/.claude/skills/claude-power-pack/tools/gsd_mission.py supervise --actions-only`).
- Sweep log `~/a7-env/home/.claude/state/gsd-mission-sweep.log`: from 2026-10-01 22:45 mission
  `m-1f344b8bc428` (renewal 1 of lineage `m-839353decb65`, ws `luckyarena-arena7`) relays every 10 min
  ("owner's turn ended without completion: host lists session idle", `gsd: OK`, no `held`) until
  `iterations 48 >= max 48`; then renewed as `m-677f1ae19a43`, which burned another 48. 96+ relaunches, 0 work.
- Every worker transcript (e.g. `~/a7-env/home/.claude/projects/-home-kobii-kobii-a7/71e107ea-3171-4da7-b4bb-aedbc33d3f78.jsonl`,
  39 rows) has exactly ONE assistant row: `model: "<synthetic>"`, text `Login expired · Please run /login`,
  usage all zeros, turn_duration 418 ms. Job timeline: `{"state":"blocked","detail":"Login expired"}`.
- **Root cause, measured:** the a7 PP install (`~/a7-env/home/.claude/skills/claude-power-pack`, git checkout,
  HEAD `0119999` 2026-09-27 23:34) PREDATES `tools/provider_breaker.py` (`6fedb1d4`, 2026-09-28). Its
  `gsd_mission.py` (line ~1183) only calls `quota_hold_from_transcript` -> an auth refusal is not a quota ->
  relay. `python3 -c "import provider_breaker"` in that tools dir: ModuleNotFoundError.
- **Current code already classifies the real transcript:** with this repo's `tools/`,
  `provider_breaker.worker_outcome(sid, find=lambda s: <that jsonl>)` ->
  `{'class': 'auth', 'text': 'Login expired · Please run /login', 'at': 1790915703.852}`, and `decide()` returns
  QUARANTINE for AUTH. `python3 tools/test_provider_breaker.py` -> 18/18.
- **Remaining C gaps in current code (the fix targets):**
  1. `gsd_mission.provider_hold` fallback (breaker import fails) checks quota ONLY -> an auth refusal relaunches.
     `V-BREAKER-UNAVAILABLE-IS-VISIBLE` asserts the fallback is visible with `hold=None`. A missing breaker must
     still park on an auth-class host reply (minimal hunk in gsd_mission.py; keep the ledger row).
  2. "until a qualifying precondition change": today an AUTH quarantine clears only by
     `provider_breaker.py clear`. A re-login rewrites `$HOME/.claude/.credentials.json`; a credentials change
     AFTER the quarantine evidence is a qualifying precondition change (un-park), while an unchanged file keeps
     the park. Decide where this lives (breaker `decide`, injected reader, no secret read: mtime + expiresAt only).
  3. Renewal: the lineage was RENEWED after 48 dead iterations ("no progress" check did not stop it). Check
     whether a parked/quarantined mission can still be renewed; a renewal must not launder a quarantine.
- Red test = the real shape (synthetic `Login expired · Please run /login`, zero usage, no tool call) driven
  through `supervise` with injected seams (see `tools/test_gsd_mission.py` / `tools/test_provider_breaker.py`
  fixtures) -> relaunch observed (red) against the gap, park observed after the fix. Copy the transcript SHAPE
  into a fixture; never read the a7 file from a test.

### Remote environment integrity (pillar B)
- Credentials (shape only, never values; `cred_shape` style read of key names + expiry):
  a7 `.credentials.json` `claudeAiOauth.expiresAt = 0`, mtime 2026-10-01T22:45:02 (2 s before
  m-1f344b8bc428 launched), `refreshTokenExpiresAt` 2026-10-27. a5 and main: expiresAt 2026-10-03T22:06 (valid).
  => auth readiness must read `expiresAt` (0 or past = NOT_READY, typed `auth_expired`), never the token.
- PP install staleness: a7 PP checkout at `0119999` vs this repo HEAD; `~/a7-env/pp.head` records
  `01199995c7d15a9540dc4180c8f3a50d6e1244b3`, `~/a7-env/pp.bundle` exists (bundle-based deploy precedent).
  a5 env: `~/a5-env/` (same layout, `settings.linux.json`, `a5_linux.patch`).
- Interpreters: the main GEX44 node is v18.19.1; `plan_graph_check` refuses it (`engine: node v18.19.1 outside
  ^22.23.2 || ^24.14.0`) -> `tools/test_gsd_mission.py` V-MC-PLAN-FACTS-REFUSES-OVERLAP is red on GEX44 main.
  The a5/a7 envs carry their own node under `~/a?-env/node/bin` (check its version in the preflight).
- Stale rules / hooks: hooks on this host still inject Windows-only advice on Linux (e.g. the Woz
  "bare git is not on PowerShell PATH" card fires on every `git` Bash call on GEX44). Hook health = the
  dispatcher's chains are registered and their scripts exist and run under the env's node.
- `tools/gsd_x_runtime_preflight.js` exists (read-only, SATISFIED / UNMET / UNMEASURABLE, exit 0/1/2,
  `DEFAULT_GSD_LIB = 'C:/Users/User/.claude/gsd-core/bin/lib'` -- Windows default). Extend or call it; do not fork.
</evidence>

<decisions>
## Implementation Decisions

- **Run plane:** this GEX44 clone is NOT live. Editing `tools/gsd_mission.py` here deploys nothing. B and C each
  touch it in ONE minimal hunk, red test first. Reaching the laptop live file is an Owner-run fetch + deploy at
  >= 4 GB free (audit G6) -> `[B]`/`[C]` lines in `vault/programs/incremental-cognition/owner-bundle.md`.
- **Never** edit `~/.claude/**`, `~/a5-env/**`, `~/a7-env/**` from this phase (HR-001 + live sweeps run there).
  The deploy script is BUILT and TESTED here against a scratch env dir (tmp HOME with a fake PP checkout); running
  it on a5/a7 is an Owner action -> `[B]` owner-bundle line with the exact command. The preflight MAY be run
  read-only against a5/a7 to produce evidence (label `plane: gex44`).
- **Re-login** of a7 is an Owner action (interactive OAuth) -> `[B]` line. Never bypass, never copy credentials
  between envs.
- **Never read or print a secret.** Credentials: key names, `expiresAt`, mtime only (HR-SECRET-002).
- Preflight outcomes typed and four-valued like gsd_x_runtime_preflight (READY / NOT_READY(reason) /
  UNMEASURABLE); UNMEASURABLE never reads as READY. Refusal reasons are a closed set (e.g. `auth_expired`,
  `pp_install_stale`, `hooks_broken`, `interpreter_unsupported`, `unmeasurable`).
- Preflight wiring into launch: gsd_mission launch path refuses with the typed reason and a ledger row instead of
  launching; kill switch env var; fail-closed only on a measured NOT_READY, UNMEASURABLE is recorded and (decide
  and justify) does not churn.
- Every mutation drill restores the file and proves restoration (sha256).
- Program-owned paths: `vault/programs/incremental-cognition/**`, `.planning/workstreams/incremental-cognition/**`,
  new files the phase creates (tests, the deploy script). Commit by explicit pathspec only. Never push.
- Do NOT write `state.B` / `state.C` terminals in the ledger unless the pillar's frozen rule is fully met with
  `gate` + `prg` evidence; a PRG for C/B is laptop-plane or Owner-run (a real parked mission / a real deploy) ->
  record in the owner bundle and leave the terminal open. Write phase EVIDENCE.md (Product Delta + Intelligence
  Delta) under `vault/programs/incremental-cognition/evidence/`.

### Claude's Discretion
Module boundaries (new `tools/gex44_env_preflight.py` vs extending the JS preflight), test file names, CLI shape.
</decisions>

<code_context>
## Existing Code Insights

- `tools/gsd_mission.py` (2059 lines): `supervise` ~1333; relay/replace hold at ~1466-1490 calls
  `provider_hold(rec, now)`; `provider_hold` ~1863 (breaker, fallback quota-only); `quota_hold` ~1900;
  renewal + "no progress" check ~1440-1452; `align_cwd` / `CWD_ALIGN_BLOCKING` (pillar A, do not touch).
- `tools/provider_breaker.py`: classes quota/auth/transient/no_reply, `AUTH_RE`, `decide`, `hold_for`,
  `clear` CLI, ledger `provider_cleared`.
- Tests: `tools/test_provider_breaker.py` (18/18), `tools/test_gsd_mission.py` (212/213 on GEX44, the 1 red is
  the node-v18 plan-graph fact), `tools/test_gsd_epoch.py` (82/82), `tools/test_gsd_mission_cwd_align.py` (16/16).
  All must stay green (except the pre-existing node fact, which B's interpreter preflight explains).
- Python is `/usr/bin/python3`; node `/usr/bin/node` v18.
</code_context>

<deferred>
## Deferred Ideas

- Upgrading GEX44 main node to 22/24: Owner action (system package) -> owner bundle `[B]`.
</deferred>
