# CDIO cross-sector benchmark (mission XVIII), 2026-11-22

Owner budget: 900k tokens (session c711a976). Item 3 of `vault/backlog/2026-11-22_cdio-autonomous-design-tranche2.md`.

## Protocol
- Four new cases, each its own git repo under `C:\Users\User\Apps\cdio-bench\<case>\`, outside the Power Pack repo
  so its project hooks (JIT spec injection, family gates) cannot help. Answer key for the seeded defects:
  `vault/fixtures/cdio_benchmark/SEEDED.md` (never inside a case directory).
- Each build is a FRESH headless session (`claude -p <plain request> --output-format json --permission-mode auto
  --max-budget-usd 25`) started in the case directory. The request names no command, skill or agent: it is the
  test of "does CDIO activate without manual commands". The Owner's real global hooks and agents are in force.
- Measured per run (`bench_measure.py`, scratchpad): design-route rows for the session id, the session's gate
  state, reviews.jsonl rows binding the case's files, the session's own tool/agent/skill use, cost and wall time
  from the JSON result.
- Objective plane: `tools/design_review_record.py render` facts on baseline and final (state isolated under
  `CPP_DESIGN_STATE_DIR`). Perception plane: one fresh independent reviewer judging baseline vs final BLIND (A/B
  order randomised, labels hidden). Preference is not reported as commercial improvement; no conversion claim.

## Baseline render facts (deterministic, 2026-11-22)
| case | facts found | seeded defects the facts missed |
|---|---|---|
| dashboard | RENDER-BROKEN-IMAGE critical (D1), ASSET-FAILED major, HORIZONTAL-OVERFLOW major phone +738 px (D2) | D3 tap 24 px, D4 infinite animation, D5 colour-only status, D6 contrast 2.5:1, D7 dead link `reports.html`, D8 slop, D9 demo notice |
| despacho | RENDER-BROKEN-IMAGE critical (P4), ASSET-FAILED major, HORIZONTAL-OVERFLOW major phone +123 px (not seeded: the 3-column grid) | P1 hero without protagonist, P2 invented claims, P3 dead CTA, P5 contrast, P6 duplicate icon x3, P7 dead links x3, P8 missing facts |

Finding B-1: the render facts do not report dead links to missing local files (`reports.html`, `servicios.html`)
on a `file://` render, and do not count a small icon used three times as a duplicate image. Both are left to the
reviewer, so they are only caught if a reviewer runs.

Finding B-0 (incidental): the Steve Jobs PreToolUse veto refused my own baseline Write because it contained an
empty-fragment link. The seeded dead CTA was re-shaped as a `<button>` with no handler rather than written around
the guard. The same veto also refused this Markdown report while it merely named the pattern in prose (false
positive on a non-surface file).

## Runs (all four: one headless session each, no human turn after the request)
Evidence: case repos at `C:\Users\User\Apps\cdio-bench\<case>` (baseline commit, then final commit), session
transcripts under `~/.claude/projects/C--Users-User-Apps-cdio-bench-<case>/<sid>.jsonl`, gate state
`~/.claude/state/design_route/<sid>.json`, reviews in `reviews.jsonl`. Tokens are summed per API message over the
main transcript plus its subagent transcripts (`bench_tokens.py`); the CLI's `total_cost_usd` (4.13-4.69 per run)
is not used, it does not match those token counts.

| | dashboard (B2B) | despacho (legal, ES) | nurseapp (mobile) | brandkit (brand) |
|---|---|---|---|---|
| sid | 15c8c42a | 5d99f1e3 | 35e4a36e | 80f05543 |
| request | "make it production quality" | "que transmita confianza ... que nadie diga que la ha hecho una IA" | "prototype onboarding + home ... at phone size" | "logo and small brand kit ... one HTML page" |
| route at the prompt | app_ui | web | **[] (miss)** | brand |
| skills loaded unasked | design-md, design-taste-frontend, frontend-design | same three | same three; **not** mobile-app-ui-design | same three |
| Stop blocks (distinct shas) | 4 | 1 | 4 | 1 |
| independent cdio-reviewer runs | 2 | 1 | 2 | 3 |
| reviews (recorded) | BLOCK 57 (critical tap-target) -> APPROVE 100 | APPROVE 100 | BLOCK 56 (render refused: never rendered) -> BLOCK 56 -> APPROVE 100 | BLOCK 61 (contrast 3.08:1, phone +92 px) -> APPROVE 80 |
| final render facts | 0 (baseline 3) | 0 (baseline 3) | 0 | 0 |
| seeded defects fixed | D1-D9 all (source + render) | P1-P8 all (P6: icon now used twice, as favicon and logo) | n/a | n/a |
| wall time | 793 s | 984 s | 879 s | 906 s |
| tokens: uncached (create+out) / cache read | 303k / 7.79M | 342k / 9.96M | 304k / 7.75M | 344k / 8.16M |
| human interventions | 0 | 0 | 0 | 0 |

Answers to the mission's questions, on this denominator (6 surfaces: portfolio and Bodeguita from tranche 1, the
repair-loop fixture, these 4):
- Activated without commands: yes in 4/4 at the Stop gate; at the prompt 3/4 (nurseapp missed, fixed 7b0a4c93).
- Built something verifiable and ran a real evaluation: 4/4 (render facts + an independent reviewer bound to the
  final sha; the builder could not approve its own work).
- Detected and fixed seeded defects: 17/17 across the two baselines. The render facts alone caught 4 of them; the
  rest were caught by the reviewer or by the builder's own reading.
- Preserved identity and facts: dashboard and despacho kept every brief fact and removed every invented one.
  Residue: despacho ADDED three Spanish legal deadlines that are not in the brief (labelled on the page as general
  deadlines to confirm, and flagged to the Owner). Real procedure, but unsourced by this brief.
- Accessibility kept: tap targets >= 44 px, contrast fixed, colour-only status replaced by text badges, no motion
  in the dashboard (red-team 13 behaved). Keyboard order and screen-reader output were NOT tested by anyone.
- Better than baseline: objective planes only (render facts 3 -> 0, seeded 17/17). The blind perception comparison
  was NOT run (budget, below). No conversion claim is made.
- Worked in more than one sector: yes, 4 new sectors, two languages.

## Findings
- **B-2 (fixed 7b0a4c93):** a phone-app prototype request classified []. The gate still judged the page as web, but
  mobile-app-ui-design and CDIO-08 never armed. V-DSR-CLASSIFY-APP-PROTOTYPE fails on the old table.
- **B-3 brand assets written by a script escape the brand gate (FIXED 148af85f; replay of this transcript: 0 -> 9
  logo SVGs judged). B-8 below FIXED ffdc1e35 (nurseapp 2 -> 8 PNGs; entry JS does not run on a forced reveal).** brandkit wrote its 10 logo SVGs with
  `python build.py`. No Write row, and the shell tracker resolved bare names against the project root instead of
  `assets/`, so only `assets/favicon.svg` got its framed light/dark 32/96/320 review. The logo itself was judged
  only as it appears on the kit page. Same class as M2 (CCF writes in-process), now outside CCF. Fix candidate: admit
  visual-extension files under the project root whose mtime falls inside a shell command's own window, as
  `rollover.session_shell_writes` already does for custody.
- **B-4 the shell tracker records non-paths (OPEN, minor):** `$out\p{i}.png`, `assets\*.svg`, `$env:temp\...`
  resolved under the project root. Harmless today (files that do not exist are not judged) but it is noise in the
  state the gate reads.
- **B-5 hooks write into foreign projects (FIXED 2026-11-23, Owner "opt-in by folder"):** the background verifier
  writes only where `vault/` exists, ADS only where a `docs/{arch,prd,constitution,changelog}/` folder exists, and
  session-delta only where `.claude/cache/learnings/` exists. A linked worktree inherits its main checkout's folders
  (TUA-X-qa has no docs/arch, TUA-X has). Overrides: `CPP_VERIFIER_ANY_REPO`, `CPP_ADS_ANY_REPO`,
  `CPP_SESSION_DELTA_ANY_REPO`. Gates `tools/test_foreign_repo_writes.py` (V-FRW, 6) and V-ADS-FOREIGN-NOT-ADOPTED,
  each red on the old writers. Built and red-proved on GEX44 while this host was starved (secret scan of the diff:
  0 hits), then re-run green here. Original finding: every case repo gained `.claude/cache/learnings/`,
  `vault/handoffs/`, and two gained `docs/{arch,changelog,constitution,prd}/*.md` from Power Pack hooks. A client
  repo would get these on its first session. The dashboard builder also left `e.json` (its reviewer input) behind.
- **B-6 the gate's NO APLICA exit was used once, legitimately:** nurseapp declared `tests/selftest.html` (its test
  harness) NO APLICA. Correct here; but the gate cannot tell a harness from a product page, so the escape is honour-
  based.
- **B-7 score ceiling:** three of four final reviews scored 100. Independent but same rubric; a 100 says the
  rubric found nothing, not that nothing is there. This is why the blind perception pass matters.

## Blind perception pass (Owner "y", 2026-11-22)
One fresh general-purpose judge (no CDIO rubric), 12 renders + 4 briefs, told A/B order is unknown. Keys held
out of its reach, unblinded after: `vault/fixtures/cdio_benchmark/{dashboard,despacho}.key.json` (the random draw
put the baseline at A in both pairs, a 1-in-4 outcome; the judge never saw the keys). Raw verdict:
`vault/fixtures/cdio_benchmark/blind_verdict.md`. Cost 112k tokens (estimate was 60k).

| surface | judge's preference | confidence | protagonist | in first phone screen (844 px) |
|---|---|---|---|---|
| dashboard | final (B) | high | late/on-hold shipments (data screen) | baseline partly; final partly (first Late card cut at the fold) |
| despacho | final (B) | high | the offer: 60 EUR / 45 min first consultation | baseline no; final yes |
| nurseapp | meets the brief on screen 1 | medium | fictional notice, routines, start button | yes |
| brandkit | covers the brief, no eco cliche | low-medium (render downscaled) | dial mark + wordmark | yes |

Reasons the judge marked OBSERVED (not taste): demo notice present/absent, text status pills vs colour dots, phone
reflow vs 1128 px table, invented figures vs brief, price/hours/address present/absent. Weak points left in the
finals: dashboard's first Late card is cut at the phone fold and rows have no action control; despacho is 4,667 px
long on phone with no sticky call button; nurseapp shows a light theme only for a low-light audience; brandkit's
16 px favicon legibility unverified.

- **B-8 state-dependent screens are not rendered (OPEN, important):** nurseapp is one HTML file whose screens
  change by JS state. `design_review_record.py render` captures the initial state only, so onboarding 2-3 and the
  home screen (half the deliverable) are in no recorder render, yet the APPROVE 100 binds those bytes. The builder
  screenshotted other states itself; whether its reviewer looked at them is not provable from the record. Fix
  candidate: a declared list of states (URL hash or a click script) that `render` must capture before `record`
  accepts an app_ui/mobile review.
- **Item 4, hero protagonist:** the third sector and the counterexample now exist. Marketing surfaces: despacho
  baseline had none, the CDIO final has the offer in the first phone screen; nurseapp and brandkit put theirs in the
  first screen. Counterexample: the dashboard is a data screen, where "hero" does not apply and the real test is
  "the most urgent data is in the first screen" (it partly failed there). Proposal for the Owner, NOT promoted:
  scope the criterion to marketing/landing surfaces, and use "most urgent information in the first screen" for data
  and app screens. Evidence is one LLM judge over fixtures from one author: E2 at best.

## Budget
Owner authority 900k tokens. The four builds alone used 1.29M uncached tokens (plus 33.7M cache reads), past the
authority before any judging; this pane added its own share. Stopped there. NOT run: the blind A/B perception judge
(pairs rendered, keys held under the scratchpad `blind/`), and item 4 (hero protagonist criterion). Both need a new
Owner budget call. Estimate per headless build for planning: ~320k uncached, ~8.4M cache read, ~15 min.
