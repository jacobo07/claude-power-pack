<!-- UKDL entries for the product-demo wave. Written here, not in ukdl-universal.md, because that file
     held another writer's uncommitted hunks on 2026-09-24. Fold into ukdl-universal.md when it is clean. -->
## Product Demo from the Real Product (CPP product-demo + QuickLease, 2026-09-24)

### Hard Rules

### HR-A-DEMO-FILMS-ONLY-STATES-A-REAL-USER-REACHES-ON-THE-DEPLOYED-PRODUCT-001

A product demo may film only states a real user reaches on the deployed product, driven through the
product's own UI. Overlays (cursor, callouts, frames) are presentation anchored to geometry measured
at capture, and never impersonate product state. Defects the camera would record are fixed BEFORE
filming, not cropped out. Evidence: QuickLease — an unmerged branch held the better story (filming
it would show an unreachable state); the region-proposal card, the intake's key moment, rendered
1.1:1 contrast under the dark theme and was fixed first (#420). #CROSS-PROJECT

### HR-A-SECURITY-TEST-PINS-THE-CHECK-THE-LIBRARY-DISABLES-UNDER-TEST-001

Before trusting a test that a security check admits X, pair it with a control that the same check
REFUSES Y. Libraries relax checks in test environments: better-auth 1.6.11 skips its origin check
whenever it detects a test (create-context.mjs:207). The unpinned accept-test passed while also
accepting https://evil.example; only the refuse-control exposed it. Pin the production setting in
the harness. Evidence: InfinityOps #419 lib/auth-origins.test.ts. #CROSS-PROJECT

### Process Rules

### PR-DRIVE-THE-DEPLOYED-PRODUCT-IT-IS-A-SMOKE-TEST-001

Capturing a demo from the deployed product is a production smoke test; run it before trusting a
funnel. Its first honest output here was a refusal, not a video: sign-up on the product subdomain
was CORS-blocked in production (auth client pinned to the apex origin). Localhost proofs could not
see it — there client and server share an origin. Evidence: InfinityOps #419. #CROSS-PROJECT

### PR-NEVER-TRUST-A-FILL-READ-IT-BACK-001

After filling a field through automation, settle and read the value back; refuse on mismatch. A
value typed before React hydration is silently reset by the controlled input, and the flow then dies
on native validation — a recorder that trusted the fill would film typing the product discarded.
Evidence: CPP product_demo INPUT_NOT_ACCEPTED (d309865). #CROSS-PROJECT

### PR-A-WALL-CLOCK-BOUND-NEEDS-THE-WHOLE-TREE-001

A timeout that kills only the direct child is not a bound: a grandchild holding the stdout pipe makes
communicate() wait for it. Measured: a 15 s timeout returned after 127 s; with a Windows Job Object
(KILL_ON_JOB_CLOSE, TerminateJobObject) it returns at 15 s and nothing survives, while an unrelated
sibling is untouched. The drill must assert the elapsed time — "no survivors" alone passes both ways.
Evidence: CPP product_demo/runner.py, V-DEMO-KILL-TREE (dc0cf8a). #CROSS-PROJECT

### Traps

### T-WAIT-FOR-URL-GLOB-MATCHES-THE-CURRENT-QUERY-STRING-001

`wait_for_url("**/new-case**")` returned instantly on `/sign-up?redirect_to=/ql/new-case`: the glob
matched the current URL's own query. Wait for leaving the page (`lambda u: "/sign-up" not in u`), not
for a substring of the destination. #CROSS-PROJECT

### T-PROCESS-MATCHER-WITH-FORWARD-SLASH-NEVER-MATCHES-WINDOWS-001

`-like "*@playwright/mcp*"` never matched `...\@playwright\mcp\cli.js`; only a broad
`*playwright*cli.js*` kept the janitor alive — and it also killed Python Playwright's driver
(`...\playwright\driver\package\cli.js`) at 10 min, mid-render. Enumerate real command lines before
narrowing a matcher; narrowing to the pattern as written would have disabled the janitor.
Evidence: be1dc28. #CROSS-PROJECT

### T-FIXED-LIGHT-TOKEN-UNDER-A-THEME-THAT-FLIPS-INK-001

A token defined for one theme (`--ql-paper: #FAF9F5`) under a theme that flips ink to light gives
1.1:1 text. The dark class also persisted across client-side navigation (auth-route default), so the
defect appeared only on the path real sign-ups take. Measure contrast of every surface token under
every theme that can be active, including via navigation. Evidence: InfinityOps #420.

### T-DECODING-EVERY-FRAME-AT-ONCE-FAILS-ON-A-STARVED-HOST-001

A page that awaits decode() of every image before ready (~420 MB of bitmaps for 36 frames at
2160x1350) had Chromium reject decode on a host with <1 GB free; small fixtures never showed it.
Decode lazily with a resident window. Evidence: 192390b.

### T-A-SUMMARISING-PROXY-MAKES-WATCH-EXIT-EARLY-001

`gh pr checks --watch` through the RTK proxy exited 0 reporting "33 pending": the summariser, not
GitHub, ended the wait. Poll `--json name,bucket` until no bucket is pending. #CROSS-PROJECT

### T-A-REFERENCE-RECORDING-CARRIES-ITS-MEDIUM-001

A reference video handed over as "the demo" was a phone screen recording of a landing page with the
demo embedded; status bar, URL bar and nav bar were the medium. Measure geometry and locate the
subject region before extracting motion grammar. Evidence:
vault/knowledge_base/product_demo/reference-hintora-forensics.md.
