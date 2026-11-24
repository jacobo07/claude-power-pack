# First CDIO-13 build: recipe 02 (ERA style) on an invented guesthouse

Owner, 2026-11-24 (D44.3): "A demo site, recipe 02". Sotomenor is invented; the site is a demo,
never published. This folder is the evidence of the first end-to-end run of a CDIO-13 recipe
through the CDIO-12 sequence.

## How it was built (CDIO-12 steps)

| Step | What happened |
|---|---|
| 1 Assets + fact sheet | Fact sheet in `DESIGN.md`: 4 rooms, March-November, car + 3 km track, contact on the reserved `.example` domain, **proof: none**. No photographs; original inline SVG illustrations. |
| 2 Folder | This folder; nothing outside the site in it except `qa/`. |
| 3 Skills | Read: `anthropics__skills/skills/frontend-design`, `MengTo__Skills/.../masked-reveal`, gsap guidance (matchMedia for reduced motion). |
| 4 Reference | ERA Residence, principles only: restrained editorial type, generous space, arch masks, paced sections. Nothing copied. |
| 5-6 Prompt + intake | Run by the agent for a demo brand; answers are the fact sheet. |
| 7 Draft | `index.html`: one page, F1 base with a brand voice (lichen / bark / moss / sloe, Bodoni Moda + Figtree). |
| 8 Review + iterate | Browser QA (`qa/qa_site.py`, Playwright, 1440x900 and 390x844) + two `cdio-reviewer` passes (below). |
| 9 Publish | Not done: demo, no domain. Publish-root and CDIO-10 legal criteria are not assessable. |

Gates before any page code: CDIO-07 picker -> `restrained` / `motion_budget: low` (visitors arrive
with a task); CDIO-06 picker -> F1 (F3 rejected: it is the cream/serif/terracotta default that
frontend-design names as the commonest generated-page tell). `tools/design_gate.py` on DESIGN.md:
first APPROVE 92 with **0 colours and no fonts read** (tokens were in a table, not front matter --
a vacuous pass), then APPROVE 100 once the tokens were in front matter and actually measured.

## Review 1 -- BLOCK, score 75 (modules.cdio.scorer, 15 verdicts)

One critical: `tap-target-size`. Header links and wordmark were inline text, about 25.6px tall
(floor 44px). The browser QA had not measured tap targets at all, and none of the recipe's four
checks (CDIO-13 sec. 6) covers them. Minor: footer said "the address above" with no address
shown; CLS had been measured unthrottled only.

## Fix and re-measure

- Header links and wordmark: `inline-flex`, `min-height: 44px`. QA gained a tap-target probe
  (every link/button outside running text): fixed page `[]` on both viewports. Red drill on a copy
  with the old style restored (`qa/qa-tap-drill.json`): Sotomenor 123x24, Rooms 50x26, Stay 32x26,
  Enquire 54x26 -- the probe can return the failing answer.
- Footer names the demo address explicitly.
- Throttled CLS (slow 4G 150 ms / 1.6 Mbps, CPU x4): desktop 0.0028, mobile 0.0018.

## Review 2 -- APPROVE, score 100 (0 critical, 0 major, 0 minor)

| Criterion | Result | Observed value (`qa/qa.json`) |
|---|---|---|
| hero-fits-first-viewport (CDIO-12) | pass | CTA bottom 834 / 900 desktop, 790 / 844 mobile |
| claims-have-source (CDIO-12) | pass | fact sheet "proof: none"; no ratings, counts or years on the page |
| primary-cta-resolves (CDIO-12) | pass | `#enquire` exists; mailto to the disclosed demo domain |
| motion-has-still-equivalent (CDIO-12) | pass | reduced motion: 0 ScrollTriggers, all arches `clip-path: none` |
| layout-before-motion | pass | JS off: arches open, all sections visible, nav scrolls |
| smooth-scroll-yields | pass (no smooth-scroll layer) | native scroll only |
| mobile-motion-checked | pass | 390x844: arches inset(30% 14%) -> inset(0%), no pinning |
| one-signature-interaction | pass | one arch reveal, once, 1.4 s; 4 ScrollTriggers of one kind |
| stable-layout-while-loading | pass | CLS 0.0028 / 0.0018 throttled |
| webgl-has-fallback, 3d-assets-budgeted, split-text-stays-readable | not applicable | no WebGL, 3D or split text |
| animations-cleaned-up | not assessed | single static page; gsap.matchMedia reverts on query change |
| Contrast | pass | sloe/lichen 6.29, bark/lichen 8.39, white/sloe 10.23, mist/moss 6.67 |
| Lens 7 (CDIO-07) | conforming | one one-shot reveal; no loop, celebration or character |

## What this run taught CDIO-13

1. The recipe's four checks are not a sufficient review: tap-target size (a CDIO-00 floor) was the
   only critical, and none of the four covers it. The CDIO-05 review must run on every recipe build.
2. A design gate that reads zero tokens still says APPROVE; tokens belong in DESIGN.md front matter.
