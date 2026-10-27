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

**Next 3 actions.**
1. F0b: read the real contracts of UCR-CIF, Constitutive Baseline and UWCP (`vault/specs/tla/`, `.planning/workstreams/{ucep,cognitive-reuse}`, `docs/superpowers/specs/2026-09-24-family-baselines-design.md`); decide state location, business-vs-repo identity and the recommend-vs-act boundary; amend the spec.
2. F1: Founder Kernel, a versioned business state with the evidence-class vocabulary mapped to CPP's canonical one, plus a deterministic capability router.
3. Regression safety (G13): suites of neighbours (`secret_firewall`, `repo_identity`) and `python modules/liveness/reachability.py` before any "done".

**Start.** `Set-Location` to the worktree, `git log --oneline -3`, run the three suites above, continue at action 1.
Budget plan 240k tokens (telemetry UNKNOWN unless measured). Recovery cycles max 12, campaign max 24h.
