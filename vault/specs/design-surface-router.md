---
covers: [design-surface-router, design-route, design-donegate, design-review-record, anti-slop-automation]
tier: T2
owner_decision: "Owner 2026-11-17 'go ahead' to: T2 spec, then build, a surface router + cdio-reviewer APPROVE as done-gate for all visual work"
---
# Design Surface Router + design done-gate

## Problem (measured 2026-11-17, worktree Apps\pp-bcap-verify at ab01353a)
The Owner asked whether it is automatic that no design looks like AI slop and that every PP design stack is used.
It is not. What runs on its own today:
- `hooks/cdio_visual_advisory.js` (PreToolUse Edit chain): scores the project's DESIGN.md tokens. It DENIES only in a
  project that has a DESIGN.md; elsewhere it advises. It never sees the rendered surface.
- web_surface B7 (2026-11-16): the Taste hard bans reach a prompt only when it is classified into the web_surface
  family, and `tools/family_donegate_stop.py` judges them only in a repo that is a family member.
Not automatic:
- the skills (`design-md`, `design-taste-frontend`, `frontend-design`, `mobile-app-ui-design`, `image-calco`,
  `motion-promo`, `web-design-guidelines`, ...) load only if the model chooses them from their descriptions;
- `cdio-reviewer` (the only judge of the rendered surface, APPROVE = score >= 80 and zero critical) runs only when
  someone dispatches it, and its verdict is a chat report: nothing persists it, so nothing can require it;
- the Taste lint (`modules/cdio/taste.py`, 27 checks) runs on no surface outside the web_surface family.

## What "always use all the design tools" becomes
Literally loading every design tool on every visual task is wrong, not just costly: `image-calco` exists to copy a
reference pixel-exactly, which contradicts the anti-template doctrine of `design-taste-frontend`; `motion-promo`
writes an HTML film that is not a web page. So the rule is: every visual task gets EVERY tool that applies to its
surface kind, chosen by a table, and the choice is checked, not trusted.

## Architecture
1. `vault/config/design_routes.json` (data): surface kinds (web, app_ui, mobile, calco, motion, dataviz, brand). Each
   kind: prompt regex, required skills, recommended skills, whether Taste and the rendered review apply, and the kinds
   it overrides (calco and motion override web/app_ui: a copy is judged against its reference, a film by its own gate).
2. `modules/cdio/design_route.py` (logic, no I/O policy): classify a prompt; map written paths to kinds; scan a
   transcript incrementally (Skill tool uses, `<command-name>` slash loads, Write/Edit/MultiEdit targets); hash
   surfaces; read review records; `judge()` returns per-surface problems.
3. `tools/design_route_prompt.py` (UserPromptSubmit-chain member): on a prompt that names a visual surface, inject ONE
   block: the kinds, the skills to load now (Skill tool), the recommended ones, and what the Stop gate will check. Records
   the kinds for the session under `~/.claude/state/design_route/<sid>.json`. Silent otherwise.
4. `tools/design_review_record.py` (the recorder `cdio-reviewer` calls):
   - `render <file.html>...` renders each HTML surface headless (Playwright Chromium, already vendored for
     motion-promo / product-demo) to PNG and records `{surface sha256 -> png}`;
   - `record --verdicts v.json --files f...` folds the Taste lint verdicts of every HTML file into the reviewer's
     verdicts, runs `modules.cdio.scorer.review_gate`, and appends one row to `reviews.jsonl` binding the verdict to the
     sha256 of every file. It REFUSES to record APPROVE when: fewer than 6 reviewer verdicts, fewer than 2 dimensions,
     or a file has no render (HTML: a `render` row for the same bytes; other files: `--screenshot` PNG newer than the
     file). Exit 0 only on is_done.
5. `tools/design_donegate_stop.py` (Stop-chain member): for every visual file written in this session inside the
   session cwd and still on disk, judge three things on the CURRENT bytes:
   - TASTE: HTML files, blocking (critical) Taste checks;
   - SKILLS: required skills of the session's kinds that no Skill call loaded;
   - REVIEW: no `reviews.jsonl` row with is_done for these exact bytes (kinds whose `review` is false are exempt).
   Blocks with the list. Escape, with a reason: `NO APLICA: design-taste|design-skills|design-review: <reason>`.
   Same contract as the family done-gate: blocks at most once per (session, problem set), never when
   `stop_hook_active`, every judgement is a ledger row (`donegate.jsonl`), fail-open with the error ledgered,
   kill switch `CPP_DESIGN_DONEGATE=off`.
6. `vault/agents/cdio-reviewer.md` + its live copy: the review ends with `render` then `record`; the chat report alone
   no longer counts.

## Rules fixed after review of a9db1d43 (pp-code-reviewer: WARNING, 1 HIGH)
- F1 HIGH: ordinary words ("exactly as before", "promo code", "helm chart") classified as calco / motion / dataviz,
  and because kinds were a session UNION and any kind replaced the default, Taste and the review switched off for the
  rest of the session. Now: regexes need a visual object (calco), a film word (motion), a data word (dataviz); the
  LATEST visual prompt's kinds replace the session's; a non-gating kind never replaces web for an HTML page.
- F2 MEDIUM: an HTML page is always judged; app source (tsx/jsx/vue/css) only when the latest visual prompt named a
  gating surface (web/app_ui/mobile), so a logic fix in a component is not a design task. The once-per-set key names
  the problem (check, file, criterion), not the bytes, so re-editing a file does not re-block it.
- F3 LOW: `--screenshot` must be a PNG with an IHDR of at least 300x300.

## Re-block on a recorded non-APPROVE review (Owner 2026-11-17 'y', after the SaaS run)
Measured: the SaaS treated arm recorded BLOCK 11, Stop blocked once, the 15 s resume ended without re-reviewing, and
the once-per-set rule then let the page through with a recorded BLOCK on it. Rule now:
- `judge` marks a design-review problem `recorded` when the LATEST reviews.jsonl row naming that file (any bytes) is
  not done; its detail names that verdict, score and refusals, so the agent reads why it was refused.
- A problem set containing a `recorded` review may block up to 3 times in total (the first block + 2 re-blocks,
  `MAX_RECORDED_BLOCKS`), and these re-blocks ignore `stop_hook_active`: in a live session the Stop after a block
  always carries it, so honouring it would make the re-block unreachable. The count is the loop bound.
- Any other set keeps the old contract: once, never when `stop_hook_active`.
- Escape unchanged: `NO APLICA: design-review: <reason>`.
Acceptance: V-DSR-STOP-REBLOCKS-RECORDED-BLOCK (3 blocks, the 4th silent, with stop_hook_active true on 2-4) and
V-DSR-STOP-NO-REBLOCK-WITHOUT-RECORD (an unreviewed page still blocks once).

## Acceptance (V-DSR-*, `tools/test_design_route.py`, hermetic state dir, both poles)
- ROUTES-RESOLVE: every required skill in the table resolves to an installed SKILL.md or command (a table naming a
  skill nobody can load is a documented capability nobody can execute).
- CLASSIFY: landing / dashboard / mobile / calco / promo prompts get their kinds; a backend prompt gets none; calco
  overrides web.
- PROMPT-INJECT / PROMPT-SILENT: the prompt hook emits the block for a visual prompt and nothing for a non-visual one.
- STOP-SILENT-NO-VISUAL: a session that wrote no visual file is never judged.
- STOP-BLOCKS-SLOP: an HTML file with an em-dash and a scroll listener blocks on TASTE.
- STOP-BLOCKS-NO-SKILL / STOP-BLOCKS-NO-REVIEW: a clean file with no skill load / no review record blocks.
- STOP-PASSES-COMPLETE: skills loaded + recorded APPROVE for the current bytes -> silent.
- STOP-STALE-REVIEW: editing the file after the review makes the record not count.
- STOP-NA / STOP-ONCE / STOP-HOOK-ACTIVE / STOP-OUTSIDE-CWD / STOP-KILL.
- RECORD-REFUSES-THIN / RECORD-REFUSES-UNRENDERED / RECORD-FOLDS-TASTE (a Taste critical makes APPROVE impossible).
- RENDER-REAL: `render` produces a PNG of a real HTML file (skipped with a named reason only when Chromium is absent;
  a skip is reported, never counted as a pass).
- WIRED: the repo dispatcher lists both members.

## Evidence (laptop, 2026-11-17)
- Review: pp-code-reviewer on a9db1d43 = WARNING (1 HIGH, 1 MEDIUM, 1 LOW), all fixed in 5f97f1fb; V-DSR 39/39.
- Live: merged as 7f7529ba; `~/.claude/hooks/hook-dispatcher.js` carries both members (backup
  `~/.claude/backups/design-router-live-20261117/`); `~/.claude/agents/cdio-reviewer.md` installed from vault/agents.
- Live drill through the real dispatcher (`node hook-dispatcher.js --event=...`, private design state dir):
  UserPromptSubmit-chain with "hazme una landing page para un estudio de yoga" injected the route block (session kinds
  `['web']`); Stop-chain for a session that wrote an index.html with an em-dash and a scroll listener BLOCKED with
  TASTE-EMDASH + TASTE-SCROLL-LISTENER, the three missing skills and the missing review; one ledger row, no errors.
  Whole-chain wall times were 4.95 s (UPS) and 20.9 s (Stop, all 11 members); this member alone measured 254-402 ms
  on an 8.9 MB real transcript.

## Honest limits
- The reviewer's verdicts are still an LLM's judgement; the recorder stops an EMPTY or UNRENDERED approval, not a
  dishonest one. The deterministic floor is the Taste lint folded into the score.
- A rendered PNG proves the bytes were rendered, not that anyone looked at it.
- Non-HTML surfaces (tsx/vue/css inside an app) need the app running; the recorder takes a screenshot path for them and
  cannot render them itself.
- Skills are proven LOADED, not followed.
- Measured once, N=3 (below): the bundle helped on every task, but the effect is the WHOLE bundle (block + skills +
  reviewer + one Stop round + more tools), not separable per piece, and the judge is one model family.

## Measurement (GEX44, 2026-11-17; tools/asc_design_gate_run.py, data vault/programs/ascension/design-gate, c39ec274)
| task | Taste fails control -> treated | blind judge (both orders) | slop markers per vote, control/treated | treated review |
|---|---|---|---|---|
| clinic dashboard | 1 crit + 2 major -> 0 | treated, treated | 1/0, 3/1 | APPROVE 90 (2nd record) |
| SaaS landing | 0 crit + 2 major -> 0 | treated, treated | 6/2, 5/2 | BLOCK 11; Stop blocked once, the 15 s resume did not re-review |
| yoga landing (es) | 1 crit + 1 major -> 0 | treated, treated | 5/2, 3/4 | BLOCK 59 -> 19 -> APPROVE 100 (iterated) |
- Treated arms loaded the 3 required skills in 3/3 and dispatched cdio-reviewer in 3/3; control never could.
- Judge reasons name the anti-slop axis directly: control SaaS = "stock SaaS template: eyebrow, gradient hero, three
  icon cards, Most popular badge"; treated = specific sample data, mechanism shown, heatmap instead of bars.
- Cost: treated 316-527 s vs control 69-110 s per task (5-8x wall). Output tokens counted only for the main agent.
- Found by the run and fixed (558ec18f): 3/3 first records were refused for the css/js the rendered page itself links.
- Open: SaaS shows the one-round Stop is not enough when the review BLOCKs (the resume ended without re-reviewing);
  an APPROVE 100 means every recorded verdict passed, which is the reviewer's claim, not an independent check.
- SaaS rerun with the re-block (GEX44, e403cdcb, data f75143b1, vault/programs/ascension/design-gate-reblock): Taste
  control 1 crit + 2 major -> treated 0 crit 0 major; blind judge treated in both orders again. Stop blocked 3 times
  then went silent, as specified; the three resumes used NO tool (13.5 s, 6.1 s, 5.1 s). Cause, from the agent's own
  answers: the recorded review was BLOCK 0, driven by three CDIO-10 `legal-page-present` criticals (no privacy, terms,
  DPA page). The agent declined to write legal text for an invented company and declined `NO APLICA` because the
  review does apply, and asked the Owner. That refusal is right; the re-block cannot help a review whose criticals are
  outside the brief. It also left two fixable majors open (5 text sizes vs 3; CTAs to routes that do not exist).
  So the previous SaaS BLOCK 11 was most likely the same legal floor, not a lazy resume.
  Fixed (Owner 2026-11-18 'y'): the recorder stores `failed` [[criterion, severity, observed]] and the re-block detail
  lists them, criticals first, at most 8 (V-DSR-STOP-NAMES-FAILED-CRITERIA).
  Not changed: CDIO-10 legal pages stay critical in the design review. Checked first, as agreed: spec CDIO-10 records
  the Owner's own scope answer "blocks done" (2026-10-08), and `legal_surface` has no publish-time caller (only
  cdio-reviewer, backlog_autopilot/webslice, asc_baseline_evidence), so demoting it here would remove the only guard.
  Done (Owner 2026-11-18 'y', spec cdio-10-publish-gate.md): CDIO-10 now gates production web publishes
  (`hooks/legal_deploy_gate.js`, V-LDG 11/11, live drill denied `npx vercel --prod` and `netlify deploy --prod`,
  passed `git status`), and only then did the recorder start recording the legal criticals of a single page as major.

## Rollback
`CPP_DESIGN_DONEGATE=off` / `CPP_DESIGN_ROUTE=off`, or delete the two dispatcher lines. State lives only under
`~/.claude/state/design_route/`.
