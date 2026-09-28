# UKDL candidates -- interactive context rollover (P3), 2026-09-28

Source: `vault/specs/interactive-context-rollover.md`, commits 5624c17, 440bce4. Candidates only:
`ukdl-universal.md` had a live foreign writer when these were written, so they are staged here for
the next consolidation. Each names its evidence and whether it is universal.

## Hard Rule candidates (irreversible damage possible)

### HR-CANDIDATE-NO-FORGET-WITHOUT-READBACK
Never destroy a working context (/clear, fresh session, worker replacement) unless a continuation
capsule was written, read back from disk with a matching hash, judged complete with UNKNOWN counted
as absent, and is still those bytes at the moment of destruction.
Evidence: before P3, /kclear printed "Next: /clear" with nothing checked; `V-ROLLOVER-RED-TAMPER`.
Universal: yes (any agent runtime that resets context).

### HR-CANDIDATE-SUCCESSOR-CERTIFIES-BEFORE-MUTATING
A fresh worker may not mutate shared state until it (a) holds the one claim on the capsule, (b)
reconciled the capsule against the tree now, (c) answered the resume exam. Claim is not
consumption; retire the capsule only on certification.
Evidence: `session_start_hub.js::hookWorkStateResume` deletes the state on read, matched by cwd
only; real-state drill: a refused claimant tried to certify and was fenced (exit 5).
Universal: yes.

## Process Rule candidates

### PR-CANDIDATE-CHECKPOINT-COMPLETENESS-SAFE-RESET-REFRESH-CERTIFY
checkpoint -> completeness -> safe-to-forget -> reset -> reality refresh -> resume exam -> continue.
Preservation and destruction are separate calls; no step may be skipped by a caller in a hurry.

### PR-CANDIDATE-BIND-PER-PROJECT-ARTIFACTS-TO-THEIR-SESSION
Any artifact written to a per-PROJECT path by a per-SESSION actor (handoff, progress file, state
json) must name its session, and consumers must refuse one naming another session. Keep a
per-session copy the shared file cannot overwrite.
Evidence: first real shadow run -- all five obligations came from session e688a932's handoff;
within the hour sibling 958a5394's /kclear overwrote the shared file again.

## Trap candidates

### T-CANDIDATE-PROSE-SUMMARY-AS-CONTINUATION-STATE
A free-text handoff reads like continuation state and carries no HEAD, no goal pointer, no
obligation source and no session identity. Treat it as a note; the capsule is the state.

### T-CANDIDATE-JSON-ARGUMENT-UNDER-POWERSHELL-51
PowerShell 5.1 strips the double quotes out of a JSON argument passed to a native exe, and pipes a
UTF-8 BOM into its stdin. A CLI that takes JSON by argv or stdin must accept one flag per field and
strip the BOM, and must report "unreadable" -- never parse failure as an empty answer.
Evidence: certify saw every field as None; /kclear via PowerShell crashed before writing anything.
Cross-project: yes (every PP CLI taking JSON). Memory already records the BOM half; the argv half is new.

### T-CANDIDATE-REPORTED-RESET-IS-NOT-A-RESET
Assuming /clear succeeded because it was requested. The only evidence is the successor's own
claim + certification row in the ledger; a typed keystroke is a request.
Status: design-level; the active path is not built yet.
