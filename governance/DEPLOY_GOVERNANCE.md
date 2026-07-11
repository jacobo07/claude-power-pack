# DEPLOY_GOVERNANCE.md — DONE means HTTP 200 on the real domain

> Normative. Domain: any project with a production deploy. Imperative. Origins cited inline.

## Pre-deploy checklist (all mandatory)
Run every item before any production deploy:
- [ ] Local build passes (exit 0).
- [ ] Local principal routes return HTTP 200.
- [ ] If copy changed: run V-COPY-01 (see `COPY_GOVERNANCE.md`). Visible hits → BLOCK.
- [ ] If the project processed third-party data: grep the staging area for PII
      (phone / email / national-ID patterns). Hits → sanitize before commit. (Origin:
      the portfolio's first commit staged a third party's phone number in a planning doc.)
- [ ] External dependencies (database, payments, email keys) are configured — OR the
      public experience does not break and does not promise functionality that is not
      wired. (Origin: Deng Chaowei — a transactional store needing a real database plus
      payment/email keys; a bare deploy would have shipped a broken store. Verify it works,
      or show an honest static preview instead of a live surface that is not real.)

## Headless Vercel deploy (this host)
- Use the CLI's native login (`vercel whoami`), not harvested credential files.
- If the first `whoami` fails, clear a stale `VERCEL_TOKEN` env var first — an expired
  token masks the valid CLI session. (Origin: portfolio headless deploy.)
- Run the cached CLI directly via node; a fresh `pnpm dlx vercel@latest` is flaky on this
  host.
- Verify HTTP 200 on the CUSTOM domain, never on the `*.vercel.app` alias.

## Next.js + Vercel build approval
- Before deploying a Next.js project, confirm `pnpm-workspace.yaml` `allowBuilds` holds
  real booleans for native dependencies (sharp, unrs-resolver, @swc/core, @parcel/watcher).
  Some repos ship these entries with instructional non-boolean text, which passes locally
  but fails the Vercel build. Set each to `true`, reinstall with `CI=true` (so pnpm
  rebuilds native deps non-interactively), confirm the local build exits 0, then deploy.
  (Origin: Regina + portfolio, 2026-07-11.)

## The rule
A deploy is DONE only when the public URL returns HTTP 200 on the real domain with the
end-user experience intact. A green local build is not a deploy.
