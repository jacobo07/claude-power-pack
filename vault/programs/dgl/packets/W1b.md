# W1b -- dgl lease 2: lease epochs in GoalLedger, tests first (residual of W1)

Goal `dgl`. cwd = C:\Users\User\Apps\pp-dgl (branch dgl/durable-goal-lease). Envelope: target 4.5M, stop 4.9M.
git = & 'C:\Program Files\Git\cmd\git.exe' -C 'C:\Users\User\Apps\pp-dgl'; python = & 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe'.
Never Set-Location; absolute paths only. Never read transcripts, never read ~/.claude/state (the guard refuses it from a
bound session, correctly). Do not edit tools/gsd_mission.py, tools/mission_steward.py or hooks/.

## Why W1 failed (do not repeat)
W1 spent 15 calls / 2.07M READING and hit both breakers with no file written (W1-receipt.md). So:
- You WRITE in your 2nd call. Reading is bounded to the anchors below; do not open other files.
- Commit after every green step (the stall breaker halts a lease after ~1.05M with no tree change).

## Anchors (already read by W1; trust them, open only these regions)
modules/provider_routing/ledger.py: _gfold 189-222 (the only fold), declare_cap 256, renew 293, settle_stopped 335,
spawn 363, status 382 (status APPENDS leak rows; never use it in read-only paths). tools/mission_spend.py:
goal_declare 489-526 (Owner = `owner and not inside_agent()`), _main 802-918 (goal-* dispatch 861-898), state_dir 194.

## Design (decided by W1; implement exactly)
- New journal ops in the goal's own journal: `programme{value, source}` (same Owner rule as declare_cap),
  `lease_open{lease, cap, succession_id, prev_lease, reserves:{proof,closeout,recovery}}`, `lease_close{lease, reason,
  receipt}`, `authority_required{succession_id, need, executable}`.
- No programme/lease row => fold result byte-identical to today (one implicit lease L1, cap = goal cap).
- lease_open: idempotent by succession_id (2nd call returns the existing lease). CAS: prev_lease must equal the latest
  lease id, else refused naming the winner. It closes the predecessor. need = cap + reserves; executable = programme
  - settled - open(RESERVED+LEAKED) - reserves of other open leases. Short => exactly one authority_required row per
  succession_id; status AUTHORITY_REQUIRED.
- A cap change for a closed lease is refused in declare_cap (even Owner) and ignored by the fold.
- Per-lease used = settle watermark deltas booked while the lease was current + holds opened under it.
- CLI: `goal-lease-open --goal --succession-id --cap [--proof --closeout --recovery]`, `goal-lineage --goal`
  (read-only: _gfold(_read()) under no append), `programme-status --goal` (read-only), `goal-programme --goal --value
  --source --owner` (TTY like goal-declare --owner).

## Steps
1. Write tools/test_goal_lease.py now (V-gate style, `GOAL_LEASE_PASS=n/m`, exit 1 on any fail; every test uses
   GSD_LONG_RUN_STATE_DIR = tempfile.mkdtemp()). Gates: V-LEASE-LEGACY-FOLD (fixtures
   tools/fixtures/goal_lease/rf-p3b.spend.journal.jsonl -> cap 2,400,000 used 3,318,702; canary-20261007 -> cap
   3,000,000 used 3,973,468; copied into the temp goal dir before folding), V-LEASE-CAP-IMMUTABLE,
   V-LEASE-SUCCESSOR-IN-ENVELOPE, V-LEASE-ENVELOPE-EXHAUSTED (one row however many retries), V-LEASE-IDEMPOTENT,
   V-LEASE-DOUBLE-RACE (multiprocessing, two succession ids, one winner), V-LEASE-UNKNOWN-NOT-FREE,
   V-PROGRAMME-OWNER-ONLY, V-LINEAGE-READONLY (goal-lineage leaves the journal byte-identical). Run: record RED count.
   Commit.
2. Implement in ledger.py (additive) until GREEN. Commit.
3. CLI in mission_spend.py; extend the test with one subprocess call per new subcommand. Commit.
4. python tools/mutation_drill.py on an isolated copy: drop the CAS, ignore reserves, let a closed lease's cap change,
   make goal-lineage append. Each must turn a named gate red. Record kills.
5. Regression, before/after exit codes: tools/test_goal_budget_admission.py, tools/test_session_budget_admission.py,
   tools/test_tranche_driver.py.
6. Receipt vault/programs/dgl/W1b-receipt.md (<= 25 lines): `Status: DONE` on its own line (or PARTIAL + blocker),
   COMMITS:, red -> green, kills, regression codes, measured spend (processed tokens, not "tokens left").
7. Author packets/W2.md + packets/route-W2.json per vault/programs/dgl/CHAIN.md (authoring rule + unit W2 row), sized
   from YOUR measured per-call cost; W2 starts writing in its 2nd call too. Commit.

End with `HANDOFF NOTE: W1b done` (or the blocker).
