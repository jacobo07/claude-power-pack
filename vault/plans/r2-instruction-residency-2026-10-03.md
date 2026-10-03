---
id: PLAN-R2-RESIDENCY
title: R2 instruction residency -- two-sided delivery proof before more rules leave the prefix
status: approved (Owner "y" 2026-10-03, six Q&A defaults: <=40 subscription sessions; commit card
  only if judged delivery fails; Move 6 floor = SPLIT; no push; no CLAUDE.md; backups kept until R3)
parent: vault/plans/cognitive-control-plane-2026-10-02.md §14; P3 REPORT.md §R2 + Move 4
---

# R2 instruction residency (2026-10-03)

## Reality (scan, read-only)
HEAD `cec43401` on feature/knowledge-acquisition, 20 ahead / 0 behind origin; `d50cb079`, `31e1e25c`
local only. 771 dirty paths, live peers committing (ACV, rollover). Auto mode OFF.
Move 4: backup sha256 0c86aa17 matches; repo == live SKILL.md (b1eda762); pointer 914 B.
Remaining: technical-failure-to-product-state 6,932 B, scoped-side-effect-authority 6,602 B (mtime
09-28, no peer touching). Measured first call: arm A 116,069-116,185 (R2 rules resident), after
Move 4 113,640-114,093.

Delivery evidence, real sessions since 2026-09-29 (779 transcripts with tool use, tool_use blocks
only): the 9 moved rule-skills were invoked 14 times in total; 5 of 9 never. The destructive card
(event delivery, `hooks/destructive_doctrine_card.js`) denied-with-card 86 times in 17,177 shell
judgements over the same period. Model-judged paging rarely fires; event paging does.
Move 4 natural sample: 9 sessions started after the move, 0 ran `git commit` (n=0, not evidence).
No UKDL entry yet for "negative ablation != delivery" or "listing text counted as activation".
No deterministic owner exists for TFPS or SSEA semantics: both govern code the agent WRITES in
product repos. The agent's OWN side effects are enforced elsewhere (permissions, cascade_check_bash,
secret firewall, destructive card) and do not depend on either rule's residency.

## Classification
- Move 4 (CWST): NEGATIVE-ABLATION PROVEN ONLY (experimental). Natural event exists: `git commit`.
- TFPS: conditional design doctrine (UI/client failure handling). Mixed: ~4-line invariant + procedure.
- SSEA: conditional design doctrine with an authority core; the core must stay resident.

## Representation decisions (proposed)
- CWST: PAGED + EVENT CARD if model-judged delivery fails on the positive control; else PAGED.
- TFPS: SPLIT -- resident invariant in the pointer, body byte-identical in the skill.
- SSEA: SPLIT with a stronger resident invariant; KEEP RESIDENT if the invariant alone fails N-screen.

## Method per rule
N-screen first (rule absent, Skill disallowed, 2 runs) on a harder natural positive task. N passes ->
no discriminative power, record, no R/P spend. N fails -> R (rule appended) and P (current prefix,
Skill allowed) x2. Pass = R passes, P passes AND a Skill tool_use or card ledger row precedes the
protected action. Negative control = existing R2 tasks under P (already 4/4 for CWST).

Full inline plan: chat message of this date (Owner approval pending).
