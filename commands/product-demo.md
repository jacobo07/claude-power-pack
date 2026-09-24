---
description: Turn a real user-facing flow into a reproducible, validated demo video (MP4/WebM + poster + manifest)
argument-hint: run|probe|check-spec --spec <spec.json> [--out DIR] [--viewport NAME] [--app-repo PATH]
---

# /product-demo

Drive the REAL running product through a semantic spec, capture settled states,
compose them in a device stage, render, validate and record provenance.
Owner module: `modules/product_demo/` (entry point `modules/product_demo/cli.py`; it runs the
browser worker `modules/product_demo/capture.py` and the renderer as bounded children through
`modules/product_demo/runner.py`).

## When to use (objective triggers)
- The Owner asks for a product demo, feature video, landing hero video, walkthrough or
  "record the flow" of software that runs in a browser.
- A user-facing feature is being declared done and its landing/docs need a current demo.
- A previously rendered demo must be checked for staleness after UI changes (`probe`).

Not for synthetic promo films with no product underneath: that is `motion-promo`.

## Run
```
python -m modules.product_demo.cli check-spec --spec demo.json
python -m modules.product_demo.cli run   --spec demo.json --out out/ --app-repo <app checkout>
python -m modules.product_demo.cli probe --spec demo.json --manifest out/<viewport>/manifest.json
```
Exit: 0 VALID/CURRENT · 3 refused/invalid/STALE · 4 UNKNOWN/verifier failure · 2 bad spec.

## Authoring a spec (semantic, never pixels)
- Targets by `role`+`name`, `label`, `testid` or `text`. `css` needs `"allow_css": true`.
  A target that is missing, hidden or ambiguous is a REFUSAL, never a skipped animation.
- Steps: `goto`, `fill`, `select`, `check`, `click`, `press`, `wait_text`, `assert_absent`.
  `film: false` for setup (sign-in). Secrets via `value_env` (never stored, never filmed as text).
- `callout` text is presentation. It must describe what the real UI does at that step.
- `forbid_text`: strings that must never be on screen (debug copy, test tenants).
- `fixture_text`: synthetic personal-data values that are allowed on screen. Anything
  else PII-shaped (email, NIF/NIE, IBAN, phone, card) refuses the capture.
- `viewports[].stage`: `raw` | `browser` | `laptop` | `phone`. Several viewports = several videos.
- Film a production build of the app, not a dev server (no dev overlay, no HMR, no compile stalls).

## What you get, per viewport
`<id>_<viewport>.mp4` (+ `.webm`, `.poster.png` when listed), `telemetry.json`,
`timeline.json` (every time compression recorded), `stage_<vp>.html` (regenerable),
`manifest.json` (spec hash, app commit, frameset hash, toolchain, outputs, verdict).

## Guarantees and refusals
TARGET_DRIFT · TARGET_AMBIGUOUS · AUTH_REDIRECT · FORBIDDEN_TEXT · PRIVACY_REFUSED ·
PRODUCT_ERROR (console error, HTTP >= 400, route 404) · BLOCKED_ENV. System work is never
shown faster than 3x real time. Cursor clicks land on the recorded click point. Callouts
never cover the target and are placed to hide no measured product text. Every browser
and render step runs in a Windows Job Object: a timeout kills the whole tree, and only it.

## Gate
`python tools/test_product_demo.py` (V-DEMO-*, real browser) · `--fast` for the pure gates.
