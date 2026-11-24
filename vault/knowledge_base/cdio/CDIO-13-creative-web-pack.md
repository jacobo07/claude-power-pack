---
id: CDIO-13
name: Creative Web Pack — the Motion and Reference Axis
type: dataset
domain: cdio
status: sealed
governs: [cdio-core, cdio-reviewer]
governed_by: CDIO-00
source: PDF "The WEB Pack" (Sanjai Builds, free resource, 2026, 11 pages, links checked by its author October 2026), file Sanjai_Builds_WEB_Pack.pdf, absorbed 2026-11-24
evidence: text of all 11 pages extracted (PyMuPDF); the 53 embedded images not viewed; the 10 repos checked on the GitHub API 2026-11-24 (existence, licence, last push); 7 skill repos vendored text-only at pinned commits (see sec. 9)
---

# CDIO-13 — Creative Web Pack (the Motion and Reference Axis)

CDIO-12 answers "in what order is a website built". It says nothing about the class of site the
Owner points at when he says "make it look impossible": a scroll story, an editorial luxury
page, a kinetic portfolio with a 3D layer. Those sites are built from a small, repeatable set of
choices — which reference, which motion skills, which runtime, in which order, checked how.
CDIO-13 is that set. It is absorbed from one source, "The WEB Pack" by Sanjai Builds, and it
ships the skills that source recommends inside the pack, so an installer of Claude Power Pack
has them without fetching anything.

The pack is free and its last page says "share it". It recommends; it does not claim the three
sites were built with these skills ("The skill suggestions are learning recommendations, not
claims that the original creators used them"). This dataset keeps that distinction.

CDIO-13 adds recipes, criteria and vendored generators; it never relaxes a CDIO-00 floor. The
vendored skills are **generators**; CDIO stays the judge. Where a vendored skill and a CDIO floor
disagree, the floor wins and the disagreement is recorded (sec. 10).

## 1. Scope

CDIO-13 applies when a website build (CDIO-12) asks for **expressive motion**: scroll-driven
storytelling, editorial reveals, kinetic type, page transitions, WebGL/Three.js. It plugs into
CDIO-12 at two steps: Step 3 (which skills to load — sec. 5 and 9 here) and Step 4 (the reference
— sec. 2 here).

It does not decide how much motion a surface may carry. That is the CDIO-07 experience contract,
declared before building; a recipe below can only be used up to the ceiling the contract allows.
A site whose contract says `expressiveness: none` uses none of the recipes, and that is a passing
contract. Measured motion components already in the pack are CDIO-11 (componentry).

## 2. Three reference websites

The pack's page 2 rule: "Pick one reference website ... Study one idea, not everything." Each
reference is a source of **principles** (pacing, interaction, hierarchy), never of composition
(CDIO-12 criterion `reference-is-direction-not-copy` applies unchanged).

### Website 01 — Sweet Tape (sweet-tape.com)

Stack (public tech detection): Next.js, Three.js. Why it feels impossible: a simple product
becomes a whole visual world; huge type and bold colour blocks, one per scene; scroll drives every
reveal, so it reads as a story. Build it with: Scroll Craft (the scroll story and art direction),
WebGL Animation Skills (when the hero needs real 3D), Anthropic Frontend Design (lock the visual
direction first).

### Website 02 — ERA Residence (era-residence.com)

Stack (the creator's Webflow listing): Webflow. Why it feels impossible: restrained, editorial
typography with lots of space; arch masks and slow image reveals feel like luxury; every section
is paced, nothing moves at random. Build it with: GSAP Skills (timelines, ScrollTrigger and
SplitText), Anthropic Frontend Design (editorial layout and type), MengTo Skills (extra polish).

### Website 03 — Nick Ho (nickho-motorsports.nl)

Stack (the BORING studio case study): Webflow, Three.js. Why it feels impossible: racing energy —
big counters and kinetic text; black and white with one sharp yellow accent; signature
transitions between every section. Build it with: GSAP Skills (pacing and text motion), Web
Animation Skills (page transitions and micro-interactions), WebGL Animation Skills (shaders,
particles and the 3D layer).

## 3. The ten repos

Licences and state read from the GitHub API on 2026-11-24. "Vendored" means a text copy ships in
`web-pack/vendor/` (sec. 9); a library is an npm dependency of the site being built and is never
copied into the pack.

| # | Repo | Kind | What it is for (the pack's words, condensed) | Licence | In this pack |
|---|---|---|---|---|---|
| 01 | `greensock/gsap-skills` | official skill | core APIs, timelines, scroll patterns, plugins, framework setup, performance; "the best first pick when GSAP drives your motion" | MIT | vendored, 8 skills |
| 02 | `nateherkai/scroll-craft` | skill | immersive scroll sites: art direction, layered composition, responsive behaviour, visual checks; plan a scroll story with an opening, middle and exit | MIT | vendored, 1 skill |
| 03 | `MengTo/Skills` | skill pack | a broad collection for designers and builders, incl. visual design and polished creative web | MIT | vendored, 221 skills |
| 04 | `iart-ai/web-animation-skills` | skill pack | GSAP, SVG, Lottie, micro-interactions, page transitions, animation performance | MIT | vendored, 9 skills |
| 05 | `iart-ai/webgl-animation-skills` | skill pack | Three.js animation, GLSL shaders, particles, scroll-linked 3D, React Three Fiber | MIT | vendored, 3 skills |
| 06 | `JustineBijuPaul/frontend-ai-skills` | skill pack | architecture, React, Next.js, accessibility, performance, animation, 3D; "keeps the engineering solid" | MIT | vendored, 70 skills |
| 07 | `anthropics/skills` | official skills | Frontend Design: commit to a clear aesthetic before adding motion | Apache-2.0 per skill (no root licence) | vendored: frontend-design + docx, pdf, pptx, xlsx |
| 08 | `darkroomengineering/lenis` | library | lightweight smooth scrolling, wired carefully into scroll animation | MIT | npm dependency, not vendored |
| 09 | `pmndrs/drei` | library | React Three Fiber helpers: cameras, controls, loaders, text, environments, effects | MIT | npm dependency, not vendored |
| 10 | `pmndrs/react-three-fiber` | library | React renderer for Three.js, when the app already uses React | MIT | npm dependency, not vendored |

## 4. The build flow

The pack's order, page 8: "Get the design direction right first, then add motion, then 3D." Each
step names its repo. The heading number is the gate's FIDELITY anchor.

### Flow 01 — Design direction

Anthropic Frontend Design and MengTo. In this pack the direction is then named as a CDIO-06
family and declared in DESIGN.md before motion exists.

### Flow 02 — GSAP animation

GSAP Skills and Web Animation Skills.

### Flow 03 — Cinematic scrolling

Scroll Craft.

### Flow 04 — Three.js and WebGL

WebGL Animation Skills.

### Flow 05 — Smooth scroll

Lenis. Under this pack it is the last motion layer added and the first removed under reduced
motion (criterion `smooth-scroll-yields`).

### Flow 06 — React 3D tooling

React Three Fiber and Drei.

Throughout: Frontend AI Skills "keeps the engineering solid".

## 5. Three recipes

Each recipe names its skills, its runtime and its first milestone. The paths are the vendored
copies (sec. 9), relative to `vault/knowledge_base/cdio/web-pack/vendor/`.

### Recipe 01 — Sweet Tape style (scroll story)

- **Skills:** Anthropic Frontend Design + Scroll Craft + WebGL Animation Skills
  (`anthropics__skills/skills/frontend-design/SKILL.md`,
  `nateherkai__scroll-craft/plugins/nateherk-design/skills/scroll-craft/SKILL.md`,
  `iart-ai__webgl-animation-skills/skills/threejs-animation/SKILL.md`).
- **Runtime:** GSAP, plus Three.js if the hero needs real 3D. In React, React Three Fiber and Drei.
  Add Lenis for smooth scroll.
- **Milestone 1:** one distinctive hero with a single product interaction, then tell the story
  across the rest of the page.

### Recipe 02 — ERA style (editorial luxury)

- **Skills:** Anthropic Frontend Design + GSAP Skills; MengTo Skills for polish
  (`greensock__gsap-skills/skills/gsap-scrolltrigger/SKILL.md`,
  `greensock__gsap-skills/skills/gsap-timeline/SKILL.md`,
  `MengTo__Skills/agent-skills/web-design/masked-reveal/SKILL.md`,
  `MengTo__Skills/agent-skills/web-design/editorial-portfolio-chapters/SKILL.md`).
- **Runtime:** Webflow with custom GSAP, or a custom frontend with GSAP.
- **Milestone 1:** nail the typography, image proportions and spacing, then add one restrained
  scroll sequence.

### Recipe 03 — Nick Ho style (kinetic portfolio)

- **Skills:** GSAP Skills + Web Animation Skills; WebGL Animation Skills for one specific 3D effect
  (`iart-ai__web-animation-skills/skills/page-transition-animation/SKILL.md`,
  `MengTo__Skills/agent-skills/web-design/number-details/SKILL.md`,
  `iart-ai__webgl-animation-skills/skills/shader-glsl/SKILL.md`).
- **Runtime:** Webflow and GSAP with Three.js where needed, or a similar custom frontend.
- **Milestone 1:** a strong hero, controlled text motion and one signature transition.

## 6. Every recipe, same checks

The pack's page 9 closes with four checks for every recipe. Each became a sec. 8 criterion.

### Check 1 — Layout and navigation work before motion

Criterion `layout-before-motion`.

### Check 2 — Mobile and reduced motion tested

Criteria `smooth-scroll-yields` and `mobile-motion-checked`; the reduced-motion floor itself is
HR-EXPERIENCE-FLOOR-001 and CDIO-12 `motion-has-still-equivalent`.

### Check 3 — One signature interaction, not ten

Criterion `one-signature-interaction`.

### Check 4 — Smooth loading and stable layout

Criteria `stable-layout-while-loading` and `webgl-has-fallback`.

### The four checks are not the review

The first recipe build (`web-pack/examples/recipe-02-sotomenor/REVIEW.md`, 2026-11-24) passed all
four checks and was still **BLOCKED at 75** by the CDIO-05 review: its header links were 25.6px
tall against the 44px tap-target floor, which none of the four covers. Every recipe build
therefore also runs the full CDIO-05 review on the rendered page, and its browser QA measures tap
targets explicitly (the example's `qa/qa_site.py` does, with a red drill).

## 7. The build prompt

Verbatim from page 10 ("Works in Claude Code, Codex, Cursor or any coding agent. Replace the
green brackets with your details."):

> Build an original website for [brand and audience]. The main goal is [goal]. Required
> sections are [sections], and my assets are [assets].
>
> Use [reference URL] as inspiration for pacing and interaction principles. Create an
> original composition with my content and brand.
>
> Read these skills: [repo links or installed skill names]. Start with frontend design and
> GSAP guidance. Add scroll storytelling or WebGL guidance only where it serves the concept.
>
> First, inspect the project and propose a short visual direction: typography, palette,
> spacing, image treatment and one signature interaction. Use [preferred stack].
>
> Build the responsive layout and working controls before adding motion. Use purposeful
> timelines and clean up animations. For 3D, optimize models and textures and add a fallback.
>
> Support keyboard navigation, readable contrast and reduced motion. Check desktop and mobile
> in a browser, then report what you built, what you checked and any limits.

In this pack, `[repo links or installed skill names]` is filled with the vendored paths of the
chosen recipe (sec. 5), and two sentences are appended. Each closes a gap the prompt leaves:

> Respect the experience contract in DESIGN.md: no motion beyond its declared ceiling. Use only
> facts from the fact sheet for numbers, reviews and contact details; ask where one is missing.

The prompt composes with CDIO-12 sec. 3: when both apply, CDIO-12's intake runs first and this
prompt is the build brief that follows the intake answers.

## 8. The criteria (what CDIO-13 can fail)

Each criterion names the dimension it reports under, so the deterministic scorer in CDIO-05 sec. 4
weighs it with no change to the formula. Severity follows CDIO-05 sec. 3.

**`layout-before-motion`** (dimension `ux`, severity major). With scripts that drive motion
disabled, every section renders in reading order and every navigation control works. Observed-
value form: "with GSAP blocked, sections 3-6 stay at opacity 0; the menu button has no handler".

**`smooth-scroll-yields`** (dimension `ux`, severity critical). A smooth-scroll layer (Lenis or
equivalent) is not started under `prefers-reduced-motion: reduce`, and native keyboard scrolling
(Space, Page Down, Home/End, anchor links, focus moving into view) works with it on. Observed-
value form: "reduced motion on: Lenis still interpolates wheel input; Tab to the footer link does
not scroll it into view". Under the floor rule this is critical.

**`mobile-motion-checked`** (dimension `ux`, severity major). Every scroll sequence was observed at
390x844 in a browser, and pinned sections neither trap the scroll nor hide content behind the
mobile address bar. Observed-value form: "at 390x844 the pinned gallery needs 14 swipes to exit;
its last card is never fully visible".

**`one-signature-interaction`** (dimension `visual`, severity major). The page has one declared
signature interaction; other motion is supporting (reveals, feedback) and quieter. Observed-value
form: "four competing hero-scale effects: cursor trail, WebGL blob, kinetic marquee, page wipe".

**`stable-layout-while-loading`** (dimension `ux`, severity major). Reveals, split text and late
fonts or models cause no visible layout shift; CLS at most 0.1 on a throttled mobile profile.
Observed-value form: "CLS 0.31: SplitText re-wraps the hero headline after the font swap".

**`webgl-has-fallback`** (dimension `ux`, severity major). When WebGL is unavailable or the context
is lost, the content and the call to action are still present (a still image or a CSS
equivalent), and no error reaches the visitor. Observed-value form: "WebGL disabled: hero renders
an empty 100vh canvas; headline was drawn inside the scene".

**`3d-assets-budgeted`** (dimension `ux`, severity minor). Models and textures are compressed and
sized for the viewport (Draco/Meshopt or equivalent, textures no larger than they are displayed),
and the 3D layer loads after the first meaningful paint. Observed-value form: "hero.glb 38 MB
uncompressed, 4096px textures on a 600px object; LCP 7.4 s".

**`animations-cleaned-up`** (dimension `ux`, severity minor). Timelines, ScrollTriggers and
render loops are reverted on unmount or route change (for GSAP, `gsap.context().revert()` or
`useGSAP`), so navigation does not stack listeners. Observed-value form: "after 5 route changes
there are 5 ScrollTrigger instances on the same pin".

**`split-text-stays-readable`** (dimension `ux`, severity major). Text split for animation keeps
its accessible text: screen readers read whole words and sentences, not letters, and the
original string is the accessible name. Observed-value form: "headline split into 42 spans
without aria-label; VoiceOver reads it letter by letter".

## 9. The vendored skills

**Where:** `vault/knowledge_base/cdio/web-pack/vendor/<owner>__<repo>/`, one folder per repo, the
upstream paths kept. **What:** text only — Markdown, YAML, JSON, code, schemas; images, GIFs,
video, fonts and minified library copies are left out (`manifest.json` lists every skipped
path), **except MengTo/Skills, which ships complete** — its demo media, fonts and large demo
pages included (Owner, 2026-11-24, D44.2: "Include it"; 653 more files, 185 MB). **Pinned:** every
repo at one commit; every file by its upstream sha256 in `web-pack/manifest.json`.
**Licences:** each repo's own LICENSE ships inside its folder; attribution in `web-pack/NOTICE.md`.

| Repo | Commit | Licence | Skills | Files kept |
|---|---|---|---|---|
| greensock/gsap-skills | `aed9cfd3` | MIT | 8 | 37 |
| nateherkai/scroll-craft | `75d81f74` | MIT | 1 | 30 |
| MengTo/Skills (complete) | `e7df6eb7` | MIT | 221 | 1921 |
| iart-ai/web-animation-skills | `ed3a0451` | MIT | 9 | 41 |
| iart-ai/webgl-animation-skills | `00419338` | MIT | 3 | 19 |
| JustineBijuPaul/frontend-ai-skills | `f52d23c5` | MIT | 70 | 80 |
| anthropics/skills (18 skills) | `e4bb5d96` | Apache-2.0 | 18 | 385 |

**330 skills in total.** MengTo ships whole, by category: web-design 102, 3d 32,
game-development 25, codex 20, illustration 14, media 7, ui 7, game-combat 6, workflow 5,
video-editing 3. From `anthropics/skills`: frontend-design (the one the pack names), the four
office skills docx, pdf, pptx, xlsx, and (D44.1) academy-guide, algorithmic-art,
brand-guidelines, canvas-design, claude-api, discernment-nudge, internal-comms, mcp-builder,
skill-creator, slack-gif-creator, theme-factory, web-artifacts-builder and webapp-testing.
`doc-coauthoring` is **not** vendored: its folder carries no LICENSE and the repo has none at
its root, so redistribution could not be confirmed. canvas-design's 54 fonts, theme-factory's
showcase PDF and web-artifacts-builder's `shadcn-components.tar.gz` are left out under the
text-only rule; that last skill's script needs the tarball and so does not run from this copy.

**How they are used — read on demand, never installed as live skills.** They are not placed in
`~/.claude/skills/`, so none of their 330 descriptions enters the prompt on every call (the
pack's latent-card + JIT rule). `cdio-core` opens the SKILL.md a recipe names, or the one a
request names ("use MengTo's masked-reveal"), with Read, and follows it as guidance for that
build. `web-pack/README.md` is the index by need. An installer who wants one as a live skill
copies its folder into `~/.claude/skills/`; that is a choice per skill, not a default.

**Eleven live skills (Owner, 2026-11-24: "incluye que se instale también anydesign, impeccable y
ui-ux-pro-max", then D44.4 "Add gsap-skills (8)").** These are the exception to read-on-demand:
they are installed, at the cost of their descriptions in every prompt. Each ships as a complete
upstream folder (scripts and data included, nothing omitted) under `web-pack/live/<name>/`,
pinned by `web-pack/live/live-manifest.json`:

| Skill | Upstream | Commit | Licence | Files |
|---|---|---|---|---|
| impeccable | pbakaus/impeccable, `.claude/skills/impeccable` | `b49177d3` | Apache-2.0 | 64 |
| ui-ux-pro-max | nextlevelbuilder/ui-ux-pro-max-skill, `.claude/skills/ui-ux-pro-max` | `f2f7266b` | MIT | 82 |
| anydesign | uxKero/anydesign (repo root) | `d81bd895` | MIT | 48 |
| gsap-core, gsap-frameworks, gsap-performance, gsap-plugins, gsap-react, gsap-scrolltrigger, gsap-timeline, gsap-utils | greensock/gsap-skills, `skills/<name>` | `aed9cfd3` | MIT | 2 each (SKILL.md + repo LICENSE) |

`install.ps1` and `install.sh` (step 11) run `tools/install_cdio_live_skills.py`, which per skill
checks every file's sha256 and refuses any unlisted file first, then installs into
`~/.claude/skills/<name>` through a `.partial` folder renamed at the end. It never overwrites: a
skill already present is skipped, and so is one that an **installed and enabled** plugin already
provides (`plugins/installed_plugins.json` + `settings.json` `enabledPlugins`; a marketplace
clone or a disabled plugin does not count), so a host that has ui-ux-pro-max as a plugin does
not get it twice. Their scripts were read before
vendoring: anydesign fetches only the URL it is asked to analyse, impeccable's live mode talks
only to its own localhost server, ui-ux-pro-max starts subprocesses only in its own tests. In
the CDIO-12 sequence they are Step 3 generators (ui-ux-pro-max already is), anydesign extracts a
reference's design into tokens at Step 4, and impeccable's audit is an input to the review, never
its verdict: the score stays `modules.cdio.scorer`'s.

**Scope of the non-web skills.** Games, illustration, video, pure 3D and the office skills ship
because the Owner asked for them; they are not part of any recipe here and are routed only when a
request names their subject. Some MengTo `codex/` skills cause outward effects
(`publish-project-to-github`, `x-bookmark-quote-posts`, `elevenlabs-tts`); vendoring them grants
no authority — publishing, posting or spending still needs the Owner's yes each time
(`human-facing-external-effects`). `codex/write-like-meng-on-x` writes in its author's personal
voice and is never used to write as the Owner (his voice is `voz-jacobo`).

## 10. Floor collisions (what the pack could not mean literally)

### 10.1 Smooth scroll under reduced motion

The pack says to add Lenis "when smoother scrolling helps the experience". Kept: Lenis as the last
motion layer. Replaced: smooth scroll that runs under `prefers-reduced-motion` or breaks keyboard
scrolling, which is a floor breach. Criterion `smooth-scroll-yields`.

### 10.2 The reference sites are other studios' work

Sweet Tape, ERA Residence and Nick Ho are named because they look impossible. Kept: study one idea
from one of them. Replaced: any reuse of their layouts, assets, copy or code. The pack itself says
"Create an original composition with my content and brand". CDIO-12 criterion
`reference-is-direction-not-copy` applies; an exact copy routes to `image-calco` only for the
Owner's own designs.

### 10.3 "Looks impossible" against the mobile and loading floor

A WebGL hero is what makes two of the three references feel impossible, and it is also what most
often ships a blank screen on a phone. Kept: 3D where the concept needs it ("for one specific 3D
effect"). Replaced: 3D without a fallback or a weight budget. Criteria `webgl-has-fallback`,
`3d-assets-budgeted`.

### 10.4 Vendored guidance against CDIO floors

The 330 vendored skills were written by others for their own aims; some show scroll-scrubbed
motion, autoplaying loops or contrast pairs CDIO would fail. Kept: their techniques. Replaced:
nothing silently. When a vendored instruction and a CDIO floor disagree, the floor wins and the
review records the disagreement as an observed value.

## 11. Evidence, scope and what is still planned

| What | Status |
|---|---|
| PDF text | all 11 pages extracted with PyMuPDF and read in full |
| PDF images | not viewed: page rendering was unavailable on this host (pdftoppm absent); the 53 embedded images (site screenshots, logos) were not examined |
| Reference sites | not visited; their stacks are the pack's own claims from public listings |
| Repos | all 10 exist, none archived, licences as in sec. 3, read 2026-11-24 from the GitHub API |
| Vendoring | text only for six repos (anthropics/skills skips 54 fonts, a PDF and a tarball); MengTo/Skills complete, its 653 media files (185 MB, largest 12 MB) added by Owner decision D44.2 |
| Untrusted-text scan | 10 hits on the first 7 repos and 2 on the D44.1 skills, all reviewed benign (UTF-8 BOMs in OOXML schemas, a zero-width space in an empty `<title>`, a "never run `curl \| sh`" instruction, an example tool command); no CRITICAL secret pattern |
| Skill heat-map indexer | `tools/skill_heat_map_indexer.py` walks `~/.claude/skills/**/SKILL.md`; a vendored SKILL.md resolves to the id `claude-power-pack`, as the pack's own `skills/` folder already does, so it adds no phantom skill |
| First recipe run end to end | **DONE 2026-11-24** on an invented brand (`web-pack/examples/recipe-02-sotomenor/`): review 1 BLOCK 75 (one critical, tap target 25.6px), fixed, review 2 APPROVE 100; every assessable sec. 8 criterion passed with measured values; not published, so publish and legal criteria were not assessed |
| A recipe run on an Owner site | **PLANNED**: the first real client build records its result here |
| `anthropics/skills` doc-coauthoring | not vendored: no licence in its folder or at the repo root (backlog D44) |
| `tools/design_gate.py` vacuous pass | observed in the first run: APPROVE 92 with 0 colours and 0 fonts read when tokens were in a table instead of front matter; recorded in the backlog (D44), not fixed here |

The sec. 8 criteria derive from the pack's four checks and its prompt; the assessable ones have
been scored once, on the demo (sec. 6 records what that run showed the checks miss).

## 12. Common false positives (what CDIO-13 does not flag)

- A site with no motion at all, under a contract that declares none.
- A motion site that uses no vendored skill: the recipes improve a build; their absence is not a
  defect in the result.
- Smooth scroll that is on for visitors without a reduced-motion preference and keeps keyboard
  scrolling.
- A second animated element that is plainly supporting (a hover state, a fade-in), next to one
  signature interaction.
- A 3D scene that is decorative and has a still fallback.

## 13. Contract with the review pipeline

`cdio-core` routes a website build that asks for expressive motion to CDIO-13 after CDIO-12's
intake: the recipe from sec. 5, the vendored skills from sec. 9, the ceiling from CDIO-07.
`cdio-reviewer` applies the sec. 8 criteria inside the normal CDIO-05 lenses at CDIO-12 Step 8
and again before Step 9; the score is still computed by `modules.cdio.scorer`, and the critical
(`smooth-scroll-yields`) blocks APPROVE as any critical does. The gate for this dataset, and for
the integrity of every vendored file, is `python tools/test_cdio_web_pack.py`.
