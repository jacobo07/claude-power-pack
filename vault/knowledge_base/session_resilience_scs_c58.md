# SCS C58 — G6 Runtime (Power Beacon + Reentry + Resume Identity) built

**Sealed:** 2026-06-29
**Mode:** EXECUTION MODE — approved scope "real gaps only" (no duplication of sealed systems)
**Verifier:** `tools/test_session_resilience_build.py` → 49/49 ×3 hermetic, exit 0
**No regression:** dataset verifier 10/10; hook hubs 7/7; ram_guard 10/11 (the 1 fail is the
environment-sensitive `V-RAM-PP-OVERHEAD` live-RAM ceiling on a busy host, unrelated to G6).

## What built (the genuine residual gaps only)

The Reality Scan disproved the prompt premise that §6.6/§6.7/resume-identity had no code:
**§6.7 cold-start reentry already exists + is wired + tested** (`extension/restore_guard.js` +
`extension.js`, SCS C50); **snapshot cadence already exists** (`session_start_hub.js` hook 8 +
`ram_guard.py`); **the panel already shows human topics, not UUIDs**. So G6 runtime built only
the missing pieces:

- `modules/session_resilience/power_beacon.py` — the graceful-vs-ungraceful **classifier** with an
  fsync'd, atomically-replaced beacon. Two-signal rule for `ungraceful-shutdown` (active beacon +
  zero live terminals). Distinguishes first-run / reload / graceful-reopen / ungraceful-shutdown.
- `modules/session_resilience/reentry.py` — wires an ungraceful startup into **G5** (recovery event
  stream with `cause=ungraceful-shutdown`) and **G4** (capability-scoped verdict on the terminal
  reentry plan; an unrestorable live pane is a real miss → PARTIAL, never silent RECOVERED).
- `modules/session_resilience/resume_identity.py` — **task-type classification** (debug/research/
  review/architecture/feature/general), stable human **labels** (never a UUID), persistent
  **`session_catalog.json`**, and **`search()`** — extending RESUME_V3 §8, not a new OS.
- Integration: beacon written at SessionStart (canonical `session_start_hub.js`, reuses the existing
  detached python — no new cold start) and at the `ram_guard.py` pre-OOM threshold.

## Activation boundary (honest)

The backbone is proven headless. Three legs are Owner-side and documented in
`docs/g6-runtime-activation.md`: (1) live-mirror sync of the hub, (2) SessionEnd graceful-beacon
hook, (3) extension shell-out to record the recovery + `.vsix` install check. The end-to-end
"reboot → panes back → no Home/Agents" is the Owner-run GUI gate (SCS C50 precedent).

## Lessons sealed (UKDL)

- **HR-G6-BEACON-001** — The power beacon MUST be written synchronously with fsync + atomic replace.
  An async/buffered-only write can be lost when power dies the instant after the call, leaving the
  classifier blind to the very crash it exists to catch. `power_beacon._durable_write_json` enforces
  flush + `os.fsync` + `os.replace`.
- **PR-COLD-START-CHECK-001** — At startup, classify graceful vs ungraceful BEFORE concluding the
  session is fresh. The signal is the beacon (active-with-no-graceful + zero live terminals), checked
  with the two-signal rule. A single signal (terminals gone alone) cannot distinguish a reload from a
  cold start.
- **T-RESUME-UUID-ANTIPATTERN-001** — Exposing a raw session UUID to the operator is an anti-pattern;
  a UUID is for the system, a human label is for the human. Always derive a label from context
  (repo + cleaned first-prompt + work-type). `resume_identity.build_label` + `label_is_human` enforce
  it; the host limit (native picker title = first user message, not renamable) is documented in
  RESUME_V3 §8.5.
