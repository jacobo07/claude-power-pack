# BCAP-2 laptop-plane steps

Run 2026-11-20 by coordinator pane adcdff7b (Owner: "go ahead with these first"), branch `bcap2/laptop-steps`.

## DONE — Phases 4/5 real-browser verification
`python tools/bcap2_browser_bench.py --anime <anime.umd.min.js>` -> **21 PASS / 0 FAIL**, Chromium 148.0.7778.96,
anime.js 4.5.0 UMD (jsDelivr, MIT, sha256 8d5b3a58a1f6..., not vendored). Page: `vault/programs/bcap-2/browser/bench.html`;
evidence: `vault/programs/bcap-2/browser/BROWSER_RESULTS.json`. Every section has a GOOD and a BAD pole, and the
browser-MEASURED record is fed into `modules/cdio/ux_contracts.py`, so the contract is judged on observed values:
- real hitboxes (elementFromPoint grid): 20 px glyph + invisible inset reaches >=44 px and a tap 8 px outside lands; the
  bare glyph is caught `undersized-hit-target`; the whole label row toggles the checkbox; a nested Delete without
  stopPropagation is caught `nested-interactive-steals-tap`.
- first invalid field: enabled submit focuses Work Address, scrolls it into view, shows summary + message; the
  disabled-with-no-reason pole is caught `opaque-disabled-action` + `validation-block-with-no-error-path`.
- skeleton CLS: 0 px shift below a geometry-reserving skeleton; the spinner pole shifts content below (> 0).
- optimistic rollback: count shows 11 at once, returns to 10 on HTTP 500 with a message; the no-rollback pole keeps 11.
- reduced motion: under `reduce` the honouring element is final at 120 ms; the ignoring one is mid-flight (caught);
  final states equal across modes; without `reduce` it still animates.
- timeline unmount: `createScope().revert()` stops a looping timeline (0 ticks after unmount); removing the node
  without cancel keeps ticking (caught).
Instrument check: the first run returned 20/1 (an optimistic read raced the routed 500); fixed by reading in the
click's own task, which shows the bench can return the other answer.
Limits: one engine (Chromium), one viewport (800x700), synthetic bench page, not a CPP product surface; WebKit/Firefox
and touch input unmeasured.

## OPEN — Phase 5 (Synsation) video re-inspection
The four source videos (backlog `2026-10-13_synsation-ux-patterns-absorption.md`, sha256s listed there) are not on
this laptop as far as measured: none in Downloads/Desktop/Videos/Documents/Temp/Claude app data; a whole-profile
search by name and by each video id had matched only the backlog notes when this was written (still running). They
were uploaded into the 2026-10-13 session, so they likely never lived on disk. UX-07..20 stay INFERRED until the
Owner supplies the files (then: `video-analyzer` with audio transcript, verify sha256 first).

## PARTIAL — Phase 9 (Ruflo) canary
Evidence: `vault/programs/bcap-2/ruflo/CANARY_2026-11-20.json`.
- `npm audit --json` on the sandbox lockfile: **0 vulnerabilities** (all severities) -> `audit_error` passes.
- `npm audit signatures`: UNMEASURED (GEX44 npm on node 18 predates the 2025-01-29 registry key rotation:
  EEXPIREDSIGNATUREKEY). Re-run with npm >= 10.
- Fixture drive against the real MCP transport: NOT RUN. No isolated plane exists (GEX44: bwrap/unshare cannot create a
  net namespace, no docker access, node 18 < engines >=20; laptop: npm broken). Running it without isolation would be
  third-party code with live egress next to GEX44's live ~/.claude. Unblock options are listed in the JSON; each needs an
  Owner-approved host change. Activation stays REFUSED. Nothing has left the sandbox.

## Platform note
On Windows, `test_bcap2_dbg` (Linux-path real-bug replay), `test_bcap2_tdd` (needs the pytest+coverage interpreter) and
`test_bcap2_ruflo` (symlink privilege, WinError 1314) fail for platform reasons; `test_bcap2_synsation` 35/0 and
`test_bcap2_animejs` 35/0 pass. done_gate is a GEX44-plane gate.
