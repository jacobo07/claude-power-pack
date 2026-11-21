---
covers: [mission-unattended-continuity, owner-question-continue, credential-token-false-positive, topup-ceiling-3x, toast-notify]
tier: T2
owner_decision: "Owner 2026-11-21 (session 3da1f022): 'quiero que las misiones puedan seguir sin estancarse durante horas'; plan A + C approved ('1. y 2.'), B without Telegram"
status: "PROVEN 2026-11-21 -- test_mission_policy 62/62 (+drills 11/11), test_mission_topup 27/27, test_mission_decision_recovery 39/39, test_mission_recovery 69/69, 10 more mission suites green. Review (pp-code-reviewer): APPROVE, 0 critical/high; M1 fixed (only Owner INPUT classes -- credential, external property, owner decision, product scope -- may continue; deploy/irreversible/guard/authority still stop), M2 fixed (verb/state-led tokens of unlisted vendors, Spanish), L1 fixed (one notice per question, not per epoch). M3: real toast run once by hand on this laptop, rc 0"
---
# Mission unattended continuity: stop parking missions for hours on questions nobody hears

## Problem (measured 2026-11-21 from the mission ledgers, not assumed)
The recent multi-hour stalls were not quota or budget. Each one was a worker question that the runtime parked as
the Owner's, plus a notification that reached no one:

| mission | idle | parked on | why it was the Owner's |
|---|---|---|---|
| m-e78bdb938339 | 14.0 h (11-21 00:02 -> 13:59) | "choose: continue Phase 2 from a fresh session or re-baseline the per-phase token lines" | `mission_policy` SECURITY_OR_CREDENTIAL matched the bare word `token` (LLM tokens) |
| m-144eafe0ff5f | 9.1 h (11-18 02:01 -> 11:06) | "start a fresh session ...; provide MIOSA_API_KEY and approve spend" | a real credential, but the rest of the work stopped with it |
| m-9aa6a1639edc | 7.9 h + 5.4 h | launch held: cwd behind and dirty | out of scope here (a destructive-state question) |

Every one of them logged `incident_notify_failed: no channel configured`: Telegram is the only channel and it is not
set. Budget top-up worked: m-144eafe0ff5f got TOPUP1 and TOPUP2 unattended. The quota governor refused 3 times in
4 days, all with the old calibration.

## Design
A1. `mission_policy.OWNER_CLASSES` SECURITY_OR_CREDENTIAL: `token` counts only in a credential shape (api/access/
    auth/bearer/bot/github/npm/oauth/refresh/session/personal-access token, an UPPER_CASE `*_TOKEN` name). "token
    lines", "tokens processed", "token budget" are spend vocabulary and fall to the other classes (AUTHORITY keeps
    "more tokens"/"budget exhausted").
A2. "continue from a fresh session" needs no rule of its own: once A1 stops misclassifying it, the existing
    RESOLVE_BY_DEFAULT path replaces the worker with a successor, which IS a fresh session.
A3. `gsd_mission.plan_next`, QUESTION_OWNER: when the typed blocker (`blocker_compiler`) has POSITIVE evidence of
    independent work (another ROADMAP unit runnable without the blocked one), the worker is replaced by a successor
    told: the question is the Owner's, record `OWNER DECISION NEEDED:`, do NOT do that part, continue the rest. The
    question is ledgered `owner_question_parked`, kept on the record (`owner_questions`), and notified. Same cap as
    decision recovery (MAX_DECISION_RECOVERIES with no tree movement between them), then surfaced as today.
    No evidence, mission-wide class, or authority hold -> surfaced exactly as today. Kill switch
    `CPP_MISSION_OWNER_PENDING_CONTINUE=off`.
B.  `mission_topup.notify`: no Telegram -> a Windows toast (Action Center keeps it while the Owner is away), spawned
    with CREATE_NO_WINDOW (console-popup rule). Kill switch `CPP_MISSION_NOTIFY_TOAST=off`. Not Windows or toast
    failure -> the old "no channel configured" / failure string, so `notify_incident` keeps retrying.
C.  `mission_topup.DEFAULT_CEILING_X` 2.0 -> 3.0 (Owner "x3"): a commits-gated mission may grow to 3x its authority.
    The quota governor (`topup` action, 85 %) still checks every grant. Env `CPP_MISSION_TOPUP_CEILING_X` unchanged.

## Acceptance (each from both poles)
- AC1 "re-baseline the per-phase token lines" is not OWNER_REQUIRED; "provide the GitHub token", "set TELEGRAM_BOT_TOKEN",
  "API key" still are SECURITY_OR_CREDENTIAL; "need more tokens" still AUTHORITY.
- AC2 QUESTION_OWNER + independent evidence -> action replace with an OWNER_REQUIRED decision; without evidence, with
  the switch off, or over the cap -> surface_blocked. The answer forbids the Owner-class part.
- AC3 notify with no Telegram calls the toaster and returns a delivered string; switch off -> "no channel configured".
- AC4 default_terms(10M) ceiling 30M.
- AC5 existing suites unchanged: mission_policy / owner-escalation, topup, cost_hold, mission_gate, self_heal,
  blocked_intent.

## Rollback
Each part has its kill switch; code rollback is one commit revert. C alone: `CPP_MISSION_TOPUP_CEILING_X=2`.

## Out of scope
The cwd behind-dirty hold (m-9aa6a1639edc), host permission prompts, re-arming October missions (done separately,
case by case, after checking their branches).
