---
name: state-lifetime-and-incarnation
metadata:
  opportunity_detector: none
  opportunity_detector_reason: "doctrine skill relocated from ~/.claude/rules by cognitive-economy E1; no opportunity detector exists for it yet"
description: "Use when state is keyed by a long-lived container (pane, tab, row, connection slot) but describes a short-lived occupant (shell, process, session), or when handling reload, reattach, handle rotation and genuine replacement. Write down what each safety-relevant field describes and what creates, clears and must not clear it, clear same-subject state in one action, and test the four transitions separately. Core rule - state lives exactly as long as the thing it describes, so the storage key must equal the subject."
---

# State Lifetime and Incarnation

A piece of state must live exactly as long as the thing it describes. If it lives shorter, the
safety it provides disappears. If it lives longer, stale state poisons whatever comes next. The
usual cause of the second failure is **storage key ≠ subject**. The state is keyed by a long-lived
container (a pane, a tab, a row, a connection slot) but describes a short-lived occupant (one shell,
one process, one session). The container outlives every occupant, so the state becomes immortal.

## Hard Rules

- **State that authorizes a destructive effect must live at least as long as the authority that
  consumes it, or its loss must fail closed.** Renderer-local evidence cannot be the only witness
  for something a host still holds after the renderer dies.
- **State scoped to one incarnation must not survive into a genuinely new one,** unless a stronger
  logical owner translates it on purpose.
- **Reattaching to the same live resource and creating a new resource are different lifecycle
  events.** Route them through different callbacks, and never infer "new" from a remount, a new
  handle or a selection.
- **Logical-session state (an explicit exit, a user decision) outlives lower-level process churn.**
  Only a real start of a new or resumed session may lift it, never the shell or process layer
  beneath it.

## Process Rules

- For every safety-relevant field, write down the object it describes before deciding where it is
  stored. Then list what creates it, what must clear it, and what must NOT clear it.
- Test the four transitions separately: reload, reattach, handle rotation, genuine replacement. One
  test per transition, each able to go red on its own.
- When a fresh incarnation starts, clear the pieces of state that describe the same thing in ONE
  action. Two call sites drift, and the one added later is always the one missed.
- Before blaming your change for a broad red, prove the red is pre-existing by running the same
  suite with and without your change and diffing the failure lists.

## Traps

- **A missing local record often acts as a trigger to ask the authority, so a stale local record
  silently switches that check off.** Measured in Orca X: Sleep asked the host about an unsent line
  only when the renderer had no typing stamp for the pane. A stamp left by a dead shell skipped
  the check for the new shell, whose line nobody else was watching.
- **Pane-keyed storage makes shell-scoped state immortal.** Sweeping the key on close is not
  enough, because a new shell reuses the same key without any close.
- **A fixed flush reads "never happened" on a starved host.** Bound "did it happen" waits on the
  condition, and give "it did not happen" controls a precondition proving the attempt ran. Measured:
  the spawn callback landed after the test's flush, then leaked into the next test as a false call.

## Source

Incident evidence moved to `~/.claude/knowledge_vault/rules-evidence/state-lifetime-and-incarnation.md` (2026-09-28) so it is not re-read on every call. The rule text above is unchanged.
