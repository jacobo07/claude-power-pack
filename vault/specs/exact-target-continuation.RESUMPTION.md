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
Coherence anchor: GSDLR 60, GSDAC 26, ACPS 33, CXT 28, CWIRE 14 -- all green at `9190432`.

## 3. This run's state
- Session `37cfb187-ec05-43db-b57d-4bdcb5625362`, marker armed 12 cycles / 24 h,
  command `/gsd-autonomous`, mission `continuation,autocompact,thresholds,resume,exactness`.
- Wall narrowed to **35,40,30** -- crossing at 40% used, rearm under 30%, a 10-point band.
- Route measured live: `terminal-inbox`, exact, no focus needed. An owned-but-expired probe
  was refused by the extension that owns this pane; a foreign-ancestor control was ignored.
- Verdict to reach: `gsd_long_run.py report --session <sid>` = **PROVEN** (>=2 crossings,
  each with a confirmed resume).

## 4. Not proven (do not claim)
- No live crossing yet. Every marker on this host still reads UNPROVEN or NO_CROSSINGS.
- No real delivery through `orca-exact` (GSDX-C08); Orca is not running on this host.
- No live two-pane drill (GSDX-C09) -- that is Phase 1.
- UserPromptSubmit chain: 19.4 s and 17.1 s against a 15 s cap. Cause unmeasured -- Phase 2.

## 5. Do not re-litigate without new evidence
Low context is not compaction. Focus is not identity. `accepted` is not consumed. A turn
that has not ended has not reached the Stop chain -- an empty watchdog heartbeat for a live
session is that, not a dead guard.

## 6. Next actions
1. Let the run execute the roadmap's phases; honour every trailing-line instruction the
   watchdog returns (`/compact ...`, then exactly `/gsd-autonomous`).
2. After the second confirmed resume, read `report` and record the verdict here.
3. Then Phase 1 (two-pane drill), Phase 2 (prompt-chain deadline), Phase 3 (UKDL
   promotion + the stale router line), Phase 4 (reap the seven stale markers).

Start: read the spec, then this file, then action 1. Update this file after each sealed unit.
