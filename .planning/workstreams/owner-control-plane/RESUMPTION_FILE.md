# RESUMPTION — owner-control-plane

**Identity.** Worktree `C:\Users\User\Apps\pp-owner-control`, branch `ocp/owner-control`, goal `owner-control-plane` (programme 22M, applied from capital packet sha 0878ac15a056). Thesis: model exhaustion must never remove Owner control; capital changes run providerless and wake the work.

**State.** Sealed: plan `vault/plans/owner-control-plane-2026-10-19.md`, workstream files here, capital applied, goal declared (L1 4M). Pending: all 11 phases in `ROADMAP.md`. Coherence anchor: `git log -1` on this branch plus `programme-status --goal owner-control-plane`.

**Decisions.** Extend `hooks/econ_admission.js` and `capital_authority` — no new hook lane. Closed grammar only; no model parses capital. The econ-safex programme is changed only by an Owner-typed message. Automatic-succession tranche problem is solved in Phase 6.

**Update 2026-10-20 (pane fc51683d).** Mission m-c80a568be8b7 is terminal HALTED (epoch 3); a relaunch needs a fresh arm and was not done. Goal ledger is healthy: programme 72M, L2 cap 54M, remaining ~52.2M. Phase 1 was NOT sealed; the semantic breaker stopped the pane. Verified for P1 (cite these): UserPromptSubmit order = econ_admission.js, then hook-dispatcher UserPromptSubmit-chain, then orca claude-hook.cmd (settings.json:778-815). econ_admission is registered from the MAIN checkout path, so worktree edits are not live until merged (settings.json:785). Capture runs inside econ_admission BEFORE decide(), so a block does not stop it (econ_admission.js:144-152). Verbs are only `econ status|detach` (econ_admission.js:29). econ_admission is out of the chain on purpose (hook-dispatcher.js:595-600). `modules/provider_routing/succession.py` does not exist. Still OPEN: read ledger.py lease_open/set_programme (ledger.py:194,400), read owner-capital-ctx-rent-2026-10-11.md, re-measure econ-safex (programme 32M, 70M unapplied), list Decision Plane entry points.

**Next three actions.** 1) Phase 1: finish the OPEN list above, write `vault/programs/owner-control-plane/P1-reality.md` with file:line evidence, update STATE.md. 2) Phase 2: grammar module and V-OCP-GRAMMAR tests. 3) Phase 3: router in econ_admission.

**Start.** Read this file, `ROADMAP.md`, the plan; run `git status --short` and `programme-status`; continue at the first unchecked phase. Update `STATE.md` and this file after every sealed phase.
