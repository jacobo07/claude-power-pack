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
   rules ceiling 8238 -> exit 1, 8239 -> exit 0. FLOOR 69/69, drill 23/23. done_gate CR-33..36 all PASS;
   W0 receipt imported verbatim from 9ecdf2cfd. done_gate now 28 pass / 1 fail (CR-31) / 7 unknown of 36. 03b77e40.
5. DONE (Owner "y" 2026-11-03): incremental-cognition floor/reference.json re-baselined from post-diet session
   bcf0a0bc (total 182,303 chars; memory_global 7,871, rules 8,239). Old one (2026-10-05) was already exit 2 for
   wake_check (layer_absent:other:deferred_tools_record). Self-check exit 0; wake_check gate cmd exit 0.
   KNOWN FLAP: --project-dir picks the newest transcript by mtime; pre-diet sessions still open (8639e1eb from
   11-01, bfa8b8ff from 11-02 13:18) carry 19,163 / 12,126 and read MATERIAL_RISE / OVER_BUDGET when they write
   last. Correct verdict for those windows, clears when they close; not a regression.
6. Phase 5 Safe-to-Forget (Owner "y" 2026-11-03, spec vault/specs/ccr-safe-to-forget-main.md): BUILT cc993f2f
   (safeToForget + CCR_MAIN_PROJECT=1 opt-in + projected page faults; plugin test 36/0, mutation killed, DONEGATE 43/43,
   review APPROVE, M1+5 LOW fixed). Released 0.1.0-9bdf5998; smoke 1 measured NOTHING -> ROLLED BACK to 0.1.0-39151f03
   (HR-2), b699bdaa: host auto-updated to Claude Code 2.1.317 (2026-11-03 02:32), outside COMPAT -> ALL CCR shadow
   (main-lean canary off on every pane since); and the 52 KB fixture was host-persisted. Fixture now 18,735 chars;
   driver + done_gate count only compatible runs with a project receipt (DONEGATE 45/45). Null receipt:
   ctx-rent-x/phase5-smoke-null-host-2.1.317.json.
   Owner "y" to the governed reprobe. Ran TWICE (ccr-next-verify/tools/ccr_compat_gate.py reprobe --confirm), 856,181 +
   767,245 haiku tokens: S1a S1b S2 S4 S5 PASS, S3 FAIL both times -> gate REFUSES to widen; COMPAT unchanged.
   S3 FAIL is not a hook verdict: the probe's Bash command itself exits 127 (shell never starts; `exit 3` -> 127 too).
   The Bash tool 127s INTERMITTENTLY on this host (this pane, a subagent, fresh `claude -p`); CLAUDE_CODE_GIT_BASH_PATH /
   PATH order looked like a fix at n=1 and then failed again: cause unknown (memory feedback_bash_127_scoop_git_first.md).
   Owner chose (a) 2026-11-04. CAUSE CONFIRMED: Git for Windows git-prompt.sh loads git-completion; Claude Code's
   shell snapshot serializes those __git_* functions corruptly and sourcing it kills the shell (127). Single-variable
   A/B (scratchpad bash127_ab.py, fresh claude -p haiku, one echo): control 0/6, disableAllHooks 0/3,
   WINELOADERNOEXEC=1 only 3/3, fake HOME 8/8. Hooks/CCR/rtk ruled out. Host is now 2.1.318 (on disk 11-03 23:02).
   FIX INSTALLED 2026-11-05 (Owner "1"): ~/.config/git/git-prompt.sh (skip git-completion when $CLAUDECODE set;
   rollback = delete it). Fresh claude -p echo 3/3 after (0/6 before). Open panes keep their old snapshot until restart.
   Reprobe 2.1.318: ALL PASS incl. S3 (845,338 haiku tokens). `ccr_compat_gate.py auto` from detached worktree
   .claude/worktrees/ccr-compat-2.1.318 (@83069706 + 3 gate scripts copied from ccr-next-verify, which 83069706 lacks):
   gates green, RELEASED 0.1.0-4a6f6f61, SAME_EXCEPT_COMPAT + COVERED. Smoke: fresh claude -p, Bash SMOKE-OK, start
   receipt compatible:true releaseId 0.1.0-4a6f6f61 (modes as pre-update). Main tree COMPAT += 2.1.318 (plugin 36/0).
   DONE 2026-11-05: Phase 5 RELEASED from main 0.1.0-a2116a3b (COVERED); smoke FNNFFN all 6 valid + correct, ON
   applied 3/3 (safe-hoisted), OFF shadow 3/3; KEPT (HR-2 green). done_gate CR-09/10/13 PASS: 32,310 chars
   externalised, processed mean ON 139,424 vs OFF 142,367 (-2.1%, n=3/arm), 0 projected faults. DONE_GATE 31/1/4
   (fail CR-31 shared-tree dirt). Receipt vault/programs/ctx-rent-x/phase5-safe-to-forget.json. Rollback point
   0.1.0-4a6f6f61.
7. DONE 2026-11-05 (Owner "y", conditional on n=10/arm): CCR_MAIN_PROJECT DEFAULT-ON, spec Amendment A.
   n=10 (phase5-safe-to-forget-n10.json): ON 10/10 applied, 20/20 correct, 0 faults, mean 139,594 vs 142,307 (-1.9%).
   Code 2d0c5802 (lift unless =0; main loop only, review M1; unreadable env = off; flag = lift changed the mode).
   Plugin 36/0, DONEGATE 45/45, 2 mutants killed, review APPROVE (M1+L1 fixed). RELEASED 0.1.0-b4aede4f (COVERED).
   HR-2 smoke (phase5-default-on-hr2.json, arms F=0/N=1/D=unset): N and D applied 3/3 each with mainProject, F never;
   9/9 correct, 0 faults -> KEPT. Rollback: CCR_MAIN_PROJECT=0, or ccr_release.py rollback (-> 0.1.0-a2116a3b).
Open debt: repo CLAUDE.md diet (another pane's uncommitted edit), l6 driver defects,
CR-16/07/22/30 unknown, unattributed -13.8K GEX44 floor change, GEX44 dangling doctrine pointers, GEX44 budget file,
throwaway worktree .claude/worktrees/ccr-compat-2.1.318, open panes need a restart for Bash (old snapshot),
subagent shell projection unmeasured (excluded from the lift).

## Start
GPF items 1-7 DONE. Next: Owner picks from the open debt (or closes GPF).
