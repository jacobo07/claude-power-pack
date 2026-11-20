# BI-30 Impeccable anti-generic transfer audit (read-only, partial)

Source: github.com/pbakaus/impeccable @ b49177d32788f2dc585c42831d845dacf1ebed2c (main, not archived, Apache-2.0 via GitHub SPDX; LICENSE 10766 B, NOTICE.md present in tree).
Fetched read-only 2026-11-20: `.agent/skills/impeccable/reference/critique-rubric.md` sha256 ba070404e3f61c62b40c25a5d096b803825408de12a0fbb559b1587c89692866; `critique.md` sha256 fe32f927dcd3e1bff056b8ff5e37feeec1ae0a67983f4ed9864dfb24cdde4cd8.

## Findings (what was actually read)
1. critique-rubric.md is a UX rubric (cognitive load, Nielsen 10 heuristics, five personas). It carries no logo or symbol rule and no category-convention ban.
2. critique.md leads with a "Design Specificity Verdict": does the result feel authored for this product or category-interchangeable. It is an unanchored LLM judgement paired with a deterministic detector scan, and the detector itself was NOT read or run.
3. CDIO-06 already owns the anti-slop kit (section 4) and the rule that a default without declared intent is slop; its APPROVE means "no slop detected in the declared system".

## Transfer decision (reasoned, not measured)
- The one idea worth porting is the two-part shape: a deterministic scan plus a separately reported LLM judgement, each stated apart, with detector false positives flagged. CDIO-05/06 already separate deterministic score from agent verdict, so the net new value is small.
- Do NOT port the detector or the P0-P3 scheme: detector source unread, so rights and behaviour are unassessed. Reference only; no code admitted.
- Symbol distinctiveness (does the mark resemble known marks) is a different question from UI logo-swap behaviour (can the brand mark be replaced with another brand and the page still read the same). Keep them as two separate fields; the swap test belongs to the UI surface (governance/DESIGN_GOVERNANCE.md VQ-6), the symbol test belongs to BI-29 similarity screening.

## Not done (BI-30 stays open)
- Impeccable detector rules not read; no identity-neutral detection strengthened; no valid-category-convention false-positive corpus built; no before/after measurement.
