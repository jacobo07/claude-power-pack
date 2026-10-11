# WU-E4 -- closer-guard backstop, child results, context-epoch carry, rubric text (M6, M8, M10)

Common brief: `PROGRAMME.md`. Read E1-E3 receipts + `PREMISES.md` first. Route M (20 calls). cwd `C:\Users\User\Apps\wt_ewc`.

Steps:
1. M6 `hooks/closer-guard.js` (canonical in the worktree): new class `RECOMMENDATION_STOP` -- the closer recommends or
   defers an action the agent could do itself ("recommend doing X next", "next iteration should", "I suggest you run",
   "left for a follow-up") while not ending on a question and not naming an Owner category (reuse the E2 patterns JSON;
   no third copy of the regexes). It must NOT fire on: a closing question to the Owner, a genuine human-gate package,
   a report whose last section is "next task for another pane/session per HANDOFF BLOCK" (the estate's own handoff
   contract), or a tool-call turn whose tool call followed the text. Respect the file's doctrine: narrow, both poles,
   near-miss controls, the existing `endsOnText` order bit. Coordinate with gsd_stop_continuation: closer-guard blocks
   at most once in a row (unchanged); the EWC gate already stands down when closer-guard blocked.
   Record (do not perform) the live-copy step for E6: `~/.claude/hooks/closer-guard.js` differs from canonical
   (PREMISES d) -- E6 copies after merge, or the live file stays stale.
2. M8 child work: an unread background task output or an Agent result never reconciled becomes an obligation
   (actionability NOW, kind UNCONSUMED_CHILD) for interactive sessions too, reusing gsd_stop_continuation's
   nextAction() task-output scan (it is mission-only today).
3. M8 context epochs: the mission successor card (`tools/gsd_mission.py`) and the /kclear capsule renderer (PREMISES f)
   include open obligations (<= 10 lines: id, severity, next_action) so a fresh parent context sees them without the
   old context. Test: write obligations, render both, assert they appear; a fresh-epoch fixture where the next action
   exists only in the ledger still yields CONTINUE at Stop.
4. M10 `modules/autonomy_gate/rubric.json`: add one sentence -- a recommendation the agent can carry out itself is not a
   stop reason; record findings as obligations, do the AGENT ones, stop only on a named gate. Keep the file the single
   source for the Stop hook, the gate and the successor card (tools/test_gsd_mission.py and test_autonomy_gate must stay
   green).
5. Run every touched suite: `node hooks/tests/run-all.js` (if present in the worktree), closer-guard's own drills
   (`test-closer-guard-*.js`), tools/test_gsd_mission.py, tools/test_autonomy_gate.py, tools/test_ewc.py.
Receipt: new class precision on the fixtures + the closer-guard drill counts before/after (no regression allowed).
