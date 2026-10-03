---
name: presence-is-not-residency
description: Working-set virtualization doctrine. Use when many subjects (terminals, agent sessions, panes, tasks) can be visible while few are running: sleep, dormant and parked states, lazy restore, re-materialization on activation, remount or selection, render deferrals mistaken for a residency policy, snapshots and restore plans, pinning or retention vs materialization, identity below presentation. Core rule - a row that survives is not a released runtime; prove the ordinary path back leaves dormant subjects dormant.
metadata:
  opportunity_detector: none
  opportunity_detector_reason: coverage class none; no registered card hook and no CO-12 adapter names this skill
---

# Presence Is Not Residency

A system that lets many subjects be *visible* while only a few are *running* — terminals, agent
sessions, editor panes, remote tasks, long AI workflows — owes three separate answers, and the
first two are routinely mistaken for the third:

- **durable** — does the subject survive a crash or restart?
- **releasable** — can its expensive runtime be removed while it survives?
- **composable** — can the working set the user arranged be reconstructed later, in order, with
  each subject's identity intact?

A row that survives is not a virtualized subject. A record that lets a process resume is not
proof that nothing resumed it. **Working-set virtualization is a claim about what happens on the
ordinary path back** — opening the project, switching to it, reloading — and it holds only if that
path leaves the dormant subjects dormant until policy or the user asks for them.

## Prove it across the boundary that re-materializes

The failure is quiet by construction: release works, the row stays, every test of the release
passes. What brings the process back is a different code path — activation, remount, reveal —
written by someone optimizing something else.

So before claiming residency is controlled, **characterize the re-entry path**, and write the
characterization as today's behaviour, not the desired one. When the fix lands, the test inverts
and the diff *is* the evidence. Pair it with a control proving the mechanism you are relying on
can fire at all, or the characterization can pass vacuously.

## A render deferral is not a residency policy

Deferring mounts to save frame time looks exactly like lazy restore and is not one. Check three
things before crediting it:

- **What does it need to defer?** A deferral that requires a live runtime to cover the hidden
  subject (a watcher, a stream, a snapshot provider) cannot defer a subject that has no runtime —
  which is precisely the dormant one.
- **Does it have a threshold?** Below it, everything mounts.
- **Does it dissolve?** Many deferrals end once every subject has been revealed once, returning to
  fully-mounted semantics.

Any "yes" means the deferral is a performance tool that happens to overlap the residency question
on some inputs.

## One materialization authority, many reasons

When several reasons can keep a subject from materializing — render cost, a covering watcher, a
dormant policy, a mobile lock — they belong in **one** decision that returns *why*. Separate gates
combined by each caller will disagree, and the caller that forgets one reason wakes the subject.

Keep lifecycle states distinct inside that authority even when they produce the same "don't mount"
answer: a **parked** subject still has a live runtime and something watching it; a **dormant** one
has neither. Folding them into one flag breaks the restore path of whichever one it was not
designed for.

## Composition is its own contract

- **Identity lives below presentation.** Two rows may share a title. Anything that stores, orders,
  restores or matches rows keys them by the durable subject id, and a test with two identical
  titles is the cheapest proof.
- **Display order and revival order are different contracts.** Store both; derive one from the
  other only when the user left it unspecified, and only at capture.
- **Capability is not policy.** "Can this come back exactly?" and "should it come back
  automatically?" are orthogonal. Unknown capability stays unknown — never a default launch.
- **Capability is not authority.** A subject being restorable says nothing about whether it may be
  destroyed now; that stays with whatever already owns destructive eligibility.
- **Before reusing an existing revision counter as a capture-coherence token,** list what the
  capture must hold constant and check the counter moves on exactly that set. A fencing epoch that
  advances on runtime churn and ignores reorder is the wrong instrument however apt its name.

## Restore is interpretation, then application

- **Captured capability is evidence, not authority.** Whatever can change between save and restore
  (a transcript, a directory, a profile, a host) is re-read at restore time. A positive verdict
  needs today's world to confirm it; a negative one needs today's world to prove it; everything in
  between stays unknown, with the captured verdict kept beside it so a later attempt can be offered
  without being promised.
- **"Not found" is rarely proof of absence.** A search that covers default roots cannot prove a
  subject gone when the subject may live under another account, distro or host. Only a recorded,
  directly addressable location that the filesystem reports missing is positive evidence.
- **A valid artifact can reference subjects that are no longer actionable.** Validity of the
  container and restorability of each member are separate answers; never invalidate one for the
  other.
- **Plan purely, then apply once.** Build an inspectable plan from the artifact plus today's facts,
  then apply it in one synchronous turn after the last await, re-checking the target at that moment.
  A retry should recognise its own result (by durable identity) rather than add a second copy.
- **A sealed pointer needs a sealed referent.** If the live store rewrites or collects what the
  artifact names, the artifact must own a copy, made durable before the artifact is published.
- **An unavailable store is not an empty one.** A client with no store must say so; a fallback that
  answers a list call with `[]` tells the user they have no history.
- **Restoring composition is not materializing it.** Rows can come back with no process and a lazy
  resume handle; whether activation then wakes them is a separate authority, and measuring that is
  part of the restore's evidence, not an afterthought.

## Dormancy is positive evidence, and selection is not an open

- **The absence of a runtime is not dormancy.** A brand-new subject about to spawn, a failed one,
  and one deliberately left asleep all look identical: no process. Only a marker the lifecycle
  wrote says "leave this alone". Infer dormancy from absence and you suppress every new subject;
  the cheapest proof is a control where an unmarked subject with no runtime still starts.
- **Put the veto in the one decision every render site asks, ahead of anything that can
  dissolve.** A restriction that has a threshold, ends after a full reveal or turns off with a kill
  switch will eventually stop protecting a dormant subject if dormancy is expressed through it.
- **Restored selection is composition, not authorization.** Rehydrating "this was the selected
  row" must not count as someone asking for it to run, and a generic select action usually has
  dozens of programmatic callers — workspace activation among them. Give the selected dormant
  subject a lightweight surface with one explicit action instead of waking it on selection.
- **End dormancy at proof of success, not at the request.** Hold the request as transient state
  the persisted form drops, and clear the marker only when the runtime actually binds. A failed
  open then stays dormant across a restart instead of becoming a subject that respawns itself.
- **When the characterization you pinned earlier finally turns, invert it in place.** The diff
  between the two versions of the same test is the evidence; a new, weaker test beside a deleted
  one is not.
- **Prove "nothing started" by identity, not by count.** A population with churn — sessions from
  a moment ago still exiting — keeps a count flat while new members arrive. Capture ids before the
  step and require every new one to belong to a subject you meant to start.
- **Retention is not materialization.** "Keep this awake" (a pin) says: while it runs, don't
  reclaim it. It does not say "start it". Pinning a slept or dormant subject must change no
  runtime state, and an already-asleep subject should keep reporting as asleep rather than as
  pinned. Before treating any marker as retention, check what it already protects: a favourite
  or sort pin is presentation; Orca's tab pin already refused destructive close, so it was the
  retention intent and needed no new flag (Resource-Aware Sleep W6, 2026-09-17).

## DON'T

- **Don't infer "already lazy" from a comment on one path.** A bulk path that excludes dormant
  records says nothing about the interactive path.
- **Don't copy a live-state schema's tolerance into a sealed artifact.** Salvaging entries and
  ignoring unknown fields are right for a hot file a build owns and wrong for a manifest someone
  sealed: a salvaged manifest is not the one that was sealed.
- **Don't store the conclusion when the evidence is available.** Persist the raw launch and resume
  facts and derive identity and capability on read; an inference written once outlives the
  evidence that justified it.

## Source

Incident evidence moved to `~/.claude/knowledge_vault/rules-evidence/presence-is-not-residency.md` (2026-09-28) so it is not re-read on every call. The rule text above is unchanged.
