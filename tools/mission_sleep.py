"""A held mission is asleep, and says what wakes it (GGMC C5, vault/specs/goal-governed-mission-control.md).

Every supervise pass used to restate an unchanged hold: measured 2026-10-06, 3,011 of 3,029 `quota_held`
rows and 1,530 of 1,661 `launch_held` transitions repeated the previous row of the same mission. A hold is
now a `sleep` entry on the record, and the row that announces it is written only when the entry changes.

Wake predicates (closed vocabulary):
  time        {"kind": "time", "at": <epoch s>}                 the provider said when
  owner       {"kind": "owner", "action": <text>}               quarantine: only an Owner release wakes it
  env_ready   {"kind": "env_ready", "reasons": [...]}           the env preflight must answer READY
  cwd_aligned {"kind": "cwd_aligned", "cwd", "work_dir", "status"}  the cwd must carry the work
"""
from __future__ import annotations

WAKE_KINDS = ("time", "owner", "env_ready", "cwd_aligned")


def entry(cause: str, wake: dict, epoch, reason, now: float) -> dict:
    if wake.get("kind") not in WAKE_KINDS:
        raise ValueError(f"unknown wake kind {wake.get('kind')!r}")
    return {"cause": cause, "wake": wake, "epoch": epoch, "reason": reason, "since": now}


def provider_wake(hold: dict) -> dict:
    """A quarantine has no time to wait for; anything else wakes at `until` (None = unknown time)."""
    if hold.get("quarantine"):
        return {"kind": "owner", "action": "provider release after the cause is fixed"}
    return {"kind": "time", "at": hold.get("until")}


def _key(e: dict | None):
    return None if not isinstance(e, dict) else {k: v for k, v in e.items() if k != "since"}


def same(rec: dict, new: dict) -> bool:
    """True when the record already sleeps on exactly this hold: writing it again would be news of nothing."""
    return _key(rec.get("sleep")) == _key(new)
