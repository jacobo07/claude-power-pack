# Backlog — Absorb Anime.js into Claude Power Pack Design

**Created:** 2026-10-10 · **Priority:** P1 · **Source:** https://animejs.com/ · **Owner intent:** absorb the useful capability surface of Anime.js into Claude Power Pack Design so future visual work can inherit it without rediscovery.

## Mission

Perform a full evidence-first absorption of the current Anime.js design/motion capability into Claude Power Pack's existing design architecture.

This is **not** a request to blindly vendor Anime.js, add another motion subsystem, or turn every product into an Anime.js product.

The target is semantic and institutional absorption:

- everything Anime.js teaches that can improve future web motion, interaction, visual composition, SVG animation, responsive motion, scroll behaviour, draggable interaction, sequencing, easing, and implementation quality should become discoverable and reusable inside Claude Power Pack;
- existing CPP owners must be extended rather than duplicated;
- stack-specific implementation remains stack-specific;
- universal principles are promoted only at the narrowest scope supported by evidence;
- the result must reduce rediscovery cost for future design work.

## Current Anime.js capability surface to audit

The official site currently exposes, at minimum:

- Timer
- Animation
- Timeline
- Animatable
- Draggable
- Scope
- Scroll
- SVG
- Utils
- Easings
- WAAPI integration
- per-property parameters
- flexible keyframes
- enhanced/individual CSS transforms
- transform composition / blend behaviour
- function-based values
- Scroll Observer with multiple synchronisation modes, thresholds and callbacks
- advanced staggering across time, values and timeline positions
- SVG shape morphing
- SVG line drawing
- SVG motion paths
- spring-based interaction
- drag / snap / flick / throw interaction
- timeline sequencing and advanced time positions
- responsive motion through media-query-aware scopes
- modular imports / bundle-size-aware composition
- easing authoring / selection
- examples and learning material that may encode reusable motion patterns

Treat this list as the starting inventory, not as proof of completeness. Audit the current official docs, examples, GitHub source, version, licence, changelog, and any upstream behavioural contracts before absorption.

## Correct CPP ownership hypothesis

Reality Scan must decide final ownership. Initial hypothesis:

- **CDIO-07 Experience Contract** — motion intent, motion budget, reduced-motion equivalence, feedback timing, waiting/success/error behaviour.
- **visual-patterns knowledge base** — reusable motion and interaction patterns with applicability, exclusions, evidence level and “when NOT to use”.
- **CDIO motion pattern resolver** — automatic applicability/routing from DESIGN.md + surface kind.
- **CDICF / component capability routing** — where reusable implementation primitives/components are involved.
- **frontend/design lieutenant** — automatic surfacing when motion or animation work is requested.
- **design reference/template compiler** — when Anime.js examples reveal transferable whole-surface motion grammars.
- **performance/reliability owners** — frame budget, layout thrash, event/listener cleanup, resource lifecycle, bundle cost, scroll performance.
- **accessibility owners** — reduced motion, pause/stop controls, keyboard/touch parity, seizure/flashing constraints where applicable.
- **dependency/provenance owners** — upstream version, licence, source, update drift and dependency-exit plan.

Do not create a parallel “Anime Design OS” unless a Reality Scan proves an existing owner cannot represent a necessary capability.

## Required absorption method

For every upstream concept, classify it as one of:

1. **Already owned** — point to the existing canonical CPP owner; do not duplicate.
2. **Extend existing owner** — add only the missing semantic capability.
3. **Reusable visual/motion pattern** — register with applicability, exclusions, evidence and fallback.
4. **Implementation primitive** — keep stack/library-specific and route through the proper implementation owner.
5. **Convention / heuristic** — useful guidance, never a hard failing rule by itself.
6. **First-principle criterion** — may become a review/gate criterion only if it traces to an observable human/system constraint.
7. **Unverified** — record without promoting.
8. **Rejected** — record why it conflicts with stronger CPP doctrine or reality.
9. **Upstream-only detail** — useful when Anime.js is actually selected, not universal CPP knowledge.

The absorption is complete only when every meaningful upstream capability has one disposition.

## Important design questions to resolve

The audit must answer, with evidence:

- Which Anime.js primitives map cleanly to the existing CDIO-07 motion contract?
- Which existing CPP motion patterns are weaker than Anime.js's expressive or compositional capabilities?
- Which Anime.js behaviours should become new visual-pattern entries versus implementation recipes?
- Can stagger, timeline, scroll sync, SVG morph/draw/path, draggable physics and scope-aware motion be expressed as reusable design grammars independent of Anime.js?
- Which patterns are safe defaults, which require explicit opt-in, and which should be refused on trust-critical or accessibility-sensitive surfaces?
- How should the system select between CSS/native scroll animations, Motion, GSAP, Anime.js, WAAPI and no animation?
- What is the minimum sufficient dependency surface for a task?
- How do we prevent motion inflation and “animation because the library can do it”?
- How do we guarantee cleanup, interruption, cancellation, resize/reflow correctness, route-change lifecycle and responsive behaviour?
- How do we verify real browser behaviour rather than screenshots?
- How do we make a fresh agent discover the right Anime.js-derived pattern without loading the entire upstream corpus?

## Motion-quality invariants

Absorption must preserve or strengthen these laws:

- Motion must have a purpose.
- Absence of motion is a valid outcome.
- Motion budget may constrain expression but may not be silently raised by a recommendation engine.
- Reduced-motion users receive equivalent information and state change.
- Scroll-linked effects must not destroy navigation, reading, input, focus or browser expectations.
- Draggable interactions require non-drag alternatives where the action is essential.
- Animation must not hide real latency or fake progress.
- Timeline sequencing must preserve application state truth.
- SVG effects must not replace accessible semantic content.
- Performance regressions are design defects when caused by optional motion.
- No library-specific API becomes universal doctrine merely because the library supports it.

## Deterministic / adversarial verification targets

Build the narrowest useful verification supported by the architecture. Candidate scenarios include:

- reduced-motion branch is actually populated and exercised;
- timeline pause / resume / reverse / cancel semantics;
- interrupted navigation during an active animation;
- component unmount while timers/observers/draggables are active;
- resize and orientation changes;
- responsive scope/media-query changes while animation is running;
- scroll observer entering/leaving thresholds repeatedly;
- nested scroll containers;
- rapid repeated user actions;
- touch vs pointer vs keyboard parity;
- draggable snap/release edge cases;
- transform-composition conflicts;
- SVG path/morph incompatibility;
- hidden/offscreen animation work;
- zero-population false-green tests;
- stale animation state after remount;
- hydration/SSR boundaries where applicable;
- bundle-size regression from importing unnecessary Anime.js modules;
- production browser render under real app state.

Mutation or adversarial drills should prove that the relevant gates can go red.

## Design-system integration

The final capability must be reachable automatically from normal design work.

A future agent should be able to start from a task such as:

- animate this hero;
- create a scroll-driven product story;
- draw this SVG path;
- build a draggable interaction;
- choreograph these states;
- make this motion responsive;

and have CPP route it to the minimum sufficient applicable motion knowledge without the user needing to name Anime.js.

The route should consider:

- project DESIGN.md;
- CDIO-07 experience contract;
- surface type;
- aesthetic family;
- trust posture;
- motion budget;
- reduced-motion requirements;
- existing project stack and dependencies;
- browser/runtime constraints;
- existing motion library already in the project;
- proven reusable patterns.

## Upstream / dependency sovereignty

Before using Anime.js as a runtime dependency:

- verify the current upstream licence and exact version;
- record provenance;
- prefer existing project dependency when it already satisfies the need;
- avoid importing the entire package when modular imports are sufficient;
- define an exit/migration path for any baseline that depends on Anime.js-specific semantics;
- separate universal motion doctrine from library-specific adapters;
- add update/drift intelligence if the dependency becomes part of a reusable CPP capability.

## Knowledge and baseline ratchet

At close:

- write project-specific findings to the Knowledge Vault;
- distill only genuinely transferable Hard Rules, Process Rules and Traps into UKDL;
- update visual-pattern evidence levels;
- promote a baseline only where evidence reaches the required scope;
- do not universalise one-off demo effects;
- record rejected upstream rules so future absorptions do not re-argue them;
- ensure future design work can discover the result automatically.

## Done-gate

This backlog item is complete only when:

1. the full current Anime.js capability surface has been inventoried from authoritative upstream sources;
2. every meaningful capability has an explicit disposition;
3. overlap with CDIO, visual-patterns, CDICF, frontend lieutenant, accessibility, performance and reliability owners is mapped;
4. no duplicate motion subsystem is introduced without evidence;
5. useful missing capabilities are implemented or registered at the correct owner;
6. the applicable knowledge is automatically reachable during normal design work;
7. reduced-motion and production-browser behaviour are verified;
8. relevant adversarial/mutation tests demonstrate red capability;
9. upstream provenance/licence/version are recorded;
10. UKDL and Knowledge Vault are updated at the correct scope;
11. Constitutive Baseline Ratchet promotion is evaluated;
12. a fresh agent can use the absorbed capability without this conversation or a manual Anime.js lookup;
13. the next comparable motion/design task is measurably cheaper, more reliable, or more deterministic.

## First action when activated

Run a Reality Scan against the then-current CPP and Anime.js upstream. Produce a reuse/extend/build decision ledger before changing code. Do not begin by installing Anime.js.
