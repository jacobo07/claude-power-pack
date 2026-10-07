# RESUMPTION -- Cognitive Economy Amendment A3 (goal ce-a3)

**Identity.** Worktree `C:\Users\User\Apps\pp-ce-a3`, branch `ce/a3` (off 5617f901 + merge a1/a1-2 at 9a02b315).
Card `vault/programs/cognitive-economy/gen2/AMENDMENT-A3-2026-10-07.md` (APPROVED, Owner 'y', pane 2aa0b0fb).
Thesis: pre-call goal admission exists (31f1e714/b79f4737); A3 binds panes by default, sub-caps coordinators,
splits the fresh floor host vs CPP, extends authority to GEX44.

**State.** Goal `ce-a3` declared 2026-10-07T18:55:10Z: cap 9,900,000 for sessions bound by cwd root
`c:\users\user\apps\pp-ce-a3`, host DESKTOP-PMT5BS8 only. Total program cap 12M INCLUDES coordinator pane 2aa0b0fb
(that pane's cwd moved into the root, so it binds too -- meter it with goal-status). U0 done. U1 launched 20:56 local
as headless sonnet (max 14 turns), packet `gen2/packets/A3-U1.md`, out.json in pane 2aa0b0fb's scratchpad.
Coherence anchor: `python tools/mission_spend.py goal-status --goal ce-a3`.

**Decisions.** No coordinating pane after U0: each unit = one packet + one bounded headless sonnet worker with cwd
= root. Live canary canary-20261007 belongs to pane 2a90c34a -- consume its CANARY.md, never re-run unless that pane
died without writing it. ~/.claude edits are Owner diffs (HR-001). A1 stays ECONOMIC_CONTAINMENT; A2 superseded.
Crossed cap = stop, never raised (raise needs `--owner` TTY anyway).

**U1 DONE (658b1c5b).** Receipt `gen2/evidence/a3/U1-RECEIPT.md`, A3AUTOPSY_PASS=10/10. Floor ~120k (not 105k);
floor x calls = 42-72% of each pane, growth 28-58%, 28-34% of calls carry no effect; repeated Reads negligible.
=> lever order: fewer pane calls (U2 binding/sub-cap) > floor (U3) > growth. Worker hit max_turns at 1,822,163
(1.52x of 1.2M, no commit; pane committed). Packets must budget turns from the ~120k floor and commit early.
**Budget after U1:** goal-status used 5,463,546 / 9.9M (settled 3.72M + open leases 1.75M), remaining 4,436,454.
U2+U3+U4+U5 planned 7.2M does NOT fit. Reforecast: U2 (2.0M, 16 turns) then U3 (2.0M); U4/U5 only if the remainder
allows, else STOP and ask the Owner for a new goal id (a crossed cap is never raised).

**Next 3.** (1) Check goal-status (open leases settle as panes end). (2) Write packet A3-U2 (default
binding by program path + coordinator sub-cap + superseded/stale/late-usage gates, extending
`tools/test_goal_budget_admission.py` V-GOAL; spec `vault/specs/goal-budget-admission.md`) using U1's top rent
classes, launch it the same way. (3) Then U3 floor probes, U4 GEX44, U5 UKDL/KV/CBR + A1 reforecast.

**Start.** In a FRESH pane with cwd C:\Users\User\Apps\pp-ce-a3: read this file only, then do Next 1.
