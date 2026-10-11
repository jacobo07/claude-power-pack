# WU-E3 -- Pre-Stop Unresolved Obligation Gate + anti-livelock (M5, M7)

Common brief: `PROGRAMME.md`. Read E1/E2 receipts + `PREMISES.md` first. Route L (28 calls). cwd `C:\Users\User\Apps\wt_ewc`.

Steps:
1. EXTEND `hooks/gsd_stop_continuation.js` (no new hook; keep fail-open ABSOLUTE, no subprocess, critical-lane cheap).
   New decision order, before the marker check:
   a. kill switch / no sid -> allow (unchanged);
   b. read open obligations: goal log if the session is goal-bound (resolve with `hooks/lib/goal_binding.js`
      readBinding, observe mode, never write a binding), else the E2 session ledger; plus the E2 patterns JSON applied
      to the LAST assistant turn text (reuse closer-guard's transcript-tail reader style: bounded tail read, never the
      whole transcript) as a backstop for findings the agent never recorded;
   c. unreadable state -> receipt `STOP_UNKNOWN`, allow; NEVER `STOP_COMPLETE`;
   d. any obligation AGENT/NOW (E2 classify rules mirrored from the JSON, not re-invented) -> verdict CONTINUE_<reason>,
      naming ONE next obligation by id + its next_action;
   e. only OWNER/external left -> `STOP_HUMAN_GATE` / `STOP_RESOURCE_BLOCKED` + a <= 6-line decision package
      (proven green, what remains subjective, the exact yes/no needed);
   f. none -> `STOP_COMPLETE`.
   MODES: env/config `CPP_EWC_GATE=shadow|enforce|off`. Default: `shadow` for interactive sessions (receipt only, never
   block); `enforce` for armed missions and goal-bound sessions with a marker. Never flip interactive default to
   enforce here -- that is a later Owner decision on shadow data.
   For armed missions, remove narrative authority: when the ledger holds an AGENT/NOW obligation, "say so plainly" no
   longer ends the run; the injected text says which obligation is open instead.
2. M7 anti-livelock: the fingerprint gains a digest of the open-obligation set (id, state, severity). A second block
   needs that digest or the existing mission facts to move. Semantic progress = fewer open NOW obligations or lower
   max severity. 3 consecutive continuations without progress -> `STALLED` receipt + a recorded diagnosis obligation
   (owner AGENT, actionability NOW, kind "change strategy") and allow the stop. Keep MAX_STREAK, cycle/hour budgets,
   RAM floor and the closer-guard non-ping-pong rule exactly.
3. Receipts: same file `~/.claude/state/autonomy-decisions.jsonl`, `source: gsd_stop_continuation`, new categories
   above, plus `mode` (shadow/enforce) and `would_block` so shadow data is measurable. Heartbeat unchanged.
4. Tests (`tools/test_ewc.py` + a Node unit test beside existing hooks tests): the three E1 fixtures now pass at Stop
   level (incident -> CONTINUE in enforce, would_block=true in shadow; controls correct); livelock (same digest twice
   -> no second block; 3 no-progress -> STALLED); unreadable ledger -> STOP_UNKNOWN; budget exhausted -> allow with
   BUDGET; RAM floor -> allow. Every branch both poles. Mutation drill (tools/mutation_drill.py) on the CONTINUE
   branch and on the STOP_UNKNOWN branch: each must go red.
5. Measure the added critical-lane latency: n=5 runs on a large real transcript copy, before/after medians in ms.
   If the median grows > 300 ms, cut work until it does not.
Receipt: latency numbers with the command, drill results, test counts, the exact mode semantics shipped.
