# PROJECT_INVENTORY — `C:\Users\User\Desktop\Cursor Projects\`

Swept 2026-08-03. **57 directories**: 20 git repos, 24 linked worktrees
(21 × TUA-X, 3 × InfinityOps), 13 non-git folders.

Classification rule: ACTIVE = last commit within 30 days (>= 2026-07-04).
`dirty` = `git status --porcelain` line count. `b/a` = behind/ahead of upstream.

## Correction to the sweep's own premise

Two assumptions in the brief did not survive measurement:

1. **CostaLuz is not at R216.** The GEO-audit repo is at **R219**
   (`docs/changelog/scripts__r219_ws3*_*.py.md`, written today) and
   `docs/operator-actions/cls-emergency-runbook-R218.md` was written today.
   R216 is three rounds behind the frontier, so "exclude R216, it is in
   progress" excludes far less than intended — R217, R218 and R219 all
   postdate it and are in scope.
2. **`REMOTE_DELTA = 0 0` is not a reachable done-gate for most of these
   repos.** 6 of the 20 have **no git remote at all** (GEO-audit, CostaLuz
   Lawyers, AKOS, Computer Personal Ops, kobicraft-auth, Mytilus). For those,
   the gate is "clean tree / intended commits present", not a remote delta.

## ACTIVE repos (last commit within 30 days)

| Repo | Branch | Last commit | dirty | b/a | Remote | Notes |
|---|---|---|---|---|---|---|
| GEO-audit | master | 2026-08-03 | **425** | — | none | CostaLuz SEO/GEO engine, rounds R1→R219. Live concurrent work today. |
| Jacobo | hermes-phase-a | 2026-08-03 | 7 | 0/**4** | yes | KIW compendium. 4 commits unpushed. |
| kobicraft-web | main | 2026-08-03 | 0 | 0/0 | yes | Clean and synced. |
| CostaLuz Lawyers | master | 2026-07-31 | 13 | — | none | ClientOS / brain API / haven datasets. |
| TUA-X | sprint/acmf-corpus | 2026-07-28 | **240** | — | VPS ssh | 21 worktrees. Corpus-governance heavy. |
| kobicraft-panel | main | 2026-07-26 | 5 | 0/0 | yes | dirty = generated `docs/{arch,changelog,constitution,prd}` + tsbuildinfo only. |
| KobiiSpy | main | 2026-07-21 | 0 | 0/**11** | yes | Clean tree, **11 commits unpushed**. |
| InfinityOps | feat/cci-vis001 | 2026-07-14 | 9 | 0/0 | yes | 3 worktrees (bis-capab, gscfix, journal). |
| Computer Personal Ops | main | 2026-07-13 | 0 | — | none | Clean. |
| kobicraft-auth | main | 2026-07-13 | 0 | — | none | Clean. |
| AKOS | master | 2026-07-12 | 11 | — | none | Knowledge/dataset engine. |
| Mytilus Belgian Restaurant | main | 2026-07-09 | 4 | — | none | Client site. |

## DORMANT repos (last commit older than 30 days)

| Repo | Branch | Last commit |
|---|---|---|
| Regina Margherita | master | 2026-07-03 |
| system-knowledge | main | 2026-07-03 |
| infinityops-mail-studio | infinityops/base | 2026-06-28 |
| mail-studio | main | 2026-06-28 |
| Club Náutico | master | 2026-06-20 |
| LaptOps | main | 2026-05-31 |
| RAM Guard | master | 2026-05-23 |
| CPGS | master | 2026-02-20 (archived) |

## Worktrees (not independent projects — same object store as the parent)

- **TUA-X (21)**: qa, fe17, fgr-emergent, cross-angle, formula-variety,
  ooa-fbr, ucce-genome, redesign, cbin-recommend, cbin-status, waitlist-source,
  waitlist-gate, landing-intel, spend-analytics, msr, msr-market, niche-bench,
  offercap, wpr-lvs, gs-crossangle, ece-wt.
- **InfinityOps (3)**: bis-capab, gscfix, journal.

Worktrees inflate every naive file sweep — the same tracked path appears once
per worktree. All counts in `REPORTS_INVENTORY.md` are collapsed to the parent.

## Non-git directories (13)

`.governance-cache`, `Brady McCann`, `costaluz-rrss-pipeline-v2-prd-bootstrap`,
`KME Datasets`, `kobicraft-server-staging`, `Minecraft Projects`, `NexumOps`,
`Project-Template`, `UGC-v6`, `Vibe Coding Projects`, `Wii Projects`,
`_global_config`, `_sha_backup_20260228_155239`.

No version control, so no commit-based activity signal and nothing to
pathspec-scope a commit against. Out of scope for PASO 4.
