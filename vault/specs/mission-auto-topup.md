---
covers: [mission-auto-topup, mission-budget-at-arm, mission-budget-suggest, cost-breaker-topup]
status: approved by Owner 2026-10-23 ("y")
date: 2026-10-23
---

# Mission auto top-up: a pre-authorised budget that does not lose the night

## Why

2026-10-22, Credit Score Engine, mission m-b3303ade7741: armed at 23:23 with no Owner authority, so the breaker
judged it against an auto envelope of 7.6M (2 x 7.6M = 15.2M default ceiling). It tripped at 00:01 having spent
17.1M on a real milestone start (plan, phase 5, three phase-6 tasks), and waited seven hours for the Owner to wake.
The previous mission on the same repo cost 154M for 4 phases. Three causes: `arm` takes no token ceiling and the
`/cpp-gsd-long` card never asks for one; the auto estimate ignores measured cost; a stop is silent.

## What it does

1. **Budget at arm.** `mission_topup.py budget --mission M --authority 120M --topups 3 --step 40M` records the
   Owner's authority (through `gsd_mission.set_authority`) and a top-up policy in
   `<state>/mission-topup-<M>.json`, with the execution root's HEAD as the progress base.
2. **Auto top-up.** `mission_topup.py sweep` (run by the 5-minute sweep after `supervise`) looks at every mission
   that has a policy. It raises the authority by one step, releases the hold and wakes the worker with a decision
   only when ALL hold:
   - the mission is not terminal and holds a cost hold whose reason is the mission-authority trip
     (`cost breaker (mission authority)`); the default-ceiling, estimate-ratio and stall trips are never topped up;
   - top-ups used < policy maximum;
   - **progress since the last grant**: the execution root has commits after the recorded head whose diff touches
     something other than `.planning/` (bookkeeping is not progress).
   Each grant appends `{n, at, from, to, head, spent}` to the policy and a `authority_auto_topup` ledger row.
3. **Refusal is recorded and surfaced once.** No progress, top-ups exhausted, or an unmeasurable root leaves the
   hold standing (the policy records `last_refusal`), and the Owner is notified once per hold: Telegram when
   `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set, otherwise the refusal says `notify: no channel configured`.
4. **Suggest.** `mission_topup.py suggest --cwd <repo>` counts the open phases in `.planning/ROADMAP.md` and
   multiplies by a per-phase rate (default 40M, measured: 154M / 4 phases on this repo, 2026-10-15; override
   `CPP_MISSION_PHASE_TOKENS`), and prints the `budget` command to run.

## Anti-goals

- A top-up without commits: the stall breaker and this progress rule are the safety; spend without code is a stop.
- Touching a hold this module did not recognise (Owner pause, resource, stall, default ceiling).
- A second grant for the same hold (a sweep pass that crashes between grant and release must not double-grant:
  the grant is written to the policy before the authority is raised, and the next pass sees the authority
  already above the trip and only releases).

## Kill switch

`CPP_MISSION_AUTO_TOPUP=off` makes `sweep` a no-op. Removing the policy file disables it for one mission.

## Done means

`python tools/test_mission_topup.py` exit 0: grant with progress; refusal without progress (paired control);
refusal for bookkeeping-only commits; exhaustion after N; non-authority holds untouched; kill switch; no double
grant on a re-run; suggest arithmetic.
