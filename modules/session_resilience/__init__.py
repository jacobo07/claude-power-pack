"""Session Resilience OS -- headless backbone (Path A, 2026-06-27).

Implements the self-verifiable Python half of the Session Resilience OS dataset
family (vault/knowledge_base/session_resilience/). Per the IMPLEMENTATION
READINESS REPORT (vault/plans/build-session-resilience-2026-06-27.md), the editor
UI *capture/apply* (G1) is extension-JS and the visual "OOM = Reload Window"
done-gate is Owner-run; everything here is real, hermetic and agent-verifiable.

Data-flow (corrected vs the build prompt): G1 -> {G2, G3} -> G4 -> G5.

Modules:
  models               -- shared canonical StateDescription + dimension extractors
  acceptance      (G4) -- the recovery arbiter: scorecard, equivalence, gate
  telemetry       (G5) -- recovery observability: events, metrics, diagnostics
  snapshot_versioning (G3) -- delta capture + restorable versions  (next sprint)
  multi_window    (G2) -- cross-window census + coordination logic  (next sprint)
  ui_state        (G1) -- Python half: manifest model + diff adapter (next sprint)
"""
from __future__ import annotations

__all__ = ["models", "acceptance", "telemetry"]
