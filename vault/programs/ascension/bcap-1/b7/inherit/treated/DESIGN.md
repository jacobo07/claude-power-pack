---
experience:
  expressiveness: none
  feedback: native
  waiting: none
  reduced_motion: equivalent
---

# Minutehand landing page

Design Read: a calm, editorial pre-launch page for busy managers. It shows the product's output (a short owned to-do list) instead of describing it, using warm paper tones, one deep-green accent and the system font stack.

## Decisions
- Static preview. No backend, forms, payments or analytics exist, so the page promises none: the only call to action is "Compare plans" (scrolls to pricing), and plans state that signups open at launch instead of carrying buy buttons that go nowhere.
- Testimonials are visibly labelled as example quotes with role-only attribution. No invented names or companies are shown as real customers; the terms page repeats this.
- The sample output in the hero uses roles rather than personal names and is captioned as illustrative.
- Hero height follows its content; there are no full-viewport sections, scroll listeners or scroll cues.
- Motion: one 150 ms colour transition on the button hover, plus smooth anchor scrolling. Both are disabled under `prefers-reduced-motion: reduce`.

## Accessibility
- Skip link, landmark elements, one h1 per page, labelled sections.
- Body text 17px; text colours meet WCAG AA on their backgrounds (ink #1c1d1f and soft ink #4a4c50 on #f7f5f0; white on #1f5f4a).
- Visible focus outlines; tap targets at least 44px tall.
- Mobile-first layout: single column, switching to multi-column at 52rem.

## Legal
- `privacy.html` and `terms.html` are linked from the footer of every page.
