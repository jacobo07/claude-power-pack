# SCS C56 — Session-Resilience-OS-active

Sealed 2026-06-27. Builds on SCS C55 (datasets) + the headless backbone build.
Companion: `modules/session_resilience/` (G1-G5 + integration),
`tools/test_session_resilience_build.py` (40/40 hermetic),
`vault/knowledge_base/session_resilience/` (datasets + G1 extension spec).

## SCS C55 addendum

G1–G5 are **implemented and tested** (Python-feasible backbone), not just
specified. The dataset family (C55) defined the standard; this build realizes the
self-verifiable half of it. The contract is active for everything a headless
agent can prove; the editor-UI capture/apply (G1) and the visual
"indistinguishable from Reload Window" gate remain extension-JS + Owner-run.

## Standard (C56)

A crash/OOM activates the Recovery OS automatically through the integration entry
points (`integration.on_session_start` / `on_ram_threshold`), both **fail-open**.
The roles are fixed:

- **G4 Recovery Acceptance Framework is the arbiter** — no recovery is "complete"
  without a `RECOVERED` verdict from G4. `PARTIAL`/`FAILED` hold the claim and
  enumerate the gap. (HR-SESSION-RESILIENCE-001)
- **G5 observes everything** — every recovery lifecycle event is logged,
  secret-redacted (URB), aggregated and diagnosable.
- **G3 maintains versions** — cheap deltas + exact restore-to-a-prior-version,
  integrity-validated; G4 validates a reconstructed snapshot before use.
- **G2 coordinates windows** — PID-free census, conflict-free restore order,
  single foreground, no two windows owning one conversation.
- **G1 restores the UI** — Python half (manifest model + diff adapter +
  capability-aware marking) is live; capture/apply is extension-JS (spec).

## What is real vs Owner-side

- **Real + agent-verified (40/40 hermetic ×3):** G4 verdict/gate, G5
  events/metrics/diagnosis/redaction, G3 delta/version/integrity/compaction,
  G2 census/identity/binding/order/focus/lock, G1 model/diff/capability/compose,
  integration hub+ram fail-open.
- **Owner-side (documented, not faked):** the extension-JS editor capture/apply
  (`G1_EXTENSION_CAPTURE_SPEC.md`), the live-hook wiring of the integration entry
  points into `session_start_hub` / `ram_guard` (HR-001: agent must not
  self-register global ~/.claude hooks), and the visual indistinguishability gate.

## Corrected dependency graph (sealed)

Data flow is `G1 → {G2, G3} → G4 → G5` (G2/G3 consume G1; G4 consumes G3; G5
consumes G4). The build prompt's graph was inverted at G3↔G4 and G1↔G2/G3 —
caught by reading the datasets + source, not by trusting the prompt.
(T-DEPENDENCY-GRAPH-INVERSION-001)

## UKDL entries added (see ukdl-universal.md §HARD-RULES)

- **HR-SESSION-RESILIENCE-001** — no recovery is complete without a G4 verdict.
- **PR-SNAPSHOT-BEFORE-RISK-001** — before OOM threshold / update / forced kill,
  G3 snapshot + G4 validation; fail-open.
- **T-UI-STATE-API-LIMITS-001** — scroll/focus/tab-order may be host-unavailable;
  G4 is capability-aware (excludes what the platform cannot restore); G5 logs the
  gap. Never force an API that does not exist.
- **T-DEPENDENCY-GRAPH-INVERSION-001** — read the code before trusting a prompt's
  dependency graph; the correct graph is `G1 → {G2,G3} → G4 → G5`.

## Verification

`python tools/test_session_resilience_build.py` → SESSION_RESILIENCE_BUILD_PASS=40/40
(hermetic ×3, EXIT 0). `python tools/test_session_resilience.py` → 8/8 (datasets,
no regression). The anti-thrash gate (Rule 1) governed this build: the sanctioned
recovery is Read-then-one-consolidated-edit, never circumvented.
