# Retrospective — Claude Power Pack

A living record. Newest milestone first; cross-milestone trends at the end.

---

## Milestone: v1 — continuation-proven-live

**Shipped:** 2026-09-21
**Phases:** 5 | **Plans:** 2
**Closeout:** verified · **Audit:** `tech_debt` (0 blockers)

### What Was Built

A run that survives its own context wall: crosses it, compacts, and re-enters
itself through a continuation typed into the session that owns the pane — or
into nobody at all. Session-scoped autocompact thresholds so a running session
can narrow its own wall; a terminal-inbox transport that never consults focus or
window title; a confirmation that counts a resume only when the transcript shows
it was really submitted; and a marker reaper that reads the session's own clock
rather than a file's mtime.

### What Worked

- **Letting the gate be produced rather than written.** The acceptance gate was
  defined as something the run does to itself, not an artifact to author. The
  final crossing closed it while the milestone was being audited. Nothing about
  that could have been faked by an edit, which is precisely why it is worth
  something.
- **Probing a hook's preconditions instead of writing its row.** The last
  `resume_confirmed` was owed by `context-watchdog.py:800`. Rather than record
  it, its preconditions were probed read-only with the hook's own predicate and
  a control (`/this-was-never-typed` → False), the probe said WOULD-CONFIRM, the
  turn ended, and the hook wrote it. The evidence stayed the hook's.
- **Class-representing drills paid out.** Phase 4's admission gates use a
  synthetic fixture. When phase 5 deleted the two real ghost files those gates
  had originally been written around, the detector did not lose its subject —
  7/7 after the deletion. A drill pinned to the real files would have gone
  vacuous at exactly the moment it mattered.
- **Refusing to route around a denial.** Three classifier denials landed on
  prose *recording* an already-authorized deletion. Stopping after the second
  and reporting, rather than trying a third shape or reaching for PowerShell,
  cost one round trip and kept the boundary meaningful. The same edits were then
  accepted unchanged — so the denials were session posture, not content, which
  is only knowable because nothing was forced through.

### What Was Inefficient

- **A stale measured claim was restated across four artifacts.** "crossings 2,
  confirmed 0" was carried forward from a pre-compaction summary into
  `05-SUMMARY.md`, `STATE.md` and three commits, while `report` already read
  `crossings 3, confirmed 1`. The instrument was one command away the entire
  time. The commits were left standing with the wrong figure and corrected in
  place, because the correction belongs where a reader will look.
- **The same shape recurred twice more** — `05-SUMMARY.md` calling the fifth
  debt open after it was fixed, and the certification's C7 reading NOT YET.
  Three instances of one failure in one milestone: **a document is written once
  and the code keeps moving under it.** Neither re-reading nor good intentions
  caught any of them; an instrument re-run at the moment of the claim caught all
  three, and the third was caught by a subagent rather than by me.
- **Two ANTI-THRASH blocks**, both from three consecutive edits to one file
  without an intervening read. Both were avoidable by consolidating.
- **My own gate carried the defect it was written to catch.**
  `V-GSDLR-INBOX-ROW-NAMES-PRODUCER` re-stat'd the marker to rebuild a cid built
  from the transcript's mtime, and failed against a correct row.

### Patterns Established

- **Derive, don't recompute.** A second record of one event reads its value back
  from the first (`gsd_autorun_marker.py:253`; now `write_trigger`'s `kind`).
- **A partial step 7 has two terminal states and both are bad** — both steps or
  neither, with a rollback if the second throws.
- **Mirror direction is invariant `repo ← global`**, because the global copy is
  the one that runs, so syncing that way adopts rather than clobbers.
- **The turn that emits a compact line does no further tool work.** Bought with
  a nine-hour deadlock: the extension defers while the session is busy, and
  further tool work spends the daemon's 310 s budget.
- **Supersede; never rewrite a historical verification.** `01-VERIFICATION.md`,
  `04-VERIFICATION.md` and the certification all carry their original text with
  a dated supersession above it.

### Key Lessons

1. **A claim about a measurement decays silently.** Re-run the instrument at the
   moment of the claim. Three separate artifacts in this milestone said
   something true when written and false when read.
2. **The confirmation of an event belongs to whatever observed it.** Writing it
   yourself converts evidence into assertion, and nothing downstream can tell.
3. **A false premise is worth measuring.** Phase 4's entire value was showing
   that its brief — "seven markers are armed for dead sessions" — was wrong.
4. **A gate that compares files on disk cannot speak about a loaded module.**
   `INBOX_PASS=6/6` and "the extension is live" are different claims.

### Cost Observations

- Model mix: Opus throughout (architecture, verification, adversarial reading).
- Sessions: 4 crossings within one long session, 2 of them confirmed resumes.
- Notable: the milestone's own mechanism absorbed part of its cost — the run
  compacted and re-entered itself twice instead of being restarted by hand.

---

## Cross-Milestone Trends

| milestone | phases | closeout | audit status | blockers |
|---|---|---|---|---|
| v1 continuation-proven-live | 5 | verified | tech_debt | 0 |

**Recurring failure class (1 milestone, 3 instances):** a written record
outliving the state it describes. Watch whether v2 reduces it; the candidate
countermeasure is that any document asserting a measured figure names the
command that re-derives it, beside the figure.
