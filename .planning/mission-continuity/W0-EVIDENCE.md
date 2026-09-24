# W0 evidence — host primitives for Ralph-style continuation

Host: Windows 11, Claude Code 2.1.281, 32 GB (≈4 GB free at start). Sandbox:
`<scratchpad>/mc-w0/p1repo` (disposable; 60 data files). Hook logger registered ONLY for
the probe sessions via `--settings` (`mc-w0/hooklog.py`). Workers launched from
`C:\Users\User\AppData\Local\Temp` (trusted) with `--add-dir <sandbox>`.

Each row: what was asked · what the host did · instrument.

| # | question | observed | instrument |
|---|---|---|---|
| E1 | Does `claude --bg` run in an untrusted cwd? | **No** — `Workspace not trusted. Run claude in <dir> once and accept the trust prompt`, exit 1 | launch stderr |
| E2 | Is trust inherited from a trusted parent? | **No** — `C:/Users/User/AppData/Local/Temp` is trusted in `~/.claude.json`, its subdirectory was refused | E1 + `.claude.json` read-only |
| E3 | Does a `--bg` session inherit the launcher's environment? | **No** — `CPP_MISSION_ID` absent in every hook payload env of every worker; `CLAUDE_CODE_SESSION_ID` also empty at SessionStart | `hooklog.jsonl` `env_mission` |
| E4 | Can the launcher pre-choose the session id? | **No** — `warning: --bg manages the session id; ignoring --session-id` | launch stderr |
| E5 | How does the launcher learn the worker's identity? | synchronously: `backgrounded · <8-hex id> · <name>` on stdout; the id is the prefix of the `sessionId` in `agents --json` | launch stdout + `agents --json` |
| E6 | Is a worker blocked on a human distinguishable from a dead one? | **Yes** — `agents --json` row: `status:"waiting"`, `waitingFor:"permission prompt"`, `state:"blocked"` | `claude agents --json` |
| E7 | Does `claude stop` produce an observable end? | host: `state:"stopped"` in `agents --json --all` — always. `SessionEnd` hook: **fired for `24eabf64`, did NOT fire for `9603cb39`** → SessionEnd is not a reliable stop witness | `agents --json --all`, `hooklog.jsonl` |
| E8 | Can an unattended `acceptEdits` worker commit with git on this host? | **No** — the inherited global doctrine routes git through PowerShell; `--allowedTools "Bash(git *)"` never matches; `PowerShell(& '<git>' *)` did not match the identical emitted command; `PowerShell(*git.exe*)` let `git log` through but prompted on `git add`. Three shapes, three blocks → pivot (Regla 12): probe continues without git | `claude logs <id>` |
| E9 | Does `claude agents --json` answer quickly? | not always — one call exceeded 60 s on this host under load | tool timeout |
| E10 | Startup context cost of a worker | 24 instruction files = 304.8k chars, over the host's 150k limit warning — every fresh worker pays the global doctrine | `claude logs` banner |

| E11 | Does a fresh session continue EXACTLY where the previous one stopped? | **Yes, twice.** Iteration 1 (`0b75ac7f`) found `f01` already recorded and did f02–f07; iteration 2 (`eb058184`), a new process with no shared memory, did f08–f13: 13 rows, in order, 0 duplicates, 0 wrong | `mc-w0/verify.py` |
| E12 | RAM of one worker | `0b75ac7f`: 660 MB working set, ~1 GB private | `Get-Process` |
| E13 | Does `claude stop` free the process immediately? | **No** — pid still alive right after `stopped`; gone within the next launch (~1 min) → the relay must WAIT for the pid before launching the successor | `Get-Process` before/after |
| E14 | What does the host do when a busy background worker's process is killed? | **Restarts it by itself**: `133c6f91` killed at row 28 (taskkill); host injected `isMeta` "Continue from where you left off. Note: this session was automatically restarted after its process exited unexpectedly…" and it resumed at f29 | `mc-w0/writers.py` over its transcript |
| E15 | Consequence of treating that kill as a death | the replacement I launched (`7bb4d1bc`) ran BESIDE the revived worker: both wrote, `f30` recorded twice (`rows=33 in_order=False dupes=1`) | `verify.py` + per-worker write attribution |
| E16 | Host state after killing an IDLE worker | `done` — the same word as a clean finish → host `done` means "not running", never "mission complete" | `agents --json --all` |
| E17 | Do the user's global hooks run in a `--bg` worker? | **Yes** — `context-watchdog` logged `session=0b75ac7f used_pct=24.0 outcome=pass ms=9654` | `~/.claude/logs/context-watchdog.log` |

## W8 — live relay on the production path (mission `m-7cebf2b33bf3`, 2026-09-24)

| # | observed | instrument |
|---|---|---|
| E18 | attempt 1: variadic `--add-dir` swallowed the prompt → worker "idle — send a prompt to start" (fixed `9355f8e`) | launch stdout |
| E19 | attempt 2: an orphan of a halted mission wrote the same file as the next worker (fixed `46739ca`) | `writers.py` |
| E20 | both launches: the worker's own SessionStart hub never completed (chain abandoned at 1035 MB free once; silent once) → supervisor ADOPTED on the host witness at 23:57:29 and 00:15:50 | ledger `worker_adopted`, hub log, dispatcher errors |
| E21 | the Stop-only wall was blind mid-turn: used_pct 39 → 45 in ONE turn with zero watchdog lines; the PostToolUse wall (`4616039`) fired at 00:32:00 | metrics file, `mission-wall-*.flag` |
| E22 | worker 1 stopped at f23 and ended with a `HANDOFF NOTE` naming the next file and a non-repo fact (anti-thrash cadence) | transcript |
| E23 | a finished background turn reads host `done` → REPLACE; relay at 00:41:25: note 509 chars from the transcript, card 1058 B via `--append-system-prompt` | ledger, mission record |
| E24 | **worker 2 (fresh process, fresh session) wrote f24, f25, f26… — sole writer; 27 rows in order, 0 dupes, 0 wrong** | `writers.py 88525fc9`, `verify.py` |
| E25 | W8 closed as designed: worker 2 reached the wall at f41 (00:58:41 `handoff_already_asked` — the mid-turn flag had already asked), its turn ended, the budget (2 iterations) HALTED the mission at 01:05:23 and the halt stopped the worker (`orphan_stopped` 01:05:30). **Final: 41 rows, in order, 0 dupes, 0 wrong; writers disjoint (ef5fe657 f01–f23, 88525fc9 f24–f41)** | ledger, `verify.py`, `writers.py` |

## Adversarial review (2026-09-24) — 3 HIGH / 3 MEDIUM closed in `3c2116f`

Found by reading, not by a live failure; each fix carries a V-MC gate with a control, and a
mutation drill that reverts it (7/7 caught, restore SHA-256 OK). H1 overdue launch + host
unanswerable now AWAITS (never replace on UNKNOWN). H2 the lease leaves the predecessor at the
claim. H3 budget binds UNKNOWN/BLOCKED owners; UNKNOWN past `HEARTBEAT_STALE_S` is surfaced.
M1 replace waits for the dead owner's pid. M2 reaping spares the launch in flight. M3 one
mission's exception no longer aborts the pass. L1 (stale-lock race) stays recorded debt.

## M6 — real `/gsd-autonomous` (started 2026-09-24)

Mission `m-7f6d988e3c93` on `Desktop\Cursor Projects\gsd-long-smoke` (the v2 canary, already
trusted; 1/8 phases done, GSD `OK`), worker 1 `f3c0b67e`, `--permission-mode auto` (Owner
decision; default since `18c7299`), budget 5 iterations / 8 h. Witness snapshot of the project
at HEAD `4f09667` in `<scratchpad>\m6-smoke-snapshot`. Rows below are appended as the run moves.

## Consequences for the design

- Identity: bind the lease from the launcher's own synchronous stdout (E5), never by env (E3),
  never by pre-chosen id (E4), never by "the new session that appeared" (T-CONT-08).
- Stop witness: host state (E7), not SessionEnd.
- Liveness: `agents --json` is authoritative but slow (E9) → bounded timeout, and a timeout is
  UNKNOWN, never DEAD.
- Permission mode of real workers is an Owner decision (E8): `acceptEdits` cannot commit here.
- **A background worker is never replaced for dying** (E14/E15): crash recovery is the host's.
  The mission relays only when a worker's TURN ENDS (hand-off, or idle without completion)
  and only after the predecessor's pid is gone (E13). Pinned by `V-MC-BG-KILLED-*`, mutation
  `bg-owner-judged-by-pid` → 50/52.
