---
type: improvement
created: 2026-10-02
updated: 2026-10-02
sources: [2026-10-02-state-centric-reality-scan]
status: IDEA
effort: S
---

# Mutation drill anchors rot between runs

## Observed

`tools/test_gsd_x_goal_mutation.py` mutates code by exact-text anchors. Two anchors no longer
existed when it was next run, because later commits rewrote the code they target (`0ff7cf7`,
2026-09-25; `fe2be9c`, 2026-09-28). The drill reports such a case as INVALID, not a verdict, and
the suite fails its threshold, so it was visible when run. It was not run between those commits,
so for days two safety clauses had no mutation guard ([[2026-10-02-state-centric-reality-scan]]).
Repaired in `7d5b3bd`; suite now 58/58 at `738ed40`.

## Idea

Anchor validity is static and cheap: check every anchor exists in its target file without running
any suite (seconds, vs ~7 min for the drill). Run it in `record-gates` (the moment autonomy is
licensed) and in the commit path for files the drill targets. A rewrite that breaks an anchor then
fails at the commit that caused it, not at the next drill.

Interpretation: same family as [[overview]] point 5. The guard existed; nothing ran it when its
subject changed.

Related: [[goal-spine]], [[verdict-pinned-to-what-runs]].
