---
title: UKDL candidates -- motion grammar from a reference video, and the CDIO hook defects it exposed
date: 2026-09-30
status: CANDIDATES -- NOT promoted into ukdl-universal.md (another writer held that file uncommitted
  for this whole session; per concurrent-writers doctrine a new file cannot be swallowed). The Owner,
  or the next session that finds ukdl-universal.md clean, lifts these entries verbatim.
evidence: vault/knowledge_base/visual-patterns/evidence/REF-MOTION-001/OBSERVATION.md;
  tools/test_motion_grammar.py (V-MGRAM-*); hooks/cdio_visual_advisory.js; this session's commits
---

# 1. Ownership sweep (before drafting)

ukdl-universal.md searched for cold start, fail-open silence, throttle keys, truncation, motion,
corpus reachability. Owned already, cited not re-drafted:
- `PR-COLD-START-IS-A-BUDGET-NOT-A-CEILING-001` owns "a timeout sized to the warm path is blind to
  the cold one". The CDIO hook's 6000 ms budget is another instance: gate work 0.7 s, interpreter
  start 0.4-5.9 s on a RAM-starved host, full run 9.2 s.
- Memory `feedback_hook_fanout_disables_the_antihang_guards` owns "timeouts fail open". What it does
  not say is how an ADVISORY gate should fail open -- that is T-CAND-2 below.
- `documented-capability-must-be-executable` (rule) owns "a documented capability nobody executes".
  PR-CAND-1 is its motion-corpus instance, recorded because the fix shape (contract-aware
  retrieval at the write hook) is reusable.

# 2. Hard-rule candidate

## HR-CAND-AUTOADVANCE-SHIPS-PAUSE-AND-REDUCED-EQUIVALENT
Content that advances on its own (carousel, device demo, rotating proof) ships a visible,
keyboard-operable pause, stops when hidden or off screen, and under reduced motion does not
autoplay while every state stays reachable by a non-motion control. Evidence: the reference that
seeded VP-016 had no pause control (WCAG 2.2.2 failure); copying it literally would have shipped the
defect. Floor-class (CDIO-07 sec.5 non-arbitrable), so it is also the strongest entry in
`BASELINE_CANDIDATES.json`. #CROSS-PROJECT

# 3. Process-rule candidates

## PR-CAND-1-PATTERN-KNOWLEDGE-IS-RETRIEVED-AT-THE-DECISION
A pattern corpus is institutional capability only if the path that makes the decision reads it,
filtered by the project's declared contract. Keyword search after an opt-in refresh is not that
path: it served the same ambient-grain texture to a payments console and to a hero. Fix shape:
discover entries (never enrol), resolve against contract + surface kind at the write hook, inject
one line (ids or `abstain`), and prove it at the real node->python boundary in both directions.
`modules/cdio/motion_patterns.py`, `V-MGRAM-HOOK-POSITIVE/-NEGATIVE`.

## PR-CAND-2-A-PREDICATE-VARIES-ONLY-THE-FACTOR-IT-NAMES
A check named for one factor must hold every other factor fixed, or another factor can decide it.
`pred_discriminates` (restrained dashboard -> only VP-018) was green on a resolver that ignored the
contract entirely, because on a dashboard the SURFACE excluded every other pattern. Caught only by
the ignores-floors mutant; fixed by `pred_contract_discriminates` (same surface, two contracts).
Run each semantic predicate against a mutant that removes exactly the factor it names.

## PR-CAND-3-A-PERFORMANCE-GATE-OBSERVES-ONLY-THE-SUBJECT'S-WINDOW
"The motion causes no long tasks" was first measured over the whole page life and failed on 2
tasks. Attribution across 4 runs (with and without screenshots): every long task started before
`loadEventEnd` -- parse and first paint -- and none fell inside a cycle. The aperture, not the
subject, was wrong. Bound the observation to the subject's window, and report what fell outside
it rather than dropping it (`V-MGRAM-PR-NO-LONG-TASKS`).

## PR-CAND-4-REFERENCE-VIDEO-DECOMPOSITION
Decode every frame; measure change per REGION, not per frame; read state boundaries from a crop of
the subject; label each claim OBSERVED / INFERRED / HYPOTHESIZED / UNKNOWN; hash the source. Record
what the capture cannot resolve (easing, loop) as UNKNOWN instead of estimating it. The reusable
tools are `evidence/REF-MOTION-001/decompose.py` and `crop.py`.

# 4. Trap candidates

## T-CAND-1-HANDHELD-CAPTURE-MEASURES-THE-CAMERA
A social video of a screen is often a phone filming a laptop. Whole-frame difference then measures
camera shake and the presenter's hand: the three largest spikes in REF-MOTION-001 were the hand
crossing the device, not app transitions, and the variance map was bright everywhere. Transition
timing from such a capture is +/-1 frame at best and easing is unrecoverable.

## T-CAND-2-FAIL-OPEN-THAT-IS-ALSO-FAIL-SILENT
An advisory gate that fails open by returning nothing makes "gate ran, nothing to say" and "gate
never finished" the same observable -- an unchecked write reads as a checked one. The CDIO hook's
timeout returned `{}`; on a loaded host that silently disabled the whole design gate, BLOCKs
included. Fail open, but SAY so: `adviseUnevaluated` names the cause and the command to run.
Drilled with a real interpreter that cannot run the gate (`V-MGRAM-HOOK-UNEVALUATED-VISIBLE`).

## T-CAND-3-A-TRUNCATED-PATH-KEY-IS-ITS-PREFIX
Sanitising a path and slicing it to N characters keeps only its prefix, so every path sharing the
first N characters shares the key. The CDIO throttle used `.slice(0, 32)`: every project under the
user's home shared one 15-minute advisory slot. Showed up only as a test that failed on its SECOND
run within the window. Hash the full key. Drilled against an isolated copy of the old line
(`[true,false]` -> fixed `[true,true]`), `V-MGRAM-HOOK-THROTTLE-PER-PROJECT`.

## T-CAND-4-A-TEST-THAT-PASSES-ONLY-WHEN-THE-GATE-DOES-NOT-RUN
`tools/test_design_hook.js` V-HOOK-BOUNDARY asserts an inner repo is never judged against its outer
repo's DESIGN.md, while `findDesignMd` has deliberately promoted to the enclosing repo since
2026-09-13 (TUA-X fix). The test was green whenever the gate timed out and red whenever it
finished. OPEN: which intent wins is an Owner decision; neither side was changed this session.

## T-CAND-6-A-MOTION-SUITE-IS-BLIND-TO-THE-STATIC-FRAME
44 of 44 motion gates (order, dwell, build, composited properties, reduced motion,
keyboard, responsive) were green on a page whose brand eyebrow was 4.48:1 on its ground --
below AA. Every lane observed behaviour; none observed the pixels at rest. The rendered
CDIO-05 review (cdio-reviewer, score 75, BLOCK) was the only instrument whose plane
included it. Motion work is judged on BOTH planes: the behaviour suite AND the rendered
review, and the suite now carries a rendered text-contrast check with a positive control
that restores the old token and must go red (`V-MGRAM-PR-TEXT-CONTRAST`, `-CONTRAST-CONTROL`).
Instance of `validation-planes-do-not-transfer`; recorded because the blindness is
specific and likely: a motion task invites a motion-only suite.

## T-CAND-5-A-SENTINEL-ANSWER-SATISFIES-A-NEGATIVE-CHECK
"Context is non-empty and names no motion pattern" is satisfied by a timeout message. Every check
that asserts an absence must first assert the instrument ran (`ran(ctx)` in lane E). Caught by
reading the check back, before it ever produced a false pass.
