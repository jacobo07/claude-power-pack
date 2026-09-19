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

**Plans:** 1 plan

Plans:
- [ ] 01-PLAN.md — live two-pane drill: real extension, real second Cursor
  terminal, real transcripts; owner-answered refusal ledgered with its own
  `decide()` reason, plus the negative control that makes B's absence mean
  something.

Planning note (source: `01-PLAN.md` § mechanism_corrections): an *unowned*
request is ledgered `refused` by `Refuse-NoExact` after the 10 s no-provider
timeout, with detail `no exact-session delivery: ...` — the daemon saying it
found no provider, not any window judging the request. The plan therefore
delivers the owner-answered refusal (`Poll-Inbox` -> `terminal inbox refused:
<decide() reason>`) as the load-bearing evidence and records the unowned case
separately as the weaker observation.

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

## Phase 4: Reap the stale autorun markers — COMPLETE (`d0477b8`)

Premise as written: *"Seven markers are armed for sessions that no longer
exist."* Measured before acting, it is false — **zero of nine** qualify under
any of the three instruments, and the reason is that each one is a proxy other
events move. The phase therefore delivered the instrument rather than a purge:
the reap clock reads the session's newest timestamped row instead of the
transcript's file mtime (measured drift up to 19.0 h on a 48 h threshold),
liveness reads the session registry and answers `live` or `unknown` but never
`dead`, and a marker's `cwd` is absolutised at arming so the sweep can no longer
resolve `"."` against itself — which would have let one project's `ALL_COMPLETE`
unlink every other project's marker.

Done: `sweep --dry-run --explain` names, per marker, the clause that held it, so
an empty sweep is distinguishable from a sweep that judged nothing; GSDLR
87/87 with four mutations driven red; no project config needed restoring because
nothing was reaped.
