"""Omni-Singularity Agent (OSA) — proactive Zero-Issue auditor.

Sleepy by default. Activated only by high-signal triggers:
  T1 post-deploy receipt
  T2 post-rollback receipt
  T3 CEPS error cluster (>=3 distinct in current session)
  T4 long session timer (>=120 min)
  T5 manual via /osa CLI

Throttle-gated for the 2026-06-15 programmatic-credit pricing shift.
Graceful degradation when GPU Eyes host is unreachable.

Public surface:
  throttle:    check(), consume(), status()
  never_again: inject(), top_recurring()
  gpu_eyes:    run_visual_qa(), check_availability()
  dispatcher:  should_activate(), run_if_warranted()

Sealed 2026-05-28.
"""
__version__ = "1.0.0"
