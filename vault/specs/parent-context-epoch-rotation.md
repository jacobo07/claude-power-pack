---
covers: [parent-context-epoch-rotation, gsd-mission, cpp-gsd-long, context-epoch, sweep-liveness, turn-continuation, gsd-epoch]
status: IMPLEMENTED (5eee90a, 717554f); live multi-rotation proof S10 IN FLIGHT (mission m-916e905e23d4)
date: 2026-09-27 (plan) / 2026-09-28 (implementation, pane claude-power-pack-c2)
mode: ULTRA-PLAN for the turn/epoch decision (Reality Scan), EXECUTION for every slice after it
---

# Parent Context Epoch Rotation -- plan

> **UPDATE 2026-09-28 (supersedes the two blocks below where they disagree).**
>
> **Host primitive, verified in session (probe `7a42f96f`, scratchpad `probe_resume2.log`):** after
> `claude stop <id>`, `claude --bg --resume <sid> "<prompt>"` with NO other flag wakes the SAME
> session id and transcript with its context ("SAME_SESSION_CONTINUED True CONTEXT_PRESERVED True").
> With any flag the host starts a COPY under a new id -- host text: "keeps its own saved options, so
> the flags you passed started a copy". So same-session turn continuation EXISTS on this host and
> the old "every turn end = fresh worker" was a design choice, not a host limit.
>
> **Economics, measured:** worker floor 186,856 tokens resident at call #1 (4aa2e2d3,
> session_autopsy); the resumed probe turn wrote 125,483 and read 33,949 -- a new process breaks the
> prompt cache near the front, so a continuation costs ~current context and a fresh worker
> ~floor + reconstruction. Policy: continue below `CONTINUE_MAX_TOKENS` = 300k, rotate at/above it.
>
> **Count correction (supersedes "1 of 499"):** `tools/gsd_epoch.py census` finds **10**
> wall-witnessed rotations in production (KobiiCraft x5, CavEX x2, orca x1, gsd-long-smoke M6 x2),
> 434 turn-end relays, 9 recoveries, 3 launch retries, 26 initial, 18 renewals. The "1" counted only
> `handoff_asked`; the mid-turn wall writes `mission-wall-<sid>-e<N>.flag` and the Stop hook then
> writes `handoff_already_asked`. Corroborated in worker cb70bd86's transcript. The historical 10 are
> classified by reason + witness (basis `reason+wall_witness`); from 717554f on, every launch
> ledgers `launch_cause` and rotations are certified by that cause, never by counting sessions.
>
> **Implemented:** `5eee90a` tools/gsd_epoch.py (causes, decide_turn_end, continue_worker, G6
> child_work over main + subagent transcripts, S7 identity_check, G3 epoch_compacted, G4 epochs +
> census); `717554f` supervise wiring (HOLD / CONTINUE / ROTATE; continuations counted by T5's
> next_progress; kill switch `CPP_MISSION_CONTINUATION=off`). Gates epoch 56/56, mission 184/184,
> 8/8 mutants killed on an isolated copy.

> **CORRECTION 2026-09-27 ~23:40 (supersedes the "in production" claims in sections 1 and 5).**
> Measured across the whole mission ledger: **499 launches in 43 missions, and exactly ONE was
> caused by the context wall** (`handoff_asked` = 1, the W8 synthetic `/mc-task` relay of
> 2026-09-24). 444 relays were "owner's turn ended without completion" (268 idle, 176 blocked). The
> `kme-reconstruction` lineage's 192 epochs were quota refusals: worker `60679bea` ended its only
> turn with "You've hit your weekly limit", 0 tool calls; the supervisor relaunched every ~10 min
> (fixed at HEAD by `30ccdeb`). So what production exercised is **iteration continuation**, not
> **context rotation**. Honest status of wall-triggered fresh-context rotation: HOST VERIFIED on one
> relay, NOT multi-epoch, NOT production-verified. The reset mechanism (fresh-session replacement,
> card via `--append-system-prompt`) is unchanged; its proof is what was overstated.
> Economics finding: every fresh epoch starts with a ~736 KB `instructions` attachment (worker
> `60679bea`), the floor each rotation pays -- to be measured in tokens before any wall policy.
>
> **Ownership split agreed with pane `claude-power-pack-e9` (mission-continuity T1-T8):** theirs =
> T4 history `seq`, T5 progress/livelock, T6 code identity, T7 remainder (lease + tree reap), T8
> certification/UKDL. Mine = G3, G4 (built on their `seq` + `epoch`, no third counter), G6, the
> rehydration identity check (S7), and the multi-epoch Production Reality proof (S10). Edits to
> `tools/gsd_mission.py` are announced to them first.

## 1. Reality (measured 2026-09-27, read-only)

HEAD `48bbbb7` on `feature/knowledge-acquisition`; ~20 foreign dirty files incl. `tools/gsd_mission.py`,
which another pane is editing live (its line numbers shifted between two reads in this scan).

**The capability already exists and is in production, under a misleading name.** "Ralph" here is
NOT Stop-hook re-activation. `/cpp-gsd-long` arms a mission (`tools/gsd_mission.py`); the work runs
in `claude --bg` worker sessions; at the wall (35/40 %, judged mid-turn by `hooks/mission_wall.js`
and at Stop) the worker commits and writes `HANDOFF NOTE:`; the sweep stops it, waits for its pid,
and launches a FRESH session with a <= 8 KB card via `--append-system-prompt`. The arming pane does
no work. So the "parent session whose meter fills" IS the worker, and it is replaced every epoch.

Evidence: 43 mission records. Lineage `kme-reconstruction` = 4 renewals x 48 iterations, each a new
session under one lineage id; many 12- and 24-iteration missions; all ended on budget, none on a
rotation fault.

**Host mechanism, named precisely:** fresh-session replacement, not clear. No supported API
triggers `/clear`; keystroke delivery into a pane (v2 `/compact` typing) was retired 2026-09-25 as
unreliable -- rebuilding it for `/clear` would be CLASS 0. Postcondition = the new session's own
SessionStart ack (`worker_acked`, strong) or the host listing its id (`worker_adopted`, weaker).

## 2. Defects found (evidence, not hypotheses unless marked)

- **G0 CRITICAL, live now -- the rotator is not running.** 7 `gsd_long_run.py sweep` processes
  alive since 20:01, none finished; sweep log silent since 19:58; host 477 MB free. The task's 15-min
  limit ends wscript, not the python grandchild, so `IgnoreNew` does not stop overlap: concurrent
  supervisors are running right now. Consequence: mission `m-8ab6628b7acd` is RUNNING, owner alive
  46 h against `max_hours 24`, never relayed. A rollover trigger with no caller reaching it.
  Which stage hangs: UNKNOWN (diagnose first).
- **G1 -- budget is enforced only by the supervisor**, so G0 disables it too.
- **G2 -- semantic progress is not tracked.** `last_progress_at` is written only at create
  (grep: one writer, value None). A livelocked mission is stopped only by `max_cycles`.
- **G3 -- compaction is invisible.** `session_start(session_id, source)` ignores `source`; a worker
  compacted by its native 600k safety net continues under the same epoch, recorded as clean.
- **G4 -- "epoch" is overloaded.** `epoch` is the CAS fence; `iterations` counts relays; they
  diverge (m-130c epoch 2 / 0 iterations). No per-epoch record of session, card hash, end reason.
- **G5 -- no runtime binding.** An epoch can start on a changed CPP (hooks, gsd_mission itself);
  nothing records or compares it. UWCP `runtime_identity` (S1-10) exists to CONNECT.
- **G6 -- no child-work barrier.** The wall says "finish the step and commit"; nothing checks the
  worker's own background tasks/agents before `stop_owner` kills the tree. Results can die silently.
- **G7 -- card is not from the Goal Spine.** `render_card` uses record+git+GSD; the goal/brief.py
  merge is deferred in UWCP (hourly concurrent writer on that function).
- Hypothesis REFUTED this scan: "an adopted worker gets no wall marker" -- m-8ab6's marker exists.

## 3. Ownership (EXTEND / CONNECT before NEW)

| responsibility | owner | action |
|---|---|---|
| logical run | mission lineage (`lineage_id`, renewals) | REUSE |
| run generation | mission record `m-*` | REUSE |
| context epoch | worker iteration | EXTEND: explicit epoch rows derived from the ledger |
| fence / recovery ownership | CAS `epoch` + `_Lock` | REUSE; add supervisor single-instance lease |
| pressure | context-watchdog marker `wall` + mission_wall.js | REUSE |
| reset mechanism | `stop_owner` + `launch_worker` | REUSE |
| postcondition | SessionStart hub ack / host adopt | REUSE; add compaction + mismatch labels |
| brief | `render_card` -> goal/brief.py when bound | CONNECT (last, coordinated) |
| semantic progress | GSD STATE + HEAD + goal receipts | NEW small module |
| runtime binding | UWCP runtime_identity | CONNECT |
| history checking | modules/history_check | EXTEND (epoch checkers) |
| formal model | UWCP TLC harness | EXTEND only if G4 adds states (expected: no) |

No new continuity engine. Interactive-pane rotation is a SEPARATE brief and is out of scope.

## 4. Slices (EXECUTION mode, this pane -- NOT under /cpp-gsd-long: the supervisor is the
## subject under repair and is currently hung; using it to drive its own repair is the bootstrap trap)

- **S0 triage (first, Owner-authorised):** capture a stack of one stuck sweep (py-spy or
  faulthandler via env), then reap the 7 orphans by exact cmdline. Record in the vault.
- **S1 sweep liveness (G0/G1):** per-stage wall-clock bound; single-instance lease with
  stale takeover by pid+start time; tree reap on timeout; supervisor heartbeat; `status` reports
  NOT_RUNNING / STALE instead of silence. Test drives a hung stage and two concurrent sweeps.
- **S2 epoch identity (G4):** `epochs(mission_id)` view from ledger events: epoch_no,
  session, pid+proc_start, card sha256, start/end, end_reason, compacted, runtime id, progress.
- **S3 compaction truth (G3):** SessionStart `source=compact` in a worker -> ledger
  `epoch_compacted`; certification counts only uncompacted epochs as clean.
- **S4 runtime binding (G5):** record runtime id per epoch; schema mismatch -> BLOCKED
  `version_mismatch`; code change -> card line "runtime changed".
- **S5 semantic progress (G2):** at relay, evidence = HEAD advanced OR GSD phase/plan advanced
  OR goal receipt; write `last_progress_at`; K=3 epochs without evidence -> HALTED `no_progress`,
  renewal refused.
- **S6 child barrier (G6):** at relay, predecessor transcript -> launched-but-unnotified
  background tasks/agents; unreadable = UNKNOWN = hold; bounded wait, then named `children_lost`
  in the card. Epoch receipts already reject stale results (ReceiptRefused): pin with a test.
- **S7 rehydration check:** worker SessionStart compares record cwd/workstream/.git HEAD file
  with the card; mismatch -> `rehydration_mismatch` + STOP line. No git subprocess (hub deadline).
- **S8 history + fault matrix:** new checkers (NoTwoLiveWorkers, CompactedNotClean,
  NoLaunchBeforeStopConfirmed, StaleEpochCannotAck, NoProgressHalts); env-gated crash points
  at every supervise boundary; deterministic replays.
- **S9 card from Goal Spine (G7):** after identifying the render_card writer; new module,
  minimal call site.
- **S10 Production Reality:** real mission in `gsd-long-smoke` with a lowered per-mission wall,
  >= 3 relays: plain; background task in flight at wall; supervisor killed mid-relay; CPP commit
  mid-run; a deliberately stuck workstream must HALT `no_progress`. Judged by the history checker
  run out of process.
- **S11 institutional:** Knowledge Vault entries (G0 the headline), UKDL three-level evaluation,
  UCR-CIF status, liveness registry, `commands/cpp-gsd-long.md` corrected (terminology).

Each slice = one or more pathspec commits; new files preferred while gsd_mission.py has a live
foreign writer; hunk headers checked before every commit.

## 5. Certification now

*(Rewritten 2026-09-28; the earlier text claimed "multi-epoch verified, hundreds of epochs" --
those were turn-end relays, not rotations.)*

| claim | tier | evidence |
|---|---|---|
| same-session turn continuation exists on this host | HOST VERIFIED | probe `7a42f96f` (scratch `probe_resume2.log`) |
| turn end continues, wall/ceiling rotates, child holds | IMPLEMENTED + ADVERSARIALLY TESTED | V-EPOCH 71/71, 11/11 mutants, crash points, peer review F1 fixed |
| wall-driven rotation happened in production (historical) | CLASSIFIED, 10 epochs | census `reason+wall_witness`; 1 corroborated by transcript (cb70bd86) |
| every launch names its cause | PRODUCTION (since 717554f) | `launch_cause` rows from the live sweep (first: m-916e905e23d4 INITIAL) |
| turn continuation in production | see Live proof | `turn_continued` rows |
| ≥ 3 certified rotations in one real mission | see Live proof | `gsd_epoch.py certify` |
| supervisor liveness | e9 T7 `dfe968f` + heartbeat | heartbeat rc 0 both stages |

### Live proof (S10) -- mission m-916e905e23d4

Armed 2026-09-28 00:44Z (PREPARED), launched by the production sweep 00:47Z (`launch_cause`
INITIAL/fresh), worker `9e89a87e` adopted 00:51Z and entered the smoke worktree. Wall 29/30/28 % of
a 1M window; parent context 19 % at start, 24 % at 01:41Z. Single-owner witness: 26 answered
samples 00:46Z–02:05Z, never 2 live workers; continued by `gsd_epoch.py watch`.
02:20Z: worker crossed the wall (flag `mission-wall-9e89a87e…-e1.flag`, used_pct 31 ≥ 30; its own
transcript carries "CONTEXT WALL"). certify at 02:32Z: epoch 1 = 13 commits in the work tree
(phases 5–6 done, 7 planned), wall witnessed, 8 more owner samples all ≤ 1 live worker; the
worker was still finishing its step, so no epoch 2 yet. The in-session watcher and waiter were
killed by the host's low-memory reaper (312 MB free) and deliberately not restarted.
Certified rotations so far: **0**. This section is updated from
`python tools/gsd_epoch.py certify --mission m-916e905e23d4`, never from the mission's own output.

## 6. Rollback

Each slice is additive; S1 lease and S5 halt carry kill switches (`CPP_SWEEP_LEASE=off`,
`CPP_MISSION_PROGRESS_HALT=off`). No change to the retired v2 path.
