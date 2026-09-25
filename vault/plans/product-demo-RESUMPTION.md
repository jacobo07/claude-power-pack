# RESUMPTION: Product Demo capability (closed 2026-09-25 -- first proof LIVE)

IDENTITY. Claude Power Pack `C:\Users\User\.claude\skills\claude-power-pack` (branch
`feature/knowledge-acquisition`, shared: pathspec commits, re-read HEAD first). Capability
`modules/product_demo` + `/product-demo`; gate `python tools/test_product_demo.py` (23 gates).

STATE (all verified).
- PP commits: a62e9bf be1dc28 dc0cf8a f463feb d309865 9ae2eca dfe149c 90ccbde 192390b bf5942f
  9fa9516 82369d6 551e479.
- InfinityOps (live): #419 7b0d94cd same-origin auth (QL sign-up restored) · #420 83268ab4 dark-theme
  contrast · #421 62829621 "See it work" section on https://quicklease.ai/ (desktop 16:9 cut).
- Production gate 2026-09-25: assets 200 (mp4 966,505 B / webm 733,814 B / poster 271,620 B); plays on
  1280 and 390 px (currentTime advances), no overflow, 0 console errors; reduced-motion = paused + controls.
- Demo source: InfinityOps `17_Businesses/QuickLease/demo/` (spec, run_demo.py, manifest).

OPEN (ranked).
1. Phone 9:16 cut: render was killed by the memory reaper (host at ~0.4 GB free). Re-render
   `run_demo.py --viewport phone` only after freeing RAM, then restore the phone branch in
   `ql-product-demo.tsx` (removed for the desktop-only ship).
2. Stage background: the cool grey stage canvas shows as a rectangle on the warm landing; add a
   spec-level stage background (e.g. `stage_bg`) to stage.py/template, re-render.
3. Fold `vault/knowledge_base/product_demo/ukdl-product-demo-2026-09-24.md` into ukdl-universal.md
   when that file is clean.
4. UNVERIFIED: iOS Safari autoplay, Core Web Vitals impact, sign-in on the QL host (same client path
   as sign-up), Google OAuth on the QL host, staleness probe against live QL.

START. Read this file; `python tools/test_product_demo.py --fast`; pick OPEN 1 or 2.
