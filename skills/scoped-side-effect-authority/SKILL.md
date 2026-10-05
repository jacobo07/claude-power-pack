---
name: scoped-side-effect-authority
metadata:
  opportunity_detector: none
  opportunity_detector_reason: "doctrine skill relocated from ~/.claude/rules by cognitive-economy E1; no opportunity detector exists for it yet"
description: "Use when software acts for several tenants, workspaces, projects or external accounts and decides whether it may spend money, send messages, publish, provision or mutate third-party state. A process-global flag is only a ceiling, per-scope posture is persisted append-only, absence resolves to the least capability, resolution happens at the side-effect boundary, and observe, mutate, autonomy, capital and credential authorities stay separate. Core rule - process-global mutable state never decides a per-scope side effect."
---

# Scoped Side-Effect Authority

Software that acts on behalf of more than one tenant, workspace, project, customer, or
external account must not decide *whether it may touch the outside world* with
process-global mutable state. The moment two scopes can legitimately hold different
permissions, one global flag forces a process per customer — which is not a product —
or forces every scope to the permission of the most privileged one, which is worse.

This applies to any side effect that is expensive, public, or irreversible: money spent,
messages sent, records published, infrastructure provisioned, third-party accounts
mutated.

## The shape

Separate **the ceiling** from **the operating posture**.

- A process-global control is legitimate as a **ceiling** (a fleet-wide emergency stop)
  and as a **default for new scopes**. It may only ever *lower* a scope's capability.
- The scope's own posture is **persisted, per-scope, append-only**, so a downgrade has an
  actor and a timestamp and "who granted this, when, on what evidence" is answerable
  after an incident. A mutable column loses the previous value, which makes a wrong
  escalation indistinguishable from a scope that always had the permission.
- **Absence means the least capability.** No row, unknown scope, blank scope, unreadable
  value, failed read — all resolve to the safest posture, never to the ambient global.
  This is also the entire migration story: nothing to backfill, and running the migration
  cannot escalate anyone.

Resolve **at the side-effect boundary** — not at planning time, not at dispatch time. That
is what makes a downgrade dominate work that was already queued, and it is what stops a
stale producer from authorising what current state forbids. Authority carried in a message
is *evidence*; it may de-escalate further, it is never authority by itself.

## Do not collapse independent authorities into one enum

Most such systems have several, with different owners and different refusals:

- may the world be **observed** (read)
- may the world be **changed** (mutate)
- who may decide — machine or human (autonomy)
- how much may be committed (capital / quota)
- is the connection sound (credential or provider health)
- which external account is bound to this scope

**Observe and mutate are the pair most often welded together**, and the weld is
invisible until you need to separate them. One historical switch turned "talk to
the real API" on, so reading real state and changing it became the same
permission. The consequence only appears when someone asks for a non-mutating
observation mode: you cannot show a customer their own live data without also
being able to spend their money, and "observe for real, change nothing" turns
out not to be a state the system can be in.

Splitting them is usually additive and small: a second property beside the
mutation one, with its own refusal reason so a scope that may read and not spend
is not told it "is not LIVE" — which points at the wrong fix. Then **re-assert
the mutation gate in the same commit**, including whatever factory decides
which client gets constructed. Widening one safety property is exactly when the
one beside it widens unnoticed, and a test that only checked the new right would
report success in that world.

Stronger still where the shape allows it: make the read path hold a client class
that *has no mutating methods*, so the separation is a property of the type
rather than of a check somebody has to remember. See
`real-context-reachability.md`.

An action must satisfy each independently. Folding them into one boolean loses the
difference between "allowed to call the API" and "allowed to spend", and those need
different error messages because they need different fixes.

## Pick the scope by measurement, not by naming

Ask what the external-account binding is keyed to. If one tenant can hold only one
account per provider, tenant is exactly the right grain. If one tenant can hold several
with different permissions, tenant is too broad and the authority belongs further down.
Read the data model; do not inherit the word from a previous document.

## DON'T

- **Don't assume "take the strictest" composes every gate.** It is correct for a gate that
  always decides. It is *wrong* for a gate that only fires in one specific state — walking
  the mode out of that state switches the guard off, so de-escalation weakens safety.
  Before composing two safety inputs, write down each gate's **no-op branch**.
- **Don't let a test seam bypass the gate on convention alone.** If an injected collaborator
  skips authorization, ship a test that enumerates production modules and asserts none uses
  the seam — with a positive control that the sweep found something, and a second test that
  drives the matcher against the exact bypass shape.
- **Don't change a parameter's default to a sentinel without grepping for callers passing
  the old default explicitly.** They silently move to the other branch.
- **Don't let a read-path convenience authorise an action.** A fallback that resolves an
  unmapped identity to a shared default is fine for rendering a page and is horizontal
  privilege escalation for anything that acts. Keep the fallback; deny it to side effects.
- **Don't grep for the gate to find out who lacks it.** Enumerate the side-effect population
  by an independent marker — HTTP mutation verbs, adapter constructors, job decorators —
  then test each member for the property. See `instrument-before-claim.md`.
- **Don't call the model proven because a multi-scope test is green.** Mutate the resolver
  back to the global read and confirm the drill fails. A green nobody has driven the red
  branch of could have every clause removed and read the same.

## The completeness bar

A side-effecting multi-scope feature is not done until it demonstrates: correct scope
grain; a single canonical resolver; fail-closed on every unknown; a global ceiling that
overrides; scoped state that cannot leak between scopes; persistence that survives
restart without becoming more permissive; enforcement at the side-effect boundary rather
than only in the UI or the dispatcher; parity across UI, API and CLI; an audit trail for
transitions; and a downgrade that beats already-queued work.

## Source

Incident evidence moved to `~/.claude/knowledge_vault/rules-evidence/scoped-side-effect-authority.md` (2026-09-28) so it is not re-read on every call. The rule text above is unchanged.
