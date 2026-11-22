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

## READ of the detector (epoch 4, 2026-11-21)
Pin b49177d3 (Apache-2.0; LICENSE 10766 B; NOTICE.md lists only third-party fonts, platform-skill text and consent rules, none of which we would take). The detector is a Rust workspace: `crates/detect` (cli.rs 65 KB, detect_text.rs 107 KB, design_system.rs 99 KB), a rule registry in `crates/foundation/src/registry.rs`, a 3.2 MB browser bundle and about 330 HTML/JSX/Vue fixtures. Read: `crates/live/assets/antipatterns.json` (sha256 ea61e3bb0ba5be71ddefa3ae25f67209cadb737031258f8c5eec5bcd99cba199) = 62 rules, 31 `slop` and 31 `quality`; header of `detect_text.rs` (a regex engine for CSS/JSX/Vue/Svelte, port of an .mjs engine) and `list_rules.rs`.

Decision: PRINCIPLES ONLY, no port. Reasons: a Rust+CDP+browser-bundle detector cannot be wired into our Python gates without a toolchain we do not run; porting 200+ KB of regex logic is not reviewable; and about a third of the slop ids already have an owner in `modules/cdio/taste.py` (gradient-text, em-dash, marquee, eyebrow/kicker, numbered-section, overused serif/font). Not ported, so NOTICE is not needed; if code is ever ported, keep Apache-2.0 LICENSE + NOTICE.

Net-new ideas worth a future row (named, not built): flat-type-hierarchy (heading/body ratio under 1.25x), nested-cards, icon-tile-stack, cream-palette, bounce-easing, pulsing-dot, tight-leading (<1.3), line-length (>~80ch), text-occlusion, and the split of every rule into `slop` (taste) vs `quality` (defect). The split itself is the transferable shape: it matches CDIO's score-vs-verdict separation. Rules marked advisory (em-dash) are advisory because humans use em-dashes; that is a false-positive note we already honour.

## Not done (BI-30 stays open)
- Detector rule list read (62 ids) but no rule's detection logic was run;  no identity-neutral detection strengthened; no valid-category-convention false-positive corpus built; no before/after measurement.
