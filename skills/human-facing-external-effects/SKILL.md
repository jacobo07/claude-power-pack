---
name: human-facing-external-effects
metadata:
  opportunity_detector: none
  opportunity_detector_reason: "doctrine skill relocated from ~/.claude/rules by cognitive-economy E1; no opportunity detector exists for it yet"
description: "Use when code sends email, chat, SMS or community posts to a person, gates a message transport, builds an approval queue for outbound messages, or ingests replies. Separate requested from system-initiated sending, send at most once (persisted intent, atomic claim, provider idempotency key, no automatic retry), bind approvals to a hash of the exact bytes, treat inbound replies as untrusted data, and turn a reply into evidence only through an attributable reading. Core rule - a message to a person cannot be taken back."
---

# Human-Facing External Effects

A message to a person — email, chat, a community post, an SMS — is an external
mutation that cannot be taken back and whose cost is paid in someone's
attention. It shares the machinery of other side effects and needs four things
that machinery usually does not give it.

## 1. Classify the sender before you gate the transport

Most mail an application sends answers a request the recipient made: a sign-in
link, a confirmation, a receipt. Mail the system decides to send on someone's
behalf is a different effect. Put the posture / kill-switch / execution gate on
the second class only. Gating the transport itself looks safer and locks users
out the first time the safe default is in force.

Enforce the split structurally: enumerate every module that can reach the
transport (import edge, not a search for the guard), require each to carry a
class and a reason, and require the initiated class to hold the authority and
disclosure guards. Floor on the population, stale-entry clause, synthetic drill.

## 2. At most once, then reconcile

A queue built for machine egress is usually at-least-once, and its stale-claim
recovery resends. For a person that is a duplicate interruption nobody can
retract. So:

- persist the intent before the effect, with its own id;
- claim it atomically (conditional update, rowcount) and commit before sending;
- send under a provider idempotency key equal to that id;
- never retry automatically; an ambiguous result is reconciled only by
  repeating the same keyed request **inside the provider's key window**, and
  outside it a human decides.

Keep accepted, delivered, bounced and replied as separate states. Acceptance is
not delivery.

## 3. An approval names the bytes

Store the hash of exactly what the approver saw. Any edit voids the approval
and re-classifies the text; dispatch re-hashes what it is about to send and
re-checks the recipient's current authorization and address. A generic approval
queue whose client can submit an already-approved item proves nothing.

Refuse the "log it instead" fallback for anything confidential: writing the
message to stdout when no transport is configured is a disclosure to whoever
reads the logs.

## 4. Replies are data

Inbound messages are authenticated by the provider's signature, deduplicated by
the provider's delivery id at the database, and correlated by a signed token in
the reply address plus provider-reported sender — never by subject or quoted
headers. Fetch a body only after correlation names a tenant. Store the text as
untrusted, and make the ingesting module structurally unable to act: it imports
nothing that sends, grants, decides or calls a model, and a test says so. Keep
"could not verify" separate from "verified false".

If the recipient may be a blind evaluator of the same decision, showing them
the system's answer invalidates the evaluation — check before sending.

## 5. A reply becomes evidence only through an attributable reading

- **Separate the author's words first.** A reply carries the message it
  answers. Quoted history, forwards, signatures and footers are set aside
  before anything is read. An HTML reduction that turns tags into spaces
  erases the quoting and, with it, that boundary.
- **Every extracted claim quotes the new author verbatim.** This covers
  numbers and stated confidence too: write "probably", never "92%". The rule
  binds a human structuring the reply as much as a machine. Absent fields
  stay absent.
- **The machine proposes and a person accepts.** Readings are append-only
  and name the row they replace. The database, not only the service, refuses
  a second successor.
- **Origin is computed, never supplied.** It is derived from marks only the
  verified ingestion path leaves, and a sweep proves that path is the only
  writer. Synthetic replies run the whole judgement and count for nothing.
- **Advice about whom to ask stays unimportable** from anything that
  decides, sends or routes until a graduation decision says otherwise.
- **Judge a second source with the first source's rule,** on the same
  observed facts, one sample per (subject, source).
  - Say what the design cannot know: if the effect lies inside a bracket,
    "followed" is `None`, not `0`.
  - If the question shows the system's answer, agreement is anchored.

## DON'T

- **Don't call a race test evidence until the race is positioned** (a
  barrier after the read) and the store has real transactions. An in-memory
  pool that shares one connection turns every rollback into data loss for the
  other session, and a race that never happened passes.
- **Don't drive a surface with identifiers you typed.** Use the ones the
  product mints; an id-grammar mismatch between two planes is invisible until
  you do (measured: a tenant generator and an admission validator disagreed on
  underscores, so no operator could admit a reviewer to their own workspace).
- **Don't forget closure-based gates when you add an entrance.** An env or
  surface gate that walks imports from a fixed entrance list cannot see the new
  path.
- **Don't call a UI test written when the package cannot run it.** Check the
  runner is a declared dependency.

## Source

Incident evidence moved to `~/.claude/knowledge_vault/rules-evidence/human-facing-external-effects.md` (2026-09-28) so it is not re-read on every call. The rule text above is unchanged.
