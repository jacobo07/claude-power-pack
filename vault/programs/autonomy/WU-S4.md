# WU-S4 -- Autonomy Convergence unit S4

Read `vault/programs/autonomy/PROGRAMME.md` first (session loop, continuation units, constraints).
Your scope: Plan section 2 item 4 + section 3 row 'Status'.

## Do
tools/programme_status.py: deterministic projection of a programme from durable state only (chain.json, mission records, receipts, goal ledger, git heads): state, current unit, worker, last verified transition, spend settled/reserved/UNKNOWN/available, forecast if present, blocker, next eligible transition, debt, and the HANDOFF block rendered. O(current state); never reads transcripts beyond spend measurement. Material-event notification only (programme done, blocked, authority edge). Tests incl. a large fake history that must not change output size.

Receipt: `vault/programs/autonomy/WU-S4-receipt.md`.
