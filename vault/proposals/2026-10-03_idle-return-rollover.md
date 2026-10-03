---
to: SPEC-ECON-ROLLOVER owner (vault/specs/economic-rollover-trigger.md, tools/rollover.py, modules/zero-crash/hooks/context-watchdog.py)
from: state-centric-cognition mission, step S6 (vault/plans/state-centric-cognition-reality-scan-2026-10-02.md)
kind: proposal -- no edit to the owner's files was made
date: 2026-10-03
status: OPEN (owner decides)
---

# Proposal -- idle-return rollover (A1)

## The measurement

`wiki/tools/token_economy_deep.py` over 7 days to 2026-10-02T20:48Z (finding F4,
`wiki/syntheses/token-economy-brainstorm.md`): 307 mid-session prefix rebuilds. In 224 of them
(73 %, about $541 API-equivalent, at most 6.5 % of the window) the session came back after more
than 1 h idle, so the prompt cache had expired. The first call after the gap rewrote the whole
context, about 300k at p50, at the cache-write price.

**Re-measured the same day** (`token_economy_deep.2026-10-03.out` [P], after removing
`<synthetic>` client rows that were being read as model switches): **252 idle rebuilds, ~$611.**
Part of this class is returns from a usage limit. 25 of the 43 synthetic rows found right before
a rebuild were limit notices. The Owner cannot shorten those waits. Once the notice appears, no model call can run, so `/kclear`
cannot seal at that point. A warm seal would have to come earlier, from the usage meter nearing
the limit. That is unchecked: it needs the meter to be readable from a hook.

## A correction to how the idea was first written

The brainstorm says "the cache is already cold, so a fresh epoch is free." Measured against the
shipped code, that is wrong.

- A capsule is SAFE_TO_FORGET only if it carries a handoff written by the same session and less
  than `HANDOFF_MAX_AGE_S` = 30 min old (`tools/rollover.py:403`). A capsule sealed before a gap
  longer than 1 h always fails that check.
- So after the gap, `/kclear` needs one model turn over the full context. That turn is the cold
  rewrite F4 measured. It is paid whether the session continues or rolls over.
- With the rule as it is, idle-return therefore adds nothing that `decide()` does not already
  price. The rewrite is sunk on both sides. Rolling over also costs a new floor write (about
  126k), and it is repaid only by the cheaper reads in later turns. This is the same break-even
  `decide()` already computes on measured remaining-work evidence (ccp-s16 D1a/D1b, `7fefbc46`,
  `4bc970d6`).

**No idle trigger is needed to capture the "later reads" part.** Firing `decide()` on the first
Stop after an idle return would be a cardinality change only. It is worth doing only if the
replay shows that sessions resumed after idle have a different remaining-work prior.

## What would actually save the $541: a decision only the owner can make

The rewrite is avoided only if no model call happens on the old context after the gap. That
means a `UserPromptSubmit` hook that sees a gap of 1 h or more, used context above floor plus
margin, and an ordinary session (no mission marker). It then blocks the prompt before any call
and routes to `/clear` -> `/kresume` from a capsule compiled **without** a fresh handoff:

- obligations from the goal file. This already works: `compile_capsule` falls back to it at
  `rollover.py:351-352`;
- refresh against the tree (RECOMPILE when the tree moved, unchanged);
- the resume exam unchanged.

The cost is a weaker quality authority. The successor loses whatever the model knew and had not
written to the goal file or a commit. **That is a change to SAFE_TO_FORGET (spec Behaviour 4),
which is why it is a proposal and not a patch.** Suggested bounds if the owner wants it:

1. Allow it only when the last `/kclear` handoff of this session exists, even if stale, AND the
   goal file was written after that handoff or the session made no writes since. Otherwise use
   the current path.
2. Ask, never auto-clear. The prompt is blocked with one line, and the Owner chooses between
   rolling over and continuing. A blocked prompt costs nothing; a wrong forget costs the work.
3. Kill switch `CPP_ROLLOVER_IDLE=0`. Ledger row `rollover_idle_offered` with gap_s, used_pct
   and the choice made, so the $ bound can be re-measured against what was actually accepted.

## Acceptance, if adopted

- gap >= 1 h, above floor, ordinary session, eligible capsule -> prompt blocked with the offer.
  Control: the same inputs with gap < 1 h -> no block.
- mission worker, below floor, kill switch, no prior handoff -> no block, each paired with the
  firing control.
- A drill that removes the gap check must go red. A drill that lets an ineligible capsule through
  must go red.
- Production Reality: count `rollover_idle_offered` rows and accepted rows, then re-run
  `token_economy_deep.py` F4 a week later. The idle-rebuild $ must fall by roughly the accepted
  share. If it does not, the hook fired on the wrong call.

## What I have not checked

- Whether a `UserPromptSubmit` block happens before the harness sends anything to the model. It
  must, or nothing is saved. Check with one idle session's transcript (no assistant usage row
  between the blocked prompt and `/clear`).
- Whether the 224 rebuilds come from resumable sessions (goal file present) or from
  conversational sessions with no goal. Only the first kind is eligible. `token_economy_deep.py`
  can split the 224 by whether a capsule-able goal existed.
