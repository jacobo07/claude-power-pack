---
status: APPROVED 2026-09-23 by Owner (autonomous W0→W10; unattended workers = acceptEdits, scratch repo only)
opened: 2026-09-23
session: claude-power-pack-e3 [2f4d40]
branch: feature/knowledge-acquisition
covers: [cpp-gsd-long, gsd-long-run, mission-continuity, context-watchdog, continuation, liveness, fresh-worker, autocompact]
supersedes: nothing yet — extends gsd-long-run-v2.md and exact-target-continuation.md
---

# Mission Continuity — the mission outlives the session

## 0. Reality Scan (measured 2026-09-23, before any design)

| # | finding | instrument |
|---|---|---|
| R1 | 9 armed runs on this host; **9/9 verdict NO_CROSSINGS** (6 `stalled`, 2 `armed`, 1 `refused`). Nothing distinguishes a live run from an abandoned one | `gsd_long_run.py status` |
| R2 | Ledger: 21 `armed` vs **1 `started`** (hand-written with evidence), 229 `stalled`, 66 `reaped`, 13 crossings, 9 confirmed, 2 finished | event tally over `gsd-autorun-ledger.jsonl` (111,943 B) |
| R3 | Across 709 transcripts / 3.98 GB / 30 days: **374 compactions, 100 % manual, 0 native auto** | `scratchpad/auto_compact_probe.py` |
| R4 | Host ships a native, per-launch auto-compact window: `--autocompact <100k–1M>`, `CLAUDE_CODE_AUTO_COMPACT_WINDOW`, `/autocompact` (persists to the `autoCompactWindow` setting) | `claude --help`; code.claude.com/docs/en/model-config |
| R5 | Host documents `PostCompact` and `SessionStart` with `source=compact`; output of compact-source SessionStart hooks **is added to the compacted context** | code.claude.com/docs/en/hooks, /context-window |
| R6 | **No PostCompact hook is registered**; nothing in the long-run path reads SessionStart `source` | `~/.claude/settings.json` hook tally |
| R7 | Host-supervised workers exist: `claude --bg`, `claude agents --json` (no TTY), `attach`, `logs`, `stop`, `respawn`. `--bg --resume <id>` "starts a copy and says so when the session is already running" — i.e. the host itself refuses two writers on one session | `claude --help`, `claude agents --help` |
| R8 | Session registry rows carry `pid`, **`procStart`**, host-written **`status`/`statusUpdatedAt`** and a `messagingSocketPath`; `session_liveness()` uses none of procStart/status and can never answer `dead` | `~/.claude/sessions/*.json`; `gsd_long_run.py:875-905` |
| R9 | Marker is keyed by session id (`gsd-autorun-<sid>.json`): the mission dies with the session. `/cpp-gsd-long` rejected headless resume because of two writers on one transcript — a **fresh** session has its own transcript, so that objection does not apply to replacement | `gsd_autorun_marker.py:44-47`; `commands/cpp-gsd-long.md:192-194` |
| R10 | Certification C1–C7 proven (C7 on 2026-09-21), but it certifies **one mechanism** (keystroke `/compact` + resume). F6 (EBUSY on `/compact`) still an open hypothesis | `vault/specs/cpp-gsd-long.CERTIFICATION.md` |

## 1. Mode decision

- **Architecture: ULTRA-PLAN** — the ownership question (session vs mission; keystroke vs host-native primitives) is genuinely open and a wrong choice is expensive.
- **W0 probes: EXECUTION** — they are measurements that decide two branches of the plan.
- **W1–W10: EXECUTION** per slice once W0 has settled the branches. No slice gets its own ULTRA pass.

## 2. Architectural thesis (tested, and the parts still conditional)

The common genome of F1/F2/F3, armed-never-started, resume-owed-never-delivered and
dead-run-looks-healthy is confirmed by R1/R2/R6/R8:

> **A lifecycle transition happened, or failed to, with no independently observable,
> time-bounded acknowledgement — and the only owner of the mission was the session
> whose failure we were trying to observe.**

Target: a **mission record** owns the work; sessions hold a **lease** on it and are
replaceable. Every critical transition carries an expected acknowledgement and a
deadline; a missed deadline becomes a recovery path, never silence. Liveness is judged
by the sweep, outside the worker's failure domain, from host-written evidence.

**OWNER DECISION 2026-09-23 (mid-W0), supersedes the ordering below:** Ralph-style
fresh-session continuation is the PRIMARY path of `/cpp-gsd-long` — "prefiero empezar
sesiones nuevas y continuar exactamente igual antes que compactar por tema RAM". At the
context wall the worker writes its checkpoint and ends; a NEW process (`claude --bg`,
new session id) is launched with the rehydration card and continues exactly. Native
auto-compaction stays only as a SAFETY NET (worker launched with an `--autocompact`
window above the handoff wall), and the keystroke `/compact` path becomes legacy.
Consequence for W0: P3/P4 (bg lifecycle, hooks in bg, RAM per worker) and a Ralph
hand-off probe come first; P1 is demoted to a safety-net check.

Continuation paths (original ordering, kept for the record):

| path | when | depends on |
|---|---|---|
| **A. Native auto-compaction** mid-turn, rehydrated by a `SessionStart(source=compact)` card | default for runs launched with a narrowed `--autocompact` window | **P1 (unproven, R3)** |
| **B. Keystroke `/compact` + resume** via the terminal inbox (existing, C1–C7) | interactive panes where A is unavailable | kept unchanged until W8 proves A |
| **C. Fresh worker** `claude --bg` in the mission's cwd, new session id, rehydrated by a `SessionStart(source=startup)` card | the lease holder is **proven DEAD**, or repeated transition failure | **P3/P4** |
| **D. Halt, explicitly** (`BLOCKED`/`BUDGET_EXHAUSTED`/`ORPHANED`) | budget, mission freshness, recovery attempts exhausted | — |

## 3. Ownership map (EXTEND / CONNECT before NEW)

| capability | existing owner | action |
|---|---|---|
| mission record, lease, lifecycle state | `gsd_autorun_marker.py` (session-keyed marker) | **EXTEND** → schema v3: `mission_id`, `state`, `epoch`, `owner{session_id,pid,procStart,heartbeat_at}`, `pending{kind,id,expect,deadline}`. Session file kept as a lease pointer; legacy v2 markers adopted in place |
| heartbeat / progress | `context-watchdog.py` Stop path (already stamps endpoint) | **EXTEND** (one stamp, critical lane already) |
| liveness authority | `gsd_long_run.session_liveness` | **EXTEND** → ALIVE / DEAD / UNKNOWN; DEAD only on positive evidence (pid gone, or procStart mismatch); `claude agents --json` as a second witness |
| transition deadlines, recovery | `gsd_long_run.sweep` (scheduled task, already out of band) | **EXTEND** |
| compaction witness | `compaction_observed()` (boundary row) | **EXTEND** with PostCompact + SessionStart(compact) stamps; any witness = observed, disagreement ledgered |
| rehydration | `record_intent()` + Stop `reason` | **EXTEND** into a mechanical card emitted by a new SessionStart-chain member, ≤ 8 KB |
| keystroke delivery | `continuation_transport.py`, terminal inbox, daemon | **KEEP** (path B) |
| fresh worker | none | **NEW, minimal**: one launcher function inside `gsd_long_run.py`, lease-CAS guarded |
| verdicts | `report()` / `status()` | **EXTEND** with `state`, `liveness`, `pending`, `overdue`, `last_progress` |
| certification | `cpp-gsd-long.CERTIFICATION.md` | **SUPERSEDE by addendum** — mission-continuity claims; history left as written |
| bounded loop / `/loops` | GSD autonomous + sweep budget | **DO NOT BUILD** — the loop exists and is bounded; a second one would be a parallel runtime |

## 4. External absorption matrix (revisions pinned)

| source @ rev | mechanism | decision | why |
|---|---|---|---|
| claude-code-handoff @ `d46bc32` (v0.18.6) | `SessionStart source=compact` cheap re-inject vs full load on startup | **ADOPT** | host-native rehydration; matches R5 |
| handoff | PostCompact resets only transcript-shaped state, keeps identity state | **ADOPT** | state-lifetime doctrine |
| handoff | "verify state matches reality" literal command block in the card | **ADOPT** | reconcile before replay |
| handoff | SessionStart stdout budget ~9 KB, measured, overridable | **ADOPT as constraint** (card ≤ 8 KB, re-measured here) | silent truncation risk |
| handoff | hook-chain self-diagnosis (Stop hook provably dead after N prompts) | **ADOPT** as `heartbeat overdue` | guard-event reachability |
| handoff | HMAC + untracked trust tier | **DO NOT ADOPT** | card is built mechanically from `~/.claude/state` + git, never from a repo file — no clone-delivery vector. Revisit if a repo-local file ever feeds the card |
| buildomator @ `3dcdbc0` | throttled PostToolUse checkpoint (microcompact skips PreCompact) | **ADOPT as heartbeat only** (cheap stamp, 60 s throttle, no git) | covers long single turns with no Stop |
| buildomator | detection ≠ deletion ownership (resume deletes last) | **ADOPT** | a failed rehydration keeps its evidence |
| buildomator | refuse trivial automatic overwrite | **ADOPT** | heartbeat never blanks a mission |
| buildomator | unsigned imperative auto-resume from repo file | **REJECT** | injection surface |
| buildomator | dual-plugin election | **REJECT** | self-inflicted problem |
| claude-code-auto-compact @ `fa7bad2` | tmux send-keys transport | **REJECT** | no Windows path; host-native A supersedes it |
| auto-compact | split text then delayed Enter | **ALREADY OWNED** (inbox sends 2 Enters, F5 closed) | — |
| auto-compact | debounce keyed by identity, not global | **ADOPT as check** on existing throttles | — |
| auto-compact | token math from last assistant `usage` | **ALREADY OWNED** (watchdog) | — |
| ralph @ `38c367f` | fresh process per iteration, durable plan outside context | **ADOPT the principle** as path C, with GSD phases as the plan | context rot + worker death |
| ralph | flat checklist, no progress detection, `bypassPermissions` default | **REJECT** | GSD proof state is richer; PP gates stricter |

## 5. Waves

| wave | content | mode | gate |
|---|---|---|---|
| **W0** | Probes in a disposable scratch repo (never a real project): **P1** does a `--bg` session launched with `--autocompact 100k` continue working after a native compaction with no input? **P2** exact PostCompact / SessionStart(compact) payloads, via `--settings` on the disposable session only. **P3** `--bg` launch → `agents --json` state → kill process → state/`respawn`. **P4** do user-settings hooks (Stop chain) run in a `--bg` session? **P5** is `/autocompact` persisted globally (would affect all 33 panes)? | EXECUTION | evidence file `.planning/mission-continuity/W0-EVIDENCE.md`; branches A/C decided |
| W1 | Characterization tests that pin TODAY's failures as red: armed-never-started reads healthy; dead owner = `unknown`; missing boundary with PostCompact fired; wall sidecar lost | EXECUTION | tests red on HEAD by design, inverted later |
| W2 | Mission record v3 + lifecycle (PREPARED ≠ RUNNING) + lease + heartbeat; migration of v2 markers | EXECUTION | V-MC-STATE-*, mutation drills |
| W3 | Liveness authority + transition deadlines + recovery routing in `sweep`; `status`/`report` gain state/liveness/overdue | EXECUTION | V-MC-LIVE-*, V-MC-DEADLINE-* |
| W4 | Multi-witness compaction (PostCompact + SessionStart(compact) stamps) + rehydration card (≤ 8 KB, reconcile block) | EXECUTION | V-MC-WITNESS-*, V-MC-CARD-* |
| W5 | Path A: arming records the window; the launcher for new runs uses `--autocompact`; **conditional on P1** | EXECUTION | live crossing in W8 |
| W6 | Path C: fresh-worker replacement, lease CAS on `epoch`, bounded attempts, budget, refuses on UNKNOWN; **conditional on P3/P4** | EXECUTION | V-MC-REPLACE-* incl. duplicate-launch race |
| W7 | Fault-injection matrix (≥ 25 cases from the mission prompt, each tagged REPRODUCED / SIMULATED / UNVERIFIABLE) + mutation drills with SHA-256 restores | EXECUTION | every protection's removal turns a named case red |
| W8 | Production Reality on a disposable GSD project: ≥ 2 native compactions with continued commits, one worker killed and replaced, work finished after the recovery | EXECUTION | ledger + transcripts + git |
| W9 | Legacy retirement, evidence-driven: threshold retune, wall sidecar, daemon path — each KEEP/DEPRECATE/DELETE with reason | EXECUTION | nothing removed before W8 |
| W10 | Certification addendum, command doc, UKDL (HR/PR/T), knowledge vault, baseline entry, adversarial review agent, handoff + RESUMPTION | EXECUTION | full regression suites |

## 5b. Ralph design (primary path, decided 2026-09-23 after the Owner's redirect)

W0 facts it rests on (evidence: `.planning/mission-continuity/W0-EVIDENCE.md`):
- `claude --bg` refuses an untrusted cwd, and trust is **exact-path, not inherited** (Temp is
  trusted, its subdirectory was refused). Missions run in their own, already-trusted project.
- The launcher's environment is **NOT inherited** by a `--bg` session (`CPP_MISSION_ID` absent in
  every hook of the worker): the host spawns it, not the launcher. Identity therefore travels by
  **`--session-id <uuid>` chosen before launch**, never by env and never by "the new session that
  appeared" (T-CONT-08).
- `claude agents --json` reports `status` (busy/idle/waiting), `waitingFor` ("permission prompt")
  and `state` (working/blocked/done/stopped): **blocked is distinguishable from dead**.
- `claude stop <id>` fires SessionEnd: a clean stop is observable.
- An unattended worker inherits the global doctrine (git through PowerShell), so a `Bash(git *)`
  allowlist blocks it on a permission prompt forever. Allowlists derive from the doctrine the
  worker will obey.

Mechanism:
1. **Mission record** `~/.claude/state/gsd-mission-<mission_id>.json` — owns cwd, resume command,
   workstream, mission terms, budget, wall, `state`, `epoch`, `owner`, `pending`, `iterations`.
   The session marker stays (the watchdog reads it) and gains `mission_id` + `epoch`.
2. **Launch** — `/cpp-gsd-long` arms the mission and launches iteration 1 as a `--bg` worker
   with a pre-chosen session id, `acceptEdits`, a doctrine-derived allowlist, and an
   `--autocompact` window ABOVE the handoff wall (safety net only). State `LAUNCHING` with a
   start deadline; the worker's first hook ack moves it to `RUNNING`. Prepared ≠ running.
3. **Hand-off at the wall** — the watchdog's crossing on a ralph-mode mission asks for a
   hand-off instead of `/compact`: finish the atomic step, commit, record the note
   (`gsd_long_run.py handoff`), end the turn. The Stop that ends that turn launches the successor
   (predecessor is idle by construction), epoch+1, marker for the new session written BEFORE
   launch; predecessor stopped after the successor's ack.
4. **Rehydration** — a SessionStart-chain member emits the mission card (≤ 8 KB) for any
   session whose marker carries a mission with epoch > 1: mission, note, HEAD, dirty paths,
   recent commits, GSD phase status, and a literal reconcile-first block.
5. **Liveness / recovery** (sweep, out of band) — owner absent from `agents --json` AND pid
   gone or procStart mismatch → DEAD → replace (bounded). `blocked` → BLOCKED, surfaced, never
   replaced. Overdue `pending` → recovery by kind. UNKNOWN never replaces.

## 6. Non-goals

tmux; HMAC signing; a new orchestrator/scheduler/daemon; a `/loops` command; replacing
GSD's phase state; touching the vendor gsd-core tree; modifying any live project's
marker except by the migration; any keystroke into a pane that is not the run's own.

## 7. Risks

- **P1 fails** (native auto-compaction does not continue work) → path A drops; B stays primary, C still ships.
- **`/autocompact` is global** → never used from a hook; only `--autocompact` on launched workers.
- **Two writers** → replacement only on DEAD with a procStart-verified witness; UNKNOWN never replaces.
- **Concurrent panes** in this repo (hundreds of dirty foreign paths) → new files preferred, pathspec commits, HEAD re-read before each commit.
- **Host memory starvation** → W0/W8 check free RAM before launching a worker; a starved run is INCONCLUSIVE, not a failure.

## 8. Definition of Done

Every item of the mission prompt's Production-Reality Done Gate, with these made
measurable: `status` shows PREPARED vs RUNNING vs ORPHANED for the 9 live markers;
a killed worker is replaced exactly once under a duplicate-launch race; ≥ 2 native
compactions (or, if P1 fails, 2 keystroke crossings) plus one replacement in one mission
with commits after each boundary; each protection has a mutation that turns a named case
red; Windows is the tested host throughout.
