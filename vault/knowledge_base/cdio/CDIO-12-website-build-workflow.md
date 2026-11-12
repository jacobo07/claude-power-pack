---
id: CDIO-12
name: Website Build Workflow — the Construction Axis
type: dataset
domain: cdio
status: sealed
governs: [cdio-core, cdio-reviewer]
governed_by: CDIO-00
source: video fDTwHIKltpc "The EASY way to build a beautiful website with Claude Code (full workflow)" (Create a Pro Website, uploaded 2026-07-02, 26:00), absorbed 2026-11-12
evidence: full transcript read (Spanish auto-dub track es-US-orig, 5,357 words) + video description; no frames viewed (see sec. 8)
---

# CDIO-12 — Website Build Workflow (the Construction Axis)

Every other CDIO dataset answers a question about a surface that already exists or is about to
be chosen: is it good (CDIO-00..05), which family does it belong to (CDIO-06), how may it behave
(CDIO-07), which legal pages does it owe (CDIO-10). None of them answers the question the Owner
asks first when a business needs a site: **what do we do, in what order, from an empty folder to
a live domain?** CDIO-12 is that answer. It is the construction axis: a sequence of steps, each
with what it consumes, what it produces, and what the review will later check it against.

The sequence is absorbed step for step from one source, the video "The EASY way to build a
beautiful website with Claude Code (full workflow)" by the channel Create a Pro Website. The
Owner asked for the method to be ingested "exactamente igual", so every step the video shows is
kept, in the video's order, with the video's timestamps. Four of those steps, done literally,
would breach a floor this pack already enforces; for those four the step is kept and the
breaching part is replaced, and sec. 6 says what was replaced and why. The Owner also chose a
generic publishing step over the video's Hostinger walkthrough; sec. 7 records that choice.

CDIO-12 adds a workflow and criteria; it never relaxes a CDIO-00 floor. Where it and an older
dataset appear to disagree, CDIO-00 decides.

## 1. Scope

CDIO-12 applies when the Owner asks to build, rebuild or redesign a **website for a business or
a person**: a brochure site, a local-service site, a portfolio, a landing site with a handful of
sections. That is the class of site the video builds (a full-service landscaping company in
Austin, Texas, delivered as one HTML file with an inline video hero).

It does not apply on its own to:

- **App screens.** A native or hand-held app surface is CDIO-08.
- **A single decision surface.** An onboarding modal or confirmation dialog is CDIO-09.
- **Commerce with a catalogue, a cart or subscriptions.** The build sequence still holds, but
  the structure of the site belongs to the commerce backlog items (TUA-X #4, #7, #10), absorbed
  in phase 2 of SPEC-CDIO-12.
- **A product that needs a backend.** The video says so itself at 20:59: a site that takes
  payments or stores user data needs more than static hosting. The stack question in sec. 4
  routes it away from the single-file default.

## 2. The method, step by step

Nine steps. The number and title of each step below is the gate's FIDELITY anchor: removing one
fails `V-CDIO-BUILD-FIDELITY`. Timestamps are the video's.

### Step 1 — Gather the assets before anything else (01:09-02:58)

The video's first instruction is not about Claude at all: collect the business information, the
logo, the brand colours, and any professional photos or video **before** starting, in one folder.
Where professional media does not exist, generate it (the video used an image and video
generation platform for every image, the before/after pair and the hero video). The stated
reason is practical: during design you find everything at once instead of hunting for it later.

In CDIO terms, this step produces the **asset folder** (`media/` inside the project) and the
**fact sheet**: business name, city, services, phone, email, address, opening hours, and any
proof facts (years in business, number of projects, named reviews). Every number or testimonial
that appears on the finished site must trace back to this fact sheet (criterion
`claims-have-source`). Generated imagery is allowed and must be labelled as such in the fact
sheet, because a generated "before/after" is an illustration, not a record of a job; the site
must not present it as one unless the Owner confirms it depicts real work.

### Step 2 — Create the project folder and trust it (02:58-05:02)

One new folder per site, named for the site, with the asset folder inside it. The session is
opened on that folder and the workspace is trusted so the agent can read every asset. In the
video this is Claude Desktop's "Code" tab, "New session", "Open folder", "Trust workspace". In
the CLI it is starting the session with that folder as the working directory. The point that
transfers: the build folder **is** the deliverable (Step 9 publishes its contents), so nothing
that is not part of the site belongs in it.

### Step 3 — Load the two design skills (05:02-07:34)

The video installs two skills globally and calls skipping them "how you get generic, boring
AI websites":

1. **`frontend-design`** (Anthropic): steers away from over-used fonts and default palettes
   toward a distinct typographic and layout direction.
2. **`ui-ux-pro-max`** (nextlevelbuilder): a searchable library of palettes, font pairings, UI
   styles and stack guidance. Its own SKILL.md makes `--design-system` the required first call:
   `python3 skills/ui-ux-pro-max/scripts/search.py "<product> <industry> <keywords>" --design-system -p "<Name>"`.

Both are installed on this host (`~/.claude/skills/frontend-design`,
`~/.claude/plugins/cache/ui-ux-pro-max-skill/ui-ux-pro-max`). In this pack they are
**generators**; CDIO stays the judge. Their output is a candidate direction that CDIO-06 names
as a family and CDIO-05 later scores. Where a skill's recommendation and a CDIO floor disagree
(a contrast pair, a font size under the floor), the floor wins and the disagreement is recorded.

### Step 4 — Choose a reference from a curated gallery (07:34-09:45)

"Instead of blindly asking it to build a website from scratch, give it a reference image or a
link to another site." The video uses two galleries: Awwwards (award-winning sites, with live
previews) and Dribbble (searchable; the video searches the vertical, "landscaping"). Two ways to
use them: take one site you like and capture **the whole page**, or capture parts of several and
assemble a "Frankenstein" of favourite sections.

What the reference is for, in CDIO terms: it fixes the **section inventory** and the **general
direction** (density, rhythm, image-to-text ratio, hero treatment). It is not a template to
clone. Sec. 6.1 records why, and where an exact copy is genuinely wanted (`image-calco`).

### Step 5 — Write the first prompt with the reference attached (09:45-11:00)

One message: the skill invoked by slash command (`/ui-ux-pro-max`), the reference screenshot
pasted, and a prompt in plain language. The template is in sec. 3. The video singles out its
last sentence, "please ask me any questions you need to complete this job", as "very important":
it makes the agent come back with what it needs instead of the Owner guessing. The video also
dictates the prompt by voice and leaves permission mode on auto; neither is part of the method's
substance.

### Step 6 — Answer the intake questions (11:00-13:00)

The agent returns a short questionnaire before writing code. The video's four questions were:
does the brand already exist (colours, logo) or should it be designed; which sections (the
reference had hero, trust bar, about, services, blog, contact; the Owner added a before/after
section and a four-step process section); how to build it (one HTML file, a multi-file static
site, or a React/Next.js project; the agent recommended one HTML file and the video took it);
which services the business offers. Sec. 4 keeps those four and adds the ones CDIO needs.

### Step 7 — First draft from the asset folder (13:00-14:00)

The agent searches the project folder, finds the logo, extracts the brand colours from it,
finds the before/after photos and builds every agreed section, then checks its own work and
reports what it did. The video's lesson: because the material was supplied up front, the agent
"knows exactly what to look for". CDIO adds two checks at this point: the colours used must be
the ones extracted from the Owner's logo or brand file (`brand-from-owner-assets`), and the
section list built must equal the section list agreed in Step 6
(`sections-declared-match-built`).

### Step 8 — Review in preview and iterate (14:00-19:55)

The video opens the preview and walks the page top to bottom. What it found is the most useful
part of the method, because each finding is a recurring defect class:

- The hero is cut off at the bottom of the first viewport (fixed: "make sure the elements fit
  above the fold") — criterion `hero-fits-first-viewport`.
- The primary call to action ("get a free quote") actually scrolls to its target — criterion
  `primary-cta-resolves`, checked rather than assumed.
- The team photo sits in the wrong section, and a three-image row crops the crew — criterion
  `image-fit-and-placement`.
- The blog cards lead nowhere (the video calls them a stand-in to fill later) — criterion
  `no-empty-section`.
- The agent wrote all the copy, including a project story ("completed in 11 days") and a reviews
  section — criterion `claims-have-source`.
- The hero image is replaced by a video that plays as the visitor scrolls (scroll-scrubbed) —
  criteria `motion-has-still-equivalent` and `hero-media-weight`.

The iteration tools the video uses are Claude Desktop's: refresh the preview, open the localhost
link in a normal browser, draw on the preview and attach the drawing to the chat, or select an
element and describe the change ("one horizontal crew image instead of three, uncropped"). The
CLI equivalent is a local static server plus browser screenshots at the two review viewports
(1440x900 and 390x844). Before publishing, the video insists: replace every sample value — the
phone number, the quote details, the contact information — with the real ones
(`real-contact-data`).

### Step 9 — Publish the folder contents to a host with a domain (19:55-26:00)

Until now the site exists only on localhost. The video buys static hosting with a bundled free
domain, chooses "migrate an existing site", uploads a backup archive and attaches the domain.
The step that transfers to any host, and that the video stresses as "very important": **compress
the contents of the build folder, not the folder itself**, so that `index.html` sits at the
document root. Compressing the folder publishes a site whose root is a subdirectory. Sec. 7
replaces the specific host with the pack's deploy governance (Owner answer 2) and keeps this
rule as criterion `publish-root-is-site-root`.

## 3. The first-prompt template

Back-translated from the Spanish auto-dub track; the English original was not retrievable
(sec. 8), so the wording is close, not verbatim:

> Please create a website for **{business name}** here in **{city, region}**. I'd like this
> website to use this reference image as inspiration, but using my own branding, colours and
> logos. I'd also like to include some specific sections on my website. Please ask me any
> questions you need to complete this job.

Attached in the same message: the reference capture (Step 4), and the skill invocation
`/ui-ux-pro-max`. In this pack, three clauses are added after the video's last sentence. Each
closes a gap the video's own review exposed:

> Use only facts from the fact sheet in `media/` for numbers, reviews, dates and contact
> details; where a fact is missing, ask instead of writing one. Do not add a section that has
> no real content yet. Any motion must have a still equivalent under reduced motion.

The video's sentence "ask me any questions" is the load-bearing one and must never be dropped:
it is what turns the first turn into an intake instead of a guess.

## 4. The intake questions

The agent asks these before writing code. Questions 1-4 are the video's; 5-9 are what the rest
of CDIO needs and would otherwise be filled by inference.

1. **Brand.** Do you already have a logo and brand colours, or should they be designed? (If
   designed, the work routes to the brand-identity backlog item and `cpp creative`, not to an
   improvised palette.)
2. **Sections.** Which sections? Start from the reference's inventory, then add the business's
   own (the video added before/after and a four-step process).
3. **Stack.** One HTML file, a multi-file static site, or a framework project? Default: one
   HTML file for a brochure site with no backend, as the video recommends; a framework only when
   the site needs routing, a CMS or server code.
4. **Offering.** Which services, in the business's own words?
5. **Goal.** What is the one action a visitor should take (call, quote form, booking)? This is
   the primary call to action CDIO-04 scores.
6. **Proof.** Which reviews, numbers and project stories are real, and where is their source?
7. **Contact data.** The real phone, email, address and hours.
8. **Jurisdiction.** Where does the business operate (us / eu / es)? CDIO-10 needs it to plan
   the legal pages: `python -m modules.cdio.legal_surface plan --jurisdiction <j>`.
9. **Motion.** How much motion may the site carry? Answered through the CDIO-07 experience
   picker, never by the agent's taste.

## 5. The criteria (what CDIO-12 can fail)

Each criterion names the dimension it reports under, so the deterministic scorer in CDIO-05 sec.
4 weighs it without any change to the formula. Severity follows CDIO-05 sec. 3.

**`brand-from-owner-assets`** (dimension `visual`, severity major). When the Owner supplied a
logo or brand colours, the site's palette and mark come from them. Observed-value form: "accent
#2F7D4A not present in logo.svg; logo's greens are #1E5B3A and #8DBF5A". An invented palette
beside a supplied one is the generic-site failure the video's skills exist to prevent.

**`reference-is-direction-not-copy`** (dimension `visual`, severity major). The reference fixed
the section inventory and the direction; the built site is not a clone of the reference's
layout, typography and copy. Observed-value form: "hero headline, font pairing and three-column
grid identical to the reference capture". An exact copy, when the Owner actually wants one,
routes to `image-calco` and is out of this criterion.

**`sections-declared-match-built`** (dimension `ux`, severity major). Every section agreed at
intake is present, and no section exists that was not agreed. Observed-value form: "intake
agreed 8 sections; page renders 7 (process section absent)".

**`no-empty-section`** (dimension `trust`, severity major). No section, card or navigation target
is an empty stand-in: every link leads to real content. Observed-value form: "three blog cards
link to `#`; no post exists". A navigation item that dead-ends is critical under the general
rule and is reported as such.

**`claims-have-source`** (dimension `trust`, severity critical). Every testimonial, rating,
count, duration, year and named client traces to the fact sheet. Observed-value form: "'completed
in 11 days' and five five-star reviews; fact sheet lists no project duration and no reviews".
Invented proof is critical because it is a false statement to a buyer, not a design weakness.

**`hero-fits-first-viewport`** (dimension `ux`, severity major). At 1440x900 and 390x844 the
hero's headline and primary call to action are fully visible without scrolling. Observed-value
form: "at 1440x900 the trust cards start at y=930; the hero CTA is cut at y=884".

**`primary-cta-resolves`** (dimension `conversion`, severity major). The primary call to action
reaches a working target: an anchor that exists, a form that submits somewhere real, a `tel:` or
`mailto:` with the real value. Observed-value form: "'Get a free quote' scrolls to `#quote`; no
element has id `quote`".

**`real-contact-data`** (dimension `trust`, severity major). Phone, email, address and hours are
the Owner's real values from the fact sheet. Observed-value form: "header phone (512) 555-0147
is a 555 sample number; fact sheet phone differs".

**`image-fit-and-placement`** (dimension `visual`, severity minor). Each image sits in the section
its subject belongs to and is not cropped through a face or the subject. Observed-value form:
"team photo used in services; crew cropped at the shoulders in a three-up row".

**`motion-has-still-equivalent`** (dimension `ux`, severity critical). A scroll-scrubbed,
autoplaying or looping video or animation has a still equivalent under `prefers-reduced-motion`,
and no information exists only inside the motion. Observed-value form: "reduced motion on: hero
video still scrubs with scroll; no poster frame". This is a floor (HR-EXPERIENCE-FLOOR-001), so
it is critical.

**`hero-media-weight`** (dimension `ux`, severity minor). A hero video has a poster image, is
compressed for the web, and does not block the first render. Observed-value form: "hero.mp4
48 MB, no poster; LCP 6.8 s on a throttled mobile profile".

**`publish-root-is-site-root`** (dimension `ux`, severity major). On the live domain, `/` serves
the site's `index.html`. Observed-value form: "https://example.com/ returns a directory listing;
the site is at /landscaping-website/". This is the video's "compress the contents, not the
folder" rule made checkable.

## 6. The four floor collisions (what "exactly the same" could not mean)

The Owner asked for the method "exactamente igual". Every step is kept. In four places the
video's literal action breaches a floor this pack already enforces; there the step stays and
the breaching part is replaced.

### 6.1 The reference as a template

The video lets the agent "mimic the reference image quite well" and is pleased that it does.
CDIO's art direction asks for an original surface, and a clone of a third-party award-winning
site is also another studio's work. Kept: the reference fixes inventory and direction.
Replaced: the clone. Criterion `reference-is-direction-not-copy`; exact-match work goes to
`image-calco`.

### 6.2 The scroll-scrubbed hero video

Kept: the hero may be a video, and it may respond to scroll if the CDIO-07 contract allows that
much motion. Replaced: a motion with no still equivalent, which HR-EXPERIENCE-FLOOR-001 makes
critical. Criterion `motion-has-still-equivalent`.

### 6.3 The empty blog

The video notices the blog leads nowhere and leaves it for later. The Reality Contract forbids
shipping a section with nothing behind it. Kept: a blog, if there is content. Replaced: an empty
one; the section is removed until there is content. Criterion `no-empty-section`.

### 6.4 The invented copy and proof

The video praises the agent for writing "all the copy" and generating a project story. The
evidence gate for generated content (`generated-content-needs-an-evidence-gate`) holds that a
claim about the world needs a fact. Kept: the agent drafts the copy. Replaced: invented numbers,
reviews and stories; those come from the fact sheet or are asked for. Criterion
`claims-have-source`.

## 7. Publishing (Owner answer 2: generic, under DEPLOY_GOVERNANCE)

The video's host, coupon and affiliate link are not adopted. What is kept from Step 9:

1. The site is published from the build folder's **contents** (criterion
   `publish-root-is-site-root`).
2. A custom domain is attached before the site is called live.
3. Every sample value was replaced first (`real-contact-data`).

What the pack adds, from `governance/DEPLOY_GOVERNANCE.md`: done means HTTP 200 on the real
domain, observed, not a successful upload. Before publishing, the legal pages from CDIO-10 exist
(`python -m modules.cdio.legal_surface check <site_root> --jurisdiction <j>` exits 0), and the
CDIO-05 review returned APPROVE. Any static host satisfies Step 9: a host the Owner already uses
(Vercel per the deploy governance), or a plain static host that accepts an archive upload.

## 8. Evidence, scope and what is still planned

| What | Status |
|---|---|
| Transcript | read in full: the only downloadable track was the Spanish auto-dub `es-US-orig` (5,357 words); the English tracks returned HTTP 429 |
| Prompt wording | back-translated from the auto-dub, not verbatim English (sec. 3) |
| Skill names and links | taken from the video description, not from the speech |
| Frames | not viewed; the `yt-research` pipeline exited 1 with no output, so no visual of the reference site or the result was examined |
| The method run end to end in this pack | **PLANNED**: no site has yet been built through CDIO-12; the first real build records its result here |
| Hostinger walkthrough (19:55-26:00) | observed in the transcript, deliberately not adopted (sec. 7) |

The criteria in sec. 5 are derived from defects the video itself shows and fixes on screen, so
each has at least one observed instance. None has yet been scored on an Owner site.

## 9. Common false positives (what CDIO-12 does not flag)

- A site built without a gallery reference. Step 4 improves the first draft; its absence is
  not a defect in the result.
- A site built in a framework instead of one HTML file, when the intake chose it for a reason.
- Generated imagery that is labelled in the fact sheet and not presented as a real job.
- A hero video under an experience contract that allows it, with a still equivalent.
- Copy drafted by the agent that makes no factual claim.

## 10. Contract with the review pipeline

`cdio-core` routes any request to build, rebuild or redesign a website to CDIO-12 for the
sequence, to CDIO-06 for the direction Step 3's skills propose, to CDIO-07 for intake question 9,
and to CDIO-10 for the legal pages. `cdio-reviewer` applies the sec. 5 criteria inside the normal
CDIO-05 lenses at Step 8 and again before Step 9; the score is still computed by
`modules.cdio.scorer`, and a critical (`claims-have-source`, `motion-has-still-equivalent`)
blocks APPROVE as any critical does. The gate for this dataset is `python tools/test_cdio_build.py`.
