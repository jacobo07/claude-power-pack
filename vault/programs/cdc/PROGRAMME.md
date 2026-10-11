# Cognitive Deflation Closure (CDC) -- common brief for every unit worker

Binding plan: `vault/plans/cognitive-deflation-closure-MASTER-PLAN-2026-10-10.md` (b0d72dda, Owner "y" 2026-10-10).
Read sections 2-4 and 7 once; your unit packet names what is yours. No orchestrator exists above you. The chain
(`chain.json` here, ticked every 10 min by the zero-model task PP-CdcChain-Tick) arms the next unit when your receipt
says DONE. Goal `cdc`, hard stop 80M processed tokens for the whole programme.

## Session loop
1. Work in `C:\Users\User\Apps\pp-cdc` (branch feat/cdc). Tests first (RED), then code, pathspec micro-commits with
   the Co-Authored-By line from the commit attribution. Never `git add -A`.
2. Land into live PP ONLY with `python tools/land_worktree.py --worktree C:\Users\User\Apps\pp-cdc --live
   C:\Users\User\.claude\skills\claude-power-pack --test "<declared cmd>"` (script-style tests as `python tools/x.py`).
   Never edit the live checkout directly. Never push.
3. Close: overwrite your receipt `WU-<id>-receipt.md` beside your packet. Line 1 `# <id> receipt`, line 2
   `Status: DONE`, then commits (worktree + live landing sha), PROVEN / NOT_PROVEN / BLOCKED_* / INCONCLUSIVE per claim,
   calls used, what the next unit must know (<= 8 lines). Commit it.
4. Unit too big for one session (stop starting new work at 85 % of your calls): commit what is done, INSERT a
   continuation unit into `chain.json` right after your entry (id `<id>b`, `after` = your id, packet `WU-<id>b.md`
   with the exact remaining steps, same route), then receipt `Status: DONE` (slice done); commit all three together.
   Never leave uncommitted work. Never write PARTIAL: the chain does not re-arm a unit that ended without DONE.
5. `BLOCKED_HUMAN` (stops the chain) ONLY for an act no tool can perform: credentials/secrets, money, legal or
   product approval, a production deploy go, or a permission prompt the host shows only to the Owner. Everything
   else is yours (Owner 2026-10-11: "esto se deberia haber hecho y decidido de forma 100% autonoma"):
   - land_worktree REFUSED (REBASE_CONFLICT, stale live, failing test after rebase) -> insert a reconcile unit
     `<id>L` (rebase onto live HEAD, keep BOTH semantics, run every touched tool's tests, land), receipt DONE.
   - overlap with another writer's uncommitted live file -> receipt DONE with `LANDING_PENDING_OVERLAP: <files>`;
     never edit, stash or commit their file.
   - a choice code + tests cannot settle -> write the question precisely, take the conservative side (live wins).

## Owners to reuse (never rebuild)
work_proof.py (NO_WORK, receipts) · tier_routing.py · route_admission.py · cost_to_completion.py · mission_spend.py +
hooks/lib/goal_binding.js + hooks/session_budget_guard.js (spend lease, deny budget) · usage_index.py ·
session_autopsy.py · change_impact.py · land_worktree.py · gsdx_chain.py · cep_gen2.py · rollover.py (epochs, capsule) ·
hookreg + tools/test_matcher_liveness · UKDL / FIOS / Knowledge Vault. Read the EVC (`.claude/worktrees/evc`),
ctx-same-pane (`Apps/pp-ctx-same-pane`) and autonomy (`Apps/pp-ucda-wt`) receipts before duplicating anything;
never write into those worktrees.

## Hard constraints
- Windows: git/python via the PowerShell tool, absolute paths (`C:\Program Files\Git\cmd\git.exe`,
  `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`). No Bash for git/python. No `Agent`, no GSD
  fan-out, no `/gsd-autonomous`, no `EnterWorktree` (you are already in the worktree).
- Every new guard: env kill switch, fails OPEN on its own error, a test that drives its red branch (mutation drill),
  registered so test_matcher_liveness sees it. Fast path: a tiny deterministic action must not pay new overhead.
- Host limit (EXTERNAL_LIMITATION): the main model turn cannot be intercepted. Enforce only at Agent/Task spawn,
  worker launch, tool calls, UserPromptSubmit and epoch rotation. Never claim more.
- QuickLease is READ-ONLY for this programme (only C12 reads it). No product change, no GEX44 deploy, no push,
  no credential work.
- UNKNOWN is not zero; no observed model call is not proof; never write PASS for an unobserved claim.
- Iterate with `C:\Users\User\Downloads\Promptsss\Prompts pa iterar\Universal\iteracion-avanzada-universal.txt` at the
  checkpoints your packet names (read it once per session, apply, do not paste it into commits).
- Every bug found: Knowledge Vault entry (symptom, trigger, root cause, fix, prevention, regression proof).
