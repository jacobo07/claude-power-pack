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

**Next 3 actions.**
1. G14 inheritance: show a build task for a NEW feature (not a business prompt) is not burdened, and that the Owner can `revert` the auto entry; decide whether PII-refusal also belongs in a non-business family.
2. G13 breadth: run the wider CPP suites (`tools/test_*.py` touching `secret_firewall`, hooks, installer) and compare liveness against a clean baseline commit.
3. F7: UKDL entries for I-1, I-2, I-3 (incident, root cause, regression test, guard, vault, classification), then the second-order meta-analysis and the two-layer handoff. If the Owner supplies a metrics source, run the F5 loop for real first.

**Start.** `Set-Location` to the worktree, `git log --oneline -3`, run `tools/test_founder_os*.py`, `tools/test_family_baselines.py`, `tools/test_family_injection.py`, continue at action 1.
Budget plan 240k tokens (telemetry UNKNOWN unless measured). Recovery cycles max 12, campaign max 24h.
