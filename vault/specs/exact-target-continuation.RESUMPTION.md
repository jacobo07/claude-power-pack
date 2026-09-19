# RESUMPTION -- exact-target continuation (GSD X)

## 1. Identity
Repo `~/.claude/skills/claude-power-pack`, branch `feature/knowledge-acquisition`. Spec
`vault/specs/exact-target-continuation.md`. Thesis: a continuation reaches the session that
owns it, or nobody; a lifecycle state is claimed only from its post-condition.

**A /cpp-gsd-long run is IN FLIGHT in this session.** If you are reading this after a
compaction, the watchdog will ask you -- at the end of a turn -- to emit exactly
`/gsd-autonomous` as a single trailing line. Do that. Do not wrap up, do not stop.

## 2. Sealed (commits)
- `9676617` spec. `5d17c1e` C1: "compaction" requires a transcript `compact_boundary` newer
  than the cycle reference; one resume per boundary; fail closed.
- `01211b5` C2/C3: `tools/continuation_transport.py`. `fd87e39` C4: one door
  `_dispatch_continuation`; non-Orca -> terminal inbox; live daemon refuses by default.
- `547e4ae` **session-scoped autocompact thresholds.** `_thresholds(session_id)` reads
  `~/.claude/state/ctxwd-thresholds-<sid>.json` ahead of the launch-time env knob, one
  shared `valid_thresholds()` rule, fail-safe on junk. Writer:
  `gsd_long_run.py thresholds --session <sid> --set "35,40,30"`. GSDLR 60/60; mutations
  57/60 (file source removed) and 59/60 (session id not delivered); restores SHA-256 verified.
  Also seeds `.planning/` -- GSD parsed 0 phases here, so arming refused outright.
- `9190432` roadmap restructure: the narrow-wall proof is the milestone's acceptance gate,
  not a phase. GSD parses 4 incomplete phases.
- `691c09a` delivery deadline: inbox TTL 300 s (the Stop chain measures 82 s here, so the
  old 60 s always expired before the session could go `idle`), made safe by
  transcript-bounded withdrawal. ACPS 33 -> 38.
- `64ec155` **the sweep sends the RESUME after a compaction, not the `/compact` again.**
  `owed_line()`: a `/compact` tail is the same line in two opposite states -- never
  submitted, and submitted-with-the-compaction-landed (the agent has not spoken since, so
  the tail does not move). The boundary row (C1) is the only discriminator; the resume is
  gated by `resume_gate` and writes the `resume_requested` row that spends a cycle and
  advances the one-resume-per-boundary fence. GSDLR 60 -> 68; mutation 62/68 reproducing
  the production symptom byte-for-byte; restore SHA-256 `111DB4D2`.
Coherence anchor: GSDLR 68, GSDAC 26, ACPS 38, CXT 28, CWIRE 14 -- green at `64ec155`.

## 3. This run's state
- Session `37cfb187-ec05-43db-b57d-4bdcb5625362`, marker armed 12 cycles / 24 h,
  command `/gsd-autonomous`, mission `continuation,autocompact,thresholds,resume,exactness`.
- Wall narrowed to **35,40,30** -- crossing at 40% used, rearm under 30%, a 10-point band.
- Route measured live: `terminal-inbox`, exact, no focus needed. An owned-but-expired probe
  was refused by the extension that owns this pane; a foreign-ancestor control was ignored.
- Verdict to reach: `gsd_long_run.py report --session <sid>` = **PROVEN** (>=2 crossings,
  each with a confirmed resume).
- **Stop-chain reachability confirmed** 22:23:11Z: `session=37cfb187 used_pct=39.0
  outcome=pass ms=2025` in `~/.claude/logs/context-watchdog.log`. The watchdog does judge
  this session's turns. It read 39 against a 40 wall, so `pass` is correct -- and note that
  at 39 the production constants would also pass, so this line proves REACHABILITY, not yet
  that the narrow band is the one being applied. The crossing is what discriminates.
- Run position: Phase 1, research sealed (`cf9ba22`), planner in flight.

## 3b. What the live run has and has not done (measured from the ledger)
- Crossing 1 `22:39:30` -> `delivery_inbox_requested` -> `refused` 78 s later (the 60 s TTL
  defect, fixed in `691c09a`).
- Crossing 2 `23:06:01` -> `delivery_inbox_requested` -> **no outcome row was ever written**,
  yet the `/compact` DID land. So delivery works and its ledger leg is missing: a `sent`
  row for crossing 2 does not exist, which `report` cannot count. OPEN.
- Then `recovered` x3 (23:51, 00:16, 00:51), each re-typing the SAME `/compact` line ->
  "Not enough messages to compact" x2 -> `stalled` x9 across nine hours. That is the
  defect `64ec155` closes.
- The focus argument is NOT the defect: all three invocations carry
  `<command-args>focus on ...</command-args>` in the transcript. The arg was delivered
  every time and the host honoured it.

## 3c. Sealed later the same day (2026-09-19)
- `f2462ee` **the confirmation could not see the row it looks for.** A resume is confirmed
  by a Stop hook running at the END of the turn the resume began, and that turn has already
  written its whole tool output ahead of the row. Against a 262,144 byte window the
  `/gsd-autonomous` row sat 598,625 bytes from the end of a 5.8 MB transcript, so every Stop
  chain read False. The coupling is perverse -- the more the turn did, the further back the
  row -- so it failed exactly in the case it exists for. Aperture now sized to the question
  (8 MB) and cheap because only lines CONTAINING the command are parsed. Real-bytes proof
  False -> True with a never-issued control still False. GSDLR 68 -> 72; mutation 71/72;
  restore SHA-256 `1B95B8AF`.
- `62da863` **Phase 2 COMPLETE.** Startup (process spawn -> deadline clock) = **42 ms**
  median, n=5, at 15.5% free RAM; deadline 11,500 ms, cap 15,000 ms. Neither the cap nor the
  clock is the defect; the 19.4/17.1 s readings predate the deadline that fixed them
  (`15,173 -> 6,595`). The TOTAL (3,589 ms median) is a LOWER BOUND -- synthetic payload, so
  transcript-proportional hooks including `jit_skill_loader` did less than a real turn.
- `1b2d6f4` + `b788b25` **Phase 3 COMPLETE.** HR-CONT-01..03, PR-CONT-01..04, T-CONT-01..07
  in the UKDL with their ids; the global router's "SendKeys presses Enter when Cursor is
  foreground" sentence replaced by the exact-or-refused delivery that actually happens.
- `c5f82c0` Phase 1 Task 1: `tools/two_pane_drill.py` + `tools/test_two_pane_exactness.py`.
  `probe` 7/7 live, red branch driven in two scenarios (absent / unreadable / too-old all
  distinct). `arm`/`fire`/`observe` UNEXERCISED -- they need an operator-started subject.
Coherence anchor: GSDLR 72, GSDAC 26, CWIRE 14 -- green at `f2462ee`.

## 4. Not proven (do not claim)
- `report` is still UNPROVEN: two crossings, zero `resume_confirmed`. The aperture fix
  removes the reason the confirmation kept failing, but NO confirmed resume has been
  observed since -- the next crossing is what tests it.
- No real delivery through `orca-exact` (GSDX-C08); Orca is not running on this host.
- No live two-pane drill (GSDX-C09) -- Phase 1 Tasks 2-3, blocked on the operator step.
- Phase 2's TOTAL is a lower bound; the straggler under a real transcript is unmeasured.

## 5. Do not re-litigate without new evidence
Low context is not compaction. Focus is not identity. `accepted` is not consumed. A turn
that has not ended has not reached the Stop chain -- an empty watchdog heartbeat for a live
session is that, not a dead guard. But TWO ended turns without a `resume_confirmed` is not
that, and on 2026-09-19 it was a real defect (`f2462ee`) -- "pending" is only honest until
the next Stop chain has run.

## 5b. Two unversioned files this work depends on
`~/.claude/hooks/auto-compact-sendkeys-daemon.ps1` (the 300 s inbox TTL) and
`~/.claude/CLAUDE.md` (the corrected router sentence) are edited live and tracked by nothing.
`hooks/hook-dispatcher.js` IS mirrored in the repo and both copies carry the startup
instrument. Losing the first two loses the fixes silently.

## 5c. The UKDL carries another producer's uncommitted rows
1,031 malformed CEPS auto-append rows sit uncommitted in `vault/knowledge_base/ukdl-universal.md`
and grow while you work. Committing that file with a plain pathspec takes them ALL under your
message. Defect recorded in `vault/lessons/ceps-autoappend-keys-are-not-tools.md`; Owner
decision was to leave them in place. If you must commit the UKDL: back it up byte-exact,
`git checkout --` it, append only your lines, commit, then restore the block and verify the
CEPS row count is unchanged.

## 6. Next actions
1. Let the run execute the roadmap's phases; honour every trailing-line instruction the
   watchdog returns (`/compact ...`, then exactly `/gsd-autonomous`).
2. After the next crossing, read `report` -- that is the first real test of `f2462ee`.
3. Then Phase 1 (two-pane drill), Phase 2 (prompt-chain deadline), Phase 3 (UKDL
   promotion + the stale router line), Phase 4 (reap the seven stale markers).

Start: read the spec, then this file, then action 1. Update this file after each sealed unit.
