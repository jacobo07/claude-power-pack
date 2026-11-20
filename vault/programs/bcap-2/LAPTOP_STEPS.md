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

## Platform note
On Windows, `test_bcap2_dbg` (Linux-path real-bug replay), `test_bcap2_tdd` (needs the pytest+coverage interpreter) and
`test_bcap2_ruflo` (symlink privilege, WinError 1314) fail for platform reasons; `test_bcap2_synsation` 38/0 and
`test_bcap2_animejs` 35/0 pass. done_gate is a GEX44-plane gate.
