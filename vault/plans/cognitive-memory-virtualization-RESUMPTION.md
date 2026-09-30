# Cognitive Memory Virtualization — RESUMPTION

Read this and continue with zero prior context. Update after every sealed unit.

## 1. Identity
Repo `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`.
Plan of record: `vault/plans/cognitive-memory-virtualization-2026-09-30.md` (APPROVED 2026-09-30: "yes to all,
as long as I don't lose output quality"). Thesis: 0 new systems; extend context-rent + cognitive-resource-os.
Live peer writers in this tree (~600 dirty paths, not ours): commit by explicit pathspec only; never stage
`tools/rollover.py` (peer-dirty); `modules/pp_eval` is peer-active (e079c57) — add files, do not rewrite runner.py.

## 2. Sealed
- `a270ab3` T1 session_autopsy.growth_sources (kind / tool / unchanged vs post-edit re-reads). 15/15.
- `61c80ae` T2 fresh_context_tax by_day. 5/5. Worker floor 194.8k (09-25) -> 150.4k (09-30).
- `a5bacc8` plan + audit A1-A17 folded.
- `e796446` T3 modules/pp_eval/floor.py: arms A/context/hooks/skills/mcp/plugins/all, positive control per
  arm, A/A noise, synthetic = UNMEASURED. tools/test_pp_eval_floor.py 19/19.
- `4ead645` /cost-autopsy wires floor.py (was ORPHAN on /liveness; now absent from the unreachable list).
- `f2a4788` rtk-rewrite.js rewrites Bash only. It had been breaking PowerShell `gh`/`pytest`/`docker`/bare `git`
  calls with ParserError (measured live). tools/test_rtk_rewrite_scope.py 4/4. Found while planning T6.
Coherence anchor: `python tools/test_pp_eval_floor.py` 19/19; `python tools/test_session_autopsy.py` 15/15.

## 3. Measured facts
- Neutral cwd first call 92,535 tok (one probe, 2026-09-30); Ralph workers in repos 150.4k median.
- Growth (60 transcripts): tool_result 78 %, Read 56.5 % of it, PowerShell 26 %, Agent 0.9 %.
- Floor attribution run (T3/T4, 2 cwds x 7 arms x 2 reps): results -> section 4 once read.

## 4. Next 3 actions
1. Read the floor run (scratchpad floor_neutral.json / floor_pprepo.json of session 9e694f9a, or re-run
   `python -m modules.pp_eval.floor --cwd <dir> --reps 2 --out <json>`); write the per-lever table here.
2. T5: rank V1 moves by measured delta; each move = backup -> change -> B-prime arm (content loadable,
   not removed) -> keep/revert. Claim only "no degradation observed" unless >= 2 tasks/rule failed without it.
3. T6 (PLAN mode): PowerShell tee branch in rtk-rewrite.js — flag default OFF, no permissionDecision allow,
   `$LASTEXITCODE` preserved, both dispatchers diffed.

## 5. Start instruction
Run the coherence anchor; read the plan's task table; continue at the first unchecked action above.
