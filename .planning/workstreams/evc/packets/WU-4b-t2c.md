# WU-4b-t2c — finish plan 01-02 Task 2 on the half-edited tree (evc/e2)

You are in `C:\Users\User\.claude\skills\claude-power-pack\.claude\worktrees\evc` (branch `evc/e2`). Work only here.
Use the PowerShell tool for git and python. git = `& 'C:\Program Files\Git\cmd\git.exe'`,
python = `& 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'`. Set `$env:PYTHONIOENCODING='utf-8'` first.
Budget: about 20 tool calls. Do not re-read what is described below; read only the exact lines you edit.

## State you inherit (do not redo it)
HEAD `e6b65ddc` = 01-02 Task 1. Uncommitted and KEPT in `tools/test_evc_usage_truth.py`: `import re`, new
`section_statement_forms()` and `section_surfaces()` (all Task 2 gate names already appended to REQUIRED; scan regex,
its two controls and the stale-branch red/green predicate written). The renderer (`format_age`, `snapshot_of`,
`spend_statement`, `hold_text`) is in `tools/mission_spend.py` and plan_next's final "none" reason already uses it.
Spec reference only if a step is unclear: `.planning/workstreams/evc/phases/01-usage-truth-plane/01-02-PLAN.md` Task 2.

## Steps — ONE Edit per message, never two Edits to the same file in one message
1. `tools/test_evc_usage_truth.py` `main()`: call `section_statement_forms()` and `section_surfaces()` right after
   `section_statement()`. Run `python tools\test_evc_usage_truth.py` once and confirm the new gates FAIL (red first).
2. `tools/gsd_mission.py`, plan_next hold branch: the owner-DEAD settle reason (~line 537) ends with
   `_ms.hold_text(hold, verdicts, now, limit=200)` instead of the raw hold reason.
3. Same file: the launched-worker settle reason (~line 549), same change.
4. Same file: `renewal_refusal` (~line 2180) gains a `now=None` keyword (default `time.time()` inside) and its body text
   comes from `hold_text(...)` (lazy `import mission_spend`) instead of the raw `reason`; keep the "owner hold" prefix.
   Existing three-argument callers must keep working.
5. `tools/mission_surface.py` `classify` (~line 35): when the plan reason starts with "owner hold", reuse it; otherwise
   build the text with `hold_text` (lazy import inside the function). Keep the four-argument signature.

## Verify (each once, foreground; one fix attempt per failure, at most 3 in total)
- `python tools\test_evc_usage_truth.py`
- `python tools\test_gsd_mission_owner_hold.py`
- `python tools\test_gsd_mission_surface.py`
- `python tools\test_mission_spend.py`

## Finish
All exit 0 → `git commit -m "feat(evc-01-02): task 2 -- Every statement form, then every remaining echo site, with the source scan" -- tools/test_evc_usage_truth.py tools/gsd_mission.py tools/mission_surface.py tools/mission_spend.py`.
Otherwise do not commit; report BLOCKED with the exact remaining step.

## Never
No edits outside those four files. No reset, clean, restore, stash, amend, rebase, push or force. No subagents.
No EnterWorktree. No questions.

## Report (your final message, nothing else)
```
WU-4b-t2c STATUS: DONE | BLOCKED:<reason>
HEAD: <git rev-parse --short=8 HEAD>
COMMIT: <sha or none>
RED-FIRST: <step 1 result: which new gates failed>
VERIFY: <each command: exit code and its final summary line>
```
