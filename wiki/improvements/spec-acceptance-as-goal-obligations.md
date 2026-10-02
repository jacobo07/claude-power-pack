---
type: improvement
created: 2026-10-02
updated: 2026-10-02
sources: [2026-10-02-state-centric-reality-scan, 2026-10-01-sdd-internal-inventory, 2026-10-01-cbr-internal-inventory]
status: DISCUSSING
effort: M
---

# Spec acceptance becomes goal obligations; "done" becomes a judge receipt

## Problem

Two earlier audits found the same hole from opposite ends:

- SDD-OS checks a spec exists, never that its acceptance runs. AC "executable / mapped 1:1 to
  tests" is ◐, "done names the evidence" ◐, "effectiveness measured" ✗ ([[sdd-os-gap-analysis]],
  rows 7, 30, 33); 9 of 64 criteria satisfied in the done-gate audit (cited there).
- CBR: "APPLIED needs evidence, not a tick" ◐, "per-entry outcome metric" ✗
  ([[cbr-gap-analysis]], rows 21, 29).

Meanwhile the [[goal-spine]] now does exactly the missing half, live: pinned gates, re-run by an
independent judge at the final tree, re-derived on every read, re-gated by a scheduler when the
tree moves ([[goal-spine-connect-not-build]]).

## Proposal

`gsd_x_goal.py from-spec <spec.md>`: read the spec's front matter (`id`, `covers`, `owner_go`) and
its `## Acceptance` block; declare a goal whose intent quotes the spec's approval line and whose
obligations are the acceptance commands, each pinned to the files it runs. Mark autonomous. Then:

- "T2 done" = judge PASS on that goal, not a claim in chat.
- A later commit that breaks the acceptance re-opens the goal within one sweep pass: regression
  detection for every spec, for free.
- Per-spec outcome data accumulates in goal logs (the measurement SDD #33 lacks).

## Open questions (for the Owner)

1. Does a spec's `owner_go` line count as the Founder's intent for a goal, or must each goal be
   declared by the Owner? (Goal-spine rule: intent is verbatim Founder input.)
2. Scope: new specs only, or also the 33 existing ones (most have no runnable acceptance)?
3. Cost: each autonomous goal adds gate runs per tree move; cap per repo?

## Evidence that it is cheap

This session's three specs each name one runnable acceptance command
(`vault/specs/goal-sweep-scheduled.md`, `vault/specs/goal-observe-ralph-mission.md`,
`vault/specs/economic-rollover-trigger.md`). No new engine capability needed: declare, oblige,
autonomous, judge all exist and are LIVE.

Related: [[sdd-os]], [[constitutive-baseline-ratchet]].
