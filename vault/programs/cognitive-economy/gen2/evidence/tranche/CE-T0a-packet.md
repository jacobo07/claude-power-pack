done_gate: python tools/test_self_spend_attribution.py

# CE-T0a -- spend attribution truth (gen2 completion, tranche T0, EXECUTION)

Contract: `vault/programs/cognitive-economy/gen2/COMPLETION-PLAN.md` (read only its "Verified reality" and "Economics"
sections). Fresh worker, no parent transcript. Do NOT spawn agents. Do NOT edit ~/.claude config. One Write per new file.

## Problem (observed 2026-10-07, not yet explained)
`python vault/programs/cognitive-economy/gen2/evidence/stage0/self_spend.py --session 71ccfa86-6902-4449-a345-dacb4b1ba2de`
printed `files 9 calls 411 processed 83,894,371 (ctx 83,722,227 out 172,144) subagent calls 284 subagent ctx
47,843,339`. That session spawned NO Agent and made well under 150 tool calls. Every envelope in this program is priced
from this meter (tranche_driver.spend uses it), so a wrong attribution corrupts every cap.

## Do
1. Find, by reading `self_spend.py` and the files it globs for that sid under `~/.claude/projects/` (list names, sizes,
   first-record sessionId/isSidechain/parent fields only -- never print message content), exactly which files it
   counts and why. Classify each counted file: this session's main transcript / its own subagents / another session's
   transcript (e.g. a pre-/clear session, a hook-spawned `claude -p`, a resumed parent) / other.
2. If it over-attributes, fix it in `self_spend.py` (smallest change; it is executed by tranche_driver.spend with only
   `sid=` and `d=` rewritten -- keep those two assignment lines' shape). If attribution is correct, say so with the
   per-file evidence and explain the 284 subagent calls.
3. `tools/test_self_spend_attribution.py`: fixture project dir in a tmp dir with (a) a main transcript, (b) its real
   subagent file, (c) a foreign file that today's code wrongly counts (if any). Assert both poles: own + own-subagent
   counted, foreign excluded; a sid with no transcript -> None-equivalent output, never 0. Mutation check: copy the
   module, revert the fix, assert red. Print `SELF_SPEND_ATTRIBUTION_PASS=n/n`.
4. Re-measure 71ccfa86 with the fixed meter; put both numbers (before/after) in the receipt.
5. gen2 `budget_tokens.spent_measured`: do NOT invent a total. Fill it only as an object
   `{"value": <sum or null>, "sources": [...], "unknown": [...]}` from Spend tables already on disk
   (`vault/plans/tok18-tranche-context-runtime-2026-10-06.md`, gen2 evidence receipts, tranche results JSON). Missing
   parts are listed under `unknown`; if anything material is unknown, `value` is null. Merge into ledger.json (load,
   change that key only, dump with indent=1) -- never rewrite other keys.

## Receipt
`vault/programs/cognitive-economy/gen2/evidence/tranche/CE-T0a-receipt.md`: classification table, fix (or none),
test pass line, before/after for 71ccfa86, spent_measured object, and a `COMMITS: <hash ...>` line. Pathspec commits
only. Never push.
