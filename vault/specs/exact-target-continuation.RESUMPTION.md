# RESUMPTION -- exact-target continuation (GSD X)

## 1. Identity
Repo `~/.claude/skills/claude-power-pack`, branch `feature/knowledge-acquisition`. Spec
`vault/specs/exact-target-continuation.md`. Thesis: a continuation reaches the session that
owns it, or nobody; a lifecycle state is claimed only from its post-condition.

## 2. Sealed (commits)
- `9676617` spec. `5d17c1e` C1: "compaction" requires a transcript `compact_boundary` newer
  than the cycle reference; one resume per boundary; fail closed.
- `01211b5` C2/C3: `tools/continuation_transport.py` (Orca: `ORCA_PANE_KEY` -> `terminal
  list` -> `terminal send --terminal <handle>`, receipts, job files).
- `fd87e39` C4: one door `_dispatch_continuation`; non-Orca -> terminal inbox (`e5ed2d3`,
  other pane); live daemon refuses by default, legacy foreground only with
  `CPP_LEGACY_FOREGROUND_SENDKEYS=1`; `no-own-window` deleted.
Coherence anchor: live daemon sha256 `EB8D00B9...`; suites CTRUTH 15, CXT 28, CWIRE 14,
ACPS 33, GSDLR 46, GSDAC 26, CWHB 6 -- all green at `fd87e39`.

## 3. Not proven (do not claim)
- No real delivery through `orca-exact` yet (GSDX-C08). Orca's
  `%APPDATA%\orca\orca-runtime.json` was missing while the app ran -> `runtime_unavailable`.
- No live two-pane drill (GSDX-C09); proven only on a fake Orca CLI.
- UserPromptSubmit chain: 19.4 s and 17.1 s against a 15 s cap with an 11.5 s internal
  deadline. It discards hook output, not the prompt. Cause unmeasured (hypothesis: time
  before the deadline clock starts, under RAM starvation).
- The last Stop chain of 8178f7d0 took 82 s.

## 4. Do not re-litigate without new evidence
Low context is not compaction. Focus is not identity. `accepted` is not consumed. The
inbox and Orca transport are both exact; the fallback to foreground is the defect.

## 5. Next actions
1. When `orca-runtime.json` exists, run one `/cpp-gsd-long` in an Orca terminal with
   `CTXWD_TEST_THRESHOLDS`; require `resume_confirmed via=orca-exact` in the ledger.
2. Measure the UserPromptSubmit chain start-to-deadline gap (one bounded run).
3. Promote `vault/lessons/exact-target-continuation.md` entries into
   `ukdl-universal.md` once its concurrent edit is committed; update the stale
   "SendKeys daemon presses Enter" line in the global CLAUDE.md Context Pressure section.

Start: read the spec, then this file, then do action 1. Update this file after each unit.
