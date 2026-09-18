---
name: mobile-app-ui-design
description: Design mobile app screens, flows and components that hold up under a CDIO review — onboarding, home and dashboard screens, search, status tracking, settings, navigation, as HTML/React prototypes or React Native / Flutter / SwiftUI-style mockups. Use when someone asks to design an app screen, make app mockups, build mobile UI components, improve an existing app screen ("make this screen look better"), design an onboarding flow or mobile navigation, or says "design an app". Do not wait to be named. Generates; the verdict belongs to cdio-reviewer against CDIO-08.
origin: github.com/ceorkm/mobile-app-ui-design (README declares MIT), absorbed into Claude Power Pack 2026-09-18 and rewritten to CDIO doctrine; what was kept, changed and rejected is classified in vault/knowledge_base/cdio/CDIO-08-mobile-app-surface.md
---

# Mobile App UI Design

You build app screens meant for a phone held in one hand. You do not grade them:
`cdio-reviewer` does, with the deterministic scorer, against CDIO-00 to CDIO-08.
Your job is to hand it a screen that has already been built to pass.

Knowledge base, read the parts you need before building:

- `vault/knowledge_base/cdio/CDIO-08-mobile-app-surface.md` — the criteria this
  screen will be judged on (§3), the industry conventions (§5), and the list of
  advice that was **rejected** (§7). Read §7 first; it is the list of things you
  will be tempted to do.
- `CDIO-06` — pick one aesthetic family before any token.
- `CDIO-07` — declare the experience contract before the first interactive
  component. Peak-End (§11) tells you where that contract spends itself.
- `CDIO-01` / `CDIO-03 §7` — type, colour, spacing thresholds; state design.

## Before you design, answer three questions

1. What is the user trying to finish on this screen? Everything else is weight.
2. How should it feel — calm, confident, playful, safe? That answer is the CDIO-07
   contract, and on anything involving money or health it is `trust_posture`
   first.
3. What is the one thing they notice first? If you cannot name one, the screen has
   no hierarchy yet.

## The process (five steps, in order)

**1. Context.** App category, user stage (first run, returning, power user), the
primary action, and the category's conventions (CDIO-08 §5). Conventions explain
a choice; they are not rules, and breaking one needs a reason you can state.

**2. Structure before style.** Map the screen before and after this one. Keep only
what this screen needs. Put the primary action in reach of the thumb — lower third
or docked to the bottom. Expose content instead of hiding it behind extra taps.
Give every empty state guidance and a next action. Choose input by use: chips for
a small known set (with "Other"), a numeric field for exact or frequent values, a
slider only for a coarse value set once. A bottom tab bar holds three to five
destinations.

**3. Visual system.**
- One type family, two at most for a stated reason. At most three competing type
  levels in view; a caption can be a fourth size. Numbers that change or align use
  **tabular figures**. The value is bigger than its label.
- Colour: start from roughly 60 neutral / 30 complementary / 10 accent, then check
  what actually matters — the accent marks things you can tap or that carry
  meaning, and every opacity step of text still clears 4.5:1 after blending.
- Spacing on the 8-point grid. Related items close; the gap between groups about
  double the gap inside them. Phone sections do not take 80–96px of padding.
- Shadows soft; on a coloured surface, tinted toward its hue.
- People are shown as photos before initials before generic icons. Imagery keeps
  one style across the app.

**4. The emotional arc, inside the contract.** Find the one step that closes real
effort and spend whatever acknowledgement the declared `celebration_policy`
allows there — nowhere else. Give the flow an ending that names what was done.
Remove negative peaks first: waits get the declared `waiting` treatment, errors
explain and offer recovery. No confetti on money that has not settled.

**5. Every state.** Empty, loading, error, success, and first run versus returning
where both exist. Tap targets 44×44 at least (48dp on Android). Test at 320 wide,
not only 375.

## Patterns worth reaching for

- **Search** never opens blank: recent, popular or suggested items below the field.
- **Status tracking** is a visual timeline with the current step marked, opened by
  one confident sentence ("Arriving by 14:30"), humanised with a name or photo and
  a quick action.
- **Category screens**: colour-coded tiles on soft backgrounds with clean isolated
  images, one consistent treatment across all of them.
- **Selection over typing**: tappable options with an icon or emoji, "Other" as the
  escape.

## Do not

- Add glow, backdrop blur or gradients as default polish. They are a family choice
  (CDIO-06 F5/F7), not finish.
- Make celebration the default success state.
- Put a label above its value at a larger size ("Sales" over "591").
- Use a slider for an amount the user must get exactly right.
- Put the primary action at the top of a screen whose job is that action.
- Use pure grey or black shadows on a saturated background.

## Implementation

For HTML or React prototypes: CSS variables for the colour and type tokens, one
icon set used everywhere, CSS transitions for state changes that respect
`prefers-reduced-motion`, rounded cards if the chosen family calls for them. The
toolchain is yours to choose; CDIO judges the rendered screen, not the library.

## Done

The screen is done when `cdio-reviewer` returns APPROVE (score ≥ 80, zero
critical) including the CDIO-08 criteria, and the CDIO-07 floors hold. A screen
you think looks right is not a verdict.
