---
name: recurring-work-cardinality
description: Recurring-work scaling doctrine. Use when adding, reviewing or shrinking a timer, poll, watcher, worker, retry loop or scheduler: what multiplies it (panes, rows, worktrees, hosts, subscribers), whether it stops when its subject stops being live, caps that move cost into latency, sharing one clock across cadences, batching the transport but not the verdict, and a shrink-only ratchet over producers. Core rule - cost follows the live or visible set, never the remembered set.
---

# Recurring Work Cardinality

A timer that costs nothing with three panes is structural debt at a hundred. The failure is
invisible at the scale anyone tests at, so it has to be made visible by construction: every
recurring producer says what multiplies it, and the list of producers that multiply with
something users grow may only shrink.

## The question to ask of every timer, poll, watcher, worker or retry loop

> **What multiplies this, and does it stop when its subject stops being live?**

Record the owner, trigger and cadence. Record the lifetime (persistent, while-active or bounded)
and the scaling (global, per-window, per-worktree, per-pane, per-subscriber ...). Record what it
does while hidden and while its subject is dormant, and any process it launches.

Some producers scale with something users accumulate: panes, rows, worktrees, hosts,
subscriptions. If such a producer never stops by itself, it either states what caps it or it is
debt.

Cost should follow the live or visible set, not the remembered set. A pane that is asleep, closed,
or hidden with nothing to watch should cost nothing.

## Inventory before optimizing

Enumerate the population structurally, then rank. The first candidate you already know about is a
lead, not a conclusion. Read each candidate's surrounding throttles before ranking it: a cadence
times a count is not a cost if something upstream caps the count.

## A cap moves cost; it does not remove it

A shared queue with a start budget turns "N panes poll N times" into "N panes each wait N times
longer". Volume is bounded; freshness is not. Pin both in a test: the total stays under the budget
**and** every subject is still reached.

A queue also outlives its producers. A task enqueued before dispose still runs after it, unless
the task re-checks its owner's liveness when it **starts**.

## Sharing has an exception

The default is one shared producer, fanned out to many consumers. A safety check made at the moment
of a destructive action is the exception: it keeps its own fresh read and is never served from the
shared snapshot. And replacing N timers with one callback that does N identical expensive queries
is not a fix.

## A ratchet over producers

- Key each site by what it **is** (file, kind, enclosing symbol), not by line. A rename re-keys it
  and forces re-classification, so debt cannot be renamed away.
- Classify every discovered site. Keep no "unclassified" baseline, or new debt hides in it.
- The debt list only shrinks: new debt fails, fixed debt must be pruned.
- Put a floor on the population, so a sweep that silently stopped matching cannot read clean.
- Give the drill a synthetic red subject, so it survives the day the real offender is fixed.
- Scheduler helpers that take a callback hide their consumers. Declare the helpers and classify
  their call sites.
- A spawn reached from a callback must be declared, and the gate checks the declaration.
- Know what the ratchet cannot judge: whether a stated bound is true. Keep dispositions in one
  diffable file, so turning debt into "justified" is a visible review decision.

## Shrinking a producer

- **Fewer timers is not less work.** One shared timer can still stat every subject every tick.
  Measure the repeated work (stats, listings, calls) at several subject counts, before and after,
  and report the timer count separately.
- **Find the real multiplier before designing.** A producer described as "per repo" may already
  be shared by a key coarser than the repo, while its sibling is the one that multiplies.
- **Polling that exists to see outside changes needs an outside-change golden.** Make the change
  from another process, never through the app's own write path. Run the golden while the subject
  is active and again after it has gone quiet.
- **A quiet tier needs a fallback and a way back.** Quiet subjects still run at a slower cadence.
  Any change they see returns them to full cadence. Mutate each half and require red.
- **A shared producer owes three answers:**
  - what happens at zero subjects (stop the timer);
  - whether a slow subject can overlap itself or stall the rest (single-flight, bounded slots, a
    release for hung runs);
  - whether one failure blinds the others.
- **Declare the shared producer's accessor as a helper**, so every new consumer that subscribes
  must be classified.
- **A UI projection is not an observation owner.** Cards, rows and tabs register subjects with one
  owner per window. Key a subject by every argument it sends, so a changed argument becomes a new
  subject and two projections of one subject ask once.
- **Share the clock, not the cadence.** Families with different freshness contracts tick on one
  scheduler, and the slower ones run every Nth tick.
- **Call the scheduler helper by name.** A helper reached through an injected parameter is
  invisible to a text sweep, and the gate reads clean.
- **A poll at its cache's TTL skips every other tick** when entries are stamped on the answer.
  Give the scheduled call a max age below the interval, and test with a lookup that takes time.
- **Parallel probes can supersede each other.** If the provider refreshes under one generation
  counter, N concurrent probes to one host return one answer and N−1 failures. Queue per host,
  run hosts in parallel, and bound each sample with a budget so a stuck probe cannot hold the
  queue. (Orca X sleep W7, 2026-09-17: proved on the host service; the 60 s tick fired its
  per-worktree listings in parallel, so it would answer only one worktree per host — inferred,
  not observed in the running app.)
- **A rate cap turns volume into latency.** Measure how long a missed event takes to notice at 1
  and 50 subjects, not only how many calls were made.
- **Per-subject cadences can share one clock by due time.** Each subject registers when it is due.
  One timer fires at the earliest, and it runs every subject due within a fraction of its own
  interval. Cadences converge on shared ticks, and no subject is asked faster than that fraction
  allows.
- **Batch the transport, not the verdict.**
  - Answers are keyed by subject identity.
  - An unanswered or failed subject is unknown.
  - Each answer is applied only through that subject's own generation fence.
  - Keep one call in flight per host, so a slow host cannot stall the others.
- **Stop at the version boundary if crossing it costs a process.** Where a peer's endpoint carries
  its protocol version, batching that leg leaves the old peer running beside a new one after every
  update. Batch the legs that ship together, and report the remaining per-subject leg.
- **Prove a backstop with the fast signal absent by construction**, and attribute the result to
  the backstop from something only that path produces.

## DON'T

- **Don't count a debounce as recurring work.** A timeout is recurring only if its callback
  reaches its own scheduler again.
- **Don't trust a text sweep's anchor without replaying it.** Diff two sweep versions and read
  what moved. The unit tests will not show you these errors.
- **Don't let an automated classifier's disposition stand unreviewed.** Classifiers told to be
  conservative still rationalise a persistent per-repo poll as "visibility-gated, so justified".
  Being paused while hidden is not a cap on the count.
- **Don't claim runtime cardinality from source.** Count producer invocations at several consumer
  counts, and after disposal.
- **Don't let a formatter launder a shared file.** Running a formatter over a file whose checkout
  was never format-clean rewrites other people's lines. Restore it and re-apply only your hunk.

## Source

Incident evidence moved to `~/.claude/knowledge_vault/rules-evidence/recurring-work-cardinality.md` (2026-09-28) so it is not re-read on every call. The rule text above is unchanged.
