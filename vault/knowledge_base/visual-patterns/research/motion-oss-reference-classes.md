# Motion OSS reference classes

Retrieval date: 2026-09-30. Method: GitHub API (gh), raw LICENSE files on `main`, shallow clones + grep, npm registry. Anything not observed is marked UNVERIFIED.

Verification notes: license text read from the raw LICENSE files on `main`; dates from GitHub `pushed_at` and `git log -1` of shallow clones; reduced-motion via GitHub code search and grep of shallow clones (Motion Primitives, Animate UI, Magic UI). Code search can be incomplete: "NOT FOUND" means not found by those methods, not proof of absence. GitHub Releases: only Animata publishes them (v3.4.1, 2026-09-14); the others return 404, so release date is UNVERIFIED (Motion: see npm).

## 1. Motion Primitives
- Repo: https://github.com/ibelick/motion-primitives
- License: file is `LICENCE.md` (sic), "MIT License", Copyright (c) 2024 ibelick. No extra clause seen.
- Last commit: 2026-09-28 ("fix: remove .vercelignore").
- Runtime dep: `motion` ^11.12.0 (+ tailwindcss-animate). Copy-paste components via CLI.
- prefers-reduced-motion: NOT FOUND (0 hits for useReducedMotion / prefers-reduced-motion / reducedMotion in clone .ts/.tsx/.css and in code search). Consumer must add `MotionConfig reducedMotion="user"`.
- Principles:
  1. Shared-element continuity via `layoutId` (`components/core/morphing-dialog.tsx`, `morphing-popover.tsx`, `animated-background.tsx`): trigger and content share an id so open/close reads as one object transforming.
  2. Transition config injected once at the container (`MotionConfig transition={transition}` in morphing-dialog): timing is a system decision, not per child.
  3. Stagger is a group-level property (`animated-group.tsx`, `text-effect.tsx`): parent declares order, children declare variants.
  4. Spring for spatial moves (carousel, morphing-popover, animated-group); disclosure state keeps aria wiring beside the motion (`aria-expanded`, `aria-controls`).

## 2. Animate UI
- Repo: https://github.com/animate-ui/animate-ui (old path imskyleen/animate-ui has identical LICENSE text).
- License: LICENSE.md titled "MIT + Commons Clause License Condition", Copyright (c) 2025 Elliot Sutton. Grants use "as part of an application, website, or product"; a "Commons Clause Restriction" section bars selling/redistributing the components themselves. GitHub reports NOASSERTION.
- Last commit observed: 2025-12-31 (merge of PR #168); nothing newer on main as of retrieval (~9 months quiet).
- Runtime dep: `motion` ^12.23.x.
- prefers-reduced-motion: PARTIAL. Docs `apps/www/content/docs/accessibility.mdx` recommend `<MotionConfig reducedMotion="user">`; `apps/www/registry/primitives/effects/click/index.tsx:68` checks `matchMedia('(prefers-reduced-motion: reduce)')`. Only 2 source files reference it; support is mostly delegated to Motion.
- Principles:
  1. Reduced motion is a root policy: drop transform/layout animation, keep opacity/colour (accessibility.mdx).
  2. A single moving highlight follows hover/selection via `layoutId` (`components/effects/motion-highlight.tsx`, `registry/components/base/menu/index.tsx`): one indicator, not N toggled backgrounds.
  3. Springs for tab/indicator moves (`components/animate/tabs.tsx`); presence exits via AnimatePresence (`effects/motion-effect.tsx`).
  4. Small primitives (motion-effect, motion-highlight) compose into components: a reusable timing vocabulary.

## 3. Magic UI
- Repo: https://github.com/magicuidesign/magicui
- License: LICENSE.md, "MIT License", Copyright (c) Magic UI. No extra clause seen. Site content licensing: UNVERIFIED.
- Last commit: 2026-09-20 ("feat(showcase): add OverlayUI showcase entry (#1013)").
- Runtime dep: `motion` ^12.23.12 (apps/www); many components use CSS keyframes.
- prefers-reduced-motion: PARTIAL, per component. `apps/www/registry/magicui/dia-text-reveal.tsx` imports useReducedMotion; `docs/components/icon-cloud.mdx` states rotation pauses under prefers-reduced-motion; `retro-grid.tsx`, `floating-3d-particles.tsx`, `icon-cloud.tsx` matched. Only 5 source files match across a large registry, so most components do NOT honour it.
- Principles:
  1. Progressive reveal: `registry/magicui/text-animate.tsx` (stagger) and `animated-list.tsx` (items enter one by one, AnimatePresence): sequence communicates a stream of events.
  2. Device mockups (`registry/example/android-demo*.tsx`, iPhone/Safari mockups): demo content sits in static device chrome so only the content moves.
  3. Springs for small state changes (`animated-subscribe-button.tsx`, text-3d-flip demo); CSS/tween for ambient loops (border-beam, retro-grid), which are the ones needing a reduced-motion switch.
  4. layoutId: NOT FOUND in this repo.

## 4. React Bits
- Repo: https://github.com/DavidHDev/react-bits
- License: LICENSE.md titled "MIT + Commons Clause License Condition v1.0", Copyright (c) 2026 David Haz. Quote: "You may use this Software, including for any commercial purpose, so long as you do not sell, sublicense, or redistribute the components themselves-whether alone, in a bundle, or as a ported version." GitHub reports NOASSERTION.
- Last commit/push: 2026-09-29.
- Runtime deps (varies by variant): gsap ^3.13.0, motion ^12.23.12, ogl ^1.0.11, three ^0.180.0.
- prefers-reduced-motion: YES in part. Code search: 162 files for useReducedMotion, 273 for reduced-motion; e.g. `src/utils/renderGate.js`, `src/hooks/usePreviewMediaAllowed.js`, `src/content/Micro/SpringCheck/SpringCheck.jsx` (confirmed `useReducedMotion` from motion/react + `type: 'spring'`), `src/content/Micro/StatusMark/StatusMark.jsx`, `src/content/Micro/Shredder/Shredder.css`. Per-component coverage of the whole catalog UNVERIFIED (hits may include the docs site shell).
- Principles:
  1. Heavy effects (ogl/three) sit behind a render gate / media-allowed hook (`renderGate.js`, `usePreviewMediaAllowed.js`): expensive or vestibular-risk visuals are opt-in by capability and preference.
  2. Micro-interactions (SpringCheck, StatusMark) express a state change as a small spring with a reduced-motion branch.
  3. Most of the catalog is decorative text/background effects, which must degrade to static.

## 5. Animata
- Repo: https://github.com/codse/animata
- License: LICENSE.md, "MIT License", Copyright (c) Animata. No extra clause seen.
- Last commit/push: 2026-09-14; release v3.4.1 published 2026-09-14.
- Runtime deps: `motion` ^12.38.0, `tw-animate-css` ^1.4.0; many components are Tailwind/CSS-only.
- prefers-reduced-motion: YES in part. Shared hook `hooks/use-prefers-reduced-motion.ts` (useSyncExternalStore on `(prefers-reduced-motion: reduce)`); CSS files reference it (`animata/text/roll-text.css`, `animata/fabs/speed-dial.css`, `animata/text/metis-text.css`; 45 code-search hits); `app/demo/demo-experience.tsx`. Whole-catalog coverage UNVERIFIED.
- Principles:
  1. One shared hook plus the CSS media query is the contract: JS motion checks the hook, CSS motion uses the media query.
  2. CSS-first animation for simple state changes (fab speed-dial, text rolls): no runtime cost, reduced-motion is a one-line override.
  3. Motion library reserved for sequences/presence.

## 6. Motion (motion.dev, formerly Framer Motion)
- Repo: https://github.com/motiondivision/motion (monorepo: framer-motion, motion-dom).
- License: LICENSE.md, "The MIT License (MIT)", Copyright (c) 2024 Motion B.V.
- Last commit/push: 2026-09-30. npm `motion` latest 13.4.6, registry modified 2026-09-29 (no GitHub Releases).
- Runtime dep: it is the runtime (`motion/react`, vanilla `motion`).
- prefers-reduced-motion: YES, first-class. `packages/framer-motion/src/utils/reduced-motion/use-reduced-motion.ts`, `use-reduced-motion-config.ts`, `packages/motion-dom/src/render/utils/reduced-motion/index.ts`; `MotionConfig reducedMotion="user"` disables transform and layout animations while keeping opacity/colour (as documented by Animate UI).
- Principles (API-level claims inferred from source paths and downstream repos; motion.dev doc pages not fetched, so UNVERIFIED as doc quotes):
  1. State transitions as declarative targets/variants with presence exits (AnimatePresence).
  2. Continuity via `layoutId`: the library computes the move between two DOM positions.
  3. Spring for spatial/physical, tween for opacity/colour; transitions set at MotionConfig scope.
  4. Reduced motion is centralised: one config switch, semantic (drop transform, keep opacity).

## Summary table

| source | license | reduced-motion support | recommended use |
|---|---|---|---|
| Motion Primitives | MIT (LICENCE.md) | NOT FOUND | LEARN-PRINCIPLE-ONLY (add MotionConfig ourselves) |
| Animate UI | MIT + Commons Clause | Partial (docs + 2 files, delegates to Motion) | LEARN-PRINCIPLE-ONLY (Commons Clause bars redistributing components; repo quiet since 2025-12-31) |
| Magic UI | MIT | Partial (5 files) | LEARN-PRINCIPLE-ONLY (most components lack reduced-motion) |
| React Bits | MIT + Commons Clause v1.0 | Partial/broad (162 hits) | LEARN-PRINCIPLE-ONLY; AVOID redistributing its components in any shipped kit |
| Animata | MIT | Partial (shared hook + CSS, 45 hits) | LEARN-PRINCIPLE-ONLY |
| Motion | MIT | Yes, first-class | SAFE-TO-DEPEND |

## Cross-source principles (seen in >=2 sources)
1. Shared-element continuity through one shared id (`layoutId`): Motion Primitives (morphing-dialog/popover/animated-background), Animate UI (motion-highlight, menu, header), implemented by Motion.
2. Reduced motion is a root-level policy: drop transform/layout, keep opacity/colour (Animate UI accessibility.mdx, Motion `reducedMotion="user"`); Animata and React Bits add per-component hooks. Motion Primitives shows the failure mode when nobody sets it.
3. Stagger belongs to the parent/group; children only supply variants (Motion Primitives animated-group/text-effect, Animate UI splitting, Magic UI text-animate).
4. Spring for spatial/physical state changes, tween/CSS for opacity and ambient loops (Motion Primitives, Animate UI, Magic UI, React Bits SpringCheck).
5. Timing configured once at a container/config scope, not per element (Motion Primitives MotionConfig, Motion, Animate UI docs).
6. Ambient/looping and heavy decorative effects are what need a preference gate (Magic UI icon-cloud, React Bits renderGate, Animate UI a11y doc).
7. Not promoted (single source): device-mockup/product-demo sequences appear only in Magic UI.
