# Evaluation Without Closure (EWC) -- common brief for every unit worker

Owner approval: inline plan "y" + budget "22M, full plan" (AskUserQuestion), 2026-10-11, coordinator pane.
Goal `ewc`, cap 22,000,000 processed tokens for the whole programme (planning pane spend is outside the units).
`chain.json` here is ticked every 10 min by the zero-model task PP-EwcChain-Tick, which arms the next unit when
your receipt says DONE. No orchestrator exists above you. Your packet names what is yours.

## The defect this programme removes
An agent evaluates its own work, lists objective FAILs, actionable WARNs, an unwritten evidence artifact, uncommitted
work and an explicit next iteration -- then STOPS and recommends doing that iteration later. The next action was
internal, reversible, authorized and evidence-derivable: it should have continued. Generalise: a CPP session must not
voluntarily stop while an agent-owned, actionable, blocking obligation remains open. NOT a perfection loop: when only a
genuine human gate (preference, irreversible, outward-facing, resource) remains, stopping with a compact decision
package is correct. Unknown completion state is never COMPLETE.

## Reality already measured by the planning pane (verify each with ONE read before relying on it)
- `hooks/closer-guard.js` classify() (~l.459): Stop, critical lane, block:true. Judges closer SHAPE only (EMPTY,
  PASSIVE_WAIT, INTENT_NARRATION, NULL_ACK). hasResult() (~l.413) treats any digit as a result, so an evaluation table
  with "2 FAIL / recommend iteration 4 next" PASSES. LIVE copy is `~/.claude/hooks/closer-guard.js` (dispatcher runs
  `./closer-guard.js` from ~/.claude/hooks): canonical != live until copied (memory: dispatcher split-brain).
- `hooks/gsd_stop_continuation.js`: Ralph turn continuation, critical lane, no subprocess allowed. l.269 returns when
  the session has no `gsd-autorun-<sid>.json` marker (interactive sessions get nothing); l.283 opt-in
  `continuation:"stop-block"`; fingerprint/nextAction read only `.planning/` + task outputs, never Goal Spine
  obligations; l.371 "say so plainly" lets the model's own claim end the run (narrative authority).
  It runs from the PP live checkout path, so a merge into the live checkout makes it live.
- `modules/gsd_x/goal/convergence.py`: Goal Spine obligation model (obligation.accepted / satisfied / dispositioned,
  planes, "Unknown is never N/A", gate_class). No Stop path reads it.
- `modules/daif/obligation_extractor.py`: prose -> obligations (kinds, commitment frame, wish refusal, de-dup). CLI only.
- `modules/autonomy_gate/gate.py` + `rubric.json`: Self-Continuation 4 Owner categories, fail-closed, receipts in
  `~/.claude/state/autonomy-decisions.jsonl`. Classifies a QUESTION, never the turn's leftover work.
- `hooks/hook-dispatcher.js` Stop-chain: closer-guard (critical) -> gsd_stop_continuation (critical) -> zero-issue-gate ...
  The chain measures ~55 s per turn end; the critical lane must stay cheap (JSON reads, no python, no git).

## Architecture (approved; EXTEND/CONNECT, no new Completion OS)
Goal Spine owns obligations (session scope added for unbound sessions, same model/format). DAIF extractor is the
evaluation->obligation compiler. autonomy_gate classifies each obligation's next action (AGENT/OWNER + category).
gsd_stop_continuation.js becomes the Pre-Stop Unresolved Obligation Gate (SHADOW first: receipts, no block, for
interactive sessions; enforce for armed missions / goal-bound sessions). closer-guard gets one backstop class
RECOMMENDATION_STOP. Receipts reuse autonomy-decisions.jsonl. Patterns shared by JS and Python live in ONE JSON file
(as rubric.json already does) so the two sides cannot drift. Stop reasons: COMPLETE, HUMAN_GATE, RESOURCE_BLOCKED,
SCHEDULED_WAIT, SAFETY, TERMINAL_FAILURE, BUDGET, STALLED, UNKNOWN; continue reasons CONTINUE_<OPEN_OBLIGATION|
FAILED_GATE|ACTIONABLE_WARNING|MISSING_EVIDENCE|KNOWN_NEXT_ACTION|UNCONSUMED_CHILD>. Interactive enforcement is a
LATER Owner decision taken on shadow data -- never flip it inside this programme.

## Paths
- Work tree (your cwd): `C:\Users\User\Apps\wt_ewc` (branch ewc/closure from feature/knowledge-acquisition 696ce37a).
  All code commits go here. Never write code into the live checkout except in E6 (merge).
- Programme files and receipts: `C:\Users\User\.claude\skills\claude-power-pack\vault\programs\ewc\` (live checkout,
  branch feature/knowledge-acquisition). Other panes write there too: pathspec commits only.

## Session loop
1. Tests first (RED), then code. Pathspec micro-commits ending with
   `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`. Never `git add -A`. Git via
   `& 'C:\Program Files\Git\cmd\git.exe' -C <path>`; never Set-Location into another goal's root.
2. Close: overwrite `WU-<id>-receipt.md` beside your packet. Line 1 `# <id> receipt`, line 2 `Status: DONE`, then
   commits, PROVEN / NOT_PROVEN / BLOCKED_* / INCONCLUSIVE per claim, measured numbers with the command that produced
   them, calls used, what the next unit must know (<= 8 lines). Commit it (live checkout, pathspec).
3. Unit too big (stop starting new work at 85 % of your calls): commit what is done, INSERT a continuation unit into
   `chain.json` right after yours (id `<id>b`, `after` = your id, packet `WU-<id>b.md` with the exact remaining steps,
   route = route-S.json), then receipt `Status: DONE` (slice done); commit all three together. Never write PARTIAL.
4. Blocked on something only the Owner can do: receipt `Status: BLOCKED_HUMAN` with the exact command/action.
   Only: writes the classifier denies (e.g. ~/.claude/hooks, settings.json), capital, credentials, push.
5. This programme's own rule applies to you: before ending a session, list your open obligations; if any is
   agent-owned and actionable, do it instead of recommending it.

## Hard constraints
- Windows: git/python via the PowerShell tool with absolute paths (`C:\Users\User\AppData\Local\Programs\Python\
  Python312\python.exe`). No Bash for git/python. Background commands SOLO in their batch.
- No `/gsd-autonomous`, no EnterWorktree, no push, no cap change. Agent spawns only where your packet allows (E5).
- Every guard ships with a test that drives its red branch and a positive control; mutation drills through
  `tools/mutation_drill.py` only (never mutate a live-loaded file in place).
- New module => `python modules/liveness/reachability.py` must stay exit 0 (wire or declare it).
- Iterate with `C:\Users\User\Downloads\Promptsss\Prompts pa iterar\Universal\iteracion-avanzada-universal.txt` at each
  failure (read once per session).
- Every bug found: an entry in `vault/programs/ewc/KNOWLEDGE.md` (symptom, trigger, root cause, impact, fix,
  prevention, proof). E6 promotes them.
