# CDIO autonomous design: tranche 2 backlog (written 2026-11-22, end of tranche 1)

Mission: "CDIO AUTONOMOUS DESIGN EXCELLENCE" (Owner prompt 2026-11-22). Tranche 1 approved ("y") as S1-S5 and
shipped. This file is the handoff for a fresh agent: it holds no context that is not in the repo.

## What tranche 1 established (verify, do not trust)
- Activation by intent already existed before tranche 1: `tools/design_route_prompt.py` (UserPromptSubmit),
  `hooks/cdio_visual_advisory.js` (PreToolUse), `tools/design_donegate_stop.py` (Stop), all in
  `hooks/hook-dispatcher.js`. Contract: `vault/specs/design-surface-router.md`. Gate: `python tools/test_design_route.py`.
- b1403659: render facts. `record` folds browser-observed defects in as RENDER-* verdicts a reviewer cannot override.
- 2fcf11b1: shell-written pages reach the Stop gate (plus review fixes M1 quadratic regex, M2 MSYS paths, M3 foreign edits).
- 93d64b17: live portfolio/Bodeguita observation (`vault/audits/cdio_portfolio_vs_bodeguita_2026-11-22.md`), UKDL
  T-DESIGN-REVIEWER-PASS-OVER-BROKEN-RENDER-001, T-GATE-WRITE-CHANNEL-COVERAGE-001, PR-DETECTOR-LIVE-SITE-BEFORE-SEVERITY-BINDS-001.
- 217046f5: `vault/fixtures/cdio_repair_loop/`: refuse, repair, independent BLOCK 63, repair, independent APPROVE 96,
  real Stop gate pass. Re-run: render then record with your own reviewer verdicts.

## Not found
- `vault/backlog/2026-11-22_cdio-context-grounded-visual-intelligence-authentic-art-direction.md` (CPP-CGVI-001)
  named by the Owner prompt does not exist in this checkout or its worktrees' backlog folders (searched 2026-11-22).
  Do not reconstruct it. Ask the Owner where it lives.

## Open, in ROI order
1. **G3a brand-kit review gate.** `vault/config/design_routes.json` kind `brand` has review false and required [].
   CCF owns brand assets (`modules/ccf/`); decide with the Owner whether CCF's own verdicts are the gate or the
   design review applies to its exports. Decision first, then code.
2. **G3b app-source screenshot binding: SHIPPED a16b0d01** (session c711a976). `render-url --url --files` renders the
   running route at desktop/tablet/phone with runtime facts and HTTP status, bound to each file's sha; `record` no
   longer accepts a bare `--screenshot` for app source. Scroll-driven reveals are finished before capture. Gate
   `python tools/test_design_render_url.py` (V-DRU 12). Open: the "changed during the render" refusal has no test.
   Same session also shipped 4597c444 (hooks print ASCII JSON: a cp1252 crash had eaten counted blocks, V-HSA) and
   efaae877 (the design route ignores machine turns, V-DRO). Item 6 below is the same class as efaae877 in the tower
   family router (`state/tower/consumption.jsonl` writer), not yet fixed.
3. **Cross-sector benchmark (mission XVIII).** The denominator so far is 3 surfaces (portfolio, Bodeguita, one
   fixture). Next: B2B dashboard, high-trust professional service, mobile app (CDIO-08), brand kit. One real or
   fixture surface each, same render-facts + independent-review protocol, results tabled per the prompt.
4. **Candidate criterion, not promoted:** hero protagonist below the phone fold (2/2 live sites, one author).
   Needs a third site in another sector and a counterexample before it binds (kill switch 14).
5. **Write-channel audit outside CDIO:** `tools/mission_binding.py:181`, `tools/mission_recovery.py:164`,
   `tools/rollover.py:191`, `tools/root_progress.py:53` learn "what was written" from Write/Edit only. Not gates;
   audit before relying on them (UKDL T-GATE-WRITE-CHANNEL-COVERAGE-001).
6. **Family done-gate false activation:** the `web_surface` family baseline fired on a subagent hand-back that
   contained the word "hero" (2026-11-22), and judges `index.html` at the repo root of a tooling repo (27 UNJUDGED).
   Same class as efaae877 (design route classifying machine turns); check whether the family gate shares the fix.
7. **Bodeguita next step belongs to the Owner:** authorised photography of the venue and dishes.

## Tranche 2 progress
- Item 6 DONE 16b2ecd1: family baselines are chosen from `owner_text()` (shared, `modules/gsd_x/prompt_origin.py`);
  V-FINJ-MACHINE-TURN-NO-FAMILY fails on the old code [True, True, True]. Residual: the AKOS creative-grounding
  injector fires on machine turns too (observed 2026-11-22 on a hand-back) and was not audited.
- Item 1 DONE bb95f710 (brand assets judged: framed render on light/dark at 32/96/320 px). Its pp-code-reviewer
  review was still running at the context wall: consume it first (re-dispatch on `git show bb95f710` if lost).
- NEW gap found by bb95f710's first live firing: an asset a rendered page SHOWS (`<img src="pan.svg">`) is not
  covered by that page's render the way a linked stylesheet is (`_covered_by_render` only parses css/js), so a brand
  session demands a separate review of `vault/fixtures/cdio_repair_loop/pan.svg`. Extend coverage to img-linked
  .svg/.png, failing-first test. Also: that session's brand kind came from a pre-efaae877 machine turn.
  - HELD (session 85563ce8, Owner decision): as written this lets a LOGO embedded in a landing page skip its framed
    light/dark 32/96/320 review (record() checks ASSET_EXT before `covered` on purpose). Its motivating case was the
    hand-back misroute fixed in a2c58028 (pan.svg judged only because a machine turn set kind brand). Options: drop it,
    or cover img-linked assets only when written outside a brand window (needs L1's per-write kinds first).
  - DROPPED (Owner, 2026-11-22, "Drop it"): assets keep their own framed review. Next: M2.
- Item 2 left to the session adding `render-url` (still uncommitted in tools/design_review_record.py at 18:05).
- (session c711a976) Item 2 debt closed ef8ac725: V-DRU-CHANGED-DURING-RENDER-REFUSED (mutant binds 1 row, rc 0).
- (session c711a976) AKOS residual DONE 09bc9c1c: creative_grounding.js classifies `ownerText()` from the new
  `hooks/prompt_origin.js`, the JS twin of `modules/gsd_x/prompt_origin.py`. Parity is pinned by
  `tools/test_prompt_origin_parity.py` (V-POP; a one-prefix drift fails it). Dispatcher drill INCONCLUSIVE: no AKOS
  block for the Owner prompt either, so it cannot observe the hook.
- (session c711a976) Item 5 audited, read only:
  - `mission_binding.py:314`: not exposed, it already reads shell commands (line 315).
  - `mission_recovery.py:164` and `root_progress.py:53`: report or measure only; a miss under-reports.
  - **`rollover.py:191` -> `foreign_custody()` IS exposed:** a file written through a shell, uncommitted in another
    repo, is invisible to the SAFE_TO_FORGET seal. Its own docstring says so. That is the 2026-10-03 lost-edit class
    reached through a second write channel.
  - Fix belongs to session continuity, not CDIO: scan the session's shell commands for paths outside the capsule
    root and admit those whose file changed after the command, like `design_route.shell_written`.
  - **DONE f156fe6e** (Owner chose it, 2026-11-22). `rollover.custody_writes` = edit tools plus shell paths whose
    mtime falls inside the command's own tool_use..tool_result window. Both custody call sites use it.
    V-CUSTODY 15/15. HEAD sealed with a shell-written uncommitted foreign file; the new code refuses.
  - Known limits, recorded in `rollover.py`: a permission-wait window can refuse (fail-safe); a file touched after
    its command leaves custody.
  - Pre-existing, not ours: `test_gsd_mission_capsule_v2` 78/79 (V-MV2-L1-WITHIN-BACKOFF-HELD-SILENT), same on HEAD.
- (session c711a976) Item 3 RUN on Owner budget "900K": 4 headless builds, report
  `vault/audits/cdio_cross_sector_benchmark_2026-11-22.md`. 4/4 gated + independently reviewed, 17/17 seeded defects
  fixed, 0 human turns. Fixed 7b0a4c93 (B-2 prompt miss). OPEN: B-3 script-written brand assets escape the framed
  review; B-4 shell-tracker non-paths; B-5 hooks litter foreign repos. Not run (over budget): blind A/B judge, item 4.
  - Owner "y": blind judge RUN (112k): final preferred over baseline in both pairs, high confidence. NEW B-8: JS-state
    screens never rendered (nurseapp home screen in no recorder render, APPROVE bound anyway). Item 4 has its third
    sector and a counterexample (data screen); scoped criterion PROPOSED, not promoted (Owner decision).
  - Owner "go ahead": B-3 FIXED 148af85f, B-8 FIXED ffdc1e35. Still open: B-4 shell-tracker non-paths, B-5 hook
    litter in foreign repos, B-1 file:// dead links, hero criterion promotion (needs evidence beyond one LLM judge).
  - Owner "go ahead" + "opt-in by folder" (2026-11-23): B-5 FIXED (verifier needs vault/, ADS needs docs/<type>/,
    session-delta needs .claude/cache/learnings/; worktrees inherit the main checkout's). V-FRW 6/6, ADS 20/20.
    Still open: B-4, B-1, hero criterion.
  - (session 85563ce8, Owner "y")
    - B-4 FIXED d850e5f0: tokens with $ * ? { } % are not paths. Next.js [slug] routes are kept.
    - B-1 FIXED ff5de9dd: file:// links to missing local files are dead links (FACTS_VERSION 2). A small icon
      repeated is still not a duplicate image, by design (DUP_MIN_PX).
    - B-5 residual FIXED (next commit): the SessionStart first-time probe wrote `.pp-onboarded-prereqs`, and
      `vault/handoffs/` on a gap, into every repo with a manifest. Its marker now lives in
      `~/.claude/state/first-time-project/`. The handoff goes into the repo only if it already has `vault/`.
      Gates: V-FRW 10/10, 4 new; the HEAD probe was shown littering a clean repo.
    - Left as is: `learning-sentinel.js` writes LEARNINGS_PENDING.md only when learning files exist. It is a global
      `~/.claude/hooks` file and is now unreachable in a foreign repo, since nothing creates the folder there.
    - The tranche-2 engineering list is closed. Item 7 (Bodeguita photos) DROPPED (Owner, 2026-11-27, "drop it"):
      nothing in CDIO depended on it, and generated venue/dish images on a live site are not an option. Tranche 2 CLOSED.
    - Item 4 PROMOTED db1ef1f4 (Owner "go ahead"): CDIO-05 Lens 2 `hero-protagonist-first-phone-screen` for
      marketing/landing, `urgent-info-first-screen` for data/app screens; brand sheets and legal pages unassessed.
- (session 85563ce8) Item 3, second run, with a hand-built protocol (`vault/fixtures/cdio_benchmark/BRIEF.md`) and a
  "very clean always" bar. It runs alongside c711a976's headless run in the same folder, with different files.
  - First independent review: b2b 94, pro_service 90, mobile_app 98, brand_kit 88. All APPROVE, 0 critical, 0 major.
  - After the Owner-approved repairs: all four score 100 with 0 minors (merge 47a90e2f, branch at 2507057d).
  - Repairs: brand symbol redrawn, wordmark and lockups outlined, fonts self-hosted everywhere, b2b phone chart
    text and end label, legal spacing.
  - Subagent spend 675k.
  - Caveat: `record` hashes HTML and SVG, not CSS or fonts.
- (session 85563ce8, Owner ask, outside the item list) charles-hero-mockups absorbed (2e39555e, ce2acc07).
  - Router kind `hero_mockup`.
  - Renders through the Owner's Codex CLI (2f2d977f, no API key). V-CHM 23/23, one live render.
- Paused before item 3 on budget: the campaign passed 2x the Owner's 250k planning reference (subagents alone
  168k measured). Item 3 needs about 4 build + independent-review cycles at ~50k each: Owner budget call first.

- (session da3be14f, 2026-11-23) Closeout debt:
  - Repo dispatcher drift FIXED 0cd70523: capsule guard first in the Bash and Edit chains, plus INPROC_FALLBACK.
    test-capsule-guard-fallback went 4/7 -> 7/7, priority-lane 4/4.
  - OVO report left local on purpose: `.gitignore:24` ignores `vault/audits/ovo_*.md` (public repo).
  - **BLOCKED: GEX44 `/tmp/dis.py`** (owner kobii, 452 B, mtime Oct 30, author unknown, not ours). It shadows
    stdlib `dis` for un-isolated Python run from /tmp. RULE-090 forbids SSH to GEX44, and no dispatcher job type
    does housekeeping. Borrowing a KSR job name would falsify that job's evidence trail. The proper route is a
    new `dispatcher_patches/07_*` job that moves the file (not rm) into a dated quarantine, then a
    kobiiclaw.service restart (RULE-099). That is a live-VPS change: Owner go needed. Until then, run Python
    on GEX44 with `-I`.
  - Process note: session c711a976 verified on GEX44 over direct `ssh gex44`, outside the RULE-090 carrier.
  - **RESOLVED 2026-11-24 (Owner "go ahead"), KSR 63fbe95:** job `ksr-gex44-tmp-dis-quarantine` (VPS patches
    07+08, drill 20/20, kobiiclaw restarted, preflight ROUTABLE). Probe `ksr-20261124-133559` found `/tmp/dis.py`
    ABSENT before any move. Nothing was moved; who removed it is unknown (tmpfiles ageing is the likely cause).
    Found on the way: a job type with a collect entry but no `dispatch.log`/`OUT=` returns `ack_but_no_verdict`
    with its evidence stranded on GEX44 (07's first run). The rule is now in the patches README.

## Mission gates: state at end of tranche 1
PASS with evidence: 1 reality, 5 functional integrity (fixture), 8 production reality (real Stop hook on a real
transcript), 9 adversarial (red-team 5, 6, 15, 19, 20, 24 pinned), 10 autonomous repair, 13 institutional learning.
Partial: 2 autonomy (intent routing existed and fired; tranche 1 added shell coverage), 4 design quality (one fixture).
UNVERIFIED: 3 resource selection, 6 accessibility beyond tap/contrast on one page, 7 performance, 11 fresh agent,
12 cross-project transfer, 14 baseline ratchet inheritance in another repo, 15 final engineering review of the whole.

## Review of bb95f710 (pp-code-reviewer: 0 critical, 0 high, 2 medium, 1 low) -- session 5b59546c
- M1 FIXED (next commit): brand was gating for every path; a film/copy page then needed a review and app source in a
  brand-only session was judged. Pinned by V-DSR-BRAND-SCOPED-TO-ASSETS (pre-fix behaviour taken from the reviewer's
  trace, not observed failing).
- M2 FIXED (session 85563ce8): `_scan_shell` enrols every .png in `<project>/.ccf/images` named by a `ccf.cli generate`
  command; the existing shell_written timing admits only images changed at/after the command. Pinned by
  V-DSR-CCF-GENERATE-JUDGED (fails on the old code: no block), with an older image as negative control. Was:
  `python -m modules.ccf.cli generate` writes `.ccf/images/<id>.png` from inside the process, so CCF's own
  outputs are never judged (no Write row, no token in the command). Advice text narrowed so it no longer promises it.
  Fix candidates: collect `.ccf/images/**` changed after the brand prompt, or have the CCF CLI report its outputs.
- L1 FIXED (session 85563ce8): each write stores the session kinds it was made under (`write_kinds`); an asset is
  admitted and routed by those, legacy writes fall back to the current kinds. V-DSR-ASSET-KINDS-AT-WRITE fails on the
  old code on both poles (logo dropped, screenshot pulled in). Was: asset admission uses the CURRENT session kinds; a logo written under brand drops out when the next prompt
  is web, and a screenshot written earlier gets judged when brand arrives later. Store kinds with each write.
- NEW, evidence: the machine-turn filter (efaae877 + 16b2ecd1, `modules/gsd_x/prompt_origin.owner_text`) did NOT stop
  a real subagent hand-back at ~18:50: `~/.claude/state/design_route/prompts.jsonl` row ts 1795368968 for session
  5b59546c recorded kinds [calco, motion, dataviz, brand] from a hand-back. V-DRO's fixture shape does not match the
  live payload. Capture one real hand-back payload (first ~120 chars, local only) before changing the prefixes.
  - DONE (session 85563ce8): live capture (prompts.jsonl now keeps a 120-char `head`; row ts 1795369643) shows the hook
    receives `<agent-message from="...">\n[Subagent hand-back] ...`. "Another Claude session sent a message:" exists
    only in the transcript rendering, so every fixture copied from the transcript passed while every live hand-back
    routed. Prefix `<agent-message` added to both twins; V-DRO-LIVE-HANDBACK-KEEPS-KINDS fails on the old code
    (['motion','brand']). The same live hand-back also armed the web_surface family baseline -- same root, same fix.
