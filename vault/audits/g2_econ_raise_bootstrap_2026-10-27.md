# G2 review: d3f66e44e (econ raise bootstraps an envelope), 2026-10-27

Reviewer: pp-code-reviewer subagent (read-only, did not run suites). Verdict: APPROVE with notes. CRITICAL 0, HIGH 0, MEDIUM 2, LOW 3.
Persisted by the parent session; the findings below are the reviewer's words, the "Parent check" lines are the parent's.

## MEDIUM-1 `raise` CLI has no Owner check (tools/econ_plane.py:279-310)
A model can run `python tools/econ_plane.py raise --goal X --amount N` through a shell. hooks/session_budget_guard.js:238
allowlists only `status|detach`. The risk predates the commit for goals that have an envelope; the commit widens it to envelope-less goals.
The spec line "the model never calls this" holds by convention only.
Parent check: grep over hooks/ finds only allowlists (session_budget_guard.js:238, lib/goal_binding.js:145), no deny of `raise`;
~/.claude/settings.json has no mention of econ_plane. NOT exercised: running it would raise a real goal.
Suggested fix: PreToolUse deny on a shell command that runs `econ_plane.py ... raise`. econ_admission.js starts the CLI from node
(child process), not as a tool call, so that deny would not touch the Owner path.

## MEDIUM-2 reserves of the current lease are dropped (bootstrap with cap present, programme None)
`_bootstrap_envelope` opens the successor with reserves={}; `_open_successor` carries them. A recovery reserve in flight on `cur`
does not carry over. Intent to confirm; spec point 2 is silent.

## LOW
- LOW-1: `g` folded outside the ledger lock; a hold released between fold and set_programme leaves executable above the amount by that hold.
- LOW-2: two panes racing on one goal with different amounts: the lease key is shared, a second programme row can raise programme above the lease; surplus stays executable. `_open_successor` behaves the same.
- LOW-3: programme set + cap None, no replay: returned programme_old/new are misreported (the grant itself is correct).

## Tests
Three gates use one session, no open leases and no reserves; several leases/reserves/sessions are correct by reading, not by test.
Not covered: replay with a different amount or approval_uuid, concurrent raises, A4/A5 beyond existing tests.

## Disposition (Owner "rec", same day)
- MEDIUM-1 FIXED: hooks/session_budget_guard.js `raiseDeny` denies a Bash/PowerShell command that runs `econ_plane.py raise` or calls
  raise_goal/raise_capital/_bootstrap_envelope, for every session, before the CPP_SESSION_BUDGET switch. Gate V-ECON-RAISE-MODEL-DENIED
  (8 denied, 6 controls pass); mutant "remove the deny" KILLED. Seen live: a text-only probe containing the verb was denied.
  Limit (same boundary as GOAL_STATE): stops the direct call, not an agent that writes a script or edits the hook.
- MEDIUM-2 FIXED: `_bootstrap_envelope` carries the current lease's reserves (recovery net of rsettled). Gate
  V-ECON-RAISE-BOOTSTRAP-CARRIES-RESERVES; mutant "drop reserves=carry" KILLED (reserves {} and executable 3500 instead of 3000).
- LOW-1, LOW-2, LOW-3: NOT fixed. LOW-2 and the pre-existing `_open_successor` share the race; LOW-3 is a misreport of programme_old/new
  only. Candidates for a later slice.

## Verified by the reviewer
Callers of raise_goal/raise_capital are only `_main`; `_bootstrap_envelope` is only called by `_opener`; executable == amount by the
arithmetic of ledger.py:488-492; L1 does not match L11 in the replay tag.
