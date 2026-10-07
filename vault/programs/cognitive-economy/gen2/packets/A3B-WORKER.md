# Work packet -- Amendment A3b (goal ce-a3b), Owner 'y' 2026-10-07 (pane 886d7bb9)

work_tree: C:\Users\User\Apps\pp-ce-a3b   (branch ce/a3b off ce/a3 2b59d938; never push; never edit ~/.claude/ -- Owner diffs only, HR-001)
goal: ce-a3b, cap 8,000,000 processed INCLUDING any pane; you are bound by cwd. A guard refusal = stop, write state.
done_gate: python tools/test_cognitive_economy_program.py --generation 2 --final  (C21-C25 green; frozen clauses OPEN)
bound: 45 turns total. Commit after every unit. Append facts to `gen2/evidence/a3b/RECEIPT.md` AS YOU GO.

Context you need and nothing else: `vault/plans/ce-a3-RESUMPTION.md` (A3 state, U2 rerun scope add),
`gen2/packets/A3-U2.md` (packet 2b59d938), `vault/specs/goal-budget-admission.md`, `gen2/evidence/a3/U1-RECEIPT.md`.
Pathspec commits only. Never write C:\Users\User\Apps\pp-ce-a3 (goal ce-a3, another pane).

Law: CPP present = its SessionStart/UserPromptSubmit hook runs. Presence must bind every session to a budget before
expensive cognition; a missing setting resolves to the cheapest certified value, never to the maximal one. Extend
the existing owners (session_budget_guard.js, mission_spend.py goal-*, gsd_mission.py arm/envelope/admit,
loop_budget); build no new system. A1 moratorium stays: no ContextImage compiler, no extinction engines.

## Units (in order; skip a unit only by writing why in RECEIPT.md)
B0 (cap 1M) Deterministic entry-point matrix: a script scanning the launch sites (claude --bg / -p, Agent/Task
   spawn, gsd_mission arm/relay, tranche_driver, scheduled tasks, kclear/kresume, GEX44 bridge) and printing, per entry:
   budget binding today, null-config behaviour, interceptable pre-launch (yes/no/host). Output
   `gen2/evidence/a3b/ENTRY_MATRIX.md`. No model reasoning beyond writing the scanner.
B1 (cap 2.5M) U2 rerun from packet 2b59d938 plus its scope add: default binding (a session with no goal gets a
   per-session envelope derived from the measured ~120k floor; unbound = refused-or-enveloped, never unlimited;
   shadow first, kill switch CPP_SESSION_BUDGET=off), coordinator sub-cap, goal refusal gets NO closeout Reads,
   UNKNOWN fails closed in goal mode at gsd_mission.admit_route (processed None) and loop_budget.admit_subagent
   (est 0 / negative remaining). RED first, admitted control for every refusal (AC8). Extend
   tools/test_goal_budget_admission.py (V-GOAL).
B2 (cap 2M) Null-config in gsd_mission arm/envelope: no model -> sonnet for workers; no autocompact -> floor + packet
   + margin; no continue-max -> certified default; no packet -> raw planner/researcher grammar refused unless a
   recorded reason (legacy lane stays available with reason). Ralph relay renews the per-epoch admission from the
   remaining goal budget (defect: m-595b674b8e41 stuck LAUNCHING; A2 worker parked on a permission prompt).
B3 (cap 1.5M) Canaries, prompts never mention economy: zero-activation (a normal small task in a separate project
   dir, read-only or scratch branch; evidence = guard binding row + envelope), null-config arm, expensive-path denial
   (raw grammar without reason refused; with reason admitted), tiny-cap budget (refusal before the call, closeout
   share 0). Record each as PROVEN / OBSERVED / UNJUDGED.
Ledger: obligations C21 (no session unbounded by default), C22 (null-config = certified value), C23 (expensive path
   denied without reason, available with reason), C24 (zero-activation canary, separate project), C25 (relay renews
   admission), each with an executable check once its unit lands. Spend: `measure/attribute.py --session` AGREE only.
</content>
</invoke>
