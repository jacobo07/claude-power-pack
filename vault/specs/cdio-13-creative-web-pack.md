---
id: SPEC-CDIO-13
title: CDIO-13 Creative Web Pack (absorption of "The WEB Pack" by Sanjai Builds, with its skill repos vendored)
tier: T2
status: approved
covers: [cdio-13, creative-web-pack, web-pack, sanjai-builds, test_cdio_web_pack]
owner_go: "mete todo esto dentro de CDIO para que cuando alguien instale claude power pack les venga dentro: Sanjai_Builds_WEB_Pack.pdf" (2026-11-24); scope answers in the same session - "option 1 with all skill repos in the backlog", then "actually download the skills you want and the ones you feel are the most useful for claude power pack", then "no, include games, illustration, video, pure 3D and anthropic's office skills"
---

# SPEC — CDIO-13 Creative Web Pack

## Objective

CDIO-12 gives the order of a website build but no account of how an expressive motion site
(scroll story, editorial reveals, kinetic type, WebGL) is chosen and checked. "The WEB Pack"
(Sanjai Builds, 2026, 11 pages) gives one: three reference sites, ten repos, a six-step build
flow, three recipes, four checks and a build prompt. This spec absorbs it as dataset CDIO-13 and
ships the skill repos it recommends inside the pack, so an installer of Claude Power Pack has them.

## Scope

1. `vault/knowledge_base/cdio/CDIO-13-creative-web-pack.md` — sealed dataset: references (sec. 2),
   repos (3), flow (4), recipes (5), checks (6), prompt verbatim (7), criteria in the CDIO-08
   grammar (8), vendored skills (9), floor collisions (10), evidence (11).
2. `vault/knowledge_base/cdio/web-pack/` — `vendor/` (7 repos, text only, pinned commits, 317
   skills), `manifest.json` (upstream sha256 per file, skipped paths), `README.md` (generated
   index), `NOTICE.md` (attribution and licences). `.gitattributes` marks `vendor/**` `-text` so
   a CRLF checkout does not break the hashes.
3. Wiring: CDIO-00 `governs`, the three CDIO agents (repo + live mirrors), `tools/test_cdio.py`
   dataset count 13 -> 14.
4. `tools/test_cdio_web_pack.py` — V-CDIO-WEBPACK-* done-gate.
5. Live skills (Owner, same session: "incluye que se instale también anydesign, impeccable y
   ui-ux-pro-max"): complete folders in `web-pack/live/` + `live-manifest.json`, installed by
   `tools/install_cdio_live_skills.py` from step 11 of `install.ps1` and `install.sh`; never
   overwrites, skips a plugin-provided skill, refuses a tampered copy (V-CDIO-WEBPACK-LIVE).

## Out of scope

- No new Python module, no scorer change: criteria report under the existing dimensions.
- The vendored skills are not installed into `~/.claude/skills/` (no prompt-prefix cost); they
  are read on demand. Lenis, Drei and React Three Fiber are npm libraries and are not copied.
- Images, video, fonts and minified library copies from the repos are not vendored.
- `anthropics/skills/doc-coauthoring` (no licence found) and a recipe run on a real Owner site:
  backlog D44.

## Phase 2 — D44 (Owner 2026-11-24: "do D44", then "Include it" / "A demo site, recipe 02" /
"Add gsap-skills (8)")

6. 13 more `anthropics/skills` skills vendored (330 total); MengTo/Skills vendored complete with
   its 653 media files (185 MB); gsap-skills' 8 skills added to the live set (11 live).
7. First recipe run: `web-pack/examples/recipe-02-sotomenor/` (site, DESIGN.md, QA script and
   measurements, REVIEW.md with the BLOCK 75 -> APPROVE 100 history); CDIO-13 sec. 6 and 11
   record what it showed. Acceptance unchanged: `python tools/test_cdio_web_pack.py` exit 0, now
   also checking 330 skills, 11 live skills and the recorded first run.

## Acceptance

- `python tools/test_cdio_web_pack.py` exit 0, with red drills (removed recipe, malformed
  criterion, flipped vendored byte, stray vendored file, removed kernel pointer, mirror drift).
- `python tools/test_cdio.py`, `tools/test_cdio_build.py`, `tools/test_cdio_mobile.py` exit 0.

## Rollback

Delete the dataset, `web-pack/`, the gate and this spec; remove the `.gitattributes` line; restore
`EXPECTED_DATASETS = 13`; remove the CDIO-13 lines from the kernel and the three agents (repo +
`~/.claude/agents/`).
