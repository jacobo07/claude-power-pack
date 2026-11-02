# RESUMPTION_FILE -- Global Prefix Floor (GPF), laptop coordinator

Repo `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition` (shared tree, 1,200+ foreign dirty
paths: commit ONLY your own paths and verify `git log -1`). Plan `vault/plans/global-prefix-floor-2026-11-02.md` (Owner "y go").
Evidence: `vault/programs/global-prefix-floor/LAPTOP_RESULTS.md` (read it first; it is the record of everything below).

## Sealed (do not redo)
- W0 GEX44 floor split (mission m-6d478d311437, branch worktree-gpf-run 0d301018): CLAUDE.md chain 27.3K, rules 13.9K of 131.9K.
- Laptop doctrine diet LIVE: call-1 78.4K -> 71.9K (-6,444, N=4/arm), quality 6/6; backup `~/.claude/backups/gpf-apply-20261102T160717`.
- CCR successor-frontier fix LIVE: release 0.1.0-39151f03 (source 83069706). Clean A/B S5/S6: frontier basis=capsule. CR-11/14 PASS.
- Harness traps fixed + in memory: pin --session-id; reader thread; never plan mode; never type into an unfinished turn.

## In flight
- CR-29/CR-15 probe `vault/programs/global-prefix-floor/gpf_cr29_kclear.py` (real /kclear -> /clear -> /kresume in a temp repo
  under %TEMP%). K1/K2/K3 ABORTED SAFELY at the trust dialog. K3 raw screen PROVES it is the real dialog ("Yes, I trust this
  folder", default "No, exit"); trust is not inherited from the trusted `%TEMP%` entry.
  The agent-side pre-trust write was DENIED by the auto-mode classifier (Self-Modification) = HR-001 class; not worked around.
  Shipped instead: driver reuses a fixed, marker-gated root `%TEMP%/gpf-cr29-probe` when it exists (else mkdtemp, aborts safely),
  and `gpf_cr29_owner_trust.py` = the Owner-run half (backup, merge one key, read back).
  K4 DONE (Owner ran gpf_cr29_owner_trust.py from an external PowerShell; `!` runs had no effect): CR-29 PASS, CR-15 PASS 91 s.
  Rerun: `python vault/programs/global-prefix-floor/gpf_cr29_kclear.py vault/programs/global-prefix-floor/gpf-cr29.json K5`.

## Next
1. DONE: capsule fixes (seal_capsule writes latest/ pointer; named goal file's verbatim Next items win). test_rollover_obligations 8/8
   (red pole 6 FAIL on HEAD), review APPROVE. K5: 0 failed certifies, frontier basis `capsule`, 51 s, processed -53% vs K4 (n=1).
2. DONE: GEX44 diet LIVE (GEX44_APPLY.md): smoke green, attributable -13,786/call-1 (-13.8%, n=2). Backup /home/kobii/.claude/backups/gpf-apply-20261102T183952.
3. DONE: done_gate reads CR-11/14/15/29 from receipts.
4. DONE (W3, spec vault/specs/gpf-resident-admission.md, Owner "y" 2026-11-02): floor_regression_gate.py --budget
   (absolute per-layer ceilings read from the session window) + resident_budget.json (measured +10%); live: exit 0,
   rules ceiling 8238 -> exit 1, 8239 -> exit 0. FLOOR 69/69, drill 22/22. done_gate CR-33..36 all PASS;
   W0 receipt imported verbatim from 9ecdf2cfd. done_gate now 28 pass / 1 fail (CR-31) / 7 unknown of 36.
5. OWNER QUESTION (not done): re-baseline incremental-cognition floor/reference.json (2026-10-05, pre-diet) with
   --write-reference --replace? K-prg.md says re-baseline is the Owner's call; tools/wake_check.py (scheduled) reads it.
Open debt: repo CLAUDE.md diet (another pane's uncommitted edit), l6 driver defects, CR-09/10/13 unbuilt (Phase 5),
CR-16/07/22/30 unknown, unattributed -13.8K GEX44 floor change, GEX44 dangling doctrine pointers, GEX44 budget file.

## Start
Ask the Owner item 5; otherwise the next build is Phase 5 (CR-09/10/13) and needs its own plan.
