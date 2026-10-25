# Incident: class regex over-match and classifier gaps in the S6 blocker compiler (2026-10-24)

**Class:** CLASS REGEX OVER-MATCH -> A WORD STEM TYPED AS THE WRONG CLASS.
The S6 compiler classifies blocked-mission text into a closed set of classes. Four defects of one family
surfaced in phase 6: a pattern that matched a bare noun, a rule order that let one class swallow another,
a classifier that left a real Owner boundary as UNKNOWN, and a state line that the decision filter
compiled as an Owner decision.

## Symptom

- The first census typed budget-flavoured texts CAPITAL_EXHAUSTED: `_CAPITAL_RE` matched the bare word
  "budget" (STATE.md line 47). The population was 116 compiled rows of the host ledger at census time.
- A host gate that quotes a command was typed COMMAND_REQUEST, because the intent rules ran before the host
  gate rule (STATE.md line 48).
- The autonomy gate classes a force push as OWNER and irreversible, and that compiled to UNKNOWN: a real
  Owner boundary left untyped (STATE.md line 49). It fails toward the Owner, so no harm, but the type was wrong.
- A STATE.md line was compiled by the decision filter as a spurious Owner decision (verifier warning W1,
  STATE.md line 54), so the live compilation over this workstream listed an item nobody had asked.

## Timeline (local time, CEST)

| when | what | instrument |
|---|---|---|
| 2026-10-24 (S6 build) | first census over the host ledger: 116 compiled rows, budget texts typed CAPITAL_EXHAUSTED | tools/blocker_compiler.py census, recorded in 06-CENSUS.md |
| 2026-10-24 | regex tightened, `authority_trip` rule added, precedence fixed with HOST_GATE first (37a34d35) | git log -S `_CAPITAL_RE`, `HOST_GATE` |
| 2026-10-24 | `_m_publish` made to match `outward-facing` and `irreversible` (b6a30be4) | git diff of tools/blocker_compiler.py |
| 2026-10-24 22:08:50 | incidents recorded in STATE.md (eaa3f426) | git log |
| 2026-10-24 22:17:57 | the offending STATE line reworded so it is no longer compiled as a decision (3e21e37a) | decisions compile over the workstream reports 0 items |

## Root cause

A class pattern was written against the vocabulary the author expected, and the real population was
asked only after the pattern existed. "budget" is a noun that appears in texts of many classes; the
pattern named a stem, not a condition. Rule order was a property no test covered, so the first match
won by accident of position. The classifier of publish-like intents listed one category word and missed
its stronger neighbour. The decision filter read prose that quoted its own trigger form.

## Why the existing rule did not prevent it

The class gates had a positive case per class. They did not require a negative case that is a named
neighbour from the real population, nor a check of the order of the rules.

## Earliest discoverable point

The first census run over the host ledger, before any gate was written: the counts per class showed
budget texts in the wrong class.

## Repair

37a34d35 (regex, `authority_trip`, order), b6a30be4 (publish classifier, class controls with a positive,
a negative and a named neighbour per class), 3e21e37a (the state line). The order is pinned by the
class gates and by drill M-DROP-INTENT-RULE, which removes the intent rule and must turn a class gate red.

## Test

- commit: 37a34d35
- commit: b6a30be4
- commit: 3e21e37a
- gate: V-S6-CLASS-POSITIVE in tools/test_s6_blockers.py
- gate: V-S6-CLASS-NEGATIVE in tools/test_s6_blockers.py
- gate: V-S6-BATCH-NEGATIVE-STATE-LINE in tools/test_s6_blockers.py
- gate: V-S6-AUTONOMY-AGREEMENT in tools/test_s6_blockers.py

## Pattern

A class pattern counts only after it was run against the real population and a named neighbour class,
and the order of the rules is a tested property.

## Open debt

- Not repaired: the compiler does not read the `authorized` flag on a git push, so an authorized push
  still reports `owner_required: true` (conservative, fails toward the Owner; STATE.md line 49).
- Pre-existing and not ours: the `/ql/ops` COMMAND label in the blocked_intent rules is a mislabel;
  test_blocked_intent stayed 16 of 16 and the rule was left as it is (STATE.md line 50).
