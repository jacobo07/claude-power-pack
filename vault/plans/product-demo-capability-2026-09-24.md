---
covers: [product-demo, demo-capture, demoability, quicklease-demo]
status: APPROVED 2026-09-24 (Owner Q&A) -> /ultra phase 3 revised; phase 4 audit pending
date: 2026-09-24
head_at_scan: 1f0cf4d (branch feature/knowledge-acquisition, 463 dirty paths from a concurrent writer)
---

# Product Demo Capability — revised plan (persisted copy; inline chat plan is authoritative)

## Owner decisions (Q&A, 2026-09-24)
1. QuickLease: fix the 3 filmed defects in InfinityOps first (pipeline sidebar hard-coded `complete`, developer copy
   "Llamando a /api/ql/leases POST...", tenant_id "ui-tenant"), then film the REAL form -> generate -> contract ready.
2. State: local stack (Next dev + local Phoenix), demo account via the REAL sign-up path, fixed fake-but-valid data. No backdoor.
3. Stage: BOTH laptop 16:9 and phone 9:16 (two viewports, two captures) — proves the stage layer is generic.
4. Ceiling: deploy to the QL landing authorized. DEPLOY hard rules read before that step; gate = HTTP 200 on the real
   domain + muted inline playback on mobile + asset path resolves.

## Reality snapshot (measured)
- Reference: ~/Downloads/Screen_Recording_20260921_202925_Brave.mp4 (26.26 s, 1080x2340, VFR ~52 fps, AAC). Phone recording of
  hintora.ai; the demo is an embedded video. Static stage; motion = app state + notch state pill + anchored numbered callouts +
  cursor; ~86% holds; beat every ~2.4 s; payoff-first loop. Inference: coded animation of a mocked desktop.
- Recordly: AGPL-3.0 + added terms (UI attribution, no branding); Electron GUI. Principles only; no code/dependency.
- Owners (audit, scratchpad/ownership_audit.md): motion-promo = frame-stepped canvas + imageio-ffmpeg/libx264 pipe, no external
  layer, MP4 only, no tree reap, zero external callers. sleepless_qa = QA dumper, swallows step errors, child-only timeout.
  cdio = evaluator. design-md/surface_architecture = read-only inputs; no demo-flow declaration anywhere.
  loop_budget.py (cognitive_os) = canonical bounded loop, PLANNED, zero callers. lib/license_gate.js = license tiers incl. AGPL.
  /liveness enumerates modules/** only. demo-ready = live-meeting readiness (name collision).
- HAZARD: tools/playwright_stale_killer.ps1 matches `*playwright*cli.js*` = Python Playwright's driver; kills at age >= 10 min;
  watchdog task installed + Running. motion-promo renders take 5-15 min.
- Doc drift: CLAUDE.md names `python tools/test_motion_promo.py`; real path is skills/motion-promo/tools/test_motion_promo.py.
- QuickLease app: InfinityOps/13_UI_Product_Layer/infinity_ui/app/ql; /ql/leases/new = static 19-field form -> /api/ql/leases ->
  Phoenix (QL_ENGINE_URL); cookie-gated by Better Auth via proxy.ts.

## Ownership (HR-NOVELTY-001: NEW_MODULE)
- modules/product_demo — primary runtime owner (spec, capture, telemetry, time map, compose, validate, manifest, staleness).
  Under modules/ so /liveness sees it. skills/product-demo = activation surface only.
- Shared, extracted: bounded browser run (wall bound + Windows process-tree reap + janitor-safe) and the libx264 encoder
  (motion-promo re-pointed to it; its 11 gates must stay green).
- CONNECT: cognitive_os/loop_budget (self-correction loop), cdio scorer + cdio-reviewer (judge), secret_firewall redactor
  (page-text privacy scan), license_gate.js (Recordly disposition), design-md/surface_architecture (read-only inputs).
- FIX: stale_killer matcher narrowed to MCP, with red-branch test.
- NOT: second Playwright lifecycle beside WebDumper/knowledge_acquisition without the shared primitive; zoom by default;
  any Recordly code.

## Commit series
1 vault forensics + spec · 2 janitor matcher fix + test · 3 bounded browser run · 4 encoder extraction · 5 spec + telemetry capture ·
6 time map + synthetic cursor · 7 composition stage (raw/browser/laptop/phone) · 8 validator (4 outcomes) + manifest ·
9 staleness probe · 10 skill surface + liveness + CLAUDE.md activation + doc-drift fix · 11 [InfinityOps] 3 QL fixes ·
12 QL demo proof (16:9 + 9:16) · 13 [InfinityOps] landing embed + deploy · 14 UKDL + baseline decision.

## Done-gates
V-DEMO-* unit gates (spec, missing-target refusal, time map, cursor/event alignment, callout binding, manifest, staleness,
4 validator outcomes), kill drill (Chromium tree gone), janitor red branch, mutation drills (reverting each guard reds its gate),
/liveness clean, motion-promo 11/11, real-app capture with zero console errors and no 401/404, ffprobe on outputs, contact
sheet inspected, landing HTTP 200 + mobile playback.
