---
status: DRAFT 2026-10-27 (awaiting Owner approval; nothing implemented)
covers: [econ-raise-envelope-bootstrap, owner-raise, raise_goal, subelo-goal, envelope-less-goal, ccr-a2]
extends: [owner-control-plane-2026-10-19.md]
tier: T2 (spend authority, persisted ledger rows, hook-reachable)
---

# Owner raise on a goal with no envelope (bootstrap)

## Objective
`subelo <N> <goal>`, typed by the Owner, works on a declared goal that has no programme envelope and no lease cap in this
host's ledger. Today it is refused: `UNKNOWN: goal has no programme envelope or lease cap` (2026-10-27, `subelo 50M ccr-a2`,
goal declared with cap 81M on GEX44, only settled spend present on the laptop).

## Premises (verified in source, 2026-10-27)
- `tools/econ_plane.py:191-193` (`raise_goal`) and `:235-237` (`raise_capital`) return the refusal when `g["programme"] is None or cur["cap"] is None`.
- `modules/provider_routing/ledger.py:507` refuses a lease with no programme envelope (`unknown headroom is not free`).
- `tools/test_goal_lease.py:320` pins that refusal at the ledger level. It must stay true there.
- Authority today is the Owner-typed verb read by `hooks/econ_admission.js`, no model call. That path is what stays the only writer.

## Design
1. Only `raise_goal` / `raise_capital` bootstrap. `lease_open` and `set_programme` called by anything else keep refusing.
2. Bootstrap = programme := settled `used` + N (the typed amount is the whole new headroom; past spend is not forgiven),
   then the existing `_open_successor` opens the lease. One journal row source tag `owner-raise:bootstrap:<goal>:<uuid>` so a replay is a no-op.
3. Refused still: goal not in `read_index()`; N outside 1..RAISE_MAX; a goal whose journal is unreadable (unknown stays unknown).
4. The model never calls this. No agent verb, no tool, no new hook lane.

## Out of scope
Changing `RAISE_MAX`; auto-raising from a model turn; GEX44 ledger; the CCR compat pipeline (separate spec).

## Open question for the first implementation step
Confirm in `led._executable(g)` that programme is cumulative authority including settled spend. If it is not, design point 2 changes
to programme := N and the acceptance numbers below change with it.

## Acceptance (each driven red -> green)
- A1 envelope-less declared goal + typed raise 50M: ok, programme = used + 50M, one successor lease, executable = 50M.
- A2 crash replay: the programme row was written and the lease was not. The retry (matched by the lease id inside the row's tag,
  `_opener` in `tools/econ_plane.py`) writes no second programme row and opens exactly one lease. A second typed message AFTER a
  completed bootstrap is a new raise by the ordinary path, as it is today (not idempotent, and not claimed to be).
- A3 `lease_open` / `set_programme` called directly on an envelope-less goal: still refused (existing test at `test_goal_lease.py:320` stays green).
- A4 undeclared goal: refused. Amount 0, negative, bool, above RAISE_MAX: refused.
- A5 goal that already has an envelope: behaviour byte-identical to today (regression test on the current success path).
- Mutants: remove the bootstrap branch -> A1 red; remove the replay tag -> A2 red.
- Real-path check: the typed phrase through `hooks/econ_admission.js` on a scratch goal, not an in-process call only.

## Rollback
Revert the commit. A bootstrapped goal keeps its journal rows (append-only); `revoke <goal>` zeroes headroom.
