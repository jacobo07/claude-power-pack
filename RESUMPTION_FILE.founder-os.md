# RESUMPTION — Founder OS v1 campaign
(The repo-root `RESUMPTION_FILE.md` belongs to a different programme, gsd-long; do not edit it for this campaign.)

**Identity.** Extend Founder OS v0 (PR #10, `jacobo07/claude-power-pack`) into a repo-isolated business-intelligence
capability whose impact claims are observed, and whose proven lessons raise the CPP baseline for later builds.
Work ONLY in this worktree: `C:\Users\User\.claude\skills\claude-power-pack-wt-founder-os`, branch
`feat/founder-os-v1-20261027` (tracks the PR branch). The main checkout is on another branch with other panes'
dirty files; never edit there. Never merge to `main` without the Owner's explicit word. The Owner approved the plan
inline on 2026-10-27. That approval does NOT cover spending, publishing, contacting people, using credentials, or
irreversible external changes.

**State (sealed).** F0 audit done in commits `3847d92cc` and `44c41f03a`. Real findings, all fixed with regression tests:
PII and Stripe keys passed the firewall; amounts without currency; duplicate `action_ref`; torn last line after a crash;
dead-writer lock. Evidence, all exit 0: `python tools/test_founder_os.py` 17/17, `tools/test_founder_os_f0.py` 7/7,
`tools/test_founder_os_cli.py` 4/4. Installer discovery verified (`_repo_population('commands')` holds the command).
Spec: `vault/specs/founder-os-v1.md` (`covers:` set; amend it BEFORE each phase's first edit).

**State (pending, not claimed).** Global activation: `~/.claude/commands/cpp-founder-round.md` does not exist and the
installed PP checkout lacks `tools/founder_round.py` until this lands, so gate G2 is NOT passed. Gates G3-G14 not run.
Shared Secret Firewall (`modules/secret_firewall/detector.py`) still lacks a Stripe pattern; Founder guards locally.
Deferred with reasons (in the spec): chain-truncation anchor; `authorization_ref` verification (needs an owner-grant store).

**Decisions.** Reuse `modules/repo_identity`, installer discovery, UCR-CIF / `strength_ladder` / UKDL for promotion.
No second identity engine, backlog or ratchet platform. UNKNOWN stays UNKNOWN; INCONCLUSIVE is never PASS.
`/cpp-gsd-long` is NOT armed: it runs `/gsd-autonomous` over a GSD roadmap, and this worktree has none for this campaign.
Arm it only after `/gsd-new-milestone` inside this worktree, and only if context pressure demands it.

**Also sealed.** F0b decisions are in the spec (commit `40bd18c0e`): the Constitutive Baseline machinery is LIVE
(`vault/tower/families|baselines`, `tools/family_baseline.py`, injection via `modules/gsd_x/cli.py`), UWCP is the
Universal Workstream Continuity Plane (TLA+ model, not a business-state concern). F1 Founder Kernel
(`modules/founder_os/kernel.py`, `python tools/founder_round.py --repo . kernel`), suite `tools/test_founder_os_kernel.py` 8/8.

**Incidents for the UKDL step (F7), each needs root cause, regression test, guard and a vault entry.**
- I-1 Secret Firewall passes Stripe keys and PII (fixed locally; shared detector still open).
- I-2 `{"status": X, **row}` lets the row's own `status` overwrite X (STALE reported as OBSERVED). Found by the kernel
  test, fixed in `kernel.py`. Class: dict-spread key-order override. Candidate Trap; a grep-able detector is feasible.
- I-3 Anti-thrash hook blocks a 3rd Edit on a file without a Read between; plan one consolidated Edit per Read.

**F6 first slice sealed (G10 evidence, not yet G14).** Family `business_round` (`vault/tower/families/business_round.json`),
predeclared alone in `4b59d4d32` BEFORE the family existed; B0 = 5 Owner-sealed entries with verified citations; B1 = first
mission-derived entry (`business_round-journal-refuses-customer-data`, status `auto`, awaiting Owner `review`). A fresh
prompt receives it through the real CLI and the real node hook (`tools/test_founder_os_ratchet.py` 8/8). Existing gates
extended, not weakened: `test_family_baselines.py` 22/22, `test_family_injection.py` 26/26. Limit: the promoted entry cites a
repo-relative file, so `verify_origin` needs cwd = the PP root. Liveness: `modules/liveness/reachability.py` exits 1 on 71
pre-existing orphans, none Founder (not compared against a clean baseline).

**F2, F3, F4 sealed** (commits `d4a514085`, `b198ec67a`, `df548b56f`): compiler (`modules/founder_os/compiler.py`, 10 tests),
assessment (`assessment.py`, 9), evolution (`evolution.py`, 9). New commands on the CLI: `context --lens`, `assess`, `backlog`.
Founder Skill is UNVERIFIED (not on disk, no web match for an 11-skill repo); the Owner must name the repository. F5 connector
probe is in the spec: Vercel connected, Web Analytics NOT enabled on `kobicraft-web`, no GA/Ads/CRM, so the Real-World Loop is
BLOCKED on an Owner action. Gate suite `tools/test_founder_os_gates.py` (G9 no-network/authorization, G11 two businesses,
G12 fresh agent and documented-commands-exist) 6/6.

**Anti-thrash rule learned (I-3):** a `Write` counts as an attempt, so after creating a file only ONE Edit fits before a Read.

**Later commits (all sealed, local):** `43b77bc79` gate suite (`tools/test_founder_os_gates.py`, 8 tests), `1bbfc5855` G14 revert +
ordinary-prompt tests (`test_founder_os_ratchet.py`, 10 tests), `597af64dd` spread fix in `_append` + AST detector + UKDL entries
(section "Founder OS v1" in `vault/knowledge_base/ukdl-universal.md`), `e7135ca79` gate ledger in the spec. Suites: 82 Founder tests,
all exit 0. G13: 12 of 15 neighbouring suites pass; `test_install_population`, `test_mirror_parity`, `test_hook_mirror_identity`
fail identically on the clean PR base `d698513cf` (pre-existing drift). **G12 verified by a genuinely fresh agent** (2026-10-27): it
followed this file, reproduced every exit code and got `discover / Research / business_model` from `kernel`; it found this file stale,
which is why this block exists.

**Owner choice 2026-10-27: the business repo for the first real round is `C:\Users\User\Desktop\Cursor Projects\GEO-audit`.**
It is a dirty working tree with other sessions' changes (never edit or commit there from this campaign); its nested `geo-seo-os/`
is its own git repo. Its client hard rules win every conflict (flat fees, no invented data, English/Spanish only). SEO/GEO decisions
there must cite the corpus per `~/.claude/rules/seo-geo-corpus-methodology.md`. Founder OS writes only to `~/.claude/state/founder-os/`.

**GEO-audit reconnaissance (read-only, observed 2026-10-27, nothing recorded in any journal yet).** Business per its CLAUDE.md:
an SEO/GEO/AIO audit service whose reference client is CostaLuz Lawyers (flat fees). Sources found:
- `data/costaluz-seo/measurement.db` (modified 2026-03-28): the 6 expected tables exist and ALL have 0 rows (`gsc_daily`,
  `gsc_query_daily`, `ai_citations`, `lead_attribution`, `content_actions`, `technical_audit`). Empty schema = no stored measurements; it
  is NOT evidence that no measurements exist elsewhere.
- Authentic GSC exports: `clients/costaluz/icp-R146/gsc-mvt-baseline-R146.json` (sha256 prefix 62fc911bbeca16f8, generated 2026-06-21,
  window 28d: site clicks 3561, impressions 616791); `clients/costaluz/r270-dnv-leg2-gsc.json` (b5466d7468a5af1c, window
  2026-06-18..2026-09-16, 90d, ONLY 32 queries: clicks 61, impressions 5607); `geo-seo-os/data/costaluz-seo/gsc_api/monthly_traffic.json`
  (4c3f8fb5ff8f93c1; 2025-04..2026-03 monthly clicks 6419 to 1674, impressions 397k to 330k).
- DO NOT compare R146 with R270 as a before/after: different windows (28d vs 90d) and R270 is a 32-query subset, not site totals. A
  valid comparison needs two same-window, same-scope exports; otherwise close the round INCONCLUSIVE.
- Data-quality defects in `monthly_traffic.json`: month 2025-12 appears twice (identical rows) and 2026-02 is missing; 2026-03 looks partial.
  Record these as CONTRADICTED/UNKNOWN facts, not smoothed.
- Hard rules in force there: no invented data, client hard rules win, SEO/GEO decisions cite the corpus (SG-IDs). The working tree is
  dirty with other sessions' work: never write or commit inside it.

**Next 3 actions.**
1. F5 real round on GEO-audit: `init`, `start` with `--repo "C:\Users\User\Desktop\Cursor Projects\GEO-audit"`, then record only what the sources above support (`source_ref: repo:<path>#sha256:<hash>`), including the measurement.db emptiness and the monthly_traffic defects as observations; keep client PII out of summaries (the journal refuses emails, IBANs, cards, phones).
2. Run `kernel`, `assess`, `backlog` on that journal and close the round honestly (`INCONCLUSIVE` unless a before and after measurement exists).
3. Second-order meta-analysis and the two-layer final handoff; push decision is still the Owner's.

**Start.** `Set-Location` to the worktree, `git log --oneline -3`, run `tools/test_founder_os*.py`, `tools/test_family_baselines.py`, `tools/test_family_injection.py`, continue at action 1.
Budget plan 240k tokens (telemetry UNKNOWN unless measured). Recovery cycles max 12, campaign max 24h.
