---
phase: 1
name: Two-pane exactness drill
status: complete
verification_status: passed
date: 2026-09-20
---

# Phase 1 — Two-pane exactness drill

Both legs the phase asked for are now driven on real bytes. The refusal legs
were produced on 2026-09-19 and recorded in `.planning/01-EVIDENCE-refusal-legs.md`;
the positive leg, which that file closed as `UNEXERCISED`, is produced here.

## What the phase asked for

> both panes' transcripts read; A carries the resume line, B carries none; one
> deliberately unowned request is ledgered `refused` with its reason.

## The positive leg — A carries it, nobody else does

Judged by the **product's own** predicate, `gsd_long_run.user_issued_command_since`,
over an 8,388,608 B tail — not a re-implementation, because a copy of that
matcher was wrong on its first day earlier in this milestone.

Artifact: `twopane_d2.out` (scratchpad), window opening 19:51:04Z.

```
live panes in the last 6 h: 33
  PANE A 37cfb187  received=True   (17,269,047 B)
pane B panes that got the line: 0
V-TWOPANE-POSITIVE: PASS
```

## Two corrections the run forced, both against my own instruments

**The windows were nested.** `twopane_positive.py` was pinned to a single
`SINCE` of 13:11:22Z. That window *contains* the 19:52 delivery, so its PASS
could not say which delivery satisfied it — it was one observation wearing the
costume of two. `SINCE` now takes an argv bound and the attributable run is the
19:51:04Z one. The earlier window is retained but is **not** independent
evidence.

**My submission counter was looser than the product.** Its first version asked
`NEEDLE in text` and returned 16 submissions. Fourteen were prose: Stop-hook
feedback rows quoting the command, compaction-continuation summaries, and the
`/cpp-gsd-long` skill body itself. Tightened to the product's shape — a
`<command-name>` wrapper, or text *starting with* the command — it returns two:

```
2026-09-19T09:08:06.552Z  <command-name>/gsd-autonomous</command-name>
2026-09-20T19:53:03.644Z  <command-name>/gsd-autonomous</command-name>
before 19:00Z : 1     after 19:00Z : 1
V-SUBMIT-TWO-DELIVERIES: PASS — two submissions in disjoint windows.
```

Artifact: `count_submissions.out`. Worth stating in the direction it actually
ran: the product predicate was the strict one and my probe was the loose one.
The instrument was the defect, not the subject.

**The duplicate pane.** Pane A resolved under two project directories at
identical size. Measured rather than assumed: `same inode (hardlink, one
file): True`. One file under two names, so the pane-B denominator is 31
distinct panes, and the duplicate is incapable of masking a hit.

## The refusal legs (2026-09-19, unchanged)

- **Owned and answered:** a request whose `claude_pid` has no session file →
  `decide()` returns `session-unreadable`, acked in 0.28 s by this window
  (`window_cwd` = this project). Refusal carries `decide()`'s own reason.
- **Unowned:** ancestors present in no process table → no ack in 15.04 s, the
  request untouched. This silence means something **only** because leg A was
  answered in the same run; an extension that was not polling produces leg B's
  result exactly.
- Ledger also carries a live `terminal inbox refused: expired` at
  `2026-09-20T19:14:58Z` — a real crossing refused rather than typed.

Every refusal returns before the `term.sendText` branch, which is reachable
only through `action: "send"`, so a request built to be refused cannot produce
a keystroke.

## What this phase does NOT establish

The two submissions above are the evidence for the **milestone** acceptance
(`report` = PROVEN), and that verdict is the ledger's to write, not this
phase's. At the time of writing `report` reads PARTIAL: 7 crossings, 1
confirmed. The second `resume_confirmed` is written by the Stop chain on the
turn that follows the 19:53:03Z submission, so it is pending rather than
missing — the same shape as the first confirmation, which landed at
2026-09-19T09:30:37Z.
