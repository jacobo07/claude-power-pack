#!/usr/bin/env python3
"""CEPS capture entry point for hooks.

Reads one JSON object from stdin and forwards it to
`tools.ceps.record_error`. Exists so hook authors never hand-build a
`python -c` string: the 80-day silent outage of 2026-05..08 was a single
wrong keyword (`scope='session'`) buried in a concatenated `-c` payload,
where no linter, no type checker and no test could see it.

stdin:  {"category":..., "subsystem":..., "root_cause":..., "confidence":...}
stdout: `RECORDED <event_id>` or `REJECTED` (the rejection ledger holds why).
exit:   0 recorded, 3 rejected, 4 malformed input. Never raises -- a hook
        must not disrupt the user path.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.ceps import record_error  # noqa: E402


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (ValueError, OSError):
        print("REJECTED malformed-stdin")
        return 4
    if not isinstance(payload, dict):
        print("REJECTED non-object-stdin")
        return 4

    event = record_error(
        category=str(payload.get("category") or "tooling"),
        subsystem=str(payload.get("subsystem") or "unknown"),
        root_cause=str(payload.get("root_cause") or ""),
        confidence=str(payload.get("confidence") or "low"),
        scope=str(payload.get("scope") or "project"),
    )
    if event is None:
        print("REJECTED")
        return 3
    print(f"RECORDED {event['id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
