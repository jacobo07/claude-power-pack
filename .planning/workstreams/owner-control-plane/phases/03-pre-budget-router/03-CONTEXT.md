# Phase 3: Pre-budget router - Context

**Gathered:** 2026-10-20 (autonomous, discuss skipped; decisions below are binding defaults)

## Goal
Inside `hooks/econ_admission.js`, classify an Owner-typed message BEFORE the affordability block (`decide()`), using the Phase 2 closed grammar (`modules/provider_routing/capital_grammar.py`, no model call), and bind principal + target goal. Dormant until merged to MAIN (the hook is registered from the MAIN checkout).

## Locked facts (see vault/programs/owner-control-plane/P1-reality.md)
- Capture runs before `decide()` at `econ_admission.js:144-152`; `owner_capital_capture.js` is `require`d fail-open, not a separate registration.
- Verbs today: only `econ status|detach` (`econ_admission.js:29`); they stay unchanged.
- MODEL_REQUIRED stays fenced (a message that needs a model call is still blocked at zero headroom).
- Target = explicit goal in the message, or the single open `authority_required` boundary. cwd alone NEVER selects a programme.
- Reuse `tools/decision_plane.py resolve-transcript` as the provenance path; do not reimplement receipts (Phase 4 owns the owner_intent receipt).

## Mandatory fixes carried in (Owner decision D-ocp-1)
1. **D9a**: `capital_authority.py:240` `apply_pending` takes the transcript from `approvals.jsonl[-1]` (latest row of ANY pane). Resolve the transcript per row (the row's own pane/session), never `[-1]`.
2. **Uppercase-sha mismatch**: `capital_authority.py:99` `find_owner_decisions` matches the packet sha in lowercase only; normalise case on both sides so a displayed uppercase hash binds.

## Acceptance (from ROADMAP)
Zero-headroom status, ADD, SET, STOP and random chat each behave per the plan: status answers providerlessly; ADD/SET/STOP classify to an intent routed to the goal; random chat falls through unchanged to `decide()`. Tests drive each from both poles (V-OCP-ROUTER-*), plus D9a and uppercase-sha regressions; existing `tools/test_capital_authority.py` stays green.

## Constraints
- No model call on the router path. Fail-open on hook errors must not weaken the fence (a router error falls through to existing `decide()`).
- Work only in this worktree. Do not touch econ-safex ledger state, open leases, or request capital.
- Foreground bounded test runs; the host is memory-starved, keep calls small.
