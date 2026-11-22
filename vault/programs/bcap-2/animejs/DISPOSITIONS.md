# BCAP-2 Phase 4 — Anime.js dispositions

Upstream pin: juliangarnier/anime @ 01b81be1df6843ccfe0a71c0699a746bf740dd77 (v4.5.0, MIT). Campaign B (Phase 1) read the three formerly UNVERIFIED rows at the same pin (no UNVERIFIED row remains). Basis: READ = upstream `src/` dir or file listed
was read this phase. Vocabulary: ALREADY OWNED, EXTEND (new registered pattern/doctrine at the owner), IMPL-PRIMITIVE (library-specific, stays
upstream-only until selected), HEURISTIC, UPSTREAM-ONLY, REJECT, UNVERIFIED. Machine-checked by `tools/test_bcap2_animejs.py`.

| capability | upstream path | disposition | cpp owner | note |
|---|---|---|---|---|
| Animation (per-property params, keyframes, function values) | src/animation | IMPL-PRIMITIVE | modules/cdio/motion_patterns.py | API detail; contract decides whether motion may exist |
| Timer | src/timer | UPSTREAM-ONLY | vault/knowledge_base/visual-patterns/motion-library-selection.md | clock primitive, no design meaning |
| Timeline + time positions | src/timeline | EXTEND | vault/knowledge_base/visual-patterns/staggered-timeline-choreography.md | VP-AJS-001 |
| Stagger | src/timeline/stagger.js | EXTEND | vault/knowledge_base/visual-patterns/staggered-timeline-choreography.md | VP-AJS-001 |
| Animatable (follow-cursor) | src/animatable | IMPL-PRIMITIVE | modules/cdio/motion_patterns.py | READ campaign B: src/animatable/animatable.js:1-161 (per-property setters, pause/begin handlers), examples/animatable-follow-cursor/index.js:30-35 drives it from `window.onpointermove` only: no keyboard path, no reduced-motion branch (grep over src+examples = 0 hits). Any CPP pattern must carry a keyboard equivalent per CDIO-07 floors; not promoted |
| Draggable (snap, flick, throw) | src/draggable | EXTEND | vault/knowledge_base/visual-patterns/draggable-snap-with-alternative.md | VP-AJS-002; non-drag alternative mandatory |
| Scope (mediaQueries, revert) | src/scope | EXTEND | vault/knowledge_base/visual-patterns/motion-library-selection.md | lifecycle contract; mechanism not policy |
| Scroll observer (sync modes, thresholds) | src/events/scroll.js | ALREADY OWNED | vault/knowledge_base/visual-patterns/scroll-driven-reveal.md | + scroll-overflow-fade; CDIO-13 lifecycle covers capture rules |
| SVG line drawing | src/svg/drawable.js | ALREADY OWNED | vault/knowledge_base/visual-patterns/self-drawing-stroke.md | VP-024 |
| SVG morph | src/svg/morphto.js | EXTEND | vault/knowledge_base/visual-patterns/svg-shape-morph.md | VP-AJS-003 |
| SVG motion path | src/svg/motionpath.js | IMPL-PRIMITIVE | modules/cdio/motion_patterns.py | READ campaign B: src/svg/motionpath.js:1-88 createMotionPath returns translateX/translateY/rotate function values from getPointAtLength + getCTM (:47-73). Needs a real SVG DOM to observe, so a CPP pattern would be browser-plane (LAPTOP); not promoted |
| Text split / scramble | src/text | ALREADY OWNED | vault/knowledge_base/visual-patterns/scramble-text-reveal.md | split detail upstream-only |
| Springs / irregular / steps / cubic-bezier easings | src/easings | HEURISTIC | vault/knowledge_base/visual-patterns/motion-library-selection.md | easing choice is guidance, never a failing rule |
| Layout (auto-layout transitions) | src/layout | ALREADY OWNED | vault/knowledge_base/visual-patterns/shared-element-continuity.md | shared-element continuity |
| WAAPI integration | src/waapi | EXTEND | vault/knowledge_base/visual-patterns/motion-library-selection.md | selection ladder rung 3 |
| Engine / additive composition / transforms | src/engine | IMPL-PRIMITIVE | vault/knowledge_base/visual-patterns/motion-library-selection.md | transform-composition conflicts are an implementation check |
| Adapters (three.js) | src/adapters | REJECT | modules/cdio/motion_patterns.py | WebGL scene work is outside the CDIO surface contract |
| Utils | src/utils | UPSTREAM-ONLY | vault/knowledge_base/visual-patterns/motion-library-selection.md | helpers |
| Modular imports / bundle size | package.json exports | EXTEND | vault/knowledge_base/visual-patterns/motion-library-selection.md | ladder rung 5 requires modular import |
| Reduced-motion handling | (absent in src) | EXTEND | vault/knowledge_base/cdio/CDIO-07-experience-contract.md | upstream has none; CPP floor stays CRITICAL |
| Examples (26 entries) | examples/ | UPSTREAM-ONLY | modules/cdio/motion_patterns.py | READ campaign B: 25 dirs + tsconfig.json; 21 index.js scanned for API use (animate, createTimeline, createDraggable, createAnimatable, onScroll, svg.createDrawable/morphTo): all map to rows above; none reads prefers-reduced-motion. Demos, not patterns; none promoted |
