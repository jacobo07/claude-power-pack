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
1. SCOPED, both root causes CONFIRMED (CCR_CAPSULE_DEFECTS_SCOPE.md): (a) the /kclear seal path never writes `latest/<rkey>.json`
   (`session_checkpoint.seal_capsule` lacks `write_latest_pointer`), so the frontier is `unreadable`; (b) `compile_capsule` lets the
   model's `pending` paraphrase override the goal file's verbatim Next items. Python-only fixes plus V-LATEST-KCLEAR and 4 V-OBL gates,
   then K5 must certify on the first try with basis `capsule`. Governing spec: vault/specs/interactive-context-rollover.md. Awaiting Owner go to implement.
2. DONE: GEX44 diet LIVE (GEX44_APPLY.md): smoke green, attributable -13,786/call-1 (-13.8%, n=2). Backup /home/kobii/.claude/backups/gpf-apply-20261102T183952.
3. DONE: done_gate reads CR-11/14/15/29 from receipts; 24 pass / 1 fail (CR-31 dirty shared tree) / 7 unknown.
Open debt: repo CLAUDE.md diet (another pane's uncommitted edit), l6 driver defects, CR-09/10/13 unbuilt, unattributed -13.8K GEX44 floor change, GEX44 dangling doctrine pointers.

## Start
Read CCR_CAPSULE_DEFECTS_SCOPE.md, then do Next 1 once the Owner says go.
