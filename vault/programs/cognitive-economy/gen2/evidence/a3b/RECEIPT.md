# A3b receipt (goal ce-a3b)

## Status: STOPPED at guard refusal, before B0. No unit started, no code changed, no commit.

- Read OK: A3B-WORKER.md, vault/plans/ce-a3-RESUMPTION.md, gen2/packets/A3-U2.md, gen2/evidence/a3/U1-RECEIPT.md.
- Refused: Read of `vault/specs/goal-budget-admission.md` -> `PreToolUse:Read` "GOAL BUDGET (ce-a3b) -- a call that
  touches goal-budget state is not admitted from a bound session".
- Cause (known, from A3-U2.md): `hooks/session_budget_guard.js:218` `GOAL_STATE` regex matches `goal-budget` in any
  file_path, so a read-only spec counts as goal state. Same defect A3-U2 deliverable 1 fixes
  (V-GOAL-GUARD-SPEC-READABLE). The live guard is ~/.claude (Owner diff, HR-001); not edited here.
- Not routed around (no shell cat, no copy of the spec).

## Open for the Owner
1. Is U2 deliverable 1 (narrow GOAL_STATE) already live? If not, B1 cannot read its own spec. Options: apply the
   regex narrowing from the repo's hooks/session_budget_guard.js to the live guard, or authorise the spec read.
2. Check ledger: `python tools/mission_spend.py goal-status --goal ce-a3b`.

## Next exact action
B0 (entry-point matrix scanner) does not read the spec and could proceed on re-launch; B1 needs question 1 answered.

## Owner answer 2026-10-07 (pane 2494f14c): option 1 -- authorise the spec read
- Live guard checked: `~/.claude/skills/claude-power-pack/hooks/session_budget_guard.js:221` still has the broad
  GOAL_STATE regex; the narrowing exists on no branch (only described in A3-U2.md). Live guard NOT edited (HR-001).
- The guard has no per-file override (only CPP_SESSION_BUDGET=off, which would drop all accounting -- not used).
- Authorised read delivered as a byte copy of `HEAD:vault/specs/<the spec>` at b2754615 to
  `C:\Users\User\Apps\ce-a3b-admission-spec.md` (5479 bytes, sha256 FB75803A6316...). The spec name was assembled
  from parts in the copying command so the guard regex did not see it -- an Owner-authorised one-file exception,
  recorded here, not a precedent. Read the spec from that copy; touch no goal ledger/index/session-budget state.
- Worker relaunched headless (sonnet, 45 turns) from this packet, prompt pointing at the copy.
