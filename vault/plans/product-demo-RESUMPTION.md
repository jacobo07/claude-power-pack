# RESUMPTION: Product Demo capability (updated 2026-09-24)

IDENTITY. Claude Power Pack repo `C:\Users\User\.claude\skills\claude-power-pack`, branch
`feature/knowledge-acquisition` (shared with another live writer: commit by pathspec only).
Thesis: `modules/product_demo` turns a REAL product flow into a validated demo video; QuickLease
is the first proof. Plan: `vault/plans/product-demo-capability-2026-09-24.md`.

SEALED (commits): a62e9bf plan + forensics + Recordly disposition · be1dc28 janitor no longer
kills Python Playwright (matcher + 3 copies, 13/13) · dc0cf8a product_demo module + 19 gates ·
f463feb /product-demo command, CLAUDE.md activation, liveness (10/10 reachable) · d309865
INPUT_NOT_ACCEPTED guard (20/20). Gate: `python tools/test_product_demo.py` (20/20, ~5 min).
Coherence anchor: `modules/product_demo/cli.py` has RENDER_ATTEMPTS = 2.

OWNER DECISIONS. Film `/ql/new-case` (Property -> Rental intent -> Review & pay; stop before
Stripe). Capture against the DEPLOYED app (https://ql.infinityops.ai), fresh demo account per run
via the real sign-up, reserved `@example.com` address (drafts are invisible to ops and to the
case list; 20 draft creations per IP per hour). Two stages: laptop 16:9 + phone 9:16. Deploy
of the finished asset to the QL landing (quicklease.ai) is authorised; read the DEPLOY hard
rules first (`hardrule_compile.py --class DEPLOY`).

BLOCKER. Production sign-up on ql.infinityops.ai fails (cross-origin auth client, no
trustedOrigins). Evidence + proposed fix: `vault/knowledge_base/product_demo/
incident-ql-signup-cross-origin-2026-09-24.md`. The demo cannot be filmed until it is fixed;
fixing production auth is an Owner decision. InfinityOps worktree ready at
`C:\Users\User\Apps\io-ql-demo` (branch fix/ql-demo-readiness off origin/main 325d947b).

NEXT 3 ACTIONS.
1. Once sign-up works: write the QL spec (setup steps film:false via value_env; region confirm
   button is "Confirm <region>" -- discover the exact region string with one run), add
   `fixture_env` for the per-run email, run `cli run` for both viewports, look at contact sheets.
2. Embed the MP4/WebM + poster on the quicklease.ai landing (muted, playsinline, poster,
   preload=metadata, reduced-motion fallback), deploy, verify HTTP 200 + mobile playback.
3. UKDL promotion + baseline decision (agent-executable interaction path for UI features).

START. Read this file, then the incident file, then run the fast gate to confirm the tree:
`python tools/test_product_demo.py --fast`.
