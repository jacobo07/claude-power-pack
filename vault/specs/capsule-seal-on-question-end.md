---
status: APPROVED 2026-11-05 (Owner "1. y")
covers: [capsule-seal-question-end, guard-disable-owner-class]
owner: tools/gsd_mission.py _capsule_rotate · tools/mission_policy.py gate_question
---

# Seal the capsule when a blocked worker ended its turn on a question; never default-answer a guard switch

## Incident (measured, mission m-81b9650c6ff2, TTB WU-FE2 attempt 3, 2026-11-03)
Ledger `~/.claude/state/gsd-autorun-ledger.jsonl`:
- 15:02:37Z the worker (bg session ab43180e) ended its turn: the transcript logs `turn_duration`. It had left a
  handoff. Its job file says `state: blocked`, `needs: "set CPP_SEM_BREAKER=off (or clear the breaker) ..."`.
- 15:11:59Z to 15:41:48Z: `capsule_seal_refused` 7 times, "owner BLOCKED and its turn has not ended".
  `_capsule_rotate` reads `liveness()` = WAITING_HUMAN for any bare host `blocked`. That is neither idle nor DEAD,
  so `origins = []` until the 1800 s grace runs out.
- 15:46:33Z `outgoing_stop_authorized` (**supervisor_fallback**): a degraded capsule, not the worker's handoff,
  30 minutes late.
- 15:47:10Z `decision_recovered` gate **RESOLVE_BY_DEFAULT** on "set CPP_SEM_BREAKER=off". No Owner class matches
  a request to switch off a guard, so the successor would have been told to take that option. It never ran:
  the relay was re-admitted, `route DEFER` (13,780,200 needed vs 13,653,289 left), and the mission HALTED.

Two defects:
1. **D1:** `plan_next` already types a bare `blocked` from the job's `needs` (`blocked_recovery`, AMR-X), but
   `_capsule_rotate` does not. A turn that ended on a question is treated as a busy turn.
2. **D2:** `gate_question` has no Owner class for disabling a guard (a breaker, gate, hook or kill switch, set
   `off`/disabled/cleared/bypassed). DONE_GATE_RX covers only envelope/stop.

## Change
- **D1, `_capsule_rotate`:** when the verdict is WAITING_HUMAN, the host row has no `waitingFor`, and
  `blocked_recovery(rec)` classifies the job as `QUESTION_RESOLVABLE` or `QUESTION_OWNER` (the model ended its
  turn), treat the owner as idle. The `worker_handoff` origin, and the existing note-request path, then apply on
  this pass. PERMISSION_PROMPT, HOST_GATE, UNKNOWN and None keep today's behaviour: refuse, then the grace clock.
  STOPPED is already a dead owner.
- **D2, `mission_policy.OWNER_CLASSES`:** add `GUARD_DISABLE`, placed before AUTHORITY. It matches a switch-off
  verb (off, disable, clear, reset, bypass, skip, silence, mute, turn off) within 60 characters of a guard noun
  (breaker, guard, gate, hook, kill switch, firewall, sentinel), or `CPP_[A-Z_]+=(off|0|false)`.
  "the gate passed" or "run the gate" must not match.

## Acceptance
- `tools/test_gsd_mission_capsule_v2.py`, new V-MV2-QUESTION-END-SEALS: a bare-blocked owner whose job needs a
  resolvable question seals `worker_handoff` on the FIRST pass (with a note) and starts no grace clock.
  V-MV2-PERMISSION-STILL-HELD: `waitingFor` set gives the same refusal as today. V-MV2-UNKNOWN-JOB-HELD: no job
  file gives the same refusal as today.
- `tools/test_mission_policy*` (existing gate suite), new cases: the m-81b9650c6ff2 text gives
  OWNER_REQUIRED/GUARD_DISABLE, `CPP_SEM_BREAKER=off` alone also does, and three negatives stay RESOLVE_BY_DEFAULT
  ("run the gate", "the breaker receipt says GOOD_PROGRESS", "which gate order?").
- Mutation drills: removing the D1 branch turns QUESTION-END-SEALS red; removing GUARD_DISABLE turns the policy
  case red.
- The full capsule-v2, mission and policy suites stay green. pp-code-reviewer reviews before the commit.

## Review (pp-code-reviewer 2026-11-05: APPROVE with notes, 0 CRITICAL / 0 HIGH / 2 MEDIUM / 1 LOW, all fixed)
- F1: a question-ended worker with NO note is not asked for one. Its stop overwrites the job's `needs`, so a resumed
  note turn would lose the runtime answer. It seals `supervisor_fallback` on the same pass and the answer is carried
  (V-MV2-QUESTION-END-NO-NOTE-CARRIES-ANSWER).
- F2: GUARD_DISABLE now matches only an imperative acting on a guard (verb + determiner + noun, or "set/turn ... off").
  Status sentences ("kill gate K5 cleared at 3/3"), the adjective ("not clear which gate") and "kick off the gate
  suite" are negatives in V-MPOL-GATE-GUARD-DISABLE.
- F3: `_ended_on_question` is driven directly for question / waitingFor / no job / host gate / stopped / kill switch
  (V-MV2-ENDED-ON-QUESTION-UNIT). The supervise-level held gates were stopped earlier by plan_next.
Measured: policy 54/54, drills 9/9; capsule-v2 78/79 (V-MV2-L1-WITHIN-BACKOFF-HELD-SILENT failed before this change
too); with `_ended_on_question` forced False, 4 new gates go red; gsd_mission 242/242, pivot 29/29, s6 72/72.

## Never
- Never seal `worker_handoff` for a permission prompt or an unreadable job: that worker may still be mid-turn.
- Never let the runtime answer a request to switch a guard off.

## Rollback
Revert the D1 branch in `_capsule_rotate` and the `GUARD_DISABLE` tuple. No stored state depends on either.
