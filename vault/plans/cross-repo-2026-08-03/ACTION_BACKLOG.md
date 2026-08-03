# ACTION_BACKLOG — cross-repo, 2026-08-03

Priority = impact × how long it has been open × whether anything is blocked
behind it. `Executor` is the honest one: several of the highest-impact items
are **not agent-executable** — they need a human with credentials the agent
does not have. For those, the agent's real deliverable is the ask, not the fix.

## IMMEDIATE

| # | Repo | Action | Executor | Status |
|---|---|---|---|---|
| A1 | GEO-audit | **Disable the LiveChat auto-greeting.** Kills 72% of a CLS of 1.325 across all 493 flagged URLs in one toggle. Open 17 months; written up 3× (R179, R204, R218) and re-measured live today. CrUX p75 = 0.62 SLOW, 61.7% of real mobile visits Poor. | **María only** (~1 min) | OPEN |
| A2 | GEO-audit | **Check the `marialuisa@costaluzlawyers.es` thread** for the reply to the R194b email (sent 2026-07-20, `19f8044d5c77532b`). Two decisions frozen behind it: #29131-vs-#34404 consolidation and R198's NIE-duplicate redirect. The system can send but cannot read an inbox, so no round can self-unblock. | **Jacobo** (~2 min) | OPEN 14d |

A1 and A2 are the entire IMMEDIATE tier and neither is agent-executable. What
the agent *can* do this session is make them impossible to keep missing —
see E1/E2 below.

## HIGH

| # | Repo | Action | Executor | Status |
|---|---|---|---|---|
| B1 | GEO-audit | Work the §72 review queue (R188 consolidated + the six still-open R163→R169 items). TIER 0 `#26529` force-majeure needs a firm position, not a guess; TIER 1 `#29131` has two corrected tax facts **live and unconfirmed** on a ~2,391 impr/28d page. | María, agent prepares | OPEN |
| B2 | kobicraft-web | ~~Apply the KHRS time gate.~~ **ALREADY DONE — 2026-08-03 verification.** See execution log. | — | **ALREADY_DONE** |
| B3 | CostaLuz Lawyers | Act on `api-audit.md`: decide the DNS repoint for `api.`/`wa.` (both 403 today, SiteGround default), and add `GET /client/me` before ClientOS V1 — `GET /crm/clients` currently returns every client to any valid staff Bearer. | Agent + Owner (DNS) | OPEN (deferred) |
| B4 | KobiiSpy | Push 11 unpushed commits (clean tree, oldest 2026-07-21) — real work sitting only on this disk. | **Agent** | **DONE 2026-08-03** |
| B5 | Jacobo | Push 4 unpushed commits on `hermes-phase-a` (KIW DS-01 sealed + COMPLETITUD v1.0.3). | **Agent** | **DONE 2026-08-03** |

## MEDIUM

| # | Repo | Action | Executor | Status |
|---|---|---|---|---|
| C1 | GEO-audit | Read R217 ws3/ws4 and R207/R201/R202 publication audits; confirm closed or promote. | Agent | UNVERIFIED |
| C2 | kobicraft-panel | Verify the one correctness bug + one design-system inconsistency from `DESIGN_SYSTEM_GAP_AUDIT.md` (baseline `920c1d8`) are fixed on current HEAD. | Agent | UNVERIFIED |
| C3 | GEO-audit | 425 dirty files on a repo with **no remote**. Everything here exists in exactly one place. Needs a commit strategy — not a blind `git add`. | Agent + Owner | OPEN |
| C4 | TUA-X | 240 dirty files, remote is the VPS. Same exposure, larger. | Agent + Owner | OPEN |

## LOW

| # | Repo | Action |
|---|---|---|
| D1 | Computer Personal Ops | `disk-audit-plan.md` (2026-07-08) — evergreen, no deadline. |
| D2 | GEO-audit | ~190 `_commit_msg_r*.txt` / `_logs_r*.log` scratch files in the repo root, R16→R163. Housekeeping. |

## ALREADY_DONE / NOT-A-REQUEST

| Repo | Why it is not backlog |
|---|---|
| TUA-X (76 matches) | Corpus-governance `PART_*` files — dataset *content* named "audit", not pending actions. |
| InfinityOps (29) | Doctrine/vault records. Uniform mtime `2026-08-03T12:35` is a checkout touch. |
| AKOS (5) | `DELIVERY_REPORT_*` = post-hoc records of completed work. |
| Jacobo `CONTAMINATION-AUDIT.md` | Standing process doctrine for the KIW compendium. |
| GEO-audit R217 ws1/ws2 | Closed: all 32 articles indexed, 0 noindex, 32/32 self-canonical. |
| GEO-audit R179 / R204 CWV | Superseded by R218. |

## EXECUTION LOG — 2026-08-03

| # | Status | Action taken | Evidence |
|---|---|---|---|
| **E1** | **DONE** | Single send-ready message to María consolidating A1 + B1, following the established `yoast-whatsapp-msg.txt` convention (context block → verbatim Spanish message → verification → escalation). A1 is presented alone and first, with the §72 queue visually separated — burying A1 inside long documents is how it was lost three times. Sourced from all four runbooks (R179, R204, R218, R188). | `E1_mensaje_maria.md` — complete, nothing left to fill in |
| **E2** | **DONE** | Created `docs/operator-actions/OPEN_ITEMS.md` in GEO-audit with A2 fully fielded: opened 2026-07-20, registered 2026-08-03 (14 days stalled before it had a home), what is expected, why the system cannot self-resolve (send-email exists, inbox-read does not), both blocked decisions, and a **dated** closure condition. | commit `47dcf42` · 1 file changed, 83 insertions |
| **B4** | **DONE** | Tree verified clean, 11 commits confirmed, pushed. | `36631ab..d6bc185 main -> main` · REMOTE_DELTA `0 0` |
| **B5** | **DONE** | Pushed **`hermes-phase-a`**, not `main` — the brief said `main`, but that branch does not carry this work. 4 commits confirmed first. | `33bc78a..db50f1a hermes-phase-a` · REMOTE_DELTA `0 0` |
| **B2** | **ALREADY_DONE — no change made** | The complete STOP chain is in history: `1332ec6` audit [STOP1] → `9fbe6c4` implementation [STOP2] → `6b9682d deploy(web): KHRS time-gated + Pocket popup live [STOP3]`. So the fix is not merely committed, it is **deployed**. `9fbe6c4` had already applied **all four** items of the audit's §5. Verified in source, not inferred: `PHASE_BANDS` = `dawnStart 4 / duskStart 20`; `resolveMode` puts the time gate at Level 2, **above** `osDark`; all four `@media (prefers-color-scheme: dark)` blocks are gated by `:where([data-khrs-night-window])`; `prefers-contrast: more` left ungated as the P0 accessibility floor; `CircadianMode.tsx:87-89` sets and removes the attribute; `PocketSuggestion.tsx` shipped. Tree clean. | globals.css 143/208/218/297 · circadian.mjs 34-39, 114-128 |

### Correction to this backlog's own B2 entry

The STOP #1 version of this file said *"Six commits since went elsewhere; the
fix was never applied."* **That was wrong.** It was inferred from a six-entry
`git log --oneline` window, and the time-gate commit sits outside that window.
The audit document is still headed STOP #1 / read-only, which made a stale
*document* look like a stale *codebase*.

The check that would have caught it — reading the code the audit names — is the
one this portfolio's own doctrine already prescribes: the brief is the prompt,
the code is the empirical snapshot, and the code wins. Recorded here rather
than quietly amended, and **no commit was manufactured to make B2 look
executed.**

### Left deliberately untouched

- **kobicraft-web has 1 unpushed commit** (`60513e5 docs(web): deploy
  verification + KHRS i18n audit`) from a concurrent pane. Not mine, not in
  B2's scope, so not pushed — another pane's unreviewed commit is not mine to
  publish. Tree is clean, which is B2's stated done-gate.
- **Jacobo has 7 untracked paths** (`.pp-onboarded*`, `.specify/`, `CLAUDE.md`,
  `docs/`, `hermes/`). Untracked files do not affect a push; never `git add -A`.
- **GEO-audit's other 425 dirty files** — live concurrent work from another
  pane. The E2 commit was pathspec-scoped to one path and `git show --stat`
  confirms exactly 1 file.

**Deferred** with reasons: B1 (needs María, not agent work), B3 (DNS is an
Owner decision; the `/client/me` endpoint is its own spec-gated task), C1/C2
(verification passes, cheap but not urgent), C3/C4 (665 dirty files across two
repos is its own session and needs Owner input on what is intentional).

**Not touched:** R216, per the brief.
