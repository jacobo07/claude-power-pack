# BCAP-2: Absorption campaign (the 9 open absorption backlogs) — plan of record

Owner, 2026-11-19, laptop pane 2cf9ec6d: "continua esa mision de absorcion hasta terminarlo todo". Answers to the arm questions:
- Vehicle: **unattended campaign on GEX44** (same mechanism as campaign 1, `vault/plans/ascension-backlog-capability-2026-11-16.md`).
- Budget: **120M authority + 3 x 40M top-ups** (a top-up only after commits outside `.planning/` since the last grant).
- Ruflo: **"corregir todos los holds de seguridad e instalar la version segura con ellos pero bien hechos"** = fix every
  security HOLD in CPP-owned code, then install the hardened version. This is the separate approval the Ruflo spec requires,
  scoped to an isolated GEX44 sandbox (see Phase 9). Laptop activation stays a LAPTOP_STEP.

## Scope (from `vault/plans/deferred-backlog.md:1763-1778`, verified open on 2026-11-19)
State check on the laptop at 942d5352: no row is marked closed; names searched in modules/tools/skills/hooks/commands/agents.

| # | Backlog file (vault/backlog/) | Item | State at arm |
|---|---|---|---|
| 1 | 2026-10-11_diagnosing-bugs-causal-proof-ratchet.md | CPP-DBG-001 | BACKLOG / NOT STARTED |
| 2 | 2026-10-11_tdd-evidence-first-vertical-slice-ratchet.md | CPP-TDD-001 | backlog only |
| 3 | 2026-10-11_addyosmani-agent-skills-selective-absorption.md | CPP-AGSK-001 | backlog intent only |
| 4 | 2026-10-10_animejs-design-absorption.md | Anime.js into PP Design | backlog only (451530a8) |
| 5 | 2026-10-13_synsation-ux-patterns-absorption.md | Synsation UX patterns | backlog only (b8a98796) |
| 6 | 2026-10-02_cdio-modern-saas-styles.md | 3 modern SaaS styles | partial: F1 PROVISIONAL (97d08474) |
| 7 | 2026-10-21_cdio-brand-identity-logo-absorption.md | Brand Identity & Logos | audit only (9ec46cdd), NOT DONE |
| 8 | 2026-10-30_cdio-21-design-resources-universal-absorption.md | 21 design resources, 36 gates | NOTHING ABSORBED |
| 9 | 2026-10-11_ruflo-security-absorption-sovereign-updates.md | CPP-RUFLO-001 | HOLD |

Out of scope (separate rows, not absorption): Orca relay routing, Meta Astryx (origin NOT FOUND, LAPTOP_STEPS 2 of campaign 1).

## Binding laws (campaign 1 laws 1-8 apply verbatim; additions)
1. Each backlog file is the item's spec. Its "first action" (Reality Scan) runs first; do not re-derive what campaign 1
   already proved (inventory, ledger, webslice, CCF integrity, promotion gate, B5/B7).
2. REUSE > EXTEND > MERGE > CONNECT > GENERALIZE > BUILD. Owners to extend, never duplicate: CRAIF/OSR (DBG), test-gaps/
   mutation/done_gate (TDD), skills + capability_runtime (AGSK), modules/cdio + vault/knowledge_base/cdio + design-md
   (Anime.js, Synsation, SaaS, 21 resources), modules/ccf (Brand), modules/backlog_autopilot ledger (state of every row).
3. Licence gate before any copy: MIT/Apache/BSD/CC0 may be adapted with attribution (NOTICE); AGPL/GPL/unknown/proprietary
   = principles only, never code or assets. Record the licence in the ledger row.
4. An item is CLOSED only when its own "measurable completion criteria" are met with recorded exit-0 evidence, a
   both-poles gate `tools/test_bcap2_<item>.py`, liveness reachability (wired or declared), and its ledger row moves to
   ACTIVATED with execution evidence. Anything short of that is PARTIALLY_PROVEN with named residuals, never DONE.
   A criterion that needs the laptop plane, a paid call or a human is a named residual + LAPTOP_STEPS entry.
5. Network: read-only fetch of upstream sources (git clone at a pinned commit, WebFetch of docs) is allowed for the
   absorption phases. No paid provider/API calls, no publishing, no push, no PR, no merge, no deploy.
6. Ruflo exception (Phase 9 only): npm/git install is allowed **only** inside an isolated sandbox dir on GEX44, pinned
   version + lockfile + integrity hashes, no credentials or tokens in env, no hooks/daemons registered in any real
   `~/.claude`, no network egress beyond the package registry during install, nothing auto-started. Every HOLD in the spec
   must have a CPP-owned correction with a RED->GREEN gate BEFORE the install; a HOLD that cannot be corrected keeps the
   install refused and becomes a named residual.
7. When the backlog row closes, update its line in `vault/plans/deferred-backlog.md` with the closing commit
   (the index's own rule) and the backlog file's Status line.

## Plane
GEX44 clone `~/missions/bcap2`, worktree `.claude/worktrees/bcap2`, branch `mission/bcap-2-run`, base = laptop
`feature/knowledge-acquisition` committed HEAD at arm. Laptop tree is NOT the base (thousands of foreign dirty paths).
Laptop-plane facts go to `vault/programs/bcap-2/LAPTOP_STEPS.md` as BLOCKED-ON-LAPTOP.

## Closeout
`python3 vault/programs/bcap-2/done_gate.py` aggregates the nine item gates + liveness + ledger; HANDOFF at
`vault/programs/bcap-2/HANDOFF.md` with per-item verdict (CLOSED / PARTIALLY_PROVEN + residuals).
