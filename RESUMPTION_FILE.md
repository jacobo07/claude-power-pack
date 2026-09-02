# RESUMPTION — effective state, and the barrier that consumes it

**Repo** `~/.claude/skills/claude-power-pack` · **branch** `frontier28/session-2026-08-26`
· **worktree** isolated. The installed tree is on `feature/knowledge-acquisition` with
**217 dirty files** and unpushed commits — another pane, heavily active. Do not switch,
reset, merge into, or check out over it.

**Thesis.** The install location is a git working tree, so the bytes that run are whichever
branch a pane last checked out. Committed, pushed, and even merged to `main` is not
delivered.

## State

`origin/main` carries this branch. **SHADOWED is still 5** — re-measured after the merge.
Integration and delivery are two events.

What now exists beyond the detector: `is_done` was a weighted score at threshold 70, so
delivery could fail and the deliverable still pass on the other checks. Replayed against a
claim a prior session really made, the score model returned **OQS 100 and Done**. Contracts
now carry **preconditions that veto beside the score**; `code` and `deploy` declare one,
`docs` and `test` deliberately do not. Applicability is by declared claim scope — `source`,
`repository` and `integration` pass over a shadowed artifact; only `runtime` and `production`
owe proof. `is_done` and `is_done_for_tier` inherit it without any caller being edited.

The 4×-recurring PowerShell trap has **two** broken edges, both measured: the pattern was
absent from `CORRECTNESS_TRAPS` (fixed), and that registry's only consumer,
`cascade_check_bash.js`, is registered with matcher `Bash` while the trap occurs on
PowerShell (not fixed — Owner-sovereign). Verdict: **DETECTED, NOT YET REACHABLE.**

`predictive-governance-debt` is **PASS** (was red across sessions) — fixed with real
oracles, not a baseline reset. 13+9 carried offenders are older suites, untouched.

Coherence anchors, all exit 1 by design:
`tools/mirror_unpaired_audit.py --quiet` → 5 SHADOWED ·
`tools/capture_liveness.py` → PowerShell unobserved ·
`tools/test_correctness_traps.py` → 8/10, the two reds naming the matcher.

## The one Owner action

`python tools/migrate_capture_surface.py --apply` — widens two registrations whose code
already accepts PowerShell. It buys **prevention**, not just observation: it is the same
matcher that keeps `cascade_check_bash` blind. HR-001 makes `settings.json` Owner-sovereign
permanently; that is governance working, not a task to keep forwarding. The tool exists only
on this branch, so it needs the installed tree on `main` first.

Do **not** copy `hook-dispatcher.js` to `~/.claude/hooks/` — measured obsolete, and it would
delete `closer-guard.js` from production.

## Next three actions

1. When the concurrent pane is idle, put the installed tree on `main`; then
   `mirror_unpaired_audit.py` SHADOWED must fall to 0.
2. Then `migrate_capture_surface.py --apply`; `capture_liveness.py` must flip to COVERED and
   `test_correctness_traps.py` to 10/10.
3. Then watch the corpus broaden past `bash:*` — 103 of 118 today while Bash is 27.6% of
   command traffic.

## Start instruction

Run the three anchor commands above; their output is the current truth. Re-measure any
forwarded Owner action before executing it — two of the last three were wrong, one harmful.
And state a completion claim's SCOPE: `certify()` will tell you if you have overclaimed.
