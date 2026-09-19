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

## 3d. Phase 4 sealed, and the aperture fix proved itself (2026-09-19, later)
- **`report` moved UNPROVEN -> PARTIAL**: 3 crossings, and crossing 2 (23:06:01) carries
  `resume_confirmed` at `09:30:37` -- the first confirmed resume this estate has ever
  recorded. That is `f2462ee` working on real bytes, not a test. Crossing 3 (10:10:22) is
  the compaction this session came through; its confirmation is still owed.
- `d0477b8` **Phase 4.** The roadmap's premise ("seven markers armed for sessions that no
  longer exist") is FALSE: zero of nine markers are reapable. Three defects in the
  instruments instead. (1) The reap clock read the transcript's file **mtime**, which
  `custom-title` / `cost-state` rows -- carrying no timestamp of their own -- advance
  without the session speaking; measured drift up to **19.0 h** on a 48 h threshold.
  (2) Liveness now reads `~/.claude/sessions/<pid>.json` and answers `live` or `unknown`,
  **never `dead`**: `fa6961b6` had no row at 11:40 while conversing 0.00 h earlier, and
  acquired one at 12:24 under a NEW pid (53548, CLI 2.1.278). (3) `cwd` was stored as the
  caller typed it -- `"."` in 8 of 9 markers -- and `Path(".").is_dir()` is true
  everywhere, so ONE project reaching `ALL_COMPLETE` would have unlinked every other
  project's marker and restored the wrong config. Arming absolutises it; `marker_project()`
  refuses a relative one. GSDLR 72 -> 87/87; mutations 83/87, 85/87, 85/87, 86/87, the
  last of which SURVIVED its first run (the gate asserted on the helper's return rather
  than on what `write_marker` stores) and was re-pointed. Restores SHA-256 verified.
- **Nothing was reaped, deliberately**: no marker qualifies, and a purge run on a rule
  written the same hour tests nothing. `sweep --dry-run --explain` now names the clause
  holding each of the nine.
- **`d0477b8` carries two hunks that are not mine.** A concurrent session added
  `PHASE_STALL_MINUTES` + `_phase_advance_ok()` to `tools/gsd_long_run.py` and the
  "ARMING IS NOT STARTING" banner to `tools/gsd_autorun_marker.py` while this work was in
  flight; commit isolation is file-granular. Their bytes are intact. The commit message
  names the first; this file names both, so neither is lost by being mis-titled.

## 3e. The live drill, and the certificate (2026-09-19, later still)
- `e2acb69` **the two-pane drill, hardened by running it.** Three defects, none visible from
  the tests: (1) `arm` identified its subject as "the one new session since I started
  watching" and, on a host whose registry grew 25 -> 31 rows during one drill, adopted a
  colleague's `/ultra plan mode` pane -- it aborted only because a session registers BEFORE
  its transcript exists, so an accident saved the run and nothing in the rule did. Identity
  is now the NONCE, read from a TYPED user row. (2) A session with no transcript is simply
  not a candidate yet. (3) `arm` returned PASS on a subject in Windows Terminal
  (`claude.exe -> powershell.exe -> WindowsTerminal.exe`) that no window can own, and `fire`
  spent its 10 s producing a refusal INDISTINGUISHABLE from the deliberate one;
  addressability is now a precondition, checked against the terminal registry the extension
  publishes. Pane B (this session) is recorded at fire time and gated by
  `V-TWOPANE-B-UNTOUCHED`; a run with no B returns HARNESS-FAILED. TWOPANE 4/4, mutations
  3/4 x3, restores SHA-256 verified.
- `d55c7c7` T-CONT-08..11 and PR-CONT-05 in the UKDL, spliced around the other producer's
  block: working copy proven to be exactly HEAD + 90,507 bytes / 337 `ceps_` rows, committed
  alone (52 insertions, 0 deletions), block restored, arithmetic closed 561+337=898.
- `293ef15` **`vault/specs/cpp-gsd-long.CERTIFICATION.md`** -- the Owner-requested
  certificate. Seven claims; five PROVEN, C5 proven on its refusal side only, C7 (the
  command's own done-gate) PARTIAL. It states the failure honestly on page one.
- Phase 4's rule would have degraded THIS run's marker (`cwd: "."`), so the marker was
  absolutised in place, backed up first, every other field preserved.
- **Context at 38-39 % against a 40 % wall** as of 12:27Z, climbing ~1 point per turn: the
  fourth crossing is what C7 needs, and it arrives by working, not by engineering.

## 4. Not proven (do not claim)
- **C5 positive side: no line has EVER been observed typed into a subject's own terminal.**
  It needs a Claude session inside a Cursor integrated terminal; the drill cannot create one
  and the unattended attempt (a `folderOpen` task in a new Cursor window) was DENIED by the
  auto-mode classifier as `Create Unsafe Agents`. Recorded, not worked around.
- `report` is PARTIAL, not PROVEN: 3 crossings, 1 confirmed resume. PROVEN needs a SECOND
  crossing whose resume the transcript shows was really submitted.
- Phase 4 changed the reap rule and **no reap has ever executed under it** on real state.
  The gates drive it on fixtures; the live population has no qualifying subject.
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
3. Phases 2, 3 and 4 are COMPLETE. Phase 1 Tasks 2-3 (the two-pane drill) are the only
   remaining phase work and they are blocked on the operator opening a second terminal.

Start: read the spec, then this file, then action 1. Update this file after each sealed unit.
