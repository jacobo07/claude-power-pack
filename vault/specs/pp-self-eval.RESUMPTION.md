# PP Self-Eval — resumption (2026-09-30)

Repo `C:\Users\User\.claude\skills\claude-power-pack`, branch `feature/knowledge-acquisition`.
Spec `vault/specs/pp-self-eval.md` (Owner decisions §2, do not re-litigate). Other panes commit
here constantly: commit by pathspec only.

## State (coherence anchor: commit 0ba8565)
SEALED in 0ba8565: modules/pp_eval (common, harvest, runner, verdict, nightly), tools/pp_eval.py,
tools/test_pp_eval.py 37/37 (fake claude, no model calls), /pp-eval command, registry SCHEDULED.
Mutation drills (scratchpad `eval_drill.py`, isolated copies + clean-copy control): S1 4/4 killed;
S2-S4 7/12 killed, 0 survived. NOT RUN: the last 5 drills (quota mid-night stop, quota ceiling,
lock, owner-active, proposal gating) — Claude Code reaped the drill for host memory pressure
(1.9 GB free of 31 GB at 2026-09-30 ~14:10).
Real harvest over PP: stopped by the same reap. Bank `~/.claude/state/pp-eval/bank.json`: 0 tasks,
2 rejected, both legitimately (env-dependent mirror test; 200-check suite red at its own fix).
Scheduled task PP-SelfEval: INSTALLED 2026-09-30, daily 03:30 (wscript -> hidden_launch.vbs ->
pp_eval.py night). Nights now harvest before the quota check (harvest makes no model calls), so the
bank fills automatically while quota is high; gate 38/38 after that reorder.
Quota: 7-day window read 93% at ~12:40; model runs refuse at >= 80% until the reset.

## Next 3 actions
1. Read `~/.claude/state/pp-eval/nights.jsonl` after 2026-10-01 03:30: expect a harvest block or a
   recorded skip (RAM < 6 GB / owner active). Acceptance §4.4 is that row, observed.
2. When free RAM >= 6 GB and the Owner agrees: re-run the 5 missing drills (`drills_s2s4.json`
   entries 9-13, scratchpad) and require KILLED.
3. Once the bank has >= 8 tasks, report the count; if PP yields too few, add repos to
   `~/.claude/state/pp-eval/config.json` "repos".

Start: read this file, then `python tools/pp_eval.py status`.
