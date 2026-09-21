---
milestone: v1
milestone_name: continuation-proven-live
checked: 2026-09-21
phases_audited: [01, 02, 03, 04, 05]
blockers: 0
warnings: 4
process_findings: 1
---

# Cross-phase integration check — milestone v1 `continuation-proven-live`

Produced by the `gsd-integration-checker` subagent dispatched from
`gsd-audit-milestone` step 3. **The subagent could not write this file** — the
`Write` tool is disabled for subagents in this session — so it handed the report
back as text and the orchestrator wrote it here.

**Provenance matters for how you read this.** The body below is a subagent's
report: model output, not a measurement I took. The four findings it rests on
were therefore **re-verified against the source before being recorded**, and
each carries the line I read. A report that is pasted without that step is a
claim about a claim.

| finding | re-verified at | holds? |
|---|---|---|
| F1 — `05-SUMMARY.md` calls the fifth debt open; the code fixed it | `05-SUMMARY.md:235-238` still said "is NOT fixed"; `tools/gsd_long_run.py:725` writes the row | **yes** — corrected in `05-SUMMARY.md` |
| F3 — a second, unexercised producer of `resume_confirmed` | `tools/continuation_transport.py:344` | **yes** |
| F4 — filename-derived vs row-derived session id inside one reap | `tools/gsd_long_run.py:891` matches `data.get("sessionId")` | **yes** |
| F0 — no `REQUIREMENTS.md` | absent from `.planning/` | **yes** |

---

## Verdict

Every expected cross-phase connection in the milestone's stated end-to-end flow
resolves to **WIRED**. **Zero blockers.** Four warnings, all about *records* or
*unexercised parallel paths* rather than broken links.

## End-to-end flow, per leg

| leg | owner phases | status | evidence |
|---|---|---|---|
| watchdog crosses wall → dispatch | 2, 5 | WIRED | `context-watchdog.py:648` `_dispatch_continuation` is the single door; compact leg armed at `:1245` with `expect_prefix="/compact"` |
| route decision (exact / inbox / manual) | 3, 5 | WIRED | `context-watchdog.py:621-645` `_route_for`; both branches ledger (`:665`, `:675`, `:678`) |
| `/compact` typed into the session's OWN pane | 1, 5 | WIRED | flag written `context-watchdog.py:671`; daemon reads `expect_line`/`expect_prefix` at `auto-compact-sendkeys-daemon.ps1:169-170`; extension consumes the tail via `extension/src/extension.js:35,160` → `extension/src/terminal_inbox.js:71` |
| arg-tail rule shared, not duplicated | 5 | WIRED | `terminal_inbox.js:71` defines, `:180` exports, `extension.js:35` imports, `:160` calls; no second regex in `extension.js` |
| daemon records what the extension did | 5 | WIRED | `auto-compact-sendkeys-daemon.ps1:405-406` — `enters=$ent arg_tail=[$at]`, read from the ack |
| resume requested → confirmed | 1, 5 | WIRED | `context-watchdog.py:800-812` `_confirm_resume`, keyed on the marker's `resume_command` and the done-flag mtime |
| stale markers reaped by the session's own clock | 4 | WIRED | `gsd_long_run.py:901` `reap_decision`; clock `session_idle_seconds` `:794`; liveness `:868` |

No leg of the stated flow is broken.

## FINDING 0 (process) — no requirements denominator

There is no `REQUIREMENTS.md`, so no coverage percentage is computable and none
is reported. Phase 4 already says so (`04-VERIFICATION.md:7`). Phase 5 mints
local ids `DEBT-1..3` (`05-SUMMARY.md:55`) that exist in no shared register —
traceable within phase 5 only, not across phases.

## FINDING 1 (WARNING, phase 4 ↔ phase 5) — a SUMMARY moved under its code

`05-SUMMARY.md:235-238` recorded as an open fifth debt: *"a manual
`gsd_long_run.write_trigger()` writes the flag the daemon consumes but not the
`delivery_inbox_requested` ledger row"*. The code today **does** write it —
`tools/gsd_long_run.py:725-727`, `producer="gsd_long_run.write_trigger"`, `kind`
derived from the payload just written.

Failure mode: a reader plans already-done work, or believes the gate's
`crossings`/`confirmed` figures still under-count manual re-arms when they no
longer do.

**CLOSED** — `05-SUMMARY.md` now carries a SUPERSEDED note on that bullet and on
the stale gate figure beside it.

## FINDING 2 (WARNING, phase 5 ↔ runtime) — proven in the repo, wired at runtime only after a reload

`05-SUMMARY.md:74-83,213` declared `V-INBOX-LIVE-MATCHES-REPO` failing *by
design*: the executing copy is `~/.cursor/extensions/kobii.pp-sessions-0.4.0`,
untouched by `f702c5a`.

**Half-closed since the report was written.** The mirror has been applied and
that assertion now passes (`INBOX_PASS=6/6`, `sha=234C8DB0BA7B9051`). What
remains is exactly one thing a gate on disk cannot cover: **the extension host
still runs the previously-loaded module until `Developer: Reload Window`.**
Owner action, unchanged.

## FINDING 3 (WARNING, phase 2/5 ↔ live host) — two producers of the verdict's own event

`_route_for` calls `ct.capture_endpoint()` (`context-watchdog.py:635,639`) on
every dispatch, so `continuation_transport` is on both legs' critical path *for
the route decision*. But delivery through it (`ct.spawn_delivery`, `:662-664`)
happens only on the `orca-exact` branch. On this host the route resolves to
`terminal-inbox` (`:644`), which never calls it for delivery.

So there are **two producers of `resume_confirmed`** —
`continuation_transport.py:344` and `context-watchdog.py:812` — and only the
second has ever fired in this milestone. The milestone verdict (`PROVEN`) rests
on an event whose other implementation this flow has never executed.

Not a break. It is an unexercised parallel implementation of the confirmation
the verdict depends on, and it is named here so nobody later reads
`continuation_transport`'s confirmation path as covered by these two cycles.

## FINDING 4 (WARNING, internal to phase 4) — one decision, two ways of resolving an id

Phase 4 admits a marker only on the **payload** field (`gsd_long_run.py:954`).
Phase 1 judges with `user_issued_command_since` over a transcript located by
`find_transcript(session_id)` (`:318-322`), which globs `*/{session_id}.jsonl` —
a filename, though derived from that same payload id.

Inside one reap decision the id is resolved both ways: `find_transcript` matches
the transcript **filename**, `session_liveness` matches the transcript **row
field** `sessionId` (`:891`). A transcript whose rows carry a different
`sessionId` than its filename (a copy or rename) yields `liveness="unknown"`
with a readable clock — the conservative direction, so it cannot cause a wrong
deletion. Fragility, not a break.

## FINDING 5 (Q5) — nothing one phase fixed was silently re-broken

Specifically checked and intact:

- Phase 4's `resolve_cwd` at `gsd_autorun_marker.py:98` — phase 5 deliberately
  left it and fixed only the sibling `:253` that phase 4 had flagged as adjacent.
- Phase 4's G1 non-admission visibility (`c3b493b`) survives phase 5's residue
  deletion: the two ghost files it named were deleted, but phase 4's gates are
  **synthetic** (`tools/test_marker_admission.py:102` mints its own fixture), so
  the detector did not lose its subject — 7/7 re-run after the deletion. This is
  the class-representing-drill rule paying for itself: a drill pinned to those
  real files would have gone vacuous the moment they were removed.
- Phase 5's floor-instead-of-equality repair to `tools/test_terminal_inbox.py`
  strictly widens what phase 1's instruments can see.

## Scope of this check

15 tool calls, 5 of 5 phases, bounded at 20. Method: read each SUMMARY and
VERIFICATION, then trace each claimed connection into code. It judges **wiring
between phases**; it does not re-run any phase's gates and does not re-measure
the milestone acceptance gate.
