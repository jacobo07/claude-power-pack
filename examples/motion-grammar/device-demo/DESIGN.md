---
version: alpha
name: Fieldnote
description: Warm editorial research-notes product; one device demo in the onboarding hero, calm everywhere else
aesthetic_family: F3   # Warm Editorial -- a prosumer writing tool, type-led
required_wcag: AA
bundle_budget_kb: 40
unresolved_ux_findings:
# CDIO-07 contract, reached with prompts/experience-picker.md:
#  Q1 cost of a mistake: recoverable (marketing/onboarding page) -> continue
#  Q2 habit or task: arrives with a question ("what is this?") -> confirm
#  Q3 the interface IS the product being shown -> moderate is defensible,
#     every floor in CDIO-07 sec.5 still applies (reduced_motion: equivalent).
experience:
  expressiveness: moderate
  motion_budget: medium
  reduced_motion: equivalent
  feedback_latency_ms: 100
  progress_threshold_ms: 1000
  waiting: none
  progress_language: none
  success_posture: confirm
  error_posture: explain_and_recover
  celebration_policy: never
  character_policy: none
  trust_posture: standard
colors:
  primary: "#191817"
  secondary: "#6b665f"
  accent: "#b4532f"
  neutral: "#f4f3ee"
  surface: "#fffdf9"
  on-surface: "#191817"
  error: "#a33a28"
typography:
  h1:
    fontFamily: Instrument Serif
    fontSize: 52px
    fontWeight: 400
    lineHeight: 1.05
  body-md:
    fontFamily: Work Sans
    fontSize: 17px
    fontWeight: 400
    lineHeight: 1.6
motion:
  transition-ms: 180        # state swap (VP-016); REF-MOTION-001 observed ~100-250
  build-gap-ms: 420         # between built lines (VP-017); >= one short line's reading time
  shared-ms: 260            # shared-element continuity (VP-018)
  hold-ms: 2600             # default dwell per state; transition:hold ~1:14
---

# Fieldnote — design system

A transfer target for the REF-MOTION-001 grammar, deliberately NOT the source's
domain: the source demoed a fitness app; this demos a research-notes app. The
grammar that transfers is structural (stable shell, rotating proof, built
state, shared element); nothing about fitness, colours or bezel carries over.

Motion tokens above are the only timing values the page may use. The page
names which pattern each behaviour implements with `data-pattern`, and
`tools/test_motion_grammar.py` checks every named pattern was one the CDIO
hook actually returned for this surface.
