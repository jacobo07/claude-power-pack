# WU-P52b -- PCC wave 5.2 (trust core), part 2 of 3: plans 05-2-02 and 05-2-03

Mission: the id on your rehydration card. Follows WU-P52a (read its receipt only). 
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
1. 05-2-02: certificate forgery (N16) through the REAL judge. Every attack is RED-first and each has a control in
   which the legitimate certificate is admitted (a gate that refuses everything passes every refusal). SUMMARY, commit.
2. 05-2-03: canonical environment (N17, audit A4: `proof.environment_fingerprint` records tool versions, not names)
   and platform vs portability proof (N19). First search `modules/tower`, `modules/capability_runtime` and the
   applicability runtime for an existing environment owner (one Grep), and extend it if one exists. RED-first.
   Run `test_gsd_x_goal_invalidation.py` and `test_gsd_x_goal_certificate.py` once each. SUMMARY, commit.

## Done-gate
Both SUMMARYs committed; the forgery suite and the environment suite green on the Windows plane; liveness exit 0.
## Receipt
`packets/WU-P52b-receipt.md` (<= 20 lines). Line 2 must be exactly `Status: DONE` (or `Status: PARTIAL -- <blocker>`).
Then: mission id, commits, gate lines verbatim with plane, DENOMINATOR rows moved, open points. Commit it, end with
`HANDOFF NOTE: WU-P52b done` (or PARTIAL + next step), then end the session. Write the receipt at the latest when you
judge ~35 calls are used; a PARTIAL with an exact next step beats a cut with nothing.