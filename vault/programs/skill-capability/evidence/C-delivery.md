# [C] opportunity / delivery / recall / precision -- evidence

Frozen C rule (ledger.json, never edited here):

> opportunity, delivery, recall and precision are computed by one gate from transcripts over a named window; recall and precision report n and are never extrapolated from n < 5

## Definitions

- opportunity: a commit-card judgement row with decision `opportunity` or `deny-card` that lists at least one foreign file (the capability was needed or shown at a commit).
- delivered: the capability reached the model at or before the judgement `ts` in the same session, by the card (decision `deny-card`) OR by an invocation (a Skill tool_use or a typed command counted by tools/skill_invocations.py); a mention, listing or hook body is never delivery.
- recall: delivered / opportunities whose delivery is measured. An opportunity with no transcript read or only untimed candidate rows is UNMEASURED and sits outside n, never counted as not delivered.
- precision: (delivered AND needed) / delivered with a needed label; needed = frozen D-CARD ground truth or the window fixture's per-row label.
- small n: a rate is printed with its n, and with n < 5 no ratio is printed or estimated.
- a skill with no opportunity detector reports opportunity UNMEASURED, never 0.

## Planes

- Window F is the fixture plane: synthetic rows authored for a known answer, host-independent.
- No figure in this file sums across windows. Each figure line carries its window prefix and its n.

## Window F

- [F] plane: fixture
- [F] selection: synthetic: every row authored for a known answer
- [F] opportunities: 8
- [F] delivery measured: 6
- [F] delivery UNMEASURED: 2 (outside the recall n): f0000000-0000-4000-8000-000000000006 opportunity 2026-10-01T11:30:00.000Z: no transcript read; f0000000-0000-4000-8000-000000000008 opportunity 2026-10-01T12:00:00.000Z: only untimed candidate rows
- [F] delivered: 4 (card 3, invocation-only 1, card and invocation 1)
- [F] recall: 4/6 = 0.667 (n=6)
- [F] precision: n=4 (< 5, not estimated)
- [F] pass-after-card rows (not opportunities): 1
- [F] no_opportunity rows: 1
- [F] judgement unknown or timeout rows: 2
- [F] non-commit rows ignored: 1

## Commands

- command: python3 tools/test_skill_delivery.py
- command: python3 tools/test_skill_delivery.py --write-evidence

## D-SESSIONS

- 0 fresh sessions were consumed in this phase (frozen D-SESSIONS: new_benchmark_cap 10).
