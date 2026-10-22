---
id: SPEC-ECON-OWNER-RAISE
title: Owner raise verb — "subelo 70M" unblocks a spent goal without a model call
tier: T2
status: approved
covers: [econ-owner-raise, owner-raise, econ_admission, econ_plane, subelo, econ-raise, test_econ_containment]
owner_go: "te dije que pudiera aumentarlo con un mensaje tipo 'subelo 70M' ... y que eso este en whitelist" (2026-10-20); answers: +N added to current, successor lease + /kclear
rollback: remove the RAISE branch in hooks/econ_admission.js and the `raise` verb in tools/econ_plane.py; ledger rows already written are ordinary programme/lease_open rows and stay valid
---

# SPEC — Owner raise verb

## Problem

A pane whose goal crossed its cap is blocked before the model by `econ_admission.js`
(TOMBSTONED / EXHAUSTED / NEXT CALL DOES NOT FIT). The status text says "the cap is never
raised here", so the only way out is a terminal `goal-declare --owner` or an OCA packet round
trip. The Owner asked for a typed message that raises the budget and is let through.

## Behaviour

1. **Verb.** A whole-message `subelo N`, `sube N`, `econ raise N`, `raise N` (accents ignored,
   `N` = `70M`, `1.5M`, `800k`, or raw tokens; no comma decimals). Anything else, including the
   same words inside a longer sentence, is not the verb.
2. **Authority.** The verb is executed inside the UserPromptSubmit hook from the harness-supplied
   prompt, which only the Owner types. The model never runs the ledger leg; after a successful raise it receives the message plus the rollover order (item 4).
3. **Effect (blocked session only).** `programme += N`, then a successor lease opens with
   `cap = N + the current lease's unspent remainder` (amended 2026-10-22: a lease cap is that lease's own
   budget, so `current cap + N` re-asked for the spent cap and refused every N once the programme was
   nearly spent: gsdx-factory-2, 69,882,516 short for both 70M and 150M), carrying the current lease's proof/closeout/recovery reserves
   (same carry rule as `GoalLedger._auto_succeed`). Both rows are ordinary journal ops.
4. **Automatic rollover (amended 2026-10-20, Owner: "automaticamente despues se haga el rollout").**
   A crossed cap is still not raised in place; the money is a successor lease. The blocked pane's
   tombstone is lifted by a new journal op `untomb {sid, lease}` written only by this verb and
   only for the lease it just opened (folded by `ledger.py`, `econ_admission.js`, `goal_binding.js`;
   a later tombstone re-fences). The message is NOT blocked: it reaches the model with
   `additionalContext` ordering `/kclear`. The existing rails do the rest: `/kclear` seals,
   `context-watchdog` `_self_sealed_step` types `/clear` once the gate says SAFE_TO_FORGET, and
   `rollover_autotype.js` types `/kresume` in the fresh session.
5. **Idempotent.** Succession id `owner-raise:<sid>:<lease>`; the programme row carries the same
   tag and is skipped when already the last programme row. A pane whose own successor already
   exists (earlier build, or a crash before the untomb) is only unfenced (`resumed`), no new money.
   Once unfenced, the same message answers "not blocked" and writes nothing.
6. **Unbounded (amended 2026-10-20, Owner: "debo poder subirlo la cantidad que quiera").** The old
   1..200M ceiling is gone. `N` must be 1..10^12 tokens, an arithmetic guard only (float precision), not a
   budget policy. The envelope check in item 7 is the only money check.
7. **Refusals say why.** No programme envelope, unknown goal, envelope too small for
   `cap + reserves` (journals the usual `authority_required` row), not blocked, not bound.
8. **Works from any pane (amended 2026-10-20).** The first Owner attempts ran from a pane with no goal
   (`c1fade24`, cwd under no goal root) and got the status screen: the hook only read the binding
   *record*, which a pane that has not yet made a mutating call does not have.
   - No record: the goal the pane would bind to by cwd (`goalBinding`, observe-only, quarantine
     included) is the target.
   - `subelo N <goal>` (name, accents/case ignored) addresses any declared goal from any pane
     (`econ_plane.py raise --goal`, `raise_goal`). Same money path; no pane is unfenced; a fenced pane of
     that goal gets the successor on `/clear`. Answered as a block (0 model tokens, no rollover order).
   - No record, no goal root, no name: refused with the recent goal names, never the status screen.

## Acceptance

`python tools/test_econ_containment.py` exit 0 with new `V-ECON-RAISE-*` gates, each refusal
paired with a control in which the same input is admitted.
