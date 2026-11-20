---
id: DOC-MOTION-LIB
name: Motion library selection and lifecycle contract
type: doctrine
domain: visual-patterns
status: active
---

# Motion library selection and lifecycle contract

Absorbs the library-independent lessons of Anime.js v4.5.0 (MIT, @ 01b81be1; ledger `vault/programs/bcap-2/animejs/DISPOSITIONS.md`).
Owner of the decision: CDIO-07 (`experience:` contract) and `modules/cdio/motion_patterns.py`. This file adds no second resolver.

## Observed upstream fact that shapes this doctrine

Anime.js `src/` contains no `prefers-reduced-motion` handling (grep, 0 hits at the pin). Its `Scope` offers `matchMedia`-driven
`mediaQueries`, which is the mechanism, not the policy. The reduced-motion floor (CDIO-07 sec.5) therefore belongs to CPP and is
never inherited from a library.

## Selection ladder (minimum sufficient dependency, stop at the first rung that satisfies the task)

1. No animation. Valid outcome; the only outcome when the contract says `expressiveness: none` or `motion_budget: none`.
2. CSS transitions / CSS scroll-driven animations (native, no dependency, free reduced-motion via media query).
3. WAAPI directly (cancelable, no dependency).
4. The motion library the project already depends on. Never add a second one for a task the first can do.
5. A new library, only when rungs 1-4 cannot express the task (springs, draggable physics, SVG morph, many-element timelines) and
   only per its modular import, recorded licence and exit path. Anime.js is a rung-5 candidate, never a default.

## Lifecycle contract (every motion implementation, any library)

- Cancelable and interruptible: route change, unmount, resize/orientation, repeated user actions leave a consistent final state.
- Listeners, observers, timers and draggables are released on unmount (a scope/revert owner exists).
- Responsive changes while running re-resolve, not stack.
- Offscreen work is paused; scroll-linked effects never capture navigation, reading, focus or input.
- Reduced motion is populated and exercised, with equivalent information and state change.
- Motion never raises the declared budget and never fabricates progress or success.

## Not universal

Library API names (`createTimeline`, `stagger`, `morphTo`, `createDraggable`, `createScope`) are upstream-only detail: use them only
once Anime.js is selected. Registered patterns: VP-AJS-001..003 in `vault/knowledge_base/visual-patterns/`.
