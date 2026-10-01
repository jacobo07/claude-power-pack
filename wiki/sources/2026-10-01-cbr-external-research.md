---
type: source
created: 2026-10-01
updated: 2026-10-01
sources: [2026-10-01-cbr-external-research]
raw: raw/2026-10-01-cbr-external-research.md
kind: note
origin: web research subagent, 2026-10-01, ~33 sources (15 opened, rest search snippets, each marked)
---

# What makes a baseline ratchet work (external research, 2026-10-01)

Evidence-graded benchmark (tiers A/B/C) for a CBR-like mechanism. It covers ratchets in code
quality, golden paths and scorecards, template update flows, fitness functions, checklist research,
lessons-learned systems, context injection into coding agents, family classification, and how to
measure lift. It ends in a 32-item checklist. Feeds [[cbr-gap-analysis]]. Companion to
[[2026-10-01-sdd-external-research]], which covers context files (C2).

## Takeaways that carry the synthesis

- **Placement beats content.** Infer: 70% fix rate at diff time vs 0% in batch for the same
  analysis (CACM 2019; snippet-verified).
- **Compliance is not the outcome.**
  - OpenSSF: higher Scorecard scores went with more reported vulnerabilities, R² 9-12% (verified).
  - The Ontario mandated surgical checklist showed no significant mortality change (tier A,
    snippet).
- **Checklists to defaults.** Google moved per-service readiness reviews into frameworks new
  services inherit (tier B, opened).
- **Auto-admitted memory propagates errors** (arXiv 2505.16067; verified for "experience-following"
  and "error propagation"; the "gated beats accumulate-all" claim is weaker than stated).
- **Context injection.**
  - Rule updates raised compliance on the targeted behaviour from 49% to 72% (arXiv 2606.12231).
  - Compliance falls with instruction count (IFScale).
  - Agents rarely fetch rules on their own (arXiv 2607.26819).
- **Lift needs a counterfactual.** METR: developers felt about 20% faster and were measured 19%
  slower.

## Caveats

- 18 of ~33 sources are snippet-only. Two popular figures had no traceable primary source and are
  excluded: ADR "<5 records", postmortem "<40% closed in 90 days".
- No study measures rule injection across projects of a family, the exact CBR claim (open question 1).
