# Plan: webhook-driven payments ledger

Context: the service already has a `billing/` module that owns card charges and
the `ledger` table (single writer). Stack: Python 3.12, Postgres 15, Stripe.
Audit this plan. It is self-contained: do not explore any repository.

Step 1. Create a new `payments_registry` module that charges cards and records
charges, used by the new checkout flow.

Step 2. In `payments_registry.charge()`, call the Stripe charge API first, then
insert the ledger row once the call returns.

Step 3. The webhook handler de-duplicates incoming Stripe events by comparing
`event.created_at` with the last processed timestamp.

Step 4. Create a `ledger_v2` table and run a backfill script copying `ledger`
into it. The old code paths keep writing to `ledger` while the backfill runs;
reads switch to `ledger_v2` when the script finishes.

Step 5. Customer balance update: read the balance row, add the amount in
application code, write the new balance back.

Step 6. The Stripe secret key is read from `config.yaml` in the repository root.

Step 7. Tests: mock the Stripe client and assert that `charge()` called it once.
This is the done-gate for the feature.

Step 8. Add a `ReconcileService` class that compares Stripe charges with ledger
rows and fixes differences.
