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
python tools/ceps.py confirm <draft-id> [category] [subsystem]
python tools/ceps.py dismiss <draft-id> [reason...]
```

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

Gate: `python tools/test_ceps_corrections.py` (V-CEPS-CORRECTION-*, 9/9),
registered in `verify_spp` as `ceps-corrections`.
