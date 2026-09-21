# ROADMAP — Long-run continuation proven live

**Milestone:** v1 `continuation-proven-live`

The machinery for an unattended multi-cycle run exists and is tested: the
autocompact watchdog, the autorun marker, the resume gate, the exact-target
continuation transport and the terminal inbox. What has never been produced is
a run that actually crossed a context wall twice and came back both times —
every armed run on this host reads `UNPROVEN` or `NO_CROSSINGS`. These phases
close that, and the debts the attempt exposed.

## Phases

Added 2026-09-21. This list did not exist, and its absence was not cosmetic:
`phase.complete` marks a phase by ticking its checkbox here, so with no
checkboxes it could record nothing. Run against phases 2, 3 and 4 it reported
`roadmap_updated: false` and changed only a timestamp, while every index kept
reporting all four phases incomplete against four committed VERIFICATION.md
files. The roadmap could not express what the evidence already said.

- [x] **Phase 1: Two-pane exactness drill** - the continuation reaches A's own terminal and never B's (completed 2026-09-21)
- [x] **Phase 2: UserPromptSubmit chain deadline** - is the cap or the clock discarding hook output (completed 2026-09-21)
- [x] **Phase 3: Promote the exact-target lessons** - the CONT rules into the UKDL, the router sentence corrected (completed 2026-09-21)
- [x] **Phase 4: Reap the stale autorun markers** - reap by the session's own clock, not the file's (completed 2026-09-21)
- [x] **Phase 5: Close the continuation debts** - the three this milestone exposed and did not fix (completed 2026-09-21; debt 3 answered by the Owner at the checkpoint, digests in 05-RESIDUE-INVENTORY.md)

Added 2026-09-21, and the reason is mechanical rather than editorial. With
4/4 phases complete, `gsd_long_run.py preflight` REFUSES to arm a run
(`nothing to run: 4/4 phases complete`, `gsd_long_run.py:588`) — so the
acceptance gate below had become unreachable by construction: it is produced
by a run, and no run could be armed. The gate is not satisfied by planning
this phase; it is satisfied by the crossings that executing it produces.

## Phase 5: Close the continuation debts

Three debts this milestone surfaced and left open. Each is small, named, and
independently verifiable — the point is that they are real work, not filler
to generate crossings.

1. **Ledger cwd fidelity.** `gsd_autorun_marker.py:253` passes raw `args.cwd`
   to `ledger_append` while `:98` passes `resolve_cwd(cwd)`. A relative `cwd`
   in a ledger row cannot be resolved by any later reader — the same class of
   defect `marker_project` already REFUSES rather than resolves
   (`gsd_long_run.py:749`).
2. **A red branch for the argument-tail delivery.** The `/compact` arg-tail
   submission added in `f771f55` is driven by nothing. It lives in the VS Code
   extension, unreachable from the Python gates, so it rests on one Owner
   observation. If a future build changes the completion-popup behaviour the
   tail becomes a stray message in every crossing and no test says so.
3. **Residue.** `tools/gsd_long_run.py.pre-phase-advance`, the
   `gsd-autorun-intent-ghost-*.json` fixtures, and
   `gsd-autorun-37cfb187-….json.pre-phase4` — deletions, so they wait for an
   explicit decision rather than being swept.

Done: 1 and 2 land with a driven red branch each; 3 is either deleted with
the Owner's word or recorded as a kept decision with its reason.

## Acceptance gate (not a phase — the run produces it by running)

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

**Plans:** 1/1 plans complete

Plans:

- [x] 01-PLAN.md — live two-pane drill: real extension, real second Cursor
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

## Phase 4: Reap the stale autorun markers

Implemented in `d0477b8`. Status lives in the checklist above, not in this
heading: a name that carries its own verdict is read as a name by every parser
that consumes it, which is why this phase displayed as
`Reap the stale autorun markers — COMPLET…` in `/gsd-progress` and in STATE's
`current_phase_name`.

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
