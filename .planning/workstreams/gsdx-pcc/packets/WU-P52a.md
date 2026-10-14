# WU-P52a -- PCC wave 5.2 (trust core), part 1 of 3: plan-check fixes + plan 05-2-01

Mission: the id on your rehydration card. 
cwd `C:\Users\User\Apps\pp-gsdx-pcc`, branch `gsdx/pcc`, workstream `gsdx-pcc`. UNATTENDED: nobody answers questions.
Authority: Owner, 2026-10-14 ("Aprobar 175M"; plan `.planning/workstreams/gsdx-pcc/CONTINUATION-PLAN-2026-10-14.md`).
Phase dir: `.planning/workstreams/gsdx-pcc/phases/05-2-trust-core/` (Part A is committed in 7e139cb3).
Base packet: `packets/WU-P52.md`. Its Never list and execution rules apply. Its Budget, Part A and Part C are superseded here.

## Why this unit is narrow (read it, it is the point)
WU-P52 (m-d563551d7aa9) was stopped by the semantic breaker TOKEN_INCIDENT: 25 tool calls without progress, spent
re-reading five phase docs before writing anything. Its receipt (untracked `packets/WU-P52-receipt.md`, do not edit it)
lists the next actions. Rules for you:
- Read ONLY what your plan(s) cite: the PLAN file, the exact file:line ranges it names, and 05-2-RESEARCH.md
  sections it points to. Never re-read a file you already read this session.
- Make progress every <= 12 calls: an Edit/Write of a test or module, or a commit. RED first, then commit the RED log.
- Do not try to read `~/.claude/state/session-budget-*.json`; the goal-budget guard refuses it. The driver measures burn.
- The concurrent-writers hook refuses a commit that contains hunks this session did not write. Commit only your own
  files; never stage `packets/WU-P52-receipt.md`, `*.partial.json`, other `*.residual.md`, `.claude/`, `vault/progress.md`,
  `LEARNINGS_PENDING.md`, `vault/specs/salvage/`.

## Execution
INLINE with PowerShell. Git: `& 'C:\Program Files\Git\cmd\git.exe' -C . ...`. Python
`C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`, `$env:PYTHONIOENCODING='utf-8'`. One suite per call,
`timeout: 600000`, logs under the phase dir `logs/`. Commit by pathspec with `-F <msgfile>` (UTF-8 no BOM, message ends
`Co-Authored-By: Claude Sonnet <noreply@anthropic.com>`), verify `git log -1 --format=%s`. Never push, never arm a
mission, never ssh, never write outside this worktree. A heavy run that RAM kills: mark it UNRUN, do not retry.
Each plan ends with its `05-2-0N-SUMMARY.md` (gates verbatim with plane `Windows laptop`, drills, deviations).

## Work
1. Persist the plan-check verdict the predecessor never saved: write `05-2-PLAN-CHECK.md` from the receipt's
   findings (a)-(g) verbatim, each with your disposition. Apply them to the PLAN files they concern:
   (a) inherited events with no authority field: admitted as "claims nothing above original"; `inherit.apply`
       stamps authority (05-2-01);
   (b) add `tools/test_gsd_x_goal_certificate.py` to the regression list (05-2-05);
   (c) route `inherit.ineligible` and `verification_set` for D11, and name `verification_set` in 05-2-04;
   (d) define the legacy `contract_hash` for F8 (05-2-02);
   (e) add V-DONE-COUNT>=40 and a MIGRATION-ONCE task (05-2-05);
   (f) F3 needs a control with a legitimately different verdict gate class (05-2-02);
   (g) F1/F12 are baseline, never RED (05-2-02).
   Commit.
2. Execute 05-2-01 (trust substrate: revocation, lineage, authority monotonicity; N01 N02 N05 N23).
   - Start by writing `tools/test_gsd_x_goal_trust.py` (gates named in the receipt's open point 1; reuse the
     helpers of `tools/test_gsd_x_goal_judge_validate.py`). Run it, confirm RED for the right reason, commit the RED log.
   - Then implement `modules/gsd_x/goal/trust.py` plus the `proof.py` / `inherit.py` / `sweep._certify` edits named
     in the plan. GREEN, then run `test_gsd_x_goal_judge_validate.py` and `test_gsd_x_goal_invalidation.py` once each
     (no regression). Wire `trust.py` (liveness: `python modules/liveness/reachability.py` exit 0). SUMMARY, commit.

## Done-gate
`GSDX_TRUST_PASS=n/n` committed; `05-2-01-SUMMARY.md` and `05-2-PLAN-CHECK.md` committed; liveness exit 0.
## Receipt
`packets/WU-P52a-receipt.md` (<= 20 lines). Line 2 must be exactly `Status: DONE` (or `Status: PARTIAL -- <blocker>`).
Then: mission id, commits, gate lines verbatim with plane, DENOMINATOR rows moved, open points. Commit it, end with
`HANDOFF NOTE: WU-P52a done` (or PARTIAL + next step), then end the session. Write the receipt at the latest when you
judge ~35 calls are used; a PARTIAL with an exact next step beats a cut with nothing.