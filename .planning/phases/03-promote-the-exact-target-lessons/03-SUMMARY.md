---
phase: 3
name: Promote the exact-target lessons
status: complete
verification_status: passed
date: 2026-09-20
---

# Phase 3 — Promote the exact-target lessons

Both halves of the phase's Done condition are satisfied and both are verifiable
from committed files rather than from recollection.

## Half 1 — the UKDL carries the rules with their ids

`vault/knowledge_base/ukdl-universal.md`, spliced after `PR-CONT-05`:

```
10189: ### HR-CONT-04 — an advisory may be layered onto a load-bearing path, never swapped in
10200: ### T-CONT-12  — a rate limit bounds an advisory's noise, never its interference
10210: ### T-CONT-13  — a manual probe can consume the one-shot event it was written to measure
10220: ### PR-CONT-06 — delivery is not submission, and a spent budget is not a landed effect
```

Re-derive with `grep -n 'HR-CONT-04|T-CONT-12|T-CONT-13|PR-CONT-06'` against
that file.

The splice was **hunk-isolated**: 43 lines staged, 0 foreign. Another writer
had 92 uncommitted CEPS lines in the same file at the time, and those were left
uncommitted rather than swept into this commit. That is the file-granular limit
of pathspec scoping handled deliberately, not avoided by luck.

## Half 2 — the router sentence describes the delivery that happens

The stale claim was that the SendKeys daemon presses Enter. The global router's
Context Pressure Response section now reads that the daemon routes the line **by
SESSION id** to the terminal inbox, that it is typed only if the extension
owning that terminal accepts, that **focus is never consulted and neither is the
window title**, and that with no owning extension the request is REFUSED and
ledgered rather than typed into whichever window is in front. Foreground
SendKeys survives only as an Owner opt-in (`CPP_LEGACY_FOREGROUND_SENDKEYS=1`),
with the 2026-09-18 incident named as the reason it is no longer the default.

That is the behaviour this milestone measured on both legs, so the sentence and
the code now agree.

## Why this phase had no directory

The work landed as commits without GSD artifacts, so the projection read the
phase as not started while the content was already in the tree. This SUMMARY is
the registration, written after re-reading both artifacts — not a claim
reconstructed from memory of having done it.

## What this phase does NOT establish

Promotion is not activation. These four rules are now discoverable by id in the
UKDL; nothing here measures whether any future session actually consults them.
That is the standing `presence is not reachability` gap this estate has recorded
before, and it is not closed by writing the entries.
