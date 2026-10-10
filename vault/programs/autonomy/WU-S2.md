# WU-S2 -- Autonomy Convergence unit S2

Read `vault/programs/autonomy/PROGRAMME.md` first (session loop, continuation units, constraints).
Your scope: Plan section 2 item 2 + section 3 row 'Programme authority'.

## Do
The goal ledger in mission_spend (goal-declare/goal-status, goal autonomy-convergence) is the programme authority. Close its gaps: (1) a mission armed with plain `arm` whose cwd is a declared goal root binds to that goal (no new parent capital from a new mission id); (2) one programme spend view: settled / reserved / UNKNOWN / available, measured from transcripts, no pane arithmetic; (3) session roles worker / control / interactive so Owner chat is attributed but not mixed into productive spend; (4) unattributed material spend is reported as a telemetry failure. Tests incl. mutation drill: a new mission id under the same root must not reset spend.

Receipt: `vault/programs/autonomy/WU-S2-receipt.md`.
