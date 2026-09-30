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
- Ralph workers in repos: 150.4k median first call.
- FLOOR ATTRIBUTION, neutral cwd (`vault/audits/floor-attribution-2026-09-30-neutral.json`; 14/14 runs valid,
  every control held, A/A noise 1,035): baseline 91,863. Delta when switched off: CLAUDE.md+rules (context)
  44,692 · skills listing 6,502 · hooks 4,797 · MCP 2,049 · plugins 1,355 · all off 57,364 -> 34,499 left
  (harness system prompt + tool schemas, not movable by CPP). context = 78 % of the movable floor.
  bytes/3.8 had ESTIMATED those files at ~30k: the estimate undercounts by ~1.5x.
  Hook injections at startup, arm A: SessionStart 7,215 + 3,604 chars, UserPromptSubmit 2,185, Stop 356.
- PP-repo cwd run: KILLED by Claude Code for host memory pressure (390 MB free of 32 GB). Not re-run; the
  ~58k project-dependent part stays unattributed until the Owner asks for a re-run on a host with headroom.
- Growth (60 transcripts): tool_result 78 %, Read 56.5 % of it, PowerShell 26 %, Agent 0.9 %.
- Floor attribution run (T3/T4, 2 cwds x 7 arms x 2 reps): results -> section 4 once read.

- GEX44 substrate (Owner option 2, 2026-09-30): GEX44's ~/.claude is NOT the laptop's (CLAUDE.md 3,748 B vs
  40,117; no rules/; claude 2.1.113 on PATH, 2.1.284 at ~/.local/bin). Laptop instructions staged as project
  memory in ~/cmv-probe (CLAUDE.md = laptop ~/CLAUDE.md; work/CLAUDE.md = laptop global; work/.claude/rules = 23
  rules; pp/ = modules/pp_eval). No CLAUDE_CONFIG_DIR swap (would need credentials). `caeec1a` adds
  PP_FLOOR_CONTEXT_FILES. First run: 6/6 `<synthetic>` "weekly limit, resets Oct 4 8pm Europe/Berlin" ->
  UNMEASURED. Re-run after the reset: cmv_gex_run.sh shape (nohup, disown, --arms A,context --reps 3).
- GEX44 after Owner re-login (2026-09-30 evening), laptop instructions staged, 3 reps/arm, A/A noise 0, every
  run valid (vault/audits/floor-attribution-2026-09-30-gex44-laptop-*.json): all 25 files 43,843 tok (laptop
  neutral run 44,692 -> reproduces within 2 %). Split: rules/ 24,329 (69,099 B, 2.84 B/tok) · global
  CLAUDE.md 16,923 (40,117 B, 2.37 B/tok) · home CLAUDE.md 2,591 by remainder. bytes/3.8 undercounts 1.3-1.6x.
- Ablation validity limit: most movable global-CLAUDE.md text is Windows transport doctrine; a Linux (GEX44)
  ablation cannot exercise it, and P3 tasks sit at ceiling. Evidence-only moves (no rule sentence removed) are
  verifiable by a rule-sentence reconstruction check; rule-text moves need a Windows ablation.
- Move candidate (global CLAUDE.md, 39,810 chars): "Parallel Subagent Limit" 13,505 (incident accounts of rules
  I-L), "Root + history" 4,664. Move narratives only, keep rule text; B-prime arm = narratives reachable on demand.

## 4. Next 3 actions
1. Read the floor run (scratchpad floor_neutral.json / floor_pprepo.json of session 9e694f9a, or re-run
   `python -m modules.pp_eval.floor --cwd <dir> --reps 2 --out <json>`); write the per-lever table here.
2. T5: rank V1 moves by measured delta; each move = backup -> change -> B-prime arm (content loadable,
   not removed) -> keep/revert. Claim only "no degradation observed" unless >= 2 tasks/rule failed without it.
3. T6 (PLAN mode): PowerShell tee branch in rtk-rewrite.js — flag default OFF, no permissionDecision allow,
   `$LASTEXITCODE` preserved, both dispatchers diffed.

## 5. Start instruction
Run the coherence anchor; read the plan's task table; continue at the first unchecked action above.
