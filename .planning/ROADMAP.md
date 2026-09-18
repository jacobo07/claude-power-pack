# ROADMAP — Long-run continuation proven live

**Milestone:** v1 `continuation-proven-live`

The machinery for an unattended multi-cycle run exists and is tested: the
autocompact watchdog, the autorun marker, the resume gate, the exact-target
continuation transport and the terminal inbox. What has never been produced is
a run that actually crossed a context wall twice and came back both times —
every armed run on this host reads `UNPROVEN` or `NO_CROSSINGS`. These phases
close that, and the debts the attempt exposed.

## Milestone acceptance (not a phase — the run produces it by running)

The narrow-wall proof is not work to plan; it is what happens to this run while
it executes the phases below. The milestone is accepted when
`gsd_long_run.py report --session <sid>` returns **PROVEN**: at least two
crossings, each followed by a resume the transcript shows was really submitted,
typed by the terminal inbox that owns the pane rather than by a human.

## Phase 1: Two-pane exactness drill

Prove the exactness claim the transport was rebuilt for: with two live sessions
in two panes, a continuation armed for session A is submitted into A's own
terminal and never into B's, and a request whose owner does not answer is
refused rather than typed into whatever window has focus.

Done: both panes' transcripts read; A carries the resume line, B carries none;
one deliberately unowned request is ledgered `refused` with its reason.

## Phase 2: UserPromptSubmit chain deadline

The prompt chain measured 19.4 s and 17.1 s against a 15 s cap with an 11.5 s
internal deadline, so hook output is discarded on a loaded host. Measure the
gap between the chain starting and its deadline clock starting, under a known
memory condition, and say whether the cap or the clock is the defect.

Done: one bounded run with the interval measured and reported in milliseconds,
against a recorded free-RAM figure, with the cause named rather than guessed.

## Phase 3: Promote the exact-target lessons

Move the `vault/lessons/exact-target-continuation.md` entries into
`vault/knowledge_base/ukdl-universal.md`, and correct the stale line in the
global router that still says the SendKeys daemon presses Enter — it refuses by
default since the transport became exact.

Done: the UKDL carries the rules with their ids, and the router sentence
describes the delivery that actually happens.

## Phase 4: Reap the stale autorun markers

Seven markers are armed for sessions that no longer exist, each holding a
project's GSD config at retuned thresholds. Reap them by name and restore every
project config no live marker still needs.

Done: `gsd_long_run.py status` lists only live runs, and each reaped project's
`.planning/config.json` is back to what it held before arming.
