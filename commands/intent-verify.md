---
description: Does the output satisfy the intent that started the work? Joins a spec's declared criteria to the evidence the repo can actually observe, and refuses a done claim when a critical criterion is unmet or unobserved.
---

# /intent-verify

`spec_gate` and `sdd_os/pre_exec_gate` ask whether an intent artifact EXISTS before
coding. Nothing asked whether the output SATISFIES it afterwards. Measured 2026-08-14
across 58 executable gate surfaces: **zero read an intent artifact at close**
(`vault/audits/DONE_GATE_AUDIT.md`). Green tests prove the mechanism works; they say
nothing about whether the right mechanism was built.

This is the other half of that loop, over the artifact that already exists. It defines
no second schema -- the intent is `vault/specs/*.md`, bound to a task by `covers:`
front matter, stating its criteria as V-gate ids.

## Use

```
python tools/intent_verify.py                          # standing gate: resolve + ratchet
python tools/intent_verify.py --task "<description>"   # + observe the spec bound to it
python tools/intent_verify.py --spec vault/specs/x.md --observe
python tools/intent_verify.py --baseline               # freeze today's debt by name
```

## Two tiers, because they prove different things

**resolve** (static) -- does any executable file emit this criterion's id, and does the
standing gate reach that file? This proves an owner EXISTS. It is the weaker statement,
and it is the one the rest of the repo was already making everywhere.

**observe** (bounded subprocess) -- run the owner and read its output for this id.
Only this produces evidence. Only `test_*` / `verify_*` files are ever executed: an
emitter is any file naming the id, and some of those mutate the repo.

## Verdicts (CLAE Part 27 §6 vocabulary, not a new one)

| Verdict | Meaning |
|---|---|
| `DONE_VERIFIED` | every critical criterion observed passing |
| `PARTIAL_VERIFIED` | criticals pass, an advisory criterion does not |
| `BLOCKED` | a critical criterion was observed FAILING |
| `EVIDENCE_INCOMPLETE` | a critical criterion produced no evidence |
| `INTENT_NOT_CAPTURED` | no spec binds this task -- recorded as debt, never blocks |

`EVIDENCE_INCOMPLETE` is deliberately not `BLOCKED`. "I could not check it" and "I
checked it and it failed" are different claims, and collapsing them teaches people to
route around the gate instead of closing it.

## Two constraints that keep it honest

**The blocking condition is an absolute**, never a ratio -- a ratio is satisfied by
deleting criteria.

**The criterion set is a named ratchet** (`vault/governance/intent_ratchet.json`). A
criterion that disappears from a spec is reported as `withdrawn` by name; a criterion
that was reachable and no longer is, as `unjoined_back`. Debt falling is always allowed;
debt growing must be named to be accepted.
