# WU-C3 -- Model-call admission firewall at the interceptable edges

Common brief: `vault/programs/cdc/PROGRAMME.md`. Plan section: 2, 3 (C3).

Goal: a material cognitive spawn needs a capability produced by the admission path.
1. `hooks/cognitive_admission.js` on PreToolUse `Agent|Task` (register via hookreg, kill `CPP_COG_ADMISSION=off`,
   fail-open on own error, fast path < 50 ms). Decide from the Agent input + session binding:
   - NO_WORK: `work_proof.py` verdict for the bound unit says satisfied -> deny with reason.
   - Bound unit effect ZERO/DETERMINISTIC without deopt (C2) -> deny.
   - Spawn while the session's goal lease is closed/exhausted (goal_binding) -> deny.
   - Duplicate in-flight subagent with the same normalized prompt hash in this session -> deny ("subscribe").
   - Otherwise allow and append a capability row (`~/.claude/state/cognitive-admission.jsonl`: sid, unit, effect,
     reason, prompt hash, cap_id). Unbound interactive sessions: allow + log only (no new friction for the Owner).
2. Worker launch edge: `gsd_mission.arm` already admits; add the same capability row there (one writer function in
   `tools/cognitive_admission.py`, used by both).
3. Tests: each deny branch RED->GREEN; a mutation drill disabling each predicate turns its test RED.
4. Production Reality: in a real throwaway session, observe one denied Agent spawn in the jsonl. Record it.
Iterate after step 1. Land via land_worktree.
