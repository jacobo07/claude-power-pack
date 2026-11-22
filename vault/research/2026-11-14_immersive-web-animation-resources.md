---
title: Immersive web animation resources (scroll photo journeys + 3D camera tours)
date: 2026-11-14
origin: Owner request in Landcaster Real Estate ("hay recursos en GitHub que hagan estas animaciones, o creamos uno para futuras webs?")
evidence: gh search repos / gh repo view / gh api repos/<r> on 2026-11-14 (stars and licences measured that day)
grade: E2 (popularity + licence measured; fitness judged from READMEs and known APIs, not benchmarked)
---

# Immersive web animation resources

Two effects were built for the Landcaster prototype (spec `docs/specs/immersive-journeys.md` in that repo):
1. **Photo journey.** Sticky full-viewport stage, scroll-driven cross-dissolve, a slow camera move on each photo, a gold SVG
   line drawn with scroll progress, and a finale with a CTA.
2. **3D cinematic tour.** three.js camera and target on CatmullRom paths, a gold ground line growing with progress,
   one headline per stop, and pause/exit.

## Scroll / photo journey

| Repo | Stars | Licence | Fit |
|---|---|---|---|
| motiondivision/motion | 35.1k | MIT | React `useScroll`/`useTransform`. Best fit for Next.js. |
| greensock/GSAP (+ScrollTrigger) | 30.6k | own licence (no SPDX) | Industry standard for pin + scrub. Free since 2025 as I understand it, but not OSI: check before client use. |
| darkroomengineering/lenis | 17.3k | MIT | Smooth scroll; pairs with GSAP/Motion. |
| russellsamora/scrollama | 6.0k | MIT | Step detection via IntersectionObserver; tiny. |
| basementstudio/scrollytelling | 1.7k | NOASSERTION | React+GSAP scrollytelling. Do not use until the licence is clear. |

Native option: CSS scroll-driven animations (`animation-timeline: scroll()/view()`). Zero JS. Check current browser
support (Firefox) before relying on it, and always keep a stacked no-JS / reduced-motion fallback.

## 3D camera tour

| Repo | Stars | Licence | Fit |
|---|---|---|---|
| yomotsu/camera-controls | 2.5k | MIT | Smooth transitions between camera poses. Fits plain three.js. |
| theatre-js/theatre | 13.0k | Apache-2.0 | Visual editor for authored camera paths. Last push 2024-08: maintenance risk. |
| pmndrs/react-three-fiber + drei | 33.7k / 10.2k | MIT | R3F stack (`ScrollControls`, camera helpers). Means rewriting a vanilla viewer. |
| 14islands/r3f-scroll-rig | 1.0k | MIT | Syncs 3D meshes with DOM scroll. |
| pmndrs/postprocessing, N8python/n8ao | 3.0k / 0.5k | MIT-family | SMAA/AO polish; desktop-only. |

## Existing "for future sites" skill

`nateherkai/scroll-craft` (5.1k, MIT) is an agent skill and Claude Code plugin for premium scroll-driven sites: design
workflow, engine, verification tools, eight "page grammars". It is one practitioner's design doctrine, built from ten
of their own sites. Use it as reference (METHOD, not DATA), not as our standard.

## Recommendation

1. Landcaster: keep the dependency-free implementation (own rAF, plus the three.js the viewer already uses). No new
   weight, no licence review.
2. Future sites: after the Landcaster journeys ship, extract them into a reusable PP kit. That means the photo journey
   and the camera tour, their no-JS and reduced-motion fallbacks, and their QA flows (axe AA, overflow 320-1440, journey
   reaches its finale, tour reaches its final stop, exit works).
3. Escalate to GSAP/Motion (scroll) and camera-controls (3D) only when a site needs more: video scrubbing, many pinned
   sections, or authored multi-shot camera work.
