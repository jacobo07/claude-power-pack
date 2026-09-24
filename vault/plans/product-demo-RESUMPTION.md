# RESUMPTION: Product Demo capability (updated 2026-09-24, late)

IDENTITY. Claude Power Pack `C:\Users\User\.claude\skills\claude-power-pack`, branch
`feature/knowledge-acquisition` (shared with live writers: pathspec commits only; re-read HEAD first).
Capability: `modules/product_demo` + `/product-demo`. Gate: `python tools/test_product_demo.py` (22/22).
Plan: `vault/plans/product-demo-capability-2026-09-24.md`.

SEALED (PP): a62e9bf plan/forensics · be1dc28 janitor matcher · dc0cf8a module+gates · f463feb wiring ·
d309865 INPUT_NOT_ACCEPTED · 9ae2eca incident · dfe149c fixture_env · 90ccbde hover · 192390b lazy decode.
SEALED (InfinityOps, live on prod): #419 7b0d94cd same-origin auth (sign-up on ql.infinityops.ai works;
apex sign-in regression-checked) · #420 83268ab4 dark-theme QL paper contrast (1.1:1 -> 14.3:1).

IN FLIGHT. InfinityOps worktree `C:\Users\User\Apps\io-ql-demo`, branch `feat/ql-landing-demo` (off 83268ab4),
uncommitted: `17_Businesses/QuickLease/demo/{new-case.demo.json,run_demo.py}`,
`components/ui/quicklease/ql-product-demo.tsx`, `app/quicklease/page.tsx` (section between hero and how-it-works).
Last desktop render was REFUSED by the validator (OCCLUSION: callout on the rental radio hid 1459 px^2 of
text) -> callout moved to save-2 in the spec; re-render needed. Phone render was running.
UKDL entries: `vault/knowledge_base/product_demo/ukdl-product-demo-2026-09-24.md` (ukdl-universal.md was
dirty from another writer; fold in when clean). Not yet committed.

NEXT.
1. `python 17_Businesses/QuickLease/demo/run_demo.py --out <dir>` (each viewport = 1 fresh demo account;
   20 drafts/IP/hour). Both must be VALID; look at a contact sheet of each MP4.
2. Copy `<id>_<vp>.{mp4,webm,poster.png}` to `13_UI_Product_Layer/infinity_ui/public/quicklease/demo/`
   (component expects `ql-new-case_desktop.*`, `ql-new-case_phone.*`); check sizes; commit; PR; CI; merge;
   verify https://quicklease.ai/ shows the section, assets 200, and the build-info SHA matches.
3. Commit UKDL file + update plan/handoff; baseline decision (agent-executable interaction path, PLANNED).

START. Read this file, then run `python tools/test_product_demo.py --fast`.
