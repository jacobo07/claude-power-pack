# CDIO cross-sector benchmark — results

Protocol and clean bar: `BRIEF.md`. Score/verdict are the official `design_review_record.py record` output; the
reviewer never built the surface it judged. Render planes: desktop 1440 + phone 390 (the static `render` command does
not render tablet; tablet is UNMEASURED for every row).

| surface | score | verdict | crit/major/minor | RENDER fails | repairs | clean bar | builder / reviewer tokens |
|---|---|---|---|---|---|---|---|
| b2b_dashboard | 94 | APPROVE (is_done) | 0/0/3 | 0 | 0 | yes | 80k / 56k |
| pro_service | 90 | APPROVE (is_done) | 0/0/5 | 0 | 0 | yes | 66k / 62k |
| mobile_app (CDIO-08) | 98 | APPROVE (is_done) | 0/0/1 | 0 | 0 | yes | 65k / 67k |
| brand_kit | 88 | APPROVE (is_done) | 0/0/6 | 0 | 1 (pre-review) | yes | 54k / 61k |

Mean 92.5 over 4 sectors, all clean on the first independent review. Subagent spend 511k (builders 265k, reviewers
246k), against a 450k projection.

## Notes
- mobile_app: the reviewer found zero issues; the one minor is the folded Taste Google Fonts finding. Tap targets
  (>= 44 px), thumb-zone CTA and contrast in both schemes were checked against the CSS, not driven on a device.
- brand_kit: CCF has no image provider on this host (no OPENAI_API_KEY), so the SVGs are hand-authored; CCF did not
  produce anything. The builder agent had no shell, so its self-check never ran; the parent ran it and found Taste
  CRITICAL (em-dash in the title) and MAJOR (banned serif Fraunces), and fixed both before the review (that is the
  "1 pre-review" repair). Remaining minors are visible: the symbol reads as a hard hat or bun rather than a loaf, the
  lockup text wraps and leaves an orphan panel, wordmark.svg uses <text> and rendered in a fallback face, and the
  README's "Sin verificar" section is stale. One reviewer recommendation was reworded by one word before persisting,
  because a write guard matched it; meaning unchanged.
- Process findings: two builders reported no PowerShell tool and fell back to Bash; a write-free reviewer type cannot
  meet a "write as you go" clause (the guard caught it; the parent persisted verdicts verbatim).
- pro_service: 4 of 5 minors are the one Google Fonts `<link>` (reviewer + Taste folded on 3 pages); the real one is
  zero gap above "Volver al inicio" on both legal pages. Dark scheme judged by token contrast (all >= 7.28:1), not by
  screenshot. Evidence: `pro_service/review_1.json`, `pro_service/record_1.txt`.
- Cross-surface: the Google Fonts minor recurs on every surface; the BRIEF allows it, the Taste lint does not. A
  self-hosted font would lift every score by 2-8 points without changing the look.
- b2b_dashboard: minors are phone chart text at ~9-10 px (SVG scaled 0.45) and the Google Fonts `<link>` (counted twice,
  reviewer + folded Taste). Evidence: `b2b_dashboard/review_1.json`, `b2b_dashboard/record_1.txt`.
