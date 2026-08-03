# REPORTS_INVENTORY — cross-repo report sweep, 2026-08-03

## Method, and why the first two attempts were wrong

1. **Full-tree `Get-ChildItem -Recurse`** over `Cursor Projects\` timed out at
   5 minutes — it walks `node_modules` before any filter applies.
2. **`git ls-files` per repo** (respects `.gitignore`, so `node_modules` is
   never walked) returned in seconds: **1626 name matches**. Too broad — the
   21 TUA-X worktrees duplicate every tracked path, and *GEO-audit* matched
   678 times because its rounds are named `R###` and its repo name contains
   "audit".
3. **Collapsed to parent repo + filtered to mtime >= 2026-07-04**: 529.

**mtime is not a recency signal in worktree-heavy repos.** Every InfinityOps
match carries mtime `2026-08-03T12:35` and every TUA-X block `2026-07-10T15:02`
— those are branch-checkout touches, not edits. Recency below is taken from
round number and git history, not from the filesystem.

## Repos holding actionable reports

| Repo | Matches (collapsed) | Verdict |
|---|---|---|
| GEO-audit | 410 | **Signal.** `docs/operator-actions/` = 144 human-actionable runbooks. |
| TUA-X | 76 | Noise. Corpus-governance `PART_*` dataset content, not pending actions. |
| InfinityOps | 29 | Noise. Doctrine/vault records; mtime is a checkout artifact. |
| CostaLuz Lawyers | 3 | **Signal.** `docs/haven/build/api-audit.md`. |
| kobicraft-panel | 3 | **Signal.** design-system gap audit. |
| AKOS | 5 | Post-hoc delivery reports (record, not request). |
| kobicraft-web | 1 | **Signal.** `docs/khrs/TIME_GATE_AUDIT.md` (STOP #1). |
| Jacobo | 1 | Process doctrine, not a pending action. |
| Computer Personal Ops | 1 | `disk-audit/disk-audit-plan.md`, stale (2026-07-08). |

## GEO-audit — `docs/operator-actions/` (144 files, R7 → R218)

These are the only reports in the sweep whose content is *a request for
someone to do something*. The frontier set:

| Round | File | Type | Status |
|---|---|---|---|
| R218 | `cls-emergency-runbook-R218.md` | CWV / CLS emergency | **OPEN — 17 months** |
| R217 | `r217-ws1-ws2-zero-impression-diagnosis.md` | Index diagnosis | Closed (32/32 clean) |
| R217 | `r217-ws3-regression-diagnosis.md` | Regression | Needs read |
| R217 | `r217-ws4-census-and-content.md` | Census/content | Needs read |
| R216 | ×2 | — | **EXCLUDED per brief** |
| R215–R209 | 10 files | census / hub-links / snippets | Sprint-internal, agent-executed |
| R208 | `homepage-copy-R208.md`, `ws2-ws3-new-content-R208.md` | Content | Likely closed |
| R207 | `homepage-audit-R207.md` | Audit | Needs read |
| R204 | `cwv-final-runbook-R204.md` | CWV | **Superseded by R218** |
| R201/R202 | `sprint-publication-audit-R20{1,2}.md` | Publication audit | Needs read |
| R199 | `maria-signoff-status-R199.md` | Human sign-off | **OPEN — blocked 14d** |
| R199 | `nie-redirect-runbook-R199.md` | Redirect decision | **OPEN — same block** |
| R188 | `MARIA-S72-REVIEW-QUEUE-CONSOLIDATED-R188.md` | Legal §72 review | **OPEN — live pages** |
| R179 | `livechat-greeting-runbook-R179.md` | CWV | **Superseded by R218** |

### The dominant finding: one action, written three times

`cls-emergency-runbook-R218.md` states it plainly — *"This runbook is the
third time this action has been written up (R179, R204, now R218)."*

Re-measured live today, not carried over:

- GSC reports **CLS > 0.25 on 493 URLs**, up from 304 in May (**+62%**),
  first detected 21-mar-2025 — **17 months unresolved**.
- Throttled Lighthouse mobile trace, homepage, zero interaction:
  `#chat-widget-container` (LiveChat auto-greeting) = **CLS 0.960, 72% of
  total 1.325**. R178 measured 0.578–0.960 on the same profile — **it got
  worse, not better**.
- CrUX field data (the actual ranking signal): **p75 = 0.62, SLOW. 61.7% of
  real mobile visits experience Poor CLS.**
- All three probed URLs return identical origin-level field data → **the "493
  URLs" is one site-wide widget, not 493 problems. One toggle moves all of
  them.**
- Fix: **disable the LiveChat auto-greeting. ~1 minute. Only María can do it.**

### The second blocker: a sign-off that was asked for and never chased

`maria-signoff-status-R199.md` — the R194b email asking María to choose
between `#29131` and `#34404` was sent **2026-07-20T16:03:43Z**
(messageId `19f8044d5c77532b`). The system has send-email but **no
inbox-read capability**, so no round since has been able to check for a
reply. Two decisions are frozen behind it (the #29131/#34404 consolidation
and R198's NIE-duplicate redirect). Unblocking is one inbox check by Jacobo.

### The third: legal review on pages that are already live

`MARIA-S72-REVIEW-QUEUE-CONSOLIDATED-R188.md` — supersedes the R163→R169
queue, whose six items *remain open*. Pages carry a `COSTALUZ-72-UNREVIEWED`
marker **while live**. TIER 0 is `#26529` force-majeure: five FAQPage answers
scored PARTIAL grounding (0.49–0.67), none confidently grounded; the tooling
labelled it RENDER_VISIBLE and the report says that label **overstates the
confidence**. TIER 1 is `#29131` (~2,391 impr/28d) where two tax-fact errors
were corrected and are **now live pending María's confirmation**.

## Other repos — one report each

**CostaLuz Lawyers** · `docs/haven/build/api-audit.md` · `estado: COMPLETO`,
2026-07-31. Verified live: `crm.costaluzlawyers.com` → 200, but
`api.costaluzlawyers.com` and `wa.costaluzlawyers.com` → **403 (SiteGround
default, DNS never repointed to Hetzner)**. This *confirms* the deployment
runbook's "OFFLINE INTENTIONAL" and *contradicts* the session prompt that
claimed brain API and WhatsApp companion were already live. Also flags a
security-shaped gap: `GET /crm/clients` returns the full client list to any
valid staff Bearer, so ClientOS needs a new `GET /client/me` that resolves
from token identity — never a list.

**kobicraft-web** · `docs/khrs/TIME_GATE_AUDIT.md` · marked **STOP #1**,
read-only, no code changed. Finding: night mode has **two independent
triggers, neither with a time gate** — `prefers-color-scheme: dark` in
`app/globals.css` (lines 129, 194, 204, 279) fires regardless of local hour.
The six commits since are i18n and content work, so **the fix was never
applied**.

**kobicraft-panel** · `docs/DESIGN_SYSTEM_GAP_AUDIT.md` · read-only, baseline
`920c1d8` 2026-07-14. Opens by correcting its own brief: STOP #2 as written
is a no-op and STOP #3 was ~70% already done. What it *did* find — one
correctness bug and one design-system inconsistency introduced by the
dash-wide glass rollout — has an unverified fix status.

**AKOS** · `governance/DELIVERY_REPORT_GAP_CLOSURE.md`,
`DELIVERY_REPORT_SEGMENTER_REPAIR.md` · post-hoc delivery records. These
report work already done; they are not requests.

**Computer Personal Ops** · `disk-audit/disk-audit-plan.md` · 2026-07-08,
repo clean since 2026-07-13. A plan, not a finding.
