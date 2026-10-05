---
covers: [mission-envelope, set_envelope, token_estimate-setter, mission-model-setter, mission-autocompact-setter, compiled-wu-launch, wu_packet, launch_prompt, cwops-c2, cwops-c3]
status: LIVE once the commit carrying this spec, tools/gsd_mission.py and tools/test_gsd_mission_envelope.py lands
parent: vault/specs/mission-owner-hold.md; vault/plans/cwops-compiled-execution-2026-10-05.md (Next 1, Owner "y" 2026-10-05)
---

# Mission envelope setter (c2) and compiled work-unit launch (c3)

## Why
* c2: `plan_next`/`_cost_breaker` read `token_estimate`, and `worker_argv` reads `model` and `autocompact`,
  but nothing sets them on an existing mission: `arm` has no flag for them and there is no other setter.
  The only way was a hand edit of the record, outside the CAS and the ledger.
* c3: every launch and same-session continuation sends `resume_command` (`/gsd-autonomous ...`). Measured
  2026-10-05 (figure carried by the CWOPS-C23 work-unit brief, not re-measured here): a relaunch spent
  ~3.2M processed of GSD re-entry overhead before concluding; compiled packets in the same plan
  (Results) ran whole work units for 1.4M and 2.8M. Three misses of the first packet run are carried into
  every compiled launch (state from git, decide within authority, await effects before evidence runs).

## Contract
* `set_envelope(mission_id, *, token_estimate=None, model=None, autocompact=None, wu_packet=None)` and
  CLI `gsd_mission.py envelope --mission ID [--token-estimate N] [--model M] [--autocompact N] [--wu-packet PATH]`.
  - Goes through `transition()` (CAS on the observed epoch and state), event `envelope_set`, reason naming
    every field as `old -> new`. State, epoch, owner, `created_at` and `cost_mark` are untouched: the
    budget clock is not reset.
  - Refused (MissionError, nothing written): no field given; unknown mission; terminal mission;
    `token_estimate` / `autocompact` not a positive count (`16000000`, `16M`, `300k`, `1.5m`);
    `model` not an alias (`sonnet`, `opus`, `haiku`, `fable`) or a `claude-` model id;
    `wu_packet` not an existing, non-empty file.
  - Stored as: `token_estimate` int; `autocompact` normalised string (`300k`, the form `--autocompact`
    takes); `model` as given; `wu_packet` = `{path: absolute, sha256, bytes, set_at}`.
* `launch_prompt(rec)`: with no `wu_packet`, exactly `bind_workstream(resume_command, workstream)` (legacy
  bytes unchanged). With one, a compiled prompt naming the packet path and its CURRENT sha256, the three
  lessons, and no `/gsd-` command. Used by `launch_worker` and the same-session continuation.
* A packet that cannot be read at launch refuses the launch BEFORE the epoch is claimed (ledger
  `launch_refused_packet`, `{ok: False}`): a worker is never started without its packet, and never falls
  back to `/gsd-autonomous`.
* GSD completion/hold gates keep keying on `resume_command`; a packet changes only what the worker is told.

## Acceptance (each can go red)
1. Envelope set: fields stored and normalised; state/epoch/created_at/cost_mark unchanged; ledger row
   `envelope_set`; `worker_argv` then carries `--model` and `--autocompact` with the new values and
   `mission_spend.judge` uses the new estimate.
2. Refusals: no field, `0`, `-5`, `abc`, model `gpt-4`/`--x`, missing or empty packet, terminal mission.
   Control: a valid value on the same mission is accepted.
3. `launch_prompt` without packet == bound resume_command (control); with packet contains path, sha256,
   the three lessons and no `/gsd-autonomous`.
4. `launch_worker` with a packet passes the compiled prompt as the last argv element (runner captured);
   with the packet deleted it refuses, the record's epoch is unchanged and no runner call happens.
5. Mutation drill: make `launch_prompt` ignore the packet -> 3 and 4 red; drop the empty-field refusal -> 2 red.

## Rollback
Revert the commit. A record carrying `wu_packet` under old code is ignored (old code sends resume_command);
envelope fields were already read by old code.
