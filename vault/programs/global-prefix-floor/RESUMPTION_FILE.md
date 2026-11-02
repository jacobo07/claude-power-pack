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
  under %TEMP%). K1 ABORTED SAFELY: the trust dialog appeared. Trust is NOT inherited from the trusted `C:/Users/User/AppData/Local/Temp`
  entry, and the driver correctly refused to type into the dialog.
  Fix before K2: in the driver, after creating the temp root, set `~/.claude.json` `projects["<root with / separators>"].hasTrustDialogAccepted=true`
  (back up first, write a temp file + os.replace; read HR-001 in `vault/hard_rules/HARD_RULES.md` first: agent-owned global config).
  Then run it in the background: `python vault/programs/global-prefix-floor/gpf_cr29_kclear.py vault/programs/global-prefix-floor/gpf-cr29.json K2`.

## Next
1. Apply the trust fix, run K2, then record CR-29 (fresh-agent recovery: done.txt == token) and CR-15 (seconds/tokens to first correct action) in LAPTOP_RESULTS.md; commit.
2. Make `vault/programs/ctx-rent-x/done_gate.py` read CR-11/14/15/29 from `gpf-l1-successor.json` / `gpf-cr29.json` instead of hardcoding UNKNOWN; run it; commit.
3. Report to the Owner. Open debt: repo CLAUDE.md diet (blocked by another pane's uncommitted edit), l6 driver defects, CR-09/10/13 unbuilt, GEX44 mission BLOCKED (live ~/.claude apply on GEX44 is an Owner decision).

## Start
Read LAPTOP_RESULTS.md, then do Next 1.
