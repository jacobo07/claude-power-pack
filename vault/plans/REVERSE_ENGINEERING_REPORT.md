# Reverse-Engineering Report — Logo Concept Generator + Brand Kit Workflow

> Phase 0 output (blocking). Sources: Recurso A (`Brendan Jowett - Master Logo & Brand Design With
> Claude! (Full Course).mp4`, 12:20, analyzed via 37 frames @ 1/20s + full narration cross-check)
> and Recurso B (`NoteGPT_Transcript_...txt`, read in full, 62 lines). Evidence labels:
> **EXTRACTED** (verbatim, on-screen or spoken) / **INFERRED** (reasoned from what's shown)
> / **GENERALIZED** (pattern lifted beyond this one example) / **NOVEL** (not evidenced,
> proposed for the CCF — justification required).

## Correction to the Phase -1 assumption

Phase -1 assumed the real implementation ("logo concept generator") was undisclosed/paywalled.
**That was wrong** — the video shows the actual private GitHub repo
(`brendanjowett/logo-concept-generator`), its file tree, its README, a live Claude Code session
using it, and a Claude-generated mermaid diagram of its own architecture. Evidence quality is
**far higher** than the transcript alone suggested. Correcting per `feedback_reality_scan_before_corpus_build` / `feedback_founding_finding_is_a_hypothesis` — the founding assumption was
re-measured against an independent instrument (the video) and revised.

## A. Workflow Stages — EXTRACTED

Two phases, both sharing one shape (**EXTRACTED**, verbatim from the on-screen doc
`docs/how-it-works.md`): *"a config/source file → a plain Node build script → HTML → headless
Chrome print-to-PDF. No dependencies, no design tool."*

**Phase 1 — concept generation** (EXTRACTED from mermaid diagram + live demo):
1. `config.json` defines N companies × 6 concepts (e.g. 5×6=30 in one example, 6 concepts/company
   confirmed in the live Claude-AI demo).
2. Per concept: **assemble prompt** = font + colours + bg + spelled-out wordmark text +
   "avoid-the-real-mark" instruction + this concept's icon description, plus global
   theme/accent/headFont/labels fields from config.
3. **One call per concept** to `OpenAI gpt-image-2`, resolution **1536×1024**, `quality: high`.
   Output: `<company>-openai-set/NN-name.png`, explicitly labeled "raw output, no post-editing."
4. `build-html.mjs` (plain Node, zero deps) lays the PNG set into `<company>-logo-concepts-openai.html`
   (A4, 2×3 grid, built-in disclaimer text).
5. Headless Chrome `print-to-pdf` → `<company>-logo-concepts-openai.pdf` (showcase sheet, the
   one shown for Discord/Spotify/Oracle/Tesla in the video's cold open).

**Phase 2 — brand kit** (EXTRACTED from the rendered PDF, INFERRED pipeline mechanics — Phase 2's
own mermaid half was not visible on any sampled frame, only its output):
1. Human picks **one** concept from the Phase-1 showcase.
2. `build-brandkit.mjs` (new script, shown being written live) reads the chosen `.svg`, extracts
   the mark and wordmark as SVG `<symbol>` elements (`#lockup`, `#note`, `#type` in the observed
   example), and emits HTML.
3. Recoloring (on-white / on-green / mono variants seen in the PDF) is driven by CSS custom
   properties (`--mark`, `--type`) on the *same* symbol paths — one source of truth, multiple
   renders, not separately hand-edited assets.
4. Same HTML → headless-Chrome-print-to-PDF finisher as Phase 1. Output observed: 6-page PDF,
   *"verified page by page"* (Claude's own words) — pages seen: cover, lockup-variant grid
   (primary-horizontal / stacked / icon-only × on-white / on-green / mono), typography spec
   (display/heading/body/label type scale with exact weights and tracking), app-icon variations
   (dark/green/light circle), a "now playing" UI application mock, source-render reference.
5. Manual post-processing (**EXTRACTED from transcript + video, outside the repo**): Adobe
   Express's PNG→SVG converter (not a separate "Adobe" tool — a feature inside adobe.com/express;
   correcting the ASR transcript's garbled tool name) turns the chosen PNG into an SVG; **Vectorpea**
   (transcript ASR mis-heard this as "Vector Peep" — confirmed via on-screen Google search: a free
   browser-based vector editor by Photopea's developer, an Illustrator alternative) is used to
   recolor, resize, and export per-channel social-media sizes (profile picture, banner, icon-only).

## B. Architectural Decisions — mixed

- **Zero-dependency, script-not-framework bias** (EXTRACTED, stated by Claude in-session): *"I made
  it a build script rather than hand-pasting the path data, so if you re-trace or tweak the logo
  you just run `node build-brandkit.mjs` and re-print."* Deliberate choice: config/source-of-truth
  → deterministic script → HTML → headless-Chrome-PDF, avoiding any PDF library or design tool
  dependency entirely.
- **Docs pattern reused across a family of "generator" tools** (EXTRACTED): Claude explicitly
  matches `docs/how-it-works.md` to *"the pattern you already use in the Instagram generator"* —
  the creator (`INFLATE AI PTY LTD`, per the observed file path) runs a whole family of near-identical
  Node generator repos (`instagram-post-generator`, `logo-concept-generator`, others visible in the
  VS Code sidebar), each following the same config→script→HTML→PDF shape.
- **One image call per concept, no iteration** (EXTRACTED): explicitly "raw output, no
  post-editing" — the system does not critique-and-regenerate automatically; a bad concept is
  caught by a human or by Claude reviewing the sheet after the fact (see the Airbnb incident below).

## C. Hidden Assumptions — INFERRED

- Assumes an OpenAI API key already provisioned (`.env`, `OPENAI_API_KEY=sk-...`) — the demo
  shows Claude *copying* a key from a sibling generator's `.env` because this one had none, i.e.
  the workflow silently assumes "you already have a working key somewhere in this workspace."
- Assumes the user already has a populated personal/business context tree in the coding agent's
  workspace (the ~20-folder sidebar) — narrator says this is optional but the demo is run inside
  that context, not a clean slate.
- Assumes headless Chrome is already installed on the machine (README: *"whatever Chrome is
  already on your machine"*) — no bundled browser, no Puppeteer/Playwright dependency declared.

## D. Manual Operations & Automation Opportunities

- **Manual, EXTRACTED**: picking one concept out of six; the PNG→SVG conversion step (external,
  browser-based, no repo integration); the Vectorpea recolor/export/social-sizing step (fully
  manual, click-driven).
- **Automatable, INFERRED**: PNG→SVG vectorization is a solved, scriptable problem (potrace-class
  tracing) — the creator's manual browser-tool step is a gap, not a hard constraint. Per-channel
  social-size export (YouTube profile/cover, Instagram, etc.) is a fixed, enumerable size table —
  scriptable.
- **Should NOT automate (NOVEL judgment, not evidenced)**: final concept selection is an aesthetic
  human judgment call — the six-concepts-then-pick pattern exists precisely so a human chooses,
  and collapsing that into an automatic top-1 pick would remove the one human-in-the-loop gate the
  whole pipeline is built around.

## E. Reusable Abstractions — GENERALIZED

The config→script→HTML→headless-Chrome-PDF shape, and the "N variants → single showcase sheet
→ human picks one → deepen the chosen one" two-phase pattern, generalize directly to a UI
Compiler (N layout variants → showcase → pick → full spec) or Presentation Compiler (N deck
concepts → showcase → pick → full deck). What's brand-specific: the SVG `<symbol>` +
CSS-custom-property recolor trick (only works because a logo is a small, flat vector shape);
the `avoid-the-real-mark` prompt field (a trademark-collision concern specific to generating
marks that resemble other companies' logos, not a general creative-generation concern).

## F. Agent Boundaries — INFERRED

Single Claude Code agent runs the whole visible pipeline (no distinct sub-agents observed) —
Claude edits the mermaid doc, writes `build-brandkit.mjs`, invokes `generate.mjs`, reviews the
config, and reports cost/results in one continuous chat. Parallelism seen: the `generate.mjs`
--dry-run flag (README) exists to print prompts without spending an API call, implying concept
generation *could* fan out per-company, but only one company's run was demonstrated live.

## G. Artifact Lifecycle — EXTRACTED

- `config.json` → `generate.mjs` → `<company>-openai-set/NN-name.png` (raw, versionless, one
  shot) → `build-html.mjs` → `<company>-logo-concepts-openai.html` → `to-pdf.mjs` (headless
  Chrome) → `<company>-logo-concepts-openai.pdf`.
- Canonical naming observed: `claude-openai-set/01-spark.png` … `06-monogram.png`,
  `claude-logo-concepts-openai.pdf` (4.7 MB with imagery; ~57 KB "empty shell" when the PNG set
  doesn't exist — a real footgun: `to-pdf.mjs` rebuilds **every** company in `config.json`
  regardless of whether images exist for it).
- No version numbers, no hashes, no manifest observed on any artifact — versioning is
  filesystem-implicit (re-run overwrites), not a tracked lineage.

## H. Quality Gates & Human Approval Points — EXTRACTED

- Objective, code-enforced: `spelled` config field (wordmark text is checked against the render —
  *"All six spelled 'Claude' correctly — the spelled field in the config does its job"*); `avoid`
  config field (bans landing on an explicitly named competitor mark).
- Subjective, human-only: picking 1 of 6 concepts; "verified page by page" review of the brand-kit
  PDF (Claude's own words — a manual check, not a script).
- **Documented gate failure** (EXTRACTED, load-bearing finding): concept 02 ("Thread" — *"a
  continuous rounded line that loops back on itself"*) rendered as a near-identical copy of
  Airbnb's Bélo mark. Claude's own diagnosis: *"the `avoid` field only guards against landing on
  a third party's mark [when named], so nothing guards against loosely-specified icon prompts...
  it's a scan of any future set before you use it — the tool won't catch this for you."* This is
  the single most important quality-gate finding in the whole corpus: **a purely textual
  icon-description prompt has no automatic trademark-similarity check**; only an explicit named
  ban list, checked after the fact by a human or by Claude re-reading its own output.

## I. Weak Points & Technical Debt — EXTRACTED + INFERRED

- No automatic visual-similarity/trademark check on generated marks (above).
- `to-pdf.mjs` silently produces near-empty PDFs for companies with no generated images —
  no warning surfaced to the user in the demo.
- Single-provider hard dependency: the entire generation step is `gpt-image-2` only; no fallback
  provider, no retry-with-different-model path observed or documented.
- Cost/latency observed directly: 7 image calls (6 concepts + 1 Airbnb-collision retry) at
  gpt-image-2 high quality, **~90 seconds each** (~10–11 minutes wall-clock for one company's
  Phase 1 run) — this does not scale casually to "100+ brands" without serious parallelization
  the repo doesn't currently do.
- Manual vectorization step (PNG→SVG via Adobe Express, then Vectorpea) is entirely outside the
  repo — brittle, undocumented, dependent on two free third-party web tools staying available.
- Legal exposure is self-acknowledged in the README (EXTRACTED, verbatim from Claude's report):
  demo lockups *"carry Anthropic's registered name, so they're fine as a demo with the built-in
  on-page disclaimer, but not anything presented as official or affiliated — and not for the
  shop"* — i.e. the tool's own author flags it as demo-only, not production-brand-safe, by design.

## J. Provider Lock-in — EXTRACTED

- Image generation: OpenAI `gpt-image-2` exclusively (config-driven parameters — resolution,
  quality — but no provider abstraction; switching providers means rewriting `generate.mjs`).
  Narrator explicitly rejected Claude-native SVG/image generation as the image engine (*"the
  creativity that Claude has is not really a match... I would say that GPT Image 2... the results
  are just that much better"*) — a **deliberate, evidenced provider choice**, not an oversight.
- Orchestration: Claude Code (VS Code extension) — swappable in principle, not abstracted in
  practice; all prompts, file writes, and mermaid-doc generation are done by whichever agent is
  wired into the editor.
- Post-processing: Adobe Express (PNG→SVG) and Vectorpea — both free-tier web tools, zero
  programmatic API integration, 100% manual/browser-driven.

## Consequence for CCF architecture (feeds Phase 1)

This single example is a **complete, small, real reference implementation** of exactly the
"genuinely NEW" slice identified in `PP_CAPABILITY_INVENTORY.md`: a provider adapter
(`generate.mjs`'s job, generalized), and brand-domain pipeline stages (concept-brainstorm →
prompt-assembly → generate → showcase → pick → deepen → vectorize). The config→script→HTML→
headless-Chrome-PDF shape is *itself* a candidate REUSE target — it is a simpler, more concrete
answer to "Artifact Compiler" than anything in the original 15-subsystem CCF spec, and should be
adopted rather than re-invented in Phase 2.
