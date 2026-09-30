# Plan: admin CSV export

Context: multi-tenant SaaS, Next.js frontend, Express API mounted at `/api`,
Postgres. Tenants have up to 5 million rows in `orders`. Audit this plan. It is
self-contained: do not explore any repository.

Step 1. New API route `/admin/export`, guarded by the existing `isLoggedIn`
middleware.

Step 2. The route builds its query as
`"SELECT * FROM orders WHERE tenant = '" + req.query.tenant + "'"`.

Step 3. The dashboard gets an Export button that calls `/api/admin/export`.

Step 4. On failure the button shows the caught error's message to the user.

Step 5. The route loads all matching rows into an array, converts it to CSV in
memory, and sends it.

Step 6. The feature is behind `EXPORT_ENABLED`, read from `process.env`.

Step 7. If the query returns no rows, the UI shows the toast "Export complete"
and downloads an empty file.

Step 8. Done-gate: a screenshot showing the Export button rendered on the
dashboard.
