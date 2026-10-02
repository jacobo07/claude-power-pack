---
id: SPEC-ECON-ROLLOVER
title: Economic rollover trigger — cross when it pays, not only at the 45 % wall
tier: T2
status: approved
covers: [economic-rollover, rollover-economic, rollover-trigger, context-rent, test_rollover_economic, weekly-limit-burn-2026-10-02]
owner_go: "go ahead" (2026-10-02), after the weekly-limit RCA (vault/plans/weekly-limit-burn-rca-2026-10-02.md §11)
---

# SPEC — Economic rollover trigger

## Problem (measured, RCA §10-11)

Active rollover (`/kclear` -> gate -> `/clear` -> `/kresume`) is ON, but is asked only at the
advisory wall, 45 % ≈ 450k tokens on a 1M window. The break-even decider
(`tools/rollover.py::decide`) runs once, in SHADOW, at 40 %, without `start_head`, so its
work-boundary test needs a clean tracked tree, which a shared tree never has: 110 of 126
in-window decisions were "worth it, but not at a work boundary". Sessions pay re-read rent on
the band between their ~126k floor and ~450k.

## Behaviour

1. **Start head.** On the first Stop of an ordinary session (no mission marker) inside a git
   repo, the watchdog records `HEAD` as the session's start head.
2. **Evaluate on a commit.** On a later Stop with `used_pct >= CPP_ROLLOVER_ECON_PCT`
   (default 20) whose `HEAD` differs from the last evaluated head, the watchdog spawns the
   existing detached shadow with `--tier econ --start-head <start head>` and records the head
   it evaluated. Cardinality: at most one evaluation per commit per session, never per Stop.
3. **Act on the verdict.** `rollover.py shadow` writes its decision to
   `<state>/decisions/<session>.json` with the head it judged. On a later Stop, if that file
   says `would_rollover: true` for the current `HEAD`, the watchdog sets the existing ASK flag
   and returns the `/kclear` block. From there the existing step 2 (gate -> `/clear`) runs
   unchanged.
4. **Quality authority unchanged.** Only a SAFE_TO_FORGET gate verdict on the capsule the
   model sealed licenses `/clear`.
5. **No compact fallback for an economic ask.** If the capsule never arrives
   (`ROLLOVER_MAX_WAIT` Stops), the economic ask withdraws: ASK/WAIT flags cleared, the head
   recorded as declined (no re-ask until the next commit), ADVISORY and CLEAR flags untouched,
   so the 45 % wall still fires exactly as today.
6. Mission workers, sessions outside git, and `used_pct` below the floor are never asked.

Kill switches: `CPP_ROLLOVER_ECONOMIC=0` (this trigger only), `CPP_ROLLOVER_ACTIVE=0` (all).

## Acceptance (`python tools/test_rollover_economic.py`)

- would_rollover at the current head -> ASK flag set + `/kclear` block (control: it fires).
- would_rollover for a stale head, would_rollover false, below the floor, mission worker,
  kill switch -> no ask (each paired with the firing control).
- No commit since the last evaluation -> no second spawn (cardinality).
- Economic ask whose capsule never arrives -> withdraws without clearing ADVISORY and without
  setting CLEAR (the wall path survives).
- `rollover.py shadow --start-head` writes the decision file and passes the head to
  `at_boundary`, so a session commit is a boundary on a dirty tree.
- Existing suites unchanged: `test_rollover.py`, `test_rollover_active_path.py`.

Production Reality: the rollover ledger shows `tier: econ` candidates with `would_rollover`
true, followed by `rollover_kclear_asked route=economic` rows, and the mean context per call
measured by `token_ground_truth.window_usage` against the 2026-10-02 window.

## Rollback

`CPP_ROLLOVER_ECONOMIC=0`, or revert the commit. Nothing else reads the decision files.
