---
covers: [gex44-resident, goal-resident, resident-health, mission-record, recovery-census, cancel-by-handle, stagnation, F7, F8, F9, F10, F14, resident-isolated, work-dispatch, write-set]
status: APPROVED-BY-PLAN (kseip-p8-gdd-resident-20260924 §§28-34, 51-53; fixes F7-F10, F14)
owner: LANE RESIDENT (PP worktree factory/resident; NEW files only; never edits tools/gsd_x_goal.py
       or existing modules/gsd_x/goal/*.py — those belong to LANE GDD)
---

# GOAL RESIDENT (provisional working name) — the goal engine's supervised driver

## What it is and is not
A restartable driver of the EXISTING goal engine: each cycle it runs the engine's reconcile and
admission, dispatches through the engine's providers, and writes goal events only through the engine
API. It owns no goal truth, no judge, no second store, no second recursion. It is `sweep` made
resident, bounded and recoverable.

## Durable state (under a state dir from env GSDX_RESIDENT_STATE; default <goals_root>/../resident)
- `lock`: single-instance lock (O_EXCL file with pid + process start time; a stale lock is reclaimed
  only on positive evidence the holder is dead: pid absent OR start time differs).
- `heartbeat.json` (atomic replace): generation, pid, host, health, current goal@rev, mission id,
  provider, last_progress_ts, last_evidence_ts, budget snapshot, blockers.
- `missions/<id>.json` (atomic replace, CAS by a version field): identity, goal, revision, provider,
  provider attempt id, worktree, base commit, declared write set, pgid, process start time, scope unit
  name / claude bg id when present, state, uncertainty flags, created/updated ts. States:
  PROPOSED, ADMITTED, ISOLATED, DISPATCHED, RUNNING, RETURNED, HARVESTED, JUDGED, RECONCILED; terminal
  CANCELLED, EXPIRED, LOST, STALE_REVISION, UNCERTAIN, REFUSED (isolation or write-set refusal,
  evidence recorded on the mission). Illegal transitions raise.
- `intents.jsonl` (append-only): intent + provider attempt id written BEFORE any dispatch (F9).
- `gain.jsonl` (append-only): per goal per cycle, the information-gain verdict (F10).
- `leases/<resource>.json`: holder, heartbeat ts, TTL; expired leases are reclaimable (F14).
- STOP file: `<state>/STOP` — present ⇒ the loop exits cleanly after cancelling owned missions.

## Health (computed, never asserted)
HEALTHY, IDLE_NO_APPROVED_GOAL, RUNNING, WAITING_FOR_PROVIDER, WAITING_FOR_EVIDENCE,
WAITING_FOR_AUTHORITY, STALLED, DEGRADED, RECOVERING, FAILED. HEALTHY requires progress (gain) within
a configured window; an alive loop with no gain is STALLED, never HEALTHY.

## Cycle (bounded: max cycles per wake, max wall per mission, sleep bounds)
recover → load goals that are governed (authority.is_governed, when mode != ABSENT) and autonomous
and not paused → for each: engine reconcile → pick at most one mission per goal by the reconciler's
decision → admit (licence verdict, provider caps, leases, pause, stop file) → record intent → dispatch
via the engine provider → persist mission → observe/harvest on later cycles → hand receipts to the
engine (never judge itself) → gain verdict → heartbeat.

## Recovery census (F9)
On start: for every non-terminal mission record: probe the provider by its handle (probe/observe) and
the process by pgid + start time; classify DONE (receipt available), INCOMPLETE (provably not
started or provably dead with no effect), UNCERTAIN (anything else). UNCERTAIN missions are reconciled
against the provider's own record (intent attempt id) before any retry; a mission is never
re-dispatched blind.

## Cancel (F7)
By handle, not by pgid alone: provider cancel (which kills the POSIX process group since 908b543),
plus scope unit stop / `claude stop <id>` when the record carries one; then an orphan census by pgid
(POSIX: /proc scan for the pgid) whose result is recorded; a failed stop is a recorded failure, never
swallowed.

## Stagnation (F10)
Gain = change in obligation state, verdict, or failure signature set for the goal between cycles.
Commits, receipts and tree moves alone are NOT gain. K consecutive no-gain cycles ⇒ STALLED for that
goal ⇒ escalation record in order: RCA mission, provider/method change, subgoal, decision packet.

## ISOLATED stage — work epochs (codex, claude-headless, claude-interactive)
Added 2026-09-25 (`modules/gsd_x/goal/resident/isolate.py`; proof `tools/test_gsd_x_resident_isolate.py`,
V-ISO-*). The gate provider is unchanged: it reads the goal root and writes nothing.

**Before anything is spent** (no epoch begun, no mission, no intent; reported, WAITING_FOR_PROVIDER
or WAITING_FOR_AUTHORITY as named): the declared write set is the goal's `scope.paths` exactly as
declared — the `["."]` default the gate path uses is NOT a write set.
- `EMPTY_WRITE_SET` — no `scope.paths` declared.
- `WRITE_SET_ESCAPES_REPO` — a path is absolute, contains `..`, names `.git`, or resolves outside
  the repo root.
- `NO_CLEAN_BASE` — the goal root has no HEAD, or its scope is dirty (`tree_id` is `work:`): the
  state the engine judged is not a commit a worktree can start from.
- `WORK_AWAITING_MERGE` — an earlier work mission for the same goal+obligation delivered commits
  whose branch tip is not an ancestor of the goal root's HEAD. Re-running the same work against an
  unchanged tree spends the provider for no new information (the reconciler cannot see an unmerged
  branch); a person merges or discards the branch first.

**Isolation** (after `epoch.begin`, BEFORE the intent): `git worktree add -b resident/<mission-id>
<state>/worktrees/<mission-id> <base>` where base = goal root HEAD. The mission records `worktree`,
`branch`, `base_commit`, `write_set`, `root` (goal repo), `root_head_at_isolation` and
`root_ref_at_isolation`, and moves ADMITTED → ISOLATED by CAS. Refusals here end the epoch
CANCELLED ("nothing ran") and make the mission REFUSED (terminal): `WORKTREE_PATH_EXISTS`,
`WORKTREE_INSIDE_REPO` (a state dir inside the goal repo), `WORKTREE_ADD_FAILED` (git's own text).
Then the intent is recorded and the provider is dispatched with `root` = the worktree and nothing
else; codex receives `prompt` and claude `brief`, both from `brief.compile_brief` with the worktree
as its "where you work".

**Harvest = write-set enforcement, before ingestion.** Changed paths are the union of
`git diff --name-only --no-renames <base> HEAD` and `git status --porcelain --no-renames
--untracked-files=all` in the worktree. A path is in scope iff it equals or lies under a declared
path. Refused with `WRITE_SET_VIOLATION` (nothing ingested; epoch ended FAILED so the reconciler
never blind-retries it; mission REFUSED with the offending paths, head and reasons recorded) when
any of: a path outside the write set; worktree HEAD no longer descends from base (history
rewritten); the worktree left its branch; `MAIN_BRANCH_MOVED` — the goal root's HEAD moved since
isolation in a way that implicates the epoch: non-fast-forward (the old head is no longer an
ancestor), or the new root HEAD reaches any commit in base..worktree-HEAD. Worktrees share refs, so a
provider CAN move main; the resident cannot undo it and records it. An ordinary fast-forward commit
by a person on main is NOT a violation. Honest limit: a provider that commits directly in the goal
root (`git -C <root> commit`) is indistinguishable from a person's commit by this check. Otherwise the provider's receipt is ingested through `epoch.ingest_receipt` and
the mission records `deliverable_head`.

**The resident NEVER merges into, pushes, or rewrites the goal's branch.** The deliverable is the
branch `resident/<mission-id>`; its commits reach the goal tree only when a person merges it.

**Integration (Owner decision "option 1", 2026-09-25).** After a harvest that passed the write-set
check and ingested its receipt, the resident offers the delivery on ONE dedicated branch,
`factory/integration`, in the goal repo. Order, each step fail-closed, outcome recorded on the
mission as `integration` = {state, reason, detail, gates, ref_before, ref_after}:
1. `NOTHING_TO_INTEGRATE` — the worktree HEAD equals base (no commit delivered). No gates run.
2. `INTEGRATION_WORKTREE_DIRTY` — the worktree holds uncommitted bytes; gates would judge bytes the
   commit does not carry. No gates run.
3. **Gates in the worktree.** Every obligation of the goal whose disposition is not retired
   (DEFERRED/REJECTED/NOT_APPLICABLE) has its done gate run with cwd = the job's worktree, through a
   dedicated `GateProvider` instance (run dir `<state>/runs/integration`) — the same supervised
   process, own session/process group, result file and tree-kill cancel as any gate epoch; there is
   no second gate runner. Each run is bounded by `Config.integration_gate_wall_s` (default 900 s)
   and cancelled at the bound; a cancelled or unreadable run counts as NOT green. This runs
   synchronously inside the cycle (the cycle is blocked for at most n_gates × bound). The results
   are recorded on the mission as evidence and are **NOT** a satisfaction of any obligation: nothing
   of them is written to the goal log. The goal is judged on its own tree only.
   `NO_GATES` (the goal has no live gate — nothing proved) and `GATES_RED` (any gate not exit 0) ⇒
   no integration. `INTEGRATION_HEAD_MOVED` — the worktree HEAD after the gates is not the commit
   that was judged ⇒ no integration.
4. **Fast-forward `factory/integration` to the job commit**, in this order:
   `INTEGRATION_CHECKED_OUT` if `git worktree list --porcelain` shows `refs/heads/factory/integration`
   checked out anywhere (updating a checked-out branch desynchronises that worktree's index from its
   HEAD). If the ref does not exist it is created at the job's base with `git update-ref <ref> <base>
   ""` (the empty old value = "must not exist"). Then `INTEGRATION_NOT_FAST_FORWARD` unless the
   current tip is an ancestor of the job commit (`merge-base --is-ancestor`) — never merge, rebase or
   force; a person decides. Then `git update-ref <ref> <job> <tip>` (compare-and-swap):
   `INTEGRATION_RACE_LOST` if the ref moved since it was read. A tip already equal to the job commit
   is `ALREADY_INTEGRATED`, not an error.
   The resident touches NO other ref: never the goal's current branch, never a remote (no fetch,
   no push), never `resident/*`.
The engine's epoch outcome is unchanged by integration (the work epoch already ended with the
provider's outcome); red gates are resident evidence, not an engine verdict.

**The re-dispatch guard, qualified.** `WORK_AWAITING_MERGE` still blocks every re-dispatch while a
delivered branch is not an ancestor of the goal root's HEAD, and now says which case holds:
`INTEGRATED` (kind `AWAITING_MERGE`: `factory/integration` carries the delivery; the Owner merges
`factory/integration` into the goal branch) or `NOT_INTEGRATED(<reason>)` (kind
`DELIVERED_NOT_INTEGRATED`: red gates or a refused integration; a person merges, repairs or discards
the branch). Both are person kinds. The guard clears by the existing merge detection once the goal
HEAD contains the delivered commit. A second job starts from the goal HEAD; after the Owner's merge
that HEAD contains the previous integration tip, so the second job fast-forwards on top of it. If the
Owner squashed or rebased instead, the tip is no longer an ancestor ⇒ `INTEGRATION_NOT_FAST_FORWARD`.

**What integration does NOT protect.** The checked-out test and the CAS are two reads, not one
atomic step: a `git checkout factory/integration` landing between them is not seen. Green gates in
the worktree say the job commit passed the gates *on its own base*; they say nothing about the
commit merged onto a goal branch that moved since. A gate that writes untracked files into the
worktree keeps that worktree from automatic removal (cleanup never deletes dirty trees). The
integration ref is local only; nothing leaves the machine. Integration refusals do not retry: the
record stays until a person acts.

**Cleanup** (terminal missions only, every cycle and at census): `git worktree remove <path>` WITHOUT
`--force`, attempted only when `git status --porcelain` in it is empty (git re-checks and refuses a
dirty tree itself). The branch is ALWAYS kept. A dirty worktree is never removed: the mission records
`worktree_kept` with the reason, and it stays for a person.

**Census of an ISOLATED mission.** With an intent: unchanged (probe the provider's record; adopt or
LOST). Without an intent (crash between isolation and intent): the worktree is inspected —
absent, or present and pristine (HEAD == base, clean) ⇒ INCOMPLETE ⇒ LOST, and the pristine worktree
is removed by the cleanup rule (discarded, never reused: the epoch is resolved by the engine's own
recovery, and a later decision begins a new epoch with a new worktree); present with commits or
uncommitted bytes ⇒ UNCERTAIN (terminal, blocks its goal), nothing deleted.

**Not built here:** a budget system (spend stays under provider caps + each provider's own
per-day/wall bounds); merging into the goal branch; pushing anything.

## Entrance
`tools/gsd_x_resident.py` with `run` (the loop, what systemd calls), `once` (one cycle), `status
[--json]`, `stop` (writes STOP), `census`. The systemd USER unit template under
`install/gex44/goal-resident.service` (Restart=always, RestartSec bounded, KillMode=control-group,
ExecStopPost = `census`, absolute PATH including /home/factory/.local/bin — non-interactive ssh does
not read ~/.profile, measured 2026-09-24).

## Proof (tools/test_gsd_x_resident.py, V-RES-*; both poles each; fake providers + temp stores)
lock refusal + stale reclaim only on evidence · STOP honoured mid-cycle and owned missions cancelled
· intent written before dispatch (a crash injected between intent and dispatch yields UNCERTAIN and
no second dispatch) · census classifies DONE/INCOMPLETE/UNCERTAIN · reused pid with different start
time is not "alive" · noise-committing fake provider reaches STALLED within K (control: a provider
that closes an obligation keeps HEALTHY) · expired lease reclaimed, live lease respected · health is
never HEALTHY without gain · cancel records orphan census; a failing stop is recorded · ungoverned or
paused goal is not admitted. Linux-only cases (process groups, /proc) print UNJUDGED on Windows.
Chaos on GEX44 later (wave H): kill -9 mid-mission, unit stop during mission, real reboot.
