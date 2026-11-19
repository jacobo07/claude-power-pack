---
id: VP-NEG-MOTION-001
name: Motion Negative Examples
type: anti-pattern
domain: visual-patterns
status: active
---

# VP-NEG-MOTION-001 — Motion negative examples (BCAP-2 D21-E08)

Counterexamples, each tied to a CDIO-07 contract field and to the check in
`modules/cdicf/motion_select.py` that refuses it. CPP-authored; no third-party
content. Evidence level: reasoned from CDIO-07 and WCAG, not yet observed in a
rendered build (`live_verified` false).

## 1. Spring overrun on a destructive control
A delete or confirm-payment button that overshoots and settles. Overshoot moves
the hit target under a pointer already committed to a click. Contract: a
`trust_posture: critical` surface carries `expressiveness: none|restrained`;
bounded overshoot is only defensible where nothing irreversible hangs on it.

## 2. Unnecessary animation in a payments console
Entrance choreography on a ledger table. The contract is `restrained`, budget
`low`; the animation delays reading numbers and serves no purpose. `no_animation`
is a valid E05 decision and `expressiveness: none` is a passing contract.

## 3. Hover-only content
Information or actions revealed only on hover. Unreachable by touch and keyboard.
Every hover reveal needs a focus and tap path with identical content.

## 4. Drag action without keyboard alternative
A reorder or slider that only responds to pointer drag. A keyboard or button
equivalent must exist and reach the same state.

## 5. Broken focus after a transition
A route or panel transition unmounts the focused element, so focus resets to the
document body. Focus must be moved deliberately to the new context before the
transition is declared done.

## 6. Animated text that is inaccessible
Per-letter or split-text effects whose accessible name becomes a run of single
characters, or text that is unreadable mid-animation. The full string must be the
accessible name and the final state must be reachable under reduced motion.

## 7. Fake loading and progress illusion
A spinner or bar timed to look busy with no operation behind it. Refused by
`check_motion_semantics` (`fake_loading`, `progress_illusion` must be ruled out).

## Evidence
Pending first observed instance in a CPP build.
