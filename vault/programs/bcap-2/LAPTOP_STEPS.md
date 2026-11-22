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

## DONE — Phase 5 (Synsation) video re-inspection with audio
The Owner put the four videos in Downloads; all four sha256 match the backlog. Offline transcripts (video-analyzer
whisper.cpp, TRANSCRIPT_OK x4) kept OFF the public repo (third-party content; Owner 2026-11-20) at laptop
`~/.claude/private/bcap2-synsation-transcripts/`; per-claim verdicts with short quotes in `synsation/DISPOSITIONS.md`
("Audio re-inspection"). UX-07..09, 11, 13, 14, 16..20 CONFIRMED by wording; UX-10 and UX-12 are CPP-derived, not in
the source; UX-15 partial; video 4 is SPONSORED (Vanta), so UX-14..18 rest on one vendor source. New from audio: a
control disabled while a just-clicked action runs is correct; `check_disabled_control` now exempts `pending_submission`
only with `pending_visible` (test_bcap2_synsation 35 -> 38, seeded mutant flips).

## DONE (activation still refused) — Phase 9 (Ruflo) canary
Evidence: `ruflo/CANARY_2026-11-20.json`, raw `ruflo/canary/{adv,retry}.out.jsonl`, harness
`ruflo/canary/{run_canary.sh,driver.cjs,steps_*.json}`. Owner chose Docker on GEX44; `kobii` added to the docker group.
- isolation: `docker run --network none --read-only --cap-drop ALL`, proved per run (NET_FAIL inside, 200 outside).
- `npm audit`: 0 vulnerabilities. `npm audit signatures` (npm 11.19.1): 586/586 registry signatures verified,
  0 invalid/missing; ruflo and @claude-flow/* carry NO provenance attestation (residual confirmed by measurement).
- real `ruflo mcp start` (393 tools) driven with advisory fixtures: GHSA-vqpp fix OBSERVED (no escaped file on disk);
  `file://` refused (half of 5pxg); `__proto__` key ACCEPTED by memory_store; hgp6, rx87, jwwq, #4750 unreached
  (degraded / admin-gated / offline); session_export fixture defect; bridge and #3294 not driven by design.
- the CPP gateway refuses all 12 attack fixtures and accepts the benign poles.
- NEW: Ruflo attempted unsolicited egress to IPFS gateways (cloudflare-ipfs.com, w3s.link); blocked by isolation.
Nothing left the sandbox.

## Campaign B laptop steps: run 2026-11-22 (Owner "do laptop steps", pane 6e2df121)
Evidence: `saas-styles/LIVE_MEASURE_2026-11-22.json`, measured with Chromium 148, 1280x800, dark scheme, logged out. Screenshots and
visible text stay off the public repo, at `~/.claude/private/bcap2-saas-refs/` on the laptop. Only their sha256 is committed.
- **B1 DONE (data).** All 4 surfaces were captured. ChatGPT and Perplexity were measured headless and their composers were
  measured. claude.ai and Mistral served a Cloudflare challenge to headless, so they were captured headed:
  - claude.ai logged out is the sign-in page, which has no composer;
  - Mistral's composer sits behind a Terms of Service accept modal, which was not accepted, so it is NOT_MEASURED.
  This bank stays external corroboration for style 3, never a PASS.
- **B2 already DONE 2026-11-20** (coordinator pane adcdff7b, `UPSTREAM_BRAND_PROBE.json` `bi16_cross_platform`). The Windows run
  gave combined hash 84c031a31fbb, identical to GEX44's Linux run. macOS was not measured. No CCF adapter was built. Not re-run.
- **B3 measured; rules stay PROVISIONAL until someone reviews this data.**
  - Rule 5, focus ring after one Tab, measured on all 3 sites:
    - Linear: 1px solid rgb(94,105,209), offset 2px;
    - Vercel: 2px solid rgb(82,168,255), offset 4px;
    - Raycast: outline-style `auto`, a browser-drawn ring, so its computed colour is not the painted colour.
  - Rule 6, dark modal measured on 2 of 3 sites:
    - Linear: page rgb(8,9,10), command menu rgb(15,16,17);
    - Vercel docs: page rgb(0,0,0), command menu rgb(10,10,10);
    - Raycast: no public modal was found.
  - A first pass counted a hidden `role=dialog` node on vercel.com as a modal. That result was rejected, and the visibility
    check that replaced it re-finds Linear's modal.
- **B4 BLOCKED.** The laptop has no Docker or VM, so there is no clean-room plane here. Driving hgp6, rx87, jwwq and #4750 also
  needs a networked, throwaway Ruflo, which is the Owner's call. Activation stays refused.

## BLOCKED-ON-LAPTOP (campaign B) - Phase 1 / Phase 6 inputs
B1. SaaS style 3 reference bank (conversational AI surface): ChatGPT, Perplexity, Claude.ai and Mistral return 403 to GEX44, so
    no reference could be read here (`saas-styles/REUSE_LEDGER.md` row 2). On the laptop, in a real browser, save one screenshot
    plus the visible text of each of the four chat surfaces (logged out landing/composer view) under
    `vault/programs/bcap-2/saas-styles/refs/` and commit them. Owner confirmed option (b) for style 3, so Phase 6 builds it from
    the dataset's own rules and records this bank as the missing external corroboration, never as a PASS.

B2. BI-16 cross-platform determinism (sigilgen c3f605b7): GEX44 measured same-host, two processes, 11 cases, one combined hash
    (`UPSTREAM_BRAND_PROBE.json`). On the laptop (Windows, Node >= 22): clone sigilgen at c3f605b7, `pnpm install --ignore-scripts`,
    build, run `scripts/check-determinism.mjs`, and commit the combined hash beside the GEX44 one. Same hash = cross-platform
    identity PASS; a different hash is the finding, recorded as-is. A CCF adapter for the vector lane is NOT built (needs that
    result and Owner direction on shipping a Node dependency); BI-16 stays PARTIALLY_PROVEN.

B3. SaaS style 1 (dark monochrome) CDIO-06 sec.10 rules 5 and 6 are still open: rule 5 needs a real Tab-key focus-ring
    measurement and rule 6 a reference with a dark modal, both against live third-party sites. On the laptop, in a real
    browser, record for Linear, Vercel and Raycast: the focus-ring colour/width after one Tab press, and the modal background
    vs page background (computed styles). Commit the numbers under `vault/programs/bcap-2/saas-styles/` as data; the rules stay
    PROVISIONAL until then.

## Platform note
On Windows, `test_bcap2_dbg` (Linux-path real-bug replay), `test_bcap2_tdd` (needs the pytest+coverage interpreter) and
`test_bcap2_ruflo` (symlink privilege, WinError 1314) fail for platform reasons; `test_bcap2_synsation` 38/0 and
`test_bcap2_animejs` 35/0 pass. done_gate is a GEX44-plane gate.

B4. Ruflo (campaign B Phase 7): the GEX44 residuals are measured (audit 0 vulns, dist structure). Still needs a clean-room plane: build `v3/@claude-flow/cli` from tag v3.78.0 in an isolated VM with scripts reviewed, then byte-compare against the tarball dist (GEX44 refuses to run upstream build scripts); and drive hgp6/rx87/jwwq/#4750 with a networked, throwaway ruflo. Activation stays refused.
