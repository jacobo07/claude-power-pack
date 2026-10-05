# Cognitive Economy generation 2 (TOK-18 v2) -- compiled mission card

Approved by the Owner 2026-10-05 ("y"). Workers read this card and their own work unit. They do not read the
source brief (`vault/plans/cognitive-microkernel-brief-2026-10-04.md`, 89 KB, cold) unless a work unit names a
section of it.

## Invariants
- Generation 1 (`../CLOSE.md`, 20/20 terminals) is sealed history. Its measured rejections stand: F 1.88 %,
  K 2.67 %, P 0.50 %, C-tools 0.002 %, D <= 0.19 %. Do not re-measure or build them without a reopen trigger.
- Connect, never duplicate: capsule-v2 (continuation), zero-rescan plan, skill-capability, incremental-cognition,
  Goal spine, usage_index, fanout_ledger / estate_shadow, CBR (pp-cbr-wt), UKDL.
- No saving without a realized measurement. Upper bound != saving. UNKNOWN stays UNKNOWN.
- No percentage of the weekly limit (no reliable mapping).
- Never stop, rearm or edit another pane's mission. Commits are pathspec-only.

## Budget
Authorization boundary 150M processed tokens for W1-W9+R (E1 is separately authorized). Pre-launch estimate
low 40M / central 78M / high 150M. Crossing the boundary = one Owner question.

## Owner boundaries
- Tier 3+ (W5 onward) not before 2026-10-11T18:00Z.
- capsule-v2 T8 HELD by the Owner (W6).
- No push without the Owner.

## Work units (state lives in `ledger.json`, not here)
W1 compile mission (this card, ledger, gate) - W2 GEX44 supervisor diagnosis (E1 stuck replace; held mission
relays) - W3 E1 floor (authorized) - W4 offline replay over usage_index - W5 envelope canary champion/challenger
on a real backlog task - W6 zero-transcript proof (HELD) - W7 conditional primitives - W8 self-hosting pass -
W9 UKDL/CBR + close - R independent review.

## Done-gate
`python tools/test_cognitive_economy_program.py --generation 2 --final`
