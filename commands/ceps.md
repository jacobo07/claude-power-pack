---
description: Read and resolve the CEPS error corpus — query recurrence, and confirm or dismiss the Owner-correction drafts that had no reader until now.
---

# /ceps

The capture layer records failures automatically. This is the surface that reads
them back, and the surface that resolves the one signal only a human can classify:
**the Owner correcting the agent.**

Until 2026-09-04 this command did not exist. The PostToolUse advisory printed
`-> Run /ceps query to inspect recurrence` on every captured error, naming a
command that was in neither the 73 PP commands nor `~/.claude/commands`. The
advice was unreachable, which is why nobody ever acted on it.

## Recurrence

```
python tools/ceps.py propagate "<what you are about to do>"
```

Returns the past events whose pattern matches the work at hand — the read side of
the corpus. Silence means nothing relevant was recorded, not that nothing is wrong.

## Correction drafts

`from_stop_hook()` watches the last user turns for an Owner correction — *"no,
actually"*, *"that's wrong"*, *"revert"*, *"no es así"* — and writes a
**low-confidence draft**, never an event. That distinction is deliberate: a
correction is a signal about the agent, not yet a diagnosed defect. Only a human
knows what it was *about*, so only a human closes it.

```
python tools/ceps.py drafts                                 # what is pending
python tools/ceps.py confirm <draft-id> [category] [subsystem] [--root-cause <diagnosis...>]
python tools/ceps.py dismiss <draft-id> [reason...]
```

**Confirming is not diagnosing (SI-00, 2026-11-21).** `confirm` proves one thing:
the Owner corrected the agent. Without `--root-cause` the event is filed
`root_cause_status=UNDIAGNOSED`, `confidence=low`, and its `root_cause` field holds
the symptom (the Owner's redacted words). Pass `--root-cause "<why the agent was
wrong>"` only when the cause is known: it is then `OWNER_DIAGNOSED`/`high`.
`VERIFIED` is reserved for a cause reproduced and fixed. Until 2026-11-21 every
confirmation was stored as a high-confidence root cause.

The detector (`ceps.correction_cue`) fires on a correction that LEADS the turn
(*"no, …"*, *"eso no"*, *"no deberías…"*) or criticises a past act in second person
(*"por qué no has…"*, *"you ignored…"*). Every draft is a HEURISTIC signal and
carries the cue that fired. Retrospective view across sessions: `/analyze-transcripts`.

`category` defaults to `spec-violation` and must be one of: `regression`,
`security`, `drift`, `scaffold`, `incomplete-shell`, `integration`,
`spec-violation`, `tooling`, `env`.

**Both exits matter.** `confirm` promotes the draft into a real event that joins
recurrence scoring and cross-project promotion. `dismiss` retires a false positive.
A queue whose only exit is promotion strands every false positive forever and
grows while reading as healthy — the status-field-nobody-can-transition trap this
estate has already sealed once. Neither verdict deletes the draft: both move it to
`vault/ceps/drafts/{confirmed,dismissed}/`, and a confirmed one carries
`confirmed_event_id` back to the event it became.

## What this does not do

It does not judge the correction for you, and it does not auto-confirm. An
auto-promoted correction would inject the agent's own guess about why the Owner
objected into every future project — worse than the silence it replaces.

Gate: `python tools/test_ceps_corrections.py` (V-CEPS-CORRECTION-*, V-CEPS-CONFIRM-*,
15/15 on 2026-11-21), registered in `verify_spp` as `ceps-corrections`.
