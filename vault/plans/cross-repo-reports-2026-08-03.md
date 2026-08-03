# Cross-repo report inventory + action backlog — 2026-08-03

Institutional backup of the STOP #1 delivery. Full artifacts:

- [`cross-repo-2026-08-03/PROJECT_INVENTORY.md`](cross-repo-2026-08-03/PROJECT_INVENTORY.md)
- [`cross-repo-2026-08-03/REPORTS_INVENTORY.md`](cross-repo-2026-08-03/REPORTS_INVENTORY.md)
- [`cross-repo-2026-08-03/ACTION_BACKLOG.md`](cross-repo-2026-08-03/ACTION_BACKLOG.md)

## Scope

57 directories under `C:\Users\User\Desktop\Cursor Projects\` — 20 git repos,
24 worktrees, 13 non-git. 1626 raw name matches reduced to 529 after
collapsing worktrees and filtering by recency; the actionable set is
**GEO-audit `docs/operator-actions/`** (144 runbooks, R7→R218) plus one
report each in CostaLuz Lawyers, kobicraft-web and kobicraft-panel.

## Two premise corrections

1. **CostaLuz is at R219, not R216.** `scripts__r219_*` changelog entries and
   `cls-emergency-runbook-R218.md` were both written today. Excluding R216
   leaves R217/R218/R219 in scope.
2. **`REMOTE_DELTA = 0 0` is unreachable for 6 of 20 repos** — GEO-audit,
   CostaLuz Lawyers, AKOS, Computer Personal Ops, kobicraft-auth and Mytilus
   have no git remote. Their gate is a clean tree, not a remote delta.

## The finding that matters

One action has been written up three times (R179, R204, R218) and is
**17 months open**: disabling the LiveChat auto-greeting on costaluzlawyers.com.
It is 72% of a measured CLS of 1.325, CrUX p75 = 0.62 (SLOW, 61.7% of real
mobile visits Poor), and all 493 flagged URLs share one origin-level number —
so one toggle moves all of them. It takes about a minute and only María can
do it.

The pattern across the top of the backlog is the same: the blockers are not
analytical. A1 needs María, A2 needs one inbox check by Jacobo, B1 needs a
legal position. More analysis produces a fourth runbook, not a fix.

## Status

STOP #1 — awaiting Owner approval of the execution set (E1, E2, B4, B5, B2)
before PASO 4. Nothing has been executed or committed in any target repo.
