---
id: goal-budget-admission
tier: T3
covers: [goal-budget, goal-admission, session_budget_guard, mission_spend, SpendLedger, GoalLedger, A1, ECONOMIC_CONTAINMENT, pre-call admission]
origin: vault/programs/cognitive-economy/gen2/AMENDMENT-A1-2026-10-07.md (INCIDENT 2026-10-07)
novelty: EXTEND_EXISTING_OWNER (HR-NOVELTY-001) -- session_budget_guard.js, tools/mission_spend.py, modules/provider_routing/ledger.py
status: draft
---

# Goal budget admission -- reserve before spend

## Problem
A1's 20M cap was a number C16 read after the spend (42,307,381 = 111.5 % over). The pre-call
breaker that did exist (`hooks/session_budget_guard.js`) could not have stopped it:
1. opt-in per session -- coordinator panes 423e33b0 / b9bd9469 (41.2M of 42.3M) never declared;
2. per session, not per goal -- no sum across the panes that spend one budget;
3. blind to subagents -- subagent tool calls fire PreToolUse with the PARENT session id (measured
   2026-10-07: 16/16 hook rows in `<sid>/subagents/agent-a017d67e416bbe3e4.jsonl`, sessionId =
   parent), but their usage lands in `<sid>/subagents/*.jsonl`, which the guard never read;
4. no reservation -- N panes each see "under cap" at once.

## Design
- **Goal ledger** = `GoalLedger(SpendLedger)` at `<state>/goal-budget/<goal>/`. Journal ops added:
  `cap` (the cap is journal state, folded under the lock; constructor caps are ignored) and
  `settle` (sid, cumulative measured). Booked spend per sid = max measured seen (watermark), so a
  replayed or duplicated settle books nothing twice. `used = sum(watermarks) + open reservations`
  (RESERVED or LEAKED and not yet closed by a settle of their sid).
- **Lease**: `renew(sid, measured, per_call)` settles the sid, closes its open reservations, and
  reserves `min(remaining, lease_calls x per_call)` as `<goal>:<sid>:<seq>`. At most one open lease
  per sid. Refused when nothing remains.
- **Agent spawn**: `spawn(sid, estimate, base=measured)` reserves the estimate (default one lease)
  or refuses. The hold shrinks as the sid's settled spend passes `base` and closes when it reaches
  the estimate; a renew closes only LEASES (review M1: the parent's first renew used to drop it).
- **Cap changes**: initial declare and lowering always allowed. A raise or a rebind needs the
  Owner's authority: `goal-declare --owner`, which requires an interactive TTY and the goal id typed
  back. `CLAUDECODE` set refuses too, as a backstop only (an agent can unset it -- review H1). A raise
  is refused when used >= cap (CONTAINED: the only way forward is a new goal id). `source` recorded.
- **Local lease is a cache**: the guard admits on a cached lease only while the journal holds that
  id open with the same amount and base (review H1a: a forged `{amount: 1e15}`).

## Trust boundary
Everything here runs as one OS user, the same one the agent's shell runs as. The gate defeats the
accidental and casual paths -- an undeclared pane, a forgotten Agent, a substring-shaped bypass, a
forged cache, an env flag unset -- and makes every refusal and settle a durable journal row. It does
not stop an agent that deliberately edits this hook, `settings.json`, or the journal itself; those
are covered by the existing self-modification denials, not by this gate.
- **Binding** (precedence, first wins): env `CPP_GOAL` > session cwd under a goal's `roots`
  (`<state>/goal-budget/index.json`) > `goal` field in `session-budget-<sid>.json`. A new goal whose
  roots overlap an open goal's roots is refused.
- **Guard (goal mode)**: measure main transcript + `<sid>/subagents/*.jsonl` incrementally; when
  `measured - lease.base >= lease.amount`, `spawnSync` `mission_spend.py goal-renew` (8 s timeout).
  Refusal -> deny + `continue:false`. Renew failure / timeout / unparseable -> deny (fail CLOSED in
  goal mode; unbound sessions keep fail-open). Host not in goal `hosts` -> deny (UNKNOWN).
  Substring exemption is off in goal mode; only a bare `mission_spend.py goal-status` is exempt.

## Overshoot bound (declared, not zero)
Hooks see tool calls, not API requests. Per bound pane: one lease + the tokens of the call that
crosses it + the in-flight turn after a deny (`continue:false` ends it). Canary measures it.

## Acceptance
- AC1 two processes racing the last lease: exactly one admitted.
- AC2 Agent spawn whose estimate exceeds remaining: denied before launch.
- AC3 resume (same sid, new process / state file wiped): booked spend does not reset.
- AC4 two sessions on different accounts, one goal: one cap.
- AC5 crash with a live lease: the lease keeps counting (LEAKED counts) until settled.
- AC6 UNKNOWN (host not listed, transcript unreadable, renew failure): denied.
- AC7 cap raise while CONTAINED, or from inside an agent: refused; journal unchanged.
- AC8 every refusal paired with a control where the same input fits and is admitted.
- Live canary: tiny cap, several bound sessions + an Agent, settled spend <= cap + declared bound.

## Kill switch / rollback
`CPP_SESSION_BUDGET=off` disables the guard (both modes). Deleting `<state>/goal-budget/index.json`
unbinds cwd-bound panes. Rollback = revert the branch; journals are append-only and inert without it.

## Owner steps (HR-001)
Registering `Task|Agent` PreToolUse to `hook-dispatcher.js --event=PreToolUse-Agent-default` in
`~/.claude/settings.json` and copying the dispatcher to `~/.claude/hooks/`: `vault/OWNER_QUEUE.md`.
