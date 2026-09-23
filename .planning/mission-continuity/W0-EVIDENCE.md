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
